"""Preregistered league-heterogeneity audit for kickoff/calendar context.

This is a follow-up to KICKOFF_CALENDAR_CONTEXT_V1. It cannot rescue the
negative pooled result. The comparison rule is frozen before league-specific
evaluation and uses the same reference/validation/OOT seasons and market baseline.
"""
from __future__ import annotations

import itertools
import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

import kickoff_calendar_context_v1 as base

EXPERIMENT_ID = "KICKOFF_CALENDAR_LEAGUE_HETEROGENEITY_V1"
LEAGUES = base.LEAGUE_ORDER
REFERENCE = base.REFERENCE
VALIDATION = base.VALIDATION
TEST = base.TEST
BOOTSTRAP_DRAWS = 5000
SEED = 20261005
PAIRWISE_ALPHA = 0.05 / 3.0


def _league_design(frame: pd.DataFrame, with_calendar: bool) -> np.ndarray:
    p = frame["p_market_over25"].clip(1e-6, 1 - 1e-6).to_numpy(float)
    market_logit = np.log(p / (1.0 - p)).reshape(-1, 1)
    cols = [market_logit]

    if with_calendar:
        weekday = frame["weekday"].astype(int)
        for day in base.WEEKDAYS[1:]:
            cols.append((weekday == day).astype(float).to_numpy().reshape(-1, 1))

        hour = frame["hour"].to_numpy(float)
        radians = 2.0 * math.pi * hour / 24.0
        cols.append(np.sin(radians).reshape(-1, 1))
        cols.append(np.cos(radians).reshape(-1, 1))

        slot = frame["slot"].astype(str)
        for name in base.SLOTS[1:]:
            cols.append((slot == name).astype(float).to_numpy().reshape(-1, 1))

    return np.hstack(cols)


def _loss_delta(
    frame: pd.DataFrame,
    baseline: LogisticRegression,
    calendar: LogisticRegression,
) -> np.ndarray:
    y = frame["target_over25"].to_numpy(int)
    p_base = baseline.predict_proba(_league_design(frame, False))[:, 1]
    p_cal = calendar.predict_proba(_league_design(frame, True))[:, 1]
    eps = 1e-12
    base_loss = -(
        y * np.log(np.clip(p_base, eps, 1 - eps))
        + (1 - y) * np.log(np.clip(1 - p_base, eps, 1 - eps))
    )
    calendar_loss = -(
        y * np.log(np.clip(p_cal, eps, 1 - eps))
        + (1 - y) * np.log(np.clip(1 - p_cal, eps, 1 - eps))
    )
    return calendar_loss - base_loss


def _bootstrap_mean(values: np.ndarray, seed: int) -> dict[str, float | int]:
    if len(values) == 0:
        raise RuntimeError("bootstrap values are empty")
    rng = np.random.default_rng(seed)
    draws = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    for idx in range(BOOTSTRAP_DRAWS):
        draws[idx] = float(rng.choice(values, size=len(values), replace=True).mean())
    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": seed,
        "mean": float(draws.mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "probability_below_zero": float((draws < 0.0).mean()),
    }


def _pairwise_bootstrap_difference(
    left: np.ndarray,
    right: np.ndarray,
    seed: int,
) -> dict[str, float | int | bool]:
    if len(left) == 0 or len(right) == 0:
        raise RuntimeError("pairwise bootstrap values are empty")
    rng = np.random.default_rng(seed)
    draws = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    for idx in range(BOOTSTRAP_DRAWS):
        l = rng.choice(left, size=len(left), replace=True).mean()
        r = rng.choice(right, size=len(right), replace=True).mean()
        draws[idx] = float(l - r)

    low_q = PAIRWISE_ALPHA / 2.0
    high_q = 1.0 - low_q
    low = float(np.quantile(draws, low_q))
    high = float(np.quantile(draws, high_q))
    excludes_zero = bool(low > 0.0 or high < 0.0)
    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": seed,
        "bonferroni_familywise_alpha": 0.05,
        "per_pair_alpha": PAIRWISE_ALPHA,
        "ci_low": low,
        "ci_high": high,
        "mean_difference": float(draws.mean()),
        "excludes_zero": excludes_zero,
    }


