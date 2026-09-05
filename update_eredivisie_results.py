"""Sync immutable Eredivisie finished results from configured public Football-Data CSV."""

from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from database import supabase
from football_data_current_results import fetch_current_finished_results
import league_supabase_persistence as persistence
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG

LEAGUE = EREDIVISIE_RUNTIME_CONFIG.identity.identifier
SEASON = EREDIVISIE_RUNTIME_CONFIG.finished_results_source.season
TIMEZONE = ZoneInfo(EREDIVISIE_RUNTIME_CONFIG.identity.timezone)


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
    aliases = EREDIVISIE_RUNTIME_CONFIG.aliases
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
        "source_competition": EREDIVISIE_RUNTIME_CONFIG.identity.odds_sport_key,
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
        raise ValueError("Duplicate Eredivisie finished-result identity from provider")
    return frame


def sync_results(*, write: bool) -> dict:
    provider = fetch_current_finished_results(EREDIVISIE_RUNTIME_CONFIG)
    frame = provider["frame"]
    print("=" * 88)
    print("EREDIVISIE FINISHED RESULTS SYNC — PUBLIC FOOTBALL-DATA CSV")
    print("=" * 88)
    print("source:", provider["source_url"])
    print("source rows:", provider["source_rows"])
    print("finished rows:", len(frame))
    print("paid provider requests:", provider["paid_provider_requests"])
    if not frame.empty:
        print(frame.to_string(index=False))
    if not write:
        print("DRY RUN: no Supabase writes")
        return {
            "inserted": 0, "unchanged": 0, "conflicts": 0,
            "finished_rows": len(frame), "paid_provider_requests": 0,
        }
    metrics = persistence.persist_results(supabase, frame, EREDIVISIE_RUNTIME_CONFIG)
    result = {
        "inserted": int(metrics["inserted"]),
        "unchanged": int(metrics["unchanged"]),
        "conflicts": int(metrics["conflicts"]),
        "finished_rows": len(frame),
        "paid_provider_requests": 0,
    }
    print("persistence:", result)
    print("production model used:", False)
    print("Structural V2 used:", False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    sync_results(write=args.write)


if __name__ == "__main__":
    main()
