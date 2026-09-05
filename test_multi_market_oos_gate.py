from types import SimpleNamespace

import pytest

import multi_market_oos_gate as gate


class FakeQuery:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.columns = None
        self.start = 0
        self.end = None

    def select(self, columns, **kwargs):
        self.columns = columns
        self.client.selects.append((self.table, columns))
        self.count = kwargs.get("count")
        return self

    def limit(self, value):
        self.end = value - 1
        return self

    def order(self, *_args, **_kwargs):
        return self

    def range(self, start, end):
        self.start, self.end = start, end
        self.client.ranges.append((self.table, start, end))
        return self

    def execute(self):
        rows = self.client.rows.get(self.table, [])
        if self.end is None:
            data = rows[self.start:]
        else:
            data = rows[self.start:self.end + 1]
        return SimpleNamespace(data=data, count=len(rows) if getattr(self, "count", None) == "exact" else None)


class FakeClient:
    def __init__(self, rows=None):
        self.rows = rows or {}
        self.selects = []
        self.ranges = []

    def table(self, name):
        return FakeQuery(self, name)


def test_default_status_never_reads_outcome_fields_or_calls_evaluator(monkeypatch):
    client = FakeClient({
        gate.SNAPSHOT_TABLE: [{"snapshot_key": "s", "league": "L", "event_id": "e"}],
        gate.SETTLEMENT_TABLE: [{"settlement_key": "x", "snapshot_key": "s", "league": "L", "event_id": "e"}],
    })
    monkeypatch.setattr(gate, "evaluate", lambda *_args: pytest.fail("evaluator must not be called"))

    status = gate.outcome_agnostic_status(client)

    assert status["status"] == "MANUAL_EVALUATION_REQUIRED"
    assert status["outcome_fields_read"] is False
    assert status["evaluator_called"] is False
    assert all("payload" not in columns for _, columns in client.selects)
    assert all("outcome" not in columns for _, columns in client.selects)


def test_manual_evaluation_requires_exact_frozen_protocol_acknowledgement():
    client = FakeClient()
    with pytest.raises(PermissionError, match="manual acknowledgement"):
        gate.manual_evaluate(client, acknowledgement="yes")
    assert client.selects == []


def test_manual_evaluation_stops_before_outcome_load_when_schema_blocked(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(gate, "probe_schema", lambda _client: {"all_ready": False, "blocked_tables": [gate.SETTLEMENT_TABLE]})
    monkeypatch.setattr(gate, "evaluate", lambda *_args: pytest.fail("evaluator must not be called"))

    result = gate.manual_evaluate(client, acknowledgement=gate.MANUAL_ACK)

    assert result["status"] == "BLOCKED_SCHEMA"
    assert result["evaluator_called"] is False
    assert client.selects == []


def test_manual_loader_pages_full_snapshot_and_settlement_corpora(monkeypatch):
    snapshots = [{"snapshot_key": f"s{i}"} for i in range(1001)]
    settlements = [{"settlement_key": f"x{i}"} for i in range(1001)]
    client = FakeClient({gate.SNAPSHOT_TABLE: snapshots, gate.SETTLEMENT_TABLE: settlements})
    monkeypatch.setattr(gate, "probe_schema", lambda _client: {"all_ready": True, "blocked_tables": []})
    captured = {}

    def fake_evaluate(snapshot_rows, settlement_rows):
        captured["snapshots"] = list(snapshot_rows)
        captured["settlements"] = list(settlement_rows)
        return {"protocol_version": gate.PROTOCOL_VERSION, "usable_observations": 0}

    monkeypatch.setattr(gate, "evaluate", fake_evaluate)

    result = gate.manual_evaluate(client, acknowledgement=gate.MANUAL_ACK)

    assert result["status"] == "EVALUATED_MANUALLY"
    assert result["snapshot_rows_loaded"] == 1001
    assert result["settlement_rows_loaded"] == 1001
    assert len(captured["snapshots"]) == 1001
    assert len(captured["settlements"]) == 1001
    assert client.ranges == [
        (gate.SNAPSHOT_TABLE, 0, 999),
        (gate.SNAPSHOT_TABLE, 1000, 1999),
        (gate.SETTLEMENT_TABLE, 0, 999),
        (gate.SETTLEMENT_TABLE, 1000, 1999),
    ]
