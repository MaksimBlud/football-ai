"""Read-only live audit for RPL odds snapshots and durable state.

No writes, no model loading, no Structural V2 activation.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from database import supabase
from rpl_snapshot_readiness import audit_snapshot_readiness


SNAPSHOT_COLUMNS = (
    "league,event_id,snapshot_time_utc,commence_time_utc,"
    "home_team,away_team,home_odds,draw_odds,away_odds"
)


def _count(table: str, league: str = "RPL") -> int:
    response = (
        supabase
        .table(table)
        .select("*", count="exact")
        .eq("league", league)
        .limit(1)
        .execute()
    )
    if response.count is not None:
        return int(response.count)
    return len(response.data or [])


def fetch_rpl_snapshots() -> pd.DataFrame:
    response = (
        supabase
        .table("odds_snapshots")
        .select(SNAPSHOT_COLUMNS)
        .eq("league", "RPL")
        .order("snapshot_time_utc", desc=True)
        .limit(10000)
        .execute()
    )
    return pd.DataFrame(response.data or [])


def main() -> None:
    snapshots = fetch_rpl_snapshots()
    audit = audit_snapshot_readiness(snapshots)

    print("=" * 88)
    print("RPL LIVE READINESS AUDIT — READ ONLY")
    print("=" * 88)
    print("snapshot rows:", len(snapshots))
    print("readiness:", audit.get("ready"))
    print("reason:", audit.get("reason"))
    print("unique events:", audit.get("unique_events", 0))
    print("invalid time rows:", audit.get("invalid_time_rows", 0))
    print("invalid odds rows:", audit.get("invalid_odds_rows", 0))
    print("post-kickoff rows:", audit.get("post_kickoff_rows", 0))
    print("aliases used:", audit.get("aliases_used", []))

    teams = audit.get("normalized_teams", [])
    print("teams:", teams)

    if not snapshots.empty:
        work = snapshots.copy()
        work["snapshot_time_utc"] = pd.to_datetime(
            work["snapshot_time_utc"], utc=True, errors="coerce"
        )
        work["commence_time_utc"] = pd.to_datetime(
            work["commence_time_utc"], utc=True, errors="coerce"
        )
        now = pd.Timestamp(datetime.now(timezone.utc))
        future = work.loc[work["commence_time_utc"] > now].copy()
        latest = (
            future.sort_values("snapshot_time_utc")
            .groupby("event_id", as_index=False)
            .tail(1)
            .sort_values("commence_time_utc")
        )
        print("future snapshot rows:", len(future))
        print("future unique events:", int(future["event_id"].nunique()))
        print("latest future fixtures:")
        for row in latest.itertuples(index=False):
            print(
                f"  {row.commence_time_utc} | {row.home_team} vs {row.away_team} | "
                f"odds={row.home_odds}/{row.draw_odds}/{row.away_odds} | "
                f"snapshot={row.snapshot_time_utc}"
            )
    else:
        print("future snapshot rows: 0")
        print("future unique events: 0")

    print("durable observations:", _count("league_structural_v2_observations"))
    print("prediction ledger rows:", _count("league_prediction_ledger"))
    print("finished results rows:", _count("league_finished_results"))
    print("Structural V2 used:", False)
    print("production model used:", False)
    print("PASS: READ-ONLY AUDIT COMPLETE")


if __name__ == "__main__":
    main()
