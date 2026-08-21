from pathlib import Path
import requests
import pandas as pd


OUT_DIR = Path(
    "data/external/football_data_odds"
)
OUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


SEASONS = {
    "2019/2020": "1920",
    "2020/2021": "2021",
    "2021/2022": "2122",
    "2022/2023": "2223",
    "2023/2024": "2324",
    "2024/2025": "2425",
}


BASE = (
    "https://www.football-data.co.uk/"
    "mmz4281/{code}/E0.csv"
)


print("=" * 110)
print(
    "FOOTBALL-DATA.CO.UK — "
    "EPL OPEN/CLOSE ODDS DOWNLOAD"
)
print("=" * 110)


for season, code in SEASONS.items():

    url = BASE.format(
        code=code
    )

    path = (
        OUT_DIR
        / f"EPL_{code}.csv"
    )

    print()
    print(
        f"{season}: {url}"
    )

    r = requests.get(
        url,
        timeout=60,
    )

    r.raise_for_status()

    path.write_bytes(
        r.content
    )

    df = pd.read_csv(
        path
    )

    print(
        f"✅ rows={len(df)} "
        f"cols={len(df.columns)}"
    )

    relevant = [
        c
        for c in df.columns
        if (
            c.startswith("B365")
            or c.startswith("PS")
            or c.startswith("Max")
            or c.startswith("Avg")
        )
    ]

    print(
        "ODDS COLUMNS:"
    )

    for col in relevant:
        print(
            " -",
            col,
        )


print()
print("=" * 110)
print(
    "OPEN/CLOSE COLUMN INVENTORY"
)
print("=" * 110)


all_columns = {}

for season, code in SEASONS.items():

    path = (
        OUT_DIR
        / f"EPL_{code}.csv"
    )

    df = pd.read_csv(
        path,
        nrows=5,
    )

    odds_cols = [
        c
        for c in df.columns
        if any(
            key in c
            for key in [
                "B365",
                "PS",
                "Max",
                "Avg",
            ]
        )
    ]

    all_columns[
        season
    ] = odds_cols


for season, cols in all_columns.items():

    print()
    print(
        season
    )

    for col in cols:
        print(
            " -",
            col,
        )


print()
print("=" * 110)
print(
    "SAMPLE 2024/25"
)
print("=" * 110)

df = pd.read_csv(
    OUT_DIR
    / "EPL_2425.csv"
)

wanted = [
    "Date",
    "HomeTeam",
    "AwayTeam",
    "FTHG",
    "FTAG",
    "FTR",

    "PSH",
    "PSD",
    "PSA",

    "PSCH",
    "PSCD",
    "PSCA",

    "AvgH",
    "AvgD",
    "AvgA",

    "AvgCH",
    "AvgCD",
    "AvgCA",

    "MaxH",
    "MaxD",
    "MaxA",

    "MaxCH",
    "MaxCD",
    "MaxCA",
]

wanted = [
    c
    for c in wanted
    if c in df.columns
]

print(
    df[
        wanted
    ]
    .head(15)
    .to_string(
        index=False
    )
)


print()
print(
    "Сохранено в:",
    OUT_DIR,
)

print(
    "Production-файлы НЕ изменены."
)
