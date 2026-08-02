import requests

from config import FOOTBALL_DATA_API_KEY

headers = {
    "X-Auth-Token": FOOTBALL_DATA_API_KEY
}

urls = [
    "https://api.football-data.org/v4/competitions/PL",
    "https://api.football-data.org/v4/competitions/PL/teams",
    "https://api.football-data.org/v4/competitions/PL/standings"
]

for url in urls:
    print("=" * 60)
    print(url)

    response = requests.get(url, headers=headers)

    print("Статус:", response.status_code)

    try:
        print(response.json())
    except:
        print(response.text)