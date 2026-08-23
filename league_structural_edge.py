"""Walk-forward Structural Edge Layer V1.

Research-only.

Uses independent football structure:
- Elo strength
- recent form
- venue strength
- recent scoring / conceding

Does NOT use bookmaker odds as structural features.

For every evaluated season:
- scaler/statistics are learned only from earlier OOS data;
- structural rule is frozen before the test season;
- market remains the baseline;
- no model artifact is saved;
- no production promotion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import league_model_diagnostics as diag
import league_model_sweep as sweep


ROOT = Path(__file__).resolve().parent

OUTPUT_DIR = (
    ROOT
    / "experiments"
    / "league_structural_edge"
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

WALKFORWARD_TEST_SEASONS = (
    "2021-2022",
    "2022-2023",
    "2023-2024",
    "2024-2025",
    "2025-2026",
)

STRUCTURAL_FEATURES = (
    "elo_difference",
    "form_difference",
    "venue_win_rate_difference",
    "home_goals_scored_last5",
    "away_goals_scored_last5",
    "home_goals_conceded_last5",
    "away_goals_conceded_last5",
    "home_venue_goals_scored",
    "away_venue_goals_scored",
    "home_venue_goals_conceded",
    "away_venue_goals_conceded",
)

# Fixed in advance.
STRUCTURAL_ALPHA = 0.10
EDGE_THRESHOLD = 0.75


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def production_state() -> dict:
    return {
        name: sha256(ROOT / name)
        for name in PRODUCTION_ARTIFACTS
    }


def metrics(
    y: np.ndarray,
    probability: np.ndarray,
) -> dict:
    from sklearn.metrics import (
        accuracy_score,
        log_loss,
    )

    prediction = np.argmax(
        probability,
        axis=1,
    )

    one_hot = np.eye(3)[y]

    brier = float(
        np.mean(
            np.sum(
                (
                    probability
                    - one_hot
                ) ** 2,
                axis=1,
            )
        )
    )

    return {
        "accuracy": float(
            accuracy_score(
                y,
                prediction,
            )
        ),
        "logloss": float(
            log_loss(
                y,
                probability,
                labels=[0, 1, 2],
            )
        ),
        "brier": brier,
    }


def fit_scaler(
    frame: pd.DataFrame,
) -> dict:
    stats = {}

    for feature in STRUCTURAL_FEATURES:
        values = pd.to_numeric(
            frame[feature],
            errors="coerce",
        )

        mean = float(
            values.mean()
        )

        std = float(
            values.std(ddof=0)
        )

        if (
            not np.isfinite(std)
            or std == 0
        ):
            std = 1.0

        stats[feature] = {
            "mean": mean,
            "std": std,
        }

    return stats


def zscore(
    frame: pd.DataFrame,
    feature: str,
    stats: dict,
) -> pd.Series:
    values = pd.to_numeric(
        frame[feature],
        errors="coerce",
    )

    return (
        values
        - stats[feature]["mean"]
    ) / stats[feature]["std"]


def structural_score(
    frame: pd.DataFrame,
    stats: dict,
) -> pd.Series:
    # Strength.
    strength = zscore(
        frame,
        "elo_difference",
        stats,
    )

    # Form.
    form = zscore(
        frame,
        "form_difference",
        stats,
    )

    # Venue quality.
    venue = zscore(
        frame,
        "venue_win_rate_difference",
        stats,
    )

    # Attack differential.
    attack_raw = (
        pd.to_numeric(
            frame[
                "home_goals_scored_last5"
            ],
            errors="coerce",
        )
        - pd.to_numeric(
            frame[
                "away_goals_scored_last5"
            ],
            errors="coerce",
        )
    )

    attack_mean = float(
        attack_raw.mean()
    )

    attack_std = float(
        attack_raw.std(ddof=0)
    )

    if (
        not np.isfinite(attack_std)
        or attack_std == 0
    ):
        attack_std = 1.0

    attack = (
        attack_raw
        - attack_mean
    ) / attack_std

    # Defensive advantage:
    # lower home conceded and higher away conceded
    # support the home side.
    defence_raw = (
        pd.to_numeric(
            frame[
                "away_goals_conceded_last5"
            ],
            errors="coerce",
        )
        - pd.to_numeric(
            frame[
                "home_goals_conceded_last5"
            ],
            errors="coerce",
        )
    )

    defence_mean = float(
        defence_raw.mean()
    )

    defence_std = float(
        defence_raw.std(ddof=0)
    )

    if (
        not np.isfinite(defence_std)
        or defence_std == 0
    ):
        defence_std = 1.0

    defence = (
        defence_raw
        - defence_mean
    ) / defence_std

    # Fixed equal-weight V1.
    return (
        strength
        + form
        + venue
        + attack
        + defence
    ) / 5.0


def apply_structural_correction(
    market: np.ndarray,
    score: np.ndarray,
) -> tuple[
    np.ndarray,
    np.ndarray,
]:
    result = market.copy()

    enabled = (
        np.abs(score)
        >= EDGE_THRESHOLD
    )

    for i in range(
        len(result)
    ):
        if not enabled[i]:
            continue

        correction = (
            STRUCTURAL_ALPHA
            * min(
                abs(
                    float(score[i])
                ),
                2.0,
            )
            / 2.0
        )

        if score[i] > 0:
            # Structural edge toward HOME.
            transfer = correction * (
                result[i, 1]
                + result[i, 2]
            )

            if (
                result[i, 1]
                + result[i, 2]
            ) > 0:
                draw_share = (
                    result[i, 1]
                    / (
                        result[i, 1]
                        + result[i, 2]
                    )
                )
            else:
                draw_share = 0.5

            result[i, 0] += transfer

            result[i, 1] -= (
                transfer
                * draw_share
            )

            result[i, 2] -= (
                transfer
                * (
                    1.0
                    - draw_share
                )
            )

        else:
            # Structural edge away from HOME:
            # reduce home probability and distribute
            # toward draw / away in their market ratio.
            transfer = (
                correction
                * result[i, 0]
            )

            denominator = (
                result[i, 1]
                + result[i, 2]
            )

            if denominator > 0:
                draw_share = (
                    result[i, 1]
                    / denominator
                )
            else:
                draw_share = 0.5

            result[i, 0] -= transfer

            result[i, 1] += (
                transfer
                * draw_share
            )

            result[i, 2] += (
                transfer
                * (
                    1.0
                    - draw_share
                )
            )

    result = np.clip(
        result,
        1e-9,
        None,
    )

    result = (
        result
        / result.sum(
            axis=1,
            keepdims=True,
        )
    )

    return result, enabled


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--league",
        choices=sorted(
            sweep.INPUTS
        ),
        required=True,
    )

    args = parser.parse_args()

    league = args.league

    before = production_state()

    feature_set, model_name = (
        diag.load_sweep_winner(
            league
        )
    )

    source = pd.read_csv(
        sweep.INPUTS[league]
    )

    source = source.copy()

    source["target"] = (
        source["result"]
        .map(
            sweep.TARGET_MAP
        )
    )

    seasons = (
        sweep.SELECTION_TEST_SEASONS
        + (
            sweep.FINAL_HOLDOUT_SEASON,
        )
    )

    predictions = (
        diag.generate_oos_predictions(
            source,
            feature_set_name=feature_set,
            model_name=model_name,
            seasons=seasons,
        )
    )

    key = [
        "season",
        "match_date",
        "home_team",
        "away_team",
    ]

    feature_frame = source[
        key
        + list(
            STRUCTURAL_FEATURES
        )
    ].copy()

    predictions = predictions.merge(
        feature_frame,
        on=key,
        how="left",
        validate="one_to_one",
    )

    print("=" * 72)
    print("STRUCTURAL EDGE WALK-FORWARD")
    print("=" * 72)

    print(
        "league:",
        league,
    )

    print(
        "AI winner:",
        feature_set,
        "+",
        model_name,
    )

    print(
        "structural alpha:",
        STRUCTURAL_ALPHA,
    )

    print(
        "edge threshold:",
        EDGE_THRESHOLD,
    )

    fold_rows = []
    usage_rows = []

    for test_season in (
        WALKFORWARD_TEST_SEASONS
    ):
        train = (
            predictions[
                predictions["season"]
                .astype(str)
                < test_season
            ]
            .copy()
        )

        test = (
            predictions[
                predictions["season"]
                .astype(str)
                == test_season
            ]
            .copy()
        )

        if train.empty or test.empty:
            continue

        stats = fit_scaler(
            train
        )

        train_score = structural_score(
            train,
            stats,
        )

        # The V1 score itself is fixed.
        # Training scores are computed only
        # for diagnostics and distribution checks.
        test_score = structural_score(
            test,
            stats,
        )

        market = test[
            [
                "market_home_probability",
                "market_draw_probability",
                "market_away_probability",
            ]
        ].to_numpy()

        ai = test[
            [
                "ai_home_probability",
                "ai_draw_probability",
                "ai_away_probability",
            ]
        ].to_numpy()

        y = (
            test["target"]
            .astype(int)
            .to_numpy()
        )

        structural_prob, enabled = (
            apply_structural_correction(
                market,
                test_score.to_numpy(),
            )
        )

        market_metric = metrics(
            y,
            market,
        )

        ai_metric = metrics(
            y,
            ai,
        )

        structural_metric = metrics(
            y,
            structural_prob,
        )

        enabled_rows = int(
            enabled.sum()
        )

        enabled_rate = (
            enabled_rows
            / len(test)
        )

        fold_rows.append({
            "test_season":
                test_season,

            "training_rows":
                len(train),

            "test_rows":
                len(test),

            "enabled_rows":
                enabled_rows,

            "enabled_rate":
                enabled_rate,

            "train_score_mean":
                float(
                    train_score.mean()
                ),

            "test_score_mean":
                float(
                    test_score.mean()
                ),

            "market_accuracy":
                market_metric[
                    "accuracy"
                ],

            "structural_accuracy":
                structural_metric[
                    "accuracy"
                ],

            "ai_accuracy":
                ai_metric[
                    "accuracy"
                ],

            "market_logloss":
                market_metric[
                    "logloss"
                ],

            "structural_logloss":
                structural_metric[
                    "logloss"
                ],

            "market_brier":
                market_metric[
                    "brier"
                ],

            "structural_brier":
                structural_metric[
                    "brier"
                ],

            "accuracy_gap":
                structural_metric[
                    "accuracy"
                ]
                - market_metric[
                    "accuracy"
                ],

            "logloss_gap":
                structural_metric[
                    "logloss"
                ]
                - market_metric[
                    "logloss"
                ],

            "brier_gap":
                structural_metric[
                    "brier"
                ]
                - market_metric[
                    "brier"
                ],
        })

        usage = test[
            key
        ].copy()

        usage[
            "structural_score"
        ] = (
            test_score.to_numpy()
        )

        usage[
            "correction_enabled"
        ] = enabled

        usage[
            "test_season"
        ] = test_season

        usage_rows.append(
            usage
        )

        print()
        print(test_season)

        print(
            " enabled:",
            enabled_rows,
            f"({enabled_rate:.1%})",
        )

        print(
            " market:",
            market_metric,
        )

        print(
            " structural:",
            structural_metric,
        )

    folds = pd.DataFrame(
        fold_rows
    )

    usage = pd.concat(
        usage_rows,
        ignore_index=True,
    )

    probability_wins = (
        (
            folds[
                "logloss_gap"
            ] < 0
        )
        &
        (
            folds[
                "brier_gap"
            ] < 0
        )
    )

    full_wins = (
        probability_wins
        &
        (
            folds[
                "accuracy_gap"
            ] > 0
        )
    )

    report = {
        "league":
            league,

        "structural_features":
            list(
                STRUCTURAL_FEATURES
            ),

        "structural_alpha":
            STRUCTURAL_ALPHA,

        "edge_threshold":
            EDGE_THRESHOLD,

        "fold_count":
            len(folds),

        "probability_win_rate":
            float(
                probability_wins.mean()
            ),

        "full_win_rate":
            float(
                full_wins.mean()
            ),

        "average_accuracy_gap_vs_market":
            float(
                folds[
                    "accuracy_gap"
                ].mean()
            ),

        "average_logloss_gap_vs_market":
            float(
                folds[
                    "logloss_gap"
                ].mean()
            ),

        "average_brier_gap_vs_market":
            float(
                folds[
                    "brier_gap"
                ].mean()
            ),

        "worst_logloss_gap_vs_market":
            float(
                folds[
                    "logloss_gap"
                ].max()
            ),

        "best_logloss_gap_vs_market":
            float(
                folds[
                    "logloss_gap"
                ].min()
            ),

        "average_correction_rate":
            float(
                folds[
                    "enabled_rate"
                ].mean()
            ),

        "next_true_unseen_period":
            "2026-2027",

        "promotion_gate":
            "NOT_EVALUATED",
    }

    after = production_state()

    production_unchanged = (
        before == after
    )

    report[
        "production_unchanged"
    ] = production_unchanged

    report[
        "candidate_model_saved"
    ] = False

    report[
        "promotion_performed"
    ] = False

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    folds_path = (
        OUTPUT_DIR
        / f"{league.lower()}_folds.csv"
    )

    usage_path = (
        OUTPUT_DIR
        / f"{league.lower()}_usage.csv"
    )

    report_path = (
        OUTPUT_DIR
        / f"{league.lower()}_report.json"
    )

    folds.to_csv(
        folds_path,
        index=False,
    )

    usage.to_csv(
        usage_path,
        index=False,
    )

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
    print("STRUCTURAL EDGE SUMMARY")
    print("=" * 72)

    print(
        folds.to_string(
            index=False
        )
    )

    print()

    for key_name, value in (
        report.items()
    ):
        if (
            key_name
            in {
                "structural_features",
            }
        ):
            continue

        print(
            f"{key_name:35}",
            value,
        )

    print()
    print(
        "folds:",
        folds_path,
    )

    print(
        "usage:",
        usage_path,
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

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
