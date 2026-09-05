from types import SimpleNamespace

import pytest

import odds_api_budget_guard as guard


class FakeSession:
    def __init__(self, *, status_code=200, remaining="195", used="305", last="0"):
        self.status_code = status_code
        self.headers = {
            "x-requests-remaining": remaining,
            "x-requests-used": used,
            "x-requests-last": last,
        }
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append((url, dict(params), timeout))
        return SimpleNamespace(
            status_code=self.status_code,
            headers=self.headers,
            text="error" if self.status_code != 200 else "[]",
        )


def test_budget_allows_operation_above_reserve(monkeypatch):
    monkeypatch.setattr(guard, "THE_ODDS_API_KEY", "test-key")
    session = FakeSession(remaining="195")
    result = guard.check_budget(max_cost=4, session=session)
    assert result["allowed"] is True
    assert result["minimum_required_credits"] == 104
    assert result["hard_reserve_credits"] == 100
    assert result["paid_provider_requests"] == 0
    assert result["preflight_cost_credits"] == 0
    assert len(session.calls) == 1
    assert session.calls[0][0].endswith("/sports/")


def test_budget_blocks_before_crossing_hard_reserve(monkeypatch):
    monkeypatch.setattr(guard, "THE_ODDS_API_KEY", "test-key")
    result = guard.check_budget(max_cost=2, session=FakeSession(remaining="101"))
    assert result["allowed"] is False
    assert result["reason"] == "HARD_RESERVE_PROTECTED"
    assert result["minimum_required_credits"] == 102


def test_budget_boundary_is_allowed():
    result = guard.evaluate_budget(remaining=101, max_cost=1, reserve=100)
    assert result["allowed"] is True


def test_invalid_cost_fails_closed_without_provider_call(monkeypatch):
    monkeypatch.setattr(guard, "THE_ODDS_API_KEY", "test-key")
    session = FakeSession()
    with pytest.raises(ValueError, match="max_cost"):
        guard.evaluate_budget(remaining=195, max_cost=0)
    assert session.calls == []


def test_missing_quota_header_fails_closed(monkeypatch):
    monkeypatch.setattr(guard, "THE_ODDS_API_KEY", "test-key")
    with pytest.raises(RuntimeError, match="quota header missing"):
        guard.check_budget(max_cost=1, session=FakeSession(remaining=None))


def test_preflight_http_error_fails_closed(monkeypatch):
    monkeypatch.setattr(guard, "THE_ODDS_API_KEY", "test-key")
    with pytest.raises(RuntimeError, match="quota preflight HTTP 500"):
        guard.check_budget(max_cost=1, session=FakeSession(status_code=500))
