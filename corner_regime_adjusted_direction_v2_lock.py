"""Offline immutable cohort-lock validator for CORNER_REGIME_ADJUSTED_DIRECTION_V2.

This module accepts only a previously captured metadata artifact. It performs no
network I/O and never authorizes odds acquisition.
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
import corner_regime_adjusted_direction_v2 as v2
import corner_regime_adjusted_direction_v2_metadata as metadata

LOCK_EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V2_COHORT_LOCK"
EXPECTED_PRIOR_EXCLUDED_IDS = 151
_SHA256_RE = re.compile(r"^(?:sha256:)?([0-9a-fA-F]{64})$")
_METADATA_FIELDS = (
    "fixture_id",
    "league",
    "league_id",
    "kickoff_utc",
    "home_team",
    "away_team",
)


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


def _read_exact_json_member(zf: zipfile.ZipFile, suffix: str) -> Any:
    names = [name for name in zf.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise RuntimeError(
            f"metadata artifact must contain exactly one {suffix}, got {len(names)}"
        )
    return json.loads(zf.read(names[0]).decode("utf-8"))


def load_cohort_plan(metadata_zip: Path) -> dict[str, Any]:
    """Compatibility helper that reads only the cohort plan."""
    with zipfile.ZipFile(metadata_zip) as zf:
        payload = _read_exact_json_member(zf, "cohort_plan.json")
    if not isinstance(payload, dict):
        raise RuntimeError("cohort_plan.json must contain a JSON object")
    return payload


def load_metadata_artifact(
    metadata_zip: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with zipfile.ZipFile(metadata_zip) as zf:
        plan = _read_exact_json_member(zf, "cohort_plan.json")
        fixture_rows = _read_exact_json_member(zf, "future_fixture_metadata.json")

    if not isinstance(plan, dict):
        raise RuntimeError("cohort_plan.json must contain a JSON object")
    if not isinstance(fixture_rows, list) or not all(
        isinstance(row, dict) for row in fixture_rows
    ):
        raise RuntimeError("future_fixture_metadata.json must contain a list of objects")
    return plan, fixture_rows


def _normalize_digest(value: str) -> str:
    match = _SHA256_RE.fullmatch(value.strip())
    if not match:
        raise ValueError("source artifact digest must be a SHA-256 hex digest")
    return "sha256:" + match.group(1).lower()


def _validate_block(block: Any) -> None:
    if not isinstance(block, dict):
        raise RuntimeError("candidate block must be an object")

    league = str(block.get("league") or "")
    date = str(block.get("kickoff_date_utc") or "")
    regime_block = str(block.get("regime_block") or "")
    fixture_ids = block.get("fixture_ids")
    fixture_count = block.get("fixture_count")
    potential_pairs = block.get("potential_pairs")

    if league not in v2.LEAGUE_ORDER:
        raise RuntimeError(f"unexpected block league {league}")
    if regime_block != f"{league}|{date}":
        raise RuntimeError(f"invalid regime block identity {regime_block}")
    if not isinstance(fixture_ids, list) or not fixture_ids:
        raise RuntimeError(f"{regime_block}: fixture_ids must be a non-empty list")

    ids = [str(value).strip() for value in fixture_ids]
    if any(not value for value in ids):
        raise RuntimeError(f"{regime_block}: empty fixture ID")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"{regime_block}: duplicate fixture IDs")

    n = len(ids)
    if int(fixture_count) != n:
        raise RuntimeError(f"{regime_block}: fixture_count mismatch")
    if int(potential_pairs) != n * (n - 1) // 2:
        raise RuntimeError(f"{regime_block}: potential_pairs mismatch")


def _validate_frozen_contract(plan: dict[str, Any]) -> None:
    if plan.get("status") != "COHORT_LOCKED" or plan.get("locked") is not True:
        raise RuntimeError("source metadata plan is not COHORT_LOCKED")

    required_exact = {
        "experiment_id": v2.EXPERIMENT_ID,
        "metadata_live_experiment_id": metadata.EXPERIMENT_ID,
        "research_only": True,
        "metadata_only": True,
        "odds_endpoint_used": False,
        "market_prices_opened": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "paid_subscription_used": False,
        "future_cutoff_utc": v2.FUTURE_CUTOFF_UTC,
        "total_prior_excluded_fixture_ids": EXPECTED_PRIOR_EXCLUDED_IDS,
    }
    for key, expected in required_exact.items():
        if plan.get(key) != expected:
            raise RuntimeError(
                f"source metadata contract mismatch for {key}: "
                f"expected {expected!r}, got {plan.get(key)!r}"
            )

    expected_lock_gate = {
        "minimum_blocks_per_league": v2.MIN_BLOCKS_PER_LEAGUE,
        "minimum_total_blocks": v2.MIN_TOTAL_BLOCKS,
        "minimum_metadata_potential_pairs": v2.MIN_METADATA_POTENTIAL_PAIRS,
    }
    if plan.get("cohort_lock_gate") != expected_lock_gate:
        raise RuntimeError("source metadata cohort-lock gate differs from frozen V2")

    expected_statistical_gate = {
        "minimum_total_rows": v2.MIN_TOTAL_ROWS,
        "minimum_leagues_with_pairs": v2.MIN_LEAGUES_WITH_PAIRS,
        "minimum_regime_blocks": v2.MIN_REGIME_BLOCKS,
        "minimum_comparable_pairs": v2.MIN_COMPARABLE_PAIRS,
        "minimum_concordance": v2.MIN_CONCORDANCE,
        "permutations": v2.PERMUTATIONS,
        "permutation_seed": v2.PERMUTATION_SEED,
        "maximum_pvalue": v2.MAX_PVALUE,
    }
    if plan.get("statistical_gate_unchanged_from_v1") != expected_statistical_gate:
        raise RuntimeError("source statistical gate differs from frozen V1/V2 contract")


def validate_locked_plan(plan: dict[str, Any]) -> dict[str, Any]:
    _validate_frozen_contract(plan)

    candidate_blocks = plan.get("candidate_blocks")
    if not isinstance(candidate_blocks, list):
        raise RuntimeError("candidate_blocks must be a list")
    for block in candidate_blocks:
        _validate_block(block)

    all_candidate_ids: list[str] = []
    for block in candidate_blocks:
        all_candidate_ids.extend(str(fid) for fid in block["fixture_ids"])
    if len(all_candidate_ids) != len(set(all_candidate_ids)):
        raise RuntimeError("candidate blocks contain duplicate fixture IDs")

    expected = v2._prefix_status(candidate_blocks)
    if expected.get("status") != "COHORT_LOCKED":
        raise RuntimeError("candidate_blocks do not satisfy frozen cohort-lock gate")

    exact_keys = (
        "selected_blocks",
        "selected_block_count",
        "selected_fixture_ids",
        "selected_fixture_count",
        "metadata_potential_pairs",
        "blocks_by_league",
    )
    for key in exact_keys:
        if plan.get(key) != expected.get(key):
            raise RuntimeError(
                f"source selected cohort is not the deterministic earliest prefix: {key}"
            )

    selected_blocks = plan["selected_blocks"]
    selected_fixture_ids = [str(value) for value in plan["selected_fixture_ids"]]
    concatenated_ids = [
        str(fid)
        for block in selected_blocks
        for fid in block["fixture_ids"]
    ]
    if selected_fixture_ids != concatenated_ids:
        raise RuntimeError(
            "selected_fixture_ids do not exactly equal ordered whole-block fixture IDs"
        )
    if len(selected_fixture_ids) != len(set(selected_fixture_ids)):
        raise RuntimeError("selected cohort contains duplicate fixture IDs")

    return expected


def selected_fixture_metadata(
    plan: dict[str, Any],
    fixture_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return exact selected fixture metadata in frozen fixture-ID order."""
    validate_locked_plan(plan)

    selected_ids = [str(value) for value in plan["selected_fixture_ids"]]
    block_by_id: dict[str, dict[str, Any]] = {}
    for block in plan["selected_blocks"]:
        for fixture_id in block["fixture_ids"]:
            key = str(fixture_id)
            if key in block_by_id:
                raise RuntimeError(f"selected fixture {key} appears in multiple blocks")
            block_by_id[key] = block

    metadata_by_id: dict[str, dict[str, Any]] = {}
    for raw in fixture_rows:
        fixture_id = str(raw.get("fixture_id") or "").strip()
        if not fixture_id:
            continue
        if fixture_id in metadata_by_id:
            raise RuntimeError(f"duplicate fixture metadata for {fixture_id}")
        metadata_by_id[fixture_id] = raw

    missing = [fixture_id for fixture_id in selected_ids if fixture_id not in metadata_by_id]
    if missing:
        raise RuntimeError(
            "selected fixture metadata missing for IDs: " + ",".join(missing[:10])
        )

    cutoff = pd.Timestamp(v2.FUTURE_CUTOFF_UTC)
    frozen_rows: list[dict[str, Any]] = []
    for fixture_id in selected_ids:
        raw = metadata_by_id[fixture_id]
        block = block_by_id[fixture_id]
        league = str(raw.get("league") or "").strip()
        league_id = str(raw.get("league_id") or "").strip()
        kickoff = pd.to_datetime(raw.get("kickoff_utc"), utc=True, errors="coerce")
        home = str(raw.get("home_team") or "").strip()
        away = str(raw.get("away_team") or "").strip()

        if not fixture_id.isdigit():
            raise RuntimeError(f"selected fixture ID is not numeric: {fixture_id}")
        if league != str(block["league"]):
            raise RuntimeError(f"{fixture_id}: fixture metadata league mismatch")
        if league not in replication.LEAGUES:
            raise RuntimeError(f"{fixture_id}: unsupported fixture metadata league {league}")
        if league_id != str(replication.LEAGUES[league]):
            raise RuntimeError(f"{fixture_id}: fixture metadata league_id mismatch")
        if pd.isna(kickoff) or kickoff < cutoff:
            raise RuntimeError(f"{fixture_id}: invalid or pre-cutoff kickoff_utc")
        if kickoff.strftime("%Y-%m-%d") != str(block["kickoff_date_utc"]):
            raise RuntimeError(f"{fixture_id}: kickoff date does not match selected block")
        if not home or not away:
            raise RuntimeError(f"{fixture_id}: missing home/away fixture metadata")

        frozen_rows.append(
            {
                "fixture_id": fixture_id,
                "league": league,
                "league_id": league_id,
                "kickoff_utc": kickoff.isoformat(),
                "home_team": home,
                "away_team": away,
            }
        )

    return frozen_rows


