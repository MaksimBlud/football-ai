"""Selection-aware parametric null for frozen historical strategy validation.

Research only. Under the benchmark that each market-pick success is Bernoulli with the
stored no-vig market confidence, this module repeatedly simulates outcomes, re-runs the
EXACT frozen rule-selection ranking on the first three seasons, and evaluates the selected
rule on all later seasons. Segment membership and quoted odds stay fixed; only outcomes
are redrawn. This is equivalent to full categorical simulation for this strategy because
profit depends only on whether the fixed market pick wins.

No rule is tuned or activated, and no production state is changed.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from historical_strategy_frozen_validation import (
    INITIAL_TRAINING_SEASONS,
    MIN_TRAINING_MATCHES,
    frozen_validation,
)
from historical_strategy_stability import add_confidence_bucket

DEFAULT_SIMULATIONS = 20000
DEFAULT_SEED = 20260901
DEFAULT_BATCH_SIZE = 1000


@dataclass(frozen=True)
class Candidate:
    market_pick: str
    confidence_bucket: str
    training_matches: int
    training_indices_by_season: tuple[np.ndarray, ...]
    test_indices: np.ndarray


def _validate(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "league", "season", "market_pick", "market_confidence",
        "selected_odds", "won", "profit",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
    result = frame.copy()
    result["market_confidence"] = pd.to_numeric(result["market_confidence"], errors="coerce")
    result["selected_odds"] = pd.to_numeric(result["selected_odds"], errors="coerce")
    valid = (
        result["market_confidence"].between(0.0, 1.0, inclusive="both")
        & result["selected_odds"].gt(1.0)
    )
    return result.loc[valid].reset_index(drop=True)


def _observed_summary(frame: pd.DataFrame) -> pd.DataFrame:
    summary, _ = frozen_validation(frame)
    return summary[[
        "league", "market_pick", "confidence_bucket", "test_matches",
        "test_wins", "test_profit", "test_roi",
    ]].copy()


def _league_candidates(league_frame: pd.DataFrame) -> tuple[list[Candidate], list[str], np.ndarray, np.ndarray]:
    prepared = add_confidence_bucket(league_frame).reset_index(drop=True)
    seasons = sorted(prepared["season"].astype(str).unique())
    if len(seasons) <= INITIAL_TRAINING_SEASONS:
        return [], seasons, np.array([], dtype=float), np.array([], dtype=float)
    train_seasons = seasons[:INITIAL_TRAINING_SEASONS]
    test_seasons = seasons[INITIAL_TRAINING_SEASONS:]
    season_text = prepared["season"].astype(str)
    training_mask = season_text.isin(train_seasons)
    training = prepared.loc[training_mask]

    candidates: list[Candidate] = []
    for (pick, bucket), group in training.groupby(
        ["market_pick", "confidence_bucket"], observed=True, sort=True
    ):
        if len(group) < MIN_TRAINING_MATCHES:
            continue
        full_segment = prepared[
            (prepared["market_pick"].astype(str) == str(pick))
            & (prepared["confidence_bucket"].astype(str) == str(bucket))
        ]
        training_indices_by_season = tuple(
            full_segment.index[full_segment["season"].astype(str) == season].to_numpy(dtype=int)
            for season in train_seasons
        )
        test_indices = full_segment.index[
            full_segment["season"].astype(str).isin(test_seasons)
        ].to_numpy(dtype=int)
        candidates.append(Candidate(
            market_pick=str(pick),
            confidence_bucket=str(bucket),
            training_matches=len(group),
            training_indices_by_season=training_indices_by_season,
            test_indices=test_indices,
        ))

    return (
        candidates,
        seasons,
        prepared["market_confidence"].to_numpy(dtype=float),
        prepared["selected_odds"].to_numpy(dtype=float),
    )


def _simulate_candidate_metrics(
    candidate: Candidate,
    probabilities: np.ndarray,
    odds: np.ndarray,
    *,
    simulations: int,
    rng: np.random.Generator,
    batch_size: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    train_roi = np.empty(simulations, dtype=float)
    positive_share = np.empty(simulations, dtype=float)
    test_wins = np.empty(simulations, dtype=int)
    test_profit = np.empty(simulations, dtype=float)
    test_roi = np.empty(simulations, dtype=float)

    nonempty_training_seasons = tuple(
        indices for indices in candidate.training_indices_by_season if len(indices)
    )
    all_train = np.concatenate(nonempty_training_seasons)
    test_indices = candidate.test_indices
    for start in range(0, simulations, batch_size):
        stop = min(start + batch_size, simulations)
        size = stop - start

        p_train = probabilities[all_train]
        wins_train = rng.random((size, len(all_train))) < p_train
        train_profit = (wins_train * odds[all_train]).sum(axis=1) - len(all_train)
        train_roi[start:stop] = train_profit / len(all_train)

        offset = 0
        positive = np.zeros(size, dtype=float)
        for indices in nonempty_training_seasons:
            count = len(indices)
            season_wins = wins_train[:, offset : offset + count]
            season_profit = (season_wins * odds[indices]).sum(axis=1) - count
            positive += season_profit > 0.0
            offset += count
        positive_share[start:stop] = positive / len(nonempty_training_seasons)

        if len(test_indices):
            p_test = probabilities[test_indices]
            wins_test = rng.random((size, len(test_indices))) < p_test
            wins_count = wins_test.sum(axis=1)
            profit = (wins_test * odds[test_indices]).sum(axis=1) - len(test_indices)
            test_wins[start:stop] = wins_count
            test_profit[start:stop] = profit
            test_roi[start:stop] = profit / len(test_indices)
        else:
            test_wins[start:stop] = 0
            test_profit[start:stop] = 0.0
            test_roi[start:stop] = np.nan

    return train_roi, positive_share, test_wins, test_profit, test_roi


def _candidate_tiebreak(candidate: Candidate) -> tuple[int, str, str]:
    return (-candidate.training_matches, candidate.market_pick, candidate.confidence_bucket)


def _simulate_league(
    league_frame: pd.DataFrame,
    *,
    simulations: int,
    rng: np.random.Generator,
    batch_size: int,
) -> pd.DataFrame:
    candidates, _, probabilities, odds = _league_candidates(league_frame)
    if not candidates:
        return pd.DataFrame()

    train_roi_columns = []
    positive_columns = []
    test_wins_columns = []
    test_profit_columns = []
    test_roi_columns = []
    for candidate in candidates:
        train_roi, positive, test_wins, test_profit, test_roi = _simulate_candidate_metrics(
            candidate,
            probabilities,
            odds,
            simulations=simulations,
            rng=rng,
            batch_size=batch_size,
        )
        train_roi_columns.append(train_roi)
        positive_columns.append(positive)
        test_wins_columns.append(test_wins)
        test_profit_columns.append(test_profit)
        test_roi_columns.append(test_roi)

    train_roi_matrix = np.column_stack(train_roi_columns)
    positive_matrix = np.column_stack(positive_columns)
    matches = np.array([candidate.training_matches for candidate in candidates], dtype=int)

    order = sorted(range(len(candidates)), key=lambda index: _candidate_tiebreak(candidates[index]))
    selected = np.full(simulations, order[0], dtype=int)
    best_roi = train_roi_matrix[:, order[0]].copy()
    best_positive = positive_matrix[:, order[0]].copy()
    best_matches = np.full(simulations, matches[order[0]], dtype=int)
    for index in order[1:]:
        roi = train_roi_matrix[:, index]
        positive = positive_matrix[:, index]
        candidate_matches = matches[index]
        better = (
            (roi > best_roi)
            | ((roi == best_roi) & (positive > best_positive))
            | ((roi == best_roi) & (positive == best_positive) & (candidate_matches > best_matches))
        )
        selected[better] = index
        best_roi[better] = roi[better]
        best_positive[better] = positive[better]
        best_matches[better] = candidate_matches

    test_wins_matrix = np.column_stack(test_wins_columns)
    test_profit_matrix = np.column_stack(test_profit_columns)
    test_roi_matrix = np.column_stack(test_roi_columns)
    row_index = np.arange(simulations)

    return pd.DataFrame({
        "simulation": row_index,
        "selected_market_pick": [candidates[index].market_pick for index in selected],
        "selected_confidence_bucket": [candidates[index].confidence_bucket for index in selected],
        "test_matches": [len(candidates[index].test_indices) for index in selected],
        "test_wins": test_wins_matrix[row_index, selected],
        "test_profit": test_profit_matrix[row_index, selected],
        "test_roi": test_roi_matrix[row_index, selected],
    })


def familywise_null_summary(
    observed_summary: pd.DataFrame,
    simulations_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Correct for looking across all tested leagues after within-league rule selection."""
    if observed_summary.empty or simulations_frame.empty:
        return pd.DataFrame()
    valid_observed = observed_summary.dropna(subset=["observed_test_roi"])
    if valid_observed.empty:
        return pd.DataFrame()
    observed_best = valid_observed.loc[valid_observed["observed_test_roi"].idxmax()]
    global_max = simulations_frame.groupby("simulation", sort=True)["test_roi"].max().dropna()
    exceedances = int((global_max >= observed_best["observed_test_roi"]).sum())
    return pd.DataFrame([{
        "leagues_tested": int(valid_observed["league"].nunique()),
        "observed_best_league": observed_best["league"],
        "observed_best_market_pick": observed_best["observed_market_pick"],
        "observed_best_confidence_bucket": observed_best["observed_confidence_bucket"],
        "observed_best_test_roi": float(observed_best["observed_test_roi"]),
        "simulations": len(global_max),
        "null_global_max_roi_mean": float(global_max.mean()),
        "null_global_max_roi_median": float(global_max.median()),
        "null_global_max_roi_q95": float(global_max.quantile(0.95)),
        "null_global_max_roi_q99": float(global_max.quantile(0.99)),
        "familywise_roi_exceedances": exceedances,
        "familywise_roi_upper_tail": float((exceedances + 1) / (len(global_max) + 1)),
    }])


