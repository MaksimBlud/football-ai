"""Selection-aware parametric null for frozen historical strategy validation.

Research only. Under the benchmark that each match outcome is drawn from the stored
no-vig market probabilities, this module repeatedly simulates full outcomes, re-runs the
EXACT frozen rule-selection procedure on the first three seasons, and evaluates the
selected rule on all later seasons. This quantifies how often training-set selection alone
can produce a frozen OOS ROI/excess at least as large as the observed result.

No rule is tuned or activated, and no production state is changed.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from historical_strategy_frozen_validation import (
    INITIAL_TRAINING_SEASONS,
    MIN_TRAINING_MATCHES,
    frozen_validation,
)
from historical_strategy_stability import add_confidence_bucket

SIDES = np.array(["H", "D", "A"], dtype=object)
PROBABILITY_COLUMNS = (
    "market_home_probability",
    "market_draw_probability",
    "market_away_probability",
)
DEFAULT_SIMULATIONS = 20000
DEFAULT_SEED = 20260901


def _validate(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "league", "season", "market_pick", "market_confidence",
        "selected_odds", "won", *PROBABILITY_COLUMNS,
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
    result = frame.copy()
    probabilities = result[list(PROBABILITY_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    valid = probabilities.notna().all(axis=1) & probabilities.ge(0.0).all(axis=1)
    sums = probabilities.sum(axis=1)
    valid &= sums.gt(0.0)
    result = result.loc[valid].copy()
    probabilities = probabilities.loc[valid].div(sums.loc[valid], axis=0)
    result.loc[:, list(PROBABILITY_COLUMNS)] = probabilities.to_numpy()
    result["selected_odds"] = pd.to_numeric(result["selected_odds"], errors="coerce")
    result = result[result["selected_odds"].gt(1.0)].copy()
    return result.reset_index(drop=True)


def _simulate_results(probabilities: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    draws = rng.random(len(probabilities))
    cumulative = probabilities.cumsum(axis=1)
    result_index = (draws[:, None] > cumulative[:, :2]).sum(axis=1)
    return SIDES[result_index]


def _with_simulated_outcomes(base: pd.DataFrame, simulated_results: np.ndarray) -> pd.DataFrame:
    result = base.copy()
    result["won"] = result["market_pick"].astype(str).to_numpy() == simulated_results
    selected_odds = result["selected_odds"].to_numpy(dtype=float)
    result["profit"] = np.where(result["won"].to_numpy(), selected_odds - 1.0, -1.0)
    return result


def _observed_summary(frame: pd.DataFrame) -> pd.DataFrame:
    summary, _ = frozen_validation(frame)
    return summary[[
        "league", "market_pick", "confidence_bucket", "test_matches",
        "test_wins", "test_profit", "test_roi",
    ]].copy()


def selection_aware_null(
    frame: pd.DataFrame,
    *,
    simulations: int = DEFAULT_SIMULATIONS,
    seed: int = DEFAULT_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if simulations <= 0:
        raise ValueError("simulations must be positive")
    prepared = _validate(frame)
    observed = _observed_summary(prepared)
    probabilities = prepared[list(PROBABILITY_COLUMNS)].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)

    simulation_rows: list[dict[str, object]] = []
    for simulation in range(simulations):
        outcomes = _simulate_results(probabilities, rng)
        simulated = _with_simulated_outcomes(prepared, outcomes)
        summary, _ = frozen_validation(simulated)
        for row in summary.itertuples(index=False):
            simulation_rows.append({
                "simulation": simulation,
                "league": row.league,
                "selected_market_pick": row.market_pick,
                "selected_confidence_bucket": row.confidence_bucket,
                "test_matches": row.test_matches,
                "test_wins": row.test_wins,
                "test_profit": row.test_profit,
                "test_roi": row.test_roi,
            })

    simulations_frame = pd.DataFrame(simulation_rows)
    rows = []
    for observed_row in observed.itertuples(index=False):
        league_sim = simulations_frame[simulations_frame["league"] == observed_row.league]
        if league_sim.empty:
            continue
        roi_tail = (league_sim["test_roi"] >= observed_row.test_roi).mean()
        profit_tail = (league_sim["test_profit"] >= observed_row.test_profit).mean()
        same_rule = (
            (league_sim["selected_market_pick"] == observed_row.market_pick)
            & (league_sim["selected_confidence_bucket"] == observed_row.confidence_bucket)
        )
        rows.append({
            "league": observed_row.league,
            "observed_market_pick": observed_row.market_pick,
            "observed_confidence_bucket": observed_row.confidence_bucket,
            "observed_test_matches": observed_row.test_matches,
            "observed_test_wins": observed_row.test_wins,
            "observed_test_profit": observed_row.test_profit,
            "observed_test_roi": observed_row.test_roi,
            "simulations": len(league_sim),
            "seed": seed,
            "null_test_roi_mean": float(league_sim["test_roi"].mean()),
            "null_test_roi_median": float(league_sim["test_roi"].median()),
            "null_test_roi_q95": float(league_sim["test_roi"].quantile(0.95)),
            "null_test_roi_q99": float(league_sim["test_roi"].quantile(0.99)),
            "selection_aware_roi_upper_tail": float(roi_tail),
            "selection_aware_profit_upper_tail": float(profit_tail),
            "same_rule_selection_share": float(same_rule.mean()),
            "initial_training_seasons": INITIAL_TRAINING_SEASONS,
            "min_training_matches": MIN_TRAINING_MATCHES,
        })

    return pd.DataFrame(rows), simulations_frame


def main() -> None:
    parser = argparse.ArgumentParser(description="Selection-aware frozen-rule market null simulation")
    parser.add_argument("prepared_matches", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/historical_strategy_selection_null"),
    )
    parser.add_argument("--simulations", type=int, default=DEFAULT_SIMULATIONS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    summary, simulation_rows = selection_aware_null(
        pd.read_csv(args.prepared_matches),
        simulations=args.simulations,
        seed=args.seed,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "selection_aware_null_summary.csv", index=False)
    simulation_rows.to_csv(args.output_dir / "selection_aware_null_simulations.csv", index=False)
    print("SELECTION-AWARE FROZEN RULE NULL — RESEARCH ONLY")
    print(summary.to_string(index=False))
    print("Each simulation redraws outcomes from no-vig market probabilities, then repeats the original frozen training selection.")
    print("This is a conditional parametric market benchmark; it does not prove match independence or production profitability.")
    print("No tuning, activation, training, Supabase writes, Structural changes, or .pkl changes performed.")


if __name__ == "__main__":
    main()
