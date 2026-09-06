import pandas as pd
import pytest
from types import SimpleNamespace

from prekickoff_observability import (
    SNAPSHOT_TABLE,
    LEDGER_TABLE,
    _load_rows,
    analyze_market_movement,
    build_prekickoff_lineage,
    live_report,
)


def test_market_movement_excludes_post_kickoff_snapshots():
    rows = pd.DataFrame([
        {"league":"EPL","event_id":"e1","snapshot_time_utc":"2026-09-01T10:00:00Z","commence_time_utc":"2026-09-01T12:00:00Z","home_odds":2.0,"draw_odds":3.0,"away_odds":4.0},
        {"league":"EPL","event_id":"e1","snapshot_time_utc":"2026-09-01T11:00:00Z","commence_time_utc":"2026-09-01T12:00:00Z","home_odds":1.8,"draw_odds":3.2,"away_odds":4.5},
        {"league":"EPL","event_id":"e1","snapshot_time_utc":"2026-09-01T12:01:00Z","commence_time_utc":"2026-09-01T12:00:00Z","home_odds":1.2,"draw_odds":8.0,"away_odds":15.0},
    ])
    out = analyze_market_movement(rows, league="EPL")
    assert len(out) == 1
    assert out.iloc[0]["snapshots"] == 2
    assert str(out.iloc[0]["latest_pre_kickoff_utc"]) == "2026-09-01 11:00:00+00:00"


def test_market_movement_rejects_cross_league_input():
    rows = pd.DataFrame([{"league":"LA_LIGA","event_id":"e1","snapshot_time_utc":"2026-09-01T10:00:00Z","commence_time_utc":"2026-09-01T12:00:00Z","home_odds":2.0,"draw_odds":3.0,"away_odds":4.0}])
    with pytest.raises(ValueError, match="league mismatch"):
        analyze_market_movement(rows, league="EPL")


def test_lineage_is_outcome_free_and_checks_point_in_time():
    snapshots = pd.DataFrame([{"league":"EPL","event_id":"e1"}])
    ledger = pd.DataFrame([{"league":"EPL","event_id":"e1","snapshot_time_utc":"2026-09-01T11:00:00Z","kickoff_utc":"2026-09-01T12:00:00Z","prediction_mode":"MARKET_ONLY"}])
    out = build_prekickoff_lineage(league="EPL", event_id="e1", snapshots=snapshots, ledger=ledger)
    assert out["ledger_pre_kickoff"] is True
    assert out["outcome_reads"] == 0
    assert out["prediction_modes"] == ["MARKET_ONLY"]


def test_lineage_flags_post_kickoff_ledger_row():
    snapshots = pd.DataFrame([{"league":"EPL","event_id":"e1"}])
    ledger = pd.DataFrame([{"league":"EPL","event_id":"e1","snapshot_time_utc":"2026-09-01T12:01:00Z","kickoff_utc":"2026-09-01T12:00:00Z"}])
    assert build_prekickoff_lineage(league="EPL", event_id="e1", snapshots=snapshots, ledger=ledger)["ledger_pre_kickoff"] is False


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


def test_live_lineage_reads_only_snapshot_and_ledger_tables():
    client = FakeClient({
        SNAPSHOT_TABLE: [{"league":"EPL","event_id":"e1"}],
        LEDGER_TABLE: [{"league":"EPL","event_id":"e1","snapshot_time_utc":"2026-09-01T11:00:00Z","kickoff_utc":"2026-09-01T12:00:00Z","prediction_mode":"MARKET_ONLY"}],
    })
    out = live_report(client=client, league="EPL", event_id="e1")
    assert [call[0] for call in client.calls] == [SNAPSHOT_TABLE, LEDGER_TABLE]
    assert out["outcome_reads"] == 0
    assert out["ledger_pre_kickoff"] is True


def test_bounded_pagination_fails_closed_when_limit_exhausted():
    client = FakeClient({SNAPSHOT_TABLE: [
        {"league":"EPL","event_id":str(i)} for i in range(3)
    ]})
    with pytest.raises(RuntimeError, match="bounded pagination exhausted"):
        _load_rows(client, SNAPSHOT_TABLE, league="EPL", page_size=1, max_pages=2)
    assert len(client.calls) == 2
