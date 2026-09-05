"""Zero-cost current-season Football-Data CSV finished-results loader.

The loader accepts only an explicit repository runtime contract with
``finished_results_source.provider == 'FOOTBALL_DATA_CSV'``. It never guesses
competition/season codes and never calls The Odds API.
"""
from __future__ import annotations

from io import StringIO
from typing import Any

import pandas as pd
import requests

from league_offline_history import normalize_football_data_frame
from league_runtime_config import LeagueRuntimeConfig

URL = "https://www.football-data.co.uk/mmz4281/{season_code}/{competition_code}.csv"


def source_url(config: LeagueRuntimeConfig) -> str:
    source = config.finished_results_source
    if source.provider != "FOOTBALL_DATA_CSV":
        raise ValueError(
            f"{config.identity.identifier}: finished results source is not FOOTBALL_DATA_CSV"
        )
    if not source.competition_code or not source.season_code or not source.season:
        raise ValueError(f"{config.identity.identifier}: incomplete Football-Data source contract")
    return URL.format(
        season_code=source.season_code,
        competition_code=source.competition_code,
    )


def finished_mask(frame: pd.DataFrame) -> pd.Series:
    required = {"FTR", "FTHG", "FTAG"}
    if not required.issubset(frame.columns):
        missing = sorted(required - set(frame.columns))
        raise ValueError("Missing Football-Data finished-result columns: " + ", ".join(missing))
    result = frame["FTR"].astype(str).isin(["H", "D", "A"])
    home_goals = pd.to_numeric(frame["FTHG"], errors="coerce")
    away_goals = pd.to_numeric(frame["FTAG"], errors="coerce")
    return result & home_goals.notna() & away_goals.notna()


def normalize_current_results(frame: pd.DataFrame, config: LeagueRuntimeConfig) -> pd.DataFrame:
    mask = finished_mask(frame)
    finished = frame.loc[mask].copy()
    if finished.empty:
        return pd.DataFrame(
            columns=[
                "league", "season", "match_date", "home_team", "away_team",
                "home_goals", "away_goals", "result", "source", "source_competition",
            ]
        )
    normalized = normalize_football_data_frame(
        finished,
        config=config,
        season=config.finished_results_source.season,
        require_complete=False,
    )
    normalized["source"] = "football-data-csv"
    normalized["source_competition"] = config.finished_results_source.competition_code
    return normalized


def fetch_current_results(
    config: LeagueRuntimeConfig,
    *,
    session: Any | None = None,
) -> tuple[pd.DataFrame, dict]:
    url = source_url(config)
    owned = session is None
    if session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": "football-ai-current-results/1.0"})
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        text = response.text
        if not text.strip():
            raise ValueError("empty Football-Data CSV response")
        raw = pd.read_csv(StringIO(text))
    finally:
        if owned:
            session.close()
    normalized = normalize_current_results(raw, config)
    return normalized, {
        "provider": "FOOTBALL_DATA_CSV",
        "url": url,
        "source_rows": int(len(raw)),
        "finished_rows": int(len(normalized)),
        "odds_api_requests": 0,
        "odds_api_credits": 0,
    }
