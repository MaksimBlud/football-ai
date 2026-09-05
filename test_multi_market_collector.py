from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import multi_market_collector as collector


class FakeQuery:
    def __init__(self, rows, ranges):
        self._rows = rows
        self._ranges = ranges
        self._start = 0
        self._end = len(rows) - 1

    def select(self, *_args, **_kwargs):
        return self

    def in_(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def range(self, start, end):
        self._start = start
        self._end = end
        self._ranges.append((start, end))
        return self

    def execute(self):
        return SimpleNamespace(data=self._rows[self._start:self._end + 1])


class FakeSupabase:
    def __init__(self, rows):
        self.rows = rows
        self.ranges = []

    def table(self, name):
        assert name == collector.TABLE
        return FakeQuery(self.rows, self.ranges)


def _row(event_id, timestamp):
    return {
        "league": "LA_LIGA",
        "event_id": event_id,
        "snapshot_time_utc": timestamp.isoformat(),
    }


def test_latest_collection_times_pages_past_global_postgrest_cap(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)

    # One noisy event fills the first 1000 globally newest rows. The target
    # event is still recent enough to suppress another paid request, but its
    # latest row is only visible on page two.
    rows = [
        _row("busy-event", now - timedelta(minutes=i))
        for i in range(1000)
    ]
    target_time = now - timedelta(hours=2)
    rows.append(_row("target-event", target_time))

    fake = FakeSupabase(rows)
    monkeypatch.setattr(collector, "supabase", fake)

    latest = collector.load_latest_collection_times(
        ["busy-event", "target-event"]
    )

    assert latest[("LA_LIGA", "target-event")] == target_time
    assert fake.ranges == [(0, 999), (1000, 1999)]


def test_recent_event_hidden_beyond_first_page_cannot_trigger_paid_fetch(monkeypatch):
    now = datetime(2026, 9, 5, 13, 0, tzinfo=UTC)
    rows = [
        _row("busy-event", now - timedelta(minutes=i))
        for i in range(1000)
    ]
    rows.append(_row("target-event", now - timedelta(hours=2)))

    fake = FakeSupabase(rows)
    monkeypatch.setattr(collector, "supabase", fake)
    monkeypatch.setattr(
        collector,
        "load_future_events",
        lambda _now: [{
            "league": "LA_LIGA",
            "event_id": "target-event",
            "home_team": "Home",
            "away_team": "Away",
            "commence_time_utc": (now + timedelta(hours=8)).isoformat(),
        }, {
            "league": "LA_LIGA",
            "event_id": "busy-event",
            "home_team": "Busy Home",
            "away_team": "Busy Away",
            "commence_time_utc": (now + timedelta(hours=9)).isoformat(),
        }],
    )
    monkeypatch.setattr(
        collector,
        "fetch_quota_status",
        lambda: {"remaining": 1000},
    )

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
