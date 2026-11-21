"""Forward-only original Serie A V2 research preview from *older* GitHub source archives.

This is not a live betting/product model.  It reads stored odds and GitHub
Actions artifacts only. No The Odds API and no protected-season outcome reads.
All V2 shadow forecasts remain NO_BET / NOT frozen-prospective-admissible.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from io import BytesIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import re
from typing import Any
import zipfile

import pandas as pd
import requests

from serie_a_v2_frozen_shadow_preview import (
    FROZEN_SHA, fetch_saved_upcoming_serie_a_quotes, parse_utc,
)
from serie_a_v2_live_diagnostic_report import make_report
from serie_a_v2_prequote_source_archive_gate import (
    ARCHIVE_REPORT, SOURCE_DIR, MAX_ZIP_BYTES, verify_archive,
)

REPOSITORY = "MaksimBlud/football-ai"
ARTIFACT_NAME = "serie-a-v2-free-real-quote-diagnostic"
SOURCE_WORKFLOW_PATH = ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml"
GITHUB_API = f"https://api.github.com/repos/{REPOSITORY}"
SCHEMA_VERSION = "SERIE_A_ORIGINAL_V2_FORWARD_SOURCE_BEFORE_QUOTE_V1"


def require_v2_live_access() -> None:
    """Fail closed unless the owner explicitly clears the V2 source/quote hold."""
    allowed = os.environ.get("MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED", "false")
    if allowed.strip().lower() != "true":
        raise PermissionError(
            "original V2 source/quote access is held; "
            "MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=true is required"
        )





def _require_v2_inference_access() -> dict:
    """Require explicit provider inference clearance and private artifact storage."""
    from market_anchor_v2_direct_access import require_v2_inference_access
    return require_v2_inference_access()


def require_private_repository(*, token: str, get=requests.get) -> dict:
    """Fail closed before source/quote access unless this exact repo is private."""
    require_v2_live_access()
    if not token:
        raise ValueError("GitHub Actions read token missing for private-repository verification")
    url = GITHUB_API
    response = get(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }, timeout=30, allow_redirects=False)
    if getattr(response, "url", None) != url:
        raise ValueError("unexpected GitHub repository metadata response URL")
    status = getattr(response, "status_code", None)
    if status != 200:
        raise ValueError(f"GitHub repository metadata request returned HTTP {status}")
    data = response.json()
    if not isinstance(data, dict) or data.get("full_name") != REPOSITORY:
        raise ValueError("GitHub repository metadata identity mismatch")
    if data.get("private") is not True:
        raise PermissionError(
            "original V2 source/quote access requires the exact GitHub repository to be private"
        )
    return {"repository": REPOSITORY, "private": True}


def _github_json(url: str, *, token: str, get=requests.get) -> dict:
    require_v2_live_access()
    _require_v2_inference_access()
    if not token:
        raise ValueError("GitHub Actions read token missing")
    if not url.startswith(GITHUB_API + "/"):
        raise ValueError("external GitHub repository URL forbidden")
    r = get(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict):
        raise ValueError("unexpected GitHub artifact response")
    return data


def discover_archives(*, token: str, get=requests.get) -> list[dict]:
    """Bound pagination and accept only main-branch, correct-name artifacts."""
    out = []
    seen_ids = set()
    for page in range(1, 4):
        url = f"{GITHUB_API}/actions/artifacts?name={ARTIFACT_NAME}&per_page=100&page={page}"
        data = _github_json(url, token=token, get=get)
        items = data.get("artifacts")
        if not isinstance(items, list):
            raise ValueError("GitHub response lacks artifact array")
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("malformed GitHub artifact item")
            if item.get("name") != ARTIFACT_NAME or item.get("expired") is True:
                continue
            flow = item.get("workflow_run")
            if not isinstance(flow, dict) or flow.get("head_branch") != "main":
                continue
            run_id = flow.get("id")
            head_sha = flow.get("head_sha")
            if (type(run_id) is not int or run_id <= 0
                    or not isinstance(head_sha, str)
                    or not re.fullmatch(r"[0-9a-f]{40}", head_sha)):
                raise ValueError("source artifact missing GitHub parent run identity")
            artifact_id = item.get("id")
            if not isinstance(artifact_id, int) or artifact_id <= 0 or artifact_id in seen_ids:
                raise ValueError("invalid or duplicate GitHub artifact id")
            seen_ids.add(artifact_id)
            digest = item.get("digest")
            if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                raise ValueError("missing GitHub source archive SHA256 digest")
            created = parse_utc(item["created_at"])
            out.append({
                "artifact_id": artifact_id,
                "run_id": run_id,
                "head_sha": head_sha,
                "created_at": created,
                "sha256": digest.removeprefix("sha256:"),
            })
        if len(items) < 100:
            break
    return sorted(out, key=lambda x: (x["created_at"], x["artifact_id"]), reverse=True)


def verify_source_run(archive: dict, *, quote_time: datetime,
                      token: str, get=requests.get) -> dict:
    """Authenticate artifact parent as our exact successful public CSV collector.

    The artifact name+main branch alone are NOT evidence that its bytes came
    from the verified source workflow. A successful parent run must also have
    finished BEFORE the saved bookmaker quote, not only before inspection.
    """
    require_v2_live_access()
    _require_v2_inference_access()
    run_id = archive["run_id"]
    if type(run_id) is not int or run_id <= 0:
        raise ValueError("source archive is missing a parent GitHub run")
    j = _github_json(f"{GITHUB_API}/actions/runs/{run_id}", token=token, get=get)
    if (j.get("id") != run_id or j.get("path") != SOURCE_WORKFLOW_PATH
            or j.get("head_branch") != "main"
            or j.get("head_sha") != archive["head_sha"]
            or j.get("status") != "completed" or j.get("conclusion") != "success"
            or j.get("event") not in ("push", "schedule", "workflow_dispatch")):
        raise ValueError("source artifact parent run is not the verified original V2 collector")
    completed = parse_utc(j["updated_at"])
    if not completed < quote_time:
        raise ValueError("source workflow was not successfully finished before quote")
    created = parse_utc(j["created_at"])
    if not created <= archive["created_at"] or not archive["created_at"] <= completed:
        raise ValueError("source workflow and archived artifact times conflict")
    return {
        "run_id": run_id,
        "run_head_sha": archive["head_sha"],
        "workflow_path": SOURCE_WORKFLOW_PATH,
        "run_completed_at_utc": completed.isoformat(),
    }


def get_archive(artifact_id: int, *, token: str, get=requests.get) -> bytes:
    require_v2_live_access()
    _require_v2_inference_access()
    if not isinstance(artifact_id, int) or artifact_id <= 0:
        raise ValueError("invalid artifact id")
    url = f"{GITHUB_API}/actions/artifacts/{artifact_id}/zip"
    if not token:
        raise ValueError("GitHub token required")
    r = get(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }, timeout=90)
    r.raise_for_status()
    raw = r.content
    if not raw or len(raw) > MAX_ZIP_BYTES:
        raise ValueError("missing or oversized source archive")
    return raw


def prepare_forward_capture(
    quotes: list[dict], archive_metadata: list[dict], *,
    as_of_utc: datetime, load_archive, verify_parent_run,
    write_archives_to: Path | None = None,
) -> dict:
    """Only score quotes with a GitHub source ZIP strictly older than the quote.

    A source-before-quote check is necessary but not sufficient for prospective
    admission: frozen incumbent, current-season form and outcome gate still
    missing. All resulting original-V2 probabilities are diagnostic only.
    """
    require_v2_live_access()
    _require_v2_inference_access()
    if as_of_utc.tzinfo is None:
        raise ValueError("as_of_utc must be timezone-aware")
    now = as_of_utc.astimezone(timezone.utc)
    from serie_a_v2_frozen_shadow_preview import _guard_outcome_free
    if write_archives_to is not None:
        write_archives_to.mkdir(parents=True, exist_ok=True)
    rows, cache = [], {}
    verified_runs = {}
    used_archives = {}
    for q in quotes:
        _guard_outcome_free(q)
        if q.get("league") != "SERIE_A":
            raise ValueError("forward capture accepts Serie A quotes only")
        quote_time = parse_utc(q["snapshot_time_utc"])
        kickoff = parse_utc(q["commence_time_utc"])
        if quote_time > now or not quote_time < kickoff:
            raise ValueError("invalid stored quote timing")
        if not now < kickoff:
            continue
        key = (q["event_id"], quote_time)
        if any((r["event_id"], r["quote_time_utc"]) == (q["event_id"], quote_time.isoformat()) for r in rows):
            raise ValueError("duplicate saved quote observation")
        record = {
            "event_id": q["event_id"],
            "quote_time_utc": quote_time.isoformat(),
            "kickoff_utc": kickoff.isoformat(),
            "status": "NO_EARLIER_SOURCE_ARCHIVE",
            "v2_preview": None,
            "eligible_for_frozen_prospective_cohort": False,
            "no_bet": True,
        }
        candidates = []
        for archive in archive_metadata:
            if archive["created_at"] >= quote_time:
                continue
            parent_completed_at = archive.get("verified_parent_completed_at_utc")
            if (
                parent_completed_at is not None
                and not parse_utc(parent_completed_at) < quote_time
            ):
                continue
            candidates.append(archive)
        if not candidates:
            rows.append(record)
            continue
        chosen = max(candidates, key=lambda a: (a["created_at"], a["artifact_id"]))
        artifact_id = chosen["artifact_id"]
        if artifact_id not in verified_runs:
            verified_runs[artifact_id] = verify_parent_run(chosen, quote_time)
        if not isinstance(verified_runs[artifact_id], dict) or not verified_runs[artifact_id].get("run_completed_at_utc"):
            raise ValueError("missing verified source workflow provenance")
        if not parse_utc(verified_runs[artifact_id]["run_completed_at_utc"]) < quote_time:
            raise ValueError("source workflow finished after another quote")
        if artifact_id not in cache:
            raw = load_archive(artifact_id)
            if not isinstance(raw, bytes):
                raise ValueError("archive loader returned non-bytes")
            cache[artifact_id] = raw
            if write_archives_to is not None:
                (write_archives_to / f"source_artifact_{artifact_id}.zip").write_bytes(raw)
        raw = cache[artifact_id]
        # Original offline guard validates the *full ZIP*, every CSV, time,
        # score embargo and separately retrieved GitHub digest.
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            src = Path(td) / "original_source.zip"
            src.write_bytes(raw)
            gate = verify_archive(
                src, [q], as_of_utc=now,
                github_artifact_sha256=chosen["sha256"],
                github_artifact_created_at_utc=chosen["created_at"].isoformat(),
            )
        if gate["source_archive_prequote_ready"] != 1:
            raise ValueError("source archive unexpectedly failed pre-quote gate")
        with zipfile.ZipFile(BytesIO(raw), "r") as z:
            archived_report = json.loads(z.read(ARCHIVE_REPORT))
            audits = archived_report["public_source_files"]
            history = pd.concat([
                pd.read_csv(BytesIO(z.read(
                    SOURCE_DIR + a["archived_source_name"]
                )), low_memory=False)
                for a in audits
            ], ignore_index=True)
        scored = make_report([q], history, audits, as_of_utc=now)
        if scored["diagnostic_scored"] != 1:
            record["status"] = "STALE_QUOTE_OR_MISSING_FEATURES"
        else:
            record["status"] = "SOURCE_BEFORE_QUOTE_V2_DIAGNOSTIC_ONLY"
            record["v2_preview"] = scored["diagnostic_previews"][0]
            record["source_artifact_id"] = artifact_id
            record["source_artifact_sha256"] = chosen["sha256"]
            record["verified_source_workflow_run"] = verified_runs[artifact_id]
            used_archives[artifact_id] = chosen["sha256"]
        rows.append(record)
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "RESTORED_ORIGINAL_V2_RESEARCH_ONLY_NO_BET",
        "captured_at_utc": now.isoformat(),
        "quotes_seen": len(quotes),
        "future_quotes_checked": len(rows),
        "v2_diagnostic_previews_captured": sum(
            r["v2_preview"] is not None for r in rows),
        "blocked_no_prior_source": sum(
            r["status"] == "NO_EARLIER_SOURCE_ARCHIVE" for r in rows),
        "archived_sources_used": used_archives,
        "source_workflow_run_attestation_required": True,
        "rows": rows,
        "uses_original_frozen_v2": True,
        "independent_incumbent_asof_verified": False,
        "uses_2026_27_results": False,
        "eligible_for_frozen_prospective_cohort": False,
        "eligible_for_product_publication": False,
        "no_bet": True,
        "paid_provider_calls": 0,
        "supabase_writes": 0,
        "training_or_promotion": False,
    }


def capture_forward_with_source_preflight(
    archive_metadata: list[dict],
    *,
    as_of_utc: datetime,
    fetch_quotes,
    load_archive,
    verify_parent_run,
    write_archives_to: Path | None = None,
) -> dict:
    """Verify the latest source parent and complete ZIP before the first quote read.

    The owner-controlled live-access flag is checked before any callback. Only
    the newest source artifact is used: if it is missing or invalid, fail closed
    rather than silently falling back to older source bytes.
    """
    require_v2_live_access()
    _require_v2_inference_access()
    if (
        not isinstance(as_of_utc, datetime)
        or as_of_utc.tzinfo is None
        or as_of_utc.utcoffset() is None
    ):
        raise ValueError("source preflight clock must be timezone-aware")
    if not isinstance(archive_metadata, list):
        raise ValueError("source archive metadata must be a list")
    if not callable(fetch_quotes) or not callable(load_archive) or not callable(verify_parent_run):
        raise ValueError("source preflight callbacks must be callable")

    now = as_of_utc.astimezone(timezone.utc)
    candidates = []
    for archive in archive_metadata:
        if not isinstance(archive, dict):
            raise ValueError("malformed source archive metadata")
        created_at = archive.get("created_at")
        if (
            not isinstance(created_at, datetime)
            or created_at.tzinfo is None
            or created_at.utcoffset() is None
        ):
            raise ValueError("source archive metadata requires a timezone-aware created_at")
        if created_at.astimezone(timezone.utc) < now:
            candidates.append(archive)
    if not candidates:
        raise RuntimeError("no original V2 source archive before quote read")

    chosen = max(
        candidates,
        key=lambda item: (
            item["created_at"].astimezone(timezone.utc),
            item.get("artifact_id", 0),
        ),
    )
    parent = verify_parent_run(chosen, now)
    if (
        not isinstance(parent, dict)
        or parent.get("run_id") != chosen.get("run_id")
        or parent.get("run_head_sha") != chosen.get("head_sha")
        or parent.get("workflow_path") != SOURCE_WORKFLOW_PATH
        or not parent.get("run_completed_at_utc")
    ):
        raise ValueError("source parent workflow identity mismatch before quote read")
    parent_completed = parse_utc(parent["run_completed_at_utc"])
    if not parent_completed < now:
        raise ValueError("source parent workflow is not complete before quote read")

    artifact_id = chosen.get("artifact_id")
    raw = load_archive(artifact_id)
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_ZIP_BYTES:
        raise ValueError("source archive loader returned empty or oversized bytes")
    with TemporaryDirectory() as temporary_directory:
        archive_path = Path(temporary_directory) / "original-v2-source.zip"
        archive_path.write_bytes(raw)
        proof = verify_archive(
            archive_path,
            [],
            as_of_utc=now,
            github_artifact_sha256=chosen.get("sha256"),
            github_artifact_created_at_utc=chosen["created_at"].isoformat(),
        )
    if (
        proof.get("github_digest_matched") is not True
        or proof.get("archived_csv_count") != 10
        or proof.get("historical_match_rows", 0) <= 0
        or proof.get("original_candidate_sha256") != FROZEN_SHA
        or proof.get("quotes_checked") != 0
        or proof.get("eligible_for_frozen_prospective_cohort") is not False
        or proof.get("no_bet") is not True
    ):
        raise ValueError("original V2 source archive preflight is incomplete")

    verified_archive = {
        **chosen,
        "verified_parent_completed_at_utc": parent_completed.isoformat(),
    }
    # This is deliberately the first point at which the saved-quote reader runs.
    quotes = fetch_quotes()
    if not isinstance(quotes, list):
        raise ValueError("saved quote reader must return a list")

    def load_verified_archive(requested_id: int) -> bytes:
        if requested_id != artifact_id:
            raise ValueError("requested source archive was not preflight-verified")
        return raw

    def verify_parent_for_quote(archive: dict, quote_time: datetime) -> dict:
        if archive.get("artifact_id") != artifact_id:
            raise ValueError("requested source parent was not preflight-verified")
        if not parent_completed < quote_time:
            raise ValueError("source workflow finished after quote")
        return parent

    report = prepare_forward_capture(
        quotes,
        [verified_archive],
        as_of_utc=now,
        load_archive=load_verified_archive,
        verify_parent_run=verify_parent_for_quote,
        write_archives_to=write_archives_to,
    )
    report["source_preflight"] = {
        "verified": True,
        "source_artifact_id": artifact_id,
        "source_artifact_sha256": chosen["sha256"],
        "source_artifact_created_at_utc": chosen["created_at"].isoformat(),
        "source_parent_run_id": parent["run_id"],
        "source_parent_completed_at_utc": parent_completed.isoformat(),
        "verified_historical_csv_count": proof["archived_csv_count"],
        "verified_historical_match_rows": proof["historical_match_rows"],
        "original_candidate_sha256": proof["original_candidate_sha256"],
        "quotes_read_after_source_preflight": True,
    }
    report["quote_read_skipped"] = False
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sources-output-dir", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise RuntimeError("wrong GitHub repository scope")
    require_v2_live_access()
    try:
        _require_v2_inference_access()
    except PermissionError as exc:
        from market_anchor_v2_source_rights import write_research_scope_blocked_report
        report = write_research_scope_blocked_report(
            args.output, "SERIE_A_ORIGINAL_V2_FORWARD_CAPTURE", str(exc)
        )
        print(json.dumps(report, sort_keys=True))
        return
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise RuntimeError("GitHub Actions read token is required after the V2 live-access gate")
    now = datetime.now(timezone.utc)
    archives = discover_archives(token=token)
    raw_cache = {}
    parent_cache = {}

    def load_cached_archive(artifact_id: int) -> bytes:
        if artifact_id not in raw_cache:
            raw_cache[artifact_id] = get_archive(artifact_id, token=token)
        return raw_cache[artifact_id]

    def verify_parent(archive: dict, quote_time: datetime) -> dict:
        artifact_id = archive["artifact_id"]
        if artifact_id not in parent_cache:
            parent_cache[artifact_id] = verify_source_run(
                archive, quote_time=quote_time, token=token
            )
        return parent_cache[artifact_id]

    def fetch_quotes():
        # Import/initialize Supabase only after parent-run and ZIP SHA preflight.
        from database import supabase
        return fetch_saved_upcoming_serie_a_quotes(supabase, now=now)

    report = capture_forward_with_source_preflight(
        archives,
        as_of_utc=now,
        fetch_quotes=fetch_quotes,
        load_archive=load_cached_archive,
        verify_parent_run=verify_parent,
        write_archives_to=args.sources_output_dir,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "mode", "quotes_seen", "future_quotes_checked",
        "v2_diagnostic_previews_captured", "blocked_no_prior_source",
        "eligible_for_frozen_prospective_cohort", "paid_provider_calls",
        "supabase_writes", "no_bet", "source_preflight",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
