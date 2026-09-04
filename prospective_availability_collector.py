"""Collect prospective pre-match availability without touching production inference."""
from __future__ import annotations

from datetime import datetime, timezone
import os

import pandas as pd

from database import supabase
from league_fixture_export import prepare_upcoming_fixtures
from league_runtime_config import EPL_RUNTIME_CONFIG, LA_LIGA_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
import prospective_availability_persistence as persistence
from prospective_availability_provider import (
    build_session,
    fetch_fixtures,
    fetch_injuries,
    resolve_league,
)
from prospective_availability_snapshot import match_provider_fixture, normalize_poll

SEASON = 2026
LOOKAHEAD_DAYS = 14
LEAGUE_ORDER = ("EPL", "LA_LIGA", "SERIE_A")
RUNTIMES = {
    "EPL": EPL_RUNTIME_CONFIG,
    "LA_LIGA": LA_LIGA_RUNTIME_CONFIG,
    "SERIE_A": SERIE_A_RUNTIME_CONFIG,
}


def load_upcoming(runtime, *, now=None) -> pd.DataFrame:
    response = (
        supabase.table("odds_snapshots")
        .select("league,event_id,snapshot_time_utc,commence_time_utc,home_team,away_team")
        .eq("league", runtime.identity.identifier)
        .order("snapshot_time_utc", desc=True)
        .limit(10000)
        .execute()
    )
    return prepare_upcoming_fixtures(
        pd.DataFrame(response.data or []),
        runtime,
        normalize_team=lambda value: runtime.aliases.get(str(value).strip(), str(value).strip()),
        now=now,
    )


def preflight_provider(session, api_key: str) -> dict[str, object]:
    """Resolve every required league before any collector persistence is allowed."""
    resolved = {}
    for league in LEAGUE_ORDER:
        resolved[league] = resolve_league(session, api_key, league, SEASON)
    return resolved


def collect_league(
    session,
    api_key: str,
    league: str,
    *,
    resolved_league=None,
    observed_at=None,
) -> dict:
    runtime = RUNTIMES[league]
    observed = pd.Timestamp(observed_at or datetime.now(timezone.utc))
    if observed.tzinfo is None:
        observed = observed.tz_localize("UTC")
    observed = observed.tz_convert("UTC")
    resolved = resolved_league or resolve_league(session, api_key, league, SEASON)
    upcoming = load_upcoming(runtime, now=observed.to_pydatetime())
    horizon = observed + pd.Timedelta(days=LOOKAHEAD_DAYS)
    upcoming = upcoming.loc[pd.to_datetime(upcoming["commence_time_utc"], utc=True) <= horizon].copy()
    provider_fixtures = fetch_fixtures(
        session,
        api_key,
        int(resolved.provider_league_id),
        SEASON,
        observed.date(),
        horizon.date(),
    )
    metrics = {
        "league": league,
        "canonical_fixtures": len(upcoming),
        "matched_fixtures": 0,
        "unmatched_fixtures": 0,
        "polls_inserted": 0,
        "polls_unchanged": 0,
        "observations_inserted": 0,
        "observations_unchanged": 0,
    }
    for _, fixture_row in upcoming.iterrows():
        canonical = fixture_row.to_dict()
        try:
            provider_fixture = match_provider_fixture(
                canonical,
                provider_fixtures,
                aliases=dict(runtime.aliases),
            )
        except ValueError as exc:
            metrics["unmatched_fixtures"] += 1
            print(f"WAIT {league} fixture {canonical.get('event_id')}: {exc}")
            continue
        injury_payload = fetch_injuries(
            session,
            api_key,
            int((provider_fixture.get("fixture") or {})["id"]),
        )
        poll, observations = normalize_poll(
            canonical_row=canonical,
            provider_fixture=provider_fixture,
            injury_payload=injury_payload,
            observed_at_utc=observed,
        )
        persisted = persistence.persist_poll(supabase, poll, observations)
        metrics["matched_fixtures"] += 1
        metrics["polls_inserted"] += int(persisted["poll_inserted"])
        metrics["polls_unchanged"] += int(persisted["poll_unchanged"])
        metrics["observations_inserted"] += int(persisted["observations_inserted"])
        metrics["observations_unchanged"] += int(persisted["observations_unchanged"])
    return metrics


def run() -> list[dict]:
    status, detail = persistence.check_schema(supabase)
    if status != "PASS":
        raise RuntimeError(detail)
    api_key = os.getenv("API_FOOTBALL_KEY", "").strip()
    if not api_key:
        raise RuntimeError("API_FOOTBALL_KEY is required; value is never printed")
    session = build_session()

    # Global activation barrier: all required provider league identities and injury
    # coverage must resolve successfully before the first persistence path is entered.
    resolved = preflight_provider(session, api_key)
    print("PASS: global provider preflight complete for EPL, LA_LIGA, SERIE_A")

    results = []
    for league in LEAGUE_ORDER:
        metrics = collect_league(
            session,
            api_key,
            league,
            resolved_league=resolved[league],
        )
        results.append(metrics)
        print(metrics)
    return results


if __name__ == "__main__":
    run()
