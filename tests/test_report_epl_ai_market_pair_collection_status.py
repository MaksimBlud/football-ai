from types import SimpleNamespace

import pandas as pd

from report_epl_ai_market_pair_collection_status import (
    EXPERIMENT_ID,
    LEAGUE,
    PAIR_TABLE,
    SNAPSHOT_TABLE,
    _read_paginated,
    build_status,
    load_live_status,
)


class FakeQuery:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.filters = {}
        self.bounds = None

    def select(self, _columns):
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def range(self, start, end):
        self.bounds = (start, end)
        return self

    def execute(self):
        self.client.calls.append((self.table_name, dict(self.filters), self.bounds))
        rows = [r for r in self.client.rows.get(self.table_name, [])
                if all(r.get(k) == v for k, v in self.filters.items())]
        start, end = self.bounds
        return SimpleNamespace(data=rows[start:end + 1])


class FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def table(self, name):
        return FakeQuery(self, name)


def test_status_counts_distinct_events_and_marks_stale_snapshot_for_manual_review():
    pairs = pd.DataFrame([{"event_id": "e1"}, {"event_id": "e1"}, {"event_id": "e2"}])
    snapshots = pd.DataFrame([
        {"event_id": "e3", "snapshot_time_utc": "2026-09-05T10:00:00Z", "commence_time_utc": "2026-09-07T12:00:00Z"}
    ])
    out = build_status(
        pairs=pairs,
        snapshots=snapshots,
        now_utc=pd.Timestamp("2026-09-06T13:00:00Z"),
        primary_cohort_size=100,
    )
    assert out["collected_events"] == 2
    assert out["remaining_events"] == 98
    assert out["future_snapshot_events"] == 1
    assert out["collection_status"] == "MANUAL_REVIEW"
    assert out["automatic_paid_calls"] is False
    assert out["outcome_reads"] == 0


def test_status_is_fresh_under_24_hours():
    out = build_status(
        pairs=pd.DataFrame(),
        snapshots=pd.DataFrame([
            {"event_id": "e1", "snapshot_time_utc": "2026-09-06T12:00:00Z", "commence_time_utc": "2026-09-07T12:00:00Z"}
        ]),
        now_utc=pd.Timestamp("2026-09-06T13:00:00Z"),
        primary_cohort_size=100,
    )
    assert out["collection_status"] == "FRESH"


def test_live_status_reads_only_pair_and_snapshot_tables(monkeypatch, tmp_path):
    contract = tmp_path / "contract.json"
    contract.write_text('{"evaluation":{"primary_cohort_size":100}}', encoding="utf-8")
    monkeypatch.setattr("report_epl_ai_market_pair_collection_status.CONTRACT_PATH", contract)
    client = FakeClient({
        PAIR_TABLE: [{"experiment_id": EXPERIMENT_ID, "event_id": "e1"}],
        SNAPSHOT_TABLE: [{"league": LEAGUE, "event_id": "e2", "snapshot_time_utc": "2026-09-06T12:00:00Z", "commence_time_utc": "2026-09-07T12:00:00Z"}],
    })
    out = load_live_status(client, now_utc=pd.Timestamp("2026-09-06T13:00:00Z"))
    assert [call[0] for call in client.calls] == [PAIR_TABLE, SNAPSHOT_TABLE]
    assert out["collected_events"] == 1
    assert out["outcome_reads"] == 0


def test_paginated_reader_is_bounded(monkeypatch):
    monkeypatch.setattr("report_epl_ai_market_pair_collection_status.PAGE_SIZE", 1)
    monkeypatch.setattr("report_epl_ai_market_pair_collection_status.MAX_PAGES", 2)
    client = FakeClient({PAIR_TABLE: [
        {"experiment_id": EXPERIMENT_ID, "event_id": "e1"},
        {"experiment_id": EXPERIMENT_ID, "event_id": "e2"},
        {"experiment_id": EXPERIMENT_ID, "event_id": "e3"},
    ]})
    try:
        _read_paginated(client, PAIR_TABLE, "event_id", filters={"experiment_id": EXPERIMENT_ID})
        raised = False
    except RuntimeError:
        raised = True
    assert raised
    assert len(client.calls) == 2
