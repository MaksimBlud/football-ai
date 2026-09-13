"""Leakage-safe historical team-strength trajectory research.

Research only. Adds fixed, point-in-time Elo trajectory and performance-vs-expectation
signals to the existing Historical Football Signal Lab. All features for a fixture are
snapshotted before that fixture result is used.
"""
from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from historical_football_signal_lab import RESULT_TO_INT, add_difference_features
from historical_football_market_incremental import CORNERS10, MARKET

TRAJECTORY5 = [
    "diff_elo_level",
    "diff_elo_delta_5",
    "diff_performance_residual_5",
]
FEATURE_SETS = {
    "CORNERS10": CORNERS10,
    "CORNERS10_TRAJECTORY": CORNERS10 + TRAJECTORY5,
    "MARKET_MODEL": MARKET,
    "MARKET_TRAJECTORY": MARKET + TRAJECTORY5,
}
PAIRS = (
    ("CORNERS10", "CORNERS10_TRAJECTORY"),
    ("MARKET_MODEL", "MARKET_TRAJECTORY"),
)


def _expected_score(home_rating: float, away_rating: float, home_advantage: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((away_rating - (home_rating + home_advantage)) / 400.0))


def _actual_score(result: str) -> float:
    return 1.0 if result == "H" else 0.5 if result == "D" else 0.0


def _mean_last(values: deque[float], n: int) -> float:
    data = list(values)[-n:]
    return float(np.mean(data)) if data else np.nan


def add_team_strength_trajectory(
    frame: pd.DataFrame,
    *,
    initial_rating: float = 1500.0,
    k_factor: float = 20.0,
    home_advantage: float = 65.0,
) -> pd.DataFrame:
    """Add fixed pre-match strength-level, five-match trajectory and residual signals."""
    required = {"league", "match_date", "home_team", "away_team", "result"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing trajectory columns: {sorted(missing)}")

    out = frame.copy()
    for prefix in ("home", "away"):
        for name in ("elo_level", "elo_delta_5", "performance_residual_5"):
            out[f"{prefix}_{name}"] = np.nan

    for _, league_df in out.groupby("league", sort=False):
        ratings: dict[str, float] = defaultdict(lambda: initial_rating)
        pre_ratings: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=10))
        residuals: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=10))

        ordered = league_df.sort_values(
            ["match_date", "home_team", "away_team"],
            kind="stable",
        )
        for idx, row in ordered.iterrows():
            home = str(row.home_team)
            away = str(row.away_team)
            home_rating = float(ratings[home])
            away_rating = float(ratings[away])

            out.at[idx, "home_elo_level"] = home_rating
            out.at[idx, "away_elo_level"] = away_rating

            for team, prefix, rating in (
                (home, "home", home_rating),
                (away, "away", away_rating),
            ):
                history = pre_ratings[team]
                if len(history) >= 5:
                    out.at[idx, f"{prefix}_elo_delta_5"] = rating - list(history)[-5]
                if residuals[team]:
                    out.at[idx, f"{prefix}_performance_residual_5"] = _mean_last(
                        residuals[team], 5
                    )

            expected_home = _expected_score(home_rating, away_rating, home_advantage)
            actual_home = _actual_score(str(row.result))
            actual_away = 1.0 - actual_home
            expected_away = 1.0 - expected_home

            pre_ratings[home].append(home_rating)
            pre_ratings[away].append(away_rating)
            residuals[home].append(actual_home - expected_home)
            residuals[away].append(actual_away - expected_away)

            delta = k_factor * (actual_home - expected_home)
            ratings[home] = home_rating + delta
            ratings[away] = away_rating - delta

    out["diff_elo_level"] = out.home_elo_level - out.away_elo_level
    out["diff_elo_delta_5"] = out.home_elo_delta_5 - out.away_elo_delta_5
    out["diff_performance_residual_5"] = (
        out.home_performance_residual_5 - out.away_performance_residual_5
    )
    return out


