from pathlib import Path
import time

import pandas as pd
import requests

BASE = "https://sdp-prem-prod.premier-league-prod.pulselive.com/api"

OUTPUT = Path("data/pl_official_2024_2025.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.premierleague.com/en/matches",
    "Origin": "https://www.premierleague.com",
    "Accept": "application/json, text/plain, */*",
}

TEAM_NAME_MAP = {
    "Brighton and Hove Albion": "Brighton",
    "Ipswich Town": "Ipswich",
    "Leicester City": "Leicester",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Newcastle United": "Newcastle",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves",
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
            print(
                f"429 rate limit. Жду {wait} сек..."
            )
            time.sleep(wait)
            continue

        response.raise_for_status()
        return response.json()

    raise RuntimeError(
        f"Не удалось получить {url} после {retries} попыток."
    )


def get_all_matches():
    all_matches = []
    cursor = None
    page = 1

    while True:
        params = {
            "competition": "8",
            "season": "2024",
            "_limit": "100",
        }

        if cursor:
            params["_next"] = cursor

        data = request_json(
            "/v2/matches",
            params=params,
        )

        matches = data.get("data", [])
        pagination = data.get("pagination", {})

        print(
            f"Страница {page}: {len(matches)} матчей"
        )

        all_matches.extend(matches)

        cursor = pagination.get("_next")

        if not cursor:
            break

        page += 1

    unique = {}

    for match in all_matches:
        unique[str(match["matchId"])] = match

    matches = list(unique.values())

    matches.sort(
        key=lambda x: x["kickoff"]
    )

    return matches


def extract_side_stats(stats_data):
    result = {
        "Home": {},
        "Away": {},
    }

    for item in stats_data:
        side = item.get("side")

        if side not in result:
            continue

        stats = item.get("stats", {})

        result[side] = {
            "shots": int(
                stats.get("totalScoringAtt", 0) or 0
            ),
            "shots_target": int(
                stats.get("ontargetScoringAtt", 0) or 0
            ),
            "corners": int(
                stats.get("cornerTaken", 0) or 0
            ),
            "yellow": int(
                stats.get("totalYelCard", 0) or 0
            ),
            "red": int(
                stats.get("totalRedCard", 0) or 0
            ),
            "possession": float(
                stats.get("possessionPercentage", 0) or 0
            ),
        }

    return result


def save_rows(rows):
    df = pd.DataFrame(rows)

    if not df.empty:
        df = df.drop_duplicates(
            subset=["match_id"],
            keep="last",
        )

        df = df.sort_values(
            ["match_date", "match_time"]
        ).reset_index(drop=True)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT,
        index=False,
    )


print(
    "Загружаю полный сезон Premier League 2024/25..."
)

matches = get_all_matches()

finished = [
    match
    for match in matches
    if match.get("period") == "FullTime"
]

print()
print("Всего матчей:", len(matches))
print("Завершённых:", len(finished))

if len(finished) != 380:
    print(
        "ВНИМАНИЕ: ожидалось 380 завершённых матчей."
    )

rows = []
done_ids = set()

if OUTPUT.exists():
    old = pd.read_csv(OUTPUT)

    if not old.empty:
        rows = old.to_dict(
            orient="records"
        )

        done_ids = set(
            old["match_id"]
            .astype(str)
        )

    print(
        "Уже сохранено:",
        len(done_ids),
    )

for index, match in enumerate(
    finished,
    start=1,
):
    match_id = str(match["matchId"])

    if match_id in done_ids:
        continue

    print(
        f"[{index}/{len(finished)}] "
        f"{match['homeTeam']['name']} — "
        f"{match['awayTeam']['name']}"
    )

    home_team = normalize_team(
        match["homeTeam"]["name"]
    )

    away_team = normalize_team(
        match["awayTeam"]["name"]
    )

    home_score = match["homeTeam"].get("score")
    away_score = match["awayTeam"].get("score")

    if home_score is None or away_score is None:
        detail = request_json(
            f"/v2/matches/{match_id}"
        )

        home_score = detail["homeTeam"]["score"]
        away_score = detail["awayTeam"]["score"]

    home_goals = int(home_score)
    away_goals = int(away_score)

    if home_goals > away_goals:
        result = "H"
    elif home_goals < away_goals:
        result = "A"
    else:
        result = "D"

    stats = extract_side_stats(
        request_json(
            f"/v3/matches/{match_id}/stats"
        )
    )

    kickoff = pd.to_datetime(
        match["kickoff"]
    )

    rows.append({
        "match_id": match_id,
        "season": "2024/2025",
        "league": "EPL",
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
        "home_possession": stats["Home"].get("possession", 0),
        "away_possession": stats["Away"].get("possession", 0),
    })

    done_ids.add(match_id)

    save_rows(rows)

    time.sleep(0.30)


save_rows(rows)

df = pd.read_csv(OUTPUT)

print()
print("=" * 70)
print("ГОТОВО")
print("=" * 70)
print("Сохранено матчей:", len(df))
print("Файл:", OUTPUT)

print()
print("Команд:", len(
    set(df["home_team"]) |
    set(df["away_team"])
))

print()
print("Распределение результатов:")
print(
    df["result"]
    .value_counts()
    .to_string()
)

print()
print("Последние 5 матчей:")
print(
    df.tail(5).to_string(
        index=False
    )
)
