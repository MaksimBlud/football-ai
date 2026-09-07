"""Classify historical CORNERS10 portability from paired season robustness.

Research only. Classification thresholds are documented in
research/SEASON_INVARIANT_CORNERS_V1.md. This module does not train or promote
production models and does not read prospective outcomes.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PRIMARY_BASELINE = "GOALS10"
PRIMARY_LEAGUES = ("EPL", "LA_LIGA", "SERIE_A")
MIN_SEASONS = 5
STRONG_WIN_RATE = 0.70
SUPPORTIVE_WIN_RATE = 0.55


def classify_leagues(
    paired_summary: pd.DataFrame,
    baseline: str = PRIMARY_BASELINE,
) -> pd.DataFrame:
    required = {
        "league", "candidate", "baseline", "seasons",
        "mean_delta_brier", "mean_delta_log_loss",
        "brier_win_rate", "log_loss_win_rate",
    }
    missing = required - set(paired_summary.columns)
    if missing:
        raise ValueError(f"missing robustness summary columns: {sorted(missing)}")

    rows = []
    source = paired_summary[paired_summary.baseline == baseline].copy()
    for league in PRIMARY_LEAGUES:
        matches = source[source.league == league]
        if len(matches) != 1:
            rows.append({"league": league, "baseline": baseline, "classification": "UNSTABLE", "reason": "MISSING_OR_DUPLICATE_SUMMARY"})
            continue
        row = matches.iloc[0]
        enough = int(row.seasons) >= MIN_SEASONS
        means_better = float(row.mean_delta_brier) < 0 and float(row.mean_delta_log_loss) < 0
        strong = (
            enough and means_better
            and float(row.brier_win_rate) >= STRONG_WIN_RATE
            and float(row.log_loss_win_rate) >= STRONG_WIN_RATE
        )
        supportive = (
            enough and means_better
            and float(row.brier_win_rate) >= SUPPORTIVE_WIN_RATE
            and float(row.log_loss_win_rate) >= SUPPORTIVE_WIN_RATE
        )
        classification = "STRONG" if strong else ("SUPPORTIVE" if supportive else "UNSTABLE")
        rows.append(
            {
                "league": league,
                "baseline": baseline,
                "seasons": int(row.seasons),
                "mean_delta_brier": float(row.mean_delta_brier),
                "mean_delta_log_loss": float(row.mean_delta_log_loss),
                "brier_win_rate": float(row.brier_win_rate),
                "log_loss_win_rate": float(row.log_loss_win_rate),
                "classification": classification,
                "reason": "FIXED_STABILITY_RULE",
            }
        )
    return pd.DataFrame(rows)


def overall_portability(league_classification: pd.DataFrame) -> str:
    required = {"league", "classification"}
    missing = required - set(league_classification.columns)
    if missing:
        raise ValueError(f"missing league classification columns: {sorted(missing)}")
    subset = league_classification[league_classification.league.isin(PRIMARY_LEAGUES)]
    if set(subset.league) != set(PRIMARY_LEAGUES):
        return "NOT_PORTABLE"
    values = subset.classification.tolist()
    if all(value == "STRONG" for value in values):
        return "PORTABLE_STRONG"
    if all(value != "UNSTABLE" for value in values) and sum(value in {"STRONG", "SUPPORTIVE"} for value in values) >= 2:
        return "PORTABLE_SUPPORTIVE"
    return "NOT_PORTABLE"


def write_invariant_report(paired_summary: pd.DataFrame, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    leagues = classify_leagues(paired_summary)
    portability = overall_portability(leagues)
    leagues.to_csv(output_dir / "season_invariant_corners_v1.csv", index=False)
    (output_dir / "season_invariant_corners_v1_status.txt").write_text(portability + "\n", encoding="utf-8")
    return leagues, portability
