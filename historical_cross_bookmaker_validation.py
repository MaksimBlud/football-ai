"""Cross-bookmaker validation of already frozen historical market rules.

Rules are selected elsewhere from Bet365 standard prices. This module applies the exact
same market-pick and confidence-bucket semantics to other providers without re-tuning.
Research only; no production side effects.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SIDES = ("H", "D", "A")
PROVIDERS = {
    "BET365": (("B365H", "B365D", "B365A"), ("B365CH", "B365CD", "B365CA")),
    "PINNACLE": (("PSH", "PSD", "PSA"), ("PSCH", "PSCD", "PSCA")),
}
BOUNDS = {
    "<40%": (0.0, 0.40), "40–50%": (0.40, 0.50), "50–60%": (0.50, 0.60),
    "60–70%": (0.60, 0.70), "≥70%": (0.70, 1.0000001),
}


def _evaluate(frame: pd.DataFrame, columns: tuple[str, str, str], *, pick: str, bucket: str) -> dict:
    if bucket not in BOUNDS:
        raise ValueError(f"Unsupported confidence bucket: {bucket}")
    if not all(c in frame.columns for c in columns):
        return {"matches": 0, "wins": 0, "profit": 0.0, "roi": None, "average_odds": None}
    odds = frame[list(columns)].apply(pd.to_numeric, errors="coerce")
    valid = odds.gt(1.0).all(axis=1) & frame["FTR"].astype(str).isin(SIDES)
    odds = odds.loc[valid]
    actual = frame.loc[valid, "FTR"].astype(str)
    implied = 1.0 / odds
    probs = implied.div(implied.sum(axis=1), axis=0)
    chosen = pd.Series([SIDES[i] for i in probs.to_numpy().argmax(axis=1)], index=probs.index)
    confidence = pd.Series(probs.to_numpy().max(axis=1), index=probs.index)
    low, high = BOUNDS[bucket]
    mask = chosen.eq(pick) & confidence.ge(low) & confidence.lt(high)
    selected_odds = odds.loc[mask].iloc[:, SIDES.index(pick)]
    selected_actual = actual.loc[mask]
    n = len(selected_odds)
    if not n:
        return {"matches": 0, "wins": 0, "profit": 0.0, "roi": None, "average_odds": None}
    won = selected_actual.eq(pick)
    profit = pd.Series(-1.0, index=selected_odds.index)
    profit.loc[won] = selected_odds.loc[won] - 1.0
    total = float(profit.sum())
    return {
        "matches": n, "wins": int(won.sum()), "accuracy": float(won.mean()),
        "average_odds": float(selected_odds.mean()), "profit": total, "roi": total / n,
    }


def validate(raw_root: Path, frozen_summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    season_rows = []
    for rule in frozen_summary.itertuples(index=False):
        league = str(rule.league)
        first_test = str(rule.first_test_season)
        for path in sorted((raw_root / league.lower()).glob("*.csv")):
            years = path.stem.rsplit("_", 2)[-2:]
            season = f"{years[0]}-{years[1]}"
            if season < first_test:
                continue
            frame = pd.read_csv(path)
            for provider, (standard, closing) in PROVIDERS.items():
                for timing, columns in (("standard", standard), ("closing", closing)):
                    metrics = _evaluate(frame, columns, pick=str(rule.market_pick), bucket=str(rule.confidence_bucket))
                    season_rows.append({
                        "league": league, "season": season, "provider": provider, "timing": timing,
                        "market_pick": rule.market_pick, "confidence_bucket": rule.confidence_bucket, **metrics,
                    })
    by_season = pd.DataFrame(season_rows)
    rows = []
    for keys, group in by_season.groupby(["league", "provider", "timing", "market_pick", "confidence_bucket"], sort=True):
        league, provider, timing, pick, bucket = keys
        usable = group[group["matches"] > 0]
        matches = int(usable["matches"].sum())
        profit = float(usable["profit"].sum())
        rows.append({
            "league": league, "provider": provider, "timing": timing,
            "market_pick": pick, "confidence_bucket": bucket,
            "seasons_with_data": len(usable), "matches": matches,
            "wins": int(usable["wins"].sum()),
            "profit": profit, "roi": profit / matches if matches else None,
            "positive_seasons": int((usable["roi"] > 0).sum()),
        })
    return pd.DataFrame(rows), by_season


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-bookmaker frozen rule validation")
    parser.add_argument("raw_root", type=Path)
    parser.add_argument("frozen_summary", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/historical_strategy_cross_bookmaker"))
    args = parser.parse_args()
    summary, by_season = validate(args.raw_root, pd.read_csv(args.frozen_summary))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "cross_bookmaker_summary.csv", index=False)
    by_season.to_csv(args.output_dir / "cross_bookmaker_by_season.csv", index=False)
    print("CROSS-BOOKMAKER FROZEN RULE VALIDATION — RESEARCH ONLY")
    print(summary.to_string(index=False))
    print("No provider-specific re-selection or threshold tuning performed.")


if __name__ == "__main__":
    main()
