"""API-Football bootstrap for prospective availability research only."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from typing import Any

import requests

from prospective_availability_contract import (
    API_FOOTBALL_LEAGUE_IDS,
    FIXTURES_ENDPOINT,
    INJURIES_ENDPOINT,
    LEAGUES_ENDPOINT,
    PROVIDER_BASE_URL,
)


@dataclass(frozen=True)
class ProviderLeague:
    league: str
    expected_name: str
    country: str
    provider_league_id: int | None


PROVIDER_LEAGUES = {
    "EPL": ProviderLeague("EPL", "Premier League", "England", API_FOOTBALL_LEAGUE_IDS["EPL"]),
    "LA_LIGA": ProviderLeague("LA_LIGA", "La Liga", "Spain", API_FOOTBALL_LEAGUE_IDS["LA_LIGA"]),
    "SERIE_A": ProviderLeague("SERIE_A", "Serie A", "Italy", API_FOOTBALL_LEAGUE_IDS["SERIE_A"]),
}


class ProviderContractError(RuntimeError):
    pass


def canonical_json_sha256(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _get(session, api_key: str, endpoint: str, params: dict) -> dict:
    response = session.get(
        PROVIDER_BASE_URL + endpoint,
        headers={"x-apisports-key": api_key},
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    errors = payload.get("errors") or {}
    if errors:
        raise ProviderContractError(f"API-Football error for {endpoint}: {errors}")
    return payload


def _coverage_injuries(item: dict, season: int) -> bool:
    for entry in item.get("seasons") or []:
        if int(entry.get("year", -1)) == int(season):
            return bool((entry.get("coverage") or {}).get("injuries"))
    return False


def resolve_league(session, api_key: str, league: str, season: int) -> ProviderLeague:
    expected = PROVIDER_LEAGUES[league]
    if expected.provider_league_id is None:
        params = {"country": expected.country, "season": season}
    else:
        params = {"id": expected.provider_league_id, "season": season}
    payload = _get(session, api_key, LEAGUES_ENDPOINT, params)
    matches = []
    for item in payload.get("response") or []:
        provider_league = item.get("league") or {}
        country = item.get("country") or {}
        if (
            str(provider_league.get("name", "")).strip() == expected.expected_name
            and str(country.get("name", "")).strip() == expected.country
        ):
            matches.append(item)
    if len(matches) != 1:
        raise ProviderContractError(
            f"Expected exactly one {expected.expected_name}/{expected.country} provider league, got {len(matches)}"
        )
    item = matches[0]
    provider_id = int((item.get("league") or {})["id"])
    if expected.provider_league_id is not None and provider_id != expected.provider_league_id:
        raise ProviderContractError(f"Provider league id mismatch for {league}")
    if not _coverage_injuries(item, season):
        raise ProviderContractError(f"coverage.injuries is false for {league} season {season}")
    return ProviderLeague(league, expected.expected_name, expected.country, provider_id)


def fetch_fixtures(
    session,
    api_key: str,
    provider_league_id: int,
    season: int,
    from_date: date,
    to_date: date,
) -> list[dict]:
    payload = _get(
        session,
        api_key,
        FIXTURES_ENDPOINT,
        {
            "league": provider_league_id,
            "season": season,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "timezone": "UTC",
        },
    )
    return list(payload.get("response") or [])


def fetch_injuries(session, api_key: str, provider_fixture_id: int) -> dict:
    return _get(session, api_key, INJURIES_ENDPOINT, {"fixture": provider_fixture_id})


def build_session() -> requests.Session:
    return requests.Session()
