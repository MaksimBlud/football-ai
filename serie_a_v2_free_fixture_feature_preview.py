"""Zero-credit Serie A fixture metadata + frozen V2 feature-readiness preview.

This is a manually dispatched, read-only research probe. It makes exactly one
The Odds API /events request (no odds market), requires the provider's
x-requests-last header to confirm zero credits, verifies a fresh authenticated
current-form source archive first, computes only the original 19 input features,
and never emits probabilities, reads target outcomes, or writes Supabase.
"""
from __future__ import annotations

import argparse
from datetime import datetime, time, timezone
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit

import pandas as pd
import requests

from historical_football_signal_lab import FEATURE_SETS, _snapshot
from serie_a_v2_asof_feature_manifest import (
    FROZEN_FEATURE_BUILDER_GIT_BLOB_SHA,
    _canonical,
    _stats_asof,
    _validate_history,
    _verify_original_feature_builder,
)
from serie_a_v2_current_form_forward_capture import (
    MAX_SOURCE_AGE,
    discover_archives,
    get_archive,
    verify_and_load_archive,
    verify_latest_source_archive,
    verify_source_run,
)
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA, load_verified_original

REPOSITORY = "MaksimBlud/football-ai"
SPORT_KEY = "soccer_italy_serie_a"
EVENTS_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/events"
ALLOWED_EVENT_KEYS = frozenset({
    "id", "sport_key", "sport_title", "commence_time", "home_team", "away_team",
})
MAX_RESPONSE_BYTES = 2_000_000
SCHEMA_VERSION = "SERIE_A_V2_FREE_FIXTURE_FEATURE_PREVIEW_V1"


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("capture clocks must carry a real UTC offset")
    return value.astimezone(timezone.utc)


