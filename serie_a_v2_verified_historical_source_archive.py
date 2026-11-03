"""Reuse only pre-freeze CSV members from a verified current-form GitHub artifact.

The 2026/27 ZIP member is intentionally never opened, hashed, parsed, or copied.
The artifact's GitHub digest, successful main parent run, manifest, and all ten
old-season CSV hashes are verified before the historical frame is returned.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
from typing import Any, Mapping
import zipfile

import pandas as pd
import requests

from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from serie_a_v2_asof_feature_manifest import REQUIRED, _validate_history
from serie_a_v2_current_form_forward_capture import (
    ARTIFACT_NAME,
    MAX_ARCHIVE_BYTES,
    SOURCE_WORKFLOW_PATH,
    discover_archives,
    get_archive,
    verify_source_run,
)
from serie_a_v2_current_form_source_capture import (
    CURRENT_CODE,
    CURRENT_FILENAME,
    CURRENT_SEASON,
    CURRENT_URL,
    MANIFEST_FILENAME,
    MIN_COMPLETED_FEATURE_SOURCE_EVENTS,
    MAX_CURRENT_CSV_BYTES,
    SCHEMA_VERSION,
)
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA, parse_utc

REPOSITORY = "MaksimBlud/football-ai"
PUBLIC_BASE = "https://www.football-data.co.uk/mmz4281"
OLD_CUTOFF = pd.Timestamp("2026-07-01")
MAX_HISTORICAL_CSV_BYTES = 2_000_000
SHA256_RE = re.compile(r"[0-9a-f]{64}\\Z")


def _utc(value: Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field} requires a real UTC offset")
        return value.astimezone(timezone.utc)
    return parse_utc(value)


def verify_historical_only_archive(
    raw: bytes,
    archive: Mapping[str, Any],
    parent: Mapping[str, Any],
    *,
    now: datetime,
    capture_dir: Path | None = None,
) -> dict:
    """Verify and load only ten pre-freeze CSV members; never read CURRENT_FILENAME."""
    at = _utc(now, field="archive verification clock")
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("current-form source archive is empty or exceeds frozen size limit")

    artifact_id = archive.get("artifact_id")
    run_id = archive.get("run_id")
    head_sha = archive.get("head_sha")
    declared_sha = archive.get("sha256")
    if type(artifact_id) is not int or artifact_id <= 0:
        raise ValueError("source artifact id is invalid")
    if type(run_id) is not int or run_id <= 0:
        raise ValueError("source artifact parent run id is invalid")
    if not isinstance(head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", head_sha):
        raise ValueError("source artifact parent SHA is invalid")
    if not isinstance(declared_sha, str) or not SHA256_RE.fullmatch(declared_sha):
        raise ValueError("GitHub source artifact SHA256 is invalid")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != declared_sha:
        raise ValueError("GitHub current-form source artifact SHA256 mismatch")

    artifact_created = _utc(archive.get("created_at"), field="GitHub artifact created_at")
    if artifact_created >= at:
        raise ValueError("source artifact is not strictly before diagnostic time")
    if (parent.get("run_id") != run_id
            or parent.get("run_head_sha") != head_sha
            or parent.get("workflow_path") != SOURCE_WORKFLOW_PATH):
        raise ValueError("source artifact parent attestation does not match artifact metadata")
    run_created = _utc(parent.get("run_created_at_utc"), field="parent run created_at")
    run_completed = _utc(parent.get("run_completed_at_utc"), field="parent run completed_at")
    if not (run_created <= artifact_created <= run_completed < at):
        raise ValueError("source artifact is not inside a completed successful parent run")

    historical_codes = list(SERIE_A_RUNTIME_CONFIG.historical_source.season_codes)
    if not historical_codes or historical_codes != list(sorted(historical_codes)):
        raise ValueError("frozen historical season order is invalid")
    historical_names = {f"serie_a_{code}.csv" for code in historical_codes}
    expected_names = historical_names | {CURRENT_FILENAME, MANIFEST_FILENAME}

    try:
        with zipfile.ZipFile(BytesIO(raw), "r") as z:
            infos = z.infolist()
            names = [item.filename for item in infos]
            if len(names) != len(expected_names) or len(set(names)) != len(names) or set(names) != expected_names:
                raise ValueError("source artifact member set differs from the frozen 10+current manifest")
            info_by_name = {item.filename: item for item in infos}
            if any(item.is_dir() for item in infos):
                raise ValueError("source artifact contains an unexpected directory member")
            if info_by_name[MANIFEST_FILENAME].file_size > 3_000_000:
                raise ValueError("source artifact manifest is oversized")
            if info_by_name[CURRENT_FILENAME].file_size <= 0 or info_by_name[CURRENT_FILENAME].file_size > MAX_CURRENT_CSV_BYTES:
                raise ValueError("protected current-season member metadata has invalid size")
            for name in historical_names:
                if info_by_name[name].file_size <= 0 or info_by_name[name].file_size > MAX_HISTORICAL_CSV_BYTES:
                    raise ValueError("historical source CSV member is empty or oversized")

            # Manifest is metadata only. The protected current-season member is never read.
            manifest = json.loads(z.read(MANIFEST_FILENAME))
            if (manifest.get("schema_version") != SCHEMA_VERSION
                    or manifest.get("experiment_id") != "MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY"
                    or manifest.get("mode") != "RESEARCH_ONLY_CURRENT_FORM_SOURCE_ARCHIVE"
                    or manifest.get("repository") != REPOSITORY
                    or manifest.get("workflow_path") != SOURCE_WORKFLOW_PATH
                    or manifest.get("git_sha") != head_sha
                    or str(manifest.get("workflow_run_id")) != str(run_id)
                    or manifest.get("frozen_candidate_sha256") != FROZEN_SHA
                    or manifest.get("feature_count") != 19
                    or manifest.get("historical_season_codes") != historical_codes
                    or manifest.get("current_season_code") != CURRENT_CODE
                    or manifest.get("current_season") != CURRENT_SEASON
                    or manifest.get("current_season_source_url") != CURRENT_URL
                    or manifest.get("source_file_count") != len(expected_names) - 1
                    or manifest.get("historical_old_season_file_count") != len(historical_codes)):
                raise ValueError("current-form source manifest violates frozen original V2 contract")

            manifest_created = _utc(
                manifest.get("source_archive_created_at_utc"),
                field="manifest source_archive_created_at_utc",
            )
            if not (run_created <= manifest_created <= artifact_created):
                raise ValueError("source manifest creation time conflicts with parent/artifact")

            gate = manifest.get("feature_source_gate")
            if (not isinstance(gate, dict)
                    or gate.get("type") != "CURRENT_FORM_FEATURE_INPUT_ONLY"
                    or gate.get("primary_league") != "SERIE_A"
                    or gate.get("season") != CURRENT_SEASON
                    or gate.get("minimum_completed_primary_events") != MIN_COMPLETED_FEATURE_SOURCE_EVENTS
                    or type(gate.get("observed_completed_primary_events")) is not int
                    or gate.get("observed_completed_primary_events") < MIN_COMPLETED_FEATURE_SOURCE_EVENTS
                    or gate.get("score_or_result_fields_selected_for_gate") is not False
                    or gate.get("passed") is not True):
                raise ValueError("source artifact feature-input metadata gate is invalid")

            target_gate = manifest.get("target_outcome_evaluation_gate")
            if (not isinstance(target_gate, dict)
                    or target_gate.get("minimum_completed_eligible_prospective_forecasts") != 30
                    or target_gate.get("outcomes_read_for_evaluation") is not False
                    or target_gate.get("outcome_gate_open") is not False
                    or manifest.get("target_outcomes_read") is not False
                    or manifest.get("target_outcomes_scored") is not False):
                raise ValueError("source artifact target-outcome embargo is not closed")
            if (manifest.get("model_refit_or_promotion") is not False
                    or manifest.get("paid_provider_calls") != 0
                    or manifest.get("supabase_writes") != 0
                    or manifest.get("eligible_for_product_publication") is not False
                    or manifest.get("no_bet") is not True):
                raise ValueError("source artifact violates research-only/no-write contract")

            audits = manifest.get("source_files")
            if not isinstance(audits, list) or len(audits) != len(historical_codes) + 1:
                raise ValueError("source manifest file audit is incomplete")
            by_code: dict[str, Mapping[str, Any]] = {}
            for item in audits:
                if not isinstance(item, Mapping):
                    raise ValueError("source manifest contains malformed file metadata")
                code = item.get("season_code")
                if not isinstance(code, str) or code in by_code:
                    raise ValueError("source manifest has duplicate or invalid season code")
                by_code[code] = item
            if set(by_code) != set(historical_codes) | {CURRENT_CODE}:
                raise ValueError("source manifest season set differs from frozen source contract")

            # Validate current-season metadata only. Do not call z.read(CURRENT_FILENAME).
            current_item = by_code[CURRENT_CODE]
            current_sha = manifest.get("current_season_source_sha256")
            current_observed_text = manifest.get("current_season_source_observed_at_utc")
            if (current_item.get("archived_source_name") != CURRENT_FILENAME
                    or current_item.get("season") != CURRENT_SEASON
                    or current_item.get("source_url") != CURRENT_URL
                    or current_item.get("csv_sha256") != current_sha
                    or current_item.get("source_observed_at_utc") != current_observed_text
                    or not isinstance(current_sha, str)
                    or not SHA256_RE.fullmatch(current_sha)):
                raise ValueError("protected current-season source metadata is inconsistent")
            current_observed = parse_utc(current_observed_text)
            if current_observed > manifest_created:
                raise ValueError("protected current-season source observation postdates manifest")

            frames = []
            source_audit = []
            verified_bytes: dict[str, bytes] = {}
            competition = SERIE_A_RUNTIME_CONFIG.historical_source.competition_code
            for code in historical_codes:
                item = by_code[code]
                filename = f"serie_a_{code}.csv"
                expected_url = f"{PUBLIC_BASE}/{code}/{competition}.csv"
                if (item.get("archived_source_name") != filename
                        or item.get("source_url") != expected_url):
                    raise ValueError("historical source metadata has unexpected name or URL")
                source_sha = item.get("csv_sha256")
                if not isinstance(source_sha, str) or not SHA256_RE.fullmatch(source_sha):
                    raise ValueError("historical source CSV SHA256 is invalid")
                observed = parse_utc(item.get("source_observed_at_utc"))
                if observed > manifest_created or observed > artifact_created:
                    raise ValueError("historical source was observed after source archive creation")
                row_count = item.get("completed_source_rows")
                if type(row_count) is not int or row_count <= 0:
                    raise ValueError("historical source row count is invalid")
                body = z.read(filename)
                if hashlib.sha256(body).hexdigest() != source_sha:
                    raise ValueError("historical source CSV SHA256 mismatch")
                frame = pd.read_csv(BytesIO(body), low_memory=False)
                if len(frame) != row_count:
                    raise ValueError("historical source CSV row count mismatch")
                if not REQUIRED.issubset(frame.columns):
                    raise ValueError("historical source CSV lacks original V2 statistics")
                frame = frame.loc[:, list(sorted(REQUIRED))].copy()
                frames.append(frame)
                source_audit.append({
                    "season_code": code,
                    "source_url": expected_url,
                    "csv_sha256": source_sha,
                    "archived_source_name": filename,
                    "source_observed_at_utc": observed.isoformat(),
                    "completed_source_rows": row_count,
                })
                verified_bytes[filename] = body

            history = _validate_history(pd.concat(frames, ignore_index=True))
            if (history["_match_date"] >= OLD_CUTOFF).any():
                raise ValueError("historical-only archive contains protected 2026/27 results")

            if capture_dir is not None:
                capture_dir.mkdir(parents=True, exist_ok=True)
                for filename, body in verified_bytes.items():
                    (capture_dir / filename).write_bytes(body)
                (capture_dir / MANIFEST_FILENAME).write_text(
                    json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\\n",
                    encoding="utf-8",
                )
    except zipfile.BadZipFile as exc:
        raise ValueError("source artifact is not a valid ZIP archive") from exc

    return {
        "history": history.loc[:, list(sorted(REQUIRED))].copy(),
        "source_audit": source_audit,
        "source_archive": {
            "artifact_id": artifact_id,
            "artifact_sha256": digest,
            "created_at_utc": artifact_created.isoformat(),
            "parent_run_id": run_id,
            "parent_head_sha": head_sha,
            "parent_run_created_at_utc": run_created.isoformat(),
            "parent_run_completed_at_utc": run_completed.isoformat(),
            "historical_old_season_file_count": len(source_audit),
            "historical_match_rows": int(len(history)),
            "current_season_member_opened": False,
            "current_season_member_sha_checked": False,
        },
    }


def load_latest_historical_source_archive(
    *,
    token: str,
    now: datetime,
    capture_dir: Path | None = None,
    get=requests.get,
) -> dict:
    """Discover and authenticate the latest successful main source artifact."""
    at = _utc(now, field="source archive lookup clock")
    if not isinstance(token, str) or not token.strip():
        raise ValueError("GitHub actions:read token is required")
    archives = discover_archives(token=token, get=get)
    candidates = [
        item for item in archives
        if _utc(item.get("created_at"), field="artifact created_at") < at
    ]
    if not candidates:
        raise RuntimeError("no earlier main current-form source artifact is available")
    archive = candidates[0]
    parent = verify_source_run(
        archive, quote_time=at, token=token, get=get
    )
    raw = get_archive(archive["artifact_id"], token=token, get=get)
    return verify_historical_only_archive(
        raw, archive, parent, now=at, capture_dir=capture_dir
    )
