
import requests

from database import supabase
from config import API_FOOTBALL_KEY

url = "https://v3.football.api-sports.io/teams"

headers = {
    "x-apisports-key": API_FOOTBALL_KEY
}

params = {
    "league": 39,
    "season": 2026
}

response = requests.get(url, headers=headers, params=params)

print("Статус:", response.status_code)

if response.status_code != 200:
    print(response.text)
    exit()

data = response.json()

if data.get("errors"):
    print(data["errors"])
    exit()

teams = data["response"]

print(f"Найдено команд: {len(teams)}")

for item in teams:
    team = item["team"]

    row = {
        "api_id": team["id"],
        "name": team["name"],
        "short_name": team["code"],
        "tla": team["code"],
        "crest": team["logo"]
    }

    try:
        existing = (
            supabase.table("teams")
            .select("id")
            .eq("api_id", team["id"])
            .execute()
        )

        if existing.data:
            supabase.table("teams").update(row).eq("api_id", team["id"]).execute()
        else:
            supabase.table("teams").insert(row).execute()

        print(f"✅ {team['name']}")

    except Exception as e:
        print(f"❌ {team['name']}: {e}")

print("Готово!")