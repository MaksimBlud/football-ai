"""Predict La Liga standard-to-explicit-closing 1X2 market movement.

Research only. Football-Data non-C Bet365 fields are called standard, never opening.
Targets use explicit B365 closing fields. No match outcome is used as a target or
feature. Selection is 2024-25 and the final temporal OOT is 2025-26.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from bookmaker_reconstruction_devig_v1 import power
from historical_football_signal_lab import FEATURE_SETS, add_difference_features, build_point_in_time_features
from historical_football_signal_runner import BASE, LEAGUES

EXPERIMENT_ID = "LA_LIGA_STANDARD_TO_CLOSE_SIGNAL_V6"
LEAGUE = "LA_LIGA"
TRAIN_SEASONS = tuple(f"{y}-{y+1}" for y in range(2016, 2024))
VALIDATION_SEASON = "2024-2025"
TEST_SEASON = "2025-2026"
LATEST_ALLOWED_DATE = pd.Timestamp("2026-06-30")
FEATURE_VARIANTS = ("MARKET_STATE", "FORM", "FORM_GOALS", "FORM_GOALS_CORNERS", "ALL_FOOTBALL")
RIDGE_ALPHA = 10.0
STANDARD_COLUMNS = ("B365H", "B365D", "B365A")
CLOSING_COLUMNS = ("B365CH", "B365CD", "B365CA")
TARGET_COLUMNS = ("target_home_vs_draw", "target_away_vs_draw")


def _valid_odds(frame: pd.DataFrame, columns: tuple[str, str, str]) -> pd.Series:
    if not all(c in frame.columns for c in columns):
        return pd.Series(False, index=frame.index)
    odds = frame[list(columns)].apply(pd.to_numeric, errors="coerce")
    return odds.gt(1.0).all(axis=1)


def _power_from_odds(odds: np.ndarray) -> np.ndarray:
    odds = np.asarray(odds, dtype=float)
    if odds.ndim != 2 or odds.shape[1] != 3 or not np.isfinite(odds).all() or (odds <= 1.0).any():
        raise ValueError("odds must be finite Nx3 decimal prices > 1")
    return power(1.0 / odds)


def movement_targets(standard_prob: np.ndarray, closing_prob: np.ndarray) -> np.ndarray:
    standard_prob = np.asarray(standard_prob, dtype=float)
    closing_prob = np.asarray(closing_prob, dtype=float)
    if standard_prob.shape != closing_prob.shape or standard_prob.ndim != 2 or standard_prob.shape[1] != 3:
        raise ValueError("standard and closing probabilities must be matching Nx3 matrices")
    if (standard_prob <= 0).any() or (closing_prob <= 0).any():
        raise ValueError("probabilities must be positive")
    standard_log_ratio = np.column_stack([
        np.log(standard_prob[:, 0] / standard_prob[:, 1]),
        np.log(standard_prob[:, 2] / standard_prob[:, 1]),
    ])
    closing_log_ratio = np.column_stack([
        np.log(closing_prob[:, 0] / closing_prob[:, 1]),
        np.log(closing_prob[:, 2] / closing_prob[:, 1]),
    ])
    return closing_log_ratio - standard_log_ratio


def load_history(raw_dir: Path) -> pd.DataFrame:
    cfg = LEAGUES[LEAGUE]
    allowed = set(TRAIN_SEASONS) | {VALIDATION_SEASON, TEST_SEASON}
    raw_frames: list[pd.DataFrame] = []
    raw_dir.mkdir(parents=True, exist_ok=True)
    for code, season in cfg.historical_source.season_codes.items():
        if season not in allowed:
            continue
        response = requests.get(BASE.format(code=code, comp=cfg.historical_source.competition_code), timeout=60)
        response.raise_for_status()
        raw = pd.read_csv(pd.io.common.BytesIO(response.content))
        raw["_season"] = season
        raw_frames.append(raw)
    if not raw_frames:
        raise RuntimeError("no La Liga history loaded")
    raw = pd.concat(raw_frames, ignore_index=True)
    features = build_point_in_time_features(raw, LEAGUE, "MULTI_SEASON")

    market_rows = []
    for _, row in raw.iterrows():
        market_rows.append({
            "match_date": pd.to_datetime(row.get("Date"), dayfirst=True, errors="coerce"),
            "home_team": str(row.get("HomeTeam")),
            "away_team": str(row.get("AwayTeam")),
            "season": str(row.get("_season")),
            **{c: pd.to_numeric(row.get(c), errors="coerce") for c in STANDARD_COLUMNS + CLOSING_COLUMNS},
        })
    market = pd.DataFrame(market_rows)
    features = features.drop(columns=["season"]).merge(
        market, on=["match_date", "home_team", "away_team"], how="left", validate="one_to_one"
    )
    if features["season"].isna().any():
        raise RuntimeError("failed to restore La Liga season labels")
    return features


def prepare_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    out = add_difference_features(frame)
    allowed = set(TRAIN_SEASONS) | {VALIDATION_SEASON, TEST_SEASON}
    out = out[(out["league"] == LEAGUE) & out["season"].isin(allowed) & (out["match_date"] <= LATEST_ALLOWED_DATE)].copy()
    standard_valid = _valid_odds(out, STANDARD_COLUMNS)
    closing_valid = _valid_odds(out, CLOSING_COLUMNS)
    paired = standard_valid & closing_valid
    coverage = {
        "rows": int(len(out)),
        "standard_valid_rows": int(standard_valid.sum()),
        "closing_valid_rows": int(closing_valid.sum()),
        "paired_valid_rows": int(paired.sum()),
        "paired_coverage": float(paired.mean()) if len(out) else 0.0,
    }
    out = out.loc[paired].copy()
    standard = _power_from_odds(out[list(STANDARD_COLUMNS)].to_numpy(float))
    closing = _power_from_odds(out[list(CLOSING_COLUMNS)].to_numpy(float))
    targets = movement_targets(standard, closing)
    out["standard_home_prob"] = standard[:, 0]
    out["standard_draw_prob"] = standard[:, 1]
    out["standard_away_prob"] = standard[:, 2]
    out[TARGET_COLUMNS[0]] = targets[:, 0]
    out[TARGET_COLUMNS[1]] = targets[:, 1]
    return out.sort_values("match_date", kind="stable").reset_index(drop=True), coverage


def feature_columns(variant: str) -> list[str]:
    market = ["standard_home_prob", "standard_draw_prob", "standard_away_prob"]
    if variant == "MARKET_STATE":
        return market
    if variant not in FEATURE_SETS:
        raise KeyError(variant)
    return market + list(FEATURE_SETS[variant])


def fit_model(train: pd.DataFrame, variant: str) -> Pipeline:
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=RIDGE_ALPHA)),
    ])
    model.fit(train[feature_columns(variant)], train[list(TARGET_COLUMNS)].to_numpy(float))
    return model


def movement_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    if actual.shape != predicted.shape or actual.ndim != 2 or actual.shape[1] != 2:
        raise ValueError("movement arrays must be matching Nx2")
    error = predicted - actual
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error ** 2))),
        "direction_accuracy": float(np.mean(np.sign(predicted) == np.sign(actual))),
    }


def _evaluate(model: Pipeline, frame: pd.DataFrame, variant: str) -> tuple[dict[str, float], np.ndarray]:
    actual = frame[list(TARGET_COLUMNS)].to_numpy(float)
    predicted = np.asarray(model.predict(frame[feature_columns(variant)]), dtype=float)
    return movement_metrics(actual, predicted), predicted


def evaluate_frame(frame: pd.DataFrame) -> dict:
    frame, coverage = prepare_frame(frame)
    train = frame[frame["season"].isin(TRAIN_SEASONS)].copy()
    validation = frame[frame["season"] == VALIDATION_SEASON].copy()
    test = frame[frame["season"] == TEST_SEASON].copy()
    if min(len(train), len(validation), len(test)) == 0:
        raise RuntimeError("V6 requires paired standard/closing rows in train, validation and test")

    validation_actual = validation[list(TARGET_COLUMNS)].to_numpy(float)
    validation_baseline = movement_metrics(validation_actual, np.zeros_like(validation_actual))
    choices = []
    fitted = {}
    for variant in FEATURE_VARIANTS:
        model = fit_model(train, variant)
        fitted[variant] = model
        metrics, _ = _evaluate(model, validation, variant)
        choices.append({"feature_variant": variant, **metrics})
    admissible = [c for c in choices if c["mae"] < validation_baseline["mae"] and c["rmse"] < validation_baseline["rmse"]]
    selected = min(admissible, key=lambda c: (c["rmse"], c["mae"], c["feature_variant"])) if admissible else None

    test_actual = test[list(TARGET_COLUMNS)].to_numpy(float)
    test_baseline = movement_metrics(test_actual, np.zeros_like(test_actual))
    if selected is None:
        candidate_metrics = dict(test_baseline)
        accepted = False
        selected_variant = "ZERO_MOVEMENT_BASELINE"
    else:
        selected_variant = str(selected["feature_variant"])
        candidate_metrics, _ = _evaluate(fitted[selected_variant], test, selected_variant)
        accepted = candidate_metrics["mae"] < test_baseline["mae"] and candidate_metrics["rmse"] < test_baseline["rmse"]

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_OOT_MARKET_MOVEMENT",
        "league": LEAGUE,
        "research_only": True,
        "production_promotion": False,
        "betting_enabled": False,
        "result": "NO_BET",
        "opened_2026_27_outcomes_used": False,
        "match_outcome_used_as_target": False,
        "standard_is_labeled_opening": False,
        "standard_columns": list(STANDARD_COLUMNS),
        "explicit_closing_columns": list(CLOSING_COLUMNS),
        "devig_method": "POWER",
        "target": "closing_minus_standard_log_probability_ratios_home_draw_and_away_draw",
        "baseline": "ZERO_MOVEMENT",
        "feature_variants": list(FEATURE_VARIANTS),
        "ridge_alpha": RIDGE_ALPHA,
        "train_seasons": list(TRAIN_SEASONS),
        "validation_season": VALIDATION_SEASON,
        "untouched_test_season": TEST_SEASON,
        "coverage": coverage,
        "train_n": int(len(train)),
        "validation_n": int(len(validation)),
        "test_n": int(len(test)),
        "validation_zero_movement": validation_baseline,
        "validation_candidates": choices,
        "selected_feature_variant": selected_variant,
        "validation_selected": selected,
        "test_zero_movement": test_baseline,
        "test_candidate": candidate_metrics,
        "test_delta_mae": float(candidate_metrics["mae"] - test_baseline["mae"]),
        "test_delta_rmse": float(candidate_metrics["rmse"] - test_baseline["rmse"]),
        "movement_signal_accepted": bool(accepted),
        "active_mode": "MOVEMENT_SIGNAL" if accepted else "ZERO_MOVEMENT_FALLBACK",
        "acceptance_rule": "candidate must beat zero-movement baseline on both MAE and RMSE on validation and untouched OOT",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/la_liga_standard_to_close_signal_v6/work"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/la_liga_standard_to_close_signal_v6/report.json"))
    args = parser.parse_args()
    report = evaluate_frame(load_history(args.work_dir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
