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


# ---------------------------------------------------------------------------
# Generic live market-shadow contract.
#
# These functions intentionally contain no Structural V2/model logic and
# perform no database writes.
# ---------------------------------------------------------------------------

from datetime import datetime, timezone
from pathlib import Path


MARKET_SHADOW_OUTPUT_COLUMNS = [
    "league",
    "event_id",
    "home_team",
    "away_team",
    "commence_time_utc",
    "generated_at_utc",
    "snapshot_time_utc",
    "hours_before_kickoff",
    "home_odds",
    "draw_odds",
    "away_odds",
    "market_home_probability",
    "market_draw_probability",
    "market_away_probability",
    "previous_snapshot_time_utc",
    "previous_market_home_probability",
    "previous_market_draw_probability",
    "previous_market_away_probability",
    "market_home_movement",
    "market_draw_movement",
    "market_away_movement",
    "maximum_absolute_market_movement",
    "market_argmax",
    "previous_market_argmax",
    "market_argmax_changed",
    "market_shadow_status",
    "market_only",
]

MARKET_MOVEMENT_EPSILON = 1e-12


def build_market_shadow(
    upcoming: pd.DataFrame,
    snapshots: pd.DataFrame,
    config: LeagueRuntimeConfig,
    *,
    previous_history: pd.DataFrame | None = None,
    generated_at_utc: datetime | None = None,
) -> pd.DataFrame:
    """Build one league's market-only live shadow.

    No model.
    No Structural V2.
    No persistence.
    """

    config.validate()

    league_id = config.identity.identifier

    if not upcoming.empty:
        if "league" not in upcoming.columns:
            raise ValueError(
                "Upcoming data missing league column"
            )

        if not (
            upcoming["league"] == league_id
        ).all():
            raise ValueError(
                "Upcoming data contains non-target league rows"
            )

    snapshots = prepare_snapshots(
        snapshots,
        config,
    )

    if generated_at_utc is None:
        generated_at_utc = datetime.now(
            timezone.utc
        )

    generated = pd.Timestamp(
        generated_at_utc
    )

    if generated.tzinfo is None:
        generated = generated.tz_localize(
            "UTC"
        )
    else:
        generated = generated.tz_convert(
            "UTC"
        )

    if previous_history is None:
        previous_history = pd.DataFrame(
            columns=MARKET_SHADOW_OUTPUT_COLUMNS
        )

    records = []

    for _, fixture in upcoming.iterrows():
        event_id = fixture["event_id"]

        kickoff = pd.Timestamp(
            fixture["commence_time_utc"]
        )

        if kickoff.tzinfo is None:
            kickoff = kickoff.tz_localize(
                "UTC"
            )
        else:
            kickoff = kickoff.tz_convert(
                "UTC"
            )

        observations = snapshots[
            snapshots["event_id"] == event_id
        ].copy()

        # Defensive second gate: even if prepare_snapshots already
        # filtered by each snapshot's stored kickoff, require the
        # snapshot to precede THIS fixture's kickoff too.
        observations = observations[
            observations["snapshot_time_utc"]
            < kickoff
        ].copy()

        observations = observations.sort_values(
            "snapshot_time_utc"
        )

        row = {
            column: None
            for column in MARKET_SHADOW_OUTPUT_COLUMNS
        }

        row.update(
            {
                "league": league_id,
                "event_id": event_id,
                "home_team": fixture["home_team"],
                "away_team": fixture["away_team"],
                "commence_time_utc":
                    kickoff.isoformat(),
                "generated_at_utc":
                    generated.isoformat(),
                "market_shadow_status":
                    "NO_MARKET_ODDS",
                "market_only": True,
            }
        )

        if observations.empty:
            records.append(row)
            continue

        current = observations.iloc[-1]

        try:
            (
                p_home,
                p_draw,
                p_away,
            ) = normalized_market_probabilities(
                current["home_odds"],
                current["draw_odds"],
                current["away_odds"],
            )
        except ValueError:
            row[
                "market_shadow_status"
            ] = "INVALID_MARKET_ODDS"

            records.append(row)
            continue

        snapshot_time = pd.Timestamp(
            current["snapshot_time_utc"]
        )

        current_argmax = probability_argmax(
            p_home,
            p_draw,
            p_away,
        )

        row.update(
            {
                "snapshot_time_utc":
                    snapshot_time.isoformat(),

                "hours_before_kickoff":
                    (
                        kickoff
                        - snapshot_time
                    ).total_seconds()
                    / 3600.0,

                "home_odds":
                    float(current["home_odds"]),

                "draw_odds":
                    float(current["draw_odds"]),

                "away_odds":
                    float(current["away_odds"]),

                "market_home_probability":
                    p_home,

                "market_draw_probability":
                    p_draw,

                "market_away_probability":
                    p_away,

                "market_argmax":
                    current_argmax,

                "market_shadow_status":
                    "OK",
            }
        )

        previous = previous_history[
            (
                previous_history["event_id"]
                == event_id
            )
            & (
                previous_history[
                    "market_shadow_status"
                ]
                == "OK"
            )
        ].copy()

        if not previous.empty:
            previous[
                "_snapshot_time"
            ] = pd.to_datetime(
                previous[
                    "snapshot_time_utc"
                ],
                utc=True,
                errors="coerce",
            )

            previous = previous[
                previous["_snapshot_time"]
                < snapshot_time
            ].copy()

        if not previous.empty:
            previous = previous.sort_values(
                [
                    "_snapshot_time",
                    "generated_at_utc",
                ]
            )

            prev = previous.iloc[-1]

            prev_home = float(
                prev[
                    "market_home_probability"
                ]
            )

            prev_draw = float(
                prev[
                    "market_draw_probability"
                ]
            )

            prev_away = float(
                prev[
                    "market_away_probability"
                ]
            )

            movements = [
                p_home - prev_home,
                p_draw - prev_draw,
                p_away - prev_away,
            ]

            movements = [
                (
                    0.0
                    if abs(value)
                    < MARKET_MOVEMENT_EPSILON
                    else value
                )
                for value in movements
            ]

            row.update(
                {
                    "previous_snapshot_time_utc":
                        str(
                            prev[
                                "snapshot_time_utc"
                            ]
                        ),

                    "previous_market_home_probability":
                        prev_home,

                    "previous_market_draw_probability":
                        prev_draw,

                    "previous_market_away_probability":
                        prev_away,

                    "market_home_movement":
                        movements[0],

                    "market_draw_movement":
                        movements[1],

                    "market_away_movement":
                        movements[2],

                    "maximum_absolute_market_movement":
                        max(
                            abs(value)
                            for value
                            in movements
                        ),

                    "previous_market_argmax":
                        prev[
                            "market_argmax"
                        ],

                    "market_argmax_changed":
                        (
                            str(
                                prev[
                                    "market_argmax"
                                ]
                            )
                            != current_argmax
                        ),
                }
            )

        records.append(row)

    return pd.DataFrame(
        records,
        columns=MARKET_SHADOW_OUTPUT_COLUMNS,
    )


