"""Combined season/team stress audit for already frozen historical OOS rules.

Research only. For every frozen league rule, remove one OOS season and one home team
simultaneously, without re-selection or tuning, and report the remaining ROI. This tests
whether separate season and team robustness can hide a concentrated team-season effect.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from historical_frozen_team_concentration import frozen_oos_rows


def team_season_stress(
    prepared: pd.DataFrame, frozen_summary: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected = frozen_oos_rows(prepared, frozen_summary)
    detail_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []

    for league, group in selected.groupby("league", sort=True):
        seasons = sorted(group["season"].astype(str).unique())
        teams = sorted(group["home_team"].astype(str).unique())
        for excluded_season in seasons:
            for excluded_team in teams:
                remaining = group[
                    (group["season"].astype(str) != excluded_season)
                    & (group["home_team"].astype(str) != excluded_team)
                ]
                matches = len(remaining)
                profit = float(remaining["profit"].sum())
                detail_rows.append({
                    "league": league,
                    "excluded_season": excluded_season,
                    "excluded_home_team": excluded_team,
                    "remaining_matches": matches,
                    "remaining_profit": profit,
                    "remaining_roi": profit / matches if matches else float("nan"),
                })

        league_detail = pd.DataFrame([row for row in detail_rows if row["league"] == league])
        valid_roi = league_detail["remaining_roi"].dropna()
        worst = league_detail.loc[league_detail["remaining_roi"].idxmin()]
        best = league_detail.loc[league_detail["remaining_roi"].idxmax()]
        summary_rows.append({
            "league": league,
            "base_matches": len(group),
            "base_profit": float(group["profit"].sum()),
            "base_roi": float(group["profit"].sum()) / len(group) if len(group) else float("nan"),
            "seasons": len(seasons),
            "home_teams": len(teams),
            "combinations": len(league_detail),
            "min_remaining_roi": float(valid_roi.min()),
            "max_remaining_roi": float(valid_roi.max()),
            "all_combinations_positive": bool((valid_roi > 0).all()),
            "worst_excluded_season": worst["excluded_season"],
            "worst_excluded_home_team": worst["excluded_home_team"],
            "worst_remaining_matches": int(worst["remaining_matches"]),
            "worst_remaining_profit": float(worst["remaining_profit"]),
            "best_excluded_season": best["excluded_season"],
            "best_excluded_home_team": best["excluded_home_team"],
        })

    return pd.DataFrame(summary_rows), pd.DataFrame(detail_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Frozen-rule combined home-team/season stress audit")
    parser.add_argument("prepared_matches", type=Path)
    parser.add_argument("frozen_summary", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/historical_strategy_team_season_stress"),
    )
    args = parser.parse_args()

    summary, details = team_season_stress(
        pd.read_csv(args.prepared_matches), pd.read_csv(args.frozen_summary)
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "team_season_stress_summary.csv", index=False)
    details.to_csv(args.output_dir / "team_season_stress_details.csv", index=False)
    print("FROZEN RULE TEAM × SEASON STRESS — RESEARCH ONLY")
    print(summary.to_string(index=False))
    print("Every row removes one OOS season and one home team simultaneously; the frozen rule is never re-selected.")
    print("No tuning, activation, training, Supabase writes, Structural changes, or .pkl changes performed.")


if __name__ == "__main__":
    main()
