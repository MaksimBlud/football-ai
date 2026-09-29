"""Freeze one full-calendar recovery Stage-B mapping for V2B.

Research-only. Consumes the immutable 43-fixture full-calendar feasibility artifact.
The mapping uses only total full-calendar rest across both teams and a feature-only
cohort median frozen before any V2B direction outcome is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPERIMENT_ID = "V2B_FULL_CALENDAR_REST_STAGE_B_FREEZE_V1"
PRIMARY_MAPPING_ID = "JOINT_FULL_REST_COHORT_MEDIAN_SIGN_V1"
FEASIBILITY_EXPERIMENT_ID = "V2B_FULL_CALENDAR_LOAD_FEASIBILITY_V1"

EXPECTED_FEASIBILITY_ARTIFACT_ID = "11041563442"
EXPECTED_FEASIBILITY_ARTIFACT_DIGEST = (
    "sha256:93a2f808b7542a5f9c6429e2808e6f462f044404f3219adef5a1b80d880cf68c"
)
EXPECTED_LOCKED_FIXTURES = 43
EXPECTED_BASELINE = 11.0
EXPECTED_CALLS = {"UP": 17, "DOWN": 19, "NO_CALL": 7}


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validate_feasibility(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("experiment_id") != FEASIBILITY_EXPERIMENT_ID:
        raise RuntimeError("unexpected full-calendar feasibility experiment")
    if payload.get("status") != "FULL_43_RECONSTRUCTABLE_14D":
        raise RuntimeError("full-calendar feasibility is not complete")
    if payload.get("research_only") is not True:
        raise RuntimeError("feasibility artifact is not research-only")
    if payload.get("source_feasibility_audit") is not True:
        raise RuntimeError("source feasibility flag missing")
    if int(payload.get("lookback_days", -1)) != 14:
        raise RuntimeError("unexpected lookback")
    if int(payload.get("locked_fixture_count", -1)) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("unexpected locked fixture count")
    if int(payload.get("identity_matched_fixture_count", -1)) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("identity coverage changed")
    if int(payload.get("full_calendar_feasible_fixture_count", -1)) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("full-calendar feasibility coverage changed")

    for flag in (
        "market_rows_read",
        "v2b_odds_read",
        "centre_delta_read",
        "direction_test_performed",
        "match_outcome_target_used",
    ):
        if payload.get(flag) is not False:
            raise RuntimeError(f"feasibility safety flag changed: {flag}")

    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError("unexpected full-calendar rows")

    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("full-calendar row must be an object")
        fixture_id = str(row.get("fixture_id") or "")
        if not fixture_id or fixture_id in seen:
            raise RuntimeError("missing or duplicate fixture ID")
        seen.add(fixture_id)
        if row.get("identity_status") != "MATCHED":
            raise RuntimeError(f"{fixture_id}: identity is not matched")
        if row.get("full_calendar_feasible") is not True:
            raise RuntimeError(f"{fixture_id}: full calendar is not feasible")
        for side in ("home_load", "away_load"):
            load = row.get(side)
            if not isinstance(load, dict):
                raise RuntimeError(f"{fixture_id}: missing {side}")
            value = load.get("full_rest_days")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise RuntimeError(f"{fixture_id}: invalid {side}.full_rest_days")
            if float(value) < 0:
                raise RuntimeError(f"{fixture_id}: negative rest days")
    return rows


def _joint_rest(row: dict[str, Any]) -> float:
    return float(row["home_load"]["full_rest_days"]) + float(
        row["away_load"]["full_rest_days"]
    )


def freeze(feasibility: dict[str, Any]) -> dict[str, Any]:
    rows = _validate_feasibility(feasibility)
    joint_values = [_joint_rest(row) for row in rows]
    baseline = float(statistics.median(joint_values))
    if baseline != EXPECTED_BASELINE:
        raise RuntimeError(
            f"feature-only cohort median changed: expected {EXPECTED_BASELINE}, got {baseline}"
        )

    identities: list[dict[str, str]] = []
    frozen_features: list[dict[str, Any]] = []
    frozen_rows: list[dict[str, Any]] = []

    for row in rows:
        joint = _joint_rest(row)
        score = joint - baseline
        call = "UP" if score > 0 else "DOWN" if score < 0 else "NO_CALL"

        identity = {
            "fixture_id": str(row["fixture_id"]),
            "league": str(row["league"]),
            "kickoff_utc": str(row["kickoff_utc"]),
            "home_team": str(row["home_team"]),
            "away_team": str(row["away_team"]),
        }
        frozen = {
            **identity,
            "home_full_rest_days": float(row["home_load"]["full_rest_days"]),
            "away_full_rest_days": float(row["away_load"]["full_rest_days"]),
            "joint_full_rest_days": joint,
            "stage_b_score": score,
            "stage_b_call": call,
        }
        identities.append(identity)
        frozen_features.append(
            {
                **frozen,
                "cohort_median_joint_full_rest_days": baseline,
            }
        )
        frozen_rows.append(frozen)

    calls = {
        call: sum(1 for row in frozen_rows if row["stage_b_call"] == call)
        for call in ("UP", "DOWN", "NO_CALL")
    }
    if calls != EXPECTED_CALLS:
        raise RuntimeError(
            f"feature-only frozen call distribution changed: {calls}"
        )

    by_league: dict[str, dict[str, int]] = {}
    for row in frozen_rows:
        league = row["league"]
        league_calls = by_league.setdefault(
            league, {"rows": 0, "UP": 0, "DOWN": 0, "NO_CALL": 0}
        )
        league_calls["rows"] += 1
        league_calls[row["stage_b_call"]] += 1

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "feature_freeze_only": True,
        "primary_mapping_id": PRIMARY_MAPPING_ID,
        "source_feasibility_artifact_id": EXPECTED_FEASIBILITY_ARTIFACT_ID,
        "source_feasibility_artifact_digest": EXPECTED_FEASIBILITY_ARTIFACT_DIGEST,
        "source_lookback_days": 14,
        "mapping_rationale": (
            "For a total-corners direction hypothesis, aggregate recovery across both "
            "teams is used rather than home-away recovery difference. More joint rest "
            "than the feature-only cohort median maps to UP; less maps to DOWN."
        ),
        "mapping_formula": (
            "joint_full_rest_days=home_full_rest_days+away_full_rest_days; "
            "baseline=median(joint_full_rest_days across all 43 frozen feature rows); "
            "stage_b_score=joint_full_rest_days-baseline; "
            "score>0=>UP; score<0=>DOWN; score==0=>NO_CALL"
        ),
        "baseline_definition": "feature-only median across all 43 frozen V2B rows",
        "cohort_median_joint_full_rest_days": baseline,
        "locked_fixture_count": EXPECTED_LOCKED_FIXTURES,
        "stage_b_calls": calls,
        "calls_by_league": by_league,
        "eligible_fixture_sha256": _sha256_json(identities),
        "frozen_feature_sha256": _sha256_json(frozen_features),
        "market_rows_read": False,
        "v2b_odds_read": False,
        "opening_lambda_read": False,
        "fair_centre_read": False,
        "centre_delta_read": False,
        "direction_test_performed": False,
        "match_outcome_target_used": False,
        "threshold_fitted_to_outcomes": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "rows": frozen_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feasibility-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    feasibility = json.loads(args.feasibility_report.read_text(encoding="utf-8"))
    report = freeze(feasibility)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
