from types import SimpleNamespace

import pandas as pd

from report_epl_ai_market_pair_collection_status import (
    EXPERIMENT_ID,
    LEAGUE,
    MANUAL_REVIEW_EXIT_CODE,
    PAIR_TABLE,
    SNAPSHOT_TABLE,
    _read_paginated,
    _required_interval_hours,
    build_status,
    load_live_status,
    status_exit_code,
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


def test_scheduler_interval_matches_production_cadence():
    assert _required_interval_hours(80) == 12
    assert _required_interval_hours(40) == 6
    assert _required_interval_hours(12) == 4
    assert _required_interval_hours(1.5) == 2
    assert _required_interval_hours(None) == 24


def test_near_match_marks_manual_review_after_two_hours_not_twenty_four():
    pairs = pd.DataFrame([{"event_id": "e1"}, {"event_id": "e1"}, {"event_id": "e2"}])
    snapshots = pd.DataFrame([
        {"event_id": "e3", "snapshot_time_utc": "2026-09-06T10:00:00Z", "commence_time_utc": "2026-09-06T14:00:00Z"}
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
    assert out["scheduler_required_interval_hours"] == 2
    assert out["scheduler_would_request_snapshot"] is True
    assert out["collection_status"] == "MANUAL_REVIEW"
    assert out["collection_status_reason"] == "SNAPSHOT_DUE"
    assert out["automatic_paid_calls"] is False
    assert out["outcome_reads"] == 0


def test_near_match_is_fresh_when_two_hour_cadence_not_due():
    out = build_status(
        pairs=pd.DataFrame(),
        snapshots=pd.DataFrame([
            {"event_id": "e1", "snapshot_time_utc": "2026-09-06T12:00:00Z", "commence_time_utc": "2026-09-06T14:00:00Z"}
        ]),
        now_utc=pd.Timestamp("2026-09-06T13:00:00Z"),
        primary_cohort_size=100,
    )
    assert out["scheduler_required_interval_hours"] == 2
    assert out["scheduler_would_request_snapshot"] is False
    assert out["collection_status"] == "FRESH"
    assert out["collection_status_reason"] == "CADENCE_NOT_DUE"


def test_no_future_matches_uses_twenty_four_hour_cooldown():
    out = build_status(
        pairs=pd.DataFrame(),
        snapshots=pd.DataFrame([
            {"event_id": "e1", "snapshot_time_utc": "2026-09-06T00:00:00Z", "commence_time_utc": "2026-09-06T01:00:00Z"}
        ]),
        now_utc=pd.Timestamp("2026-09-06T13:00:00Z"),
        primary_cohort_size=100,
    )
    assert out["future_snapshot_events"] == 0
    assert out["scheduler_required_interval_hours"] == 24
    assert out["scheduler_would_request_snapshot"] is False
    assert out["collection_status_reason"] == "NO_FUTURE_MATCH_COOLDOWN"


def test_require_fresh_exit_code_is_actionable_but_does_not_trigger_any_call():
    assert status_exit_code({"collection_status": "FRESH"}, require_fresh=True) == 0
    assert status_exit_code({"collection_status": "MANUAL_REVIEW"}, require_fresh=False) == 0
    assert status_exit_code({"collection_status": "MANUAL_REVIEW"}, require_fresh=True) == MANUAL_REVIEW_EXIT_CODE


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
