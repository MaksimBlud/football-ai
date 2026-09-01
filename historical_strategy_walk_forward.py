"""Selection-free expanding-window diagnostics for Historical Strategy Lab.

Research only. Every candidate segment in the predeclared universe is evaluated in every
eligible test season. Training statistics use only earlier seasons; the test season is
never used to choose, filter, or tune a segment. This keeps historical discovery separate
from canonical forward OOS and avoids turning a post-hoc best bucket into a strategy.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from historical_strategy_stability import (
    CONFIDENCE_LABELS,
    add_confidence_bucket,
)

SIDES = ("H", "D", "A")
MIN_PRIOR_SEASONS = 3


def _metrics(group: pd.DataFrame) -> dict[str, float | int]:
    n = len(group)
    profit = float(group["profit"].sum()) if n else 0.0
    return {
        "matches": n,
        "wins": int(group["won"].sum()) if n else 0,
        "accuracy": float(group["won"].mean()) if n else float("nan"),
        "average_odds": float(group["selected_odds"].mean()) if n else float("nan"),
        "profit": profit,
        "roi": profit / n if n else float("nan"),
    }


def _positive_season_share(group: pd.DataFrame) -> float:
    if group.empty:
        return float("nan")
    season = group.groupby(group["season"].astype(str), sort=True)["profit"].agg(["sum", "size"])
    return float(((season["sum"] / season["size"]) > 0).mean())


def walk_forward(frame: pd.DataFrame) -> pd.DataFrame:
    """Evaluate every fixed market segment on unseen seasons.

    No candidate is selected. Each output row is one league × candidate × test-season
    evaluation. Training fields are computed strictly from seasons before test_season.
    """
    prepared = add_confidence_bucket(frame)
    rows: list[dict[str, object]] = []

    for league, league_frame in prepared.groupby("league", sort=True):
        league_frame = league_frame.copy()
        league_frame["season"] = league_frame["season"].astype(str)
        seasons = sorted(league_frame["season"].dropna().unique())

        for test_index in range(MIN_PRIOR_SEASONS, len(seasons)):
            test_season = seasons[test_index]
            prior_seasons = seasons[:test_index]
            training_all = league_frame[league_frame["season"].isin(prior_seasons)]
            test_all = league_frame[league_frame["season"] == test_season]

            for pick in SIDES:
                for bucket in CONFIDENCE_LABELS:
                    training = training_all[
                        (training_all["market_pick"] == pick)
                        & (training_all["confidence_bucket"].astype(str) == bucket)
                    ]
                    test = test_all[
                        (test_all["market_pick"] == pick)
                        & (test_all["confidence_bucket"].astype(str) == bucket)
                    ]
                    train_metrics = _metrics(training)
                    test_metrics = _metrics(test)
                    rows.append({
                        "league": league,
                        "market_pick": pick,
                        "confidence_bucket": bucket,
                        "test_season": test_season,
                        "prior_seasons": len(prior_seasons),
                        "training_matches": train_metrics["matches"],
                        "training_wins": train_metrics["wins"],
                        "training_accuracy": train_metrics["accuracy"],
                        "training_average_odds": train_metrics["average_odds"],
                        "training_profit": train_metrics["profit"],
                        "training_roi": train_metrics["roi"],
                        "training_positive_season_share": _positive_season_share(training),
                        "test_matches": test_metrics["matches"],
                        "test_wins": test_metrics["wins"],
                        "test_accuracy": test_metrics["accuracy"],
                        "test_average_odds": test_metrics["average_odds"],
                        "test_profit": test_metrics["profit"],
                        "test_roi": test_metrics["roi"],
                    })

    return pd.DataFrame(rows)


def summary_table(evaluations: pd.DataFrame) -> pd.DataFrame:
    """Aggregate unseen-season results per fixed candidate without selection."""
    columns = [
        "league", "market_pick", "confidence_bucket", "test_seasons",
        "seasons_with_bets", "matches", "wins", "accuracy", "profit", "roi",
        "positive_test_seasons", "positive_test_season_share",
    ]
    if evaluations.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for keys, group in evaluations.groupby(
        ["league", "market_pick", "confidence_bucket"], sort=True
    ):
        league, pick, bucket = keys
        active = group[group["test_matches"] > 0].copy()
        matches = int(active["test_matches"].sum()) if not active.empty else 0
        wins = int(active["test_wins"].sum()) if not active.empty else 0
        profit = float(active["test_profit"].sum()) if not active.empty else 0.0
        positive = int((active["test_roi"] > 0).sum()) if not active.empty else 0
        active_seasons = len(active)
        rows.append({
            "league": league,
            "market_pick": pick,
            "confidence_bucket": bucket,
            "test_seasons": len(group),
            "seasons_with_bets": active_seasons,
            "matches": matches,
            "wins": wins,
            "accuracy": wins / matches if matches else float("nan"),
            "profit": profit,
            "roi": profit / matches if matches else float("nan"),
            "positive_test_seasons": positive,
            "positive_test_season_share": positive / active_seasons if active_seasons else float("nan"),
        })
    return pd.DataFrame(rows).sort_values(
        ["league", "market_pick", "confidence_bucket"], kind="stable"
    ).reset_index(drop=True)


def write_reports(frame: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluations = walk_forward(frame)
    summary = summary_table(evaluations)
    paths = {
        "summary": output_dir / "walk_forward_summary.csv",
        "evaluations": output_dir / "walk_forward_evaluations.csv",
    }
    summary.to_csv(paths["summary"], index=False)
    evaluations.to_csv(paths["evaluations"], index=False)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Selection-free expanding-window historical strategy diagnostics"
    )
    parser.add_argument("input", type=Path, help="prepared_matches.csv from Historical Strategy Lab")
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("experiments/historical_strategy_walk_forward")
    )
    args = parser.parse_args()
    paths = write_reports(pd.read_csv(args.input), args.output_dir)
    print("HISTORICAL STRATEGY WALK-FORWARD — RESEARCH ONLY")
    print(pd.read_csv(paths["summary"]).to_string(index=False))
    print("Every fixed candidate is evaluated; no best segment is selected.")
    print("Training fields use only seasons earlier than each test season.")
    print("No training, Supabase writes, live activation, or .pkl changes performed.")


if __name__ == "__main__":
    main()
