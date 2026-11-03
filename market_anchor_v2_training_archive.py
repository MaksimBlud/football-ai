"""Load the frozen V2 training inputs from an existing GitHub artifact.

This recovery helper makes no Football-Data request, no Supabase request/write,
and never opens the mutable 2026/27 CSV. It accepts only the ten frozen
2016/17--2025/26 CSVs in the successful main Free Real-Quote Diagnostic artifact.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import zipfile
from urllib.parse import urlsplit

import pandas as pd
import requests

from market_anchor_v2_source_rights import (
    DEFAULT_RIGHTS_MANIFEST_PATH,
    require_ai_model_training_permission,
)

REPOSITORY = "MaksimBlud/football-ai"
API_BASE = f"https://api.github.com/repos/{REPOSITORY}"
SOURCE_WORKFLOW_PATH = ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml"
SOURCE_ARTIFACT_NAME = "serie-a-v2-free-real-quote-diagnostic"
SOURCE_SCRIPT_PATH = "serie_a_v2_live_diagnostic_report.py"
SOURCE_SCRIPT_BLOB_SHA = "932e58a4f93b0d471ac4b4e0c81fa01f923e46d5"
REPORT_NAME = "serie_a_v2_real_quote_diagnostic.json"
SOURCE_DIR = "serie_a_v2_source_capture/"
PUBLIC_BASE = "https://www.football-data.co.uk/mmz4281"
COMPETITION_CODE = "I1"
SEASON_CODES = ("1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526")
CANDIDATE_SHA = "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
TRAINING_CUTOFF = date(2026, 7, 1)
MAX_ARCHIVE_BYTES = 5_000_000
MAX_CSV_BYTES = 2_000_000
MAX_TOTAL_CSV_BYTES = 10_000_000
MAX_REPORT_BYTES = 1_000_000
REQUIRED_COLUMNS = {
    "Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR",
    "HC", "AC", "HY", "AY", "HR", "AR",
}
FORBIDDEN_REPORT_KEYS = {
    "result", "outcome", "home_goals", "away_goals", "score",
    "final_score", "fthg", "ftag", "ftr", "home_score", "away_score",
}


def parse_utc(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be an explicit UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} is not a valid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def _reject_report_outcome_fields(value, path: str = "report") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).strip().lower() in FORBIDDEN_REPORT_KEYS:
                raise ValueError(f"source diagnostic report contains protected outcome field: {path}.{key}")
            _reject_report_outcome_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_report_outcome_fields(child, f"{path}[{index}]")


def _github_json(url: str, *, token: str, get=requests.get) -> dict:
    response = get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("GitHub API returned a non-object response")
    return payload


def verify_parent_source_code(*, run: dict, token: str, get=requests.get) -> str:
    """Pin the source-download implementation used by the artifact parent run.

    The historical-only report records the requested URL, but older code could
    follow redirects without recording the final response URL. Require the exact
    no-redirect implementation introduced by the V2 source-provenance PR before
    any historical artifact bytes can be used for recovery.
    """
    head_sha = run.get("head_sha")
    if not isinstance(head_sha, str) or re.fullmatch(r"[0-9a-f]{40}", head_sha) is None:
        raise ValueError("training source parent run has an invalid head SHA")
    url = f"{API_BASE}/contents/{SOURCE_SCRIPT_PATH}?ref={head_sha}"
    payload = _github_json(url, token=token, get=get)
    if (
        payload.get("path") != SOURCE_SCRIPT_PATH
        or payload.get("type") != "file"
        or payload.get("sha") != SOURCE_SCRIPT_BLOB_SHA
    ):
        raise ValueError(
            "training source parent does not contain the frozen direct-URL no-redirect fetch implementation"
        )
    return SOURCE_SCRIPT_BLOB_SHA


def _download_artifact_zip(artifact_id: int, *, token: str, get=requests.get) -> bytes:
    if type(artifact_id) is not int or artifact_id <= 0:
        raise ValueError("invalid GitHub training artifact id")
    response = get(
        f"{API_BASE}/actions/artifacts/{artifact_id}/zip",
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
        response.raise_for_status()
        final = urlsplit(getattr(response, "url", ""))
        if (
            final.scheme != "https"
            or not final.hostname
            or final.username is not None
            or final.password is not None
            or not (
                final.hostname == "github.com"
                or final.hostname.endswith(".githubusercontent.com")
                or final.hostname.endswith(".actions.githubusercontent.com")
            )
        ):
            raise ValueError("GitHub artifact download ended at an unapproved HTTPS host")
        headers = getattr(response, "headers", {}) or {}
        declared = headers.get("Content-Length")
        if declared is not None:
            if not isinstance(declared, str):
                raise ValueError("invalid GitHub training artifact Content-Length")
            text = declared.strip()
            if not text.isascii() or not text.isdecimal():
                raise ValueError("invalid GitHub training artifact Content-Length")
            if int(text) > MAX_ARCHIVE_BYTES:
                raise ValueError("GitHub training artifact exceeds archive byte limit")
        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            if not isinstance(chunk, bytes):
                raise ValueError("GitHub training artifact yielded a non-bytes chunk")
            total += len(chunk)
            if total > MAX_ARCHIVE_BYTES:
                raise ValueError("GitHub training artifact exceeds archive byte limit")
            chunks.append(chunk)
        raw = b"".join(chunks)
        if not raw:
            raise ValueError("GitHub training artifact ZIP is empty")
        return raw
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            close()


def verify_and_extract_archive(
    raw: bytes,
    *,
    artifact: dict,
    run: dict,
    output_dir: Path,
    now: datetime,
    source_script_blob_sha: str,
    rights_manifest_path: Path = DEFAULT_RIGHTS_MANIFEST_PATH,
    rights_repo_root: Path | None = None,
) -> dict:
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("training archive verification clock must have a real UTC offset")
    now_utc = now.astimezone(timezone.utc)
    source_rights = require_ai_model_training_permission(
        rights_manifest_path, repo_root=rights_repo_root, now=now_utc
    )
    if source_script_blob_sha != SOURCE_SCRIPT_BLOB_SHA:
        raise ValueError("training source code blob is not the frozen direct-URL no-redirect implementation")
    if artifact.get("name") != SOURCE_ARTIFACT_NAME or artifact.get("expired") is not False:
        raise ValueError("training artifact is not the exact unexpired Free Diagnostic artifact")
    artifact_id = artifact.get("id")
    if type(artifact_id) is not int or artifact_id <= 0:
        raise ValueError("training artifact id is invalid")
    if type(artifact.get("size_in_bytes")) is not int or artifact["size_in_bytes"] != len(raw):
        raise ValueError("GitHub training artifact size does not match downloaded ZIP")
    if not raw or len(raw) > MAX_ARCHIVE_BYTES:
        raise ValueError("GitHub training artifact ZIP exceeds the frozen size limit")
    digest_text = artifact.get("digest")
    match = re.fullmatch(r"sha256:([0-9a-f]{64})", digest_text or "")
    if not match:
        raise ValueError("GitHub training artifact has no valid SHA-256 digest")
    archive_sha256 = hashlib.sha256(raw).hexdigest()
    if archive_sha256 != match.group(1):
        raise ValueError("GitHub training artifact SHA-256 mismatch")

    if (
        run.get("path") != SOURCE_WORKFLOW_PATH
        or run.get("head_branch") != "main"
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or run.get("event") not in {"schedule", "workflow_dispatch", "push"}
    ):
        raise ValueError("training artifact parent is not a successful approved main Free Diagnostic run")
    run_id = run.get("id")
    if type(run_id) is not int or run_id <= 0:
        raise ValueError("training artifact parent run id is invalid")
    run_created = parse_utc(run["created_at"], "parent run created_at")
    run_completed = parse_utc(run["updated_at"], "parent run updated_at")
    artifact_created = parse_utc(artifact["created_at"], "artifact created_at")
    if not (run_created <= artifact_created <= run_completed < now_utc):
        raise ValueError("training artifact timestamps do not fit its successful parent run")

    expected_names = {REPORT_NAME}
    expected_names.update(SOURCE_DIR + f"serie_a_{code}.csv" for code in SEASON_CODES)
    extracted: dict[str, bytes] = {}
    audits: dict[str, dict] = {}
    with zipfile.ZipFile(BytesIO(raw), "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(expected_names) or set(names) != expected_names:
            raise ValueError("training artifact must contain exactly the ten frozen old-season CSVs and one report")
        total_csv_bytes = 0
        for info in infos:
            if info.is_dir() or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("training artifact contains a directory or symbolic link")
            limit = MAX_REPORT_BYTES if info.filename == REPORT_NAME else MAX_CSV_BYTES
            if info.file_size <= 0 or info.file_size > limit:
                raise ValueError("training artifact member is empty or oversized")
            if info.filename != REPORT_NAME:
                total_csv_bytes += info.file_size
                if total_csv_bytes > MAX_TOTAL_CSV_BYTES:
                    raise ValueError("training artifact CSV collection exceeds total byte limit")
        report = json.loads(archive.read(REPORT_NAME))
        _reject_report_outcome_fields(report)
        if (
            report.get("schema_version") != "SERIE_A_V2_LIVE_DIAGNOSTIC_SOURCE_ATTESTATION_V1"
            or report.get("mode") != "RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET"
            or report.get("historical_source") != "FOOTBALL_DATA_CSV"
            or report.get("frozen_candidate_sha256") != CANDIDATE_SHA
            or report.get("protect_2026_27_prospective_outcomes") is not True
            or report.get("2026_27_public_results_downloaded") is not False
            or report.get("paid_provider_requests") != 0
            or report.get("supabase_writes") != 0
            or report.get("model_training") is not False
            or report.get("model_promotion") is not False
            or report.get("eligible_for_frozen_prospective_cohort") is not False
            or report.get("eligible_for_product_publication") is not False
            or report.get("no_bet") is not True
            or report.get("feature_count") != 19
            or report.get("public_http_requests") != len(SEASON_CODES)
        ):
            raise ValueError("Free Diagnostic report does not satisfy the frozen historical-only recovery contract")
        report_time = parse_utc(report["as_of_utc"], "diagnostic report as_of_utc")
        if report_time > artifact_created:
            raise ValueError("diagnostic report was created after its GitHub artifact")

        public_files = report.get("public_source_files")
        if not isinstance(public_files, list) or len(public_files) != len(SEASON_CODES):
            raise ValueError("training source audit does not contain exactly ten old seasons")
        for item in public_files:
            if not isinstance(item, dict):
                raise ValueError("training source audit row is not an object")
            code = item.get("season_code")
            if code not in SEASON_CODES or code in audits:
                raise ValueError("training source audit contains an unexpected or duplicate season")
            filename = f"serie_a_{code}.csv"
            expected_url = f"{PUBLIC_BASE}/{code}/{COMPETITION_CODE}.csv"
            if (
                item.get("archived_source_name") != filename
                or item.get("source_url") != expected_url
            ):
                raise ValueError("training source audit URL or filename differs from the frozen allowlist")
            file_sha = item.get("csv_sha256")
            if not isinstance(file_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", file_sha):
                raise ValueError("training source audit contains an invalid CSV SHA-256")
            observed = parse_utc(item.get("source_observed_at_utc"), "source_observed_at_utc")
            if observed < run_created:
                raise ValueError("historical source observation predates its successful parent run")
            if not (observed <= report_time <= artifact_created):
                raise ValueError("historical source observation is after the report or archive")
            row_count = item.get("completed_source_rows")
            if type(row_count) is not int or row_count <= 0:
                raise ValueError("historical source audit has an invalid row count")
            member = SOURCE_DIR + filename
            body = archive.read(member)
            if hashlib.sha256(body).hexdigest() != file_sha:
                raise ValueError(f"historical training CSV SHA-256 mismatch: {code}")
            frame = pd.read_csv(BytesIO(body), low_memory=False)
            if len(frame) != row_count or frame.empty or not REQUIRED_COLUMNS.issubset(frame.columns):
                raise ValueError(f"historical training CSV schema or row count mismatch: {code}")
            dates = pd.to_datetime(frame["Date"], dayfirst=True, format="mixed", errors="coerce")
            if dates.isna().any() or (dates >= pd.Timestamp(TRAINING_CUTOFF)).any():
                raise ValueError(f"historical training CSV crosses the frozen 2026-06-30 cutoff: {code}")
            results = frame["FTR"].fillna("").astype(str).str.strip().str.upper()
            if not results.isin(("H", "D", "A")).all():
                raise ValueError(f"historical training CSV contains incomplete results: {code}")
            extracted[code] = body
            audits[code] = {
                "filename": filename,
                "sha256": file_sha,
                "source_observed_at_utc": observed.isoformat(),
                "rows": row_count,
            }
        if set(audits) != set(SEASON_CODES):
            raise ValueError("training source audit season coverage is incomplete")
        total_rows = sum(item["rows"] for item in audits.values())
        if report.get("history_rows") != total_rows:
            raise ValueError("training source report row count differs from archived CSV members")

    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError("training archive output directory must be empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    for code in SEASON_CODES:
        (output_dir / f"serie_a_{code}.csv").write_bytes(extracted[code])
    manifest = {
        "schema_version": "MARKET_ANCHOR_V2_VERIFIED_TRAINING_ARCHIVE_V1",
        "candidate_sha256": CANDIDATE_SHA,
        "artifact_id": artifact_id,
        "artifact_name": SOURCE_ARTIFACT_NAME,
        "artifact_sha256": archive_sha256,
        "artifact_created_at_utc": artifact_created.isoformat(),
        "parent_run_id": run_id,
        "parent_run_head_sha": run.get("head_sha"),
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "source_script_path": SOURCE_SCRIPT_PATH,
        "source_script_blob_sha": source_script_blob_sha,
        "season_codes": list(SEASON_CODES),
        "season_csv_sha256": {code: audits[code]["sha256"] for code in SEASON_CODES},
        "source_observed_at_utc": {code: audits[code]["source_observed_at_utc"] for code in SEASON_CODES},
        "historical_match_rows": total_rows,
        "protected_2026_27_csv_opened": False,
        "target_outcomes_read": False,
        "paid_provider_calls": 0,
        "supabase_writes": 0,
        "eligible_for_frozen_prospective_cohort": False,
        "product_publishable": False,
        "source_rights": source_rights,
    }
    (output_dir / "training_source_archive_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def load_latest_training_archive(
    output_dir: Path,
    *,
    token: str,
    repository: str = REPOSITORY,
    now: datetime | None = None,
    get=requests.get,
    rights_manifest_path: Path = DEFAULT_RIGHTS_MANIFEST_PATH,
    rights_repo_root: Path | None = None,
) -> dict:
    if repository != REPOSITORY:
        raise ValueError("training archive recovery is pinned to the original GitHub repository")
    if not token:
        raise ValueError("GitHub actions:read token is required")
    if now is None:
        now = datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("training archive recovery clock must have a real UTC offset")
    # Rights are checked before any GitHub API request, artifact listing, download, or extraction.
    require_ai_model_training_permission(
        rights_manifest_path, repo_root=rights_repo_root, now=now
    )

    workflows = _github_json(f"{API_BASE}/actions/workflows?per_page=100", token=token, get=get)
    matches = [
        item for item in workflows.get("workflows", [])
        if item.get("path") == SOURCE_WORKFLOW_PATH and item.get("state") == "active"
    ]
    if len(matches) != 1 or type(matches[0].get("id")) is not int:
        raise ValueError("could not uniquely identify the pinned Free Diagnostic workflow")
    workflow_id = matches[0]["id"]
    runs_payload = _github_json(
        f"{API_BASE}/actions/workflows/{workflow_id}/runs?branch=main&per_page=100",
        token=token,
        get=get,
    )
    candidates = sorted(
        (
            run for run in runs_payload.get("workflow_runs", [])
            if run.get("path") == SOURCE_WORKFLOW_PATH
            and run.get("head_branch") == "main"
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
            and run.get("event") in {"schedule", "workflow_dispatch", "push"}
        ),
        key=lambda run: run.get("created_at", ""),
        reverse=True,
    )
    for run in candidates:
        run_id = run.get("id")
        if type(run_id) is not int or run_id <= 0:
            continue
        # Verify the parent commit used the strict no-redirect Football-Data
        # fetch code before looking up, downloading, or extracting any artifact.
        source_script_blob_sha = verify_parent_source_code(run=run, token=token, get=get)
        artifacts_payload = _github_json(
            f"{API_BASE}/actions/runs/{run_id}/artifacts",
            token=token,
            get=get,
        )
        artifacts = [
            item for item in artifacts_payload.get("artifacts", [])
            if item.get("name") == SOURCE_ARTIFACT_NAME and item.get("expired") is False
        ]
        if not artifacts:
            continue
        artifact = max(artifacts, key=lambda item: item.get("created_at", ""))
        raw = _download_artifact_zip(artifact.get("id"), token=token, get=get)
        return verify_and_extract_archive(
            raw,
            artifact=artifact,
            run=run,
            output_dir=output_dir,
            now=now,
            source_script_blob_sha=source_script_blob_sha,
            rights_manifest_path=rights_manifest_path,
            rights_repo_root=rights_repo_root,
        )
    raise RuntimeError("no successful main Free Diagnostic artifact with the exact historical-only source set was found")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if repository != REPOSITORY:
        raise RuntimeError("training archive recovery must run in the original GitHub repository")
    manifest = load_latest_training_archive(args.output_dir, token=token, repository=repository)
    print(json.dumps({
        "mode": "VERIFIED_EXISTING_TRAINING_ARCHIVE_NO_PUBLIC_DOWNLOAD",
        "artifact_id": manifest["artifact_id"],
        "artifact_sha256": manifest["artifact_sha256"],
        "parent_run_id": manifest["parent_run_id"],
        "historical_csv_count": len(manifest["season_codes"]),
        "historical_match_rows": manifest["historical_match_rows"],
        "protected_2026_27_csv_opened": manifest["protected_2026_27_csv_opened"],
        "paid_provider_calls": manifest["paid_provider_calls"],
        "supabase_writes": manifest["supabase_writes"],
        "source_rights_manifest_sha256": manifest["source_rights"]["rights_manifest_sha256"],
        "source_rights_evidence_sha256": manifest["source_rights"]["evidence_sha256"],
        "no_bet": True,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
