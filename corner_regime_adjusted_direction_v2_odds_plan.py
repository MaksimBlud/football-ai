"""Offline acquisition-plan builder for CORNER_REGIME_ADJUSTED_DIRECTION_V2.

Consumes only an immutable cohort-lock manifest. Performs no network I/O and
does not authorize live odds acquisition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import corner_regime_adjusted_direction_v2 as v2
import corner_regime_adjusted_direction_v2_lock as lock

PLAN_EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V2_ODDS_PLAN"
MAX_ODDS_REQUESTS_PER_RUN = 30


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_lock_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("cohort lock manifest must be a JSON object")
    return payload


def _expected_selection_hash(manifest: dict[str, Any]) -> str:
    identity = {
        "future_cutoff_utc": manifest.get("future_cutoff_utc"),
        "cohort_lock_gate": manifest.get("cohort_lock_gate"),
        "selected_blocks": manifest.get("selected_blocks"),
        "selected_fixture_ids": manifest.get("selected_fixture_ids"),
        "selected_fixture_metadata": manifest.get("selected_fixture_metadata"),
    }
    return "sha256:" + hashlib.sha256(_canonical_json_bytes(identity)).hexdigest()


def _expected_fixture_metadata_hash(manifest: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(
        _canonical_json_bytes(manifest.get("selected_fixture_metadata"))
    ).hexdigest()


def validate_lock_manifest(manifest: dict[str, Any]) -> None:
    expected_exact = {
        "lock_experiment_id": lock.LOCK_EXPERIMENT_ID,
        "lock_status": "IMMUTABLE_COHORT_LOCKED",
        "research_only": True,
        "offline_only": True,
        "immutable": True,
        "odds_acquisition_authorized": False,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "future_cutoff_utc": v2.FUTURE_CUTOFF_UTC,
        "prior_excluded_fixture_ids": lock.EXPECTED_PRIOR_EXCLUDED_IDS,
    }
    for key, expected in expected_exact.items():
        if manifest.get(key) != expected:
            raise RuntimeError(
                f"lock manifest mismatch for {key}: "
                f"expected {expected!r}, got {manifest.get(key)!r}"
            )

    expected_lock_gate = {
        "minimum_blocks_per_league": v2.MIN_BLOCKS_PER_LEAGUE,
        "minimum_total_blocks": v2.MIN_TOTAL_BLOCKS,
        "minimum_metadata_potential_pairs": v2.MIN_METADATA_POTENTIAL_PAIRS,
    }
    if manifest.get("cohort_lock_gate") != expected_lock_gate:
        raise RuntimeError("cohort lock gate differs from frozen V2")

    expected_stat_gate = {
        "minimum_total_rows": v2.MIN_TOTAL_ROWS,
        "minimum_leagues_with_pairs": v2.MIN_LEAGUES_WITH_PAIRS,
        "minimum_regime_blocks": v2.MIN_REGIME_BLOCKS,
        "minimum_comparable_pairs": v2.MIN_COMPARABLE_PAIRS,
        "minimum_concordance": v2.MIN_CONCORDANCE,
        "permutations": v2.PERMUTATIONS,
        "permutation_seed": v2.PERMUTATION_SEED,
        "maximum_pvalue": v2.MAX_PVALUE,
    }
    if manifest.get("statistical_gate_unchanged_from_v1") != expected_stat_gate:
        raise RuntimeError("statistical gate differs from frozen V1/V2 contract")

    selected_blocks = manifest.get("selected_blocks")
    selected_ids = manifest.get("selected_fixture_ids")
    selected_metadata = manifest.get("selected_fixture_metadata")
    if not isinstance(selected_blocks, list) or not isinstance(selected_ids, list):
        raise RuntimeError("selected blocks and fixture IDs must be lists")
    if not isinstance(selected_metadata, list):
        raise RuntimeError("selected fixture metadata must be a list")

    ordered_block_ids = [
        str(fid)
        for block in selected_blocks
        for fid in block.get("fixture_ids", [])
    ]
    normalized_ids = [str(fid) for fid in selected_ids]
    metadata_ids = [str(row.get("fixture_id") or "") for row in selected_metadata]

    if normalized_ids != ordered_block_ids:
        raise RuntimeError(
            "selected fixture IDs do not equal ordered whole-block fixture IDs"
        )
    if normalized_ids != metadata_ids:
        raise RuntimeError(
            "selected fixture metadata does not match ordered selected fixture IDs"
        )
    if len(normalized_ids) != len(set(normalized_ids)):
        raise RuntimeError("selected fixture IDs contain duplicates")

    if int(manifest.get("selected_fixture_count", -1)) != len(normalized_ids):
        raise RuntimeError("selected fixture count mismatch")
    if int(manifest.get("selected_block_count", -1)) != len(selected_blocks):
        raise RuntimeError("selected block count mismatch")

    required_metadata_fields = {
        "fixture_id",
        "league",
        "league_id",
        "kickoff_utc",
        "home_team",
        "away_team",
    }
    for row in selected_metadata:
        if not isinstance(row, dict):
            raise RuntimeError("selected fixture metadata row must be an object")
        if not required_metadata_fields.issubset(row):
            raise RuntimeError("selected fixture metadata row is incomplete")

    expected_metadata_hash = _expected_fixture_metadata_hash(manifest)
    if manifest.get("fixture_metadata_sha256") != expected_metadata_hash:
        raise RuntimeError("fixture_metadata_sha256 mismatch")

    expected_hash = _expected_selection_hash(manifest)
    if manifest.get("selection_sha256") != expected_hash:
        raise RuntimeError("selection_sha256 mismatch")


def build_acquisition_plan(manifest: dict[str, Any]) -> dict[str, Any]:
    validate_lock_manifest(manifest)

    selected_ids = [str(fid) for fid in manifest["selected_fixture_ids"]]
    selected_metadata = list(manifest["selected_fixture_metadata"])
    batches = []
    for start in range(0, len(selected_ids), MAX_ODDS_REQUESTS_PER_RUN):
        fixture_ids = selected_ids[start : start + MAX_ODDS_REQUESTS_PER_RUN]
        fixture_metadata = selected_metadata[
            start : start + MAX_ODDS_REQUESTS_PER_RUN
        ]
        batches.append(
            {
                "batch_index": len(batches) + 1,
                "fixture_ids": fixture_ids,
                "fixture_metadata": fixture_metadata,
                "planned_requests": len(fixture_ids),
            }
        )

    flattened = [
        fixture_id
        for batch in batches
        for fixture_id in batch["fixture_ids"]
    ]
    flattened_metadata = [
        row
        for batch in batches
        for row in batch["fixture_metadata"]
    ]
    if flattened != selected_ids:
        raise RuntimeError("deterministic batching changed fixture order or membership")
    if flattened_metadata != selected_metadata:
        raise RuntimeError("deterministic batching changed fixture metadata order")

    return {
        "plan_experiment_id": PLAN_EXPERIMENT_ID,
        "source_lock_experiment_id": manifest["lock_experiment_id"],
        "source_lock_status": manifest["lock_status"],
        "source_selection_sha256": manifest["selection_sha256"],
        "source_fixture_metadata_sha256": manifest["fixture_metadata_sha256"],
        "source_workflow_run_id": manifest.get("source_workflow_run_id"),
        "source_artifact_id": manifest.get("source_artifact_id"),
        "source_artifact_digest": manifest.get("source_artifact_digest"),
        "research_only": True,
        "offline_only": True,
        "live_odds_acquisition_authorized": False,
        "requires_explicit_live_authorization": True,
        "fixture_reselection_allowed": False,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "future_cutoff_utc": manifest["future_cutoff_utc"],
        "selected_fixture_count": len(selected_ids),
        "selected_fixture_ids": selected_ids,
        "selected_fixture_metadata": selected_metadata,
        "max_odds_requests_per_run": MAX_ODDS_REQUESTS_PER_RUN,
        "total_planned_odds_requests": len(selected_ids),
        "batch_count": len(batches),
        "batches": batches,
        "resume_rule": "REQUEST_ONLY_MISSING_IDS_FROM_SAME_LOCKED_COHORT",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock-manifest", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/corner_regime_adjusted_direction_v2_odds_plan/"
            "acquisition_plan.json"
        ),
    )
    args = parser.parse_args()

    plan = build_acquisition_plan(load_lock_manifest(args.lock_manifest))
    _write_json(args.output, plan)
    print(json.dumps(plan, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
