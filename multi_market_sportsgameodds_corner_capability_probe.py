"""Research-only SportsGameOdds bookmaker corner-line capability probe.

The probe is deliberately separate from the existing The Odds API path.  It is
manual-only at workflow level, performs at most one authenticated provider
request, never writes Supabase, and never touches production model artifacts.

Capability is confirmed only when the exact preregistered prospective fixture
contains an available bookmaker offering BOTH sides of the full-match total
corner market with a matching line and explicit bookmaker prices.
"""
from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

import requests

OUTPUT = Path("artifacts/sportsgameodds_corner_capability_probe.json")
API_URL = "https://api.sportsgameodds.com/v2/events"
PROVIDER = "SPORTSGAMEODDS"
PROVIDER_LEAGUE_ID = "BUNDESLIGA"
MAX_PROVIDER_REQUESTS = 1
CORNER_ODD_IDS = (
    "cornerKicks-all-game-ou-over",
    "cornerKicks-all-game-ou-under",
)
TARGET = {
    "league": "BUNDESLIGA",
    "home_team": "Union Berlin",
    "away_team": "FC Schalke 04",
    "commence_time_utc": "2026-09-11T18:30:00+00:00",
}
TARGET_TEAM_ALIASES = {
    "home_team": frozenset({"Union Berlin", "1. FC Union Berlin", "FC Union Berlin"}),
    "away_team": frozenset({"FC Schalke 04", "Schalke 04"}),
}


class ProviderRequestAttemptedError(RuntimeError):
    """Failure after the single SportsGameOdds request boundary was crossed."""

    def __init__(self, result: dict[str, Any], cause: Exception):
        self.result = dict(result)
        self.cause = cause
        super().__init__(str(cause))


def _base_result(*, status: str) -> dict[str, Any]:
    return {
        "schema_version": "SPORTSGAMEODDS_CORNER_CAPABILITY_PROBE_V1",
        "research_only": True,
        "preregistered": True,
        "provider": PROVIDER,
        "provider_league_id": PROVIDER_LEAGUE_ID,
        "target": dict(TARGET),
        "requested_odd_ids": list(CORNER_ODD_IDS),
        "max_provider_requests": MAX_PROVIDER_REQUESTS,
        "provider_request_attempted": False,
        "provider_requests": 0,
        "writes_performed": False,
        "external_account_action_performed": False,
        "subscription_change_performed": False,
        "status": status,
    }


def build_request_params() -> dict[str, str]:
    """Return the fixed, minimal request shape for the manual capability probe."""
    return {
        "leagueID": PROVIDER_LEAGUE_ID,
        "oddsAvailable": "true",
        "started": "false",
        "oddID": ",".join(CORNER_ODD_IDS),
        "includeOpposingOdds": "false",
        "includeAltLines": "false",
        "limit": "100",
    }


