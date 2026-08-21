from pathlib import Path
import requests


ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"

BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 39  # English Premier League
SEASONS = list(range(2019, 2026))


def load_key():
    if not ENV_FILE.exists():
        raise SystemExit("❌ .env не найден.")

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("API_FOOTBALL_KEY="):
            key = line.split("=", 1)[1].strip()

            if key:
                return key

    raise SystemExit("❌ API_FOOTBALL_KEY не найден в .env.")


api_key = load_key()

headers = {
    "x-apisports-key": api_key,
}


print()
print("=" * 105)
print("API-FOOTBALL — EPL COVERAGE CHECK")
print("=" * 105)

print(
    f"{'SEASON':<12}"
    f"{'LINEUPS':<10}"
    f"{'INJURIES':<11}"
    f"{'FIX_STATS':<12}"
    f"{'PLAYER_STATS':<14}"
    f"{'PLAYERS':<10}"
    f"{'STATUS'}"
)

print("-" * 105)


for season in SEASONS:

    try:
        response = requests.get(
            f"{BASE_URL}/leagues",
            headers=headers,
            params={
                "id": LEAGUE_ID,
                "season": season,
            },
            timeout=30,
        )

    except requests.RequestException as exc:
        print(
            f"{season}/{season + 1:<7}"
            f"{'-':<10}"
            f"{'-':<11}"
            f"{'-':<12}"
            f"{'-':<14}"
            f"{'-':<10}"
            f"REQUEST ERROR: {exc}"
        )
        continue


    remaining = (
        response.headers.get(
            "x-ratelimit-requests-remaining"
        )
        or response.headers.get(
            "X-RateLimit-Requests-Remaining"
        )
        or "?"
    )


    if response.status_code != 200:
        print(
            f"{season}/{season + 1:<7}"
            f"{'-':<10}"
            f"{'-':<11}"
            f"{'-':<12}"
            f"{'-':<14}"
            f"{'-':<10}"
            f"HTTP {response.status_code}"
        )
        continue


    payload = response.json()

    errors = payload.get(
        "errors",
        {},
    )

    if errors:
        print(
            f"{season}/{season + 1:<7}"
            f"{'-':<10}"
            f"{'-':<11}"
            f"{'-':<12}"
            f"{'-':<14}"
            f"{'-':<10}"
            f"API ERROR: {errors}"
        )
        continue


    items = payload.get(
        "response",
        [],
    )

    if not items:
        print(
            f"{season}/{season + 1:<7}"
            f"{'-':<10}"
            f"{'-':<11}"
            f"{'-':<12}"
            f"{'-':<14}"
            f"{'-':<10}"
            f"NO DATA | remaining={remaining}"
        )
        continue


    seasons_data = items[0].get(
        "seasons",
        [],
    )

    season_data = next(
        (
            s
            for s in seasons_data
            if s.get("year") == season
        ),
        None,
    )

    if not season_data:
        print(
            f"{season}/{season + 1:<7}"
            f"{'-':<10}"
            f"{'-':<11}"
            f"{'-':<12}"
            f"{'-':<14}"
            f"{'-':<10}"
            f"SEASON OBJECT MISSING"
        )
        continue


    coverage = season_data.get(
        "coverage",
        {},
    )

    fixtures = coverage.get(
        "fixtures",
        {},
    )


    lineups = fixtures.get(
        "lineups",
        False,
    )

    injuries = coverage.get(
        "injuries",
        False,
    )

    fixture_stats = fixtures.get(
        "statistics_fixtures",
        False,
    )

    player_stats = fixtures.get(
        "statistics_players",
        False,
    )

    players = coverage.get(
        "players",
        False,
    )


    print(
        f"{season}/{season + 1:<7}"
        f"{str(lineups):<10}"
        f"{str(injuries):<11}"
        f"{str(fixture_stats):<12}"
        f"{str(player_stats):<14}"
        f"{str(players):<10}"
        f"OK | remaining={remaining}"
    )


print()
print("=" * 105)
print("Ключ API в вывод не печатался.")
