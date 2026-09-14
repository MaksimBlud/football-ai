"""Early exploratory EPL AI-vs-market evaluation after user-authorized outcome read.

This does NOT replace or satisfy the original 100-event no-peek primary gate.
The underlying AI/market pairs remain genuinely prospective: every selected pair was
captured before kickoff. The interim cohort uses the pre-existing frozen selection rule
from ``epl_ai_market_pair_evaluation.select_frozen_evaluation_pairs`` (latest eligible
market snapshot per event), then restricts by a fixed completion cutoff.

Because outcomes were exposed before this interim manifest was created, this evidence
must remain labelled exploratory and the original pristine primary no-peek claim is no
longer available.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from epl_ai_market_pair_evaluation import (
    FROZEN_MODEL_SHA256,
    FIRST_PERMITTED_OUTCOME_READ_UTC,
    PRIMARY_COHORT_SIZE,
    select_frozen_evaluation_pairs,
)

EXPERIMENT_ID = "EPL_AI_MARKET_PAIR_V1_EARLY_INTERIM_11"
PARENT_EXPERIMENT_ID = "EPL_AI_MARKET_PAIR_V1"
EVIDENCE_STATUS = "EARLY_EXPLORATORY_OUTCOME_READ"
COMPLETED_CUTOFF_UTC = pd.Timestamp("2026-09-14T00:00:00Z")
EXPECTED_TOTAL = 11
EXPECTED_RESULTS_CSV_SHA256 = "eedc87d7abf4497e8582397eb1e78737df952af3a9d703963ec9378fc8e2d013"
BET_DECISION = "NO_BET"
OUTCOMES = ("H", "D", "A")

MODEL_COLUMNS = ("model_home_prob", "model_draw_prob", "model_away_prob")
MARKET_COLUMNS = ("market_home_prob", "market_draw_prob", "market_away_prob")

EXPECTED_PAIR_KEYS = {
    "1f776abf5bbae738e5ac049ca9194916fb7a1d77a5a6c0c348b24c6f69685ae7",
    "56584a8a7441ac909e0646e032a93b3f66fa1cfe280d1da2823c0a07aaf97c38",
    "b09f1d4695f9420ae8a64dda7ae4ed37deff6a8823e4cea0a318ea51b20bf165",
    "4a649ff3a429e97e982d0ab66a34d47cf0a5e32c6f35b36005cbe7edfc080d58",
    "8fc25d89193f281bb0c7d19cd0c6a60742ea793cc86972d107a36e3278f43d7a",
    "b99bded30df00f8eebde2e1fe52757567446aef91ac54d5a047171ed63014754",
    "954fd3d1243373541b6e783e424a3e576890a2712e6cd01cce868c66492ed74a",
    "a415b8e8858f87fdd5bc29a94bae341fef025de2da87e46cbdeef9208b5db266",
    "b1648a615fe99d140b2103b26d28139268bc06d85e747f007b896137d8023a2f",
    "ca2878c50d071cfbab1266daad21377ef7adc6233abd61e4626c0fadf1fbee7f",
    "811e4af8f69c02fa1aa28b3070970fff23866f6b1eec035bb816ce1579c4960f",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_completed_pairs(pair_ledger: pd.DataFrame) -> pd.DataFrame:
    """Reuse the pre-outcome frozen selector, then take completed fixtures by time only."""
    selected, excluded = select_frozen_evaluation_pairs(pair_ledger)
    if excluded:
        raise RuntimeError(f"Ambiguous EPL pair identities in interim input: {excluded}")
    work = selected.copy()
    work["kickoff_utc"] = pd.to_datetime(work["kickoff_utc"], utc=True, errors="raise")
    return (
        work.loc[work["kickoff_utc"] < COMPLETED_CUTOFF_UTC]
        .sort_values(["kickoff_utc", "event_id", "pair_key"])
        .reset_index(drop=True)
    )


def _probabilities(frame: pd.DataFrame, columns: tuple[str, str, str], label: str) -> np.ndarray:
    matrix = frame.loc[:, list(columns)].astype(float).to_numpy()
    if matrix.shape != (EXPECTED_TOTAL, 3):
        raise ValueError(f"{label} matrix has wrong shape: {matrix.shape}")
    if not np.isfinite(matrix).all() or (matrix < 0).any() or (matrix > 1).any():
        raise ValueError(f"invalid {label} probabilities")
    if not np.allclose(matrix.sum(axis=1), 1.0, atol=1e-9, rtol=0):
        raise ValueError(f"{label} probabilities do not sum to one")
    return matrix


def evaluate(frame: pd.DataFrame) -> dict[str, object]:
    required = {
        "pair_key", "event_id", "kickoff_utc", "market_snapshot_time_utc",
        "model_generated_at_utc", "model_artifact_sha256", "result",
        *MODEL_COLUMNS, *MARKET_COLUMNS,
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing interim evaluation columns: {sorted(missing)}")
    if len(frame) != EXPECTED_TOTAL:
        raise ValueError("early EPL interim requires exactly 11 rows")
    if frame["event_id"].duplicated().any() or frame["pair_key"].duplicated().any():
        raise ValueError("duplicate EPL early-interim identity")
    if set(frame["pair_key"].astype(str)) != EXPECTED_PAIR_KEYS:
        raise ValueError("EPL early-interim pair keys differ from frozen canonical set")
    if set(frame["model_artifact_sha256"].astype(str)) != {FROZEN_MODEL_SHA256}:
        raise ValueError("EPL early-interim model artifact hash drifted")

    kickoff = pd.to_datetime(frame["kickoff_utc"], utc=True, errors="raise")
    snapshot = pd.to_datetime(frame["market_snapshot_time_utc"], utc=True, errors="raise")
    generated = pd.to_datetime(frame["model_generated_at_utc"], utc=True, errors="raise")
    if not (kickoff < COMPLETED_CUTOFF_UTC).all():
        raise ValueError("future/uncompleted event leaked into EPL early interim")
    if not ((snapshot < kickoff) & (generated < kickoff)).all():
        raise ValueError("non-prospective pair leaked into EPL early interim")

    model = _probabilities(frame, MODEL_COLUMNS, "model")
    market = _probabilities(frame, MARKET_COLUMNS, "market")
    results = frame["result"].astype(str).to_numpy()
    if not set(results).issubset(OUTCOMES):
        raise ValueError("invalid H/D/A result")
    target_index = np.asarray([OUTCOMES.index(value) for value in results], dtype=int)
    target = np.zeros((EXPECTED_TOTAL, 3), dtype=float)
    target[np.arange(EXPECTED_TOTAL), target_index] = 1.0

    def brier(probs: np.ndarray) -> float:
        return float(np.mean(np.sum((probs - target) ** 2, axis=1)))

    def log_loss(probs: np.ndarray) -> float:
        actual = np.clip(probs[np.arange(EXPECTED_TOTAL), target_index], 1e-15, 1.0)
        return float(-np.mean(np.log(actual)))

    model_pick = np.argmax(model, axis=1)
    market_pick = np.argmax(market, axis=1)
    model_correct = model_pick == target_index
    market_correct = market_pick == target_index
    disagree = model_pick != market_pick

    return {
        "experiment_id": EXPERIMENT_ID,
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "evidence_status": EVIDENCE_STATUS,
        "n": EXPECTED_TOTAL,
        "model_brier": brier(model),
        "market_brier": brier(market),
        "delta_brier_model_minus_market": brier(model) - brier(market),
        "model_log_loss": log_loss(model),
        "market_log_loss": log_loss(market),
        "delta_log_loss_model_minus_market": log_loss(model) - log_loss(market),
        "model_accuracy": float(np.mean(model_correct)),
        "market_accuracy": float(np.mean(market_correct)),
        "model_correct_n": int(model_correct.sum()),
        "market_correct_n": int(market_correct.sum()),
        "top1_disagreement_n": int(disagree.sum()),
        "disagreement_model_correct_market_wrong": int((disagree & model_correct & ~market_correct).sum()),
        "disagreement_market_correct_model_wrong": int((disagree & market_correct & ~model_correct).sum()),
        "disagreement_both_wrong": int((disagree & ~model_correct & ~market_correct).sum()),
        "draw_actual_n": int((target_index == 1).sum()),
        "draw_actual_rate": float(np.mean(target_index == 1)),
        "model_mean_draw_probability": float(model[:, 1].mean()),
        "market_mean_draw_probability": float(market[:, 1].mean()),
        "model_draw_top1_n": int((model_pick == 1).sum()),
        "market_draw_top1_n": int((market_pick == 1).sum()),
        "descriptive_result": "AI_UNDERPERFORMED_MARKET_ON_BOTH_PROBABILISTIC_METRICS_AND_TOP1_ACCURACY",
        "bet_decision": BET_DECISION,
        "original_primary_cohort_size": PRIMARY_COHORT_SIZE,
        "original_first_permitted_outcome_read_utc": FIRST_PERMITTED_OUTCOME_READ_UTC.isoformat(),
        "future_primary_claim_status": "PRISTINE_PRIMARY_NO_PEEK_CLAIM_NO_LONGER_AVAILABLE",
    }
