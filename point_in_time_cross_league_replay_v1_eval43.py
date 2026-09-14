"""Evaluate the mature 43-event slice of POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1.

The slice is frozen by kickoff maturity only, before any target outcomes are read.
Four not-yet-mature events are rolled into the next sample.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from point_in_time_cross_league_replay_v1_evaluation import (
    MODEL_COLUMNS,
    MARKET_COLUMNS,
    multiclass_brier,
    multiclass_log_loss,
    top1_accuracy,
    descriptive_status,
)

EXPERIMENT_ID = "POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1_EVAL43"
FREEZE_PATH = Path("experiments/point_in_time_cross_league_replay_v1_eval43_freeze.json")
SELECTION_CUTOFF_UTC = datetime(2026, 9, 14, 15, 17, 18, tzinfo=UTC)
EXPECTED_TOTAL = 43
EXPECTED_COUNTS = {
    "BUNDESLIGA": 9,
    "EREDIVISIE": 9,
    "LA_LIGA": 9,
    "LIGUE_1": 9,
    "SERIE_A": 7,
}
EXPECTED_INCLUDED_SHA256 = "d83a0a7d4e835e17e3f12848c223326cc9bcc2a371588503f3c0c285c850f1f0"
EXPECTED_ROLLOVER_SHA256 = "41402534c1c628184670efeebe9f2ce85226d5b958175ccfc26e46e7f6b09697"
OUTCOMES = ("H", "D", "A")
BET_DECISION = "NO_BET"


def _canonical_sha(rows: list[dict]) -> str:
    text = "\n".join(
        json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        for row in rows
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_and_validate_freeze(path: Path = FREEZE_PATH) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload["experiment_id"] != EXPERIMENT_ID:
        raise RuntimeError("eval43 experiment id drifted")
    if payload["outcome_fields_read_before_freeze"] is not False:
        raise RuntimeError("eval43 no-peek attestation drifted")
    if payload["included_total"] != EXPECTED_TOTAL:
        raise RuntimeError("eval43 event count drifted")
    if payload["included_league_counts"] != EXPECTED_COUNTS:
        raise RuntimeError("eval43 league counts drifted")
    if payload["included_identities_sha256"] != EXPECTED_INCLUDED_SHA256:
        raise RuntimeError("eval43 embedded included hash drifted")
    if payload["rollover_identities_sha256"] != EXPECTED_ROLLOVER_SHA256:
        raise RuntimeError("eval43 embedded rollover hash drifted")
    if _canonical_sha(payload["included"]) != EXPECTED_INCLUDED_SHA256:
        raise RuntimeError("eval43 included identities changed")
    if _canonical_sha(payload["rollover_next_sample"]) != EXPECTED_ROLLOVER_SHA256:
        raise RuntimeError("eval43 rollover identities changed")
    if len(payload["rollover_next_sample"]) != 4:
        raise RuntimeError("eval43 rollover count drifted")
    cutoff = pd.Timestamp(payload["selection_cutoff_utc"])
    for row in payload["included"]:
        if pd.Timestamp(row["mature_at_utc"]) > cutoff:
            raise RuntimeError("non-mature event leaked into eval43")
    for row in payload["rollover_next_sample"]:
        if pd.Timestamp(row["mature_at_utc"]) <= cutoff:
            raise RuntimeError("mature event incorrectly rolled over")
    return payload


def expected_identities() -> set[tuple[str, str]]:
    payload = load_and_validate_freeze()
    return {(str(r["league"]), str(r["event_id"])) for r in payload["included"]}


def require_gate_open(now_utc: datetime) -> None:
    if now_utc.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware")
    if now_utc.astimezone(UTC) < SELECTION_CUTOFF_UTC:
        raise RuntimeError("eval43 outcome read attempted before frozen cutoff")


def _probability_matrix(frame: pd.DataFrame, columns: tuple[str, str, str], label: str) -> np.ndarray:
    matrix = frame.loc[:, list(columns)].astype(float).to_numpy()
    if matrix.shape != (EXPECTED_TOTAL, 3):
        raise ValueError(f"{label} matrix has wrong shape: {matrix.shape}")
    if not np.isfinite(matrix).all() or (matrix < 0).any() or (matrix > 1).any():
        raise ValueError(f"invalid {label} probabilities")
    if not np.allclose(matrix.sum(axis=1), 1.0, atol=1e-9, rtol=0):
        raise ValueError(f"{label} probabilities do not sum to one")
    return matrix


def _targets(results: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    values = results.astype(str).to_numpy()
    if len(values) != EXPECTED_TOTAL or not set(values).issubset(OUTCOMES):
        raise ValueError("eval43 requires exactly 43 H/D/A outcomes")
    indices = np.asarray([OUTCOMES.index(v) for v in values], dtype=int)
    target = np.zeros((EXPECTED_TOTAL, 3), dtype=float)
    target[np.arange(EXPECTED_TOTAL), indices] = 1.0
    return target, indices


def evaluate(frame: pd.DataFrame) -> dict:
    required = {"league", "event_id", "result", *MODEL_COLUMNS, *MARKET_COLUMNS}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing evaluation columns: {sorted(missing)}")
    if len(frame) != EXPECTED_TOTAL:
        raise ValueError("eval43 requires exactly 43 rows")
    if frame.duplicated(["league", "event_id"]).any():
        raise ValueError("duplicate eval43 identity")
    observed = set(zip(frame["league"].astype(str), frame["event_id"].astype(str)))
    if observed != expected_identities():
        raise ValueError("evaluation identities differ from frozen eval43 cohort")
    counts = frame.groupby("league")["event_id"].nunique().to_dict()
    if counts != EXPECTED_COUNTS:
        raise ValueError(f"eval43 league counts drifted: {counts}")

    model = _probability_matrix(frame, MODEL_COLUMNS, "model")
    market = _probability_matrix(frame, MARKET_COLUMNS, "market")
    target, target_indices = _targets(frame["result"])

    model_brier = multiclass_brier(model, target)
    market_brier = multiclass_brier(market, target)
    model_log_loss = multiclass_log_loss(model, target_indices)
    market_log_loss = multiclass_log_loss(market, target_indices)
    model_accuracy = top1_accuracy(model, target_indices)
    market_accuracy = top1_accuracy(market, target_indices)
    delta_brier = model_brier - market_brier
    delta_log_loss = model_log_loss - market_log_loss

    model_pick = np.argmax(model, axis=1)
    market_pick = np.argmax(market, axis=1)
    disagree = model_pick != market_pick
    if int(disagree.sum()) != 10:
        raise RuntimeError("pre-frozen disagreement count drifted from 10")
    model_correct = model_pick == target_indices
    market_correct = market_pick == target_indices

    return {
        "experiment_id": EXPERIMENT_ID,
        "n": EXPECTED_TOTAL,
        "rollover_next_sample_n": 4,
        "model_brier": model_brier,
        "market_brier": market_brier,
        "delta_brier_ai_minus_market": delta_brier,
        "model_log_loss": model_log_loss,
        "market_log_loss": market_log_loss,
        "delta_log_loss_ai_minus_market": delta_log_loss,
        "model_accuracy": model_accuracy,
        "market_accuracy": market_accuracy,
        "model_correct_n": int(model_correct.sum()),
        "market_correct_n": int(market_correct.sum()),
        "disagreement_n": int(disagree.sum()),
        "disagreement_ai_correct_market_wrong": int((disagree & model_correct & ~market_correct).sum()),
        "disagreement_market_correct_ai_wrong": int((disagree & market_correct & ~model_correct).sum()),
        "disagreement_both_wrong": int((disagree & ~model_correct & ~market_correct).sum()),
        "status": descriptive_status(delta_brier, delta_log_loss),
        "bet_decision": BET_DECISION,
    }
