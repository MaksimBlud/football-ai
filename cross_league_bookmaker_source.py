"""Shared zero-cost Bundesliga/Ligue 1 Football-Data source gate."""
from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd
import requests

from cross_league_direct_markets_transport import _official_or_pinned_mirror_get

BASE = "https://www.football-data.co.uk/mmz4281/{code}/{comp}.csv"
LEAGUES = {"BUNDESLIGA": "D1", "LIGUE_1": "F1"}
SEASONS = {f"{year % 100:02d}{(year + 1) % 100:02d}": f"{year}-{year + 1}" for year in range(2019, 2026)}


def download_and_audit(bookmakers: dict[str, Any]) -> tuple[dict[tuple[str, str], bytes], dict[str, Any], list[str]]:
    """Audit headers before loading outcomes and return frozen paired payloads."""
    payloads: dict[tuple[str, str], bytes] = {}
    source_files: dict[str, Any] = {}
    eligible = {bookmaker: True for bookmaker in bookmakers}
    original_get = requests.get
    try:
        requests.get = _official_or_pinned_mirror_get
        for league, competition in LEAGUES.items():
            for code, season in SEASONS.items():
                response = requests.get(BASE.format(code=code, comp=competition), timeout=60)
                response.raise_for_status()
                payload = response.content
                payloads[(league, season)] = payload
                header = pd.read_csv(BytesIO(payload), nrows=0)
                columns = set(header.columns)
                info: dict[str, Any] = {"bookmakers": {}, "has_outcome_column": "FTR" in columns}
                for bookmaker, horizon_map in bookmakers.items():
                    required = {column for cols in horizon_map.values() for column in cols}
                    missing = sorted(required - columns)
                    info["bookmakers"][bookmaker] = {"missing_required_columns": missing}
                    if season in {"2024-2025", "2025-2026"} and missing:
                        eligible[bookmaker] = False
                source_files[f"{league}:{season}"] = info
    finally:
        requests.get = original_get

    included = [bookmaker for bookmaker, ok in eligible.items() if ok]
    return payloads, {
        "outcome_read_before_audit": False,
        "candidate_bookmakers": list(bookmakers),
        "included_bookmakers": included,
        "excluded_bookmakers": [bookmaker for bookmaker in bookmakers if bookmaker not in included],
        "source_files": source_files,
        "validation_test_column_gate_passed": len(included) >= 2,
        "transport_leagues": list(LEAGUES),
    }, included
