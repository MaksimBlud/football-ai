"""Export future RPL fixtures from existing odds snapshots.

Read-only Supabase access. No model. No Structural V2.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from database import supabase
from league_fixture_export import prepare_upcoming_fixtures as prepare_generic
from league_runtime_config import RPL_RUNTIME_CONFIG


OUTPUT_PATH = RPL_RUNTIME_CONFIG.paths.upcoming_fixtures
DB_COLUMNS = (
    "league,event_id,snapshot_time_utc,commence_time_utc,home_team,away_team"
)


def normalize_rpl_team(value: str) -> str:
    value = str(value).strip()
    if not value:
        return value
    return RPL_RUNTIME_CONFIG.aliases.get(value, value)


def fetch_rpl_snapshots() -> pd.DataFrame:
    response = (
        supabase
        .table("odds_snapshots")
        .select(DB_COLUMNS)
        .eq("league", RPL_RUNTIME_CONFIG.identity.identifier)
        .order("snapshot_time_utc", desc=True)
        .limit(10000)
        .execute()
    )
    return pd.DataFrame(response.data or [])


def prepare_upcoming_fixtures(
    snapshots: pd.DataFrame,
    *,
    now: datetime | None = None,
) -> pd.DataFrame:
    return prepare_generic(
        snapshots,
        RPL_RUNTIME_CONFIG,
        normalize_team=normalize_rpl_team,
        now=now,
    )


def main() -> None:
    structural = RPL_RUNTIME_CONFIG.structural_v2
    if (
        structural.calibration_status != "CALIBRATION_REQUIRED"
        or structural.structural_alpha is not None
        or structural.edge_threshold is not None
    ):
        raise RuntimeError("Unexpected RPL Structural V2 state")

    snapshots = fetch_rpl_snapshots()
    upcoming = prepare_upcoming_fixtures(snapshots)

    if upcoming.empty:
        raise RuntimeError("No future RPL fixtures found in Supabase")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    upcoming.to_csv(OUTPUT_PATH, index=False)

    print("=" * 72)
    print("RPL UPCOMING FIXTURES")
    print("=" * 72)
    print("source snapshots:", len(snapshots))
    print("fixtures:", len(upcoming))
    print("unique events:", upcoming["event_id"].nunique())
    print("Structural V2 used:", False)
    print("output:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
