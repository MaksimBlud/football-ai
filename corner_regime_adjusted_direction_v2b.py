"""Offline cohort replanner for CORNER_REGIME_ADJUSTED_DIRECTION_V2B.

V2B is a post-metadata / pre-odds operational amendment. It consumes an already
captured V2 metadata artifact and applies the explicitly revised 10-block /
74-potential-pair cohort gate. It performs no provider/network I/O.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

import corner_regime_adjusted_direction_v2 as v2

EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V2B"
SOURCE_EXPERIMENT_ID = v2.EXPERIMENT_ID
SOURCE_METADATA_EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V2_METADATA_LIVE"

FUTURE_CUTOFF_UTC = v2.FUTURE_CUTOFF_UTC
LEAGUE_ORDER = v2.LEAGUE_ORDER
MIN_FIXTURES_PER_BLOCK = v2.MIN_FIXTURES_PER_BLOCK
MIN_BLOCKS_PER_LEAGUE = 2
MIN_TOTAL_BLOCKS = 10
MIN_METADATA_POTENTIAL_PAIRS = 74
EXPECTED_PRIOR_EXCLUDED_IDS = 151

# Statistical direction gate is intentionally unchanged from V1/V2.
MIN_TOTAL_ROWS = v2.MIN_TOTAL_ROWS
MIN_LEAGUES_WITH_PAIRS = v2.MIN_LEAGUES_WITH_PAIRS
MIN_REGIME_BLOCKS = v2.MIN_REGIME_BLOCKS
MIN_COMPARABLE_PAIRS = v2.MIN_COMPARABLE_PAIRS
MIN_CONCORDANCE = v2.MIN_CONCORDANCE
PERMUTATIONS = v2.PERMUTATIONS
PERMUTATION_SEED = v2.PERMUTATION_SEED
MAX_PVALUE = v2.MAX_PVALUE


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


def load_source_metadata_artifact(
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


def validate_source_plan(plan: dict[str, Any]) -> None:
    required_exact = {
        "experiment_id": SOURCE_EXPERIMENT_ID,
        "metadata_live_experiment_id": SOURCE_METADATA_EXPERIMENT_ID,
        "research_only": True,
        "metadata_only": True,
        "odds_endpoint_used": False,
        "market_prices_opened": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "paid_subscription_used": False,
        "future_cutoff_utc": FUTURE_CUTOFF_UTC,
        "total_prior_excluded_fixture_ids": EXPECTED_PRIOR_EXCLUDED_IDS,
    }
    for key, expected in required_exact.items():
        if plan.get(key) != expected:
            raise RuntimeError(
                f"source metadata contract mismatch for {key}: "
                f"expected {expected!r}, got {plan.get(key)!r}"
            )

    if plan.get("status") not in {"WAIT_FOR_COHORT", "COHORT_LOCKED"}:
        raise RuntimeError("unexpected source metadata status")

    expected_stat_gate = {
        "minimum_total_rows": MIN_TOTAL_ROWS,
        "minimum_leagues_with_pairs": MIN_LEAGUES_WITH_PAIRS,
        "minimum_regime_blocks": MIN_REGIME_BLOCKS,
        "minimum_comparable_pairs": MIN_COMPARABLE_PAIRS,
        "minimum_concordance": MIN_CONCORDANCE,
        "permutations": PERMUTATIONS,
        "permutation_seed": PERMUTATION_SEED,
        "maximum_pvalue": MAX_PVALUE,
    }
    if plan.get("statistical_gate_unchanged_from_v1") != expected_stat_gate:
        raise RuntimeError("source statistical gate differs from frozen V1/V2 contract")

    blocks = plan.get("candidate_blocks")
    if not isinstance(blocks, list):
        raise RuntimeError("source candidate_blocks must be a list")

    seen_ids: set[str] = set()
    for block in blocks:
        if not isinstance(block, dict):
            raise RuntimeError("candidate block must be an object")
        league = str(block.get("league") or "")
        date = str(block.get("kickoff_date_utc") or "")
        regime_block = str(block.get("regime_block") or "")
        fixture_ids = block.get("fixture_ids")
        if league not in LEAGUE_ORDER:
            raise RuntimeError(f"unexpected candidate block league {league}")
        if regime_block != f"{league}|{date}":
            raise RuntimeError(f"invalid regime block identity {regime_block}")
        if not isinstance(fixture_ids, list) or len(fixture_ids) < MIN_FIXTURES_PER_BLOCK:
            raise RuntimeError(f"{regime_block}: insufficient fixture IDs")

        ids = [str(value).strip() for value in fixture_ids]
        if any(not value for value in ids):
            raise RuntimeError(f"{regime_block}: empty fixture ID")
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"{regime_block}: duplicate fixture IDs")
        if seen_ids.intersection(ids):
            raise RuntimeError("candidate blocks contain duplicate fixture IDs")
        seen_ids.update(ids)

        n = len(ids)
        if int(block.get("fixture_count", -1)) != n:
            raise RuntimeError(f"{regime_block}: fixture_count mismatch")
        if int(block.get("potential_pairs", -1)) != n * (n - 1) // 2:
            raise RuntimeError(f"{regime_block}: potential_pairs mismatch")


def _prefix_status(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {league: 0 for league in LEAGUE_ORDER}
    total_pairs = 0
    fixture_ids: list[str] = []

    for idx, block in enumerate(blocks):
        league = str(block["league"])
        counts[league] += 1
        total_pairs += int(block["potential_pairs"])
        fixture_ids.extend(str(value) for value in block["fixture_ids"])

        locked = (
            all(counts[league] >= MIN_BLOCKS_PER_LEAGUE for league in LEAGUE_ORDER)
            and idx + 1 >= MIN_TOTAL_BLOCKS
            and total_pairs >= MIN_METADATA_POTENTIAL_PAIRS
        )
        if locked:
            chosen = blocks[: idx + 1]
            return {
                "status": "COHORT_LOCKED",
                "locked": True,
                "selected_blocks": chosen,
                "selected_block_count": len(chosen),
                "selected_fixture_ids": fixture_ids,
                "selected_fixture_count": len(fixture_ids),
                "metadata_potential_pairs": int(total_pairs),
                "blocks_by_league": dict(counts),
            }

    total_counts = {league: 0 for league in LEAGUE_ORDER}
    total_pairs = 0
    for block in blocks:
        total_counts[str(block["league"])] += 1
        total_pairs += int(block["potential_pairs"])

    return {
        "status": "WAIT_FOR_COHORT",
        "locked": False,
        "selected_blocks": [],
        "selected_block_count": 0,
        "selected_fixture_ids": [],
        "selected_fixture_count": 0,
        "metadata_potential_pairs": int(total_pairs),
        "blocks_by_league": total_counts,
        "available_candidate_block_count": len(blocks),
        "available_candidate_fixture_count": sum(
            len(block["fixture_ids"]) for block in blocks
        ),
    }


def build_v2b_plan(source_plan: dict[str, Any]) -> dict[str, Any]:
    validate_source_plan(source_plan)
    candidate_blocks = list(source_plan["candidate_blocks"])
    status = _prefix_status(candidate_blocks)

    return {
        "experiment_id": EXPERIMENT_ID,
        "source_experiment_id": SOURCE_EXPERIMENT_ID,
        "source_metadata_experiment_id": SOURCE_METADATA_EXPERIMENT_ID,
        "research_only": True,
        "metadata_only": True,
        "post_metadata_pre_odds_amendment": True,
        "odds_endpoint_used": False,
        "market_prices_opened": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "paid_subscription_used": False,
        "future_cutoff_utc": FUTURE_CUTOFF_UTC,
        "league_order": list(LEAGUE_ORDER),
        "total_prior_excluded_fixture_ids": EXPECTED_PRIOR_EXCLUDED_IDS,
        "candidate_blocks": candidate_blocks,
        "cohort_lock_gate": {
            "minimum_blocks_per_league": MIN_BLOCKS_PER_LEAGUE,
            "minimum_total_blocks": MIN_TOTAL_BLOCKS,
            "minimum_metadata_potential_pairs": MIN_METADATA_POTENTIAL_PAIRS,
        },
        "statistical_gate_unchanged_from_v1": {
            "minimum_total_rows": MIN_TOTAL_ROWS,
            "minimum_leagues_with_pairs": MIN_LEAGUES_WITH_PAIRS,
            "minimum_regime_blocks": MIN_REGIME_BLOCKS,
            "minimum_comparable_pairs": MIN_COMPARABLE_PAIRS,
            "minimum_concordance": MIN_CONCORDANCE,
            "permutations": PERMUTATIONS,
            "permutation_seed": PERMUTATION_SEED,
            "maximum_pvalue": MAX_PVALUE,
        },
        **status,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata-zip", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/corner_regime_adjusted_direction_v2b"),
    )
    args = parser.parse_args()

    source_plan, fixture_rows = load_source_metadata_artifact(args.metadata_zip)
    v2b_plan = build_v2b_plan(source_plan)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(args.output_dir / "cohort_plan.json", v2b_plan)
    _write_json(args.output_dir / "future_fixture_metadata.json", fixture_rows)
    print(json.dumps(v2b_plan, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
