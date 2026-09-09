"""Read-only operational coverage cycle for PROSPECTIVE_MARKET_PATH_V1."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from prospective_market_path import LEAGUES
from prospective_market_path_revisions import (
    STATUS_QUARANTINED_REVISION,
    STATUS_SUPERSEDED,
)
from prospective_market_status import build_market_status, render_market_status

PAGE_SIZE = 1000
OUTPUT_DIR = Path("artifacts/prospective_market_path_v1")


def _fetch_snapshots(league: str) -> list[dict]:
    # Keep the Supabase client at the actual I/O boundary. This lets the status
    # assembly remain importable/testable without opening a database connection.
    from database import supabase

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

    market_status = build_market_status(snapshots)
    coverage = market_status.coverage
    summary = market_status.leagues
    live_priority = market_status.live_refresh_queue

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    coverage.to_csv(OUTPUT_DIR / "fixture_coverage_monitor.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "fixture_coverage_summary.csv", index=False)
    live_priority.to_csv(OUTPUT_DIR / "live_refresh_priority.csv", index=False)

    print(render_market_status(market_status))
    if not coverage.empty:
        problem = coverage[coverage["status"].isin(["IRRECOVERABLE", "CONFLICT"])]
        if not problem.empty:
            print("\nATTENTION: fixtures unavailable to frozen V1 path protocol:")
            print(problem[["league", "event_id", "home_team", "away_team", "kickoff_utc", "status", "reason"]].to_string(index=False))
        quarantined = coverage[coverage["status"] == STATUS_QUARANTINED_REVISION]
        if not quarantined.empty:
            print("\nINFO: deterministic provider schedule revisions quarantined from frozen research:")
            print(quarantined[["league", "event_id", "home_team", "away_team", "status", "reason"]].to_string(index=False))
        superseded = coverage[coverage["status"] == STATUS_SUPERSEDED]
        if not superseded.empty:
            print("\nINFO: stale provider schedule revisions excluded from operational risk counts:")
            print(superseded[["league", "event_id", "home_team", "away_team", "kickoff_utc", "status", "reason"]].to_string(index=False))
    print("READ_ONLY_COVERAGE_AUDIT: no outcome scores, no Supabase writes, no production changes")
    return {
        "summary": summary.to_dict(orient="records"),
        "fixtures": int(len(coverage)),
        "actionable_refresh_due": int(len(live_priority)),
        "live_refresh_queue": live_priority.to_dict(orient="records"),
    }


if __name__ == "__main__":
    run()
