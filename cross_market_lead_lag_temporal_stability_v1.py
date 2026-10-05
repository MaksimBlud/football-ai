"""Frozen temporal-stability diagnostic for cross-market lead-lag.

Uses the existing alignment_dot statistic unchanged across all frozen seasons and
five leagues. This diagnostic cannot rescue the failed independent replication gate.
No match outcomes are used.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from cross_market_lead_lag_anomaly_audit_v1 import LEAGUES, SEASONS, _raw_and_rows

EXPERIMENT_ID = "CROSS_MARKET_LEAD_LAG_TEMPORAL_STABILITY_V1"
BOOTSTRAP_DRAWS = 5000
PERMUTATION_DRAWS = 5000
SEED = 20261005


def _stratified_bootstrap_mean(
    frame: pd.DataFrame,
    seed: int,
) -> dict[str, float | int]:
    rng = np.random.default_rng(seed)
    groups = {
        league: frame.loc[
            frame["league"].astype(str) == league,
            "alignment_dot",
        ].to_numpy(float)
        for league in LEAGUES
    }
    if any(len(values) == 0 for values in groups.values()):
        raise RuntimeError("season bootstrap missing a frozen league")

    total_rows = sum(len(values) for values in groups.values())
    draws = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    for idx in range(BOOTSTRAP_DRAWS):
        total = 0.0
        for values in groups.values():
            total += float(
                rng.choice(values, size=len(values), replace=True).sum()
            )
        draws[idx] = total / total_rows

    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": seed,
        "mean": float(draws.mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "probability_positive": float((draws > 0.0).mean()),
    }


def _between_season_stat(values: np.ndarray, seasons: np.ndarray) -> float:
    season_count = len(SEASONS)
    counts = np.bincount(seasons, minlength=season_count).astype(float)
    sums = np.bincount(seasons, weights=values, minlength=season_count)
    if np.any(counts == 0):
        raise RuntimeError("temporal stability statistic missing a frozen season")
    means = sums / counts
    global_mean = float(values.mean())
    return float(np.sum(counts * (means - global_mean) ** 2) / len(values))


def _temporal_heterogeneity_permutation(
    frame: pd.DataFrame,
) -> dict[str, float | int]:
    values = frame["alignment_dot"].to_numpy(float)
    season_labels = frame["season"].astype(str).to_numpy()
    league_labels = frame["league"].astype(str).to_numpy()
    season_to_code = {season: idx for idx, season in enumerate(SEASONS)}
    try:
        season_codes = np.asarray(
            [season_to_code[value] for value in season_labels],
            dtype=int,
        )
    except KeyError as exc:
        raise RuntimeError(f"unexpected season in temporal stability frame: {exc}") from exc

    observed = _between_season_stat(values, season_codes)
    league_indices = {
        league: np.flatnonzero(league_labels == league)
        for league in LEAGUES
    }
    if any(len(indices) == 0 for indices in league_indices.values()):
        raise RuntimeError("temporal permutation missing a frozen league")

    rng = np.random.default_rng(SEED)
    null = np.empty(PERMUTATION_DRAWS, dtype=float)
    for draw in range(PERMUTATION_DRAWS):
        permuted = season_codes.copy()
        for indices in league_indices.values():
            permuted[indices] = rng.permutation(season_codes[indices])
        null[draw] = _between_season_stat(values, permuted)

    p_value = float(
        (1 + np.sum(null >= observed))
        / (PERMUTATION_DRAWS + 1)
    )
    return {
        "draws": PERMUTATION_DRAWS,
        "seed": SEED,
        "observed_between_season_variance": observed,
        "null_mean": float(null.mean()),
        "null_ci95_low": float(np.quantile(null, 0.025)),
        "null_ci95_high": float(np.quantile(null, 0.975)),
        "p_value": p_value,
    }


def evaluate() -> dict[str, Any]:
    frames: list[pd.DataFrame] = []
    coverage: dict[str, Any] = {}
    for league in LEAGUES:
        _, rows, league_coverage = _raw_and_rows(league)
        frames.append(rows)
        coverage[league] = league_coverage

    data = pd.concat(frames, ignore_index=True)
    data = data[data["season"].astype(str).isin(SEASONS)].copy()
    if data.empty:
        raise RuntimeError("temporal stability dataset is empty")

    season_results: dict[str, Any] = {}
    positive_seasons = 0
    ci_above_zero_seasons = 0
    for season_index, season in enumerate(SEASONS):
        local = data[data["season"].astype(str) == season].copy()
        if local.empty:
            raise RuntimeError(f"{season}: frozen temporal stability split is empty")
        by_league = {}
        positive_leagues = 0
        for league in LEAGUES:
            league_rows = local[local["league"] == league]
            if league_rows.empty:
                raise RuntimeError(f"{season}/{league}: no frozen rows")
            mean = float(league_rows["alignment_dot"].mean())
            positive_leagues += int(mean > 0.0)
            by_league[league] = {
                "rows": int(len(league_rows)),
                "mean_alignment_dot": mean,
            }

        mean_alignment = float(local["alignment_dot"].mean())
        positive_seasons += int(mean_alignment > 0.0)
        bootstrap = _stratified_bootstrap_mean(
            local,
            SEED + 100 * season_index,
        )
        ci_above_zero_seasons += int(bootstrap["ci95_low"] > 0.0)
        season_results[season] = {
            "rows": int(len(local)),
            "mean_alignment_dot": mean_alignment,
            "median_alignment_dot": float(local["alignment_dot"].median()),
            "positive_mean_alignment_leagues": int(positive_leagues),
            "league_count": len(LEAGUES),
            "by_league": by_league,
            "bootstrap": bootstrap,
        }

    heterogeneity = _temporal_heterogeneity_permutation(data)
    temporal_instability = bool(heterogeneity["p_value"] < 0.05)
    strict_stability_pattern = bool(
        not temporal_instability
        and positive_seasons >= 6
        and ci_above_zero_seasons >= 4
    )

    if temporal_instability:
        decision = "TEMPORAL_INSTABILITY_DETECTED"
        plain = (
            "The frozen alignment statistic varies across seasons more than expected "
            "under within-league season-label permutation, indicating temporal instability."
        )
    elif strict_stability_pattern:
        decision = "TEMPORAL_STABILITY_PATTERN_ONLY_NO_RESCUE"
        plain = (
            "The frozen alignment statistic shows a strict descriptive stability pattern, "
            "but the failed independent replication validation gate remains binding."
        )
    else:
        decision = "NO_STABLE_POSITIVE_LEAD_LAG"
        plain = (
            "The frozen alignment statistic does not satisfy the preregistered strict "
            "temporal-stability pattern across 2019/20-2025/26."
        )

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "FROZEN_TEMPORAL_STABILITY_DIAGNOSTIC",
        "primary_statistic": "alignment_dot",
        "statistic_changed_from_parent": False,
        "match_outcomes_used": False,
        "opened_2026_27_data_used": False,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_model_operations": 0,
        "production_promotion": False,
        "parent_replication_issue": 482,
        "parent_replication_decision": "LEAD_LAG_REPLICATION_NOT_SUPPORTED",
        "parent_replication_decision_unchanged": True,
        "replication_gate_rescued": False,
        "leagues": list(LEAGUES),
        "seasons": list(SEASONS),
        "rows": int(len(data)),
        "coverage": coverage,
        "season_results": season_results,
        "positive_season_count": int(positive_seasons),
        "season_count": len(SEASONS),
        "ci_above_zero_season_count": int(ci_above_zero_seasons),
        "temporal_heterogeneity_permutation": heterogeneity,
        "temporal_instability_detected": temporal_instability,
        "strict_stability_pattern": strict_stability_pattern,
        "decision": decision,
        "result": "NO_BET_NO_RESCUE",
        "summary": {"plain_language": plain},
    }
