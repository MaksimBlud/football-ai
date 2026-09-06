from types import SimpleNamespace

import pytest

from multi_market_activation_status import CAPABILITY_PAGE_SIZE
from multi_market_cycle import run_cycle
from multi_market_policy import MIN_COLLECTION_REMAINING_CREDITS


CORNER_EVIDENCE_ROW = {
    "snapshot_key": "capability-s1",
    "league": "EPL",
    "event_id": "capability-e1",
    "payload": {"provider_market_keys": ["spreads", "alternate_totals_corners"]},
}
NON_CORNER_EVIDENCE_ROW = {
    "snapshot_key": "plain-s1",
    "league": "EREDIVISIE",
    "event_id": "plain-e1",
    "payload": {"provider_market_keys": ["spreads", "totals"]},
}


class FakeQuery:
    def __init__(self, client, table_name, response=None, error=None):
        self.client = client
        self.table_name = table_name
        self.response = response
        self.error = error
        self.columns = ""
        self.count_requested = False
        self.limit_value = None
        self.range_start = None
        self.range_end = None

    def select(self, columns="", *args, **kwargs):
        self.columns = columns
        self.count_requested = kwargs.get("count") == "exact"
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, value, *args, **kwargs):
        self.limit_value = value
        return self

    def range(self, start, end, *args, **kwargs):
        self.range_start = start
        self.range_end = end
        return self

    def execute(self):
        if self.error is not None:
            raise self.error
        if (
            self.table_name == "league_multi_market_snapshots"
            and self.columns == "snapshot_key,league,event_id,payload"
        ):
            rows = list(self.client.snapshot_rows)
            if self.range_start is not None:
                rows = rows[self.range_start : self.range_end + 1]
            elif self.limit_value is not None:
                rows = rows[: self.limit_value]
            return SimpleNamespace(data=rows, count=len(rows))
        return self.response or SimpleNamespace(data=[], count=0)


class FakeClient:
    def __init__(self, table_errors=None, *, capability_ready=True, snapshot_rows=None):
        self.table_errors = table_errors or {}
        self.tables = []
        if snapshot_rows is not None:
            self.snapshot_rows = list(snapshot_rows)
        else:
            self.snapshot_rows = [CORNER_EVIDENCE_ROW] if capability_ready else []

    def table(self, name):
        self.tables.append(name)
        return FakeQuery(self, name, error=self.table_errors.get(name))


def test_cycle_does_not_call_collect_when_schema_blocked():
    client = FakeClient({"league_multi_market_snapshots": RuntimeError("PGRST205")})
    calls = {"collect": 0, "quota": 0}

    def quota():
        calls["quota"] += 1
        return {"remaining": "999", "last_cost": "0"}

    def collect():
        calls["collect"] += 1
        return {"fetched": 1}

    result = run_cycle(client, quota, collect, collection_enabled=True)
    assert result["action"] == "NOOP_BLOCKED"
    assert result["collection_called"] is False
    assert result["paid_provider_requests"] == 0
    assert calls == {"collect": 0, "quota": 1}


def test_cycle_does_not_call_collect_when_quota_below_credit_threshold():
    client = FakeClient()
    calls = {"collect": 0}
    result = run_cycle(
        client,
        lambda: {"remaining": str(MIN_COLLECTION_REMAINING_CREDITS - 1), "last_cost": "0"},
        lambda: calls.__setitem__("collect", calls["collect"] + 1) or {"fetched": 1},
        collection_enabled=True,
    )
    assert result["action"] == "NOOP_BLOCKED"
    assert result["readiness"]["quota_ready"] is False
    assert result["collection_called"] is False
    assert result["paid_provider_requests"] == 0
    assert calls["collect"] == 0


def test_infrastructure_and_quota_ready_without_corner_evidence_blocks_cycle_even_if_enabled():
    client = FakeClient(capability_ready=False)
    calls = {"collect": 0}
    result = run_cycle(
        client,
        lambda: {"remaining": "204", "last_cost": "0"},
        lambda: calls.__setitem__("collect", calls["collect"] + 1) or {"fetched": 1},
        collection_enabled=True,
    )
    assert result["action"] == "NOOP_BLOCKED"
    assert result["readiness"]["quota_ready"] is True
    assert result["readiness"]["infrastructure_collection_ready"] is True
    assert result["readiness"]["provider_corner_capability_ready"] is False
    assert result["readiness"]["collection_ready"] is False
    assert "PROVIDER_CORNER_CAPABILITY_UNPROVEN" in result["readiness"]["blockers"]
    assert result["collection_called"] is False
    assert result["paid_provider_requests"] == 0
    assert calls["collect"] == 0


