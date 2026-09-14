"""Outcome evaluation contract for POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1.

The replay predictions were frozen before target reads.  This module keeps
outcome access and scoring separate from reconstruction and refuses evaluation
before every frozen fixture has had a conservative four-hour settlement
window.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from point_in_time_cross_league_replay_v1_freeze_guard import (
    EXPECTED_COUNTS,
    EXPECTED_PREDICTIONS_CANONICAL_SHA256,
    EXPECTED_TOTAL_EVENTS,
    validate_frozen_predictions,
)

EXPERIMENT_ID = "POINT_IN_TIME_CROSS_LEAGUE_REPLAY_V1"
FROZEN_PREDICTIONS_PATH = Path(
    "experiments/point_in_time_cross_league_replay_v1_predictions.json"
)
# Latest frozen kickoff is 2026-09-14T19:00:00Z.  Four hours mirrors the
# conservative result-availability buffer used during reconstruction.
FIRST_PERMITTED_OUTCOME_READ_UTC = datetime(2026, 9, 14, 23, 0, 0, tzinfo=UTC)
BET_DECISION = "NO_BET"

OUTCOMES = ("H", "D", "A")
MODEL_COLUMNS = ("model_home_prob", "model_draw_prob", "model_away_prob")
MARKET_COLUMNS = ("market_home_prob", "market_draw_prob", "market_away_prob")


def outcome_read_gate(now_utc: datetime) -> dict:
    if now_utc.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware")
    now = now_utc.astimezone(UTC)
    allowed = now >= FIRST_PERMITTED_OUTCOME_READ_UTC
    return {
        "allowed": allowed,
        "first_permitted_outcome_read_utc": FIRST_PERMITTED_OUTCOME_READ_UTC.isoformat(),
        "reason": "GATE_OPEN" if allowed else "FROZEN_COHORT_NOT_FULLY_MATURE",
    }


def require_outcome_read_gate(now_utc: datetime) -> None:
    gate = outcome_read_gate(now_utc)
    if not gate["allowed"]:
        raise RuntimeError(
            "Outcome read forbidden before "
            + gate["first_permitted_outcome_read_utc"]
        )


def frozen_identities(path: Path = FROZEN_PREDICTIONS_PATH) -> set[tuple[str, str]]:
    payload = validate_frozen_predictions(path)
    if payload["predictions_canonical_sha256"] != EXPECTED_PREDICTIONS_CANONICAL_SHA256:
        raise RuntimeError("frozen prediction hash mismatch")
    return {
        (str(row["league"]), str(row["event_id"]))
        for row in payload["predictions"]
    }


def _validate_probability_matrix(frame: pd.DataFrame, columns: tuple[str, str, str], label: str) -> np.ndarray:
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"missing {label} probability columns: {sorted(missing)}")
    matrix = frame.loc[:, list(columns)].astype(float).to_numpy()
    if matrix.shape != (EXPECTED_TOTAL_EVENTS, 3):
        raise ValueError(f"{label} probability matrix has wrong shape: {matrix.shape}")
    if not np.isfinite(matrix).all():
        raise ValueError(f"{label} probabilities must be finite")
    if (matrix < 0).any() or (matrix > 1).any():
        raise ValueError(f"{label} probabilities must be in [0, 1]")
    if not np.allclose(matrix.sum(axis=1), 1.0, atol=1e-9, rtol=0):
        raise ValueError(f"{label} probabilities must sum to one")
    return matrix


def _target_matrix(results: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    values = results.astype(str).to_numpy()
    if not set(values).issubset(OUTCOMES):
        raise ValueError("results must contain only H/D/A")
    if len(values) != EXPECTED_TOTAL_EVENTS:
        raise ValueError("result count must equal frozen cohort size")
    indices = np.asarray([OUTCOMES.index(value) for value in values], dtype=int)
    targets = np.zeros((len(indices), 3), dtype=float)
    targets[np.arange(len(indices)), indices] = 1.0
    return targets, indices


def multiclass_brier(probabilities: np.ndarray, targets: np.ndarray) -> float:
    return float(np.mean(np.sum((probabilities - targets) ** 2, axis=1)))


def multiclass_log_loss(probabilities: np.ndarray, target_indices: np.ndarray) -> float:
    clipped = np.clip(probabilities, 1e-15, 1.0)
    return float(-np.mean(np.log(clipped[np.arange(len(target_indices)), target_indices])))


def top1_accuracy(probabilities: np.ndarray, target_indices: np.ndarray) -> float:
    return float(np.mean(np.argmax(probabilities, axis=1) == target_indices))


def descriptive_status(delta_brier: float, delta_log_loss: float) -> str:
    if delta_brier < 0 and delta_log_loss < 0:
        return "EARLY_SIGNAL"
    if delta_brier > 0 and delta_log_loss > 0:
        return "WARNING"
    return "INCONCLUSIVE"


def evaluate_frozen_replay(frame: pd.DataFrame, *, frozen_path: Path = FROZEN_PREDICTIONS_PATH) -> dict:
    required = {"league", "event_id", "result", *MODEL_COLUMNS, *MARKET_COLUMNS}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"evaluation frame missing columns: {sorted(missing)}")
    if len(frame) != EXPECTED_TOTAL_EVENTS:
        raise ValueError(f"evaluation requires exactly {EXPECTED_TOTAL_EVENTS} rows")
    if frame.duplicated(["league", "event_id"]).any():
        raise ValueError("duplicate evaluation identity")

    observed = set(zip(frame["league"].astype(str), frame["event_id"].astype(str)))
    expected = frozen_identities(frozen_path)
    if observed != expected:
        missing_ids = sorted(expected - observed)[:5]
        extra_ids = sorted(observed - expected)[:5]
        raise ValueError(
            f"evaluation identities differ from freeze; missing={missing_ids}, extra={extra_ids}"
        )

    counts = frame.groupby("league")["event_id"].nunique().to_dict()
    if counts != EXPECTED_COUNTS:
        raise ValueError(f"league counts differ from freeze: {counts}")

    model = _validate_probability_matrix(frame, MODEL_COLUMNS, "model")
    market = _validate_probability_matrix(frame, MARKET_COLUMNS, "market")
    targets, target_indices = _target_matrix(frame["result"])

    model_brier = multiclass_brier(model, targets)
    market_brier = multiclass_brier(market, targets)
    model_log_loss = multiclass_log_loss(model, target_indices)
    market_log_loss = multiclass_log_loss(market, target_indices)
    model_accuracy = top1_accuracy(model, target_indices)
    market_accuracy = top1_accuracy(market, target_indices)
    delta_brier = model_brier - market_brier
    delta_log_loss = model_log_loss - market_log_loss

    return {
        "experiment_id": EXPERIMENT_ID,
        "n": EXPECTED_TOTAL_EVENTS,
        "model_brier": model_brier,
        "market_brier": market_brier,
        "delta_brier_ai_minus_market": delta_brier,
        "model_log_loss": model_log_loss,
        "market_log_loss": market_log_loss,
        "delta_log_loss_ai_minus_market": delta_log_loss,
        "model_accuracy": model_accuracy,
        "market_accuracy": market_accuracy,
        "status": descriptive_status(delta_brier, delta_log_loss),
        "bet_decision": BET_DECISION,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evaluation_csv")
    parser.add_argument("--output")
    args = parser.parse_args()

    # Gate is checked BEFORE the file containing target outcomes is opened.
    require_outcome_read_gate(datetime.now(UTC))
    frame = pd.read_csv(args.evaluation_csv)
    report = evaluate_frozen_replay(frame)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
