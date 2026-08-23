"""Automated model/feature sweep for league research.

Current implementation: LA_LIGA.

Design:
- selection seasons: 2020-2021 .. 2024-2025
- final holdout: 2025-2026
- winner selected WITHOUT using final holdout
- final holdout evaluated only for selected winner
- bookmaker odds are benchmark-only
- no .pkl artifact is saved
- no production promotion
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    log_loss,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from xgboost import XGBClassifier


ROOT = Path(__file__).resolve().parent

INPUTS = {
    "LA_LIGA": (
        ROOT
        / "data"
        / "la_liga_features_with_elo_trainable.csv"
    ),
}

OUTPUT_DIR = (
    ROOT
    / "experiments"
    / "league_model_sweep"
)

PRODUCTION_ARTIFACTS = (
    "football_model_xgboost_elo.pkl",
    "football_model_no_odds.pkl",
    "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)

TARGET_MAP = {
    "H": 0,
    "D": 1,
    "A": 2,
}

SELECTION_TEST_SEASONS = (
    "2020-2021",
    "2021-2022",
    "2022-2023",
    "2023-2024",
    "2024-2025",
)

FINAL_HOLDOUT_SEASON = (
    "2025-2026"
)


CORE_FEATURES = [
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
]


ELO_FEATURES = [
    "home_elo",
    "away_elo",
    "elo_difference",
]


VENUE_FEATURES = [
    "home_venue_win_rate",
    "away_venue_win_rate",

    "home_venue_goals_scored",
    "home_venue_goals_conceded",
    "away_venue_goals_scored",
    "away_venue_goals_conceded",

    "venue_win_rate_difference",
]


DISCIPLINE_FEATURES = [
    "home_corners_last5",
    "away_corners_last5",

    "home_yellow_last5",
    "away_yellow_last5",
]


FEATURE_SETS = {
    "core":
        CORE_FEATURES,

    "core_elo":
        CORE_FEATURES
        + ELO_FEATURES,

    "full_no_odds":
        CORE_FEATURES
        + ELO_FEATURES
        + VENUE_FEATURES
        + DISCIPLINE_FEATURES,
}


MODEL_VARIANTS = {
    "logistic_l2": {
        "kind": "logistic",
        "params": {
            "C": 0.5,
        },
    },

    "xgb_shallow": {
        "kind": "xgb",
        "params": {
            "n_estimators": 250,
            "max_depth": 2,
            "learning_rate": 0.03,
            "min_child_weight": 2,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "reg_lambda": 2.0,
            "reg_alpha": 0.0,
        },
    },

    "xgb_base": {
        "kind": "xgb",
        "params": {
            "n_estimators": 300,
            "max_depth": 3,
            "learning_rate": 0.02,
            "min_child_weight": 1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_lambda": 1.0,
            "reg_alpha": 0.0,
        },
    },

    "xgb_regularized": {
        "kind": "xgb",
        "params": {
            "n_estimators": 400,
            "max_depth": 3,
            "learning_rate": 0.015,
            "min_child_weight": 3,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_lambda": 3.0,
            "reg_alpha": 0.1,
        },
    },
}


def sha256(
    path: Path,
) -> str | None:
    if not path.exists():
        return None

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def production_state():
    return {
        name: sha256(
            ROOT / name
        )
        for name
        in PRODUCTION_ARTIFACTS
    }


def market_probabilities(
    frame: pd.DataFrame,
) -> np.ndarray:
    odds = frame[
        [
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ].astype(float).to_numpy()

    implied = 1.0 / odds

    return (
        implied
        / implied.sum(
            axis=1,
            keepdims=True,
        )
    )


def brier_score(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> float:
    target = np.eye(3)[
        y_true
    ]

    return float(
        np.mean(
            np.sum(
                (
                    probabilities
                    - target
                ) ** 2,
                axis=1,
            )
        )
    )


def metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> dict:
    predicted = np.argmax(
        probabilities,
        axis=1,
    )

    return {
        "accuracy":
            float(
                accuracy_score(
                    y_true,
                    predicted,
                )
            ),

        "logloss":
            float(
                log_loss(
                    y_true,
                    probabilities,
                    labels=[0, 1, 2],
                )
            ),

        "brier":
            brier_score(
                y_true,
                probabilities,
            ),
    }


def make_model(
    model_name: str,
):
    config = (
        MODEL_VARIANTS[
            model_name
        ]
    )

    if (
        config["kind"]
        == "logistic"
    ):
        return Pipeline([
            (
                "scale",
                StandardScaler(),
            ),
            (
                "model",
                LogisticRegression(
                    C=config[
                        "params"
                    ]["C"],
                    max_iter=2000,
                    random_state=42,
                ),
            ),
        ])

    if (
        config["kind"]
        == "xgb"
    ):
        return XGBClassifier(
            **config["params"],
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=2,
        )

    raise ValueError(
        model_name
    )


def evaluate_selection_variant(
    frame: pd.DataFrame,
    *,
    feature_set_name: str,
    model_name: str,
) -> dict:
    features = (
        FEATURE_SETS[
            feature_set_name
        ]
    )

    probabilities = []
    actual = []

    fold_rows = []

    for season in (
        SELECTION_TEST_SEASONS
    ):
        train = frame[
            frame["season"]
            .astype(str)
            < season
        ].copy()

        test = frame[
            frame["season"]
            .astype(str)
            == season
        ].copy()

        required = (
            features
            + [
                "target",
                "home_odds",
                "draw_odds",
                "away_odds",
            ]
        )

        train = train.dropna(
            subset=required
        )

        test = test.dropna(
            subset=required
        )

        model = make_model(
            model_name
        )

        model.fit(
            train[features],
            train[
                "target"
            ].astype(int),
        )

        probability = (
            model.predict_proba(
                test[features]
            )
        )

        y = (
            test["target"]
            .astype(int)
            .to_numpy()
        )

        fold_metric = metrics(
            y,
            probability,
        )

        fold_rows.append({
            "season":
                season,

            "train_rows":
                len(train),

            "test_rows":
                len(test),

            **fold_metric,
        })

        probabilities.append(
            probability
        )

        actual.append(
            y
        )

    probability_all = np.vstack(
        probabilities
    )

    actual_all = np.concatenate(
        actual
    )

    aggregate = metrics(
        actual_all,
        probability_all,
    )

    return {
        **aggregate,

        "selection_rows":
            int(
                len(
                    actual_all
                )
            ),

        "folds":
            fold_rows,
    }


def selection_market_metrics(
    frame: pd.DataFrame,
) -> dict:
    selected = frame[
        frame[
            "season"
        ]
        .astype(str)
        .isin(
            SELECTION_TEST_SEASONS
        )
    ].dropna(
        subset=[
            "target",
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    )

    probabilities = (
        market_probabilities(
            selected
        )
    )

    y = (
        selected["target"]
        .astype(int)
        .to_numpy()
    )

    return metrics(
        y,
        probabilities,
    )


def evaluate_final_holdout(
    frame: pd.DataFrame,
    *,
    feature_set_name: str,
    model_name: str,
) -> dict:
    features = (
        FEATURE_SETS[
            feature_set_name
        ]
    )

    train = frame[
        frame["season"]
        .astype(str)
        < FINAL_HOLDOUT_SEASON
    ].copy()

    test = frame[
        frame["season"]
        .astype(str)
        == FINAL_HOLDOUT_SEASON
    ].copy()

    required = (
        features
        + [
            "target",
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    )

    train = train.dropna(
        subset=required
    )

    test = test.dropna(
        subset=required
    )

    model = make_model(
        model_name
    )

    model.fit(
        train[features],
        train[
            "target"
        ].astype(int),
    )

    ai_probability = (
        model.predict_proba(
            test[features]
        )
    )

    market_probability = (
        market_probabilities(
            test
        )
    )

    y = (
        test["target"]
        .astype(int)
        .to_numpy()
    )

    ai = metrics(
        y,
        ai_probability,
    )

    market = metrics(
        y,
        market_probability,
    )

    return {
        "season":
            FINAL_HOLDOUT_SEASON,

        "train_rows":
            len(train),

        "test_rows":
            len(test),

        "ai":
            ai,

        "market":
            market,

        "ai_beats_market_accuracy":
            ai["accuracy"]
            > market["accuracy"],

        "ai_beats_market_logloss":
            ai["logloss"]
            < market["logloss"],

        "ai_beats_market_brier":
            ai["brier"]
            < market["brier"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--league",
        choices=sorted(
            INPUTS
        ),
        required=True,
    )

    args = parser.parse_args()

    league = args.league

    before = production_state()

    frame = pd.read_csv(
        INPUTS[league]
    )

    frame = frame.copy()

    frame["target"] = (
        frame["result"]
        .map(TARGET_MAP)
    )

    print("=" * 72)
    print("LEAGUE MODEL SWEEP")
    print("=" * 72)

    print(
        "league:",
        league,
    )

    print(
        "rows:",
        len(frame),
    )

    print(
        "feature sets:",
        len(FEATURE_SETS),
    )

    print(
        "model variants:",
        len(MODEL_VARIANTS),
    )

    print(
        "total variants:",
        (
            len(FEATURE_SETS)
            * len(MODEL_VARIANTS)
        ),
    )

    print(
        "selection seasons:",
        SELECTION_TEST_SEASONS,
    )

    print(
        "locked final holdout:",
        FINAL_HOLDOUT_SEASON,
    )

    market = (
        selection_market_metrics(
            frame
        )
    )

    print()
    print("SELECTION MARKET:")

    print(
        market
    )

    leaderboard_rows = []

    detailed = {}

    variant_number = 0

    total_variants = (
        len(FEATURE_SETS)
        * len(MODEL_VARIANTS)
    )

    for feature_set_name in (
        FEATURE_SETS
    ):
        for model_name in (
            MODEL_VARIANTS
        ):
            variant_number += 1

            print()
            print(
                f"[{variant_number}/{total_variants}]",
                feature_set_name,
                "+",
                model_name,
            )

            result = (
                evaluate_selection_variant(
                    frame,
                    feature_set_name=(
                        feature_set_name
                    ),
                    model_name=(
                        model_name
                    ),
                )
            )

            beats_accuracy = (
                result["accuracy"]
                > market["accuracy"]
            )

            beats_logloss = (
                result["logloss"]
                < market["logloss"]
            )

            beats_brier = (
                result["brier"]
                < market["brier"]
            )

            gate = all([
                beats_accuracy,
                beats_logloss,
                beats_brier,
            ])

            leaderboard_rows.append({
                "feature_set":
                    feature_set_name,

                "model":
                    model_name,

                "selection_rows":
                    result[
                        "selection_rows"
                    ],

                "accuracy":
                    result["accuracy"],

                "logloss":
                    result["logloss"],

                "brier":
                    result["brier"],

                "market_accuracy":
                    market["accuracy"],

                "market_logloss":
                    market["logloss"],

                "market_brier":
                    market["brier"],

                "accuracy_gap":
                    result["accuracy"]
                    - market[
                        "accuracy"
                    ],

                "logloss_gap":
                    result["logloss"]
                    - market[
                        "logloss"
                    ],

                "brier_gap":
                    result["brier"]
                    - market[
                        "brier"
                    ],

                "beats_market_accuracy":
                    beats_accuracy,

                "beats_market_logloss":
                    beats_logloss,

                "beats_market_brier":
                    beats_brier,

                "selection_gate":
                    gate,
            })

            detailed[
                (
                    feature_set_name
                    + "__"
                    + model_name
                )
            ] = result

            print(
                " accuracy:",
                f'{result["accuracy"]:.4f}',
                "market:",
                f'{market["accuracy"]:.4f}',
            )

            print(
                " logloss:",
                f'{result["logloss"]:.4f}',
                "market:",
                f'{market["logloss"]:.4f}',
            )

            print(
                " brier:",
                f'{result["brier"]:.4f}',
                "market:",
                f'{market["brier"]:.4f}',
            )

    leaderboard = pd.DataFrame(
        leaderboard_rows
    )

    # Primary ranking is probabilistic quality.
    # Accuracy only breaks ties afterwards.
    leaderboard = (
        leaderboard
        .sort_values(
            [
                "logloss",
                "brier",
                "accuracy",
            ],
            ascending=[
                True,
                True,
                False,
            ],
        )
        .reset_index(drop=True)
    )

    leaderboard.insert(
        0,
        "rank",
        np.arange(
            1,
            len(leaderboard) + 1,
        ),
    )

    winner = (
        leaderboard.iloc[0]
    )

    winner_feature_set = str(
        winner["feature_set"]
    )

    winner_model = str(
        winner["model"]
    )

    print()
    print("=" * 72)
    print("SELECTION LEADERBOARD")
    print("=" * 72)

    print(
        leaderboard[
            [
                "rank",
                "feature_set",
                "model",
                "accuracy",
                "logloss",
                "brier",
                "accuracy_gap",
                "logloss_gap",
                "brier_gap",
                "selection_gate",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print("=" * 72)
    print("SELECTED WINNER")
    print("=" * 72)

    print(
        "feature set:",
        winner_feature_set,
    )

    print(
        "model:",
        winner_model,
    )

    print(
        "IMPORTANT: winner selected "
        "without using final holdout."
    )

    final_holdout = (
        evaluate_final_holdout(
            frame,
            feature_set_name=(
                winner_feature_set
            ),
            model_name=(
                winner_model
            ),
        )
    )

    print()
    print("=" * 72)
    print("FINAL LOCKED HOLDOUT")
    print("=" * 72)

    print(
        "season:",
        final_holdout["season"],
    )

    print(
        "AI:",
        final_holdout["ai"],
    )

    print(
        "Market:",
        final_holdout[
            "market"
        ],
    )

    final_gate = all([
        final_holdout[
            "ai_beats_market_accuracy"
        ],
        final_holdout[
            "ai_beats_market_logloss"
        ],
        final_holdout[
            "ai_beats_market_brier"
        ],
    ])

    selection_gate = bool(
        winner[
            "selection_gate"
        ]
    )

    overall_gate = (
        selection_gate
        and final_gate
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    leaderboard_path = (
        OUTPUT_DIR
        / f"{league.lower()}_leaderboard.csv"
    )

    report_path = (
        OUTPUT_DIR
        / f"{league.lower()}_report.json"
    )

    leaderboard.to_csv(
        leaderboard_path,
        index=False,
    )

    after = production_state()

    production_unchanged = (
        before == after
    )

    report = {
        "league":
            league,

        "variant_count":
            total_variants,

        "selection_seasons":
            list(
                SELECTION_TEST_SEASONS
            ),

        "final_holdout_season":
            FINAL_HOLDOUT_SEASON,

        "selection_market":
            market,

        "winner": {
            "feature_set":
                winner_feature_set,

            "model":
                winner_model,

            "selection_accuracy":
                float(
                    winner[
                        "accuracy"
                    ]
                ),

            "selection_logloss":
                float(
                    winner[
                        "logloss"
                    ]
                ),

            "selection_brier":
                float(
                    winner[
                        "brier"
                    ]
                ),

            "selection_gate":
                selection_gate,
        },

        "final_holdout":
            final_holdout,

        "final_gate":
            final_gate,

        "overall_gate":
            overall_gate,

        "production_unchanged":
            production_unchanged,

        "candidate_model_saved":
            False,

        "promotion_performed":
            False,
    }

    report_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("FINAL SWEEP RESULT")
    print("=" * 72)

    print(
        "selection gate:",
        selection_gate,
    )

    print(
        "final holdout gate:",
        final_gate,
    )

    print(
        "overall gate:",
        overall_gate,
    )

    print(
        "production unchanged:",
        production_unchanged,
    )

    print(
        "candidate model saved:",
        False,
    )

    print(
        "promotion performed:",
        False,
    )

    print(
        "leaderboard:",
        leaderboard_path,
    )

    print(
        "report:",
        report_path,
    )

    if not production_unchanged:
        print(
            "FAIL: production safety violation"
        )

        return 2

    if overall_gate:
        print()
        print(
            "PASS: research winner beats "
            "market on selection and holdout."
        )

        print(
            "NOTE: still no automatic promotion."
        )

    else:
        print()
        print(
            "REJECTED: no promotion-quality "
            "candidate established."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
