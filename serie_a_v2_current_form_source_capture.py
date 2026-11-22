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
import re
from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import requests
from supabase import create_client

from historical_football_signal_lab import FEATURE_SETS
from market_anchor_1x2_v2_shadow import FIRST_OUTCOME_READ_GATE, outcome_read_permitted
from market_anchor_v2_direct_access import require_v2_source_capture_access
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
PROTOCOL_PATH = Path(__file__).resolve().parent / "experiments" / "market_anchor_1x2_v2_protocol.json"
PREREGISTERED_PROTOCOL_BLOB_SHA1 = "65729e9639720e67624c1481190aa22ae606f151"
MIN_COMPLETED_FEATURE_SOURCE_EVENTS = FIRST_OUTCOME_READ_GATE
MAX_CURRENT_CSV_BYTES = 2_000_000
REQUIRED_COLUMNS = (
    "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
    "HC", "AC", "HY", "AY", "HR", "AR",
)
NUMERIC_COLUMNS = ("FTHG", "FTAG", "HC", "AC", "HY", "AY", "HR", "AR")
V2_ONLY_ALIASES = {"Atalanta BC": "Atalanta"}

def _clock_utc(clock, *, field: str) -> datetime:
    """Require an explicit timezone before persisting source-provenance timestamps."""
    value = clock()
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must return a timezone-aware datetime")
    return value.astimezone(timezone.utc)


def _archive_creation_utc(clock, *, observed_at: datetime) -> datetime:
    """Do not write an archive timestamp that predates the source observation."""
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("source observation timestamp must be timezone-aware")
    observed = observed_at.astimezone(timezone.utc)
    created = _clock_utc(clock, field="source archive creation clock")
    if created < observed:
        raise ValueError("source archive creation clock precedes source observation")
    return created




def validate_preregistered_outcome_read_gate() -> dict[str, Any]:
    """Fail closed unless the exact frozen V2 protocol still declares the 30-event gate."""
    try:
        raw = PROTOCOL_PATH.read_bytes()
    except OSError as exc:
        raise RuntimeError("preregistered V2 outcome-read protocol is unavailable") from exc
    git_blob_header = b"blob " + str(len(raw)).encode("ascii") + bytes([0])
    git_blob = hashlib.sha1(git_blob_header + raw).hexdigest()
    if git_blob != PREREGISTERED_PROTOCOL_BLOB_SHA1:
        raise RuntimeError("preregistered V2 outcome-read protocol blob changed")
    try:
        protocol = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("preregistered V2 outcome-read protocol is malformed") from exc
    if not isinstance(protocol, dict):
        raise RuntimeError("preregistered V2 outcome-read protocol is malformed")
    gate = protocol.get("first_outcome_read_gate")
    cohort = protocol.get("primary_cohort")
    if (
        not isinstance(gate, dict)
        or not isinstance(cohort, dict)
        or gate.get("completed_primary_events") != FIRST_OUTCOME_READ_GATE
        or gate.get("outcome_read_before_gate") is not False
        or cohort.get("league") != "SERIE_A"
        or cohort.get("other_leagues_count_toward_gate") is not False
    ):
        raise RuntimeError("preregistered V2 outcome-read gate contract mismatch")
    return {
        "protocol_path": "experiments/market_anchor_1x2_v2_protocol.json",
        "protocol_blob_sha1": git_blob,
        "required_completed_primary_events": FIRST_OUTCOME_READ_GATE,
        "primary_league": "SERIE_A",
    }


