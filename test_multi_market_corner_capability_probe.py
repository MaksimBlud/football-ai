from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

import multi_market_corner_capability_probe as probe


GOOD_ROW = {
    **probe.TARGET,
    "snapshot_time_utc": "2026-09-08T09:00:00+00:00",
}
NOW = datetime(2026, 9, 8, 13, 45, tzinfo=UTC)
SPORT_KEY = "soccer_germany_bundesliga"


class Query:
    def __init__(self, row):
        self.row = row
        self.filters = {}

    def select(self, *_args, **_kwargs): return self
    def eq(self, key, value):
        self.filters[key] = value
        return self
    def order(self, *_args, **_kwargs): return self
    def limit(self, *_args, **_kwargs): return self
    def execute(self):
        if self.row is None:
            return SimpleNamespace(data=[])
        if any(str(self.row.get(k)) != str(v) for k, v in self.filters.items()):
            return SimpleNamespace(data=[])
        return SimpleNamespace(data=[dict(self.row)])


class Client:
    def __init__(self, row=GOOD_ROW):
        self.row = row
        self.tables = []

    def table(self, name):
        self.tables.append(name)
        assert name == probe.SOURCE_TABLE
        return Query(self.row)


def test_preregistered_rollover_target_is_exact_and_probe_eligible():
    assert probe.TARGET == {
        "league": "BUNDESLIGA",
        "event_id": "115c6679a72c5a360640b6baaa16e78c",
        "home_team": "Union Berlin",
        "away_team": "FC Schalke 04",
        "commence_time_utc": "2026-09-11T18:30:00+00:00",
    }
    assert probe.TARGET["league"] not in probe.PROHIBITED_LEAGUES


def test_missing_preregistered_target_blocks_before_quota_or_provider():
    calls = []
    result = probe.run_probe(
        Client(None),
        lambda: calls.append("quota"),
        lambda *_args, **_kwargs: calls.append("provider"),
        sport_key=SPORT_KEY,
        now_utc=NOW,
    )
    assert result["status"] == "BLOCKED"
    assert result["blocker"] == "PREREGISTERED_TARGET_NOT_FOUND"
    assert result["provider_request_attempted"] is False
    assert result["paid_provider_requests"] == 0
    assert result["paid_provider_credits"] == 0
    assert result["paid_provider_credit_cost_known"] is True
    assert result["writes_performed"] is False
    assert calls == []


def test_target_identity_mismatch_fails_before_quota_or_provider():
    calls = []
    bad = dict(GOOD_ROW, home_team="Different Club")
    with pytest.raises(RuntimeError, match="target mismatch"):
        probe.run_probe(
            Client(bad),
            lambda: calls.append("quota"),
            lambda *_args, **_kwargs: calls.append("provider"),
            sport_key=SPORT_KEY,
            now_utc=NOW,
        )
    assert calls == []


def test_past_target_fails_before_quota_or_provider():
    calls = []
    with pytest.raises(RuntimeError, match="no longer prospective"):
        probe.run_probe(
            Client(),
            lambda: calls.append("quota"),
            lambda *_args, **_kwargs: calls.append("provider"),
            sport_key=SPORT_KEY,
            now_utc=datetime(2026, 9, 11, 18, 30, tzinfo=UTC),
        )
    assert calls == []


def test_hard_reserve_blocks_before_paid_provider_call():
    calls = []
    result = probe.run_probe(
        Client(),
        lambda: {"remaining": "101", "used": "399", "last_cost": "0"},
        lambda *_args, **_kwargs: calls.append("provider"),
        sport_key=SPORT_KEY,
        now_utc=NOW,
    )
    assert result["status"] == "BLOCKED"
    assert result["blocker"] == "HARD_RESERVE_PROTECTED"
    assert result["provider_request_attempted"] is False
    assert result["paid_provider_requests"] == 0
    assert result["paid_provider_credits"] == 0
    assert result["paid_provider_credit_cost_known"] is True
    assert calls == []


