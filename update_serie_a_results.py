"""Sync immutable Serie A finished results from The Odds API scores endpoint."""

from __future__ import annotations

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from database import supabase
import league_supabase_persistence as persistence
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from serie_a_scores_service import get_serie_a_scores

LEAGUE = SERIE_A_RUNTIME_CONFIG.identity.identifier
SEASON = SERIE_A_RUNTIME_CONFIG.finished_results_source.season
SOURCE = "the-odds-api"
SOURCE_COMPETITION = SERIE_A_RUNTIME_CONFIG.identity.odds_sport_key
TIMEZONE = ZoneInfo(SERIE_A_RUNTIME_CONFIG.identity.timezone)


def result_from_score(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "H"
    if away_goals > home_goals:
        return "A"
    return "D"


def _score_map(event: dict) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in event.get("scores") or []:
        name = str(row.get("name") or "").strip()
        score = row.get("score")
        if name and score is not None:
            result[name] = int(score)
    return result


def build_finished_row(event: dict) -> dict | None:
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
    canonical_home = aliases.get(home_team, home_team)
    canonical_away = aliases.get(away_team, away_team)
    return {
        "league": LEAGUE,
        "season": SEASON,
        "match_date": kickoff_local.strftime("%Y-%m-%d"),
        "match_time": kickoff_local.strftime("%H:%M"),
        "home_team": canonical_home,
        "away_team": canonical_away,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "result": result_from_score(home_goals, away_goals),
        "source": SOURCE,
        "source_competition": SOURCE_COMPETITION,
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


def sync_results(*, write: bool) -> dict:
    provider = get_serie_a_scores(days_from=3)
    frame = build_finished_frame(provider["events"])
    print("=" * 88)
    print("SERIE A FINISHED RESULTS SYNC")
    print("=" * 88)
    print("provider events:", len(provider["events"]))
    print("finished rows:", len(frame))
    print("quota:", provider["quota"])
    if not frame.empty:
        print(frame.to_string(index=False))
    if not write:
        print("DRY RUN: no Supabase writes")
        return {"inserted": 0, "unchanged": 0, "conflicts": 0, "finished_rows": len(frame)}
    metrics = persistence.persist_results(supabase, frame, SERIE_A_RUNTIME_CONFIG)
    result = {
        "inserted": int(metrics["inserted"]),
        "unchanged": int(metrics["unchanged"]),
        "conflicts": int(metrics["conflicts"]),
        "finished_rows": len(frame),
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
