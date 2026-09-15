"""Evaluate the frozen 2026-09-15 La Liga prospective Market Anchor cohort.

This evaluator is intentionally outcome-separated from the prediction runner. It accepts only
three final H/D/A labels after the predeclared evaluation-not-before time and never refits or
retunes the model. Primary metrics: multiclass Brier and log loss. Accuracy is secondary.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

EXPERIMENT_ID = "LA_LIGA_MARKET_ANCHOR_PROSPECTIVE_20260915_V1"
EXPECTED_EVENT_IDS = {
    "b9a6e597fd597637efa24b92d51dda62",
    "d6474326396cdd0e300afd0193c7c93d",
    "0b57607f4a514ee24df31b0c2db9ddc5",
}
RESULT_TO_INT = {"H": 0, "D": 1, "A": 2}
EVALUATION_NOT_BEFORE = pd.Timestamp("2026-09-15T21:30:00Z")


def _sha256_json(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_freeze(report: Mapping[str, Any]) -> None:
    if report.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError("wrong experiment_id")
    if report.get("evidence_class") != "PROSPECTIVE_SHADOW":
        raise ValueError("freeze is not prospective shadow evidence")
    if report.get("outcomes_available_to_runner") is not False:
        raise ValueError("freeze runner must be outcome-blind")
    if float(report.get("active_lambda")) != 0.0 or float(report.get("shadow_lambda")) != 1.0:
        raise ValueError("lambda contract changed")
    rows = report.get("predictions")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("freeze must contain exactly three predictions")
    ids = {str(row["event_id"]) for row in rows}
    if ids != EXPECTED_EVENT_IDS:
        raise ValueError("freeze event identity changed")
    supplied = report.get("freeze_sha256")
    body = dict(report)
    body.pop("freeze_sha256", None)
    if supplied != _sha256_json(body):
        raise ValueError("freeze sha256 mismatch")
    for row in rows:
        market = np.asarray(row["market_probabilities"], dtype=float)
        active = np.asarray(row["active_lambda_0_probabilities"], dtype=float)
        shadow = np.asarray(row["shadow_lambda_1_probabilities"], dtype=float)
        for name, p in (("market", market), ("active", active), ("shadow", shadow)):
            if p.shape != (3,) or not np.isfinite(p).all() or (p <= 0).any() or not np.isclose(p.sum(), 1.0, atol=1e-10):
                raise ValueError(f"invalid {name} probabilities")
        if not np.allclose(active, market, atol=1e-15, rtol=0):
            raise ValueError("active lambda=0 must equal market")


def validate_outcomes(outcomes: Mapping[str, Any]) -> dict[str, str]:
    if set(outcomes) != EXPECTED_EVENT_IDS:
        raise ValueError("outcomes must contain exactly the three frozen event_ids")
    result = {str(k): str(v).upper() for k, v in outcomes.items()}
    bad = {k: v for k, v in result.items() if v not in RESULT_TO_INT}
    if bad:
        raise ValueError(f"invalid H/D/A outcomes: {bad}")
    return result


def score(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    one_hot = np.eye(3)[y]
    brier = float(np.mean(np.sum((p - one_hot) ** 2, axis=1)))
    chosen = np.clip(p[np.arange(len(y)), y], 1e-15, 1.0)
    log_loss = float(-np.mean(np.log(chosen)))
    accuracy = float(np.mean(np.argmax(p, axis=1) == y))
    return {"brier": brier, "log_loss": log_loss, "accuracy": accuracy}


def evaluate(freeze: Mapping[str, Any], outcomes: Mapping[str, Any], now_utc: pd.Timestamp | None = None) -> dict[str, Any]:
    validate_freeze(freeze)
    labels = validate_outcomes(outcomes)
    now = now_utc or pd.Timestamp(datetime.now(timezone.utc))
    now = now.tz_convert("UTC") if now.tzinfo is not None else now.tz_localize("UTC")
    if now < EVALUATION_NOT_BEFORE:
        raise RuntimeError("outcome gate is still closed")

    rows = freeze["predictions"]
    y = np.asarray([RESULT_TO_INT[labels[str(row["event_id"])]] for row in rows], dtype=int)
    market = np.asarray([row["market_probabilities"] for row in rows], dtype=float)
    shadow = np.asarray([row["shadow_lambda_1_probabilities"] for row in rows], dtype=float)
    market_score = score(y, market)
    shadow_score = score(y, shadow)

    per_match = []
    for i, row in enumerate(rows):
        yi = y[i]
        market_brier = float(np.sum((market[i] - np.eye(3)[yi]) ** 2))
        shadow_brier = float(np.sum((shadow[i] - np.eye(3)[yi]) ** 2))
        market_ll = float(-math.log(max(float(market[i, yi]), 1e-15)))
        shadow_ll = float(-math.log(max(float(shadow[i, yi]), 1e-15)))
        per_match.append({
            "event_id": row["event_id"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "result": labels[str(row["event_id"])],
            "market_brier": market_brier,
            "shadow_brier": shadow_brier,
            "delta_brier": shadow_brier - market_brier,
            "market_log_loss": market_ll,
            "shadow_log_loss": shadow_ll,
            "delta_log_loss": shadow_ll - market_ll,
        })

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "PROSPECTIVE_MICRO_COHORT_EVALUATION",
        "cohort_n": 3,
        "freeze_sha256": freeze["freeze_sha256"],
        "evaluation_time_utc": now.isoformat(),
        "market": market_score,
        "shadow_lambda_1": shadow_score,
        "delta_brier_vs_market": shadow_score["brier"] - market_score["brier"],
        "delta_log_loss_vs_market": shadow_score["log_loss"] - market_score["log_loss"],
        "delta_accuracy_vs_market": shadow_score["accuracy"] - market_score["accuracy"],
        "dual_probabilistic_metric_win": bool(
            shadow_score["brier"] < market_score["brier"] and shadow_score["log_loss"] < market_score["log_loss"]
        ),
        "interpretation_limit": "Three-match prospective micro-cohort only; never sufficient for production promotion by itself.",
        "per_match": per_match,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--outcomes", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/la_liga_market_anchor_prospective_20260915/evaluation.json"))
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    outcomes = json.loads(args.outcomes.read_text(encoding="utf-8"))
    report = evaluate(freeze, outcomes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
