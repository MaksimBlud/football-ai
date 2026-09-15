"""Research-only benchmark of bookmaker 1X2 de-vigging methods.

Selection uses 2024-2025 only; 2025-2026 is untouched temporal OOT. No production
artifacts, Supabase state, paid APIs, or opened 2026-27 outcomes are used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from historical_football_signal_runner import LEAGUES, download
from market_anchor_1x2_v1 import RESULT_TO_INT, score_probabilities

EXPERIMENT_ID = "BOOKMAKER_RECONSTRUCTION_DEVIG_V1"
VALIDATION_SEASON = "2024-2025"
TEST_SEASON = "2025-2026"
METHODS = ("PROPORTIONAL", "POWER", "SHIN")
EPS = 1e-12


def _raw_implied(frame: pd.DataFrame) -> np.ndarray:
    odds = frame[["market_home", "market_draw", "market_away"]].to_numpy(float)
    if not np.isfinite(odds).all() or (odds <= 1.0).any():
        raise ValueError("decimal market odds must be finite and > 1")
    return 1.0 / odds


def proportional(q: np.ndarray) -> np.ndarray:
    return q / q.sum(axis=1, keepdims=True)


def power(q: np.ndarray) -> np.ndarray:
    out = np.empty_like(q, dtype=float)
    for i, row in enumerate(q):
        f = lambda k: float(np.power(row, k).sum() - 1.0)
        k = brentq(f, 0.01, 20.0)
        out[i] = np.power(row, k)
    return out


def shin(q: np.ndarray) -> np.ndarray:
    out = np.empty_like(q, dtype=float)
    for i, row in enumerate(q):
        s = float(row.sum())
        if s <= 1.0:
            out[i] = row / s
            continue
        def probs(z: float) -> np.ndarray:
            return (np.sqrt(z * z + 4.0 * (1.0 - z) * row * row / s) - z) / (2.0 * (1.0 - z))
        f = lambda z: float(probs(z).sum() - 1.0)
        try:
            z = brentq(f, 0.0, 1.0 - 1e-10)
            p = probs(z)
            out[i] = p / p.sum()
        except ValueError:
            out[i] = row / s
    return out


def probabilities(frame: pd.DataFrame, method: str) -> np.ndarray:
    q = _raw_implied(frame)
    if method == "PROPORTIONAL": return proportional(q)
    if method == "POWER": return power(q)
    if method == "SHIN": return shin(q)
    raise ValueError(f"unknown method: {method}")


def _score(frame: pd.DataFrame, method: str) -> dict[str, float]:
    y = frame["result"].map(RESULT_TO_INT).to_numpy()
    return score_probabilities(y, probabilities(frame, method))


def evaluate_frame(frame: pd.DataFrame) -> dict:
    clean = frame[frame["result"].isin(RESULT_TO_INT)].dropna(subset=["market_home", "market_draw", "market_away"]).copy()
    leagues = []
    pooled_val, pooled_test = [], []
    for league, g in clean.groupby("league"):
        val = g[g["season"] == VALIDATION_SEASON].copy()
        test = g[g["season"] == TEST_SEASON].copy()
        if val.empty or test.empty: raise RuntimeError(f"{league}: missing validation/test season")
        val_scores = {m: _score(val, m) for m in METHODS}
        selected = min(METHODS, key=lambda m: (val_scores[m]["log_loss"], val_scores[m]["brier"], m))
        test_scores = {m: _score(test, m) for m in METHODS}
        leagues.append({"league": league, "validation_n": len(val), "test_n": len(test), "selected_on_validation": selected,
                        "validation": val_scores, "untouched_test": test_scores,
                        "selected_test": test_scores[selected]})
        pooled_val.append(val); pooled_test.append(test)
    pv, pt = pd.concat(pooled_val), pd.concat(pooled_test)
    pooled_validation = {m: _score(pv, m) for m in METHODS}
    pooled_selected = min(METHODS, key=lambda m: (pooled_validation[m]["log_loss"], pooled_validation[m]["brier"], m))
    pooled_test = {m: _score(pt, m) for m in METHODS}
    base = pooled_test["PROPORTIONAL"]
    return {"experiment_id": EXPERIMENT_ID, "research_only": True, "production_promotion": False,
            "opened_2026_27_outcomes_used": False, "validation_season": VALIDATION_SEASON,
            "untouched_test_season": TEST_SEASON, "methods": list(METHODS), "selection_metric": "validation LogLoss, then Brier",
            "pooled_selected_on_validation": pooled_selected, "pooled_validation": pooled_validation,
            "pooled_untouched_test": pooled_test,
            "pooled_selected_test_delta_vs_proportional": {
                "brier": pooled_test[pooled_selected]["brier"] - base["brier"],
                "log_loss": pooled_test[pooled_selected]["log_loss"] - base["log_loss"]},
            "league_reports": leagues}


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--work-dir", type=Path, default=Path("artifacts/bookmaker_reconstruction_devig_v1/work")); p.add_argument("--output", type=Path, default=Path("artifacts/bookmaker_reconstruction_devig_v1/report.json")); a = p.parse_args()
    frame = pd.concat([download(cfg, league, a.work_dir / league.lower()) for league, cfg in LEAGUES.items()], ignore_index=True)
    report = evaluate_frame(frame); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"); print(json.dumps(report, indent=2, sort_keys=True))

if __name__ == "__main__": main()
