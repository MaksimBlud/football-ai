"""Autonomous read-only cycle for PROSPECTIVE_MARKET_PATH_V1."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from database import supabase
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


def load_results() -> pd.DataFrame:
    columns = "league,match_date,home_team,away_team,result"
    frames = [
        pd.DataFrame(_fetch_league_rows("league_finished_results", columns, league, "match_date"))
        for league in LEAGUES
    ]
    frames = [frame for frame in frames if not frame.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def run() -> dict:
    snapshots = load_snapshots()
    if snapshots.empty:
        raise RuntimeError("No odds_snapshots available")
    paths = build_market_paths(snapshots)
    results = load_results()
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
        print("WAIT: PROSPECTIVE_MARKET_PATH_SAMPLE_NOT_READY; no outcome scores computed")
        return {"status": "WAIT", "readiness": readiness_rows}

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
    print("SCORED_RESEARCH_ONLY: no production activation or writes")
    return {"status": "SCORED_RESEARCH_ONLY", "blocks": len(blocks)}


if __name__ == "__main__":
    run()
