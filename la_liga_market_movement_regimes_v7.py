"""La Liga V7: predict whether standard-to-closing 1X2 repricing is material.

Research only. The target is derived only from paired Bet365 standard and explicit
closing prices. 2024-25 selects a fixed movement threshold and candidate; 2025-26
is untouched temporal OOT. Match outcomes are never used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from historical_football_signal_lab import FEATURE_SETS
from la_liga_standard_to_close_signal_v6 import (
    TEST_SEASON, TRAIN_SEASONS, VALIDATION_SEASON, feature_columns as v6_feature_columns,
    load_history, prepare_frame,
)

EXPERIMENT_ID = "LA_LIGA_MARKET_MOVEMENT_REGIMES_V7"
FEATURE_VARIANTS = ("MARKET_STATE", "FORM", "FORM_GOALS", "FORM_GOALS_CORNERS", "ALL_FOOTBALL")
MOVEMENT_QUANTILE = 0.75
C = 0.1


def movement_magnitude(frame: pd.DataFrame) -> np.ndarray:
    y = frame[["target_home_vs_draw", "target_away_vs_draw"]].to_numpy(float)
    return np.sqrt(np.sum(y * y, axis=1))


def regime_feature_columns(variant: str) -> list[str]:
    base = list(v6_feature_columns(variant))
    # Market geometry is observable in the standard snapshot and is therefore safe.
    if variant == "MARKET_STATE":
        return base
    return base


def classification_metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-12, 1 - 1e-12)
    prevalence = float(y.mean())
    return {
        "prevalence": prevalence,
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, np.column_stack([1-p, p]), labels=[0, 1])),
        "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else float("nan"),
        "average_precision": float(average_precision_score(y, p)) if y.sum() else float("nan"),
    }


def baseline_metrics(y: np.ndarray, prevalence: float) -> dict[str, float]:
    return classification_metrics(y, np.full(len(y), prevalence, dtype=float))


def fit_candidate(train: pd.DataFrame, y: np.ndarray, variant: str) -> Pipeline:
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("logit", LogisticRegression(C=C, max_iter=2000, class_weight=None)),
    ])
    model.fit(train[regime_feature_columns(variant)], y)
    return model


def evaluate_frame(frame: pd.DataFrame) -> dict:
    frame, coverage = prepare_frame(frame)
    train = frame[frame["season"].isin(TRAIN_SEASONS)].copy()
    validation = frame[frame["season"] == VALIDATION_SEASON].copy()
    test = frame[frame["season"] == TEST_SEASON].copy()
    if min(len(train), len(validation), len(test)) == 0:
        raise RuntimeError("V7 requires train, validation and OOT paired market rows")

    train_mag = movement_magnitude(train)
    threshold = float(np.quantile(train_mag, MOVEMENT_QUANTILE))
    train_y = (train_mag >= threshold).astype(int)
    val_y = (movement_magnitude(validation) >= threshold).astype(int)
    test_y = (movement_magnitude(test) >= threshold).astype(int)
    train_prevalence = float(train_y.mean())

    val_baseline = baseline_metrics(val_y, train_prevalence)
    candidates = []
    fitted = {}
    for variant in FEATURE_VARIANTS:
        model = fit_candidate(train, train_y, variant)
        fitted[variant] = model
        p = model.predict_proba(validation[regime_feature_columns(variant)])[:, 1]
        m = classification_metrics(val_y, p)
        candidates.append({"feature_variant": variant, **m})

    admissible = [c for c in candidates if c["brier"] < val_baseline["brier"] and c["log_loss"] < val_baseline["log_loss"]]
    selected = min(admissible, key=lambda c: (c["log_loss"], c["brier"], c["feature_variant"])) if admissible else None

    test_baseline = baseline_metrics(test_y, train_prevalence)
    if selected is None:
        selected_variant = "CONSTANT_PREVALENCE_BASELINE"
        test_candidate = dict(test_baseline)
        accepted = False
    else:
        selected_variant = str(selected["feature_variant"])
        p = fitted[selected_variant].predict_proba(test[regime_feature_columns(selected_variant)])[:, 1]
        test_candidate = classification_metrics(test_y, p)
        accepted = test_candidate["brier"] < test_baseline["brier"] and test_candidate["log_loss"] < test_baseline["log_loss"]

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_OOT_MARKET_MOVEMENT_REGIME",
        "league": "LA_LIGA",
        "research_only": True,
        "production_promotion": False,
        "betting_enabled": False,
        "result": "NO_BET",
        "match_outcome_used": False,
        "opened_2026_27_data_used": False,
        "standard_is_labeled_opening": False,
        "target": "material_standard_to_explicit_closing_POWER_1x2_repricing",
        "movement_magnitude": "euclidean_norm_of_two_closing_minus_standard_log_probability_ratios",
        "movement_quantile": MOVEMENT_QUANTILE,
        "movement_threshold_fit_on_train_only": threshold,
        "baseline": "CONSTANT_TRAIN_PREVALENCE",
        "feature_variants": list(FEATURE_VARIANTS),
        "logistic_c": C,
        "train_n": int(len(train)),
        "validation_n": int(len(validation)),
        "test_n": int(len(test)),
        "coverage": coverage,
        "train_material_n": int(train_y.sum()),
        "validation_material_n": int(val_y.sum()),
        "test_material_n": int(test_y.sum()),
        "validation_baseline": val_baseline,
        "validation_candidates": candidates,
        "validation_selected": selected,
        "selected_feature_variant": selected_variant,
        "test_baseline": test_baseline,
        "test_candidate": test_candidate,
        "test_delta_brier": float(test_candidate["brier"] - test_baseline["brier"]),
        "test_delta_log_loss": float(test_candidate["log_loss"] - test_baseline["log_loss"]),
        "regime_signal_accepted": bool(accepted),
        "active_mode": "MOVEMENT_REGIME_SIGNAL" if accepted else "CONSTANT_PREVALENCE_FALLBACK",
        "acceptance_rule": "candidate must beat constant train prevalence on both Brier and LogLoss on validation and untouched OOT",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/la_liga_market_movement_regimes_v7/work"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/la_liga_market_movement_regimes_v7/report.json"))
    args = parser.parse_args()
    report = evaluate_frame(load_history(args.work_dir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
