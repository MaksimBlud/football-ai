"""Normalize Football-Data La Liga team names to canonical project names.

Research-only:
- reads local La Liga history;
- writes a separate normalized dataset under data/;
- performs no Supabase write;
- performs no training;
- performs no production artifact modification.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


INPUT = Path(
    "data/la_liga_official_history_2016_2026.csv"
)

UPCOMING = Path(
    "data/upcoming_matches_la_liga.csv"
)

OUTPUT = Path(
    "data/la_liga_official_history_2016_2026_normalized.csv"
)


# Football-Data name -> canonical project / Odds API name.
ALIASES = {
    "Ath Bilbao": "Athletic Bilbao",
    "Ath Madrid": "Atlético Madrid",
    "Osasuna": "CA Osasuna",
    "Celta": "Celta Vigo",
    "La Coruna": "Deportivo La Coruña",
    "Elche": "Elche CF",
    "Malaga": "Málaga",
    "Betis": "Real Betis",
    "Sociedad": "Real Sociedad",
}

# Current clubs legitimately absent from the 2016-2026
# La Liga top-flight history. They must remain explicit cold starts,
# never silently mapped to another team.
ALLOWED_COLD_START = {
    "Real Racing Club de Santander",
}


def normalize_team(
    value: str,
) -> str:
    value = str(value).strip()

    return ALIASES.get(
        value,
        value,
    )


def main() -> None:
    history = pd.read_csv(
        INPUT
    )

    upcoming = pd.read_csv(
        UPCOMING
    )

    print("=" * 72)
    print("LA LIGA TEAM NAME NORMALIZATION")
    print("=" * 72)

    historical_teams_before = sorted(
        set(
            history["home_team"]
            .dropna()
            .astype(str)
        )
        |
        set(
            history["away_team"]
            .dropna()
            .astype(str)
        )
    )

    print()
    print("HISTORICAL TEAMS BEFORE NORMALIZATION:")

    for team in historical_teams_before:
        print(" ", team)

    print()
    print("ALIASES FOUND:")

    for source, target in (
        ALIASES.items()
    ):
        exists = (
            source
            in historical_teams_before
        )

        print(
            f"{source:20} -> "
            f"{target:32} "
            f"{'FOUND' if exists else 'NOT FOUND'}"
        )

    history = history.copy()

    history["home_team_source"] = (
        history["home_team"]
    )

    history["away_team_source"] = (
        history["away_team"]
    )

    history["home_team"] = (
        history["home_team"]
        .map(normalize_team)
    )

    history["away_team"] = (
        history["away_team"]
        .map(normalize_team)
    )

    historical_teams = (
        set(history["home_team"])
        |
        set(history["away_team"])
    )

    upcoming_teams = (
        set(
            upcoming[
                "home_team_model"
            ]
            .dropna()
            .astype(str)
        )
        |
        set(
            upcoming[
                "away_team_model"
            ]
            .dropna()
            .astype(str)
        )
    )

    covered = sorted(
        upcoming_teams
        & historical_teams
    )

    missing = sorted(
        upcoming_teams
        - historical_teams
    )

    print()
    print("=" * 72)
    print("UPCOMING COVERAGE")
    print("=" * 72)

    print(
        "covered:",
        len(covered),
        "/",
        len(upcoming_teams),
    )

    print(
        "coverage:",
        (
            f"{len(covered) / len(upcoming_teams):.1%}"
            if upcoming_teams
            else "0%"
        ),
    )

    print()
    print("COVERED:")

    for team in covered:
        print(" ", team)

    print()
    print("MISSING:")

    for team in missing:
        print(" ", team)

    duplicates = int(
        history.duplicated(
            subset=[
                "season",
                "match_date",
                "home_team",
                "away_team",
            ]
        ).sum()
    )

    print()
    print("duplicate fixtures:", duplicates)

    unexpected_missing = sorted(
        set(missing) - ALLOWED_COLD_START
    )

    cold_start = sorted(
        set(missing) & ALLOWED_COLD_START
    )

    print()
    print("COLD START:")
    for team in cold_start:
        print(" ", team)

    if unexpected_missing:
        raise RuntimeError(
            "Unexpected canonical coverage gap: "
            + ", ".join(unexpected_missing)
        )

    if duplicates:
        raise RuntimeError(
            f"Normalization created {duplicates} duplicate fixtures"
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    history.to_csv(
        OUTPUT,
        index=False,
    )

    print()
    print("=" * 72)
    print("RESULT")
    print("=" * 72)

    print(
        "rows:",
        len(history),
    )

    print(
        "seasons:",
        history[
            "season"
        ].nunique(),
    )

    print(
        "canonical teams:",
        len(historical_teams),
    )

    print(
        "upcoming coverage:",
        f"{len(covered)}/{len(upcoming_teams)}",
    )

    print(
        "output:",
        OUTPUT,
    )

    print()
    print(
        "PASS: La Liga historical names normalized."
    )


if __name__ == "__main__":
    main()
