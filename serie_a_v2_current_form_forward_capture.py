"""Forward-only V2 current-form shadow capture from authenticated source artifacts.

Only saved odds snapshots are read. Source archives and their successful main
workflow runs must both predate each quote. Current-season results are used
strictly as lagged features; target outcomes are never read or scored here.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping
import zipfile

import pandas as pd
import requests
from supabase import create_client

from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from serie_a_v2_asof_feature_manifest import build_manifest
from serie_a_v2_current_form_source_capture import (
    CURRENT_CODE, CURRENT_FILENAME, CURRENT_SEASON, CURRENT_URL,
    MANIFEST_FILENAME, MIN_COMPLETED_FEATURE_SOURCE_EVENTS,
    REQUIRED_COLUMNS, _canonical_team, validate_current_season_csv,
)
from serie_a_v2_frozen_shadow_preview import (
    FROZEN_SHA, fetch_saved_upcoming_serie_a_quotes, parse_utc, shadow_preview, _guard_outcome_free,
)
from serie_a_v2_live_diagnostic_report import PUBLIC_BASE, _source_codes
from serie_a_v2_prequote_source_archive_gate import MAX_ZIP_BYTES

REPOSITORY = "MaksimBlud/football-ai"
GITHUB_API = f"https://api.github.com/repos/{REPOSITORY}"
ARTIFACT_NAME = "serie-a-v2-current-form-source-capture"
SOURCE_WORKFLOW_PATH = ".github/workflows/serie-a-v2-current-form-source-capture.yml"
SCHEMA_VERSION = "SERIE_A_V2_CURRENT_FORM_FORWARD_CAPTURE_V1_1"
SOURCE_MANIFEST_V1 = "SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1"
SOURCE_MANIFEST_V1_1 = "SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1_1"
CURRENT_FORM_POLICY_REVISION = "1.1"
MAX_QUOTE_AGE = timedelta(hours=24)
MAX_SOURCE_AGE = timedelta(hours=24)
MAX_ARCHIVE_BYTES = 16_000_000
OLD_CUTOFF = pd.Timestamp("2026-07-01")


def _github_json(url: str, *, token: str, get=requests.get) -> dict:
    if not token:
        raise ValueError("GitHub Actions actions:read token missing")
    if not url.startswith(GITHUB_API + "/"):
        raise ValueError("external GitHub repository URL forbidden")
    response = get(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }, timeout=30)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("unexpected GitHub API response")
    return data


def discover_archives(*, token: str, get=requests.get) -> list[dict]:
    out, seen_ids = [], set()
    for page in range(1, 4):
        data = _github_json(
            f"{GITHUB_API}/actions/artifacts?name={ARTIFACT_NAME}&per_page=100&page={page}",
            token=token, get=get,
        )
        items = data.get("artifacts")
        if not isinstance(items, list):
            raise ValueError("GitHub artifact response lacks artifact list")
        for item in items:
            if not isinstance(item, dict) or item.get("name") != ARTIFACT_NAME or item.get("expired") is True:
                continue
            run = item.get("workflow_run")
            if not isinstance(run, dict) or run.get("head_branch") != "main":
                continue
            run_id, head_sha, artifact_id = run.get("id"), run.get("head_sha"), item.get("id")
            digest = item.get("digest")
            if (type(run_id) is not int or run_id <= 0
                    or not isinstance(head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", head_sha)
                    or type(artifact_id) is not int or artifact_id <= 0 or artifact_id in seen_ids
                    or not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest)):
                raise ValueError("malformed current-form source artifact metadata")
            seen_ids.add(artifact_id)
            out.append({
                "artifact_id": artifact_id,
                "run_id": run_id,
                "head_sha": head_sha,
                "created_at": parse_utc(item["created_at"]),
                "sha256": digest.removeprefix("sha256:"),
            })
        if len(items) < 100:
            break
    return sorted(out, key=lambda item: (item["created_at"], item["artifact_id"]), reverse=True)


def verify_source_run(
    archive: Mapping[str, Any], *, quote_time: datetime, token: str, get=requests.get
) -> dict:
    run_id = archive.get("run_id")
    if type(run_id) is not int or run_id <= 0:
        raise ValueError("source artifact lacks parent workflow run")
    run = _github_json(f"{GITHUB_API}/actions/runs/{run_id}", token=token, get=get)
    if (run.get("id") != run_id
            or run.get("path") != SOURCE_WORKFLOW_PATH
            or run.get("head_branch") != "main"
            or run.get("head_sha") != archive.get("head_sha")
            or run.get("status") != "completed"
            or run.get("conclusion") != "success"
            or run.get("event") not in ("push", "schedule", "workflow_dispatch")):
        raise ValueError("artifact parent is not a successful main current-form source run")
    created = parse_utc(run["created_at"])
    completed = parse_utc(run["updated_at"])
    if not (created <= archive["created_at"] <= completed < quote_time):
        raise ValueError("source workflow/artifact did not finish strictly before quote")
    return {
        "run_id": run_id,
        "run_head_sha": archive["head_sha"],
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "run_created_at_utc": created.isoformat(),
        "run_completed_at_utc": completed.isoformat(),
    }


def get_archive(artifact_id: int, *, token: str, get=requests.get) -> bytes:
    if type(artifact_id) is not int or artifact_id <= 0:
        raise ValueError("invalid source artifact id")
    response = get(
        f"{GITHUB_API}/actions/artifacts/{artifact_id}/zip",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=90,
    )
    response.raise_for_status()
    raw = response.content
    if not raw or len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("current-form source archive is empty or too large")
    return raw


def verify_and_load_archive(
    raw: bytes, archive: Mapping[str, Any], parent: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict]:
    if not raw or len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("current-form source archive is empty or too large")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != archive.get("sha256"):
        raise ValueError("GitHub current-form artifact SHA256 mismatch")
    with zipfile.ZipFile(BytesIO(raw), "r") as z:
        old_names = {f"serie_a_{code}.csv" for code in _source_codes()}
        expected = old_names | {CURRENT_FILENAME, MANIFEST_FILENAME}
        names = z.namelist()
        if len(names) != len(expected) or set(names) != expected:
            raise ValueError("current-form archive has unexpected/missing files")
        manifest = json.loads(z.read(MANIFEST_FILENAME))
        manifest_schema = manifest.get("schema_version")
        if (manifest_schema not in (SOURCE_MANIFEST_V1, SOURCE_MANIFEST_V1_1)
                or manifest.get("experiment_id") != "MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY"
                or manifest.get("workflow_path") != SOURCE_WORKFLOW_PATH
                or manifest.get("git_sha") != archive.get("head_sha")
                or str(manifest.get("workflow_run_id")) != str(archive.get("run_id"))
                or manifest.get("frozen_candidate_sha256") != FROZEN_SHA
                or manifest.get("current_season_code") != CURRENT_CODE
                or manifest.get("current_season") != CURRENT_SEASON
                or manifest.get("current_season_source_url") != CURRENT_URL
                or manifest.get("historical_season_codes") != list(_source_codes())
                or manifest.get("feature_count") != 19
                or manifest.get("source_file_count") != 11
                or manifest.get("historical_old_season_file_count") != 10):
            raise ValueError("current-form source manifest violates frozen candidate/season contract")
        policy_revision = manifest.get("policy_revision", "1.0_LEGACY")
        if ((manifest_schema == SOURCE_MANIFEST_V1_1 and policy_revision != CURRENT_FORM_POLICY_REVISION)
                or (manifest_schema == SOURCE_MANIFEST_V1 and policy_revision not in (None, "1.0", "1.0_LEGACY"))):
            raise ValueError("current-form source policy revision is inconsistent with its schema")
        if (manifest.get("original_feature_builder_git_blob_sha1") != "401b3a0893371bfa4a488ec92a4a54af2678c8f7"):
            raise ValueError("current-form source manifest does not pin the original feature builder")
        gate = manifest.get("feature_source_gate")
        if (not isinstance(gate, dict)
                or gate.get("type") != "CURRENT_FORM_FEATURE_INPUT_ONLY"
                or gate.get("primary_league") != "SERIE_A"
                or gate.get("season") != CURRENT_SEASON
                or gate.get("minimum_completed_primary_events") != MIN_COMPLETED_FEATURE_SOURCE_EVENTS
                or not isinstance(gate.get("observed_completed_primary_events"), int)
                or gate["observed_completed_primary_events"] < MIN_COMPLETED_FEATURE_SOURCE_EVENTS
                or gate.get("score_or_result_fields_selected_for_gate") is not False
                or gate.get("passed") is not True):
            raise ValueError("current-form feature input gate is not authenticated/open")
        evaluation_gate = manifest.get("target_outcome_evaluation_gate")
        if (not isinstance(evaluation_gate, dict)
                or evaluation_gate.get("minimum_completed_eligible_prospective_forecasts") != 30
                or evaluation_gate.get("outcomes_read_for_evaluation") is not False
                or evaluation_gate.get("outcome_gate_open") is not False):
            raise ValueError("target outcome evaluation gate unexpectedly opened or changed")
        if (manifest.get("target_outcomes_read") is not False
                or manifest.get("target_outcomes_scored") is not False
                or manifest.get("model_refit_or_promotion") is not False
                or manifest.get("paid_provider_calls") != 0
                or manifest.get("supabase_writes") != 0):
            raise ValueError("current-form source manifest violates no-score/no-write contract")
        source_files = manifest.get("source_files")
        if not isinstance(source_files, list) or len(source_files) != 11:
            raise ValueError("current-form source file audit is incomplete")
        by_code = {item.get("season_code"): item for item in source_files if isinstance(item, dict)}
        expected_codes = list(_source_codes()) + [CURRENT_CODE]
        if len(by_code) != 11 or set(by_code) != set(expected_codes):
            raise ValueError("current-form source audit has duplicate or unexpected seasons")
        source_times = []
        old_frames = []
        for code in _source_codes():
            item = by_code[code]
            filename = f"serie_a_{code}.csv"
            expected_url = f"{PUBLIC_BASE}/{code}/{SERIE_A_RUNTIME_CONFIG.historical_source.competition_code}.csv"
            if (item.get("archived_source_name") != filename
                    or item.get("source_url") != expected_url):
                raise ValueError("unexpected frozen historical source URL/file")
            body = z.read(filename)
            if hashlib.sha256(body).hexdigest() != item.get("csv_sha256"):
                raise ValueError("frozen historical source CSV hash mismatch")
            observed = parse_utc(item["source_observed_at_utc"])
            if observed > archive["created_at"]:
                raise ValueError("historical source was observed after artifact upload")
            source_times.append(observed)
            frame = pd.read_csv(BytesIO(body), low_memory=False)
            if not set(REQUIRED_COLUMNS).issubset(frame.columns):
                raise ValueError("frozen historical source lacks original V2 statistics")
            if len(frame) != item.get("completed_source_rows"):
                raise ValueError("frozen historical source row count mismatch")
            dates = pd.to_datetime(frame["Date"], dayfirst=True, format="mixed", errors="raise")
            if (dates >= OLD_CUTOFF).any():
                raise ValueError("old-season archive contains protected-season rows")
            old_frames.append(frame.loc[:, list(REQUIRED_COLUMNS)].copy())
        current_item = by_code[CURRENT_CODE]
        if (current_item.get("archived_source_name") != CURRENT_FILENAME
                or current_item.get("source_url") != CURRENT_URL
                or current_item.get("csv_sha256") != manifest.get("current_season_source_sha256")
                or current_item.get("source_observed_at_utc") != manifest.get("current_season_source_observed_at_utc")):
            raise ValueError("current-season source audit mismatch")
        current_raw = z.read(CURRENT_FILENAME)
        if hashlib.sha256(current_raw).hexdigest() != current_item.get("csv_sha256"):
            raise ValueError("current-season source CSV hash mismatch")
        current_observed = parse_utc(current_item["source_observed_at_utc"])
        if current_observed > archive["created_at"]:
            raise ValueError("current-season source observed after artifact upload")
        current_frame, _excluded = validate_current_season_csv(
            current_raw, captured_at=current_observed
        )
        if (len(current_frame) != manifest.get("current_season_completed_prior_day_rows")
                or current_item.get("completed_source_rows") != len(current_frame)):
            raise ValueError("current-season completed row count mismatch")
        current_dates = pd.to_datetime(current_frame["Date"], dayfirst=True, format="mixed", errors="raise")
        if current_dates.empty or (current_dates < OLD_CUTOFF).any():
            raise ValueError("current-season archive contains pre-2026/27 rows or no usable rows")
        latest_match_date = current_dates.max().date()
        days_since_latest_match = (current_observed.date() - latest_match_date).days
        if days_since_latest_match < 0:
            raise ValueError("current-season latest match date is after source observation")
        if manifest_schema == SOURCE_MANIFEST_V1_1 and (
            manifest.get("current_season_latest_match_date") != latest_match_date.isoformat()
            or manifest.get("current_season_days_since_latest_match_at_capture") != days_since_latest_match
            or manifest.get("policy_path") != "experiments/market_anchor_1x2_v2_current_form_policy_v1_1.json"
        ):
            raise ValueError("current-form source latest-match date or policy revision does not match CSV")
        if manifest_schema == SOURCE_MANIFEST_V1 and (
            manifest.get("current_season_latest_match_date") is not None
            or manifest.get("current_season_days_since_latest_match_at_capture") is not None
        ):
            raise ValueError("legacy source manifest unexpectedly contains V1.1-only fields")
        current_fixture_keys = []
        for (_, row), match_day in zip(current_frame.iterrows(), current_dates):
            current_fixture_keys.append((
                match_day.date().isoformat(),
                _canonical_team(row["HomeTeam"]),
                _canonical_team(row["AwayTeam"]),
            ))
        source_times.append(current_observed)
        history = pd.concat(old_frames + [current_frame], ignore_index=True)
        latest_source = max(source_times)
        declared_latest = parse_utc(manifest["current_season_source_observed_at_utc"])
        declared_archive = parse_utc(manifest["source_archive_created_at_utc"])
        if latest_source != declared_latest or declared_archive < latest_source:
            raise ValueError("source observation and archive timestamps conflict")
        if declared_archive > archive["created_at"] or archive["created_at"] > parse_utc(parent["run_completed_at_utc"]):
            raise ValueError("source archive artifact timing conflicts with parent run")
        return history, {
            "manifest": manifest,
            "artifact_sha256": digest,
            "latest_source_observed_at_utc": latest_source.isoformat(),
            "archive_created_at_utc": archive["created_at"].isoformat(),
            "parent_run": dict(parent),
            "historical_match_rows": len(history),
            "current_season_history_rows": len(current_frame),
            "current_season_latest_match_date": latest_match_date.isoformat(),
            "current_season_days_since_latest_match_at_capture": days_since_latest_match,
            "current_season_fixture_keys": current_fixture_keys,
            "policy_revision": policy_revision,
            "source_manifest_schema": manifest_schema,
        }


def fetch_saved_serie_a_fixture_metadata(client: Any) -> list[dict]:
    """Read saved fixture identity/timing only; never odds prices or result fields."""
    response = (
        client.table("odds_snapshots")
        .select("event_id,league,home_team,away_team,commence_time_utc,snapshot_time_utc")
        .eq("league", "SERIE_A")
        .gte("commence_time_utc", "2026-07-01T00:00:00+00:00")
        .order("snapshot_time_utc", desc=True)
        .limit(1000)
        .execute()
    )
    rows = response.data or []
    if not isinstance(rows, list):
        raise ValueError("saved Serie A fixture metadata response is malformed")
    if len(rows) >= 1000:
        raise ValueError("saved Serie A fixture metadata exceeds safe completeness-check bound")
    return rows


def _latest_fixture_metadata(rows: list[dict], *, as_of_utc: datetime) -> list[dict]:
    latest: dict[str, dict] = {}
    latest_snapshot: dict[str, datetime] = {}
    for row in rows:
        _guard_outcome_free(row)
        if row.get("league") != "SERIE_A":
            raise ValueError("fixture metadata query returned a non-Serie A event")
        event_id = row.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("fixture metadata has no event_id")
        home, away = _canonical_team(row.get("home_team")), _canonical_team(row.get("away_team"))
        if home == away:
            raise ValueError("fixture metadata has identical canonical teams")
        kickoff = parse_utc(row["commence_time_utc"])
        snapshot = parse_utc(row["snapshot_time_utc"])
        if snapshot > as_of_utc:
            raise ValueError("fixture metadata contains a snapshot from the future")
        old = latest.get(event_id)
        if old is not None and (
            old["canonical_home_team"] != home or old["canonical_away_team"] != away
        ):
            raise ValueError("one event_id maps to conflicting canonical team identities")
        if event_id not in latest or snapshot > latest_snapshot[event_id]:
            latest[event_id] = {
                **row,
                "canonical_home_team": home,
                "canonical_away_team": away,
                "parsed_kickoff_utc": kickoff,
                "parsed_snapshot_utc": snapshot,
            }
            latest_snapshot[event_id] = snapshot
    return list(latest.values())


def assess_source_schedule_completeness(
    source_meta: Mapping[str, Any],
    fixture_metadata: list[dict] | None,
    *,
    as_of_utc: datetime,
) -> dict:
    """Fail closed if known prior-day scheduled fixtures are absent from current-form CSV."""
    if as_of_utc.tzinfo is None:
        raise ValueError("schedule completeness clock must be timezone-aware")
    source_time = parse_utc(source_meta["latest_source_observed_at_utc"])
    base = {
        "metadata_available": bool(fixture_metadata),
        "source_observed_at_utc": source_time.isoformat(),
        "source_latest_match_date": source_meta["current_season_latest_match_date"],
        "checked_at_utc": as_of_utc.astimezone(timezone.utc).isoformat(),
        "checked_prior_day_fixture_count": 0,
        "gap_count": 0,
        "gaps": [],
    }
    if not fixture_metadata:
        return {**base, "complete": False, "status": "SCHEDULE_METADATA_UNAVAILABLE"}
    rows = _latest_fixture_metadata(fixture_metadata, as_of_utc=as_of_utc.astimezone(timezone.utc))
    current_keys = {tuple(key) for key in source_meta.get("current_season_fixture_keys", [])}
    gaps = []
    checked = set()
    for row in rows:
        kickoff = row["parsed_kickoff_utc"]
        # Date-only source: same-calendar-day matches are deliberately excluded.
        if kickoff.date() < date(2026, 7, 1) or kickoff.date() >= source_time.date():
            continue
        key = (
            kickoff.date().isoformat(),
            row["canonical_home_team"],
            row["canonical_away_team"],
        )
        if key in checked:
            continue
        checked.add(key)
        if key not in current_keys:
            gaps.append({
                "event_id": row["event_id"],
                "home_team": row["home_team"],
                "away_team": row["away_team"],
                "canonical_home_team": row["canonical_home_team"],
                "canonical_away_team": row["canonical_away_team"],
                "kickoff_utc": kickoff.isoformat(),
                "missing_fixture_key": list(key),
            })
    gaps.sort(key=lambda item: (item["kickoff_utc"], item["event_id"]))
    return {
        **base,
        "metadata_available": True,
        "checked_prior_day_fixture_count": len(checked),
        "gap_count": len(gaps),
        "gaps": gaps,
        "complete": len(gaps) == 0,
        "status": "COMPLETE" if not gaps else "CURRENT_FORM_SOURCE_BEHIND_SCHEDULE",
    }


def verify_latest_source_archive(
    archive_metadata: list[dict],
    *,
    as_of_utc: datetime,
    load_archive,
    verify_parent_run,
    write_sources_to: Path | None = None,
    fixture_metadata: list[dict] | None = None,
) -> dict:
    """Verify the latest successful main source artifact even when all quotes are stale."""
    if as_of_utc.tzinfo is None:
        raise ValueError("source verification clock must be timezone-aware")
    now = as_of_utc.astimezone(timezone.utc)
    candidates = sorted(
        (item for item in archive_metadata if item["created_at"] < now),
        key=lambda item: (item["created_at"], item["artifact_id"]),
        reverse=True,
    )
    if not candidates:
        return {
            "status": "NO_SOURCE_ARCHIVE",
            "verified": False,
            "verified_at_utc": now.isoformat(),
            "target_outcomes_read": False,
            "target_outcomes_scored": False,
            "paid_provider_calls": 0,
            "supabase_writes": 0,
        }
    archive = candidates[0]
    parent = verify_parent_run(archive, quote_time=now)
    raw = load_archive(archive["artifact_id"])
    history, source_meta = verify_and_load_archive(raw, archive, parent)
    if write_sources_to is not None:
        write_sources_to.mkdir(parents=True, exist_ok=True)
        (write_sources_to / f"current-form-source-artifact-{archive['artifact_id']}.zip").write_bytes(raw)
    latest_source = parse_utc(source_meta["latest_source_observed_at_utc"])
    age_seconds = (now - latest_source).total_seconds()
    if age_seconds < 0:
        raise ValueError("source archive contains a source timestamp after verification time")
    manifest = source_meta["manifest"]
    schedule_check = assess_source_schedule_completeness(
        source_meta, fixture_metadata, as_of_utc=now
    )
    policy_current = source_meta["policy_revision"] == CURRENT_FORM_POLICY_REVISION
    source_age_fresh = age_seconds <= MAX_SOURCE_AGE.total_seconds()
    eligible = policy_current and source_age_fresh and schedule_check["complete"]
    if not schedule_check["metadata_available"]:
        status = "VERIFIED_SCHEDULE_METADATA_UNAVAILABLE"
    elif schedule_check["gap_count"]:
        status = "VERIFIED_WITH_SCHEDULE_GAPS"
    elif not policy_current:
        status = "VERIFIED_LEGACY_POLICY_NOT_ELIGIBLE"
    elif not source_age_fresh:
        status = "VERIFIED_SOURCE_CONTENT_TOO_OLD"
    else:
        status = "VERIFIED_FRESH"
    return {
        "status": status,
        "verified": True,
        "verified_at_utc": now.isoformat(),
        "artifact_id": archive["artifact_id"],
        "artifact_sha256": source_meta["artifact_sha256"],
        "source_archive_created_at_utc": source_meta["archive_created_at_utc"],
        "latest_source_observed_at_utc": source_meta["latest_source_observed_at_utc"],
        "source_age_seconds_at_verification": int(age_seconds),
        "fresh_for_new_quote": eligible,
        "eligible_for_new_quote": eligible,
        "policy_revision": source_meta["policy_revision"],
        "source_manifest_schema": source_meta["source_manifest_schema"],
        "current_season_latest_match_date": source_meta["current_season_latest_match_date"],
        "current_season_days_since_latest_match_at_capture": source_meta["current_season_days_since_latest_match_at_capture"],
        "source_schedule_completeness": schedule_check,
        "parent_run": source_meta["parent_run"],
        "feature_input_gate_count": manifest["feature_source_gate"]["observed_completed_primary_events"],
        "historical_old_season_file_count": manifest["historical_old_season_file_count"],
        "source_file_count": manifest["source_file_count"],
        "historical_match_rows": source_meta["historical_match_rows"],
        "current_season_history_rows": source_meta["current_season_history_rows"],
        "candidate_sha256": FROZEN_SHA,
        "target_outcomes_read": False,
        "target_outcomes_scored": False,
        "target_outcome_evaluation_gate_open": False,
        "paid_provider_calls": 0,
        "supabase_writes": 0,
        "no_bet": True,
    }


def _latest_quotes(quotes: list[dict], *, now: datetime) -> list[dict]:
    latest = {}
    seen = set()
    for q in quotes:
        _guard_outcome_free(q)
        if q.get("league") != "SERIE_A":
            raise ValueError("current-form forward capture accepts Serie A only")
        event = q.get("event_id")
        home, away = q.get("home_team"), q.get("away_team")
        if not all(isinstance(x, str) and x.strip() for x in (event, home, away)):
            raise ValueError("quote identity is incomplete")
        kickoff = parse_utc(q["commence_time_utc"])
        snapshot = parse_utc(q["snapshot_time_utc"])
        if snapshot > now or not snapshot < kickoff:
            raise ValueError("invalid current-form quote timing")
        identity = (event, home, away, kickoff)
        key = (*identity, snapshot)
        if key in seen:
            raise ValueError("duplicate exact current-form quote observation")
        seen.add(key)
        old = latest.get(identity)
        if old is None or snapshot > old[0]:
            latest[identity] = (snapshot, q)
    return [value[1] for value in latest.values()]


def prepare_forward_capture(
    quotes: list[dict],
    archive_metadata: list[dict],
    *,
    as_of_utc: datetime,
    load_archive,
    verify_parent_run,
    write_sources_to: Path | None = None,
    fixture_metadata: list[dict] | None = None,
) -> dict:
    if as_of_utc.tzinfo is None:
        raise ValueError("current-form forward clock must be timezone-aware")
    now = as_of_utc.astimezone(timezone.utc)
    if write_sources_to is not None:
        write_sources_to.mkdir(parents=True, exist_ok=True)
    latest_quotes = _latest_quotes(quotes, now=now)
    report_rows = []
    blocked = {
        "NO_EARLIER_SOURCE_ARCHIVE": 0,
        "SOURCE_PARENT_UNVERIFIED": 0,
        "SOURCE_ARCHIVE_TOO_OLD": 0,
        "STALE_MARKET_QUOTE": 0,
        "EXPIRED_FIXTURE": 0,
        "NO_FEATURES": 0,
        "ALL_FEATURES_MEDIAN_IMPUTED": 0,
        "CURRENT_FORM_SOURCE_BEHIND_SCHEDULE": 0,
        "SCHEDULE_METADATA_UNAVAILABLE": 0,
        "LEGACY_SOURCE_POLICY_NOT_ELIGIBLE": 0,
    }
    cache: dict[int, tuple[pd.DataFrame, dict]] = {}
    parent_cache: dict[tuple[int, datetime], dict] = {}
    used_sources = {}
    for quote in sorted(latest_quotes, key=lambda q: (parse_utc(q["commence_time_utc"]), q["event_id"])):
        quote_time = parse_utc(quote["snapshot_time_utc"])
        kickoff = parse_utc(quote["commence_time_utc"])
        base = {
            "event_id": quote["event_id"],
            "home_team": quote["home_team"],
            "away_team": quote["away_team"],
            "quote_time_utc": quote_time.isoformat(),
            "kickoff_utc": kickoff.isoformat(),
        }
        if not now < kickoff:
            blocked["EXPIRED_FIXTURE"] += 1
            report_rows.append({**base, "status": "EXPIRED_FIXTURE", "v2_preview": None})
            continue
        if now - quote_time > MAX_QUOTE_AGE:
            blocked["STALE_MARKET_QUOTE"] += 1
            report_rows.append({**base, "status": "STALE_MARKET_QUOTE", "v2_preview": None})
            continue
        selected = None
        parent = None
        source_error = None
        for archive in archive_metadata:
            if archive["created_at"] >= quote_time:
                continue
            key = (archive["artifact_id"], quote_time)
            try:
                parent = parent_cache.get(key)
                if parent is None:
                    parent = verify_parent_run(archive, quote_time=quote_time)
                    parent_cache[key] = parent
                selected = archive
                break
            except (ValueError, KeyError, TypeError) as exc:
                source_error = str(exc)
                continue
        if selected is None:
            if source_error:
                blocked["SOURCE_PARENT_UNVERIFIED"] += 1
                status = "SOURCE_PARENT_UNVERIFIED"
            else:
                blocked["NO_EARLIER_SOURCE_ARCHIVE"] += 1
                status = "NO_EARLIER_SOURCE_ARCHIVE"
            report_rows.append({**base, "status": status, "source_error": source_error, "v2_preview": None})
            continue
        artifact_id = selected["artifact_id"]
        if artifact_id not in cache:
            raw = load_archive(artifact_id)
            history, source_meta = verify_and_load_archive(raw, selected, parent)
            cache[artifact_id] = (history, source_meta)
            if write_sources_to is not None:
                path = write_sources_to / f"current-form-source-artifact-{artifact_id}.zip"
                path.write_bytes(raw)
            used_sources[str(artifact_id)] = {
                "artifact_id": artifact_id,
                "artifact_sha256": source_meta["artifact_sha256"],
                "source_archive_created_at_utc": source_meta["archive_created_at_utc"],
                "latest_source_observed_at_utc": source_meta["latest_source_observed_at_utc"],
                "parent_run": source_meta["parent_run"],
                "historical_match_rows": source_meta["historical_match_rows"],
                "current_season_history_rows": source_meta["current_season_history_rows"],
                "current_season_latest_match_date": source_meta["current_season_latest_match_date"],
                "current_season_days_since_latest_match_at_capture": source_meta["current_season_days_since_latest_match_at_capture"],
                "policy_revision": source_meta["policy_revision"],
            }
        history, source_meta = cache[artifact_id]
        schedule_check = assess_source_schedule_completeness(
            source_meta, fixture_metadata, as_of_utc=now
        )
        if not schedule_check["metadata_available"]:
            blocked["SCHEDULE_METADATA_UNAVAILABLE"] += 1
            report_rows.append({
                **base, "status": "SCHEDULE_METADATA_UNAVAILABLE",
                "source_artifact_id": artifact_id,
                "source_schedule_completeness": schedule_check,
                "v2_preview": None,
            })
            continue
        if schedule_check["gap_count"]:
            blocked["CURRENT_FORM_SOURCE_BEHIND_SCHEDULE"] += 1
            report_rows.append({
                **base, "status": "CURRENT_FORM_SOURCE_BEHIND_SCHEDULE",
                "source_artifact_id": artifact_id,
                "source_archive_sha256": source_meta["artifact_sha256"],
                "current_season_latest_match_date": source_meta["current_season_latest_match_date"],
                "current_season_days_since_latest_match_at_capture": source_meta["current_season_days_since_latest_match_at_capture"],
                "source_schedule_completeness": schedule_check,
                "v2_preview": None,
            })
            continue
        if source_meta["policy_revision"] != CURRENT_FORM_POLICY_REVISION:
            blocked["LEGACY_SOURCE_POLICY_NOT_ELIGIBLE"] += 1
            report_rows.append({
                **base, "status": "LEGACY_SOURCE_POLICY_NOT_ELIGIBLE",
                "source_artifact_id": artifact_id,
                "source_manifest_schema": source_meta["source_manifest_schema"],
                "source_policy_revision": source_meta["policy_revision"],
                "v2_preview": None,
            })
            continue
        source_time = parse_utc(source_meta["latest_source_observed_at_utc"])
        if source_time >= quote_time or quote_time - source_time > MAX_SOURCE_AGE:
            blocked["SOURCE_ARCHIVE_TOO_OLD"] += 1
            report_rows.append({
                **base, "status": "SOURCE_ARCHIVE_TOO_OLD",
                "source_artifact_id": artifact_id,
                "source_observed_at_utc": source_time.isoformat(),
                "v2_preview": None,
            })
            continue
        manifest = build_manifest(history, [quote])["feature_manifests"][0]
        feature = {
            "event_id": manifest["event_id"],
            "home_team": manifest["home_team"],
            "away_team": manifest["away_team"],
            "commence_time_utc": manifest["commence_time_utc"],
            "feature_history_cutoff_utc": source_time.isoformat(),
            "features": manifest["features"],
            "history_coverage": manifest["history_coverage"],
            "source_archive_sha256": source_meta["artifact_sha256"],
            "source_archive_created_at_utc": source_meta["archive_created_at_utc"],
            "source_observed_at_utc": source_meta["latest_source_observed_at_utc"],
        }
        preview_report = shadow_preview([quote], [feature], as_of_utc=now)
        if preview_report["scored"] != 1:
            reasons = preview_report["blocked"]
            if reasons.get("ALL_FEATURES_MEDIAN_IMPUTED", 0):
                blocked["ALL_FEATURES_MEDIAN_IMPUTED"] += 1
                status = "ALL_FEATURES_MEDIAN_IMPUTED"
            elif reasons.get("NO_FEATURES", 0):
                blocked["NO_FEATURES"] += 1
                status = "NO_FEATURES"
            elif reasons.get("STALE_MARKET", 0):
                blocked["STALE_MARKET_QUOTE"] += 1
                status = "STALE_MARKET_QUOTE"
            elif reasons.get("EXPIRED_FIXTURE", 0):
                blocked["EXPIRED_FIXTURE"] += 1
                status = "EXPIRED_FIXTURE"
            else:
                status = "V2_PREVIEW_BLOCKED"
            report_rows.append({
                **base, "status": status, "source_artifact_id": artifact_id,
                "v2_preview": None, "preview_blocked": reasons,
            })
            continue
        preview = preview_report["previews"][0]
        preview["shadow_evidence_status"] = "SOURCE_ARCHIVE_AND_PARENT_RUN_VERIFIED_BEFORE_QUOTE"
        preview["eligible_for_frozen_prospective_cohort"] = False
        preview["eligible_for_current_form_forward_shadow"] = True
        preview["eligible_for_product_publication"] = False
        preview["no_bet"] = True
        report_rows.append({
            **base,
            "status": "CURRENT_FORM_V2_SHADOW_CAPTURED_PREKICKOFF",
            "source_artifact_id": artifact_id,
            "source_artifact_sha256": source_meta["artifact_sha256"],
            "source_archive_created_at_utc": source_meta["archive_created_at_utc"],
            "source_observed_at_utc": source_meta["latest_source_observed_at_utc"],
            "source_age_at_quote_seconds": int((quote_time - source_time).total_seconds()),
            "current_season_latest_match_date": source_meta["current_season_latest_match_date"],
            "current_season_days_since_latest_match_at_capture": source_meta["current_season_days_since_latest_match_at_capture"],
            "source_schedule_completeness": schedule_check,
            "historical_match_rows": source_meta["historical_match_rows"],
            "current_season_history_rows": source_meta["current_season_history_rows"],
            "observed_frozen_feature_count": preview["observed_frozen_feature_count"],
            "median_imputed_frozen_feature_count": preview["median_imputed_frozen_feature_count"],
            "v2_preview": preview,
        })
    scored = sum(row["status"] == "CURRENT_FORM_V2_SHADOW_CAPTURED_PREKICKOFF" for row in report_rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "experiment_id": "MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY",
        "mode": "READ_ONLY_PREKICKOFF_SHADOW_NO_BET",
        "candidate_sha256": FROZEN_SHA,
        "as_of_utc": now.isoformat(),
        "quotes_seen": len(latest_quotes),
        "fixture_metadata_rows_seen": len(fixture_metadata or []),
        "v2_current_form_shadow_captured": scored,
        "blocked": blocked,
        "rows": report_rows,
        "source_artifacts_used": list(used_sources.values()),
        "active_lambda": 0.0,
        "shadow_residual_lambda": 1.0,
        "active_model_is_exact_de_vigged_market": True,
        "target_outcomes_read": False,
        "target_outcomes_scored": False,
        "target_outcome_evaluation_gate_open": False,
        "model_refit_or_selection": False,
        "production_or_supabase_writes": 0,
        "paid_provider_calls": 0,
        "eligible_for_frozen_original_cohort": False,
        "eligible_for_current_form_forward_shadow": scored > 0,
        "eligible_for_product_publication": False,
        "no_bet": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sources-output-dir", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise RuntimeError("current-form forward capture must run in the original GitHub repository")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("current-form V2 source/forecast workflow must run from main")
    token = os.environ.get("GITHUB_TOKEN", "")
    url, key = os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_KEY", "")
    if not token or not url or not key:
        raise RuntimeError("GitHub actions:read and Supabase read-only credentials are required")
    now = datetime.now(timezone.utc)
    archives = discover_archives(token=token)
    raw_cache = {}

    def load_cached_archive(artifact_id: int) -> bytes:
        if artifact_id not in raw_cache:
            raw_cache[artifact_id] = get_archive(artifact_id, token=token)
        return raw_cache[artifact_id]

    def verify_parent(archive: Mapping[str, Any], *, quote_time: datetime) -> dict:
        return verify_source_run(archive, quote_time=quote_time, token=token)

    source_verification = verify_latest_source_archive(
        archives,
        as_of_utc=now,
        load_archive=load_cached_archive,
        verify_parent_run=verify_parent,
        write_sources_to=args.sources_output_dir,
    )
    client = create_client(url, key)
    quotes = fetch_saved_upcoming_serie_a_quotes(client, now=now)
    report = prepare_forward_capture(
        quotes,
        archives,
        as_of_utc=now,
        load_archive=load_cached_archive,
        verify_parent_run=verify_parent,
        write_sources_to=args.sources_output_dir,
    )
    report["latest_source_archive_verification"] = source_verification
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({
        "mode": report["mode"],
        "candidate_sha256": report["candidate_sha256"],
        "quotes_seen": report["quotes_seen"],
        "latest_source_archive_verification": report["latest_source_archive_verification"],
        "v2_current_form_shadow_captured": report["v2_current_form_shadow_captured"],
        "blocked": report["blocked"],
        "target_outcomes_read": report["target_outcomes_read"],
        "target_outcomes_scored": report["target_outcomes_scored"],
        "paid_provider_calls": report["paid_provider_calls"],
        "production_or_supabase_writes": report["production_or_supabase_writes"],
        "no_bet": report["no_bet"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
