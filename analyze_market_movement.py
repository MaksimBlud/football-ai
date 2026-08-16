import pandas as pd

from database import supabase


TABLE = "odds_snapshots"


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
)

df["commence_time_utc"] = pd.to_datetime(
    df["commence_time_utc"],
    utc=True,
)


rows = []

for event_id, group in df.groupby(
    "event_id"
):

    group = group.sort_values(
        "snapshot_time_utc"
    )

    first = group.iloc[0]
    last = group.iloc[-1]

    home_move = (
        last["home_probability"]
        - first["home_probability"]
    )

    draw_move = (
        last["draw_probability"]
        - first["draw_probability"]
    )

    away_move = (
        last["away_probability"]
        - first["away_probability"]
    )

    moves = {
        "HOME": home_move,
        "DRAW": draw_move,
        "AWAY": away_move,
    }

    strongest_side = max(
        moves,
        key=lambda x: abs(moves[x]),
    )

    strongest_move = moves[
        strongest_side
    ]

    observation_hours = (
        last["snapshot_time_utc"]
        - first["snapshot_time_utc"]
    ).total_seconds() / 3600

    rows.append({
        "event_id": event_id,

        "home_team":
            last["home_team"],

        "away_team":
            last["away_team"],

        "commence_time_utc":
            last["commence_time_utc"],

        "snapshots":
            len(group),

        "first_snapshot":
            first["snapshot_time_utc"],

        "last_snapshot":
            last["snapshot_time_utc"],

        "observation_hours":
            observation_hours,

        "home_first":
            first["home_probability"],

        "home_last":
            last["home_probability"],

        "home_move":
            home_move,

        "draw_first":
            first["draw_probability"],

        "draw_last":
            last["draw_probability"],

        "draw_move":
            draw_move,

        "away_first":
            first["away_probability"],

        "away_last":
            last["away_probability"],

        "away_move":
            away_move,

        "strongest_side":
            strongest_side,

        "strongest_move":
            strongest_move,

        "max_abs_move":
            max(
                abs(home_move),
                abs(draw_move),
                abs(away_move),
            ),
    })


movement = pd.DataFrame(
    rows
)

movement = movement.sort_values(
    [
        "commence_time_utc",
        "max_abs_move",
    ],
    ascending=[
        True,
        False,
    ],
).reset_index(drop=True)


print("=" * 100)
print("EPL MARKET MOVEMENT")
print("=" * 100)

print(
    "Матчей:",
    len(movement)
)

print(
    "Всего snapshot-строк:",
    len(df)
)

print(
    "Уникальных snapshot times:",
    df[
        "snapshot_time_utc"
    ].nunique()
)

print()


for _, row in movement.iterrows():

    print(
        row["home_team"],
        "-",
        row["away_team"],
    )

    print(
        " kickoff:",
        row[
            "commence_time_utc"
        ],
    )

    print(
        " snapshots:",
        row["snapshots"],
        "| observation:",
        f"{row['observation_hours']:.2f} h",
    )

    print(
        " HOME:",
        f"{row['home_first']:.3%}",
        "->",
        f"{row['home_last']:.3%}",
        "|",
        f"{row['home_move']:+.3%}",
    )

    print(
        " DRAW:",
        f"{row['draw_first']:.3%}",
        "->",
        f"{row['draw_last']:.3%}",
        "|",
        f"{row['draw_move']:+.3%}",
    )

    print(
        " AWAY:",
        f"{row['away_first']:.3%}",
        "->",
        f"{row['away_last']:.3%}",
        "|",
        f"{row['away_move']:+.3%}",
    )

    print(
        " strongest:",
        row["strongest_side"],
        f"{row['strongest_move']:+.3%}",
    )

    print()


print("=" * 100)
print("SUMMARY")
print("=" * 100)

print(
    "Средний max abs move:",
    f"{movement['max_abs_move'].mean():.4%}",
)

print(
    "Median max abs move:",
    f"{movement['max_abs_move'].median():.4%}",
)

print(
    "Maximum:",
    f"{movement['max_abs_move'].max():.4%}",
)

print()

for threshold in [
    0.001,
    0.0025,
    0.005,
    0.01,
    0.02,
]:

    n = (
        movement[
            "max_abs_move"
        ]
        >= threshold
    ).sum()

    print(
        f">= {threshold:.2%}:",
        n,
    )


print()
print(
    "The Odds API НЕ вызывался."
)
print(
    "Файлы данных НЕ изменены."
)
