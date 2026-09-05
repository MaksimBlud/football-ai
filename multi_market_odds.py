"""Read-only helpers for research multi-market odds coverage.

This module does not write to Supabase and does not modify production models.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

import requests

from config import THE_ODDS_API_KEY
from the_odds_service import BASE_URL

FEATURED_MARKETS = ("h2h", "spreads", "totals")
EVENT_MARKETS = (
    "alternate_spreads",
    "alternate_totals",
    "team_totals",
    "alternate_team_totals",
    "alternate_spreads_corners",
    "alternate_totals_corners",
    "alternate_team_totals_corners",
)


def _require_key() -> str:
    if not THE_ODDS_API_KEY:
        raise RuntimeError("THE_ODDS_API_KEY not found in environment")
    return THE_ODDS_API_KEY


def fetch_sport_markets(sport_key: str, *, regions: str = "eu", markets: Iterable[str] = FEATURED_MARKETS):
    response = requests.get(
        f"{BASE_URL}/sports/{sport_key}/odds/",
        params={
            "apiKey": _require_key(),
            "regions": regions,
            "markets": ",".join(markets),
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        },
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(f"The Odds API sport markets error HTTP {response.status_code}: {response.text[:500]}")
    return response.json(), {
        "remaining": response.headers.get("x-requests-remaining"),
        "used": response.headers.get("x-requests-used"),
        "last_cost": response.headers.get("x-requests-last"),
    }


def fetch_event_markets(sport_key: str, event_id: str, *, regions: str = "eu", markets: Iterable[str] = EVENT_MARKETS):
    response = requests.get(
        f"{BASE_URL}/sports/{sport_key}/events/{event_id}/odds",
        params={
            "apiKey": _require_key(),
            "regions": regions,
            "markets": ",".join(markets),
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        },
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(f"The Odds API event markets error HTTP {response.status_code}: {response.text[:500]}")
    return response.json(), {
        "remaining": response.headers.get("x-requests-remaining"),
        "used": response.headers.get("x-requests-used"),
        "last_cost": response.headers.get("x-requests-last"),
    }


def summarize_market_coverage(event: dict) -> dict[str, dict]:
    """Return coverage counts and available points without exposing bookmaker-specific prices."""
    books_by_market: dict[str, set[str]] = defaultdict(set)
    points_by_market: dict[str, set[float]] = defaultdict(set)
    outcomes_by_market: dict[str, set[str]] = defaultdict(set)
    for bookmaker in event.get("bookmakers", []):
        book = str(bookmaker.get("key") or bookmaker.get("title") or "unknown")
        for market in bookmaker.get("markets", []):
            key = market.get("key")
            if not key:
                continue
            books_by_market[key].add(book)
            for outcome in market.get("outcomes", []):
                if outcome.get("point") is not None:
                    points_by_market[key].add(float(outcome["point"]))
                if outcome.get("name") is not None:
                    outcomes_by_market[key].add(str(outcome["name"]))
    keys = sorted(set(books_by_market) | set(points_by_market) | set(outcomes_by_market))
    return {
        key: {
            "bookmakers": len(books_by_market[key]),
            "points": sorted(points_by_market[key]),
            "outcomes": sorted(outcomes_by_market[key]),
        }
        for key in keys
    }
