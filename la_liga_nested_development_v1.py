"""Preregistered La Liga historical development protocol v1.

This is research-only model development. It deliberately does NOT treat the
already-observed 2025-2026 season as a fresh holdout. All model selection,
alpha selection, and outer walk-forward evaluation are restricted to seasons
strictly before 2025-2026.

The candidate space is intentionally limited to the feature/model variants
already present in league_model_sweep.py and the alpha grid already present in
the pre-existing hybrid diagnostic. The script writes reports only: no model
artifact, no calibrator, no production promotion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from league_model_sweep import (
    FEATURE_SETS,
    INPUTS,
    MODEL_VARIANTS,
    TARGET_MAP,
    make_model,
    market_probabilities,
    metrics,
    production_state,
)


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "experiments" / "la_liga_nested_development_v1"

LEAGUE = "LA_LIGA"
OBSERVED_HOLDOUT_SEASON = "2025-2026"

# These seasons are the complete pre-observed-holdout development universe
# for model-selection OOS predictions. Each season is always predicted by a
# model fitted only on earlier seasons.
OOS_DEVELOPMENT_SEASONS = (
    "2020-2021",
    "2021-2022",
    "2022-2023",
    "2023-2024",
    "2024-2025",
)

# Nested outer checks start only after two earlier OOS seasons exist for inner
# selection. This yields three chronological outer checks.
OUTER_TEST_SEASONS = (
    "2022-2023",
    "2023-2024",
    "2024-2025",
)

# Reuse the pre-existing diagnostic grid; do not expand it after seeing the
# 2025-2026 result.
ALPHAS = (
    0.05,
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
)

MIN_METRIC_WIN_FOLDS = 2
MIN_ALL_THREE_WIN_FOLDS = 2


def _as_float(value: object) -> float:
    return float(value)


def prepare_development_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Return pre-2025-2026 rows and prove later seasons cannot enter."""

    data = frame.copy()
    data["season"] = data["season"].astype(str)

    later = sorted(
        data.loc[
            data["season"] > OBSERVED_HOLDOUT_SEASON,
            "season",
        ].unique().tolist()
    )
    if later:
        raise ValueError(
            "Future/post-boundary seasons are forbidden in development v1: "
            + ", ".join(later)
        )

    excluded_rows = int(
        (data["season"] == OBSERVED_HOLDOUT_SEASON).sum()
    )
    if excluded_rows <= 0:
        raise ValueError(
            f"Expected observed holdout season {OBSERVED_HOLDOUT_SEASON} "
            "so its explicit exclusion can be proven"
        )

    data = data[
        data["season"] < OBSERVED_HOLDOUT_SEASON
    ].copy()

    present = set(data["season"].unique().tolist())
    missing = [
        season
        for season in OOS_DEVELOPMENT_SEASONS
        if season not in present
    ]
    if missing:
        raise ValueError(
            "Missing required development seasons: " + ", ".join(missing)
        )

    data["target"] = data["result"].map(TARGET_MAP)
    return data, excluded_rows


def inner_seasons_for_outer(outer_season: str) -> tuple[str, ...]:
    if outer_season not in OUTER_TEST_SEASONS:
        raise ValueError(f"Unsupported outer season: {outer_season}")

    seasons = tuple(
        season
        for season in OOS_DEVELOPMENT_SEASONS
        if season < outer_season
    )
    if len(seasons) < 2:
        raise ValueError(
            f"Outer season {outer_season} has fewer than two inner OOS seasons"
        )
    return seasons


def hybrid_probability(
    market_probability: np.ndarray,
    ai_probability: np.ndarray,
    alpha: float,
) -> np.ndarray:
    result = (
        (1.0 - float(alpha)) * market_probability
        + float(alpha) * ai_probability
    )
    return result / result.sum(axis=1, keepdims=True)


