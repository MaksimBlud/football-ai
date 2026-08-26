"""
Export upcoming La Liga fixtures from already collected Supabase odds snapshots.

Research / fixture layer only.

This script:
- performs no Odds API request;
- performs no Supabase write;
- reads only LA_LIGA rows;
- keeps the newest known representation of each fixture;
- writes data/upcoming_matches_la_liga.csv;
- does not invoke any EPL prediction model.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from database import supabase
from league_config import LA_LIGA
from team_names import normalize_team_name

from league_fixture_export import (
    prepare_upcoming_fixtures as prepare_generic_upcoming_fixtures,
)
from league_runtime_config import (
    LA_LIGA_RUNTIME_CONFIG,
)


OUTPUT_PATH = Path(
    "data/upcoming_matches_la_liga.csv"
)

LOCAL_TIMEZONE = ZoneInfo(
    LA_LIGA.timezone
)

DB_COLUMNS = (
    "league,"
    "event_id,"
    "snapshot_time_utc,"
    "commence_time_utc,"
    "home_team,"
    "away_team"
)


def fetch_la_liga_snapshots() -> pd.DataFrame:
    response = (
        supabase
        .table("odds_snapshots")
        .select(DB_COLUMNS)
        .eq(
            "league",
            LA_LIGA.identifier,
        )
        .order(
            "snapshot_time_utc",
            desc=True,
        )
        .limit(10000)
        .execute()
    )

    return pd.DataFrame(
        response.data or []
    )


def prepare_upcoming_fixtures(
    snapshots: pd.DataFrame,
    *,
    now: datetime | None = None,
) -> pd.DataFrame:
    """La Liga compatibility facade over the generic fixture core."""

    return prepare_generic_upcoming_fixtures(
        snapshots,
        LA_LIGA_RUNTIME_CONFIG,
        normalize_team=normalize_team_name,
        now=now,
    )


def main() -> None:
    snapshots = (
        fetch_la_liga_snapshots()
    )

    upcoming = (
        prepare_upcoming_fixtures(
            snapshots
        )
    )

    if upcoming.empty:
        raise RuntimeError(
            "No future La Liga fixtures "
            "found in Supabase."
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    upcoming.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("=" * 72)
    print(
        "LA LIGA UPCOMING FIXTURES EXPORTED"
    )
    print("=" * 72)

    print(
        "League:",
        LA_LIGA.identifier,
    )

    print(
        "Source snapshot rows:",
        len(snapshots),
    )

    print(
        "Upcoming fixtures:",
        len(upcoming),
    )

    print(
        "Output:",
        OUTPUT_PATH,
    )

    print()
    print(
        upcoming.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
