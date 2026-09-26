"""Zero-cost point-in-time CORNERS10 replay feasibility audit for V2B.

This module does not read V2B odds or compute any direction statistic.
It checks fixture identity and prior top-flight corner-history coverage only.
"""
from __future__ import annotations

import argparse
import json
import math
import unicodedata
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from audit_multi_market_corner_outcomes import configured_csv_contract
from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
from league_runtime_config import EPL_RUNTIME_CONFIG, LA_LIGA_RUNTIME_CONFIG
from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from team_names import normalize_team_name


EXPERIMENT_ID = "V2B_CORNERS10_REPLAY_FEASIBILITY"
EXPECTED_LOCK_SELECTION_SHA256 = (
    "sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73"
)
EXPECTED_LOCK_FIXTURE_METADATA_SHA256 = (
    "sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb"
)
EXPECTED_LOCKED_FIXTURES = 43
PREVIOUS_SEASON = "2025-2026"
CURRENT_SEASON = "2026-2027"
FOOTBALL_DATA_URL = (
    "https://www.football-data.co.uk/mmz4281/{season_code}/{competition_code}.csv"
)

CONFIGS = {
    "EPL": EPL_RUNTIME_CONFIG,
    "LA_LIGA": LA_LIGA_RUNTIME_CONFIG,
    "SERIE_A": SERIE_A_RUNTIME_CONFIG,
    "BUNDESLIGA": BUNDESLIGA_RUNTIME_CONFIG,
    "LIGUE_1": LIGUE1_RUNTIME_CONFIG,
}

# Provider -> repository/Football-Data identity plumbing only.
# These aliases are frozen before this audit reads any direction result.
LOCK_IDENTITY_ALIASES = {
    "EPL": {
        "Man Utd": "Man United",
        "Nottm Forest": "Nott'm Forest",
    },
    "LA_LIGA": {
        "Athletic Club": "Ath Bilbao",
        "Atletico Madrid": "Atl. Madrid",
        "CD Alaves": "Alaves",
        "Deportivo A Coruna": "La Coruna",
        "Racing Santander": "Santander",
    },
    "SERIE_A": {},
    "BUNDESLIGA": {
        "Bayer Leverkusen": "Leverkusen",
        "Borussia Dortmund": "Dortmund",
        "Borussia M'gladbach": "M'gladbach",
        "Cologne": "FC Koln",
        "Eintracht Frankfurt": "Ein Frankfurt",
        "SC Freiburg": "Freiburg",
        "Schalke": "Schalke 04",
        "TSG Hoffenheim": "Hoffenheim",
        "VfB Stuttgart": "Stuttgart",
    },
    "LIGUE_1": {
        "PSG": "Paris SG",
    },
}


def _identity_key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch.lower() for ch in text if ch.isalnum())


def _canonical_source_team(value: Any, config) -> str:
    team = str(value).strip()
    team = str(config.aliases.get(team, team))
    return str(normalize_team_name(team)).strip()


def _canonical_lock_team(value: Any, league: str) -> str:
    config = CONFIGS[league]
    team = str(value).strip()
    team = LOCK_IDENTITY_ALIASES.get(league, {}).get(team, team)
    team = str(config.aliases.get(team, team))
    return str(normalize_team_name(team)).strip()


def _previous_contract(config) -> dict[str, str]:
    if config.historical_source.provider != "FOOTBALL_DATA_CSV":
        raise RuntimeError(
            f"{config.identity.identifier}: previous-season Football-Data CSV unavailable"
        )
    matches = [
        code
        for code, season in config.historical_source.season_codes.items()
        if season == PREVIOUS_SEASON
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"{config.identity.identifier}: expected exactly one {PREVIOUS_SEASON} code"
        )
    return {
        "competition_code": config.historical_source.competition_code,
        "season_code": matches[0],
    }


def _current_contract(config) -> dict[str, str]:
    contract = configured_csv_contract(config)
    if contract is None:
        raise RuntimeError(
            f"{config.identity.identifier}: current Football-Data corner contract unavailable"
        )
    return {
        "competition_code": str(contract["competition_code"]),
        "season_code": str(contract["season_code"]),
    }


def _fetch_csv(session: requests.Session, contract: dict[str, str]) -> pd.DataFrame:
    url = FOOTBALL_DATA_URL.format(**contract)
    response = session.get(url, timeout=30)
    response.raise_for_status()
    if not response.text.strip():
        raise ValueError(f"empty Football-Data CSV response: {url}")
    frame = pd.read_csv(StringIO(response.text))
    frame.attrs["source_url"] = url
    return frame


