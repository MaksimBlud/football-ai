"""Paired probability audit: does a model add information beyond the market?

Research only. Input rows must contain the same fixtures/timestamps for market and model
probabilities. Lower Brier/log loss is better; reported deltas are model minus market.
No model fitting, threshold search, Supabase writes, or production activation occurs here.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

CLASSES = ("H", "D", "A")
EPS = 1e-15


def _validate_probabilities(frame: pd.DataFrame, prefix: str) -> np.ndarray:
    cols = [f"{prefix}_{c.lower()}_prob" for c in CLASSES]
    missing = [c for c in cols if c not in frame.columns]
    if missing:
        raise ValueError(f"missing {prefix} probability columns: {missing}")
    values = frame[cols].astype(float).to_numpy()
    if not np.isfinite(values).all() or (values < 0).any() or (values > 1).any():
        raise ValueError(f"invalid {prefix} probabilities")
    if not np.allclose(values.sum(axis=1), 1.0, atol=1e-6):
        raise ValueError(f"{prefix} probabilities must sum to 1")
    return values


def paired_scores(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"actual_result"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    actual = frame["actual_result"].astype(str).str.upper()
    if not actual.isin(CLASSES).all():
        raise ValueError("actual_result must be H, D, or A")

    market = _validate_probabilities(frame, "market")
    model = _validate_probabilities(frame, "model")
    y = np.zeros_like(market)
    index = {label: idx for idx, label in enumerate(CLASSES)}
    for row, label in enumerate(actual):
        y[row, index[label]] = 1.0

    market_brier = np.square(market - y).sum(axis=1)
    model_brier = np.square(model - y).sum(axis=1)
    actual_idx = np.array([index[label] for label in actual])
    market_logloss = -np.log(np.clip(market[np.arange(len(frame)), actual_idx], EPS, 1.0))
    model_logloss = -np.log(np.clip(model[np.arange(len(frame)), actual_idx], EPS, 1.0))

    out = frame.copy()
    out["market_brier"] = market_brier
    out["model_brier"] = model_brier
    out["brier_delta_model_minus_market"] = model_brier - market_brier
    out["market_logloss"] = market_logloss
    out["model_logloss"] = model_logloss
    out["logloss_delta_model_minus_market"] = model_logloss - market_logloss
    return out


def _bootstrap_mean_ci(values: np.ndarray, *, simulations: int, seed: int) -> dict[str, float]:
    if len(values) == 0:
        return {"mean": math.nan, "ci95_low": math.nan, "ci95_high": math.nan, "p_mean_ge_0": math.nan}
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(simulations, len(values)), replace=True).mean(axis=1)
    return {
        "mean": float(values.mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "p_mean_ge_0": float((np.count_nonzero(draws >= 0) + 1) / (simulations + 1)),
    }


def audit(frame: pd.DataFrame, *, simulations: int = 20000, seed: int = 20260901) -> dict:
    scored = paired_scores(frame)
    brier_delta = scored["brier_delta_model_minus_market"].to_numpy(float)
    logloss_delta = scored["logloss_delta_model_minus_market"].to_numpy(float)
    return {
        "matches": int(len(scored)),
        "market_brier": float(scored["market_brier"].mean()),
        "model_brier": float(scored["model_brier"].mean()),
        "market_logloss": float(scored["market_logloss"].mean()),
        "model_logloss": float(scored["model_logloss"].mean()),
        "brier_delta_model_minus_market": _bootstrap_mean_ci(brier_delta, simulations=simulations, seed=seed),
        "logloss_delta_model_minus_market": _bootstrap_mean_ci(logloss_delta, simulations=simulations, seed=seed + 1),
        "interpretation": "Negative model-minus-market score deltas favor the model. A Football-AI-specific claim requires paired pre-kickoff probabilities on the same untouched fixtures; this audit does not fit or tune the model.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Paired market-vs-model incremental-information audit")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("experiments/market_model_incremental_audit.json"))
    parser.add_argument("--simulations", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=20260901)
    args = parser.parse_args()
    result = audit(pd.read_csv(args.input), simulations=args.simulations, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    print("RESEARCH ONLY: no fitting, threshold search, Supabase writes, or production activation.")


if __name__ == "__main__":
    main()
