"""Build local historical La Liga dataset from Football-Data CSVs.

Research-only:
- downloads public historical CSV files;
- writes only under data/;
- performs no Supabase writes;
- performs no training;
- performs no model promotion.
"""

from __future__ import annotations

from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd


DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "la_liga_raw"

OUTPUT = DATA_DIR / "la_liga_official_history_2016_2026.csv"

SEASONS = {
    "1617": "2016-2017",
    "1718": "2017-2018",
    "1819": "2018-2019",
    "1920": "2019-2020",
    "2021": "2020-2021",
    "2122": "2021-2022",
    "2223": "2022-2023",
    "2324": "2023-2024",
    "2425": "2024-2025",
    "2526": "2025-2026",
}

BASE_URL = (
    "https://www.football-data.co.uk/"
    "mmz4281/{code}/SP1.csv"
)

COLUMN_MAP = {
    "Date": "match_date",
    "Time": "match_time",
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",
    "FTHG": "home_goals",
    "FTAG": "away_goals",
    "FTR": "result",
    "HS": "home_shots",
    "AS": "away_shots",
    "HST": "home_shots_target",
    "AST": "away_shots_target",
    "HC": "home_corners",
    "AC": "away_corners",
    "HY": "home_yellow",
    "AY": "away_yellow",
    "HR": "home_red",
    "AR": "away_red",
    "B365H": "home_odds",
    "B365D": "draw_odds",
    "B365A": "away_odds",
}

OUTPUT_COLUMNS = [
    "match_id",
    "season",
    "league",
    "match_date",
    "match_time",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
    "home_shots",
    "away_shots",
    "home_shots_target",
    "away_shots_target",
    "home_corners",
    "away_corners",
    "home_yellow",
    "away_yellow",
    "home_red",
    "away_red",
    "home_odds",
    "draw_odds",
    "away_odds",
]


def download(
    url: str,
    path: Path,
) -> None:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 football-ai-research"
            )
        },
    )

    with urlopen(
        request,
        timeout=30,
    ) as response:
        content = response.read()

    if len(content) < 1000:
        raise RuntimeError(
            f"Downloaded file suspiciously small: "
            f"{url} ({len(content)} bytes)"
        )

    path.write_bytes(content)


def normalize(
    path: Path,
    *,
    season: str,
) -> pd.DataFrame:
    source = pd.read_csv(
        path,
        encoding_errors="replace",
    )

    required = {
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "FTR",
    }

    missing = required - set(
        source.columns
    )

    if missing:
        raise ValueError(
            f"{path}: missing {sorted(missing)}"
        )

    frame = pd.DataFrame()

    for source_col, target_col in (
        COLUMN_MAP.items()
    ):
        if source_col in source.columns:
            frame[target_col] = (
                source[source_col]
            )
        else:
            frame[target_col] = pd.NA

    frame["match_date"] = (
        pd.to_datetime(
            frame["match_date"],
            dayfirst=True,
            errors="coerce",
        )
    )

    frame = frame.dropna(
        subset=[
            "match_date",
            "home_team",
            "away_team",
            "home_goals",
            "away_goals",
            "result",
        ]
    ).copy()

    frame["match_date"] = (
        frame["match_date"]
        .dt.strftime("%Y-%m-%d")
    )

    frame["match_time"] = (
        frame["match_time"]
        .fillna("00:00")
        .astype(str)
    )

    numeric = [
        "home_goals",
        "away_goals",
        "home_shots",
        "away_shots",
        "home_shots_target",
        "away_shots_target",
        "home_corners",
        "away_corners",
        "home_yellow",
        "away_yellow",
        "home_red",
        "away_red",
        "home_odds",
        "draw_odds",
        "away_odds",
    ]

    for column in numeric:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    integer_defaults = [
        "home_shots",
        "away_shots",
        "home_shots_target",
        "away_shots_target",
        "home_corners",
        "away_corners",
        "home_yellow",
        "away_yellow",
        "home_red",
        "away_red",
    ]

    for column in integer_defaults:
        frame[column] = (
            frame[column]
            .fillna(0)
        )

    frame["season"] = season
    frame["league"] = "LA_LIGA"

    frame["match_id"] = (
        "LA_LIGA:"
        + frame["season"].astype(str)
        + ":"
        + frame["match_date"].astype(str)
        + ":"
        + frame["home_team"].astype(str)
        + ":"
        + frame["away_team"].astype(str)
    )

    return frame[
        OUTPUT_COLUMNS
    ].copy()


def main() -> None:
    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    datasets = []

    print("=" * 72)
    print("LA LIGA HISTORICAL DATASET BUILD")
    print("=" * 72)

    for code, season in (
        SEASONS.items()
    ):
        url = BASE_URL.format(
            code=code
        )

        raw_path = (
            RAW_DIR
            / f"SP1_{season}.csv"
        )

        if not raw_path.exists():
            print(
                "download:",
                season,
                url,
            )

            download(
                url,
                raw_path,
            )

        else:
            print(
                "cached:",
                season,
            )

        frame = normalize(
            raw_path,
            season=season,
        )

        print(
            f"{season}:",
            len(frame),
            "matches",
        )

        datasets.append(frame)

    combined = pd.concat(
        datasets,
        ignore_index=True,
    )

    duplicates = int(
        combined.duplicated(
            subset=[
                "season",
                "match_date",
                "home_team",
                "away_team",
            ]
        ).sum()
    )

    if duplicates:
        raise RuntimeError(
            f"Duplicate fixtures: {duplicates}"
        )

    combined = (
        combined
        .sort_values(
            [
                "match_date",
                "match_time",
                "home_team",
            ]
        )
        .reset_index(drop=True)
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    combined.to_csv(
        OUTPUT,
        index=False,
    )

    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)

    print(
        "rows:",
        len(combined),
    )

    print(
        "seasons:",
        combined["season"].nunique(),
    )

    print(
        "teams:",
        len(
            set(combined["home_team"])
            | set(combined["away_team"])
        ),
    )

    print(
        "date range:",
        combined["match_date"].min(),
        "->",
        combined["match_date"].max(),
    )

    print(
        "duplicates:",
        duplicates,
    )

    print()
    print("rows per season:")

    print(
        combined[
            "season"
        ]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print(
        "output:",
        OUTPUT,
    )


if __name__ == "__main__":
    main()