def test_204_credits_and_corner_capability_are_ready_but_still_require_activation():
    client = FakeClient()
    calls = {"collect": 0}
    result = run_cycle(
        client,
        lambda: {"remaining": "204", "last_cost": "0"},
        lambda: calls.__setitem__("collect", calls["collect"] + 1) or {"fetched": 1},
    )
    assert result["action"] == "NOOP_ACTIVATION_REQUIRED"
    assert result["readiness"]["quota_ready"] is True
    assert result["readiness"]["provider_corner_capability_ready"] is True
    assert result["readiness"]["collection_ready"] is True
    assert result["collection_called"] is False
    assert calls["collect"] == 0


def test_historical_corner_evidence_beyond_first_page_keeps_cycle_capability_ready():
    rows = [
        dict(NON_CORNER_EVIDENCE_ROW, snapshot_key=f"plain-{index:04d}")
        for index in range(CAPABILITY_PAGE_SIZE)
    ]
    rows.append(dict(CORNER_EVIDENCE_ROW, snapshot_key="older-corner"))
    client = FakeClient(snapshot_rows=rows)
    calls = {"collect": 0}

    result = run_cycle(
        client,
        lambda: {"remaining": "204", "last_cost": "0"},
        lambda: calls.__setitem__("collect", calls["collect"] + 1) or {"fetched": 1},
    )

    assert result["action"] == "NOOP_ACTIVATION_REQUIRED"
    assert result["readiness"]["provider_corner_capability_ready"] is True
    assert result["readiness"]["provider_corner_capability"]["pages_inspected"] == 2
    assert result["readiness"]["provider_corner_capability"]["rows_inspected"] == 1001
    assert calls["collect"] == 0


def test_cycle_calls_collect_only_when_all_gates_and_activation_ready():
    client = FakeClient()
    calls = {"collect": 0}

    def collect():
        calls["collect"] += 1
        return {"fetched": 2, "inserted": 2, "provider_paid_requests": 2, "provider_paid_credits": 4}

    result = run_cycle(
        client,
        lambda: {"remaining": "204", "last_cost": "0"},
        collect,
        collection_enabled=True,
    )
    assert result["action"] == "COLLECTION_ATTEMPTED"
    assert result["collection_activation_enabled"] is True
    assert result["collection_called"] is True
    assert result["paid_provider_requests"] == 2
    assert calls["collect"] == 1
    assert result["prospective_oos_evaluation_active"] is False


def test_cycle_reports_two_http_requests_for_one_amortized_complete_event():
    client = FakeClient()
    result = run_cycle(
        client,
        lambda: {"remaining": "195", "last_cost": "0"},
        lambda: {
            "fetched": 1,
            "inserted": 1,
            "featured_requests": 1,
            "event_requests": 1,
            "provider_paid_requests": 2,
            "provider_paid_credits": 4,
        },
        collection_enabled=True,
    )
    assert result["paid_provider_requests"] == 2
    assert result["collection"]["fetched"] == 1
    assert result["collection"]["provider_paid_requests"] == 2


def test_cycle_keeps_fetched_as_legacy_request_count_fallback():
    client = FakeClient()
    result = run_cycle(
        client,
        lambda: {"remaining": "195", "last_cost": "0"},
        lambda: {"fetched": 1, "inserted": 1},
        collection_enabled=True,
    )
    assert result["paid_provider_requests"] == 1


def test_invalid_explicit_provider_request_count_fails_closed():
    client = FakeClient()
    for value in (-1, "not-an-int"):
        with pytest.raises(ValueError, match="provider paid request count"):
            run_cycle(
                client,
                lambda: {"remaining": "195", "last_cost": "0"},
                lambda value=value: {"fetched": 1, "provider_paid_requests": value},
                collection_enabled=True,
            )
