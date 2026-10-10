import pytest

from product_markets import fixture_key
from product_web import assemble_product_market_view, build_odds_by_fixture


def prediction(**overrides):
    row = {
        "match_date": "2026-09-12",
        "match_time": "15:00",
        "home_team": "Arsenal",
        "away_team": "Coventry City",
        "home_team_model": "Arsenal",
        "away_team_model": "Coventry City",
        "home_probability": 0.60,
        "draw_probability": 0.24,
        "away_probability": 0.16,
        "over_2_5_probability": 0.58,
        "under_2_5_probability": 0.42,
    }
    row.update(overrides)
    return row


def odds_row(**overrides):
    row = {
        "match_date": "2026-09-12",
        "match_time": "15:00",
        "home_team": "Arsenal",
        "away_team": "Coventry City",
        "home_team_model": "Arsenal",
        "away_team_model": "Coventry City",
        "home_odds": 1.90,
        "draw_odds": 4.00,
        "away_odds": 7.00,
    }
    row.update(overrides)
    return row


def test_odds_index_uses_full_scheduled_fixture_identity():
    first = odds_row()
    second = odds_row(
        match_date="2026-10-03",
        match_time="17:30",
        home_odds=1.70,
    )

    index = build_odds_by_fixture([first, second])

    assert len(index) == 2
    assert index[fixture_key(first)]["home_odds"] == pytest.approx(1.90)
    assert index[fixture_key(second)]["home_odds"] == pytest.approx(1.70)


def test_server_assembly_attaches_price_only_to_exact_fixture():
    first = prediction()
    second = prediction(match_date="2026-10-03", match_time="17:30")

    payload = assemble_product_market_view([first, second], [odds_row()])

    first_item = payload["matches"][0]
    second_item = payload["matches"][1]
    first_home = first_item["markets"]["1x2"]["selections"][0]
    second_home = second_item["markets"]["1x2"]["selections"][0]

    assert first_home["bookmaker_odds"] == pytest.approx(1.90)
    assert first_home["raw_expected_value"] == pytest.approx(0.14)
    assert first_item["main_forecast"]["status"] == "model_forecast"
    assert first_item["value_signal"]["status"] == "positive_raw_ev"
    assert first_item["bet_decision"]["status"] == "no_bet"

    assert second_home["bookmaker_odds"] is None
    assert second_home["raw_expected_value"] is None
    assert second_item["main_forecast"]["status"] == "model_forecast"
    assert second_item["value_signal"]["status"] == "none"


def test_adapter_never_creates_goal_total_bookmaker_price_or_promotes_model_only_tier():
    payload = assemble_product_market_view(
        [prediction(over_2_5_probability=0.70, under_2_5_probability=0.30)],
        [odds_row()],
    )

    item = payload["matches"][0]
    total = item["markets"]["total_goals"]
    assert total["display_selection"]["code"] == "OVER_2_5"
    assert total["display_selection"]["bookmaker_odds"] is None
    assert total["readiness"]["decision_tier"] == 1
    assert total["readiness"]["eligible_for_main_forecast"] is True
    assert total["readiness"]["eligible_for_value"] is False

    assert item["main_forecast"]["market"] == "1x2"
    assert item["alternatives"][0]["market"] == "total_goals"
    assert item["confidence"]["level"] == "operational"


# Schedule-only endpoint contract (independent of AI probabilities and book prices)
from datetime import datetime, timezone

from product_fixture_schedule import (
    ESPN_URL,
    OFFICIAL_SCHEDULE_URL,
    fetch_upcoming_fixtures,
    official_week_6_fallback,
    parse_espn_schedule,
)


SCHEDULE_TEST_NOW = datetime(2026, 10, 9, 15, 0, tzinfo=timezone.utc)


def sample_calendar_event(*, identity="schedule-1", date="2026-10-10T11:30:00Z",
                          home="Arsenal", away="Leeds United", state="pre"):
    return {
        "id": identity,
        "date": date,
        "status": {"type": {"state": state, "completed": state == "post"}},
        "competitions": [{"competitors": [
            {"homeAway": "home", "team": {"displayName": home}},
            {"homeAway": "away", "team": {"displayName": away}},
        ]}],
    }


