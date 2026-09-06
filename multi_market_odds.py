"""Read-only helpers for research multi-market odds coverage."""
from __future__ import annotations
from collections import defaultdict
from typing import Iterable
import requests
from config import THE_ODDS_API_KEY
from the_odds_service import BASE_URL

FEATURED_MARKETS = ("h2h", "spreads", "totals")
# Card V1 only needs spreads/totals from the league-level featured endpoint.
# One request returns these markets for all upcoming events in the league.
FEATURED_CARD_MARKETS = ("spreads", "totals")
# Keep event-level requests only for markets unavailable from the featured
# league endpoint. This amortizes handicap/goals cost across all league events.
EVENT_MARKETS = (
    "alternate_totals_corners",
    "alternate_team_totals_corners",
)


def _require_key():
    if not THE_ODDS_API_KEY:
        raise RuntimeError("THE_ODDS_API_KEY not found in environment")
    return THE_ODDS_API_KEY


def _quota(response):
    return {"remaining": response.headers.get("x-requests-remaining"), "used": response.headers.get("x-requests-used"), "last_cost": response.headers.get("x-requests-last")}


def fetch_quota_status():
    """Use the provider's zero-cost /sports endpoint before any paid market call."""
    response = requests.get(f"{BASE_URL}/sports/", params={"apiKey": _require_key()}, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"The Odds API quota preflight HTTP {response.status_code}: {response.text[:500]}")
    return _quota(response)


def fetch_sport_markets(sport_key: str, *, regions="eu", markets: Iterable[str] = FEATURED_MARKETS):
    response = requests.get(f"{BASE_URL}/sports/{sport_key}/odds/", params={"apiKey": _require_key(), "regions": regions, "markets": ",".join(markets), "oddsFormat": "decimal", "dateFormat": "iso"}, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"The Odds API sport markets error HTTP {response.status_code}: {response.text[:500]}")
    return response.json(), _quota(response)


def fetch_event_markets(sport_key: str, event_id: str, *, regions="eu", markets: Iterable[str] = EVENT_MARKETS):
    response = requests.get(f"{BASE_URL}/sports/{sport_key}/events/{event_id}/odds", params={"apiKey": _require_key(), "regions": regions, "markets": ",".join(markets), "oddsFormat": "decimal", "dateFormat": "iso"}, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"The Odds API event markets error HTTP {response.status_code}: {response.text[:500]}")
    return response.json(), _quota(response)


def index_sport_events(events: Iterable[dict]) -> dict[str, dict]:
    """Index one league-level featured response by canonical Odds API event id."""
    return {str(event.get("id")): event for event in events if event.get("id")}


def merge_event_market_payloads(featured_event: dict | None, event_markets: dict) -> dict:
    """Merge featured spreads/totals with event-only corner markets by bookmaker.

    The returned object keeps one bookmaker entry per key/title and never invents
    markets. Event-level metadata wins when both payloads provide it.
    """
    featured_event = featured_event or {}
    merged = dict(featured_event)
    merged.update({k: v for k, v in event_markets.items() if k != "bookmakers"})
    books: dict[str, dict] = {}
    order: list[str] = []
    for payload in (featured_event, event_markets):
        for book in payload.get("bookmakers", []) or []:
            key = str(book.get("key") or book.get("title") or "unknown")
            if key not in books:
                books[key] = {k: v for k, v in book.items() if k != "markets"}
                books[key]["markets"] = []
                order.append(key)
            seen = {m.get("key") for m in books[key]["markets"]}
            for market in book.get("markets", []) or []:
                if market.get("key") not in seen:
                    books[key]["markets"].append(market)
                    seen.add(market.get("key"))
    merged["bookmakers"] = [books[key] for key in order]
    return merged


def summarize_market_coverage(event: dict) -> dict[str, dict]:
    books, points, outcomes = defaultdict(set), defaultdict(set), defaultdict(set)
    for bookmaker in event.get("bookmakers", []):
        book = str(bookmaker.get("key") or bookmaker.get("title") or "unknown")
        for market in bookmaker.get("markets", []):
            key = market.get("key")
            if not key:
                continue
            books[key].add(book)
            for outcome in market.get("outcomes", []):
                if outcome.get("point") is not None: points[key].add(float(outcome["point"]))
                if outcome.get("name") is not None: outcomes[key].add(str(outcome["name"]))
    return {key: {"bookmakers": len(books[key]), "points": sorted(points[key]), "outcomes": sorted(outcomes[key])} for key in sorted(set(books) | set(points) | set(outcomes))}
