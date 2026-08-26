"""Pure league-aware upcoming-fixture projection.

No database access.
No file writes.
No model inference.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from zoneinfo import ZoneInfo

import pandas as pd

from league_runtime_config import (
    LeagueRuntimeConfig,
)


OUTPUT_COLUMNS = [
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


def _now_utc(
    now: datetime | None,
) -> pd.Timestamp:
    if now is None:
        now = datetime.now(
            timezone.utc
        )

    value = pd.Timestamp(
        now
    )

    if value.tzinfo is None:
        return value.tz_localize(
            "UTC"
        )

    return value.tz_convert(
        "UTC"
    )


def prepare_upcoming_fixtures(
    snapshots: pd.DataFrame,
    config: LeagueRuntimeConfig,
    *,
    normalize_team: Callable[[str], str],
    now: datetime | None = None,
) -> pd.DataFrame:
    """Project latest future fixture representations for one league."""

    if snapshots.empty:
        return pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    required = {
        "league",
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
        "home_team",
        "away_team",
    }

    missing = (
        required
        - set(
            snapshots.columns
        )
    )

    if missing:
        raise ValueError(
            "Missing snapshot columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    frame = snapshots.copy()

    league_id = (
        config.identity.identifier
    )

    if not (
        frame["league"]
        == league_id
    ).all():
        observed = sorted(
            frame[
                "league"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        raise ValueError(
            "Mixed/non-target league rows supplied: "
            f"expected={league_id}, observed={observed}"
        )

    frame[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        frame[
            "snapshot_time_utc"
        ],
        utc=True,
        errors="coerce",
    )

    frame[
        "commence_time_utc"
    ] = pd.to_datetime(
        frame[
            "commence_time_utc"
        ],
        utc=True,
        errors="coerce",
    )

    frame = frame.dropna(
        subset=[
            "event_id",
            "snapshot_time_utc",
            "commence_time_utc",
            "home_team",
            "away_team",
        ]
    ).copy()

    frame = frame[
        frame[
            "commence_time_utc"
        ]
        > _now_utc(now)
    ].copy()

    frame = frame.sort_values(
        "snapshot_time_utc",
        ascending=False,
    )

    frame = frame.drop_duplicates(
        subset=[
            "league",
            "event_id",
        ],
        keep="first",
    )

    local_timezone = ZoneInfo(
        config.identity.timezone
    )

    local_dt = (
        frame[
            "commence_time_utc"
        ]
        .dt.tz_convert(
            local_timezone
        )
    )

    frame[
        "match_date"
    ] = local_dt.dt.strftime(
        "%Y-%m-%d"
    )

    frame[
        "match_time"
    ] = local_dt.dt.strftime(
        "%H:%M"
    )

    frame[
        "match_datetime_local"
    ] = local_dt.astype(str)

    frame[
        "home_team_model"
    ] = (
        frame[
            "home_team"
        ]
        .map(
            normalize_team
        )
    )

    frame[
        "away_team_model"
    ] = (
        frame[
            "away_team"
        ]
        .map(
            normalize_team
        )
    )

    frame = frame.sort_values(
        [
            "commence_time_utc",
            "home_team",
            "away_team",
        ]
    ).reset_index(
        drop=True
    )

    return frame[
        OUTPUT_COLUMNS
    ]
