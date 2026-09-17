from datetime import datetime, timezone

import pytest

import five_dollar_corners_backfill_v1 as b


def _fixture(*, fixture_id="123", league="EPL", opening=True, closing=True):
    corner = {}
    if opening:
        corner["opening"] = {"line": 9.5, "over": 1.90, "under": 1.90}
    if closing:
        corner["closing"] = {"line": 10.0, "over": 2.00, "under": 1.80}
    return {
        "id": int(fixture_id),
        "status": "finished",
        "kickoff_utc": "2016-08-13T14:00:00+00:00",
        "league": {"id": int(b.LEAGUES[league]), "name": "League"},
        "teams": {"home": {"name": "Home"}, "away": {"name": "Away"}},
        "odds": {
            "bookmakers": [
                {
                    "slug": "bet365",
                    "odds": {"corner_line": corner},
                }
            ]
        },
    }


def test_frozen_season_window_and_2026_27_rejection():
    start, end = b._season_window("2016-17")
    assert datetime.fromtimestamp(start, tz=timezone.utc) == datetime(2016, 7, 1, tzinfo=timezone.utc)
    assert datetime.fromtimestamp(end, tz=timezone.utc) == datetime(2017, 7, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="forbidden season"):
        b._season_window("2026-27")
    with pytest.raises(ValueError, match="outside frozen backfill"):
        b._season_window("2015-16")


def test_inline_bet365_opening_is_required_but_closing_is_diagnostic_only():
    row = b.normalize_fixture_market(_fixture(closing=True), "EPL", "2016-17")
    assert row is not None
    assert row["opening_line"] == 9.5
    assert row["closing_line"] == 10.0

    opening_only = b.normalize_fixture_market(_fixture(closing=False), "EPL", "2016-17")
    assert opening_only is not None
    assert opening_only["opening_line"] == 9.5
    assert opening_only["closing_line"] is None

    assert b.normalize_fixture_market(_fixture(opening=False), "EPL", "2016-17") is None


def test_inline_odds_parser_accepts_nested_endpoint_shape():
    fixture = _fixture()
    bookmakers = fixture["odds"]["bookmakers"]
    fixture["odds"] = {"data": {"bookmakers": bookmakers}}
    row = b.normalize_fixture_market(fixture, "EPL", "2016-17")
    assert row is not None
    assert row["bookmaker"] == "bet365"


def test_wrong_league_or_unfinished_fixture_is_rejected():
    fixture = _fixture()
    fixture["league"]["id"] = int(b.LEAGUES["LA_LIGA"])
    assert b.normalize_fixture_market(fixture, "EPL", "2016-17") is None
    fixture = _fixture()
    fixture["status"] = "scheduled"
    assert b.normalize_fixture_market(fixture, "EPL", "2016-17") is None


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_insufficient_plan_fails_closed(monkeypatch):
    def fake_get(*args, **kwargs):
        return _FakeResponse(403, {"success": 0, "error": {"code": "insufficient_plan", "type": "permission_error"}})

    monkeypatch.setattr(b.requests, "get", fake_get)
    with pytest.raises(b.HistoryAccessRequired):
        b.preflight_history_access("test-key", b.RateLimiter(interval_seconds=0))


def test_preflight_requires_parseable_old_fixture(monkeypatch):
    def fake_get(*args, **kwargs):
        return _FakeResponse(200, {"success": 1, "data": [], "pagination": {"has_more": False}})

    monkeypatch.setattr(b.requests, "get", fake_get)
    with pytest.raises(b.HistoryPreflightFailed, match="no finished fixture"):
        b.preflight_history_access("test-key", b.RateLimiter(interval_seconds=0))


def test_coverage_report_is_acquisition_only():
    row = b.normalize_fixture_market(_fixture(), "EPL", "2016-17")
    report = b._coverage_report(
        [row],
        {("EPL", "2016-17"): 2},
        request_count=3,
    )
    assert report["acquisition_only"] is True
    assert report["model_evaluation_performed"] is False
    assert report["betting_enabled"] is False
    assert report["provider_request_budget"] == 300
    season = report["league_reports"]["EPL"]["2016-17"]
    assert season["finished_fixtures"] == 2
    assert season["valid_opening_corner_markets"] == 1
    assert season["opening_market_coverage_rate"] == 0.5
