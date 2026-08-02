from pathlib import Path

import pandas as pd
import requests


SEASONS = [
    ("1617", "2016_2017"),
    ("1718", "2017_2018"),
    ("1819", "2018_2019"),
    ("1920", "2019_2020"),
    ("2021", "2020_2021"),
    ("2122", "2021_2022"),
    ("2223", "2022_2023"),
    ("2324", "2023_2024"),
    ("2425", "2024_2025"),
    ("2526", "2025_2026"),
]

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


for url_season, file_season in SEASONS:
    url = (
        "https://www.football-data.co.uk/"
        f"mmz4281/{url_season}/E0.csv"
    )

    file_path = RAW_DIR / f"epl_{file_season}.csv"

    print(f"Скачиваю сезон {file_season}...")

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    file_path.write_bytes(response.content)

    df = pd.read_csv(file_path)

    print(
        f"Сохранён {file_path}. "
        f"Матчей: {len(df)}"
    )


print("Загрузка сезонов завершена.")
