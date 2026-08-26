"""Pure market-shadow primitives for one configured league.

No Supabase access.
No file writes.
No prediction model.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from league_runtime_config import (
    LeagueRuntimeConfig,
)


def normalized_market_probabilities(
    home_odds: float,
    draw_odds: float,
    away_odds: float,
) -> tuple[float, float, float]:
    odds = np.array(
        [
            home_odds,
            draw_odds,
            away_odds,
        ],
        dtype=float,
    )

    if (
        not np.isfinite(
            odds
        ).all()
        or (
            odds
            <= 1.0
        ).any()
    ):
        raise ValueError(
            "Odds must be finite decimal prices greater than 1.0"
        )

    raw = (
        1.0
        / odds
    )

    total = raw.sum()

    if (
        not np.isfinite(
            total
        )
        or total
        <= 0
    ):
        raise ValueError(
            "Invalid implied probability total"
        )

    normalized = (
        raw
        / total
    )

    return (
        float(
            normalized[0]
        ),
        float(
            normalized[1]
        ),
        float(
            normalized[2]
        ),
    )


def probability_argmax(
    home: float,
    draw: float,
    away: float,
) -> str:
    values = {
        "H": float(home),
        "D": float(draw),
        "A": float(away),
    }

    return max(
        values,
        key=values.get,
    )


def prepare_snapshots(
    snapshots: pd.DataFrame,
    config: LeagueRuntimeConfig,
) -> pd.DataFrame:
    required = {
        "league",
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
        "home_team",
        "away_team",
        "home_odds",
        "draw_odds",
        "away_odds",
    }

    missing = (
        required
        - set(
            snapshots.columns
        )
    )

    if missing:
        raise ValueError(
            "Snapshot data missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    if snapshots.empty:
        return snapshots.copy()

    result = snapshots.copy()

    league_id = (
        config.identity.identifier
    )

    if not (
        result[
            "league"
        ]
        == league_id
    ).all():
        observed = sorted(
            result[
                "league"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        raise ValueError(
            "Mixed/non-target market snapshots supplied: "
            f"expected={league_id}, observed={observed}"
        )

    result[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        result[
            "snapshot_time_utc"
        ],
        utc=True,
        errors="coerce",
    )

    result[
        "commence_time_utc"
    ] = pd.to_datetime(
        result[
            "commence_time_utc"
        ],
        utc=True,
        errors="coerce",
    )

    for column in (
        "home_odds",
        "draw_odds",
        "away_odds",
    ):
        result[
            column
        ] = pd.to_numeric(
            result[
                column
            ],
            errors="coerce",
        )

    result = result.dropna(
        subset=[
            "event_id",
            "snapshot_time_utc",
            "commence_time_utc",
            "home_odds",
            "draw_odds",
            "away_odds",
        ]
    ).copy()

    result = result[
        result[
            "snapshot_time_utc"
        ]
        < result[
            "commence_time_utc"
        ]
    ].copy()

    return result.sort_values(
        [
            "event_id",
            "snapshot_time_utc",
        ]
    ).reset_index(
        drop=True
    )
