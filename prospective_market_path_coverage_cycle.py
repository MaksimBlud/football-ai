"""Read-only operational coverage cycle for PROSPECTIVE_MARKET_PATH_V1."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from database import supabase
from prospective_market_path import LEAGUES
from prospective_market_path_coverage import build_fixture_coverage, summarize_fixture_coverage

PAGE_SIZE = 1000
OUTPUT_DIR = Path("artifacts/prospective_market_path_v1")


def _fetch_snapshots(league: str) -> list[dict]:
    rows: list[dict] = []
    start = 0
    columns = "league,event_id,home_team,away_team,commence_time_utc,snapshot_time_utc"
    while True:
        response = (
            supabase.table("odds_snapshots")
            .select(columns)
            .eq("league", league)
            .order("snapshot_time_utc", desc=False)
            .range(start, start + PAGE_SIZE - 1)
            .execute()
        )
        page = list(response.data or [])
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows
        start += PAGE_SIZE


def run() -> dict:
    frames = [pd.DataFrame(_fetch_snapshots(league)) for league in LEAGUES]
    frames = [frame for frame in frames if not frame.empty]
    snapshots = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if snapshots.empty:
        raise RuntimeError("No odds_snapshots available for market-path coverage audit")

    coverage = build_fixture_coverage(snapshots)
    summary = summarize_fixture_coverage(coverage)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(OUTPUT_DIR / "fixture_coverage_monitor.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "fixture_coverage_summary.csv", index=False)

    print(summary.to_string(index=False))
    if not coverage.empty:
        problem = coverage[coverage["status"].isin(["IRRECOVERABLE", "CONFLICT"])]
        if not problem.empty:
            print("\nATTENTION: fixtures unavailable to frozen V1 path protocol:")
            print(problem[["league", "event_id", "home_team", "away_team", "kickoff_utc", "status", "reason"]].to_string(index=False))
    print("READ_ONLY_COVERAGE_AUDIT: no outcome scores, no Supabase writes, no production changes")
    return {"summary": summary.to_dict(orient="records"), "fixtures": int(len(coverage))}


if __name__ == "__main__":
    run()