def write_market_shadow_outputs(
    latest: pd.DataFrame,
    *,
    latest_path: Path,
    history_path: Path,
) -> pd.DataFrame:
    """Write latest + idempotent observation history locally."""

    for path in (
        latest_path,
        history_path,
    ):
        if (
            Path("experiments").resolve()
            not in path.resolve().parents
        ):
            raise ValueError(
                "Market-shadow outputs must stay under experiments/"
            )

    latest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    latest.to_csv(
        latest_path,
        index=False,
    )

    if history_path.exists():
        existing = pd.read_csv(
            history_path
        )

        combined = pd.concat(
            [
                existing,
                latest,
            ],
            ignore_index=True,
            sort=False,
        )
    else:
        combined = latest.copy()

    observations = combined[
        combined[
            "snapshot_time_utc"
        ].notna()
    ].drop_duplicates(
        subset=[
            "league",
            "event_id",
            "snapshot_time_utc",
        ],
        keep="first",
    )

    without_market = combined[
        combined[
            "snapshot_time_utc"
        ].isna()
    ].drop_duplicates(
        subset=[
            "league",
            "event_id",
            "generated_at_utc",
        ],
        keep="first",
    )

    combined = pd.concat(
        [
            observations,
            without_market,
        ],
        ignore_index=True,
        sort=False,
    )

    combined.to_csv(
        history_path,
        index=False,
    )

    return combined
