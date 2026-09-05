from datetime import UTC, datetime
import importlib
import sys
import types


class _FakeTable:
    def __init__(self, rows, table_name):
        self.rows = rows
        self.table_name = table_name
        self.pending = None

    def insert(self, row):
        self.pending = row
        return self

    def execute(self):
        self.rows.append(self.pending)
        return type("Response", (), {"data": [self.pending]})()


class _FakeSupabase:
    def __init__(self):
        self.rows = []
        self.expected_table = None

    def table(self, name):
        if self.expected_table is not None:
            assert name == self.expected_table
        return _FakeTable(self.rows, name)


def test_turkey_and_portugal_route_to_their_multi_market_sport_keys(monkeypatch):
    fake_database = types.ModuleType("database")
    fake_database.supabase = _FakeSupabase()
    monkeypatch.setitem(sys.modules, "database", fake_database)
    sys.modules.pop("multi_market_collector", None)
    collector = importlib.import_module("multi_market_collector")
    fake_database.supabase.expected_table = collector.TABLE

    now = datetime(2026, 9, 5, 8, 0, tzinfo=UTC)
    events = [
        {
            "league": "TURKEY_SUPER_LIG",
            "event_id": "turkey-e1",
            "home_team": "Turkey Home",
            "away_team": "Turkey Away",
            "commence_time_utc": "2026-09-06T06:00:00Z",
            "snapshot_time_utc": "2026-09-05T07:00:00Z",
        },
        {
            "league": "PRIMEIRA_LIGA",
            "event_id": "portugal-e1",
            "home_team": "Portugal Home",
            "away_team": "Portugal Away",
            "commence_time_utc": "2026-09-06T07:00:00Z",
            "snapshot_time_utc": "2026-09-05T07:00:00Z",
        },
    ]
    provider_calls = []

    monkeypatch.setattr(collector, "fetch_quota_status", lambda: {"remaining": 1000})
    monkeypatch.setattr(collector, "load_future_events", lambda _now: events)
    monkeypatch.setattr(collector, "load_latest_collection_times", lambda _event_ids: {})
    monkeypatch.setattr(collector, "build_multi_market_card", lambda _payload: {"total_goals": {"point": 2.5}})

    def fake_fetch_event_markets(sport_key, event_id, **_kwargs):
        provider_calls.append((sport_key, event_id))
        return {
            "home_team": "Home",
            "away_team": "Away",
            "bookmakers": [],
        }, {"remaining": 999}

    monkeypatch.setattr(collector, "fetch_event_markets", fake_fetch_event_markets)

    summary = collector.collect(now)

    assert provider_calls == [
        ("soccer_turkey_super_league", "turkey-e1"),
        ("soccer_portugal_primeira_liga", "portugal-e1"),
    ]
    assert summary["eligible_events"] == 2
    assert summary["fetched"] == 2
    assert summary["inserted"] == 2
    assert summary["skipped_unsupported"] == 0
    assert {row["league"] for row in fake_database.supabase.rows} == {"TURKEY_SUPER_LIG", "PRIMEIRA_LIGA"}
