"""Zero-Odds-API cross-source team identity audit for Turkey and Portugal.

The audit compares current-season Football-Data team identities with team names
already persisted in canonical ``odds_snapshots``. It is read-only and does not
consume The Odds API quota or read match outcomes.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


FOOTBALL_DATA_URL = "https://www.football-data.co.uk/mmz4281/{code}/{competition}.csv"
LEAGUES = (
    TURKEY_SUPER_LIG_RUNTIME_CONFIG,
    PRIMEIRA_LIGA_RUNTIME_CONFIG,
)


def _canonical(name: str, aliases: dict[str, str]) -> str:
    value = str(name or "").strip()
    return str(aliases.get(value, value)).strip()


def _current_season_contract(config) -> tuple[str, str]:
    items = list(config.historical_source.season_codes.items())
    if not items:
        raise ValueError(f"{config.identity.identifier}: no configured seasons")
    return items[-1]


def fetch_current_football_data_teams(config, session: requests.Session) -> dict:
    code, season = _current_season_contract(config)
    competition = config.historical_source.competition_code
    url = FOOTBALL_DATA_URL.format(code=code, competition=competition)
    response = session.get(url, timeout=30)
    response.raise_for_status()
    frame = pd.read_csv(StringIO(response.text))
    required = {"HomeTeam", "AwayTeam"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{config.identity.identifier}: missing columns {sorted(missing)}")
    raw = sorted(
        set(frame["HomeTeam"].dropna().astype(str).str.strip())
        | set(frame["AwayTeam"].dropna().astype(str).str.strip())
    )
    canonical = sorted({_canonical(team, config.aliases) for team in raw})
    return {
        "season": season,
        "url": url,
        "source_rows": int(len(frame)),
        "raw_teams": raw,
        "canonical_teams": canonical,
    }


def fetch_snapshot_teams(config, supabase_client) -> dict:
    league = config.identity.identifier
    response = (
        supabase_client.table("odds_snapshots")
        .select("event_id,commence_time_utc,home_team,away_team")
        .eq("league", league)
        .order("commence_time_utc", desc=True)
        .limit(1000)
        .execute()
    )
    rows = list(response.data or [])
    raw = sorted(
        {
            str(row.get(field) or "").strip()
            for row in rows
            for field in ("home_team", "away_team")
            if str(row.get(field) or "").strip()
        }
    )
    canonical = sorted({_canonical(team, config.aliases) for team in raw})
    events = {str(row.get("event_id") or "").strip() for row in rows if row.get("event_id")}
    return {
        "snapshot_rows": len(rows),
        "unique_events": len(events),
        "raw_teams": raw,
        "canonical_teams": canonical,
    }


def compare_identity(config, football_data: dict, snapshots: dict) -> dict:
    historical = set(football_data["canonical_teams"])
    provider = set(snapshots["canonical_teams"])
    provider_only = sorted(provider - historical)
    historical_not_observed = sorted(historical - provider)

    if snapshots["snapshot_rows"] == 0:
        status = "BLOCKED_NO_CANONICAL_SNAPSHOTS"
    elif provider_only:
        status = "ALIAS_REQUIRED"
    else:
        status = "READY"

    return {
        "league": config.identity.identifier,
        "season": football_data["season"],
        "status": status,
        "aliases_configured": dict(config.aliases),
        "football_data_source_rows": football_data["source_rows"],
        "football_data_team_count": len(historical),
        "snapshot_rows": snapshots["snapshot_rows"],
        "snapshot_unique_events": snapshots["unique_events"],
        "snapshot_team_count": len(provider),
        "provider_only_unmatched": provider_only,
        "historical_not_observed_in_snapshots": historical_not_observed,
        "football_data_raw_teams": football_data["raw_teams"],
        "snapshot_raw_teams": snapshots["raw_teams"],
    }


def run_audit(*, supabase_client=None, session: requests.Session | None = None) -> dict:
    if supabase_client is None:
        from database import supabase as supabase_client
    session = session or requests.Session()
    session.headers.update({"User-Agent": "football-ai-team-identity-audit/1.0"})

    leagues = []
    for config in LEAGUES:
        football_data = fetch_current_football_data_teams(config, session)
        snapshots = fetch_snapshot_teams(config, supabase_client)
        leagues.append(compare_identity(config, football_data, snapshots))

    return {
        "audit": "TURKEY_PORTUGAL_TEAM_IDENTITY_V1",
        "research_only": True,
        "outcomes_read": False,
        "odds_api_requests": 0,
        "supabase_reads": True,
        "supabase_writes": 0,
        "production_model_operations": 0,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "leagues": leagues,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_audit()
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
