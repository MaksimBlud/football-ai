"""Track descriptive La Liga market-state transitions.

Research-only.

The tracker:
- reads existing La Liga market-shadow history;
- uses distinct real market observations;
- classifies every adjacent observation pair;
- derives transitions between consecutive movement states;
- performs no Odds API request;
- performs no Supabase write;
- invokes no AI/production model.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from classify_la_liga_market_movements import (
    classify_movements,
    load_history,
)
from generate_la_liga_market_shadow import (
    HISTORY_OUTPUT,
    MOVEMENT_EPSILON,
)
from league_config import LA_LIGA


DEFAULT_OUTPUT = Path(
    "experiments/la_liga_market_transitions.csv"
)

PAIR_COLUMNS = [
    "league",
    "event_id",
    "home_team",
    "away_team",
    "commence_time_utc",
    "pair_index",
    "from_snapshot_time_utc",
    "to_snapshot_time_utc",
    "from_hours_before_kickoff",
    "to_hours_before_kickoff",
    "home_movement",
    "draw_movement",
    "away_movement",
    "movement_magnitude",
    "from_market_argmax",
    "to_market_argmax",
    "market_argmax_changed",
    "dominant_direction",
    "movement_state",
]

OUTPUT_COLUMNS = [
    "league",
    "event_id",
    "home_team",
    "away_team",
    "commence_time_utc",
    "observation_count",
    "movement_pair_count",
    "transition_count",
    "previous_pair_index",
    "latest_pair_index",
    "previous_state",
    "latest_state",
    "previous_direction",
    "latest_direction",
    "previous_movement_magnitude",
    "latest_movement_magnitude",
    "previous_market_argmax",
    "latest_market_argmax",
    "transition",
    "direction_transition",
    "state_changed",
    "direction_changed",
    "research_only",
]


def _zero_small(value: float) -> float:
    value = float(value)

    if abs(value) < MOVEMENT_EPSILON:
        return 0.0

    return value


def build_pair_states(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """Classify every adjacent observation pair."""

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
        fixture = (
            fixture
            .sort_values(
                "snapshot_time_utc"
            )
            .reset_index(drop=True)
        )

        if len(fixture) < 2:
            continue

        for pair_index in range(
            1,
            len(fixture),
        ):
            previous = fixture.iloc[
                pair_index - 1
            ]

            latest = fixture.iloc[
                pair_index
            ]

            home_movement = _zero_small(
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

            draw_movement = _zero_small(
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

            away_movement = _zero_small(
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

            from_argmax = str(
                previous[
                    "market_argmax"
                ]
            )

            to_argmax = str(
                latest[
                    "market_argmax"
                ]
            )

            (
                state,
                direction,
            ) = classify_movements(
                home_movement,
                draw_movement,
                away_movement,
                previous_argmax=from_argmax,
                latest_argmax=to_argmax,
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

                "pair_index":
                    pair_index,

                "from_snapshot_time_utc":
                    previous[
                        "snapshot_time_utc"
                    ].isoformat(),

                "to_snapshot_time_utc":
                    latest[
                        "snapshot_time_utc"
                    ].isoformat(),

                "from_hours_before_kickoff":
                    float(
                        previous[
                            "hours_before_kickoff"
                        ]
                    ),

                "to_hours_before_kickoff":
                    float(
                        latest[
                            "hours_before_kickoff"
                        ]
                    ),

                "home_movement":
                    home_movement,

                "draw_movement":
                    draw_movement,

                "away_movement":
                    away_movement,

                "movement_magnitude":
                    magnitude,

                "from_market_argmax":
                    from_argmax,

                "to_market_argmax":
                    to_argmax,

                "market_argmax_changed":
                    from_argmax
                    != to_argmax,

                "dominant_direction":
                    direction,

                "movement_state":
                    state,
            })

    return pd.DataFrame(
        records,
        columns=PAIR_COLUMNS,
    )


def build_transitions(
    history: pd.DataFrame,
) -> pd.DataFrame:
    pair_states = build_pair_states(
        history
    )

    records = []

    if pair_states.empty:
        return pd.DataFrame(
            columns=OUTPUT_COLUMNS
        )

    for (
        league,
        event_id,
    ), fixture_pairs in pair_states.groupby(
        [
            "league",
            "event_id",
        ],
        sort=False,
    ):
        fixture_pairs = (
            fixture_pairs
            .sort_values(
                "pair_index"
            )
            .reset_index(drop=True)
        )

        if len(fixture_pairs) < 2:
            continue

        observation_count = (
            len(fixture_pairs) + 1
        )

        transition_count = (
            len(fixture_pairs) - 1
        )

        # Preserve every consecutive state transition.
        # With N observations there are N-1 movement pairs
        # and N-2 state transitions.
        for transition_index in range(
            1,
            len(fixture_pairs),
        ):
            previous = fixture_pairs.iloc[
                transition_index - 1
            ]

            latest = fixture_pairs.iloc[
                transition_index
            ]

            previous_state = str(
                previous["movement_state"]
            )

            latest_state = str(
                latest["movement_state"]
            )

            previous_direction = str(
                previous[
                    "dominant_direction"
                ]
            )

            latest_direction = str(
                latest[
                    "dominant_direction"
                ]
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
                    ],

                "observation_count":
                    observation_count,

                "movement_pair_count":
                    len(fixture_pairs),

                "transition_count":
                    transition_count,

                "previous_pair_index":
                    int(
                        previous[
                            "pair_index"
                        ]
                    ),

                "latest_pair_index":
                    int(
                        latest[
                            "pair_index"
                        ]
                    ),

                "previous_state":
                    previous_state,

                "latest_state":
                    latest_state,

                "previous_direction":
                    previous_direction,

                "latest_direction":
                    latest_direction,

                "previous_movement_magnitude":
                    float(
                        previous[
                            "movement_magnitude"
                        ]
                    ),

                "latest_movement_magnitude":
                    float(
                        latest[
                            "movement_magnitude"
                        ]
                    ),

                "previous_market_argmax":
                    previous[
                        "to_market_argmax"
                    ],

                "latest_market_argmax":
                    latest[
                        "to_market_argmax"
                    ],

                "transition":
                    (
                        previous_state
                        + " -> "
                        + latest_state
                    ),

                "direction_transition":
                    (
                        previous_direction
                        + " -> "
                        + latest_direction
                    ),

                "state_changed":
                    previous_state
                    != latest_state,

                "direction_changed":
                    previous_direction
                    != latest_direction,

                "research_only":
                    True,
            })

    return pd.DataFrame(
        records,
        columns=OUTPUT_COLUMNS,
    )


def write_transitions(
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

    pair_states = build_pair_states(
        history
    )

    transitions = build_transitions(
        history
    )

    write_transitions(
        transitions,
        args.output,
    )

    print("=" * 72)
    print(
        "LA LIGA MARKET TRANSITIONS"
    )
    print("=" * 72)

    print(
        "valid observations:",
        len(history),
    )

    print(
        "movement pairs:",
        len(pair_states),
    )

    print(
        "fixtures with transitions:",
        len(transitions),
    )

    if transitions.empty:
        print(
            "HOLD: at least 3 observations "
            "per fixture are required"
        )
        return

    print()
    print("TRANSITION COUNTS:")

    print(
        transitions[
            "transition"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "STATE CHANGES:",
        int(
            transitions[
                "state_changed"
            ].sum()
        ),
    )

    print()
    print("LATEST TRANSITIONS:")

    columns = [
        "home_team",
        "away_team",
        "observation_count",
        "previous_state",
        "latest_state",
        "transition",
        "previous_movement_magnitude",
        "latest_movement_magnitude",
        "state_changed",
    ]

    print(
        transitions[
            columns
        ]
        .sort_values(
            "latest_movement_magnitude",
            ascending=False,
        )
        .to_string(index=False)
    )

    print()
    print(
        "output:",
        args.output,
    )


if __name__ == "__main__":
    main()
