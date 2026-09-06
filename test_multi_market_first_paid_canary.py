from types import SimpleNamespace

import pytest

import multi_market_first_paid_canary as canary


class Query:
    def __init__(self, client):
        self.client = client
        self.count_requested = False
        self.limit_value = None

    def select(self, *_args, **kwargs):
        self.count_requested = kwargs.get("count") == "exact"
        return self

    def order(self, *_args, **_kwargs): return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        if self.count_requested:
            return SimpleNamespace(count=len(self.client.rows), data=[])
        rows = list(self.client.rows)
        if self.limit_value is not None:
            rows = rows[: self.limit_value]
        return SimpleNamespace(data=rows)


class Client:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    def table(self, name):
        assert name == canary.TABLE
        return Query(self)


def plan(leagues=("EREDIVISIE", "EREDIVISIE")):
    return {
        "read_only": True,
        "writes_performed": False,
        "paid_provider_requests": 0,
        "paid_provider_credits": 0,
        "hard_reserve_preserved": True,
        "remaining_credits": 195,
        "planned_events": 2,
        "planned_credits_worst_case": 6,
        "worst_case_remaining_credits": 189,
        "events": [
            {"league": leagues[0], "event_id": "e1", "worst_case_marginal_credits": 4},
            {"league": leagues[1], "event_id": "e2", "worst_case_marginal_credits": 2},
        ],
    }


def stored(event_id):
    return {
        "snapshot_key": f"key-{event_id}",
        "league": "EREDIVISIE",
        "event_id": event_id,
        "home_team": f"H-{event_id}",
        "away_team": f"A-{event_id}",
        "kickoff_utc": "2026-09-06T10:15:00+00:00",
        "snapshot_time_utc": "2026-09-06T03:10:00+00:00",
        "provider": "THE_ODDS_API",
        "payload": {
            "provider_market_keys": ["spreads", "totals", "alternate_totals_corners"],
            "bookmakers": [{"key": "book-a", "markets": []}],
        },
    }


def collection():
    return {
        "quota_blocked": False,
        "quota_before": {"remaining": "195", "last_cost": "0"},
        "collection_leagues": ["EREDIVISIE"],
        "featured_requests": 1,
        "event_requests": 2,
        "provider_paid_requests": 3,
        "provider_paid_credits": 6,
        "fetched": 2,
        "inserted": 2,
        "max_paid_requests": 3,
        "max_paid_credits": 6,
    }


def test_import_is_independent_of_live_database_module():
    assert canary.TABLE == "league_multi_market_snapshots"
    assert canary._default_build_plan.__module__ == canary.__name__
    assert canary._default_collect.__module__ == canary.__name__


def test_nonempty_snapshot_table_blocks_before_planner_or_provider():
    client = Client([stored("old")])
    calls = []
    result = canary.run_canary(
        client,
        build_plan_fn=lambda **_kwargs: calls.append("plan"),
        collect_fn=lambda **_kwargs: calls.append("collect"),
        fetch_quota_fn=lambda: calls.append("quota"),
    )
    assert result["status"] == "BLOCKED"
    assert result["blocker"] == "FIRST_CANARY_REQUIRES_EMPTY_SNAPSHOT_TABLE"
    assert calls == []


def test_two_event_same_league_canary_uses_exact_caps_and_audits_rows():
    client = Client()
    calls = []

    def collect_fn(**kwargs):
        calls.append(kwargs)
        client.rows.extend([stored("e1"), stored("e2")])
        return collection()

    result = canary.run_canary(
        client,
        build_plan_fn=lambda **kwargs: (calls.append(kwargs) or plan()),
        collect_fn=collect_fn,
        fetch_quota_fn=lambda: {"remaining": "189", "used": "311", "last_cost": "0"},
    )
    assert calls == [{"max_paid_credits": 6}, {"max_paid_requests": 3, "max_paid_credits": 6}]
    assert result["status"] == "PASSED"
    assert result["snapshot_count_before"] == 0
    assert result["snapshot_count_after"] == 2
    assert result["preflight"]["paid_provider_requests"] == 0
    assert result["collection"]["featured_requests"] == 1
    assert result["collection"]["event_requests"] == 2
    assert result["collection"]["provider_paid_requests"] == 3
    assert result["collection"]["provider_paid_credits"] == 6
    assert result["post_collection"]["unique_events"] == 2
    assert result["post_collection"]["unique_snapshot_keys"] == 2
    assert "alternate_totals_corners" in result["post_collection"]["provider_market_keys"]
    assert result["quota_after"]["remaining"] == "189"


def test_mixed_league_plan_fails_before_collection():
    calls = []
    with pytest.raises(RuntimeError, match="same league"):
        canary.run_canary(
            Client(),
            build_plan_fn=lambda **_kwargs: plan(("EREDIVISIE", "LIGUE_1")),
            collect_fn=lambda **_kwargs: calls.append("collect"),
            fetch_quota_fn=lambda: {"remaining": "195"},
        )
    assert calls == []


def test_canary_rejects_missing_corner_market_after_write():
    client = Client()

    def collect_fn(**_kwargs):
        bad = stored("e1")
        bad["payload"]["provider_market_keys"] = ["spreads", "totals"]
        client.rows.extend([bad, stored("e2")])
        return collection()

    with pytest.raises(RuntimeError, match="no corner market"):
        canary.run_canary(
            client,
            build_plan_fn=lambda **_kwargs: plan(),
            collect_fn=collect_fn,
            fetch_quota_fn=lambda: {"remaining": "189"},
        )
