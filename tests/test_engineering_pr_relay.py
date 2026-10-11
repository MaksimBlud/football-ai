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
    assert not eligible("backend", branch, comparison("backend", behind_by=1), "a" * 40)
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


def mocked_api(role="frontend", complete=True, posted=None):
    main, head = "a" * 40, "b" * 40
    def fake_api(url, method="GET", payload=None):
        if method == "POST":
            assert posted is not None
            posted.append(payload)
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
            return comparison(role, files=safe_files(role) if complete else [safe_files(role)[1]])
        if url.startswith("repos/MaksimBlud/football-ai/pulls?"):
            return []
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
    assert len(posted) == 1
    assert posted[0]["draft"] is True
    assert posted[0]["base"] == "main"
    assert "GITHUB_TOKEN" in posted[0]["body"]
