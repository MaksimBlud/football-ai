"""Live, zero-cost historical foundation audit for Turkey and Portugal.

Research-only contract:
- reads public Football-Data CSV files only;
- never calls The Odds API;
- never reads/writes Supabase;
- never loads, trains, or promotes production models;
- validates only seasons that are complete as of the audit date;
- treats the current/in-progress season as availability-only.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import date, datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

from league_offline_features import build_temporal_elo_features
from league_offline_history import normalize_football_data_frame
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


FOOTBALL_DATA_URL = "https://www.football-data.co.uk/mmz4281/{code}/{competition}.csv"
FEATURE_COLUMNS = {
    "home_prior_matches",
    "away_prior_matches",
    "home_last5_points",
    "away_last5_points",
    "form_difference",
    "home_goals_scored_last5",
    "home_goals_conceded_last5",
    "away_goals_scored_last5",
    "away_goals_conceded_last5",
    "home_venue_win_rate",
    "away_venue_win_rate",
    "venue_win_rate_difference",
    "home_elo",
    "away_elo",
    "elo_diff",
    "elo_difference",
    "trainable",
}


def season_is_complete(season: str, as_of: date) -> bool:
    """Conservatively classify European Aug-May seasons as completed after June."""
    _, end_year_raw = season.split("-", maxsplit=1)
    end_year = int(end_year_raw)
    return end_year < as_of.year or (end_year == as_of.year and as_of.month >= 7)


def _fetch_csv(
    session: requests.Session,
    *,
    code: str,
    competition: str,
    attempts: int = 4,
) -> tuple[pd.DataFrame, str]:
    url = FOOTBALL_DATA_URL.format(code=code, competition=competition)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            if not response.text.strip():
                raise ValueError("empty CSV response")
            return pd.read_csv(StringIO(response.text)), url
        except (requests.RequestException, ValueError, pd.errors.ParserError) as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(float(attempt))

    raise RuntimeError(f"Unable to fetch {url}: {last_error}")


def _canonical_team_collision_check(source: pd.DataFrame, config) -> None:
    raw_teams = sorted(
        set(source["HomeTeam"].dropna().astype(str).str.strip())
        | set(source["AwayTeam"].dropna().astype(str).str.strip())
    )
    canonical = [config.aliases.get(team, team) for team in raw_teams]
    if len(set(canonical)) != len(canonical):
        raise ValueError("Configured aliases collapse distinct teams within a season")


def _feature_contract_check(features: pd.DataFrame, normalized: pd.DataFrame) -> None:
    missing = FEATURE_COLUMNS - set(features.columns)
    if missing:
        raise ValueError("Missing temporal feature columns: " + ", ".join(sorted(missing)))
    if len(features) != len(normalized):
        raise ValueError("Temporal feature row count differs from normalized history")
    if features[list(FEATURE_COLUMNS - {"trainable"})].isna().any().any():
        raise ValueError("Temporal feature columns contain null values")
    if not features["trainable"].isin([True, False]).all():
        raise ValueError("Unexpected trainable values")

    first_home = features.groupby("home_team", sort=False).head(1)
    first_away = features.groupby("away_team", sort=False).head(1)
    if (first_home["home_prior_matches"] < 0).any() or (first_away["away_prior_matches"] < 0).any():
        raise ValueError("Negative prior-match count")


def audit_league(config, *, as_of: date, session: requests.Session) -> dict:
    config.validate()
    source_contract = config.historical_source
    completed_normalized: list[pd.DataFrame] = []
    seasons: list[dict] = []

    for code, season in source_contract.season_codes.items():
        source, url = _fetch_csv(
            session,
            code=code,
            competition=source_contract.competition_code,
        )
        completed = season_is_complete(season, as_of)
        record = {
            "code": code,
            "season": season,
            "url": url,
            "available": True,
            "completed": completed,
            "source_rows": int(len(source)),
        }

        required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
        missing = required - set(source.columns)
        if missing:
            raise ValueError(f"{config.identity.identifier} {season}: missing columns {sorted(missing)}")

        _canonical_team_collision_check(source, config)
        raw_teams = sorted(
            set(source["HomeTeam"].dropna().astype(str).str.strip())
            | set(source["AwayTeam"].dropna().astype(str).str.strip())
        )
        record["raw_team_count"] = len(raw_teams)
        record["aliases_applied"] = sum(1 for team in raw_teams if team in config.aliases)

        if completed:
            normalized = normalize_football_data_frame(
                source,
                config=config,
                season=season,
                require_complete=True,
            )
            completed_normalized.append(normalized)
            record["normalized_rows"] = int(len(normalized))
            record["expected_rows"] = int(len(raw_teams) * (len(raw_teams) - 1))
            record["complete_double_round_robin"] = True
        else:
            record["normalized_rows"] = 0
            record["complete_double_round_robin"] = None

        seasons.append(record)

    if not completed_normalized:
        raise ValueError(f"{config.identity.identifier}: no completed seasons available")

    combined = pd.concat(completed_normalized, ignore_index=True).sort_values(
        ["match_date", "home_team", "away_team"], kind="stable"
    ).reset_index(drop=True)
    features = build_temporal_elo_features(combined, config)
    _feature_contract_check(features, combined)

    return {
        "league": config.identity.identifier,
        "competition_code": source_contract.competition_code,
        "configured_seasons": len(source_contract.season_codes),
        "available_seasons": sum(int(item["available"]) for item in seasons),
        "completed_seasons": sum(int(item["completed"]) for item in seasons),
        "completed_matches": int(len(combined)),
        "canonical_teams_across_completed_history": int(
            len(set(combined["home_team"]) | set(combined["away_team"]))
        ),
        "temporal_feature_rows": int(len(features)),
        "trainable_rows": int(features["trainable"].sum()),
        "calibration_status": config.structural_v2.calibration_status,
        "aliases_configured": dict(config.aliases),
        "seasons": seasons,
    }


def run_audit(*, as_of: date) -> dict:
    session = requests.Session()
    session.headers.update({"User-Agent": "football-ai-research-historical-audit/1.0"})
    configs: Iterable = (
        TURKEY_SUPER_LIG_RUNTIME_CONFIG,
        PRIMEIRA_LIGA_RUNTIME_CONFIG,
    )
    results = [audit_league(config, as_of=as_of, session=session) for config in configs]
    return {
        "audit": "TURKEY_PORTUGAL_HISTORICAL_FOUNDATION_V1",
        "research_only": True,
        "provider": "FOOTBALL_DATA_CSV",
        "odds_api_requests": 0,
        "supabase_writes": 0,
        "production_model_operations": 0,
        "as_of": as_of.isoformat(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "leagues": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    as_of = date.fromisoformat(args.as_of)
    report = run_audit(as_of=as_of)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