def build_lock_manifest(
    plan: dict[str, Any],
    fixture_rows: list[dict[str, Any]],
    *,
    source_run_id: str,
    source_artifact_id: str,
    source_artifact_digest: str,
) -> dict[str, Any]:
    validate_locked_plan(plan)
    frozen_metadata = selected_fixture_metadata(plan, fixture_rows)

    digest = _normalize_digest(source_artifact_digest)
    run_id = str(source_run_id).strip()
    artifact_id = str(source_artifact_id).strip()
    if not run_id or not artifact_id:
        raise ValueError("source run ID and artifact ID are required")

    lock_gate = {
        "minimum_blocks_per_league": v2.MIN_BLOCKS_PER_LEAGUE,
        "minimum_total_blocks": v2.MIN_TOTAL_BLOCKS,
        "minimum_metadata_potential_pairs": v2.MIN_METADATA_POTENTIAL_PAIRS,
    }
    identity = {
        "future_cutoff_utc": v2.FUTURE_CUTOFF_UTC,
        "cohort_lock_gate": lock_gate,
        "selected_blocks": plan["selected_blocks"],
        "selected_fixture_ids": plan["selected_fixture_ids"],
        "selected_fixture_metadata": frozen_metadata,
    }
    selection_sha256 = "sha256:" + hashlib.sha256(
        _canonical_json_bytes(identity)
    ).hexdigest()
    fixture_metadata_sha256 = "sha256:" + hashlib.sha256(
        _canonical_json_bytes(frozen_metadata)
    ).hexdigest()

    return {
        "lock_experiment_id": LOCK_EXPERIMENT_ID,
        "source_experiment_id": plan["experiment_id"],
        "source_metadata_experiment_id": plan["metadata_live_experiment_id"],
        "source_workflow_run_id": run_id,
        "source_artifact_id": artifact_id,
        "source_artifact_digest": digest,
        "research_only": True,
        "offline_only": True,
        "immutable": True,
        "lock_status": "IMMUTABLE_COHORT_LOCKED",
        "odds_acquisition_authorized": False,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "future_cutoff_utc": v2.FUTURE_CUTOFF_UTC,
        "prior_excluded_fixture_ids": EXPECTED_PRIOR_EXCLUDED_IDS,
        "cohort_lock_gate": lock_gate,
        "statistical_gate_unchanged_from_v1": plan[
            "statistical_gate_unchanged_from_v1"
        ],
        "selected_blocks": plan["selected_blocks"],
        "selected_block_count": int(plan["selected_block_count"]),
        "selected_fixture_ids": plan["selected_fixture_ids"],
        "selected_fixture_count": int(plan["selected_fixture_count"]),
        "selected_fixture_metadata": frozen_metadata,
        "fixture_metadata_sha256": fixture_metadata_sha256,
        "metadata_potential_pairs": int(plan["metadata_potential_pairs"]),
        "blocks_by_league": plan["blocks_by_league"],
        "selection_sha256": selection_sha256,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-zip", type=Path, required=True)
    parser.add_argument("--source-run-id", required=True)
    parser.add_argument("--source-artifact-id", required=True)
    parser.add_argument("--source-artifact-digest", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/corner_regime_adjusted_direction_v2_lock/cohort_lock.json"
        ),
    )
    args = parser.parse_args()

    plan, fixture_rows = load_metadata_artifact(args.metadata_zip)
    manifest = build_lock_manifest(
        plan,
        fixture_rows,
        source_run_id=args.source_run_id,
        source_artifact_id=args.source_artifact_id,
        source_artifact_digest=args.source_artifact_digest,
    )
    _write_json(args.output, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
