"""Gate-controlled, no-cost current-form source capture for frozen Serie A V2.

The source is used only as lagged features for future fixtures. It does not
read target scores for evaluation, fit/select weights, write Supabase, or call
a paid odds provider. A separate prospective-evaluation gate remains closed
until 30 eligible forecasts from this new forward-only cohort have completed.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

import pandas as pd
import requests
from supabase import create_client

from historical_football_signal_lab import FEATURE_SETS
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA, load_verified_original
from serie_a_v2_live_diagnostic_report import PUBLIC_BASE, _source_codes, fetch_public_history

REPOSITORY = "MaksimBlud/football-ai"
WORKFLOW_PATH = ".github/workflows/serie-a-v2-current-form-source-capture.yml"
SCHEMA_VERSION = "SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1"
CURRENT_CODE = SERIE_A_RUNTIME_CONFIG.finished_results_source.season_code
CURRENT_SEASON = SERIE_A_RUNTIME_CONFIG.finished_results_source.season
CURRENT_SEASON_START = date(int(CURRENT_SEASON[:4]), 7, 1)
CURRENT_SEASON_END = date(int(CURRENT_SEASON[5:9]), 6, 30)
CURRENT_URL = f"{PUBLIC_BASE}/{CURRENT_CODE}/{SERIE_A_RUNTIME_CONFIG.finished_results_source.competition_code}.csv"
CURRENT_FILENAME = f"serie_a_{CURRENT_CODE}.csv"
MANIFEST_FILENAME = "serie_a_v2_current_form_source_manifest.json"
MIN_COMPLETED_FEATURE_SOURCE_EVENTS = 30
MAX_CURRENT_CSV_BYTES = 2_000_000
REQUIRED_COLUMNS = (
    "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
    "HC", "AC", "HY", "AY", "HR", "AR",
)
NUMERIC_COLUMNS = ("FTHG", "FTAG", "HC", "AC", "HY", "AY", "HR", "AR")
V2_ONLY_ALIASES = {"Atalanta BC": "Atalanta"}

def _assert_approved_current_url(url: str) -> None:
    """Fail closed unless the current-season source is the exact public CSV endpoint."""
    parts = urlsplit(url)
    expected_path = (
        f"/mmz4281/{CURRENT_CODE}/"
        f"{SERIE_A_RUNTIME_CONFIG.finished_results_source.competition_code}.csv"
    )
    if (
        parts.scheme != "https"
        or parts.hostname != "www.football-data.co.uk"
        or parts.port not in (None, 443)
        or parts.username is not None
        or parts.password is not None
        or parts.path != expected_path
        or parts.query
        or parts.fragment
    ):
        raise ValueError("current-season source URL is not the approved HTTPS Football-Data URL")


def _canonical_team(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("completed primary event has an empty team identity")
    value = value.strip()
    if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value):
        raise ValueError("completed primary event team identity contains control characters")
    known = SERIE_A_RUNTIME_CONFIG.aliases.get(value, value)
    canonical = V2_ONLY_ALIASES.get(known, known)
    if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in canonical):
        raise ValueError("completed primary event team identity contains control characters")
    return canonical


def count_unique_completed_primary_events(
    rows: list[Mapping[str, Any]], *, before_date: date
) -> int:
    """Count fixture identities only; never request or inspect goal/result fields."""
    unique: set[tuple[str, str, str]] = set()
    for row in rows:
        match_date = row.get("match_date")
        if isinstance(match_date, datetime):
            parsed_date = match_date.date()
        elif isinstance(match_date, date):
            parsed_date = match_date
        elif isinstance(match_date, str):
            try:
                parsed_date = date.fromisoformat(match_date[:10])
            except ValueError as exc:
                raise ValueError("invalid primary event date in gate metadata") from exc
        else:
            raise ValueError("missing primary event date in gate metadata")
        if parsed_date < CURRENT_SEASON_START:
            raise ValueError("primary event metadata contains a pre-season fixture identity")
        if parsed_date > CURRENT_SEASON_END:
            raise ValueError("primary event metadata contains a post-season fixture identity")
        if parsed_date >= before_date:
            continue
        home = _canonical_team(row.get("home_team"))
        away = _canonical_team(row.get("away_team"))
        if home == away:
            raise ValueError("invalid primary event identity in gate metadata")
        identity = (parsed_date.isoformat(), home, away)
        if (identity[0], away, home) in unique:
            raise ValueError("primary event metadata contains a reversed duplicate fixture identity")
        unique.add(identity)
    return len(unique)


def read_completed_primary_event_count(client: Any, *, now: datetime) -> int:
    """Read only event date/team metadata; no goals, result or settlement columns."""
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("feature-source gate clock must have a real UTC offset")
    cutoff = now.astimezone(timezone.utc).date().isoformat()
    rows: list[dict[str, Any]] = []
    start = 0
    page_size = 1000
    while True:
        response = (
            client.table("league_finished_results")
            .select("match_date,home_team,away_team")
            .eq("league", "SERIE_A")
            .eq("season", CURRENT_SEASON)
            .gte("match_date", CURRENT_SEASON_START.isoformat())
            .lt("match_date", cutoff)
            .range(start, start + page_size - 1)
            .execute()
        )
        page = response.data or []
        if not isinstance(page, list):
            raise ValueError("Supabase feature-source gate returned malformed event metadata")
        rows.extend(page)
        if len(page) < page_size:
            break
        start += page_size
        if start > 10000:
            raise ValueError("Supabase feature-source gate pagination exceeded safety bound")
    return count_unique_completed_primary_events(rows, before_date=now.astimezone(timezone.utc).date())


def _primary_event_identities(
    rows: list[Mapping[str, Any]], *, before_date: date
) -> set[tuple[str, str, str]]:
    """Canonical event identities used to prove that the source CSV covers the gate."""
    unique: set[tuple[str, str, str]] = set()
    for row in rows:
        match_date = row.get("match_date")
        if isinstance(match_date, datetime):
            parsed_date = match_date.date()
        elif isinstance(match_date, date):
            parsed_date = match_date
        elif isinstance(match_date, str):
            try:
                parsed_date = date.fromisoformat(match_date[:10])
            except ValueError as exc:
                raise ValueError("invalid primary event date in gate metadata") from exc
        else:
            raise ValueError("missing primary event date in gate metadata")
        if parsed_date < CURRENT_SEASON_START:
            raise ValueError("primary event metadata contains a pre-season fixture identity")
        if parsed_date > CURRENT_SEASON_END:
            raise ValueError("primary event metadata contains a post-season fixture identity")
        if parsed_date >= before_date:
            continue
        home = _canonical_team(row.get("home_team"))
        away = _canonical_team(row.get("away_team"))
        if home == away:
            raise ValueError("invalid primary event identity in gate metadata")
        identity = (parsed_date.isoformat(), home, away)
        if (identity[0], away, home) in unique:
            raise ValueError("primary event metadata contains a reversed duplicate fixture identity")
        unique.add(identity)
    return unique


def read_completed_primary_event_identities(
    client: Any, *, now: datetime
) -> set[tuple[str, str, str]]:
    """Read only date/team metadata and return canonical identities for source parity."""
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("feature-source gate clock must have an explicit UTC offset")
    cutoff_date = now.astimezone(timezone.utc).date()
    cutoff = cutoff_date.isoformat()
    rows: list[dict[str, Any]] = []
    start = 0
    page_size = 1000
    while True:
        response = (
            client.table("league_finished_results")
            .select("match_date,home_team,away_team")
            .eq("league", "SERIE_A")
            .eq("season", CURRENT_SEASON)
            .gte("match_date", CURRENT_SEASON_START.isoformat())
            .lt("match_date", cutoff)
            .range(start, start + page_size - 1)
            .execute()
        )
        page = response.data or []
        if not isinstance(page, list):
            raise ValueError("Supabase feature-source gate returned malformed event metadata")
        rows.extend(page)
        if len(page) < page_size:
            break
        start += page_size
        if start > 10000:
            raise ValueError("Supabase feature-source gate pagination exceeded safety bound")
    return _primary_event_identities(rows, before_date=cutoff_date)


def validate_current_season_csv(raw: bytes, *, captured_at: datetime) -> tuple[pd.DataFrame, int]:
    """Return only completed, fully observed rows strictly before capture day.

    Football-Data is date-only. Same-day results are excluded because no reliable
    kickoff clock is available. Unplayed future rows may exist in the CSV but
    are never converted to features. The returned frame contains no incomplete
    fixtures and exactly the original V2 builder's required columns.
    """
    if (
        not isinstance(captured_at, datetime)
        or captured_at.tzinfo is None
        or captured_at.utcoffset() is None
    ):
        raise ValueError(
            "current-season source capture clock must be timezone-aware with a real UTC offset"
        )
    if not raw or len(raw) > MAX_CURRENT_CSV_BYTES:
        raise ValueError("current-season CSV is empty or exceeds size limit")
    frame = pd.read_csv(BytesIO(raw), low_memory=False)
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError("current-season source lacks required original V2 statistics: "
                         + ", ".join(sorted(missing)))
    missing_date = frame["Date"].isna() | frame["Date"].astype(str).str.strip().eq("")
    payload_columns = ["HomeTeam", "AwayTeam", "FTR", *NUMERIC_COLUMNS]
    has_payload = frame.loc[:, payload_columns].apply(
        lambda column: column.notna() & column.astype(str).str.strip().ne(""),
        axis=0,
    ).any(axis=1)
    if (missing_date & has_payload).any():
        raise ValueError("current-season source contains populated fixture row without date")
    nonblank_dates = ~missing_date
    parsed_dates = pd.to_datetime(frame["Date"], dayfirst=True, format="mixed", errors="coerce")
    if parsed_dates.loc[nonblank_dates].isna().any():
        raise ValueError("current-season source contains an unparseable fixture date")
    frame = frame.loc[nonblank_dates].copy()
    frame["_parsed_date"] = parsed_dates.loc[nonblank_dates].dt.date
    cutoff = captured_at.astimezone(timezone.utc).date()
    ftr = frame["FTR"].fillna("").astype(str).str.strip().str.upper()
    valid_result = ftr.isin(("H", "D", "A"))
    has_statistics = frame.loc[:, list(NUMERIC_COLUMNS)].notna().any(axis=1)
    malformed_prior_result = (
        frame["_parsed_date"].lt(cutoff) & ~valid_result & has_statistics
    )
    if malformed_prior_result.any():
        raise ValueError(
            "past current-season row has statistics but invalid full-time result marker"
        )
    future_completed = frame["_parsed_date"].gt(cutoff) & valid_result
    if future_completed.any():
        raise ValueError("current-season source contains a completed result after capture date")
    pre_season_completed = frame["_parsed_date"].lt(CURRENT_SEASON_START) & valid_result
    if pre_season_completed.any():
        raise ValueError("current-season source contains a completed row before season start")
    post_season_completed = frame["_parsed_date"].gt(CURRENT_SEASON_END) & valid_result
    if post_season_completed.any():
        raise ValueError("current-season source contains a completed row after season end")
    completed = frame.loc[frame["_parsed_date"].lt(cutoff) & valid_result].copy()
    completed["FTR"] = ftr.loc[completed.index]
    if completed.empty:
        raise ValueError("current-season source has no completed prior-day matches")
    for field in NUMERIC_COLUMNS:
        completed[field] = pd.to_numeric(completed[field], errors="coerce")
        if completed[field].isna().any() or (completed[field] < 0).any():
            raise ValueError("completed current-season match has missing/invalid " + field)
        if not completed[field].map(lambda value: float(value).is_integer()).all():
            raise ValueError("completed current-season match has non-integer " + field)
    if ((completed["FTHG"] > completed["FTAG"]) != (completed["FTR"] == "H")).any() or (
        (completed["FTHG"] < completed["FTAG"]) != (completed["FTR"] == "A")
    ).any():
        raise ValueError("current-season result does not match full-time goals")
    identities = []
    direction_by_pair: dict[tuple[str, str, str], tuple[str, str, str]] = {}
    for _, row in completed.iterrows():
        home = _canonical_team(row["HomeTeam"])
        away = _canonical_team(row["AwayTeam"])
        if home == away:
            raise ValueError("current-season fixture has identical canonical teams")
        date_key = row["_parsed_date"].isoformat()
        identity = (date_key, home, away)
        unordered_pair = (date_key, *sorted((home, away)))
        previous_direction = direction_by_pair.get(unordered_pair)
        if previous_direction is not None and previous_direction != identity:
            raise ValueError(
                "current-season source has reversed duplicate fixture identity"
            )
        direction_by_pair[unordered_pair] = identity
        identities.append(identity)
    if len(identities) != len(set(identities)):
        raise ValueError("current-season source has duplicate fixture identities")
    completed["Date"] = completed["_parsed_date"].map(
        lambda value: value.strftime("%d/%m/%Y")
    )
    result = completed.loc[:, list(REQUIRED_COLUMNS)].copy()
    return result, len(frame) - len(completed)


def _read_bounded_current_source_body(response: Any) -> bytes:
    """Consume the pinned current-season CSV with a hard in-memory byte bound.

    requests.get(stream=True) is required: checking response.content after a
    normal eager request does not bound the bytes buffered in memory. The
    response is closed on every success and failure path.
    """
    try:
        if getattr(response, "status_code", None) != 200:
            raise ValueError("current-season source must return a direct HTTP 200 response")
        if getattr(response, "url", None) != CURRENT_URL:
            raise ValueError("current-season source response URL differs from approved HTTPS URL")
        response.raise_for_status()

        headers = getattr(response, "headers", {}) or {}
        declared_length = headers.get("Content-Length")
        if declared_length is not None:
            try:
                declared_bytes = int(declared_length)
            except (TypeError, ValueError):
                raise ValueError("current-season source has an invalid Content-Length") from None
            if declared_bytes < 0:
                raise ValueError("current-season source has a negative Content-Length")
            if declared_bytes > MAX_CURRENT_CSV_BYTES:
                raise ValueError("current-season source exceeds size limit")

        iterator = getattr(response, "iter_content", None)
        if not callable(iterator):
            raise ValueError("current-season source response does not support bounded streaming")
        chunks: list[bytes] = []
        total = 0
        for chunk in iterator(chunk_size=64 * 1024):
            if not chunk:
                continue
            if not isinstance(chunk, bytes):
                raise ValueError("current-season source stream yielded non-byte content")
            total += len(chunk)
            if total > MAX_CURRENT_CSV_BYTES:
                raise ValueError("current-season source exceeds size limit")
            chunks.append(chunk)
        raw = b"".join(chunks)
        if not raw:
            raise ValueError("current-season source response body is empty")
        return raw
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                # Do not replace the source-integrity error with a cleanup error.
                pass


def _current_source_fixture_identities(
    frame: pd.DataFrame,
) -> set[tuple[str, str, str]]:
    """Canonical fixture identities in the already validated current-season CSV."""
    identities: set[tuple[str, str, str]] = set()
    for _, row in frame.iterrows():
        parsed_date = pd.to_datetime(
            row["Date"], dayfirst=True, format="mixed", errors="raise"
        ).date()
        home = _canonical_team(row["HomeTeam"])
        away = _canonical_team(row["AwayTeam"])
        identities.add((parsed_date.isoformat(), home, away))
    return identities


def _fixture_identity_sha256(
    identities: set[tuple[str, str, str]],
) -> str:
    for identity in identities:
        if (
            not isinstance(identity, tuple)
            or len(identity) != 3
            or not all(isinstance(value, str) and value for value in identity)
        ):
            raise ValueError("fixture identity must contain exactly three non-empty strings")
        if any(
            ord(char) < 32 or 127 <= ord(char) <= 159
            for value in identity
            for char in value
        ):
            raise ValueError("fixture identity contains control characters")
    payload = "\n".join("\t".join(identity) for identity in sorted(identities))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def capture_source_archive(
    *,
    output_dir: Path,
    client: Any,
    now: datetime,
    get=requests.get,
    history_fetch=fetch_public_history,
    clock=lambda: datetime.now(timezone.utc),
) -> dict:
    """Capture the ten frozen historical seasons plus the gated current-season source."""
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("source capture clock must have a real UTC offset")
    at = now.astimezone(timezone.utc)
    # Authenticate the frozen candidate and exact source URL before any metadata read,
    # network request, or filesystem output. The manifest must attest the verified artifact.
    candidate = load_verified_original()
    if candidate["artifact_sha256"] != FROZEN_SHA:
        raise ValueError("current-form source capture frozen candidate attestation mismatch")
    _assert_approved_current_url(CURRENT_URL)
    gate_identities = read_completed_primary_event_identities(client, now=at)
    gate_count = len(gate_identities)
    if gate_count < MIN_COMPLETED_FEATURE_SOURCE_EVENTS:
        raise RuntimeError(
            "current-form feature-source gate closed: "
            f"{gate_count} completed primary events < {MIN_COMPLETED_FEATURE_SOURCE_EVENTS}; "
            "no current-season source request was made"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    old_history, old_audit = history_fetch(get=get, capture_dir=output_dir)
    if old_history.empty or len(old_audit) != len(_source_codes()):
        raise ValueError("original frozen historical source archive incomplete")
    response = get(
        CURRENT_URL, timeout=30, allow_redirects=False, stream=True
    )
    # Stream and enforce the actual decompressed byte cap before materializing the
    # CSV. The observation clock is sampled only after the complete bounded body.
    raw = _read_bounded_current_source_body(response)
    observed_clock = clock()
    if (
        not isinstance(observed_clock, datetime)
        or observed_clock.tzinfo is None
        or observed_clock.utcoffset() is None
    ):
        raise ValueError("source observation clock must have a real UTC offset")
    observed_at = observed_clock.astimezone(timezone.utc)
    if observed_at < at:
        raise ValueError("source observation timestamp precedes feature-source gate check")
    current_rows, excluded_rows = validate_current_season_csv(raw, captured_at=observed_at)
    if len(current_rows) < MIN_COMPLETED_FEATURE_SOURCE_EVENTS:
        raise RuntimeError(
            "public current-season source has fewer completed prior-day matches than the feature-source gate"
        )
    source_identities = _current_source_fixture_identities(current_rows)
    missing_gate_identities = gate_identities - source_identities
    if missing_gate_identities:
        raise RuntimeError(
            "current-form CSV omits "
            f"{len(missing_gate_identities)} completed fixture identities used by the metadata gate"
        )
    archive_clock = clock()
    if (
        not isinstance(archive_clock, datetime)
        or archive_clock.tzinfo is None
        or archive_clock.utcoffset() is None
    ):
        raise ValueError("source archive creation clock must have a real UTC offset")
    archive_created_at = archive_clock.astimezone(timezone.utc)
    if archive_created_at < observed_at:
        raise ValueError("source archive creation timestamp precedes source observation")
    current_path = output_dir / CURRENT_FILENAME
    current_path.write_bytes(raw)
    audits = list(old_audit) + [{
        "season_code": CURRENT_CODE,
        "season": CURRENT_SEASON,
        "source_url": CURRENT_URL,
        "archived_source_name": CURRENT_FILENAME,
        "csv_sha256": hashlib.sha256(raw).hexdigest(),
        "source_observed_at_utc": observed_at.isoformat(),
        "completed_source_rows": len(current_rows),
        "total_source_rows": int(pd.read_csv(BytesIO(raw), low_memory=False).shape[0]),
        "excluded_incomplete_or_same_day_rows": excluded_rows,
    }]
    if any(item["season_code"] == CURRENT_CODE for item in old_audit):
        raise ValueError("current season unexpectedly appeared in frozen old-season source list")
    report = {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": "MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY",
        "mode": "RESEARCH_ONLY_CURRENT_FORM_SOURCE_ARCHIVE",
        "repository": REPOSITORY,
        "workflow_path": WORKFLOW_PATH,
        "git_sha": os.environ.get("GITHUB_SHA", ""),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "source_archive_created_at_utc": archive_created_at.isoformat(),
        "frozen_candidate_sha256": candidate["artifact_sha256"],
        "original_feature_builder_git_blob_sha1": "401b3a0893371bfa4a488ec92a4a54af2678c8f7",
        "feature_count": len(candidate["features"]),
        "historical_season_codes": list(_source_codes()),
        "current_season_code": CURRENT_CODE,
        "current_season": CURRENT_SEASON,
        "current_season_source_url": CURRENT_URL,
        "current_season_source_sha256": hashlib.sha256(raw).hexdigest(),
        "current_season_source_observed_at_utc": observed_at.isoformat(),
        "current_season_completed_prior_day_rows": len(current_rows),
        "current_season_total_csv_rows": audits[-1]["total_source_rows"],
        "current_season_excluded_incomplete_or_same_day_rows": excluded_rows,
        "feature_source_gate": {
            "type": "CURRENT_FORM_FEATURE_INPUT_ONLY",
            "primary_league": "SERIE_A",
            "season": CURRENT_SEASON,
            "minimum_completed_primary_events": MIN_COMPLETED_FEATURE_SOURCE_EVENTS,
            "observed_completed_primary_events": gate_count,
            "checked_at_utc": at.isoformat(),
            "metadata_fields_read": ["match_date", "home_team", "away_team"],
            "score_or_result_fields_selected_for_gate": False,
            "gate_fixture_identity_sha256": _fixture_identity_sha256(gate_identities),
            "gate_fixture_identities": [list(identity) for identity in sorted(gate_identities)],
            "gate_fixture_identity_count": gate_count,
            "gate_fixture_identities_covered_by_current_source": len(gate_identities & source_identities),
            "gate_fixture_identities_missing_from_current_source": len(missing_gate_identities),
            "current_source_fixture_identity_sha256": _fixture_identity_sha256(source_identities),
            "current_source_fixture_identity_count": len(source_identities),
            "passed": True,
        },
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
            "purpose_after_gate": "diagnostic review only; no fitting, selection, or promotion",
        },
        "source_files": audits,
        "historical_old_season_file_count": len(old_audit),
        "source_file_count": len(audits),
        "eligible_for_frozen_old_season_cohort": False,
        "eligible_for_current_form_forward_shadow": False,
        "eligible_for_product_publication": False,
        "no_bet": True,
        "paid_provider_calls": 0,
        "supabase_reads": 1,
        "supabase_writes": 0,
        "target_outcomes_read": False,
        "target_outcomes_scored": False,
        "model_refit_or_promotion": False,
    }
    manifest_path = output_dir / MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise RuntimeError("current-form source capture must run in the original GitHub repository")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("current-form V2 source/forecast workflow must run from main")
    url, key = os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise RuntimeError("Supabase read-only source gate credentials are missing")
    client = create_client(url, key)
    report = capture_source_archive(
        output_dir=args.output_dir, client=client, now=datetime.now(timezone.utc)
    )
    print(json.dumps({
        "mode": report["mode"],
        "current_season": report["current_season"],
        "feature_source_gate_passed": report["feature_source_gate"]["passed"],
        "completed_primary_events": report["feature_source_gate"]["observed_completed_primary_events"],
        "current_season_completed_prior_day_rows": report["current_season_completed_prior_day_rows"],
        "historical_old_season_file_count": report["historical_old_season_file_count"],
        "source_file_count": report["source_file_count"],
        "candidate_sha256": report["frozen_candidate_sha256"],
        "paid_provider_calls": report["paid_provider_calls"],
        "supabase_writes": report["supabase_writes"],
        "target_outcomes_scored": report["target_outcomes_scored"],
        "no_bet": report["no_bet"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
