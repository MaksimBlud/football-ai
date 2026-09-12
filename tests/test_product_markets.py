import math

import pytest

from product_markets import (
    build_product_match,
    build_product_market_view,
    fair_odds,
    fixture_key,
    raw_expected_value,
)


def sample_prediction(**overrides):
    row = {
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


def test_positive_1x2_candidate_becomes_provisional_main_choice():
    view = build_product_match(
        sample_prediction(),
        {
            "home_odds": 1.90,
            "draw_odds": 4.00,
            "away_odds": 7.00,
        },
    )

    assert view["main_choice"]["status"] == "provisional_candidate"
    assert view["main_choice"]["market"] == "1x2"
    assert view["main_choice"]["selection"]["code"] == "HOME"
    assert view["main_choice"]["selection"]["raw_expected_value"] == pytest.approx(0.14)


def test_no_positive_priced_edge_returns_no_bet():
    view = build_product_match(
        sample_prediction(),
        {
            "home_odds": 1.60,
            "draw_odds": 3.80,
            "away_odds": 5.50,
        },
    )

    assert view["main_choice"]["status"] == "no_bet"
    assert view["main_choice"]["selection"] is None


def test_missing_bookmaker_prices_preserve_probabilities_but_not_main_choice():
    view = build_product_match(sample_prediction())

    one_x_two = view["markets"]["1x2"]
    assert one_x_two["display_selection"]["code"] == "HOME"
    assert one_x_two["display_selection"]["probability"] == pytest.approx(0.60)
    assert one_x_two["display_selection"]["fair_odds"] == pytest.approx(1.0 / 0.60)
    assert one_x_two["display_selection"]["bookmaker_odds"] is None
    assert view["main_choice"]["status"] == "no_bet"


def test_goal_total_is_visible_but_not_eligible_for_main_choice():
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
    assert total["readiness"]["status"] == "model_only"
    assert total["readiness"]["eligible_for_main_choice"] is False
    assert view["main_choice"]["status"] == "no_bet"


def test_research_markets_never_fabricate_selections():
    view = build_product_match(sample_prediction())

    for market_name in ("handicap", "corners_total"):
        market = view["markets"][market_name]
        assert market["readiness"]["status"] == "research_only"
        assert market["readiness"]["eligible_for_main_choice"] is False
        assert market["selections"] == []
        assert market["display_selection"] is None


def test_nan_values_are_serialization_safe():
    view = build_product_match(
        sample_prediction(
            home_probability=math.nan,
            expected_total_goals=math.nan,
        )
    )

    home = view["markets"]["1x2"]["selections"][0]
    assert home["probability"] is None
    assert home["fair_odds"] is None
    assert view["model_context"]["expected_total_goals"] is None


def test_fixture_key_includes_scheduled_kickoff_fields():
    first = sample_prediction(match_date="2026-09-12", match_time="15:00")
    second = sample_prediction(match_date="2026-10-03", match_time="17:30")

    assert fixture_key(first) != fixture_key(second)


def test_market_view_does_not_cross_match_same_teams_at_different_kickoffs():
    first = sample_prediction(match_date="2026-09-12", match_time="15:00")
    second = sample_prediction(match_date="2026-10-03", match_time="17:30")
    odds_by_fixture = {
        fixture_key(first): {
            "home_odds": 1.90,
            "draw_odds": 4.00,
            "away_odds": 7.00,
        }
    }

    payload = build_product_market_view(
        [first, second],
        odds_by_fixture=odds_by_fixture,
    )

    first_market = payload["matches"][0]["markets"]["1x2"]
    second_market = payload["matches"][1]["markets"]["1x2"]
    assert first_market["selections"][0]["bookmaker_odds"] == pytest.approx(1.90)
    assert second_market["selections"][0]["bookmaker_odds"] is None
    assert payload["matches"][1]["main_choice"]["status"] == "no_bet"


def test_versioned_view_exposes_readiness_and_selection_policy():
    payload = build_product_market_view([sample_prediction()])

    assert payload["schema_version"] == "product-market-view.v1"
    assert "match_date" in payload["fixture_identity"]
    assert payload["market_readiness"]["1x2"]["status"] == "comparison_ready"
    assert payload["market_readiness"]["corners_total"]["status"] == "research_only"
    assert "reliability-aware" in payload["selection_policy"]["future"]
    assert len(payload["matches"]) == 1
