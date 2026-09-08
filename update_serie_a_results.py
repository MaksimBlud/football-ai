"""Sync immutable Serie A finished results from provider-free public sources.

Football-Data remains primary. ESPN scoreboard is a keyless fallback used only
after bounded transient primary-source exhaustion. No Odds API calls are made.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from espn_current_results_fallback import (
    ESPNResultsSourceUnavailable,
    PROVIDER as ESPN_PROVIDER,
    fetch_football_data_like_results,
)
from football_data_current_results import (
    PublicResultsSourceUnavailable,
    build_finished_frame as build_public_finished_frame,
    fetch_current_finished_results,
)
import league_supabase_persistence as persistence
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG

LEAGUE = SERIE_A_RUNTIME_CONFIG.identity.identifier
SEASON = SERIE_A_RUNTIME_CONFIG.finished_results_source.season
TIMEZONE = ZoneInfo(SERIE_A_RUNTIME_CONFIG.identity.timezone)


def result_from_score(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "H"
    if away_goals > home_goals:
        return "A"
    return "D"


def _score_map(event: dict) -> dict[str, int]:
    """Compatibility helper for historical Odds-API-shaped unit fixtures."""
    result: dict[str, int] = {}
    for row in event.get("scores") or []:
        name = str(row.get("name") or "").strip()
        score = row.get("score")
        if name and score is not None:
            result[name] = int(score)
    return result


def build_finished_row(event: dict) -> dict | None:
    """Pure compatibility converter; the operational sync no longer calls it."""
    if not bool(event.get("completed")):
        return None
    home_team = str(event.get("home_team") or "").strip()
    away_team = str(event.get("away_team") or "").strip()
    commence = event.get("commence_time")
    if not home_team or not away_team or not commence:
        return None
    scores = _score_map(event)
    if home_team not in scores or away_team not in scores:
        return None
    kickoff_utc = datetime.fromisoformat(str(commence).replace("Z", "+00:00"))
    kickoff_local = kickoff_utc.astimezone(TIMEZONE)
    home_goals = int(scores[home_team])
    away_goals = int(scores[away_team])
    aliases = SERIE_A_RUNTIME_CONFIG.aliases
    return {
        "league": LEAGUE,
        "season": SEASON,
        "match_date": kickoff_local.strftime("%Y-%m-%d"),
        "match_time": kickoff_local.strftime("%H:%M"),
        "home_team": aliases.get(home_team, home_team),
        "away_team": aliases.get(away_team, away_team),
        "home_goals": home_goals,
        "away_goals": away_goals,
        "result": result_from_score(home_goals, away_goals),
        "source": "the-odds-api",
        "source_competition": SERIE_A_RUNTIME_CONFIG.identity.odds_sport_key,
    }


def build_finished_frame(events: list[dict]) -> pd.DataFrame:
    rows = [row for event in events if (row := build_finished_row(event)) is not None]
    columns = [
        "league", "season", "match_date", "match_time", "home_team", "away_team",
        "home_goals", "away_goals", "result", "source", "source_competition",
    ]
    frame = pd.DataFrame(rows, columns=columns)
    if frame.empty:
        return frame
    identity = ["league", "season", "match_date", "home_team", "away_team"]
    if frame.duplicated(subset=identity).any():
        raise ValueError("Duplicate Serie A finished-result identity from provider")
    return frame


def fetch_espn_finished_results() -> dict:
    """Fetch zero-cost fallback and reuse the existing generic normalizer."""
    provider = fetch_football_data_like_results(league=LEAGUE)
    frame = build_public_finished_frame(provider["frame"], SERIE_A_RUNTIME_CONFIG)
    return {
        **provider,
        "frame": frame,
        "finished_rows": int(len(frame)),
    }


def _source_unavailable(primary: PublicResultsSourceUnavailable, fallback: ESPNResultsSourceUnavailable) -> dict:
    return {
        "status": "SOURCE_UNAVAILABLE",
        "source_url": fallback.url,
        "source_provider": ESPN_PROVIDER,
        "http_status": fallback.status_code,
        "primary_source_url": primary.url,
        "primary_http_status": int(primary.status_code),
        "primary_public_http_requests": int(primary.attempts),
        "fallback_used": True,
        "fallback_public_http_requests": int(fallback.attempts),
        "inserted": 0,
        "unchanged": 0,
        "conflicts": 0,
        "finished_rows": 0,
        "public_http_requests": int(primary.attempts + fallback.attempts),
        "paid_provider_requests": 0,
    }


def sync_results(
    *,
    write: bool,
    client=None,
    fetch_fn=None,
    fallback_fn=None,
) -> dict:
    if fetch_fn is None:
        fetch_fn = fetch_current_finished_results
    if fallback_fn is None:
        fallback_fn = fetch_espn_finished_results

    primary_error: PublicResultsSourceUnavailable | None = None
    try:
        provider = fetch_fn(SERIE_A_RUNTIME_CONFIG)
        fallback_used = False
    except PublicResultsSourceUnavailable as exc:
        primary_error = exc
        try:
            provider = fallback_fn()
            fallback_used = True
        except ESPNResultsSourceUnavailable as fallback_exc:
            result = _source_unavailable(exc, fallback_exc)
            print("=" * 88)
            print("SERIE A FINISHED RESULTS SYNC — BOTH PUBLIC SOURCES UNAVAILABLE")
            print("=" * 88)
            print("primary:", exc.url, exc.status_code, "attempts:", exc.attempts)
            print("fallback:", fallback_exc.url, fallback_exc.status_code, "attempts:", fallback_exc.attempts)
            return result

    frame = provider["frame"]
    source_provider = str(provider.get("source_provider") or "FOOTBALL_DATA_CSV")
    total_requests = int(provider["public_http_requests"] + (primary_error.attempts if primary_error else 0))

    print("=" * 88)
    print("SERIE A FINISHED RESULTS SYNC — PROVIDER-FREE PUBLIC RESULTS")
    print("=" * 88)
    print("source:", provider["source_url"])
    print("source provider:", source_provider)
    print("fallback used:", fallback_used)
    print("source rows:", provider["source_rows"])
    print("finished rows:", len(frame))
    print("paid provider requests:", provider["paid_provider_requests"])
    if not frame.empty:
        print(frame.to_string(index=False))

    base = {
        "source_url": provider["source_url"],
        "source_provider": source_provider,
        "fallback_used": bool(fallback_used),
        "primary_public_http_requests": int(primary_error.attempts if primary_error else provider["public_http_requests"]),
        "fallback_public_http_requests": int(provider["public_http_requests"] if fallback_used else 0),
        "finished_rows": len(frame),
        "public_http_requests": total_requests,
        "paid_provider_requests": 0,
    }
    if primary_error is not None:
        base["primary_source_url"] = primary_error.url
        base["primary_http_status"] = int(primary_error.status_code)

    if not write:
        print("DRY RUN: no Supabase writes")
        return {
            **base,
            "status": "DRY_RUN",
            "inserted": 0,
            "unchanged": 0,
            "conflicts": 0,
        }

    if client is None:
        from database import supabase as client
    metrics = persistence.persist_results(client, frame, SERIE_A_RUNTIME_CONFIG)
    result = {
        **base,
        "status": "WRITTEN",
        "inserted": int(metrics["inserted"]),
        "unchanged": int(metrics["unchanged"]),
        "conflicts": int(metrics["conflicts"]),
    }
    print("persistence:", result)
    print("production model used:", False)
    print("Structural V2 used:", False)
    return result


def _write_status(path_value: str | None, payload: dict) -> None:
    if not path_value:
        return
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--status-json")
    args = parser.parse_args()
    try:
        result = sync_results(write=args.write)
    except Exception as exc:
        failure = {
            "league": LEAGUE,
            "status": "FAILED",
            "error_type": type(exc).__name__,
            "error": str(exc)[:1000],
            "paid_provider_requests": 0,
        }
        _write_status(args.status_json, failure)
        raise
    payload = {"league": LEAGUE, **result}
    _write_status(args.status_json, payload)
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
