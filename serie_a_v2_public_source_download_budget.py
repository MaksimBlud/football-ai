"""Shared rate guard for the two existing V2 public-source download workflows.

This module talks only to the repository's GitHub Actions API. It does not
contact Football-Data, Supabase, an odds provider, or any match-outcome source.
A marker is uploaded before either workflow can begin a public CSV download.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Mapping

import requests

REPOSITORY = "MaksimBlud/football-ai"
GITHUB_API = f"https://api.github.com/repos/{REPOSITORY}"
MARKER_ARTIFACT_NAME = "serie-a-v2-public-source-download-attempt"
MIN_DOWNLOAD_INTERVAL = timedelta(hours=170)
ALLOWED_WORKFLOW_PATHS = {
    ".github/workflows/serie-a-v2-current-form-source-capture.yml",
    ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml",
}
LEGACY_SOURCE_ARTIFACTS = {
    "serie-a-v2-current-form-source-capture": ".github/workflows/serie-a-v2-current-form-source-capture.yml",
    "serie-a-v2-free-real-quote-diagnostic": ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml",
}
# Current-form capture may also follow a successful main Free Diagnostic workflow_run;
# its workflow-level guard restricts that parent to schedule/workflow_dispatch. Push is offline-only.
ALLOWED_EVENTS = {"schedule", "workflow_dispatch", "workflow_run"}
SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")


def parse_utc(value: Any, *, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a real UTC offset")
    return parsed.astimezone(timezone.utc)


def _api_json(url: str, *, token: str, get: Callable[..., Any]) -> Mapping[str, Any]:
    if not url.startswith(GITHUB_API + "/"):
        raise ValueError("public-source budget API URL escaped the fixed repository")
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
        raise ValueError("GitHub public-source budget API returned an unexpected URL")
    if getattr(response, "status_code", None) != 200:
        raise RuntimeError(
            f"GitHub public-source budget API failed with HTTP {getattr(response, 'status_code', None)}"
        )
    data = response.json()
    if not isinstance(data, Mapping):
        raise ValueError("GitHub public-source budget API returned a non-object response")
    return data


def discover_latest_download_attempt(
    *,
    token: str,
    workflow_path: str,
    get: Callable[..., Any] = requests.get,
) -> datetime | None:
    """Return the latest attempt for this workflow, bootstrapping from its legacy artifact.

    Each of the two approved source workflows gets at most one attempt per
    170 hours. Together they can therefore make at most two attempts in any
    seven-day span. The shared GitHub concurrency group serializes reservations.
    """
    if not isinstance(token, str) or not token.strip():
        raise ValueError("GitHub actions:read token is required for the shared download budget")
    if workflow_path not in ALLOWED_WORKFLOW_PATHS:
        raise ValueError("workflow path is not allowed to inspect the public-source budget")

    candidates: list[tuple[datetime, Mapping[str, Any]]] = []
    page_size = 100
    max_pages = 3
    for page in range(1, max_pages + 1):
        url = (
            f"{GITHUB_API}/actions/artifacts?name={MARKER_ARTIFACT_NAME}"
            f"&per_page={page_size}&page={page}"
        )
        payload = _api_json(url, token=token, get=get)
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, list):
            raise ValueError("download-attempt marker listing lacks an artifacts array")
        for artifact in artifacts:
            if not isinstance(artifact, Mapping):
                raise ValueError("download-attempt marker listing contains a malformed item")
            if artifact.get("name") != MARKER_ARTIFACT_NAME or artifact.get("expired") is True:
                continue
            flow = artifact.get("workflow_run")
            if not isinstance(flow, Mapping):
                raise ValueError("download-attempt marker lacks its GitHub workflow parent")
            if flow.get("head_branch") != "main":
                continue
            run_id = flow.get("id")
            head_sha = flow.get("head_sha")
            if type(run_id) is not int or run_id <= 0:
                raise ValueError("download-attempt marker has an invalid parent run id")
            if not isinstance(head_sha, str) or SHA1_RE.fullmatch(head_sha) is None:
                raise ValueError("download-attempt marker has an invalid parent SHA")
            created = parse_utc(artifact.get("created_at"), field="marker artifact created_at")
            candidates.append((created, {"run_id": run_id, "head_sha": head_sha}))
        if len(artifacts) < page_size:
            break
        if page == max_pages:
            raise ValueError("download-attempt marker pagination exceeded its safety bound")

    # Marker artifacts share one name. Authenticate parent runs and select only
    # the latest marker for the workflow whose slot is being checked.
    for created, parent in sorted(candidates, key=lambda item: item[0], reverse=True):
        run_id = parent["run_id"]
        run = _api_json(f"{GITHUB_API}/actions/runs/{run_id}", token=token, get=get)
        if (
            run.get("id") != run_id
            or run.get("path") not in ALLOWED_WORKFLOW_PATHS
            or run.get("head_branch") != "main"
            or run.get("head_sha") != parent["head_sha"]
            or run.get("event") not in ALLOWED_EVENTS
            or run.get("status") not in {"in_progress", "completed"}
        ):
            raise ValueError("download-attempt marker parent is not an approved main source workflow")
        run_created = parse_utc(run.get("created_at"), field="marker parent run created_at")
        if created < run_created:
            raise ValueError("download-attempt marker predates its parent workflow run")
        if run.get("path") != workflow_path:
            continue
        if run.get("status") == "completed":
            run_completed = parse_utc(run.get("updated_at"), field="marker parent run updated_at")
            if created > run_completed:
                raise ValueError("download-attempt marker postdates its parent workflow completion")
        return created

    # Bootstrap this workflow's own slot from its matching legacy artifact.
    # Do not let the other workflow's earlier schedule starve this one.
    legacy_name = next(
        (name for name, path in LEGACY_SOURCE_ARTIFACTS.items() if path == workflow_path),
        None,
    )
    if legacy_name is None:
        raise ValueError("workflow path has no approved legacy source artifact")
    legacy_candidates: list[tuple[datetime, int, str]] = []
    for page in range(1, max_pages + 1):
        url = (
            f"{GITHUB_API}/actions/artifacts?name={legacy_name}"
            f"&per_page={page_size}&page={page}"
        )
        payload = _api_json(url, token=token, get=get)
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, list):
            raise ValueError("legacy source artifact listing lacks an artifacts array")
        for artifact in artifacts:
            if not isinstance(artifact, Mapping):
                raise ValueError("legacy source artifact listing contains a malformed item")
            if artifact.get("name") != legacy_name or artifact.get("expired") is True:
                continue
            flow = artifact.get("workflow_run")
            if not isinstance(flow, Mapping):
                raise ValueError("legacy source artifact lacks its GitHub workflow parent")
            if flow.get("head_branch") != "main":
                continue
            run_id = flow.get("id")
            head_sha = flow.get("head_sha")
            if type(run_id) is not int or run_id <= 0:
                raise ValueError("legacy source artifact has an invalid parent run id")
            if not isinstance(head_sha, str) or SHA1_RE.fullmatch(head_sha) is None:
                raise ValueError("legacy source artifact has an invalid parent SHA")
            created = parse_utc(artifact.get("created_at"), field="legacy source artifact created_at")
            legacy_candidates.append((created, run_id, head_sha))
        if len(artifacts) < page_size:
            break
        if page == max_pages:
            raise ValueError("legacy source artifact pagination exceeded its safety bound")

    if not legacy_candidates:
        return None
    created, run_id, head_sha = max(legacy_candidates, key=lambda item: item[0])
    run = _api_json(f"{GITHUB_API}/actions/runs/{run_id}", token=token, get=get)
    if (
        run.get("id") != run_id
        or run.get("path") != workflow_path
        or run.get("head_branch") != "main"
        or run.get("head_sha") != head_sha
        or run.get("event") not in ALLOWED_EVENTS
        or run.get("status") not in {"in_progress", "completed"}
    ):
        raise ValueError("legacy source artifact parent is not its approved main source workflow")
    run_created = parse_utc(run.get("created_at"), field="legacy source parent run created_at")
    if created < run_created:
        raise ValueError("legacy source artifact predates its parent workflow run")
    if run.get("status") == "completed":
        run_completed = parse_utc(run.get("updated_at"), field="legacy source parent run updated_at")
        if created > run_completed:
            raise ValueError("legacy source artifact postdates its parent workflow completion")
    return created


def decide_download_permission(
    *, now: datetime, latest_attempt_at: datetime | None
) -> tuple[bool, datetime | None]:
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("public-source budget clock must have a real UTC offset")
    captured = now.astimezone(timezone.utc)
    if latest_attempt_at is None:
        return True, None
    if not isinstance(latest_attempt_at, datetime) or latest_attempt_at.tzinfo is None or latest_attempt_at.utcoffset() is None:
        raise ValueError("latest public-source download marker must be timezone-aware")
    latest = latest_attempt_at.astimezone(timezone.utc)
    if latest > captured:
        raise ValueError("latest public-source download marker is in the future")
    next_allowed = latest + MIN_DOWNLOAD_INTERVAL
    return captured >= next_allowed, next_allowed


def build_attempt_marker(
    *,
    now: datetime,
    workflow_path: str,
    run_id: int,
    head_sha: str,
    latest_attempt_at: datetime | None,
) -> dict[str, Any]:
    if workflow_path not in ALLOWED_WORKFLOW_PATHS:
        raise ValueError("workflow path is not allowed to reserve the public-source budget")
    if type(run_id) is not int or run_id <= 0:
        raise ValueError("workflow run id must be a positive integer")
    if not isinstance(head_sha, str) or SHA1_RE.fullmatch(head_sha) is None:
        raise ValueError("workflow head SHA must be a lowercase 40-character Git SHA")
    allowed, _ = decide_download_permission(now=now, latest_attempt_at=latest_attempt_at)
    if not allowed:
        raise ValueError("public-source download budget is still in cooldown")
    return {
        "schema_version": "SERIE_A_V2_PUBLIC_SOURCE_DOWNLOAD_ATTEMPT_V1",
        "attempt_reserved_at_utc": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "workflow_path": workflow_path,
        "repository": REPOSITORY,
        "workflow_run_id": run_id,
        "git_sha": head_sha,
        "minimum_interval_hours": int(MIN_DOWNLOAD_INTERVAL.total_seconds() // 3600),
        "previous_attempt_at_utc": (
            latest_attempt_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            if latest_attempt_at is not None else None
        ),
        "budget_guard_uses_supabase": False,
        "budget_guard_reads_target_outcomes": False,
        "no_paid_provider_calls": True,
        "no_model_or_schedule_changes": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow-path", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise RuntimeError("public-source budget may run only in the original repository")
    if os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise RuntimeError("public-source budget may run only from main")
    token = os.environ.get("GITHUB_TOKEN", "")
    run_id_text = os.environ.get("GITHUB_RUN_ID", "")
    head_sha = os.environ.get("GITHUB_SHA", "")
    if not run_id_text.isascii() or not run_id_text.isdecimal():
        raise RuntimeError("GitHub workflow run id is missing or malformed")
    run_id = int(run_id_text)
    now = datetime.now(timezone.utc)

    latest = discover_latest_download_attempt(token=token, workflow_path=args.workflow_path)
    allowed, next_allowed = decide_download_permission(now=now, latest_attempt_at=latest)
    output_values = {
        "allowed": "true" if allowed else "false",
        "next_allowed_at_utc": (
            next_allowed.isoformat().replace("+00:00", "Z") if next_allowed else ""
        ),
    }
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as handle:
            for key, value in output_values.items():
                handle.write(f"{key}={value}\n")

    if allowed:
        marker = build_attempt_marker(
            now=now,
            workflow_path=args.workflow_path,
            run_id=run_id,
            head_sha=head_sha,
            latest_attempt_at=latest,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(marker, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": "PUBLIC_SOURCE_DOWNLOAD_ALLOWED", **output_values}, sort_keys=True))
    else:
        print(json.dumps({
            "status": "PUBLIC_SOURCE_DOWNLOAD_SKIPPED_COOLDOWN",
            "latest_attempt_at_utc": latest.isoformat().replace("+00:00", "Z"),
            **output_values,
        }, sort_keys=True))


if __name__ == "__main__":
    main()
