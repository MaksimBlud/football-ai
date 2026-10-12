"""Conservative autonomous merge gate for BOT-authored engineering PRs only.

Runs from trusted default-branch GitHub Actions after actual CI completion.
Never executes or checks out PR code using a write-capable token. Never merges
model, production, auth, workflow, research, or deployment changes. Fail closed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import os
import re
import subprocess
import sys
from typing import Any

from engineering_pr_relay import (
    CI_WORKFLOWS,
    ROLE_FILES,
    api,
    qualified_branch,
    safe_change_set,
)

EXPECTED_CHECKS = frozenset(name for _, name in CI_WORKFLOWS)
TRUSTED_CHECK_APP = "github-actions"
MAX_OPEN_SCAN = 100
MAX_BOT_HEAD_AGE = timedelta(hours=48)
HEX_SHA = re.compile(r"[0-9a-f]{40}\Z")
BOT = "github-actions[bot]"
MANUAL_LABELS = frozenset({"manual-review", "no-automerge", "security-review"})


class UnsafeAutoMerge(ValueError):
    """An eligibility invariant was not satisfied; no merge is allowed."""


def exact_sha(value: Any) -> bool:
    return isinstance(value, str) and HEX_SHA.fullmatch(value) is not None


def candidate_role(pr: dict[str, Any], repo: str) -> str | None:
    """Only existing relay-generated agent draft PRs in this exact repository."""
    if pr.get("state") != "open" or pr.get("merged_at"):
        return None
    if pr.get("draft") is not True:
        return None
    if (pr.get("user") or {}).get("login") != BOT:
        return None
    if not str(pr.get("title") or "").startswith("draft(agents): staged "):
        return None
    if (pr.get("base") or {}).get("ref") != "main":
        return None
    if (pr.get("base") or {}).get("repo", {}).get("full_name") != repo:
        return None
    head = pr.get("head") or {}
    if (head.get("repo") or {}).get("full_name") != repo:
        return None
    if not exact_sha(head.get("sha")):
        return None
    if pr.get("requested_reviewers") or pr.get("requested_teams"):
        return None
    labels = {
        str(label.get("name", "")).casefold()
        for label in (pr.get("labels") or [])
        if isinstance(label, dict)
    }
    if labels & MANUAL_LABELS:
        return None
    matches = [role for role in ROLE_FILES if qualified_branch(str(head.get("ref") or ""), role)]
    if len(matches) != 1:
        return None
    return matches[0]


def pinned_checks_green(payload: dict[str, Any], head_sha: str, repo: str) -> bool:
    """Exactly six real GitHub Actions SUCCESS jobs at the pinned current head."""
    if not exact_sha(head_sha):
        return False
    checks = payload.get("check_runs")
    if not isinstance(checks, list):
        return False
    matches = {}
    for check in checks:
        if not isinstance(check, dict):
            continue
        name = check.get("name")
        if name not in EXPECTED_CHECKS:
            continue
        if check.get("head_sha") != head_sha:
            continue
        app = check.get("app") or {}
        if app.get("slug") != TRUSTED_CHECK_APP:
            continue
        url = str(check.get("details_url") or "")
        if not url.startswith(f"https://github.com/{repo}/actions/runs/"):
            continue
        if name in matches:
            # Duplicate check names make an exact pass ambiguous.
            return False
        matches[name] = check
    return (
        len(matches) == len(EXPECTED_CHECKS)
        and all(
            run.get("status") == "completed" and run.get("conclusion") == "success"
            for run in matches.values()
        )
    )


def safe_comparison(pr: dict[str, Any], compare: dict[str, Any],
                    current_main_sha: str, role: str) -> bool:
    head = pr["head"]
    return (
        exact_sha(current_main_sha)
        and pr.get("base", {}).get("sha") == current_main_sha
        and compare.get("base_commit", {}).get("sha") == current_main_sha
        and compare.get("status") == "ahead"
        and compare.get("behind_by") == 0
        and isinstance(compare.get("ahead_by"), int)
        and 1 <= compare["ahead_by"] <= 6
        and compare.get("commits", [{}])[-1].get("sha") == head["sha"]
        and safe_change_set(role, compare.get("files", []))
        and pr.get("mergeable") is True
        and pr.get("mergeable_state") not in ("dirty", "blocked", "unknown", "draft")
    )


def recently_committed(repo: str, head_sha: str, now: datetime) -> bool:
    commit = api(f"repos/{repo}/commits/{head_sha}")
    value = ((commit.get("commit") or {}).get("committer") or {}).get("date")
    try:
        date = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return False
    if date.tzinfo is None:
        return False
    age = now - date.astimezone(timezone.utc)
    return timedelta(0) <= age <= MAX_BOT_HEAD_AGE


def check_candidate(repo: str, pr: dict[str, Any], main_sha: str,
                    now: datetime) -> tuple[str, str] | None:
    role = candidate_role(pr, repo)
    if role is None:
        return None
    head = pr["head"]
    head_sha = head["sha"]
    if not recently_committed(repo, head_sha, now):
        return None
    comparison = api(f"repos/{repo}/compare/main...{head_sha}")
    if not safe_comparison(pr, comparison, main_sha, role):
        return None
    checks = api(f"repos/{repo}/commits/{head_sha}/check-runs?per_page=100")
    if not pinned_checks_green(checks, head_sha, repo):
        return None
    return role, head_sha


def latest_pr(repo: str, number: int) -> dict[str, Any]:
    return api(f"repos/{repo}/pulls/{number}")


def main_sha(repo: str) -> str:
    return api(f"repos/{repo}/branches/main")["commit"]["sha"]


def mark_ready(repo: str, number: int) -> None:
    result = subprocess.run(
        ["gh", "pr", "ready", str(number), "--repo", repo],
        check=False, capture_output=True, text=True,
    )
    if result.returncode:
        raise RuntimeError(f"could not mark PR ready: {result.stderr[:350]}")


def run(repo: str, *, apply: bool = False, now: datetime | None = None) -> list[int]:
    """Check newest 100 PRs. Process at most ONE safe merge per invocation."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("invalid repository")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current = main_sha(repo)
    if not exact_sha(current):
        raise UnsafeAutoMerge("invalid main source SHA")
    open_prs = api(f"repos/{repo}/pulls?state=open&per_page={MAX_OPEN_SCAN}&sort=updated&direction=desc")
    if not isinstance(open_prs, list):
        raise UnsafeAutoMerge("invalid open PR response")

    for brief in open_prs:
        number = brief.get("number")
        if not isinstance(number, int) or number < 1:
            continue
        pr = latest_pr(repo, number)
        eligible = check_candidate(repo, pr, current, now)
        if eligible is None:
            continue
        role, expected_head = eligible
        print(f"SAFE_AUTO_MERGE_ELIGIBLE: PR #{number} role={role} head={expected_head}")
        if not apply:
            print("SAFE_AUTO_MERGE_DRY_RUN: no PR state or main changed")
            return [number]

        # The real token-privileged action happens only after a new exact-head
        # main/PR/CI verification. No PR files are executed or checked out.
        if main_sha(repo) != current:
            print(f"SAFE_AUTO_MERGE_REFUSED_MOVED_MAIN: PR #{number}")
            return []
        fresh = latest_pr(repo, number)
        if fresh["head"]["sha"] != expected_head or check_candidate(repo, fresh, current, now) is None:
            print(f"SAFE_AUTO_MERGE_REFUSED_CHANGED_PR: PR #{number}")
            return []

        mark_ready(repo, number)
        ready_pr = latest_pr(repo, number)
        if (ready_pr.get("draft") is not False or
            ready_pr.get("head", {}).get("sha") != expected_head or
            ready_pr.get("base", {}).get("sha") != current or
            main_sha(repo) != current):
            raise UnsafeAutoMerge("PR or main changed after ready-for-review")

        # sha locks merge to the exact tested PR head. Only squash, never force.
        result = api(
            f"repos/{repo}/pulls/{number}/merge", method="PUT",
            payload={"sha": expected_head, "merge_method": "squash"},
        )
        if result.get("merged") is not True or not exact_sha(result.get("sha")):
            raise UnsafeAutoMerge("GitHub did not confirm a successful exact-head merge")
        print(f"SAFE_AUTO_MERGE_SUCCESS: PR #{number} source={expected_head} commit={result['sha']}")
        return [number]

    print("SAFE_AUTO_MERGE_HEALTHY_NOOP: no eligible bot PR with verified six-check CI")
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="actually merge strict eligible bot PR")
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY", ""))
    args = parser.parse_args()
    try:
        run(args.repo, apply=args.apply)
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"SAFE_AUTO_MERGE_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
