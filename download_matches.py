
import requests
import os
import json
from datetime import datetime

from config import FOOTBALL_DATA_API_KEY

headers = {
    "X-Auth-Token": FOOTBALL_DATA_API_KEY
}

url = "https://api.football-data.org/v4/competitions/PL/matches"

response = requests.get(url, headers=headers)

print("Статус:", response.status_code)

if response.status_code != 200:
    print(response.text)
    exit()

os.makedirs("data/raw", exist_ok=True)

filename = f"data/raw/pl_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

with open(filename, "w", encoding="utf-8") as f:
    json.dump(response.json(), f, ensure_ascii=False, indent=2)

