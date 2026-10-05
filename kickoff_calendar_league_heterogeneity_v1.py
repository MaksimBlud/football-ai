"""Preregistered league-heterogeneity audit for kickoff/calendar O/U 2.5.

This is a diagnostic follow-up to the already-negative pooled kickoff/calendar result.
It cannot rescue the pooled null and cannot authorize betting or production promotion.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression

from kickoff_calendar_context_v1 import (
    BOOTSTRAP_DRAWS,
    LEAGUE_ORDER,
    REFERENCE,
    SEED,
    TEST,
    VALIDATION,
    _design,
    _download_rows,
)

EXPERIMENT_ID = "KICKOFF_CALENDAR_LEAGUE_HETEROGENEITY_V1"
PAIRWISE_ALPHA = 0.05 / 3.0
CI_LOW_Q = PAIRWISE_ALPHA / 2.0
CI_HIGH_Q = 1.0 - PAIRWISE_ALPHA / 2.0


def _loss_delta(y: np.ndarray, p_base: np.ndarray, p_cal: np.ndarray) -> np.ndarray:
    eps = 1e-12
    p_base = np.clip(p_base.astype(float), eps, 1.0 - eps)
    p_cal = np.clip(p_cal.astype(float), eps, 1.0 - eps)
    y = y.astype(int)
    base_loss = -(y * np.log(p_base) + (1 - y) * np.log(1 - p_base))
    cal_loss = -(y * np.log(p_cal) + (1 - y) * np.log(1 - p_cal))
    return cal_loss - base_loss


def _pairwise_bootstrap(
    delta_a: np.ndarray,
    delta_b: np.ndarray,
    *,
    seed: int,
) -> dict[str, float | int | bool]:
    if len(delta_a) < 2 or len(delta_b) < 2:
        raise RuntimeError("pairwise heterogeneity bootstrap requires >=2 rows per league")

    rng = np.random.default_rng(seed)
    draws = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    for i in range(BOOTSTRAP_DRAWS):
        a = rng.choice(delta_a, size=len(delta_a), replace=True)
        b = rng.choice(delta_b, size=len(delta_b), replace=True)
        draws[i] = float(a.mean() - b.mean())

    observed = float(delta_a.mean() - delta_b.mean())
    low = float(np.quantile(draws, CI_LOW_Q))
    high = float(np.quantile(draws, CI_HIGH_Q))
    excludes_zero = bool(low > 0.0 or high < 0.0)
    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": seed,
        "observed_difference": observed,
        "ci_level": float(1.0 - PAIRWISE_ALPHA),
        "ci_low": low,
        "ci_high": high,
        "excludes_zero": excludes_zero,
    }


def _split_report(
    frame,
    baseline: LogisticRegression,
    calendar: LogisticRegression,
    *,
    split_name: str,
) -> dict[str, Any]:
    if frame.empty:
        raise RuntimeError(f"{split_name}: empty split")

    y = frame["target_over25"].to_numpy(int)
    p_base = baseline.predict_proba(_design(frame, False))[:, 1]
    p_cal = calendar.predict_proba(_design(frame, True))[:, 1]
    delta = _loss_delta(y, p_base, p_cal)

    league_reports: dict[str, Any] = {}
    league_deltas: dict[str, np.ndarray] = {}
    league_values = frame["league"].astype(str).to_numpy()

    for league in LEAGUE_ORDER:
        idx = np.flatnonzero(league_values == league)
        if len(idx) < 2:
            raise RuntimeError(f"{split_name}: missing frozen league {league}")
        local = delta[idx]
        league_deltas[league] = local
        league_reports[league] = {
            "rows": int(len(local)),
            "calendar_minus_baseline_log_loss": float(local.mean()),
            "calendar_better_rate": float((local < 0.0).mean()),
        }

    pairwise: dict[str, Any] = {}
    for pair_index, (league_a, league_b) in enumerate(combinations(LEAGUE_ORDER, 2)):
        key = f"{league_a}__minus__{league_b}"
        pairwise[key] = {
            "league_a": league_a,
            "league_b": league_b,
            **_pairwise_bootstrap(
                league_deltas[league_a],
                league_deltas[league_b],
                seed=SEED + pair_index,
            ),
        }

    return {
        "split": split_name,
        "rows": int(len(frame)),
        "pooled_calendar_minus_baseline_log_loss": float(delta.mean()),
        "by_league": league_reports,
        "pairwise_bonferroni_bootstrap": pairwise,
    }


def _stable_pairwise_heterogeneity(
    validation: dict[str, Any],
    test: dict[str, Any],
) -> list[str]:
    stable: list[str] = []
    for key, val_pair in validation["pairwise_bonferroni_bootstrap"].items():
        test_pair = test["pairwise_bonferroni_bootstrap"][key]
        val_diff = float(val_pair["observed_difference"])
        test_diff = float(test_pair["observed_difference"])
        same_direction = bool(val_diff * test_diff > 0.0)
        if (
            val_pair["excludes_zero"]
            and test_pair["excludes_zero"]
            and same_direction
        ):
            stable.append(key)
    return stable


def evaluate() -> dict[str, Any]:
    data, coverage = _download_rows()
    reference = data[data["season"].isin(REFERENCE)].copy()
    validation = data[data["season"] == VALIDATION].copy()
    test = data[data["season"] == TEST].copy()
    if min(len(reference), len(validation), len(test)) == 0:
        raise RuntimeError("one or more frozen temporal splits are empty")

    baseline = LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs")
    calendar = LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs")
    y_ref = reference["target_over25"].to_numpy(int)
    baseline.fit(_design(reference, False), y_ref)
    calendar.fit(_design(reference, True), y_ref)

    validation_report = _split_report(
        validation,
        baseline,
        calendar,
        split_name=VALIDATION,
    )
    test_report = _split_report(
        test,
        baseline,
        calendar,
        split_name=TEST,
    )
    stable_pairs = _stable_pairwise_heterogeneity(validation_report, test_report)
    supported = bool(stable_pairs)

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "PREREGISTERED_LEAGUE_HETEROGENEITY_DIAGNOSTIC",
        "research_only": True,
        "parent_pooled_hypothesis_supported": False,
        "pooled_null_rescued": False,
        "betting_enabled": False,
        "production_promotion": False,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "opened_2026_27_data_used": False,
        "leagues": list(LEAGUE_ORDER),
        "reference_seasons": list(REFERENCE),
        "validation_season": VALIDATION,
        "test_season": TEST,
        "coverage": coverage,
        "reference_rows": int(len(reference)),
        "pairwise_familywise_alpha": 0.05,
        "pairwise_bonferroni_ci_level": float(1.0 - PAIRWISE_ALPHA),
        "validation": validation_report,
        "test": test_report,
        "stable_heterogeneity_pairs": stable_pairs,
        "supported": supported,
        "decision": (
            "STABLE_KICKOFF_CALENDAR_LEAGUE_HETEROGENEITY"
            if supported
            else "NO_STABLE_KICKOFF_CALENDAR_LEAGUE_HETEROGENEITY"
        ),
        "interpretation_guard": (
            "League heterogeneity is diagnostic only and cannot rescue the already "
            "rejected pooled kickoff/calendar OOS hypothesis."
        ),
        "result": "RESEARCH_ONLY",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(evaluate(), indent=2, sort_keys=True, ensure_ascii=False))
