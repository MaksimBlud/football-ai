"""Adaptive AI + market hybrid research.

Research-only.

Policy is selected from historical selection seasons only.
The already-inspected 2025-2026 season is used only as a retrospective check.

No model artifact is saved.
No production artifact is modified or promoted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss

import league_model_diagnostics as diag
import league_model_sweep as sweep


ROOT = Path(__file__).resolve().parent

OUTPUT_DIR = (
    ROOT
    / "experiments"
    / "league_adaptive_hybrid"
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

ALPHAS = (
    0.00,
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
)

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


def brier(
    y_true: np.ndarray,
    probability: np.ndarray,
) -> float:
    one_hot = np.eye(3)[y_true]

    return float(
        np.mean(
            np.sum(
                (probability - one_hot) ** 2,
                axis=1,
            )
        )
    )


def metrics(
    y_true: np.ndarray,
    probability: np.ndarray,
) -> dict:
    prediction = np.argmax(
        probability,
        axis=1,
    )

    return {
        "accuracy": float(
            accuracy_score(
                y_true,
                prediction,
            )
        ),
        "logloss": float(
            log_loss(
                y_true,
                probability,
                labels=[0, 1, 2],
            )
        ),
        "brier": brier(
            y_true,
            probability,
        ),
    }


def add_segments(
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

    result[
        "ai_prediction"
    ] = np.argmax(
        ai,
        axis=1,
    )

    result[
        "market_prediction"
    ] = np.argmax(
        market,
        axis=1,
    )

    result[
        "agree"
    ] = (
        result["ai_prediction"]
        == result["market_prediction"]
    )

    result[
        "market_confidence"
    ] = market.max(
        axis=1
    )

    result[
        "confidence_bucket"
    ] = pd.cut(
        result[
            "market_confidence"
        ],
        bins=CONFIDENCE_BINS,
        labels=CONFIDENCE_LABELS,
        include_lowest=True,
        right=False,
    ).astype(str)

    result[
        "agreement_bucket"
    ] = np.where(
        result["agree"],
        "AGREE",
        "DISAGREE",
    )

    result[
        "segment"
    ] = (
        result[
            "confidence_bucket"
        ].astype(str)
        + "__"
        + result[
            "agreement_bucket"
        ].astype(str)
    )

    return result


def probabilities(
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


def select_segment_policy(
    selection: pd.DataFrame,
) -> tuple[
    dict[str, float],
    pd.DataFrame,
]:
    rows = []

    policy = {}

    for segment, group in (
        selection.groupby(
            "segment",
            sort=True,
        )
    ):
        y, ai, market = (
            probabilities(
                group
            )
        )

        market_metric = metrics(
            y,
            market,
        )

        candidate_rows = []

        for alpha in ALPHAS:
            hybrid = (
                diag.hybrid_probability(
                    market,
                    ai,
                    alpha,
                )
            )

            hybrid_metric = metrics(
                y,
                hybrid,
            )

            candidate_rows.append({
                "segment":
                    segment,

                "rows":
                    len(group),

                "alpha":
                    alpha,

                "accuracy":
                    hybrid_metric[
                        "accuracy"
                    ],

                "logloss":
                    hybrid_metric[
                        "logloss"
                    ],

                "brier":
                    hybrid_metric[
                        "brier"
                    ],

                "market_accuracy":
                    market_metric[
                        "accuracy"
                    ],

                "market_logloss":
                    market_metric[
                        "logloss"
                    ],

                "market_brier":
                    market_metric[
                        "brier"
                    ],
            })

        candidates = pd.DataFrame(
            candidate_rows
        )

        # Select using proper scoring rules.
        # Accuracy only breaks ties.
        candidates = (
            candidates
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

        winner = (
            candidates.iloc[0]
        )

        selected_alpha = float(
            winner["alpha"]
        )

        policy[
            str(segment)
        ] = selected_alpha

        candidates[
            "selected"
        ] = False

        candidates.loc[
            0,
            "selected",
        ] = True

        rows.append(
            candidates
        )

    report = pd.concat(
        rows,
        ignore_index=True,
    )

    return policy, report


def apply_policy(
    frame: pd.DataFrame,
    policy: dict[str, float],
) -> np.ndarray:
    _, ai, market = (
        probabilities(frame)
    )

    result = np.zeros_like(
        market,
        dtype=float,
    )

    for position, (
        _,
        row,
    ) in enumerate(
        frame.iterrows()
    ):
        segment = str(
            row["segment"]
        )

        alpha = float(
            policy.get(
                segment,
                0.0,
            )
        )

        result[position] = (
            (1.0 - alpha)
            * market[position]
            + alpha
            * ai[position]
        )

    result = (
        result
        / result.sum(
            axis=1,
            keepdims=True,
        )
    )

    return result


def evaluate(
    frame: pd.DataFrame,
    policy: dict[str, float],
) -> dict:
    y, ai, market = (
        probabilities(frame)
    )

    adaptive = apply_policy(
        frame,
        policy,
    )

    return {
        "rows":
            len(frame),

        "ai":
            metrics(
                y,
                ai,
            ),

        "market":
            metrics(
                y,
                market,
            ),

        "adaptive":
            metrics(
                y,
                adaptive,
            ),
    }


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
    print("ADAPTIVE HYBRID RESEARCH")
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
        "selection seasons:",
        sweep.SELECTION_TEST_SEASONS,
    )

    print(
        "retrospective season:",
        sweep.FINAL_HOLDOUT_SEASON,
    )

    selection = (
        diag.generate_oos_predictions(
            frame,
            feature_set_name=(
                feature_set
            ),
            model_name=model_name,
            seasons=(
                sweep.SELECTION_TEST_SEASONS
            ),
        )
    )

    selection = add_segments(
        selection
    )

    policy, policy_table = (
        select_segment_policy(
            selection
        )
    )

    selection_result = evaluate(
        selection,
        policy,
    )

    print()
    print("=" * 72)
    print("SELECTED POLICY")
    print("=" * 72)

    for segment in sorted(
        policy
    ):
        print(
            f"{segment:25}",
            "alpha=",
            policy[segment],
        )

    print()
    print("SELECTION RESULT:")

    print(
        json.dumps(
            selection_result,
            indent=2,
        )
    )

    # This season has already been inspected in earlier research.
    # It is NOT a new promotion holdout.
    retrospective = (
        diag.generate_oos_predictions(
            frame,
            feature_set_name=(
                feature_set
            ),
            model_name=model_name,
            seasons=(
                sweep.FINAL_HOLDOUT_SEASON,
            ),
        )
    )

    retrospective = add_segments(
        retrospective
    )

    retrospective_result = (
        evaluate(
            retrospective,
            policy,
        )
    )

    print()
    print("=" * 72)
    print("2025-2026 RETROSPECTIVE CHECK")
    print("=" * 72)

    print(
        json.dumps(
            retrospective_result,
            indent=2,
        )
    )

    selection_adaptive = (
        selection_result[
            "adaptive"
        ]
    )

    selection_market = (
        selection_result[
            "market"
        ]
    )

    retrospective_adaptive = (
        retrospective_result[
            "adaptive"
        ]
    )

    retrospective_market = (
        retrospective_result[
            "market"
        ]
    )

    selection_probability_gain = all([
        selection_adaptive[
            "logloss"
        ]
        < selection_market[
            "logloss"
        ],

        selection_adaptive[
            "brier"
        ]
        < selection_market[
            "brier"
        ],
    ])

    retrospective_probability_gain = all([
        retrospective_adaptive[
            "logloss"
        ]
        < retrospective_market[
            "logloss"
        ],

        retrospective_adaptive[
            "brier"
        ]
        < retrospective_market[
            "brier"
        ],
    ])

    after = production_state()

    production_unchanged = (
        before == after
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    policy_table_path = (
        OUTPUT_DIR
        / f"{league.lower()}_policy_search.csv"
    )

    report_path = (
        OUTPUT_DIR
        / f"{league.lower()}_report.json"
    )

    policy_table.to_csv(
        policy_table_path,
        index=False,
    )

    report = {
        "league":
            league,

        "feature_set":
            feature_set,

        "model":
            model_name,

        "policy":
            policy,

        "selection":
            selection_result,

        "retrospective_2025_2026":
            retrospective_result,

        "selection_probability_gain":
            selection_probability_gain,

        "retrospective_probability_gain":
            retrospective_probability_gain,

        "promotion_gate":
            "NOT_EVALUATED",

        "next_true_holdout":
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
    print("RESEARCH RESULT")
    print("=" * 72)

    print(
        "selection probability gain:",
        selection_probability_gain,
    )

    print(
        "retrospective probability gain:",
        retrospective_probability_gain,
    )

    print(
        "promotion gate:",
        "NOT_EVALUATED",
    )

    print(
        "next true holdout:",
        "2026-2027",
    )

    print(
        "production unchanged:",
        production_unchanged,
    )

    print(
        "candidate saved:",
        False,
    )

    print(
        "promotion:",
        False,
    )

    print(
        "policy table:",
        policy_table_path,
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
