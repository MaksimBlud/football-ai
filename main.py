import os
import requests
from dotenv import load_dotenv
from supabase import create_client

# Загружаем переменные окружения
load_dotenv()

# Ключи
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Подключение к Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Запрос к Football-Data API
headers = {
    "X-Auth-Token": API_KEY
}

url = "https://api.football-data.org/v4/competitions/PL/matches"

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
    }

    try:
        result = supabase.table("matches").insert(data).execute()
        print(f"✔ Добавлен матч {match['id']}")
    except Exception as e:
        print(f"⚠ Матч {match['id']} уже существует или произошла ошибка:")
        print(e)

print("Готово!")
