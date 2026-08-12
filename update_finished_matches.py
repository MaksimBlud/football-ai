import argparse
import time
from datetime import datetime

import pandas as pd
import requests

from database import supabase

BASE = "https://sdp-prem-prod.premier-league-prod.pulselive.com/api"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.premierleague.com/en/matches",
    "Origin": "https://www.premierleague.com",
    "Accept": "application/json, text/plain, */*",
}

SEASON_API = "2026"
SEASON_DB = "2026/2027"
LEAGUE = "EPL"

TEAM_NAME_MAP = {
    "AFC Bournemouth": "Bournemouth",
    "Bournemouth": "Bournemouth",
    "Brighton and Hove Albion": "Brighton",
    "Coventry City": "Coventry City",
    "Hull City": "Hull",
    "Ipswich Town": "Ipswich",
    "Leeds United": "Leeds",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
}

def normalize_team(name):
    return TEAM_NAME_MAP.get(name, name)

def request_json(path, params=None, retries=5):
    url = f"{BASE}{path}"
    for attempt in range(1, retries + 1):
        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=30,
        )
        if response.status_code == 429:
            wait = min(60, 5 * attempt)
            print(f"429 rate limit. Жду {wait} сек...")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(
        f"Не удалось получить {url} после {retries} попыток."
    )

def get_all_season_matches():
    rows = []
    cursor = None
    page = 1
    while True:
        params = {
            "competition": "8",
            "season": SEASON_API,
            "_limit": "100",
        }
        if cursor:
            params["_next"] = cursor
        data = request_json(
            "/v2/matches",
            params=params,
        )
        page_rows = data.get("data", [])
        print(f"Страница {page}: {len(page_rows)} матчей")
        rows.extend(page_rows)
        cursor = data.get("pagination", {}).get("_next")
        if not cursor:
            break
        page += 1

    unique = {}
    for match in rows:
        unique[str(match["matchId"])] = match
    return sorted(
        unique.values(),
        key=lambda x: x["kickoff"],
    )

def get_stats(match_id):
    data = request_json(
        f"/v3/matches/{match_id}/stats"
    )
    result = {
        "Home": {},
        "Away": {},
    }
    for item in data:
        side = item.get("side")
        if side not in result:
            continue
        stats = item.get("stats", {})
        result[side] = {
            "shots": int(stats.get("totalScoringAtt", 0) or 0),
            "shots_target": int(stats.get("ontargetScoringAtt", 0) or 0),
            "corners": int(stats.get("cornerTaken", 0) or 0),
            "yellow": int(stats.get("totalYelCard", 0) or 0),
            "red": int(stats.get("totalRedCard", 0) or 0),
        }
    return result

def build_row(match):
    match_id = str(match["matchId"])
    home_team = normalize_team(
        match["homeTeam"]["name"]
    )
    away_team = normalize_team(
        match["awayTeam"]["name"]
    )

    home_goals = match["homeTeam"].get("score")
    away_goals = match["awayTeam"].get("score")

    if home_goals is None or away_goals is None:
        detail = request_json(
            f"/v2/matches/{match_id}"
        )
        home_goals = detail["homeTeam"]["score"]
        away_goals = detail["awayTeam"]["score"]

    home_goals = int(home_goals)
    away_goals = int(away_goals)

    if home_goals > away_goals:
        result = "H"
    elif home_goals < away_goals:
        result = "A"
    else:
        result = "D"

    kickoff = pd.to_datetime(
        match["kickoff"]
    )
    stats = get_stats(match_id)

    return {
        "season": SEASON_DB,
        "league": LEAGUE,
        "match_date": kickoff.date().isoformat(),
        "match_time": kickoff.strftime("%H:%M"),
        "home_team": home_team,
        "away_team": away_team,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "result": result,
        "home_shots": stats["Home"].get("shots", 0),
        "away_shots": stats["Away"].get("shots", 0),
        "home_shots_target": stats["Home"].get("shots_target", 0),
        "away_shots_target": stats["Away"].get("shots_target", 0),
        "home_corners": stats["Home"].get("corners", 0),
        "away_corners": stats["Away"].get("corners", 0),
        "home_yellow": stats["Home"].get("yellow", 0),
        "away_yellow": stats["Away"].get("yellow", 0),
        "home_red": stats["Home"].get("red", 0),
        "away_red": stats["Away"].get("red", 0),
        "home_odds": None,
        "draw_odds": None,
        "away_odds": None,
    }

def get_existing_keys():
    result = (
        supabase
        .table("matches")
        .select(
            "match_date,home_team,away_team"
        )
        .eq("season", SEASON_DB)
        .execute()
    )
    rows = result.data or []
    return {
        (
            str(row["match_date"]),
            row["home_team"],
            row["away_team"],
        )
        for row in rows
    }

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Добавляет завершённые матчи "
            "Premier League 2026/27 в Supabase."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Фактически записать новые матчи в Supabase.",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("FOOTBALL AI — ОБНОВЛЕНИЕ ЗАВЕРШЁННЫХ МАТЧЕЙ")
    print("=" * 70)

    matches = get_all_season_matches()
    finished = [
        match
        for match in matches
        if match.get("period") == "FullTime"
    ]

    print()
    print("Всего матчей сезона:", len(matches))
    print("Завершённых:", len(finished))

    existing_keys = get_existing_keys()
    print(
        "Уже есть в Supabase:",
        len(existing_keys),
    )

    new_matches = []
    for match in finished:
        kickoff = pd.to_datetime(
            match["kickoff"]
        )
        key = (
            kickoff.date().isoformat(),
            normalize_team(
                match["homeTeam"]["name"]
            ),
            normalize_team(
                match["awayTeam"]["name"]
            ),
        )
        if key not in existing_keys:
            new_matches.append(match)

    print(
        "Новых завершённых:",
        len(new_matches),
    )

    if not new_matches:
        print()
        print("Новых матчей нет.")
        print("Supabase не изменялся.")
        return

    print()
    for i, match in enumerate(
        new_matches,
        start=1,
    ):
        print(
            f"[{i}/{len(new_matches)}] "
            f"{match['kickoff']} | "
            f"{match['homeTeam']['name']} — "
            f"{match['awayTeam']['name']} | "
            f"matchId={match['matchId']}"
        )

    if not args.apply:
        print()
        print(
            "DRY-RUN: запись НЕ выполнялась."
        )
        print(
            "Для записи запусти:"
        )
        print(
            "python3 update_finished_matches.py --apply"
        )
        return

    print()
    print("Получаю статистику и записываю матчи...")

    inserted = 0
    for i, match in enumerate(
        new_matches,
        start=1,
    ):
        print(
            f"[{i}/{len(new_matches)}] "
            f"{match['homeTeam']['name']} — "
            f"{match['awayTeam']['name']}"
        )

        row = build_row(match)
        key = (
            row["match_date"],
            row["home_team"],
            row["away_team"],
        )

        if key in existing_keys:
            print("  Уже есть — пропускаю.")
            continue

        (
            supabase
            .table("matches")
            .insert(row)
            .execute()
        )

        existing_keys.add(key)
        inserted += 1
        time.sleep(0.30)

    print()
    print("=" * 70)
    print("ГОТОВО")
    print("=" * 70)
    print("Добавлено матчей:", inserted)
    print(
        "Время:",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    )

if __name__ == "__main__":
    main()
