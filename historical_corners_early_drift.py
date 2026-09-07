"""Early-season drift audit for the historical CORNERS10 football signal.

Research only. This module asks a practical question: how many matches into a held-out
season are needed before the direction of CORNERS10 vs simpler football baselines starts
to resemble the full-season result?

It never reads prospective experiment tables, writes Supabase, touches production .pkl
artifacts, searches thresholds, or promotes a model.
"""
from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from historical_football_signal_lab import RESULT_TO_INT, add_difference_features
from historical_football_window_audit import WINDOW_SETS

CANDIDATE = "CORNERS10"
BASELINES = ("FORM10", "GOALS10")
EARLY_PREFIXES = (20, 40, 80, 160)


def _model() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000)),
        ]
    )


def _per_match_losses(y: np.ndarray, probabilities: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if len(y) != len(probabilities):
        raise ValueError("y and probabilities length mismatch")
    onehot = np.eye(3)[y]
    brier = np.sum((probabilities - onehot) ** 2, axis=1)
    chosen = probabilities[np.arange(len(y)), y]
    logloss = -np.log(np.clip(chosen, 1e-15, 1.0))
    return brier, logloss


def prefix_loss_comparison(
    y: np.ndarray,
    candidate_probabilities: np.ndarray,
    baseline_probabilities: np.ndarray,
    prefixes: Iterable[int] = EARLY_PREFIXES,
) -> pd.DataFrame:
    """Compare cumulative candidate-vs-baseline loss without using later rows in a prefix."""
    cand_brier, cand_log = _per_match_losses(y, candidate_probabilities)
    base_brier, base_log = _per_match_losses(y, baseline_probabilities)
    brier_diff = cand_brier - base_brier
    log_diff = cand_log - base_log
    full_brier = float(np.mean(brier_diff))
    full_log = float(np.mean(log_diff))

    rows = []
    seen = set()
    for raw_n in prefixes:
        n = int(raw_n)
        if n <= 0:
            raise ValueError("prefixes must be positive")
        if n in seen:
            raise ValueError("prefixes must be unique")
        seen.add(n)
        if n > len(y):
            continue
        prefix_brier = float(np.mean(brier_diff[:n]))
        prefix_log = float(np.mean(log_diff[:n]))
        rows.append(
            {
                "prefix_matches": n,
                "delta_brier": prefix_brier,
                "delta_log_loss": prefix_log,
                "candidate_brier_better": bool(prefix_brier < 0),
                "candidate_log_loss_better": bool(prefix_log < 0),
                "full_season_delta_brier": full_brier,
                "full_season_delta_log_loss": full_log,
                "brier_direction_agrees_with_full": bool((prefix_brier < 0) == (full_brier < 0)),
                "log_loss_direction_agrees_with_full": bool((prefix_log < 0) == (full_log < 0)),
            }
        )
    return pd.DataFrame(rows)


def run_early_drift_audit(
    frame: pd.DataFrame,
    min_train_seasons: int = 3,
    prefixes: Iterable[int] = EARLY_PREFIXES,
) -> pd.DataFrame:
    """Run expanding-season, held-out-season early drift checks for each league."""
    frame = add_difference_features(frame)
    rows = []
    for league, league_df in frame.groupby("league"):
        seasons = sorted(league_df["season"].dropna().unique())
        for i in range(min_train_seasons, len(seasons)):
            train_seasons = seasons[:i]
            test_season = seasons[i]
            train = league_df[league_df.season.isin(train_seasons)].copy()
            test = league_df[league_df.season == test_season].copy()
            test = test.sort_values("match_date", kind="stable")

            y_train = train.result.map(RESULT_TO_INT).to_numpy()
            y_test = test.result.map(RESULT_TO_INT).to_numpy()
            probabilities: dict[str, np.ndarray] = {}
            for feature_set in (CANDIDATE, *BASELINES):
                model = _model()
                model.fit(train[WINDOW_SETS[feature_set]], y_train)
                probabilities[feature_set] = model.predict_proba(test[WINDOW_SETS[feature_set]])

            for baseline in BASELINES:
                detail = prefix_loss_comparison(
                    y_test,
                    probabilities[CANDIDATE],
                    probabilities[baseline],
                    prefixes,
                )
                for record in detail.to_dict("records"):
                    rows.append(
                        {
                            "league": league,
                            "test_season": test_season,
                            "candidate": CANDIDATE,
                            "baseline": baseline,
                            "test_matches": len(test),
                            **record,
                        }
                    )
    return pd.DataFrame(rows).sort_values(["baseline", "prefix_matches", "league", "test_season"])


def summarize_early_drift(detail: pd.DataFrame) -> pd.DataFrame:
    required = {
        "baseline",
        "prefix_matches",
        "delta_brier",
        "delta_log_loss",
        "candidate_brier_better",
        "candidate_log_loss_better",
        "brier_direction_agrees_with_full",
        "log_loss_direction_agrees_with_full",
    }
    missing = required - set(detail.columns)
    if missing:
        raise ValueError(f"missing early-drift columns: {sorted(missing)}")

    rows = []
    for (baseline, prefix), group in detail.groupby(["baseline", "prefix_matches"]):
        rows.append(
            {
                "candidate": CANDIDATE,
                "baseline": baseline,
                "prefix_matches": int(prefix),
                "season_tests": int(len(group)),
                "mean_delta_brier": float(group.delta_brier.mean()),
                "mean_delta_log_loss": float(group.delta_log_loss.mean()),
                "brier_improvement_rate": float(group.candidate_brier_better.mean()),
                "log_loss_improvement_rate": float(group.candidate_log_loss_better.mean()),
                "brier_direction_agreement_rate": float(group.brier_direction_agrees_with_full.mean()),
                "log_loss_direction_agreement_rate": float(group.log_loss_direction_agrees_with_full.mean()),
            }
        )
    return pd.DataFrame(rows).sort_values(["baseline", "prefix_matches"])


def write_early_drift_reports(frame: pd.DataFrame, output_dir) -> tuple[pd.DataFrame, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    detail = run_early_drift_audit(frame)
    summary = summarize_early_drift(detail)
    detail.to_csv(output_dir / "corners_early_drift_detail.csv", index=False)
    summary.to_csv(output_dir / "corners_early_drift_summary.csv", index=False)
    return detail, summary
