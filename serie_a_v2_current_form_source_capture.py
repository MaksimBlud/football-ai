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

import pandas as pd
import requests
from supabase import create_client

from historical_football_signal_lab import FEATURE_SETS
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA
from serie_a_v2_live_diagnostic_report import PUBLIC_BASE, _source_codes, fetch_public_history

REPOSITORY = "MaksimBlud/football-ai"
WORKFLOW_PATH = ".github/workflows/serie-a-v2-current-form-source-capture.yml"
SCHEMA_VERSION = "SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1"
CURRENT_CODE = SERIE_A_RUNTIME_CONFIG.finished_results_source.season_code
CURRENT_SEASON = SERIE_A_RUNTIME_CONFIG.finished_results_source.season
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


def _require_aware_utc(value: datetime, *, label: str) -> datetime:
    """Fail closed unless a timestamp has an explicit, valid UTC offset."""
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _validated_archive_created_at(observed_at: datetime, created_at: datetime) -> datetime:
    """Require the archive timestamp to be aware and not precede source observation."""
    observed = _require_aware_utc(observed_at, label="current-season source observation clock")
    created = _require_aware_utc(created_at, label="source archive creation clock")
    if created < observed:
        raise ValueError("source archive creation time precedes source observation time")
    return created


def _canonical_team(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("completed primary event has an empty team identity")
    value = value.strip()
    known = SERIE_A_RUNTIME_CONFIG.aliases.get(value, value)
    return V2_ONLY_ALIASES.get(known, known)


def count_unique_completed_primary_events(
    rows: list[Mapping[str, Any]], *, before_date: date
) -> int:
    """Count fixture identities only; never request or inspect goal/result fields."""
    unique: set[tuple[str, str, str]] = set()
    for row in rows:
        match_date = row.get("match_date")
        if isinstance(match_date, date):
            parsed_date = match_date
        elif isinstance(match_date, str):
            try:
                parsed_date = date.fromisoformat(match_date[:10])
            except ValueError as exc:
                raise ValueError("invalid primary event date in gate metadata") from exc
        else:
            raise ValueError("missing primary event date in gate metadata")
        if parsed_date >= before_date:
            continue
        home = _canonical_team(row.get("home_team"))
        away = _canonical_team(row.get("away_team"))
        if home == away:
            raise ValueError("invalid primary event identity in gate metadata")
        unique.add((parsed_date.isoformat(), home, away))
    return len(unique)


def read_completed_primary_event_count(client: Any, *, now: datetime) -> int:
    """Read only event date/team metadata; no goals, result or settlement columns."""
    if now.tzinfo is None:
        raise ValueError("feature-source gate clock must be timezone-aware")
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
            .gte("match_date", "2026-07-01")
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


def validate_current_season_csv(raw: bytes, *, captured_at: datetime) -> tuple[pd.DataFrame, int]:
    """Return only completed, fully observed rows strictly before capture day.

    Football-Data is date-only. Same-day results are excluded because no reliable
    kickoff clock is available. Unplayed future rows may exist in the CSV but
    are never converted to features. The returned frame contains no incomplete
    fixtures and exactly the original V2 builder's required columns.
    """
    if captured_at.tzinfo is None:
        raise ValueError("current-season source capture clock must be timezone-aware")
    if not raw or len(raw) > MAX_CURRENT_CSV_BYTES:
        raise ValueError("current-season CSV is empty or exceeds size limit")
    frame = pd.read_csv(BytesIO(raw), low_memory=False)
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError("current-season source lacks required original V2 statistics: "
                         + ", ".join(sorted(missing)))
    nonblank_dates = frame["Date"].notna()
    parsed_dates = pd.to_datetime(frame["Date"], dayfirst=True, format="mixed", errors="coerce")
    if parsed_dates.loc[nonblank_dates].isna().any():
        raise ValueError("current-season source contains an unparseable fixture date")
    frame = frame.loc[nonblank_dates].copy()
    frame["_parsed_date"] = parsed_dates.loc[nonblank_dates].dt.date
    cutoff = captured_at.astimezone(timezone.utc).date()
    ftr = frame["FTR"].fillna("").astype(str).str.strip().str.upper()
    valid_result = ftr.isin(("H", "D", "A"))
    future_completed = frame["_parsed_date"].gt(cutoff) & valid_result
    if future_completed.any():
        raise ValueError("current-season source contains a completed result after capture date")
    completed = frame.loc[frame["_parsed_date"].lt(cutoff) & valid_result].copy()
    completed["FTR"] = ftr.loc[completed.index]
    if completed.empty:
        raise ValueError("current-season source has no completed prior-day matches")
    for field in NUMERIC_COLUMNS:
        completed[field] = pd.to_numeric(completed[field], errors="coerce")
        if completed[field].isna().any() or (completed[field] < 0).any():
            raise ValueError("completed current-season match has missing/invalid " + field)
    if ((completed["FTHG"] > completed["FTAG"]) != (completed["FTR"] == "H")).any() or (
        (completed["FTHG"] < completed["FTAG"]) != (completed["FTR"] == "A")
    ).any():
        raise ValueError("current-season result does not match full-time goals")
    identities = []
    for _, row in completed.iterrows():
        home = _canonical_team(row["HomeTeam"])
        away = _canonical_team(row["AwayTeam"])
        if home == away:
            raise ValueError("current-season fixture has identical canonical teams")
        identities.append((row["_parsed_date"].isoformat(), home, away))
    if len(identities) != len(set(identities)):
        raise ValueError("current-season source has duplicate fixture identities")
    completed["Date"] = completed["_parsed_date"].map(
        lambda value: value.strftime("%d/%m/%Y")
    )
    result = completed.loc[:, list(REQUIRED_COLUMNS)].copy()
    return result, len(frame) - len(completed)


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
    at = _require_aware_utc(now, label="source capture clock")
    gate_count = read_completed_primary_event_count(client, now=at)
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
    response = get(CURRENT_URL, timeout=30)
    response.raise_for_status()
    raw = response.content
    observed_at = _require_aware_utc(
        clock(), label="current-season source observation clock"
    )
    current_rows, excluded_rows = validate_current_season_csv(raw, captured_at=observed_at)
    if len(current_rows) < MIN_COMPLETED_FEATURE_SOURCE_EVENTS:
        raise RuntimeError(
            "public current-season source has fewer completed prior-day matches than the feature-source gate"
        )
    archive_created_at = _validated_archive_created_at(observed_at, clock())
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
        "frozen_candidate_sha256": FROZEN_SHA,
        "original_feature_builder_git_blob_sha1": "401b3a0893371bfa4a488ec92a4a54af2678c8f7",
        "feature_count": len(FEATURE_SETS["ALL_FOOTBALL"]),
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
