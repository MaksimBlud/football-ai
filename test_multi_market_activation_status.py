from multi_market_activation_status import CORNER_SOURCE_READY_LEAGUES, build_status
from multi_market_policy import (
    EVENT_REQUEST_MAX_CREDITS,
    HARD_RESERVE_CREDITS,
    MIN_COLLECTION_REMAINING_CREDITS,
)


class Response:
    def __init__(self, count=0):
        self.count = count
        self.data = []


class Query:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table

    def select(self, columns, count=None):
        self.client.calls.append(("select", self.table_name, columns, count))
        return self

    def limit(self, value):
        self.client.calls.append(("limit", self.table_name, value))
        return self

    def execute(self):
        self.client.calls.append(("execute", self.table_name))
        if self.table_name in self.client.missing:
            raise RuntimeError("PGRST205 missing relation")
        return Response(self.client.counts.get(self.table_name, 0))


class Client:
    def __init__(self, *, missing=(), counts=None):
        self.missing = set(missing)
        self.counts = counts or {}
        self.calls = []

    def table(self, name):
        self.calls.append(("table", name))
        return Query(self, name)


def quota(remaining):
    return {"remaining": str(remaining), "used": "10", "last_cost": "0"}


def test_all_schema_and_minimum_credit_budget_is_ready_but_awaits_manual_activation():
    status = build_status(Client(), lambda: quota(MIN_COLLECTION_REMAINING_CREDITS))
    assert status["quota_ready"] is True
    assert status["collection_ready"] is True
    assert status["manual_collection_activation_required"] is True
    assert status["scheduled_collection_enabled"] is False
    assert status["status"] == "INFRASTRUCTURE_READY_AWAITING_MANUAL_ACTIVATION"
    assert status["blockers"] == []
    assert status["quota_threshold"] == HARD_RESERVE_CREDITS + EVENT_REQUEST_MAX_CREDITS
    assert status["hard_reserve_credits"] == HARD_RESERVE_CREDITS
    assert status["event_request_max_credits"] == EVENT_REQUEST_MAX_CREDITS
    assert status["paid_provider_requests"] == 0
    assert status["paid_provider_credits"] == 0
    assert status["writes_performed"] is False


def test_current_september_style_remaining_is_ready_without_crossing_reserve():
    status = build_status(Client(), lambda: quota(204))
    assert status["quota_ready"] is True
    assert status["collection_ready"] is True


def test_missing_all_tables_blocks_each_lifecycle_stage_even_with_high_quota():
    missing = {"league_multi_market_snapshots", "league_multi_market_settlements", "league_corner_results"}
    status = build_status(Client(missing=missing), lambda: quota(9999))
    assert status["quota_ready"] is True
    assert status["collection_ready"] is False
    assert status["status"] == "BLOCKED"
    assert status["goals_settlement_ready"] is False
    assert status["corner_storage_ready"] is False
    assert status["oos_structural_ready"] is False
    assert len([b for b in status["blockers"] if b.startswith("SCHEMA_")]) == 3


def test_low_quota_blocks_before_one_worst_case_event_call():
    status = build_status(Client(), lambda: quota(MIN_COLLECTION_REMAINING_CREDITS - 1))
    assert status["quota_ready"] is False
    assert status["collection_ready"] is False
    assert status["goals_settlement_ready"] is True
    assert status["corner_storage_ready"] is True
    assert "QUOTA_BELOW_CREDIT_RESERVE_OR_UNAVAILABLE" in status["blockers"]


def test_quota_failure_is_fail_closed_and_recorded():
    def fail():
        raise RuntimeError("provider unavailable")
    status = build_status(Client(), fail)
    assert status["quota"] is None
    assert "provider unavailable" in status["quota_error"]
    assert status["quota_ready"] is False
    assert status["collection_ready"] is False
    assert status["paid_provider_requests"] == 0
    assert status["paid_provider_credits"] == 0


def test_only_audited_corner_source_leagues_are_marked_source_ready():
    status = build_status(Client(), lambda: quota(999))
    assert tuple(status["corner_source_ready_leagues"]) == CORNER_SOURCE_READY_LEAGUES
    assert set(status["per_league_corner_readiness"]) == set(CORNER_SOURCE_READY_LEAGUES)
    assert all(v["source_ready"] for v in status["per_league_corner_readiness"].values())
