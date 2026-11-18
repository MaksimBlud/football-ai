"""Offline-only Bet365 opening-quote adapter for the unchanged original Serie A V2.

This module has no HTTP client and never calls a provider, GitHub, Supabase or
any network. It consumes an already captured private raw odds response, verifies
its SHA-256 and timestamps, and delegates the unchanged 19-feature calculation
to the existing 5Dollar source adapter.

Only the Bet365 1X2 opening price is accepted. Closing and in-play prices are
never read. The checked-in provider-rights manifest remains HOLD, so real use
fails closed until the existing approval gates are explicitly satisfied.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlparse

import numpy as np
import pandas as pd

import serie_a_v2_5dollar_source_adapter as source_adapter
from historical_football_signal_lab import _market_probabilities
from market_anchor_1x2_v1 import validate_probabilities
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA

PROVIDER = "5DollarFootballAPI"
PROVIDER_HOST = "api.5dollarfootballapi.com"
SERIE_A_LEAGUE_ID = 3405541143
QUOTE_SCHEMA = "5DOLLAR_PRIVATE_OPENING_QUOTE_CAPTURE_V1"
OUTPUT_SCHEMA = "SERIE_A_ORIGINAL_V2_5DOLLAR_OPENING_PREQUOTE_V1"

QUOTE_CAPTURE_FIELDS = frozenset({
    "schema_version",
    "provider",
    "api_plan",
    "storage_class",
    "capture_run_id",
    "capture_commit_sha",
    "source_capture_run_id",
    "source_capture_commit_sha",
    "source_capture_manifest_sha256",
    "source_capture_completed_at_utc",
    "response_file",
    "request_url",
    "http_status",
    "request_started_at_utc",
    "response_received_at_utc",
    "captured_at_utc",
    "response_sha256",
    "response_bytes",
    "paid_provider_calls",
    "supabase_writes",
    "target_outcomes_read",
    "target_outcomes_scored",
})
FIXTURE_FIELDS = frozenset({
    "fixture_id",
    "event_id",
    "league_id",
    "league",
    "home_team",
    "away_team",
    "commence_time_utc",
    "status",
})
FORBIDDEN_TARGET_FIELDS = frozenset({
    "result",
    "outcome",
    "score",
    "goals",
    "home_goals",
    "away_goals",
    "final_score",
    "corners",
    "cards",
    "events",
    "statistics",
    "settlement",
    "prediction_correct",
    "match_winner",
})


def _sha256_json(value: dict) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _positive_finite_odds(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite decimal price greater than 1")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite decimal price greater than 1") from exc
    if not math.isfinite(number) or number <= 1.0:
        raise ValueError(f"{label} must be a finite decimal price greater than 1")
    return number


def _validate_private_relative_file(directory: Path, value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("response_file is required")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("response_file must be a safe relative path")
    path = source_adapter._require_private_file(directory / relative, "raw opening-odds response")
    try:
        path.relative_to(directory.resolve())
    except ValueError as exc:
        raise ValueError("raw opening-odds response escaped its private archive") from exc
    return path


def _validate_fixture_metadata(fixture: dict) -> tuple[str, str, str, datetime]:
    if not isinstance(fixture, dict):
        raise ValueError("fixture_metadata must be an object")
    forbidden = FORBIDDEN_TARGET_FIELDS.intersection(fixture)
    if forbidden:
        raise ValueError(
            "target outcome fields are forbidden: " + ", ".join(sorted(forbidden))
        )
    unexpected = set(fixture) - FIXTURE_FIELDS
    if unexpected:
        raise ValueError(
            "fixture_metadata contains unapproved fields: " + ", ".join(sorted(unexpected))
        )
    required = FIXTURE_FIELDS
    missing = required - set(fixture)
    if missing:
        raise ValueError(
            "fixture_metadata is missing fields: " + ", ".join(sorted(missing))
        )

    fixture_id = str(fixture["fixture_id"]).strip()
    if not re.fullmatch(r"\d{1,20}", fixture_id):
        raise ValueError("fixture_id must be the provider's numeric fixture id")
    if str(fixture["event_id"]).strip() != fixture_id:
        raise ValueError("event_id must equal the provider fixture id for source-history exclusion")
    if fixture["league_id"] != SERIE_A_LEAGUE_ID or fixture["league"] != "SERIE_A":
        raise ValueError("only the exact Serie A provider league is accepted")
    if fixture["status"] != "scheduled":
        raise ValueError("target fixture must be explicitly scheduled")
    home = fixture["home_team"]
    away = fixture["away_team"]
    if not isinstance(home, str) or not home.strip():
        raise ValueError("home_team is required")
    if not isinstance(away, str) or not away.strip():
        raise ValueError("away_team is required")
    if home.strip().casefold() == away.strip().casefold():
        raise ValueError("home_team and away_team must be distinct")
    kickoff = source_adapter._parse_utc(
        fixture["commence_time_utc"], "fixture_metadata.commence_time_utc"
    )
    return fixture_id, home.strip(), away.strip(), kickoff


def _validate_quote_url(value: object, fixture_id: str) -> str:
    if not isinstance(value, str):
        raise ValueError("request_url is required")
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != PROVIDER_HOST:
        raise ValueError("only the documented 5Dollar HTTPS API host is accepted")
    if parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise ValueError("request_url must not contain credentials, query parameters or fragments")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("request_url has an invalid port") from exc
    if port not in (None, 443):
        raise ValueError("request_url must use the standard HTTPS port")
    expected_path = f"/v1/fixtures/{fixture_id}/odds"
    if parsed.path.rstrip("/") != expected_path:
        raise ValueError("request_url must be the exact per-fixture odds endpoint")
    return value


def _validate_capture_manifest(
    quote_capture: dict,
    source_capture: dict,
    fixture_id: str,
    kickoff: datetime,
) -> dict:
    if not isinstance(quote_capture, dict):
        raise ValueError("quote_capture_manifest must be an object")
    unexpected = set(quote_capture) - QUOTE_CAPTURE_FIELDS
    if unexpected:
        raise ValueError(
            "quote_capture_manifest contains unapproved fields: "
            + ", ".join(sorted(unexpected))
        )
    missing = QUOTE_CAPTURE_FIELDS - set(quote_capture)
    if missing:
        raise ValueError(
            "quote_capture_manifest is missing fields: " + ", ".join(sorted(missing))
        )
    if quote_capture["schema_version"] != QUOTE_SCHEMA:
        raise ValueError("unsupported opening-quote capture schema")
    if quote_capture["provider"] != PROVIDER:
        raise ValueError("quote provider does not match 5DollarFootballAPI")
    if quote_capture["api_plan"] != "free":
        raise PermissionError("only the $0 Free plan is accepted")
    if quote_capture["storage_class"] not in {"private_local", "private_object_store"}:
        raise PermissionError("raw opening odds must remain in an approved private archive")
    if quote_capture["http_status"] != 200:
        raise ValueError("opening-odds response must have HTTP 200")
    if quote_capture["paid_provider_calls"] != 0 or quote_capture["supabase_writes"] != 0:
        raise PermissionError("paid provider calls and Supabase writes must remain zero")
    if quote_capture["target_outcomes_read"] is not False:
        raise PermissionError("target outcomes must not be read")
    if quote_capture["target_outcomes_scored"] is not False:
        raise PermissionError("target outcomes must not be scored")

    capture_run_id = quote_capture["capture_run_id"]
    source_run_id = source_capture.get("capture_run_id")
    if not isinstance(capture_run_id, str) or not re.fullmatch(r"\d{5,20}", capture_run_id):
        raise ValueError("quote capture_run_id must be a numeric GitHub Actions run id")
    if not isinstance(source_run_id, str) or not re.fullmatch(r"\d{5,20}", source_run_id):
        raise ValueError("source capture_run_id must be a numeric GitHub Actions run id")
    if quote_capture["source_capture_run_id"] != source_run_id:
        raise ValueError("quote capture references a different source capture run")
    source_commit = source_capture.get("capture_commit_sha")
    if not isinstance(source_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("source capture commit must be a full Git SHA")
    if quote_capture["source_capture_commit_sha"] != source_commit:
        raise ValueError("quote capture references a different source capture commit")
    quote_commit = quote_capture["capture_commit_sha"]
    if not isinstance(quote_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", quote_commit):
        raise ValueError("quote capture commit must be a full Git SHA")
    if quote_capture["source_capture_manifest_sha256"] != _sha256_json(source_capture):
        raise ValueError("source capture manifest SHA-256 mismatch")

    source_received = source_adapter._parse_utc(
        source_capture.get("response_received_at_utc"),
        "source_capture.response_received_at_utc",
    )
    source_completed = source_adapter._parse_utc(
        quote_capture["source_capture_completed_at_utc"],
        "source_capture_completed_at_utc",
    )
    request_started = source_adapter._parse_utc(
        quote_capture["request_started_at_utc"], "quote request_started_at_utc"
    )
    response_received = source_adapter._parse_utc(
        quote_capture["response_received_at_utc"], "quote response_received_at_utc"
    )
    captured_at = source_adapter._parse_utc(
        quote_capture["captured_at_utc"], "quote captured_at_utc"
    )
    if source_received > source_completed:
        raise ValueError("source workflow cannot complete before its final source response")
    if source_completed >= request_started:
        raise ValueError("source workflow must complete strictly before the quote request starts")
    if request_started >= response_received:
        raise ValueError("quote response must be received after its request starts")
    if captured_at != response_received:
        raise ValueError("captured_at_utc must equal the exact quote response receipt time")
    if response_received >= kickoff:
        raise ValueError("raw quote response must be received strictly before kickoff")
    if request_started >= kickoff:
        raise ValueError("quote request must start strictly before kickoff")

    _validate_quote_url(quote_capture["request_url"], fixture_id)
    digest = quote_capture["response_sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("response_sha256 must be a lowercase SHA-256 digest")
    byte_count = quote_capture["response_bytes"]
    if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count <= 0:
        raise ValueError("response_bytes must be a positive integer")

    return {
        "source_response_received_at": source_received,
        "source_capture_completed_at": source_completed,
        "request_started_at": request_started,
        "response_received_at": response_received,
        "captured_at": captured_at,
    }


def build_opening_prequote_manifest(
    source_archive_dir: Path,
    source_capture_manifest: dict,
    quote_archive_dir: Path,
    quote_capture_manifest: dict,
    fixture_metadata: dict,
) -> dict:
    """Verify private source/quote bytes and build the unchanged 19-feature prequote manifest.

    The function is offline-only. The provider rights manifest is checked before
    any raw quote bytes are read. A separate GitHub Actions run/artifact audit is
    still required; this function never marks source_before_quote_verified true.
    """
    source_adapter._assert_rights_approved()
    if source_capture_manifest.get("api_plan") != "free":
        raise PermissionError("only the $0 Free source archive is accepted")
    if (
        source_capture_manifest.get("target_outcomes_read") is not False
        or source_capture_manifest.get("target_outcomes_scored") is not False
        or source_capture_manifest.get("paid_provider_calls") != 0
        or source_capture_manifest.get("supabase_writes") != 0
    ):
        raise PermissionError("source archive violates the no-outcome/no-paid-call/no-write contract")

    source_archive_dir = source_adapter._require_private_directory(
        Path(source_archive_dir), "raw source archive"
    )
    quote_archive_dir = source_adapter._require_private_directory(
        Path(quote_archive_dir), "raw opening-odds archive"
    )
    fixture_id, home, away, kickoff = _validate_fixture_metadata(fixture_metadata)
    timings = _validate_capture_manifest(
        quote_capture_manifest, source_capture_manifest, fixture_id, kickoff
    )

    quote_path = _validate_private_relative_file(
        quote_archive_dir, quote_capture_manifest["response_file"]
    )
    raw_bytes = quote_path.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if digest != quote_capture_manifest["response_sha256"]:
        raise ValueError("raw opening-odds response SHA-256 mismatch")
    if len(raw_bytes) != quote_capture_manifest["response_bytes"]:
        raise ValueError("raw opening-odds response byte count mismatch")
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("raw opening-odds response is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or payload.get("success") != 1:
        raise ValueError("provider response must have success=1")
    if set(payload) - {"success", "data"}:
        raise ValueError("opening-odds response contains unapproved top-level fields")
    data = payload.get("data")
    if not isinstance(data, dict) or set(data) - {"fixture_id", "bookmakers"}:
        raise ValueError("opening-odds response contains unapproved data fields")
    if str(data.get("fixture_id")) != fixture_id:
        raise ValueError("opening-odds response fixture_id does not match target metadata")
    bookmakers = data.get("bookmakers")
    if not isinstance(bookmakers, list):
        raise ValueError("opening-odds response bookmakers must be an array")
    bet365 = [row for row in bookmakers if isinstance(row, dict) and row.get("slug") == "bet365"]
    if len(bet365) != 1:
        raise ValueError("exactly one Bet365 quote is required")
    odds = bet365[0].get("odds")
    if not isinstance(odds, dict):
        raise ValueError("Bet365 odds object is missing")
    one_x_two = odds.get("1x2")
    if not isinstance(one_x_two, dict):
        raise ValueError("Bet365 1X2 market is missing")
    opening = one_x_two.get("opening")
    if not isinstance(opening, dict):
        raise ValueError("Bet365 1X2 opening prices are required; closing/in-play are not substitutes")

    home_odds = _positive_finite_odds(opening.get("home"), "opening.home")
    draw_odds = _positive_finite_odds(opening.get("draw"), "opening.draw")
    away_odds = _positive_finite_odds(opening.get("away"), "opening.away")
    opened_at = source_adapter._parse_utc(opening.get("opened_at"), "Bet365 1X2 opening.opened_at")
    if opened_at <= timings["source_capture_completed_at"]:
        raise ValueError("Bet365 opening quote was not opened strictly after source workflow completion")
    if opened_at > timings["response_received_at"]:
        raise ValueError("Bet365 opening quote timestamp is later than the captured response")
    if opened_at >= kickoff:
        raise ValueError("Bet365 opening quote must be strictly before kickoff")

    market_row = pd.Series({
        "B365H": home_odds,
        "B365D": draw_odds,
        "B365A": away_odds,
    })
    probabilities = np.asarray([_market_probabilities(market_row)], dtype=float)
    probabilities = validate_probabilities(probabilities)
    if probabilities.shape != (1, 3):
        raise ValueError("original market conversion did not return one valid 1X2 probability row")

    quote_metadata = {
        "event_id": fixture_id,
        "league": "SERIE_A",
        "home_team": home,
        "away_team": away,
        "commence_time_utc": kickoff.isoformat(),
        "snapshot_time_utc": opened_at.isoformat(),
    }
    feature_report = source_adapter.build_manifest_from_private_archive(
        source_archive_dir,
        source_capture_manifest,
        [quote_metadata],
    )
    if feature_report.get("candidate_sha256") != FROZEN_SHA:
        raise ValueError("feature report does not reference the original frozen V2 candidate")
    if feature_report.get("feature_count") != 19:
        raise ValueError("feature report does not contain the original 19 V2 features")
    if feature_report.get("model_inference_performed") is not False:
        raise ValueError("opening-quote adapter must not perform model inference")
    if feature_report.get("target_outcomes_read") is not False:
        raise ValueError("opening-quote adapter must not read target outcomes")

    return {
        "schema_version": OUTPUT_SCHEMA,
        "candidate_sha256": FROZEN_SHA,
        "feature_count": 19,
        "feature_manifest": feature_report["feature_manifests"][0],
        "source_capture": feature_report["source_capture"],
        "quote_capture": {
            "provider": PROVIDER,
            "api_plan": "free",
            "bookmaker_slug": "bet365",
            "market_price_stage": "opening",
            "provider_fixture_id": fixture_id,
            "source_capture_run_id": source_capture_manifest["capture_run_id"],
            "source_capture_commit_sha": source_capture_manifest["capture_commit_sha"],
            "source_capture_manifest_sha256": quote_capture_manifest["source_capture_manifest_sha256"],
            "source_response_received_at_utc": timings["source_response_received_at"].isoformat(),
            "source_capture_completed_at_utc": timings["source_capture_completed_at"].isoformat(),
            "quote_opened_at_utc": opened_at.isoformat(),
            "quote_request_started_at_utc": timings["request_started_at"].isoformat(),
            "quote_response_received_at_utc": timings["response_received_at"].isoformat(),
            "kickoff_utc": kickoff.isoformat(),
            "raw_response_sha256": digest,
            "raw_response_bytes": len(raw_bytes),
            "upstream_quote_observation_timestamp_available": True,
            "upstream_source_observation_timestamp_available": False,
            "source_before_quote_order_validated": True,
            "source_before_quote_verified": False,
            "source_capture_attestation_required": True,
            "quote_capture_attestation_required": True,
        },
        "market_odds": {
            "home": home_odds,
            "draw": draw_odds,
            "away": away_odds,
        },
        "market_probabilities": {
            "home": float(probabilities[0, 0]),
            "draw": float(probabilities[0, 1]),
            "away": float(probabilities[0, 2]),
        },
        "source_before_quote_order_validated": True,
        "source_before_quote_verified": False,
        "source_capture_attestation_required": True,
        "quote_capture_attestation_required": True,
        "model_inference_performed": False,
        "target_outcomes_read": False,
        "target_outcomes_scored": False,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "scored": False,
        "paid_provider_calls": 0,
        "supabase_writes": 0,
        "training_or_promotion": False,
    }
