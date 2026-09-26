"""Offline immutable cohort lock for CORNER_REGIME_ADJUSTED_DIRECTION_V2B."""
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
import corner_regime_adjusted_direction_v2b as v2b

LOCK_EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V2B_COHORT_LOCK"
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


def _read_exact_json_member(zf: zipfile.ZipFile, suffix: str) -> Any:
    names = [name for name in zf.namelist() if name.endswith(suffix)]
    if len(names) != 1:
        raise RuntimeError(
            f"V2B artifact must contain exactly one {suffix}, got {len(names)}"
        )
    return json.loads(zf.read(names[0]).decode("utf-8"))


def load_v2b_artifact(
    artifact_zip: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with zipfile.ZipFile(artifact_zip) as zf:
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
    match = _SHA256_RE.fullmatch(str(value).strip())
    if not match:
        raise ValueError("source artifact digest must be a SHA-256 hex digest")
    return "sha256:" + match.group(1).lower()


def validate_v2b_plan(plan: dict[str, Any]) -> None:
    required_exact = {
        "experiment_id": v2b.EXPERIMENT_ID,
        "source_experiment_id": v2b.SOURCE_EXPERIMENT_ID,
        "source_metadata_experiment_id": v2b.SOURCE_METADATA_EXPERIMENT_ID,
        "research_only": True,
        "metadata_only": True,
        "post_metadata_pre_odds_amendment": True,
        "odds_endpoint_used": False,
        "market_prices_opened": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "paid_subscription_used": False,
        "future_cutoff_utc": v2b.FUTURE_CUTOFF_UTC,
        "total_prior_excluded_fixture_ids": v2b.EXPECTED_PRIOR_EXCLUDED_IDS,
        "status": "COHORT_LOCKED",
        "locked": True,
    }
    for key, expected in required_exact.items():
        if plan.get(key) != expected:
            raise RuntimeError(
                f"V2B plan mismatch for {key}: expected {expected!r}, "
                f"got {plan.get(key)!r}"
            )

    expected_gate = {
        "minimum_blocks_per_league": v2b.MIN_BLOCKS_PER_LEAGUE,
        "minimum_total_blocks": v2b.MIN_TOTAL_BLOCKS,
        "minimum_metadata_potential_pairs": v2b.MIN_METADATA_POTENTIAL_PAIRS,
    }
    if plan.get("cohort_lock_gate") != expected_gate:
        raise RuntimeError("V2B cohort lock gate mismatch")

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
    if plan.get("statistical_gate_unchanged_from_v1") != expected_stat_gate:
        raise RuntimeError("V2B statistical gate mismatch")

    candidate_blocks = plan.get("candidate_blocks")
    if not isinstance(candidate_blocks, list):
        raise RuntimeError("V2B candidate_blocks must be a list")

    expected = v2b._prefix_status(candidate_blocks)
    if expected.get("status") != "COHORT_LOCKED":
        raise RuntimeError("candidate blocks do not satisfy V2B 10/74 gate")

    for key in (
        "selected_blocks",
        "selected_block_count",
        "selected_fixture_ids",
        "selected_fixture_count",
        "metadata_potential_pairs",
        "blocks_by_league",
    ):
        if plan.get(key) != expected.get(key):
            raise RuntimeError(
                f"V2B selected cohort differs from deterministic earliest prefix: {key}"
            )

    selected_ids = [str(value) for value in plan["selected_fixture_ids"]]
    concatenated = [
        str(fid)
        for block in plan["selected_blocks"]
        for fid in block["fixture_ids"]
    ]
    if selected_ids != concatenated:
        raise RuntimeError("selected fixture IDs differ from whole-block concatenation")
    if len(selected_ids) != len(set(selected_ids)):
        raise RuntimeError("selected fixture IDs contain duplicates")


def selected_fixture_metadata(
    plan: dict[str, Any],
    fixture_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    validate_v2b_plan(plan)

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

    cutoff = pd.Timestamp(v2b.FUTURE_CUTOFF_UTC)
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
            raise RuntimeError(f"{fixture_id}: unsupported league {league}")
        if league_id != str(replication.LEAGUES[league]):
            raise RuntimeError(f"{fixture_id}: fixture metadata league_id mismatch")
        if pd.isna(kickoff) or kickoff < cutoff:
            raise RuntimeError(f"{fixture_id}: invalid or pre-cutoff kickoff")
        if kickoff.strftime("%Y-%m-%d") != str(block["kickoff_date_utc"]):
            raise RuntimeError(f"{fixture_id}: kickoff date does not match selected block")
        if not home or not away:
            raise RuntimeError(f"{fixture_id}: missing home/away metadata")

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
    source_metadata_workflow_run_id: str,
    source_metadata_artifact_id: str,
    source_metadata_artifact_digest: str,
) -> dict[str, Any]:
    validate_v2b_plan(plan)
    frozen_metadata = selected_fixture_metadata(plan, fixture_rows)

    run_id = str(source_metadata_workflow_run_id).strip()
    artifact_id = str(source_metadata_artifact_id).strip()
    if not run_id or not artifact_id:
        raise ValueError("source metadata run/artifact IDs are required")
    artifact_digest = _normalize_digest(source_metadata_artifact_digest)

    lock_gate = {
        "minimum_blocks_per_league": v2b.MIN_BLOCKS_PER_LEAGUE,
        "minimum_total_blocks": v2b.MIN_TOTAL_BLOCKS,
        "minimum_metadata_potential_pairs": v2b.MIN_METADATA_POTENTIAL_PAIRS,
    }
    identity = {
        "future_cutoff_utc": v2b.FUTURE_CUTOFF_UTC,
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
        "source_metadata_workflow_run_id": run_id,
        "source_metadata_artifact_id": artifact_id,
        "source_metadata_artifact_digest": artifact_digest,
        "research_only": True,
        "offline_only": True,
        "immutable": True,
        "post_metadata_pre_odds_amendment": True,
        "lock_status": "IMMUTABLE_COHORT_LOCKED",
        "odds_acquisition_authorized": False,
        "betting_enabled": False,
        "production_promotion_authorized": False,
        "future_cutoff_utc": v2b.FUTURE_CUTOFF_UTC,
        "prior_excluded_fixture_ids": v2b.EXPECTED_PRIOR_EXCLUDED_IDS,
        "cohort_lock_gate": lock_gate,
        "statistical_gate_unchanged_from_v1": plan[
            "statistical_gate_unchanged_from_v1"
        ],
        "selected_blocks": plan["selected_blocks"],
        "selected_block_count": int(plan["selected_block_count"]),
        "selected_fixture_ids": plan["selected_fixture_ids"],
        "selected_fixture_count": int(plan["selected_fixture_count"]),
        "selected_fixture_metadata": frozen_metadata,
        "metadata_potential_pairs": int(plan["metadata_potential_pairs"]),
        "blocks_by_league": plan["blocks_by_league"],
        "fixture_metadata_sha256": fixture_metadata_sha256,
        "selection_sha256": selection_sha256,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v2b-artifact-zip", type=Path, required=True)
    parser.add_argument("--source-metadata-workflow-run-id", required=True)
    parser.add_argument("--source-metadata-artifact-id", required=True)
    parser.add_argument("--source-metadata-artifact-digest", required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/corner_regime_adjusted_direction_v2b_lock/cohort_lock.json"),
    )
    args = parser.parse_args()

    plan, fixture_rows = load_v2b_artifact(args.v2b_artifact_zip)
    manifest = build_lock_manifest(
        plan,
        fixture_rows,
        source_metadata_workflow_run_id=args.source_metadata_workflow_run_id,
        source_metadata_artifact_id=args.source_metadata_artifact_id,
        source_metadata_artifact_digest=args.source_metadata_artifact_digest,
    )
    _write_json(args.output, manifest)
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
