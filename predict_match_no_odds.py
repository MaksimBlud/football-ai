from pathlib import Path

import joblib
import numpy as np

from model_utils import build_match_features


MODEL_PATH = Path(
    "football_model_no_odds.pkl"
)

CALIBRATOR_PATH = Path(
    "1x2_calibrator.pkl"
)


OUTCOME_NAMES = {
    0: "HOME",
    1: "DRAW",
    2: "AWAY",
}


def normalize_probabilities(
    probabilities,
):
    probabilities = np.clip(
        probabilities,
        1e-7,
        1 - 1e-7,
    )

    return (
        probabilities
        / probabilities.sum()
    )


def calibrate_probabilities(
    raw_probabilities,
):
    if not CALIBRATOR_PATH.exists():
        raise FileNotFoundError(
            f"Калибратор не найден: "
            f"{CALIBRATOR_PATH}"
        )

    calibrator = joblib.load(
        CALIBRATOR_PATH
    )

    raw_probabilities = (
        normalize_probabilities(
            np.asarray(
                raw_probabilities,
                dtype=float,
            )
        )
    )

    method = calibrator.get(
        "method",
        "RAW",
    )

    if method == "MULTINOMIAL":
        model = calibrator["model"]

        log_probabilities = np.log(
            raw_probabilities
        ).reshape(1, -1)

        calibrated = (
            model.predict_proba(
                log_probabilities
            )[0]
        )

        return normalize_probabilities(
            calibrated
        )

    if method == "TEMPERATURE":
        temperature = float(
            calibrator["temperature"]
        )

        logits = np.log(
            raw_probabilities
        )

        scaled = (
            logits
            / temperature
        )

        scaled = (
            scaled
            - scaled.max()
        )

        calibrated = np.exp(
            scaled
        )

        return normalize_probabilities(
            calibrated
        )

    return raw_probabilities


def predict_match_no_odds(
    home_team,
    away_team,
):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Модель не найдена: "
            f"{MODEL_PATH}"
        )

    model = joblib.load(
        MODEL_PATH
    )

    # build_match_features пока
    # технически требует odds.
    # Эти значения НЕ передаются
    # в no-odds модель.
    features = build_match_features(
        home_team=home_team,
        away_team=away_team,
        home_odds=2.0,
        draw_odds=2.0,
        away_odds=2.0,
    )

    model_features = features[
        list(model.feature_names_in_)
    ]

    raw_probabilities = (
        model.predict_proba(
            model_features
        )[0]
    )

    calibrated_probabilities = (
        calibrate_probabilities(
            raw_probabilities
        )
    )

    prediction_index = int(
        np.argmax(
            calibrated_probabilities
        )
    )

    return {
        "home_team": home_team,
        "away_team": away_team,

        "prediction": (
            OUTCOME_NAMES[
                prediction_index
            ]
        ),

        # Калиброванные вероятности.
        "home_probability": float(
            calibrated_probabilities[0]
        ),
        "draw_probability": float(
            calibrated_probabilities[1]
        ),
        "away_probability": float(
            calibrated_probabilities[2]
        ),

        # Сырые вероятности XGBoost.
        "raw_home_probability": float(
            raw_probabilities[0]
        ),
        "raw_draw_probability": float(
            raw_probabilities[1]
        ),
        "raw_away_probability": float(
            raw_probabilities[2]
        ),

        "home_last5_points": int(
            features.iloc[0][
                "home_last5_points"
            ]
        ),

        "away_last5_points": int(
            features.iloc[0][
                "away_last5_points"
            ]
        ),

        "home_elo": float(
            features.iloc[0]["home_elo"]
        ),

        "away_elo": float(
            features.iloc[0]["away_elo"]
        ),

        "odds_used": False,
        "probabilities_calibrated": True,
    }
