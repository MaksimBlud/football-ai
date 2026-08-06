import requests
import pandas as pd


LEAGUE = "EPL"
SEASONS = list(range(2019, 2026))
OUTPUT = "data/understat_xg.csv"


def download_season(season):
    url = (
        f"https://understat.com/"
        f"getLeagueData/{LEAGUE}/{season}"
    )

    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": (
                f"https://understat.com/"
                f"league/{LEAGUE}/{season}"
            ),
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    rows = []

    for team_data in data["teams"].values():
        team_name = team_data["title"]

        for match in team_data["history"]:
            rows.append({
                "season_start": season,
                "team": team_name,
                "venue": match["h_a"],
                "match_date": match["date"],
                "xg": match["xG"],
                "xga": match["xGA"],
                "npxg": match["npxG"],
                "npxga": match["npxGA"],
                "scored": match["scored"],
                "conceded": match["missed"],
                "result": match["result"],
            })

    return rows


all_rows = []

for season in SEASONS:
    print(f"Загружаю сезон {season}/{season + 1}...")

    season_rows = download_season(season)

    all_rows.extend(season_rows)

    print("Строк получено:", len(season_rows))


df = pd.DataFrame(all_rows)

df["match_date"] = pd.to_datetime(
    df["match_date"],
    errors="coerce",
)

df = df.sort_values(
    ["match_date", "team"]
).reset_index(drop=True)

df.to_csv(
    OUTPUT,
    index=False,
)

print()
print("Файл создан:", OUTPUT)
print("Строк:", len(df))
print("Сезонов:", df["season_start"].nunique())
