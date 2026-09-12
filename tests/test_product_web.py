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
    second = prediction(
        match_date="2026-10-03",
        match_time="17:30",
    )

    payload = assemble_product_market_view(
        [first, second],
        [odds_row()],
    )

    first_home = payload["matches"][0]["markets"]["1x2"]["selections"][0]
    second_home = payload["matches"][1]["markets"]["1x2"]["selections"][0]

    assert first_home["bookmaker_odds"] == pytest.approx(1.90)
    assert first_home["raw_expected_value"] == pytest.approx(0.14)
    assert second_home["bookmaker_odds"] is None
    assert second_home["raw_expected_value"] is None
    assert payload["matches"][1]["main_choice"]["status"] == "no_bet"


def test_adapter_never_creates_goal_total_bookmaker_price():
    payload = assemble_product_market_view(
        [prediction(over_2_5_probability=0.70)],
        [odds_row()],
    )

    total = payload["matches"][0]["markets"]["total_goals"]
    assert total["display_selection"]["code"] == "OVER_2_5"
    assert total["display_selection"]["bookmaker_odds"] is None
    assert total["readiness"]["eligible_for_main_choice"] is False
