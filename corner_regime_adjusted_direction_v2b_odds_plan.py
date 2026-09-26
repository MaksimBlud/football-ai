"""Offline deterministic acquisition-plan builder for V2B.

Consumes only the immutable V2B cohort lock. Performs no provider/network I/O.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import corner_regime_adjusted_direction_v2b as v2b
import corner_regime_adjusted_direction_v2b_lock as lock

PLAN_EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V2B_ODDS_PLAN"
MAX_ODDS_REQUESTS_PER_BATCH = 30
EXPECTED_SELECTED_FIXTURES = 43
EXPECTED_SELECTED_BLOCKS = 10
EXPECTED_METADATA_POTENTIAL_PAIRS = 74
EXPECTED_SELECTION_SHA256 = (
    "sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73"
)
EXPECTED_FIXTURE_METADATA_SHA256 = (
    "sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb"
)
_SHA256_RE = re.compile(r"^(?:sha256:)?([0-9a-fA-F]{64})$")


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


def _normalize_digest(value: str) -> str:
    match = _SHA256_RE.fullmatch(str(value).strip())
    if not match:
        raise ValueError("lock artifact digest must be a SHA-256 hex digest")
    return "sha256:" + match.group(1).lower()


def load_lock_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("V2B cohort lock manifest must be a JSON object")
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
        "source_experiment_id": v2b.EXPERIMENT_ID,
        "lock_status": "IMMUTABLE_COHORT_LOCKED",
        "research_only": True,
        "offline_only": True,
        "immutable": True,
        "post_metadata_pre_odds_amendment": True,
        "odds_acquisition_authorized": False,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "future_cutoff_utc": v2b.FUTURE_CUTOFF_UTC,
        "prior_excluded_fixture_ids": v2b.EXPECTED_PRIOR_EXCLUDED_IDS,
        "selected_block_count": EXPECTED_SELECTED_BLOCKS,
        "selected_fixture_count": EXPECTED_SELECTED_FIXTURES,
        "metadata_potential_pairs": EXPECTED_METADATA_POTENTIAL_PAIRS,
    }
    for key, expected in expected_exact.items():
        if manifest.get(key) != expected:
            raise RuntimeError(
                f"V2B lock mismatch for {key}: "
                f"expected {expected!r}, got {manifest.get(key)!r}"
            )

    expected_gate = {
        "minimum_blocks_per_league": v2b.MIN_BLOCKS_PER_LEAGUE,
        "minimum_total_blocks": v2b.MIN_TOTAL_BLOCKS,
        "minimum_metadata_potential_pairs": v2b.MIN_METADATA_POTENTIAL_PAIRS,
    }
    if manifest.get("cohort_lock_gate") != expected_gate:
        raise RuntimeError("V2B cohort gate mismatch")

    expected_stat_gate = {
        "minimum_total_rows": v2b.MIN_TOTAL_ROWS,
        "minimum_leagues_with_pairs": v2b.MIN_LEAGUES_WITH_PAIRS,
        "minimum_regime_blocks": v2b.MIN_REGIME_BLOCKS,
        "minimum_comparable_pairs": v2b.MIN_COMPARABLE_PAIRS,
        "minimum_concordance": v2b.MIN_CONCORDANCE,
        "permutations": v2b.PERMUTATIONS,
        "permutation_seed": v2b.PERMUTATION_SEED,
        "maximum_pvalue": v2b.MAX_PVALUE,
    }
    if manifest.get("statistical_gate_unchanged_from_v1") != expected_stat_gate:
        raise RuntimeError("V2B statistical gate mismatch")

    selected_blocks = manifest.get("selected_blocks")
    selected_ids = manifest.get("selected_fixture_ids")
    selected_metadata = manifest.get("selected_fixture_metadata")
    if not isinstance(selected_blocks, list):
        raise RuntimeError("selected_blocks must be a list")
    if not isinstance(selected_ids, list):
        raise RuntimeError("selected_fixture_ids must be a list")
    if not isinstance(selected_metadata, list):
        raise RuntimeError("selected_fixture_metadata must be a list")

    normalized_ids = [str(value) for value in selected_ids]
    ordered_block_ids = [
        str(fid)
        for block in selected_blocks
        for fid in block.get("fixture_ids", [])
    ]
    metadata_ids = [str(row.get("fixture_id") or "") for row in selected_metadata]

    if normalized_ids != ordered_block_ids:
        raise RuntimeError("locked fixture IDs differ from whole-block order")
    if normalized_ids != metadata_ids:
        raise RuntimeError("locked fixture metadata order differs from fixture IDs")
    if len(normalized_ids) != len(set(normalized_ids)):
        raise RuntimeError("locked fixture IDs contain duplicates")

    if manifest.get("selection_sha256") != EXPECTED_SELECTION_SHA256:
        raise RuntimeError("V2B selection hash differs from expected immutable lock")
    if manifest.get("fixture_metadata_sha256") != EXPECTED_FIXTURE_METADATA_SHA256:
        raise RuntimeError("V2B fixture metadata hash differs from expected immutable lock")

    if _expected_selection_hash(manifest) != manifest["selection_sha256"]:
        raise RuntimeError("V2B selection_sha256 recomputation mismatch")
    if _expected_fixture_metadata_hash(manifest) != manifest["fixture_metadata_sha256"]:
        raise RuntimeError("V2B fixture_metadata_sha256 recomputation mismatch")


def build_acquisition_plan(
    manifest: dict[str, Any],
    *,
    source_lock_workflow_run_id: str,
    source_lock_artifact_id: str,
    source_lock_artifact_digest: str,
) -> dict[str, Any]:
    validate_lock_manifest(manifest)

    run_id = str(source_lock_workflow_run_id).strip()
    artifact_id = str(source_lock_artifact_id).strip()
    if not run_id or not artifact_id:
        raise ValueError("source lock workflow run/artifact IDs are required")
    artifact_digest = _normalize_digest(source_lock_artifact_digest)

    selected_ids = [str(value) for value in manifest["selected_fixture_ids"]]
    selected_metadata = list(manifest["selected_fixture_metadata"])

    batches: list[dict[str, Any]] = []
    for start in range(0, len(selected_ids), MAX_ODDS_REQUESTS_PER_BATCH):
        fixture_ids = selected_ids[start : start + MAX_ODDS_REQUESTS_PER_BATCH]
        fixture_metadata = selected_metadata[
            start : start + MAX_ODDS_REQUESTS_PER_BATCH
        ]
        batches.append(
            {
                "batch_index": len(batches) + 1,
                "fixture_ids": fixture_ids,
                "fixture_metadata": fixture_metadata,
                "planned_requests": len(fixture_ids),
            }
        )

    flattened_ids = [
        fixture_id for batch in batches for fixture_id in batch["fixture_ids"]
    ]
    flattened_metadata = [
        row for batch in batches for row in batch["fixture_metadata"]
    ]
    if flattened_ids != selected_ids:
        raise RuntimeError("deterministic batching changed fixture membership/order")
    if flattened_metadata != selected_metadata:
        raise RuntimeError("deterministic batching changed fixture metadata order")

    if [batch["planned_requests"] for batch in batches] != [30, 13]:
        raise RuntimeError("V2B expected deterministic 30+13 batching")

    return {
        "plan_experiment_id": PLAN_EXPERIMENT_ID,
        "source_lock_experiment_id": manifest["lock_experiment_id"],
        "source_lock_status": manifest["lock_status"],
        "source_lock_workflow_run_id": run_id,
        "source_lock_artifact_id": artifact_id,
        "source_lock_artifact_digest": artifact_digest,
        "source_selection_sha256": manifest["selection_sha256"],
        "source_fixture_metadata_sha256": manifest["fixture_metadata_sha256"],
        "research_only": True,
        "offline_only": True,
        "post_metadata_pre_odds_amendment": True,
        "live_odds_acquisition_authorized": False,
        "requires_explicit_live_authorization": True,
        "fixture_reselection_allowed": False,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "future_cutoff_utc": manifest["future_cutoff_utc"],
        "selected_fixture_count": len(selected_ids),
        "selected_fixture_ids": selected_ids,
        "selected_fixture_metadata": selected_metadata,
        "max_odds_requests_per_batch": MAX_ODDS_REQUESTS_PER_BATCH,
        "total_planned_odds_requests": len(selected_ids),
        "batch_count": len(batches),
        "batches": batches,
        "resume_rule": "REQUEST_ONLY_MISSING_IDS_FROM_SAME_LOCKED_COHORT",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock-manifest", type=Path, required=True)
    parser.add_argument("--source-lock-workflow-run-id", required=True)
    parser.add_argument("--source-lock-artifact-id", required=True)
    parser.add_argument("--source-lock-artifact-digest", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/corner_regime_adjusted_direction_v2b_odds_plan/"
            "acquisition_plan.json"
        ),
    )
    args = parser.parse_args()

    plan = build_acquisition_plan(
        load_lock_manifest(args.lock_manifest),
        source_lock_workflow_run_id=args.source_lock_workflow_run_id,
        source_lock_artifact_id=args.source_lock_artifact_id,
        source_lock_artifact_digest=args.source_lock_artifact_digest,
    )
    _write_json(args.output, plan)
    print(json.dumps(plan, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
