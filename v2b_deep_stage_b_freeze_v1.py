"""Freeze a territorial-depth Stage-B mapping for the V2B tactical cohort.

Research-only. Uses the immutable Understat tactical-pressure feasibility artifact
and a completed-2025/26 pooled top-five deep/deep_allowed baseline. It never
reads V2B market direction or opening-market state.
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

from v2b_understat_tactical_pressure_feasibility_v1 import (
    EXPERIMENT_ID as FEASIBILITY_EXPERIMENT_ID,
    prepare_tactical_histories,
)
from v2b_true_xg_replay_feasibility_v1 import LEAGUE_SLUGS, fetch_understat_league

EXPERIMENT_ID = "V2B_DEEP_STAGE_B_FREEZE_V1"
PRIMARY_MAPPING_ID = "POOLED_2025_DEEP_ENVIRONMENT_SIGN_V1"
EXPECTED_LOCKED = 43
EXPECTED_ELIGIBLE = 34
EXPECTED_BY_LEAGUE = {
    "EPL": 6,
    "LA_LIGA": 9,
    "SERIE_A": 7,
    "BUNDESLIGA": 6,
    "LIGUE_1": 6,
}
BASELINE_SEASON = 2025


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validate_feasibility(payload: dict[str, Any]) -> pd.DataFrame:
    if payload.get("experiment_id") != FEASIBILITY_EXPERIMENT_ID:
        raise RuntimeError("unexpected tactical feasibility experiment")
    if payload.get("status") != "PARTIAL_TACTICAL5_FEASIBLE":
        raise RuntimeError("unexpected tactical feasibility status")
    if payload.get("research_only") is not True:
        raise RuntimeError("tactical feasibility is not research-only")
    if int(payload.get("locked_fixture_count", -1)) != EXPECTED_LOCKED:
        raise RuntimeError("unexpected locked count")
    if int(payload.get("identity_matched_fixture_count", -1)) != EXPECTED_LOCKED:
        raise RuntimeError("identity coverage changed")
    if int(payload.get("tactical5_feasible_fixture_count", -1)) != EXPECTED_ELIGIBLE:
        raise RuntimeError("tactical feasible count changed")
    for field in (
        "market_rows_read",
        "v2b_odds_read",
        "opening_lambda_read",
        "fair_centre_read",
        "centre_delta_read",
        "direction_test_performed",
    ):
        if payload.get(field) is not False:
            raise RuntimeError(f"feasibility safety flag changed: {field}")

    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_LOCKED:
        raise RuntimeError("unexpected feasibility rows")
    frame = pd.DataFrame(rows)
    required = {
        "fixture_id", "league", "kickoff_utc", "home_team", "away_team",
        "identity_status", "both_teams_have_tactical5",
        "home_deep_last5", "home_deep_allowed_last5",
        "away_deep_last5", "away_deep_allowed_last5",
    }
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"missing tactical columns: {sorted(missing)}")
    frame["fixture_id"] = frame["fixture_id"].astype(str)
    if frame["fixture_id"].duplicated().any():
        raise RuntimeError("duplicate fixture IDs")

    eligible = frame[
        (frame["identity_status"] == "MATCHED")
        & frame["both_teams_have_tactical5"].astype(bool)
    ].copy()
    if len(eligible) != EXPECTED_ELIGIBLE:
        raise RuntimeError("eligible tactical cohort changed")
    by_league = {
        league: int((eligible["league"] == league).sum())
        for league in EXPECTED_BY_LEAGUE
    }
    if by_league != EXPECTED_BY_LEAGUE:
        raise RuntimeError(f"unexpected coverage by league: {by_league}")
    for col in (
        "home_deep_last5", "home_deep_allowed_last5",
        "away_deep_last5", "away_deep_allowed_last5",
    ):
        eligible[col] = pd.to_numeric(eligible[col], errors="coerce")
    if eligible[
        ["home_deep_last5","home_deep_allowed_last5",
         "away_deep_last5","away_deep_allowed_last5"]
    ].isna().any().any():
        raise RuntimeError("eligible tactical row has missing deep value")
    return eligible.reset_index(drop=True)


def _baseline_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    histories, titles, _ = prepare_tactical_histories([(BASELINE_SEASON, payload)])
    values: list[float] = []
    for frame in histories.values():
        if frame.empty:
            continue
        total = (
            pd.to_numeric(frame["deep"], errors="coerce")
            + pd.to_numeric(frame["deep_allowed"], errors="coerce")
        )
        values.extend(float(v) for v in total.dropna())
    if not values:
        raise RuntimeError("no previous-season deep environment rows")
    return {
        "source_team_count": len(titles),
        "team_match_rows": len(values),
        "mean_total_deep_environment": float(sum(values) / len(values)),
    }


def fetch_pooled_baseline(
    *, session: requests.Session | None = None
) -> dict[str, Any]:
    owned = session is None
    if session is None:
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "football-ai-v2b-deep-stageb-freeze/1.0"}
        )
    summaries: dict[str, dict[str, Any]] = {}
    try:
        for league in LEAGUE_SLUGS:
            payload = fetch_understat_league(
                session, league=league, season=BASELINE_SEASON
            )
            summaries[league] = _baseline_from_payload(payload)
    finally:
        if owned:
            session.close()
    rows = sum(item["team_match_rows"] for item in summaries.values())
    if rows <= 0:
        raise RuntimeError("empty pooled deep baseline")
    pooled = sum(
        item["mean_total_deep_environment"] * item["team_match_rows"]
        for item in summaries.values()
    ) / rows
    return {
        "source": "UNDERSTAT_PUBLIC_LEAGUE_HISTORY",
        "season_start": BASELINE_SEASON,
        "definition": (
            "pooled mean of deep+deep_allowed across valid 2025/26 team-match "
            "rows from EPL, La Liga, Serie A, Bundesliga and Ligue 1"
        ),
        "pooled_team_match_rows": int(rows),
        "pooled_total_deep_environment": float(pooled),
        "by_league": summaries,
    }


def stage_b_components(row: pd.Series, baseline: float) -> dict[str, Any]:
    expected_home = 0.5 * (
        float(row["home_deep_last5"]) + float(row["away_deep_allowed_last5"])
    )
    expected_away = 0.5 * (
        float(row["away_deep_last5"]) + float(row["home_deep_allowed_last5"])
    )
    joint = expected_home + expected_away
    score = joint - float(baseline)
    call = "UP" if score > 0 else "DOWN" if score < 0 else "NO_CALL"
    return {
        "expected_home_deep": expected_home,
        "expected_away_deep": expected_away,
        "joint_expected_deep": joint,
        "stage_b_score": score,
        "stage_b_call": call,
    }


def freeze(
    feasibility: dict[str, Any],
    baseline_summary: dict[str, Any],
) -> dict[str, Any]:
    eligible = _validate_feasibility(feasibility)
    baseline = float(baseline_summary["pooled_total_deep_environment"])
    if not pd.notna(baseline) or baseline <= 0:
        raise RuntimeError("invalid pooled deep baseline")

    identities: list[dict[str, str]] = []
    feature_identity: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for _, row in eligible.iterrows():
        identity = {
            "fixture_id": str(row["fixture_id"]),
            "league": str(row["league"]),
            "kickoff_utc": str(row["kickoff_utc"]),
            "home_team": str(row["home_team"]),
            "away_team": str(row["away_team"]),
        }
        components = stage_b_components(row, baseline)
        frozen = {
            **identity,
            "home_deep_last5": float(row["home_deep_last5"]),
            "home_deep_allowed_last5": float(row["home_deep_allowed_last5"]),
            "away_deep_last5": float(row["away_deep_last5"]),
            "away_deep_allowed_last5": float(row["away_deep_allowed_last5"]),
            **components,
        }
        identities.append(identity)
        feature_identity.append({**frozen, "pooled_baseline": baseline})
        rows.append(frozen)

    calls = {
        call: sum(1 for row in rows if row["stage_b_call"] == call)
        for call in ("UP", "DOWN", "NO_CALL")
    }
    by_league = {
        league: sum(1 for row in rows if row["league"] == league)
        for league in EXPECTED_BY_LEAGUE
    }
    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "feature_freeze_only": True,
        "primary_mapping_id": PRIMARY_MAPPING_ID,
        "primary_feature_family": "DEEP_AND_DEEP_ALLOWED_ONLY",
        "ppda_used_in_primary_mapping": False,
        "mapping_formula": (
            "expected_home_deep=0.5*(home_deep_last5+away_deep_allowed_last5); "
            "expected_away_deep=0.5*(away_deep_last5+home_deep_allowed_last5); "
            "joint_expected_deep=expected_home_deep+expected_away_deep; "
            "stage_b_score=joint_expected_deep-pooled_2025_26_top5_deep_baseline; "
            "score>0=>UP; score<0=>DOWN; score==0=>NO_CALL"
        ),
        "baseline_summary": baseline_summary,
        "locked_fixture_count": EXPECTED_LOCKED,
        "eligible_fixture_count": len(rows),
        "eligible_by_league": by_league,
        "stage_b_calls": calls,
        "eligible_fixture_sha256": _sha256_json(identities),
        "frozen_feature_sha256": _sha256_json(feature_identity),
        "market_rows_read": False,
        "v2b_odds_read": False,
        "opening_lambda_read": False,
        "fair_centre_read": False,
        "centre_delta_read": False,
        "direction_test_performed": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feasibility-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    feasibility = json.loads(args.feasibility_report.read_text(encoding="utf-8"))
    report = freeze(feasibility, fetch_pooled_baseline())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
