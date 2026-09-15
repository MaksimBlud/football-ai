"""Full-coverage final-season diagnostic: Football-Data AVG vs B365.

BOOKMAKER_RECONSTRUCTION_CONSENSUS_V1 showed that PS coverage truncates in the
second half of 2025-2026, while B365 and AVG both cover the full three-league
2025-2026 cohort. This module fixes the comparison to B365 vs AVG with proportional
de-vigging, audits how far back AVG is actually available, and measures persistence
only on same-fixture historical cohorts where both sources exist.

This is a post-outcome diagnostic, not a new untouched OOT experiment. No source is
selected from these results and no production behavior may be changed from it.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from bookmaker_reconstruction_consensus_v1 import fair_probabilities, raw_source_frame, source_available
from historical_football_signal_lab import RESULT_TO_INT
from historical_football_signal_runner import BASE, LEAGUES
from market_anchor_1x2_v1 import score_probabilities

EXPERIMENT_ID = "BOOKMAKER_RECONSTRUCTION_FULL_COVERAGE_V1"
BASELINE_SOURCE = "B365"
CANDIDATE_SOURCE = "AVG"
SEASONS = tuple(f"{year}-{year + 1}" for year in range(2016, 2026))
FINAL_SEASON = "2025-2026"
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260915
EPS = 1e-12


def load_history(raw_dir: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    allowed = set(SEASONS)
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
            frames.append(raw_source_frame(pd.read_csv(path), league, season))
    if not frames:
        raise RuntimeError("no historical rows loaded")
    frame = pd.concat(frames, ignore_index=True)
    missing = set(SEASONS) - set(frame["season"].unique())
    if missing:
        raise RuntimeError(f"missing required seasons: {sorted(missing)}")
    return frame


def pair_mask(frame: pd.DataFrame) -> pd.Series:
    return source_available(frame, BASELINE_SOURCE) & source_available(frame, CANDIDATE_SOURCE)


def _score(frame: pd.DataFrame, source: str) -> dict[str, float]:
    y = frame["result"].map(RESULT_TO_INT).to_numpy(dtype=int)
    return score_probabilities(y, fair_probabilities(frame, source))


def metric_deltas(frame: pd.DataFrame) -> dict[str, float | int | bool]:
    if frame.empty:
        raise ValueError("metric comparison requires at least one paired row")
    baseline = _score(frame, BASELINE_SOURCE)
    candidate = _score(frame, CANDIDATE_SOURCE)
    delta_brier = float(candidate["brier"] - baseline["brier"])
    delta_log_loss = float(candidate["log_loss"] - baseline["log_loss"])
    return {
        "matches": int(len(frame)),
        "baseline_brier": baseline["brier"],
        "candidate_brier": candidate["brier"],
        "delta_brier": delta_brier,
        "baseline_log_loss": baseline["log_loss"],
        "candidate_log_loss": candidate["log_loss"],
        "delta_log_loss": delta_log_loss,
        "baseline_accuracy": baseline["accuracy"],
        "candidate_accuracy": candidate["accuracy"],
        "dual_metric_win": bool(delta_brier < 0.0 and delta_log_loss < 0.0),
    }


def paired_loss_deltas(frame: pd.DataFrame) -> dict[str, np.ndarray]:
    y = frame["result"].map(RESULT_TO_INT).to_numpy(dtype=int)
    baseline = fair_probabilities(frame, BASELINE_SOURCE)
    candidate = fair_probabilities(frame, CANDIDATE_SOURCE)
    onehot = np.eye(3)[y]
    baseline_brier = np.sum((baseline - onehot) ** 2, axis=1)
    candidate_brier = np.sum((candidate - onehot) ** 2, axis=1)
    rows = np.arange(len(y))
    baseline_log = -np.log(np.clip(baseline[rows, y], EPS, 1.0))
    candidate_log = -np.log(np.clip(candidate[rows, y], EPS, 1.0))
    return {
        "brier": candidate_brier - baseline_brier,
        "log_loss": candidate_log - baseline_log,
    }


def paired_bootstrap(deltas: np.ndarray, *, reps: int = BOOTSTRAP_REPS, seed: int = BOOTSTRAP_SEED) -> dict[str, float | int]:
    values = np.asarray(deltas, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError("paired bootstrap requires finite non-empty 1D deltas")
    if reps <= 0:
        raise ValueError("bootstrap reps must be positive")
    rng = np.random.default_rng(seed)
    n = len(values)
    means = np.empty(reps, dtype=float)
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
        "bootstrap_probability_avg_better_than_b365": float(np.mean(means < 0.0)),
    }


def _bootstrap(frame: pd.DataFrame, seed_offset: int = 0) -> dict[str, dict[str, float | int]]:
    return {
        metric: paired_bootstrap(values, seed=BOOTSTRAP_SEED + seed_offset + i)
        for i, (metric, values) in enumerate(paired_loss_deltas(frame).items())
    }


def _coverage(frame: pd.DataFrame) -> dict[str, object]:
    total = int(len(frame))
    baseline = int(source_available(frame, BASELINE_SOURCE).sum())
    candidate = int(source_available(frame, CANDIDATE_SOURCE).sum())
    common = int(pair_mask(frame).sum())
    return {
        "total_matches": total,
        "B365_available": baseline,
        "AVG_available": candidate,
        "pair_available": common,
        "pair_fraction": float(common / total) if total else 0.0,
        "pair_full_coverage": bool(total > 0 and common == total),
    }


def _diagnostic_row(group: pd.DataFrame, **identity: object) -> dict[str, object]:
    paired = group.loc[pair_mask(group)]
    coverage = _coverage(group)
    if paired.empty:
        return {**identity, "status": "NO_PAIR_COVERAGE", **coverage}
    return {
        **identity,
        "status": "FULL_PAIR_COVERAGE" if coverage["pair_full_coverage"] else "PARTIAL_PAIR_COVERAGE",
        **coverage,
        **metric_deltas(paired),
    }


def evaluate_frame(frame: pd.DataFrame) -> dict:
    finished = frame[frame["result"].isin(RESULT_TO_INT) & frame["season"].isin(SEASONS)].copy()
    if finished.empty:
        raise RuntimeError("no finished historical rows")

    pooled_by_season = []
    for season in SEASONS:
        all_season = finished[finished["season"] == season]
        if all_season.empty:
            raise RuntimeError(f"missing raw season {season}")
        pooled_by_season.append(_diagnostic_row(all_season, season=season))

    league_season = []
    for league, league_frame in finished.groupby("league"):
        for season in SEASONS:
            group = league_frame[league_frame["season"] == season]
            if group.empty:
                raise RuntimeError(f"{league}: missing raw season {season}")
            league_season.append(_diagnostic_row(group, league=str(league), season=season))

    paired = finished.loc[pair_mask(finished)].copy()
    if paired.empty:
        raise RuntimeError("no B365/AVG paired rows in historical range")

    full_final = finished[finished["season"] == FINAL_SEASON]
    final = full_final.loc[pair_mask(full_final)]
    if len(final) != len(full_final) or len(final) == 0:
        raise RuntimeError(
            f"{FINAL_SEASON} must have full B365/AVG pair coverage: paired={len(final)} total={len(full_final)}"
        )

    final_league_bootstrap = {
        str(league): _bootstrap(group, seed_offset=(index + 1) * 100)
        for index, (league, group) in enumerate(final.groupby("league"))
    }
    available_seasons = [row for row in pooled_by_season if row["status"] != "NO_PAIR_COVERAGE"]
    full_coverage_seasons = [row for row in pooled_by_season if row["status"] == "FULL_PAIR_COVERAGE"]
    available_league_seasons = [row for row in league_season if row["status"] != "NO_PAIR_COVERAGE"]

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "POST_OUTCOME_FULL_COVERAGE_DIAGNOSTIC",
        "research_only": True,
        "production_promotion": False,
        "betting_enabled": False,
        "result": "NO_BET",
        "opened_2026_27_outcomes_used": False,
        "baseline_source": BASELINE_SOURCE,
        "fixed_candidate_source": CANDIDATE_SOURCE,
        "devig_method_fixed": "PROPORTIONAL",
        "candidate_selected_from_outcomes": False,
        "candidate_rationale": "AVG is the full-2025-2026-coverage multi-book aggregate source identified by the coverage audit; no outcome-based source selection is performed here",
        "requested_historical_seasons": list(SEASONS),
        "historical_coverage_is_measured_not_assumed": True,
        "available_pair_seasons": [str(row["season"]) for row in available_seasons],
        "full_pair_coverage_seasons": [str(row["season"]) for row in full_coverage_seasons],
        "all_available_pair_rows": int(len(paired)),
        "pooled_all_available_pairs": metric_deltas(paired),
        "pooled_by_season": pooled_by_season,
        "league_season": league_season,
        "available_pooled_season_comparisons": int(len(available_seasons)),
        "pooled_season_dual_metric_wins": int(sum(bool(row.get("dual_metric_win", False)) for row in available_seasons)),
        "available_league_season_comparisons": int(len(available_league_seasons)),
        "league_season_dual_metric_wins": int(sum(bool(row.get("dual_metric_win", False)) for row in available_league_seasons)),
        "final_season": FINAL_SEASON,
        "final_season_full_pair_coverage": True,
        "final_season_metrics": metric_deltas(final),
        "final_season_paired_bootstrap": _bootstrap(final),
        "final_season_league_paired_bootstrap": final_league_bootstrap,
        "interpretation_contract": (
            "post-outcome diagnostic only; historical AVG coverage is reported rather than synthesized or assumed; results may motivate a separately frozen prospective market-baseline contract but cannot mutate existing market anchors or production inference"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/bookmaker_reconstruction_full_coverage_v1/work"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/bookmaker_reconstruction_full_coverage_v1/report.json"))
    args = parser.parse_args()
    report = evaluate_frame(load_history(args.work_dir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
