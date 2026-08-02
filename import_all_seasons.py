from pathlib import Path

import pandas as pd

from database import supabase


RAW_DIR = Path("data/raw")

SEASONS = {
    "2016_2017": "2016/2017",
    "2017_2018": "2017/2018",
    "2018_2019": "2018/2019",
    "2019_2020": "2019/2020",
    "2020_2021": "2020/2021",
    "2021_2022": "2021/2022",
    "2022_2023": "2022/2023",
    "2023_2024": "2023/2024",
    "2024_2025": "2024/2025",
    "2025_2026": "2025/2026",
}


def value_or_none(row, column):
    if column not in row.index:
        return None

    value = row[column]

    if pd.isna(value):
        return None

    return value


def load_existing_seasons():
    response = (
        supabase
        .table("matches")
        .select("season")
        .execute()
    )

    return {
        row["season"]
        for row in response.data
        if row.get("season")
    }


def parse_date(value):
    return pd.to_datetime(
        value,
        dayfirst=True,
        errors="raise"
    ).strftime("%Y-%m-%d")


existing_seasons = load_existing_seasons()

print("Уже загружены:", sorted(existing_seasons))

for file_key, season_name in SEASONS.items():
    file_path = RAW_DIR / f"epl_{file_key}.csv"

    if season_name in existing_seasons:
        print(f"Пропускаю {season_name}: уже есть в Supabase")
        continue

    print(f"\nОбрабатываю сезон {season_name}...")

    df = pd.read_csv(file_path)

    records = []

    for _, row in df.iterrows():
        record = {
            "season": season_name,
            "league": "EPL",

            "match_date": parse_date(row["Date"]),
            "match_time": value_or_none(row, "Time"),

            "home_team": row["HomeTeam"],
            "away_team": row["AwayTeam"],

            "home_goals": int(row["FTHG"]),
            "away_goals": int(row["FTAG"]),
            "result": row["FTR"],

            "home_shots": value_or_none(row, "HS"),
            "away_shots": value_or_none(row, "AS"),

            "home_shots_target": value_or_none(row, "HST"),
            "away_shots_target": value_or_none(row, "AST"),

            "home_corners": value_or_none(row, "HC"),
            "away_corners": value_or_none(row, "AC"),

            "home_yellow": value_or_none(row, "HY"),
            "away_yellow": value_or_none(row, "AY"),

            "home_red": value_or_none(row, "HR"),
            "away_red": value_or_none(row, "AR"),

            "home_odds": value_or_none(row, "AvgH"),
            "draw_odds": value_or_none(row, "AvgD"),
            "away_odds": value_or_none(row, "AvgA"),
        }

        records.append(record)

    batch_size = 100

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]

        supabase.table("matches").insert(batch).execute()

        print(
            f"Загружено {min(start + batch_size, len(records))}"
            f" из {len(records)}"
        )

    print(f"Сезон {season_name} импортирован.")


print("\nИмпорт завершён.")