def test_published_week_six_fallback_is_explicit_schedule_only():
    rows = official_week_6_fallback(now_utc=SCHEDULE_TEST_NOW)
    assert len(rows) == 10
    assert rows[0]["home_team"] == "Arsenal"
    assert rows[0]["kickoff_utc"] == "2026-10-10T11:30:00+00:00"
    assert rows[-1]["home_team"] == "Coventry City"
    assert rows[-1]["kickoff_utc"] == "2026-10-12T19:00:00+00:00"
    assert all(row["schedule_source"] == "premier_league_official_published_schedule" for row in rows)
    assert all(row["model_forecast_status"] == "not_available" for row in rows)
    assert all(row["bookmaker_odds_status"] == "not_available" for row in rows)


def test_expired_published_fixture_fallback_returns_no_past_matches():
    assert official_week_6_fallback(
        now_utc=datetime(2026, 10, 13, tzinfo=timezone.utc)
    ) == []


def test_keyless_espn_calendar_returns_only_pre_kickoff_events_sorted():
    data = {"events": [
        sample_calendar_event(identity="later", date="2026-10-11T13:00:00Z"),
        sample_calendar_event(identity="early"),
        sample_calendar_event(identity="finished", state="post"),
        sample_calendar_event(identity="past", date="2026-10-09T10:00:00Z"),
    ]}
    items = parse_espn_schedule(data, now_utc=SCHEDULE_TEST_NOW)
    assert [x["schedule_id"] for x in items] == ["espn:early", "espn:later"]
    assert all(x["model_forecast_status"] == "not_available" for x in items)


def test_keyless_calendar_rejects_duplicate_event_ids_and_malformed_identity():
    event = sample_calendar_event()
    with pytest.raises(ValueError, match="duplicated"):
        parse_espn_schedule({"events": [event, event]}, now_utc=SCHEDULE_TEST_NOW)
    broken = sample_calendar_event()
    broken["competitions"][0]["competitors"][1]["homeAway"] = "home"
    with pytest.raises(ValueError, match="home/away"):
        parse_espn_schedule({"events": [broken]}, now_utc=SCHEDULE_TEST_NOW)
    with pytest.raises(ValueError, match="status"):
        parse_espn_schedule({"events": [{"id": "bad", "status": "pre"}]}, now_utc=SCHEDULE_TEST_NOW)
    with pytest.raises(ValueError, match="bounded list"):
        parse_espn_schedule({}, now_utc=SCHEDULE_TEST_NOW)


def test_keyless_calendar_get_has_no_keys_no_redirects_and_one_call():
    calls = []

    class Response:
        status_code = 200

        def json(self):
            return {"events": [sample_calendar_event()]}

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    result = fetch_upcoming_fixtures(now_utc=SCHEDULE_TEST_NOW, get=fake_get)
    assert result["source_mode"] == "espn_public_schedule"
    assert result["has_model_forecasts"] is False
    assert result["has_bookmaker_odds"] is False
    assert len(result["fixtures"]) == 1
    assert len(calls) == 1
    assert calls[0][0] == ESPN_URL
    assert set(calls[0][1]["params"]) == {"dates"}
    assert calls[0][1]["allow_redirects"] is False
    assert calls[0][1]["timeout"] <= 12


def test_offline_calendar_fallback_expires_without_fabricating_predictions():
    def offline(url, **kwargs):
        raise OSError("fixture source unavailable")

    result = fetch_upcoming_fixtures(now_utc=SCHEDULE_TEST_NOW, get=offline)
    assert result["source_mode"] == "official_published_schedule_fallback"
    assert result["source_url"] == OFFICIAL_SCHEDULE_URL
    assert len(result["fixtures"]) == 10
    assert result["has_model_forecasts"] is False
    result_after = fetch_upcoming_fixtures(
        now_utc=datetime(2026, 10, 13, tzinfo=timezone.utc),
        get=offline,
    )
    assert result_after["source_mode"] == "unavailable"
    assert result_after["fixtures"] == []


def test_public_calendar_route_is_separate_from_prediction_snapshots():
    from pathlib import Path

    web = Path("web_app.py").read_text(encoding="utf-8")
    ui = Path("static/index_v2.html").read_text(encoding="utf-8")
    assert 'from product_fixture_schedule import live_upcoming_fixtures' in web
    assert '@app.get("/upcoming-fixtures")' in web
    assert "return live_upcoming_fixtures()" in web
    assert "fetch('/upcoming-fixtures'" in ui
    assert "AI-прогноз отсутствует" in ui
    assert "Коэффициенты букмекера отсутствуют" in ui
    assert "data.has_model_forecasts!==false" in ui
    assert "data.has_bookmaker_odds!==false" in ui
