"""Evaluate frozen V2B result-strength Stage-B calls against opened market direction.

Research-only opened-sample hypothesis generation. This evaluator consumes:
- the immutable frozen Stage-B feature artifact;
- the already-opened V2B market evaluation rows.

It makes no provider calls, performs no feature refit and does not alter Stage A.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

EXPERIMENT_ID = "V2B_RESULT_STRENGTH_TRAJECTORY_EVALUATOR_V1"
FEATURE_EXPERIMENT_ID = "V2B_RESULT_STRENGTH_TRAJECTORY_FREEZE_V1"
PRIMARY_MAPPING_ID = "JOINT_PERFORMANCE_RESIDUAL_5_SIGN_V1"

EXPECTED_FEATURE_ARTIFACT_ID = "10975465958"
EXPECTED_FEATURE_ARTIFACT_DIGEST = (
    "sha256:d30f4231e7e0a9149d0869ac6d775eac9d2182316593610f2b42637afc26dbe3"
)
EXPECTED_FEATURE_COHORT_SHA256 = (
    "sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1"
)
EXPECTED_MARKET_ARTIFACT_ID = "10899842049"
EXPECTED_MARKET_ARTIFACT_DIGEST = (
    "sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff"
)
EXPECTED_ELIGIBLE_FIXTURES = 34
EXPECTED_STAGE_B_CALLS = {"UP": 16, "DOWN": 18, "NO_CALL": 0}
EPS = 1e-12


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path}: expected JSON object")
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _validate_feature_freeze(payload: dict[str, Any]) -> pd.DataFrame:
    if payload.get("experiment_id") != FEATURE_EXPERIMENT_ID:
        raise RuntimeError("unexpected feature-freeze experiment")
    if payload.get("research_only") is not True:
        raise RuntimeError("feature freeze is not research-only")
    if payload.get("feature_freeze_only") is not True:
        raise RuntimeError("feature artifact is not marked feature-freeze only")
    if payload.get("primary_mapping_id") != PRIMARY_MAPPING_ID:
        raise RuntimeError("unexpected Stage-B mapping")
    if payload.get("eligible_fixture_sha256") != EXPECTED_FEATURE_COHORT_SHA256:
        raise RuntimeError("unexpected frozen eligible-fixture hash")
    if int(payload.get("eligible_fixture_count", -1)) != EXPECTED_ELIGIBLE_FIXTURES:
        raise RuntimeError("unexpected frozen eligible count")
    if payload.get("stage_b_calls") != EXPECTED_STAGE_B_CALLS:
        raise RuntimeError("frozen Stage-B call distribution changed")
    if payload.get("direction_test_performed") is not False:
        raise RuntimeError("feature artifact unexpectedly contains direction testing")
    if payload.get("v2b_odds_read") is not False:
        raise RuntimeError("feature artifact unexpectedly read V2B odds")
    if payload.get("opening_lambda_read") is not False:
        raise RuntimeError("feature artifact unexpectedly read opening lambda")
    if payload.get("centre_delta_read") is not False:
        raise RuntimeError("feature artifact unexpectedly read centre delta")

    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ELIGIBLE_FIXTURES:
        raise RuntimeError("unexpected feature rows")
    frame = pd.DataFrame(rows)
    required = {
        "fixture_id",
        "league",
        "kickoff_utc",
        "home_team",
        "away_team",
        "stage_b_score",
        "stage_b_call",
        "home_performance_residual_5",
        "away_performance_residual_5",
    }
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"feature rows missing columns {sorted(missing)}")

    frame["fixture_id"] = frame["fixture_id"].astype(str)
    if frame["fixture_id"].duplicated().any():
        raise RuntimeError("duplicate frozen feature fixture IDs")
    frame["stage_b_score"] = pd.to_numeric(frame["stage_b_score"], errors="coerce")
    if not np.isfinite(frame["stage_b_score"].to_numpy(float)).all():
        raise RuntimeError("non-finite Stage-B score")
    if not set(frame["stage_b_call"]).issubset({"UP", "DOWN", "NO_CALL"}):
        raise RuntimeError("invalid Stage-B call")
    return frame


def _validate_market_rows(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "fixture_id",
        "league",
        "kickoff_utc",
        "home_team",
        "away_team",
        "centre_delta",
        "movement_magnitude",
    }
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"market rows missing columns {sorted(missing)}")

    out = frame.copy()
    out["fixture_id"] = out["fixture_id"].astype(str)
    if out["fixture_id"].duplicated().any():
        raise RuntimeError("duplicate market fixture IDs")
    for column in ("centre_delta", "movement_magnitude"):
        out[column] = pd.to_numeric(out[column], errors="coerce")
    if not np.isfinite(out[["centre_delta", "movement_magnitude"]].to_numpy(float)).all():
        raise RuntimeError("non-finite market movement values")
    if len(out) != 43:
        raise RuntimeError(f"expected complete 43-row V2B market artifact, got {len(out)}")
    return out


def _correlations(frame: pd.DataFrame) -> dict[str, float | None]:
    if len(frame) < 2:
        return {"pearson": None, "spearman": None}
    x = frame["stage_b_score"].astype(float)
    y = frame["centre_delta"].astype(float)
    pearson = float(x.corr(y, method="pearson"))
    spearman = float(
        x.rank(method="average").corr(
            y.rank(method="average"),
            method="pearson",
        )
    )
    return {
        "pearson": pearson if np.isfinite(pearson) else None,
        "spearman": spearman if np.isfinite(spearman) else None,
    }


def _league_report(group: pd.DataFrame) -> dict[str, Any]:
    comparable = group[
        (group["stage_b_call"] != "NO_CALL")
        & (group["centre_delta"].abs() > EPS)
    ]
    concordant = comparable[
        comparable["stage_b_call"] == comparable["observed_direction"]
    ]
    return {
        "rows": int(len(group)),
        "zero_movement_rows": int((group["centre_delta"].abs() <= EPS).sum()),
        "comparable_rows": int(len(comparable)),
        "concordant_rows": int(len(concordant)),
        "concordance": (
            float(len(concordant) / len(comparable)) if len(comparable) else None
        ),
    }


def evaluate(
    feature_freeze: dict[str, Any],
    market_rows: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    features = _validate_feature_freeze(feature_freeze)
    market = _validate_market_rows(market_rows)

    merged = features.merge(
        market[
            [
                "fixture_id",
                "league",
                "kickoff_utc",
                "home_team",
                "away_team",
                "centre_delta",
                "movement_magnitude",
            ]
        ],
        on=["fixture_id", "league"],
        how="left",
        suffixes=("_feature", "_market"),
        validate="one_to_one",
    )
    if len(merged) != EXPECTED_ELIGIBLE_FIXTURES:
        raise RuntimeError("market join changed frozen 34-fixture cohort")
    if merged[["centre_delta", "movement_magnitude"]].isna().any().any():
        raise RuntimeError("market rows missing for frozen Stage-B fixture")

    # Identity consistency is an audit guard, not a selection criterion.
    if not (
        (merged["home_team_feature"] == merged["home_team_market"]).all()
        and (merged["away_team_feature"] == merged["away_team_market"]).all()
    ):
        raise RuntimeError("feature/market team identity mismatch")

    merged["observed_direction"] = np.where(
        merged["centre_delta"] > EPS,
        "UP",
        np.where(merged["centre_delta"] < -EPS, "DOWN", "ZERO"),
    )
    merged["comparable"] = (
        (merged["stage_b_call"] != "NO_CALL")
        & (merged["centre_delta"].abs() > EPS)
    )
    merged["concordant"] = (
        merged["comparable"]
        & (merged["stage_b_call"] == merged["observed_direction"])
    )

    comparable = merged[merged["comparable"]]
    concordant = merged[merged["concordant"]]

    call_groups: dict[str, Any] = {}
    for call in ("UP", "DOWN", "NO_CALL"):
        group = merged[merged["stage_b_call"] == call]
        call_groups[call] = {
            "rows": int(len(group)),
            "mean_centre_delta": (
                float(group["centre_delta"].mean()) if len(group) else None
            ),
            "median_centre_delta": (
                float(group["centre_delta"].median()) if len(group) else None
            ),
            "mean_movement_magnitude": (
                float(group["movement_magnitude"].mean()) if len(group) else None
            ),
            "zero_movement_rows": int((group["centre_delta"].abs() <= EPS).sum()),
        }

    by_league = {
        league: _league_report(group)
        for league, group in merged.groupby("league", sort=True)
    }
    supporting_leagues = sum(
        1
        for item in by_league.values()
        if item["comparable_rows"] >= 2
        and item["concordance"] is not None
        and item["concordance"] > 0.50
    )

    pooled_concordance = (
        float(len(concordant) / len(comparable)) if len(comparable) else None
    )
    up_mean = call_groups["UP"]["mean_centre_delta"]
    down_mean = call_groups["DOWN"]["mean_centre_delta"]
    sign_means_aligned = bool(
        up_mean is not None
        and down_mean is not None
        and up_mean > 0.0
        and down_mean < 0.0
    )

    # Reuse the same fixed exploratory consistency gate previously applied to
    # the CORNERS10 opened-sample hypothesis. No new threshold is introduced.
    promising = bool(
        pooled_concordance is not None
        and pooled_concordance > 0.60
        and supporting_leagues >= 3
        and sign_means_aligned
    )

    confusion: dict[str, dict[str, int]] = {}
    for call in ("UP", "DOWN", "NO_CALL"):
        subset = merged[merged["stage_b_call"] == call]
        confusion[call] = {
            observed: int((subset["observed_direction"] == observed).sum())
            for observed in ("UP", "DOWN", "ZERO")
        }

    report = {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "opened_sample_hypothesis_generation": True,
        "confirmatory_replication": False,
        "primary_mapping_id": PRIMARY_MAPPING_ID,
        "source_feature_artifact_id": EXPECTED_FEATURE_ARTIFACT_ID,
        "source_feature_artifact_digest": EXPECTED_FEATURE_ARTIFACT_DIGEST,
        "source_feature_cohort_sha256": EXPECTED_FEATURE_COHORT_SHA256,
        "source_market_artifact_id": EXPECTED_MARKET_ARTIFACT_ID,
        "source_market_artifact_digest": EXPECTED_MARKET_ARTIFACT_DIGEST,
        "frozen_eligible_fixture_count": EXPECTED_ELIGIBLE_FIXTURES,
        "evaluated_rows": int(len(merged)),
        "predicted_call_counts": {
            call: int((merged["stage_b_call"] == call).sum())
            for call in ("UP", "DOWN", "NO_CALL")
        },
        "observed_movement_counts": {
            direction: int((merged["observed_direction"] == direction).sum())
            for direction in ("UP", "DOWN", "ZERO")
        },
        "zero_observed_movement_rows": int(
            (merged["centre_delta"].abs() <= EPS).sum()
        ),
        "comparable_rows": int(len(comparable)),
        "concordant_rows": int(len(concordant)),
        "pooled_concordance": pooled_concordance,
        "supporting_leagues_with_at_least_2_comparable_rows": int(
            supporting_leagues
        ),
        "call_group_mean_deltas_aligned": sign_means_aligned,
        "call_groups": call_groups,
        "by_league": by_league,
        "confusion": confusion,
        "continuous_correlations": _correlations(merged),
        "classification": (
            "PROMISING_DIRECTION_HYPOTHESIS"
            if promising
            else "WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS"
        ),
        "evaluation_rule": (
            "PROMISING iff pooled non-zero-move concordance >0.60, at least "
            "3 leagues have >=2 comparable rows with concordance >0.50, and "
            "mean centre_delta is >0 for frozen UP calls and <0 for frozen "
            "DOWN calls"
        ),
        "stage_a_threshold_selected": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "interpretation": (
            "Opened-sample hypothesis generation only. The frozen Stage-B "
            "mapping cannot be retuned from this result; confirmation requires "
            "a new unseen market cohort."
        ),
    }
    return merged, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-freeze", type=Path, required=True)
    parser.add_argument("--market-rows", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    rows, report = evaluate(
        _read_json(args.feature_freeze),
        pd.read_csv(args.market_rows),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows.to_csv(args.output_dir / "evaluation_rows.csv", index=False)
    _write_json(args.output_dir / "report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
