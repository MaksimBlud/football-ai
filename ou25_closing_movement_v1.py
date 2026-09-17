"""Frozen O/U 2.5 opening-to-closing market-discovery experiment.

Research-only. Target is bookmaker closing probability, not match outcome.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import cross_league_direct_markets_v1 as direct
from cross_league_direct_markets_transport import _official_or_pinned_mirror_get

EXPERIMENT_ID = "OU25_CLOSING_MOVEMENT_V1"
LEAGUE_IDS = direct.LEAGUE_IDS
TRAIN_SEASONS = direct.TRAIN_SEASONS
VALIDATION_SEASON = direct.VALIDATION_SEASON
TEST_SEASON = direct.TEST_SEASON

PAIRED_PRICE_COLUMNS = (
    ("B365>2.5", "B365<2.5", "B365C>2.5", "B365C<2.5", "BET365"),
    ("P>2.5", "P<2.5", "PC>2.5", "PC<2.5", "PINNACLE"),
    ("Avg>2.5", "Avg<2.5", "AvgC>2.5", "AvgC<2.5", "AVERAGE"),
)

FEATURES = [
    "opening_logit",
    "home_goals_for_10",
    "home_goals_against_10",
    "away_goals_for_10",
    "away_goals_against_10",
    "home_corners_for_10",
    "home_corners_against_10",
    "away_corners_for_10",
    "away_corners_against_10",
    "home_goals_for_venue5",
    "home_goals_against_venue5",
    "away_goals_for_venue5",
    "away_goals_against_venue5",
    "home_corners_for_venue5",
    "home_corners_against_venue5",
    "away_corners_for_venue5",
    "away_corners_against_venue5",
]


def _sigmoid(value: np.ndarray | float) -> np.ndarray:
    x = np.clip(np.asarray(value, dtype=float), -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-x))


def _paired_prices(row: pd.Series):
    for open_over, open_under, close_over, close_under, source in PAIRED_PRICE_COLUMNS:
        values = [
            pd.to_numeric(row.get(column), errors="coerce")
            for column in (open_over, open_under, close_over, close_under)
        ]
        if all(np.isfinite(value) and value > 1.0 for value in values):
            return (*map(float, values), source)
    return None


def _market_rows(raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for _, row in raw.iterrows():
        paired = _paired_prices(row)
        if paired is None:
            continue
        open_over, open_under, close_over, close_under, source = paired
        opening_probability = direct._binary_devig(open_over, open_under)
        closing_probability = direct._binary_devig(close_over, close_under)
        opening_logit = direct._logit(opening_probability)
        closing_logit = direct._logit(closing_probability)
        rows.append(
            {
                "match_date": row.get("match_date"),
                "home_team": row.get("HomeTeam"),
                "away_team": row.get("AwayTeam"),
                "season": row.get("_season"),
                "price_source": source,
                "opening_probability": opening_probability,
                "closing_probability": closing_probability,
                "opening_logit": opening_logit,
                "closing_logit": closing_logit,
                "movement_logit": closing_logit - opening_logit,
            }
        )
    return pd.DataFrame(rows)


def load_league_frame(league: str) -> pd.DataFrame:
    # Keep the evaluator unchanged while replacing only the blocked HTTP transport.
    direct.requests.get = _official_or_pinned_mirror_get
    raw = direct._download_league_raw(league)
    state = direct._point_in_time_state(raw, league)
    market = _market_rows(raw)
    if market.empty:
        raise RuntimeError(f"{league}: no paired opening/closing O/U 2.5 rows")
    frame = market.merge(
        state,
        on=["match_date", "home_team", "away_team", "season"],
        how="left",
        validate="one_to_one",
    )
    return frame.sort_values(["match_date", "home_team", "away_team"]).reset_index(drop=True)


def _estimator() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", Ridge(alpha=1.0)),
        ]
    )


def _scores(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    error = predicted - actual
    return {
        "rmse": float(np.sqrt(np.mean(error**2))),
        "mae": float(np.mean(np.abs(error))),
    }


def _direction_accuracy(
    opening: np.ndarray,
    actual_closing: np.ndarray,
    predicted_closing: np.ndarray,
) -> dict[str, float | int | None]:
    opening = np.asarray(opening, dtype=float)
    actual_closing = np.asarray(actual_closing, dtype=float)
    predicted_closing = np.asarray(predicted_closing, dtype=float)
    actual_delta = actual_closing - opening
    predicted_delta = predicted_closing - opening
    mask = np.abs(actual_delta) >= 1e-9
    n = int(mask.sum())
    if n == 0:
        return {"n": 0, "accuracy": None}
    return {
        "n": n,
        "accuracy": float((np.sign(predicted_delta[mask]) == np.sign(actual_delta[mask])).mean()),
    }


def _predict_closing(model: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    predicted_movement = model.predict(frame[FEATURES])
    return np.clip(
        _sigmoid(frame["opening_logit"].to_numpy(float) + predicted_movement),
        1e-6,
        1.0 - 1e-6,
    )


def evaluate_league(frame: pd.DataFrame, league: str) -> tuple[dict, dict]:
    train = frame[frame["season"].isin(TRAIN_SEASONS)].copy()
    validation = frame[frame["season"] == VALIDATION_SEASON].copy()
    test = frame[frame["season"] == TEST_SEASON].copy()
    if train.empty or validation.empty or test.empty:
        raise RuntimeError(
            f"{league}: empty split train={len(train)} validation={len(validation)} test={len(test)}"
        )

    model = _estimator()
    model.fit(train[FEATURES], train["movement_logit"].to_numpy(float))

    validation_actual = validation["closing_probability"].to_numpy(float)
    validation_baseline = validation["opening_probability"].to_numpy(float)
    validation_candidate = _predict_closing(model, validation)
    validation_baseline_scores = _scores(validation_actual, validation_baseline)
    validation_candidate_scores = _scores(validation_actual, validation_candidate)
    admissible = bool(
        validation_candidate_scores["rmse"] < validation_baseline_scores["rmse"]
        and validation_candidate_scores["mae"] < validation_baseline_scores["mae"]
    )

    test_actual = test["closing_probability"].to_numpy(float)
    test_baseline = test["opening_probability"].to_numpy(float)
    test_raw_candidate = _predict_closing(model, test)
    test_selected = test_raw_candidate if admissible else test_baseline.copy()
    test_baseline_scores = _scores(test_actual, test_baseline)
    test_candidate_scores = _scores(test_actual, test_raw_candidate)
    test_selected_scores = _scores(test_actual, test_selected)
    passed = bool(
        admissible
        and test_candidate_scores["rmse"] < test_baseline_scores["rmse"]
        and test_candidate_scores["mae"] < test_baseline_scores["mae"]
    )

    source_counts = dict(Counter(frame["price_source"].astype(str)))
    season_counts = {
        str(season): int(count)
        for season, count in frame.groupby("season", sort=True).size().items()
    }
    report = {
        "league": league,
        "features": FEATURES,
        "coverage": {
            "train": int(len(train)),
            "validation": int(len(validation)),
            "test": int(len(test)),
            "price_sources": source_counts,
            "season_counts": season_counts,
        },
        "validation_baseline": validation_baseline_scores,
        "validation_candidate": validation_candidate_scores,
        "validation_delta_rmse": validation_candidate_scores["rmse"] - validation_baseline_scores["rmse"],
        "validation_delta_mae": validation_candidate_scores["mae"] - validation_baseline_scores["mae"],
        "validation_admissible": admissible,
        "test_baseline": test_baseline_scores,
        "test_raw_candidate": test_candidate_scores,
        "test_selected": test_selected_scores,
        "test_delta_rmse": test_candidate_scores["rmse"] - test_baseline_scores["rmse"],
        "test_delta_mae": test_candidate_scores["mae"] - test_baseline_scores["mae"],
        "test_direction": _direction_accuracy(test_baseline, test_actual, test_raw_candidate),
        "replication_status": "PASS" if passed else "FAIL",
        "final_active_mode": "MOVEMENT_MODEL" if passed else "NO_MOVEMENT_FALLBACK",
    }
    pooled = {
        "actual": test_actual,
        "baseline": test_baseline,
        "selected": test_selected,
        "passed": passed,
    }
    return report, pooled


def evaluate() -> dict:
    league_reports: list[dict] = []
    pooled_parts: list[dict] = []
    for league in LEAGUE_IDS:
        frame = load_league_frame(league)
        report, pooled = evaluate_league(frame, league)
        league_reports.append(report)
        pooled_parts.append(pooled)

    actual = np.concatenate([part["actual"] for part in pooled_parts])
    baseline = np.concatenate([part["baseline"] for part in pooled_parts])
    selected = np.concatenate([part["selected"] for part in pooled_parts])
    baseline_scores = _scores(actual, baseline)
    selected_scores = _scores(actual, selected)
    pass_count = sum(bool(part["passed"]) for part in pooled_parts)
    pooled_better = bool(
        selected_scores["rmse"] < baseline_scores["rmse"]
        and selected_scores["mae"] < baseline_scores["mae"]
    )
    decision = "PILOT" if pass_count >= 2 and pooled_better else "SKIP"

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_MARKET_TEMPORAL_OOT",
        "research_only": True,
        "production_promotion": False,
        "betting_enabled": False,
        "result": "NO_BET",
        "opened_2026_27_data_used": False,
        "train_seasons": list(TRAIN_SEASONS),
        "validation_season": VALIDATION_SEASON,
        "test_season": TEST_SEASON,
        "target": "CLOSING_OU25_DEVIG_PROBABILITY",
        "baseline": "OPENING_OU25_DEVIG_PROBABILITY_NO_MOVEMENT",
        "league_reports": league_reports,
        "pooled": {
            "n": int(len(actual)),
            "league_pass_count": int(pass_count),
            "league_count": len(pooled_parts),
            "baseline": baseline_scores,
            "validation_selected": selected_scores,
            "delta_rmse": selected_scores["rmse"] - baseline_scores["rmse"],
            "delta_mae": selected_scores["mae"] - baseline_scores["mae"],
            "pooled_better_both": pooled_better,
            "decision": decision,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/ou25_closing_movement_v1/report.json"),
    )
    args = parser.parse_args()
    report = evaluate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