def test_provider_exception_is_conservatively_accounted_as_one_attempt():
    def event_call(*_args, **_kwargs):
        raise RuntimeError("provider transport failed")

    with pytest.raises(probe.ProviderRequestAttemptedError, match="provider transport failed") as caught:
        probe.run_probe(
            Client(),
            lambda: {"remaining": "193", "used": "307", "last_cost": "0"},
            event_call,
            sport_key=SPORT_KEY,
            now_utc=NOW,
        )

    result = caught.value.result
    assert result["target_verified"] is True
    assert result["provider_request_attempted"] is True
    assert result["paid_provider_requests"] == 1
    assert result["paid_provider_credits"] is None
    assert result["paid_provider_credit_cost_known"] is False
    assert result["writes_performed"] is False


def test_empty_corner_payload_is_one_request_capability_miss_without_write():
    calls = []

    def event_call(sport_key, event_id, **kwargs):
        calls.append((sport_key, event_id, kwargs))
        return {"id": event_id, "bookmakers": []}, {"remaining": "193", "used": "307", "last_cost": "0"}

    result = probe.run_probe(
        Client(),
        lambda: {"remaining": "193", "used": "307", "last_cost": "0"},
        event_call,
        sport_key=SPORT_KEY,
        now_utc=NOW,
    )
    assert result["status"] == "CAPABILITY_MISS"
    assert result["target_verified"] is True
    assert result["provider_request_attempted"] is True
    assert result["paid_provider_requests"] == 1
    assert result["paid_provider_credits"] == 0
    assert result["paid_provider_credit_cost_known"] is True
    assert result["corner_market_keys"] == []
    assert result["corner_bookmaker_keys"] == []
    assert result["writes_performed"] is False
    assert calls == [(
        SPORT_KEY,
        probe.TARGET["event_id"],
        {"regions": "eu", "markets": probe.CORNER_MARKETS},
    )]


def test_corner_payload_confirms_capability_inside_one_request_two_credit_cap():
    payload = {
        "bookmakers": [
            {"key": "pinnacle", "markets": [{"key": "alternate_totals_corners", "outcomes": []}]},
            {"key": "book-b", "markets": [{"key": "alternate_team_totals_corners", "outcomes": []}]},
        ]
    }
    result = probe.run_probe(
        Client(),
        lambda: {"remaining": "193", "used": "307", "last_cost": "0"},
        lambda *_args, **_kwargs: (payload, {"remaining": "191", "used": "309", "last_cost": "2"}),
        sport_key=SPORT_KEY,
        now_utc=NOW,
    )
    assert result["status"] == "CAPABILITY_CONFIRMED"
    assert result["provider_request_attempted"] is True
    assert result["paid_provider_requests"] == 1
    assert result["paid_provider_credits"] == 2
    assert result["paid_provider_credit_cost_known"] is True
    assert result["quota_after"]["remaining"] == "191"
    assert result["corner_market_keys"] == [
        "alternate_team_totals_corners",
        "alternate_totals_corners",
    ]
    assert result["corner_bookmaker_keys"] == ["book-b", "pinnacle"]
    assert result["corner_bookmaker_count"] == 2
    assert result["writes_performed"] is False


def test_provider_cost_above_cap_fails_closed_with_known_cost_preserved():
    with pytest.raises(probe.ProviderRequestAttemptedError, match="outside cap") as caught:
        probe.run_probe(
            Client(),
            lambda: {"remaining": "193", "used": "307", "last_cost": "0"},
            lambda *_args, **_kwargs: ({"bookmakers": []}, {"remaining": "190", "used": "310", "last_cost": "3"}),
            sport_key=SPORT_KEY,
            now_utc=NOW,
        )
    result = caught.value.result
    assert result["provider_request_attempted"] is True
    assert result["paid_provider_requests"] == 1
    assert result["paid_provider_credits"] == 3
    assert result["paid_provider_credit_cost_known"] is True


def test_provider_remaining_below_reserve_fails_closed():
    with pytest.raises(probe.ProviderRequestAttemptedError, match="crossed hard reserve") as caught:
        probe.run_probe(
            Client(),
            lambda: {"remaining": "193", "used": "307", "last_cost": "0"},
            lambda *_args, **_kwargs: ({"bookmakers": []}, {"remaining": "99", "used": "401", "last_cost": "2"}),
            sport_key=SPORT_KEY,
            now_utc=NOW,
        )
    result = caught.value.result
    assert result["provider_request_attempted"] is True
    assert result["paid_provider_requests"] == 1
    assert result["paid_provider_credits"] == 2
    assert result["paid_provider_credit_cost_known"] is True