def selection_aware_null(
    frame: pd.DataFrame,
    *,
    simulations: int = DEFAULT_SIMULATIONS,
    seed: int = DEFAULT_SEED,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if simulations <= 0:
        raise ValueError("simulations must be positive")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    prepared = _validate(frame)
    observed = _observed_summary(prepared)
    rng = np.random.default_rng(seed)

    simulation_frames = []
    for league, league_frame in prepared.groupby("league", sort=True):
        simulated = _simulate_league(
            league_frame.reset_index(drop=True),
            simulations=simulations,
            rng=rng,
            batch_size=batch_size,
        )
        if not simulated.empty:
            simulated.insert(1, "league", league)
            simulation_frames.append(simulated)
    simulations_frame = pd.concat(simulation_frames, ignore_index=True) if simulation_frames else pd.DataFrame()

    rows = []
    for observed_row in observed.itertuples(index=False):
        league_sim = simulations_frame[simulations_frame["league"] == observed_row.league]
        if league_sim.empty:
            continue
        valid_roi = league_sim["test_roi"].dropna()
        roi_exceedances = int((valid_roi >= observed_row.test_roi).sum())
        profit_exceedances = int((league_sim["test_profit"] >= observed_row.test_profit).sum())
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
            "null_test_roi_mean": float(valid_roi.mean()),
            "null_test_roi_median": float(valid_roi.median()),
            "null_test_roi_q95": float(valid_roi.quantile(0.95)),
            "null_test_roi_q99": float(valid_roi.quantile(0.99)),
            "selection_aware_roi_exceedances": roi_exceedances,
            "selection_aware_roi_upper_tail": float((roi_exceedances + 1) / (len(valid_roi) + 1)),
            "selection_aware_profit_exceedances": profit_exceedances,
            "selection_aware_profit_upper_tail": float((profit_exceedances + 1) / (len(league_sim) + 1)),
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
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    args = parser.parse_args()

    summary, simulation_rows = selection_aware_null(
        pd.read_csv(args.prepared_matches),
        simulations=args.simulations,
        seed=args.seed,
        batch_size=args.batch_size,
    )
    global_summary = familywise_null_summary(summary, simulation_rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "selection_aware_null_summary.csv", index=False)
    simulation_rows.to_csv(args.output_dir / "selection_aware_null_simulations.csv", index=False)
    global_summary.to_csv(args.output_dir / "selection_aware_global_summary.csv", index=False)
    print("SELECTION-AWARE FROZEN RULE NULL — RESEARCH ONLY")
    print(summary.to_string(index=False))
    print("FAMILY-WISE LEAGUE MAXIMUM")
    print(global_summary.to_string(index=False))
    print("Each simulation redraws fixed market-pick wins from no-vig confidence and repeats the original frozen training selection.")
    print("The family-wise row also corrects for inspecting multiple leagues and highlighting the best observed OOS ROI.")
    print("Upper-tail estimates use the finite-simulation plus-one correction; raw exceedance counts are also reported.")
    print("This is a conditional parametric market benchmark; it does not prove match independence or production profitability.")
    print("No tuning, activation, training, Supabase writes, Structural changes, or .pkl changes performed.")


if __name__ == "__main__":
    main()
