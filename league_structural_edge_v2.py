"""Argmax-preserving Structural Edge V2.

Research-only.

Improvements over V1:
- every normalization statistic is fitted on prior data only;
- no test-distribution normalization;
- structural correction cannot change market argmax;
- market therefore keeps the same 1X2 decision;
- evaluation focuses on probability quality (LogLoss/Brier);
- no model artifact or production promotion.
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
    / "league_structural_edge_v2"
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

BASE_FEATURES = (
    "elo_difference",
    "form_difference",
    "venue_win_rate_difference",
)

DERIVED_COMPONENTS = (
    "attack_difference",
    "defence_difference",
)

STRUCTURAL_ALPHA = 0.10
EDGE_THRESHOLD = 0.75

# Small safety margin so corrected probabilities cannot tie
# or cross the original market winner.
ARGMAX_MARGIN = 1e-8


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


def add_components(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    result = frame.copy()

    result["attack_difference"] = (
        pd.to_numeric(
            result["home_goals_scored_last5"],
            errors="coerce",
        )
        - pd.to_numeric(
            result["away_goals_scored_last5"],
            errors="coerce",
        )
    )

    # Positive means defensive profile favors home.
    result["defence_difference"] = (
        pd.to_numeric(
            result["away_goals_conceded_last5"],
            errors="coerce",
        )
        - pd.to_numeric(
            result["home_goals_conceded_last5"],
            errors="coerce",
        )
    )

    return result


def fit_stats(
    training: pd.DataFrame,
) -> dict:
    training = add_components(
        training
    )

    features = (
        BASE_FEATURES
        + DERIVED_COMPONENTS
    )

    stats = {}

    for feature in features:
        values = pd.to_numeric(
            training[feature],
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


def standardized(
    values: pd.Series,
    stats: dict,
    feature: str,
) -> pd.Series:
    numeric = pd.to_numeric(
        values,
        errors="coerce",
    )

    return (
        numeric
        - stats[feature]["mean"]
    ) / stats[feature]["std"]


def structural_score(
    frame: pd.DataFrame,
    stats: dict,
) -> pd.Series:
    work = add_components(
        frame
    )

    components = []

    for feature in (
        BASE_FEATURES
        + DERIVED_COMPONENTS
    ):
        components.append(
            standardized(
                work[feature],
                stats,
                feature,
            )
        )

    score = sum(
        components
    ) / len(components)

    return score


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
        "brier": float(
            np.mean(
                np.sum(
                    (
                        probability
                        - one_hot
                    ) ** 2,
                    axis=1,
                )
            )
        ),
    }


def raw_structural_correction(
    market_row: np.ndarray,
    score: float,
    *,
    structural_alpha: float | None = None,
) -> np.ndarray:
    result = (
        market_row
        .astype(float)
        .copy()
    )

    alpha = (
        STRUCTURAL_ALPHA
        if structural_alpha is None
        else float(structural_alpha)
    )

    if not (
        0.0
        <= alpha
        <= 1.0
    ):
        raise ValueError(
            "structural_alpha must be in [0, 1]"
        )

    correction = (
        alpha
        * min(
            abs(float(score)),
            2.0,
        )
        / 2.0
    )

    if score > 0:
        # Structural profile supports HOME.
        pool = (
            result[1]
            + result[2]
        )

        if pool <= 0:
            return result

        transfer = (
            correction
            * pool
        )

        draw_share = (
            result[1]
            / pool
        )

        result[0] += transfer
        result[1] -= (
            transfer
            * draw_share
        )
        result[2] -= (
            transfer
            * (
                1.0
                - draw_share
            )
        )

    else:
        # Structural profile weakens HOME.
        transfer = (
            correction
            * result[0]
        )

        pool = (
            result[1]
            + result[2]
        )

        if pool <= 0:
            draw_share = 0.5
        else:
            draw_share = (
                result[1]
                / pool
            )

        result[0] -= transfer
        result[1] += (
            transfer
            * draw_share
        )
        result[2] += (
            transfer
            * (
                1.0
                - draw_share
            )
        )

    result = np.clip(
        result,
        1e-12,
        None,
    )

    return (
        result
        / result.sum()
    )


def preserve_market_argmax(
    market_row: np.ndarray,
    candidate_row: np.ndarray,
) -> tuple[
    np.ndarray,
    float,
]:
    """Shrink correction until original market argmax is preserved."""

    market_winner = int(
        np.argmax(
            market_row
        )
    )

    candidate_winner = int(
        np.argmax(
            candidate_row
        )
    )

    if (
        candidate_winner
        == market_winner
    ):
        return (
            candidate_row,
            1.0,
        )

    # Binary search largest safe interpolation between
    # market and candidate correction.
    low = 0.0
    high = 1.0

    best = market_row.copy()

    for _ in range(60):
        weight = (
            low + high
        ) / 2.0

        trial = (
            market_row
            + weight
            * (
                candidate_row
                - market_row
            )
        )

        trial = np.clip(
            trial,
            1e-12,
            None,
        )

        trial = (
            trial
            / trial.sum()
        )

        winner = int(
            np.argmax(
                trial
            )
        )

        if winner == market_winner:
            # Also ensure original winner is strictly above
            # every competitor.
            winner_probability = (
                trial[
                    market_winner
                ]
            )

            competitor = np.max(
                np.delete(
                    trial,
                    market_winner,
                )
            )

            if (
                winner_probability
                > competitor
                + ARGMAX_MARGIN
            ):
                best = trial
                low = weight
                continue

        high = weight

    return (
        best,
        low,
    )


def apply_correction(
    market: np.ndarray,
    score: np.ndarray,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    output = market.copy()

    enabled = (
        np.abs(score)
        >= EDGE_THRESHOLD
    )

    realized_weights = np.zeros(
        len(market),
        dtype=float,
    )

    for i in range(
        len(market)
    ):
        if not enabled[i]:
            continue

        candidate = (
            raw_structural_correction(
                market[i],
                float(score[i]),
            )
        )

        safe, weight = (
            preserve_market_argmax(
                market[i],
                candidate,
            )
        )

        output[i] = safe
        realized_weights[i] = weight

    output = np.clip(
        output,
        1e-12,
        None,
    )

    output = (
        output
        / output.sum(
            axis=1,
            keepdims=True,
        )
    )

    return (
        output,
        enabled,
        realized_weights,
    )


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

    required_features = [
        "elo_difference",
        "form_difference",
        "venue_win_rate_difference",
        "home_goals_scored_last5",
        "away_goals_scored_last5",
        "home_goals_conceded_last5",
        "away_goals_conceded_last5",
    ]

    key = [
        "season",
        "match_date",
        "home_team",
        "away_team",
    ]

    feature_frame = source[
        key
        + required_features
    ].copy()

    predictions = predictions.merge(
        feature_frame,
        on=key,
        how="left",
        validate="one_to_one",
    )

    print("=" * 72)
    print("ARGMAX-PRESERVING STRUCTURAL EDGE V2")
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

        if (
            train.empty
            or test.empty
        ):
            continue

        stats = fit_stats(
            train
        )

        test_score = (
            structural_score(
                test,
                stats,
            )
        )

        market = test[
            [
                "market_home_probability",
                "market_draw_probability",
                "market_away_probability",
            ]
        ].to_numpy()

        y = (
            test["target"]
            .astype(int)
            .to_numpy()
        )

        corrected, enabled, weights = (
            apply_correction(
                market,
                test_score.to_numpy(),
            )
        )

        market_argmax = np.argmax(
            market,
            axis=1,
        )

        corrected_argmax = np.argmax(
            corrected,
            axis=1,
        )

        argmax_changes = int(
            np.sum(
                market_argmax
                != corrected_argmax
            )
        )

        if argmax_changes != 0:
            raise RuntimeError(
                "Argmax preservation failed: "
                f"{argmax_changes} changed rows"
            )

        market_metric = metrics(
            y,
            market,
        )

        corrected_metric = metrics(
            y,
            corrected,
        )

        enabled_rows = int(
            enabled.sum()
        )

        clipped_rows = int(
            np.sum(
                enabled
                & (
                    weights
                    < 0.999999
                )
            )
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
                (
                    enabled_rows
                    / len(test)
                ),

            "argmax_changes":
                argmax_changes,

            "argmax_clipped_rows":
                clipped_rows,

            "market_accuracy":
                market_metric[
                    "accuracy"
                ],

            "v2_accuracy":
                corrected_metric[
                    "accuracy"
                ],

            "market_logloss":
                market_metric[
                    "logloss"
                ],

            "v2_logloss":
                corrected_metric[
                    "logloss"
                ],

            "market_brier":
                market_metric[
                    "brier"
                ],

            "v2_brier":
                corrected_metric[
                    "brier"
                ],

            "accuracy_gap":
                corrected_metric[
                    "accuracy"
                ]
                - market_metric[
                    "accuracy"
                ],

            "logloss_gap":
                corrected_metric[
                    "logloss"
                ]
                - market_metric[
                    "logloss"
                ],

            "brier_gap":
                corrected_metric[
                    "brier"
                ]
                - market_metric[
                    "brier"
                ],

            "mean_realized_weight":
                float(
                    weights[
                        enabled
                    ].mean()
                )
                if enabled_rows
                else 0.0,
        })

        usage = test[
            key
        ].copy()

        usage[
            "structural_score"
        ] = test_score.to_numpy()

        usage[
            "correction_enabled"
        ] = enabled

        usage[
            "realized_correction_weight"
        ] = weights

        usage[
            "market_argmax"
        ] = market_argmax

        usage[
            "v2_argmax"
        ] = corrected_argmax

        usage_rows.append(
            usage
        )

        print()
        print(test_season)

        print(
            " enabled:",
            enabled_rows,
        )

        print(
            " clipped:",
            clipped_rows,
        )

        print(
            " argmax changes:",
            argmax_changes,
        )

        print(
            " market:",
            market_metric,
        )

        print(
            " V2:",
            corrected_metric,
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

    accuracy_preserved = (
        folds[
            "accuracy_gap"
        ].abs()
        < 1e-12
    )

    report = {
        "league":
            league,

        "version":
            "STRUCTURAL_EDGE_V2",

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

        "accuracy_preservation_rate":
            float(
                accuracy_preserved.mean()
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

        "total_argmax_changes":
            int(
                folds[
                    "argmax_changes"
                ].sum()
            ),

        "average_correction_rate":
            float(
                folds[
                    "enabled_rate"
                ].mean()
            ),

        "average_realized_weight":
            float(
                folds[
                    "mean_realized_weight"
                ].mean()
            ),

        "promotion_gate":
            "NOT_EVALUATED",

        "next_true_unseen_period":
            "2026-2027",
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
    print("STRUCTURAL EDGE V2 SUMMARY")
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

    if (
        report[
            "total_argmax_changes"
        ]
        != 0
    ):
        print(
            "FAIL: argmax preservation violated"
        )
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
