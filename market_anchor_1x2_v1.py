"""Market-anchored 1X2 residual candidate, research only.

The bookmaker market is the mandatory prior. Football-only state may add a bounded
logit-space residual, but the active candidate fails closed to the exact de-vigged
market unless an untouched temporal OOT test improves both multiclass Brier and
LogLoss. No production model artifact is read, written, trained, or promoted.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from historical_football_signal_lab import FEATURE_SETS, RESULT_TO_INT, add_difference_features
from historical_football_signal_runner import LEAGUES, download

EXPERIMENT_ID = "MARKET_ANCHOR_1X2_V1"
TRAIN_SEASONS = tuple(f"{y}-{y+1}" for y in range(2016, 2024))
VALIDATION_SEASON = "2024-2025"
TEST_SEASON = "2025-2026"
LATEST_ALLOWED_DATE = pd.Timestamp("2026-06-30")
FEATURE_VARIANTS = ("FORM", "FORM_GOALS", "FORM_GOALS_CORNERS", "ALL_FOOTBALL")
LAMBDA_GRID = (0.0, 0.10, 0.25, 0.50, 0.75, 1.0)
L2_PENALTY = 1.0
EPS = 1e-12


def validate_probabilities(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) == 0:
        raise ValueError("probabilities must be a non-empty Nx3 matrix")
    if not np.isfinite(p).all() or (p <= 0).any() or (p >= 1).any():
        raise ValueError("probabilities must be finite and strictly inside (0, 1)")
    if not np.allclose(p.sum(axis=1), 1.0, atol=1e-10):
        raise ValueError("probability rows must sum to one")
    return p


def devig_market_probabilities(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.ndim != 2 or values.shape[1] != 3:
        raise ValueError("market input must be Nx3")
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("market values must be finite and positive")
    return validate_probabilities(values / values.sum(axis=1, keepdims=True))


def _softmax(logits: np.ndarray) -> np.ndarray:
    z = np.asarray(logits, dtype=float)
    z = z - z.max(axis=1, keepdims=True)
    exp = np.exp(z)
    return exp / exp.sum(axis=1, keepdims=True)


def market_anchored_probabilities(market: np.ndarray, residual_logits: np.ndarray, lam: float) -> np.ndarray:
    market = validate_probabilities(market)
    residual_logits = np.asarray(residual_logits, dtype=float)
    if residual_logits.shape != market.shape or not np.isfinite(residual_logits).all():
        raise ValueError("residual logits must be finite and match market shape")
    if lam < 0.0 or lam > 1.0:
        raise ValueError("lambda must be in [0, 1]")
    if lam == 0.0:
        return market.copy()
    return validate_probabilities(_softmax(np.log(np.clip(market, EPS, 1.0)) + lam * residual_logits))


def score_probabilities(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    y = np.asarray(y, dtype=int)
    p = validate_probabilities(p)
    onehot = np.eye(3)[y]
    actual = np.clip(p[np.arange(len(y)), y], EPS, 1.0)
    return {
        "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
        "log_loss": float(-np.mean(np.log(actual))),
        "accuracy": float((p.argmax(axis=1) == y).mean()),
    }


def dual_metric_improvement(candidate: dict[str, float], market: dict[str, float]) -> bool:
    return candidate["brier"] < market["brier"] and candidate["log_loss"] < market["log_loss"]


@dataclass
class ResidualModel:
    imputer: SimpleImputer
    scaler: StandardScaler
    weights: np.ndarray

    def residual_logits(self, X: pd.DataFrame) -> np.ndarray:
        x = self.scaler.transform(self.imputer.transform(X))
        x = np.column_stack([np.ones(len(x)), x])
        pair = x @ self.weights
        return np.column_stack([pair[:, 0], np.zeros(len(x)), pair[:, 1]])


def fit_residual_model(X: pd.DataFrame, y: np.ndarray, market: np.ndarray, l2_penalty: float = L2_PENALTY) -> ResidualModel:
    market = validate_probabilities(market)
    y = np.asarray(y, dtype=int)
    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    x = scaler.fit_transform(imputer.fit_transform(X))
    x = np.column_stack([np.ones(len(x)), x])
    onehot = np.eye(3)[y]
    base = np.log(np.clip(market, EPS, 1.0))
    d = x.shape[1]

    def objective(flat: np.ndarray):
        w = flat.reshape(d, 2)
        pair = x @ w
        residual = np.column_stack([pair[:, 0], np.zeros(len(x)), pair[:, 1]])
        p = _softmax(base + residual)
        nll = -float(np.mean(np.log(np.clip(p[np.arange(len(y)), y], EPS, 1.0))))
        penalty = 0.5 * l2_penalty * float(np.sum(w[1:] ** 2)) / max(1, d - 1)
        err = (p - onehot) / len(y)
        grad = np.column_stack([x.T @ err[:, 0], x.T @ err[:, 2]])
        if d > 1:
            grad[1:] += (l2_penalty / max(1, d - 1)) * w[1:]
        return nll + penalty, grad.ravel()

    result = minimize(objective, np.zeros(d * 2), method="L-BFGS-B", jac=True, options={"maxiter": 500, "ftol": 1e-12})
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError(f"residual optimization failed: {result.message}")
    return ResidualModel(imputer, scaler, result.x.reshape(d, 2))


def _market(frame: pd.DataFrame) -> np.ndarray:
    return devig_market_probabilities(frame[["market_home", "market_draw", "market_away"]].to_numpy(float))


def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    out = add_difference_features(frame)
    out = out[out["match_date"] <= LATEST_ALLOWED_DATE].copy()
    allowed = set(TRAIN_SEASONS) | {VALIDATION_SEASON, TEST_SEASON}
    out = out[out["season"].isin(allowed)]
    out = out[out["result"].isin(RESULT_TO_INT)]
    out = out.dropna(subset=["market_home", "market_draw", "market_away"])
    return out.sort_values(["match_date", "league"], kind="stable").reset_index(drop=True)


def _choose_on_validation(train: pd.DataFrame, val: pd.DataFrame):
    y_val = val["result"].map(RESULT_TO_INT).to_numpy()
    market_val = _market(val)
    market_score = score_probabilities(y_val, market_val)
    choices = []
    fitted = {}
    for variant in FEATURE_VARIANTS:
        features = list(FEATURE_SETS[variant])
        model = fit_residual_model(train[features], train["result"].map(RESULT_TO_INT).to_numpy(), _market(train))
        fitted[variant] = model
        residual = model.residual_logits(val[features])
        for lam in LAMBDA_GRID:
            score = score_probabilities(y_val, market_anchored_probabilities(market_val, residual, lam))
            choices.append({"feature_variant": variant, "lambda": lam, **score})
    admissible = [c for c in choices if c["lambda"] > 0 and dual_metric_improvement(c, market_score)]
    if not admissible:
        return {"feature_variant": "MARKET", "lambda": 0.0, **market_score}, choices, None
    selected = min(admissible, key=lambda c: (c["log_loss"], c["brier"], c["lambda"], c["feature_variant"]))
    return selected, choices, fitted[selected["feature_variant"]]


def evaluate_frame(frame: pd.DataFrame) -> dict:
    frame = _prepare(frame)
    league_reports, pooled_y, pooled_market, pooled_candidate = [], [], [], []
    for league, g in frame.groupby("league"):
        train = g[g["season"].isin(TRAIN_SEASONS)].copy()
        val = g[g["season"] == VALIDATION_SEASON].copy()
        test = g[g["season"] == TEST_SEASON].copy()
        if min(len(train), len(val), len(test)) == 0:
            raise RuntimeError(f"{league}: incomplete train/validation/test seasons")
        selected, choices, model = _choose_on_validation(train, val)
        y_test = test["result"].map(RESULT_TO_INT).to_numpy()
        market_test = _market(test)
        if selected["lambda"] == 0.0:
            candidate = market_test.copy()
        else:
            features = list(FEATURE_SETS[selected["feature_variant"]])
            candidate = market_anchored_probabilities(market_test, model.residual_logits(test[features]), float(selected["lambda"]))
        market_score = score_probabilities(y_test, market_test)
        candidate_score = score_probabilities(y_test, candidate)
        league_reports.append({
            "league": league,
            "train_n": len(train), "validation_n": len(val), "test_n": len(test),
            "selected_feature_variant": selected["feature_variant"], "selected_lambda": float(selected["lambda"]),
            "validation_market": score_probabilities(val["result"].map(RESULT_TO_INT).to_numpy(), _market(val)),
            "validation_selected": {k: selected[k] for k in ("brier", "log_loss", "accuracy")},
            "test_market": market_score, "test_residual_candidate": candidate_score,
            "test_delta_brier": candidate_score["brier"] - market_score["brier"],
            "test_delta_log_loss": candidate_score["log_loss"] - market_score["log_loss"],
            "validation_candidates_evaluated": len(choices),
        })
        pooled_y.append(y_test); pooled_market.append(market_test); pooled_candidate.append(candidate)

    y = np.concatenate(pooled_y)
    market = np.vstack(pooled_market)
    candidate = np.vstack(pooled_candidate)
    market_score = score_probabilities(y, market)
    residual_score = score_probabilities(y, candidate)
    accepted = dual_metric_improvement(residual_score, market_score)
    active_score = score_probabilities(y, candidate if accepted else market)
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_OOT",
        "research_only": True,
        "production_promotion": False,
        "train_seasons": list(TRAIN_SEASONS),
        "validation_season": VALIDATION_SEASON,
        "untouched_test_season": TEST_SEASON,
        "opened_2026_09_outcomes_used": False,
        "lambda_grid": list(LAMBDA_GRID), "l2_penalty": L2_PENALTY,
        "feature_variants": list(FEATURE_VARIANTS), "test_n": int(len(y)),
        "market_test": market_score, "residual_candidate_test": residual_score,
        "residual_delta_brier": residual_score["brier"] - market_score["brier"],
        "residual_delta_log_loss": residual_score["log_loss"] - market_score["log_loss"],
        "residual_accepted": accepted,
        "active_mode": "RESIDUAL" if accepted else "MARKET_FALLBACK",
        "active_test": active_score,
        "active_delta_brier": active_score["brier"] - market_score["brier"],
        "active_delta_log_loss": active_score["log_loss"] - market_score["log_loss"],
        "acceptance_rule": "residual pooled OOT Brier < market AND residual pooled OOT LogLoss < market; otherwise exact market fallback",
        "league_reports": league_reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/market_anchor_1x2_v1/work"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/market_anchor_1x2_v1/report.json"))
    args = parser.parse_args()
    frames = [download(cfg, league, args.work_dir / league.lower()) for league, cfg in LEAGUES.items()]
    report = evaluate_frame(pd.concat(frames, ignore_index=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
