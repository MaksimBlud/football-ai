"""Uncertainty diagnostics for frozen historical strategy results.

Research only. Consumes frozen-rule season-level OOS results and reports deterministic
season-block bootstrap confidence intervals plus leave-one-season-out sensitivity.
It does not select or tune rules and never changes production state.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_BOOTSTRAP_SAMPLES = 50000
DEFAULT_SEED = 20260901


def _validate(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"league", "season", "matches", "wins", "profit", "roi"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
    result = frame.copy()
    for column in ("matches", "wins", "profit", "roi"):
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result = result.dropna(subset=["league", "season", "matches", "profit"])
    result = result[result["matches"] > 0].copy()
    if (result["matches"] <= 0).any():
        raise ValueError("matches must be positive")
    return result


def _bootstrap_roi(
    seasons: pd.DataFrame,
    *,
    samples: int,
    seed: int,
) -> np.ndarray:
    if samples <= 0:
        raise ValueError("samples must be positive")
    n = len(seasons)
    if n == 0:
        return np.array([], dtype=float)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, n, size=(samples, n))
    matches = seasons["matches"].to_numpy(dtype=float)[indices].sum(axis=1)
    profit = seasons["profit"].to_numpy(dtype=float)[indices].sum(axis=1)
    return profit / matches


def _leave_one_out(seasons: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dropped in seasons["season"].astype(str):
        kept = seasons[seasons["season"].astype(str) != dropped]
        matches = int(kept["matches"].sum())
        profit = float(kept["profit"].sum())
        rows.append({
            "dropped_season": dropped,
            "remaining_seasons": len(kept),
            "matches": matches,
            "profit": profit,
            "roi": profit / matches if matches else float("nan"),
        })
    return pd.DataFrame(rows)


def uncertainty_report(
    frame: pd.DataFrame,
    *,
    samples: int = DEFAULT_BOOTSTRAP_SAMPLES,
    seed: int = DEFAULT_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prepared = _validate(frame)
    summary_rows = []
    loo_rows = []

    for league, group in prepared.groupby("league", sort=True):
        group = group.sort_values("season", kind="stable").reset_index(drop=True)
        total_matches = int(group["matches"].sum())
        total_wins = int(group["wins"].sum())
        total_profit = float(group["profit"].sum())
        roi = total_profit / total_matches

        bootstrap = _bootstrap_roi(group, samples=samples, seed=seed)
        ci_low, median, ci_high = np.quantile(bootstrap, [0.025, 0.5, 0.975])
        nonpositive_share = float((bootstrap <= 0.0).mean())

        loo = _leave_one_out(group)
        if not loo.empty:
            loo.insert(0, "league", league)
            loo_rows.append(loo)
            loo_min = float(loo["roi"].min())
            loo_max = float(loo["roi"].max())
            loo_all_positive = bool((loo["roi"] > 0.0).all())
        else:
            loo_min = float("nan")
            loo_max = float("nan")
            loo_all_positive = False

        summary_rows.append({
            "league": league,
            "seasons": len(group),
            "matches": total_matches,
            "wins": total_wins,
            "profit": total_profit,
            "roi": roi,
            "positive_seasons": int((group["roi"] > 0).sum()),
            "bootstrap_samples": samples,
            "bootstrap_seed": seed,
            "bootstrap_roi_median": float(median),
            "bootstrap_roi_ci_2_5": float(ci_low),
            "bootstrap_roi_ci_97_5": float(ci_high),
            "bootstrap_nonpositive_share": nonpositive_share,
            "leave_one_season_out_min_roi": loo_min,
            "leave_one_season_out_max_roi": loo_max,
            "leave_one_season_out_all_positive": loo_all_positive,
        })

    summary = pd.DataFrame(summary_rows)
    leave_one_out = pd.concat(loo_rows, ignore_index=True) if loo_rows else pd.DataFrame()
    return summary, leave_one_out


def write_reports(
    frame: pd.DataFrame,
    output_dir: Path,
    *,
    samples: int = DEFAULT_BOOTSTRAP_SAMPLES,
    seed: int = DEFAULT_SEED,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary, leave_one_out = uncertainty_report(frame, samples=samples, seed=seed)
    paths = {
        "summary": output_dir / "frozen_uncertainty_summary.csv",
        "leave_one_out": output_dir / "frozen_leave_one_season_out.csv",
    }
    summary.to_csv(paths["summary"], index=False)
    leave_one_out.to_csv(paths["leave_one_out"], index=False)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Frozen-rule season-block uncertainty diagnostics")
    parser.add_argument("frozen_by_season", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/historical_strategy_uncertainty"),
    )
    parser.add_argument("--bootstrap-samples", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()

    paths = write_reports(
        pd.read_csv(args.frozen_by_season),
        args.output_dir,
        samples=args.bootstrap_samples,
        seed=args.seed,
    )
    print("FROZEN RULE UNCERTAINTY — RESEARCH ONLY")
    print(pd.read_csv(paths["summary"]).to_string(index=False))
    print("Bootstrap resamples whole test seasons, not individual matches.")
    print("Leave-one-season-out reports sensitivity; it does not re-select any rule.")
    print("No training, Supabase writes, live activation, Structural changes, or .pkl changes performed.")


if __name__ == "__main__":
    main()
