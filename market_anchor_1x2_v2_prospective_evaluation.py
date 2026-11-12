"""Read-only bridge from authenticated GitHub forward artifacts to V2 market evaluation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any, Mapping
from zipfile import BadZipFile, ZipFile

import requests

import market_anchor_1x2_v2_prospective_evaluator as evaluator
from market_anchor_1x2_v2_forward_artifact_adapter import (
    FORWARD_WORKFLOW_NAME,
    FORWARD_WORKFLOW_PATH,
    normalize_forward_report,
    select_first_eligible_forecasts,
)
from market_anchor_1x2_v2_prospective_runner import (
    _forecast_kickoff_lookup,
    _read_exact_completed_outcomes,
    evaluate_live_market_only_prospective_cohort,
)
from market_anchor_v2_source_rights import require_personal_research_inference_scope, write_research_scope_blocked_report
from market_anchor_v2_artifact_privacy import require_private_repository_for_source_artifacts
from serie_a_v2_current_form_forward_capture import (
    GITHUB_API,
    REPOSITORY,
    _current_gate_freshness,
    discover_archives,
    get_archive,
    verify_and_load_archive,
    verify_source_run,
)

FORWARD_ARTIFACT_NAME = "serie-a-v2-current-form-forward-preview"
FORWARD_REPORT_BASENAME = "serie_a_v2_current_form_forward_preview.json"
MAX_ARTIFACT_BYTES = 2_000_000
MAX_TOTAL_DOWNLOAD_BYTES = 64_000_000
MAX_UNCOMPRESSED_BYTES = 16_000_000
MAX_MEMBERS = 32
MAX_PAGES = 3
PER_PAGE = 100
ALLOWED_EVENTS = {"schedule", "workflow_dispatch", "workflow_run"}
SOURCE_ZIP_RE = re.compile(r"current-form-source-artifact-(\d+)\.zip\Z")
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")


def _utc(value: Any, field: str) -> datetime:
    return evaluator._utc(value, field)


def _github_json(url: str, token: str, get=requests.get) -> dict[str, Any]:
    if not url.startswith(GITHUB_API + "/"):
        raise ValueError("GitHub API URL is outside the configured repository")
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
    status = getattr(response, "status_code", None)
    if status != 200:
        raise RuntimeError(f"GitHub API request failed with HTTP {status}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("GitHub API response must be an object")
    return payload


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} is missing")
    digest = value.removeprefix("sha256:")
    if SHA256_RE.fullmatch(digest) is None:
        raise ValueError(f"{field} is malformed")
    return digest


def discover_forward_artifacts(token: str, *, get=requests.get) -> list[dict[str, Any]]:
    if not token:
        raise ValueError("GITHUB_TOKEN is required")
    cohort_start = evaluator.COHORT_FROZEN_AT_UTC
    found, seen = [], set()
    page_count = 0
    for page in range(1, MAX_PAGES + 1):
        payload = _github_json(
            f"{GITHUB_API}/actions/artifacts?name={FORWARD_ARTIFACT_NAME}&per_page={PER_PAGE}&page={page}",
            token, get=get,
        )
        items = payload.get("artifacts")
        if not isinstance(items, list):
            raise ValueError("GitHub forward-artifact listing is malformed")
        page_count = len(items)
        for item in items:
            if not isinstance(item, Mapping) or item.get("name") != FORWARD_ARTIFACT_NAME:
                continue
            if item.get("expired") is True:
                continue
            run_meta = item.get("workflow_run")
            if not isinstance(run_meta, Mapping) or run_meta.get("head_branch") != "main":
                continue
            artifact_id, run_id = item.get("id"), run_meta.get("id")
            if type(artifact_id) is not int or artifact_id <= 0 or type(run_id) is not int or run_id <= 0:
                raise ValueError("forward artifact or run ID is malformed")
            if artifact_id in seen:
                raise ValueError("GitHub returned a duplicate forward artifact ID")
            seen.add(artifact_id)
            size = item.get("size_in_bytes")
            if type(size) is not int or size <= 0 or size > MAX_ARTIFACT_BYTES:
                raise ValueError("forward artifact size exceeds the frozen bound")
            created = _utc(item.get("created_at"), "forward artifact created_at")
            if created < cohort_start:
                continue
            head_sha = run_meta.get("head_sha")
            if not isinstance(head_sha, str) or SHA1_RE.fullmatch(head_sha) is None:
                raise ValueError("forward artifact parent head SHA is malformed")
            found.append({
                "artifact_id": artifact_id, "run_id": run_id, "head_sha": head_sha,
                "sha256": _digest(item.get("digest"), "forward artifact digest"),
                "size_in_bytes": size, "created_at": created, "created_at_utc": created.isoformat(),
            })
        if page_count < PER_PAGE:
            break
    else:
        if page_count == PER_PAGE:
            raise ValueError("forward artifact scan reached its 300-artifact safety bound")
    return sorted(found, key=lambda item: (item["created_at"], item["artifact_id"]))


def verify_forward_run(artifact: Mapping[str, Any], token: str, *, get=requests.get) -> dict[str, Any]:
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
        or run.get("event") not in ALLOWED_EVENTS
    ):
        raise ValueError("artifact is not from the exact successful main V2 forward workflow")
    created = _utc(run.get("created_at"), "forward run created_at")
    completed = _utc(run.get("updated_at"), "forward run updated_at")
    if not created <= artifact["created_at"] <= completed:
        raise ValueError("forward artifact creation is outside its parent run interval")
    return {
        "run_id": artifact["run_id"], "head_sha": run["head_sha"], "head_branch": "main",
        "path": path, "name": run["name"], "status": "completed", "conclusion": "success",
        "event": run["event"], "run_created_at_utc": created.isoformat(),
        "run_completed_at_utc": completed.isoformat(),
        "artifact_created_at_utc": artifact["created_at"].isoformat(),
    }


def extract_forward_artifact(raw: bytes) -> tuple[dict[str, Any], dict[int, bytes]]:
    try:
        archive = ZipFile(BytesIO(raw))
    except BadZipFile as exc:
        raise ValueError("forward artifact is not a valid ZIP") from exc
    with archive:
        infos = archive.infolist()
        if len(infos) > MAX_MEMBERS:
            raise ValueError("forward artifact contains too many ZIP members")
        total, names, report_infos, embedded = 0, set(), [], {}
        for info in infos:
            name = info.filename
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name:
                raise ValueError("forward artifact contains an unsafe ZIP member path")
            if info.is_dir():
                continue
            if info.flag_bits & 0x1 or name in names:
                raise ValueError("encrypted or duplicate forward artifact ZIP member")
            names.add(name)
            total += info.file_size
            if info.file_size < 0 or total > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("forward artifact exceeds the uncompressed size bound")
            basename = path.name
            if basename == FORWARD_REPORT_BASENAME:
                report_infos.append(info)
                continue
            match = SOURCE_ZIP_RE.fullmatch(basename)
            if match is None:
                raise ValueError(f"unexpected forward artifact member: {name}")
            source_id = int(match.group(1))
            if source_id in embedded:
                raise ValueError("duplicate embedded source artifact ID")
            embedded[source_id] = archive.read(info)
        if len(report_infos) != 1 or report_infos[0].file_size > 2_000_000:
            raise ValueError("forward artifact must contain exactly one bounded report JSON")
        report = json.loads(archive.read(report_infos[0]).decode("utf-8"))
        if not isinstance(report, dict):
            raise ValueError("forward report JSON must contain an object")
        return report, embedded


def verify_source_artifacts_for_candidates(
    candidates: list[dict[str, Any]], *, token: str,
    current_gate_identities: set[tuple[str, str, str]],
) -> dict[int, str]:
    if not candidates:
        return {}
    source_by_id = {item["artifact_id"]: item for item in discover_archives(token=token)}
    groups, embedded_by_id = {}, {}
    for candidate in candidates:
        row, provenance = candidate["row"], candidate["provenance"]
        source_id = row["source_artifact_id"]
        embedded = provenance.get("embedded_source_zip_bytes")
        if not isinstance(embedded, bytes) or not embedded:
            raise ValueError("forward artifact is missing the exact embedded source ZIP")
        if source_id in embedded_by_id and embedded_by_id[source_id] != embedded:
            raise ValueError("same source artifact ID has different embedded ZIP bytes")
        embedded_by_id[source_id] = embedded
        groups.setdefault(source_id, []).append(candidate)

    verified_shas = {}
    for source_id, group in groups.items():
        source_info = group[0]["provenance"]["source_artifact_info"]
        if any(item["provenance"]["source_artifact_info"] != source_info for item in group):
            raise ValueError("same source artifact ID has conflicting forward provenance")
        parent_report = source_info["parent_run"]
        archive_meta = source_by_id.get(source_id)
        if archive_meta is None:
            raise ValueError("referenced source artifact is absent from GitHub artifact metadata")
        if (
            archive_meta["sha256"] != source_info["artifact_sha256"]
            or archive_meta["run_id"] != parent_report["run_id"]
            or archive_meta["head_sha"] != parent_report["run_head_sha"]
            or archive_meta["created_at"] != _utc(source_info["source_archive_created_at_utc"], "source archive created_at")
        ):
            raise ValueError("source artifact metadata differs from forward provenance")
        raw = embedded_by_id[source_id]
        actual_sha = hashlib.sha256(raw).hexdigest()
        if actual_sha != archive_meta["sha256"]:
            raise ValueError("embedded source ZIP SHA256 differs from GitHub source artifact digest")
        earliest_quote = min(_utc(item["row"]["quote_time_utc"], "quote_time_utc") for item in group)
        parent = verify_source_run(archive_meta, quote_time=earliest_quote, token=token)
        if (
            parent.get("run_id") != parent_report.get("run_id")
            or parent.get("run_head_sha") != parent_report.get("run_head_sha")
            or parent.get("workflow_path") != parent_report.get("workflow_path")
            or _utc(parent.get("run_created_at_utc"), "source run created_at") != _utc(parent_report.get("run_created_at_utc"), "reported source run created_at")
            or _utc(parent.get("run_completed_at_utc"), "source run completed_at") != _utc(parent_report.get("run_completed_at_utc"), "reported source run completed_at")
        ):
            raise ValueError("source parent-run provenance differs from live GitHub run")
        _, verified = verify_and_load_archive(raw, archive_meta, parent)
        manifest = verified.get("manifest")
        gate = manifest.get("feature_source_gate") if isinstance(manifest, Mapping) else None
        attestation = verified.get("feature_source_gate_attestation")
        if not isinstance(gate, Mapping) or not isinstance(attestation, Mapping) or attestation.get("verified") is not True:
            raise ValueError("source archive lacks the post-integration fixture-identity attestation")
        gate_count = attestation.get("gate_fixture_identity_count")
        current_count = attestation.get("current_source_fixture_identity_count")
        if (
            type(gate_count) is not int or gate_count < 30
            or gate.get("gate_fixture_identity_count") != gate_count
            or not isinstance(gate.get("gate_fixture_identities"), list)
            or len(gate["gate_fixture_identities"]) != gate_count
            or gate.get("gate_fixture_identity_sha256") != attestation.get("gate_fixture_identity_sha256")
            or attestation.get("gate_fixture_identities_covered_by_current_source") != gate_count
            or attestation.get("gate_fixture_identities_missing_from_current_source") != 0
            or type(current_count) is not int or current_count < gate_count
            or not isinstance(attestation.get("gate_fixture_identity_sha256"), str)
            or SHA256_RE.fullmatch(attestation["gate_fixture_identity_sha256"]) is None
            or not isinstance(attestation.get("current_source_fixture_identity_sha256"), str)
            or SHA256_RE.fullmatch(attestation["current_source_fixture_identity_sha256"]) is None
        ):
            raise ValueError("source archive fixture-identity attestation is missing or inconsistent")
        if (
            verified.get("artifact_sha256") != source_info["artifact_sha256"]
            or _utc(verified.get("archive_created_at_utc"), "verified archive created_at") != _utc(source_info["source_archive_created_at_utc"], "reported archive created_at")
            or _utc(verified.get("latest_source_observed_at_utc"), "verified source observation") != _utc(source_info["latest_source_observed_at_utc"], "reported source observation")
        ):
            raise ValueError("verified source archive differs from forward provenance")
        for candidate in group:
            quote = _utc(candidate["row"]["quote_time_utc"], "quote_time_utc")
            freshness = _current_gate_freshness(
                current_gate_identities, verified, before_date_exclusive=quote.date().isoformat()
            )
            if freshness.get("fresh") is not True:
                raise ValueError("source archive did not cover completed-fixture identities before quote")
        verified_shas[source_id] = actual_sha
    return verified_shas


def run_live_evaluation(client: Any, token: str, *, now: datetime | str | None = None):
    # Defense in depth: imported callers must not bypass the CLI rights gate.
    require_personal_research_inference_scope()
    actual_now = datetime.now(timezone.utc)
    if not isinstance(actual_now, datetime) or actual_now.tzinfo is None or actual_now.utcoffset() is None:
        raise ValueError("system evaluation clock must have a real UTC offset")
    actual_now = actual_now.astimezone(timezone.utc)
    if now is None:
        now = actual_now
    elif isinstance(now, datetime):
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("evaluation observation clock must have a real UTC offset")
        now = now.astimezone(timezone.utc)
    else:
        now = evaluator._utc(now, "evaluation observation clock")
    if now > actual_now:
        raise ValueError("evaluation observation clock cannot be later than the actual current UTC clock")
    now = now.astimezone(timezone.utc)
    observed_at_utc = now.isoformat().replace("+00:00", "Z")
    base = {
        "schema_version": "MARKET_ANCHOR_1X2_V2_PROSPECTIVE_MARKET_EVALUATION_RUN_V1",
        "run_at_utc": now.astimezone(timezone.utc).isoformat(),
        "candidate_sha256": evaluator.FROZEN_CANDIDATE_SHA256,
        "no_bet": True, "automatic_promotion": False,
        "production_or_supabase_writes": 0, "paid_provider_calls": 0,
        "raw_outcomes_included": False,
        "private_storage_verified": False,
    }
    private_storage = require_private_repository_for_source_artifacts(
        os.environ.get("GITHUB_REPOSITORY", ""), token
    )
    base["private_storage_verified"] = private_storage["private"] is True
    base["private_storage_policy"] = private_storage["storage_policy"]
    artifacts = discover_forward_artifacts(token)
    if not artifacts:
        return {**base, "status": "NO_FORWARD_ARTIFACTS", "forward_artifact_count": 0,
                "forecast_candidate_count": 0, "selected_unique_fixture_forecasts": 0,
                "target_outcomes_read": False, "target_outcomes_scored": False}

    total_bytes, candidates, artifact_reports = 0, [], []
    for artifact in artifacts:
        run = verify_forward_run(artifact, token)
        raw = get_archive(artifact["artifact_id"], token=token)
        total_bytes += len(raw)
        if len(raw) > MAX_ARTIFACT_BYTES or total_bytes > MAX_TOTAL_DOWNLOAD_BYTES:
            raise ValueError("forward artifact downloads exceeded the bounded byte budget")
        if hashlib.sha256(raw).hexdigest() != artifact["sha256"]:
            raise ValueError("forward artifact ZIP SHA256 differs from GitHub artifact digest")
        report, embedded = extract_forward_artifact(raw)
        normalized = normalize_forward_report(
            report, forward_artifact_id=artifact["artifact_id"], forward_run=run
        )
        for candidate in normalized:
            source_id = candidate["row"]["source_artifact_id"]
            if source_id not in embedded:
                raise ValueError("forward artifact omitted a source ZIP referenced by a captured row")
            candidate["provenance"]["embedded_source_zip_bytes"] = embedded[source_id]
            candidate["provenance"]["forward_artifact_sha256"] = artifact["sha256"]
        candidates.extend(normalized)
        artifact_reports.append({
            "artifact_id": artifact["artifact_id"], "run_id": run["run_id"],
            "head_sha": run["head_sha"], "artifact_sha256": artifact["sha256"],
            "artifact_created_at_utc": artifact["created_at_utc"],
            "captured_rows": len(normalized),
        })

    if not candidates:
        return {**base, "status": "NO_ELIGIBLE_FORECASTS",
                "forward_artifact_count": len(artifacts), "forward_artifacts": artifact_reports,
                "forecast_candidate_count": 0, "selected_unique_fixture_forecasts": 0,
                "target_outcomes_read": False, "target_outcomes_scored": False}

    selected, selection = select_first_eligible_forecasts(candidates)
    selected_rows, kickoff_by_identity = _forecast_kickoff_lookup(
        [item["row"] for item in selected]
    )
    outcome_state = {"called": False}
    verified_shas: dict[int, str] = {}

    def verify_source_preflight(completed_identities, gate_attestation):
        # The runner supplies the one freshly read, immutable identity snapshot
        # that the evaluator will also use for its frozen 30-forecast gate.
        # Source verification remains metadata-only and runs before any outcome
        # callback can be invoked.
        verified_shas.update(verify_source_artifacts_for_candidates(
            candidates,
            token=token,
            current_gate_identities=set(completed_identities),
        ))
        return {
            "verified": True,
            "source_archive_sha256": {str(k): v for k, v in sorted(verified_shas.items())},
            "verified_source_archive_count": len(verified_shas),
            "gate_fixture_identity_count": len(completed_identities),
            "gate_fixture_identity_sha256": evaluator._sha_fixture_set(completed_identities),
        }

    def lazy_outcome_loader(
        identities,
        *,
        completed_fixture_identities,
        completed_fixture_gate_attestation,
        source_preflight_attestation,
    ):
        outcome_state["called"] = True
        return _read_exact_completed_outcomes(
            client,
            identities,
            kickoff_by_identity,
            observed_at_utc=observed_at_utc,
            completed_fixture_identities=completed_fixture_identities,
            completed_fixture_gate_attestation=completed_fixture_gate_attestation,
            source_preflight_attestation=source_preflight_attestation,
        )

    try:
        evaluation = evaluate_live_market_only_prospective_cohort(
            client,
            selected_rows,
            lazy_outcome_loader,
            preflight=verify_source_preflight,
        )
    except Exception as exc:
        return {
            **base, "status": "BLOCKED", "forward_artifact_count": len(artifacts),
            "forward_artifacts": artifact_reports, "forecast_candidate_count": len(candidates),
            "selected_unique_fixture_forecasts": len(selected), "selection": selection,
            "source_archives_reverified": len(verified_shas),
            "source_archive_sha256": {str(k): v for k, v in sorted(verified_shas.items())},
            "target_outcomes_read": outcome_state["called"], "target_outcomes_scored": False,
            "error_type": type(exc).__name__, "error": str(exc),
        }
    if outcome_state["called"] is not bool(evaluation.get("target_outcomes_read")):
        return {
            **base, "status": "BLOCKED", "forward_artifact_count": len(artifacts),
            "forward_artifacts": artifact_reports, "forecast_candidate_count": len(candidates),
            "selected_unique_fixture_forecasts": len(selected), "selection": selection,
            "source_archives_reverified": len(verified_shas),
            "source_archive_sha256": {str(k): v for k, v in sorted(verified_shas.items())},
            "target_outcomes_read": outcome_state["called"], "target_outcomes_scored": False,
            "error": "outcome-loader invocation differs from evaluator gate attestation",
        }
    return {
        **base, "status": evaluation.get("status", "UNKNOWN"),
        "forward_artifact_count": len(artifacts), "forward_artifacts": artifact_reports,
        "forecast_candidate_count": len(candidates), "selected_unique_fixture_forecasts": len(selected),
        "selection": selection, "source_archives_reverified": len(verified_shas),
        "source_archive_sha256": {str(k): v for k, v in sorted(verified_shas.items())},
        "target_outcomes_read": outcome_state["called"],
        "target_outcomes_scored": bool(evaluation.get("target_outcomes_scored")),
        "evaluation": evaluation,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        require_personal_research_inference_scope()
    except PermissionError as exc:
        report = write_research_scope_blocked_report(
            args.output, "MARKET_ANCHOR_1X2_V2_PROSPECTIVE_EVALUATION", str(exc)
        )
        print(json.dumps(report, sort_keys=True))
        return 0
    try:
        if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY or os.environ.get("GITHUB_REF") != "refs/heads/main":
            raise ValueError("live evaluation is allowed only in the canonical repository on main")
        token, url, key = (os.environ.get(name, "") for name in ("GITHUB_TOKEN", "SUPABASE_URL", "SUPABASE_KEY"))
        if not token or not url or not key:
            raise ValueError("GitHub read token and Supabase read credentials are required")
        require_private_repository_for_source_artifacts(REPOSITORY, token)
        from supabase import create_client
        report = run_live_evaluation(create_client(url, key), token)
    except PermissionError as exc:
        report = {
            "schema_version": "MARKET_ANCHOR_1X2_V2_PROSPECTIVE_MARKET_EVALUATION_RUN_V1",
            "status": "BLOCKED_PRIVATE_STORAGE", "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "candidate_sha256": evaluator.FROZEN_CANDIDATE_SHA256,
            "private_storage_verified": False,
            "target_outcomes_read": False, "target_outcomes_scored": False,
            "no_bet": True, "automatic_promotion": False,
            "production_or_supabase_writes": 0, "paid_provider_calls": 0,
            "raw_outcomes_included": False, "error_type": type(exc).__name__, "error": str(exc),
        }
    except Exception as exc:
        report = {
            "schema_version": "MARKET_ANCHOR_1X2_V2_PROSPECTIVE_MARKET_EVALUATION_RUN_V1",
            "status": "BLOCKED", "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "candidate_sha256": evaluator.FROZEN_CANDIDATE_SHA256,
            "target_outcomes_read": False, "target_outcomes_scored": False,
            "no_bet": True, "automatic_promotion": False,
            "production_or_supabase_writes": 0, "paid_provider_calls": 0,
            "raw_outcomes_included": False, "error_type": type(exc).__name__, "error": str(exc),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report.get("status"),
        "forward_artifact_count": report.get("forward_artifact_count", 0),
        "forecast_candidate_count": report.get("forecast_candidate_count", 0),
        "selected_unique_fixture_forecasts": report.get("selected_unique_fixture_forecasts", 0),
        "target_outcomes_read": report.get("target_outcomes_read"),
        "target_outcomes_scored": report.get("target_outcomes_scored"),
        "private_storage_verified": report.get("private_storage_verified", False),
        "no_bet": report.get("no_bet", True),
    }, sort_keys=True))
    return 1 if report.get("status") == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
