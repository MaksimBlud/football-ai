"""
Shadow Market-Prior challenger for 1X2 predictions.

This module is research infrastructure.

It does NOT replace production predictions.
It does NOT modify production model artifacts.

Challenger v0 intentionally equals the normalized bookmaker market.
AI-vs-market disagreement is exposed only as a diagnostic signal.
"""

from predict_market import predict_market
from predict_match_no_odds import predict_match_no_odds
from team_names import normalize_team_name


OUTCOMES = ("home", "draw", "away")


def predict_challenger(
    home_team,
    away_team,
    home_odds,
    draw_odds,
    away_odds,
):
    home_original = home_team.strip()
    away_original = away_team.strip()

    market = predict_market(
        home_team=home_original,
        away_team=away_original,
        home_odds=home_odds,
        draw_odds=draw_odds,
        away_odds=away_odds,
    )

    ai = predict_match_no_odds(
        home_team=normalize_team_name(home_original),
        away_team=normalize_team_name(away_original),
    )

    delta = {
        outcome: (
            float(ai[f"{outcome}_probability"])
            - float(market[f"{outcome}_probability"])
        )
        for outcome in OUTCOMES
    }

    strongest_disagreement = max(
        delta,
        key=lambda outcome: abs(delta[outcome]),
    )

    # Challenger v0:
    # research has not validated a positive residual adjustment.
    # Therefore market remains the prediction source.
    challenger_probabilities = {
        outcome: float(market[f"{outcome}_probability"])
        for outcome in OUTCOMES
    }

    prediction = max(
        challenger_probabilities,
        key=challenger_probabilities.get,
    ).upper()

    return {
        "home_team": home_original,
        "away_team": away_original,

        "market": market,
        "ai": ai,

        "delta": delta,

        "strongest_disagreement": {
            "outcome": strongest_disagreement.upper(),
            "delta": delta[strongest_disagreement],
            "absolute_delta": abs(
                delta[strongest_disagreement]
            ),
        },

        "challenger": {
            "prediction": prediction,
            "home_probability": (
                challenger_probabilities["home"]
            ),
            "draw_probability": (
                challenger_probabilities["draw"]
            ),
            "away_probability": (
                challenger_probabilities["away"]
            ),
            "adjustment_weight": 0.0,
            "probability_source": "MARKET_PRIOR_V0",
        },

        "shadow_only": True,

        "note": (
            "Challenger v0 equals normalized bookmaker "
            "probabilities. AI disagreement is diagnostic only."
        ),
    }