def _parse_utc(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("provider commence_time must be an ISO-8601 timestamp")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("provider commence_time is malformed") from exc
    return _utc(parsed)


def _assert_source_precedes_request(
    source_attestation: Mapping[str, Any], request_started_at: datetime
) -> tuple[datetime, datetime]:
    started = _utc(request_started_at)
    if source_attestation.get("verified") is not True:
        raise ValueError("verified current-form source archive is required before fixture request")
    if source_attestation.get("fresh_for_new_quote") is not True:
        raise ValueError("current-form source archive is stale; provider request was not made")
    if source_attestation.get("candidate_sha256") != FROZEN_SHA:
        raise ValueError("source archive candidate SHA does not match frozen original V2")
    source_observed = _parse_utc(source_attestation.get("latest_source_observed_at_utc"))
    archive_created = _parse_utc(source_attestation.get("source_archive_created_at_utc"))
    parent = source_attestation.get("parent_run")
    if not isinstance(parent, Mapping):
        raise ValueError("source archive lacks authenticated parent-run metadata")
    parent_completed = _parse_utc(parent.get("run_completed_at_utc"))
    if not (source_observed < archive_created <= parent_completed < started):
        raise ValueError("source observation/archive/parent must finish before fixture capture")
    if started - source_observed > MAX_SOURCE_AGE:
        raise ValueError("current-form source archive exceeded the fixed 24-hour freshness limit")
    return source_observed, archive_created


def _validated_future_events(payload: Any, *, observed_at: datetime) -> list[dict]:
    observed = _utc(observed_at)
    if not isinstance(payload, list):
        raise ValueError("free events endpoint did not return a JSON array")
    fixtures: list[dict] = []
    seen_ids: set[str] = set()
    seen_identities: set[tuple[str, str, str, str]] = set()
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("free events endpoint returned a non-object event")
        extra = set(item) - ALLOWED_EVENT_KEYS
        if extra:
            raise ValueError("events payload contains non-metadata fields; refusing odds/outcome leakage")
        if item.get("sport_key") != SPORT_KEY:
            raise ValueError("free events response contains an unexpected sport key")
        event_id = item.get("id")
        home, away = item.get("home_team"), item.get("away_team")
        if not all(isinstance(v, str) and v.strip() for v in (event_id, home, away)):
            raise ValueError("event identity is incomplete")
        event_id, home, away = event_id.strip(), home.strip(), away.strip()
        kickoff = _parse_utc(item.get("commence_time"))
        # The endpoint may include in-play events; this research capture is future-only.
        if kickoff <= observed:
            continue
        canonical_home, canonical_away = _canonical(home), _canonical(away)
        if canonical_home == canonical_away:
            raise ValueError("event has identical canonical home and away teams")
        identity = (kickoff.isoformat(), canonical_home, canonical_away, event_id)
        if event_id in seen_ids or identity in seen_identities:
            raise ValueError("duplicate future event identity from provider")
        seen_ids.add(event_id)
        seen_identities.add(identity)
        fixtures.append({
            "event_id": event_id,
            "league": "SERIE_A",
            "sport_key": SPORT_KEY,
            "home_team": home,
            "away_team": away,
            "commence_time_utc": kickoff.isoformat(),
        })
    return sorted(fixtures, key=lambda row: (row["commence_time_utc"], row["event_id"]))


def build_feature_readiness_preview(
    history: pd.DataFrame,
    fixtures: list[Mapping[str, Any]],
    *,
    as_of_utc: datetime,
) -> dict:
    """Compute exact original 19 input features only; never infer probabilities."""
    as_of = _utc(as_of_utc)
    builder_sha = _verify_original_feature_builder()
    if builder_sha != FROZEN_FEATURE_BUILDER_GIT_BLOB_SHA:
        raise ValueError("original V2 feature builder SHA mismatch")
    original = load_verified_original()
    names = list(original["features"])
    if original.get("artifact_sha256") != FROZEN_SHA:
        raise ValueError("original frozen V2 candidate SHA mismatch")
    if names != list(FEATURE_SETS["ALL_FOOTBALL"]) or len(names) != 19:
        raise ValueError("original V2 feature order/count drift")
    frame = _validate_history(history)
    histories = _stats_asof(frame, before_day=as_of)
    usable = frame.loc[frame["_match_date"] < pd.Timestamp(as_of.date())]
    output = []
    seen = set()
    for fixture in fixtures:
        event_id = fixture.get("event_id")
        home_label, away_label = fixture.get("home_team"), fixture.get("away_team")
        kickoff = _parse_utc(fixture.get("commence_time_utc"))
        if kickoff <= as_of:
            raise ValueError("feature preview accepts future fixtures only")
        if not all(isinstance(v, str) and v.strip() for v in (event_id, home_label, away_label)):
            raise ValueError("feature preview fixture identity is incomplete")
        home, away = _canonical(home_label), _canonical(away_label)
        identity = (str(event_id), kickoff.isoformat(), home, away)
        if identity in seen:
            raise ValueError("duplicate fixture passed to feature preview")
        seen.add(identity)
        sides = {}
        sides.update(_snapshot(histories[home], "home"))
        sides.update(_snapshot(histories[away], "away"))
        values = {}
        for field in names:
            suffix = field.removeprefix("diff_")
            h, a = sides["home_" + suffix], sides["away_" + suffix]
            values[field] = None if pd.isna(h) or pd.isna(a) else float(h - a)
        coverage = {}
        for role, team, venue_home in (("home", home, True), ("away", away, False)):
            team_rows = usable.loc[
                (usable["_home"] == team) | (usable["_away"] == team), "_match_date"
            ]
            prior = histories[team]
            last_date = team_rows.max().date().isoformat() if not team_rows.empty else None
            coverage[role] = {
                "canonical_team": team,
                "prior_matches_in_frozen_30_match_window": len(prior),
                "prior_matches_at_fixture_venue_in_window": sum(
                    match.venue_home is venue_home for match in prior
                ),
                "last_historical_match_date": last_date,
                "days_since_last_historical_match": (
                    (as_of.date() - team_rows.max().date()).days if not team_rows.empty else None
                ),
            }
        observed_count = sum(value is not None for value in values.values())
        output.append({
            "event_id": str(event_id),
            "home_team": home_label,
            "away_team": away_label,
            "commence_time_utc": kickoff.isoformat(),
            "feature_history_cutoff_utc": datetime.combine(
                as_of.date(), time.min, tzinfo=timezone.utc
            ).isoformat(),
            "features": values,
            "history_coverage": coverage,
            "observed_frozen_feature_count": observed_count,
            "median_imputed_frozen_feature_count": 19 - observed_count,
        })
    return {
        "feature_count": 19,
        "feature_builder_git_blob_sha1": builder_sha,
        "candidate_sha256": FROZEN_SHA,
        "historical_match_rows": int(len(frame)),
        "feature_manifests": output,
        "model_probabilities_emitted": False,
        "market_quotes_read": False,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "target_outcomes_read": False,
        "target_outcomes_scored": False,
        "production_model_loaded": False,
        "production_pkl_touched": False,
        "paid_provider_calls": 0,
        "supabase_writes": 0,
    }


def capture_free_fixture_preview(
    *,
    api_key: str,
    source_attestation: Mapping[str, Any],
    history: pd.DataFrame,
    request_started_at: datetime,
    get: Callable = requests.get,
    clock: Callable = lambda: datetime.now(timezone.utc),
) -> dict:
    """Make exactly one zero-credit /events request after source attestation."""
    started = _utc(request_started_at)
    source_observed, archive_created = _assert_source_precedes_request(
        source_attestation, started
    )
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("THE_ODDS_API_KEY is missing; no provider request was made")
    try:
        response = get(
            EVENTS_URL,
            params={
                "apiKey": api_key,
                "dateFormat": "iso",
                "commenceTimeFrom": started.isoformat().replace("+00:00", "Z"),
            },
            timeout=20,
            allow_redirects=False,
        )
    except Exception as exc:
        # Never propagate a requests exception string: it may contain the query key.
        raise RuntimeError(f"free events request failed ({type(exc).__name__}); credentials redacted") from None
    received = _utc(clock())
    if received < started:
        raise ValueError("response clock precedes request start")
    if getattr(response, "history", None):
        raise ValueError("provider redirect rejected")
    if getattr(response, "status_code", None) != 200:
        raise RuntimeError(f"free events endpoint returned HTTP {getattr(response, 'status_code', 'unknown')}")
    parsed_url = urlsplit(str(getattr(response, "url", "")))
    if (
        parsed_url.scheme != "https"
        or parsed_url.netloc != "api.the-odds-api.com"
        or parsed_url.path != f"/v4/sports/{SPORT_KEY}/events"
    ):
        raise ValueError("provider response URL is outside the pinned HTTPS events endpoint")
    raw = getattr(response, "content", b"")
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("provider response body is empty or exceeds the size limit")
    last_cost = getattr(response, "headers", {}).get("x-requests-last")
    try:
        cost = float(last_cost)
    except (TypeError, ValueError):
        raise ValueError("provider did not attest the last request's quota cost; failing closed") from None
    if not math.isfinite(cost) or cost != 0.0:
        raise ValueError("provider did not attest a zero-credit request; refusing to continue")
    try:
        payload = response.json()
    except Exception:
        raise ValueError("provider events response is not valid JSON") from None
    fixtures = _validated_future_events(payload, observed_at=received)
    feature_preview = build_feature_readiness_preview(history, fixtures, as_of_utc=started)
    source_age_at_start = int((started - source_observed).total_seconds())
    source_age_at_response = int((received - source_observed).total_seconds())
    if source_age_at_response < 0 or source_age_at_response > MAX_SOURCE_AGE.total_seconds():
        raise ValueError("source archive was not fresh throughout the fixture capture")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "CAPTURED" if fixtures else "NO_UPCOMING_FIXTURES",
        "repository": REPOSITORY,
        "captured_at_utc": received.isoformat(),
        "request_started_at_utc": started.isoformat(),
        "provider_endpoint_path": f"/v4/sports/{SPORT_KEY}/events",
        "provider_last_request_cost_credits": 0,
        "provider_response_sha256": hashlib.sha256(raw).hexdigest(),
        "provider_response_bytes": len(raw),
        "future_fixture_count": len(fixtures),
        "source_archive": {
            "artifact_id": source_attestation.get("artifact_id"),
            "sha256": source_attestation.get("artifact_sha256"),
            "created_at_utc": archive_created.isoformat(),
            "latest_source_observed_at_utc": source_observed.isoformat(),
            "age_seconds_at_request_start": source_age_at_start,
            "age_seconds_at_response": source_age_at_response,
            "parent_run_id": source_attestation["parent_run"].get("run_id"),
            "parent_run_head_sha": source_attestation["parent_run"].get("run_head_sha"),
            "parent_run_completed_at_utc": source_attestation["parent_run"].get("run_completed_at_utc"),
        },
        **feature_preview,
        "no_odds_requested": True,
        "no_retry": True,
        "no_redirects": True,
        "no_supabase_access": True,
        "no_schedule": True,
    }


