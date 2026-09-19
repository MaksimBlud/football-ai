"""Metadata-only future cohort planner for corner regime-adjusted direction V2.

Research-only. This module must not call any odds endpoint. It deterministically
locks whole future league-day fixture blocks before any V2 opening/closing market
data may be inspected.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

import corner_regime_adjusted_direction_v1 as v1

EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V2"
FUTURE_CUTOFF_UTC = "2026-09-19T00:00:00Z"
LEAGUE_ORDER = ("EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA", "LIGUE_1")
MIN_FIXTURES_PER_BLOCK = 2
MIN_BLOCKS_PER_LEAGUE = 2
MIN_TOTAL_BLOCKS = 12
MIN_METADATA_POTENTIAL_PAIRS = 80

# Statistical test is intentionally inherited unchanged from V1.
MIN_TOTAL_ROWS = v1.MIN_TOTAL_ROWS
MIN_LEAGUES_WITH_PAIRS = v1.MIN_LEAGUES_WITH_PAIRS
MIN_REGIME_BLOCKS = v1.MIN_REGIME_BLOCKS
MIN_COMPARABLE_PAIRS = v1.MIN_COMPARABLE_PAIRS
MIN_CONCORDANCE = v1.MIN_CONCORDANCE
PERMUTATIONS = v1.PERMUTATIONS
PERMUTATION_SEED = v1.PERMUTATION_SEED
MAX_PVALUE = v1.MAX_PVALUE


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_fixture_rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
        rows = payload["data"]
    elif isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        rows = payload["rows"]
    else:
        raise ValueError("fixture metadata JSON must be a list or contain data/rows list")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("all fixture metadata rows must be objects")
    return rows


def _read_excluded_ids(path: Path | None) -> set[str]:
    if path is None:
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        values = payload
    elif isinstance(payload, dict) and isinstance(payload.get("fixture_ids"), list):
        values = payload["fixture_ids"]
    else:
        raise ValueError("excluded IDs JSON must be a list or contain fixture_ids list")
    return {str(value).strip() for value in values if str(value).strip()}


def normalize_future_metadata(
    rows: list[dict[str, Any]],
    *,
    excluded_ids: set[str],
) -> pd.DataFrame:
    cutoff = pd.Timestamp(FUTURE_CUTOFF_UTC)
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw in rows:
        fixture_id = str(raw.get("fixture_id") or raw.get("id") or "").strip()
        league = str(raw.get("league") or "").strip()
        status = str(raw.get("status") or "").strip().lower()
        kickoff_raw = raw.get("kickoff_utc") or raw.get("commence_time_utc")
        kickoff = pd.to_datetime(kickoff_raw, utc=True, errors="coerce")

        if not fixture_id or fixture_id in seen or fixture_id in excluded_ids:
            continue
        if league not in LEAGUE_ORDER:
            continue
        if status != "finished":
            continue
        if pd.isna(kickoff) or kickoff < cutoff:
            continue

        seen.add(fixture_id)
        normalized.append(
            {
                "fixture_id": fixture_id,
                "league": league,
                "kickoff_utc": kickoff.isoformat(),
                "kickoff_date_utc": kickoff.strftime("%Y-%m-%d"),
                "regime_block": f"{league}|{kickoff.strftime('%Y-%m-%d')}",
            }
        )

    if not normalized:
        return pd.DataFrame(
            columns=[
                "fixture_id",
                "league",
                "kickoff_utc",
                "kickoff_date_utc",
                "regime_block",
            ]
        )

    frame = pd.DataFrame(normalized)
    return frame.sort_values(
        ["kickoff_utc", "fixture_id"],
        ascending=[True, True],
        kind="stable",
    ).reset_index(drop=True)


def _candidate_blocks(frame: pd.DataFrame) -> list[dict[str, Any]]:
    league_rank = {league: idx for idx, league in enumerate(LEAGUE_ORDER)}
    blocks: list[dict[str, Any]] = []

    if frame.empty:
        return blocks

    for block, group in frame.groupby("regime_block", sort=False):
        group = group.sort_values(["kickoff_utc", "fixture_id"], kind="stable")
        if len(group) < MIN_FIXTURES_PER_BLOCK:
            continue
        league = str(group["league"].iloc[0])
        date = str(group["kickoff_date_utc"].iloc[0])
        n = int(len(group))
        blocks.append(
            {
                "regime_block": str(block),
                "league": league,
                "kickoff_date_utc": date,
                "fixture_count": n,
                "potential_pairs": int(n * (n - 1) // 2),
                "fixture_ids": group["fixture_id"].astype(str).tolist(),
                "_league_rank": league_rank[league],
            }
        )

    blocks.sort(
        key=lambda row: (
            row["kickoff_date_utc"],
            row["_league_rank"],
            row["regime_block"],
        )
    )
    for row in blocks:
        row.pop("_league_rank", None)
    return blocks


def _prefix_status(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {league: 0 for league in LEAGUE_ORDER}
    total_pairs = 0
    fixture_ids: list[str] = []

    for idx, block in enumerate(blocks):
        league = block["league"]
        counts[league] += 1
        total_pairs += int(block["potential_pairs"])
        fixture_ids.extend(block["fixture_ids"])

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
                "blocks_by_league": counts,
            }

    total_counts = {league: 0 for league in LEAGUE_ORDER}
    all_pairs = 0
    all_fixture_ids: list[str] = []
    for block in blocks:
        total_counts[block["league"]] += 1
        all_pairs += int(block["potential_pairs"])
        all_fixture_ids.extend(block["fixture_ids"])

    return {
        "status": "WAIT_FOR_COHORT",
        "locked": False,
        "selected_blocks": [],
        "selected_block_count": 0,
        "selected_fixture_ids": [],
        "selected_fixture_count": 0,
        "metadata_potential_pairs": int(all_pairs),
        "blocks_by_league": total_counts,
        "available_candidate_block_count": len(blocks),
        "available_candidate_fixture_count": len(all_fixture_ids),
    }


def plan_future_cohort(
    rows: list[dict[str, Any]],
    *,
    excluded_ids: set[str],
) -> dict[str, Any]:
    frame = normalize_future_metadata(rows, excluded_ids=excluded_ids)
    blocks = _candidate_blocks(frame)
    status = _prefix_status(blocks)
    return {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "metadata_only": True,
        "odds_endpoint_used": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "betting_enabled": False,
        "paid_subscription_used": False,
        "future_cutoff_utc": FUTURE_CUTOFF_UTC,
        "league_order": list(LEAGUE_ORDER),
        "excluded_fixture_ids_count": int(len(excluded_ids)),
        "normalized_future_fixture_count": int(len(frame)),
        "candidate_blocks": blocks,
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
    parser.add_argument("--fixtures-json", type=Path, required=True)
    parser.add_argument("--excluded-ids-json", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/corner_regime_adjusted_direction_v2/cohort_plan.json"),
    )
    args = parser.parse_args()

    report = plan_future_cohort(
        _read_fixture_rows(args.fixtures_json),
        excluded_ids=_read_excluded_ids(args.excluded_ids_json),
    )
    _write_json(args.output, report)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
