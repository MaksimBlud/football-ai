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
    columns = [
        "league",
        "event_id",
        "match_date",
        "match_time",
        "home_team",
        "away_team",
        "home_team_model",
        "away_team_model",
        "commence_time_utc",
        "match_datetime_local",
    ]

    if snapshots.empty:
        return pd.DataFrame(
            columns=columns
        )

    required = {
        "league",
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
        "home_team",
        "away_team",
    }

    missing = required - set(
        snapshots.columns
    )

    if missing:
        raise ValueError(
            "Missing snapshot columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    df = snapshots.copy()

    if not (
        df["league"]
        == LA_LIGA.identifier
    ).all():
        raise ValueError(
            "Non-La-Liga rows supplied "
            "to La Liga fixture exporter."
        )

    df["snapshot_time_utc"] = (
        pd.to_datetime(
            df["snapshot_time_utc"],
            utc=True,
            errors="coerce",
        )
    )

    df["commence_time_utc"] = (
        pd.to_datetime(
            df["commence_time_utc"],
            utc=True,
            errors="coerce",
        )
    )

    df = df.dropna(
        subset=[
            "event_id",
            "snapshot_time_utc",
            "commence_time_utc",
            "home_team",
            "away_team",
        ]
    ).copy()

    if now is None:
        now = datetime.now(
            timezone.utc
        )

    now_utc = pd.Timestamp(now)

    if now_utc.tzinfo is None:
        now_utc = now_utc.tz_localize(
            "UTC"
        )
    else:
        now_utc = now_utc.tz_convert(
            "UTC"
        )

    df = df[
        df["commence_time_utc"]
        > now_utc
    ].copy()

    # Same fixture can have many market snapshots.
    # Keep the newest snapshot representation.
    df = df.sort_values(
        "snapshot_time_utc",
        ascending=False,
    )

    df = df.drop_duplicates(
        subset=[
            "league",
            "event_id",
        ],
        keep="first",
    )

    local_dt = (
        df["commence_time_utc"]
        .dt.tz_convert(
            LOCAL_TIMEZONE
        )
    )

    df["match_date"] = (
        local_dt
        .dt.strftime("%Y-%m-%d")
    )

    df["match_time"] = (
        local_dt
        .dt.strftime("%H:%M")
    )

    df["match_datetime_local"] = (
        local_dt.astype(str)
    )

    # These columns are retained for schema compatibility only.
    # Their presence does NOT mean EPL models may be run on La Liga.
    df["home_team_model"] = (
        df["home_team"]
        .map(normalize_team_name)
    )

    df["away_team_model"] = (
        df["away_team"]
        .map(normalize_team_name)
    )

    df = df.sort_values(
        [
            "commence_time_utc",
            "home_team",
            "away_team",
        ]
    ).reset_index(
        drop=True
    )

    return df[columns]


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
