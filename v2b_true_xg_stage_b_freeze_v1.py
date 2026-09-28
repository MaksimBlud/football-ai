"""Freeze a true-npxG Stage-B mapping for the exact feasible V2B cohort.

Research-only. Consumes the immutable V2B true-xG feasibility artifact and a
public Understat 2025/26 top-five baseline. It does not read any V2B market
direction, opening line, FAIR_CENTRE, or centre_delta.
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

from v2b_true_xg_replay_feasibility_v1 import (
    EXPERIMENT_ID as FEASIBILITY_EXPERIMENT_ID,
    LEAGUE_SLUGS,
    fetch_understat_league,
    prepare_team_histories,
)

EXPERIMENT_ID = "V2B_TRUE_XG_STAGE_B_FREEZE_V1"
PRIMARY_MAPPING_ID = "POOLED_2025_NPXG_ENVIRONMENT_SIGN_V1"
EXPECTED_LOCKED_FIXTURES = 43
EXPECTED_ELIGIBLE_FIXTURES = 34
EXPECTED_BY_LEAGUE = {
    "EPL": 6,
    "LA_LIGA": 9,
    "SERIE_A": 7,
    "BUNDESLIGA": 6,
    "LIGUE_1": 6,
}
BASELINE_SEASON = 2025


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validate_feasibility(payload: dict[str, Any]) -> pd.DataFrame:
    if payload.get("experiment_id") != FEASIBILITY_EXPERIMENT_ID:
        raise RuntimeError("unexpected xG feasibility experiment")
    if payload.get("status") != "PARTIAL_XG5_FEASIBLE":
        raise RuntimeError("unexpected xG feasibility status")
    if payload.get("research_only") is not True:
        raise RuntimeError("xG feasibility is not research-only")
    if payload.get("source_feasibility_audit") is not True:
        raise RuntimeError("xG source is not a feasibility audit")
    if int(payload.get("locked_fixture_count", -1)) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("unexpected locked fixture count")
    if int(payload.get("identity_matched_fixture_count", -1)) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("xG fixture identity coverage changed")
    if int(payload.get("xg5_feasible_fixture_count", -1)) != EXPECTED_ELIGIBLE_FIXTURES:
        raise RuntimeError("unexpected xG5 feasible count")
    if payload.get("market_rows_read") is not False:
        raise RuntimeError("xG feasibility unexpectedly read market rows")
    if payload.get("v2b_odds_read") is not False:
        raise RuntimeError("xG feasibility unexpectedly read V2B odds")
    if payload.get("centre_delta_read") is not False:
        raise RuntimeError("xG feasibility unexpectedly read centre_delta")
    if payload.get("direction_test_performed") is not False:
        raise RuntimeError("xG feasibility unexpectedly tested direction")

    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("unexpected xG feasibility rows")
    frame = pd.DataFrame(rows)
    required = {
        "fixture_id",
        "league",
        "kickoff_utc",
        "home_team",
        "away_team",
        "identity_status",
        "both_teams_have_xg5",
        "home_npxg_last5",
        "home_npxga_last5",
        "away_npxg_last5",
        "away_npxga_last5",
    }
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"xG feasibility rows missing {sorted(missing)}")

    frame["fixture_id"] = frame["fixture_id"].astype(str)
    if frame["fixture_id"].duplicated().any():
        raise RuntimeError("duplicate xG feasibility fixture IDs")

    eligible = frame[
        (frame["identity_status"] == "MATCHED")
        & frame["both_teams_have_xg5"].astype(bool)
    ].copy()
    if len(eligible) != EXPECTED_ELIGIBLE_FIXTURES:
        raise RuntimeError("eligible xG5 cohort changed")

    by_league = {
        league: int((eligible["league"] == league).sum())
        for league in EXPECTED_BY_LEAGUE
    }
    if by_league != EXPECTED_BY_LEAGUE:
        raise RuntimeError(f"unexpected xG5 coverage by league: {by_league}")

    numeric = [
        "home_npxg_last5",
        "home_npxga_last5",
        "away_npxg_last5",
        "away_npxga_last5",
    ]
    for column in numeric:
        eligible[column] = pd.to_numeric(eligible[column], errors="coerce")
    if eligible[numeric].isna().any().any():
        raise RuntimeError("eligible xG5 row has missing npxG feature")
    return eligible.reset_index(drop=True)


def _league_baseline_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    histories, titles = prepare_team_histories([(BASELINE_SEASON, payload)])
    values: list[float] = []
    for frame in histories.values():
        if frame.empty:
            continue
        total = (
            pd.to_numeric(frame["npxg"], errors="coerce")
            + pd.to_numeric(frame["npxga"], errors="coerce")
        )
        values.extend(float(value) for value in total.dropna())
    if not values:
        raise RuntimeError("no valid previous-season npxG environment rows")
    return {
        "source_team_count": len(titles),
        "team_match_rows": len(values),
        "mean_total_npxg_environment": float(sum(values) / len(values)),
    }


def fetch_pooled_previous_season_baseline(
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    owned = session is None
    if session is None:
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "football-ai-v2b-true-xg-stageb-freeze/1.0"}
        )

    summaries: dict[str, dict[str, Any]] = {}
    try:
        for league in LEAGUE_SLUGS:
            payload = fetch_understat_league(
                session,
                league=league,
                season=BASELINE_SEASON,
            )
            summaries[league] = _league_baseline_from_payload(payload)
    finally:
        if owned:
            session.close()

    weighted_sum = sum(
        item["mean_total_npxg_environment"] * item["team_match_rows"]
        for item in summaries.values()
    )
    total_rows = sum(item["team_match_rows"] for item in summaries.values())
    if total_rows <= 0:
        raise RuntimeError("empty pooled previous-season baseline")
    pooled = float(weighted_sum / total_rows)
    return {
        "source": "UNDERSTAT_PUBLIC_LEAGUE_HISTORY",
        "season_start": BASELINE_SEASON,
        "definition": (
            "pooled mean of npxG+npxGA across valid 2025/26 team-match rows "
            "from EPL, La Liga, Serie A, Bundesliga and Ligue 1"
        ),
        "pooled_team_match_rows": int(total_rows),
        "pooled_total_npxg_environment": pooled,
        "by_league": summaries,
    }


def stage_b_components(row: pd.Series, baseline: float) -> dict[str, Any]:
    expected_home = 0.5 * (
        float(row["home_npxg_last5"]) + float(row["away_npxga_last5"])
    )
    expected_away = 0.5 * (
        float(row["away_npxg_last5"]) + float(row["home_npxga_last5"])
    )
    joint = expected_home + expected_away
    score = joint - float(baseline)
    if score > 0.0:
        call = "UP"
    elif score < 0.0:
        call = "DOWN"
    else:
        call = "NO_CALL"
    return {
        "expected_home_npxg": expected_home,
        "expected_away_npxg": expected_away,
        "joint_expected_npxg": joint,
        "stage_b_score": score,
        "stage_b_call": call,
    }


def freeze(
    feasibility: dict[str, Any],
    baseline_summary: dict[str, Any],
) -> dict[str, Any]:
    eligible = _validate_feasibility(feasibility)
    baseline = float(baseline_summary["pooled_total_npxg_environment"])
    if not pd.notna(baseline) or baseline <= 0:
        raise RuntimeError("invalid pooled previous-season npxG baseline")

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
            "understat_home_team": str(row.get("understat_home_team") or ""),
            "understat_away_team": str(row.get("understat_away_team") or ""),
            "home_npxg_last5": float(row["home_npxg_last5"]),
            "home_npxga_last5": float(row["home_npxga_last5"]),
            "away_npxg_last5": float(row["away_npxg_last5"]),
            "away_npxga_last5": float(row["away_npxga_last5"]),
            **components,
        }
        identities.append(identity)
        feature_identity.append(
            {
                **identity,
                "home_npxg_last5": frozen["home_npxg_last5"],
                "home_npxga_last5": frozen["home_npxga_last5"],
                "away_npxg_last5": frozen["away_npxg_last5"],
                "away_npxga_last5": frozen["away_npxga_last5"],
                "pooled_baseline": baseline,
                "stage_b_score": frozen["stage_b_score"],
                "stage_b_call": frozen["stage_b_call"],
            }
        )
        rows.append(frozen)

    by_league = {
        league: sum(1 for row in rows if row["league"] == league)
        for league in EXPECTED_BY_LEAGUE
    }
    calls = {
        call: sum(1 for row in rows if row["stage_b_call"] == call)
        for call in ("UP", "DOWN", "NO_CALL")
    }

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "feature_freeze_only": True,
        "primary_mapping_id": PRIMARY_MAPPING_ID,
        "mapping_formula": (
            "expected_home_npxg=0.5*(home_npxg_last5+away_npxga_last5); "
            "expected_away_npxg=0.5*(away_npxg_last5+home_npxga_last5); "
            "joint_expected_npxg=expected_home_npxg+expected_away_npxg; "
            "stage_b_score=joint_expected_npxg-pooled_2025_26_top5_baseline; "
            "score>0=>UP; score<0=>DOWN; score==0=>NO_CALL"
        ),
        "baseline_summary": baseline_summary,
        "locked_fixture_count": EXPECTED_LOCKED_FIXTURES,
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
    baseline = fetch_pooled_previous_season_baseline()
    report = freeze(feasibility, baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
