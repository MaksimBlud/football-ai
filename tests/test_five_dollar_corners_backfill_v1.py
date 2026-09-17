from pathlib import Path

import pytest

import five_dollar_corners_backfill_v1 as m


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _fixture(*, line=9.5):
    return {
        "id": 123,
        "league": {"id": m.LEAGUES["EPL"], "name": "Premier League"},
        "teams": {
            "home": {"name": "Arsenal"},
            "away": {"name": "Everton"},
        },
        "kickoff_utc": "2016-08-20T14:00:00+00:00",
        "status": "finished",
        "odds": {
            "bookmakers": [
                {
                    "name": "Bet 365",
                    "slug": "bet365",
                    "odds": {
                        "corner_line": {
                            "opening": {"line": line, "over": 1.91, "under": 1.89},
                            "closing": {"line": 10.0, "over": 1.95, "under": 1.85},
                        }
                    },
                }
            ]
        },
    }


def test_frozen_seasons_and_windows():
    assert m.SEASONS[0] == "2016-17"
    assert m.SEASONS[-1] == "2025-26"
    assert len(m.SEASONS) == 10
    start, end = m._season_window("2016-17")
    assert end > start
    with pytest.raises(ValueError):
        m._season_window("2026-27")


def test_normalize_inline_corner_market():
    row = m.normalize_inline_corner_market(_fixture(), "EPL", "2016-17")
    assert row is not None
    assert row["fixture_id"] == "123"
    assert row["bookmaker"] == "bet365"
    assert row["opening_line"] == 9.5
    assert row["opening_over"] == 1.91
    assert row["opening_under"] == 1.89
    assert row["closing_line"] == 10.0


def test_normalize_rejects_missing_opening_prices():
    fixture = _fixture()
    fixture["odds"]["bookmakers"][0]["odds"]["corner_line"]["opening"]["over"] = None
    assert m.normalize_inline_corner_market(fixture, "EPL", "2016-17") is None


def test_probe_records_plan_block_without_leaking_key(tmp_path, monkeypatch):
    payload = {
        "success": 0,
        "error": {"code": "insufficient_plan", "message": "date older than plan history window"},
    }
    monkeypatch.setattr(m.requests, "get", lambda *a, **k: FakeResponse(403, payload))
    report = m.probe_history_access(tmp_path, key="fb_live_secret_value")
    assert report["status"] == "HISTORY_ACCESS_BLOCKED_BY_PLAN"
    assert report["provider_requests"] == 1
    text = (tmp_path / "entitlement_probe.json").read_text()
    assert "fb_live_secret_value" not in text
    assert "model_evaluation_performed" in text


def test_probe_confirms_nonempty_old_history(tmp_path, monkeypatch):
    payload = {
        "success": 1,
        "data": [_fixture()],
        "pagination": {"page": 1, "per_page": 50, "count": 1, "has_more": False},
    }
    monkeypatch.setattr(m.requests, "get", lambda *a, **k: FakeResponse(200, payload))
    report = m.probe_history_access(tmp_path, key="x")
    assert report["status"] == "HISTORY_ACCESS_CONFIRMED"
    assert report["returned_fixtures"] == 1
    assert report["returned_bet365_corner_rows"] == 1


def test_backfill_refuses_shortened_history(tmp_path, monkeypatch):
    monkeypatch.setattr(
        m,
        "probe_history_access",
        lambda output_dir, key=None: {
            "status": "HISTORY_ACCESS_BLOCKED_BY_PLAN",
            "provider_requests": 1,
        },
    )
    with pytest.raises(RuntimeError, match="refusing a shortened backfill"):
        m.run_backfill(tmp_path, key="x")


def test_season_completeness_gate():
    assert m._season_complete(300)
    assert not m._season_complete(299)


def test_request_budget_covers_only_frozen_grid():
    assert set(m.LEAGUES) == {"EPL", "LA_LIGA", "SERIE_A"}
    assert m.MAX_PROVIDER_REQUESTS == len(m.LEAGUES) * len(m.SEASONS) * m.MAX_PAGES_PER_LEAGUE_SEASON + 1
    assert m.REQUEST_INTERVAL_SECONDS >= 1.5
