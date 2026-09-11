"""Support helpers for frozen Turkey Super Lig nested development V1."""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from feature_engineering import build_features
from league_model_sweep import TARGET_MAP
from league_offline_history import parse_football_data_date, validate_complete_double_round_robin
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG

LEAGUE = "TURKEY_SUPER_LIG"
CURRENT_FORBIDDEN_SEASON = "2026-2027"
EXCLUDED_SEASON = "2022-2023"
CONFIGURED_SEASONS = (
    "2016-2017", "2017-2018", "2018-2019", "2019-2020", "2020-2021",
    "2021-2022", "2022-2023", "2023-2024", "2024-2025", "2025-2026",
    "2026-2027",
)
ADMITTED_SEASONS = tuple(s for s in CONFIGURED_SEASONS if s not in {EXCLUDED_SEASON, CURRENT_FORBIDDEN_SEASON})
BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/{competition}.csv"
PRODUCTION_ARTIFACTS = (
    "football_model_xgboost_elo.pkl", "football_model_no_odds.pkl", "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl", "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl", "btts_calibrator.pkl",
)
REQUIRED = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR", "B365H", "B365D", "B365A"}
COLUMN_MAP = {
    "Date": "match_date", "Time": "match_time", "HomeTeam": "home_team", "AwayTeam": "away_team",
    "FTHG": "home_goals", "FTAG": "away_goals", "FTR": "result",
    "HS": "home_shots", "AS": "away_shots", "HST": "home_shots_target", "AST": "away_shots_target",
    "HC": "home_corners", "AC": "away_corners", "HY": "home_yellow", "AY": "away_yellow",
    "HR": "home_red", "AR": "away_red", "B365H": "home_odds", "B365D": "draw_odds", "B365A": "away_odds",
}
STATS = (
    "home_shots", "away_shots", "home_shots_target", "away_shots_target",
    "home_corners", "away_corners", "home_yellow", "away_yellow", "home_red", "away_red",
)


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def production_state(root: Path) -> dict[str, str | None]:
    return {name: sha256(root / name) for name in PRODUCTION_ARTIFACTS}


