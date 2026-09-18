"""Third-sample test of individual corner-market direction beyond league-day regime.

Research only. The primary statistic compares matches only within the same league
and UTC kickoff date, so a common additive market move inside that block cannot
produce the claimed individual-direction signal.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import corner_market_state_repricing_v1 as v1
import corner_repricing_direction_replication_v1 as replication

EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V1"
FIXTURES_PER_LEAGUE = 10
MIN_SELECTED_PER_LEAGUE = 6
MAX_FIXTURE_PAGES = 2
MIN_TOTAL_ROWS = 30
MIN_LEAGUES_WITH_PAIRS = 4
MIN_REGIME_BLOCKS = 8
MIN_COMPARABLE_PAIRS = 40
MIN_CONCORDANCE = 0.60
PERMUTATIONS = 20_000
PERMUTATION_SEED = 20_260_918
MAX_PVALUE = 0.10
TIE_TOLERANCE = 1e-12


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_previous_selected_fixture_ids(artifact_zip: Path) -> set[str]:
    """Read only selected fixture metadata from the prior replication artifact."""
    with zipfile.ZipFile(artifact_zip) as zf:
        names = [name for name in zf.namelist() if name.endswith("selected_fixtures.json")]
        if len(names) != 1:
            raise RuntimeError(
                "expected exactly one selected_fixtures.json in prior replication artifact, "
                f"got {len(names)}"
            )
        payload = json.loads(zf.read(names[0]).decode("utf-8"))

    if not isinstance(payload, dict):
        raise RuntimeError("prior selected_fixtures.json must be an object")

    fixture_ids: set[str] = set()
    for league in replication.LEAGUES:
        rows = payload.get(league)
        if not isinstance(rows, list):
            raise RuntimeError(f"prior selected fixtures missing league {league}")
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError(f"prior {league} selected fixture is not an object")
            fixture_id = str(row.get("fixture_id") or "").strip()
            if not fixture_id:
                raise RuntimeError(f"prior {league} selected fixture missing fixture_id")
            fixture_ids.add(fixture_id)
    return fixture_ids


def _add_regime_columns(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    kickoff = pd.to_datetime(out["kickoff_utc"], utc=True, errors="coerce")
    if kickoff.isna().any():
        raise ValueError("all eligible rows must have a valid kickoff_utc")
    out["kickoff_date_utc"] = kickoff.dt.strftime("%Y-%m-%d")
    out["regime_block"] = out["league"].astype(str) + "|" + out["kickoff_date_utc"]
    out["direction_score"] = -out["opening_lambda"].astype(float)

    medians = out.groupby("regime_block")["centre_delta"].transform("median")
    out["regime_median_delta"] = medians.astype(float)
    out["regime_adjusted_delta"] = out["centre_delta"].astype(float) - medians.astype(float)
    return out


def _pair_counts(scores: np.ndarray, deltas: np.ndarray) -> tuple[int, int]:
    concordant = 0
    comparable = 0
    n = len(scores)
    for i in range(n):
        for j in range(i + 1, n):
            score_diff = float(scores[i] - scores[j])
            delta_diff = float(deltas[i] - deltas[j])
            if abs(score_diff) <= TIE_TOLERANCE or abs(delta_diff) <= TIE_TOLERANCE:
                continue
            comparable += 1
            if score_diff * delta_diff > 0:
                concordant += 1
    return concordant, comparable


def _block_arrays(frame: pd.DataFrame) -> list[tuple[str, str, np.ndarray, np.ndarray]]:
    blocks: list[tuple[str, str, np.ndarray, np.ndarray]] = []
    for block, group in frame.groupby("regime_block", sort=True):
        ordered = group.sort_values("fixture_id", kind="stable")
        blocks.append(
            (
                str(block),
                str(ordered["league"].iloc[0]),
                ordered["direction_score"].to_numpy(float),
                ordered["centre_delta"].to_numpy(float),
            )
        )
    return blocks


def _observed_concordance(
    blocks: list[tuple[str, str, np.ndarray, np.ndarray]],
) -> tuple[int, int, dict[str, dict[str, float | int | None]], dict[str, dict[str, float | int | None]]]:
    total_concordant = 0
    total_comparable = 0
    by_block: dict[str, dict[str, float | int | None]] = {}
    league_counts: dict[str, list[int]] = {league: [0, 0] for league in replication.LEAGUES}

    for block, league, scores, deltas in blocks:
        concordant, comparable = _pair_counts(scores, deltas)
        total_concordant += concordant
        total_comparable += comparable
        league_counts.setdefault(league, [0, 0])
        league_counts[league][0] += concordant
        league_counts[league][1] += comparable
        by_block[block] = {
            "rows": int(len(scores)),
            "concordant_pairs": int(concordant),
            "comparable_pairs": int(comparable),
            "concordance": float(concordant / comparable) if comparable else None,
            "median_centre_delta": float(np.median(deltas)) if len(deltas) else None,
            "positive_share_nonzero": (
                float(np.mean(deltas[np.abs(deltas) > TIE_TOLERANCE] > 0))
                if np.any(np.abs(deltas) > TIE_TOLERANCE)
                else None
            ),
        }

    by_league: dict[str, dict[str, float | int | None]] = {}
    for league in replication.LEAGUES:
        concordant, comparable = league_counts.get(league, [0, 0])
        by_league[league] = {
            "concordant_pairs": int(concordant),
            "comparable_pairs": int(comparable),
            "concordance": float(concordant / comparable) if comparable else None,
        }
    return total_concordant, total_comparable, by_block, by_league


def regime_preserving_permutation_pvalue(
    blocks: list[tuple[str, str, np.ndarray, np.ndarray]],
    observed_concordance: float,
    *,
    permutations: int = PERMUTATIONS,
    seed: int = PERMUTATION_SEED,
) -> float:
    if permutations < 1:
        raise ValueError("permutations must be >= 1")
    rng = np.random.default_rng(seed)
    at_least_observed = 0

    for _ in range(permutations):
        concordant = 0
        comparable = 0
        for _, _, scores, deltas in blocks:
            permuted = rng.permutation(deltas)
            block_concordant, block_comparable = _pair_counts(scores, permuted)
            concordant += block_concordant
            comparable += block_comparable
        stat = float(concordant / comparable) if comparable else 0.0
        if stat + TIE_TOLERANCE >= observed_concordance:
            at_least_observed += 1

    return float((1 + at_least_observed) / (permutations + 1))


def _movement_diagnostics(frame: pd.DataFrame) -> dict[str, Any]:
    delta = frame["centre_delta"].to_numpy(float)
    positive = int(np.sum(delta > TIE_TOLERANCE))
    negative = int(np.sum(delta < -TIE_TOLERANCE))
    zero = int(len(delta) - positive - negative)

    by_league: dict[str, Any] = {}
    for league in replication.LEAGUES:
        league_delta = frame.loc[frame["league"] == league, "centre_delta"].to_numpy(float)
        nonzero = league_delta[np.abs(league_delta) > TIE_TOLERANCE]
        by_league[league] = {
            "rows": int(len(league_delta)),
            "positive": int(np.sum(league_delta > TIE_TOLERANCE)),
            "negative": int(np.sum(league_delta < -TIE_TOLERANCE)),
            "zero": int(np.sum(np.abs(league_delta) <= TIE_TOLERANCE)),
            "positive_share_nonzero": float(np.mean(nonzero > 0)) if len(nonzero) else None,
        }

    score = frame["direction_score"].astype(float)
    low_cut = float(score.quantile(0.25))
    high_cut = float(score.quantile(0.75))
    top = frame.loc[score >= high_cut, "regime_adjusted_delta"].to_numpy(float)
    bottom = frame.loc[score <= low_cut, "regime_adjusted_delta"].to_numpy(float)
    return {
        "positive": positive,
        "negative": negative,
        "zero": zero,
        "positive_share_nonzero": float(positive / (positive + negative))
        if positive + negative
        else None,
        "by_league": by_league,
        "top_score_regime_adjusted_mean": float(np.mean(top)) if len(top) else None,
        "bottom_score_regime_adjusted_mean": float(np.mean(bottom)) if len(bottom) else None,
        "top_minus_bottom_regime_adjusted_mean": (
            float(np.mean(top) - np.mean(bottom)) if len(top) and len(bottom) else None
        ),
    }


def evaluate_fresh_direction(fresh_frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    if fresh_frame.empty:
        frame = fresh_frame.copy()
        return frame, {
            "experiment_id": EXPERIMENT_ID,
            "research_only": True,
            "betting_enabled": False,
            "match_outcome_used": False,
            "football_state_used": False,
            "sample_gate_pass": False,
            "verdict": "SAMPLE_TOO_SMALL",
            "fresh_eligible_rows": 0,
        }

    frame = _add_regime_columns(fresh_frame)
    blocks = _block_arrays(frame)
    concordant, comparable, by_block, by_league = _observed_concordance(blocks)
    contributing_blocks = sum(
        int(metrics["comparable_pairs"] or 0) > 0 for metrics in by_block.values()
    )
    contributing_leagues = sum(
        int(metrics["comparable_pairs"] or 0) > 0 for metrics in by_league.values()
    )
    sample_ok = (
        len(frame) >= MIN_TOTAL_ROWS
        and contributing_leagues >= MIN_LEAGUES_WITH_PAIRS
        and contributing_blocks >= MIN_REGIME_BLOCKS
        and comparable >= MIN_COMPARABLE_PAIRS
    )

    report: dict[str, Any] = {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "betting_enabled": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "candidate_feature": "FAIR_CENTRE_ONLY",
        "candidate_direction_score": "-opening_lambda",
        "regime_block_definition": "league + UTC kickoff date",
        "fresh_eligible_rows": int(len(frame)),
        "fresh_rows_by_league": {
            league: int((frame["league"] == league).sum()) for league in replication.LEAGUES
        },
        "contributing_regime_blocks": int(contributing_blocks),
        "contributing_leagues": int(contributing_leagues),
        "comparable_pairs": int(comparable),
        "concordant_pairs": int(concordant),
        "sample_gate_pass": bool(sample_ok),
        "by_regime_block": by_block,
        "by_league_concordance": by_league,
        "movement_diagnostics": _movement_diagnostics(frame),
    }

    if not sample_ok:
        report.update(
            {
                "observed_concordance": float(concordant / comparable) if comparable else None,
                "permutation_pvalue": None,
                "direction_discrimination_confirmed": False,
                "verdict": "SAMPLE_TOO_SMALL",
            }
        )
        return frame, report

    observed = float(concordant / comparable)
    pvalue = regime_preserving_permutation_pvalue(blocks, observed)
    confirmed = bool(observed >= MIN_CONCORDANCE and pvalue < MAX_PVALUE)
    report.update(
        {
            "observed_concordance": observed,
            "permutation_count": PERMUTATIONS,
            "permutation_seed": PERMUTATION_SEED,
            "permutation_pvalue": pvalue,
            "minimum_concordance_gate": MIN_CONCORDANCE,
            "maximum_pvalue_gate": MAX_PVALUE,
            "direction_discrimination_confirmed": confirmed,
            "verdict": (
                "INDIVIDUAL_DIRECTION_DISCRIMINATION_REPLICATED"
                if confirmed
                else "INDIVIDUAL_DIRECTION_DISCRIMINATION_NOT_CONFIRMED"
            ),
        }
    )
    return frame, report



def acquire_third_holdout(
    output_dir: Path,
    *,
    key: str,
    excluded_ids: set[str],
) -> tuple[pd.DataFrame, int, dict[str, list[dict[str, Any]]]]:
    """Acquire the frozen third sample with bounded fixture discovery.\n\n    Up to ten unseen fixtures are selected per league, with a metadata-only minimum\n    of six when the Free current-season inventory is exhausted. No odds endpoint is\n    called until all five league selections are frozen.\n    """
    client = replication.ProviderClient(key=key)
    selected: dict[str, list[dict[str, Any]]] = {}

    for league, league_id in replication.LEAGUES.items():
        merged_rows: list[dict[str, Any]] = []
        chosen: list[dict[str, Any]] = []
        for page in range(1, MAX_FIXTURE_PAGES + 1):
            payload = client.get(
                f"/v1/leagues/{league_id}/fixtures",
                params={
                    "status": "finished",
                    "order": "desc",
                    "page": page,
                    "per_page": replication.LIST_PER_PAGE,
                },
            )
            _write_json(
                output_dir / "raw" / "fixtures" / f"{league}_page_{page}.json",
                payload,
            )
            data = payload.get("data")
            if not isinstance(data, list):
                raise RuntimeError(f"{league}: invalid fixture-list payload on page {page}")
            merged_rows.extend(data)
            chosen = replication.select_unseen_fixtures(
                {"success": 1, "data": merged_rows},
                league,
                excluded_ids,
            )
            pagination = payload.get("pagination")
            has_more = bool(pagination.get("has_more")) if isinstance(pagination, dict) else page < MAX_FIXTURE_PAGES
            if len(chosen) == FIXTURES_PER_LEAGUE or not has_more:
                break

        selected[league] = chosen
        if len(chosen) < MIN_SELECTED_PER_LEAGUE:
            raise RuntimeError(
                f"{league}: requires at least {MIN_SELECTED_PER_LEAGUE} unseen fixtures, "
                f"got {len(chosen)}"
            )

    _write_json(output_dir / "selected_fixtures.json", selected)

    normalized_rows: list[dict[str, Any]] = []
    for league in replication.LEAGUES:
        for fixture in selected[league]:
            fixture_id = fixture["fixture_id"]
            payload = client.get(
                f"/v1/fixtures/{fixture_id}/odds",
                params={"market": "corner"},
            )
            _write_json(output_dir / "raw" / "odds" / f"{fixture_id}.json", payload)
            row = replication.normalize_corner_odds(payload, fixture)
            if row is None:
                continue
            normalized = replication._normalize_holdout_row(row)
            if normalized is not None:
                normalized_rows.append(normalized)

    return pd.DataFrame(normalized_rows), client.request_count, selected

def run(
    pilot_zip: Path,
    screen_zip: Path,
    previous_replication_zip: Path,
    output_dir: Path,
    *,
    key: str | None = None,
) -> dict[str, Any]:
    v1_frame = v1.load_market_rows(pilot_zip, screen_zip)
    if len(v1_frame) != 55:
        raise RuntimeError(f"expected immutable V1 sample of 55 rows, got {len(v1_frame)}")

    old_ids = set(v1_frame["fixture_id"].astype(str))
    previous_ids = load_previous_selected_fixture_ids(previous_replication_zip)
    if len(previous_ids) != 50:
        raise RuntimeError(
            f"expected 50 prior replication selected fixture IDs, got {len(previous_ids)}"
        )
    if old_ids & previous_ids:
        raise RuntimeError("prior 50-row replication overlaps original V1 fixture IDs")

    excluded_ids = old_ids | previous_ids
    fresh, request_count, selected = acquire_third_holdout(
        output_dir,
        key=replication._require_key(key),
        excluded_ids=excluded_ids,
    )
    fresh_ids = set(fresh["fixture_id"].astype(str)) if not fresh.empty else set()
    if fresh_ids & excluded_ids:
        raise RuntimeError("third-sample eligible rows overlap a prior sample")

    eval_rows, report = evaluate_fresh_direction(fresh)
    output_dir.mkdir(parents=True, exist_ok=True)
    eval_rows.to_csv(output_dir / "evaluation_rows.csv", index=False)
    report.update(
        {
            "original_v1_excluded_fixture_ids": int(len(old_ids)),
            "previous_replication_excluded_fixture_ids": int(len(previous_ids)),
            "total_excluded_fixture_ids": int(len(excluded_ids)),
            "selected_fixture_count": int(sum(len(v) for v in selected.values())),
            "provider_requests": int(request_count),
            "provider_request_budget": replication.MAX_PROVIDER_REQUESTS,
            "paid_subscription_used": False,
            "prior_replication_closing_outcomes_used_for_tuning": False,
        }
    )
    _write_json(output_dir / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-zip", type=Path, required=True)
    parser.add_argument("--screen-zip", type=Path, required=True)
    parser.add_argument("--previous-replication-zip", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/corner_regime_adjusted_direction_v1"),
    )
    args = parser.parse_args()
    report = run(
        args.pilot_zip,
        args.screen_zip,
        args.previous_replication_zip,
        args.output_dir,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
