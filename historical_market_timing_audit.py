"""Audit standard vs explicit closing historical 1X2 columns.

Research only. This module does not infer that a non-C column is an opening price; it
reports column availability/coverage exactly as supplied by Football-Data CSVs.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

PAIRS = {
    "BET365": (("B365H", "B365D", "B365A"), ("B365CH", "B365CD", "B365CA")),
    "PINNACLE": (("PSH", "PSD", "PSA"), ("PSCH", "PSCD", "PSCA")),
    "AVERAGE": (("AvgH", "AvgD", "AvgA"), ("AvgCH", "AvgCD", "AvgCA")),
    "MAXIMUM": (("MaxH", "MaxD", "MaxA"), ("MaxCH", "MaxCD", "MaxCA")),
}


def _valid(frame: pd.DataFrame, columns: tuple[str, str, str]) -> pd.Series:
    if not all(column in frame.columns for column in columns):
        return pd.Series(False, index=frame.index)
    return frame[list(columns)].apply(pd.to_numeric, errors="coerce").gt(1.0).all(axis=1)


def _no_vig(frame: pd.DataFrame, columns: tuple[str, str, str]) -> pd.DataFrame:
    odds = frame[list(columns)].apply(pd.to_numeric, errors="coerce")
    implied = 1.0 / odds
    return implied.div(implied.sum(axis=1), axis=0)


def audit_frame(frame: pd.DataFrame, *, league: str, season: str) -> list[dict]:
    rows = []
    for provider, (standard, closing) in PAIRS.items():
        standard_present = all(c in frame.columns for c in standard)
        closing_present = all(c in frame.columns for c in closing)
        standard_valid = _valid(frame, standard)
        closing_valid = _valid(frame, closing)
        paired = standard_valid & closing_valid
        mean_probability_delta = None
        argmax_change_rate = None
        if paired.any():
            standard_prob = _no_vig(frame.loc[paired], standard)
            closing_prob = _no_vig(frame.loc[paired], closing)
            mean_probability_delta = float((standard_prob.to_numpy() - closing_prob.to_numpy()).__abs__().mean())
            argmax_change_rate = float((standard_prob.to_numpy().argmax(axis=1) != closing_prob.to_numpy().argmax(axis=1)).mean())
        rows.append({
            "league": league,
            "season": season,
            "provider": provider,
            "standard_columns": "/".join(standard),
            "closing_columns": "/".join(closing),
            "standard_present": standard_present,
            "closing_present": closing_present,
            "rows": len(frame),
            "standard_valid_rows": int(standard_valid.sum()),
            "closing_valid_rows": int(closing_valid.sum()),
            "paired_valid_rows": int(paired.sum()),
            "mean_abs_no_vig_probability_delta": mean_probability_delta,
            "argmax_change_rate": argmax_change_rate,
        })
    return rows


def audit_raw_tree(raw_root: Path) -> pd.DataFrame:
    rows = []
    for league_dir in sorted(path for path in raw_root.iterdir() if path.is_dir()):
        for path in sorted(league_dir.glob("*.csv")):
            frame = pd.read_csv(path)
            years = path.stem.rsplit("_", 2)[-2:]
            season = f"{years[0]}-{years[1]}" if len(years) == 2 else path.stem
            rows.extend(audit_frame(frame, league=league_dir.name.upper(), season=season))
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit historical standard vs explicit closing odds columns")
    parser.add_argument("raw_root", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/historical_strategy_timing/timing_coverage.csv"))
    args = parser.parse_args()
    report = audit_raw_tree(args.raw_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(args.output, index=False)
    print("HISTORICAL MARKET TIMING AUDIT — RESEARCH ONLY")
    print(report.to_string(index=False))
    print("Non-C columns are labeled standard, not opening. C columns are explicit closing fields only when present.")


if __name__ == "__main__":
    main()
