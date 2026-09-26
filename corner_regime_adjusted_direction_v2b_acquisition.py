"""Controlled live raw-odds acquisition for the immutable V2B cohort.

This module cannot discover fixtures or evaluate direction. It consumes only the
immutable V2B lock + acquisition plan and fetches corner odds for one frozen
batch at a time.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

import corner_repricing_direction_replication_v1 as replication
import corner_regime_adjusted_direction_v2b_odds_plan as odds_plan

ACQUISITION_EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V2B_LIVE_ACQUISITION"
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


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must contain a JSON object")
    return payload


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
        "source_fixture_metadata_sha256": lock_manifest["fixture_metadata_sha256"],
        "research_only": True,
        "offline_only": True,
        "post_metadata_pre_odds_amendment": True,
        "live_odds_acquisition_authorized": False,
        "requires_explicit_live_authorization": True,
        "fixture_reselection_allowed": False,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "selected_fixture_count": 43,
        "max_odds_requests_per_batch": 30,
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
        raise RuntimeError("acquisition plan fixture IDs differ from immutable lock")
    if acquisition_plan.get("selected_fixture_metadata") != selected_metadata:
        raise RuntimeError("acquisition plan fixture metadata differ from immutable lock")

    batches = acquisition_plan.get("batches")
    if not isinstance(batches, list) or len(batches) != 2:
        raise RuntimeError("V2B acquisition plan must contain exactly two batches")

    flattened_ids: list[str] = []
    flattened_metadata: list[dict[str, Any]] = []
    for expected_index, batch in enumerate(batches, start=1):
        if int(batch.get("batch_index", -1)) != expected_index:
            raise RuntimeError("V2B batch index mismatch")
        fixture_ids = batch.get("fixture_ids")
        fixture_metadata = batch.get("fixture_metadata")
        if not isinstance(fixture_ids, list) or not isinstance(fixture_metadata, list):
            raise RuntimeError("V2B batch payload invalid")
        if int(batch.get("planned_requests", -1)) != len(fixture_ids):
            raise RuntimeError("V2B batch request count mismatch")
        if len(fixture_ids) != len(fixture_metadata):
            raise RuntimeError("V2B batch metadata count mismatch")
        flattened_ids.extend(str(value) for value in fixture_ids)
        flattened_metadata.extend(fixture_metadata)

    if [len(batch["fixture_ids"]) for batch in batches] != [30, 13]:
        raise RuntimeError("V2B frozen batch sizes must be 30 + 13")
    if flattened_ids != selected_ids:
        raise RuntimeError("V2B batches alter locked fixture order/membership")
    if flattened_metadata != selected_metadata:
        raise RuntimeError("V2B batches alter locked fixture metadata")


def load_resume_raw(
    resume_zip: Path | None,
    *,
    selected_ids: list[str],
) -> dict[str, dict[str, Any]]:
    if resume_zip is None:
        return {}

    selected = set(selected_ids)
    raw_by_id: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(resume_zip) as zf:
        for name in zf.namelist():
            normalized = "/" + name.lstrip("/")
            if "/raw/odds/" not in normalized or not name.endswith(".json"):
                continue
            fixture_id = Path(name).stem
            if fixture_id not in selected:
                raise RuntimeError(
                    f"resume artifact contains non-locked fixture {fixture_id}"
                )
            if fixture_id in raw_by_id:
                raise RuntimeError(f"duplicate resume raw response for {fixture_id}")
            payload = json.loads(zf.read(name).decode("utf-8"))
            if not isinstance(payload, dict):
                raise RuntimeError(
                    f"resume raw response for {fixture_id} must be a JSON object"
                )
            raw_by_id[fixture_id] = payload
    return raw_by_id


def _base_report(
    *,
    lock_manifest: dict[str, Any],
    acquisition_plan: dict[str, Any],
    batch_index: int,
    raw_by_id: dict[str, dict[str, Any]],
    fetched_ids: list[str],
    provider_requests: int,
) -> dict[str, Any]:
    selected_ids = [str(value) for value in lock_manifest["selected_fixture_ids"]]
    missing = [fixture_id for fixture_id in selected_ids if fixture_id not in raw_by_id]
    target_ids = [
        str(value)
        for value in acquisition_plan["batches"][batch_index - 1]["fixture_ids"]
    ]
    return {
        "experiment_id": ACQUISITION_EXPERIMENT_ID,
        "research_only": True,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "statistical_evaluation_performed": False,
        "normalization_performed": False,
        "fixture_discovery_performed": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "paid_subscription_used": False,
        "source_lock_workflow_run_id": EXPECTED_LOCK_RUN_ID,
        "source_lock_artifact_id": EXPECTED_LOCK_ARTIFACT_ID,
        "source_lock_artifact_digest": EXPECTED_LOCK_ARTIFACT_DIGEST,
        "source_plan_workflow_run_id": EXPECTED_PLAN_RUN_ID,
        "source_plan_artifact_id": EXPECTED_PLAN_ARTIFACT_ID,
        "source_plan_artifact_digest": EXPECTED_PLAN_ARTIFACT_DIGEST,
        "source_selection_sha256": lock_manifest["selection_sha256"],
        "source_fixture_metadata_sha256": lock_manifest["fixture_metadata_sha256"],
        "batch_index": batch_index,
        "batch_target_fixture_ids": target_ids,
        "batch_planned_fixture_requests": len(target_ids),
        "fetched_fixture_ids_this_run": fetched_ids,
        "fetched_fixture_count_this_run": len(fetched_ids),
        "provider_http_requests_this_run": int(provider_requests),
        "captured_locked_raw_responses": len(raw_by_id),
        "locked_fixture_count": len(selected_ids),
        "missing_locked_fixture_ids": missing,
        "missing_locked_fixture_count": len(missing),
    }


def acquire_batch(
    lock_manifest: dict[str, Any],
    acquisition_plan: dict[str, Any],
    *,
    batch_index: int,
    output_dir: Path,
    key: str,
    resume_zip: Path | None = None,
) -> dict[str, Any]:
    validate_lock_and_plan(lock_manifest, acquisition_plan)

    if batch_index not in {1, 2}:
        raise ValueError("batch_index must be 1 or 2")
    if batch_index == 2 and resume_zip is None:
        raise RuntimeError("batch 2 requires a resume artifact from the same locked cohort")

    selected_ids = [str(value) for value in lock_manifest["selected_fixture_ids"]]
    target_ids = [
        str(value)
        for value in acquisition_plan["batches"][batch_index - 1]["fixture_ids"]
    ]
    if len(target_ids) > odds_plan.MAX_ODDS_REQUESTS_PER_BATCH:
        raise RuntimeError("target batch exceeds frozen 30-fixture cap")

    raw_by_id = load_resume_raw(resume_zip, selected_ids=selected_ids)
    target_missing = [fixture_id for fixture_id in target_ids if fixture_id not in raw_by_id]

    output_dir.mkdir(parents=True, exist_ok=True)
    for fixture_id, payload in raw_by_id.items():
        _write_json(output_dir / "raw" / "odds" / f"{fixture_id}.json", payload)

    client = replication.ProviderClient(key=key)
    fetched_ids: list[str] = []

    try:
        for fixture_id in target_missing:
            payload = client.get(
                f"/v1/fixtures/{fixture_id}/odds",
                params={"market": "corner"},
            )
            raw_by_id[fixture_id] = payload
            fetched_ids.append(fixture_id)
            _write_json(output_dir / "raw" / "odds" / f"{fixture_id}.json", payload)
    except Exception as exc:
        report = _base_report(
            lock_manifest=lock_manifest,
            acquisition_plan=acquisition_plan,
            batch_index=batch_index,
            raw_by_id=raw_by_id,
            fetched_ids=fetched_ids,
            provider_requests=client.request_count,
        )
        report.update(
            {
                "status": "ACQUISITION_INTERRUPTED",
                "acquisition_complete": False,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
        )
        _write_json(output_dir / "report.json", report)
        raise

    report = _base_report(
        lock_manifest=lock_manifest,
        acquisition_plan=acquisition_plan,
        batch_index=batch_index,
        raw_by_id=raw_by_id,
        fetched_ids=fetched_ids,
        provider_requests=client.request_count,
    )
    complete = report["missing_locked_fixture_count"] == 0
    report.update(
        {
            "status": "ACQUISITION_COMPLETE" if complete else "ACQUISITION_PARTIAL",
            "acquisition_complete": bool(complete),
        }
    )
    _write_json(output_dir / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock-manifest", type=Path, required=True)
    parser.add_argument("--acquisition-plan", type=Path, required=True)
    parser.add_argument("--batch-index", type=int, choices=(1, 2), required=True)
    parser.add_argument("--resume-zip", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/corner_regime_adjusted_direction_v2b_acquisition"),
    )
    args = parser.parse_args()

    report = acquire_batch(
        load_json_object(args.lock_manifest, label="lock manifest"),
        load_json_object(args.acquisition_plan, label="acquisition plan"),
        batch_index=args.batch_index,
        output_dir=args.output_dir,
        key=replication._require_key(),
        resume_zip=args.resume_zip,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
