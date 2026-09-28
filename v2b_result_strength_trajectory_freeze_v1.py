"""Freeze point-in-time result-strength trajectory features for the V2B cohort.

Research only. This module consumes only the immutable V2B fixture lock, the
previous zero-cost feasibility artifact, and public Football-Data match results.
It does not read V2B market odds or direction outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from historical_team_strength_trajectory import add_team_strength_trajectory
from v2b_corners10_replay_feasibility import (
    CONFIGS,
    CURRENT_SEASON,
    _canonical_lock_team,
    _canonical_source_team,
    _current_contract,
    _fetch_csv,
    _validate_lock,
)

EXPERIMENT_ID = "V2B_RESULT_STRENGTH_TRAJECTORY_FREEZE_V1"
PRIMARY_MAPPING_ID = "JOINT_PERFORMANCE_RESIDUAL_5_SIGN_V1"
EXPECTED_FEASIBILITY_EXPERIMENT = "V2B_CORNERS10_REPLAY_FEASIBILITY"
EXPECTED_LOCKED_FIXTURES = 43
EXPECTED_ELIGIBLE_FIXTURES = 34
EXPECTED_BY_LEAGUE = {
    "EPL": 6,
    "LA_LIGA": 9,
    "SERIE_A": 7,
    "BUNDESLIGA": 6,
    "LIGUE_1": 6,
}
FOOTBALL_DATA_URL = (
    "https://www.football-data.co.uk/mmz4281/{season_code}/{competition_code}.csv"
)


def stage_b_mapping(
    home_performance_residual_5: float,
    away_performance_residual_5: float,
) -> tuple[float, str]:
    """Frozen Stage-B mapping with no fitted weight or threshold."""
    score = float(home_performance_residual_5) + float(away_performance_residual_5)
    if score > 0.0:
        return score, "UP"
    if score < 0.0:
        return score, "DOWN"
    return score, "NO_CALL"


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validate_feasibility(report: dict[str, Any]) -> list[dict[str, Any]]:
    if report.get("experiment_id") != EXPECTED_FEASIBILITY_EXPERIMENT:
        raise RuntimeError("unexpected feasibility experiment")
    if report.get("research_only") is not True:
        raise RuntimeError("feasibility report is not research-only")
    if report.get("direction_test_performed") is not False:
        raise RuntimeError("feasibility report unexpectedly contains direction testing")
    if report.get("v2b_odds_read") is not False:
        raise RuntimeError("feasibility report unexpectedly read V2B odds")
    if int(report.get("locked_fixture_count", -1)) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("unexpected feasibility locked fixture count")

    rows = report.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("unexpected feasibility rows")
    fixture_ids = [str(row.get("fixture_id") or "") for row in rows]
    if any(not fixture_id for fixture_id in fixture_ids):
        raise RuntimeError("missing feasibility fixture id")
    if len(fixture_ids) != len(set(fixture_ids)):
        raise RuntimeError("duplicate feasibility fixture id")

    eligible = [
        row
        for row in rows
        if row.get("source_identity_status") == "MATCHED"
        and int(row.get("home_prior_top_flight_corner_matches", -1)) >= 5
        and int(row.get("away_prior_top_flight_corner_matches", -1)) >= 5
    ]
    if len(eligible) != EXPECTED_ELIGIBLE_FIXTURES:
        raise RuntimeError(
            f"expected {EXPECTED_ELIGIBLE_FIXTURES} five-match eligible fixtures, "
            f"got {len(eligible)}"
        )

    by_league = {
        league: sum(1 for row in eligible if row.get("league") == league)
        for league in EXPECTED_BY_LEAGUE
    }
    if by_league != EXPECTED_BY_LEAGUE:
        raise RuntimeError(f"unexpected five-match eligibility by league: {by_league}")
    return eligible


def _prepare_results_frame(
    frame: pd.DataFrame,
    *,
    league: str,
    season: str,
) -> pd.DataFrame:
    required = {"Date", "HomeTeam", "AwayTeam", "FTR"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{league} {season}: missing result columns {sorted(missing)}")

    out = frame.copy()
    out["match_date"] = pd.to_datetime(out["Date"], dayfirst=True, errors="coerce")
    out = out[
        out["FTR"].astype(str).isin(["H", "D", "A"])
        & out["match_date"].notna()
        & out["HomeTeam"].notna()
        & out["AwayTeam"].notna()
    ].copy()

    config = CONFIGS[league]
    out["home_team"] = out["HomeTeam"].map(
        lambda value: _canonical_source_team(value, config)
    )
    out["away_team"] = out["AwayTeam"].map(
        lambda value: _canonical_source_team(value, config)
    )
    out["league"] = league
    out["season"] = season
    out["result"] = out["FTR"].astype(str)
    return out[
        ["league", "season", "match_date", "home_team", "away_team", "result"]
    ].sort_values(["match_date", "home_team", "away_team"], kind="stable")


def _historical_contracts(config) -> list[tuple[str, dict[str, str]]]:
    if config.historical_source.provider != "FOOTBALL_DATA_CSV":
        raise RuntimeError(
            f"{config.identity.identifier}: historical Football-Data CSV unavailable"
        )
    contracts = [
        (
            season,
            {
                "competition_code": config.historical_source.competition_code,
                "season_code": season_code,
            },
        )
        for season_code, season in config.historical_source.season_codes.items()
    ]
    contracts.sort(key=lambda item: item[0])
    return contracts


def _fetch_history(
    *,
    session: requests.Session,
) -> dict[str, pd.DataFrame]:
    histories: dict[str, pd.DataFrame] = {}
    for league, config in CONFIGS.items():
        frames: list[pd.DataFrame] = []
        for season, contract in _historical_contracts(config):
            source = _fetch_csv(session, contract)
            frames.append(
                _prepare_results_frame(source, league=league, season=season)
            )
        current_contract = _current_contract(config)
        current_source = _fetch_csv(session, current_contract)
        frames.append(
            _prepare_results_frame(
                current_source,
                league=league,
                season=CURRENT_SEASON,
            )
        )
        history = pd.concat(frames, ignore_index=True).sort_values(
            ["match_date", "home_team", "away_team"], kind="stable"
        )
        histories[league] = add_team_strength_trajectory(history)
    return histories


def freeze_from_frames(
    lock: dict[str, Any],
    feasibility: dict[str, Any],
    histories: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    locked = _validate_lock(lock)
    eligible = _validate_feasibility(feasibility)
    locked_by_id = {str(row["fixture_id"]): row for row in locked}

    selected_identity: list[dict[str, str]] = []
    rows: list[dict[str, Any]] = []
    for eligibility in eligible:
        fixture_id = str(eligibility["fixture_id"])
        target = locked_by_id.get(fixture_id)
        if target is None:
            raise RuntimeError(f"eligible fixture missing from V2B lock: {fixture_id}")

        league = str(target["league"])
        history = histories.get(league)
        if history is None:
            raise RuntimeError(f"missing trajectory history for league {league}")

        target_date = pd.Timestamp(target["kickoff_utc"]).tz_convert(None).normalize()
        home_team = _canonical_lock_team(target["home_team"], league)
        away_team = _canonical_lock_team(target["away_team"], league)

        matched = history[
            (history["match_date"].dt.normalize() == target_date)
            & (history["home_team"] == home_team)
            & (history["away_team"] == away_team)
        ]
        if len(matched) != 1:
            raise RuntimeError(
                f"expected one trajectory source row for {fixture_id}, got {len(matched)}"
            )
        source = matched.iloc[0]

        required_features = (
            "home_elo_level",
            "away_elo_level",
            "home_elo_delta_5",
            "away_elo_delta_5",
            "home_performance_residual_5",
            "away_performance_residual_5",
        )
        if any(pd.isna(source[name]) for name in required_features):
            raise RuntimeError(f"missing frozen trajectory feature for {fixture_id}")

        score, call = stage_b_mapping(
            float(source["home_performance_residual_5"]),
            float(source["away_performance_residual_5"]),
        )
        identity = {
            "fixture_id": fixture_id,
            "league": league,
            "kickoff_utc": str(target["kickoff_utc"]),
            "home_team": str(target["home_team"]),
            "away_team": str(target["away_team"]),
        }
        selected_identity.append(identity)
        rows.append(
            {
                **identity,
                "canonical_home_team": home_team,
                "canonical_away_team": away_team,
                "recent_prior_top_flight_matches_home": int(
                    eligibility["home_prior_top_flight_corner_matches"]
                ),
                "recent_prior_top_flight_matches_away": int(
                    eligibility["away_prior_top_flight_corner_matches"]
                ),
                "home_elo_level": float(source["home_elo_level"]),
                "away_elo_level": float(source["away_elo_level"]),
                "home_elo_delta_5": float(source["home_elo_delta_5"]),
                "away_elo_delta_5": float(source["away_elo_delta_5"]),
                "home_performance_residual_5": float(
                    source["home_performance_residual_5"]
                ),
                "away_performance_residual_5": float(
                    source["away_performance_residual_5"]
                ),
                "stage_b_score": score,
                "stage_b_call": call,
            }
        )

    if len(rows) != EXPECTED_ELIGIBLE_FIXTURES:
        raise RuntimeError("trajectory freeze row count changed")

    by_league = {
        league: sum(1 for row in rows if row["league"] == league)
        for league in EXPECTED_BY_LEAGUE
    }
    if by_league != EXPECTED_BY_LEAGUE:
        raise RuntimeError(f"trajectory freeze league counts changed: {by_league}")

    calls = {
        label: sum(1 for row in rows if row["stage_b_call"] == label)
        for label in ("UP", "DOWN", "NO_CALL")
    }
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "feature_freeze_only": True,
        "primary_mapping_id": PRIMARY_MAPPING_ID,
        "mapping_formula": (
            "stage_b_score = home_performance_residual_5 + "
            "away_performance_residual_5; score>0=>UP; score<0=>DOWN; "
            "score==0=>NO_CALL"
        ),
        "eligibility_rule": (
            "source_identity_status=MATCHED and both recent prior top-flight "
            "match counts >=5 in immutable V2B feasibility artifact"
        ),
        "locked_fixture_count": EXPECTED_LOCKED_FIXTURES,
        "eligible_fixture_count": len(rows),
        "eligible_by_league": by_league,
        "stage_b_calls": calls,
        "eligible_fixture_sha256": _sha256_json(selected_identity),
        "direction_test_performed": False,
        "v2b_odds_read": False,
        "opening_lambda_read": False,
        "centre_delta_read": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "rows": rows,
    }


def run_live_freeze(
    lock: dict[str, Any],
    feasibility: dict[str, Any],
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    owned = session is None
    if session is None:
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "football-ai-v2b-result-trajectory-freeze/1.0"}
        )
    try:
        histories = _fetch_history(session=session)
    finally:
        if owned:
            session.close()
    return freeze_from_frames(lock, feasibility, histories)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock-manifest", type=Path, required=True)
    parser.add_argument("--feasibility-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    lock = json.loads(args.lock_manifest.read_text(encoding="utf-8"))
    feasibility = json.loads(args.feasibility_report.read_text(encoding="utf-8"))
    report = run_live_freeze(lock, feasibility)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
