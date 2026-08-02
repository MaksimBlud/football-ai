import requests

from database import supabase
from config import FOOTBALL_DATA_API_KEY

headers = {
    "X-Auth-Token": FOOTBALL_DATA_API_KEY
}

url = "https://api.football-data.org/v4/competitions/PL/standings"

response = requests.get(url, headers=headers)

print("Статус:", response.status_code)

if response.status_code != 200:
    print(response.text)
    exit()

table = response.json()["standings"][0]["table"]

print(f"Найдено команд: {len(table)}")

for row in table:
    api_team_id = row["team"]["id"]

    # Ищем команду в нашей базе по api_id
    team = (
        supabase.table("teams")
        .select("id")
        .eq("api_id", api_team_id)
        .execute()
    )

    if len(team.data) == 0:
        print(f"❌ Команда {row['team']['name']} не найдена в таблице teams")
        continue

    db_team_id = team.data[0]["id"]

    data = {
        "team_id": db_team_id,
        "position": row["position"],
        "played_games": row["playedGames"],
        "won": row["won"],
        "draw": row["draw"],
        "lost": row["lost"],
        "goals_for": row["goalsFor"],
        "goals_against": row["goalsAgainst"],
        "goal_difference": row["goalDifference"],
        "points": row["points"]
    }

    try:
        supabase.table("standings").upsert(
            data,
            on_conflict="team_id"
        ).execute()

        print(f"✅ {row['team']['name']}")

    except Exception as e:
        print(f"❌ Ошибка для {row['team']['name']}: {e}")

print("Готово!")