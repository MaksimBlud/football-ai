import argparse
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

from database import supabase
from team_names import normalize_team_name


SEASON_API = 2026
SEASON_DB = "2026/2027"
LEAGUE = "EPL"

BASE_URL = (
    "https://api.football-data.org/v4/"
    "competitions/PL/matches"
)


def load_api_key():
    load_dotenv(
        dotenv_path=".env"
    )

    key = (
        os.getenv("FOOTBALL_DATA_API_KEY")
        or os.getenv("API_FOOTBALL_KEY")
    )

    if not key:
        raise RuntimeError(
            "Не найден FOOTBALL_DATA_API_KEY "
            "или API_FOOTBALL_KEY."
        )

    return key


def fetch_matches():
    response = requests.get(
        BASE_URL,
        headers={
            "X-Auth-Token": load_api_key(),
        },
        params={
            "season": SEASON_API,
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "football-data.org error: "
            f"HTTP {response.status_code} | "
            f"{response.text[:1000]}"
        )

    return response.json().get(
        "matches",
        []
    )


def parse_uk_datetime(value):
    utc_dt = datetime.fromisoformat(
        str(value).replace(
            "Z",
            "+00:00",
        )
    )

    return utc_dt.astimezone(
        ZoneInfo("Europe/London")
    )


def result_from_score(
    home_goals,
    away_goals,
):
    if home_goals > away_goals:
        return "H"

    if away_goals > home_goals:
        return "A"

    return "D"


def build_finished_payload(match):
    if match.get("status") != "FINISHED":
        return None

    score = (
        match.get("score", {})
        .get("fullTime", {})
    )

    home_goals = score.get("home")
    away_goals = score.get("away")

    if (
        home_goals is None
        or away_goals is None
    ):
        return None

    kickoff = parse_uk_datetime(
        match["utcDate"]
    )

    home_source = (
        match.get("homeTeam", {})
        .get("shortName")
    )

    away_source = (
        match.get("awayTeam", {})
        .get("shortName")
    )

    if not home_source or not away_source:
        return None

    home_team = normalize_team_name(
        home_source
    )

    away_team = normalize_team_name(
        away_source
    )

    return {
        "season": SEASON_DB,
        "league": LEAGUE,

        "match_date":
            kickoff.strftime("%Y-%m-%d"),

        "match_time":
            kickoff.strftime("%H:%M"),

        "home_team":
            home_team,

        "away_team":
            away_team,

        "home_goals":
            int(home_goals),

        "away_goals":
            int(away_goals),

        "result":
            result_from_score(
                int(home_goals),
                int(away_goals),
            ),
    }


def load_existing_season():
    page_size = 1000
    offset = 0
    rows = []

    while True:
        response = (
            supabase
            .table("matches")
            .select(
                "match_date,"
                "home_team,"
                "away_team,"
                "home_goals,"
                "away_goals,"
                "result"
            )
            .eq(
                "season",
                SEASON_DB,
            )
            .range(
                offset,
                offset + page_size - 1,
            )
            .execute()
        )

        page = response.data or []

        rows.extend(page)

        if len(page) < page_size:
            break

        offset += page_size

    return rows


def match_key(row):
    return (
        str(row["match_date"]),
        normalize_team_name(
            row["home_team"]
        ),
        normalize_team_name(
            row["away_team"]
        ),
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Разрешить запись новых FINISHED "
            "матчей в Supabase."
        ),
    )

    args = parser.parse_args()

    matches = fetch_matches()

    finished_payloads = [
        payload
        for match in matches
        if (
            payload :=
            build_finished_payload(match)
        )
        is not None
    ]

    existing_rows = (
        load_existing_season()
    )

    existing = {
        match_key(row): row
        for row in existing_rows
    }

    new_rows = []
    already_present = []
    conflicts = []

    for payload in finished_payloads:
        key = match_key(payload)

        old = existing.get(key)

        if old is None:
            new_rows.append(
                payload
            )
            continue

        same_result = (
            int(old["home_goals"])
            == payload["home_goals"]
            and
            int(old["away_goals"])
            == payload["away_goals"]
            and
            str(old["result"])
            == payload["result"]
        )

        if same_result:
            already_present.append(
                payload
            )
        else:
            conflicts.append({
                "existing": old,
                "incoming": payload,
            })

    print("=" * 100)
    print("EPL RESULT UPDATER")
    print("=" * 100)

    print(
        "Матчей football-data:",
        len(matches),
    )

    print(
        "FINISHED с валидным score:",
        len(finished_payloads),
    )

    print(
        "Уже есть в Supabase:",
        len(already_present),
    )

    print(
        "Новых результатов:",
        len(new_rows),
    )

    print(
        "Конфликтов:",
        len(conflicts),
    )

    print()

    if new_rows:
        print("=" * 100)
        print("NEW RESULTS")
        print("=" * 100)

        for row in new_rows:
            print(
                row["match_date"],
                row["match_time"],
                "|",
                row["home_team"],
                row["home_goals"],
                "-",
                row["away_goals"],
                row["away_team"],
                "|",
                row["result"],
            )

    if conflicts:
        print()
        print("=" * 100)
        print("CONFLICTS")
        print("=" * 100)

        for conflict in conflicts:
            print(conflict)

    if conflicts:
        raise SystemExit(
            "Обнаружены конфликты. "
            "Запись запрещена."
        )

    if not args.write:
        print()
        print(
            "DRY RUN: Supabase НЕ изменялся."
        )
        print(
            "Для реальной записи требуется --write."
        )
        return

    if not new_rows:
        print()
        print(
            "Новых результатов для записи нет."
        )
        return

    response = (
        supabase
        .table("matches")
        .insert(
            new_rows
        )
        .execute()
    )

    print()
    print(
        "Записано строк:",
        len(response.data or []),
    )


if __name__ == "__main__":
    main()
