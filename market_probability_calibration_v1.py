"""MARKET_PROBABILITY_CALIBRATION_V1.

Research-only temporal walk-forward calibration of the existing multiplicative
1X2 market prior. No production state is modified.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
from scipy.optimize import minimize, minimize_scalar

from market_devig_methods_v1 import (
    actual_indices,
    apply_method,
    calibration_diagnostics,
    load_market_history,
    per_match_losses,
)

EXPERIMENT_ID = "MARKET_PROBABILITY_CALIBRATION_V1"
OUTPUT_DIR = Path("artifacts/market_probability_calibration_v1")
OUTPUT_PATH = OUTPUT_DIR / "report.json"

SEASONS = [
    "2019/2020",
    "2020/2021",
    "2021/2022",
    "2022/2023",
    "2023/2024",
    "2024/2025",
    "2025/2026",
]
OUTER_TEST_SEASONS = SEASONS[3:]
METHODS = (
    "RAW_MULTIPLICATIVE",
    "TEMPERATURE",
    "CLASS_BIAS",
    "TEMPERATURE_BIAS",
)
CANDIDATES = METHODS[1:]

TEMP_BOUNDS = (0.50, 2.00)
BIAS_BOUNDS = (-0.50, 0.50)
EPS = 1e-12
BOOTSTRAP_SAMPLES = 10000
BOOTSTRAP_SEED = 20260929


def validate_probabilities(probabilities: np.ndarray) -> np.ndarray:
    p = np.asarray(probabilities, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) == 0:
        raise ValueError("probabilities must be a non-empty Nx3 matrix")
    if not np.isfinite(p).all() or (p <= 0.0).any() or (p >= 1.0).any():
        raise ValueError("probabilities must be finite and strictly inside (0, 1)")
    if not np.allclose(p.sum(axis=1), 1.0, atol=1e-10):
        raise ValueError("probability rows must sum to one")
    return p


def softmax(logits: np.ndarray) -> np.ndarray:
    values = np.asarray(logits, dtype=float)
    values = values - values.max(axis=1, keepdims=True)
    exp_values = np.exp(values)
    return exp_values / exp_values.sum(axis=1, keepdims=True)


def transform_probabilities(
    probabilities: np.ndarray,
    *,
    temperature: float = 1.0,
    home_bias: float = 0.0,
    away_bias: float = 0.0,
) -> np.ndarray:
    p = validate_probabilities(probabilities)
    if not (TEMP_BOUNDS[0] <= temperature <= TEMP_BOUNDS[1]):
        raise ValueError("temperature outside frozen bounds")
    if not (BIAS_BOUNDS[0] <= home_bias <= BIAS_BOUNDS[1]):
        raise ValueError("home_bias outside frozen bounds")
    if not (BIAS_BOUNDS[0] <= away_bias <= BIAS_BOUNDS[1]):
        raise ValueError("away_bias outside frozen bounds")

    logits = np.log(np.clip(p, EPS, 1.0)) / float(temperature)
    logits = logits + np.asarray([home_bias, 0.0, away_bias], dtype=float)
    return validate_probabilities(softmax(logits))


def nll(y: np.ndarray, probabilities: np.ndarray) -> float:
    p = validate_probabilities(probabilities)
    y = np.asarray(y, dtype=int)
    actual = np.clip(p[np.arange(len(y)), y], EPS, 1.0)
    return float(-np.mean(np.log(actual)))


def fit_temperature(probabilities: np.ndarray, y: np.ndarray) -> dict:
    result = minimize_scalar(
        lambda t: nll(
            y,
            transform_probabilities(probabilities, temperature=float(t)),
        ),
        bounds=TEMP_BOUNDS,
        method="bounded",
        options={"xatol": 1e-12},
    )
    if not result.success or not math.isfinite(float(result.x)):
        raise RuntimeError("temperature optimization failed")
    return {
        "temperature": float(result.x),
        "home_bias": 0.0,
        "away_bias": 0.0,
        "train_logloss": float(result.fun),
    }


def fit_class_bias(probabilities: np.ndarray, y: np.ndarray) -> dict:
    def objective(values: np.ndarray) -> float:
        return nll(
            y,
            transform_probabilities(
                probabilities,
                home_bias=float(values[0]),
                away_bias=float(values[1]),
            ),
        )

    result = minimize(
        objective,
        x0=np.zeros(2, dtype=float),
        method="L-BFGS-B",
        bounds=[BIAS_BOUNDS, BIAS_BOUNDS],
        options={"ftol": 1e-15, "maxiter": 1000},
    )
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"class-bias optimization failed: {result.message}")
    return {
        "temperature": 1.0,
        "home_bias": float(result.x[0]),
        "away_bias": float(result.x[1]),
        "train_logloss": float(result.fun),
    }


def fit_temperature_bias(probabilities: np.ndarray, y: np.ndarray) -> dict:
    def objective(values: np.ndarray) -> float:
        return nll(
            y,
            transform_probabilities(
                probabilities,
                temperature=float(values[0]),
                home_bias=float(values[1]),
                away_bias=float(values[2]),
            ),
        )

    result = minimize(
        objective,
        x0=np.asarray([1.0, 0.0, 0.0], dtype=float),
        method="L-BFGS-B",
        bounds=[TEMP_BOUNDS, BIAS_BOUNDS, BIAS_BOUNDS],
        options={"ftol": 1e-15, "maxiter": 1000},
    )
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"temperature+bias optimization failed: {result.message}")
    return {
        "temperature": float(result.x[0]),
        "home_bias": float(result.x[1]),
        "away_bias": float(result.x[2]),
        "train_logloss": float(result.fun),
    }


def fit_candidate(method: str, probabilities: np.ndarray, y: np.ndarray) -> dict:
    if method == "TEMPERATURE":
        return fit_temperature(probabilities, y)
    if method == "CLASS_BIAS":
        return fit_class_bias(probabilities, y)
    if method == "TEMPERATURE_BIAS":
        return fit_temperature_bias(probabilities, y)
    raise ValueError(f"unsupported candidate method: {method}")


def apply_candidate(method: str, probabilities: np.ndarray, parameters: dict) -> np.ndarray:
    if method == "RAW_MULTIPLICATIVE":
        return validate_probabilities(probabilities.copy())
    return transform_probabilities(
        probabilities,
        temperature=float(parameters["temperature"]),
        home_bias=float(parameters["home_bias"]),
        away_bias=float(parameters["away_bias"]),
    )


def score(frame: pd.DataFrame, probabilities: np.ndarray) -> tuple[dict, pd.DataFrame]:
    losses = per_match_losses(frame, probabilities).reset_index(drop=True)
    y = actual_indices(frame)
    return {
        "matches": int(len(frame)),
        "logloss": float(losses["logloss"].mean()),
        "brier": float(losses["brier"].mean()),
        "accuracy": float((probabilities.argmax(axis=1) == y).mean()),
        "calibration": calibration_diagnostics(frame, probabilities),
    }, losses


def bootstrap_delta(candidate: np.ndarray, baseline: np.ndarray) -> dict:
    delta = np.asarray(candidate, dtype=float) - np.asarray(baseline, dtype=float)
    if delta.ndim != 1 or len(delta) == 0:
        raise ValueError("bootstrap delta must be a non-empty vector")

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n = len(delta)
    means = np.empty(BOOTSTRAP_SAMPLES, dtype=float)
    for index in range(BOOTSTRAP_SAMPLES):
        sample = rng.integers(0, n, size=n)
        means[index] = float(delta[sample].mean())

    return {
        "mean_delta_candidate_minus_baseline": float(delta.mean()),
        "ci95_low": float(np.quantile(means, 0.025)),
        "ci95_high": float(np.quantile(means, 0.975)),
        "bootstrap_probability_candidate_better": float((means < 0.0).mean()),
        "samples": BOOTSTRAP_SAMPLES,
        "seed": BOOTSTRAP_SEED,
    }


def evaluate(frame: pd.DataFrame) -> dict:
    if list(frame["season"].drop_duplicates()) != SEASONS:
        raise RuntimeError("market history is not ordered by frozen season contract")

    raw_all, _ = apply_method(frame, "MULTIPLICATIVE")
    frame = frame.reset_index(drop=True)

    fold_rows: list[dict] = []
    pooled_losses: dict[str, list[pd.DataFrame]] = {method: [] for method in METHODS}
    pooled_probabilities: dict[str, list[np.ndarray]] = {method: [] for method in METHODS}
    pooled_frames: list[pd.DataFrame] = []

    for test_season in OUTER_TEST_SEASONS:
        test_index = SEASONS.index(test_season)
        train_seasons = SEASONS[:test_index]
        train_mask = frame["season"].isin(train_seasons).to_numpy()
        test_mask = frame["season"].eq(test_season).to_numpy()

        train_frame = frame.loc[train_mask].reset_index(drop=True)
        test_frame = frame.loc[test_mask].reset_index(drop=True)
        train_p = raw_all[train_mask]
        test_p = raw_all[test_mask]
        y_train = actual_indices(train_frame)

        fold = {
            "test_season": test_season,
            "train_seasons": train_seasons,
            "train_matches": int(len(train_frame)),
            "test_matches": int(len(test_frame)),
            "methods": {},
        }

        raw_metrics, raw_losses = score(test_frame, test_p)
        fold["methods"]["RAW_MULTIPLICATIVE"] = {
            "metrics": raw_metrics,
            "parameters": {
                "temperature": 1.0,
                "home_bias": 0.0,
                "away_bias": 0.0,
            },
        }
        pooled_losses["RAW_MULTIPLICATIVE"].append(raw_losses)
        pooled_probabilities["RAW_MULTIPLICATIVE"].append(test_p)

        for method in CANDIDATES:
            parameters = fit_candidate(method, train_p, y_train)
            candidate_p = apply_candidate(method, test_p, parameters)
            metrics, losses = score(test_frame, candidate_p)
            fold["methods"][method] = {
                "metrics": metrics,
                "parameters": parameters,
                "delta_vs_raw": {
                    "logloss": float(metrics["logloss"] - raw_metrics["logloss"]),
                    "brier": float(metrics["brier"] - raw_metrics["brier"]),
                },
                "joint_win": bool(
                    metrics["logloss"] < raw_metrics["logloss"]
                    and metrics["brier"] < raw_metrics["brier"]
                ),
            }
            pooled_losses[method].append(losses)
            pooled_probabilities[method].append(candidate_p)

        pooled_frames.append(test_frame)
        fold_rows.append(fold)

    pooled_frame = pd.concat(pooled_frames, ignore_index=True)
    pooled_summary: dict[str, dict] = {}
    combined_losses: dict[str, pd.DataFrame] = {}

    for method in METHODS:
        combined_losses[method] = pd.concat(
            pooled_losses[method], ignore_index=True
        )
        probabilities = np.vstack(pooled_probabilities[method])
        metrics, _ = score(pooled_frame, probabilities)
        pooled_summary[method] = metrics

    baseline = pooled_summary["RAW_MULTIPLICATIVE"]
    candidate_decisions: dict[str, dict] = {}
    supported: list[str] = []

    for method in CANDIDATES:
        metrics = pooled_summary[method]
        joint_wins = int(
            sum(
                fold["methods"][method]["joint_win"]
                for fold in fold_rows
            )
        )
        bootstrap = {
            key: bootstrap_delta(
                combined_losses[method][key].to_numpy(dtype=float),
                combined_losses["RAW_MULTIPLICATIVE"][key].to_numpy(dtype=float),
            )
            for key in ("logloss", "brier")
        }
        is_supported = bool(
            metrics["logloss"] < baseline["logloss"]
            and metrics["brier"] < baseline["brier"]
            and joint_wins >= 3
            and bootstrap["logloss"]["ci95_high"] < 0.0
            and bootstrap["brier"]["ci95_high"] < 0.0
        )
        candidate_decisions[method] = {
            "pooled_delta_vs_raw": {
                "logloss": float(metrics["logloss"] - baseline["logloss"]),
                "brier": float(metrics["brier"] - baseline["brier"]),
            },
            "joint_season_wins": joint_wins,
            "paired_bootstrap": bootstrap,
            "supported": is_supported,
        }
        if is_supported:
            supported.append(method)

    if supported:
        active_method = min(
            supported,
            key=lambda method: (
                pooled_summary[method]["logloss"],
                pooled_summary[method]["brier"],
                method,
            ),
        )
        interpretation = "MARKET_CALIBRATION_SUPPORTED"
    else:
        active_method = "RAW_MULTIPLICATIVE"
        interpretation = "KEEP_RAW_MULTIPLICATIVE"

    return {
        "outer_test_seasons": OUTER_TEST_SEASONS,
        "outer_fold_count": len(fold_rows),
        "pooled_oos_matches": int(len(pooled_frame)),
        "folds": fold_rows,
        "pooled_metrics": pooled_summary,
        "candidate_decisions": candidate_decisions,
        "supported_candidates": supported,
        "active_method": active_method,
        "interpretation": interpretation,
    }


def main() -> int:
    frame = load_market_history()
    result = evaluate(frame)

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_EXPANDING_SEASON_OOS",
        "research_only": True,
        "production_promotion": False,
        "supabase_writes": False,
        "odds_api_calls": False,
        "candidate_artifact_saved": False,
        "source_rows": int(len(frame)),
        "source": "live Supabase public.matches; Football-Data AvgH/AvgD/AvgA",
        "seasons": SEASONS,
        "methods": list(METHODS),
        "temperature_bounds": list(TEMP_BOUNDS),
        "bias_bounds": list(BIAS_BOUNDS),
        "result": result,
        "package_versions": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("Research only; no production state changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
