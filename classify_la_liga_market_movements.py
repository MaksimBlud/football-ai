"""Classify descriptive La Liga market movements.

Research-only.

This module:
- reads existing La Liga market-shadow history;
- compares the latest two distinct market observations per fixture;
- does not call The Odds API;
- does not write Supabase;
- does not invoke any AI/production model;
- does not tune thresholds from observed results.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from generate_la_liga_market_shadow import (
    HISTORY_OUTPUT,
    MOVEMENT_EPSILON,
)
from league_config import LA_LIGA


DEFAULT_OUTPUT = Path(
    "experiments/la_liga_market_movement_states.csv"
)

STATES = (
    "NO_CHANGE",
    "HOME_STEAM",
    "DRAW_STEAM",
    "AWAY_STEAM",
    "ARGMAX_FLIP",
    "MIXED",
)

OUTPUT_COLUMNS = [
    "league",
    "event_id",
    "home_team",
    "away_team",
    "commence_time_utc",
    "observation_count",
    "previous_snapshot_time_utc",
    "latest_snapshot_time_utc",
    "previous_hours_before_kickoff",
    "latest_hours_before_kickoff",
    "previous_market_home_probability",
    "previous_market_draw_probability",
    "previous_market_away_probability",
    "latest_market_home_probability",
    "latest_market_draw_probability",
    "latest_market_away_probability",
    "market_home_movement",
    "market_draw_movement",
    "market_away_movement",
    "movement_magnitude",
    "previous_market_argmax",
    "latest_market_argmax",
    "market_argmax_changed",
    "dominant_direction",
    "movement_state",
    "research_only",
]


def load_history(
    path: Path = HISTORY_OUTPUT,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path
    )

    required = {
        "league",
        "event_id",
        "home_team",
        "away_team",
        "commence_time_utc",
        "snapshot_time_utc",
        "hours_before_kickoff",
        "market_home_probability",
        "market_draw_probability",
        "market_away_probability",
        "market_argmax",
        "market_shadow_status",
    }

    missing = required - set(
        frame.columns
    )

    if missing:
        raise ValueError(
            "History missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    if not (
        frame["league"]
        == LA_LIGA.identifier
    ).all():
        raise ValueError(
            "History contains non-La-Liga rows"
        )

    frame = frame[
        frame["market_shadow_status"]
        == "OK"
    ].copy()

    frame[
        "snapshot_time_utc"
    ] = pd.to_datetime(
        frame["snapshot_time_utc"],
        utc=True,
        errors="coerce",
    )

    frame[
        "commence_time_utc"
    ] = pd.to_datetime(
        frame["commence_time_utc"],
        utc=True,
        errors="coerce",
    )

    numeric = [
        "hours_before_kickoff",
        "market_home_probability",
        "market_draw_probability",
        "market_away_probability",
    ]

    for column in numeric:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame = frame.dropna(
        subset=[
            "event_id",
            "snapshot_time_utc",
            "commence_time_utc",
            *numeric,
        ]
    ).copy()

    # Defensive invariant:
    # one row per real market observation.
    frame = frame.drop_duplicates(
        subset=[
            "league",
            "event_id",
            "snapshot_time_utc",
        ],
        keep="last",
    )

    return frame.sort_values(
        [
            "event_id",
            "snapshot_time_utc",
        ]
    ).reset_index(
        drop=True
    )


def classify_movements(
    home_movement: float,
    draw_movement: float,
    away_movement: float,
    *,
    previous_argmax: str,
    latest_argmax: str,
) -> tuple[str, str]:
    """Return movement_state and dominant_direction."""

    if previous_argmax != latest_argmax:
        return (
            "ARGMAX_FLIP",
            latest_argmax,
        )

    movements = {
        "H": float(
            home_movement
        ),
        "D": float(
            draw_movement
        ),
        "A": float(
            away_movement
        ),
    }

    magnitude = max(
        abs(value)
        for value in movements.values()
    )

    if magnitude <= MOVEMENT_EPSILON:
        return (
            "NO_CHANGE",
            "NONE",
        )

    positive = {
        outcome: value
        for outcome, value
        in movements.items()
        if value > MOVEMENT_EPSILON
    }

    if not positive:
        return (
            "MIXED",
            "NONE",
        )

    max_positive = max(
        positive.values()
    )

    leaders = [
        outcome
        for outcome, value
        in positive.items()
        if abs(
            value - max_positive
        ) <= MOVEMENT_EPSILON
    ]

    if len(leaders) != 1:
        return (
            "MIXED",
            "NONE",
        )

    leader = leaders[0]

    state = {
        "H": "HOME_STEAM",
        "D": "DRAW_STEAM",
        "A": "AWAY_STEAM",
    }[
        leader
    ]

    return (
        state,
        leader,
    )


def build_states(
    history: pd.DataFrame,
) -> pd.DataFrame:
    records = []

    for (
        league,
        event_id,
    ), fixture in history.groupby(
        [
            "league",
            "event_id",
        ],
        sort=False,
    ):
        fixture = fixture.sort_values(
            "snapshot_time_utc"
        )

        observation_count = len(
            fixture
        )

        if observation_count < 2:
            continue

        previous = fixture.iloc[-2]
        latest = fixture.iloc[-1]

        home_movement = (
            float(
                latest[
                    "market_home_probability"
                ]
            )
            - float(
                previous[
                    "market_home_probability"
                ]
            )
        )

        draw_movement = (
            float(
                latest[
                    "market_draw_probability"
                ]
            )
            - float(
                previous[
                    "market_draw_probability"
                ]
            )
        )

        away_movement = (
            float(
                latest[
                    "market_away_probability"
                ]
            )
            - float(
                previous[
                    "market_away_probability"
                ]
            )
        )

        movements = [
            home_movement,
            draw_movement,
            away_movement,
        ]

        movements = [
            (
                0.0
                if abs(value)
                < MOVEMENT_EPSILON
                else value
            )
            for value in movements
        ]

        (
            home_movement,
            draw_movement,
            away_movement,
        ) = movements

        previous_argmax = str(
            previous[
                "market_argmax"
            ]
        )

        latest_argmax = str(
            latest[
                "market_argmax"
            ]
        )

        state, direction = (
            classify_movements(
                home_movement,
                draw_movement,
                away_movement,
                previous_argmax=(
                    previous_argmax
                ),
                latest_argmax=(
                    latest_argmax
                ),
            )
        )

        magnitude = max(
            abs(home_movement),
            abs(draw_movement),
            abs(away_movement),
        )

        records.append({
            "league":
                league,

            "event_id":
                event_id,

            "home_team":
                latest["home_team"],

            "away_team":
                latest["away_team"],

            "commence_time_utc":
                latest[
                    "commence_time_utc"
                ].isoformat(),

            "observation_count":
                observation_count,

            "previous_snapshot_time_utc":
                previous[
                    "snapshot_time_utc"
                ].isoformat(),

            "latest_snapshot_time_utc":
                latest[
                    "snapshot_time_utc"
                ].isoformat(),

            "previous_hours_before_kickoff":
                float(
                    previous[
                        "hours_before_kickoff"
                    ]
                ),

            "latest_hours_before_kickoff":
                float(
                    latest[
                        "hours_before_kickoff"
                    ]
                ),

            "previous_market_home_probability":
                float(
                    previous[
                        "market_home_probability"
                    ]
                ),

            "previous_market_draw_probability":
                float(
                    previous[
                        "market_draw_probability"
                    ]
                ),

            "previous_market_away_probability":
                float(
                    previous[
                        "market_away_probability"
                    ]
                ),

            "latest_market_home_probability":
                float(
                    latest[
                        "market_home_probability"
                    ]
                ),

            "latest_market_draw_probability":
                float(
                    latest[
                        "market_draw_probability"
                    ]
                ),

            "latest_market_away_probability":
                float(
                    latest[
                        "market_away_probability"
                    ]
                ),

            "market_home_movement":
                home_movement,

            "market_draw_movement":
                draw_movement,

            "market_away_movement":
                away_movement,

            "movement_magnitude":
                magnitude,

            "previous_market_argmax":
                previous_argmax,

            "latest_market_argmax":
                latest_argmax,

            "market_argmax_changed":
                previous_argmax
                != latest_argmax,

            "dominant_direction":
                direction,

            "movement_state":
                state,

            "research_only":
                True,
        })

    return pd.DataFrame(
        records,
        columns=OUTPUT_COLUMNS,
    )


def write_states(
    frame: pd.DataFrame,
    path: Path = DEFAULT_OUTPUT,
) -> None:
    experiments = Path(
        "experiments"
    ).resolve()

    resolved = path.resolve()

    if experiments not in resolved.parents:
        raise ValueError(
            "Output must remain under experiments/"
        )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        path,
        index=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        default=HISTORY_OUTPUT,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    args = parser.parse_args()

    history = load_history(
        args.input
    )

    states = build_states(
        history
    )

    write_states(
        states,
        args.output,
    )

    print("=" * 72)
    print(
        "LA LIGA MARKET MOVEMENT STATES"
    )
    print("=" * 72)

    print(
        "valid observations:",
        len(history),
    )

    print(
        "fixtures with >=2 observations:",
        len(states),
    )

    if states.empty:
        print(
            "HOLD: insufficient temporal history"
        )
        return

    print()
    print(
        "STATE COUNTS:"
    )

    print(
        states[
            "movement_state"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "DIRECTION COUNTS:"
    )

    print(
        states[
            "dominant_direction"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "ARGMAX FLIPS:",
        int(
            states[
                "market_argmax_changed"
            ].sum()
        ),
    )

    print()
    print(
        "LARGEST MOVEMENTS:"
    )

    print(
        states.sort_values(
            "movement_magnitude",
            ascending=False,
        )[
            [
                "home_team",
                "away_team",
                "observation_count",
                "latest_hours_before_kickoff",
                "movement_state",
                "dominant_direction",
                "market_home_movement",
                "market_draw_movement",
                "market_away_movement",
                "movement_magnitude",
                "previous_market_argmax",
                "latest_market_argmax",
            ]
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "output:",
        args.output,
    )


if __name__ == "__main__":
    main()
