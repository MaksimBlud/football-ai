"""Read RPL completed scores from The Odds API.

This module is side-effect free until get_rpl_scores() is called.
"""

from __future__ import annotations

import requests

from config import THE_ODDS_API_KEY
from league_runtime_config import RPL_RUNTIME_CONFIG


BASE_URL = "https://api.the-odds-api.com/v4"
DAYS_FROM = 3


def get_rpl_scores(*, days_from: int = DAYS_FROM) -> dict:
    if not THE_ODDS_API_KEY:
        raise RuntimeError("THE_ODDS_API_KEY not configured")
    if days_from < 1 or days_from > 3:
        raise ValueError("days_from must be between 1 and 3")

    sport_key = RPL_RUNTIME_CONFIG.identity.odds_sport_key
    response = requests.get(
        f"{BASE_URL}/sports/{sport_key}/scores/",
        params={
            "apiKey": THE_ODDS_API_KEY,
            "daysFrom": days_from,
            "dateFormat": "iso",
        },
        timeout=30,
    )
    if response.status_code != 200:
        try:
            payload = response.json()
        except Exception:
            payload = {}
        raise RuntimeError(
            "The Odds API scores error: "
            f"HTTP {response.status_code} | "
            f"{payload.get('error_code')} | {payload.get('message')}"
        )

    return {
        "events": response.json(),
        "quota": {
            "remaining": response.headers.get("x-requests-remaining"),
            "used": response.headers.get("x-requests-used"),
            "last_cost": response.headers.get("x-requests-last"),
        },
    }
