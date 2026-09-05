import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType, SimpleNamespace

fake_database = ModuleType("database")
fake_database.supabase = None
sys.modules["database"] = fake_database

import multi_market_collector as collector


class FakeQuery:
    def __init__(self, table, ranges):
        self.table = table
        self._ranges = ranges
        self._start = 0
        self._end = len(table.rows) - 1
        self._insert = None

    def select(self, *_args, **_kwargs): return self
    def in_(self, *_args, **_kwargs): return self
    def order(self, *_args, **_kwargs): return self
    def range(self, start, end):
        self._start, self._end = start, end
        self._ranges.append((start, end))
        return self
    def insert(self, row):
        self._insert = dict(row)
        return self
    def execute(self):
        if self._insert is not None:
            self.table.rows.append(self._insert)
            return SimpleNamespace(data=[self._insert])
        return SimpleNamespace(data=self.table.rows[self._start:self._end + 1])


class FakeTable:
    def __init__(self, rows=None): self.rows = list(rows or [])


class FakeSupabase:
    def __init__(self, rows):
        self.tables = {collector.TABLE: FakeTable(rows)}
        self.ranges = []

    def table(self, name):
        return FakeQuery(self.tables.setdefault(name, FakeTable()), self.ranges)


def _row(event_id, timestamp):
    return {"league": "LA_LIGA", "event_id": event_id, "snapshot_time_utc": timestamp.isoformat()}


def test_latest_collection_times_pages_past_global_postgrest_cap(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    rows = [_row("busy-event", now - timedelta(minutes=i)) for i in range(1000)]
    target_time = now - timedelta(hours=2)
    rows.append(_row("target-event", target_time))
    fake = FakeSupabase(rows)
    monkeypatch.setattr(collector, "supabase", fake)
    latest = collector.load_latest_collection_times(["busy-event", "target-event"])
    assert latest[("LA_LIGA", "target-event")] == target_time
    assert fake.ranges == [(0, 999), (1000, 1999)]


def test_recent_event_hidden_beyond_first_page_cannot_trigger_paid_fetch(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    rows = [_row("busy-event", now - timedelta(minutes=i)) for i in range(1000)]
    rows.append(_row("target-event", now - timedelta(hours=2)))
    fake = FakeSupabase(rows)
    monkeypatch.setattr(collector, "supabase", fake)
    monkeypatch.setattr(collector, "load_future_events", lambda _now: [
        {"league": "LA_LIGA", "event_id": "target-event", "home_team": "Home", "away_team": "Away", "commence_time_utc": (now + timedelta(hours=8)).isoformat()},
        {"league": "LA_LIGA", "event_id": "busy-event", "home_team": "Busy Home", "away_team": "Busy Away", "commence_time_utc": (now + timedelta(hours=9)).isoformat()},
    ])
    monkeypatch.setattr(collector, "fetch_quota_status", lambda: {"remaining": 1000})
    paid_calls = []
    def forbidden_paid_fetch(*args, **kwargs):
        paid_calls.append((args, kwargs))
        raise AssertionError("recent event must not consume a paid request")
    monkeypatch.setattr(collector, "fetch_event_markets", forbidden_paid_fetch)
    summary = collector.collect(now)
    assert summary["fetched"] == 0
    assert summary["skipped_recent"] == 2
    assert paid_calls == []
    assert fake.ranges == [(0, 999), (1000, 1999)]


def test_explicit_request_cap_limits_controlled_smoke_to_one_paid_fetch(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    fake = FakeSupabase([])
    monkeypatch.setattr(collector, "supabase", fake)
    monkeypatch.setattr(collector, "load_future_events", lambda _now: [
        {"league": "LA_LIGA", "event_id": "e1", "home_team": "H1", "away_team": "A1", "commence_time_utc": (now + timedelta(hours=8)).isoformat()},
        {"league": "LA_LIGA", "event_id": "e2", "home_team": "H2", "away_team": "A2", "commence_time_utc": (now + timedelta(hours=9)).isoformat()},
    ])
    monkeypatch.setattr(collector, "fetch_quota_status", lambda: {"remaining": 1000})
    monkeypatch.setattr(collector, "build_multi_market_card", lambda _payload: {})
    paid_calls = []
    def paid_fetch(*_args, **_kwargs):
        paid_calls.append(1)
        return {"bookmakers": []}, {"remaining": 999}
    monkeypatch.setattr(collector, "fetch_event_markets", paid_fetch)
    summary = collector.collect(now, max_paid_requests=1)
    assert len(paid_calls) == 1
    assert summary["fetched"] == 1
    assert summary["inserted"] == 1
    assert summary["max_paid_requests"] == 1
    assert summary["request_cap_stop"] is True


def test_invalid_request_cap_fails_before_provider_preflight():
    try:
        collector.collect(max_paid_requests=0)
    except ValueError as exc:
        assert "must be >= 1" in str(exc)
    else:
        raise AssertionError("invalid request cap must fail closed")
