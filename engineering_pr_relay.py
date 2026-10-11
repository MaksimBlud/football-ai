"""Conservative GitHub Actions relay from finished agent branches to draft PRs.

No AI inference, source mutation, automatic merging, or production access.
A draft PR created using GITHUB_TOKEN may not trigger pull_request CI: report
that limitation explicitly rather than treating PR creation as green CI.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
import re
import subprocess
import sys
from urllib.parse import quote

ROLE_FILES = {
    "frontend": {
        "code": frozenset({"static/match.html"}),
        "tests": frozenset({
            "tests/test_product_ui_contract.py",
            "tests/test_match_detail_error_accessibility.py",
        }),
        "prefix": "dev/ui-",
        "issue": 582,
    },
    "backend": {
        "code": frozenset({"product_snapshot_store.py"}),
        "tests": frozenset({"tests/test_product_snapshot_store.py"}),
        "prefix": "dev/backend-",
        "issue": 581,
    },
}
MAX_FILES = 3
MAX_CHANGED_LINES = 450
MAX_BRANCH_AGE = timedelta(hours=4)
MAX_BEHIND_COMMITS = 6  # Allow reviewable drift; merge is still forbidden without full CI.

# Existing on-PR validation contracts, deliberately reused rather than weakening CI.
# GitHub Actions GITHUB_TOKEN-created PRs do not fire pull_request workflows.
CI_WORKFLOWS = (
    ("product-pr-validation.yml", "product-contract-tests"),
    ("research-pr-validation.yml", "targeted-research-tests"),
    ("bundesliga-pr-validation.yml", "bundesliga-validation"),
    ("ligue1-pr-validation.yml", "ligue1-validation"),
    ("serie-a-pr-validation.yml", "serie-a-validation"),
    ("eredivisie-pr-validation.yml", "validate"),
)


def qualified_branch(branch: str, role: str) -> bool:
    """No arbitrary branch names or non-product roles are accepted."""
    prefix = ROLE_FILES[role]["prefix"]
    return branch.startswith(prefix) and bool(
        re.fullmatch(r"[A-Za-z0-9/_-]{1,105}", branch)
    )


def safe_change_set(role: str, files: list[dict]) -> bool:
    """Both implementation and tests required; no deletions or forbidden paths."""
    spec = ROLE_FILES[role]
    if not 2 <= len(files) <= MAX_FILES:
        return False
    names = [f.get("filename") for f in files]
    if len(set(names)) != len(names):
        return False
    if not spec["code"].intersection(names) or not spec["tests"].intersection(names):
        return False
    for f in files:
        if f.get("filename") not in spec["code"] | spec["tests"]:
            return False
        if f.get("status") not in {"modified", "added"}:
            return False
        if f.get("filename") in spec["code"] and f.get("status") != "modified":
            return False
    return sum(int(f.get("changes") or 0) for f in files) <= MAX_CHANGED_LINES


def eligible(role: str, branch: str, comparison: dict, main_sha: str) -> bool:
    """Permit small main drift for DRAFT review; never merge or rebase automatically."""
    return (
        qualified_branch(branch, role)
        and isinstance(comparison.get("behind_by"), int)
        and 0 <= comparison["behind_by"] <= MAX_BEHIND_COMMITS
        and 1 <= comparison.get("ahead_by", 0) <= 6
        and comparison.get("base_commit", {}).get("sha") == main_sha
        and safe_change_set(role, comparison.get("files", []))
    )


def fresh_commit(committed_at: str, now: datetime) -> bool:
    try:
        parsed = datetime.fromisoformat(committed_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError, TypeError):
        return False
    if parsed.tzinfo is None:
        return False
    age = now - parsed.astimezone(timezone.utc)
    return timedelta(0) <= age <= MAX_BRANCH_AGE


def api(endpoint: str, method: str = "GET", payload: dict | None = None):
    command = ["gh", "api", "--method", method, endpoint]
    if payload is not None:
        command += ["--input", "-"]
    result = subprocess.run(
        command,
        input=json.dumps(payload) if payload is not None else None,
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"GitHub {method} {endpoint} failed: {result.stderr.strip()[:700]}"
        )
    return json.loads(result.stdout) if result.stdout.strip() else {}




def bot_draft_matches(pr: dict, branch: str, head_sha: str) -> bool:
    """Do not use relay privileges on a human-authored or mismatched PR."""
    return (
        pr.get("state") == "open"
        and pr.get("draft") is True
        and pr.get("user", {}).get("login") == "github-actions[bot]"
        and pr.get("head", {}).get("ref") == branch
        and pr.get("head", {}).get("sha") == head_sha
        and pr.get("base", {}).get("ref") == "main"
    )


class LegacyBranchDispatchBlocked(RuntimeError):
    """Branch predates pinned CI workflow_dispatch and requires safe rebasing."""


def dispatch_exact_head_ci(repo: str, branch: str, head_sha: str) -> int:
    """Dispatch actual existing validation workflows (never forge check statuses)."""
    result = api(f"repos/{repo}/commits/{head_sha}/check-runs?per_page=100")
    observed = {
        run.get("name") for run in result.get("check_runs", [])
        if run.get("head_sha") == head_sha
    }
    count = 0
    for workflow, check_name in CI_WORKFLOWS:
        if check_name in observed:
            print(f"PR_RELAY_CI_ALREADY_TRIGGERED: {check_name} {head_sha}")
            continue
        # A dispatch is a trusted GitHub action supported with GITHUB_TOKEN.
        # Workflow input independently refuses any mismatch of github.sha.
        try:
            api(
                f"repos/{repo}/actions/workflows/{workflow}/dispatches",
                method="POST",
                payload={"ref": branch, "inputs": {"expected_head_sha": head_sha}},
            )
        except RuntimeError as exc:
            if (
                "HTTP 422" in str(exc)
                and "does not have 'workflow_dispatch' trigger" in str(exc)
            ):
                raise LegacyBranchDispatchBlocked(
                    f"PR_RELAY_CI_LEGACY_REF_BLOCKED {branch} {head_sha}: "
                    "ref predates workflow_dispatch; preserve draft, "
                    "do not auto-rebase or create synthetic success."
                ) from exc
            raise
        count += 1
        print(f"PR_RELAY_CI_DISPATCHED: {workflow} {head_sha}")
    return count

def relay(repo: str, checkout_sha: str, *, dry_run: bool = False) -> list[str]:
    now = datetime.now(timezone.utc)
    current_main = api(f"repos/{repo}/branches/main")["commit"]["sha"]
    if current_main != checkout_sha:
        print(f"PR_RELAY_SKIP_MAIN_MOVED: {checkout_sha} -> {current_main}")
        return []

    owner = repo.split("/")[0]
    results = []
    for role, spec in ROLE_FILES.items():
        # Use prefix-matching Git refs instead of scanning every historic branch.
        prefix = spec["prefix"]
        refs = api(f"repos/{repo}/git/matching-refs/heads/{prefix}")
        for ref in sorted(refs, key=lambda r: r.get("ref", ""), reverse=True)[:45]:
            full_ref = ref.get("ref", "")
            if not full_ref.startswith("refs/heads/"):
                continue
            branch = full_ref.removeprefix("refs/heads/")
            if not qualified_branch(branch, role):
                continue
            head_sha = ref.get("object", {}).get("sha")
            if not re.fullmatch(r"[0-9a-f]{40}", str(head_sha)):
                continue

            commit = api(f"repos/{repo}/commits/{head_sha}")
            if not fresh_commit(commit.get("commit", {}).get("committer", {}).get("date"), now):
                continue

            comparison = api(
                f"repos/{repo}/compare/main...{quote(branch, safe='/')}"
            )
            if not eligible(role, branch, comparison, current_main):
                continue

            existing = api(
                f"repos/{repo}/pulls?state=all&head="
                + quote(f"{owner}:{branch}", safe="")
            )
            if existing and (
                len(existing) != 1
                or not bot_draft_matches(existing[0], branch, head_sha)
            ):
                continue

            # Prevent stale-branch / concurrent-main races immediately before write.
            new_main = api(f"repos/{repo}/branches/main")["commit"]["sha"]
            latest_head = api(
                f"repos/{repo}/git/ref/heads/{quote(branch, safe='/')}"
            )["object"]["sha"]
            if new_main != current_main or latest_head != head_sha:
                print(f"PR_RELAY_SKIP_RACE: {branch}")
                continue

            title = f"draft(agents): staged {role} change from {branch}"
            body = (
                f"Safe deterministic **draft-only** handoff for #{spec['issue']}.\n\n"
                f"- Source agent branch: \u0060{branch}\u0060\n"
                f"- Exact head at relay: \u0060{head_sha}\u0060\n"
                f"- Base main: \u0060{current_main}\u0060\n"
                f"- Checked: recent head, main lag={comparison['behind_by']} "
                f"(max {MAX_BEHIND_COMMITS}); bounded scope, product code "
                "AND regression tests, no production artifacts.\n\n"
                "**Not an AI run, not an evaluation or passing-CI claim.** "
                "GitHub's GITHUB_TOKEN-created PR may not trigger pull_request "
                "workflows; a separate real CI proof on the exact PR head is required. "
                "Never merge automatically; never use an unverified draft as production.\n"
            )
            if dry_run:
                print(f"PR_RELAY_DRY_RUN: {role} {branch} {head_sha}")
                results.append(branch)
            else:
                if existing:
                    pr = existing[0]
                    print(f"PR_RELAY_RESUMED_BOT_DRAFT: {pr['html_url']}")
                else:
                    try:
                        pr = api(
                            f"repos/{repo}/pulls", method="POST",
                            payload={"title": title, "head": branch,
                                     "base": "main", "draft": True, "body": body},
                        )
                    except RuntimeError as exc:
                        raise RuntimeError(
                            f"PR_RELAY_WRITE_BLOCKED for {branch}: {exc}. "
                            "For GitHub HTTP 403, check repository Settings > Actions > "
                            "General > Workflow permissions > "
                            "'Allow GitHub Actions to create and approve pull requests'. "
                            "No unsafe token or CI bypass was attempted."
                        ) from exc
                    print(f"PR_RELAY_DRAFT_CREATED: {pr['html_url']}")
                # No merge is attempted: actual six CI workflows decide readiness.
                try:
                    dispatched = dispatch_exact_head_ci(repo, branch, head_sha)
                except LegacyBranchDispatchBlocked as exc:
                    print(str(exc))
                    # Keep bot draft open and scan next eligible agent branch.
                    continue
                results.append(pr["html_url"])
                print(f"PR_RELAY_CI_REQUEST_COUNT: {dispatched} {head_sha}")

            # At most one candidate per role per run.
            break
    return results


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    sha = os.environ.get("GITHUB_SHA", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("Missing or unsafe GITHUB_REPOSITORY")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Missing or unsafe GITHUB_SHA")
    if not os.environ.get("GH_TOKEN"):
        raise ValueError("Missing GH_TOKEN")
    results = relay(repo, sha, dry_run="--dry-run" in sys.argv)
    print(
        f"PR_RELAY_SUMMARY: {len(results)} draft handoffs. "
        "Check actual exact-head workflow_dispatch outcomes before any merge; "
        "NO_AUTO_MERGE, NO_AI_API, NO_PRODUCTION_WRITE."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
