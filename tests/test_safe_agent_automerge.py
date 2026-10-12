"""Safety tests for exact-head autonomous engineering merges.

All tests are synthetic and offline. They never talk to GitHub or merge PRs.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import shutil

import pytest

import safe_agent_automerge as auto


REPO = "MaksimBlud/football-ai"
BASE = "b" * 40
HEAD = "a" * 40
NOW = datetime(2026, 10, 12, 5, tzinfo=timezone.utc)
BRANCH = "dev/backend-safe-ci-20261012"


def bot_pr():
    return {
        "number": 700,
        "title": "draft(agents): staged backend change from " + BRANCH,
        "state": "open", "draft": True, "merged_at": None, "mergeable": True,
        "mergeable_state": "clean",
        "user": {"login": "github-actions[bot]"},
        "base": {"ref": "main", "sha": BASE, "repo": {"full_name": REPO}},
        "head": {"ref": BRANCH, "sha": HEAD, "repo": {"full_name": REPO}},
        "requested_reviewers": [], "requested_teams": [], "labels": [],
    }


def comparison():
    return {
        "status": "ahead", "ahead_by": 1, "behind_by": 0,
        "base_commit": {"sha": BASE},
        "commits": [{"sha": HEAD}],
        "files": [
            {"filename": "product_snapshot_store.py", "status": "modified", "changes": 10},
            {"filename": "tests/test_product_snapshot_store.py", "status": "modified", "changes": 10},
        ],
    }


def good_checks():
    return {"check_runs": [
        {
            "name": name,
            "head_sha": HEAD,
            "status": "completed",
            "conclusion": "success",
            "app": {"slug": "github-actions"},
            "details_url": f"https://github.com/{REPO}/actions/runs/900/job/42",
        }
        for name in auto.EXPECTED_CHECKS
    ]}


@pytest.mark.parametrize("tamper", [
    lambda p: p.update(user={"login": "external-user"}),
    lambda p: p.update(title="feat: arbitrary feature"),
    lambda p: p.update(draft=False),
    lambda p: p.update(state="closed"),
    lambda p: p.update(merged_at="2026-10-12T04:00:00Z"),
    lambda p: p["head"].update(ref="feature/untrusted"),
    lambda p: p["head"].update(sha="malformed"),
    lambda p: p["head"]["repo"].update(full_name="other/repo"),
    lambda p: p["base"]["repo"].update(full_name="other/repo"),
    lambda p: p["base"].update(ref="production"),
    lambda p: p.update(requested_reviewers=[{"login": "security-reviewer"}]),
    lambda p: p.update(requested_teams=[{"name": "admins"}]),
    lambda p: p.update(labels=[{"name": "no-automerge"}]),
    lambda p: p.update(labels=[{"name": "security-review"}]),
])
def test_trust_gate_blocks_unapproved_prs(tamper):
    pr = bot_pr()
    tamper(pr)
    assert auto.candidate_role(pr, REPO) is None


def test_trusted_bot_role_is_scoped_to_relay_only():
    assert auto.candidate_role(bot_pr(), REPO) == "backend"


@pytest.mark.parametrize("mutate", [
    lambda c: c.update(behind_by=1),
    lambda c: c.update(ahead_by=0),
    lambda c: c.update(ahead_by=7),
    lambda c: c.update(status="diverged"),
    lambda c: c["base_commit"].update(sha="c" * 40),
    lambda c: c["commits"][-1].update(sha="c" * 40),
    lambda c: c["files"].append({"filename": "football_model_xgboost_elo.pkl", "status": "added", "changes": 1}),
    lambda c: c["files"].append({"filename": ".github/workflows/production.yml", "status": "added", "changes": 1}),
    lambda c: c["files"].append({"filename": "config.py", "status": "modified", "changes": 1}),
    lambda c: c["files"].append({"filename": "supabase/migrations/sensitive.sql", "status": "added", "changes": 1}),
    lambda c: c["files"].append({"filename": "static/index_v2.html", "status": "modified", "changes": 1}),
    lambda c: c["files"].append({"filename": "odds_snapshots.py", "status": "modified", "changes": 1}),
    lambda c: c["files"][1].update(status="removed"),
    lambda c: c["files"][0].update(changes=500),
])
def test_compare_rejects_behind_production_or_nonallowlisted_code(mutate):
    c = comparison()
    mutate(c)
    assert not auto.safe_comparison(bot_pr(), c, BASE, "backend")


def test_compare_rejects_main_movement_and_nonmergeable_pr():
    pr = bot_pr()
    assert auto.safe_comparison(pr, comparison(), BASE, "backend")
    assert not auto.safe_comparison(pr, comparison(), "c" * 40, "backend")
    pr["mergeable"] = False
    assert not auto.safe_comparison(pr, comparison(), BASE, "backend")
    pr["mergeable"] = True
    pr["mergeable_state"] = "blocked"
    assert not auto.safe_comparison(pr, comparison(), BASE, "backend")


@pytest.mark.parametrize("mutate", [
    lambda checks: checks["check_runs"].pop(),
    lambda checks: checks["check_runs"][0].update(conclusion="failure"),
    lambda checks: checks["check_runs"][0].update(status="in_progress"),
    lambda checks: checks["check_runs"][0].update(head_sha="c" * 40),
    lambda checks: checks["check_runs"][0]["app"].update(slug="untrusted-app"),
    lambda checks: checks["check_runs"][0].update(details_url="https://attacker.invalid/check/1"),
    lambda checks: checks["check_runs"].append(deepcopy(checks["check_runs"][0])),
])
def test_six_real_head_checks_mandatory_fail_closed(mutate):
    checks = good_checks()
    mutate(checks)
    assert not auto.pinned_checks_green(checks, HEAD, REPO)


def test_exact_six_passed_are_green():
    assert len(auto.EXPECTED_CHECKS) == 6
    assert auto.pinned_checks_green(good_checks(), HEAD, REPO)


class FakeGitHub:
    def __init__(self, *, pr=None, check_payload=None, commit_age_hours=1):
        self.pr = deepcopy(pr or bot_pr())
        self.checks = deepcopy(check_payload or good_checks())
        self.current_main = BASE
        self.comparison = comparison()
        self.calls = []
        self.merge_calls = []
        self.ready_calls = []
        self.commit_date = (NOW - timedelta(hours=commit_age_hours)).isoformat()

    def api(self, endpoint, method="GET", payload=None):
        self.calls.append((endpoint, method))
        if endpoint == f"repos/{REPO}/branches/main":
            return {"commit": {"sha": self.current_main}}
        if endpoint == f"repos/{REPO}/pulls?state=open&per_page=100&sort=updated&direction=desc":
            return [{"number": self.pr["number"]}]
        if endpoint == f"repos/{REPO}/pulls/{self.pr['number']}":
            return deepcopy(self.pr)
        if endpoint == f"repos/{REPO}/commits/{HEAD}":
            return {"commit": {"committer": {"date": self.commit_date}}}
        if endpoint == f"repos/{REPO}/compare/main...{HEAD}":
            return deepcopy(self.comparison)
        if endpoint == f"repos/{REPO}/commits/{HEAD}/check-runs?per_page=100":
            return deepcopy(self.checks)
        if endpoint == f"repos/{REPO}/pulls/{self.pr['number']}/merge":
            self.merge_calls.append(payload)
            assert method == "PUT"
            assert payload == {"sha": HEAD, "merge_method": "squash"}
            self.current_main = "d" * 40
            return {"merged": True, "sha": self.current_main}
        raise AssertionError("unrecognized GitHub API path: " + endpoint)

    def ready(self, repo, number):
        assert repo == REPO and number == self.pr["number"]
        self.ready_calls.append(number)
        self.pr["draft"] = False


def test_default_run_is_dry_without_any_mutation(monkeypatch):
    fake = FakeGitHub()
    monkeypatch.setattr(auto, "api", fake.api)
    monkeypatch.setattr(auto, "mark_ready", fake.ready)
    assert auto.run(REPO, now=NOW) == [700]
    assert not fake.ready_calls
    assert not fake.merge_calls


def test_authorized_run_merges_once_on_exact_head_after_second_verification(monkeypatch):
    fake = FakeGitHub()
    monkeypatch.setattr(auto, "api", fake.api)
    monkeypatch.setattr(auto, "mark_ready", fake.ready)
    assert auto.run(REPO, now=NOW, apply=True) == [700]
    assert fake.ready_calls == [700]
    assert fake.merge_calls == [{"sha": HEAD, "merge_method": "squash"}]
    assert fake.calls.count((f"repos/{REPO}/compare/main...{HEAD}", "GET")) == 2
    assert fake.calls.count((f"repos/{REPO}/commits/{HEAD}/check-runs?per_page=100", "GET")) == 2


def test_rejects_stale_bot_head_before_ready(monkeypatch):
    fake = FakeGitHub(commit_age_hours=49)
    monkeypatch.setattr(auto, "api", fake.api)
    monkeypatch.setattr(auto, "mark_ready", fake.ready)
    assert auto.run(REPO, now=NOW, apply=True) == []
    assert not fake.ready_calls and not fake.merge_calls


def test_rejects_other_authors_and_missing_cis_without_any_mutation(monkeypatch):
    fake = FakeGitHub()
    fake.pr["user"]["login"] = "user"
    monkeypatch.setattr(auto, "api", fake.api)
    monkeypatch.setattr(auto, "mark_ready", fake.ready)
    assert auto.run(REPO, now=NOW, apply=True) == []
    assert not fake.merge_calls

    fake = FakeGitHub()
    fake.checks["check_runs"][0]["conclusion"] = "failure"
    monkeypatch.setattr(auto, "api", fake.api)
    assert auto.run(REPO, now=NOW, apply=True) == []
    assert not fake.ready_calls and not fake.merge_calls


def test_main_move_on_recheck_blocks_merge(monkeypatch):
    fake = FakeGitHub()
    orig_api = fake.api
    count = [0]

    def moved_main(endpoint, method="GET", payload=None):
        if endpoint == f"repos/{REPO}/branches/main":
            count[0] += 1
            if count[0] == 2:
                fake.current_main = "c" * 40
        return orig_api(endpoint, method, payload)

    monkeypatch.setattr(auto, "api", moved_main)
    monkeypatch.setattr(auto, "mark_ready", fake.ready)
    assert auto.run(REPO, now=NOW, apply=True) == []
    assert not fake.ready_calls and not fake.merge_calls


def test_new_pr_head_on_recheck_blocks_merge(monkeypatch):
    fake = FakeGitHub()
    orig_api = fake.api
    count = [0]

    def pushed_head(endpoint, method="GET", payload=None):
        if endpoint == f"repos/{REPO}/pulls/700":
            count[0] += 1
            if count[0] == 2:
                fake.pr["head"]["sha"] = "e" * 40
        return orig_api(endpoint, method, payload)

    monkeypatch.setattr(auto, "api", pushed_head)
    monkeypatch.setattr(auto, "mark_ready", fake.ready)
    assert auto.run(REPO, now=NOW, apply=True) == []
    assert not fake.ready_calls and not fake.merge_calls


def test_no_commit_or_release_of_arbitrary_pr_data(monkeypatch):
    fake = FakeGitHub()
    monkeypatch.setattr(auto, "api", fake.api)
    monkeypatch.setattr(auto, "mark_ready", fake.ready)
    auto.run(REPO, now=NOW, apply=True)
    assert all("/deploy" not in p and "/actions/workflows/" not in p
               for p, _ in fake.calls)


def test_trusted_workflow_has_proper_trigger_and_permission_split():
    wf = Path(".github/workflows/safe-engineering-automerge.yml").read_text(encoding="utf-8")
    assert "workflow_run:" in wf
    assert "Product PR Validation" in wf
    assert "Eredivisie PR Validation" in wf
    assert "targeted-research-tests" not in wf  # workflow names, not job aliases
    assert "cancel-in-progress: false" in wf
    assert "ref: main" in wf
    assert "persist-credentials: false" in wf
    assert "contents: write" in wf and "pull-requests: write" in wf
    assert "if: github.event_name != 'pull_request'" in wf
    assert "GH_TOKEN: " in wf
    assert "--apply" in wf
    assert "vercel" not in wf.lower()
    assert "supabase" not in wf.lower()


def test_script_syntax():
    if shutil.which("python") is None:
        pytest.skip("Python executable missing")
    result = subprocess.run(
        ["python", "-m", "py_compile", "safe_agent_automerge.py"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
