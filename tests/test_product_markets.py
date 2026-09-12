import math

import pytest

from product_markets import (
    build_product_match,
    build_product_market_view,
    fair_odds,
    fixture_key,
    product_match_id,
    raw_expected_value,
)


def sample_prediction(**overrides):
    row = {
        "league": "EPL",
        "event_id": "event-arsenal-coventry",
        "commence_time_utc": "2026-09-12T14:00:00+00:00",
        "match_date": "2026-09-12",
        "match_time": "15:00",
        "home_team": "Arsenal",
        "away_team": "Coventry City",
        "home_team_model": "Arsenal",
        "away_team_model": "Coventry City",
        "prediction": "HOME",
        "prediction_strength": "MEDIUM",
        "model_agreement": True,
        "home_probability": 0.60,
        "draw_probability": 0.24,
        "away_probability": 0.16,
        "expected_home_goals": 1.8,
        "expected_away_goals": 0.9,
        "expected_total_goals": 2.7,
        "over_2_5_probability": 0.58,
        "under_2_5_probability": 0.42,
        "btts_yes_probability": 0.51,
        "btts_no_probability": 0.49,
        "top_score": "2:1",
        "top_score_probability": 0.12,
    }
    row.update(overrides)
    return row


def test_fair_odds_and_raw_ev_for_simple_market():
    assert fair_odds(0.60) == pytest.approx(1.0 / 0.60)
    assert raw_expected_value(0.60, 1.90) == pytest.approx(0.14)


def test_main_forecast_uses_probability_not_raw_ev():
    view = build_product_match(
        sample_prediction(
            home_team="Liverpool",
            away_team="Fulham",
            home_probability=0.675,
            draw_probability=0.157,
            away_probability=0.168,
            over_2_5_probability=0.55,
            under_2_5_probability=0.45,
        ),
        {
            "home_odds": 1.43,
            "draw_odds": 4.92,
            "away_odds": 6.42,
        },
    )

    assert view["main_forecast"]["status"] == "model_forecast"
    assert view["main_forecast"]["market"] == "1x2"
    assert view["main_forecast"]["selection"]["code"] == "HOME"
    assert view["main_forecast"]["selection"]["probability"] == pytest.approx(0.675)

    assert view["value_signal"]["status"] == "positive_raw_ev"
    assert view["value_signal"]["selection"]["code"] == "AWAY"
    assert view["value_signal"]["selection"]["raw_expected_value"] > 0
    assert view["main_choice"]["selection"]["code"] == "HOME"
    assert view["bet_decision"]["status"] == "no_bet"


def test_no_positive_priced_edge_keeps_forecast_but_no_value_signal():
    view = build_product_match(
        sample_prediction(),
        {
            "home_odds": 1.60,
            "draw_odds": 3.80,
            "away_odds": 5.50,
        },
    )

    assert view["main_forecast"]["status"] == "model_forecast"
    assert view["main_forecast"]["selection"] is not None
    assert view["value_signal"]["status"] == "none"
    assert view["value_signal"]["selection"] is None


def test_missing_bookmaker_prices_preserve_forecast_without_value():
    view = build_product_match(sample_prediction())

    one_x_two = view["markets"]["1x2"]
    assert one_x_two["display_selection"]["code"] == "HOME"
    assert one_x_two["display_selection"]["probability"] == pytest.approx(0.60)
    assert one_x_two["display_selection"]["fair_odds"] == pytest.approx(1.0 / 0.60)
    assert one_x_two["display_selection"]["bookmaker_odds"] is None
    assert view["main_forecast"]["selection"] is not None
    assert view["value_signal"]["status"] == "none"


def test_higher_probability_model_only_total_stays_alternative_to_operational_1x2():
    view = build_product_match(
        sample_prediction(over_2_5_probability=0.72, under_2_5_probability=0.28),
        {
            "home_odds": 1.60,
            "draw_odds": 3.80,
            "away_odds": 5.50,
        },
    )

    total = view["markets"]["total_goals"]
    assert total["display_selection"]["code"] == "OVER_2_5"
    assert total["display_selection"]["probability"] == pytest.approx(0.72)
    assert total["readiness"]["decision_tier"] == 1
    assert total["readiness"]["decision_confidence"] == "provisional"

    assert view["main_forecast"]["market"] == "1x2"
    assert view["main_forecast"]["selection"]["code"] == "HOME"
    assert view["alternatives"][0]["market"] == "total_goals"
    assert view["alternatives"][0]["selection"]["code"] == "OVER_2_5"
    assert view["confidence"]["level"] == "operational"


