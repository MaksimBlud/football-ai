"""Offline frozen evaluator for CORNER_REGIME_ADJUSTED_DIRECTION_V2.

The evaluator cannot access the provider. It requires a complete immutable raw
odds artifact for the exact locked cohort before any normalization/statistics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

import corner_repricing_direction_replication_v1 as replication
import corner_regime_adjusted_direction_v1 as direction_v1
import corner_regime_adjusted_direction_v2 as v2
import corner_regime_adjusted_direction_v2_odds_plan as odds_plan

EVALUATOR_EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V2_EVALUATOR"
_SHA256_RE = re.compile(r"^(?:sha256:)?([0-9a-fA-F]{64})$")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _normalize_digest(value: str) -> str:
    match = _SHA256_RE.fullmatch(value.strip())
    if not match:
        raise ValueError("artifact digest must be a SHA-256 hex digest")
    return "sha256:" + match.group(1).lower()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must contain a JSON object")
    return payload


def validate_acquisition_plan(
    lock_manifest: dict[str, Any],
    acquisition_plan: dict[str, Any],
) -> None:
    odds_plan.validate_lock_manifest(lock_manifest)

    expected_exact = {
        "plan_experiment_id": odds_plan.PLAN_EXPERIMENT_ID,
        "source_lock_experiment_id": lock_manifest["lock_experiment_id"],
        "source_lock_status": lock_manifest["lock_status"],
        "source_selection_sha256": lock_manifest["selection_sha256"],
        "source_fixture_metadata_sha256": lock_manifest[
            "fixture_metadata_sha256"
        ],
        "research_only": True,
        "offline_only": True,
        "live_odds_acquisition_authorized": False,
        "requires_explicit_live_authorization": True,
        "fixture_reselection_allowed": False,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "future_cutoff_utc": v2.FUTURE_CUTOFF_UTC,
        "max_odds_requests_per_run": odds_plan.MAX_ODDS_REQUESTS_PER_RUN,
        "resume_rule": "REQUEST_ONLY_MISSING_IDS_FROM_SAME_LOCKED_COHORT",
    }
    for key, expected in expected_exact.items():
        if acquisition_plan.get(key) != expected:
            raise RuntimeError(
                f"acquisition plan mismatch for {key}: "
                f"expected {expected!r}, got {acquisition_plan.get(key)!r}"
            )

    selected_ids = [str(value) for value in lock_manifest["selected_fixture_ids"]]
    selected_metadata = lock_manifest["selected_fixture_metadata"]
    if acquisition_plan.get("selected_fixture_ids") != selected_ids:
        raise RuntimeError("acquisition plan fixture IDs differ from immutable lock")
    if acquisition_plan.get("selected_fixture_metadata") != selected_metadata:
        raise RuntimeError("acquisition plan fixture metadata differ from immutable lock")
    if int(acquisition_plan.get("selected_fixture_count", -1)) != len(selected_ids):
        raise RuntimeError("acquisition plan selected fixture count mismatch")
    if int(acquisition_plan.get("total_planned_odds_requests", -1)) != len(
        selected_ids
    ):
        raise RuntimeError("acquisition plan request count mismatch")

    batches = acquisition_plan.get("batches")
    if not isinstance(batches, list):
        raise RuntimeError("acquisition plan batches must be a list")

    flattened_ids: list[str] = []
    flattened_metadata: list[dict[str, Any]] = []
    for expected_index, batch in enumerate(batches, start=1):
        if not isinstance(batch, dict):
            raise RuntimeError("acquisition plan batch must be an object")
        if int(batch.get("batch_index", -1)) != expected_index:
            raise RuntimeError("acquisition plan batch index mismatch")
        fixture_ids = batch.get("fixture_ids")
        fixture_metadata = batch.get("fixture_metadata")
        if not isinstance(fixture_ids, list) or not isinstance(
            fixture_metadata, list
        ):
            raise RuntimeError("acquisition plan batch payload is invalid")
        if len(fixture_ids) > odds_plan.MAX_ODDS_REQUESTS_PER_RUN:
            raise RuntimeError("acquisition plan batch exceeds frozen request cap")
        if int(batch.get("planned_requests", -1)) != len(fixture_ids):
            raise RuntimeError("acquisition plan batch request count mismatch")
        if len(fixture_ids) != len(fixture_metadata):
            raise RuntimeError("acquisition batch metadata count mismatch")
        flattened_ids.extend(str(value) for value in fixture_ids)
        flattened_metadata.extend(fixture_metadata)

    if flattened_ids != selected_ids:
        raise RuntimeError("acquisition plan batches alter locked fixture order")
    if flattened_metadata != selected_metadata:
        raise RuntimeError("acquisition plan batches alter locked fixture metadata")
    if int(acquisition_plan.get("batch_count", -1)) != len(batches):
        raise RuntimeError("acquisition plan batch count mismatch")


def load_raw_odds(
    raw_odds_zip: Path,
    *,
    selected_ids: list[str],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    selected = set(selected_ids)
    raw_by_id: dict[str, dict[str, Any]] = {}

    with zipfile.ZipFile(raw_odds_zip) as zf:
        for name in zf.namelist():
            if "/raw/odds/" not in name or not name.endswith(".json"):
                continue
            fixture_id = Path(name).stem
            if fixture_id not in selected:
                raise RuntimeError(
                    f"raw odds artifact contains non-locked fixture {fixture_id}"
                )
            if fixture_id in raw_by_id:
                raise RuntimeError(f"duplicate raw odds response for {fixture_id}")
            payload = json.loads(zf.read(name).decode("utf-8"))
            if not isinstance(payload, dict):
                raise RuntimeError(
                    f"raw odds response for {fixture_id} must be a JSON object"
                )
            raw_by_id[fixture_id] = payload

    missing = [fixture_id for fixture_id in selected_ids if fixture_id not in raw_by_id]
    return raw_by_id, missing


def evaluate(
    lock_manifest: dict[str, Any],
    acquisition_plan: dict[str, Any],
    raw_odds_zip: Path,
    *,
    raw_workflow_run_id: str,
    raw_artifact_id: str,
    raw_artifact_digest: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    validate_acquisition_plan(lock_manifest, acquisition_plan)

    expected_digest = _normalize_digest(raw_artifact_digest)
    actual_digest = _file_sha256(raw_odds_zip)
    if actual_digest != expected_digest:
        raise RuntimeError(
            f"raw odds artifact digest mismatch: expected {expected_digest}, "
            f"got {actual_digest}"
        )

    selected_ids = [str(value) for value in lock_manifest["selected_fixture_ids"]]
    selected_metadata = lock_manifest["selected_fixture_metadata"]
    raw_by_id, missing = load_raw_odds(
        raw_odds_zip,
        selected_ids=selected_ids,
    )

    base: dict[str, Any] = {
        "experiment_id": EVALUATOR_EXPERIMENT_ID,
        "research_only": True,
        "offline_only": True,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "source_selection_sha256": lock_manifest["selection_sha256"],
        "source_fixture_metadata_sha256": lock_manifest[
            "fixture_metadata_sha256"
        ],
        "source_raw_workflow_run_id": str(raw_workflow_run_id),
        "source_raw_artifact_id": str(raw_artifact_id),
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
        default=Path("artifacts/corner_regime_adjusted_direction_v2_evaluator"),
    )
    args = parser.parse_args()

    lock_manifest = load_json_object(args.lock_manifest, label="lock manifest")
    acquisition_plan = load_json_object(
        args.acquisition_plan,
        label="acquisition plan",
    )
    rows, report = evaluate(
        lock_manifest,
        acquisition_plan,
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
