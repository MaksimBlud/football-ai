"""Read-only external activation monitor for Prospective Availability V1."""
from __future__ import annotations

import json
import os
from pathlib import Path

import requests

OUTPUT_DIR = Path("artifacts/prospective_availability_signal_lab")
TABLES = ("prospective_availability_polls", "prospective_availability_observations")
LEAGUES = (
    ("EPL", 39, "Premier League", "England"),
    ("LA_LIGA", 140, "La Liga", "Spain"),
    ("SERIE_A", None, "Serie A", "Italy"),
)
SEASON = 2026


def _schema_state(url: str, key: str) -> dict:
    headers = {"apikey": key, "Authorization": "Bearer " + key}
    state = {}
    for table in TABLES:
        try:
            response = requests.get(
                f"{url.rstrip('/')}/rest/v1/{table}",
                headers=headers,
                params={"select": "*", "limit": 1},
                timeout=20,
            )
            state[table] = {"ready": response.status_code == 200, "status_code": response.status_code}
        except requests.RequestException as exc:
            state[table] = {"ready": False, "error": type(exc).__name__}
    return state


def _provider_state(key: str) -> dict:
    headers = {"x-apisports-key": key}
    state = {}
    for league, known_id, expected_name, expected_country in LEAGUES:
        params = {"season": SEASON}
        if known_id is None:
            params["country"] = expected_country
        else:
            params["id"] = known_id
        try:
            response = requests.get(
                "https://v3.football.api-sports.io/leagues",
                headers=headers,
                params=params,
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            state[league] = {"ready": False, "error": type(exc).__name__}
            continue
        if payload.get("errors"):
            state[league] = {"ready": False, "provider_errors_present": True}
            continue
        matches = []
        for item in payload.get("response") or []:
            provider_league = item.get("league") or {}
            country = item.get("country") or {}
            if provider_league.get("name") == expected_name and country.get("name") == expected_country:
                matches.append(item)
        if len(matches) != 1:
            state[league] = {"ready": False, "matching_leagues": len(matches)}
            continue
        item = matches[0]
        provider_id = int(item["league"]["id"])
        season = next((s for s in item.get("seasons") or [] if int(s.get("year", -1)) == SEASON), None)
        injuries = bool(((season or {}).get("coverage") or {}).get("injuries"))
        id_ok = known_id is None or provider_id == known_id
        state[league] = {
            "ready": bool(id_ok and injuries),
            "provider_id": provider_id,
            "coverage_injuries": injuries,
        }
    return state


def run() -> dict:
    required = ("SUPABASE_URL", "SUPABASE_KEY", "API_FOOTBALL_KEY")
    secrets_present = {name: bool(os.getenv(name)) for name in required}
    schema = {}
    provider = {}
    if secrets_present["SUPABASE_URL"] and secrets_present["SUPABASE_KEY"]:
        schema = _schema_state(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
    if secrets_present["API_FOOTBALL_KEY"]:
        provider = _provider_state(os.environ["API_FOOTBALL_KEY"])
    schema_ready = len(schema) == len(TABLES) and all(item.get("ready") for item in schema.values())
    provider_ready = len(provider) == len(LEAGUES) and all(item.get("ready") for item in provider.values())
    ready = all(secrets_present.values()) and schema_ready and provider_ready
    payload = {
        "status": "READY" if ready else "BLOCKED",
        "season": SEASON,
        "secrets_present": secrets_present,
        "schema": schema,
        "provider": provider,
        "automatic_activation": False,
        "automatic_collection_enablement": False,
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "activation_readiness.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"PROSPECTIVE_AVAILABILITY_ACTIVATION={payload['status']}")
    print(f"SCHEMA_READY={schema_ready} PROVIDER_READY={provider_ready}")
    print("READ_ONLY_ACTIVATION_MONITOR: no DDL, no Supabase writes, no collector activation")
    return payload


if __name__ == "__main__":
    run()
