import requests

from config import API_FOOTBALL_KEY


BASE_URL = "https://v3.football.api-sports.io"


def get_fixture_odds(fixture_id):
    response = requests.get(
        f"{BASE_URL}/odds",
        headers={
            "x-apisports-key": API_FOOTBALL_KEY,
        },
        params={
            "fixture": int(fixture_id),
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"API-Football вернул статус "
            f"{response.status_code}"
        )

    data = response.json()

    errors = data.get("errors")

    if errors:
        raise RuntimeError(
            f"Ошибка API-Football: {errors}"
        )

    items = data.get("response", [])

    if not items:
        return {
            "odds_available": False,
        }

    item = items[0]

    bookmakers = item.get(
        "bookmakers",
        [],
    )

    if not bookmakers:
        return {
            "odds_available": False,
        }

    # Пока берём первого букмекера.
    bookmaker = bookmakers[0]

    result = {
        "odds_available": True,
        "bookmaker": bookmaker.get("name"),
        "home_odds": None,
        "draw_odds": None,
        "away_odds": None,
        "over_2_5_odds": None,
        "under_2_5_odds": None,
        "btts_yes_odds": None,
        "btts_no_odds": None,
    }

    for bet in bookmaker.get("bets", []):
        name = bet.get("name", "")

        if name == "Match Winner":
            for value in bet.get("values", []):
                label = value.get("value")
                odd = value.get("odd")

                if label == "Home":
                    result["home_odds"] = float(odd)

                elif label == "Draw":
                    result["draw_odds"] = float(odd)

                elif label == "Away":
                    result["away_odds"] = float(odd)

        elif name in (
            "Goals Over/Under",
            "Goals Over Under",
        ):
            for value in bet.get("values", []):
                label = str(
                    value.get("value", "")
                )

                odd = value.get("odd")

                if label in (
                    "Over 2.5",
                    "Over 2.5 Goals",
                ):
                    result["over_2_5_odds"] = float(odd)

                elif label in (
                    "Under 2.5",
                    "Under 2.5 Goals",
                ):
                    result["under_2_5_odds"] = float(odd)

        elif name in (
            "Both Teams Score",
            "Both Teams To Score",
        ):
            for value in bet.get("values", []):
                label = str(
                    value.get("value", "")
                ).lower()

                odd = value.get("odd")

                if label == "yes":
                    result["btts_yes_odds"] = float(odd)

                elif label == "no":
                    result["btts_no_odds"] = float(odd)

    return result
