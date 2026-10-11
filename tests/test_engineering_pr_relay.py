"""Fail-closed and no-merge contracts for unattended draft PR relay."""
from datetime import datetime, timedelta, timezone
import pytest

import engineering_pr_relay as relay_mod
from engineering_pr_relay import (
    ROLE_FILES, eligible, fresh_commit, qualified_branch, relay, safe_change_set,
)


def safe_files(role):
    spec = ROLE_FILES[role]
    return [
        {"filename": sorted(spec["code"])[0], "status": "modified", "changes": 12},
        {"filename": sorted(spec["tests"])[0], "status": "modified", "changes": 19},
    ]


def comparison(role, **changes):
    result = {
        "behind_by": 0, "ahead_by": 2,
        "base_commit": {"sha": "a" * 40},
        "files": safe_files(role),
    }
    result.update(changes)
    return result


@pytest.mark.parametrize("role,branch", [
    ("frontend", "dev/ui-match-safety-20261011"),
    ("backend", "dev/backend-581-fixture-safety"),
])
def test_complete_fresh_scope_allowed(role, branch):
    assert qualified_branch(branch, role)
    assert eligible(role, branch, comparison(role), "a" * 40)


def test_code_plus_tests_are_required_no_production_changes():
    assert not safe_change_set("backend", [safe_files("backend")[1]])
    assert not safe_change_set("frontend", [safe_files("frontend")[0]])
    assert not safe_change_set("backend", safe_files("backend") + [
        {"filename": "football_model_xgboost_elo.pkl", "status": "modified", "changes": 1},
    ])
    assert not safe_change_set("frontend", safe_files("frontend") + [
        {"filename": ".github/workflows/ci.yml", "status": "modified", "changes": 1},
    ])
    assert not safe_change_set("frontend", [
        {"filename": "static/match.html", "status": "removed", "changes": 2},
        safe_files("frontend")[1],
    ])


def test_behind_main_malformed_branch_and_oversize_are_skipped():
    branch = "dev/backend-581-ready"
    assert eligible("backend", branch, comparison("backend", behind_by=1), "a" * 40)
    assert eligible("backend", branch, comparison("backend", behind_by=6), "a" * 40)
    assert not eligible("backend", branch, comparison("backend", behind_by=7), "a" * 40)
    assert not eligible("backend", branch, comparison("backend", behind_by=-1), "a" * 40)
    assert not eligible("backend", branch, comparison("backend", behind_by=None), "a" * 40)
    assert not eligible("backend", branch, comparison("backend", ahead_by=0), "a" * 40)
    assert not eligible("backend", branch, comparison("backend", ahead_by=7), "a" * 40)
    assert not eligible("backend", branch, comparison("backend", base_commit={"sha":"b"*40}), "a" * 40)
    assert not eligible("backend", "dev/backend-../../main", comparison("backend"), "a" * 40)
    assert not eligible("backend", "research/other", comparison("backend"), "a" * 40)
    oversized = safe_files("backend")
    oversized[0]["changes"] = 451
    assert not safe_change_set("backend", oversized)


def test_only_recent_commits_are_eligible():
    now = datetime(2026, 10, 11, 5, tzinfo=timezone.utc)
    assert fresh_commit((now - timedelta(hours=3)).isoformat(), now)
    assert not fresh_commit((now - timedelta(hours=5)).isoformat(), now)
    assert not fresh_commit((now + timedelta(minutes=1)).isoformat(), now)
    assert not fresh_commit("2026-10-11T04:00:00", now)
    assert not fresh_commit("invalid", now)


