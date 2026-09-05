"""Outcome-blind historical 1X2 market coverage audit for Turkey and Portugal.

Reads only Football-Data fixture identity and bookmaker odds columns. It never
uses score/result fields, The Odds API, Supabase, or production model artifacts.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests

from audit_turkey_portugal_historical_foundation import season_is_complete
from league_historical_market import CANDIDATES, choose_market_triplet, no_vig_probabilities
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG

URL = "https://www.football-data.co.uk/mmz4281/{code}/{competition}.csv"
CONFIGS = (TURKEY_SUPER_LIG_RUNTIME_CONFIG, PRIMEIRA_LIGA_RUNTIME_CONFIG)


def fetch_frame(session: requests.Session, code: str, competition: str) -> pd.DataFrame:
    response = session.get(URL.format(code=code, competition=competition), timeout=30)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text))


def audit_league(config, *, as_of: date, session: requests.Session) -> dict:
    completed: list[tuple[str, pd.DataFrame]] = []
    for code, season in config.historical_source.season_codes.items():
        if season_is_complete(season, as_of):
            completed.append((season, fetch_frame(session, code, config.historical_source.competition_code)))
    if not completed:
        raise ValueError(f"{config.identity.identifier}: no completed seasons")

    frames = [frame for _, frame in completed]
    triplet = choose_market_triplet(frames)
    seasons = []
    for season, frame in completed:
        required_identity = {"Date", "HomeTeam", "AwayTeam"}
        missing_identity = required_identity - set(frame.columns)
        if missing_identity:
            raise ValueError(f"{config.identity.identifier} {season}: missing identity columns")
        odds_columns = [triplet.home, triplet.draw, triplet.away]
        odds = frame[odds_columns].apply(pd.to_numeric, errors="coerce")
        valid = odds.gt(1.0).all(axis=1)
        probs = no_vig_probabilities(odds[triplet.home], odds[triplet.draw], odds[triplet.away])
        if int(probs["market_valid"].sum()) != int(valid.sum()):
            raise ValueError("Market-valid reconciliation mismatch")
        seasons.append({
            "season": season,
            "rows": int(len(frame)),
            "valid_market_rows": int(valid.sum()),
            "coverage": float(valid.mean()) if len(frame) else 0.0,
            "missing_market_rows": int((~valid).sum()),
        })

    total_rows = sum(item["rows"] for item in seasons)
    valid_rows = sum(item["valid_market_rows"] for item in seasons)
    return {
        "league": config.identity.identifier,
        "competition_code": config.historical_source.competition_code,
        "completed_seasons": len(seasons),
        "market_source": triplet.source,
        "market_columns": [triplet.home, triplet.draw, triplet.away],
        "rows": total_rows,
        "valid_market_rows": valid_rows,
        "coverage": float(valid_rows / total_rows) if total_rows else 0.0,
        "candidate_triplets": [
            {"source": c.source, "columns": [c.home, c.draw, c.away]}
            for c in CANDIDATES
        ],
        "seasons": seasons,
    }


def run_audit(*, as_of: date) -> dict:
    session = requests.Session()
    session.headers.update({"User-Agent": "football-ai-historical-market-audit/1.0"})
    return {
        "audit": "TURKEY_PORTUGAL_HISTORICAL_MARKET_V1",
        "research_only": True,
        "outcomes_read": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "as_of": as_of.isoformat(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "leagues": [audit_league(config, as_of=as_of, session=session) for config in CONFIGS],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_audit(as_of=date.fromisoformat(args.as_of))
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
