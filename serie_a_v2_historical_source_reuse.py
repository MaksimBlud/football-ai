"""Reuse only authenticated pre-2026/27 historical CSV bytes from a main source artifact.

The current-season CSV inside the source artifact is deliberately not extracted or
parsed here. The caller must obtain a fresh current-season CSV separately, after
its identity-only feature-source gate. This module performs GitHub API reads only:
no Football-Data requests, Supabase access, odds, outcome reads, writes, or training.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from io import BytesIO
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any, Callable, Mapping
import zipfile

import pandas as pd
import requests

from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from serie_a_v2_asof_feature_manifest import REQUIRED, _validate_history
from serie_a_v2_frozen_shadow_preview import FROZEN_SHA

REPOSITORY = "MaksimBlud/football-ai"
GITHUB_API = f"https://api.github.com/repos/{REPOSITORY}"
ARTIFACT_NAME = "serie-a-v2-current-form-source-capture"
SOURCE_WORKFLOW_PATH = ".github/workflows/serie-a-v2-current-form-source-capture.yml"
SOURCE_WORKFLOW_NAME = "Serie A V2 Current-Form Source Capture"
SCHEMA_VERSION = "SERIE_A_V2_VERIFIED_HISTORICAL_SOURCE_REUSE_V1"
PUBLIC_BASE = "https://www.football-data.co.uk/mmz4281"
HISTORICAL_CODES = tuple(SERIE_A_RUNTIME_CONFIG.historical_source.season_codes)
CURRENT_CODE = SERIE_A_RUNTIME_CONFIG.finished_results_source.season_code
CURRENT_SEASON = SERIE_A_RUNTIME_CONFIG.finished_results_source.season
CURRENT_FILENAME = f"serie_a_{CURRENT_CODE}.csv"
CURRENT_URL = (
    f"{PUBLIC_BASE}/{CURRENT_CODE}/"
    f"{SERIE_A_RUNTIME_CONFIG.finished_results_source.competition_code}.csv"
)
MANIFEST_FILENAME = "serie_a_v2_current_form_source_manifest.json"
EXPECTED_BUILDER_BLOB_SHA1 = "401b3a0893371bfa4a488ec92a4a54af2678c8f7"
EXPECTED_FEATURE_COUNT = 19
OLD_CUTOFF = pd.Timestamp("2026-07-01")
MAX_ARCHIVE_BYTES = 16_000_000
MAX_UNCOMPRESSED_BYTES = 12_000_000
MAX_CSV_BYTES = 5_000_000
MAX_CURRENT_CSV_BYTES = 2_000_000
MAX_MANIFEST_BYTES = 2_000_000
SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
ALLOWED_EVENTS = {"schedule", "workflow_dispatch", "push"}
REQUIRED_COLUMNS = tuple(sorted(REQUIRED))


def _utc(value: Any, *, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a real UTC offset")
    return parsed.astimezone(timezone.utc)


def _fixture_identity_sha256(identities: Any) -> str:
    """Recompute the exact frozen V2 digest for canonical date/home/away identities."""
    if not isinstance(identities, (list, tuple)) or not identities:
        raise ValueError("feature-source gate identity set must be a non-empty list")
    canonical: list[tuple[str, str, str]] = []
    for identity in identities:
        if not isinstance(identity, (list, tuple)) or len(identity) != 3:
            raise ValueError("feature-source gate identity must contain date, home and away")
        raw_date, home, away = identity
        if not isinstance(raw_date, str):
            raise ValueError("feature-source gate identity date must be a canonical ISO date")
        try:
            parsed_date = date.fromisoformat(raw_date)
        except ValueError as exc:
            raise ValueError("feature-source gate identity date must be a canonical ISO date") from exc
        if parsed_date.isoformat() != raw_date or not (date(2026, 7, 1) <= parsed_date <= date(2027, 6, 30)):
            raise ValueError("feature-source gate identity date is outside the frozen 2026/27 season")
        for team in (home, away):
            if (
                not isinstance(team, str)
                or not team
                or team != team.strip()
                or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in team)
            ):
                raise ValueError("feature-source gate identity has a malformed canonical team")
        if home.casefold() == away.casefold():
            raise ValueError("feature-source gate identity cannot contain identical teams")
        canonical.append((raw_date, home, away))
    if len(set(canonical)) != len(canonical):
        raise ValueError("feature-source gate identity set contains duplicates")
    payload = "\n".join("\t".join(identity) for identity in sorted(canonical))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _github_json(url: str, *, token: str, get: Callable[..., Any]) -> dict:
    if not isinstance(token, str) or not token.strip():
        raise ValueError("GitHub actions:read token is required for historical-source reuse")
    if not isinstance(url, str) or not url.startswith(GITHUB_API + "/"):
        raise ValueError("historical-source reuse API URL escaped the fixed repository")
    response = get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
        allow_redirects=False,
    )
    if getattr(response, "url", None) != url:
        raise ValueError("GitHub API returned an unexpected URL during historical-source reuse")
    if getattr(response, "status_code", None) != 200:
        raise RuntimeError(
            "GitHub API failed during historical-source reuse: "
            f"HTTP {getattr(response, 'status_code', None)}"
        )
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("GitHub API returned a non-object historical-source response")
    return payload


def _discover_latest_artifact(*, token: str, get: Callable[..., Any]) -> dict:
    candidates: list[dict] = []
    page_size = 100
    max_pages = 3
    for page in range(1, max_pages + 1):
        payload = _github_json(
            f"{GITHUB_API}/actions/artifacts?name={ARTIFACT_NAME}"
            f"&per_page={page_size}&page={page}",
            token=token,
            get=get,
        )
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, list):
            raise ValueError("GitHub artifact listing lacks an artifacts array")
        for item in artifacts:
            if not isinstance(item, Mapping):
                raise ValueError("GitHub artifact listing contains a malformed item")
            if item.get("name") != ARTIFACT_NAME or item.get("expired") is True:
                continue
            workflow_run = item.get("workflow_run")
            if not isinstance(workflow_run, Mapping):
                raise ValueError("source artifact lacks its GitHub parent workflow metadata")
            if workflow_run.get("head_branch") != "main":
                continue
            artifact_id = item.get("id")
            run_id = workflow_run.get("id")
            head_sha = workflow_run.get("head_sha")
            digest = item.get("digest")
            if type(artifact_id) is not int or artifact_id <= 0:
                raise ValueError("source artifact has an invalid artifact ID")
            if type(run_id) is not int or run_id <= 0:
                raise ValueError("source artifact has an invalid parent run ID")
            if not isinstance(head_sha, str) or SHA1_RE.fullmatch(head_sha) is None:
                raise ValueError("source artifact has an invalid parent HEAD SHA")
            if not isinstance(digest, str) or not digest.startswith("sha256:"):
                raise ValueError("source artifact lacks a GitHub SHA-256 digest")
            digest_value = digest.removeprefix("sha256:")
            if SHA256_RE.fullmatch(digest_value) is None:
                raise ValueError("source artifact has a malformed GitHub SHA-256 digest")
            candidates.append({
                "artifact_id": artifact_id,
                "run_id": run_id,
                "head_sha": head_sha,
                "created_at": _utc(item.get("created_at"), field="artifact created_at"),
                "sha256": digest_value,
            })
        if len(artifacts) < page_size:
            break
        if page == max_pages:
            raise ValueError("source artifact pagination exceeded its fixed safety bound")
    if not candidates:
        raise RuntimeError("no successful-main current-form source artifact is available for reuse")
    return max(candidates, key=lambda item: (item["created_at"], item["artifact_id"]))


def _verify_parent_run(
    artifact: Mapping[str, Any], *, token: str, now: datetime,
    get: Callable[..., Any],
) -> dict:
    run_id = artifact.get("run_id")
    if type(run_id) is not int or run_id <= 0:
        raise ValueError("source artifact parent run ID is invalid")
    run = _github_json(
        f"{GITHUB_API}/actions/runs/{run_id}",
        token=token,
        get=get,
    )
    if (
        run.get("id") != run_id
        or run.get("path") != SOURCE_WORKFLOW_PATH
        or run.get("name") != SOURCE_WORKFLOW_NAME
        or run.get("head_branch") != "main"
        or run.get("head_sha") != artifact.get("head_sha")
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or run.get("event") not in ALLOWED_EVENTS
    ):
        raise ValueError("historical source artifact is not from the exact successful main source workflow")
    run_created = _utc(run.get("created_at"), field="source parent run created_at")
    run_completed = _utc(run.get("updated_at"), field="source parent run updated_at")
    if run_created > artifact["created_at"] or artifact["created_at"] > run_completed:
        raise ValueError("source artifact creation is outside its successful parent run interval")
    if artifact["created_at"] >= now:
        raise ValueError("source artifact is not strictly older than the current reuse operation")
    return {
        "run_id": run_id,
        "head_sha": artifact["head_sha"],
        "head_branch": "main",
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "workflow_name": SOURCE_WORKFLOW_NAME,
        "event": run["event"],
        "run_created_at_utc": run_created.isoformat(),
        "run_completed_at_utc": run_completed.isoformat(),
    }


def _download_archive(
    artifact_id: int, *, token: str, get: Callable[..., Any]
) -> bytes:
    if type(artifact_id) is not int or artifact_id <= 0:
        raise ValueError("invalid source artifact ID")
    response = get(
        f"{GITHUB_API}/actions/artifacts/{artifact_id}/zip",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=90,
        stream=True,
        allow_redirects=True,
    )
    try:
        if getattr(response, "status_code", None) != 200:
            raise RuntimeError("GitHub source artifact download did not return HTTP 200")
        final_url = getattr(response, "url", None)
        if not isinstance(final_url, str) or not final_url.startswith("https://"):
            raise ValueError("GitHub source artifact download did not finish on HTTPS")
        headers = getattr(response, "headers", {}) or {}
        declared_length = headers.get("Content-Length")
        if declared_length is not None:
            text = str(declared_length).strip()
            if not text.isascii() or not text.isdecimal():
                raise ValueError("source artifact Content-Length is malformed")
            if int(text) > MAX_ARCHIVE_BYTES:
                raise ValueError("source artifact exceeds the compressed-size bound")
        chunks: list[bytes] = []
        total = 0
        iterator = getattr(response, "iter_content", None)
        if not callable(iterator):
            raise ValueError("source artifact response does not support bounded streaming")
        for chunk in iterator(chunk_size=64 * 1024):
            if not chunk:
                continue
            if not isinstance(chunk, bytes):
                raise ValueError("source artifact stream yielded a non-bytes chunk")
            total += len(chunk)
            if total > MAX_ARCHIVE_BYTES:
                raise ValueError("source artifact exceeds the compressed-size bound")
            chunks.append(chunk)
        raw = b"".join(chunks)
        if not raw:
            raise ValueError("source artifact ZIP is empty")
        return raw
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            close()


def _verify_origin_provenance(
    reuse_meta: Any,
    *,
    artifact: Mapping[str, Any],
    parent: Mapping[str, Any],
    token: str,
    get: Callable[..., Any],
) -> tuple[dict, datetime, bool]:
    current_parent_created = _utc(parent["run_created_at_utc"], field="current parent run created_at")
    if reuse_meta is None:
        return {
            "source_artifact_id": artifact["artifact_id"],
            "source_artifact_sha256": artifact["sha256"],
            "source_artifact_created_at_utc": artifact["created_at"].isoformat(),
            "source_parent_run_id": artifact["run_id"],
            "source_parent_run_head_sha": artifact["head_sha"],
            "source_parent_run_completed_at_utc": parent["run_completed_at_utc"],
        }, artifact["created_at"], False

    if not isinstance(reuse_meta, Mapping):
        raise ValueError("historical-source reuse provenance must be an object")
    mode = reuse_meta.get("mode")
    if mode == "DIRECT_PUBLIC_HISTORICAL_DOWNLOADS":
        if (
            reuse_meta.get("historical_files_reused") != 0
            or reuse_meta.get("public_historical_csv_requests") != len(HISTORICAL_CODES)
            or reuse_meta.get("current_season_file_reused") is not False
            or reuse_meta.get("prior_feature_gate_reused") is not False
            or reuse_meta.get("protected_2026_27_source_file_read") is not False
            or reuse_meta.get("target_outcomes_read") is not False
            or reuse_meta.get("supabase_writes") != 0
            or reuse_meta.get("paid_provider_calls") != 0
        ):
            raise ValueError("direct-download provenance does not match the bootstrap contract")
        return {
            "source_artifact_id": artifact["artifact_id"],
            "source_artifact_sha256": artifact["sha256"],
            "source_artifact_created_at_utc": artifact["created_at"].isoformat(),
            "source_parent_run_id": artifact["run_id"],
            "source_parent_run_head_sha": artifact["head_sha"],
            "source_parent_run_completed_at_utc": parent["run_completed_at_utc"],
        }, artifact["created_at"], False

    if mode != "REUSED_VERIFIED_MAIN_ARTIFACT_HISTORICAL_ONLY":
        raise ValueError("source artifact uses an unknown or injected historical reuse mode")
    origin_id = reuse_meta.get("source_artifact_id")
    origin_run_id = reuse_meta.get("source_parent_run_id")
    origin_sha = reuse_meta.get("source_artifact_sha256")
    origin_head = reuse_meta.get("source_parent_run_head_sha")
    if (
        type(origin_id) is not int or origin_id <= 0
        or type(origin_run_id) is not int or origin_run_id <= 0
        or not isinstance(origin_sha, str) or SHA256_RE.fullmatch(origin_sha) is None
        or not isinstance(origin_head, str) or SHA1_RE.fullmatch(origin_head) is None
        or reuse_meta.get("historical_files_reused") != len(HISTORICAL_CODES)
        or reuse_meta.get("public_historical_csv_requests") != 0
        or reuse_meta.get("current_season_file_reused") is not False
        or reuse_meta.get("prior_feature_gate_reused") is not False
        or reuse_meta.get("protected_2026_27_source_file_read") is not False
        or reuse_meta.get("target_outcomes_read") is not False
        or reuse_meta.get("supabase_writes") != 0
        or reuse_meta.get("paid_provider_calls") != 0
    ):
        raise ValueError("historical reuse provenance lacks its immutable original-artifact anchor")
    origin_created = _utc(
        reuse_meta.get("source_artifact_created_at_utc"),
        field="origin source artifact created_at",
    )
    origin_completed_declared = _utc(
        reuse_meta.get("source_parent_run_completed_at_utc"),
        field="origin source parent completed_at",
    )
    origin_payload = _github_json(
        f"{GITHUB_API}/actions/artifacts/{origin_id}",
        token=token,
        get=get,
    )
    workflow_run = origin_payload.get("workflow_run")
    digest = origin_payload.get("digest")
    if (
        origin_payload.get("id") != origin_id
        or origin_payload.get("name") != ARTIFACT_NAME
        or origin_payload.get("expired") is True
        or not isinstance(digest, str)
        or digest != "sha256:" + origin_sha
        or _utc(origin_payload.get("created_at"), field="origin artifact created_at") != origin_created
        or not isinstance(workflow_run, Mapping)
        or workflow_run.get("id") != origin_run_id
        or workflow_run.get("head_branch") != "main"
        or workflow_run.get("head_sha") != origin_head
    ):
        raise ValueError("historical reuse origin does not match GitHub artifact metadata")
    origin_artifact = {
        "artifact_id": origin_id,
        "run_id": origin_run_id,
        "head_sha": origin_head,
        "created_at": origin_created,
        "sha256": origin_sha,
    }
    origin_parent = _verify_parent_run(
        origin_artifact,
        token=token,
        now=current_parent_created,
        get=get,
    )
    if (
        _utc(origin_parent["run_completed_at_utc"], field="origin parent completed_at")
        != origin_completed_declared
        or origin_created > origin_completed_declared
        or origin_completed_declared > current_parent_created
    ):
        raise ValueError("historical reuse origin is not completed before the current source run")
    return {
        "source_artifact_id": origin_id,
        "source_artifact_sha256": origin_sha,
        "source_artifact_created_at_utc": origin_created.isoformat(),
        "source_parent_run_id": origin_run_id,
        "source_parent_run_head_sha": origin_head,
        "source_parent_run_completed_at_utc": origin_completed_declared.isoformat(),
    }, origin_created, True


def _verify_and_extract_historical_files(
    raw: bytes,
    artifact: Mapping[str, Any],
    parent: Mapping[str, Any],
    *,
    capture_dir: Path | None,
    token: str,
    get: Callable[..., Any],
) -> tuple[pd.DataFrame, list[dict], dict]:
    if not raw or len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("source artifact ZIP is empty or oversized")
    actual_digest = hashlib.sha256(raw).hexdigest()
    if actual_digest != artifact.get("sha256"):
        raise ValueError("GitHub source artifact SHA-256 does not match downloaded ZIP")

    expected_old_names = {f"serie_a_{code}.csv" for code in HISTORICAL_CODES}
    expected_names = expected_old_names | {CURRENT_FILENAME, MANIFEST_FILENAME}
    frames: list[pd.DataFrame] = []
    audits: list[dict] = []
    source_times: list[datetime] = []
    total_uncompressed = 0

    try:
        archive = zipfile.ZipFile(BytesIO(raw), "r")
    except zipfile.BadZipFile as exc:
        raise ValueError("GitHub current-form source artifact is not a valid ZIP") from exc

    with archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(infos) != len(expected_names) or len(set(names)) != len(names) or set(names) != expected_names:
            raise ValueError("current-form source artifact has unexpected, missing, or duplicate ZIP members")
        info_by_name = {}
        for info in infos:
            path = PurePosixPath(info.filename)
            mode = info.external_attr >> 16
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in info.filename
                or info.is_dir()
                or (mode and stat.S_ISLNK(mode))
                or (info.flag_bits & 0x1)
            ):
                raise ValueError("current-form source artifact contains an unsafe ZIP member")
            total_uncompressed += info.file_size
            if info.file_size < 0 or total_uncompressed > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("current-form source artifact exceeds the uncompressed-size bound")
            if info.filename == MANIFEST_FILENAME:
                if info.file_size > MAX_MANIFEST_BYTES:
                    raise ValueError("current-form source manifest exceeds its size bound")
            elif info.filename == CURRENT_FILENAME:
                if info.file_size <= 0 or info.file_size > MAX_CURRENT_CSV_BYTES:
                    raise ValueError("current-season source member exceeds its size bound")
            elif info.file_size <= 0 or info.file_size > MAX_CSV_BYTES:
                raise ValueError("historical source CSV exceeds its size bound")
            info_by_name[info.filename] = info

        manifest = json.loads(archive.read(info_by_name[MANIFEST_FILENAME]).decode("utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("current-form source manifest must be a JSON object")
        if (
            manifest.get("schema_version") != "SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1"
            or manifest.get("experiment_id") != "MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY"
            or manifest.get("repository") != REPOSITORY
            or manifest.get("workflow_path") != SOURCE_WORKFLOW_PATH
            or manifest.get("git_sha") != artifact.get("head_sha")
            or str(manifest.get("workflow_run_id")) != str(artifact.get("run_id"))
            or manifest.get("frozen_candidate_sha256") != FROZEN_SHA
            or manifest.get("original_feature_builder_git_blob_sha1") != EXPECTED_BUILDER_BLOB_SHA1
            or manifest.get("feature_count") != EXPECTED_FEATURE_COUNT
            or manifest.get("historical_season_codes") != list(HISTORICAL_CODES)
            or manifest.get("current_season_code") != CURRENT_CODE
            or manifest.get("current_season") != CURRENT_SEASON
            or manifest.get("current_season_source_url") != CURRENT_URL
            or manifest.get("source_file_count") != len(expected_names) - 1
            or manifest.get("historical_old_season_file_count") != len(HISTORICAL_CODES)
            or manifest.get("eligible_for_product_publication") is not False
            or manifest.get("eligible_for_frozen_old_season_cohort") is not False
            or manifest.get("eligible_for_current_form_forward_shadow") is not False
            or manifest.get("no_bet") is not True
            or manifest.get("target_outcomes_read") is not False
            or manifest.get("target_outcomes_scored") is not False
            or manifest.get("model_refit_or_promotion") is not False
            or manifest.get("paid_provider_calls") != 0
            or manifest.get("supabase_writes") != 0
        ):
            raise ValueError("current-form source manifest violates the frozen historical-source reuse contract")

        feature_gate = manifest.get("feature_source_gate")
        if (
            not isinstance(feature_gate, Mapping)
            or feature_gate.get("type") != "CURRENT_FORM_FEATURE_INPUT_ONLY"
            or feature_gate.get("primary_league") != "SERIE_A"
            or feature_gate.get("season") != CURRENT_SEASON
            or feature_gate.get("minimum_completed_primary_events") != 30
            or type(feature_gate.get("observed_completed_primary_events")) is not int
            or feature_gate.get("observed_completed_primary_events") < 30
            or feature_gate.get("metadata_fields_read") != ["match_date", "home_team", "away_team"]
            or feature_gate.get("score_or_result_fields_selected_for_gate") is not False
            or feature_gate.get("passed") is not True
        ):
            raise ValueError("source artifact lacks a closed-contract identity-only feature-input gate")

        observed_gate_count = feature_gate["observed_completed_primary_events"]
        gate_identity_count = feature_gate.get("gate_fixture_identity_count")
        gate_identities = feature_gate.get("gate_fixture_identities")
        gate_identity_sha = feature_gate.get("gate_fixture_identity_sha256")
        current_identity_count = feature_gate.get("current_source_fixture_identity_count")
        current_identity_sha = feature_gate.get("current_source_fixture_identity_sha256")
        covered_identity_count = feature_gate.get("gate_fixture_identities_covered_by_current_source")
        missing_identity_count = feature_gate.get("gate_fixture_identities_missing_from_current_source")
        if (
            type(gate_identity_count) is not int
            or gate_identity_count != observed_gate_count
            or not isinstance(gate_identity_sha, str)
            or SHA256_RE.fullmatch(gate_identity_sha) is None
            or type(current_identity_count) is not int
            or current_identity_count < gate_identity_count
            or not isinstance(current_identity_sha, str)
            or SHA256_RE.fullmatch(current_identity_sha) is None
            or type(covered_identity_count) is not int
            or covered_identity_count != gate_identity_count
            or type(missing_identity_count) is not int
            or missing_identity_count != 0
        ):
            raise ValueError("feature-source gate lacks a complete digest-bound identity coverage attestation")
        if _fixture_identity_sha256(gate_identities) != gate_identity_sha:
            raise ValueError("feature-source gate identity-set SHA-256 does not match its canonical identities")
        if len(gate_identities) != gate_identity_count:
            raise ValueError("feature-source gate identity count does not match its canonical identity list")

        feature_policy = manifest.get("feature_policy")
        if (
            not isinstance(feature_policy, Mapping)
            or feature_policy.get("use_current_season_matches_only_as_lagged_features") is not True
            or feature_policy.get("model_refit") is not False
            or feature_policy.get("model_selection") is not False
            or feature_policy.get("model_weights_or_feature_definitions_changed") is not False
            or feature_policy.get("same_calendar_day_matches_excluded") is not True
            or feature_policy.get("future_or_unplayed_fixtures_used") is not False
        ):
            raise ValueError("source artifact feature policy is not the frozen research-only policy")

        outcome_gate = manifest.get("target_outcome_evaluation_gate")
        if (
            not isinstance(outcome_gate, Mapping)
            or outcome_gate.get("minimum_completed_eligible_prospective_forecasts") != 30
            or outcome_gate.get("outcomes_read_for_evaluation") is not False
            or outcome_gate.get("outcome_gate_open") is not False
        ):
            raise ValueError("source artifact unexpectedly opened the protected evaluation gate")

        archive_created = _utc(
            manifest.get("source_archive_created_at_utc"),
            field="manifest source_archive_created_at_utc",
        )
        artifact_created = artifact["created_at"]
        parent_completed = _utc(parent["run_completed_at_utc"], field="parent run completed_at")
        parent_created = _utc(parent["run_created_at_utc"], field="parent run created_at")
        if not parent_created <= archive_created <= artifact_created <= parent_completed:
            raise ValueError("source manifest/archive/parent run timestamps are inconsistent")
        origin_provenance, source_anchor_created, is_reused = _verify_origin_provenance(
            manifest.get("historical_source_reuse"),
            artifact=artifact,
            parent=parent,
            token=token,
            get=get,
        )

        source_files = manifest.get("source_files")
        if not isinstance(source_files, list) or len(source_files) != len(expected_names) - 1:
            raise ValueError("source artifact file audit is incomplete")
        by_code = {
            item.get("season_code"): item
            for item in source_files
            if isinstance(item, Mapping)
        }
        expected_codes = set(HISTORICAL_CODES) | {CURRENT_CODE}
        if len(by_code) != len(expected_codes) or set(by_code) != expected_codes:
            raise ValueError("source artifact audit has duplicate or unexpected season codes")

        current_item = by_code[CURRENT_CODE]
        if (
            current_item.get("archived_source_name") != CURRENT_FILENAME
            or current_item.get("source_url") != CURRENT_URL
            or current_item.get("csv_sha256") != manifest.get("current_season_source_sha256")
            or current_item.get("source_observed_at_utc") != manifest.get("current_season_source_observed_at_utc")
            or not isinstance(current_item.get("csv_sha256"), str)
            or SHA256_RE.fullmatch(current_item["csv_sha256"]) is None
        ):
            raise ValueError("current-season source metadata is inconsistent")
        current_observed = _utc(
            current_item.get("source_observed_at_utc"),
            field="current-season source_observed_at_utc",
        )
        gate_checked_at = _utc(
            feature_gate.get("checked_at_utc"),
            field="feature-source gate checked_at_utc",
        )
        if not parent_created <= gate_checked_at <= current_observed:
            raise ValueError("current-season source observation does not follow the authenticated feature-source gate")
        if current_observed < parent_created or current_observed > archive_created:
            raise ValueError("current-season source observation is outside the current source run")
        # Deliberately do not read or decompress CURRENT_FILENAME: this helper
        # reuses old-season inputs only, never protected 2026/27 outcomes.

        for code in HISTORICAL_CODES:
            item = by_code[code]
            filename = f"serie_a_{code}.csv"
            expected_url = (
                f"{PUBLIC_BASE}/{code}/"
                f"{SERIE_A_RUNTIME_CONFIG.historical_source.competition_code}.csv"
            )
            if (
                item.get("archived_source_name") != filename
                or item.get("source_url") != expected_url
                or not isinstance(item.get("csv_sha256"), str)
                or SHA256_RE.fullmatch(item["csv_sha256"]) is None
            ):
                raise ValueError("historical source audit has an unexpected URL, file, or SHA")
            observed = _utc(
                item.get("source_observed_at_utc"),
                field=f"historical source {code} source_observed_at_utc",
            )
            if observed > source_anchor_created or observed > archive_created or observed > artifact_created:
                raise ValueError("historical source observation postdates its authenticated origin archive")
            if not is_reused and observed < parent_created:
                raise ValueError("direct historical source observation predates its source workflow run")
            body = archive.read(info_by_name[filename])
            if hashlib.sha256(body).hexdigest() != item["csv_sha256"]:
                raise ValueError(f"historical source CSV SHA-256 mismatch for season {code}")
            frame = pd.read_csv(BytesIO(body), low_memory=False)
            if not REQUIRED.issubset(frame.columns):
                raise ValueError(f"historical source CSV lacks original V2 statistics for season {code}")
            if len(frame) != item.get("completed_source_rows"):
                raise ValueError(f"historical source row count mismatch for season {code}")
            dates = pd.to_datetime(frame["Date"], dayfirst=True, format="mixed", errors="raise")
            if dates.isna().any() or (dates >= OLD_CUTOFF).any():
                raise ValueError("reused historical CSV contains a protected 2026/27 date")
            frames.append(frame.loc[:, list(REQUIRED_COLUMNS)].copy())
            audits.append({
                "season_code": code,
                "source_url": expected_url,
                "csv_sha256": item["csv_sha256"],
                "archived_source_name": filename,
                "source_observed_at_utc": observed.isoformat(),
                "completed_source_rows": len(frame),
            })
            source_times.append(observed)
            if capture_dir is not None:
                capture_dir.mkdir(parents=True, exist_ok=True)
                (capture_dir / filename).write_bytes(body)

    history = pd.concat(frames, ignore_index=True)
    validated = _validate_history(history)
    if (validated["_match_date"] >= OLD_CUTOFF).any():
        raise ValueError("reused historical source contains protected-season rows")
    if not source_times or max(source_times) > artifact["created_at"]:
        raise ValueError("historical source timestamps are not anchored before the GitHub artifact")
    provenance = {
        "schema_version": SCHEMA_VERSION,
        "mode": "REUSED_VERIFIED_MAIN_ARTIFACT_HISTORICAL_ONLY",
        **origin_provenance,
        "historical_files_reused": len(HISTORICAL_CODES),
        "public_historical_csv_requests": 0,
        "current_season_file_reused": False,
        "prior_feature_gate_reused": False,
        "protected_2026_27_source_file_read": False,
        "target_outcomes_read": False,
        "supabase_writes": 0,
        "paid_provider_calls": 0,
    }
    return history, audits, provenance


def load_verified_historical_source_archive(
    *,
    token: str,
    now: datetime,
    get: Callable[..., Any] = requests.get,
    capture_dir: Path | None = None,
) -> tuple[pd.DataFrame, list[dict], dict]:
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("historical-source reuse clock must have a real UTC offset")
    at = now.astimezone(timezone.utc)
    artifact = _discover_latest_artifact(token=token, get=get)
    parent = _verify_parent_run(artifact, token=token, now=at, get=get)
    raw = _download_archive(artifact["artifact_id"], token=token, get=get)
    return _verify_and_extract_historical_files(
        raw, artifact, parent, capture_dir=capture_dir, token=token, get=get
    )