def _fetch(url: str, path: Path) -> None:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 football-ai-research"})
    with urlopen(request, timeout=60) as response:
        content = response.read()
    if len(content) < 1000:
        raise RuntimeError(f"Suspiciously small historical source: {url}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _required(source: pd.DataFrame, season: str) -> None:
    missing = REQUIRED - set(source.columns)
    if missing:
        raise ValueError(f"Turkey Super Lig {season}: missing source columns {sorted(missing)}")


def _normalize(source: pd.DataFrame, season: str) -> pd.DataFrame:
    _required(source, season)
    validate_complete_double_round_robin(source, season=season)
    frame = pd.DataFrame({target: source[src] if src in source.columns else pd.NA for src, target in COLUMN_MAP.items()})
    frame["match_date"] = parse_football_data_date(frame["match_date"])
    frame["match_time"] = frame["match_time"].fillna("00:00").astype(str)
    aliases = TURKEY_SUPER_LIG_RUNTIME_CONFIG.aliases
    for team_col in ("home_team", "away_team"):
        frame[team_col] = frame[team_col].astype(str).str.strip().replace(aliases)
    for col in ("home_goals", "away_goals", *STATS, "home_odds", "draw_odds", "away_odds"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    for col in STATS:
        frame[col] = frame[col].fillna(0.0)
    frame["season"], frame["league"] = season, LEAGUE
    if not set(frame["result"].astype(str)).issubset({"H", "D", "A"}):
        raise ValueError(f"Turkey Super Lig {season}: invalid result code")
    odds = frame[["home_odds", "draw_odds", "away_odds"]]
    if (odds.notna() & (odds <= 1.0)).any().any():
        raise ValueError(f"Turkey Super Lig {season}: invalid B365 odds")
    return frame


def build_history(work_dir: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    config = TURKEY_SUPER_LIG_RUNTIME_CONFIG
    if tuple(config.historical_source.season_codes.values()) != CONFIGURED_SEASONS:
        raise RuntimeError("Configured Turkey seasons changed from frozen contract")
    frames, excluded_rows = [], {}
    competition = config.historical_source.competition_code
    for code, season in config.historical_source.season_codes.items():
        if season == CURRENT_FORBIDDEN_SEASON:
            continue
        path = work_dir / "raw" / f"{competition}_{code}.csv"
        if not path.exists():
            _fetch(BASE_URL.format(code=code, competition=competition), path)
        source = pd.read_csv(path, encoding_errors="replace")
        _required(source, season)
        if season == EXCLUDED_SEASON:
            if source.empty:
                raise ValueError("Excluded 2022-2023 source is empty")
            excluded_rows[season] = int(len(source))
            continue
        frames.append(_normalize(source, season))
    history = pd.concat(frames, ignore_index=True).sort_values(
        ["match_date", "match_time", "home_team", "away_team"], kind="stable"
    ).reset_index(drop=True)
    observed = set(history["season"].astype(str).unique())
    if observed != set(ADMITTED_SEASONS) or EXCLUDED_SEASON in observed or CURRENT_FORBIDDEN_SEASON in observed:
        raise ValueError(f"Historical evidence boundary mismatch: {sorted(observed)}")
    if set(excluded_rows) != {EXCLUDED_SEASON}:
        raise RuntimeError("Frozen excluded season was not verified")
    return history, excluded_rows


def build_trainable_features(history: pd.DataFrame) -> pd.DataFrame:
    ordered = history.sort_values(["match_date", "match_time", "home_team", "away_team"], kind="stable").reset_index(drop=True)
    config = TURKEY_SUPER_LIG_RUNTIME_CONFIG
    counts, ratings = {}, {}
    home_prior, away_prior, home_elos, away_elos = [], [], [], []
    initial, k, home_adv = float(config.elo.initial_rating), float(config.elo.k_factor), float(config.elo.home_advantage)
    for row in ordered.itertuples(index=False):
        home, away = str(row.home_team), str(row.away_team)
        hp, ap = counts.get(home, 0), counts.get(away, 0)
        hr, ar = ratings.get(home, initial), ratings.get(away, initial)
        home_prior.append(hp); away_prior.append(ap); home_elos.append(hr); away_elos.append(ar)
        expected = 1.0 / (1.0 + 10.0 ** ((ar - (hr + home_adv)) / 400.0))
        actual = 1.0 if row.result == "H" else (0.0 if row.result == "A" else 0.5)
        delta = k * (actual - expected)
        ratings[home], ratings[away] = hr + delta, ar - delta
        counts[home], counts[away] = hp + 1, ap + 1
    features = build_features(ordered.copy())
    features.insert(0, "league", LEAGUE)
    features["home_prior_matches"], features["away_prior_matches"] = home_prior, away_prior
    minimum = int(config.temporal.min_prior_matches)
    features["warmup_ok"] = (features.home_prior_matches >= minimum) & (features.away_prior_matches >= minimum)
    features["home_elo"], features["away_elo"] = home_elos, away_elos
    features["elo_difference"] = features["home_elo"] - features["away_elo"]
    features["target"] = features["result"].map(TARGET_MAP)
    features = features[features["warmup_ok"]].copy().reset_index(drop=True)
    if set(features["season"].astype(str).unique()) != set(ADMITTED_SEASONS):
        raise ValueError("Trainable features crossed frozen historical boundary")
    return features


def simplex(probability: np.ndarray) -> np.ndarray:
    result = np.asarray(probability, dtype=float)
    if result.ndim != 2 or result.shape[1] != 3 or not np.isfinite(result).all():
        raise ValueError("Invalid probability matrix")
    result = np.clip(result, 1e-15, None)
    return result / result.sum(axis=1, keepdims=True)
