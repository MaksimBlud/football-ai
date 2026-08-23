"""Expanding-window OOS evaluation for a La Liga AI challenger.

Research-only:
- trains only in memory;
- saves no .pkl model;
- never touches production artifacts;
- AI model receives NO bookmaker odds;
- bookmaker implied probabilities are benchmark-only;
- each test season is evaluated using previous seasons only.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    log_loss,
)
from xgboost import XGBClassifier


INPUT = Path(
    "data/la_liga_features_with_elo_trainable.csv"
)

PREDICTIONS_OUTPUT = Path(
    "experiments/la_liga_oos_candidate_predictions.csv"
)

METRICS_OUTPUT = Path(
    "experiments/la_liga_oos_candidate_metrics.json"
)

FOLD_OUTPUT = Path(
    "experiments/la_liga_oos_candidate_folds.csv"
)


FEATURES = [
    "home_last5_points",
    "away_last5_points",
    "form_difference",

    "home_goals_scored_last5",
    "home_goals_conceded_last5",
    "away_goals_scored_last5",
    "away_goals_conceded_last5",

    "home_shots_last5",
    "away_shots_last5",

    "home_shots_target_last5",
    "away_shots_target_last5",

    "home_corners_last5",
    "away_corners_last5",

    "home_yellow_last5",
    "away_yellow_last5",

    "home_elo",
    "away_elo",
    "elo_difference",

    "home_venue_win_rate",
    "away_venue_win_rate",

    "home_venue_goals_scored",
    "home_venue_goals_conceded",
    "away_venue_goals_scored",
    "away_venue_goals_conceded",

    "venue_win_rate_difference",
]


TARGET_MAP = {
    "H": 0,
    "D": 1,
    "A": 2,
}

REVERSE_TARGET = {
    0: "H",
    1: "D",
    2: "A",
}


# Leave several seasons for genuine expanding-window OOS.
FIRST_TEST_SEASON = "2020-2021"


def normalized_market_probabilities(
    frame: pd.DataFrame,
) -> np.ndarray:
    odds = frame[
        [
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ].astype(float)

    raw = 1.0 / odds.to_numpy()

    totals = raw.sum(
        axis=1,
        keepdims=True,
    )

    return raw / totals


def multiclass_brier(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> float:
    one_hot = np.eye(3)[
        y_true
    ]

    return float(
        np.mean(
            np.sum(
                (
                    probabilities
                    - one_hot
                ) ** 2,
                axis=1,
            )
        )
    )


def build_model() -> XGBClassifier:
    return XGBClassifier(
        n_estimators=300,
        max_depth=3,
        learning_rate=0.02,
        min_child_weight=1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=2,
    )


def main() -> None:
    df = pd.read_csv(
        INPUT
    )

    df = df.copy()

    df["target"] = (
        df["result"]
        .map(TARGET_MAP)
    )

    required = (
        FEATURES
        + [
            "target",
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    )

    before = len(df)

    df = (
        df
        .dropna(
            subset=required
        )
        .reset_index(drop=True)
    )

    print("=" * 72)
    print("LA LIGA EXPANDING-WINDOW OOS")
    print("=" * 72)

    print(
        "input rows:",
        before,
    )

    print(
        "usable rows:",
        len(df),
    )

    print(
        "AI feature count:",
        len(FEATURES),
    )

    print(
        "AI uses bookmaker odds:",
        False,
    )

    seasons = sorted(
        df["season"]
        .astype(str)
        .unique()
    )

    test_seasons = [
        season
        for season in seasons
        if season >= FIRST_TEST_SEASON
    ]

    print(
        "test seasons:",
        test_seasons,
    )

    fold_rows = []
    prediction_frames = []

    for test_season in test_seasons:
        train = df[
            df["season"]
            .astype(str)
            < test_season
        ].copy()

        test = df[
            df["season"]
            .astype(str)
            == test_season
        ].copy()

        if train.empty or test.empty:
            continue

        model = build_model()

        X_train = train[
            FEATURES
        ]

        y_train = (
            train["target"]
            .astype(int)
        )

        X_test = test[
            FEATURES
        ]

        y_test = (
            test["target"]
            .astype(int)
            .to_numpy()
        )

        model.fit(
            X_train,
            y_train,
        )

        ai_prob = model.predict_proba(
            X_test
        )

        ai_pred = np.argmax(
            ai_prob,
            axis=1,
        )

        market_prob = (
            normalized_market_probabilities(
                test
            )
        )

        market_pred = np.argmax(
            market_prob,
            axis=1,
        )

        home_pred = np.zeros(
            len(test),
            dtype=int,
        )

        ai_accuracy = accuracy_score(
            y_test,
            ai_pred,
        )

        market_accuracy = accuracy_score(
            y_test,
            market_pred,
        )

        home_accuracy = accuracy_score(
            y_test,
            home_pred,
        )

        ai_logloss = log_loss(
            y_test,
            ai_prob,
            labels=[0, 1, 2],
        )

        market_logloss = log_loss(
            y_test,
            market_prob,
            labels=[0, 1, 2],
        )

        ai_brier = multiclass_brier(
            y_test,
            ai_prob,
        )

        market_brier = multiclass_brier(
            y_test,
            market_prob,
        )

        fold_rows.append({
            "test_season":
                test_season,

            "train_rows":
                len(train),

            "test_rows":
                len(test),

            "ai_accuracy":
                ai_accuracy,

            "market_accuracy":
                market_accuracy,

            "home_accuracy":
                home_accuracy,

            "ai_logloss":
                ai_logloss,

            "market_logloss":
                market_logloss,

            "ai_brier":
                ai_brier,

            "market_brier":
                market_brier,

            "ai_minus_market_accuracy":
                ai_accuracy
                - market_accuracy,

            "ai_minus_market_logloss":
                ai_logloss
                - market_logloss,
        })

        output = test[
            [
                "season",
                "match_date",
                "home_team",
                "away_team",
                "result",
                "home_odds",
                "draw_odds",
                "away_odds",
            ]
        ].copy()

        output["actual_target"] = (
            y_test
        )

        output["ai_home_probability"] = (
            ai_prob[:, 0]
        )

        output["ai_draw_probability"] = (
            ai_prob[:, 1]
        )

        output["ai_away_probability"] = (
            ai_prob[:, 2]
        )

        output["market_home_probability"] = (
            market_prob[:, 0]
        )

        output["market_draw_probability"] = (
            market_prob[:, 1]
        )

        output["market_away_probability"] = (
            market_prob[:, 2]
        )

        output["ai_prediction"] = [
            REVERSE_TARGET[int(x)]
            for x in ai_pred
        ]

        output["market_prediction"] = [
            REVERSE_TARGET[int(x)]
            for x in market_pred
        ]

        output[
            "ai_correct"
        ] = (
            ai_pred
            == y_test
        )

        output[
            "market_correct"
        ] = (
            market_pred
            == y_test
        )

        prediction_frames.append(
            output
        )

        print()
        print(
            test_season,
            f"train={len(train)}",
            f"test={len(test)}",
        )

        print(
            "  AI accuracy:",
            f"{ai_accuracy:.4f}",
        )

        print(
            "  Market accuracy:",
            f"{market_accuracy:.4f}",
        )

        print(
            "  HOME accuracy:",
            f"{home_accuracy:.4f}",
        )

        print(
            "  AI logloss:",
            f"{ai_logloss:.4f}",
        )

        print(
            "  Market logloss:",
            f"{market_logloss:.4f}",
        )

    folds = pd.DataFrame(
        fold_rows
    )

    predictions = pd.concat(
        prediction_frames,
        ignore_index=True,
    )

    y_all = (
        predictions[
            "actual_target"
        ]
        .astype(int)
        .to_numpy()
    )

    ai_all = predictions[
        [
            "ai_home_probability",
            "ai_draw_probability",
            "ai_away_probability",
        ]
    ].to_numpy()

    market_all = predictions[
        [
            "market_home_probability",
            "market_draw_probability",
            "market_away_probability",
        ]
    ].to_numpy()

    ai_pred_all = np.argmax(
        ai_all,
        axis=1,
    )

    market_pred_all = np.argmax(
        market_all,
        axis=1,
    )

    home_pred_all = np.zeros(
        len(predictions),
        dtype=int,
    )

    aggregate = {
        "oos_rows":
            int(len(predictions)),

        "folds":
            int(len(folds)),

        "ai_accuracy":
            float(
                accuracy_score(
                    y_all,
                    ai_pred_all,
                )
            ),

        "market_accuracy":
            float(
                accuracy_score(
                    y_all,
                    market_pred_all,
                )
            ),

        "home_accuracy":
            float(
                accuracy_score(
                    y_all,
                    home_pred_all,
                )
            ),

        "ai_logloss":
            float(
                log_loss(
                    y_all,
                    ai_all,
                    labels=[0, 1, 2],
                )
            ),

        "market_logloss":
            float(
                log_loss(
                    y_all,
                    market_all,
                    labels=[0, 1, 2],
                )
            ),

        "ai_brier":
            multiclass_brier(
                y_all,
                ai_all,
            ),

        "market_brier":
            multiclass_brier(
                y_all,
                market_all,
            ),
    }

    aggregate[
        "ai_minus_market_accuracy"
    ] = (
        aggregate["ai_accuracy"]
        - aggregate[
            "market_accuracy"
        ]
    )

    aggregate[
        "ai_minus_market_logloss"
    ] = (
        aggregate["ai_logloss"]
        - aggregate[
            "market_logloss"
        ]
    )

    aggregate[
        "ai_beats_market_accuracy"
    ] = (
        aggregate["ai_accuracy"]
        > aggregate[
            "market_accuracy"
        ]
    )

    aggregate[
        "ai_beats_market_logloss"
    ] = (
        aggregate["ai_logloss"]
        < aggregate[
            "market_logloss"
        ]
    )

    PREDICTIONS_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    predictions.to_csv(
        PREDICTIONS_OUTPUT,
        index=False,
    )

    folds.to_csv(
        FOLD_OUTPUT,
        index=False,
    )

    METRICS_OUTPUT.write_text(
        json.dumps(
            aggregate,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("AGGREGATE OOS RESULT")
    print("=" * 72)

    for key, value in (
        aggregate.items()
    ):
        print(
            f"{key:32}",
            value,
        )

    print()
    print(
        "predictions:",
        PREDICTIONS_OUTPUT,
    )

    print(
        "folds:",
        FOLD_OUTPUT,
    )

    print(
        "metrics:",
        METRICS_OUTPUT,
    )

    print()
    print(
        "NOTE: no model artifact was saved."
    )


if __name__ == "__main__":
    main()