def _prepare_source_frame(
    frame: pd.DataFrame,
    *,
    league: str,
    season: str,
) -> pd.DataFrame:
    required = {"Date", "HomeTeam", "AwayTeam", "FTR", "FTHG", "FTAG", "HC", "AC"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{league} {season}: missing columns {sorted(missing)}")

    out = frame.copy()
    out["match_date"] = pd.to_datetime(out["Date"], dayfirst=True, errors="coerce")
    finished = out["FTR"].astype(str).isin(["H", "D", "A"])
    hc = pd.to_numeric(out["HC"], errors="coerce")
    ac = pd.to_numeric(out["AC"], errors="coerce")
    corner_valid = (
        hc.notna()
        & ac.notna()
        & hc.ge(0)
        & ac.ge(0)
        & hc.map(lambda x: bool(pd.notna(x) and math.isfinite(float(x)) and float(x).is_integer()))
        & ac.map(lambda x: bool(pd.notna(x) and math.isfinite(float(x)) and float(x).is_integer()))
    )
    out = out.loc[finished & corner_valid & out["match_date"].notna()].copy()
    config = CONFIGS[league]
    out["home_canonical"] = out["HomeTeam"].map(
        lambda x: _canonical_source_team(x, config)
    )
    out["away_canonical"] = out["AwayTeam"].map(
        lambda x: _canonical_source_team(x, config)
    )
    out["home_key"] = out["home_canonical"].map(_identity_key)
    out["away_key"] = out["away_canonical"].map(_identity_key)
    out["HC"] = pd.to_numeric(out["HC"], errors="raise").astype(int)
    out["AC"] = pd.to_numeric(out["AC"], errors="raise").astype(int)
    out["season"] = season
    out["league"] = league
    return out[
        [
            "league",
            "season",
            "match_date",
            "HomeTeam",
            "AwayTeam",
            "home_canonical",
            "away_canonical",
            "home_key",
            "away_key",
            "HC",
            "AC",
        ]
    ].sort_values(["match_date", "home_key", "away_key"], kind="stable")


def _validate_lock(lock: dict[str, Any]) -> list[dict[str, Any]]:
    if lock.get("lock_status") != "IMMUTABLE_COHORT_LOCKED":
        raise RuntimeError("input is not immutable V2B cohort lock")
    if lock.get("selection_sha256") != EXPECTED_LOCK_SELECTION_SHA256:
        raise RuntimeError("unexpected V2B selection_sha256")
    if lock.get("fixture_metadata_sha256") != EXPECTED_LOCK_FIXTURE_METADATA_SHA256:
        raise RuntimeError("unexpected V2B fixture_metadata_sha256")
    rows = lock.get("selected_fixture_metadata")
    if not isinstance(rows, list) or len(rows) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("unexpected V2B selected fixture metadata")
    ids = [str(row.get("fixture_id") or "") for row in rows]
    if len(ids) != len(set(ids)) or any(not x for x in ids):
        raise RuntimeError("invalid locked fixture IDs")
    return rows


def _team_prior_count(history: pd.DataFrame, *, team_key: str, target_date) -> int:
    prior = history[history["match_date"] < target_date]
    mask = (prior["home_key"] == team_key) | (prior["away_key"] == team_key)
    return int(mask.sum())


def audit_from_frames(
    lock: dict[str, Any],
    frames: dict[tuple[str, str], pd.DataFrame],
) -> dict[str, Any]:
    targets = _validate_lock(lock)
    histories: dict[str, pd.DataFrame] = {}
    source_summary: dict[str, Any] = {}

    for league in CONFIGS:
        previous = _prepare_source_frame(
            frames[(league, PREVIOUS_SEASON)],
            league=league,
            season=PREVIOUS_SEASON,
        )
        current = _prepare_source_frame(
            frames[(league, CURRENT_SEASON)],
            league=league,
            season=CURRENT_SEASON,
        )
        history = pd.concat([previous, current], ignore_index=True).sort_values(
            ["match_date", "home_key", "away_key"], kind="stable"
        )
        histories[league] = history
        source_summary[league] = {
            "previous_valid_corner_rows": int(len(previous)),
            "current_valid_corner_rows": int(len(current)),
        }

    rows: list[dict[str, Any]] = []
    for target in targets:
        league = str(target["league"])
        if league not in histories:
            raise RuntimeError(f"unexpected locked league {league}")
        target_date = pd.Timestamp(target["kickoff_utc"]).tz_convert(None).normalize()
        home_canonical = _canonical_lock_team(target["home_team"], league)
        away_canonical = _canonical_lock_team(target["away_team"], league)
        home_key = _identity_key(home_canonical)
        away_key = _identity_key(away_canonical)
        history = histories[league]

        same_date = history[history["match_date"].dt.normalize() == target_date]
        matched = same_date[
            (same_date["home_key"] == home_key)
            & (same_date["away_key"] == away_key)
        ]

        if len(matched) == 1:
            match_status = "MATCHED"
            fail_reason = None
            home_prior = _team_prior_count(
                history, team_key=home_key, target_date=target_date
            )
            away_prior = _team_prior_count(
                history, team_key=away_key, target_date=target_date
            )
            corners10_feasible = home_prior >= 10 and away_prior >= 10
            if not corners10_feasible:
                fail_reason = "INSUFFICIENT_PRIOR_TOP_FLIGHT_HISTORY"
        elif len(matched) == 0:
            match_status = "UNMATCHED"
            fail_reason = "SOURCE_FIXTURE_NOT_FOUND"
            home_prior = _team_prior_count(
                history, team_key=home_key, target_date=target_date
            )
            away_prior = _team_prior_count(
                history, team_key=away_key, target_date=target_date
            )
            corners10_feasible = False
        else:
            match_status = "AMBIGUOUS"
            fail_reason = "MULTIPLE_SOURCE_FIXTURE_MATCHES"
            home_prior = _team_prior_count(
                history, team_key=home_key, target_date=target_date
            )
            away_prior = _team_prior_count(
                history, team_key=away_key, target_date=target_date
            )
            corners10_feasible = False

        rows.append(
            {
                "fixture_id": str(target["fixture_id"]),
                "league": league,
                "kickoff_date": target_date.strftime("%Y-%m-%d"),
                "locked_home_team": str(target["home_team"]),
                "locked_away_team": str(target["away_team"]),
                "canonical_home_team": home_canonical,
                "canonical_away_team": away_canonical,
                "source_identity_status": match_status,
                "home_prior_top_flight_corner_matches": home_prior,
                "away_prior_top_flight_corner_matches": away_prior,
                "both_teams_have_corners10": bool(corners10_feasible),
                "fail_reason": fail_reason,
            }
        )

    row_frame = pd.DataFrame(rows)
    matched_count = int((row_frame["source_identity_status"] == "MATCHED").sum())
    feasible_count = int(row_frame["both_teams_have_corners10"].sum())
    by_league = {}
    for league in CONFIGS:
        g = row_frame[row_frame["league"] == league]
        by_league[league] = {
            "locked_fixtures": int(len(g)),
            "matched_fixtures": int((g["source_identity_status"] == "MATCHED").sum()),
            "corners10_feasible_fixtures": int(g["both_teams_have_corners10"].sum()),
        }

    if matched_count < EXPECTED_LOCKED_FIXTURES:
        status = "IDENTITY_OR_SOURCE_GAPS"
    elif feasible_count == EXPECTED_LOCKED_FIXTURES:
        status = "FULL_43_REPLAY_FEASIBLE"
    else:
        status = "PARTIAL_REPLAY_FEASIBLE"

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "source_feasibility_audit": True,
        "direction_test_performed": False,
        "v2b_odds_read": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "locked_fixture_count": EXPECTED_LOCKED_FIXTURES,
        "matched_fixture_count": matched_count,
        "corners10_feasible_fixture_count": feasible_count,
        "status": status,
        "source_summary": source_summary,
        "by_league": by_league,
        "rows": rows,
    }


def run_live_audit(
    lock: dict[str, Any],
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    owned = session is None
    if session is None:
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "football-ai-v2b-corners10-feasibility/1.0"}
        )
    frames: dict[tuple[str, str], pd.DataFrame] = {}
    try:
        for league, config in CONFIGS.items():
            frames[(league, PREVIOUS_SEASON)] = _fetch_csv(
                session, _previous_contract(config)
            )
            frames[(league, CURRENT_SEASON)] = _fetch_csv(
                session, _current_contract(config)
            )
    finally:
        if owned:
            session.close()
    return audit_from_frames(lock, frames)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    lock = json.loads(args.lock_manifest.read_text(encoding="utf-8"))
    report = run_live_audit(lock)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