def _normalise_team(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def _allowed_team_names(side: str) -> set[str]:
    return {_normalise_team(name) for name in TARGET_TEAM_ALIASES[side]}


def _team_name(team: Any) -> str:
    if isinstance(team, str):
        return team
    if not isinstance(team, dict):
        return ""
    if team.get("name"):
        return str(team["name"])
    names = team.get("names")
    if isinstance(names, dict):
        return str(names.get("display") or names.get("name") or "")
    return ""


def _event_kickoff(event: dict[str, Any]) -> datetime | None:
    raw = event.get("startTime")
    if raw in (None, ""):
        status = event.get("status")
        if isinstance(status, dict):
            raw = status.get("startsAt")
    if raw in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _expected_kickoff() -> datetime:
    return datetime.fromisoformat(TARGET["commence_time_utc"]).astimezone(UTC)


def _event_matches_target(event: dict[str, Any]) -> bool:
    league = str(event.get("leagueID") or "")
    if league and league != PROVIDER_LEAGUE_ID:
        return False

    teams = event.get("teams")
    if not isinstance(teams, dict):
        return False
    home = _normalise_team(_team_name(teams.get("home")))
    away = _normalise_team(_team_name(teams.get("away")))
    if home not in _allowed_team_names("home_team"):
        return False
    if away not in _allowed_team_names("away_team"):
        return False

    kickoff = _event_kickoff(event)
    return kickoff == _expected_kickoff()


def _find_exact_target(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    matches = [event for event in events if isinstance(event, dict) and _event_matches_target(event)]
    if len(matches) > 1:
        raise RuntimeError("SportsGameOdds exact target identity is ambiguous")
    return matches[0] if matches else None


def _normalise_line(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _available_bookmaker_sides(event: dict[str, Any], odd_id: str) -> dict[str, dict[str, str]]:
    odds = event.get("odds")
    if not isinstance(odds, dict):
        return {}
    odd = odds.get(odd_id)
    if not isinstance(odd, dict):
        return {}
    if odd.get("oddID") not in (None, "", odd_id):
        return {}

    books = odd.get("byBookmaker")
    if not isinstance(books, dict):
        return {}

    result: dict[str, dict[str, str]] = {}
    for bookmaker_id, item in books.items():
        if not isinstance(item, dict) or item.get("available") is not True:
            continue
        line = _normalise_line(item.get("overUnder"))
        price = item.get("odds")
        if line is None or price in (None, ""):
            continue
        result[str(bookmaker_id)] = {
            "odds": str(price),
            "over_under": str(line),
            "last_updated_at": str(item.get("lastUpdatedAt") or ""),
        }
    return result


def _paired_bookmaker_evidence(event: dict[str, Any]) -> list[dict[str, Any]]:
    over = _available_bookmaker_sides(event, CORNER_ODD_IDS[0])
    under = _available_bookmaker_sides(event, CORNER_ODD_IDS[1])
    evidence: list[dict[str, Any]] = []
    for bookmaker_id in sorted(set(over).intersection(under)):
        over_line = _normalise_line(over[bookmaker_id]["over_under"])
        under_line = _normalise_line(under[bookmaker_id]["over_under"])
        if over_line is None or under_line is None or over_line != under_line:
            continue
        evidence.append(
            {
                "bookmaker_id": bookmaker_id,
                "line": str(over_line),
                "over_odds": over[bookmaker_id]["odds"],
                "under_odds": under[bookmaker_id]["odds"],
                "over_last_updated_at": over[bookmaker_id]["last_updated_at"],
                "under_last_updated_at": under[bookmaker_id]["last_updated_at"],
            }
        )
    return evidence


def _validate_response(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise RuntimeError("SportsGameOdds response is not an object")
    if payload.get("success") is not True:
        raise RuntimeError(f"SportsGameOdds response failed: {str(payload.get('error') or 'unknown error')[:500]}")
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise RuntimeError("SportsGameOdds response data is not a list")
    return [row for row in rows if isinstance(row, dict)]


def run_probe(
    fetch_events_fn: Callable[[dict[str, str]], Any],
    *,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Execute at most one provider request and evaluate exact-target evidence."""
    now_utc = (now_utc or datetime.now(UTC)).astimezone(UTC)
    result = _base_result(status="BLOCKED")
    if now_utc >= _expected_kickoff():
        result["blocker"] = "PREREGISTERED_TARGET_NOT_PROSPECTIVE"
        return result

    params = build_request_params()
    result["request_params"] = dict(params)

    # Conservatively account the request before crossing the provider boundary.
    result["provider_request_attempted"] = True
    result["provider_requests"] = 1
    try:
        rows = _validate_response(fetch_events_fn(params))
        result["returned_event_count"] = len(rows)
        target = _find_exact_target(rows)
        if target is None:
            result["target_verified"] = False
            result["paired_bookmaker_count"] = 0
            result["paired_bookmaker_evidence"] = []
            result["status"] = "CAPABILITY_MISS"
            result["blocker"] = "EXACT_TARGET_NOT_FOUND"
            return result

        result["target_verified"] = True
        result["provider_event_id"] = str(target.get("eventID") or "")
        result["provider_target_kickoff_utc"] = _event_kickoff(target).isoformat()
        evidence = _paired_bookmaker_evidence(target)
        result["paired_bookmaker_evidence"] = evidence
        result["paired_bookmaker_count"] = len(evidence)
        result["corner_bookmaker_ids"] = [item["bookmaker_id"] for item in evidence]
        if evidence:
            result["status"] = "CAPABILITY_CONFIRMED"
        else:
            result["status"] = "CAPABILITY_MISS"
            result["blocker"] = "BOOKMAKER_CORNER_LINE_PRICE_NOT_FOUND"
        return result
    except Exception as exc:
        raise ProviderRequestAttemptedError(result, exc) from exc


def fetch_events(api_key: str, params: dict[str, str]) -> dict[str, Any]:
    """Perform the one authenticated HTTP request using a header, never a URL key."""
    response = requests.get(
        API_URL,
        headers={"x-api-key": api_key},
        params=params,
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("SportsGameOdds JSON payload is not an object")
    return payload


def _write_result(result: dict[str, Any]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


def main() -> None:
    result = _base_result(status="FAILED")
    api_key = str(os.getenv("SPORTSGAMEODDS_API_KEY") or "").strip()
    if not api_key:
        result["blocker"] = "SPORTSGAMEODDS_API_KEY_MISSING"
        result["error_type"] = "RuntimeError"
        result["error"] = "SPORTSGAMEODDS_API_KEY is required for the manual provider probe"
        _write_result(result)
        raise RuntimeError(result["error"])

    try:
        result = run_probe(lambda params: fetch_events(api_key, params))
    except ProviderRequestAttemptedError as exc:
        result = dict(exc.result)
        result["status"] = "FAILED"
        result["error_type"] = type(exc.cause).__name__
        result["error"] = str(exc.cause)[:1000]
        _write_result(result)
        raise exc.cause from exc

    _write_result(result)
    if result["status"] == "BLOCKED":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
