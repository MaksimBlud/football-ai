"""Price robustness on fixtures selected only by the frozen Bet365 rule.

The fixture set is determined exclusively from Bet365 standard no-vig probabilities and
the frozen market-pick/confidence rule. Alternative bookmaker/timing columns are then
used only as prices for those same selected fixtures; they never change membership.
Research only; no production side effects.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SIDES = ("H", "D", "A")
BET365_STANDARD = ("B365H", "B365D", "B365A")
PRICE_SOURCES = {
    "BET365_STANDARD": BET365_STANDARD,
    "BET365_CLOSING": ("B365CH", "B365CD", "B365CA"),
    "PINNACLE_STANDARD": ("PSH", "PSD", "PSA"),
    "PINNACLE_CLOSING": ("PSCH", "PSCD", "PSCA"),
}
BOUNDS = {
    "<40%": (0.0, 0.40),
    "40–50%": (0.40, 0.50),
    "50–60%": (0.50, 0.60),
    "60–70%": (0.60, 0.70),
    "≥70%": (0.70, 1.0000001),
}


def bet365_selection_mask(frame: pd.DataFrame, *, pick: str, bucket: str) -> pd.Series:
    if pick not in SIDES:
        raise ValueError(f"Unsupported pick: {pick}")
    if bucket not in BOUNDS:
        raise ValueError(f"Unsupported confidence bucket: {bucket}")
    required = {"FTR", *BET365_STANDARD}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Missing Bet365 selection columns: " + ", ".join(sorted(missing)))
    odds = frame[list(BET365_STANDARD)].apply(pd.to_numeric, errors="coerce")
    valid = odds.gt(1.0).all(axis=1) & frame["FTR"].astype(str).isin(SIDES)
    probs = (1.0 / odds.loc[valid])
    probs = probs.div(probs.sum(axis=1), axis=0)
    selected_pick = pd.Series([SIDES[i] for i in probs.to_numpy().argmax(axis=1)], index=probs.index)
    confidence = pd.Series(probs.to_numpy().max(axis=1), index=probs.index)
    low, high = BOUNDS[bucket]
    chosen = selected_pick.eq(pick) & confidence.ge(low) & confidence.lt(high)
    mask = pd.Series(False, index=frame.index)
    mask.loc[chosen.index] = chosen
    return mask


def evaluate_price_source(frame: pd.DataFrame, selected_mask: pd.Series, *, pick: str, columns: tuple[str, str, str]) -> dict:
    selected_count = int(selected_mask.sum())
    if not all(column in frame.columns for column in columns):
        return {
            "selected_fixtures": selected_count,
            "priced_fixtures": 0,
            "price_coverage": 0.0 if selected_count else None,
            "wins": 0,
            "average_odds": None,
            "profit": 0.0,
            "roi": None,
        }
    odds = frame[list(columns)].apply(pd.to_numeric, errors="coerce")
    provider_valid = odds.gt(1.0).all(axis=1)
    priced_mask = selected_mask & provider_valid
    prices = odds.loc[priced_mask].iloc[:, SIDES.index(pick)]
    actual = frame.loc[priced_mask, "FTR"].astype(str)
    n = len(prices)
    if not n:
        return {
            "selected_fixtures": selected_count,
            "priced_fixtures": 0,
            "price_coverage": 0.0 if selected_count else None,
            "wins": 0,
            "average_odds": None,
            "profit": 0.0,
            "roi": None,
        }
    won = actual.eq(pick)
    profit = pd.Series(-1.0, index=prices.index)
    profit.loc[won] = prices.loc[won] - 1.0
    total = float(profit.sum())
    return {
        "selected_fixtures": selected_count,
        "priced_fixtures": n,
        "price_coverage": n / selected_count if selected_count else None,
        "wins": int(won.sum()),
        "accuracy": float(won.mean()),
        "average_odds": float(prices.mean()),
        "profit": total,
        "roi": total / n,
    }


def validate(raw_root: Path, frozen_summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    season_rows: list[dict] = []
    for rule in frozen_summary.itertuples(index=False):
        league = str(rule.league)
        pick = str(rule.market_pick)
        bucket = str(rule.confidence_bucket)
        first_test = str(rule.first_test_season)
        for path in sorted((raw_root / league.lower()).glob("*.csv")):
            years = path.stem.rsplit("_", 2)[-2:]
            season = f"{years[0]}-{years[1]}"
            if season < first_test:
                continue
            frame = pd.read_csv(path)
            selected_mask = bet365_selection_mask(frame, pick=pick, bucket=bucket)
            for source, columns in PRICE_SOURCES.items():
                season_rows.append({
                    "league": league,
                    "season": season,
                    "market_pick": pick,
                    "confidence_bucket": bucket,
                    "selection_source": "BET365_STANDARD",
                    "price_source": source,
                    **evaluate_price_source(frame, selected_mask, pick=pick, columns=columns),
                })

    by_season = pd.DataFrame(season_rows)
    summaries: list[dict] = []
    if by_season.empty:
        return pd.DataFrame(), by_season
    for keys, group in by_season.groupby(
        ["league", "market_pick", "confidence_bucket", "selection_source", "price_source"],
        sort=True,
    ):
        league, pick, bucket, selection_source, price_source = keys
        selected_fixtures = int(group["selected_fixtures"].sum())
        priced_fixtures = int(group["priced_fixtures"].sum())
        profit = float(group["profit"].sum())
        summaries.append({
            "league": league,
            "market_pick": pick,
            "confidence_bucket": bucket,
            "selection_source": selection_source,
            "price_source": price_source,
            "seasons": len(group),
            "selected_fixtures": selected_fixtures,
            "priced_fixtures": priced_fixtures,
            "price_coverage": priced_fixtures / selected_fixtures if selected_fixtures else None,
            "wins": int(group["wins"].sum()),
            "profit": profit,
            "roi": profit / priced_fixtures if priced_fixtures else None,
            "positive_seasons": int((group["roi"] > 0).sum()),
        })
    return pd.DataFrame(summaries), by_season


def main() -> None:
    parser = argparse.ArgumentParser(description="Fixed-fixture cross-bookmaker price validation")
    parser.add_argument("raw_root", type=Path)
    parser.add_argument("frozen_summary", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/historical_strategy_fixed_fixture"))
    args = parser.parse_args()
    summary, by_season = validate(args.raw_root, pd.read_csv(args.frozen_summary))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "fixed_fixture_price_summary.csv", index=False)
    by_season.to_csv(args.output_dir / "fixed_fixture_price_by_season.csv", index=False)
    print("FIXED-FIXTURE PRICE ROBUSTNESS — RESEARCH ONLY")
    print(summary.to_string(index=False))
    print("Fixture membership is determined only by BET365_STANDARD frozen-rule semantics.")


if __name__ == "__main__":
    main()
