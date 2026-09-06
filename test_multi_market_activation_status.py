from pathlib import Path

from multi_market_activation_status import (
    CAPABILITY_PAGE_SIZE,
    CORNER_SOURCE_READY_LEAGUES,
    build_status,
)
from multi_market_policy import (
    EVENT_REQUEST_MAX_CREDITS,
    FEATURED_REQUEST_MAX_CREDITS,
    FIRST_EVENT_MAX_CREDITS,
    HARD_RESERVE_CREDITS,
    MIN_COLLECTION_REMAINING_CREDITS,
)


CORNER_ROW = {
    "snapshot_key": "corner-1",
    "league": "EPL",
    "event_id": "e1",
    "payload": {"provider_market_keys": ["spreads", "alternate_totals_corners"]},
}
NON_CORNER_ROW = {
    "snapshot_key": "plain-1",
    "league": "EREDIVISIE",
    "event_id": "e0",
    "payload": {"provider_market_keys": ["spreads", "totals"]},
}


class Response:
    def __init__(self, count=0, data=None):
        self.count = count
        self.data = list(data or [])


class Query:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.count_requested = False
        self.columns = ""
        self.limit_value = None
        self.range_start = None
        self.range_end = None

    def select(self, columns, count=None):
        self.columns = columns
        self.count_requested = count == "exact"
        self.client.calls.append(("select", self.table_name, columns, count))
        return self

    def order(self, column, desc=False):
        self.client.calls.append(("order", self.table_name, column, desc))
        return self

    def limit(self, value):
        self.limit_value = value
        self.client.calls.append(("limit", self.table_name, value))
        return self

    def range(self, start, end):
        self.range_start = start
        self.range_end = end
        self.client.calls.append(("range", self.table_name, start, end))
        return self

    def execute(self):
        self.client.calls.append(("execute", self.table_name))
        if self.table_name in self.client.missing:
            raise RuntimeError("PGRST205 missing relation")
        if self.count_requested:
            return Response(self.client.counts.get(self.table_name, 0))
        if (
            self.table_name == "league_multi_market_snapshots"
            and self.columns == "snapshot_key,league,event_id,payload"
        ):
            rows = list(self.client.snapshot_rows)
            if self.range_start is not None:
                rows = rows[self.range_start : self.range_end + 1]
            elif self.limit_value is not None:
                rows = rows[: self.limit_value]
            return Response(data=rows)
        return Response()


class Client:
    def __init__(self, *, missing=(), counts=None, snapshot_rows=None):
        self.missing = set(missing)
        self.counts = counts or {}
        self.snapshot_rows = [CORNER_ROW] if snapshot_rows is None else list(snapshot_rows)
        self.calls = []

    def table(self, name):
        self.calls.append(("table", name))
        return Query(self, name)


def quota(remaining):
    return {"remaining": str(remaining), "used": "10", "last_cost": "0"}


def test_schema_quota_and_observed_corner_capability_are_ready_but_await_manual_activation():
    status = build_status(Client(), lambda: quota(MIN_COLLECTION_REMAINING_CREDITS))
    assert status["quota_ready"] is True
    assert status["infrastructure_collection_ready"] is True
    assert status["provider_corner_capability_ready"] is True
    assert status["collection_ready"] is True
    assert status["activation_ready"] is True
    assert status["manual_collection_activation_required"] is True
    assert status["scheduled_collection_enabled"] is False
    assert status["status"] == "READY_AWAITING_MANUAL_ACTIVATION"
    assert status["blockers"] == []
    assert status["quota_threshold"] == HARD_RESERVE_CREDITS + FIRST_EVENT_MAX_CREDITS
    assert status["featured_request_max_credits"] == FEATURED_REQUEST_MAX_CREDITS == 2
    assert status["event_request_max_credits"] == EVENT_REQUEST_MAX_CREDITS == 2
    assert status["first_event_max_credits"] == FIRST_EVENT_MAX_CREDITS == 4
    assert status["hard_reserve_credits"] == HARD_RESERVE_CREDITS
    assert status["paid_provider_requests"] == 0
    assert status["paid_provider_credits"] == 0
    assert status["writes_performed"] is False


def test_failed_eredivisie_canary_blocks_collection_activation_but_not_infrastructure():
    status = build_status(Client(snapshot_rows=[NON_CORNER_ROW, NON_CORNER_ROW]), lambda: quota(193))
    assert status["quota_ready"] is True
    assert status["infrastructure_collection_ready"] is True
    assert status["provider_corner_capability_ready"] is False
    assert status["provider_corner_capability"]["rows_inspected"] == 2
    assert status["provider_corner_capability"]["corner_evidence_rows"] == 0
    assert status["provider_corner_capability"]["scan_complete"] is True
    assert status["collection_ready"] is False
    assert status["activation_ready"] is False
    assert status["status"] == "INFRASTRUCTURE_READY_PROVIDER_CAPABILITY_UNPROVEN"
    assert status["blockers"] == ["PROVIDER_CORNER_CAPABILITY_UNPROVEN"]


