from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

from product_fixture_schedule import (
    OFFICIAL_SCHEDULE_URL,
    official_week_6_fallback,
    fetch_upcoming_fixtures,
    parse_espn_schedule,
)

NOW = datetime(2026, 10, 9, 15, 0, tzinfo=timezone.utc)


def event(*, id="fixture-1", date="2026-10-10T11:30:00Z",
          home="Arsenal", away="Leeds United", state="pre"):
    return {
        "id": id,
        "date": date,
        "status": {"type": {"state": state, "completed": state == "post"}},
        "competitions": [{"competitors": [
            {"homeAway": "home", "team": {"displayName": home}},
            {"homeAway": "away", "team": {"displayName": away}},
        ]}],
    }


def test_official_october_round_has_ten_real_fixtures_and_correct_utc():
    result = official_week_6_fallback(now_utc=NOW)
    assert len(result) == 10
    assert result[0]["home_team"] == "Arsenal"
    assert result[0]["kickoff_utc"] == "2026-10-10T11:30:00+00:00"
    assert result[-1]["home_team"] == "Coventry City"
    assert result[-1]["kickoff_utc"] == "2026-10-12T19:00:00+00:00"
    assert all(row["model_forecast_status"] == "not_available" for row in result)
    assert all(row["bookmaker_odds_status"] == "not_available" for row in result)


def test_expired_official_round_never_shows_past_matches():
    after = datetime(2026, 10, 13, tzinfo=timezone.utc)
    assert official_week_6_fallback(now_utc=after) == []


def test_espn_schedule_accepts_only_future_prematch_and_orders():
    payload = {"events": [
        event(id="later", date="2026-10-11T13:00:00Z", home="Hull", away="Everton"),
        event(id="early"),
        event(id="finished", state="post"),
        event(id="past", date="2026-10-09T10:00:00Z"),
    ]}
    results = parse_espn_schedule(payload, now_utc=NOW)
    assert [x["schedule_id"] for x in results] == ["espn:early", "espn:later"]
    assert results[0]["home_team"] == "Arsenal"


def test_espn_wrong_identity_fails_closed():
    broken = event()
    broken["competitions"][0]["competitors"][1]["homeAway"] = "home"
    with pytest.raises(ValueError, match="home/away"):
        parse_espn_schedule({"events": [broken]}, now_utc=NOW)


def test_espn_duplicate_id_fails_closed():
    with pytest.raises(ValueError, match="duplicated"):
        parse_espn_schedule({"events": [event(), event()]}, now_utc=NOW)


def test_espn_missing_payload_fails_closed():
    with pytest.raises(ValueError, match="bounded list"):
        parse_espn_schedule({}, now_utc=NOW)


def test_keyless_espn_one_request_and_never_calls_paid_odds_api():
    calls = []
    class Response:
        status_code = 200
        def json(self):
            return {"events": [event()]}
    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return Response()
    result = fetch_upcoming_fixtures(now_utc=NOW, get=fake_get)
    assert result["source_mode"] == "espn_public_schedule"
    assert len(result["fixtures"]) == 1
    assert len(calls) == 1
    assert calls[0][0].startswith("https://site.api.espn.com/")
    assert "apiKey" not in calls[0][1]["params"]
    assert calls[0][1]["allow_redirects"] is False
    assert result["has_model_forecasts"] is False


def test_keyless_api_failure_shows_attributed_official_schedule_not_forecasts():
    def unavailable(url, **kwargs):
        raise requests.ConnectionError("test outage")
    result = fetch_upcoming_fixtures(now_utc=NOW, get=unavailable)
    assert result["source_mode"] == "official_published_schedule_fallback"
    assert result["source_url"] == OFFICIAL_SCHEDULE_URL
    assert len(result["fixtures"]) == 10
    assert result["has_model_forecasts"] is False


def test_fixture_endpoint_is_independent_of_product_prediction_contract():
    web = Path("web_app.py").read_text(encoding="utf-8")
    ui = Path("static/index_v2.html").read_text(encoding="utf-8")
    assert '@app.get("/upcoming-fixtures")' in web
    assert "live_upcoming_fixtures" in web
    assert "fetch('/upcoming-fixtures'" in ui
    assert "Ожидается прогноз модели" in ui
    assert "Букмекерские коэффициенты ещё не загружены" in ui
