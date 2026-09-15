"""Robustness diagnostics for BOOKMAKER_RECONSTRUCTION_DEVIG_V1.

The source V1 selected POWER on 2024-2025 pooled validation and evaluated it once on
untouched 2025-2026 OOT. This module does not re-select a method. It asks whether
that already-fixed POWER-vs-PROPORTIONAL comparison is persistent across earlier
seasons and whether the final OOT improvement is distinguishable from sampling
noise under paired bootstrap resampling.

Research only. No production artifacts, Supabase writes, paid APIs, betting, or
2026-2027 outcomes are used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from bookmaker_reconstruction_devig_v1 import (
    TEST_SEASON,
    VALIDATION_SEASON,
    probabilities,
    raw_market_frame,
)
from historical_football_signal_lab import RESULT_TO_INT
from historical_football_signal_runner import BASE, LEAGUES
from market_anchor_1x2_v1 import score_probabilities

EXPERIMENT_ID = "BOOKMAKER_RECONSTRUCTION_DEVIG_V1_ROBUSTNESS"
SOURCE_EXPERIMENT_ID = "BOOKMAKER_RECONSTRUCTION_DEVIG_V1"
BASELINE_METHOD = "PROPORTIONAL"
CANDIDATE_METHOD = "POWER"
PRIOR_SEASONS = tuple(f"{year}-{year + 1}" for year in range(2016, 2024))
ALL_ALLOWED_SEASONS = PRIOR_SEASONS + (VALIDATION_SEASON, TEST_SEASON)
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260915
EPS = 1e-12


def load_all_history(raw_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    allowed = set(ALL_ALLOWED_SEASONS)
    for league, config in LEAGUES.items():
        league_dir = raw_dir / league.lower()
        league_dir.mkdir(parents=True, exist_ok=True)
        for code, season in config.historical_source.season_codes.items():
            if season not in allowed:
                continue
            url = BASE.format(code=code, comp=config.historical_source.competition_code)
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            path = league_dir / f"{league.lower()}_{code}.csv"
            path.write_bytes(response.content)
            frames.append(raw_market_frame(pd.read_csv(path), league, season))
    if not frames:
        raise RuntimeError("no allowed historical market rows were loaded")
    frame = pd.concat(frames, ignore_index=True)
    observed = set(frame["season"].unique())
    missing = set(ALL_ALLOWED_SEASONS) - observed
    if missing:
        raise RuntimeError(f"missing required robustness seasons: {sorted(missing)}")
    return frame


def _metrics(frame: pd.DataFrame, method: str) -> dict[str, float]:
    y = frame["result"].map(RESULT_TO_INT).to_numpy(dtype=int)
    p = probabilities(frame, method)
    return score_probabilities(y, p)


def metric_deltas(frame: pd.DataFrame) -> dict[str, float | bool]:
    baseline = _metrics(frame, BASELINE_METHOD)
    candidate = _metrics(frame, CANDIDATE_METHOD)
    delta_brier = candidate["brier"] - baseline["brier"]
    delta_log_loss = candidate["log_loss"] - baseline["log_loss"]
    return {
        "matches": int(len(frame)),
        "baseline_brier": baseline["brier"],
        "candidate_brier": candidate["brier"],
        "delta_brier": float(delta_brier),
        "baseline_log_loss": baseline["log_loss"],
        "candidate_log_loss": candidate["log_loss"],
        "delta_log_loss": float(delta_log_loss),
        "dual_metric_win": bool(delta_brier < 0.0 and delta_log_loss < 0.0),
    }


def paired_loss_deltas(frame: pd.DataFrame) -> dict[str, np.ndarray]:
    y = frame["result"].map(RESULT_TO_INT).to_numpy(dtype=int)
    baseline = probabilities(frame, BASELINE_METHOD)
    candidate = probabilities(frame, CANDIDATE_METHOD)
    onehot = np.eye(3)[y]
    baseline_brier = np.sum((baseline - onehot) ** 2, axis=1)
    candidate_brier = np.sum((candidate - onehot) ** 2, axis=1)
    rows = np.arange(len(y))
    baseline_log_loss = -np.log(np.clip(baseline[rows, y], EPS, 1.0))
    candidate_log_loss = -np.log(np.clip(candidate[rows, y], EPS, 1.0))
    return {
        "brier": candidate_brier - baseline_brier,
        "log_loss": candidate_log_loss - baseline_log_loss,
    }


def paired_bootstrap(
    deltas: np.ndarray,
    *,
    reps: int = BOOTSTRAP_REPS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, float | int]:
    values = np.asarray(deltas, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("paired bootstrap requires a non-empty finite 1D delta array")
    if reps <= 0:
        raise ValueError("bootstrap reps must be positive")
    rng = np.random.default_rng(seed)
    means = np.empty(reps, dtype=float)
    n = len(values)
    for i in range(reps):
        means[i] = float(values[rng.integers(0, n, size=n)].mean())
    low, high = np.quantile(means, [0.025, 0.975])
    return {
        "n": int(n),
        "reps": int(reps),
        "seed": int(seed),
        "observed_delta": float(values.mean()),
        "bootstrap_ci95_low": float(low),
        "bootstrap_ci95_high": float(high),
        "bootstrap_probability_better_than_proportional": float(np.mean(means < 0.0)),
    }


def _bootstrap_frame(frame: pd.DataFrame, seed_offset: int = 0) -> dict[str, dict[str, float | int]]:
    deltas = paired_loss_deltas(frame)
    return {
        metric: paired_bootstrap(values, seed=BOOTSTRAP_SEED + seed_offset + i)
        for i, (metric, values) in enumerate(deltas.items())
    }


def evaluate_frame(frame: pd.DataFrame) -> dict:
    clean = frame[
        frame["result"].isin(RESULT_TO_INT)
        & frame["season"].isin(ALL_ALLOWED_SEASONS)
    ].copy()
    if clean.empty:
        raise RuntimeError("empty robustness frame")

    pooled_by_season = []
    for season in ALL_ALLOWED_SEASONS:
        group = clean[clean["season"] == season]
        if group.empty:
            raise RuntimeError(f"no rows for required season {season}")
        pooled_by_season.append({"season": season, **metric_deltas(group)})

    league_season = []
    for league, league_frame in clean.groupby("league"):
        for season in ALL_ALLOWED_SEASONS:
            group = league_frame[league_frame["season"] == season]
            if group.empty:
                raise RuntimeError(f"{league}: no rows for required season {season}")
            league_season.append({"league": league, "season": season, **metric_deltas(group)})

    prior_pooled = [row for row in pooled_by_season if row["season"] in PRIOR_SEASONS]
    prior_league = [row for row in league_season if row["season"] in PRIOR_SEASONS]
    validation = clean[clean["season"] == VALIDATION_SEASON]
    final_oot = clean[clean["season"] == TEST_SEASON]

    league_bootstrap = {}
    for index, (league, group) in enumerate(final_oot.groupby("league"), start=1):
        league_bootstrap[str(league)] = _bootstrap_frame(group, seed_offset=index * 100)

    return {
        "experiment_id": EXPERIMENT_ID,
        "source_experiment_id": SOURCE_EXPERIMENT_ID,
        "evidence_class": "POST_SELECTION_ROBUSTNESS_DIAGNOSTIC",
        "research_only": True,
        "production_promotion": False,
        "betting_enabled": False,
        "result": "NO_BET",
        "opened_2026_27_outcomes_used": False,
        "baseline_method": BASELINE_METHOD,
        "fixed_candidate_method": CANDIDATE_METHOD,
        "candidate_reselected_in_robustness": False,
        "source_selection_season": VALIDATION_SEASON,
        "source_untouched_test_season": TEST_SEASON,
        "retrospective_prior_seasons": len(PRIOR_SEASONS),
        "prior_seasons": list(PRIOR_SEASONS),
        "prior_pooled_dual_metric_wins": int(sum(bool(row["dual_metric_win"]) for row in prior_pooled)),
        "prior_league_season_dual_metric_wins": int(sum(bool(row["dual_metric_win"]) for row in prior_league)),
        "prior_league_season_comparisons": int(len(prior_league)),
        "pooled_by_season": pooled_by_season,
        "league_season": league_season,
        "source_validation_replay": metric_deltas(validation),
        "final_oot_replay": metric_deltas(final_oot),
        "final_oot_paired_bootstrap": _bootstrap_frame(final_oot),
        "final_oot_league_paired_bootstrap": league_bootstrap,
        "interpretation_contract": (
            "robustness is diagnostic only; it cannot mutate BOOKMAKER_RECONSTRUCTION_DEVIG_V1, "
            "MARKET_ANCHOR_1X2_V2, or production inference"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("artifacts/bookmaker_reconstruction_devig_v1_robustness/work"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/bookmaker_reconstruction_devig_v1_robustness/report.json"),
    )
    args = parser.parse_args()
    report = evaluate_frame(load_all_history(args.work_dir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