def build_variant_oos_predictions(
    frame: pd.DataFrame,
    *,
    feature_set_name: str,
    model_name: str,
) -> pd.DataFrame:
    """Build chronological OOS predictions once for a candidate variant."""

    features = FEATURE_SETS[feature_set_name]
    rows: list[pd.DataFrame] = []

    for season in OOS_DEVELOPMENT_SEASONS:
        train = frame[
            frame["season"].astype(str) < season
        ].copy()
        test = frame[
            frame["season"].astype(str) == season
        ].copy()

        required = features + [
            "target",
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
        train = train.dropna(subset=required)
        test = test.dropna(subset=required)

        if train.empty or test.empty:
            raise ValueError(
                f"Empty train/test fold for {feature_set_name}/{model_name}/{season}"
            )

        model = make_model(model_name)
        model.fit(
            train[features],
            train["target"].astype(int),
        )

        ai = model.predict_proba(test[features])
        market = market_probabilities(test)
        target = test["target"].astype(int).to_numpy()

        fold = pd.DataFrame(
            {
                "season": season,
                "target": target,
                "ai_home_probability": ai[:, 0],
                "ai_draw_probability": ai[:, 1],
                "ai_away_probability": ai[:, 2],
                "market_home_probability": market[:, 0],
                "market_draw_probability": market[:, 1],
                "market_away_probability": market[:, 2],
            }
        )
        rows.append(fold)

    return pd.concat(rows, ignore_index=True)


def prediction_arrays(predictions: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y = predictions["target"].astype(int).to_numpy()
    ai = predictions[
        [
            "ai_home_probability",
            "ai_draw_probability",
            "ai_away_probability",
        ]
    ].to_numpy(dtype=float)
    market = predictions[
        [
            "market_home_probability",
            "market_draw_probability",
            "market_away_probability",
        ]
    ].to_numpy(dtype=float)
    return y, ai, market


def variant_leaderboard(
    predictions_by_variant: dict[tuple[str, str], pd.DataFrame],
    seasons: Iterable[str],
) -> pd.DataFrame:
    season_set = set(seasons)
    rows = []

    for (feature_set_name, model_name), predictions in predictions_by_variant.items():
        selected = predictions[
            predictions["season"].isin(season_set)
        ]
        y, ai, _ = prediction_arrays(selected)
        score = metrics(y, ai)
        rows.append(
            {
                "feature_set": feature_set_name,
                "model": model_name,
                "rows": int(len(selected)),
                **score,
            }
        )

    leaderboard = pd.DataFrame(rows).sort_values(
        ["logloss", "brier", "accuracy"],
        ascending=[True, True, False],
    ).reset_index(drop=True)
    leaderboard.insert(0, "rank", np.arange(1, len(leaderboard) + 1))
    return leaderboard


def alpha_leaderboard(
    predictions: pd.DataFrame,
    seasons: Iterable[str],
) -> pd.DataFrame:
    season_set = set(seasons)
    selected = predictions[
        predictions["season"].isin(season_set)
    ]
    y, ai, market = prediction_arrays(selected)
    market_score = metrics(y, market)

    rows = []
    for alpha in ALPHAS:
        hybrid = hybrid_probability(market, ai, alpha)
        score = metrics(y, hybrid)
        rows.append(
            {
                "alpha": float(alpha),
                "rows": int(len(selected)),
                "accuracy": score["accuracy"],
                "logloss": score["logloss"],
                "brier": score["brier"],
                "market_accuracy": market_score["accuracy"],
                "market_logloss": market_score["logloss"],
                "market_brier": market_score["brier"],
                "beats_market_accuracy": score["accuracy"] > market_score["accuracy"],
                "beats_market_logloss": score["logloss"] < market_score["logloss"],
                "beats_market_brier": score["brier"] < market_score["brier"],
            }
        )

    leaderboard = pd.DataFrame(rows).sort_values(
        ["logloss", "brier", "accuracy", "alpha"],
        ascending=[True, True, False, True],
    ).reset_index(drop=True)
    leaderboard.insert(0, "rank", np.arange(1, len(leaderboard) + 1))
    return leaderboard


def score_outer_fold(
    predictions: pd.DataFrame,
    *,
    season: str,
    alpha: float,
) -> tuple[dict, np.ndarray, np.ndarray, np.ndarray]:
    fold = predictions[predictions["season"] == season]
    y, ai, market = prediction_arrays(fold)
    hybrid = hybrid_probability(market, ai, alpha)

    ai_score = metrics(y, ai)
    market_score = metrics(y, market)
    hybrid_score = metrics(y, hybrid)

    beats = {
        "accuracy": hybrid_score["accuracy"] > market_score["accuracy"],
        "logloss": hybrid_score["logloss"] < market_score["logloss"],
        "brier": hybrid_score["brier"] < market_score["brier"],
    }

    result = {
        "season": season,
        "rows": int(len(fold)),
        "alpha": float(alpha),
        "ai": ai_score,
        "market": market_score,
        "hybrid": hybrid_score,
        "accuracy_gap": hybrid_score["accuracy"] - market_score["accuracy"],
        "logloss_gap": hybrid_score["logloss"] - market_score["logloss"],
        "brier_gap": hybrid_score["brier"] - market_score["brier"],
        "beats_market_accuracy": beats["accuracy"],
        "beats_market_logloss": beats["logloss"],
        "beats_market_brier": beats["brier"],
        "beats_market_all_three": all(beats.values()),
    }
    return result, y, market, hybrid


def development_gate(
    outer_rows: list[dict],
    *,
    aggregate_market: dict,
    aggregate_hybrid: dict,
    final_selection_beats_market_all_three: bool,
) -> dict:
    metric_fold_wins = {
        "accuracy": sum(bool(row["beats_market_accuracy"]) for row in outer_rows),
        "logloss": sum(bool(row["beats_market_logloss"]) for row in outer_rows),
        "brier": sum(bool(row["beats_market_brier"]) for row in outer_rows),
    }
    all_three_fold_wins = sum(
        bool(row["beats_market_all_three"])
        for row in outer_rows
    )

    aggregate_beats = {
        "accuracy": aggregate_hybrid["accuracy"] > aggregate_market["accuracy"],
        "logloss": aggregate_hybrid["logloss"] < aggregate_market["logloss"],
        "brier": aggregate_hybrid["brier"] < aggregate_market["brier"],
    }

    passed = all(
        [
            all(aggregate_beats.values()),
            all(
                wins >= MIN_METRIC_WIN_FOLDS
                for wins in metric_fold_wins.values()
            ),
            all_three_fold_wins >= MIN_ALL_THREE_WIN_FOLDS,
            bool(final_selection_beats_market_all_three),
        ]
    )

    return {
        "aggregate_beats_market_accuracy": aggregate_beats["accuracy"],
        "aggregate_beats_market_logloss": aggregate_beats["logloss"],
        "aggregate_beats_market_brier": aggregate_beats["brier"],
        "metric_fold_wins": metric_fold_wins,
        "minimum_metric_fold_wins_required": MIN_METRIC_WIN_FOLDS,
        "all_three_fold_wins": int(all_three_fold_wins),
        "minimum_all_three_fold_wins_required": MIN_ALL_THREE_WIN_FOLDS,
        "final_selection_beats_market_all_three": bool(
            final_selection_beats_market_all_three
        ),
        "passed": bool(passed),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--league", choices=[LEAGUE], default=LEAGUE)
    args = parser.parse_args()

    before = production_state()

    frame_raw = pd.read_csv(INPUTS[args.league])
    frame, excluded_rows = prepare_development_frame(frame_raw)

    predictions_by_variant: dict[tuple[str, str], pd.DataFrame] = {}
    for feature_set_name in FEATURE_SETS:
        for model_name in MODEL_VARIANTS:
            predictions_by_variant[(feature_set_name, model_name)] = (
                build_variant_oos_predictions(
                    frame,
                    feature_set_name=feature_set_name,
                    model_name=model_name,
                )
            )

    outer_rows: list[dict] = []
    outer_targets: list[np.ndarray] = []
    outer_markets: list[np.ndarray] = []
    outer_hybrids: list[np.ndarray] = []

    for outer_season in OUTER_TEST_SEASONS:
        inner_seasons = inner_seasons_for_outer(outer_season)
        model_table = variant_leaderboard(predictions_by_variant, inner_seasons)
        winner = model_table.iloc[0]
        key = (str(winner["feature_set"]), str(winner["model"]))

        alpha_table = alpha_leaderboard(
            predictions_by_variant[key],
            inner_seasons,
        )
        alpha = _as_float(alpha_table.iloc[0]["alpha"])

        fold_result, y, market, hybrid = score_outer_fold(
            predictions_by_variant[key],
            season=outer_season,
            alpha=alpha,
        )
        fold_result.update(
            {
                "inner_seasons": list(inner_seasons),
                "selected_feature_set": key[0],
                "selected_model": key[1],
                "inner_model_rank_logloss": _as_float(winner["logloss"]),
                "inner_model_rank_brier": _as_float(winner["brier"]),
                "inner_model_rank_accuracy": _as_float(winner["accuracy"]),
            }
        )
        outer_rows.append(fold_result)
        outer_targets.append(y)
        outer_markets.append(market)
        outer_hybrids.append(hybrid)

    y_outer = np.concatenate(outer_targets)
    market_outer = np.vstack(outer_markets)
    hybrid_outer = np.vstack(outer_hybrids)
    aggregate_market = metrics(y_outer, market_outer)
    aggregate_hybrid = metrics(y_outer, hybrid_outer)

    # If the nested robustness gate passes, this is the one recipe that would
    # be carried into a separate future-only freeze step. It is selected using
    # only pre-2025-2026 OOS development predictions.
    final_model_table = variant_leaderboard(
        predictions_by_variant,
        OOS_DEVELOPMENT_SEASONS,
    )
    final_model = final_model_table.iloc[0]
    final_key = (
        str(final_model["feature_set"]),
        str(final_model["model"]),
    )
    final_alpha_table = alpha_leaderboard(
        predictions_by_variant[final_key],
        OOS_DEVELOPMENT_SEASONS,
    )
    final_alpha_row = final_alpha_table.iloc[0]
    final_selection_beats_market_all_three = all(
        bool(final_alpha_row[column])
        for column in (
            "beats_market_accuracy",
            "beats_market_logloss",
            "beats_market_brier",
        )
    )

    gate = development_gate(
        outer_rows,
        aggregate_market=aggregate_market,
        aggregate_hybrid=aggregate_hybrid,
        final_selection_beats_market_all_three=(
            final_selection_beats_market_all_three
        ),
    )

    after = production_state()
    production_unchanged = before == after
    if not production_unchanged:
        raise RuntimeError("Production artifact state changed during research")

    status = (
        "ELIGIBLE_FOR_FUTURE_PROTOCOL_FREEZE"
        if gate["passed"]
        else "REJECTED_NO_FREEZE_RECOMMENDATION"
    )

    report = {
        "status": status,
        "league": args.league,
        "research_only": True,
        "candidate_model_saved": False,
        "promotion_performed": False,
        "paid_provider_requests": 0,
        "supabase_writes": 0,
        "observed_holdout_season": OBSERVED_HOLDOUT_SEASON,
        "observed_holdout_rows_excluded": excluded_rows,
        "observed_holdout_used_for_training_selection_or_evaluation": False,
        "development_max_season": max(OOS_DEVELOPMENT_SEASONS),
        "candidate_feature_sets": list(FEATURE_SETS.keys()),
        "candidate_models": list(MODEL_VARIANTS.keys()),
        "candidate_variant_count": len(FEATURE_SETS) * len(MODEL_VARIANTS),
        "alpha_grid": list(ALPHAS),
        "oos_development_seasons": list(OOS_DEVELOPMENT_SEASONS),
        "outer_test_seasons": list(OUTER_TEST_SEASONS),
        "outer_folds": outer_rows,
        "aggregate_outer": {
            "market": aggregate_market,
            "hybrid": aggregate_hybrid,
        },
        "final_development_selection": {
            "feature_set": final_key[0],
            "model": final_key[1],
            "alpha": _as_float(final_alpha_row["alpha"]),
            "hybrid_accuracy": _as_float(final_alpha_row["accuracy"]),
            "hybrid_logloss": _as_float(final_alpha_row["logloss"]),
            "hybrid_brier": _as_float(final_alpha_row["brier"]),
            "market_accuracy": _as_float(final_alpha_row["market_accuracy"]),
            "market_logloss": _as_float(final_alpha_row["market_logloss"]),
            "market_brier": _as_float(final_alpha_row["market_brier"]),
            "beats_market_all_three": bool(
                final_selection_beats_market_all_three
            ),
        },
        "development_gate": gate,
        "production_unchanged": production_unchanged,
        "production_state_before": before,
        "production_state_after": after,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    pd.DataFrame(outer_rows).to_csv(
        OUTPUT_DIR / "outer_folds.csv",
        index=False,
    )
    final_model_table.to_csv(
        OUTPUT_DIR / "final_model_selection.csv",
        index=False,
    )
    final_alpha_table.to_csv(
        OUTPUT_DIR / "final_alpha_selection.csv",
        index=False,
    )

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
