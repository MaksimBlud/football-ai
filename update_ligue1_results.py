"""Sync immutable Ligue 1 finished results from configured public Football-Data CSV."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from football_data_current_results import PublicResultsSourceUnavailable, fetch_current_finished_results
import league_supabase_persistence as persistence
from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG

LEAGUE = "LIGUE_1"
SEASON = "2026-2027"
TIMEZONE = ZoneInfo("Europe/Paris")


def result_from_score(h, a):
    return "H" if h > a else "A" if a > h else "D"


def _score_map(event):
    out = {}
    for row in event.get("scores") or []:
        name = str(row.get("name") or "").strip()
        score = row.get("score")
        if name and score is not None:
            out[name] = int(score)
    return out


def build_finished_row(event):
    """Compatibility helper; operational sync no longer reads The Odds API scores."""
    if not bool(event.get("completed")):
        return None
    home = str(event.get("home_team") or "").strip()
    away = str(event.get("away_team") or "").strip()
    commence = event.get("commence_time")
    if not home or not away or not commence:
        return None
    scores = _score_map(event)
    if home not in scores or away not in scores:
        return None
    local = datetime.fromisoformat(str(commence).replace("Z", "+00:00")).astimezone(TIMEZONE)
    hg = int(scores[home])
    ag = int(scores[away])
    aliases = LIGUE1_RUNTIME_CONFIG.aliases
    return {
        "league": LEAGUE,
        "season": SEASON,
        "match_date": local.strftime("%Y-%m-%d"),
        "match_time": local.strftime("%H:%M"),
        "home_team": aliases.get(home, home),
        "away_team": aliases.get(away, away),
        "home_goals": hg,
        "away_goals": ag,
        "result": result_from_score(hg, ag),
        "source": "the-odds-api",
        "source_competition": LIGUE1_RUNTIME_CONFIG.identity.odds_sport_key,
    }


def build_finished_frame(events):
    cols = [
        "league", "season", "match_date", "match_time", "home_team", "away_team",
        "home_goals", "away_goals", "result", "source", "source_competition",
    ]
    frame = pd.DataFrame(
        [row for event in events if (row := build_finished_row(event)) is not None],
        columns=cols,
    )
    if not frame.empty and frame.duplicated(
        subset=["league", "season", "match_date", "home_team", "away_team"]
    ).any():
        raise ValueError("Duplicate Ligue 1 finished-result identity")
    return frame


def sync_results(write=False, *, client=None):
    try:
        provider = fetch_current_finished_results(LIGUE1_RUNTIME_CONFIG)
    except PublicResultsSourceUnavailable as exc:
        print("LIGUE 1 FINISHED RESULTS SYNC — PUBLIC FOOTBALL-DATA CSV")
        print("source status: TRANSIENT_UNAVAILABLE")
        print("source:", exc.url)
        print("HTTP status:", exc.status_code, "attempts:", exc.attempts)
        return {
            "status": "SOURCE_UNAVAILABLE",
            "source_url": exc.url,
            "http_status": exc.status_code,
            "inserted": 0,
            "unchanged": 0,
            "conflicts": 0,
            "finished_rows": 0,
            "public_http_requests": exc.attempts,
            "paid_provider_requests": 0,
        }

    frame = provider["frame"]
    print("LIGUE 1 FINISHED RESULTS SYNC — PUBLIC FOOTBALL-DATA CSV")
    print("source:", provider["source_url"])
    print("source rows:", provider["source_rows"])
    print("finished rows:", len(frame))
    print("paid provider requests:", provider["paid_provider_requests"])
    if not write:
        print("DRY RUN: no Supabase writes")
        return {
            "status": "DRY_RUN",
            "source_url": provider["source_url"],
            "inserted": 0,
            "unchanged": 0,
            "conflicts": 0,
            "finished_rows": len(frame),
            "public_http_requests": int(provider["public_http_requests"]),
            "paid_provider_requests": 0,
        }
    if client is None:
        from database import supabase as client
    metrics = persistence.persist_results(client, frame, LIGUE1_RUNTIME_CONFIG)
    out = {
        "status": "WRITTEN",
        "source_url": provider["source_url"],
        "inserted": int(metrics["inserted"]),
        "unchanged": int(metrics["unchanged"]),
        "conflicts": int(metrics["conflicts"]),
        "finished_rows": len(frame),
        "public_http_requests": int(provider["public_http_requests"]),
        "paid_provider_requests": 0,
    }
    print("persistence:", out)
    print("production model used:", False)
    print("Structural V2 used:", False)
    return out


def _write_status(path_value: str | None, payload: dict) -> None:
    if not path_value:
        return
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
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
