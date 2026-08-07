import joblib

from model_utils import build_match_features
from poisson_utils import calculate_markets


HOME_MODEL_PATH = "home_goals_model.pkl"
AWAY_MODEL_PATH = "away_goals_model.pkl"


def predict_goal_markets(
    home_team,
    away_team,
    home_odds,
    draw_odds,
    away_odds,
):
    home_model = joblib.load(HOME_MODEL_PATH)
    away_model = joblib.load(AWAY_MODEL_PATH)

    features = build_match_features(
        home_team=home_team,
        away_team=away_team,
        home_odds=home_odds,
        draw_odds=draw_odds,
        away_odds=away_odds,
    )

    expected_home_goals = max(
        0.0,
        float(home_model.predict(features)[0]),
    )

    expected_away_goals = max(
        0.0,
        float(away_model.predict(features)[0]),
    )

    markets = calculate_markets(
        expected_home_goals=expected_home_goals,
        expected_away_goals=expected_away_goals,
    )

    top_scores = [
        {
            "home_goals": score["home_goals"],
            "away_goals": score["away_goals"],
            "probability": score["probability"],
        }
        for score in markets["top_scores"]
    ]

    return {
        "home_team": home_team,
        "away_team": away_team,
        "expected_home_goals": expected_home_goals,
        "expected_away_goals": expected_away_goals,
        "expected_total_goals": (
            expected_home_goals
            + expected_away_goals
        ),
        "home_win_probability": (
            markets["home_win_probability"]
        ),
        "draw_probability": (
            markets["draw_probability"]
        ),
        "away_win_probability": (
            markets["away_win_probability"]
        ),
        "over_2_5_probability": (
            markets["over_2_5_probability"]
        ),
        "under_2_5_probability": (
            markets["under_2_5_probability"]
        ),
        "btts_yes_probability": (
            markets["btts_yes_probability"]
        ),
        "btts_no_probability": (
            markets["btts_no_probability"]
        ),
        "top_scores": top_scores,
    }
