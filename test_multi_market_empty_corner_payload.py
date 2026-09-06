from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import multi_market_collector as collector


class NoInsertTable:
    def insert(self, _row):
        raise AssertionError("empty corner payload must never be persisted as a Multi-Market snapshot")


class NoInsertClient:
    def table(self, name):
        assert name == collector.TABLE
        return NoInsertTable()


def test_zero_cost_empty_corner_response_is_counted_but_not_persisted(monkeypatch):
    now = datetime(2026, 9, 6, 3, 9, tzinfo=UTC)
    event = {
        "league": "EREDIVISIE",
        "event_id": "1adc363118b3cddfe83b06131e04d6c3",
        "home_team": "Groningen",
        "away_team": "FC Twente Enschede",
        "commence_time_utc": (now + timedelta(hours=7)).isoformat(),
    }
    featured = {
        "id": event["event_id"],
        "home_team": event["home_team"],
        "away_team": event["away_team"],
        "bookmakers": [{"key": "book-a", "markets": [{"key": "totals", "outcomes": []}]}],
    }

    monkeypatch.setattr(collector, "supabase", NoInsertClient())
    monkeypatch.setattr(collector, "load_future_events", lambda _now: [event])
    monkeypatch.setattr(collector, "load_latest_collection_times", lambda _ids: {})
    monkeypatch.setattr(collector, "get_league_config", lambda _league: SimpleNamespace(odds_api_sport_key="soccer_netherlands_eredivisie"))
    monkeypatch.setattr(collector, "fetch_quota_status", lambda: {"remaining": "195", "used": "305", "last_cost": "0"})
    monkeypatch.setattr(collector, "fetch_sport_markets", lambda *_args, **_kwargs: ([featured], {"remaining": "193", "used": "307", "last_cost": "2"}))
    monkeypatch.setattr(collector, "fetch_event_markets", lambda *_args, **_kwargs: ({"id": event["event_id"], "bookmakers": []}, {"remaining": "193", "used": "307", "last_cost": "0"}))

    summary = collector.collect(now, max_paid_requests=2, max_paid_credits=4)

    assert summary["provider_paid_requests"] == 2
    assert summary["provider_paid_credits"] == 2
    assert summary["featured_requests"] == 1
    assert summary["event_requests"] == 1
    assert summary["fetched"] == 1
    assert summary["skipped_no_corner_market"] == 1
    assert summary["inserted"] == 0


def test_corner_market_key_detection_accepts_requested_corner_market():
    payload = {
        "bookmakers": [{
            "key": "book-a",
            "markets": [{"key": "alternate_totals_corners", "outcomes": []}],
        }]
    }
    assert collector._event_corner_market_keys(payload) == ["alternate_totals_corners"]
