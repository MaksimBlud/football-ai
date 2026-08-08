import joblib

from model_utils import build_match_features
from poisson_utils import calculate_markets


HOME_MODEL_PATH = "home_goals_model_no_odds.pkl"
AWAY_MODEL_PATH = "away_goals_model_no_odds.pkl"

OVER_CALIBRATOR_PATH = "over_2_5_calibrator.pkl"
BTTS_CALIBRATOR_PATH = "btts_calibrator.pkl"


def predict_goal_markets_no_odds(
    home_team,
    away_team,
):
    home_model = joblib.load(
        HOME_MODEL_PATH
    )

    away_model = joblib.load(
        AWAY_MODEL_PATH
    )

    # build_match_features пока технически требует odds.
    # Эти значения нужны только для построения остальных
    # признаков и НЕ передаются в no-odds модели.
    features = build_match_features(
        home_team=home_team,
        away_team=away_team,
        home_odds=2.0,
        draw_odds=2.0,
        away_odds=2.0,
    )

    home_features = features[
        list(home_model.feature_names_in_)
    ]

    away_features = features[
        list(away_model.feature_names_in_)
    ]

    expected_home_goals = max(
        0.0,
        float(
            home_model.predict(
                home_features
            )[0]
        ),
    )

    expected_away_goals = max(
        0.0,
        float(
            away_model.predict(
                away_features
            )[0]
        ),
    )

    markets = calculate_markets(
        expected_home_goals=expected_home_goals,
        expected_away_goals=expected_away_goals,
    )

    raw_over_probability = (
        markets["over_2_5_probability"]
    )

    raw_btts_probability = (
        markets["btts_yes_probability"]
    )

    over_calibrator = joblib.load(
        OVER_CALIBRATOR_PATH
    )

    btts_calibrator = joblib.load(
        BTTS_CALIBRATOR_PATH
    )

    if over_calibrator["method"] == "SIGMOID":
        over_probability = float(
            over_calibrator["model"]
            .predict_proba(
                [[raw_over_probability]]
            )[0, 1]
        )

    elif over_calibrator["method"] == "ISOTONIC":
        over_probability = float(
            over_calibrator["model"]
            .predict(
                [raw_over_probability]
            )[0]
        )

    else:
        over_probability = float(
            raw_over_probability
        )

    if btts_calibrator["method"] == "SIGMOID":
        btts_probability = float(
            btts_calibrator["model"]
            .predict_proba(
                [[raw_btts_probability]]
            )[0, 1]
        )

    elif btts_calibrator["method"] == "ISOTONIC":
        btts_probability = float(
            btts_calibrator["model"]
            .predict(
                [raw_btts_probability]
            )[0]
        )

    else:
        btts_probability = float(
            raw_btts_probability
        )

    return {
        "home_team": home_team,
        "away_team": away_team,

        "expected_home_goals": (
            expected_home_goals
        ),

        "expected_away_goals": (
            expected_away_goals
        ),

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
            over_probability
        ),

        "under_2_5_probability": (
            1.0 - over_probability
        ),

        "btts_yes_probability": (
            btts_probability
        ),

        "btts_no_probability": (
            1.0 - btts_probability
        ),

        "raw_over_2_5_probability": (
            float(raw_over_probability)
        ),

        "raw_btts_yes_probability": (
            float(raw_btts_probability)
        ),

        "top_scores": markets["top_scores"],

        "odds_used": False,
    }
