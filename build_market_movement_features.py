import pandas as pd

from database import supabase


TABLE = "odds_snapshots"

OUTPUT = (
    "data/market_movement_features.csv"
)


# ============================================================
# LOAD
# ============================================================

response = (
    supabase
    .table(TABLE)
    .select("*")
    .order(
        "snapshot_time_utc",
        desc=False,
    )
    .execute()
)

df = pd.DataFrame(
    response.data or []
)

if df.empty:
    raise SystemExit(
        "В odds_snapshots нет данных."
    )


df["snapshot_time_utc"] = pd.to_datetime(
    df["snapshot_time_utc"],
    utc=True,
    errors="coerce",
)

df["commence_time_utc"] = pd.to_datetime(
    df["commence_time_utc"],
    utc=True,
    errors="coerce",
)


probability_columns = [
    "home_probability",
    "draw_probability",
    "away_probability",
]

df = df.dropna(
    subset=[
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
        *probability_columns,
    ]
).copy()

df = df.sort_values(
    [
        "event_id",
        "snapshot_time_utc",
    ]
).reset_index(drop=True)


# ============================================================
# BASIC TIME FEATURES
# ============================================================

df["hours_to_kickoff"] = (
    (
        df["commence_time_utc"]
        - df["snapshot_time_utc"]
    )
    .dt.total_seconds()
    / 3600
)


# ============================================================
# TREND HELPERS
# ============================================================


def movement_sign(value, eps=1e-12):
    if value > eps:
        return 1

    if value < -eps:
        return -1

    return 0


def strict_streak(values):
    signs = [
        movement_sign(value)
        for value in values
    ]

    if not signs:
        return 0

    last = signs[-1]

    if last == 0:
        return 0

    streak = 0

    for current in reversed(signs):
        if current != last:
            break

        streak += 1

    return last * streak


def direction_changes(values):
    signs = [
        movement_sign(value)
        for value in values
    ]

    nonzero = [
        value
        for value in signs
        if value != 0
    ]

    if len(nonzero) < 2:
        return 0

    return sum(
        1
        for previous, current
        in zip(
            nonzero[:-1],
            nonzero[1:],
        )
        if previous != current
    )


# ============================================================
# PER-EVENT MOVEMENT FEATURES
# ============================================================

parts = []

for event_id, group in df.groupby(
    "event_id",
    sort=False,
):

    group = group.sort_values(
        "snapshot_time_utc"
    ).copy()

    group["snapshot_number"] = (
        range(
            1,
            len(group) + 1,
        )
    )

    first_time = (
        group["snapshot_time_utc"]
        .iloc[0]
    )

    group["observation_hours"] = (
        (
            group["snapshot_time_utc"]
            - first_time
        )
        .dt.total_seconds()
        / 3600
    )


    for side in [
        "home",
        "draw",
        "away",
    ]:

        probability = (
            f"{side}_probability"
        )

        first_probability = (
            group[probability]
            .iloc[0]
        )

        # Current probability minus first snapshot.
        group[
            f"{side}_move_from_first"
        ] = (
            group[probability]
            - first_probability
        )

        # Current probability minus immediately previous snapshot.
        group[
            f"{side}_move_from_previous"
        ] = (
            group[probability]
            .diff()
            .fillna(0.0)
        )

        # Hours since previous observation.
        hours_since_previous = (
            group[
                "snapshot_time_utc"
            ]
            .diff()
            .dt.total_seconds()
            .div(3600)
        )

        # Movement per hour since previous snapshot.
        group[
            f"{side}_velocity"
        ] = (
            group[
                f"{side}_move_from_previous"
            ]
            / hours_since_previous
        )

        group[
            f"{side}_velocity"
        ] = (
            group[
                f"{side}_velocity"
            ]
            .replace(
                [
                    float("inf"),
                    float("-inf"),
                ],
                0.0,
            )
            .fillna(0.0)
        )

        # ----------------------------------------------------
        # Trend quality up to each current snapshot.
        # Uses only information available at that point.
        # ----------------------------------------------------

        move_values = (
            group[
                f"{side}_move_from_previous"
            ]
            .astype(float)
            .tolist()
        )

        strict_streak_values = []
        direction_change_values = []
        total_path_values = []
        efficiency_values = []

        for position in range(
            len(group)
        ):

            # First row has no actual transition.
            transitions = (
                move_values[
                    1:position + 1
                ]
            )

            current_total_move = float(
                group[
                    f"{side}_move_from_first"
                ].iloc[position]
            )

            total_path = sum(
                abs(value)
                for value in transitions
            )

            if total_path > 0:
                efficiency = (
                    abs(current_total_move)
                    / total_path
                )
            else:
                efficiency = 0.0

            strict_streak_values.append(
                strict_streak(
                    transitions
                )
            )

            direction_change_values.append(
                direction_changes(
                    transitions
                )
            )

            total_path_values.append(
                total_path
            )

            efficiency_values.append(
                efficiency
            )

        group[
            f"{side}_strict_streak"
        ] = strict_streak_values

        group[
            f"{side}_direction_changes"
        ] = direction_change_values

        group[
            f"{side}_total_path"
        ] = total_path_values

        group[
            f"{side}_movement_efficiency"
        ] = efficiency_values


    move_first_columns = [
        "home_move_from_first",
        "draw_move_from_first",
        "away_move_from_first",
    ]

    move_previous_columns = [
        "home_move_from_previous",
        "draw_move_from_previous",
        "away_move_from_previous",
    ]

    group["max_abs_move_from_first"] = (
        group[
            move_first_columns
        ]
        .abs()
        .max(axis=1)
    )

    group["max_abs_move_from_previous"] = (
        group[
            move_previous_columns
        ]
        .abs()
        .max(axis=1)
    )


    def strongest_side(row):
        values = {
            "HOME":
                row[
                    "home_move_from_first"
                ],
            "DRAW":
                row[
                    "draw_move_from_first"
                ],
            "AWAY":
                row[
                    "away_move_from_first"
                ],
        }

        return max(
            values,
            key=lambda side: abs(
                values[side]
            ),
        )


    group["strongest_movement_side"] = (
        group.apply(
            strongest_side,
            axis=1,
        )
    )

    parts.append(group)