def mocked_api(role="frontend", complete=True, posted=None, behind=0, existing_bot=False, completed_checks=()):
    main, head = "a" * 40, "b" * 40
    def fake_api(url, method="GET", payload=None):
        if method == "POST":
            assert posted is not None
            posted.append((url, payload))
            if "/actions/workflows/" in url and url.endswith("/dispatches"):
                return {}
            assert url.endswith("/pulls")
            return {"html_url": "https://github.com/MaksimBlud/football-ai/pull/700"}
        if url.endswith("/branches/main"):
            return {"commit":{"sha":main}}
        if "/matching-refs/heads/dev/ui-" in url:
            return [{"ref": "refs/heads/dev/ui-new-good", "object":{"sha":head}}]
        if "/matching-refs/heads/dev/backend-" in url:
            return []
        if url.endswith("/commits/" + head):
            return {"commit":{"committer":{"date":(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()}}}
        if "/compare/main..." in url:
            return comparison(role, behind_by=behind, files=safe_files(role) if complete else [safe_files(role)[1]])
        if url.startswith("repos/MaksimBlud/football-ai/pulls?"):
            if not existing_bot:
                return []
            return [{
                "state": "open", "draft": True,
                "user": {"login": "github-actions[bot]"},
                "head": {"ref": "dev/ui-new-good", "sha": head},
                "base": {"ref": "main"},
                "html_url": "https://github.com/MaksimBlud/football-ai/pull/700",
            }]
        if url.endswith("/commits/" + head + "/check-runs?per_page=100"):
            return {"check_runs": [
                {"name": name, "head_sha": head} for name in completed_checks
            ]}
        if "/git/ref/heads/" in url:
            return {"object":{"sha":head}}
        raise AssertionError("Unexpected GitHub path " + url)
    return fake_api


def test_test_only_branches_never_create_pr(monkeypatch):
    monkeypatch.setattr(relay_mod, "api", mocked_api(complete=False))
    assert relay("MaksimBlud/football-ai", "a" * 40) == []


def test_dry_run_never_posts(monkeypatch):
    monkeypatch.setattr(relay_mod, "api", mocked_api())
    assert relay("MaksimBlud/football-ai", "a" * 40, dry_run=True) == [
        "dev/ui-new-good"
    ]


def test_real_handoff_is_draft_only(monkeypatch):
    posted = []
    monkeypatch.setattr(relay_mod, "api", mocked_api(posted=posted))
    assert relay("MaksimBlud/football-ai", "a" * 40) == [
        "https://github.com/MaksimBlud/football-ai/pull/700"
    ]
    assert len(posted) == 7  # one draft PR plus six real exact-head CI dispatches
    assert posted[0][0].endswith("/pulls")
    assert posted[0][1]["draft"] is True
    assert posted[0][1]["base"] == "main"
    assert "GITHUB_TOKEN" in posted[0][1]["body"]
    for url, payload in posted[1:]:
        assert url.endswith("/dispatches")
        assert payload["ref"] == "dev/ui-new-good"
        assert payload["inputs"]["expected_head_sha"] == "b" * 40


def test_relay_can_create_draft_for_recent_branch_behind_main(monkeypatch):
    """A recent diverged branch gets review, not automatic rebase or merge."""
    posted = []
    monkeypatch.setattr(relay_mod, "api", mocked_api(behind=2, posted=posted))
    assert relay("MaksimBlud/football-ai", "a" * 40) == [
        "https://github.com/MaksimBlud/football-ai/pull/700"
    ]
    assert len(posted) == 7
    assert posted[0][1]["draft"] is True
    assert "main lag=2" in posted[0][1]["body"]


def test_relay_rejects_branch_beyond_main_lag_limit(monkeypatch):
    posted = []
    monkeypatch.setattr(relay_mod, "api", mocked_api(behind=7, posted=posted))
    assert relay("MaksimBlud/football-ai", "a" * 40) == []
    assert not posted


def test_403_gate_names_exact_repository_toggle(monkeypatch):
    """Actionable blocker, without any fallback token, extra API calls or merge."""
    original = mocked_api(posted=[])
    posts = []

    def rejects_actions_pr(url, method="GET", payload=None):
        if method == "POST":
            posts.append(payload)
            raise RuntimeError(
                "GitHub POST pulls failed: GitHub Actions is not permitted "
                "to create or approve pull requests (HTTP 403)"
            )
        return original(url, method=method, payload=payload)

    monkeypatch.setattr(relay_mod, "api", rejects_actions_pr)
    with pytest.raises(RuntimeError, match="PR_RELAY_WRITE_BLOCKED") as error:
        relay("MaksimBlud/football-ai", "a" * 40)
    assert "Settings > Actions > General > Workflow permissions" in str(error.value)
    assert "Allow GitHub Actions to create and approve pull requests" in str(error.value)
    assert len(posts) == 1
    assert posts[0]["draft"] is True



def test_resume_exact_existing_bot_draft_without_duplicate_pr(monkeypatch):
    posted = []
    monkeypatch.setattr(
        relay_mod, "api", mocked_api(posted=posted, existing_bot=True)
    )
    assert relay("MaksimBlud/football-ai", "a" * 40) == [
        "https://github.com/MaksimBlud/football-ai/pull/700"
    ]
    assert len(posted) == 6
    assert all("/actions/workflows/" in url for url, _ in posted)


def test_existing_bot_draft_never_re_dispatches_completed_checks(monkeypatch):
    posted = []
    completed = tuple(name for _, name in relay_mod.CI_WORKFLOWS)
    monkeypatch.setattr(
        relay_mod, "api", mocked_api(
            posted=posted, existing_bot=True, completed_checks=completed,
        )
    )
    assert len(relay("MaksimBlud/football-ai", "a" * 40)) == 1
    assert posted == []


def test_never_operate_on_human_or_wrong_head_pr(monkeypatch):
    original = mocked_api(posted=[])
    calls = []

    def fake_api(url, method="GET", payload=None):
        if "/pulls?state=all&head=" in url:
            return [{
                "state": "open", "draft": True,
                "user": {"login": "human-user"},
                "head": {"ref": "dev/ui-new-good", "sha": "b" * 40},
                "base": {"ref": "main"},
            }]
        if method == "POST":
            calls.append((url, payload))
            raise AssertionError("never write to human PR")
        return original(url, method=method, payload=payload)

    monkeypatch.setattr(relay_mod, "api", fake_api)
    assert relay("MaksimBlud/football-ai", "a" * 40) == []
    assert calls == []


def test_api_accepts_empty_204_response(monkeypatch):
    from types import SimpleNamespace

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(relay_mod.subprocess, "run", fake_run)
    assert relay_mod.api("repos/owner/repo/actions/workflows/test.yml/dispatches",
                         method="POST", payload={"ref": "feature"}) == {}



def test_legacy_dispatch_422_preserves_draft_and_skips_safely(monkeypatch):
    posted = []
    original = mocked_api(posted=posted, existing_bot=True)

    def refuses_legacy_workflow(url, method="GET", payload=None):
        if method == "POST" and "/actions/workflows/" in url:
            raise RuntimeError(
                "GitHub POST dispatches failed: "
                "Workflow does not have 'workflow_dispatch' trigger (HTTP 422)"
            )
        return original(url, method=method, payload=payload)

    monkeypatch.setattr(relay_mod, "api", refuses_legacy_workflow)
    assert relay("MaksimBlud/football-ai", "a" * 40) == []
    # No fabricated result, no new PR, no credential or merge bypass.
    assert not posted


def test_unexpected_ci_dispatch_failure_remains_visible(monkeypatch):
    original = mocked_api(posted=[], existing_bot=True)

    def refuses_all(url, method="GET", payload=None):
        if method == "POST" and "/actions/workflows/" in url:
            raise RuntimeError("GitHub unexpected 401")
        return original(url, method=method, payload=payload)

    monkeypatch.setattr(relay_mod, "api", refuses_all)
    with pytest.raises(RuntimeError, match="401"):
        relay("MaksimBlud/football-ai", "a" * 40)
