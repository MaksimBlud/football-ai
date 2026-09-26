"""Offline frozen evaluator adapter for CORNER_REGIME_ADJUSTED_DIRECTION_V2B.

The statistical method is inherited unchanged from the already-frozen V1/V2
evaluator. This module only validates V2B provenance and feeds the complete
immutable raw artifact into the existing normalizer + direction statistic.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

import corner_repricing_direction_replication_v1 as replication
import corner_regime_adjusted_direction_v1 as direction_v1
import corner_regime_adjusted_direction_v2_evaluator as frozen
import corner_regime_adjusted_direction_v2b as v2b
import corner_regime_adjusted_direction_v2b_odds_plan as odds_plan

EVALUATOR_EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V2B_EVALUATOR"

EXPECTED_LOCK_RUN_ID = "36219786013"
EXPECTED_LOCK_ARTIFACT_ID = "10899325930"
EXPECTED_LOCK_ARTIFACT_DIGEST = (
    "sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f"
)
EXPECTED_PLAN_RUN_ID = "36220204953"
EXPECTED_PLAN_ARTIFACT_ID = "10899305926"
EXPECTED_PLAN_ARTIFACT_DIGEST = (
    "sha256:8fe2203443f4e59a5800fd7315df6d333a19771e9827d3cad64ef4f658119c56"
)
EXPECTED_RAW_RUN_ID = "36222282829"
EXPECTED_RAW_ARTIFACT_ID = "10899611444"
EXPECTED_RAW_ARTIFACT_DIGEST = (
    "sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57"
)


def _write_json(path: Path, payload: Any) -> None:
    frozen._write_json(path, payload)


def load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    return frozen.load_json_object(path, label=label)


def validate_lock_and_plan(
    lock_manifest: dict[str, Any],
    acquisition_plan: dict[str, Any],
) -> None:
    odds_plan.validate_lock_manifest(lock_manifest)

    expected = {
        "plan_experiment_id": odds_plan.PLAN_EXPERIMENT_ID,
        "source_lock_experiment_id": lock_manifest["lock_experiment_id"],
        "source_lock_status": "IMMUTABLE_COHORT_LOCKED",
        "source_lock_workflow_run_id": EXPECTED_LOCK_RUN_ID,
        "source_lock_artifact_id": EXPECTED_LOCK_ARTIFACT_ID,
        "source_lock_artifact_digest": EXPECTED_LOCK_ARTIFACT_DIGEST,
        "source_selection_sha256": lock_manifest["selection_sha256"],
        "source_fixture_metadata_sha256": lock_manifest[
            "fixture_metadata_sha256"
        ],
        "research_only": True,
        "offline_only": True,
        "post_metadata_pre_odds_amendment": True,
        "live_odds_acquisition_authorized": False,
        "requires_explicit_live_authorization": True,
        "fixture_reselection_allowed": False,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "future_cutoff_utc": v2b.FUTURE_CUTOFF_UTC,
        "selected_fixture_count": 43,
        "max_odds_requests_per_batch": odds_plan.MAX_ODDS_REQUESTS_PER_BATCH,
        "total_planned_odds_requests": 43,
        "batch_count": 2,
        "resume_rule": "REQUEST_ONLY_MISSING_IDS_FROM_SAME_LOCKED_COHORT",
    }
    for key, value in expected.items():
        if acquisition_plan.get(key) != value:
            raise RuntimeError(
                f"V2B acquisition plan mismatch for {key}: "
                f"expected {value!r}, got {acquisition_plan.get(key)!r}"
            )

    selected_ids = [str(value) for value in lock_manifest["selected_fixture_ids"]]
    selected_metadata = lock_manifest["selected_fixture_metadata"]
    if acquisition_plan.get("selected_fixture_ids") != selected_ids:
        raise RuntimeError("V2B acquisition plan fixture IDs differ from lock")
    if acquisition_plan.get("selected_fixture_metadata") != selected_metadata:
        raise RuntimeError("V2B acquisition plan fixture metadata differ from lock")

    batches = acquisition_plan.get("batches")
    if not isinstance(batches, list) or len(batches) != 2:
        raise RuntimeError("V2B acquisition plan must contain exactly two batches")

    flattened_ids: list[str] = []
    flattened_metadata: list[dict[str, Any]] = []
    for expected_index, batch in enumerate(batches, start=1):
        if not isinstance(batch, dict):
            raise RuntimeError("V2B acquisition plan batch must be an object")
        if int(batch.get("batch_index", -1)) != expected_index:
            raise RuntimeError("V2B acquisition plan batch index mismatch")
        fixture_ids = batch.get("fixture_ids")
        fixture_metadata = batch.get("fixture_metadata")
        if not isinstance(fixture_ids, list) or not isinstance(
            fixture_metadata, list
        ):
            raise RuntimeError("V2B acquisition plan batch payload invalid")
        if int(batch.get("planned_requests", -1)) != len(fixture_ids):
            raise RuntimeError("V2B acquisition plan batch request count mismatch")
        if len(fixture_ids) != len(fixture_metadata):
            raise RuntimeError("V2B acquisition plan batch metadata count mismatch")
        flattened_ids.extend(str(value) for value in fixture_ids)
        flattened_metadata.extend(fixture_metadata)

    if [len(batch["fixture_ids"]) for batch in batches] != [30, 13]:
        raise RuntimeError("V2B frozen batch sizes must be 30 + 13")
    if flattened_ids != selected_ids:
        raise RuntimeError("V2B batches alter locked fixture order/membership")
    if flattened_metadata != selected_metadata:
        raise RuntimeError("V2B batches alter locked fixture metadata")


def evaluate(
    lock_manifest: dict[str, Any],
    acquisition_plan: dict[str, Any],
    raw_odds_zip: Path,
    *,
    raw_workflow_run_id: str,
    raw_artifact_id: str,
    raw_artifact_digest: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    validate_lock_and_plan(lock_manifest, acquisition_plan)

    if str(raw_workflow_run_id) != EXPECTED_RAW_RUN_ID:
        raise RuntimeError("unexpected V2B raw workflow run ID")
    if str(raw_artifact_id) != EXPECTED_RAW_ARTIFACT_ID:
        raise RuntimeError("unexpected V2B raw artifact ID")

    expected_digest = frozen._normalize_digest(raw_artifact_digest)
    if expected_digest != EXPECTED_RAW_ARTIFACT_DIGEST:
        raise RuntimeError("unexpected V2B raw artifact digest provenance")

    actual_digest = frozen._file_sha256(raw_odds_zip)
    if actual_digest != expected_digest:
        raise RuntimeError(
            f"raw odds artifact digest mismatch: expected {expected_digest}, "
            f"got {actual_digest}"
        )

    selected_ids = [str(value) for value in lock_manifest["selected_fixture_ids"]]
    selected_metadata = lock_manifest["selected_fixture_metadata"]
    raw_by_id, missing = frozen.load_raw_odds(
        raw_odds_zip,
        selected_ids=selected_ids,
    )

    base: dict[str, Any] = {
        "experiment_id": EVALUATOR_EXPERIMENT_ID,
        "research_only": True,
        "offline_only": True,
        "post_metadata_pre_odds_amendment": True,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "source_lock_workflow_run_id": EXPECTED_LOCK_RUN_ID,
        "source_lock_artifact_id": EXPECTED_LOCK_ARTIFACT_ID,
        "source_lock_artifact_digest": EXPECTED_LOCK_ARTIFACT_DIGEST,
        "source_plan_workflow_run_id": EXPECTED_PLAN_RUN_ID,
        "source_plan_artifact_id": EXPECTED_PLAN_ARTIFACT_ID,
        "source_plan_artifact_digest": EXPECTED_PLAN_ARTIFACT_DIGEST,
        "source_selection_sha256": lock_manifest["selection_sha256"],
        "source_fixture_metadata_sha256": lock_manifest[
            "fixture_metadata_sha256"
        ],
        "source_raw_workflow_run_id": EXPECTED_RAW_RUN_ID,
        "source_raw_artifact_id": EXPECTED_RAW_ARTIFACT_ID,
        "source_raw_artifact_digest": expected_digest,
        "locked_fixture_count": len(selected_ids),
        "captured_locked_raw_responses": len(raw_by_id),
        "missing_locked_fixture_ids": missing,
    }

    if missing:
        return pd.DataFrame(), {
            **base,
            "status": "ACQUISITION_INCOMPLETE",
            "acquisition_complete": False,
            "statistical_evaluation_performed": False,
            "verdict": None,
        }

    normalized_rows: list[dict[str, Any]] = []
    ineligible_ids: list[str] = []
    for fixture in selected_metadata:
        fixture_id = str(fixture["fixture_id"])
        row = replication.normalize_corner_odds(raw_by_id[fixture_id], fixture)
        if row is None:
            ineligible_ids.append(fixture_id)
            continue
        normalized = replication._normalize_holdout_row(row)
        if normalized is None:
            ineligible_ids.append(fixture_id)
            continue
        normalized_rows.append(normalized)

    fresh = pd.DataFrame(normalized_rows)
    eval_rows, direction_report = direction_v1.evaluate_fresh_direction(fresh)

    return eval_rows, {
        **base,
        "status": "EVALUATED",
        "acquisition_complete": True,
        "statistical_evaluation_performed": True,
        "eligible_normalized_rows": int(len(eval_rows)),
        "ineligible_selected_fixture_ids": ineligible_ids,
        "frozen_direction_report": direction_report,
        "verdict": direction_report["verdict"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock-manifest", type=Path, required=True)
    parser.add_argument("--acquisition-plan", type=Path, required=True)
    parser.add_argument("--raw-odds-zip", type=Path, required=True)
    parser.add_argument("--raw-workflow-run-id", required=True)
    parser.add_argument("--raw-artifact-id", required=True)
    parser.add_argument("--raw-artifact-digest", required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/corner_regime_adjusted_direction_v2b_evaluator"),
    )
    args = parser.parse_args()

    rows, report = evaluate(
        load_json_object(args.lock_manifest, label="V2B lock manifest"),
        load_json_object(args.acquisition_plan, label="V2B acquisition plan"),
        args.raw_odds_zip,
        raw_workflow_run_id=args.raw_workflow_run_id,
        raw_artifact_id=args.raw_artifact_id,
        raw_artifact_digest=args.raw_artifact_digest,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows.to_csv(args.output_dir / "evaluation_rows.csv", index=False)
    _write_json(args.output_dir / "report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
