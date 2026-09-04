"""Explicit evaluation gate for PROSPECTIVE_MARKET_PATH_V1.

Scheduled/default execution is outcome-free and delegates to the identity-only
sample-growth readiness audit. Outcome values are queried only when an operator
explicitly passes ``--evaluate`` after the frozen readiness gate is satisfied.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from prospective_market_path import (
    LEAGUES,
    build_market_paths,
    evaluate_ready_league,
    readiness_for_league,
    settle_market_paths,
)

PAGE_SIZE = 1000
OUTPUT_DIR = Path("artifacts/prospective_market_path_v1")


def _fetch_league_rows(table: str, columns: str, league: str, order_column: str) -> list[dict]:
    # Keep database client import lazy so pure gate/contract tests do not require
    # Supabase or credentials simply to import this module.
    from database import supabase

    rows: list[dict] = []
    start = 0
    while True:
        response = (
            supabase.table(table)
            .select(columns)
            .eq("league", league)
            .order(order_column, desc=False)
            .range(start, start + PAGE_SIZE - 1)
            .execute()
        )
        page = list(response.data or [])
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows
        start += PAGE_SIZE


def _run_sample_growth() -> dict:
    # The outcome-free readiness cycle owns the canonical identity-only query.
    from prospective_market_path_sample_growth_cycle import run as run_sample_growth

    return run_sample_growth()


def load_snapshots() -> pd.DataFrame:
    columns = (
        "league,event_id,home_team,away_team,commence_time_utc,snapshot_time_utc,"
        "home_odds,draw_odds,away_odds"
    )
    frames = [
        pd.DataFrame(_fetch_league_rows("odds_snapshots", columns, league, "snapshot_time_utc"))
        for league in LEAGUES
    ]
    frames = [frame for frame in frames if not frame.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_results_for_explicit_evaluation() -> pd.DataFrame:
    """Load outcome values only for an explicitly requested evaluation run."""
    columns = "league,match_date,home_team,away_team,result"
    frames = [
        pd.DataFrame(_fetch_league_rows("league_finished_results", columns, league, "match_date"))
        for league in LEAGUES
    ]
    frames = [frame for frame in frames if not frame.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def run_readiness_only() -> dict:
    """Run the canonical identity-only readiness audit; never query outcomes."""
    result = _run_sample_growth()
    print("OUTCOME_EVALUATION_GATED: explicit --evaluate required after frozen readiness")
    return {"status": "ACCUMULATING", "sample_growth": result}


def run_explicit_evaluation() -> dict:
    """Run the frozen paired evaluation after an explicit operator request."""
    snapshots = load_snapshots()
    if snapshots.empty:
        raise RuntimeError("No odds_snapshots available")
    paths = build_market_paths(snapshots)
    results = load_results_for_explicit_evaluation()
    settled_frames = []
    readiness_rows = []
    for league in LEAGUES:
        settled = settle_market_paths(paths, results, league)
        if not settled.empty:
            settled_frames.append(settled)
        state = readiness_for_league(settled, league)
        readiness_rows.append(state.__dict__)

    readiness = pd.DataFrame(readiness_rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    readiness.to_csv(OUTPUT_DIR / "readiness.csv", index=False)
    paths.to_csv(OUTPUT_DIR / "eligible_path_coverage.csv", index=False)
    print(readiness.to_string(index=False))

    if not bool(readiness["ready"].all()):
        raise RuntimeError(
            "EXPLICIT_EVALUATION_REFUSED: all three leagues must pass the frozen readiness gate"
        )

    settled_all = pd.concat(settled_frames, ignore_index=True) if settled_frames else pd.DataFrame()
    blocks = pd.concat(
        [evaluate_ready_league(settled_all, league) for league in LEAGUES],
        ignore_index=True,
    )
    blocks.to_csv(OUTPUT_DIR / "paired_monthly_evaluation.csv", index=False)
    summary = (
        blocks.groupby("league")[["matches", "delta_brier", "delta_log_loss"]]
        .agg({"matches": "sum", "delta_brier": "mean", "delta_log_loss": "mean"})
        .reset_index()
    )
    summary.to_csv(OUTPUT_DIR / "paired_summary.csv", index=False)
    print(summary.to_string(index=False))
    print("SCORED_RESEARCH_ONLY_EXPLICIT: no production activation or writes")
    return {"status": "SCORED_RESEARCH_ONLY_EXPLICIT", "blocks": len(blocks)}


def run(*, evaluate: bool = False) -> dict:
    return run_explicit_evaluation() if evaluate else run_readiness_only()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prospective Market Path V1 cycle")
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Explicitly run the preregistered outcome evaluation after readiness.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run(evaluate=args.evaluate)
