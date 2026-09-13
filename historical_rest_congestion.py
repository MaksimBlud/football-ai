"""Leakage-safe league-schedule rest and congestion proxy research.

Research only. Football-Data historical rows contain league fixtures, not cup/European
schedules, so these signals are explicitly league-schedule proxies rather than complete
calendar congestion measures.
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

REST_CONGESTION = [
    "diff_league_rest_days",
    "diff_league_matches_7d",
    "diff_league_matches_14d",
]
FEATURE_SETS = {
    "CORNERS10": CORNERS10,
    "CORNERS10_REST": CORNERS10 + REST_CONGESTION,
    "MARKET_MODEL": MARKET,
    "MARKET_REST": MARKET + REST_CONGESTION,
}
PAIRS = (
    ("CORNERS10", "CORNERS10_REST"),
    ("MARKET_MODEL", "MARKET_REST"),
)


def add_league_schedule_rest(frame: pd.DataFrame) -> pd.DataFrame:
    """Snapshot league-only rest days and prior 7/14-day fixture counts pre-match."""
    required = {"league", "season", "match_date", "home_team", "away_team"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing rest/congestion columns: {sorted(missing)}")
    out = frame.copy()
    for prefix in ("home", "away"):
        out[f"{prefix}_league_rest_days"] = np.nan
        out[f"{prefix}_league_matches_7d"] = 0.0
        out[f"{prefix}_league_matches_14d"] = 0.0

    for _, season_df in out.groupby(["league", "season"], sort=False):
        histories: dict[str, deque[pd.Timestamp]] = defaultdict(deque)
        ordered = season_df.sort_values(
            ["match_date", "home_team", "away_team"], kind="stable"
        )
        for idx, row in ordered.iterrows():
            current = pd.Timestamp(row.match_date)
            for team, prefix in (
                (str(row.home_team), "home"),
                (str(row.away_team), "away"),
            ):
                prior = histories[team]
                if prior:
                    out.at[idx, f"{prefix}_league_rest_days"] = (
                        current - prior[-1]
                    ).total_seconds() / 86400.0
                out.at[idx, f"{prefix}_league_matches_7d"] = float(
                    sum((current - dt).total_seconds() <= 7 * 86400 for dt in prior)
                )
                out.at[idx, f"{prefix}_league_matches_14d"] = float(
                    sum((current - dt).total_seconds() <= 14 * 86400 for dt in prior)
                )
            histories[str(row.home_team)].append(current)
            histories[str(row.away_team)].append(current)

    out["diff_league_rest_days"] = (
        out.home_league_rest_days - out.away_league_rest_days
    )
    out["diff_league_matches_7d"] = (
        out.home_league_matches_7d - out.away_league_matches_7d
    )
    out["diff_league_matches_14d"] = (
        out.home_league_matches_14d - out.away_league_matches_14d
    )
    return out


def _score(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    onehot = np.eye(3)[y]
    return {
        "accuracy": float((p.argmax(axis=1) == y).mean()),
        "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
        "log_loss": float(log_loss(y, p, labels=[0, 1, 2])),
    }


def run_rest_ablation(frame: pd.DataFrame, min_train_seasons: int = 3) -> pd.DataFrame:
    enriched = add_league_schedule_rest(add_difference_features(frame))
    rows = []
    for league, league_df in enriched.groupby("league"):
        seasons = sorted(league_df.season.unique())
        for i in range(min_train_seasons, len(seasons)):
            train = league_df[league_df.season.isin(seasons[:i])]
            test = league_df[league_df.season == seasons[i]]
            for name, columns in FEATURE_SETS.items():
                market_based = name.startswith("MARKET")
                usable_train = (
                    train.dropna(subset=MARKET + ["result"])
                    if market_based
                    else train.dropna(subset=["result"])
                )
                usable_test = (
                    test.dropna(subset=MARKET + ["result"])
                    if market_based
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
                    "delta_accuracy": float(row.accuracy_candidate-row.accuracy_baseline),
                    "delta_brier": float(row.brier_candidate-row.brier_baseline),
                    "delta_log_loss": float(row.log_loss_candidate-row.log_loss_baseline),
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
                "mean_delta_accuracy": float(np.average(group.delta_accuracy, weights=weights)),
                "mean_delta_brier": float(np.average(group.delta_brier, weights=weights)),
                "mean_delta_log_loss": float(np.average(group.delta_log_loss, weights=weights)),
                "brier_wins": int((group.delta_brier < 0).sum()),
                "log_loss_wins": int((group.delta_log_loss < 0).sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["baseline", "league"])


def write_rest_reports(frame: pd.DataFrame, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    detail = run_rest_ablation(frame)
    paired = paired_incremental(detail)
    summary = summarize_paired(paired)
    detail.to_csv(output_dir / "rest_congestion_ablation.csv", index=False)
    paired.to_csv(output_dir / "rest_congestion_paired.csv", index=False)
    summary.to_csv(output_dir / "rest_congestion_summary.csv", index=False)
    return summary
