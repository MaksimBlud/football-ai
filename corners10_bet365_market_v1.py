"""Frozen CORNERS10_TOTAL vs Bet365 opening corner-market evaluator V1.

Research only. This module contains no provider download logic and cannot purchase
or upgrade any data plan. It evaluates only an already-persisted merged dataset
that satisfies research/CORNERS10_BET365_MARKET_V1.md.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

EXPERIMENT_ID = "CORNERS10_BET365_MARKET_V1"
LEAGUES = ("EPL", "LA_LIGA", "SERIE_A")
TRAIN_SEASONS = (
    "2016-17", "2017-18", "2018-19", "2019-20",
    "2020-21", "2021-22", "2022-23", "2023-24",
)
VALIDATION_SEASON = "2024-25"
OOT_SEASON = "2025-26"
FORBIDDEN_SEASON = "2026-27"

MIN_TRAIN = 600
MIN_VALIDATION = 100
MIN_OOT = 100

CORNER_STATE_FEATURES = (
    "home_corners_for_10",
    "home_corners_against_10",
    "away_corners_for_10",
    "away_corners_against_10",
    "home_corners_for_venue5",
    "home_corners_against_venue5",
    "away_corners_for_venue5",
    "away_corners_against_venue5",
)
FEATURES = ("market_logit", "opening_line") + CORNER_STATE_FEATURES
REQUIRED_INPUT = (
    "league", "season", "opening_line", "opening_over", "opening_under", "HC", "AC",
) + CORNER_STATE_FEATURES


def _number(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return result if math.isfinite(result) else float("nan")


def _is_half_line(value: float) -> bool:
    if not math.isfinite(value):
        return False
    return math.isclose(value * 2.0, round(value * 2.0), abs_tol=1e-9) and not math.isclose(
        value, round(value), abs_tol=1e-9
    )


def _devig_over(over_odds: float, under_odds: float) -> float:
    if not (math.isfinite(over_odds) and math.isfinite(under_odds)):
        raise ValueError("odds must be finite")
    if over_odds <= 1.0 or under_odds <= 1.0:
        raise ValueError("odds must be > 1")
    qo, qu = 1.0 / over_odds, 1.0 / under_odds
    return qo / (qo + qu)


def _logit(probability: float) -> float:
    p = float(np.clip(probability, 1e-6, 1.0 - 1e-6))
    return float(np.log(p / (1.0 - p)))


def prepare_rows(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(REQUIRED_INPUT) - set(frame.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if FORBIDDEN_SEASON in set(frame["season"].astype(str)):
        raise ValueError(f"forbidden season present: {FORBIDDEN_SEASON}")

    out = frame.copy()
    allowed_seasons = set(TRAIN_SEASONS) | {VALIDATION_SEASON, OOT_SEASON}
    out = out[out["league"].isin(LEAGUES) & out["season"].astype(str).isin(allowed_seasons)].copy()
    for column in ("opening_line", "opening_over", "opening_under", "HC", "AC"):
        out[column] = pd.to_numeric(out[column], errors="coerce")

    mask = (
        out["opening_line"].map(lambda x: _is_half_line(_number(x)))
        & np.isfinite(out["opening_over"])
        & np.isfinite(out["opening_under"])
        & (out["opening_over"] > 1.0)
        & (out["opening_under"] > 1.0)
        & np.isfinite(out["HC"])
        & np.isfinite(out["AC"])
    )
    out = out.loc[mask].copy()
    out["total_corners"] = out["HC"] + out["AC"]
    out["y_over"] = (out["total_corners"] > out["opening_line"]).astype(int)
    out["p_market_over"] = [
        _devig_over(float(o), float(u)) for o, u in zip(out["opening_over"], out["opening_under"])
    ]
    out["market_logit"] = out["p_market_over"].map(_logit)
    return out.reset_index(drop=True)


def _model() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(C=0.1, max_iter=2000)),
        ]
    )


def _scores(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-12, 1.0 - 1e-12)
    return {
        "accuracy": float(((p >= 0.5).astype(int) == y).mean()),
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(log_loss(y, np.column_stack([1.0 - p, p]), labels=[0, 1])),
    }


def _beats(candidate: dict[str, float], baseline: dict[str, float]) -> bool:
    return candidate["brier"] < baseline["brier"] and candidate["log_loss"] < baseline["log_loss"]


def _evaluate_league_detail(prepared: pd.DataFrame, league: str) -> tuple[dict[str, Any], pd.DataFrame]:
    g = prepared[prepared["league"] == league].copy()
    train = g[g["season"].isin(TRAIN_SEASONS)]
    validation = g[g["season"] == VALIDATION_SEASON]
    oot = g[g["season"] == OOT_SEASON]
    counts = {"train": len(train), "validation": len(validation), "oot": len(oot)}
    sufficient = counts["train"] >= MIN_TRAIN and counts["validation"] >= MIN_VALIDATION and counts["oot"] >= MIN_OOT
    base_report: dict[str, Any] = {
        "league": league,
        "counts": counts,
        "data_sufficient": sufficient,
        "validation_admissible": False,
    }
    if not sufficient:
        base_report["status"] = "DATA_INSUFFICIENT"
        return base_report, pd.DataFrame()

    model = _model()
    model.fit(train[list(FEATURES)], train["y_over"].to_numpy(int))

    val_market = validation["p_market_over"].to_numpy(float)
    val_candidate = model.predict_proba(validation[list(FEATURES)])[:, 1]
    val_y = validation["y_over"].to_numpy(int)
    val_market_scores = _scores(val_y, val_market)
    val_candidate_scores = _scores(val_y, val_candidate)
    admissible = _beats(val_candidate_scores, val_market_scores)

    oot_market = oot["p_market_over"].to_numpy(float)
    oot_candidate = model.predict_proba(oot[list(FEATURES)])[:, 1]
    oot_y = oot["y_over"].to_numpy(int)
    oot_market_scores = _scores(oot_y, oot_market)
    oot_candidate_scores = _scores(oot_y, oot_candidate)
    selected = oot_candidate if admissible else oot_market
    selected_scores = _scores(oot_y, selected)

    if not admissible:
        status = "MARKET_FALLBACK"
    elif _beats(oot_candidate_scores, oot_market_scores):
        status = "PASS"
    else:
        status = "FAIL"

    base_report.update(
        {
            "validation_admissible": admissible,
            "validation": {"market": val_market_scores, "candidate": val_candidate_scores},
            "oot": {
                "market": oot_market_scores,
                "candidate": oot_candidate_scores,
                "selected": selected_scores,
            },
            "status": status,
        }
    )
    predictions = pd.DataFrame(
        {
            "league": league,
            "y": oot_y,
            "market": oot_market,
            "candidate": oot_candidate,
            "selected": selected,
            "validation_admissible": admissible,
        }
    )
    return base_report, predictions


def evaluate(frame: pd.DataFrame) -> dict[str, Any]:
    prepared = prepare_rows(frame)
    league_reports: dict[str, Any] = {}
    prediction_parts: list[pd.DataFrame] = []
    for league in LEAGUES:
        report, predictions = _evaluate_league_detail(prepared, league)
        league_reports[league] = report
        if not predictions.empty:
            prediction_parts.append(predictions)

    pass_count = sum(report.get("status") == "PASS" for report in league_reports.values())
    if prediction_parts:
        pooled = pd.concat(prediction_parts, ignore_index=True)
        pooled_market = _scores(pooled["y"].to_numpy(int), pooled["market"].to_numpy(float))
        pooled_selected = _scores(pooled["y"].to_numpy(int), pooled["selected"].to_numpy(float))
        pooled_beats = _beats(pooled_selected, pooled_market)
        pooled_report: dict[str, Any] = {
            "matches": len(pooled),
            "market": pooled_market,
            "selected": pooled_selected,
            "selected_beats_market_both": pooled_beats,
        }
    else:
        pooled_beats = False
        pooled_report = {"matches": 0, "selected_beats_market_both": False}

    decision = "PILOT" if pass_count >= 2 and pooled_beats else "SKIP"
    return {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "betting_enabled": False,
        "production_promotion": False,
        "primary_market": "BET365_OPENING_FULL_TIME_CORNERS_HALF_LINES",
        "candidate": "MARKET_CORNERS10_TOTAL",
        "train_seasons": list(TRAIN_SEASONS),
        "validation_season": VALIDATION_SEASON,
        "oot_season": OOT_SEASON,
        "league_reports": league_reports,
        "pass_count": pass_count,
        "pooled_oot": pooled_report,
        "decision": decision,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True, help="Frozen merged CSV prepared by the historical backfill/reconciliation layer")
    parser.add_argument("--output", type=Path, default=Path("artifacts/corners10_bet365_market_v1/report.json"))
    args = parser.parse_args()
    frame = pd.read_csv(args.input)
    report = evaluate(frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
