"""Analyze La Liga temporal market behavior.

Research-only.

Derives descriptive fixture-level behavior from complete transition history:
- persistence;
- fade;
- reversal;
- argmax stability.

No API calls, no database writes, no production model usage.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_INPUT = Path(
    "experiments/la_liga_market_transitions.csv"
)

DEFAULT_OUTPUT = Path(
    "experiments/la_liga_temporal_behavior.csv"
)

DIRECTIONAL_STATES = {
    "HOME_STEAM": "H",
    "DRAW_STEAM": "D",
    "AWAY_STEAM": "A",
}

OUTPUT_COLUMNS = [
    "league",
    "event_id",
    "home_team",
    "away_team",
    "commence_time_utc",
    "observation_count",
    "transition_rows",
    "state_sequence",
    "direction_sequence",
    "latest_state",
    "latest_direction",
    "directional_state_count",
    "persistent_direction",
    "persistent_direction_count",
    "has_persistence",
    "has_fade",
    "has_reversal",
    "reversal_count",
    "argmax_changed_count",
    "argmax_stable",
    "behavior_state",
    "research_only",
]


def load_transitions(
    path: Path = DEFAULT_INPUT,
) -> pd.DataFrame:
    frame = pd.read_csv(path)

    required = {
        "league",
        "event_id",
        "home_team",
        "away_team",
        "commence_time_utc",
        "observation_count",
        "previous_pair_index",
        "latest_pair_index",
        "previous_state",
        "latest_state",
        "previous_direction",
        "latest_direction",
        "previous_market_argmax",
        "latest_market_argmax",
        "transition",
    }

    missing = required - set(
        frame.columns
    )

    if missing:
        raise ValueError(
            "Transition data missing columns: "
            + ", ".join(sorted(missing))
        )

    frame = frame.copy()

    frame = frame.drop_duplicates(
        subset=[
            "league",
            "event_id",
            "previous_pair_index",
            "latest_pair_index",
        ],
        keep="last",
    )

    return frame.sort_values(
        [
            "league",
            "event_id",
            "latest_pair_index",
        ]
    ).reset_index(drop=True)


def _state_sequence(
    fixture: pd.DataFrame,
) -> list[str]:
    fixture = fixture.sort_values(
        "latest_pair_index"
    )

    first = str(
        fixture.iloc[0][
            "previous_state"
        ]
    )

    rest = [
        str(value)
        for value in fixture[
            "latest_state"
        ].tolist()
    ]

    return [first, *rest]


def _direction_for_state(
    state: str,
) -> str:
    return DIRECTIONAL_STATES.get(
        state,
        "NONE",
    )


def analyze_fixture(
    fixture: pd.DataFrame,
) -> dict:
    fixture = fixture.sort_values(
        "latest_pair_index"
    ).reset_index(drop=True)

    states = _state_sequence(
        fixture
    )

    directions = [
        _direction_for_state(state)
        for state in states
    ]

    directional = [
        direction
        for direction in directions
        if direction != "NONE"
    ]

    persistent_direction = "NONE"
    persistent_direction_count = 0

    if directional:
        latest_direction = directional[-1]

        count = 0

        for direction in reversed(
            directional
        ):
            if direction == latest_direction:
                count += 1
            else:
                break

        if count >= 2:
            persistent_direction = (
                latest_direction
            )
            persistent_direction_count = (
                count
            )

    has_persistence = (
        persistent_direction_count >= 2
    )

    has_fade = False

    for previous, latest in zip(
        states,
        states[1:],
    ):
        if (
            previous in DIRECTIONAL_STATES
            and latest == "NO_CHANGE"
        ):
            has_fade = True
            break

    reversal_count = 0

    last_direction = None

    for direction in directional:
        if (
            last_direction is not None
            and direction != last_direction
        ):
            reversal_count += 1

        last_direction = direction

    has_reversal = (
        reversal_count > 0
    )

    argmax_changed_count = 0

    for _, row in fixture.iterrows():
        if (
            str(
                row[
                    "previous_market_argmax"
                ]
            )
            != str(
                row[
                    "latest_market_argmax"
                ]
            )
        ):
            argmax_changed_count += 1

    argmax_stable = (
        argmax_changed_count == 0
    )

    latest_state = states[-1]

    latest_direction = (
        _direction_for_state(
            latest_state
        )
    )

    if has_reversal:
        behavior_state = "REVERSAL"

    elif has_persistence:
        behavior_state = (
            "PERSISTENT_"
            + persistent_direction
        )

    elif has_fade:
        behavior_state = "FADE"

    elif latest_state == "NO_CHANGE":
        behavior_state = "STABLE"

    else:
        behavior_state = (
            "ACTIVE_"
            + latest_state
        )

    latest_row = fixture.iloc[-1]

    return {
        "league":
            latest_row["league"],

        "event_id":
            latest_row["event_id"],

        "home_team":
            latest_row["home_team"],

        "away_team":
            latest_row["away_team"],

        "commence_time_utc":
            latest_row[
                "commence_time_utc"
            ],

        "observation_count":
            int(
                latest_row[
                    "observation_count"
                ]
            ),

        "transition_rows":
            len(fixture),

        "state_sequence":
            " -> ".join(states),

        "direction_sequence":
            " -> ".join(
                directions
            ),

        "latest_state":
            latest_state,

        "latest_direction":
            latest_direction,

        "directional_state_count":
            len(directional),

        "persistent_direction":
            persistent_direction,

        "persistent_direction_count":
            persistent_direction_count,

        "has_persistence":
            has_persistence,

        "has_fade":
            has_fade,

        "has_reversal":
            has_reversal,

        "reversal_count":
            reversal_count,

        "argmax_changed_count":
            argmax_changed_count,

        "argmax_stable":
            argmax_stable,

        "behavior_state":
            behavior_state,

        "research_only":
            True,
    }


def build_behavior_summary(
    transitions: pd.DataFrame,
) -> pd.DataFrame:
    records = []

    for (
        league,
        event_id,
    ), fixture in transitions.groupby(
        [
            "league",
            "event_id",
        ],
        sort=False,
    ):
        records.append(
            analyze_fixture(
                fixture
            )
        )

    return pd.DataFrame(
        records,
        columns=OUTPUT_COLUMNS,
    )


def write_summary(
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
        default=DEFAULT_INPUT,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    args = parser.parse_args()

    transitions = load_transitions(
        args.input
    )

    summary = build_behavior_summary(
        transitions
    )

    write_summary(
        summary,
        args.output,
    )

    print("=" * 72)
    print(
        "LA LIGA TEMPORAL BEHAVIOR"
    )
    print("=" * 72)

    print(
        "fixtures:",
        len(summary),
    )

    if summary.empty:
        print(
            "HOLD: no transition history"
        )
        return

    print()
    print(
        "BEHAVIOR COUNTS:"
    )

    print(
        summary[
            "behavior_state"
        ]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "persistence:",
        int(
            summary[
                "has_persistence"
            ].sum()
        ),
    )

    print(
        "fades:",
        int(
            summary[
                "has_fade"
            ].sum()
        ),
    )

    print(
        "reversals:",
        int(
            summary[
                "has_reversal"
            ].sum()
        ),
    )

    print(
        "argmax unstable:",
        int(
            (
                ~summary[
                    "argmax_stable"
                ].astype(bool)
            ).sum()
        ),
    )

    print()
    print(
        summary[
            [
                "home_team",
                "away_team",
                "state_sequence",
                "behavior_state",
                "persistent_direction",
                "reversal_count",
                "argmax_stable",
            ]
        ].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
