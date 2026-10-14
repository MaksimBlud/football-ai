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
import re
from typing import Any
import zipfile

import pandas as pd
import requests

from serie_a_v2_frozen_shadow_preview import (
    fetch_saved_upcoming_serie_a_quotes, parse_utc,
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


def _github_json(url: str, *, token: str, get=requests.get) -> dict:
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
        candidates = [a for a in archive_metadata if a["created_at"] < quote_time]
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sources-output-dir", type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise RuntimeError("wrong GitHub repository scope")
    token = os.environ.get("GITHUB_TOKEN", "")
    from database import supabase
    now = datetime.now(timezone.utc)
    quotes = fetch_saved_upcoming_serie_a_quotes(supabase, now=now)
    archives = discover_archives(token=token)
    report = prepare_forward_capture(
        quotes, archives, as_of_utc=datetime.now(timezone.utc),
        load_archive=lambda artifact_id: get_archive(artifact_id, token=token),
        verify_parent_run=lambda a, qt: verify_source_run(a, quote_time=qt, token=token),
        write_archives_to=args.sources_output_dir,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "mode", "quotes_seen", "future_quotes_checked",
        "v2_diagnostic_previews_captured", "blocked_no_prior_source",
        "eligible_for_frozen_prospective_cohort", "paid_provider_calls",
        "supabase_writes", "no_bet",
    )}, sort_keys=True))


if __name__ == "__main__":
    main()
