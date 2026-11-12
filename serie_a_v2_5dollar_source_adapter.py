"""Offline 5Dollar fixture adapter for the unchanged original Serie A V2 features.

This module never calls a provider, odds endpoint, Supabase, GitHub API or network.
It consumes an already captured private raw-response bundle, verifies every page
SHA and collector receive-time against later pre-kickoff quotes, maps only the
original goals/corners/cards inputs, then delegates to the existing frozen
19-feature builder. It never runs model inference or scores target outcomes.

The checked-in rights manifest is HOLD. Real archives are rejected until the
owner/provider and private-storage gates are explicitly approved.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import stat
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlparse

import pandas as pd

from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from serie_a_v2_asof_feature_manifest import (
    _canonical,
    build_manifest as build_original_manifest,
)

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_RIGHTS_MANIFEST = REPO_ROOT / "research" / "source_rights" / "5dollarfootballapi.json"
SERIE_A_PROVIDER_LEAGUE_ID = 3405541143
CURRENT_SERIE_A_SEASON = SERIE_A_RUNTIME_CONFIG.finished_results_source.season
CURRENT_SERIE_A_SEASON_API_PARAMETER = CURRENT_SERIE_A_SEASON[:4]
MIN_COMPLETED_FEATURE_SOURCE_EVENTS = 30
ALLOWED_PLANS = frozenset(("free", "community"))
ALLOWED_QUOTE_FIELDS = frozenset((
    "event_id", "league", "home_team", "away_team",
    "commence_time_utc", "snapshot_time_utc",
))
FORBIDDEN_QUOTE_FIELDS = frozenset((
    "result", "outcome", "score", "home_goals", "away_goals",
    "final_score", "settlement", "prediction_correct", "match_winner",
))
REQUIRED_RIGHTS_FLAGS = (
    "provider_model_use_permitted",
    "provider_cache_permitted",
    "provider_private_retention_permitted",
    "upstream_rights_confirmed",
    "free_serie_a_required_fields_confirmed",
    "field_semantics_confirmed",
    "private_archive_verified",
)
REQUIRED_HISTORY_COLUMNS = (
    "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
    "HC", "AC", "HY", "AY", "HR", "AR",
)


def _parse_utc(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label} must include an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def _is_inside(path: Path, root: Path = REPO_ROOT) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _require_private_path(path: Path, label: str) -> Path:
    candidate = path.expanduser()
    if candidate.is_symlink():
        raise PermissionError(f"{label} must not be a symlink")
    resolved = candidate.resolve()
    if _is_inside(resolved):
        raise ValueError(f"{label} must be outside the public repository")
    if os.name != "posix":
        raise PermissionError(f"{label} filesystem permissions cannot be verified on this platform")
    metadata = resolved.stat(follow_symlinks=False)
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError(f"{label} must be an existing directory")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise PermissionError(f"{label} directory permissions must exclude group/other access")
    return resolved


def _assert_rights_approved(rights: dict) -> None:
    if rights.get("approval_status") != "APPROVED":
        raise PermissionError("5Dollar source rights manifest is HOLD; ingestion is disabled")
    missing = [flag for flag in REQUIRED_RIGHTS_FLAGS if rights.get(flag) is not True]
    if missing:
        raise PermissionError("5Dollar source rights are not approved: " + ", ".join(missing))
    if rights.get("raw_redistribution_permitted") is not False:
        raise PermissionError("raw source redistribution must remain prohibited")


def _validate_feature_source_gate(capture_manifest: dict, request_started: datetime) -> dict:
    """Require the existing 30-event metadata-only gate before any current-season result bytes are read."""
    gate = capture_manifest.get("feature_source_gate")
    if not isinstance(gate, dict):
        raise PermissionError("current-form feature-source gate is missing or closed")
    observed = gate.get("observed_completed_primary_events")
    if (
        gate.get("type") != "CURRENT_FORM_FEATURE_INPUT_ONLY"
        or gate.get("primary_league") != "SERIE_A"
        or gate.get("season") != CURRENT_SERIE_A_SEASON
        or gate.get("minimum_completed_primary_events") != MIN_COMPLETED_FEATURE_SOURCE_EVENTS
        or isinstance(observed, bool)
        or not isinstance(observed, int)
        or observed < MIN_COMPLETED_FEATURE_SOURCE_EVENTS
        or gate.get("metadata_fields_read") != ["match_date", "home_team", "away_team"]
        or gate.get("score_or_result_fields_selected_for_gate") is not False
        or gate.get("passed") is not True
    ):
        raise PermissionError("current-form feature-source gate is not valid or has fewer than 30 metadata-only events")
    checked_at = _parse_utc(gate.get("checked_at_utc"), "feature_source_gate.checked_at_utc")
    if checked_at >= request_started:
        raise ValueError("feature-source gate must be checked strictly before the first source request")

    policy = capture_manifest.get("feature_policy")
    if not isinstance(policy, dict) or any((
        policy.get("use_current_season_matches_only_as_lagged_features") is not True,
        policy.get("same_calendar_day_matches_excluded") is not True,
        policy.get("future_or_unplayed_fixtures_used") is not False,
        policy.get("model_weights_or_feature_definitions_changed") is not False,
        policy.get("model_refit") is not False,
        policy.get("model_selection") is not False,
    )):
        raise PermissionError("current-season feature policy is missing or differs from the frozen V2 contract")

    evaluation_gate = capture_manifest.get("target_outcome_evaluation_gate")
    if not isinstance(evaluation_gate, dict) or (
        evaluation_gate.get("minimum_completed_eligible_prospective_forecasts") != 30
        or evaluation_gate.get("outcomes_read_for_evaluation") is not False
        or evaluation_gate.get("outcome_gate_open") is not False
    ):
        raise PermissionError("the separate 30-forecast target-outcome gate must remain closed")
    if (
        capture_manifest.get("target_outcomes_read") is not False
        or capture_manifest.get("target_outcomes_scored") is not False
        or capture_manifest.get("supabase_writes") != 0
        or capture_manifest.get("paid_provider_calls") != 0
    ):
        raise PermissionError("capture bundle violates the no-target-outcome/no-write/no-paid-call contract")
    return {
        "type": gate["type"],
        "primary_league": gate["primary_league"],
        "season": gate["season"],
        "minimum_completed_primary_events": MIN_COMPLETED_FEATURE_SOURCE_EVENTS,
        "observed_completed_primary_events": observed,
        "checked_at_utc": checked_at.isoformat(),
        "metadata_fields_read": ["match_date", "home_team", "away_team"],
        "score_or_result_fields_selected_for_gate": False,
        "passed": True,
    }


def _safe_page_path(archive_dir: Path, value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("page file path is required")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("page file must be a safe relative path inside the private archive")
    candidate = archive_dir / relative
    current = archive_dir
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise PermissionError("captured page path must not contain symlinks")
        if current != candidate:
            directory_mode = stat.S_IMODE(current.stat(follow_symlinks=False).st_mode)
            if directory_mode & 0o077:
                raise PermissionError("private archive subdirectory permissions must exclude group/other access")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(archive_dir.resolve())
    except ValueError as exc:
        raise ValueError("page file escaped the private archive") from exc
    if not resolved.is_file():
        raise ValueError("captured page file does not exist")
    metadata = resolved.stat(follow_symlinks=False)
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("captured page must be a regular file")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise PermissionError("captured page file permissions must exclude group/other access")
    return resolved


def _validate_request_url(value: object, page_number: int, season_api_parameter: str) -> str:
    if not isinstance(value, str):
        raise ValueError("request_url is required for every captured page")
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != "api.5dollarfootballapi.com":
        raise ValueError("only the documented 5Dollar HTTPS API host is accepted")
    if parsed.username or parsed.password:
        raise ValueError("credentials must not be embedded in request_url")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("request_url has an invalid port") from exc
    if port not in (None, 443):
        raise ValueError("request_url must use the provider's standard HTTPS port")
    if parsed.fragment:
        raise ValueError("request_url fragments are not permitted")
    if parsed.path.rstrip("/") != f"/v1/leagues/{SERIE_A_PROVIDER_LEAGUE_ID}/fixtures":
        raise ValueError("only the Serie A league-fixtures endpoint is accepted")
    try:
        pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    except ValueError as exc:
        raise ValueError("request_url query string is malformed") from exc
    if any(key.lower() in {"key", "api_key", "token", "access_token", "authorization"} for key, _ in pairs):
        raise ValueError("credentials must not be embedded in request_url")
    keys = [key for key, _ in pairs]
    if len(pairs) != 3 or len(set(keys)) != 3 or set(keys) != {"season", "page", "per_page"}:
        raise ValueError("request_url must contain exactly one season, page, and per_page parameter")
    query = dict(pairs)
    if query["page"] != str(page_number):
        raise ValueError("request_url page does not match capture manifest")
    if query["season"] != season_api_parameter:
        raise ValueError("request_url must pin the exact captured season")
    try:
        per_page = int(query["per_page"])
    except ValueError as exc:
        raise ValueError("request_url per_page must be an integer") from exc
    if str(per_page) != query["per_page"] or not 1 <= per_page <= 100:
        raise ValueError("request_url per_page must be between 1 and the documented maximum of 100")
    return value


def _nonnegative_integer(value: object, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a non-negative integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a non-negative integer") from exc
    if number < 0 or str(value).strip() not in {str(number), f"{number}.0"}:
        raise ValueError(f"{label} must be a non-negative integer")
    return number


def _side_stat(fixture: dict, group: str, side: str, field: str) -> int:
    value = fixture.get(group)
    if not isinstance(value, dict):
        raise ValueError(f"finished fixture missing {group}")
    side_value = value.get(side)
    if not isinstance(side_value, dict) and group == "cards":
        raise ValueError(f"finished fixture missing cards.{side}")
    if group == "cards":
        return _nonnegative_integer(side_value.get(field), f"cards.{side}.{field}")
    return _nonnegative_integer(side_value, f"{group}.{side}")


def _unordered_fixture_identity(home: str, away: str, match_day: object) -> tuple[object, tuple[str, str]]:
    """Canonical unordered team pair plus UTC match date for identity embargoes."""
    return (match_day, tuple(sorted((_canonical(home), _canonical(away)))))


def _fixture_to_history_row(
    fixture: dict,
    capture_time: datetime,
    target_ids: set[str],
    target_identities: set[tuple[object, tuple[str, str]]],
    expected_season_id: str,
) -> dict:
    fixture_id = str(fixture.get("id") or "").strip()
    if not fixture_id:
        raise ValueError("fixture id is required")
    if fixture_id in target_ids:
        raise ValueError("target quote event id appears in source history")
    league = fixture.get("league")
    if not isinstance(league, dict) or str(league.get("id")) != str(SERIE_A_PROVIDER_LEAGUE_ID):
        raise ValueError("source fixture is not the exact Serie A provider league")
    if fixture.get("status") != "finished":
        raise ValueError("only provider-confirmed finished fixtures may become feature history")
    if fixture.get("status_reason") is not None or fixture.get("status_code") != "full":
        raise ValueError("finished fixture lacks explicit full-time confirmation")
    season_id = str(fixture.get("league_season_id") or "").strip()
    if not expected_season_id or season_id != expected_season_id:
        raise ValueError("fixture league_season_id differs from the captured season")
    kickoff = _parse_utc(fixture.get("kickoff_utc"), "fixture kickoff_utc")
    if kickoff >= capture_time:
        raise ValueError("finished source fixture kickoff is not before collector capture")
    teams = fixture.get("teams")
    if not isinstance(teams, dict):
        raise ValueError("fixture teams are missing")
    home_obj, away_obj = teams.get("home"), teams.get("away")
    if not isinstance(home_obj, dict) or not isinstance(away_obj, dict):
        raise ValueError("fixture home/away team objects are missing")
    home = home_obj.get("name")
    away = away_obj.get("name")
    if not isinstance(home, str) or not home.strip() or not isinstance(away, str) or not away.strip():
        raise ValueError("fixture home/away team names are missing")
    identity = _unordered_fixture_identity(home, away, kickoff.date())
    if identity in target_identities:
        raise ValueError("target fixture identity appears as a completed source outcome")
    goals = fixture.get("goals")
    if not isinstance(goals, dict):
        raise ValueError("finished fixture missing goals")
    home_goals = _nonnegative_integer(goals.get("home"), "goals.home")
    away_goals = _nonnegative_integer(goals.get("away"), "goals.away")
    result = "H" if home_goals > away_goals else ("A" if home_goals < away_goals else "D")
    return {
        # Match the original Football-Data day-first date representation; ISO
        # YYYY-MM-DD would be ambiguous under the frozen builder's dayfirst parser.
        "Date": kickoff.strftime("%d/%m/%Y"),
        "HomeTeam": home.strip(),
        "AwayTeam": away.strip(),
        "FTHG": home_goals,
        "FTAG": away_goals,
        "FTR": result,
        "HC": _side_stat(fixture, "corners", "home", "home"),
        "AC": _side_stat(fixture, "corners", "away", "away"),
        "HY": _side_stat(fixture, "cards", "home", "yellow"),
        "AY": _side_stat(fixture, "cards", "away", "yellow"),
        "HR": _side_stat(fixture, "cards", "home", "red"),
        "AR": _side_stat(fixture, "cards", "away", "red"),
    }


def _validate_quotes(
    quotes: list[dict],
) -> tuple[list[tuple[datetime, datetime]], set[str], set[tuple[object, tuple[str, str]]]]:
    if not isinstance(quotes, list) or not quotes:
        raise ValueError("quotes must be a non-empty list of pre-match metadata")
    timings = []
    target_ids = set()
    target_identities = set()
    for quote in quotes:
        if not isinstance(quote, dict):
            raise ValueError("quote row must be an object")
        forbidden = FORBIDDEN_QUOTE_FIELDS.intersection(quote)
        if forbidden:
            raise ValueError("target outcome fields are forbidden: " + ", ".join(sorted(forbidden)))
        unexpected = set(quote) - ALLOWED_QUOTE_FIELDS
        if unexpected:
            raise ValueError("quote metadata contains unapproved fields: " + ", ".join(sorted(unexpected)))
        if quote.get("league") != "SERIE_A":
            raise ValueError("quotes must be Serie A only")
        event_id = str(quote.get("event_id") or "").strip()
        if not event_id:
            raise ValueError("quote event_id is required")
        target_ids.add(event_id)
        quote_time = _parse_utc(quote.get("snapshot_time_utc"), "quote snapshot_time_utc")
        kickoff = _parse_utc(quote.get("commence_time_utc"), "quote commence_time_utc")
        if quote_time >= kickoff:
            raise ValueError("quote snapshot must be strictly before kickoff")
        home = quote.get("home_team")
        away = quote.get("away_team")
        if not isinstance(home, str) or not home.strip() or not isinstance(away, str) or not away.strip():
            raise ValueError("quote home/away team identity is required")
        target_identities.add(_unordered_fixture_identity(home, away, kickoff.date()))
        timings.append((quote_time, kickoff))
    return timings, target_ids, target_identities


def build_manifest_from_private_archive(
    archive_dir: Path,
    capture_manifest: dict,
    quotes: list[dict],
    rights_manifest: dict,
) -> dict:
    """Build the unchanged 19-feature manifest from a previously captured private bundle."""
    _assert_rights_approved(rights_manifest)
    archive_dir = _require_private_path(Path(archive_dir), "raw source archive")
    if capture_manifest.get("schema_version") != "5DOLLAR_PRIVATE_CAPTURE_BUNDLE_V1":
        raise ValueError("unsupported capture bundle schema")
    if capture_manifest.get("league_id") != SERIE_A_PROVIDER_LEAGUE_ID:
        raise ValueError("capture bundle must be the exact Serie A league")
    expected_season_id = str(capture_manifest.get("league_season_id") or "").strip()
    if not expected_season_id:
        raise ValueError("capture bundle must pin one league_season_id")
    season_api_parameter = str(capture_manifest.get("season_api_parameter") or "").strip()
    if (capture_manifest.get("season") != CURRENT_SERIE_A_SEASON
            or season_api_parameter != CURRENT_SERIE_A_SEASON_API_PARAMETER):
        raise ValueError("capture bundle must be pinned to the current Serie A 2026/27 season")
    if capture_manifest.get("api_plan") not in ALLOWED_PLANS:
        raise PermissionError("only an approved $0 Free or Community capture is accepted")
    if capture_manifest.get("storage_class") not in {"private_local", "private_object_store"}:
        raise PermissionError("raw source must be held in an approved private archive")
    capture_run_id = capture_manifest.get("capture_run_id")
    if not isinstance(capture_run_id, str) or not re.fullmatch(r"\d{5,20}", capture_run_id):
        raise ValueError("capture_run_id must be a numeric GitHub Actions run id")
    commit_sha = capture_manifest.get("capture_commit_sha")
    if not isinstance(commit_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise ValueError("capture_commit_sha must be a full Git SHA")
    timings, target_ids, target_identities = _validate_quotes(quotes)
    earliest_quote = min(q[0] for q in timings)
    request_started = _parse_utc(capture_manifest.get("request_started_at_utc"), "request_started_at_utc")
    response_received = _parse_utc(capture_manifest.get("response_received_at_utc"), "response_received_at_utc")
    if response_received < request_started:
        raise ValueError("response was received before the request started")
    feature_input_gate = _validate_feature_source_gate(capture_manifest, request_started)
    if response_received >= earliest_quote:
        raise ValueError("source response was not received strictly before every quote")
    if capture_manifest.get("captured_at_utc") != capture_manifest.get("response_received_at_utc"):
        raise ValueError("captured_at_utc must equal the exact response_received_at_utc")
    pages = capture_manifest.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("capture bundle pages are required")
    declared_page_count = capture_manifest.get("page_count")
    if (
        isinstance(declared_page_count, bool)
        or not isinstance(declared_page_count, int)
        or declared_page_count != len(pages)
    ):
        raise ValueError("page_count does not match captured pages")
    page_numbers = []
    all_fixtures = []
    page_evidence = []
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("page record must be an object")
        number = page.get("page_number")
        if isinstance(number, bool) or not isinstance(number, int) or number < 1:
            raise ValueError("page_number must be a positive integer")
        page_numbers.append(number)
        request_url = _validate_request_url(
            page.get("request_url"), number, season_api_parameter
        )
        request_params = dict(parse_qsl(urlparse(request_url).query, keep_blank_values=True, strict_parsing=True))
        requested_per_page = int(request_params["per_page"])
        if page.get("http_status") != 200:
            raise ValueError("all source pages must have HTTP 200")
        page_started = _parse_utc(page.get("request_started_at_utc"), "page request_started_at_utc")
        page_received = _parse_utc(page.get("response_received_at_utc"), "page response_received_at_utc")
        if page_received < page_started or page_started < request_started or page_received > response_received:
            raise ValueError("page request/response times fall outside the capture window")
        if page_received >= earliest_quote:
            raise ValueError("each page must be received before every quote")
        raw_path = _safe_page_path(archive_dir, page.get("file"))
        raw_bytes = raw_path.read_bytes()
        digest = hashlib.sha256(raw_bytes).hexdigest()
        if digest != page.get("response_sha256"):
            raise ValueError("raw source response SHA-256 mismatch")
        if page.get("response_bytes") != len(raw_bytes):
            raise ValueError("raw source response byte count mismatch")
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("raw source response is not valid UTF-8 JSON") from exc
        if payload.get("success") != 1 or not isinstance(payload.get("data"), list):
            raise ValueError("provider response must have success=1 and a data array")
        pagination = payload.get("pagination")
        if (
            not isinstance(pagination, dict)
            or isinstance(pagination.get("page"), bool)
            or not isinstance(pagination.get("page"), int)
            or pagination.get("page") != number
        ):
            raise ValueError("provider pagination page does not match capture manifest")
        if not isinstance(pagination.get("has_more"), bool):
            raise ValueError("provider pagination has_more must be boolean")
        returned_count = pagination.get("count")
        if (
            isinstance(returned_count, bool)
            or not isinstance(returned_count, int)
            or returned_count != len(payload["data"])
        ):
            raise ValueError("provider pagination count does not match page data length")
        returned_per_page = pagination.get("per_page")
        if (
            isinstance(returned_per_page, bool)
            or not isinstance(returned_per_page, int)
            or returned_per_page != requested_per_page
            or len(payload["data"]) > returned_per_page
        ):
            raise ValueError("provider pagination per_page does not match the captured request")
        expected_has_more = number < len(pages)
        if pagination["has_more"] != expected_has_more:
            raise ValueError("capture bundle is incomplete or page order is inconsistent")
        if pagination["has_more"] and len(payload["data"]) != returned_per_page:
            raise ValueError("non-final provider page is shorter than its declared per_page")
        all_fixtures.extend(payload["data"])
        page_evidence.append({
            "page_number": number,
            "request_url": request_url,
            "request_started_at_utc": page_started.isoformat(),
            "response_received_at_utc": page_received.isoformat(),
            "response_sha256": digest,
            "response_bytes": len(raw_bytes),
        })
    if page_numbers != list(range(1, len(pages) + 1)):
        raise ValueError("capture pages must be ordered and contiguous from page 1")
    if response_received != max(
        _parse_utc(page["response_received_at_utc"], "page response_received_at_utc")
        for page in pages
    ):
        raise ValueError("bundle response_received_at_utc must equal the latest page receipt")
    if any(not isinstance(fixture, dict) for fixture in all_fixtures):
        raise ValueError("fixture row must be an object")
    for fixture in all_fixtures:
        league = fixture.get("league")
        if not isinstance(league, dict) or str(league.get("id")) != str(SERIE_A_PROVIDER_LEAGUE_ID):
            raise ValueError("source page contains a fixture outside the exact Serie A league")
        if str(fixture.get("league_season_id") or "").strip() != expected_season_id:
            raise ValueError("source page contains a fixture with a different league_season_id than the pinned Serie A season")
    fixture_ids = [str(f.get("id") or "").strip() for f in all_fixtures]
    if any(not value for value in fixture_ids) or len(fixture_ids) != len(set(fixture_ids)):
        raise ValueError("source fixture ids must be present and unique across pages")
    history_rows = []
    history_identity_keys = set()
    skipped_non_finished = 0
    for fixture in all_fixtures:
        if str(fixture.get("id")) in target_ids:
            raise ValueError("target quote event id appears in raw source bundle")
        if fixture.get("status") != "finished":
            skipped_non_finished += 1
            continue
        history_row = _fixture_to_history_row(
            fixture, response_received, target_ids, target_identities, expected_season_id
        )
        match_day = datetime.strptime(history_row["Date"], "%d/%m/%Y").date()
        history_identity = _unordered_fixture_identity(
            history_row["HomeTeam"], history_row["AwayTeam"], match_day
        )
        if history_identity in history_identity_keys:
            raise ValueError("duplicate unordered historical fixture identity on the same UTC date")
        history_identity_keys.add(history_identity)
        history_rows.append(history_row)
    if len(history_rows) < MIN_COMPLETED_FEATURE_SOURCE_EVENTS:
        raise ValueError("source bundle has fewer than 30 completed current-season Serie A fixtures")
    history = pd.DataFrame(history_rows, columns=REQUIRED_HISTORY_COLUMNS)
    base = build_original_manifest(history, quotes)
    base["schema_version"] = "SERIE_A_ORIGINAL_V2_5DOLLAR_PREQUOTE_SOURCE_V1"
    base["source_provider"] = "5DollarFootballAPI"
    base["source_capture"] = {
        "api_plan": capture_manifest["api_plan"],
        "league_id": SERIE_A_PROVIDER_LEAGUE_ID,
        "league_season_id": expected_season_id,
        "season": capture_manifest.get("season"),
        "season_api_parameter": season_api_parameter,
        "capture_run_id": capture_run_id,
        "capture_commit_sha": commit_sha,
        "request_started_at_utc": request_started.isoformat(),
        "response_received_at_utc": response_received.isoformat(),
        "collector_observation_before_every_quote": True,
        "upstream_source_observation_timestamp_available": False,
        "feature_input_gate": feature_input_gate,
        "feature_input_gate_attestation_required": True,
        "feature_policy": {
            "use_current_season_matches_only_as_lagged_features": True,
            "same_calendar_day_matches_excluded": True,
            "future_or_unplayed_fixtures_used": False,
            "model_weights_or_feature_definitions_changed": False,
            "model_refit": False,
            "model_selection": False,
        },
        "target_outcome_evaluation_gate": {
            "minimum_completed_eligible_prospective_forecasts": 30,
            "outcomes_read_for_evaluation": False,
            "outcome_gate_open": False,
        },
        "attribution_required": rights_manifest.get("public_attribution_required") is True,
        "page_count": len(page_evidence),
        "pages": page_evidence,
        "source_finished_fixture_count": len(history_rows),
        "source_skipped_non_finished_fixture_count": skipped_non_finished,
        "raw_payload_emitted": False,
    }
    # The adapter never opens target outcomes or invokes the candidate.
    # Local timestamp ordering and raw SHA are validated here. The referenced
    # GitHub Actions run/logs must still be checked independently before this
    # can be called an attested source-before-quote observation.
    base["feature_input_gate_passed"] = True
    base["feature_input_gate_attestation_required"] = True
    base["source_before_quote_order_validated"] = True
    base["source_before_quote_verified"] = False
    base["source_capture_attestation_required"] = True
    base["target_outcomes_read"] = False
    base["model_inference_performed"] = False
    base["eligible_for_frozen_prospective_cohort"] = False
    base["eligible_for_product_publication"] = False
    base["scored"] = False
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", required=True, type=Path)
    parser.add_argument("--capture-manifest", required=True, type=Path)
    parser.add_argument("--quotes-json", required=True, type=Path)
    parser.add_argument("--rights-json", type=Path, default=DEFAULT_RIGHTS_MANIFEST)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    archive_dir = _require_private_path(args.archive_dir, "raw source archive")
    capture_path = _require_private_path(args.capture_manifest, "capture manifest")
    quotes_path = _require_private_path(args.quotes_json, "quote metadata")
    output_path = _require_private_path(args.output, "feature manifest output")
    rights_path = args.rights_json.resolve()
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    quotes = json.loads(quotes_path.read_text(encoding="utf-8"))
    rights = json.loads(rights_path.read_text(encoding="utf-8"))
    result = build_manifest_from_private_archive(archive_dir, capture, quotes, rights)
    if output_path.exists():
        raise FileExistsError("refusing to overwrite an existing feature manifest")
    if not output_path.parent.exists():
        raise FileNotFoundError("output parent directory must already exist")
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "schema_version": result["schema_version"],
        "candidate_sha256": result["candidate_sha256"],
        "feature_count": result["feature_count"],
        "source_before_quote_verified": result["source_before_quote_verified"],
        "source_page_count": result["source_capture"]["page_count"],
        "source_finished_fixture_count": result["source_capture"]["source_finished_fixture_count"],
        "eligible_for_frozen_prospective_cohort": False,
        "model_inference_performed": False,
        "target_outcomes_read": False,
        "output": str(output_path),
    }, indent=2))


if __name__ == "__main__":
    main()