def evaluate() -> dict[str, Any]:
    data, coverage = base._download_rows()
    league_results: dict[str, Any] = {}
    validation_deltas: dict[str, np.ndarray] = {}
    test_deltas: dict[str, np.ndarray] = {}

    for league_index, league in enumerate(LEAGUES):
        local = data[data["league"] == league].copy()
        reference = local[local["season"].isin(REFERENCE)].copy()
        validation = local[local["season"] == VALIDATION].copy()
        test = local[local["season"] == TEST].copy()
        if min(len(reference), len(validation), len(test)) == 0:
            raise RuntimeError(f"{league}: frozen temporal split is empty")

        baseline_model = LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs")
        calendar_model = LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs")
        y_reference = reference["target_over25"].to_numpy(int)
        baseline_model.fit(_league_design(reference, False), y_reference)
        calendar_model.fit(_league_design(reference, True), y_reference)

        validation_delta = _loss_delta(validation, baseline_model, calendar_model)
        test_delta = _loss_delta(test, baseline_model, calendar_model)
        validation_deltas[league] = validation_delta
        test_deltas[league] = test_delta

        league_results[league] = {
            "reference_rows": int(len(reference)),
            "validation_rows": int(len(validation)),
            "test_rows": int(len(test)),
            "validation_calendar_minus_baseline_log_loss": float(validation_delta.mean()),
            "test_calendar_minus_baseline_log_loss": float(test_delta.mean()),
            "test_bootstrap": _bootstrap_mean(
                test_delta,
                SEED + 100 * league_index,
            ),
        }

    pairs: dict[str, Any] = {}
    heterogeneity_pairs: list[str] = []
    for pair_index, (left, right) in enumerate(itertools.combinations(LEAGUES, 2)):
        validation_difference = float(
            validation_deltas[left].mean() - validation_deltas[right].mean()
        )
        test_difference = float(
            test_deltas[left].mean() - test_deltas[right].mean()
        )
        bootstrap = _pairwise_bootstrap_difference(
            test_deltas[left],
            test_deltas[right],
            SEED + 1000 + pair_index,
        )
        same_direction = bool(
            validation_difference != 0.0
            and test_difference != 0.0
            and np.sign(validation_difference) == np.sign(test_difference)
        )
        supported_pair = bool(bootstrap["excludes_zero"] and same_direction)
        name = f"{left}__vs__{right}"
        pairs[name] = {
            "validation_difference": validation_difference,
            "test_difference": test_difference,
            "same_direction_validation_and_test": same_direction,
            "test_bonferroni_bootstrap": bootstrap,
            "heterogeneity_supported": supported_pair,
        }
        if supported_pair:
            heterogeneity_pairs.append(name)

    heterogeneity_supported = bool(heterogeneity_pairs)
    decision = (
        "LEAGUE_HETEROGENEITY_SUPPORTED"
        if heterogeneity_supported
        else "NO_LEAGUE_HETEROGENEITY"
    )
    plain = (
        "At least one preregistered pair of leagues shows a Bonferroni-controlled OOT "
        "difference in calendar-minus-baseline log loss with the same direction in "
        "validation and OOT."
        if heterogeneity_supported
        else "No preregistered league pair shows a Bonferroni-controlled OOT difference "
        "with the same direction in validation and OOT."
    )

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "PREREGISTERED_LEAGUE_HETEROGENEITY",
        "parent_experiment": base.EXPERIMENT_ID,
        "parent_pooled_decision": "NO_KICKOFF_CALENDAR_OOS_SIGNAL",
        "parent_pooled_decision_unchanged": True,
        "pooled_signal_rescued": False,
        "research_only": True,
        "opened_2026_27_data_used": False,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_model_operations": 0,
        "production_promotion": False,
        "leagues": list(LEAGUES),
        "reference_seasons": list(REFERENCE),
        "validation_season": VALIDATION,
        "test_season": TEST,
        "coverage": coverage,
        "league_results": league_results,
        "pairwise_heterogeneity": pairs,
        "heterogeneity_pairs": heterogeneity_pairs,
        "heterogeneity_supported": heterogeneity_supported,
        "decision": decision,
        "result": "RESEARCH_ONLY_NO_RESCUE",
        "summary": {"plain_language": plain},
    }
