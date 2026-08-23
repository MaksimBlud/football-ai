"""Explain stable residual-edge regimes.

Research-only.

Reads:
- La Liga trainable feature dataset
- existing OOS prediction logic
- residual-edge regime definition

Produces:
- feature profiles for stable regimes
- standardized differences vs all OOS matches
- feature ranking by absolute regime separation

No training artifact is saved.
No production artifact is modified.
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
import league_residual_edge as residual


ROOT = Path(__file__).resolve().parent

OUTPUT_DIR = (
    ROOT
    / "experiments"
    / "league_regime_explainer"
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

MIN_STABLE_FOLDS = 2


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

    "home_odds",
    "draw_odds",
    "away_odds",
]


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


def stable_regimes_from_report(
    league: str,
) -> list[str]:
    path = (
        ROOT
        / "experiments"
        / "league_residual_edge"
        / f"{league.lower()}_stability.csv"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Residual stability file missing: {path}"
        )

    table = pd.read_csv(
        path
    )

    if table.empty:
        return []

    stable = table[
        table[
            "eligible_fold_count"
        ]
        >= MIN_STABLE_FOLDS
    ]

    return (
        stable["regime"]
        .astype(str)
        .tolist()
    )


def build_oos_with_features(
    league: str,
) -> pd.DataFrame:
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

    predictions = (
        residual.add_residual_segments(
            predictions
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
        + FEATURES
    ].copy()

    merged = predictions.merge(
        feature_frame,
        on=key,
        how="left",
        validate="one_to_one",
        suffixes=("", "_feature"),
    )

    for feature in FEATURES:
        alternate = (
            feature
            + "_feature"
        )

        if (
            feature not in merged.columns
            and alternate
            in merged.columns
        ):
            merged[feature] = (
                merged[alternate]
            )

        elif (
            feature in merged.columns
            and alternate
            in merged.columns
        ):
            merged[feature] = (
                merged[feature]
                .fillna(
                    merged[
                        alternate
                    ]
                )
            )

    missing = [
        feature
        for feature in FEATURES
        if feature
        not in merged.columns
    ]

    if missing:
        raise RuntimeError(
            "Missing explanation features: "
            + ", ".join(missing)
        )

    return merged


def standardized_difference(
    regime: pd.Series,
    baseline: pd.Series,
) -> float:
    regime = pd.to_numeric(
        regime,
        errors="coerce",
    ).dropna()

    baseline = pd.to_numeric(
        baseline,
        errors="coerce",
    ).dropna()

    if (
        regime.empty
        or baseline.empty
    ):
        return float("nan")

    pooled = np.sqrt(
        (
            regime.var(ddof=1)
            + baseline.var(ddof=1)
        )
        / 2.0
    )

    if (
        not np.isfinite(pooled)
        or pooled == 0
    ):
        return 0.0

    return float(
        (
            regime.mean()
            - baseline.mean()
        )
        / pooled
    )


def explain_regime(
    frame: pd.DataFrame,
    regime_name: str,
) -> pd.DataFrame:
    regime = frame[
        frame["regime"]
        == regime_name
    ].copy()

    baseline = frame[
        frame["regime"]
        != regime_name
    ].copy()

    rows = []

    for feature in FEATURES:
        regime_values = (
            pd.to_numeric(
                regime[feature],
                errors="coerce",
            )
        )

        baseline_values = (
            pd.to_numeric(
                baseline[feature],
                errors="coerce",
            )
        )

        rows.append({
            "regime":
                regime_name,

            "feature":
                feature,

            "regime_rows":
                int(
                    regime_values
                    .notna()
                    .sum()
                ),

            "baseline_rows":
                int(
                    baseline_values
                    .notna()
                    .sum()
                ),

            "regime_mean":
                float(
                    regime_values.mean()
                ),

            "baseline_mean":
                float(
                    baseline_values.mean()
                ),

            "mean_difference":
                float(
                    regime_values.mean()
                    - baseline_values.mean()
                ),

            "standardized_difference":
                standardized_difference(
                    regime_values,
                    baseline_values,
                ),
        })

    result = pd.DataFrame(
        rows
    )

    result[
        "abs_standardized_difference"
    ] = (
        result[
            "standardized_difference"
        ]
        .abs()
    )

    return (
        result
        .sort_values(
            "abs_standardized_difference",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def regime_summary(
    frame: pd.DataFrame,
    stable_regimes: list[str],
) -> pd.DataFrame:
    rows = []

    for regime_name in (
        stable_regimes
    ):
        group = frame[
            frame["regime"]
            == regime_name
        ]

        if group.empty:
            continue

        result_counts = (
            group["result"]
            .value_counts(
                normalize=True
            )
        )

        rows.append({
            "regime":
                regime_name,

            "rows":
                len(group),

            "seasons":
                group[
                    "season"
                ].nunique(),

            "home_rate":
                float(
                    result_counts.get(
                        "H",
                        0.0,
                    )
                ),

            "draw_rate":
                float(
                    result_counts.get(
                        "D",
                        0.0,
                    )
                ),

            "away_rate":
                float(
                    result_counts.get(
                        "A",
                        0.0,
                    )
                ),

            "mean_market_confidence":
                float(
                    group[
                        "market_confidence"
                    ].mean()
                ),

            "mean_residual_magnitude":
                float(
                    group[
                        "residual_magnitude"
                    ].mean()
                ),

            "agreement_rate":
                float(
                    (
                        group[
                            "agreement"
                        ]
                        == "AGREE"
                    ).mean()
                ),
        })

    return pd.DataFrame(
        rows
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

    stable_regimes = (
        stable_regimes_from_report(
            league
        )
    )

    print("=" * 72)
    print("REGIME EXPLANATION ANALYZER")
    print("=" * 72)

    print(
        "league:",
        league,
    )

    print(
        "minimum stable folds:",
        MIN_STABLE_FOLDS,
    )

    print(
        "stable regimes:",
        len(stable_regimes),
    )

    for regime in stable_regimes:
        print(
            " ",
            regime,
        )

    if not stable_regimes:
        print(
            "No stable regimes to explain."
        )
        return 0

    frame = build_oos_with_features(
        league
    )

    explanation_frames = []

    for regime_name in (
        stable_regimes
    ):
        explanation = (
            explain_regime(
                frame,
                regime_name,
            )
        )

        explanation_frames.append(
            explanation
        )

        print()
        print("=" * 72)
        print(regime_name)
        print("=" * 72)

        print(
            explanation[
                [
                    "feature",
                    "regime_mean",
                    "baseline_mean",
                    "standardized_difference",
                ]
            ]
            .head(12)
            .to_string(
                index=False
            )
        )

    explanations = pd.concat(
        explanation_frames,
        ignore_index=True,
    )

    summary = regime_summary(
        frame,
        stable_regimes,
    )

    # Features repeatedly separating multiple stable regimes.
    repeated = (
        explanations[
            explanations[
                "abs_standardized_difference"
            ]
            >= 0.20
        ]
        .groupby(
            "feature",
            as_index=False,
        )
        .agg(
            regime_count=(
                "regime",
                "nunique",
            ),
            mean_abs_standardized_difference=(
                "abs_standardized_difference",
                "mean",
            ),
            max_abs_standardized_difference=(
                "abs_standardized_difference",
                "max",
            ),
        )
        .sort_values(
            [
                "regime_count",
                "mean_abs_standardized_difference",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .reset_index(drop=True)
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    explanations_path = (
        OUTPUT_DIR
        / f"{league.lower()}_feature_profiles.csv"
    )

    summary_path = (
        OUTPUT_DIR
        / f"{league.lower()}_regime_summary.csv"
    )

    repeated_path = (
        OUTPUT_DIR
        / f"{league.lower()}_repeated_features.csv"
    )

    report_path = (
        OUTPUT_DIR
        / f"{league.lower()}_report.json"
    )

    explanations.to_csv(
        explanations_path,
        index=False,
    )

    summary.to_csv(
        summary_path,
        index=False,
    )

    repeated.to_csv(
        repeated_path,
        index=False,
    )

    after = production_state()

    production_unchanged = (
        before == after
    )

    report = {
        "league":
            league,

        "stable_regimes":
            stable_regimes,

        "stable_regime_count":
            len(stable_regimes),

        "oos_rows":
            len(frame),

        "minimum_stable_folds":
            MIN_STABLE_FOLDS,

        "top_repeated_features":
            repeated.head(
                15
            ).to_dict(
                orient="records"
            ),

        "regime_summary":
            summary.to_dict(
                orient="records"
            ),

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
    print("REGIME SUMMARY")
    print("=" * 72)

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("=" * 72)
    print("REPEATED SEPARATING FEATURES")
    print("=" * 72)

    if repeated.empty:
        print(
            "No feature reached |SMD| >= 0.20 "
            "in stable regimes."
        )
    else:
        print(
            repeated.head(
                20
            ).to_string(
                index=False
            )
        )

    print()
    print(
        "production unchanged:",
        production_unchanged,
    )

    print(
        "next true unseen period:",
        "2026-2027",
    )

    print()
    print(
        "feature profiles:",
        explanations_path,
    )

    print(
        "regime summary:",
        summary_path,
    )

    print(
        "repeated features:",
        repeated_path,
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
