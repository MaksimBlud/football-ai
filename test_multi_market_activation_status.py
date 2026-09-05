from multi_market_activation_status import (
    CORNER_SOURCE_READY_LEAGUES,
    START_MIN_REQUESTS_REMAINING,
    build_status,
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


def test_all_schema_and_quota_green_separates_collection_from_oos_activation():
    status = build_status(Client(), lambda: quota(START_MIN_REQUESTS_REMAINING))
    assert status["quota_ready"] is True
    assert status["collection_ready"] is True
    assert status["goals_settlement_ready"] is True
    assert status["corner_storage_ready"] is True
    assert status["oos_structural_ready"] is True
    assert status["prospective_oos_evaluation_active"] is False
    assert status["activation_ready"] is True
    assert status["status"] == "READY_FOR_COLLECTION"
    assert status["blockers"] == []
    assert status["paid_provider_requests"] == 0
    assert status["writes_performed"] is False


def test_missing_all_tables_blocks_each_lifecycle_stage_even_with_high_quota():
    missing = {
        "league_multi_market_snapshots",
        "league_multi_market_settlements",
        "league_corner_results",
    }
    status = build_status(Client(missing=missing), lambda: quota(9999))
    assert status["quota_ready"] is True
    assert status["collection_ready"] is False
    assert status["goals_settlement_ready"] is False
    assert status["corner_storage_ready"] is False
    assert status["oos_structural_ready"] is False
    assert len([b for b in status["blockers"] if b.startswith("SCHEMA_")]) == 3


def test_snapshot_table_plus_quota_enables_collection_but_not_settlement():
    missing = {"league_multi_market_settlements", "league_corner_results"}
    status = build_status(Client(missing=missing), lambda: quota(800))
    assert status["collection_ready"] is True
    assert status["goals_settlement_ready"] is False
    assert status["corner_storage_ready"] is False
    assert status["oos_structural_ready"] is False


def test_low_quota_blocks_collection_but_not_schema_based_settlement_structure():
    status = build_status(Client(), lambda: quota(START_MIN_REQUESTS_REMAINING - 1))
    assert status["quota_ready"] is False
    assert status["collection_ready"] is False
    assert status["goals_settlement_ready"] is True
    assert status["corner_storage_ready"] is True
    assert "QUOTA_BELOW_THRESHOLD_OR_UNAVAILABLE" in status["blockers"]


def test_quota_failure_is_fail_closed_and_recorded():
    def fail():
        raise RuntimeError("provider unavailable")

    status = build_status(Client(), fail)
    assert status["quota"] is None
    assert "provider unavailable" in status["quota_error"]
    assert status["quota_ready"] is False
    assert status["collection_ready"] is False
    assert status["paid_provider_requests"] == 0


def test_only_audited_corner_source_leagues_are_marked_source_ready():
    status = build_status(Client(), lambda: quota(999))
    assert tuple(status["corner_source_ready_leagues"]) == CORNER_SOURCE_READY_LEAGUES
    assert set(status["per_league_corner_readiness"]) == set(CORNER_SOURCE_READY_LEAGUES)
    assert all(v["source_ready"] for v in status["per_league_corner_readiness"].values())