features = pd.concat(
    parts,
    ignore_index=True,
)


# ============================================================
# OUTPUT COLUMNS
# ============================================================

columns = [
    "event_id",
    "home_team",
    "away_team",
    "commence_time_utc",
    "snapshot_time_utc",

    "snapshot_number",
    "hours_to_kickoff",
    "observation_hours",

    "bookmakers_count",

    "home_odds",
    "draw_odds",
    "away_odds",

    "home_probability",
    "draw_probability",
    "away_probability",

    "home_move_from_first",
    "draw_move_from_first",
    "away_move_from_first",

    "home_move_from_previous",
    "draw_move_from_previous",
    "away_move_from_previous",

    "home_velocity",
    "draw_velocity",
    "away_velocity",

    "home_strict_streak",
    "draw_strict_streak",
    "away_strict_streak",

    "home_direction_changes",
    "draw_direction_changes",
    "away_direction_changes",

    "home_total_path",
    "draw_total_path",
    "away_total_path",

    "home_movement_efficiency",
    "draw_movement_efficiency",
    "away_movement_efficiency",

    "max_abs_move_from_first",
    "max_abs_move_from_previous",

    "strongest_movement_side",
]

features = features[
    columns
].copy()

features.to_csv(
    OUTPUT,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print("=" * 100)
print("MARKET MOVEMENT FEATURES BUILT")
print("=" * 100)

print(
    "Snapshot rows:",
    len(features),
)

print(
    "Events:",
    features[
        "event_id"
    ].nunique(),
)

print(
    "Snapshots:",
    features[
        "snapshot_time_utc"
    ].nunique(),
)

print(
    "Output:",
    OUTPUT,
)

print()
print("=" * 100)
print("LATEST ROW PER EVENT")
print("=" * 100)

latest = (
    features
    .sort_values(
        "snapshot_time_utc"
    )
    .groupby(
        "event_id",
        as_index=False,
    )
    .tail(1)
    .sort_values(
        "max_abs_move_from_first",
        ascending=False,
    )
)

show = latest[
    [
        "home_team",
        "away_team",
        "snapshot_number",
        "hours_to_kickoff",
        "home_move_from_first",
        "draw_move_from_first",
        "away_move_from_first",
        "max_abs_move_from_first",
        "strongest_movement_side",
    ]
].copy()

print(
    show.to_string(
        index=False,
        formatters={
            "hours_to_kickoff":
                lambda x: f"{x:.1f}",

            "home_move_from_first":
                lambda x: f"{x:+.3%}",

            "draw_move_from_first":
                lambda x: f"{x:+.3%}",

            "away_move_from_first":
                lambda x: f"{x:+.3%}",

            "max_abs_move_from_first":
                lambda x: f"{x:.3%}",
        }
    )
)


print()
print("=" * 100)
print("SANITY CHECK")
print("=" * 100)

first_rows = (
    features[
        "snapshot_number"
    ]
    == 1
)

first_movement = (
    features.loc[
        first_rows,
        [
            "home_move_from_first",
            "draw_move_from_first",
            "away_move_from_first",
        ],
    ]
    .abs()
    .to_numpy()
    .max()
)

print(
    "First snapshot max movement:",
    first_movement,
)

print(
    "Negative hours_to_kickoff:",
    int(
        (
            features[
                "hours_to_kickoff"
            ]
            < 0
        ).sum()
    ),
)

print(
    "Duplicate event+snapshot:",
    int(
        features.duplicated(
            subset=[
                "event_id",
                "snapshot_time_utc",
            ]
        ).sum()
    ),
)


print()
print("The Odds API НЕ вызывался.")
print("Supabase только прочитан.")
print(
    "Production model НЕ изменена."
)
