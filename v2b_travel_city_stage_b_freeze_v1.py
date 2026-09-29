"""Freeze one travel-city Stage-B mapping for the exact V2B cohort.

Research-only. Consumes immutable travel-city source artifact 11044402420.
No market direction, centre_delta, outcome or betting field is read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPERIMENT_ID = "V2B_TRAVEL_CITY_STAGE_B_FREEZE_V1"
SOURCE_EXPERIMENT_ID = "V2B_TRAVEL_VENUE_FEASIBILITY_V1"
PRIMARY_MAPPING_ID = "JOINT_TRAVEL_CITY_COHORT_MEDIAN_SIGN_V1"

EXPECTED_SOURCE_ARTIFACT_ID = "11044402420"
EXPECTED_SOURCE_ARTIFACT_DIGEST = (
    "sha256:24eaa543e51f1d19ec34d5b348fa091b91d31e7eca2ceeac270338dbaab3ab04"
)
EXPECTED_SOURCE_STATUS = "FULL_43_TRAVEL_CITY_PROXY_FEASIBLE"
EXPECTED_FIXTURES = 43
EXPECTED_TEAM_SIDES = 86
EXPECTED_BASELINE = 600.4646884282998
EXPECTED_CALLS = {"UP": 21, "DOWN": 21, "NO_CALL": 1}
ABS_TOL = 1e-9


def _sha256_json(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _validate_source(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("experiment_id") != SOURCE_EXPERIMENT_ID:
        raise RuntimeError("unexpected travel source experiment")
    if payload.get("status") != EXPECTED_SOURCE_STATUS:
        raise RuntimeError("travel source is not fully feasible")
    if payload.get("research_only") is not True:
        raise RuntimeError("travel source is not research-only")
    if payload.get("source_feasibility_audit") is not True:
        raise RuntimeError("travel source feasibility flag missing")
    if int(payload.get("locked_fixture_count", -1)) != EXPECTED_FIXTURES:
        raise RuntimeError("unexpected travel source fixture count")
    if int(payload.get("team_side_count", -1)) != EXPECTED_TEAM_SIDES:
        raise RuntimeError("unexpected travel source team-side count")
    if int(payload.get("travel_distance_resolved_team_sides", -1)) != EXPECTED_TEAM_SIDES:
        raise RuntimeError("travel source distance coverage changed")

    for flag in (
        "market_rows_read",
        "v2b_odds_read",
        "opening_lambda_read",
        "fair_centre_read",
        "centre_delta_read",
        "direction_test_performed",
        "match_outcome_target_used",
        "threshold_fitted_to_outcomes",
    ):
        if payload.get(flag) is not False:
            raise RuntimeError(f"travel source safety flag changed: {flag}")

    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_TEAM_SIDES:
        raise RuntimeError("unexpected travel source rows")

    seen: set[tuple[str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("travel source row must be an object")
        fixture_id = str(row.get("fixture_id") or "")
        side = str(row.get("side") or "")
        if not fixture_id or side not in {"home", "away"}:
            raise RuntimeError("invalid travel source fixture/side identity")
        key = (fixture_id, side)
        if key in seen:
            raise RuntimeError("duplicate travel source fixture/side")
        seen.add(key)

        value = row.get("travel_city_km_since_previous_match")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise RuntimeError("invalid travel distance value")
        if not math.isfinite(float(value)) or float(value) < 0.0:
            raise RuntimeError("non-finite or negative travel distance")

    return rows


def _fixture_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        fixture_id = str(row["fixture_id"])
        side = str(row["side"])
        grouped.setdefault(fixture_id, {})[side] = row

    if len(grouped) != EXPECTED_FIXTURES:
        raise RuntimeError("unexpected unique fixture count")

    result: list[dict[str, Any]] = []
    for fixture_id in sorted(grouped):
        sides = grouped[fixture_id]
        if set(sides) != {"home", "away"}:
            raise RuntimeError(f"{fixture_id}: missing home/away travel side")

        home = sides["home"]
        away = sides["away"]

        if str(home["league"]) != str(away["league"]):
            raise RuntimeError(f"{fixture_id}: league mismatch")
        if str(home["current_venue_host"]) != str(away["current_venue_host"]):
            raise RuntimeError(f"{fixture_id}: current venue host mismatch")
        if str(home["team"]) != str(home["current_venue_host"]):
            raise RuntimeError(
                f"{fixture_id}: home row team is not current target host"
            )

        home_km = float(home["travel_city_km_since_previous_match"])
        away_km = float(away["travel_city_km_since_previous_match"])
        result.append(
            {
                "fixture_id": fixture_id,
                "league": str(home["league"]),
                "home_team": str(home["team"]),
                "away_team": str(away["team"]),
                "current_venue_host": str(home["current_venue_host"]),
                "home_travel_city_km": home_km,
                "away_travel_city_km": away_km,
                "joint_travel_city_km": home_km + away_km,
            }
        )

    return result


def freeze(source: dict[str, Any]) -> dict[str, Any]:
    rows = _validate_source(source)
    fixtures = _fixture_rows(rows)

    values = [float(row["joint_travel_city_km"]) for row in fixtures]
    baseline = float(statistics.median(values))
    if not math.isclose(
        baseline,
        EXPECTED_BASELINE,
        rel_tol=0.0,
        abs_tol=ABS_TOL,
    ):
        raise RuntimeError(
            "feature-only joint-travel median changed: "
            f"expected {EXPECTED_BASELINE}, got {baseline}"
        )

    identities: list[dict[str, str]] = []
    frozen_features: list[dict[str, Any]] = []
    frozen_rows: list[dict[str, Any]] = []

    for row in fixtures:
        joint = float(row["joint_travel_city_km"])
        score = baseline - joint
        if math.isclose(score, 0.0, rel_tol=0.0, abs_tol=ABS_TOL):
            score = 0.0
            call = "NO_CALL"
        elif score > 0.0:
            call = "UP"
        else:
            call = "DOWN"

        identity = {
            "fixture_id": str(row["fixture_id"]),
            "league": str(row["league"]),
            "home_team": str(row["home_team"]),
            "away_team": str(row["away_team"]),
        }
        frozen = {
            **identity,
            "current_venue_host": str(row["current_venue_host"]),
            "home_travel_city_km": float(row["home_travel_city_km"]),
            "away_travel_city_km": float(row["away_travel_city_km"]),
            "joint_travel_city_km": joint,
            "stage_b_score": score,
            "stage_b_call": call,
        }
        identities.append(identity)
        frozen_rows.append(frozen)
        frozen_features.append(
            {
                **frozen,
                "cohort_median_joint_travel_city_km": baseline,
            }
        )

    calls = {
        call: sum(1 for row in frozen_rows if row["stage_b_call"] == call)
        for call in ("UP", "DOWN", "NO_CALL")
    }
    if calls != EXPECTED_CALLS:
        raise RuntimeError(
            f"feature-only travel call distribution changed: {calls}"
        )

    by_league: dict[str, dict[str, int]] = {}
    for row in frozen_rows:
        league = row["league"]
        entry = by_league.setdefault(
            league,
            {"rows": 0, "UP": 0, "DOWN": 0, "NO_CALL": 0},
        )
        entry["rows"] += 1
        entry[row["stage_b_call"]] += 1

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "feature_freeze_only": True,
        "primary_mapping_id": PRIMARY_MAPPING_ID,
        "source_travel_artifact_id": EXPECTED_SOURCE_ARTIFACT_ID,
        "source_travel_artifact_digest": EXPECTED_SOURCE_ARTIFACT_DIGEST,
        "source_travel_status": EXPECTED_SOURCE_STATUS,
        "geographic_precision": source.get("geographic_precision"),
        "mapping_rationale": (
            "For total-corners direction, aggregate both teams' displacement "
            "since their latest full-calendar prior match. Lower joint travel "
            "than the feature-only cohort median maps to UP; higher maps to DOWN."
        ),
        "mapping_formula": (
            "joint_travel_city_km=home_travel_city_km+away_travel_city_km; "
            "baseline=median(joint_travel_city_km across all 43 frozen fixtures); "
            "stage_b_score=baseline-joint_travel_city_km; "
            "score>0=>UP; score<0=>DOWN; score==0=>NO_CALL"
        ),
        "baseline_definition": "feature-only median across all 43 frozen V2B fixtures",
        "cohort_median_joint_travel_city_km": baseline,
        "locked_fixture_count": EXPECTED_FIXTURES,
        "team_side_count": EXPECTED_TEAM_SIDES,
        "stage_b_calls": calls,
        "calls_by_league": by_league,
        "joint_travel_city_km_min": min(values),
        "joint_travel_city_km_max": max(values),
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
        "rest_feature_used": False,
        "travel_rest_interaction_used": False,
        "league_specific_threshold_used": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "rows": frozen_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--travel-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source = json.loads(args.travel_report.read_text(encoding="utf-8"))
    report = freeze(source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