def _canonical_team(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("completed primary event has an empty team identity")
    value = value.strip()
    known = SERIE_A_RUNTIME_CONFIG.aliases.get(value, value)
    return V2_ONLY_ALIASES.get(known, known)


def _canonical_fixture_identity_sha256(
    identities: set[tuple[str, str, str]] | list[tuple[str, str, str]]
) -> str:
    payload = json.dumps(
        sorted(identities), ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(
        b"SERIE_A_V2_CANONICAL_FIXTURE_IDENTITIES_V1\0" + payload
    ).hexdigest()


def summarize_completed_primary_events(
    rows: list[Mapping[str, Any]], *, before_date: date
) -> dict[str, Any]:
    """Audit raw and canonical fixture identities using metadata fields only."""
    raw_unique: set[tuple[str, str, str]] = set()
    canonical_unique: set[tuple[str, str, str]] = set()
    raw_variants_by_canonical: dict[
        tuple[str, str, str], set[tuple[str, str]]
    ] = {}
    orientation_by_unordered_pair: dict[tuple[str, str, str], tuple[str, str]] = {}
    eligible_rows = 0

    for row in rows:
        match_date = row.get("match_date")
        if isinstance(match_date, datetime):
            raise ValueError("primary event date must be date-only, not a timestamp")
        if isinstance(match_date, date):
            parsed_date = match_date
        elif isinstance(match_date, str):
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", match_date) is None:
                raise ValueError("primary event date must be canonical YYYY-MM-DD")
            try:
                parsed_date = date.fromisoformat(match_date)
            except ValueError as exc:
                raise ValueError("invalid primary event date in gate metadata") from exc
        else:
            raise ValueError("missing primary event date in gate metadata")

        if parsed_date >= before_date:
            continue
        raw_home_value = row.get("home_team")
        raw_away_value = row.get("away_team")
        if not isinstance(raw_home_value, str) or not raw_home_value.strip():
            raise ValueError("completed primary event has an empty team identity")
        if not isinstance(raw_away_value, str) or not raw_away_value.strip():
            raise ValueError("completed primary event has an empty team identity")
        raw_home, raw_away = raw_home_value.strip(), raw_away_value.strip()
        home, away = _canonical_team(raw_home), _canonical_team(raw_away)
        if home == away:
            raise ValueError("invalid primary event identity in gate metadata")

        date_key = parsed_date.isoformat()
        unordered_key = (date_key, *sorted((home, away)))
        previous_orientation = orientation_by_unordered_pair.get(unordered_key)
        if previous_orientation is not None and previous_orientation != (home, away):
            raise ValueError("reversed duplicate primary event identity in gate metadata")
        orientation_by_unordered_pair[unordered_key] = (home, away)

        raw_unique.add((date_key, raw_home, raw_away))
        canonical_key = (date_key, home, away)
        canonical_unique.add(canonical_key)
        raw_variants_by_canonical.setdefault(canonical_key, set()).add((raw_home, raw_away))
        eligible_rows += 1

    alias_collision_examples = []
    for (match_date, home, away), variants in sorted(raw_variants_by_canonical.items()):
        if len(variants) > 1:
            alias_collision_examples.append({
                "match_date": match_date,
                "canonical_home_team": home,
                "canonical_away_team": away,
                "raw_team_identity_variants": [
                    {"home_team": raw_home, "away_team": raw_away}
                    for raw_home, raw_away in sorted(variants)
                ],
            })

    raw_unique_count = len(raw_unique)
    canonical_unique_count = len(canonical_unique)
    return {
        "raw_metadata_rows": len(rows),
        "eligible_metadata_rows_before_cutoff": eligible_rows,
        "metadata_rows_on_or_after_cutoff": len(rows) - eligible_rows,
        "raw_unique_fixture_identities": raw_unique_count,
        "canonical_unique_fixture_identities": canonical_unique_count,
        "canonical_fixture_identity_sha256": _canonical_fixture_identity_sha256(canonical_unique),
        "exact_duplicate_metadata_rows": eligible_rows - raw_unique_count,
        "alias_collapsed_duplicate_identities": raw_unique_count - canonical_unique_count,
        "alias_collision_count": len(alias_collision_examples),
        "alias_collision_examples": alias_collision_examples[:20],
    }


def count_unique_completed_primary_events(
    rows: list[Mapping[str, Any]], *, before_date: date
) -> int:
    """Count canonical fixture identities only; never inspect score/result fields."""
    return summarize_completed_primary_events(
        rows, before_date=before_date
    )["canonical_unique_fixture_identities"]


def _read_completed_primary_event_summary(
    client: Any, *, now: datetime
) -> dict[str, Any]:
    """Read and hash only fixture date/team metadata; never read score/result fields."""
    if now.tzinfo is None or now.utcoffset() is None:
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
    return summarize_completed_primary_events(
        rows, before_date=now.astimezone(timezone.utc).date()
    )


def _read_completed_primary_event_count(client: Any, *, now: datetime) -> int:
    """Compatibility wrapper returning the canonical completed-event count."""
    return _read_completed_primary_event_summary(
        client, now=now
    )["canonical_unique_fixture_identities"]


def read_completed_primary_event_count(client: Any, *, now: datetime) -> int:
    """Read only fixture metadata after explicit source-capture rights and private storage checks."""
    require_v2_source_capture_access()
    return _read_completed_primary_event_count(client, now=now)


def validate_current_season_csv(raw: bytes, *, captured_at: datetime) -> tuple[pd.DataFrame, int]:
    """Return only completed, fully observed rows strictly before capture day.

    Football-Data is date-only. Same-day results are excluded because no reliable
    kickoff clock is available. Unplayed future rows may exist in the CSV but
    are never converted to features. The returned frame contains no incomplete
    fixtures and exactly the original V2 builder's required columns.
    """
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
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


def summarize_current_season_csv_identities(frame: pd.DataFrame) -> dict[str, Any]:
    """Hash canonical date/home/away identities only; never inspect score/stat columns."""
    required = {"Date", "HomeTeam", "AwayTeam"}
    if not required.issubset(frame.columns):
        raise ValueError("current-season identity frame lacks required fixture metadata")

    identities: set[tuple[str, str, str]] = set()
    orientation_by_unordered_pair: dict[tuple[str, str, str], tuple[str, str, str]] = {}
    for row in frame.loc[:, ["Date", "HomeTeam", "AwayTeam"]].itertuples(index=False):
        try:
            parsed_date = pd.to_datetime(
                row.Date, format="%d/%m/%Y", errors="raise"
            ).date()
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "current-season identity date is not canonical date-only CSV"
            ) from exc
        home = _canonical_team(row.HomeTeam)
        away = _canonical_team(row.AwayTeam)
        if home == away:
            raise ValueError("current-season identity has identical canonical teams")
        identity = (parsed_date.isoformat(), home, away)
        unordered = (identity[0], *sorted((home, away)))
        previous = orientation_by_unordered_pair.get(unordered)
        if previous is not None and previous != identity:
            raise ValueError("current-season identity has reversed duplicate fixture")
        orientation_by_unordered_pair[unordered] = identity
        identities.add(identity)

    if len(identities) != len(frame):
        raise ValueError("current-season identity frame contains duplicate fixture identities")
    return {
        "canonical_unique_fixture_identities": len(identities),
        "canonical_fixture_identity_sha256": _canonical_fixture_identity_sha256(identities),
        "identity_columns_read": ["Date", "HomeTeam", "AwayTeam"],
    }


def validate_current_season_identity_match(
    metadata_summary: Mapping[str, Any], current_rows: pd.DataFrame
) -> dict[str, Any]:
    """Require exact set equality between Supabase metadata and source CSV fixture identities."""
    source_summary = summarize_current_season_csv_identities(current_rows)
    metadata_count = metadata_summary.get("canonical_unique_fixture_identities")
    metadata_sha256 = metadata_summary.get("canonical_fixture_identity_sha256")
    if (
        type(metadata_count) is not int
        or not isinstance(metadata_sha256, str)
        or source_summary["canonical_unique_fixture_identities"] != metadata_count
        or source_summary["canonical_fixture_identity_sha256"] != metadata_sha256
    ):
        raise RuntimeError(
            "current-season CSV fixture identities do not exactly match Supabase metadata-only gate"
        )
    return {
        "metadata_canonical_fixture_identities": metadata_count,
        "source_canonical_fixture_identities": source_summary["canonical_unique_fixture_identities"],
        "metadata_identity_sha256": metadata_sha256,
        "source_identity_sha256": source_summary["canonical_fixture_identity_sha256"],
        "exact_identity_match": True,
        "identity_columns_compared": ["match_date/home_team/away_team", "Date/HomeTeam/AwayTeam"],
    }


def _capture_source_archive(
    *,
    output_dir: Path,
    client: Any,
    now: datetime,
    access: Mapping[str, Any],
    get=requests.get,
    history_fetch=fetch_public_history,
    clock=lambda: datetime.now(timezone.utc),
) -> dict:
    """Internal capture after source rights and private storage have been verified."""
    at = _clock_utc(lambda: now, field="source capture clock")
    preregistered_gate = validate_preregistered_outcome_read_gate()
    gate_identity_audit = _read_completed_primary_event_summary(client, now=at)
    gate_count = gate_identity_audit["canonical_unique_fixture_identities"]
    if not outcome_read_permitted(gate_count):
        raise RuntimeError(
            "current-form feature-source gate closed by preregistered V2 outcome-read gate: "
            f"{gate_count} completed primary events < {FIRST_OUTCOME_READ_GATE}; "
            "no current-season source request was made"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    old_history, old_audit = history_fetch(get=get, capture_dir=output_dir)
    if old_history.empty or len(old_audit) != len(_source_codes()):
        raise ValueError("original frozen historical source archive incomplete")
    response = get(CURRENT_URL, timeout=30, allow_redirects=False)
    response.raise_for_status()
    if response.status_code != 200:
        raise RuntimeError("current-season source requires HTTP 200 without redirects")
    if getattr(response, "url", None) != CURRENT_URL:
        raise ValueError("current-season source response URL differs from configured URL")
    raw = response.content
    observed_at = _clock_utc(clock, field="current-season source observation clock")
    current_rows, excluded_rows = validate_current_season_csv(raw, captured_at=observed_at)
    current_identity_audit = validate_current_season_identity_match(
        gate_identity_audit, current_rows
    )
    if len(current_rows) < MIN_COMPLETED_FEATURE_SOURCE_EVENTS:
        raise RuntimeError(
            "public current-season source has fewer completed prior-day matches than the feature-source gate"
        )
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
    archive_created_at = _archive_creation_utc(clock, observed_at=observed_at)
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
        "current_season_identity_audit": current_identity_audit,
        "current_season_total_csv_rows": audits[-1]["total_source_rows"],
        "current_season_excluded_incomplete_or_same_day_rows": excluded_rows,
        "preregistered_outcome_read_gate": {
            **preregistered_gate,
            "observed_completed_primary_events": gate_count,
            "checked_at_utc": at.isoformat(),
            "metadata_fields_read": ["match_date", "home_team", "away_team"],
            "score_or_result_fields_selected_for_gate": False,
            "identity_audit": gate_identity_audit,
            "passed": outcome_read_permitted(gate_count),
        },
        "source_capture_access": {
            "scope": access["access_scope"],
            "provider": access["rights"]["provider"],
            "provider_rights_status": access["rights"]["scope_status"],
            "rights_manifest_sha256": access["rights"]["rights_manifest_sha256"],
            "authorization_evidence_sha256": access["rights"]["authorization_evidence_sha256"],
            "artifact_repository": access["artifact_privacy"]["repository"],
            "artifact_repository_private": access["artifact_privacy"]["private"],
            "artifact_storage_policy": access["artifact_privacy"]["storage_policy"],
        },
        "feature_source_gate": {
            "type": "CURRENT_FORM_FEATURE_INPUT_ONLY",
            "primary_league": "SERIE_A",
            "season": CURRENT_SEASON,
            "minimum_completed_primary_events": FIRST_OUTCOME_READ_GATE,
            "observed_completed_primary_events": gate_count,
            "checked_at_utc": at.isoformat(),
            "metadata_fields_read": ["match_date", "home_team", "away_team"],
            "score_or_result_fields_selected_for_gate": False,
            "identity_audit": gate_identity_audit,
            "source_identity_audit": current_identity_audit,
            "uses_exact_preregistered_outcome_read_gate": True,
            "protocol_blob_sha1": preregistered_gate["protocol_blob_sha1"],
            "passed": outcome_read_permitted(gate_count),
        },
        "feature_policy": {
            "use_current_season_matches_only_as_lagged_features": True,
            "completed_current_season_match_results_read_for_lagged_features": True,
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
        "current_season_completed_match_results_read_for_lagged_features": True,
        "target_outcomes_read_for_evaluation": False,
        "target_outcomes_read_scope": (
            "legacy target_outcomes_read means evaluation targets only; completed prior "
            "2026/27 matches are separately read as lagged feature sources after the "
            "preregistered 30-primary-event gate"
        ),
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


def capture_source_archive(
    *,
    output_dir: Path,
    client: Any,
    now: datetime,
    get=requests.get,
    history_fetch=fetch_public_history,
    clock=lambda: datetime.now(timezone.utc),
) -> dict:
    """Capture only after provider source rights and private artifact storage are verified."""
    access = require_v2_source_capture_access()
    return _capture_source_archive(
        output_dir=output_dir,
        client=client,
        now=now,
        access=access,
        get=get,
        history_fetch=history_fetch,
        clock=clock,
    )


def main() -> None:
    access = require_v2_source_capture_access()
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
    report = _capture_source_archive(
        output_dir=args.output_dir,
        client=client,
        now=datetime.now(timezone.utc),
        access=access,
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
