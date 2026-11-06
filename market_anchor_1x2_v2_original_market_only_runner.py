"""Read-only runner for the frozen original V2 secondary market comparison.

Rights are checked before any network/database access. It authenticates real
GitHub Actions artifacts and code blobs, reads only identity metadata before
both frozen gates, and loads exact H/D/A outcomes lazily after both gates.
No paid odds provider, Supabase write, production model, or promotion path.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, date, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from typing import Any, Callable, Mapping
from urllib.parse import quote, urlsplit
from zipfile import BadZipFile, ZipFile

import requests
from supabase import create_client

import market_anchor_1x2_v2_original_market_only_evaluator as evaluator
from market_anchor_v2_source_rights import (
    require_personal_research_inference_scope,
    write_research_scope_blocked_report,
)
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from serie_a_v2_forward_capture import discover_archives, get_archive, verify_source_run
from serie_a_v2_prequote_source_archive_gate import verify_archive

REPOSITORY = "MaksimBlud/football-ai"
GITHUB_API = f"https://api.github.com/repos/{REPOSITORY}"
FORWARD_ARTIFACT_NAME = evaluator.FORWARD_ARTIFACT_NAME
FORWARD_WORKFLOW_PATH = evaluator.FORWARD_WORKFLOW_PATH
FORWARD_WORKFLOW_NAME = evaluator.FORWARD_WORKFLOW_NAME
FORWARD_REPORT_NAME = "serie_a_v2_forward_source_checked.json"
SOURCE_ARTIFACT_NAME = evaluator.SOURCE_ARTIFACT_NAME
SOURCE_WORKFLOW_PATH = evaluator.SOURCE_WORKFLOW_PATH
SOURCE_WORKFLOW_NAME = evaluator.SOURCE_WORKFLOW_NAME
POLICY_FROZEN_AT = datetime.fromisoformat("2026-11-06T02:46:10+00:00")
MAX_FORWARD_ARTIFACT_BYTES = 2_000_000
MAX_FORWARD_UNCOMPRESSED_BYTES = 16_000_000
MAX_FORWARD_MEMBERS = 32
MAX_ARTIFACT_PAGES = 3
PER_PAGE = 100
MAX_IDENTITY_PAGES = 10
IDENTITY_PAGE_SIZE = 1000
SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_ZIP_RE = re.compile(r"source_artifact_(\d+)\.zip\Z")

# These exact Git blob IDs are inherited from the reviewed #699 source/forward
# branch and the frozen #716 evaluator/policy. A changed dependency blocks the
# runner until the code contract is reviewed and explicitly repinned.
CURRENT_CODE_BLOBS = {
    "market_anchor_1x2_v2_original_market_only_evaluator.py": "c460f9cfacc89374c19a709a3591fa52785a9003",
    "experiments/market_anchor_1x2_v2_original_market_only_secondary_policy.json": "0d0100a48bd5df68244bc32cb5a4301b621a800f",
    "market_anchor_v2_source_rights.py": "538ae477995c3b70ba5d4adafa8e4e7516072b98",
    "research/source_rights/football_data_co_uk.json": "a8795adce411fad4679491be36867dad2565a89c",
    "research/models/market_anchor_v2_serie_a_frozen_candidate.json": "ac1303f6b096664983fbf52443bd0a381b23ba21",
}
FORWARD_CODE_BLOBS = {
    ".github/workflows/serie-a-v2-forward-preview.yml": "cfd45b2d4835facbc9ec5894548714617d2635d8",
    "serie_a_v2_forward_capture.py": "932ece29fc68aee8921f5993f88b6e85ea43b835",
    "serie_a_v2_frozen_shadow_preview.py": "01dcc546b5d05f273d8a8d6a6c710cf2759fe06f",
    "serie_a_v2_asof_feature_manifest.py": "06393c494e454149e679b2a0826c194de94ed3f5",
    "historical_football_signal_lab.py": "401b3a0893371bfa4a488ec92a4a54af2678c8f7",
    "market_anchor_1x2_v2_shadow.py": "b2770d726ffafe7a3cef706b57d3391063cbfe1b",
    "serie_a_v2_prequote_source_archive_gate.py": "c04e8faae612305f4b618cd10ef59e3ec9729b2d",
    "serie_a_v2_live_diagnostic_report.py": "d3b717ea03570413f1d0b6b6f9821b2be0db16a3",
    "serie_a_v2_attest_real_source.py": "f80361c7dd5784883a1584d261ec5e026dfcb8ca",
    "market_anchor_v2_source_rights.py": "538ae477995c3b70ba5d4adafa8e4e7516072b98",
    "research/source_rights/football_data_co_uk.json": "a8795adce411fad4679491be36867dad2565a89c",
    "research/models/market_anchor_v2_serie_a_frozen_candidate.json": "ac1303f6b096664983fbf52443bd0a381b23ba21",
    "serie_a_runtime_config.py": "305472ca129459bda69a55a1c1c9501b3aea7b51",
}
CANDIDATE_PATH = "research/models/market_anchor_v2_serie_a_frozen_candidate.json"


def _utc(value: Any, field: str) -> datetime:
    return evaluator._utc(value, field)


def _github_json(url: str, token: str, *, get=requests.get) -> dict[str, Any]:
    if not isinstance(url, str) or not url.startswith(GITHUB_API + "/"):
        raise ValueError("GitHub API URL is outside the pinned repository")
    response = get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=(10, 30),
        allow_redirects=False,
    )
    if getattr(response, "url", None) != url:
        raise ValueError("GitHub API response URL mismatch")
    if getattr(response, "status_code", None) != 200:
        raise RuntimeError(f"GitHub API request failed with HTTP {getattr(response, 'status_code', None)}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("GitHub API response must be an object")
    return payload


def _verify_blob(token: str, ref: str, path: str, expected_sha: str, *, get=requests.get) -> dict[str, Any]:
    url = f"{GITHUB_API}/contents/{quote(path, safe='/')}?ref={quote(ref, safe='')}"
    payload = _github_json(url, token, get=get)
    if payload.get("path") != path or payload.get("type") != "file" or payload.get("sha") != expected_sha:
        raise ValueError(f"frozen code blob mismatch: {path}")
    return payload


def verify_current_main_contract(token: str, current_sha: str, *, get=requests.get) -> None:
    if SHA1_RE.fullmatch(current_sha or "") is None:
        raise ValueError("GITHUB_SHA must be a full commit SHA")
    ref = _github_json(f"{GITHUB_API}/git/ref/heads/main", token, get=get)
    if ref.get("object", {}).get("sha") != current_sha:
        raise ValueError("manual runner must execute on the exact current main HEAD")
    for path, expected in CURRENT_CODE_BLOBS.items():
        item = _verify_blob(token, current_sha, path, expected, get=get)
        if path == CANDIDATE_PATH:
            encoded = item.get("content")
            if not isinstance(encoded, str) or item.get("encoding") != "base64":
                raise ValueError("frozen candidate content is not available as base64")
            raw = base64.b64decode(encoded, validate=False)
            if hashlib.sha256(raw).hexdigest() != evaluator.CANDIDATE_SHA256:
                raise ValueError("frozen candidate content SHA-256 mismatch")


def discover_forward_artifacts(token: str, *, now: datetime, get=requests.get) -> list[dict[str, Any]]:
    if not token:
        raise ValueError("GITHUB_TOKEN actions:read is required")
    found: list[dict[str, Any]] = []
    seen: set[int] = set()
    for page in range(1, MAX_ARTIFACT_PAGES + 1):
        payload = _github_json(
            f"{GITHUB_API}/actions/artifacts?name={FORWARD_ARTIFACT_NAME}&per_page={PER_PAGE}&page={page}",
            token,
            get=get,
        )
        items = payload.get("artifacts")
        if not isinstance(items, list):
            raise ValueError("GitHub forward artifact listing is malformed")
        for item in items:
            if not isinstance(item, Mapping) or item.get("name") != FORWARD_ARTIFACT_NAME:
                continue
            if item.get("expired") is True:
                continue
            run = item.get("workflow_run")
            if not isinstance(run, Mapping) or run.get("head_branch") != "main":
                continue
            artifact_id, run_id, head_sha = item.get("id"), run.get("id"), run.get("head_sha")
            size = item.get("size_in_bytes")
            digest = item.get("digest")
            if type(artifact_id) is not int or artifact_id <= 0 or artifact_id in seen:
                raise ValueError("forward artifact ID is invalid or duplicated")
            if type(run_id) is not int or run_id <= 0 or SHA1_RE.fullmatch(str(head_sha or "")) is None:
                raise ValueError("forward artifact parent identity is malformed")
            if type(size) is not int or size <= 0 or size > MAX_FORWARD_ARTIFACT_BYTES:
                raise ValueError("forward artifact exceeds the frozen byte limit")
            if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                raise ValueError("forward artifact lacks a GitHub SHA-256 digest")
            created = _utc(item.get("created_at"), "forward artifact created_at")
            if created < POLICY_FROZEN_AT or created > now:
                continue
            seen.add(artifact_id)
            found.append({
                "artifact_id": artifact_id,
                "run_id": run_id,
                "head_sha": head_sha,
                "size_in_bytes": size,
                "sha256": digest.removeprefix("sha256:"),
                "created_at": created,
            })
        if len(items) < PER_PAGE:
            break
    else:
        if len(items) == PER_PAGE:
            raise ValueError("forward artifact scan reached the frozen pagination bound")
    return sorted(found, key=lambda item: (item["created_at"], item["artifact_id"]))


def _download_zip(artifact_id: int, token: str, *, max_bytes: int, get=requests.get) -> bytes:
    if type(artifact_id) is not int or artifact_id <= 0:
        raise ValueError("artifact ID is invalid")
    url = f"{GITHUB_API}/actions/artifacts/{artifact_id}/zip"
    response = get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=90,
        stream=True,
    )
    try:
        response.raise_for_status()
        final = urlsplit(getattr(response, "url", ""))
        if final.scheme != "https" or not final.hostname or final.username is not None or final.password is not None:
            raise ValueError("artifact download did not resolve to a safe HTTPS URL")
        declared = response.headers.get("Content-Length")
        if declared is not None:
            text = str(declared).strip()
            if not text.isascii() or not text.isdecimal() or int(text) <= 0 or int(text) > max_bytes:
                raise ValueError("artifact Content-Length is invalid or oversized")
        chunks, total = [], 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not isinstance(chunk, bytes):
                raise ValueError("artifact stream yielded non-bytes")
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("artifact exceeds the frozen byte limit")
            chunks.append(chunk)
        raw = b"".join(chunks)
        if not raw:
            raise ValueError("artifact ZIP is empty")
        return raw
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            close()


def _extract_forward_report(raw: bytes) -> dict[str, Any]:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_FORWARD_ARTIFACT_BYTES:
        raise ValueError("forward artifact bytes are empty or oversized")
    try:
        archive = ZipFile(BytesIO(raw))
    except BadZipFile as exc:
        raise ValueError("forward artifact is not a valid ZIP") from exc
    with archive:
        infos = archive.infolist()
        if not infos or len(infos) > MAX_FORWARD_MEMBERS:
            raise ValueError("forward artifact member count is outside the frozen bound")
        names: set[str] = set()
        total = 0
        reports = []
        for info in infos:
            name = info.filename
            path = PurePosixPath(name)
            mode = info.external_attr >> 16
            if path.is_absolute() or ".." in path.parts or "\\" in name or stat.S_ISLNK(mode):
                raise ValueError("forward artifact contains an unsafe ZIP member")
            if name in names:
                raise ValueError("forward artifact contains a duplicate ZIP member")
            names.add(name)
            if info.flag_bits & 0x1:
                raise ValueError("encrypted forward artifact member is forbidden")
            if info.is_dir():
                continue
            total += info.file_size
            if info.file_size < 0 or total > MAX_FORWARD_UNCOMPRESSED_BYTES:
                raise ValueError("forward artifact uncompressed size exceeds the frozen bound")
            basename = path.name
            if basename == FORWARD_REPORT_NAME:
                reports.append(info)
            elif basename == "serie_a_v2_real_source_attestation.json":
                if info.file_size > 2_000_000:
                    raise ValueError("source attestation report is oversized")
            elif path.parent.as_posix() == "serie_a_v2_forward_original_sources" and SOURCE_ZIP_RE.fullmatch(basename):
                if info.file_size > 12_000_000:
                    raise ValueError("embedded source ZIP exceeds the source archive limit")
            else:
                raise ValueError(f"unexpected forward artifact member: {name}")
        if len(reports) != 1 or reports[0].file_size > 2_000_000:
            raise ValueError("forward artifact must contain exactly one bounded report JSON")
        report = json.loads(archive.read(reports[0]).decode("utf-8"))
        if not isinstance(report, dict):
            raise ValueError("forward report JSON must be an object")
        return report


def _verify_forward_run(artifact: Mapping[str, Any], token: str, *, get=requests.get) -> dict[str, Any]:
    run = _github_json(f"{GITHUB_API}/actions/runs/{artifact['run_id']}", token, get=get)
    path = str(run.get("path") or "").split("@", 1)[0]
    if (
        run.get("id") != artifact["run_id"]
        or path != FORWARD_WORKFLOW_PATH
        or run.get("name") != FORWARD_WORKFLOW_NAME
        or run.get("head_branch") != "main"
        or run.get("head_sha") != artifact["head_sha"]
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or run.get("event") not in evaluator._ALLOWED_FORWARD_EVENTS
    ):
        raise ValueError("forward artifact is not from the exact successful main original-V2 workflow")
    created = _utc(run.get("created_at"), "forward run created_at")
    completed = _utc(run.get("updated_at"), "forward run updated_at")
    if not created <= artifact["created_at"] <= completed:
        raise ValueError("forward artifact was created outside its successful parent run")
    for path, expected in FORWARD_CODE_BLOBS.items():
        _verify_blob(token, artifact["head_sha"], path, expected, get=get)
    return {
        "id": artifact["run_id"],
        "path": FORWARD_WORKFLOW_PATH,
        "name": FORWARD_WORKFLOW_NAME,
        "head_branch": "main",
        "head_sha": artifact["head_sha"],
        "event": run["event"],
        "status": "completed",
        "conclusion": "success",
        "created_at_utc": created.isoformat(),
        "completed_at_utc": completed.isoformat(),
    }


def _artifact_metadata(
    artifact: Mapping[str, Any], *, name: str, parent_run: Mapping[str, Any],
    zip_verified: bool, code_verified: bool,
) -> dict[str, Any]:
    return {
        "artifact_id": artifact["artifact_id"],
        "name": name,
        "sha256": artifact["sha256"],
        "zip_sha256_verified": zip_verified,
        "run_metadata_verified": True,
        "code_contract_verified": code_verified,
        "created_at_utc": artifact["created_at"].isoformat(),
        "parent_run": dict(parent_run),
    }


def _verify_source_artifact(
    source_info: Mapping[str, Any],
    rows: list[Mapping[str, Any]],
    *,
    token: str,
    get=requests.get,
) -> dict[str, Any]:
    quote_times = [_utc(row.get("quote_time_utc"), "quote_time_utc") for row in rows]
    if not quote_times:
        raise ValueError("source artifact cannot be verified without a quote")
    earliest, latest = min(quote_times), max(quote_times)
    source_run = _github_json(f"{GITHUB_API}/actions/runs/{source_info['run_id']}", token, get=get)
    path = str(source_run.get("path") or "").split("@", 1)[0]
    if (
        source_run.get("id") != source_info["run_id"]
        or path != SOURCE_WORKFLOW_PATH
        or source_run.get("name") != SOURCE_WORKFLOW_NAME
        or source_run.get("head_branch") != "main"
        or source_run.get("head_sha") != source_info["head_sha"]
        or source_run.get("status") != "completed"
        or source_run.get("conclusion") != "success"
        or source_run.get("event") not in evaluator._ALLOWED_SOURCE_EVENTS
    ):
        raise ValueError("source artifact is not from the exact successful main free diagnostic")
    parent = verify_source_run(
        dict(source_info), quote_time=earliest, token=token, get=get
    )
    created = _utc(source_run.get("created_at"), "source run created_at")
    completed = _utc(source_run.get("updated_at"), "source run updated_at")
    if not created <= source_info["created_at"] <= completed < earliest:
        raise ValueError("source artifact and successful source workflow must precede every quote")
    raw = get_archive(source_info["artifact_id"], token=token, get=get)
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != source_info["sha256"]:
        raise ValueError("source artifact ZIP SHA-256 differs from GitHub metadata")
    quote_payloads = [{
        "league": evaluator.PRIMARY_LEAGUE,
        "event_id": row["event_id"],
        "snapshot_time_utc": row["quote_time_utc"],
        "commence_time_utc": row["kickoff_utc"],
    } for row in rows]
    with tempfile.TemporaryDirectory() as directory:
        archive_path = Path(directory) / "original-v2-source.zip"
        archive_path.write_bytes(raw)
        gate = verify_archive(
            archive_path,
            quote_payloads,
            as_of_utc=latest,
            github_artifact_sha256=source_info["sha256"],
            github_artifact_created_at_utc=source_info["created_at"].isoformat(),
        )
    if (
        gate.get("github_digest_matched") is not True
        or gate.get("archived_csv_count") != 10
        or gate.get("source_archive_prequote_ready") != len(rows)
        or gate.get("eligible_for_frozen_prospective_cohort") is not False
        or gate.get("no_bet") is not True
    ):
        raise ValueError("source ZIP failed the original V2 prequote source gate")
    run_meta = {
        "id": source_info["run_id"],
        "path": SOURCE_WORKFLOW_PATH,
        "name": SOURCE_WORKFLOW_NAME,
        "head_branch": "main",
        "head_sha": source_info["head_sha"],
        "event": source_run["event"],
        "status": "completed",
        "conclusion": "success",
        "created_at_utc": created.isoformat(),
        "completed_at_utc": completed.isoformat(),
    }
    if (
        parent.get("run_id") != run_meta["id"]
        or parent.get("run_head_sha") != run_meta["head_sha"]
        or parent.get("workflow_path") != SOURCE_WORKFLOW_PATH
        or parent.get("source_loader_blob_sha1") != evaluator.SOURCE_LOADER_BLOB_SHA1
        or parent.get("source_rights_helper_blob_sha1") != evaluator.SOURCE_RIGHTS_HELPER_BLOB_SHA1
        or parent.get("source_rights_manifest_blob_sha1") != evaluator.SOURCE_RIGHTS_MANIFEST_BLOB_SHA1
    ):
        raise ValueError("source workflow code-contract attestation differs from the frozen evaluator")
    metadata = _artifact_metadata(
        source_info, name=SOURCE_ARTIFACT_NAME, parent_run=run_meta,
        zip_verified=True, code_verified=True,
    )
    return metadata


def _canonical_raw_aliases(canonical: str) -> list[str]:
    aliases = {canonical}
    for raw in SERIE_A_RUNTIME_CONFIG.aliases:
        try:
            if evaluator._canonical_team(raw) == canonical:
                aliases.add(raw)
        except ValueError:
            continue
    if canonical == "Atalanta":
        aliases.add("Atalanta BC")
    return sorted(aliases)


def read_completed_fixture_gate(client: Any, *, now: datetime) -> tuple[set[tuple[str, str, str]], dict[str, Any]]:
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("completed-fixture gate clock must have a real UTC offset")
    captured = now.astimezone(timezone.utc)
    cutoff = captured.date().isoformat()
    identities: set[tuple[str, str, str]] = set()
    for page in range(MAX_IDENTITY_PAGES):
        start = page * IDENTITY_PAGE_SIZE
        response = (
            client.table("league_finished_results")
            .select("match_date,home_team,away_team")
            .eq("league", evaluator.PRIMARY_LEAGUE)
            .eq("season", evaluator.PRIMARY_SEASON)
            .lt("match_date", cutoff)
            .range(start, start + IDENTITY_PAGE_SIZE - 1)
            .execute()
        )
        rows = getattr(response, "data", None)
        if not isinstance(rows, list):
            raise ValueError("identity-only Supabase gate returned malformed rows")
        for row in rows:
            if not isinstance(row, Mapping) or set(row) != {"match_date", "home_team", "away_team"}:
                raise ValueError("identity gate returned columns outside its frozen allowlist")
            identities.add(evaluator._fixture_identity(row["match_date"], row["home_team"], row["away_team"]))
        if len(rows) < IDENTITY_PAGE_SIZE:
            break
    else:
        raise ValueError("completed-fixture identity query reached its frozen page bound")
    attestation = {
        "schema_version": "MARKET_ANCHOR_1X2_V2_COMPLETED_FIXTURE_IDENTITY_GATE_V1",
        "source_table": evaluator.COMPLETED_FIXTURE_GATE_SOURCE_TABLE,
        "selected_columns": list(evaluator.COMPLETED_FIXTURE_GATE_COLUMNS),
        "league": evaluator.PRIMARY_LEAGUE,
        "season": evaluator.PRIMARY_SEASON,
        "query_contract_id": evaluator.COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_ID,
        "query_contract_sha256": evaluator.COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256,
        "captured_at_utc": captured.isoformat(),
        "cutoff_date_exclusive_utc": cutoff,
        "completed_fixture_identity_count": len(identities),
        "completed_fixture_identity_sha256": evaluator._sha_fixture_set(identities),
        "outcome_columns_selected": False,
        "target_outcomes_read": False,
    }
    evaluator._validate_completed_gate(identities, attestation)
    return identities, attestation


def _read_exact_outcomes(
    client: Any,
    identities: tuple[tuple[str, str, str], ...],
    kickoff_by_identity: Mapping[tuple[str, str, str], str],
    *,
    observed_at_utc: datetime,
) -> dict[tuple[str, str, str], dict[str, str]]:
    if not identities or not isinstance(kickoff_by_identity, Mapping):
        raise ValueError("post-gate outcome reader requires exact forecast-bound identities")
    if (
        not isinstance(observed_at_utc, datetime)
        or observed_at_utc.tzinfo is None
        or observed_at_utc.utcoffset() is None
    ):
        raise ValueError("outcome observation clock must have a real UTC offset")
    observed_at = observed_at_utc.astimezone(timezone.utc)
    result: dict[tuple[str, str, str], dict[str, str]] = {}
    for identity in identities:
        if identity not in kickoff_by_identity:
            raise ValueError("outcome request contains an identity without a frozen V2 forecast")
        kickoff = _utc(kickoff_by_identity[identity], "forecast kickoff")
        match_date, home, away = identity
        response = (
            client.table("league_finished_results")
            .select("match_date,home_team,away_team,result,persisted_at_utc")
            .eq("league", evaluator.PRIMARY_LEAGUE)
            .eq("season", evaluator.PRIMARY_SEASON)
            .eq("match_date", match_date)
            .in_("home_team", _canonical_raw_aliases(home))
            .in_("away_team", _canonical_raw_aliases(away))
            .execute()
        )
        rows = getattr(response, "data", None)
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"no persisted result found for gated fixture {identity!r}")
        labels: set[str] = set()
        persisted: list[datetime] = []
        for row in rows:
            if not isinstance(row, Mapping) or set(row) != {
                "match_date", "home_team", "away_team", "result", "persisted_at_utc"
            }:
                raise ValueError("post-gate result query returned fields outside the exact allowlist")
            if evaluator._fixture_identity(row["match_date"], row["home_team"], row["away_team"]) != identity:
                raise ValueError("post-gate result query returned a different fixture identity")
            persisted_at = _utc(row["persisted_at_utc"], "persisted_at_utc")
            if persisted_at <= kickoff:
                raise ValueError("result persistence must be strictly later than kickoff")
            if persisted_at > observed_at:
                raise ValueError("result persistence cannot be later than the evaluation observation time")
            label = row["result"]
            if not isinstance(label, str) or label not in {"H", "D", "A"}:
                raise ValueError("post-gate result label is malformed")
            labels.add(label)
            persisted.append(persisted_at)
        if len(labels) != 1:
            raise ValueError("duplicate raw team aliases disagree on the 1X2 result")
        result[identity] = {
            "result": next(iter(labels)),
            "persisted_at_utc": max(persisted).isoformat(),
        }
    return result


def run_live(
    *,
    token: str,
    current_sha: str,
    client_factory: Callable[[], Any],
    now: datetime | None = None,
    get=requests.get,
    rights_check: Callable[[], Mapping[str, Any]] = require_personal_research_inference_scope,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("runner clock must have a real UTC offset")
    at = now.astimezone(timezone.utc)
    base = {
        "schema_version": "MARKET_ANCHOR_1X2_V2_ORIGINAL_MARKET_ONLY_SECONDARY_RUNNER_V1",
        "run_at_utc": at.isoformat(),
        "candidate_sha256": evaluator.CANDIDATE_SHA256,
        "policy_id": evaluator.POLICY_ID,
        "active_lambda": 0.0,
        "shadow_residual_lambda": 1.0,
        "no_bet": True,
        "automatic_promotion": False,
        "production_writes": 0,
        "supabase_writes": 0,
        "paid_provider_calls": 0,
        "target_outcomes_read": False,
        "outcomes_scored": False,
    }

    # This local permission check must precede every GitHub or Supabase request.
    try:
        rights = dict(rights_check())
    except PermissionError as exc:
        blocked = write_research_scope_blocked_report(
            Path("artifacts/market_anchor_v2_original_secondary_evaluation.json"),
            "MARKET_ANCHOR_1X2_V2_ORIGINAL_MARKET_ONLY_SECONDARY",
            str(exc),
        )
        return {**base, **blocked, "status": "SOURCE_RIGHTS_BLOCKED_NO_EXTERNAL_READ"}

    verify_current_main_contract(token, current_sha, get=get)
    artifacts = discover_forward_artifacts(token, now=at, get=get)
    if not artifacts:
        return {
            **base, "status": "NO_POST_FREEZE_FORWARD_ARTIFACTS",
            "forward_artifact_count": 0, "eligible_forecast_count": 0,
            "target_outcomes_read": False, "outcomes_scored": False,
            "source_rights": rights,
        }

    source_by_id: dict[int, dict[str, Any]] | None = None
    source_meta_cache: dict[int, dict[str, Any]] = {}
    normalized_rows: list[dict[str, Any]] = []
    forward_artifact_ids: list[int] = []

    for artifact in artifacts:
        parent = _verify_forward_run(artifact, token, get=get)
        raw = _download_zip(
            artifact["artifact_id"], token,
            max_bytes=MAX_FORWARD_ARTIFACT_BYTES, get=get,
        )
        if hashlib.sha256(raw).hexdigest() != artifact["sha256"]:
            raise ValueError("forward artifact ZIP SHA-256 differs from GitHub metadata")
        report = _extract_forward_report(raw)
        eligible_rows = [
            row for row in report.get("rows", [])
            if isinstance(row, Mapping)
            and row.get("status") == "SOURCE_BEFORE_QUOTE_V2_DIAGNOSTIC_ONLY"
        ]
        needed_ids = {
            row.get("source_artifact_id") for row in eligible_rows
            if type(row.get("source_artifact_id")) is int
        }
        if needed_ids and source_by_id is None:
            source_by_id = {item["artifact_id"]: item for item in discover_archives(token=token, get=get)}
        for source_id in needed_ids:
            if source_by_id is None or source_id not in source_by_id:
                raise ValueError("forward report references a source artifact absent from GitHub metadata")
            grouped = [row for row in eligible_rows if row.get("source_artifact_id") == source_id]
            # Revalidate the source ZIP against every forward report that uses it.
            # A later artifact may contain an earlier quote timestamp.
            source_meta_cache[source_id] = _verify_source_artifact(
                source_by_id[source_id], grouped, token=token, get=get
            )
        forward_meta = {
            "artifact_id": artifact["artifact_id"],
            "name": FORWARD_ARTIFACT_NAME,
            "sha256": artifact["sha256"],
            "zip_sha256_verified": True,
            "run_metadata_verified": True,
            "code_contract_verified": True,
            "created_at_utc": artifact["created_at"].isoformat(),
            "parent_run": parent,
        }
        normalized_rows.extend(evaluator.normalize_original_forward_report(
            report,
            forward_artifact_metadata=forward_meta,
            source_artifacts_by_id=source_meta_cache,
        ))
        forward_artifact_ids.append(artifact["artifact_id"])

    selected = evaluator.select_first_eligible_forecast_per_fixture(normalized_rows)
    base.update({
        "forward_artifact_count": len(forward_artifact_ids),
        "forward_artifact_ids": forward_artifact_ids,
        "source_artifact_ids": sorted(source_meta_cache),
        "eligible_forecast_count": len(selected),
        "source_before_quote_verified_forecasts": len(selected),
        "source_rights": rights,
    })
    if not selected:
        return {
            **base, "status": "NO_SOURCE_BEFORE_QUOTE_FORECASTS",
            "completed_primary_fixture_identities": 0,
            "eligible_completed_forecasts": 0,
            "target_outcomes_read": False, "outcomes_scored": False,
        }

    # Only now create the read-only Supabase client and query identity metadata.
    client = client_factory()
    completed, attestation = read_completed_fixture_gate(client, now=at)
    kickoff_by_identity = {
        tuple(row["fixture_identity"]): row["kickoff_utc"] for row in selected
    }

    def lazy_outcome_loader(identities):
        return _read_exact_outcomes(
            client, identities, kickoff_by_identity, observed_at_utc=at
        )

    evaluated = evaluator.evaluate_market_only_secondary_cohort(
        selected,
        completed_fixture_identities=completed,
        completed_gate_attestation=attestation,
        load_outcomes=lazy_outcome_loader,
    )
    return {
        **base,
        **evaluated,
        "status": evaluated["status"],
        "completed_fixture_gate_attestation": attestation,
        "target_outcomes_read": evaluated.get("target_outcomes_read") is True,
        "outcomes_scored": evaluated.get("outcomes_scored") is True,
        "superiority_claim_permitted": False,
        "source_rights": rights,
    }



def _write_json_report(path: Path, report: Mapping[str, Any]) -> None:
    """Write a parseable UTF-8 JSON report with a real terminal newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True)
    path.write_text(payload + "\n", encoding="utf-8")

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise RuntimeError("runner must execute in the original GitHub repository")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("live secondary evaluation is main-only")
    token = os.environ.get("GITHUB_TOKEN", "")
    current_sha = os.environ.get("GITHUB_SHA", "")
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_KEY", "")
    if not token or not supabase_url or not supabase_key:
        raise RuntimeError("GitHub actions:read and read-only Supabase credentials are required")
    report = run_live(
        token=token,
        current_sha=current_sha,
        client_factory=lambda: create_client(supabase_url, supabase_key),
    )
    _write_json_report(args.output, report)
    print(json.dumps({
        key: report.get(key) for key in (
            "status", "forward_artifact_count", "eligible_forecast_count",
            "completed_primary_fixture_identities", "eligible_completed_forecasts",
            "target_outcomes_read", "outcomes_scored", "no_bet",
            "automatic_promotion", "supabase_writes", "paid_provider_calls",
        )
    }, sort_keys=True))


if __name__ == "__main__":
    main()
