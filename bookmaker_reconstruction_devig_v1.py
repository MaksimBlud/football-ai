"""Research-only benchmark of bookmaker 1X2 de-vigging methods.

The experiment reads raw historical decimal odds before any margin removal. Method
selection uses 2024-2025 only; 2025-2026 remains untouched temporal OOT. No
production artifacts, Supabase state, paid APIs, or opened 2026-27 outcomes are used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from scipy.optimize import brentq

from historical_football_signal_lab import MARKET_TRIPLETS, RESULT_TO_INT
from historical_football_signal_runner import BASE, LEAGUES
from market_anchor_1x2_v1 import score_probabilities

EXPERIMENT_ID = "BOOKMAKER_RECONSTRUCTION_DEVIG_V1"
VALIDATION_SEASON = "2024-2025"
TEST_SEASON = "2025-2026"
METHODS = ("PROPORTIONAL", "POWER", "SHIN")
EPS = 1e-12


def _market_odds(row: pd.Series) -> tuple[float, float, float, str] | None:
    """Return the same preferred 1X2 bookmaker triplet used by the existing lab."""
    for home_col, draw_col, away_col in MARKET_TRIPLETS:
        if not all(c in row.index for c in (home_col, draw_col, away_col)):
            continue
        odds = pd.to_numeric(pd.Series([row[home_col], row[draw_col], row[away_col]]), errors="coerce").to_numpy(float)
        if np.isfinite(odds).all() and (odds > 1.0).all():
            return float(odds[0]), float(odds[1]), float(odds[2]), home_col[:-1]
    return None


def raw_market_frame(raw: pd.DataFrame, league: str, season: str) -> pd.DataFrame:
    rows = []
    for _, row in raw.iterrows():
        result = row.get("FTR")
        if result not in RESULT_TO_INT:
            continue
        odds = _market_odds(row)
        if odds is None:
            continue
        home, draw, away, source = odds
        rows.append({
            "league": league,
            "season": season,
            "result": result,
            "market_home_odds": home,
            "market_draw_odds": draw,
            "market_away_odds": away,
            "market_source": source,
        })
    return pd.DataFrame(rows)


def load_history(raw_dir: Path) -> pd.DataFrame:
    """Download only the frozen validation and OOT seasons from the free source."""
    frames = []
    allowed = {VALIDATION_SEASON, TEST_SEASON}
    for league, config in LEAGUES.items():
        league_dir = raw_dir / league.lower()
        league_dir.mkdir(parents=True, exist_ok=True)
        for code, season in config.historical_source.season_codes.items():
            if season not in allowed:
                continue
            url = BASE.format(code=code, comp=config.historical_source.competition_code)
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            path = league_dir / f"{league.lower()}_{code}.csv"
            path.write_bytes(response.content)
            frames.append(raw_market_frame(pd.read_csv(path), league, season))
    if not frames:
        raise RuntimeError("no frozen validation/OOT market history was loaded")
    return pd.concat(frames, ignore_index=True)


def _raw_implied(frame: pd.DataFrame) -> np.ndarray:
    odds = frame[["market_home_odds", "market_draw_odds", "market_away_odds"]].to_numpy(float)
    if not np.isfinite(odds).all() or (odds <= 1.0).any():
        raise ValueError("decimal market odds must be finite and > 1")
    return 1.0 / odds


def proportional(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    return q / q.sum(axis=1, keepdims=True)


def power(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    out = np.empty_like(q, dtype=float)
    for i, row in enumerate(q):
        f = lambda k: float(np.power(row, k).sum() - 1.0)
        k = brentq(f, 0.01, 20.0)
        out[i] = np.power(row, k)
    return out


def shin(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    out = np.empty_like(q, dtype=float)
    for i, row in enumerate(q):
        s = float(row.sum())
        if s <= 1.0:
            out[i] = row / s
            continue

        def probs(z: float) -> np.ndarray:
            return (np.sqrt(z * z + 4.0 * (1.0 - z) * row * row / s) - z) / (2.0 * (1.0 - z))

        f = lambda z: float(probs(z).sum() - 1.0)
        z = brentq(f, 0.0, 1.0 - 1e-10)
        p = probs(z)
        out[i] = p / p.sum()
    return out


def probabilities(frame: pd.DataFrame, method: str) -> np.ndarray:
    q = _raw_implied(frame)
    if method == "PROPORTIONAL":
        return proportional(q)
    if method == "POWER":
        return power(q)
    if method == "SHIN":
        return shin(q)
    raise ValueError(f"unknown method: {method}")


def calibration_ece(y: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    """Top-label multiclass expected calibration error."""
    confidence = p.max(axis=1)
    predicted = p.argmax(axis=1)
    correct = (predicted == y).astype(float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(y)
    ece = 0.0
    for left, right in zip(edges[:-1], edges[1:]):
        mask = (confidence >= left) & (confidence < right if right < 1.0 else confidence <= right)
        if mask.any():
            ece += (mask.sum() / total) * abs(float(correct[mask].mean()) - float(confidence[mask].mean()))
    return float(ece)


def _score(frame: pd.DataFrame, method: str) -> dict[str, float]:
    y = frame["result"].map(RESULT_TO_INT).to_numpy()
    p = probabilities(frame, method)
    score = score_probabilities(y, p)
    score["calibration_ece"] = calibration_ece(y, p)
    return score


def _method_scores(frame: pd.DataFrame) -> dict[str, dict[str, float]]:
    return {method: _score(frame, method) for method in METHODS}


def _select(scores: dict[str, dict[str, float]]) -> str:
    return min(METHODS, key=lambda method: (scores[method]["log_loss"], scores[method]["brier"], method))


def _overround_summary(frame: pd.DataFrame) -> dict[str, float]:
    overround = _raw_implied(frame).sum(axis=1) - 1.0
    return {
        "mean": float(overround.mean()),
        "median": float(np.median(overround)),
        "min": float(overround.min()),
        "max": float(overround.max()),
    }


def evaluate_frame(frame: pd.DataFrame) -> dict:
    clean = frame[frame["result"].isin(RESULT_TO_INT)].dropna(
        subset=["market_home_odds", "market_draw_odds", "market_away_odds"]
    ).copy()
    league_reports = []
    pooled_validation, pooled_test = [], []
    for league, group in clean.groupby("league"):
        validation = group[group["season"] == VALIDATION_SEASON].copy()
        test = group[group["season"] == TEST_SEASON].copy()
        if validation.empty or test.empty:
            raise RuntimeError(f"{league}: missing frozen validation/test season")
        validation_scores = _method_scores(validation)
        selected = _select(validation_scores)
        test_scores = _method_scores(test)
        league_reports.append({
            "league": league,
            "validation_n": int(len(validation)),
            "test_n": int(len(test)),
            "market_source_counts": {str(k): int(v) for k, v in group["market_source"].value_counts().items()},
            "validation_overround": _overround_summary(validation),
            "test_overround": _overround_summary(test),
            "selected_on_validation": selected,
            "validation": validation_scores,
            "untouched_test": test_scores,
            "selected_test": test_scores[selected],
        })
        pooled_validation.append(validation)
        pooled_test.append(test)

    validation = pd.concat(pooled_validation, ignore_index=True)
    test = pd.concat(pooled_test, ignore_index=True)
    validation_scores = _method_scores(validation)
    selected = _select(validation_scores)
    test_scores = _method_scores(test)
    baseline = test_scores["PROPORTIONAL"]
    selected_test = test_scores[selected]
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_OOT",
        "research_only": True,
        "production_promotion": False,
        "betting_enabled": False,
        "result": "NO_BET",
        "opened_2026_27_outcomes_used": False,
        "validation_season": VALIDATION_SEASON,
        "untouched_test_season": TEST_SEASON,
        "methods": list(METHODS),
        "selection_metric": "validation LogLoss, then Brier; no 2025-2026 selection",
        "source_contract": "raw decimal odds; same preferred B365/PS/Avg triplet order as historical football signal lab",
        "pooled_validation_n": int(len(validation)),
        "pooled_test_n": int(len(test)),
        "pooled_selected_on_validation": selected,
        "pooled_validation": validation_scores,
        "pooled_untouched_test": test_scores,
        "pooled_selected_test_delta_vs_proportional": {
            "brier": selected_test["brier"] - baseline["brier"],
            "log_loss": selected_test["log_loss"] - baseline["log_loss"],
            "calibration_ece": selected_test["calibration_ece"] - baseline["calibration_ece"],
        },
        "league_reports": league_reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/bookmaker_reconstruction_devig_v1/work"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/bookmaker_reconstruction_devig_v1/report.json"))
    args = parser.parse_args()
    report = evaluate_frame(load_history(args.work_dir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
