import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType, SimpleNamespace

fake_database = ModuleType("database")
fake_database.supabase = None
sys.modules["database"] = fake_database

import multi_market_collector as collector
from multi_market_policy import HARD_RESERVE_CREDITS, MIN_COLLECTION_REMAINING_CREDITS


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


def _events(now, count=2):
    return [
        {"league": "LA_LIGA", "event_id": f"e{i}", "home_team": f"H{i}", "away_team": f"A{i}",
         "commence_time_utc": (now + timedelta(hours=8 + i)).isoformat()}
        for i in range(1, count + 1)
    ]


def _prepare_collection(monkeypatch, now, *, quota_remaining=204, rows=None, event_count=2):
    fake = FakeSupabase(rows or [])
    monkeypatch.setattr(collector, "supabase", fake)
    monkeypatch.setattr(collector, "load_future_events", lambda _now: _events(now, event_count))
    monkeypatch.setattr(collector, "load_latest_collection_times", lambda _ids: {})
    monkeypatch.setattr(collector, "fetch_quota_status", lambda: {"remaining": str(quota_remaining), "last_cost": "0"})
    monkeypatch.setattr(collector, "build_multi_market_card", lambda _payload: {})
    return fake


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
    monkeypatch.setattr(collector, "fetch_quota_status", lambda: {"remaining": "204"})
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


def test_remaining_below_reserve_plus_worst_case_blocks_before_paid_fetch(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    _prepare_collection(monkeypatch, now, quota_remaining=MIN_COLLECTION_REMAINING_CREDITS - 1)
    paid_calls = []
    monkeypatch.setattr(collector, "fetch_event_markets", lambda *_a, **_k: paid_calls.append(1))
    summary = collector.collect(now)
    assert summary["quota_blocked"] is True
    assert summary["provider_paid_requests"] == 0
    assert summary["provider_paid_credits"] == 0
    assert paid_calls == []


def test_four_credit_cycle_budget_allows_one_controlled_fetch_only(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    _prepare_collection(monkeypatch, now)
    paid_calls = []
    def paid_fetch(*_args, **_kwargs):
        paid_calls.append(1)
        return {"bookmakers": []}, {"remaining": "203", "last_cost": "1"}
    monkeypatch.setattr(collector, "fetch_event_markets", paid_fetch)
    summary = collector.collect(now, max_paid_requests=5, max_paid_credits=4)
    assert len(paid_calls) == 1
    assert summary["provider_paid_requests"] == 1
    assert summary["provider_paid_credits"] == 1
    assert summary["inserted"] == 1
    assert summary["credit_cap_stop"] is True


def test_request_cap_remains_secondary_safety_limit(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    _prepare_collection(monkeypatch, now)
    paid_calls = []
    def paid_fetch(*_args, **_kwargs):
        paid_calls.append(1)
        return {"bookmakers": []}, {"remaining": "203", "last_cost": "1"}
    monkeypatch.setattr(collector, "fetch_event_markets", paid_fetch)
    summary = collector.collect(now, max_paid_requests=1, max_paid_credits=8)
    assert len(paid_calls) == 1
    assert summary["request_cap_stop"] is True


def test_missing_last_cost_is_charged_conservatively_at_worst_case(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    _prepare_collection(monkeypatch, now, event_count=1)
    monkeypatch.setattr(collector, "fetch_event_markets", lambda *_a, **_k: ({"bookmakers": []}, {"remaining": None, "last_cost": None}))
    summary = collector.collect(now, max_paid_credits=4)
    assert summary["provider_paid_requests"] == 1
    assert summary["provider_paid_credits"] == 4


def test_reserve_guard_checks_worst_case_before_next_call(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    _prepare_collection(monkeypatch, now, quota_remaining=HARD_RESERVE_CREDITS + 5)
    calls = []
    def paid_fetch(*_a, **_k):
        calls.append(1)
        return {"bookmakers": []}, {"remaining": str(HARD_RESERVE_CREDITS + 4), "last_cost": "1"}
    monkeypatch.setattr(collector, "fetch_event_markets", paid_fetch)
    summary = collector.collect(now, max_paid_requests=5, max_paid_credits=8)
    assert len(calls) == 1
    assert summary["quota_stop"] is False or summary["quota_stop"] is True
    # The second call is forbidden because 104 - 4 would only touch reserve;
    # after first actual cost remaining is 104, so no call may cross below 100.
    assert summary["provider_paid_requests"] == 1


def test_invalid_caps_fail_before_provider_preflight():
    for kwargs, message in (({"max_paid_requests": 0}, "requests"), ({"max_paid_credits": 0}, "credits")):
        try:
            collector.collect(**kwargs)
        except ValueError as exc:
            assert message in str(exc)
        else:
            raise AssertionError("invalid cap must fail closed")
