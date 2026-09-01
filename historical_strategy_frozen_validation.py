"""Frozen-rule validation for Historical Strategy Lab.

Selects one segment per league using only an initial training window and then keeps that
segment unchanged for all later seasons. Research only; no training, Supabase writes,
live activation, Structural changes, or production artifact changes.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from historical_strategy_stability import add_confidence_bucket

INITIAL_TRAINING_SEASONS = 3
MIN_TRAINING_MATCHES = 100


def _segment_stats(group: pd.DataFrame) -> dict[str, float | int]:
    n = len(group)
    profit = float(group["profit"].sum())
    return {
        "matches": n,
        "wins": int(group["won"].sum()),
        "profit": profit,
        "roi": profit / n if n else float("nan"),
    }


def frozen_validation(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    prepared = add_confidence_bucket(frame)
    summaries = []
    season_rows = []
    for league, league_frame in prepared.groupby("league", sort=True):
        seasons = sorted(league_frame["season"].astype(str).unique())
        if len(seasons) <= INITIAL_TRAINING_SEASONS:
            continue
        train_seasons = seasons[:INITIAL_TRAINING_SEASONS]
        test_seasons = seasons[INITIAL_TRAINING_SEASONS:]
        training = league_frame[league_frame["season"].astype(str).isin(train_seasons)]
        candidates = []
        for (pick, bucket), group in training.groupby(["market_pick", "confidence_bucket"], observed=True, sort=True):
            if len(group) < MIN_TRAINING_MATCHES:
                continue
            stats = _segment_stats(group)
            season_stats = group.groupby(group["season"].astype(str))["profit"].agg(["sum", "size"])
            season_stats["roi"] = season_stats["sum"] / season_stats["size"]
            candidates.append({
                "market_pick": pick,
                "confidence_bucket": str(bucket),
                "training_matches": stats["matches"],
                "training_profit": stats["profit"],
                "training_roi": stats["roi"],
                "training_positive_season_share": float((season_stats["roi"] > 0).mean()),
            })
        if not candidates:
            continue
        chosen = pd.DataFrame(candidates).sort_values(
            ["training_roi", "training_positive_season_share", "training_matches", "market_pick", "confidence_bucket"],
            ascending=[False, False, False, True, True], kind="stable"
        ).iloc[0].to_dict()
        test = league_frame[
            league_frame["season"].astype(str).isin(test_seasons)
            & (league_frame["market_pick"] == chosen["market_pick"])
            & (league_frame["confidence_bucket"].astype(str) == chosen["confidence_bucket"])
        ]
        test_stats = _segment_stats(test)
        positive = 0
        for season, group in test.groupby(test["season"].astype(str), sort=True):
            stats = _segment_stats(group)
            positive += int(stats["roi"] > 0)
            season_rows.append({"league": league, "season": season, **chosen, **stats})
        summaries.append({
            "league": league,
            "training_seasons": ",".join(train_seasons),
            "first_test_season": test_seasons[0],
            "test_seasons": len(test_seasons),
            **chosen,
            "test_matches": test_stats["matches"],
            "test_wins": test_stats["wins"],
            "test_profit": test_stats["profit"],
            "test_roi": test_stats["roi"],
            "positive_test_seasons": positive,
        })
    return pd.DataFrame(summaries), pd.DataFrame(season_rows)


def write_reports(frame: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary, by_season = frozen_validation(frame)
    paths = {"summary": output_dir / "frozen_rule_summary.csv", "season": output_dir / "frozen_rule_by_season.csv"}
    summary.to_csv(paths["summary"], index=False)
    by_season.to_csv(paths["season"], index=False)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Frozen historical market strategy validation")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/historical_strategy_frozen"))
    args = parser.parse_args()
    paths = write_reports(pd.read_csv(args.input), args.output_dir)
    print("HISTORICAL STRATEGY FROZEN-RULE VALIDATION — RESEARCH ONLY")
    print(pd.read_csv(paths["summary"]).to_string(index=False))
    print("Rule selection uses only the initial training seasons and never changes afterward.")


if __name__ == "__main__":
    main()
