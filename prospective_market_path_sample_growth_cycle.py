"""Read-only sample-growth cycle for PROSPECTIVE_MARKET_PATH_V1."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from database import supabase
from prospective_market_path import LEAGUES, build_market_paths
from prospective_market_path_sample_growth import readiness_without_outcomes, settled_identity_sample
from prospective_market_path_settlement_lag import audit_settlement_lag

PAGE_SIZE = 1000
OUTPUT_DIR = Path("artifacts/prospective_market_path_v1")


def _fetch_table(table: str, columns: str, *, league: str) -> list[dict]:
    rows: list[dict] = []
    start = 0
    while True:
        response = (
            supabase.table(table)
            .select(columns)
            .eq("league", league)
            .range(start, start + PAGE_SIZE - 1)
            .execute()
        )
        page = list(response.data or [])
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows
        start += PAGE_SIZE


def run() -> dict:
    snapshot_columns = "league,event_id,home_team,away_team,commence_time_utc,snapshot_time_utc,home_odds,draw_odds,away_odds"
    result_identity_columns = "league,match_date,home_team,away_team"
    snapshot_frames = []
    result_frames = []
    for league in LEAGUES:
        snapshot_frames.append(pd.DataFrame(_fetch_table("odds_snapshots", snapshot_columns, league=league)))
        result_frames.append(pd.DataFrame(_fetch_table("league_finished_results", result_identity_columns, league=league)))

    snapshots = pd.concat([f for f in snapshot_frames if not f.empty], ignore_index=True) if any(not f.empty for f in snapshot_frames) else pd.DataFrame()
    if snapshots.empty:
        raise RuntimeError("No odds snapshots available for sample-growth audit")
    results_identity = pd.concat([f for f in result_frames if not f.empty], ignore_index=True) if any(not f.empty for f in result_frames) else pd.DataFrame(columns=result_identity_columns.split(","))

    paths = build_market_paths(snapshots)
    if paths.empty:
        settlement = pd.DataFrame(columns=["league", "event_id", "home_team", "away_team", "kickoff_utc", "grace_deadline_utc", "status", "reason"])
    else:
        settlement = audit_settlement_lag(paths, results_identity)

    sample = settled_identity_sample(paths, settlement) if not paths.empty else pd.DataFrame(columns=["league", "event_id", "kickoff_utc", "month"])
    readiness = readiness_without_outcomes(sample)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sample[[c for c in ["league", "event_id", "kickoff_utc", "month"] if c in sample.columns]].to_csv(OUTPUT_DIR / "sample_growth_settled_identities.csv", index=False)
    readiness.to_csv(OUTPUT_DIR / "sample_growth_readiness.csv", index=False)
    print(readiness.to_string(index=False))
    print("READ_ONLY_SAMPLE_GROWTH_AUDIT: result values not queried; no outcome scores; no Supabase writes")
    return {"readiness": readiness.to_dict(orient="records"), "settled_fixtures": int(len(sample))}


if __name__ == "__main__":
    run()
