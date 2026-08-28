"""Nested walk-forward EPL Structural V2 calibration research.

Research only.

For every outer test season:
1. Candidate alpha / threshold pairs are evaluated only on
   earlier inner walk-forward validation seasons.
2. A candidate must pass robustness gates on those earlier folds.
3. The selected candidate is then evaluated once on the unseen
   outer season.
4. If no candidate is robust enough, the outer fold uses
   MARKET_ONLY.

No runtime config mutation.
No Supabase writes.
No model training.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
import math

import numpy as np
import pandas as pd

from league_runtime_config import (
    EPL_RUNTIME_CONFIG,
)

from league_structural_edge_v2 import (
    WALKFORWARD_TEST_SEASONS,
)

from league_structural_v2_shadow import (
    apply_structural_v2,
    fit_reference_stats,
    structural_scores,
)


DATASET = (
    "data/"
    "epl_structural_v2_calibration_dataset.csv"
)


ALPHAS = (
    0.025,
    0.050,
    0.075,
    0.100,
    0.125,
    0.150,
    0.200,
    0.250,
)


THRESHOLDS = (
    0.25,
    0.50,
    0.75,
    1.00,
    1.25,
    1.50,
)


MARKET_COLUMNS = [
    "market_home_probability",
    "market_draw_probability",
    "market_away_probability",
]


RESULT_INDEX = {
    "H": 0,
    "D": 1,
    "A": 2,
}


def probability_matrix(
    frame: pd.DataFrame,
) -> np.ndarray:
    probability = (
        frame[
            MARKET_COLUMNS
        ]
        .to_numpy(
            dtype=float
        )
    )

    if not np.isfinite(
        probability
    ).all():
        raise ValueError(
            "Non-finite market probabilities"
        )

    total = probability.sum(
        axis=1,
        keepdims=True,
    )

    return (
        probability
        / total
    )


def targets(
    frame: pd.DataFrame,
) -> np.ndarray:
    return np.asarray(
        [
            RESULT_INDEX[
                str(value)
            ]
            for value
            in frame[
                "result"
            ]
        ],
        dtype=int,
    )


def metrics(
    probability: np.ndarray,
    y: np.ndarray,
) -> dict:
    probability = np.asarray(
        probability,
        dtype=float,
    )

    probability = np.clip(
        probability,
        1e-15,
        1.0,
    )

    probability = (
        probability
        / probability.sum(
            axis=1,
            keepdims=True,
        )
    )

    chosen = probability[
        np.arange(
            len(y)
        ),
        y,
    ]

    log_loss = float(
        -np.mean(
            np.log(
                chosen
            )
        )
    )

    one_hot = np.eye(
        3
    )[y]

    brier = float(
        np.mean(
            np.sum(
                (
                    probability
                    - one_hot
                )
                ** 2,
                axis=1,
            )
        )
    )

    accuracy = float(
        np.mean(
            np.argmax(
                probability,
                axis=1,
            )
            == y
        )
    )

    return {
        "log_loss":
            log_loss,

        "brier":
            brier,

        "accuracy":
            accuracy,
    }


def calibrated_config(
    *,
    alpha: float,
    threshold: float,
):
    structural = replace(
        EPL_RUNTIME_CONFIG.structural_v2,
        calibration_status="CALIBRATED",
        structural_alpha=float(
            alpha
        ),
        edge_threshold=float(
            threshold
        ),
    )

    config = replace(
        EPL_RUNTIME_CONFIG,
        structural_v2=structural,
    )

    config.validate()

    return config


def evaluate_structural_fold(
    *,
    training: pd.DataFrame,
    test: pd.DataFrame,
    alpha: float,
    threshold: float,
) -> dict:
    stats = fit_reference_stats(
        training,
        EPL_RUNTIME_CONFIG,
    )

    score = (
        structural_scores(
            test,
            stats,
        )
        .to_numpy(
            dtype=float
        )
    )

    if not np.isfinite(
        score
    ).all():
        raise ValueError(
            "Non-finite structural score"
        )

    market = probability_matrix(
        test
    )

    y = targets(
        test
    )

    config = calibrated_config(
        alpha=alpha,
        threshold=threshold,
    )

    (
        shadow,
        enabled,
        weights,
    ) = apply_structural_v2(
        market,
        score,
        config,
    )

    if not np.array_equal(
        np.argmax(
            market,
            axis=1,
        ),
        np.argmax(
            shadow,
            axis=1,
        ),
    ):
        raise ValueError(
            "Structural V2 changed market argmax"
        )

    market_metrics = metrics(
        market,
        y,
    )

    shadow_metrics = metrics(
        shadow,
        y,
    )

    enabled = np.asarray(
        enabled,
        dtype=bool,
    )

    weights = np.asarray(
        weights,
        dtype=float,
    )

    return {
        "rows":
            len(test),

        "market_log_loss":
            market_metrics[
                "log_loss"
            ],

        "shadow_log_loss":
            shadow_metrics[
                "log_loss"
            ],

        "log_loss_delta":
            (
                shadow_metrics[
                    "log_loss"
                ]
                - market_metrics[
                    "log_loss"
                ]
            ),

        "market_brier":
            market_metrics[
                "brier"
            ],

        "shadow_brier":
            shadow_metrics[
                "brier"
            ],

        "brier_delta":
            (
                shadow_metrics[
                    "brier"
                ]
                - market_metrics[
                    "brier"
                ]
            ),

        "market_accuracy":
            market_metrics[
                "accuracy"
            ],

        "shadow_accuracy":
            shadow_metrics[
                "accuracy"
            ],

        "correction_rows":
            int(
                enabled.sum()
            ),

        "coverage":
            float(
                enabled.mean()
            ),

        "mean_weight":
            (
                float(
                    weights[
                        enabled
                    ].mean()
                )
                if enabled.any()
                else 0.0
            ),

        "mean_abs_score":
            float(
                np.mean(
                    np.abs(
                        score
                    )
                )
            ),
    }


def weighted_average(
    frame: pd.DataFrame,
    column: str,
) -> float:
    return float(
        np.average(
            frame[
                column
            ],
            weights=frame[
                "rows"
            ],
        )
    )


def inner_candidate_report(
    data: pd.DataFrame,
    prior_seasons: list[str],
) -> pd.DataFrame:
    rows = []

    # First prior season can only be training.
    validation_seasons = (
        prior_seasons[
            1:
        ]
    )

    if not validation_seasons:
        return pd.DataFrame()

    for alpha in ALPHAS:
        for threshold in THRESHOLDS:
            fold_rows = []

            for validation_season in (
                validation_seasons
            ):
                validation_index = (
                    prior_seasons.index(
                        validation_season
                    )
                )

                training_seasons = (
                    prior_seasons[
                        :validation_index
                    ]
                )

                training = data.loc[
                    data[
                        "season"
                    ].isin(
                        training_seasons
                    )
                ].copy()

                validation = data.loc[
                    data[
                        "season"
                    ]
                    == validation_season
                ].copy()

                if (
                    training.empty
                    or validation.empty
                ):
                    continue

                result = (
                    evaluate_structural_fold(
                        training=training,
                        test=validation,
                        alpha=alpha,
                        threshold=threshold,
                    )
                )

                result[
                    "validation_season"
                ] = (
                    validation_season
                )

                fold_rows.append(
                    result
                )

            folds = pd.DataFrame(
                fold_rows
            )

            if folds.empty:
                continue

            required_positive = (
                math.ceil(
                    len(folds)
                    * 0.60
                )
            )

            ll_improved = int(
                (
                    folds[
                        "log_loss_delta"
                    ]
                    < 0
                ).sum()
            )

            brier_improved = int(
                (
                    folds[
                        "brier_delta"
                    ]
                    < 0
                ).sum()
            )

            ll_delta = (
                weighted_average(
                    folds,
                    "log_loss_delta",
                )
            )

            brier_delta = (
                weighted_average(
                    folds,
                    "brier_delta",
                )
            )

            rows.append(
                {
                    "alpha":
                        alpha,

                    "threshold":
                        threshold,

                    "inner_folds":
                        len(folds),

                    "inner_rows":
                        int(
                            folds[
                                "rows"
                            ].sum()
                        ),

                    "log_loss_delta":
                        ll_delta,

                    "brier_delta":
                        brier_delta,

                    "ll_improved_folds":
                        ll_improved,

                    "brier_improved_folds":
                        brier_improved,

                    "required_positive_folds":
                        required_positive,

                    "coverage":
                        weighted_average(
                            folds,
                            "coverage",
                        ),

                    "mean_weight":
                        weighted_average(
                            folds,
                            "mean_weight",
                        ),

                    "robust":
                        (
                            ll_delta < 0
                            and brier_delta < 0
                            and ll_improved
                                >= required_positive
                            and brier_improved
                                >= required_positive
                        ),
                }
            )

    report = pd.DataFrame(
        rows
    )

    if report.empty:
        return report

    # Primary objective = log loss.
    # Brier = secondary.
    # With practically tied performance prefer
    # smaller alpha and higher threshold.
    return (
        report
        .sort_values(
            [
                "robust",
                "log_loss_delta",
                "brier_delta",
                "alpha",
                "threshold",
            ],
            ascending=[
                False,
                True,
                True,
                True,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )


def market_only_result(
    test: pd.DataFrame,
) -> dict:
    market = probability_matrix(
        test
    )

    y = targets(
        test
    )

    baseline = metrics(
        market,
        y,
    )

    return {
        "rows":
            len(test),

        "market_log_loss":
            baseline[
                "log_loss"
            ],

        "shadow_log_loss":
            baseline[
                "log_loss"
            ],

        "log_loss_delta":
            0.0,

        "market_brier":
            baseline[
                "brier"
            ],

        "shadow_brier":
            baseline[
                "brier"
            ],

        "brier_delta":
            0.0,

        "market_accuracy":
            baseline[
                "accuracy"
            ],

        "shadow_accuracy":
            baseline[
                "accuracy"
            ],

        "correction_rows":
            0,

        "coverage":
            0.0,

        "mean_weight":
            0.0,

        "mean_abs_score":
            0.0,
    }


def main() -> None:
    data = pd.read_csv(
        DATASET
    )

    data = data.loc[
        data[
            "trainable"
        ].astype(bool)
        &
        data[
            "market_valid"
        ].astype(bool)
    ].copy()

    data[
        "match_date"
    ] = pd.to_datetime(
        data[
            "match_date"
        ],
        errors="raise",
    )

    data = (
        data
        .sort_values(
            [
                "match_date",
                "home_team",
                "away_team",
            ],
            kind="stable",
        )
        .reset_index(
            drop=True
        )
    )

    required = {
        "elo_difference",
        "form_difference",
        "venue_win_rate_difference",
        "home_goals_scored_last5",
        "home_goals_conceded_last5",
        "away_goals_scored_last5",
        "away_goals_conceded_last5",
    }

    missing = (
        required
        - set(
            data.columns
        )
    )

    if missing:
        raise SystemExit(
            "Missing Structural V2 features: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    seasons = sorted(
        data[
            "season"
        ].unique()
    )

    outer_seasons = [
        season
        for season
        in WALKFORWARD_TEST_SEASONS
        if season in seasons
    ]

    print(
        "usable rows:",
        len(data),
    )

    print(
        "all seasons:",
        seasons,
    )

    print(
        "outer OOS seasons:",
        outer_seasons,
    )

    if len(
        outer_seasons
    ) != len(
        WALKFORWARD_TEST_SEASONS
    ):
        raise SystemExit(
            "Configured walk-forward seasons missing"
        )

    outer_rows = []

    selection_counter = Counter()

    for outer_season in outer_seasons:
        outer_index = seasons.index(
            outer_season
        )

        prior_seasons = (
            seasons[
                :outer_index
            ]
        )

        training = data.loc[
            data[
                "season"
            ].isin(
                prior_seasons
            )
        ].copy()

        test = data.loc[
            data[
                "season"
            ]
            == outer_season
        ].copy()

        print()
        print(
            "=" * 78
        )

        print(
            "OUTER TEST:",
            outer_season,
        )

        print(
            "prior seasons:",
            prior_seasons,
        )

        print(
            "training rows:",
            len(training),
        )

        print(
            "test rows:",
            len(test),
        )

        inner = (
            inner_candidate_report(
                data,
                prior_seasons,
            )
        )

        if inner.empty:
            robust = inner

        else:
            robust = inner.loc[
                inner[
                    "robust"
                ].astype(bool)
            ]

        print()
        print(
            "TOP INNER CANDIDATES:"
        )

        if inner.empty:
            print(
                "no inner folds"
            )
        else:
            print(
                inner.head(
                    10
                ).to_string(
                    index=False
                )
            )

        if robust.empty:
            selection = (
                "MARKET_ONLY"
            )

            alpha = None
            threshold = None

            result = (
                market_only_result(
                    test
                )
            )

        else:
            winner = (
                robust.iloc[0]
            )

            alpha = float(
                winner[
                    "alpha"
                ]
            )

            threshold = float(
                winner[
                    "threshold"
                ]
            )

            selection = (
                f"{alpha:.3f}/"
                f"{threshold:.2f}"
            )

            result = (
                evaluate_structural_fold(
                    training=training,
                    test=test,
                    alpha=alpha,
                    threshold=threshold,
                )
            )

        selection_counter[
            selection
        ] += 1

        result.update(
            {
                "season":
                    outer_season,

                "selection":
                    selection,

                "selected_alpha":
                    alpha,

                "selected_threshold":
                    threshold,
            }
        )

        outer_rows.append(
            result
        )

        print()
        print(
            "OUTER SELECTION:",
            selection,
        )

        print(
            "outer LL delta:",
            result[
                "log_loss_delta"
            ],
        )

        print(
            "outer Brier delta:",
            result[
                "brier_delta"
            ],
        )

        print(
            "outer corrections:",
            result[
                "correction_rows"
            ],
        )

        print(
            "outer coverage:",
            result[
                "coverage"
            ],
        )

    outer = pd.DataFrame(
        outer_rows
    )

    print()
    print(
        "=" * 78
    )

    print(
        "NESTED OUTER OOS RESULTS"
    )

    print(
        "=" * 78
    )

    columns = [
        "season",
        "selection",
        "rows",
        "market_log_loss",
        "shadow_log_loss",
        "log_loss_delta",
        "market_brier",
        "shadow_brier",
        "brier_delta",
        "market_accuracy",
        "shadow_accuracy",
        "correction_rows",
        "coverage",
        "mean_weight",
    ]

    print(
        outer[
            columns
        ].to_string(
            index=False
        )
    )

    overall_market_ll = (
        weighted_average(
            outer,
            "market_log_loss",
        )
    )

    overall_shadow_ll = (
        weighted_average(
            outer,
            "shadow_log_loss",
        )
    )

    overall_market_brier = (
        weighted_average(
            outer,
            "market_brier",
        )
    )

    overall_shadow_brier = (
        weighted_average(
            outer,
            "shadow_brier",
        )
    )

    overall_market_accuracy = (
        weighted_average(
            outer,
            "market_accuracy",
        )
    )

    overall_shadow_accuracy = (
        weighted_average(
            outer,
            "shadow_accuracy",
        )
    )

    ll_delta = (
        overall_shadow_ll
        - overall_market_ll
    )

    brier_delta = (
        overall_shadow_brier
        - overall_market_brier
    )

    ll_improved_folds = int(
        (
            outer[
                "log_loss_delta"
            ]
            < 0
        ).sum()
    )

    brier_improved_folds = int(
        (
            outer[
                "brier_delta"
            ]
            < 0
        ).sum()
    )

    structural_folds = int(
        (
            outer[
                "selection"
            ]
            != "MARKET_ONLY"
        ).sum()
    )

    required_outer = (
        math.ceil(
            len(outer)
            * 0.60
        )
    )

    print()
    print(
        "===== NESTED AGGREGATE ====="
    )

    print(
        "outer rows:",
        int(
            outer[
                "rows"
            ].sum()
        ),
    )

    print(
        "market log loss:",
        overall_market_ll,
    )

    print(
        "nested shadow log loss:",
        overall_shadow_ll,
    )

    print(
        "log loss delta:",
        ll_delta,
    )

    print(
        "market brier:",
        overall_market_brier,
    )

    print(
        "nested shadow brier:",
        overall_shadow_brier,
    )

    print(
        "brier delta:",
        brier_delta,
    )

    print(
        "market accuracy:",
        overall_market_accuracy,
    )

    print(
        "nested shadow accuracy:",
        overall_shadow_accuracy,
    )

    print(
        "LL folds improved:",
        ll_improved_folds,
        "/",
        len(outer),
    )

    print(
        "Brier folds improved:",
        brier_improved_folds,
        "/",
        len(outer),
    )

    print(
        "Structural selected folds:",
        structural_folds,
        "/",
        len(outer),
    )

    print(
        "required positive folds:",
        required_outer,
    )

    print()
    print(
        "===== PARAMETER SELECTION FREQUENCY ====="
    )

    for selection, count in (
        selection_counter
        .most_common()
    ):
        print(
            selection,
            count,
        )

    print()
    print(
        "===== TRUE NESTED OOS DECISION ====="
    )

    passed = (
        ll_delta < 0
        and brier_delta < 0
        and ll_improved_folds
            >= required_outer
        and brier_improved_folds
            >= required_outer
        and structural_folds
            >= required_outer
    )

    if passed:
        print(
            "PASS: EPL STRUCTURAL V2 HAS ROBUST NESTED OOS SIGNAL"
        )

        print(
            "RESEARCH CANDIDATE ONLY — DO NOT ACTIVATE YET"
        )

    else:
        print(
            "STOP: EPL STRUCTURAL V2 DOES NOT PASS NESTED OOS GATE"
        )

        print(
            "KEEP EPL STRUCTURAL V2 CALIBRATION_REQUIRED"
        )


if __name__ == "__main__":
    main()
