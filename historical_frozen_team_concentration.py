"""Team-concentration audit for already frozen historical OOS rules.

Research only. Reconstructs each frozen rule's OOS rows without re-selection, reports
profit contribution by home team, and measures leave-one-home-team-out sensitivity.
No tuning, activation, training, Supabase writes, or production artifact changes.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from historical_strategy_stability import add_confidence_bucket


def frozen_oos_rows(prepared: pd.DataFrame, frozen_summary: pd.DataFrame) -> pd.DataFrame:
    required = {"league", "season", "market_pick", "profit", "won", "home_team"}
    missing = required - set(prepared.columns)
    if missing:
        raise ValueError("Missing prepared columns: " + ", ".join(sorted(missing)))
    summary_required = {"league", "first_test_season", "market_pick", "confidence_bucket"}
    missing_summary = summary_required - set(frozen_summary.columns)
    if missing_summary:
        raise ValueError("Missing frozen summary columns: " + ", ".join(sorted(missing_summary)))

    frame = add_confidence_bucket(prepared)
    pieces = []
    for rule in frozen_summary.itertuples(index=False):
        league_frame = frame[frame["league"] == rule.league].copy()
        seasons = sorted(league_frame["season"].astype(str).unique())
        test_seasons = [season for season in seasons if season >= str(rule.first_test_season)]
        selected = league_frame[
            league_frame["season"].astype(str).isin(test_seasons)
            & (league_frame["market_pick"].astype(str) == str(rule.market_pick))
            & (league_frame["confidence_bucket"].astype(str) == str(rule.confidence_bucket))
        ].copy()
        selected["frozen_market_pick"] = str(rule.market_pick)
        selected["frozen_confidence_bucket"] = str(rule.confidence_bucket)
        pieces.append(selected)
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def team_concentration(
    prepared: pd.DataFrame, frozen_summary: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    selected = frozen_oos_rows(prepared, frozen_summary)
    team_rows = []
    loo_rows = []
    summary_rows = []

    for league, group in selected.groupby("league", sort=True):
        total_matches = len(group)
        total_profit = float(group["profit"].sum())
        total_roi = total_profit / total_matches if total_matches else float("nan")

        team_stats = []
        for home_team, team_group in group.groupby("home_team", sort=True):
            matches = len(team_group)
            profit = float(team_group["profit"].sum())
            row = {
                "league": league,
                "home_team": home_team,
                "matches": matches,
                "wins": int(team_group["won"].sum()),
                "profit": profit,
                "roi": profit / matches if matches else float("nan"),
                "absolute_profit": abs(profit),
            }
            team_rows.append(row)
            team_stats.append(row)

            remaining = group[group["home_team"] != home_team]
            remaining_matches = len(remaining)
            remaining_profit = float(remaining["profit"].sum())
            loo_rows.append({
                "league": league,
                "excluded_home_team": home_team,
                "remaining_matches": remaining_matches,
                "remaining_profit": remaining_profit,
                "remaining_roi": remaining_profit / remaining_matches if remaining_matches else float("nan"),
            })

        team_frame = pd.DataFrame(team_stats)
        positive_contributions = team_frame[team_frame["profit"] > 0].sort_values("profit", ascending=False)
        positive_profit_sum = float(positive_contributions["profit"].sum())
        top1_profit = float(positive_contributions.head(1)["profit"].sum())
        top3_profit = float(positive_contributions.head(3)["profit"].sum())
        league_loo = pd.DataFrame([row for row in loo_rows if row["league"] == league])
        summary_rows.append({
            "league": league,
            "matches": total_matches,
            "profit": total_profit,
            "roi": total_roi,
            "home_teams": int(team_frame["home_team"].nunique()),
            "profitable_home_teams": int((team_frame["profit"] > 0).sum()),
            "positive_profit_sum": positive_profit_sum,
            "top1_positive_profit_share": top1_profit / positive_profit_sum if positive_profit_sum > 0 else float("nan"),
            "top3_positive_profit_share": top3_profit / positive_profit_sum if positive_profit_sum > 0 else float("nan"),
            "leave_one_team_out_min_roi": float(league_loo["remaining_roi"].min()),
            "leave_one_team_out_max_roi": float(league_loo["remaining_roi"].max()),
            "leave_one_team_out_all_positive": bool((league_loo["remaining_roi"] > 0).all()),
        })

    return pd.DataFrame(summary_rows), pd.DataFrame(team_rows), pd.DataFrame(loo_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Frozen-rule home-team concentration audit")
    parser.add_argument("prepared_matches", type=Path)
    parser.add_argument("frozen_summary", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/historical_strategy_team_concentration"))
    args = parser.parse_args()

    summary, by_team, leave_one_out = team_concentration(
        pd.read_csv(args.prepared_matches), pd.read_csv(args.frozen_summary)
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "team_concentration_summary.csv", index=False)
    by_team.to_csv(args.output_dir / "team_concentration_by_home_team.csv", index=False)
    leave_one_out.to_csv(args.output_dir / "team_concentration_leave_one_out.csv", index=False)
    print("FROZEN RULE TEAM CONCENTRATION — RESEARCH ONLY")
    print(summary.to_string(index=False))
    print("Rule identity and OOS boundary come from the frozen validation; no rule is re-selected.")
    print("No tuning, activation, training, Supabase writes, Structural changes, or .pkl changes performed.")


if __name__ == "__main__":
    main()
