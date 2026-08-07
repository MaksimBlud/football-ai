import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd
import requests
from bs4 import BeautifulSoup


URL = (
    "https://www.premierleague.com/en/news/"
    "4675097/all-380-fixtures-for-202627-premier-league-season"
)

OUTPUT = "data/upcoming_matches.csv"

UK_TIMEZONE = ZoneInfo("Europe/London")

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

EPL_TEAMS = {
    "AFC Bournemouth",
    "Arsenal",
    "Aston Villa",
    "Brentford",
    "Brighton & Hove Albion",
    "Chelsea",
    "Coventry City",
    "Crystal Palace",
    "Everton",
    "Fulham",
    "Hull City",
    "Ipswich Town",
    "Leeds United",
    "Liverpool",
    "Manchester City",
    "Manchester United",
    "Newcastle United",
    "Nottingham Forest",
    "Sunderland",
    "Tottenham Hotspur",
}


TEAM_NAME_MAP = {
    "AFC Bournemouth": "Bournemouth",
    "Brighton & Hove Albion": "Brighton",
    "Ipswich Town": "Ipswich",
    "Hull City": "Hull",
    "Leeds United": "Leeds",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
}


def season_year(month):
    if month >= 8:
        return 2026

    return 2027


print("Загружаю официальный календарь Premier League...")

response = requests.get(
    URL,
    headers={
        "User-Agent": "Mozilla/5.0",
    },
    timeout=30,
)

print("Статус:", response.status_code)

response.raise_for_status()

soup = BeautifulSoup(
    response.text,
    "html.parser",
)

text = soup.get_text(
    "\n",
    strip=True,
)

lines = [
    line.strip()
    for line in text.splitlines()
    if line.strip()
]

date_pattern = re.compile(
    r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
    r"\s+(\d{1,2})\s+"
    r"(" + "|".join(MONTHS.keys()) + r")"
    r"(?:\s+(\d{4}))?$"
)

match_pattern = re.compile(
    r"^(?:(\d{2}:\d{2})\s+)?"
    r"(.+?)\s+v\s+(.+?)"
    r"(?:\s+\([^)]*\))?$"
)

current_date = None
current_weekday = None

rows = []

for line in lines:
    date_match = date_pattern.match(line)

    if date_match:
        current_weekday = date_match.group(1)

        day = int(
            date_match.group(2)
        )

        month_name = date_match.group(3)
        month = MONTHS[month_name]

        explicit_year = date_match.group(4)

        if explicit_year:
            year = int(explicit_year)
        else:
            year = season_year(month)

        current_date = datetime(
            year,
            month,
            day,
        ).date()

        continue

    if current_date is None:
        continue

    match = match_pattern.match(line)

    if not match:
        continue

    explicit_time = match.group(1)
    home_team = match.group(2).strip()
    away_team = match.group(3).strip()

    # Убираем телевизионные и служебные пометки
    # вроде "(Sky Sports)*" и "(TNT Sports)**".
    home_team = re.sub(
        r"\s*\([^)]*\)\**\s*$",
        "",
        home_team,
    ).strip()

    away_team = re.sub(
        r"\s*\([^)]*\)\**\s*$",
        "",
        away_team,
    ).strip()

    # Защита от служебных строк статьи,
    # случайно содержащих " v ".
    if (
        home_team not in EPL_TEAMS
        or away_team not in EPL_TEAMS
    ):
        continue

    # Если время на официальной странице не указано,
    # Premier League сообщает:
    # выходные/Bank Holiday = 15:00,
    # будние дни = 20:00.
    if explicit_time:
        match_time = explicit_time
    elif current_weekday in (
        "Saturday",
        "Sunday",
    ):
        match_time = "15:00"
    else:
        match_time = "20:00"

    match_datetime = datetime.strptime(
        f"{current_date.isoformat()} {match_time}",
        "%Y-%m-%d %H:%M",
    ).replace(
        tzinfo=UK_TIMEZONE
    )

    rows.append({
        "match_date": current_date.isoformat(),
        "match_time": match_time,

        "home_team": home_team,
        "away_team": away_team,

        "home_team_model": TEAM_NAME_MAP.get(
            home_team,
            home_team,
        ),

        "away_team_model": TEAM_NAME_MAP.get(
            away_team,
            away_team,
        ),

        "match_datetime_uk": match_datetime.isoformat(),
    })


df = pd.DataFrame(rows)

if df.empty:
    raise RuntimeError(
        "Не удалось извлечь матчи из календаря."
    )

df = df.drop_duplicates(
    subset=[
        "match_date",
        "home_team",
        "away_team",
    ]
)

df["match_datetime_uk"] = pd.to_datetime(
    df["match_datetime_uk"],
    utc=True,
)

now = datetime.now(timezone.utc)

df = df[
    df["match_datetime_uk"] >= now
].copy()

df = df.sort_values(
    [
        "match_datetime_uk",
        "home_team",
    ]
).reset_index(drop=True)

df["match_datetime_uk"] = (
    df["match_datetime_uk"]
    .dt.tz_convert("Europe/London")
    .astype(str)
)

os.makedirs(
    os.path.dirname(OUTPUT),
    exist_ok=True,
)

df.to_csv(
    OUTPUT,
    index=False,
)

print()
print("Создан файл:", OUTPUT)
print("Будущих матчей:", len(df))

print()
print("Ближайшие 20 матчей:")
print(
    df.head(20).to_string(index=False)
)
