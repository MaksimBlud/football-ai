"""Zero-cost current-season corner outcome source audit for Multi-Market V2.

This is an infrastructure/source-feasibility audit. It reads only explicitly
configured Football-Data CSV contracts already present in repository runtime
configuration. It never guesses a season code or competition code.

No The Odds API requests. No Supabase operations. No model operations.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG
from league_runtime_config import EPL_RUNTIME_CONFIG, LA_LIGA_RUNTIME_CONFIG, RPL_RUNTIME_CONFIG
from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


SEASON = "2026-2027"
URL = "https://www.football-data.co.uk/mmz4281/{season_code}/{competition_code}.csv"
CONFIGS = (
    EPL_RUNTIME_CONFIG,
    LA_LIGA_RUNTIME_CONFIG,
    SERIE_A_RUNTIME_CONFIG,
    BUNDESLIGA_RUNTIME_CONFIG,
    LIGUE1_RUNTIME_CONFIG,
    EREDIVISIE_RUNTIME_CONFIG,
    RPL_RUNTIME_CONFIG,
    TURKEY_SUPER_LIG_RUNTIME_CONFIG,
    PRIMEIRA_LIGA_RUNTIME_CONFIG,
)


def configured_csv_contract(config) -> dict | None:
    """Resolve only a repository-configured Football-Data CSV contract."""
    finished = config.finished_results_source
    if (
        finished.provider == "FOOTBALL_DATA_CSV"
        and finished.season == SEASON
        and finished.competition_code
        and finished.season_code
    ):
        return {
            "contract_source": "finished_results_source",
            "competition_code": finished.competition_code,
            "season_code": finished.season_code,
        }

    historical = config.historical_source
    if historical.provider != "FOOTBALL_DATA_CSV":
        return None
    matching_codes = [
        code
        for code, configured_season in historical.season_codes.items()
        if configured_season == SEASON
    ]
    if len(matching_codes) == 1:
        return {
            "contract_source": "historical_source_current_season_mapping",
            "competition_code": historical.competition_code,
            "season_code": matching_codes[0],
        }
    if len(matching_codes) > 1:
        raise ValueError(
            f"{config.identity.identifier}: multiple configured season codes for {SEASON}"
        )
    return None


def _fetch_csv(session: requests.Session, url: str) -> pd.DataFrame:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    if not response.text.strip():
        raise ValueError("empty Football-Data CSV response")
    return pd.read_csv(StringIO(response.text))


def _valid_finished_mask(frame: pd.DataFrame) -> pd.Series:
    if not {"FTR", "FTHG", "FTAG"}.issubset(frame.columns):
        return pd.Series(False, index=frame.index, dtype=bool)
    result = frame["FTR"].astype(str).isin(["H", "D", "A"])
    home_goals = pd.to_numeric(frame["FTHG"], errors="coerce")
    away_goals = pd.to_numeric(frame["FTAG"], errors="coerce")
    return result & home_goals.notna() & away_goals.notna()


def _corner_valid(series: pd.Series) -> tuple[pd.Series, dict]:
    numeric = pd.to_numeric(series, errors="coerce")
    finite = numeric.map(lambda value: bool(pd.notna(value) and math.isfinite(float(value))))
    nonnegative = finite & numeric.ge(0)
    integer = nonnegative & numeric.map(
        lambda value: bool(pd.notna(value) and float(value).is_integer())
    )
    diagnostics = {
        "missing_or_non_numeric": int((~finite).sum()),
        "negative": int((finite & numeric.lt(0)).sum()),
        "non_integer": int((nonnegative & ~integer).sum()),
    }
    return integer, diagnostics


def _canonical_team(value, config) -> str:
    team = str(value).strip()
    return str(config.aliases.get(team, team))


def audit_frame(config, frame: pd.DataFrame, contract: dict, url: str) -> dict:
    league = config.identity.identifier
    required_identity = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
    missing_identity = sorted(required_identity - set(frame.columns))
    finished_mask = _valid_finished_mask(frame)
    finished = frame.loc[finished_mask].copy()
    has_hc = "HC" in frame.columns
    has_ac = "AC" in frame.columns

    record = {
        "league": league,
        "status": "AUDITED",
        "season": SEASON,
        "contract_source": contract["contract_source"],
        "competition_code": contract["competition_code"],
        "season_code": contract["season_code"],
        "url": url,
        "rows": int(len(frame)),
        "finished_rows": int(finished_mask.sum()),
        "identity_columns_complete": not missing_identity,
        "missing_identity_columns": missing_identity,
        "hc_present": has_hc,
        "ac_present": has_ac,
        "corner_columns_present": has_hc and has_ac,
        "valid_corner_rows": 0,
        "corner_coverage_finished": 0.0,
        "home_corner_diagnostics_finished": None,
        "away_corner_diagnostics_finished": None,
        "raw_team_count_finished": 0,
        "canonical_team_count_finished": 0,
        "aliases_applied_finished": 0,
        "canonical_identity_duplicates_finished": 0,
    }

    if not missing_identity and not finished.empty:
        raw_teams = set(finished["HomeTeam"].astype(str).str.strip()) | set(
            finished["AwayTeam"].astype(str).str.strip()
        )
        canonical_teams = {_canonical_team(team, config) for team in raw_teams}
        record["raw_team_count_finished"] = len(raw_teams)
        record["canonical_team_count_finished"] = len(canonical_teams)
        record["aliases_applied_finished"] = sum(
            1 for team in raw_teams if _canonical_team(team, config) != team
        )

        identities = pd.DataFrame(
            {
                "date": finished["Date"].astype(str).str.strip(),
                "home": finished["HomeTeam"].map(lambda value: _canonical_team(value, config)),
                "away": finished["AwayTeam"].map(lambda value: _canonical_team(value, config)),
            }
        )
        record["canonical_identity_duplicates_finished"] = int(
            identities.duplicated(subset=["date", "home", "away"], keep=False).sum()
        )

    if has_hc and has_ac and not finished.empty:
        home_valid, home_diag = _corner_valid(finished["HC"])
        away_valid, away_diag = _corner_valid(finished["AC"])
        valid = home_valid & away_valid
        record["valid_corner_rows"] = int(valid.sum())
        record["corner_coverage_finished"] = float(valid.mean())
        record["home_corner_diagnostics_finished"] = home_diag
        record["away_corner_diagnostics_finished"] = away_diag

    if missing_identity:
        record["status"] = "INVALID_SOURCE_SCHEMA"
    elif not (has_hc and has_ac):
        record["status"] = "CORNER_COLUMNS_MISSING"
    elif record["finished_rows"] == 0:
        record["status"] = "NO_FINISHED_ROWS_YET"
    elif record["valid_corner_rows"] == record["finished_rows"]:
        record["status"] = "CORNER_OUTCOME_COVERAGE_COMPLETE"
    else:
        record["status"] = "CORNER_OUTCOME_COVERAGE_PARTIAL"
    return record


def audit_league(config, *, session: requests.Session) -> dict:
    contract = configured_csv_contract(config)
    if contract is None:
        return {
            "league": config.identity.identifier,
            "status": "SOURCE_NOT_CONFIGURED",
            "season": SEASON,
            "reason": "no repository-configured 2026-2027 FOOTBALL_DATA_CSV contract",
        }

    url = URL.format(
        season_code=contract["season_code"],
        competition_code=contract["competition_code"],
    )
    try:
        frame = _fetch_csv(session, url)
    except Exception as exc:
        return {
            "league": config.identity.identifier,
            "status": "SOURCE_FETCH_FAILED",
            "season": SEASON,
            "contract_source": contract["contract_source"],
            "competition_code": contract["competition_code"],
            "season_code": contract["season_code"],
            "url": url,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return audit_frame(config, frame, contract, url)


def run_audit(*, session: requests.Session | None = None) -> dict:
    owned_session = session is None
    if session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": "football-ai-multi-market-corner-audit/1.0"})
    try:
        leagues = [audit_league(config, session=session) for config in CONFIGS]
    finally:
        if owned_session:
            session.close()

    configured = [item for item in leagues if item["status"] != "SOURCE_NOT_CONFIGURED"]
    complete = [
        item for item in leagues if item["status"] == "CORNER_OUTCOME_COVERAGE_COMPLETE"
    ]
    return {
        "audit": "MULTI_MARKET_V2_CORNER_OUTCOME_SOURCE_AUDIT_V1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "season": SEASON,
        "research_only": True,
        "source_feasibility_audit": True,
        "outcomes_read": True,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "configured_csv_leagues": len(configured),
        "complete_corner_coverage_leagues": len(complete),
        "leagues": leagues,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_audit()
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
