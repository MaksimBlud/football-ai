"""Historical Strategy Lab for bookmaker 1X2 research.

Research only. No training, no Supabase writes, no live activation, no artifact promotion.

The lab evaluates already historical, pre-match bookmaker prices. It deliberately keeps
historical discovery separate from the forward canonical OOS sample.
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

SIDES = ("H", "D", "A")
ODDS_COLUMNS = {
    "H": "market_home_odds",
    "D": "market_draw_odds",
    "A": "market_away_odds",
}
PROB_COLUMNS = {
    "H": "market_home_probability",
    "D": "market_draw_probability",
    "A": "market_away_probability",
}
CONFIDENCE_BUCKETS = (
    (0.0, 0.40, "<40%"),
    (0.40, 0.50, "40–50%"),
    (0.50, 0.60, "50–60%"),
    (0.60, 0.70, "60–70%"),
    (0.70, 1.0000001, "≥70%"),
)
ODDS_BUCKETS = (
    (1.0, 1.50, "1.00–1.49"),
    (1.50, 1.80, "1.50–1.79"),
    (1.80, 2.20, "1.80–2.19"),
    (2.20, 3.00, "2.20–2.99"),
    (3.00, float("inf"), "≥3.00"),
)


@dataclass(frozen=True)
class StrategyMetrics:
    matches: int
    wins: int
    accuracy: float | None
    average_odds: float | None
    profit: float
    roi: float | None
    brier: float | None
    log_loss: float | None
    max_drawdown: float


def no_vig_probabilities(home_odds: float, draw_odds: float, away_odds: float) -> dict[str, float]:
    odds = {"H": float(home_odds), "D": float(draw_odds), "A": float(away_odds)}
    if any((not math.isfinite(value)) or value <= 1.0 for value in odds.values()):
        raise ValueError("All 1X2 odds must be finite and greater than 1.0")
    implied = {side: 1.0 / value for side, value in odds.items()}
    total = sum(implied.values())
    return {side: implied[side] / total for side in SIDES}


def prepare_market_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"league", "season", "result", *ODDS_COLUMNS.values()}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

    result = frame.copy()
    result = result[result["result"].isin(SIDES)].copy()
    for column in ODDS_COLUMNS.values():
        result[column] = pd.to_numeric(result[column], errors="coerce")

    valid = pd.Series(True, index=result.index)
    for column in ODDS_COLUMNS.values():
        valid &= result[column].gt(1.0) & result[column].map(math.isfinite)
    result = result.loc[valid].copy()

    probabilities = result.apply(
        lambda row: no_vig_probabilities(
            row[ODDS_COLUMNS["H"]], row[ODDS_COLUMNS["D"]], row[ODDS_COLUMNS["A"]]
        ),
        axis=1,
    )
    for side in SIDES:
        result[PROB_COLUMNS[side]] = probabilities.map(lambda values: values[side])

    result["market_pick"] = result[[PROB_COLUMNS[s] for s in SIDES]].idxmax(axis=1).map(
        {PROB_COLUMNS["H"]: "H", PROB_COLUMNS["D"]: "D", PROB_COLUMNS["A"]: "A"}
    )
    result["market_confidence"] = result.apply(
        lambda row: row[PROB_COLUMNS[row["market_pick"]]], axis=1
    )
    result["selected_odds"] = result.apply(
        lambda row: row[ODDS_COLUMNS[row["market_pick"]]], axis=1
    )
    result["won"] = result["market_pick"] == result["result"]
    result["profit"] = result.apply(
        lambda row: row["selected_odds"] - 1.0 if row["won"] else -1.0, axis=1
    )
    result["equity"] = result["profit"].cumsum()
    running_peak = result["equity"].cummax().clip(lower=0.0)
    result["drawdown"] = result["equity"] - running_peak
    return result.reset_index(drop=True)


def evaluate(frame: pd.DataFrame) -> StrategyMetrics:
    prepared = prepare_market_frame(frame)
    n = len(prepared)
    if not n:
        return StrategyMetrics(0, 0, None, None, 0.0, None, None, None, 0.0)

    wins = int(prepared["won"].sum())
    brier_total = 0.0
    log_loss_total = 0.0
    for row in prepared.itertuples(index=False):
        actual = row.result
        probabilities = {
            "H": row.market_home_probability,
            "D": row.market_draw_probability,
            "A": row.market_away_probability,
        }
        for side in SIDES:
            brier_total += (probabilities[side] - (1.0 if side == actual else 0.0)) ** 2
        log_loss_total += -math.log(max(probabilities[actual], 1e-15))

    profit = float(prepared["profit"].sum())
    return StrategyMetrics(
        matches=n,
        wins=wins,
        accuracy=wins / n,
        average_odds=float(prepared["selected_odds"].mean()),
        profit=profit,
        roi=profit / n,
        brier=brier_total / n,
        log_loss=log_loss_total / n,
        max_drawdown=abs(float(prepared["drawdown"].min())),
    )


def segment_table(frame: pd.DataFrame, buckets: Iterable[tuple[float, float, str]], column: str) -> pd.DataFrame:
    prepared = prepare_market_frame(frame)
    rows = []
    for low, high, label in buckets:
        subset = prepared[(prepared[column] >= low) & (prepared[column] < high)]
        metrics = evaluate(subset) if len(subset) else StrategyMetrics(0, 0, None, None, 0.0, None, None, None, 0.0)
        rows.append({
            "segment": label,
            "matches": metrics.matches,
            "wins": metrics.wins,
            "accuracy": metrics.accuracy,
            "average_odds": metrics.average_odds,
            "profit": metrics.profit,
            "roi": metrics.roi,
            "brier": metrics.brier,
            "log_loss": metrics.log_loss,
            "max_drawdown": metrics.max_drawdown,
        })
    return pd.DataFrame(rows)


def by_league_and_season(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = prepare_market_frame(frame)
    rows = []
    for (league, season), group in prepared.groupby(["league", "season"], sort=True):
        metrics = evaluate(group)
        rows.append({"league": league, "season": season, **metrics.__dict__})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only historical MARKET_ONLY strategy diagnostics")
    parser.add_argument("inputs", nargs="+", type=Path, help="Normalized historical market CSV files")
    parser.add_argument("--output-dir", type=Path, default=Path("experiments/historical_strategy_lab"))
    args = parser.parse_args()

    frames = [pd.read_csv(path) for path in args.inputs]
    combined = pd.concat(frames, ignore_index=True)
    prepared = prepare_market_frame(combined)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    overall = pd.DataFrame([evaluate(prepared).__dict__])
    confidence = segment_table(prepared, CONFIDENCE_BUCKETS, "market_confidence")
    odds = segment_table(prepared, ODDS_BUCKETS, "selected_odds")
    league_season = by_league_and_season(prepared)

    overall.to_csv(args.output_dir / "overall.csv", index=False)
    confidence.to_csv(args.output_dir / "confidence_buckets.csv", index=False)
    odds.to_csv(args.output_dir / "odds_buckets.csv", index=False)
    league_season.to_csv(args.output_dir / "league_season.csv", index=False)

    print("HISTORICAL STRATEGY LAB — RESEARCH ONLY")
    print(overall.to_string(index=False))
    print("Outputs:", args.output_dir)
    print("No training, Supabase writes, live activation, or .pkl changes performed.")


if __name__ == "__main__":
    main()
