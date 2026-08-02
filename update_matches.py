import requests

from database import supabase
from config import FOOTBALL_DATA_API_KEY

headers = {
    "X-Auth-Token": FOOTBALL_DATA_API_KEY
}

url = "https://api.football-data.org/v4/competitions/PL/teams?season=2026"

response = requests.get(url, headers=headers)

print("Статус:", response.status_code)

if response.status_code != 200:
    print(response.text)
    exit()

matches = response.json()["matches"]

print(f"Получено матчей: {len(matches)}")

for match in matches:
    data = {
        "id": match["id"],
        "home_team": match["homeTeam"]["name"],
        "away_team": match["awayTeam"]["name"],
        "match_date": match["utcDate"],
        "status": match["status"],
        "competition": "Premier League"
    }

    try:
        supabase.table("matches").upsert(
            data,
            on_conflict="id"
        ).execute()

        print(f"✅ {match['homeTeam']['name']} — {match['awayTeam']['name']}")

    except Exception as e:
        print(f"❌ Ошибка для матча {match['id']}: {e}")

print("Готово!")