def test_model_only_total_can_be_provisional_main_when_operational_1x2_missing():
    view = build_product_match(
        sample_prediction(
            home_probability=None,
            draw_probability=None,
            away_probability=None,
            over_2_5_probability=0.72,
            under_2_5_probability=0.28,
        )
    )

    assert view["main_forecast"]["market"] == "total_goals"
    assert view["main_forecast"]["selection"]["code"] == "OVER_2_5"
    assert view["main_forecast"]["decision_tier"] == 1
    assert view["confidence"]["level"] == "provisional"
    assert view["bet_decision"]["status"] == "no_bet"


def test_research_markets_never_fabricate_selections():
    view = build_product_match(sample_prediction())

    for market_name in ("handicap", "corners_total"):
        market = view["markets"][market_name]
        assert market["readiness"]["status"] == "research_only"
        assert market["readiness"]["decision_tier"] == 0
        assert market["readiness"]["eligible_for_main_forecast"] is False
        assert market["readiness"]["eligible_for_value"] is False
        assert market["readiness"]["eligible_for_bet_recommendation"] is False
        assert market["selections"] == []
        assert market["display_selection"] is None


def test_nan_values_are_serialization_safe():
    view = build_product_match(
        sample_prediction(home_probability=math.nan, expected_total_goals=math.nan)
    )

    home = view["markets"]["1x2"]["selections"][0]
    assert home["probability"] is None
    assert home["fair_odds"] is None
    assert view["model_context"]["expected_total_goals"] is None


def test_fixture_key_includes_scheduled_kickoff_fields():
    first = sample_prediction(match_date="2026-09-12", match_time="15:00")
    second = sample_prediction(match_date="2026-10-03", match_time="17:30")
    assert fixture_key(first) != fixture_key(second)


def test_product_match_id_prefers_provider_event_id():
    row = sample_prediction(event_id="provider-123")
    assert product_match_id(row) == "event_provider-123"
    assert build_product_match(row)["match"]["product_match_id"] == "event_provider-123"


def test_product_match_id_has_deterministic_fixture_fallback():
    row = sample_prediction(event_id=None)
    first = product_match_id(row)
    second = product_match_id(dict(row))
    assert first == second
    assert first.startswith("fixture_")


def test_product_match_id_does_not_depend_on_list_order():
    first = sample_prediction(event_id="event-a", home_team="Arsenal")
    second = sample_prediction(event_id="event-b", home_team="Liverpool")
    normal = build_product_market_view([first, second])
    reversed_view = build_product_market_view([second, first])

    normal_ids = {m["match"]["home_team"]: m["match"]["product_match_id"] for m in normal["matches"]}
    reversed_ids = {m["match"]["home_team"]: m["match"]["product_match_id"] for m in reversed_view["matches"]}
    assert normal_ids == reversed_ids


def test_market_view_does_not_cross_match_same_teams_at_different_kickoffs():
    first = sample_prediction(event_id="event-first", match_date="2026-09-12", match_time="15:00")
    second = sample_prediction(event_id="event-second", match_date="2026-10-03", match_time="17:30")
    odds_by_fixture = {
        fixture_key(first): {"home_odds": 1.90, "draw_odds": 4.00, "away_odds": 7.00}
    }

    payload = build_product_market_view([first, second], odds_by_fixture=odds_by_fixture)

    first_market = payload["matches"][0]["markets"]["1x2"]
    second_market = payload["matches"][1]["markets"]["1x2"]
    assert first_market["selections"][0]["bookmaker_odds"] == pytest.approx(1.90)
    assert second_market["selections"][0]["bookmaker_odds"] is None
    assert payload["matches"][1]["main_forecast"]["status"] == "model_forecast"
    assert payload["matches"][1]["value_signal"]["status"] == "none"


def test_versioned_view_exposes_decision_framework_policy():
    payload = build_product_market_view([sample_prediction()])

    assert payload["schema_version"] == "product-market-view.v1"
    assert payload["decision_framework_version"] == "product-decision.v1"
    assert "event_id" in payload["fixture_identity"]
    assert payload["market_readiness"]["1x2"]["status"] == "comparison_ready"
    assert payload["market_readiness"]["corners_total"]["status"] == "research_only"
    assert "decision tier" in payload["selection_policy"]["forecast"]
    assert "never overrides forecast" in payload["selection_policy"]["value"]
    assert "no_bet" in payload["selection_policy"]["bet_decision"]
    assert len(payload["matches"]) == 1
