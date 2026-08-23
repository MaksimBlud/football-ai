"""Walk-forward residual edge analysis for AI vs market.

Research-only.

Purpose:
- identify stable regimes where AI adds information to market;
- learn regime eligibility only from earlier OOS seasons;
- apply a fixed small AI correction only in eligible regimes;
- otherwise preserve pure market probability;
- do not tune on the evaluated season;
- no .pkl artifact;
- no production promotion.

2025-2026 is retrospective only.
Next truly unseen period remains 2026-2027.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import league_adaptive_hybrid as adaptive
import league_model_diagnostics as diag
import league_model_sweep as sweep


ROOT = Path(__file__).resolve().parent

OUTPUT_DIR = (
    ROOT
    / "experiments"
    / "league_residual_edge"
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

FIXED_ALPHA = 0.10
MIN_TRAIN_ROWS = 75

CONFIDENCE_BINS = (
    0.00,
    0.45,
    0.55,
    0.65,
    1.01,
)

CONFIDENCE_LABELS = (
    "<0.45",
    "0.45-0.55",
    "0.55-0.65",
    ">=0.65",
)

RESIDUAL_BINS = (
    0.00,
    0.03,
    0.07,
    0.15,
    2.00,
)

RESIDUAL_LABELS = (
    "<0.03",
    "0.03-0.07",
    "0.07-0.15",
    ">=0.15",
)


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


def add_residual_segments(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    result = frame.copy()

    ai = result[
        [
            "ai_home_probability",
            "ai_draw_probability",
            "ai_away_probability",
        ]
    ].to_numpy()

    market = result[
        [
            "market_home_probability",
            "market_draw_probability",
            "market_away_probability",
        ]
    ].to_numpy()

    ai_pred = np.argmax(
        ai,
        axis=1,
    )

    market_pred = np.argmax(
        market,
        axis=1,
    )

    result["ai_prediction_code"] = (
        ai_pred
    )

    result["market_prediction_code"] = (
        market_pred
    )

    result["agreement"] = np.where(
        ai_pred == market_pred,
        "AGREE",
        "DISAGREE",
    )

    result["market_confidence"] = (
        market.max(axis=1)
    )

    result["ai_confidence"] = (
        ai.max(axis=1)
    )

    # Maximum absolute probability disagreement.
    result["residual_magnitude"] = (
        np.max(
            np.abs(
                ai - market
            ),
            axis=1,
        )
    )

    result["market_confidence_bucket"] = (
        pd.cut(
            result["market_confidence"],
            bins=CONFIDENCE_BINS,
            labels=CONFIDENCE_LABELS,
            include_lowest=True,
            right=False,
        )
        .astype(str)
    )

    result["residual_bucket"] = (
        pd.cut(
            result["residual_magnitude"],
            bins=RESIDUAL_BINS,
            labels=RESIDUAL_LABELS,
            include_lowest=True,
            right=False,
        )
        .astype(str)
    )

    result["regime"] = (
        result[
            "market_confidence_bucket"
        ]
        .astype(str)
        + "__"
        + result[
            "agreement"
        ].astype(str)
        + "__"
        + result[
            "residual_bucket"
        ].astype(str)
    )

    return result


def probability_arrays(
    frame: pd.DataFrame,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    y = (
        frame["target"]
        .astype(int)
        .to_numpy()
    )

    ai = frame[
        [
            "ai_home_probability",
            "ai_draw_probability",
            "ai_away_probability",
        ]
    ].to_numpy()

    market = frame[
        [
            "market_home_probability",
            "market_draw_probability",
            "market_away_probability",
        ]
    ].to_numpy()

    return y, ai, market


def evaluate_probabilities(
    y: np.ndarray,
    probability: np.ndarray,
) -> dict:
    return adaptive.metrics(
        y,
        probability,
    )


def fixed_hybrid(
    market: np.ndarray,
    ai: np.ndarray,
) -> np.ndarray:
    return diag.hybrid_probability(
        market,
        ai,
        FIXED_ALPHA,
    )


def learn_regime_table(
    training: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    for regime, group in (
        training.groupby(
            "regime",
            sort=True,
        )
    ):
        y, ai, market = (
            probability_arrays(
                group
            )
        )

        hybrid = fixed_hybrid(
            market,
            ai,
        )

        market_metric = (
            evaluate_probabilities(
                y,
                market,
            )
        )

        hybrid_metric = (
            evaluate_probabilities(
                y,
                hybrid,
            )
        )

        logloss_gain = (
            hybrid_metric["logloss"]
            < market_metric["logloss"]
        )

        brier_gain = (
            hybrid_metric["brier"]
            < market_metric["brier"]
        )

        eligible = (
            len(group)
            >= MIN_TRAIN_ROWS
            and logloss_gain
            and brier_gain
        )

        rows.append({
            "regime":
                str(regime),

            "rows":
                len(group),

            "market_accuracy":
                market_metric[
                    "accuracy"
                ],

            "hybrid_accuracy":
                hybrid_metric[
                    "accuracy"
                ],

            "market_logloss":
                market_metric[
                    "logloss"
                ],

            "hybrid_logloss":
                hybrid_metric[
                    "logloss"
                ],

            "market_brier":
                market_metric[
                    "brier"
                ],

            "hybrid_brier":
                hybrid_metric[
                    "brier"
                ],

            "accuracy_gap":
                hybrid_metric[
                    "accuracy"
                ]
                - market_metric[
                    "accuracy"
                ],

            "logloss_gap":
                hybrid_metric[
                    "logloss"
                ]
                - market_metric[
                    "logloss"
                ],

            "brier_gap":
                hybrid_metric[
                    "brier"
                ]
                - market_metric[
                    "brier"
                ],

            "eligible":
                eligible,
        })

    return pd.DataFrame(
        rows
    )


def apply_gate(
    test: pd.DataFrame,
    eligible_regimes: set[str],
) -> tuple[
    np.ndarray,
    pd.DataFrame,
]:
    work = add_residual_segments(
        test
    )

    _, ai, market = (
        probability_arrays(
            work
        )
    )

    output = market.copy()

    enabled = (
        work["regime"]
        .isin(
            eligible_regimes
        )
        .to_numpy()
    )

    if enabled.any():
        output[enabled] = (
            fixed_hybrid(
                market[enabled],
                ai[enabled],
            )
        )

    metadata = work[
        [
            "season",
            "match_date",
            "home_team",
            "away_team",
            "regime",
            "market_confidence",
            "ai_confidence",
            "residual_magnitude",
            "agreement",
        ]
    ].copy()

    metadata[
        "ai_correction_enabled"
    ] = enabled

    metadata[
        "alpha"
    ] = np.where(
        enabled,
        FIXED_ALPHA,
        0.0,
    )

    return (
        output,
        metadata,
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

    frame = pd.read_csv(
        sweep.INPUTS[league]
    )

    frame = frame.copy()

    frame["target"] = (
        frame["result"]
        .map(
            sweep.TARGET_MAP
        )
    )

    print("=" * 72)
    print("RESIDUAL EDGE WALK-FORWARD")
    print("=" * 72)

    print(
        "league:",
        league,
    )

    print(
        "feature set:",
        feature_set,
    )

    print(
        "model:",
        model_name,
    )

    print(
        "fixed alpha:",
        FIXED_ALPHA,
    )

    print(
        "minimum regime rows:",
        MIN_TRAIN_ROWS,
    )

    all_oos_seasons = (
        sweep.SELECTION_TEST_SEASONS
        + (
            sweep.FINAL_HOLDOUT_SEASON,
        )
    )

    predictions = (
        diag.generate_oos_predictions(
            frame,
            feature_set_name=(
                feature_set
            ),
            model_name=model_name,
            seasons=all_oos_seasons,
        )
    )

    predictions = (
        add_residual_segments(
            predictions
        )
    )

    fold_rows = []
    regime_reports = []
    usage_reports = []

    for test_season in (
        WALKFORWARD_TEST_SEASONS
    ):
        training = (
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
            training.empty
            or test.empty
        ):
            continue

        regime_table = (
            learn_regime_table(
                training
            )
        )

        eligible = set(
            regime_table.loc[
                regime_table[
                    "eligible"
                ],
                "regime",
            ].astype(str)
        )

        gated_probability, usage = (
            apply_gate(
                test,
                eligible,
            )
        )

        y, ai, market = (
            probability_arrays(
                test
            )
        )

        ai_metric = (
            evaluate_probabilities(
                y,
                ai,
            )
        )

        market_metric = (
            evaluate_probabilities(
                y,
                market,
            )
        )

        gated_metric = (
            evaluate_probabilities(
                y,
                gated_probability,
            )
        )

        enabled_rows = int(
            usage[
                "ai_correction_enabled"
            ].sum()
        )

        enabled_rate = (
            enabled_rows
            / len(test)
        )

        probability_gain = all([
            gated_metric["logloss"]
            < market_metric["logloss"],

            gated_metric["brier"]
            < market_metric["brier"],
        ])

        full_gain = all([
            gated_metric["accuracy"]
            > market_metric["accuracy"],

            probability_gain,
        ])

        fold_rows.append({
            "test_season":
                test_season,

            "training_rows":
                len(training),

            "test_rows":
                len(test),

            "eligible_regimes":
                len(eligible),

            "enabled_rows":
                enabled_rows,

            "enabled_rate":
                enabled_rate,

            "ai_accuracy":
                ai_metric["accuracy"],

            "market_accuracy":
                market_metric[
                    "accuracy"
                ],

            "gated_accuracy":
                gated_metric[
                    "accuracy"
                ],

            "market_logloss":
                market_metric[
                    "logloss"
                ],

            "gated_logloss":
                gated_metric[
                    "logloss"
                ],

            "market_brier":
                market_metric[
                    "brier"
                ],

            "gated_brier":
                gated_metric[
                    "brier"
                ],

            "accuracy_gap":
                gated_metric[
                    "accuracy"
                ]
                - market_metric[
                    "accuracy"
                ],

            "logloss_gap":
                gated_metric[
                    "logloss"
                ]
                - market_metric[
                    "logloss"
                ],

            "brier_gap":
                gated_metric[
                    "brier"
                ]
                - market_metric[
                    "brier"
                ],

            "probability_gain":
                probability_gain,

            "full_gain":
                full_gain,
        })

        regime_table[
            "test_season"
        ] = test_season

        regime_reports.append(
            regime_table
        )

        usage[
            "test_season"
        ] = test_season

        usage_reports.append(
            usage
        )

        print()
        print(
            test_season,
            "training=",
            len(training),
            "test=",
            len(test),
        )

        print(
            " eligible regimes:",
            len(eligible),
        )

        print(
            " AI correction rows:",
            enabled_rows,
            f"({enabled_rate:.1%})",
        )

        print(
            " market:",
            market_metric,
        )

        print(
            " gated:",
            gated_metric,
        )

        print(
            " probability gain:",
            probability_gain,
        )

        print(
            " full gain:",
            full_gain,
        )

    folds = pd.DataFrame(
        fold_rows
    )

    regimes = pd.concat(
        regime_reports,
        ignore_index=True,
    )

    usage = pd.concat(
        usage_reports,
        ignore_index=True,
    )

    probability_win_rate = float(
        folds[
            "probability_gain"
        ]
        .astype(bool)
        .mean()
    )

    full_win_rate = float(
        folds[
            "full_gain"
        ]
        .astype(bool)
        .mean()
    )

    average_logloss_gap = float(
        folds[
            "logloss_gap"
        ].mean()
    )

    average_brier_gap = float(
        folds[
            "brier_gap"
        ].mean()
    )

    average_accuracy_gap = float(
        folds[
            "accuracy_gap"
        ].mean()
    )

    average_enabled_rate = float(
        folds[
            "enabled_rate"
        ].mean()
    )

    # Stability report: regimes repeatedly qualifying
    # in walk-forward training.
    stability = (
        regimes[
            regimes["eligible"]
            .astype(bool)
        ]
        .groupby(
            "regime",
            as_index=False,
        )
        .agg(
            eligible_fold_count=(
                "test_season",
                "nunique",
            ),
            average_training_rows=(
                "rows",
                "mean",
            ),
            average_logloss_gap=(
                "logloss_gap",
                "mean",
            ),
            average_brier_gap=(
                "brier_gap",
                "mean",
            ),
            average_accuracy_gap=(
                "accuracy_gap",
                "mean",
            ),
        )
        .sort_values(
            [
                "eligible_fold_count",
                "average_logloss_gap",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .reset_index(drop=True)
    )

    after = production_state()

    production_unchanged = (
        before == after
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    folds_path = (
        OUTPUT_DIR
        / f"{league.lower()}_folds.csv"
    )

    regimes_path = (
        OUTPUT_DIR
        / f"{league.lower()}_regimes.csv"
    )

    stability_path = (
        OUTPUT_DIR
        / f"{league.lower()}_stability.csv"
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

    regimes.to_csv(
        regimes_path,
        index=False,
    )

    stability.to_csv(
        stability_path,
        index=False,
    )

    usage.to_csv(
        usage_path,
        index=False,
    )

    report = {
        "league":
            league,

        "feature_set":
            feature_set,

        "model":
            model_name,

        "fixed_alpha":
            FIXED_ALPHA,

        "minimum_training_rows_per_regime":
            MIN_TRAIN_ROWS,

        "fold_count":
            len(folds),

        "probability_win_rate":
            probability_win_rate,

        "full_win_rate":
            full_win_rate,

        "average_accuracy_gap_vs_market":
            average_accuracy_gap,

        "average_logloss_gap_vs_market":
            average_logloss_gap,

        "average_brier_gap_vs_market":
            average_brier_gap,

        "average_ai_correction_rate":
            average_enabled_rate,

        "stable_regimes":
            stability.to_dict(
                orient="records"
            ),

        "promotion_gate":
            "NOT_EVALUATED",

        "next_true_unseen_period":
            "2026-2027",

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
    print("RESIDUAL EDGE SUMMARY")
    print("=" * 72)

    print(
        folds.to_string(
            index=False
        )
    )

    print()
    print(
        "probability win rate:",
        probability_win_rate,
    )

    print(
        "full win rate:",
        full_win_rate,
    )

    print(
        "average accuracy gap:",
        average_accuracy_gap,
    )

    print(
        "average logloss gap:",
        average_logloss_gap,
    )

    print(
        "average brier gap:",
        average_brier_gap,
    )

    print(
        "average AI correction rate:",
        average_enabled_rate,
    )

    print()
    print("STABLE REGIMES:")

    if stability.empty:
        print(
            "none"
        )
    else:
        print(
            stability.to_string(
                index=False
            )
        )

    print()
    print(
        "production unchanged:",
        production_unchanged,
    )

    print(
        "promotion gate:",
        "NOT_EVALUATED",
    )

    print(
        "next true unseen period:",
        "2026-2027",
    )

    print()
    print(
        "folds:",
        folds_path,
    )

    print(
        "regimes:",
        regimes_path,
    )

    print(
        "stability:",
        stability_path,
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
