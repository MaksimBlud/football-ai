"""Stability diagnostics for Historical Strategy Lab outputs.

Research only. Uses already prepared historical bookmaker rows and produces descriptive
league/pick/confidence stability tables. It does not train models, write Supabase,
activate live logic, or modify production artifacts.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

CONFIDENCE_BINS = [0.0, 0.40, 0.50, 0.60, 0.70, 1.0000001]
CONFIDENCE_LABELS = ["<40%", "40–50%", "50–60%", "60–70%", "≥70%"]


def add_confidence_bucket(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    required = {"league", "season", "market_pick", "market_confidence", "selected_odds", "won", "profit"}
    missing = required - set(result.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
    result["confidence_bucket"] = pd.cut(
        pd.to_numeric(result["market_confidence"], errors="coerce"),
        bins=CONFIDENCE_BINS,
        labels=CONFIDENCE_LABELS,
        right=False,
    )
    return result.dropna(subset=["confidence_bucket"]).copy()


def _metrics(group: pd.DataFrame) -> dict[str, float | int]:
    matches = len(group)
    profit = float(group["profit"].sum())
    return {
        "matches": matches,
        "wins": int(group["won"].sum()),
        "accuracy": float(group["won"].mean()) if matches else float("nan"),
        "average_odds": float(group["selected_odds"].mean()) if matches else float("nan"),
        "profit": profit,
        "roi": profit / matches if matches else float("nan"),
    }


def segment_stability(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    prepared = add_confidence_bucket(frame)
    season_rows = []
    for keys, group in prepared.groupby(
        ["league", "market_pick", "confidence_bucket", "season"], observed=True, sort=True
    ):
        league, pick, bucket, season = keys
        season_rows.append({
            "league": league,
            "market_pick": pick,
            "confidence_bucket": str(bucket),
            "season": season,
            **_metrics(group),
        })
    by_season = pd.DataFrame(season_rows)

    rows = []
    for keys, group in prepared.groupby(
        ["league", "market_pick", "confidence_bucket"], observed=True, sort=True
    ):
        league, pick, bucket = keys
        metrics = _metrics(group)
        season_slice = by_season[
            (by_season["league"] == league)
            & (by_season["market_pick"] == pick)
            & (by_season["confidence_bucket"] == str(bucket))
        ].sort_values("season")
        recent = season_slice.tail(5)
        recent_matches = int(recent["matches"].sum())
        recent_profit = float(recent["profit"].sum())
        rows.append({
            "league": league,
            "market_pick": pick,
            "confidence_bucket": str(bucket),
            **metrics,
            "seasons": len(season_slice),
            "positive_seasons": int((season_slice["roi"] > 0).sum()),
            "positive_season_share": float((season_slice["roi"] > 0).mean()),
            "recent_5_season_matches": recent_matches,
            "recent_5_season_profit": recent_profit,
            "recent_5_season_roi": recent_profit / recent_matches if recent_matches else float("nan"),
        })
    summary = pd.DataFrame(rows).sort_values(
        ["roi", "matches"], ascending=[False, False], kind="stable"
    ).reset_index(drop=True)
    return summary, by_season


def write_reports(frame: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary, by_season = segment_stability(frame)
    paths = {
        "summary": output_dir / "segment_stability.csv",
        "season": output_dir / "segment_stability_by_season.csv",
    }
    summary.to_csv(paths["summary"], index=False)
    by_season.to_csv(paths["season"], index=False)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Historical market segment stability diagnostics")
    parser.add_argument("input", type=Path, help="prepared_matches.csv from Historical Strategy Lab")
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/historical_strategy_stability"))
    args = parser.parse_args()
    paths = write_reports(pd.read_csv(args.input), args.output_dir)
    print("HISTORICAL STRATEGY STABILITY — RESEARCH ONLY")
    print(pd.read_csv(paths["summary"]).to_string(index=False))
    print("No training, Supabase writes, live activation, or .pkl changes performed.")


if __name__ == "__main__":
    main()
