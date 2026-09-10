"""Normalize completed La Liga history without reading current fixtures.

This is the historical/OOS counterpart to ``normalize_la_liga_history.py``.
It deliberately omits upcoming-fixture coverage checks so completed-history
model development does not depend on a current prospective fixture export.
No Supabase access, provider call, training, or production artifact write is
performed.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from normalize_la_liga_history import ALIASES, normalize_team

INPUT = Path("data/la_liga_official_history_2016_2026.csv")
OUTPUT = Path("data/la_liga_official_history_2016_2026_normalized.csv")


def normalize_history(history: pd.DataFrame) -> pd.DataFrame:
    required = {"season", "match_date", "home_team", "away_team"}
    missing = required - set(history.columns)
    if missing:
        raise ValueError("Historical input missing columns: " + ", ".join(sorted(missing)))

    result = history.copy()
    result["home_team_source"] = result["home_team"]
    result["away_team_source"] = result["away_team"]
    result["home_team"] = result["home_team"].map(normalize_team)
    result["away_team"] = result["away_team"].map(normalize_team)

    duplicates = int(
        result.duplicated(
            subset=["season", "match_date", "home_team", "away_team"]
        ).sum()
    )
    if duplicates:
        raise RuntimeError(
            f"Historical-only normalization created {duplicates} duplicate fixtures"
        )
    return result


def main() -> int:
    history = pd.read_csv(INPUT)
    result = normalize_history(history)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False)

    source_teams = set(history["home_team"].astype(str)) | set(history["away_team"].astype(str))
    aliases_found = sorted(name for name in ALIASES if name in source_teams)
    canonical_teams = set(result["home_team"].astype(str)) | set(result["away_team"].astype(str))

    print("LA LIGA HISTORICAL-ONLY NORMALIZATION")
    print("rows:", len(result))
    print("seasons:", result["season"].nunique())
    print("canonical teams:", len(canonical_teams))
    print("aliases applied:", len(aliases_found))
    print("upcoming fixtures read: False")
    print("output:", OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
