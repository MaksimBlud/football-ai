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
    events = _events(now, event_count)
    monkeypatch.setattr(collector, "supabase", fake)
    monkeypatch.setattr(collector, "load_future_events", lambda _now: events)
    monkeypatch.setattr(collector, "load_latest_collection_times", lambda _ids: {})
    monkeypatch.setattr(collector, "fetch_quota_status", lambda: {"remaining": str(quota_remaining), "last_cost": "0"})
    monkeypatch.setattr(collector, "build_multi_market_card", lambda _payload: {})
    monkeypatch.setattr(
        collector,
        "fetch_sport_markets",
        lambda *_a, **_k: (
            [{"id": e["event_id"], "home_team": e["home_team"], "away_team": e["away_team"], "bookmakers": []} for e in events],
            {"remaining": str(quota_remaining - 2), "last_cost": "2"},
        ),
    )
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
    monkeypatch.setattr(collector, "fetch_sport_markets", forbidden_paid_fetch)
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
    monkeypatch.setattr(collector, "fetch_sport_markets", lambda *_a, **_k: paid_calls.append("featured"))
    monkeypatch.setattr(collector, "fetch_event_markets", lambda *_a, **_k: paid_calls.append("event"))
    summary = collector.collect(now)
    assert summary["quota_blocked"] is True
    assert summary["provider_paid_requests"] == 0
    assert summary["provider_paid_credits"] == 0
    assert paid_calls == []


def test_four_credit_cycle_collects_one_complete_event(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    _prepare_collection(monkeypatch, now)
    event_calls = []
    def event_fetch(*_args, **_kwargs):
        event_calls.append(1)
        return {"bookmakers": []}, {"remaining": "200", "last_cost": "2"}
    monkeypatch.setattr(collector, "fetch_event_markets", event_fetch)
    summary = collector.collect(now, max_paid_requests=5, max_paid_credits=4)
    assert len(event_calls) == 1
    assert summary["featured_requests"] == 1
    assert summary["event_requests"] == 1
    assert summary["provider_paid_requests"] == 2
    assert summary["provider_paid_credits"] == 4
    assert summary["inserted"] == 1
    assert summary["credit_cap_stop"] is True


def test_six_credits_collect_two_events_same_league_with_one_featured_request(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    _prepare_collection(monkeypatch, now)
    event_calls = []
    monkeypatch.setattr(
        collector,
        "fetch_event_markets",
        lambda *_a, **_k: (event_calls.append(1) or {"bookmakers": []}, {"remaining": "198", "last_cost": "2"}),
    )
    summary = collector.collect(now, max_paid_requests=3, max_paid_credits=6)
    assert len(event_calls) == 2
    assert summary["featured_requests"] == 1
    assert summary["event_requests"] == 2
    assert summary["provider_paid_requests"] == 3
    assert summary["provider_paid_credits"] == 6
    assert summary["inserted"] == 2


def test_batching_groups_ready_leagues_and_excludes_rpl_without_outcome_signal():
    events = [
        {"league": "LA_LIGA", "event_id": "la-1"},
        {"league": "EPL", "event_id": "epl-1"},
        {"league": "RPL", "event_id": "rpl-1"},
        {"league": "LA_LIGA", "event_id": "la-2"},
        {"league": "EPL", "event_id": "epl-2"},
    ]
    batched = collector._batch_outcome_ready_events(events)
    assert [(e["league"], e["event_id"]) for e in batched] == [
        ("LA_LIGA", "la-1"),
        ("LA_LIGA", "la-2"),
        ("EPL", "epl-1"),
        ("EPL", "epl-2"),
    ]


def test_rpl_only_input_never_enters_paid_multi_market_path(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    fake = FakeSupabase([])
    monkeypatch.setattr(collector, "supabase", fake)
    monkeypatch.setattr(collector, "load_future_events", lambda _now: [
        {"league": "RPL", "event_id": "rpl-1", "home_team": "RPL Home", "away_team": "RPL Away",
         "commence_time_utc": (now + timedelta(hours=5)).isoformat()}
    ])
    monkeypatch.setattr(collector, "fetch_quota_status", lambda: {"remaining": "204", "last_cost": "0"})
    paid_calls = []

    def forbidden_paid_fetch(*args, **kwargs):
        paid_calls.append((args, kwargs))
        raise AssertionError("RPL has no canonical corner outcome source and must not consume Multi-Market credits")

    monkeypatch.setattr(collector, "fetch_sport_markets", forbidden_paid_fetch)
    monkeypatch.setattr(collector, "fetch_event_markets", forbidden_paid_fetch)
    summary = collector.collect(now, max_paid_requests=5, max_paid_credits=20)

    assert paid_calls == []
    assert summary["source_events"] == 1
    assert summary["eligible_events"] == 0
    assert summary["skipped_no_corner_source"] == 1
    assert summary["collection_leagues"] == []
    assert summary["provider_paid_requests"] == 0
    assert summary["provider_paid_credits"] == 0
    assert summary["inserted"] == 0


def test_request_cap_requires_two_http_calls_for_first_complete_event(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    _prepare_collection(monkeypatch, now)
    calls = []
    monkeypatch.setattr(collector, "fetch_sport_markets", lambda *_a, **_k: calls.append("featured"))
    monkeypatch.setattr(collector, "fetch_event_markets", lambda *_a, **_k: calls.append("event"))
    summary = collector.collect(now, max_paid_requests=1, max_paid_credits=4)
    assert calls == []
    assert summary["request_cap_stop"] is True


def test_missing_last_cost_is_charged_conservatively_for_event_leg(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    _prepare_collection(monkeypatch, now, event_count=1)
    monkeypatch.setattr(collector, "fetch_event_markets", lambda *_a, **_k: ({"bookmakers": []}, {"remaining": None, "last_cost": None}))
    summary = collector.collect(now, max_paid_requests=2, max_paid_credits=4)
    assert summary["provider_paid_requests"] == 2
    assert summary["provider_paid_credits"] == 4


def test_reserve_guard_uses_complete_first_event_worst_case(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    _prepare_collection(monkeypatch, now, quota_remaining=HARD_RESERVE_CREDITS + 5)
    calls = []
    monkeypatch.setattr(
        collector,
        "fetch_event_markets",
        lambda *_a, **_k: (calls.append(1) or {"bookmakers": []}, {"remaining": str(HARD_RESERVE_CREDITS + 1), "last_cost": "2"}),
    )
    summary = collector.collect(now, max_paid_requests=5, max_paid_credits=8)
    assert len(calls) == 1
    assert summary["provider_paid_requests"] == 2
    assert summary["provider_paid_credits"] == 4
    assert summary["quota_stop"] is True


def test_invalid_caps_fail_before_provider_preflight():
    for kwargs, message in (({"max_paid_requests": 0}, "requests"), ({"max_paid_credits": 0}, "credits")):
        try:
            collector.collect(**kwargs)
        except ValueError as exc:
            assert message in str(exc)
        else:
            raise AssertionError("invalid cap must fail closed")