def _score(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    onehot = np.eye(3)[y]
    return {
        "accuracy": float((p.argmax(axis=1) == y).mean()),
        "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
        "log_loss": float(log_loss(y, p, labels=[0, 1, 2])),
    }


def run_trajectory_ablation(
    frame: pd.DataFrame,
    min_train_seasons: int = 3,
) -> pd.DataFrame:
    enriched = add_team_strength_trajectory(add_difference_features(frame))
    rows = []
    for league, league_df in enriched.groupby("league"):
        seasons = sorted(league_df.season.unique())
        for i in range(min_train_seasons, len(seasons)):
            train = league_df[league_df.season.isin(seasons[:i])]
            test = league_df[league_df.season == seasons[i]]
            for name, columns in FEATURE_SETS.items():
                usable_train = (
                    train.dropna(subset=MARKET + ["result"])
                    if name.startswith("MARKET")
                    else train.dropna(subset=["result"])
                )
                usable_test = (
                    test.dropna(subset=MARKET + ["result"])
                    if name.startswith("MARKET")
                    else test.dropna(subset=["result"])
                )
                if usable_train.empty or usable_test.empty:
                    continue
                model = Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                        ("model", LogisticRegression(max_iter=1000)),
                    ]
                )
                y_train = usable_train.result.map(RESULT_TO_INT).to_numpy()
                y = usable_test.result.map(RESULT_TO_INT).to_numpy()
                model.fit(usable_train[columns], y_train)
                p = model.predict_proba(usable_test[columns])
                rows.append(
                    {
                        "league": league,
                        "test_season": seasons[i],
                        "feature_set": name,
                        "matches": len(y),
                        **_score(y, p),
                    }
                )
    return pd.DataFrame(rows)


def paired_incremental(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for baseline, candidate in PAIRS:
        base = results[results.feature_set == baseline]
        cand = results[results.feature_set == candidate]
        merged = cand.merge(
            base,
            on=["league", "test_season"],
            suffixes=("_candidate", "_baseline"),
            validate="one_to_one",
        )
        if len(merged) != len(cand):
            raise ValueError(f"incomplete paired coverage for {candidate}")
        for _, row in merged.iterrows():
            rows.append(
                {
                    "league": row.league,
                    "test_season": row.test_season,
                    "baseline": baseline,
                    "candidate": candidate,
                    "matches": int(row.matches_candidate),
                    "delta_accuracy": float(row.accuracy_candidate - row.accuracy_baseline),
                    "delta_brier": float(row.brier_candidate - row.brier_baseline),
                    "delta_log_loss": float(row.log_loss_candidate - row.log_loss_baseline),
                }
            )
    return pd.DataFrame(rows).sort_values(["baseline", "league", "test_season"])


def summarize_paired(paired: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (league, baseline, candidate), group in paired.groupby(
        ["league", "baseline", "candidate"]
    ):
        weights = group.matches.to_numpy()
        rows.append(
            {
                "league": league,
                "baseline": baseline,
                "candidate": candidate,
                "matches": int(group.matches.sum()),
                "seasons": len(group),
                "mean_delta_accuracy": float(
                    np.average(group.delta_accuracy, weights=weights)
                ),
                "mean_delta_brier": float(
                    np.average(group.delta_brier, weights=weights)
                ),
                "mean_delta_log_loss": float(
                    np.average(group.delta_log_loss, weights=weights)
                ),
                "brier_wins": int((group.delta_brier < 0).sum()),
                "log_loss_wins": int((group.delta_log_loss < 0).sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["baseline", "league"])


def write_trajectory_reports(frame: pd.DataFrame, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    detail = run_trajectory_ablation(frame)
    paired = paired_incremental(detail)
    summary = summarize_paired(paired)
    detail.to_csv(output_dir / "team_strength_trajectory_ablation.csv", index=False)
    paired.to_csv(output_dir / "team_strength_trajectory_paired.csv", index=False)
    summary.to_csv(output_dir / "team_strength_trajectory_summary.csv", index=False)
    return summary