def test_no_snapshot_evidence_is_unknown_not_activation_ready():
    status = build_status(Client(snapshot_rows=[]), lambda: quota(204))
    assert status["infrastructure_collection_ready"] is True
    assert status["provider_corner_capability_ready"] is False
    assert status["collection_ready"] is False
    assert "PROVIDER_CORNER_CAPABILITY_UNPROVEN" in status["blockers"]


def test_missing_all_tables_blocks_each_lifecycle_stage_even_with_high_quota():
    missing = {"league_multi_market_snapshots", "league_multi_market_settlements", "league_corner_results"}
    status = build_status(Client(missing=missing), lambda: quota(9999))
    assert status["quota_ready"] is True
    assert status["infrastructure_collection_ready"] is False
    assert status["collection_ready"] is False
    assert status["status"] == "BLOCKED"
    assert status["goals_settlement_ready"] is False
    assert status["corner_storage_ready"] is False
    assert status["oos_structural_ready"] is False
    assert len([b for b in status["blockers"] if b.startswith("SCHEMA_")]) == 3


def test_low_quota_blocks_before_one_worst_case_event_call():
    status = build_status(Client(), lambda: quota(MIN_COLLECTION_REMAINING_CREDITS - 1))
    assert status["quota_ready"] is False
    assert status["infrastructure_collection_ready"] is False
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


def test_provider_capability_scan_is_read_only_and_stops_after_first_evidence_page():
    rows = [dict(CORNER_ROW, snapshot_key=f"corner-{index}") for index in range(1500)]
    client = Client(snapshot_rows=rows)
    status = build_status(client, lambda: quota(999))
    capability = status["provider_corner_capability"]
    assert capability["read_only"] is True
    assert capability["page_size"] == CAPABILITY_PAGE_SIZE == 1000
    assert capability["pages_inspected"] == 1
    assert capability["rows_inspected"] == 1000
    assert capability["corner_evidence_rows"] == 1000
    assert capability["corner_evidence_leagues"] == ["EPL"]
    assert capability["corner_market_keys"] == ["alternate_totals_corners"]
    assert capability["capability_ready"] is True
    assert ("range", "league_multi_market_snapshots", 0, 999) in client.calls
    assert ("range", "league_multi_market_snapshots", 1000, 1999) not in client.calls


def test_provider_capability_finds_historical_evidence_beyond_first_page():
    rows = [
        dict(NON_CORNER_ROW, snapshot_key=f"plain-{index:04d}")
        for index in range(CAPABILITY_PAGE_SIZE)
    ]
    rows.append(dict(CORNER_ROW, snapshot_key="older-corner-evidence"))
    client = Client(snapshot_rows=rows)

    status = build_status(client, lambda: quota(999))
    capability = status["provider_corner_capability"]

    assert capability["capability_ready"] is True
    assert capability["pages_inspected"] == 2
    assert capability["rows_inspected"] == CAPABILITY_PAGE_SIZE + 1
    assert capability["corner_evidence_rows"] == 1
    assert capability["corner_evidence_leagues"] == ["EPL"]
    assert capability["corner_market_keys"] == ["alternate_totals_corners"]
    assert capability["scan_complete"] is True
    assert ("range", "league_multi_market_snapshots", 0, 999) in client.calls
    assert ("range", "league_multi_market_snapshots", 1000, 1999) in client.calls


def test_provider_capability_scans_all_pages_before_declaring_unproven():
    rows = [
        dict(NON_CORNER_ROW, snapshot_key=f"plain-{index:04d}")
        for index in range(CAPABILITY_PAGE_SIZE + 5)
    ]
    status = build_status(Client(snapshot_rows=rows), lambda: quota(999))
    capability = status["provider_corner_capability"]
    assert capability["capability_ready"] is False
    assert capability["pages_inspected"] == 2
    assert capability["rows_inspected"] == CAPABILITY_PAGE_SIZE + 5
    assert capability["scan_complete"] is True
    assert capability["corner_evidence_rows"] == 0


def test_policy_changes_self_trigger_read_only_sampling_plan_workflow():
    workflow = Path(".github/workflows/multi-market-activation-status.yml").read_text()
    assert workflow.count("'multi_market_policy.py'") >= 2
    assert "Build zero-cost reserve-preserving sampling plan" in workflow
    assert "python multi_market_sampling_plan.py" in workflow
    assert "assert plan['paid_provider_requests']==0" in workflow
    assert "assert plan['paid_provider_credits']==0" in workflow