def load_verified_current_source(*, token: str, now: datetime) -> tuple[pd.DataFrame, dict]:
    """Verify the latest successful main source artifact before any provider request."""
    archives = discover_archives(token=token)
    raw_cache: dict[int, bytes] = {}

    def load_cached(artifact_id: int) -> bytes:
        if artifact_id not in raw_cache:
            raw_cache[artifact_id] = get_archive(artifact_id, token=token)
        return raw_cache[artifact_id]

    def verify_parent(archive: Mapping[str, Any], *, quote_time: datetime) -> dict:
        return verify_source_run(archive, quote_time=quote_time, token=token)

    attestation = verify_latest_source_archive(
        archives,
        as_of_utc=_utc(now),
        load_archive=load_cached,
        verify_parent_run=verify_parent,
    )
    if attestation.get("verified") is not True or attestation.get("fresh_for_new_quote") is not True:
        raise RuntimeError("no verified fresh current-form source archive; provider request was not made")
    artifact_id = attestation.get("artifact_id")
    archive = next((item for item in archives if item.get("artifact_id") == artifact_id), None)
    if archive is None or artifact_id not in raw_cache:
        raise ValueError("verified source artifact metadata/cache is missing")
    history, source_meta = verify_and_load_archive(
        raw_cache[artifact_id], archive, attestation["parent_run"]
    )
    if (
        source_meta.get("artifact_sha256") != attestation.get("artifact_sha256")
        or source_meta.get("latest_source_observed_at_utc") != attestation.get("latest_source_observed_at_utc")
        or source_meta.get("manifest", {}).get("frozen_candidate_sha256") != FROZEN_SHA
    ):
        raise ValueError("source archive re-verification disagrees with its attestation")
    return history, attestation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN", "")
    api_key = os.environ.get("THE_ODDS_API_KEY", "")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is missing; no provider request was made")
    if not api_key:
        raise RuntimeError("THE_ODDS_API_KEY is missing; no provider request was made")
    now = datetime.now(timezone.utc)
    history, source_attestation = load_verified_current_source(token=token, now=now)
    request_started = datetime.now(timezone.utc)
    report = capture_free_fixture_preview(
        api_key=api_key,
        source_attestation=source_attestation,
        history=history,
        request_started_at=request_started,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "future_fixture_count": report["future_fixture_count"],
        "provider_last_request_cost_credits": report["provider_last_request_cost_credits"],
        "provider_response_sha256": report["provider_response_sha256"],
        "source_archive_id": report["source_archive"]["artifact_id"],
        "source_archive_sha256": report["source_archive"]["sha256"],
        "candidate_sha256": report["candidate_sha256"],
        "feature_count": report["feature_count"],
        "model_probabilities_emitted": report["model_probabilities_emitted"],
        "target_outcomes_read": report["target_outcomes_read"],
        "paid_provider_calls": report["paid_provider_calls"],
        "supabase_writes": report["supabase_writes"],
    }, indent=2))


if __name__ == "__main__":
    main()
