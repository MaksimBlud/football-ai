import requests

from config import THE_ODDS_API_KEY


BASE_URL = "https://api.the-odds-api.com/v4"

SPORT = "soccer_epl"
REGIONS = "uk"
MARKETS = "h2h"


def get_h2h_odds(
    sport_key: str,
    *,
    regions: str = REGIONS,
):
    """Fetch h2h odds for an explicit Odds API sport key."""

    if not THE_ODDS_API_KEY:
        raise RuntimeError(
            "THE_ODDS_API_KEY не найден в окружении."
        )

    if not sport_key:
        raise ValueError(
            "sport_key must be non-empty"
        )

    response = requests.get(
        f"{BASE_URL}/sports/{sport_key}/odds/",
        params={
            "apiKey": THE_ODDS_API_KEY,
            "regions": regions,
            "markets": MARKETS,
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        },
        timeout=30,
    )

    if response.status_code != 200:
        try:
            data = response.json()
        except Exception:
            data = {}

        raise RuntimeError(
            "The Odds API error: "
            f"HTTP {response.status_code} | "
            f"{data.get('error_code')} | "
            f"{data.get('message')}"
        )

    events = response.json()

    return {
        "events": events,
        "quota": {
            "remaining": response.headers.get(
                "x-requests-remaining"
            ),
            "used": response.headers.get(
                "x-requests-used"
            ),
            "last_cost": response.headers.get(
                "x-requests-last"
            ),
        },
    }


def get_epl_h2h_odds():
    """Backward-compatible EPL wrapper."""

    return get_h2h_odds(
        SPORT
    )


def aggregate_event_h2h(event):

    home_team = event["home_team"]
    away_team = event["away_team"]

    home_prices = []
    draw_prices = []
    away_prices = []

    bookmaker_rows = []

    for bookmaker in event.get(
        "bookmakers",
        [],
    ):

        for market in bookmaker.get(
            "markets",
            [],
        ):

            if market.get("key") != "h2h":
                continue

            prices = {}

            for outcome in market.get(
                "outcomes",
                [],
            ):

                prices[
                    outcome.get("name")
                ] = outcome.get("price")

            home = prices.get(home_team)
            draw = prices.get("Draw")
            away = prices.get(away_team)

            if (
                home is None
                or draw is None
                or away is None
            ):
                continue

            home = float(home)
            draw = float(draw)
            away = float(away)

            home_prices.append(home)
            draw_prices.append(draw)
            away_prices.append(away)

            bookmaker_rows.append({
                "bookmaker_key": bookmaker.get(
                    "key"
                ),
                "bookmaker_title": bookmaker.get(
                    "title"
                ),
                "last_update": market.get(
                    "last_update"
                ),
                "home_odds": home,
                "draw_odds": draw,
                "away_odds": away,
            })

    if not home_prices:
        return None

    avg_home = sum(home_prices) / len(
        home_prices
    )

    avg_draw = sum(draw_prices) / len(
        draw_prices
    )

    avg_away = sum(away_prices) / len(
        away_prices
    )

    raw_home = 1.0 / avg_home
    raw_draw = 1.0 / avg_draw
    raw_away = 1.0 / avg_away

    total = (
        raw_home
        + raw_draw
        + raw_away
    )

    return {
        "event_id": event.get("id"),
        "commence_time": event.get(
            "commence_time"
        ),
        "home_team": home_team,
        "away_team": away_team,

        "bookmakers_count": len(
            bookmaker_rows
        ),

        "home_odds": avg_home,
        "draw_odds": avg_draw,
        "away_odds": avg_away,

        "home_probability": (
            raw_home / total
        ),
        "draw_probability": (
            raw_draw / total
        ),
        "away_probability": (
            raw_away / total
        ),

        "bookmakers": bookmaker_rows,
    }


if __name__ == "__main__":

    result = get_epl_h2h_odds()

    events = result["events"]

    print(
        "Матчей получено:",
        len(events),
    )

    print(
        "Quota:",
        result["quota"],
    )

    print()

    for event in events:

        aggregated = aggregate_event_h2h(
            event
        )

        if aggregated is None:
            continue

        print(
            aggregated["home_team"],
            "-",
            aggregated["away_team"],
        )

        print(
            "  bookmakers:",
            aggregated[
                "bookmakers_count"
            ],
        )

        print(
            "  avg odds:",
            f"{aggregated['home_odds']:.3f}",
            f"{aggregated['draw_odds']:.3f}",
            f"{aggregated['away_odds']:.3f}",
        )

        print(
            "  probabilities:",
            f"H={aggregated['home_probability']:.3%}",
            f"D={aggregated['draw_probability']:.3%}",
            f"A={aggregated['away_probability']:.3%}",
        )

        print()
