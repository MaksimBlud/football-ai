"""Manual-only La Liga odds snapshot collector.

This module is intentionally NOT scheduled.
Importing it performs no external API request or Supabase write.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from fixture_identity import require_league
from league_config import LA_LIGA
from save_odds_snapshot import (
    DB_COLUMNS,
    DB_CONFLICT_TARGET,
    SUPABASE_TABLE,
)
from the_odds_service import (
    aggregate_event_h2h,
    get_h2h_odds,
)


OUTPUT = Path(
    "data/odds_snapshots/la_liga_h2h_snapshots.csv"
)


def build_snapshot_rows(
    events,
    snapshot_time_utc: str,
) -> pd.DataFrame:
    """Build league-aware La Liga rows without external writes."""

    rows = []

    for event in events:
        aggregated = aggregate_event_h2h(
            event
        )

        if aggregated is None:
            continue

        rows.append({
            "league":
                LA_LIGA.identifier,

            "snapshot_time_utc":
                snapshot_time_utc,

            "event_id":
                aggregated["event_id"],

            "commence_time_utc":
                aggregated["commence_time"],

            "home_team":
                aggregated["home_team"],

            "away_team":
                aggregated["away_team"],

            "bookmakers_count":
                aggregated["bookmakers_count"],

            "home_odds":
                aggregated["home_odds"],

            "draw_odds":
                aggregated["draw_odds"],

            "away_odds":
                aggregated["away_odds"],

            "home_probability":
                aggregated["home_probability"],

            "draw_probability":
                aggregated["draw_probability"],

            "away_probability":
                aggregated["away_probability"],
        })

    return pd.DataFrame(
        rows,
        columns=DB_COLUMNS,
    )


def merge_local_history(
    old_df: pd.DataFrame,
    new_df: pd.DataFrame,
) -> pd.DataFrame:
    """Merge La Liga history using canonical snapshot identity."""

    old_df = require_league(
        old_df,
        legacy_epl=False,
    )

    new_df = require_league(
        new_df,
        legacy_epl=False,
    )

    combined = pd.concat(
        [old_df, new_df],
        ignore_index=True,
        sort=False,
    )

    combined = combined.drop_duplicates(
        subset=[
            "league",
            "snapshot_time_utc",
            "event_id",
        ],
        keep="last",
    )

    return combined.sort_values(
        [
            "snapshot_time_utc",
            "commence_time_utc",
            "home_team",
        ]
    ).reset_index(drop=True)


def save_local_history(
    new_df: pd.DataFrame,
) -> pd.DataFrame:
    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if OUTPUT.exists():
        old_df = pd.read_csv(
            OUTPUT
        )

        combined = merge_local_history(
            old_df,
            new_df,
        )

    else:
        combined = (
            require_league(
                new_df,
                legacy_epl=False,
            )
            .drop_duplicates(
                subset=[
                    "league",
                    "snapshot_time_utc",
                    "event_id",
                ],
                keep="last",
            )
            .sort_values(
                [
                    "snapshot_time_utc",
                    "commence_time_utc",
                    "home_team",
                ]
            )
            .reset_index(drop=True)
        )

    combined.to_csv(
        OUTPUT,
        index=False,
    )

    return combined


def build_db_rows(
    frame: pd.DataFrame,
) -> list[dict]:
    frame = require_league(
        frame,
        legacy_epl=False,
    )

    missing = set(
        DB_COLUMNS
    ).difference(
        frame.columns
    )

    if missing:
        raise ValueError(
            f"Missing DB columns: {sorted(missing)}"
        )

    return (
        frame[DB_COLUMNS]
        .where(
            pd.notna(
                frame[DB_COLUMNS]
            ),
            None,
        )
        .to_dict(
            orient="records"
        )
    )


def save_supabase(
    frame: pd.DataFrame,
    *,
    supabase_client=None,
) -> int:
    if supabase_client is None:
        from database import (
            supabase as supabase_client,
        )

    rows = build_db_rows(
        frame
    )

    response = (
        supabase_client
        .table(
            SUPABASE_TABLE
        )
        .upsert(
            rows,
            on_conflict=DB_CONFLICT_TARGET,
        )
        .execute()
    )

    return len(
        response.data or []
    )


def main() -> None:
    """Run one explicitly manual La Liga snapshot."""

    if not LA_LIGA.odds_api_sport_key:
        raise RuntimeError(
            "La Liga sport key is unresolved"
        )

    # Important:
    # collection_enabled remains False because this collector
    # is manual-only and intentionally not part of scheduler automation.
    result = get_h2h_odds(
        LA_LIGA.odds_api_sport_key
    )

    snapshot_time = datetime.now(
        timezone.utc
    ).isoformat()

    new_df = build_snapshot_rows(
        result["events"],
        snapshot_time,
    )

    if new_df.empty:
        raise RuntimeError(
            "The Odds API returned no usable La Liga h2h odds"
        )

    combined = save_local_history(
        new_df
    )

    inserted = save_supabase(
        new_df
    )

    print()
    print("=" * 72)
    print("LA LIGA ODDS SNAPSHOT SAVED")
    print("=" * 72)

    print(
        "League:",
        LA_LIGA.identifier,
    )

    print(
        "Sport key:",
        LA_LIGA.odds_api_sport_key,
    )

    print(
        "Snapshot UTC:",
        snapshot_time,
    )

    print(
        "Matches:",
        len(new_df),
    )

    print(
        "Local history rows:",
        len(combined),
    )

    print(
        "Supabase rows processed:",
        inserted,
    )

    print(
        "DB conflict target:",
        DB_CONFLICT_TARGET,
    )

    print(
        "Quota:",
        result["quota"],
    )


if __name__ == "__main__":
    main()
