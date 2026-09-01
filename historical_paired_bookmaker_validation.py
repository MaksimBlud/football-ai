"""Paired common-fixture validation for frozen historical market rules.

Rules and fixture membership are defined once from Bet365 standard prices. The exact same
selected rows are then priced at Bet365/Pinnacle standard and closing columns when those
prices exist. Other providers never re-select fixtures. Research only; no production side
effects.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

SIDES = ("H", "D", "A")
REFERENCE_COLUMNS = ("B365H", "B365D", "B365A")
PRICE_SETS = {
    ("BET365", "standard"): ("B365H", "B365D", "B365A"),
    ("BET365", "closing"): ("B365CH", "B365CD", "B365CA"),
    ("PINNACLE", "standard"): ("PSH", "PSD", "PSA"),
    ("PINNACLE", "closing"): ("PSCH", "PSCD", "PSCA"),
}
BOUNDS = {
    "<40%": (0.0, 0.40),
    "40–50%": (0.40, 0.50),
    "50–60%": (0.50, 0.60),
    "60–70%": (0.60, 0.70),
    "≥70%": (0.70, 1.0000001),
}


def reference_mask(frame: pd.DataFrame, *, pick: str, bucket: str) -> pd.Series:
    if pick not in SIDES:
        raise ValueError(f"Unsupported pick: {pick}")
    if bucket not in BOUNDS:
        raise ValueError(f"Unsupported confidence bucket: {bucket}")
    if not all(column in frame.columns for column in REFERENCE_COLUMNS):
        return pd.Series(False, index=frame.index)

    odds = frame[list(REFERENCE_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    valid = odds.gt(1.0).all(axis=1) & frame["FTR"].astype(str).isin(SIDES)
    implied = 1.0 / odds.loc[valid]
    probabilities = implied.div(implied.sum(axis=1), axis=0)
    argmax = pd.Series(
        [SIDES[index] for index in probabilities.to_numpy().argmax(axis=1)],
        index=probabilities.index,
    )
    confidence = pd.Series(probabilities.to_numpy().max(axis=1), index=probabilities.index)
    low, high = BOUNDS[bucket]
    selected = argmax.eq(pick) & confidence.ge(low) & confidence.lt(high)
    mask = pd.Series(False, index=frame.index)
    mask.loc[selected.index] = selected
    return mask


def price_selected_rows(
    frame: pd.DataFrame,
    selected_mask: pd.Series,
    columns: tuple[str, str, str],
    *,
    pick: str,
) -> dict[str, float | int | None]:
    reference_selected = int(selected_mask.sum())
    if not all(column in frame.columns for column in columns):
        return {
            "reference_selected_matches": reference_selected,
            "priced_matches": 0,
            "price_coverage": 0.0 if reference_selected else None,
            "wins": 0,
            "average_odds": None,
            "profit": 0.0,
            "roi": None,
        }

    selected = frame.loc[selected_mask].copy()
    prices = selected[list(columns)].apply(pd.to_numeric, errors="coerce")
    actual = selected["FTR"].astype(str)
    valid = prices.gt(1.0).all(axis=1) & actual.isin(SIDES)
    selected = selected.loc[valid]
    prices = prices.loc[valid]
    actual = actual.loc[valid]
    n = len(selected)
    coverage = n / reference_selected if reference_selected else None
    if not n:
        return {
            "reference_selected_matches": reference_selected,
            "priced_matches": 0,
            "price_coverage": coverage,
            "wins": 0,
            "average_odds": None,
            "profit": 0.0,
            "roi": None,
        }

    chosen_odds = prices.iloc[:, SIDES.index(pick)]
    won = actual.eq(pick)
    profit = pd.Series(-1.0, index=chosen_odds.index)
    profit.loc[won] = chosen_odds.loc[won] - 1.0
    total = float(profit.sum())
    return {
        "reference_selected_matches": reference_selected,
        "priced_matches": n,
        "price_coverage": coverage,
        "wins": int(won.sum()),
        "average_odds": float(chosen_odds.mean()),
        "profit": total,
        "roi": total / n,
    }


def validate(raw_root: Path, frozen_summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    season_rows: list[dict[str, object]] = []

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
            mask = reference_mask(frame, pick=pick, bucket=bucket)
            for (provider, timing), columns in PRICE_SETS.items():
                metrics = price_selected_rows(frame, mask, columns, pick=pick)
                season_rows.append({
                    "league": league,
                    "season": season,
                    "reference_provider": "BET365",
                    "reference_timing": "standard",
                    "provider": provider,
                    "timing": timing,
                    "market_pick": pick,
                    "confidence_bucket": bucket,
                    **metrics,
                })

    by_season = pd.DataFrame(season_rows)
    rows: list[dict[str, object]] = []
    for keys, group in by_season.groupby(
        ["league", "provider", "timing", "market_pick", "confidence_bucket"],
        sort=True,
    ):
        league, provider, timing, pick, bucket = keys
        reference_matches = int(group["reference_selected_matches"].sum())
        priced_matches = int(group["priced_matches"].sum())
        profit = float(group["profit"].sum())
        usable = group[group["priced_matches"] > 0]
        rows.append({
            "league": league,
            "reference_provider": "BET365",
            "reference_timing": "standard",
            "provider": provider,
            "timing": timing,
            "market_pick": pick,
            "confidence_bucket": bucket,
            "seasons": len(group),
            "reference_selected_matches": reference_matches,
            "priced_matches": priced_matches,
            "price_coverage": priced_matches / reference_matches if reference_matches else None,
            "wins": int(group["wins"].sum()),
            "profit": profit,
            "roi": profit / priced_matches if priced_matches else None,
            "positive_seasons": int((usable["roi"] > 0).sum()),
        })

    return pd.DataFrame(rows), by_season


def main() -> None:
    parser = argparse.ArgumentParser(description="Paired common-fixture frozen-rule bookmaker validation")
    parser.add_argument("raw_root", type=Path)
    parser.add_argument("frozen_summary", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/historical_strategy_paired_bookmaker"),
    )
    args = parser.parse_args()
    summary, by_season = validate(args.raw_root, pd.read_csv(args.frozen_summary))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "paired_bookmaker_summary.csv", index=False)
    by_season.to_csv(args.output_dir / "paired_bookmaker_by_season.csv", index=False)
    print("PAIRED COMMON-FIXTURE BOOKMAKER VALIDATION — RESEARCH ONLY")
    print(summary.to_string(index=False))
    print("Fixture membership is frozen from Bet365 standard prices; other providers only price those same rows.")
    print("No training, Supabase writes, live activation, Structural changes, or .pkl changes performed.")


if __name__ == "__main__":
    main()
