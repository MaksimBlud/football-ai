"""Expanding-window walk-forward validation for Historical Strategy Lab.

Research only. For each league and test season, candidate market segments are ranked
using only earlier seasons. The selected segment is then evaluated on the next unseen
season. This is exploratory validation and remains separate from canonical forward OOS.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from historical_strategy_stability import add_confidence_bucket

MIN_TRAINING_SEASONS = 3
MIN_TRAINING_MATCHES = 100


def _metrics(group: pd.DataFrame) -> dict[str, float | int]:
    n = len(group)
    profit = float(group["profit"].sum())
    return {
        "matches": n,
        "wins": int(group["won"].sum()),
        "accuracy": float(group["won"].mean()) if n else float("nan"),
        "average_odds": float(group["selected_odds"].mean()) if n else float("nan"),
        "profit": profit,
        "roi": profit / n if n else float("nan"),
    }


def walk_forward(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    prepared = add_confidence_bucket(frame)
    selections = []
    bets = []

    for league, league_frame in prepared.groupby("league", sort=True):
        seasons = sorted(league_frame["season"].dropna().astype(str).unique())
        for test_index in range(MIN_TRAINING_SEASONS, len(seasons)):
            test_season = seasons[test_index]
            training_seasons = seasons[:test_index]
            training = league_frame[league_frame["season"].astype(str).isin(training_seasons)]
            candidates = []

            for (pick, bucket), group in training.groupby(
                ["market_pick", "confidence_bucket"], observed=True, sort=True
            ):
                season_count = group["season"].astype(str).nunique()
                if season_count < MIN_TRAINING_SEASONS or len(group) < MIN_TRAINING_MATCHES:
                    continue
                metrics = _metrics(group)
                season_roi = (
                    group.groupby(group["season"].astype(str), sort=True)["profit"].agg(["sum", "size"])
                )
                season_roi["roi"] = season_roi["sum"] / season_roi["size"]
                candidates.append({
                    "market_pick": pick,
                    "confidence_bucket": str(bucket),
                    "training_seasons": season_count,
                    "training_matches": metrics["matches"],
                    "training_profit": metrics["profit"],
                    "training_roi": metrics["roi"],
                    "training_positive_season_share": float((season_roi["roi"] > 0).mean()),
                })

            if not candidates:
                continue

            ranking = pd.DataFrame(candidates).sort_values(
                ["training_roi", "training_positive_season_share", "training_matches", "market_pick", "confidence_bucket"],
                ascending=[False, False, False, True, True],
                kind="stable",
            )
            chosen = ranking.iloc[0].to_dict()
            test = league_frame[
                (league_frame["season"].astype(str) == test_season)
                & (league_frame["market_pick"] == chosen["market_pick"])
                & (league_frame["confidence_bucket"].astype(str) == chosen["confidence_bucket"])
            ].copy()
            test_metrics = _metrics(test)

            selection = {
                "league": league,
                "test_season": test_season,
                **chosen,
                **{f"test_{key}": value for key, value in test_metrics.items()},
            }
            selections.append(selection)

            if not test.empty:
                test = test.copy()
                test["walk_forward_league"] = league
                test["walk_forward_test_season"] = test_season
                test["selected_market_pick"] = chosen["market_pick"]
                test["selected_confidence_bucket"] = chosen["confidence_bucket"]
                bets.append(test)

    selection_frame = pd.DataFrame(selections)
    bet_frame = pd.concat(bets, ignore_index=True) if bets else pd.DataFrame()
    return selection_frame, bet_frame


def summary_table(selections: pd.DataFrame) -> pd.DataFrame:
    if selections.empty:
        return pd.DataFrame(columns=["league", "test_seasons", "matches", "wins", "profit", "roi", "positive_test_seasons"])
    rows = []
    for league, group in selections.groupby("league", sort=True):
        matches = int(group["test_matches"].sum())
        profit = float(group["test_profit"].sum())
        rows.append({
            "league": league,
            "test_seasons": len(group),
            "matches": matches,
            "wins": int(group["test_wins"].sum()),
            "profit": profit,
            "roi": profit / matches if matches else float("nan"),
            "positive_test_seasons": int((group["test_roi"] > 0).sum()),
        })
    total_matches = int(selections["test_matches"].sum())
    total_profit = float(selections["test_profit"].sum())
    rows.append({
        "league": "ALL",
        "test_seasons": len(selections),
        "matches": total_matches,
        "wins": int(selections["test_wins"].sum()),
        "profit": total_profit,
        "roi": total_profit / total_matches if total_matches else float("nan"),
        "positive_test_seasons": int((selections["test_roi"] > 0).sum()),
    })
    return pd.DataFrame(rows)


def write_reports(frame: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selections, bets = walk_forward(frame)
    summary = summary_table(selections)
    paths = {
        "summary": output_dir / "walk_forward_summary.csv",
        "selections": output_dir / "walk_forward_selections.csv",
        "bets": output_dir / "walk_forward_bets.csv",
    }
    summary.to_csv(paths["summary"], index=False)
    selections.to_csv(paths["selections"], index=False)
    bets.to_csv(paths["bets"], index=False)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Expanding-window historical strategy validation")
    parser.add_argument("input", type=Path, help="prepared_matches.csv from Historical Strategy Lab")
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/historical_strategy_walk_forward"))
    args = parser.parse_args()
    paths = write_reports(pd.read_csv(args.input), args.output_dir)
    print("HISTORICAL STRATEGY WALK-FORWARD — RESEARCH ONLY")
    print(pd.read_csv(paths["summary"]).to_string(index=False))
    print("Selection uses only seasons earlier than each test season.")
    print("No training, Supabase writes, live activation, or .pkl changes performed.")


if __name__ == "__main__":
    main()
