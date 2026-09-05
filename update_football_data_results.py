"""Fetch and optionally persist zero-cost current Football-Data results."""
from __future__ import annotations

import argparse
import json

from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
from database import supabase
from football_data_current_results import fetch_current_results
from league_supabase_persistence import persist_results
from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG

CONFIGS = {
    "SERIE_A": SERIE_A_RUNTIME_CONFIG,
    "BUNDESLIGA": BUNDESLIGA_RUNTIME_CONFIG,
    "LIGUE_1": LIGUE1_RUNTIME_CONFIG,
}


def run(league: str, *, write: bool = False, session=None, client=None) -> dict:
    if league not in CONFIGS:
        raise ValueError(f"Unsupported zero-cost current-results league: {league!r}")
    config = CONFIGS[league]
    frame, source = fetch_current_results(config, session=session)
    persistence = {"inserted": 0, "unchanged": 0, "conflicts": 0}
    if write:
        persistence = persist_results(client or supabase, frame, config)
    return {
        "league": league,
        "season": config.finished_results_source.season,
        "provider": config.finished_results_source.provider,
        "source": source,
        "finished_rows": int(len(frame)),
        "write_requested": bool(write),
        "persistence": persistence,
        "odds_api_requests": 0,
        "odds_api_credits": 0,
        "production_model_used": False,
        "structural_v2_used": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("league", choices=sorted(CONFIGS))
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.league, write=args.write), indent=2, default=str))


if __name__ == "__main__":
    main()
