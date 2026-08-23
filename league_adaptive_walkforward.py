"""Walk-forward validation for adaptive AI + market hybrid.

Research-only.

For each test season:
- build OOS predictions for all earlier selection seasons;
- learn adaptive alpha policy only from earlier OOS data;
- apply frozen policy to the next season;
- never tune on the evaluated season;
- small segments fall back to broader confidence policy;
- alpha=0 is always allowed;
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

import league_adaptive_hybrid as adaptive
import league_model_diagnostics as diag
import league_model_sweep as sweep


ROOT = Path(__file__).resolve().parent

OUTPUT_DIR = (
    ROOT
    / "experiments"
    / "league_adaptive_walkforward"
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

# Need enough observations before segment-level policy is trusted.
MIN_SEGMENT_ROWS = 50

# Need enough observations for confidence-bucket fallback.
MIN_CONFIDENCE_ROWS = 100

# First season has no prior OOS seasons from which to learn policy.
WALKFORWARD_TEST_SEASONS = (
    "2021-2022",
    "2022-2023",
    "2023-2024",
    "2024-2025",
    "2025-2026",
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


def calculate_metrics(
    frame: pd.DataFrame,
    probability: np.ndarray,
) -> dict:
    y = (
        frame["target"]
        .astype(int)
        .to_numpy()
    )

    return adaptive.metrics(
        y,
        probability,
    )


def select_alpha(
    frame: pd.DataFrame,
) -> float:
    y, ai, market = (
        adaptive.probabilities(
            frame
        )
    )

    rows = []

    for alpha in adaptive.ALPHAS:
        hybrid = (
            diag.hybrid_probability(
                market,
                ai,
                alpha,
            )
        )

        metric = (
            adaptive.metrics(
                y,
                hybrid,
            )
        )

        rows.append({
            "alpha":
                alpha,

            "accuracy":
                metric["accuracy"],

            "logloss":
                metric["logloss"],

            "brier":
                metric["brier"],
        })

    table = pd.DataFrame(
        rows
    )

    table = (
        table
        .sort_values(
            [
                "logloss",
                "brier",
                "accuracy",
                "alpha",
            ],
            ascending=[
                True,
                True,
                False,
                True,
            ],
        )
        .reset_index(drop=True)
    )

    return float(
        table.iloc[0][
            "alpha"
        ]
    )


def build_policy(
    training_oos: pd.DataFrame,
) -> dict:
    """Build hierarchical policy.

    Priority:
    1. specific confidence + agreement segment,
       only if enough rows;
    2. confidence bucket fallback,
       only if enough rows;
    3. global alpha;
    4. alpha=0 implicitly if key missing.
    """

    training_oos = (
        adaptive.add_segments(
            training_oos
        )
    )

    policy = {
        "segments": {},
        "confidence": {},
        "global_alpha":
            select_alpha(
                training_oos
            ),
    }

    for segment, group in (
        training_oos.groupby(
            "segment",
            sort=True,
        )
    ):
        if (
            len(group)
            < MIN_SEGMENT_ROWS
        ):
            continue

        policy[
            "segments"
        ][str(segment)] = (
            select_alpha(
                group
            )
        )

    for bucket, group in (
        training_oos.groupby(
            "confidence_bucket",
            sort=True,
        )
    ):
        if (
            len(group)
            < MIN_CONFIDENCE_ROWS
        ):
            continue

        policy[
            "confidence"
        ][str(bucket)] = (
            select_alpha(
                group
            )
        )

    return policy


def alpha_for_row(
    row: pd.Series,
    policy: dict,
) -> tuple[float, str]:
    segment = str(
        row["segment"]
    )

    confidence = str(
        row[
            "confidence_bucket"
        ]
    )

    if (
        segment
        in policy["segments"]
    ):
        return (
            float(
                policy[
                    "segments"
                ][segment]
            ),
            "SEGMENT",
        )

    if (
        confidence
        in policy["confidence"]
    ):
        return (
            float(
                policy[
                    "confidence"
                ][confidence]
            ),
            "CONFIDENCE",
        )

    if (
        "global_alpha"
        in policy
    ):
        return (
            float(
                policy[
                    "global_alpha"
                ]
            ),
            "GLOBAL",
        )

    return (
        0.0,
        "MARKET",
    )


def apply_policy(
    frame: pd.DataFrame,
    policy: dict,
) -> tuple[
    np.ndarray,
    pd.DataFrame,
]:
    work = adaptive.add_segments(
        frame
    )

    _, ai, market = (
        adaptive.probabilities(
            work
        )
    )

    output = np.zeros_like(
        market,
        dtype=float,
    )

    sources = []
    alphas = []

    for position, (
        _,
        row,
    ) in enumerate(
        work.iterrows()
    ):
        alpha, source = (
            alpha_for_row(
                row,
                policy,
            )
        )

        output[position] = (
            (1.0 - alpha)
            * market[position]
            + alpha
            * ai[position]
        )

        alphas.append(
            alpha
        )

        sources.append(
            source
        )

    output = (
        output
        / output.sum(
            axis=1,
            keepdims=True,
        )
    )

    metadata = work[
        [
            "season",
            "match_date",
            "home_team",
            "away_team",
            "segment",
            "confidence_bucket",
            "agreement_bucket",
        ]
    ].copy()

    metadata[
        "selected_alpha"
    ] = alphas

    metadata[
        "policy_source"
    ] = sources

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
    print("ADAPTIVE HYBRID WALK-FORWARD")
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
        "test seasons:",
        WALKFORWARD_TEST_SEASONS,
    )

    # Generate OOS predictions once per season.
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
            seasons=(
                all_oos_seasons
            ),
        )
    )

    fold_rows = []
    metadata_rows = []
    policy_reports = {}

    for test_season in (
        WALKFORWARD_TEST_SEASONS
    ):
        training_oos = (
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
            training_oos.empty
            or test.empty
        ):
            continue

        policy = build_policy(
            training_oos
        )

        policy_reports[
            test_season
        ] = policy

        adaptive_probability, metadata = (
            apply_policy(
                test,
                policy,
            )
        )

        y, ai, market = (
            adaptive.probabilities(
                test
            )
        )

        ai_metric = (
            adaptive.metrics(
                y,
                ai,
            )
        )

        market_metric = (
            adaptive.metrics(
                y,
                market,
            )
        )

        adaptive_metric = (
            adaptive.metrics(
                y,
                adaptive_probability,
            )
        )

        probability_gain = all([
            adaptive_metric[
                "logloss"
            ]
            < market_metric[
                "logloss"
            ],

            adaptive_metric[
                "brier"
            ]
            < market_metric[
                "brier"
            ],
        ])

        full_gain = all([
            adaptive_metric[
                "accuracy"
            ]
            > market_metric[
                "accuracy"
            ],

            probability_gain,
        ])

        fold_rows.append({
            "test_season":
                test_season,

            "training_oos_rows":
                len(training_oos),

            "test_rows":
                len(test),

            "ai_accuracy":
                ai_metric[
                    "accuracy"
                ],

            "market_accuracy":
                market_metric[
                    "accuracy"
                ],

            "adaptive_accuracy":
                adaptive_metric[
                    "accuracy"
                ],

            "ai_logloss":
                ai_metric[
                    "logloss"
                ],

            "market_logloss":
                market_metric[
                    "logloss"
                ],

            "adaptive_logloss":
                adaptive_metric[
                    "logloss"
                ],

            "ai_brier":
                ai_metric[
                    "brier"
                ],

            "market_brier":
                market_metric[
                    "brier"
                ],

            "adaptive_brier":
                adaptive_metric[
                    "brier"
                ],

            "probability_gain":
                probability_gain,

            "full_gain":
                full_gain,

            "segment_policy_count":
                len(
                    policy[
                        "segments"
                    ]
                ),

            "confidence_policy_count":
                len(
                    policy[
                        "confidence"
                    ]
                ),

            "global_alpha":
                policy[
                    "global_alpha"
                ],
        })

        metadata[
            "test_season"
        ] = test_season

        metadata_rows.append(
            metadata
        )

        print()
        print(
            test_season,
            "training_oos=",
            len(training_oos),
            "test=",
            len(test),
        )

        print(
            " market:",
            market_metric,
        )

        print(
            " adaptive:",
            adaptive_metric,
        )

        print(
            " probability gain:",
            probability_gain,
        )

        print(
            " full gain:",
            full_gain,
        )

        print(
            " global alpha:",
            policy[
                "global_alpha"
            ],
        )

    folds = pd.DataFrame(
        fold_rows
    )

    metadata = pd.concat(
        metadata_rows,
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

    avg_logloss_gap = float(
        (
            folds[
                "adaptive_logloss"
            ]
            - folds[
                "market_logloss"
            ]
        ).mean()
    )

    avg_brier_gap = float(
        (
            folds[
                "adaptive_brier"
            ]
            - folds[
                "market_brier"
            ]
        ).mean()
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

    metadata_path = (
        OUTPUT_DIR
        / f"{league.lower()}_policy_usage.csv"
    )

    report_path = (
        OUTPUT_DIR
        / f"{league.lower()}_report.json"
    )

    folds.to_csv(
        folds_path,
        index=False,
    )

    metadata.to_csv(
        metadata_path,
        index=False,
    )

    report = {
        "league":
            league,

        "feature_set":
            feature_set,

        "model":
            model_name,

        "walkforward_test_seasons":
            list(
                WALKFORWARD_TEST_SEASONS
            ),

        "min_segment_rows":
            MIN_SEGMENT_ROWS,

        "min_confidence_rows":
            MIN_CONFIDENCE_ROWS,

        "fold_count":
            len(folds),

        "probability_win_rate":
            probability_win_rate,

        "full_win_rate":
            full_win_rate,

        "average_logloss_gap_vs_market":
            avg_logloss_gap,

        "average_brier_gap_vs_market":
            avg_brier_gap,

        "policies":
            policy_reports,

        "production_unchanged":
            production_unchanged,

        "candidate_model_saved":
            False,

        "promotion_performed":
            False,

        "next_true_unseen_period":
            "2026-2027",
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
    print("WALK-FORWARD SUMMARY")
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
        "average logloss gap:",
        avg_logloss_gap,
    )

    print(
        "average brier gap:",
        avg_brier_gap,
    )

    print(
        "production unchanged:",
        production_unchanged,
    )

    print(
        "next true unseen period:",
        "2026-2027",
    )

    print(
        "folds:",
        folds_path,
    )

    print(
        "policy usage:",
        metadata_path,
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
