"""Leakage-safe fixed interaction research for validated historical signal families.

Research only. Tests whether two preregistered moderation terms add information after
including the full main effects from TEAM_STRENGTH_TRAJECTORY_V1 and
SHOT_QUALITY_PROXY_V1. REST_CONGESTION_V1 is intentionally excluded because that
same-sample hypothesis is closed negative.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from historical_football_market_incremental import CORNERS10, MARKET
from historical_football_signal_lab import RESULT_TO_INT, add_difference_features
from historical_shot_quality_profile import EVIDENCE_TIER, SHOT_QUALITY10
from historical_team_strength_trajectory import TRAJECTORY5, add_team_strength_trajectory

INTERACTION_FEATURES = [
    "interaction_elo_delta_x_abs_sot_rate",
    "interaction_sot_rate_x_abs_performance_residual",
]
MAIN_EFFECTS = TRAJECTORY5 + SHOT_QUALITY10
FEATURE_SETS = {
    "CORNERS10_TRAJECTORY_SHOT": CORNERS10 + MAIN_EFFECTS,
    "CORNERS10_TRAJECTORY_SHOT_INTERACTIONS": CORNERS10 + MAIN_EFFECTS + INTERACTION_FEATURES,
    "MARKET_TRAJECTORY_SHOT": MARKET + MAIN_EFFECTS,
    "MARKET_TRAJECTORY_SHOT_INTERACTIONS": MARKET + MAIN_EFFECTS + INTERACTION_FEATURES,
}
PAIRS = (
    ("CORNERS10_TRAJECTORY_SHOT", "CORNERS10_TRAJECTORY_SHOT_INTERACTIONS"),
    ("MARKET_TRAJECTORY_SHOT", "MARKET_TRAJECTORY_SHOT_INTERACTIONS"),
)


def add_fixed_interactions(frame: pd.DataFrame) -> pd.DataFrame:
    """Add two fixed directional moderation terms; no threshold/window search."""
    required = {
        "diff_elo_delta_5",
        "diff_performance_residual_5",
        "diff_sot_rate_for_10",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing interaction columns: {sorted(missing)}")
    out = frame.copy()
    out["interaction_elo_delta_x_abs_sot_rate"] = (
        out.diff_elo_delta_5 * out.diff_sot_rate_for_10.abs()
    )
    out["interaction_sot_rate_x_abs_performance_residual"] = (
        out.diff_sot_rate_for_10 * out.diff_performance_residual_5.abs()
    )
    return out


def build_interaction_features(frame: pd.DataFrame) -> pd.DataFrame:
    enriched = add_team_strength_trajectory(add_difference_features(frame))
    return add_fixed_interactions(enriched)


def _score(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    onehot = np.eye(3)[y]
    return {
        "accuracy": float((p.argmax(axis=1) == y).mean()),
        "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
        "log_loss": float(log_loss(y, p, labels=[0, 1, 2])),
    }


def run_interaction_ablation(frame: pd.DataFrame, min_train_seasons: int = 3) -> pd.DataFrame:
    enriched = build_interaction_features(frame)
    rows: list[dict[str, object]] = []
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
                        "evidence_tier": EVIDENCE_TIER.get(league, "UNCLASSIFIED"),
                        "test_season": seasons[i],
                        "feature_set": name,
                        "matches": len(y),
                        **_score(y, p),
                    }
                )
    return pd.DataFrame(rows)


def paired_incremental(results: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for baseline, candidate in PAIRS:
        base = results[results.feature_set == baseline]
        cand = results[results.feature_set == candidate]
        merged = cand.merge(
            base,
            on=["league", "evidence_tier", "test_season"],
            suffixes=("_candidate", "_baseline"),
            validate="one_to_one",
        )
        if len(merged) != len(cand):
            raise ValueError(f"incomplete paired coverage for {candidate}")
        for _, row in merged.iterrows():
            rows.append(
                {
                    "league": row.league,
                    "evidence_tier": row.evidence_tier,
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
    rows: list[dict[str, object]] = []
    for (league, tier, baseline, candidate), group in paired.groupby(
        ["league", "evidence_tier", "baseline", "candidate"]
    ):
        weights = group.matches.to_numpy()
        rows.append(
            {
                "league": league,
                "evidence_tier": tier,
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


def write_interaction_reports(frame: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    detail = run_interaction_ablation(frame)
    paired = paired_incremental(detail)
    summary = summarize_paired(paired)
    detail.to_csv(output_dir / "signal_interactions_ablation.csv", index=False)
    paired.to_csv(output_dir / "signal_interactions_paired.csv", index=False)
    summary.to_csv(output_dir / "signal_interactions_summary.csv", index=False)
    return summary
