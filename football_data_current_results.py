"""Zero-cost current-season finished results from configured Football-Data CSV.

This module is deliberately independent of The Odds API and production models.
It only accepts an explicit ``FOOTBALL_DATA_CSV`` finished-results contract;
no competition or season URL is guessed at runtime.
"""
from __future__ import annotations

from io import StringIO
from typing import Callable

import pandas as pd
import requests

from league_offline_history import normalize_football_data_frame
from league_runtime_config import LeagueRuntimeConfig

BASE_URL = "https://www.football-data.co.uk/mmz4281"
PROVIDER = "FOOTBALL_DATA_CSV"
RESULT_COLUMNS = (
    "league",
    "season",
    "match_date",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
)


def configured_current_csv_url(config: LeagueRuntimeConfig) -> str:
    source = config.finished_results_source
    if source.provider != PROVIDER:
        raise ValueError(
            f"{config.identity.identifier} finished-results provider is not {PROVIDER}"
        )
    season_code = str(source.season_code).strip()
    competition_code = str(source.competition_code).strip()
    if len(season_code) != 4 or not season_code.isdigit():
        raise ValueError("Football-Data current season_code must be four digits")
    if not competition_code:
        raise ValueError("Football-Data competition_code is required")
    return f"{BASE_URL}/{season_code}/{competition_code}.csv"


def build_finished_frame(raw: pd.DataFrame, config: LeagueRuntimeConfig) -> pd.DataFrame:
    required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(
            "Missing Football-Data current-result columns: "
            + ", ".join(sorted(missing))
        )

    ftr = raw["FTR"].fillna("").astype(str).str.strip()
    unexpected = sorted(set(ftr[(ftr != "") & ~ftr.isin({"H", "D", "A"})]))
    if unexpected:
        raise ValueError("Unexpected Football-Data full-time result: " + repr(unexpected[:10]))

    finished = raw.loc[ftr.isin({"H", "D", "A"})].copy()
    if finished.empty:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    home_goals = pd.to_numeric(finished["FTHG"], errors="coerce")
    away_goals = pd.to_numeric(finished["FTAG"], errors="coerce")
    if home_goals.isna().any() or away_goals.isna().any():
        raise ValueError("Finished Football-Data row has missing/non-numeric goals")
    if ((home_goals % 1) != 0).any() or ((away_goals % 1) != 0).any():
        raise ValueError("Finished Football-Data row has non-integer goals")
    if (home_goals < 0).any() or (away_goals < 0).any():
        raise ValueError("Finished Football-Data row has negative goals")

    normalized = normalize_football_data_frame(
        finished,
        config=config,
        season=config.finished_results_source.season,
        require_complete=False,
    )
    return normalized.loc[:, RESULT_COLUMNS].copy()


def fetch_current_finished_results(
    config: LeagueRuntimeConfig,
    *,
    get: Callable = requests.get,
    timeout: int = 30,
) -> dict:
    """Fetch and validate one explicitly configured public CSV source.

    ``paid_provider_requests`` is always zero because this path never calls
    The Odds API. The public HTTP request count is reported separately.
    """
    url = configured_current_csv_url(config)
    response = get(url, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"Football-Data current results HTTP {response.status_code}: "
            + str(getattr(response, "text", ""))[:300]
        )
    raw = pd.read_csv(StringIO(response.text))
    frame = build_finished_frame(raw, config)
    return {
        "frame": frame,
        "source_url": url,
        "public_http_requests": 1,
        "paid_provider_requests": 0,
        "source_rows": int(len(raw)),
        "finished_rows": int(len(frame)),
    }
