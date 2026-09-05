import pytest

from multi_market_settlement import (
    HALF_LOSS,
    HALF_WIN,
    INVALID,
    LOSS,
    NOT_OFFERED,
    PUSH,
    UNSETTLED_MISSING_OUTCOME,
    WIN,
    settle_1x2,
    settle_handicap,
    settle_multi_market_card,
    settle_total,
)


def test_1x2_classification():
    assert settle_1x2("1", 2, 1).status == WIN
    assert settle_1x2("DRAW", 2, 2).status == WIN
    assert settle_1x2("A", 2, 1).status == LOSS
    assert settle_1x2("HOME", None, 1).status == UNSETTLED_MISSING_OUTCOME


def test_total_half_and_integer_lines():
    assert settle_total("OVER", 3, 2.5).status == WIN
    assert settle_total("UNDER", 3, 2.5).status == LOSS
    assert settle_total("OVER", 3, 3.0).status == PUSH
    assert settle_total("UNDER", 2, 3.0).status == WIN


def test_total_quarter_lines():
    over_225 = settle_total("OVER", 2, 2.25)
    assert over_225.status == HALF_LOSS
    assert over_225.score == -0.5

    over_275 = settle_total("OVER", 3, 2.75)
    assert over_275.status == HALF_WIN
    assert over_275.score == 0.5

    under_225 = settle_total("UNDER", 2, 2.25)
    assert under_225.status == HALF_WIN
    assert under_225.score == 0.5

    under_275 = settle_total("UNDER", 3, 2.75)
    assert under_275.status == HALF_LOSS
    assert under_275.score == -0.5


def test_handicap_half_integer_and_quarter_lines():
    assert settle_handicap("HOME", 2, 1, -0.5).status == WIN
    assert settle_handicap("AWAY", 2, 1, -0.5).status == LOSS
    assert settle_handicap("HOME", 2, 1, -1.0).status == PUSH
    assert settle_handicap("HOME", 2, 1, -0.75).status == HALF_WIN
    assert settle_handicap("AWAY", 2, 1, -0.75).status == HALF_LOSS
    assert settle_handicap("HOME", 1, 2, 1.25).status == HALF_WIN


def test_invalid_line_increment_is_rejected():
    assert settle_total("OVER", 3, 2.3).status == INVALID
    assert settle_handicap("HOME", 2, 1, -0.3).status == INVALID


def _card():
    return {
        "schema_version": "MULTI_MARKET_V1",
        "research_only": True,
        "handicap": {
            "home_handicap": -0.5,
            "away_handicap": 0.5,
            "home_probability": 0.52,
            "away_probability": 0.48,
        },
        "total_goals": {
            "point": 2.5,
            "over_probability": 0.51,
            "under_probability": 0.49,
        },
        "total_corners": {
            "point": 9.5,
            "over_probability": 0.5,
            "under_probability": 0.5,
        },
        "team_corners": {
            "home": {
                "point": 5.5,
                "over_probability": 0.48,
                "under_probability": 0.52,
            },
            "away": {
                "point": 3.5,
                "over_probability": 0.47,
                "under_probability": 0.53,
            },
        },
    }


def test_card_settlement_uses_existing_goal_outcome_contract():
    settled = settle_multi_market_card(_card(), {"home_goals": 2, "away_goals": 1})
    assert settled["schema_version"] == "MULTI_MARKET_SETTLEMENT_V2"
    assert settled["research_only"] is True
    assert settled["handicap"]["home"]["status"] == WIN
    assert settled["handicap"]["away"]["status"] == LOSS
    assert settled["total_goals"]["over"]["status"] == WIN
    assert settled["total_goals"]["under"]["status"] == LOSS


def test_corner_markets_stay_unsettled_without_corner_observations():
    settled = settle_multi_market_card(_card(), {"home_goals": 2, "away_goals": 1})
    assert settled["total_corners"]["over"]["status"] == UNSETTLED_MISSING_OUTCOME
    assert settled["team_corners"]["home"]["over"]["status"] == UNSETTLED_MISSING_OUTCOME
    assert settled["team_corners"]["away"]["under"]["status"] == UNSETTLED_MISSING_OUTCOME


def test_corner_markets_settle_only_when_explicit_observations_are_supplied():
    settled = settle_multi_market_card(
        _card(),
        {"home_goals": 2, "away_goals": 1, "home_corners": 6, "away_corners": 4},
    )
    assert settled["total_corners"]["over"]["status"] == WIN
    assert settled["total_corners"]["under"]["status"] == LOSS
    assert settled["team_corners"]["home"]["over"]["status"] == WIN
    assert settled["team_corners"]["away"]["over"]["status"] == WIN


def test_missing_market_is_not_offered_not_fabricated():
    card = _card()
    card["total_corners"] = None
    card["team_corners"]["away"] = None
    settled = settle_multi_market_card(card, {"home_goals": 1, "away_goals": 0, "home_corners": 5, "away_corners": 2})
    assert settled["total_corners"]["over"]["status"] == NOT_OFFERED
    assert settled["team_corners"]["away"]["over"]["status"] == NOT_OFFERED


def test_non_research_or_wrong_schema_card_is_rejected():
    with pytest.raises(ValueError):
        settle_multi_market_card({"schema_version": "MULTI_MARKET_V1", "research_only": False}, {})
    with pytest.raises(ValueError):
        settle_multi_market_card({"schema_version": "OTHER", "research_only": True}, {})
