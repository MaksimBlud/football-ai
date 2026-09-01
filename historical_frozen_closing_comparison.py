"""Compare frozen historical rules at standard and explicit closing Bet365 prices.

The rule itself is read from frozen_rule_summary.csv and is never re-selected using
closing data. Standard columns are not called opening prices because their exact timing
is not asserted here. Research only; no production side effects.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

B365_STANDARD = ("B365H", "B365D", "B365A")
B365_CLOSING = ("B365CH", "B365CD", "B365CA")
SIDES = ("H", "D", "A")


def _probabilities(frame: pd.DataFrame, columns: tuple[str, str, str]) -> pd.DataFrame:
    odds = frame[list(columns)].apply(pd.to_numeric, errors="coerce")
    implied = 1.0 / odds
    return implied.div(implied.sum(axis=1), axis=0)


def compare_rule(frame: pd.DataFrame, *, pick: str, confidence_bucket: str) -> dict:
    if confidence_bucket != "60–70%" and confidence_bucket not in {"<40%", "40–50%", "50–60%", "≥70%"}:
        raise ValueError(f"Unsupported confidence bucket: {confidence_bucket}")
    required = {"FTR", *B365_STANDARD, *B365_CLOSING}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

    standard = frame[list(B365_STANDARD)].apply(pd.to_numeric, errors="coerce")
    closing = frame[list(B365_CLOSING)].apply(pd.to_numeric, errors="coerce")
    valid = standard.gt(1.0).all(axis=1) & closing.gt(1.0).all(axis=1)
    work = frame.loc[valid].copy()
    standard = standard.loc[valid]
    closing = closing.loc[valid]
    probs = _probabilities(work, B365_STANDARD)
    argmax = probs.to_numpy().argmax(axis=1)
    market_pick = pd.Series([SIDES[index] for index in argmax], index=work.index)
    confidence = pd.Series(probs.to_numpy().max(axis=1), index=work.index)

    bounds = {
        "<40%": (0.0, 0.40),
        "40–50%": (0.40, 0.50),
        "50–60%": (0.50, 0.60),
        "60–70%": (0.60, 0.70),
        "≥70%": (0.70, 1.0000001),
    }
    low, high = bounds[confidence_bucket]
    selected_mask = (market_pick == pick) & confidence.ge(low) & confidence.lt(high)
    selected = work.loc[selected_mask].copy()
    if selected.empty:
        return {"matches": 0, "wins": 0, "standard_profit": 0.0, "closing_profit": 0.0}

    side_index = SIDES.index(pick)
    standard_odds = standard.loc[selected.index].iloc[:, side_index]
    closing_odds = closing.loc[selected.index].iloc[:, side_index]
    won = selected["FTR"].astype(str).eq(pick)
    standard_profit = pd.Series(-1.0, index=selected.index)
    closing_profit = pd.Series(-1.0, index=selected.index)
    standard_profit.loc[won] = standard_odds.loc[won] - 1.0
    closing_profit.loc[won] = closing_odds.loc[won] - 1.0

    n = len(selected)
    return {
        "matches": n,
        "wins": int(won.sum()),
        "accuracy": float(won.mean()),
        "mean_standard_odds": float(standard_odds.mean()),
        "mean_closing_odds": float(closing_odds.mean()),
        "mean_close_minus_standard_odds": float((closing_odds - standard_odds).mean()),
        "share_price_shortened": float((closing_odds < standard_odds).mean()),
        "standard_profit": float(standard_profit.sum()),
        "standard_roi": float(standard_profit.sum()) / n,
        "closing_profit": float(closing_profit.sum()),
        "closing_roi": float(closing_profit.sum()) / n,
    }


def compare_from_raw(raw_root: Path, frozen_summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    season_rows = []
    summary_rows = []
    for rule in frozen_summary.itertuples(index=False):
        league = str(rule.league)
        league_dir = raw_root / league.lower()
        first_test = str(rule.first_test_season)
        files = sorted(league_dir.glob("*.csv"))
        for path in files:
            years = path.stem.rsplit("_", 2)[-2:]
            season = f"{years[0]}-{years[1]}"
            if season < first_test:
                continue
            frame = pd.read_csv(path)
            if not all(column in frame.columns for column in B365_CLOSING):
                continue
            metrics = compare_rule(frame, pick=str(rule.market_pick), confidence_bucket=str(rule.confidence_bucket))
            season_rows.append({"league": league, "season": season, "market_pick": rule.market_pick, "confidence_bucket": rule.confidence_bucket, **metrics})

        league_rows = [row for row in season_rows if row["league"] == league]
        matches = sum(int(row["matches"]) for row in league_rows)
        if not matches:
            continue
        standard_profit = sum(float(row["standard_profit"]) for row in league_rows)
        closing_profit = sum(float(row["closing_profit"]) for row in league_rows)
        weighted_standard_odds = sum(float(row["mean_standard_odds"]) * int(row["matches"]) for row in league_rows) / matches
        weighted_closing_odds = sum(float(row["mean_closing_odds"]) * int(row["matches"]) for row in league_rows) / matches
        shortened = sum(float(row["share_price_shortened"]) * int(row["matches"]) for row in league_rows) / matches
        summary_rows.append({
            "league": league,
            "market_pick": rule.market_pick,
            "confidence_bucket": rule.confidence_bucket,
            "test_seasons_with_closing": len(league_rows),
            "matches": matches,
            "wins": sum(int(row["wins"]) for row in league_rows),
            "mean_standard_odds": weighted_standard_odds,
            "mean_closing_odds": weighted_closing_odds,
            "mean_close_minus_standard_odds": weighted_closing_odds - weighted_standard_odds,
            "share_price_shortened": shortened,
            "standard_profit": standard_profit,
            "standard_roi": standard_profit / matches,
            "closing_profit": closing_profit,
            "closing_roi": closing_profit / matches,
        })
    return pd.DataFrame(summary_rows), pd.DataFrame(season_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare frozen rules at standard versus explicit closing Bet365 prices")
    parser.add_argument("raw_root", type=Path)
    parser.add_argument("frozen_summary", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/historical_strategy_closing"))
    args = parser.parse_args()
    summary, by_season = compare_from_raw(args.raw_root, pd.read_csv(args.frozen_summary))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "frozen_closing_summary.csv", index=False)
    by_season.to_csv(args.output_dir / "frozen_closing_by_season.csv", index=False)
    print("FROZEN RULE STANDARD→CLOSING COMPARISON — RESEARCH ONLY")
    print(summary.to_string(index=False))
    print("Closing data never participates in rule selection.")


if __name__ == "__main__":
    main()
