from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parent

INPUT_FILE = (
    ROOT
    / "data"
    / "external"
    / "player_day_panel.csv"
)

MAPPING_FILE = (
    ROOT
    / "data"
    / "external"
    / "player_mapping_tm.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "external"
    / "player_importance_history.csv"
)


USECOLS = [
    "fbref_player_id",
    "date",
    "minutes_played",
    "tm_player_id",
    "games_played",
]


print("=" * 100)
print("BUILD PLAYER IMPORTANCE HISTORY")
print("=" * 100)


mapping = pd.read_csv(MAPPING_FILE)

mapping["season"] = pd.to_numeric(
    mapping["season"],
    errors="coerce",
)

mapping = mapping[
    mapping["season"].between(
        2019,
        2024,
    )
].copy()


epl_ids = set(
    pd.to_numeric(
        mapping["tm_player_id"],
        errors="coerce",
    )
    .dropna()
    .astype(int)
    .unique()
)


print(
    "EPL TM player ids:",
    len(epl_ids),
)


chunks = []

rows_read = 0
rows_kept = 0


for chunk_no, chunk in enumerate(
    pd.read_csv(
        INPUT_FILE,
        usecols=USECOLS,
        chunksize=500_000,
    ),
    start=1,
):

    rows_read += len(chunk)

    chunk["tm_player_id"] = pd.to_numeric(
        chunk["tm_player_id"],
        errors="coerce",
    )

    chunk = chunk[
        chunk["tm_player_id"].isin(
            epl_ids
        )
    ].copy()

    if chunk.empty:
        print(
            f"Chunk {chunk_no}: "
            f"read={rows_read:,} | kept=0"
        )
        continue

    chunk["date"] = pd.to_datetime(
        chunk["date"],
        errors="coerce",
    ).dt.normalize()

    chunk["minutes_played"] = pd.to_numeric(
        chunk["minutes_played"],
        errors="coerce",
    ).fillna(0)

    chunk["games_played"] = pd.to_numeric(
        chunk["games_played"],
        errors="coerce",
    ).fillna(0)

    chunk = chunk.dropna(
        subset=[
            "tm_player_id",
            "date",
        ]
    )

    chunk["tm_player_id"] = (
        chunk["tm_player_id"]
        .astype(int)
    )

    rows_kept += len(chunk)

    chunks.append(
        chunk[
            [
                "tm_player_id",
                "date",
                "minutes_played",
                "games_played",
            ]
        ]
    )

    print(
        f"Chunk {chunk_no}: "
        f"read={rows_read:,} | "
        f"kept_total={rows_kept:,}"
    )


if not chunks:
    raise SystemExit(
        "❌ Не найдено строк EPL игроков."
    )


df = pd.concat(
    chunks,
    ignore_index=True,
)


# ============================================================
# COLLAPSE TO PLAYER-DAY
# ============================================================

df = (
    df
    .groupby(
        [
            "tm_player_id",
            "date",
        ],
        as_index=False,
    )
    .agg(
        minutes_played=(
            "minutes_played",
            "max",
        ),
        games_played=(
            "games_played",
            "max",
        ),
    )
)


df = df.sort_values(
    [
        "tm_player_id",
        "date",
    ]
).reset_index(drop=True)


# ============================================================
# POINT-IN-TIME CUMULATIVE IMPORTANCE
#
# Значение на дату D включает только данные
# до предыдущих дат.
# ============================================================

df[
    "career_minutes_before_date"
] = (
    df
    .groupby("tm_player_id")[
        "minutes_played"
    ]
    .cumsum()
    - df["minutes_played"]
)


df[
    "career_games_before_date"
] = (
    df
    .groupby("tm_player_id")[
        "games_played"
    ]
    .cummax()
)


# ============================================================
# ROLLING 365 DAYS MINUTES
# ============================================================

rolling_rows = []

for player_id, group in df.groupby(
    "tm_player_id",
    sort=False,
):

    group = group.sort_values(
        "date"
    ).copy()

    series = (
        group
        .set_index("date")[
            "minutes_played"
        ]
    )

    rolling = (
        series
        .rolling(
            "365D",
            closed="left",
        )
        .sum()
        .fillna(0)
        .to_numpy()
    )

    temp = group[
        [
            "tm_player_id",
            "date",
        ]
    ].copy()

    temp[
        "minutes_prev_365d"
    ] = rolling

    rolling_rows.append(temp)


rolling_df = pd.concat(
    rolling_rows,
    ignore_index=True,
)


result = df.merge(
    rolling_df,
    on=[
        "tm_player_id",
        "date",
    ],
    how="left",
    validate="one_to_one",
)


result.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 100)
print("PLAYER IMPORTANCE HISTORY CREATED")
print("=" * 100)

print("Строк:", len(result))

print(
    "Уникальных игроков:",
    result["tm_player_id"].nunique(),
)

print(
    "Дата min:",
    result["date"].min(),
)

print(
    "Дата max:",
    result["date"].max(),
)


print()
print("Колонки:")

for col in result.columns:
    print(" -", col)


print()
print("=" * 100)
print("SANITY CHECK")
print("=" * 100)

sample = (
    result[
        result[
            "career_minutes_before_date"
        ] > 0
    ]
    .sort_values(
        "career_minutes_before_date",
        ascending=False,
    )
    .head(20)
)

print(
    sample.to_string(
        index=False
    )
)


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
