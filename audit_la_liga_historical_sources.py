"""Audit available historical La Liga data sources.

Research-only:
- no Supabase writes
- no production model loading
- no artifact promotion
"""

from pathlib import Path
import pandas as pd


DATA = Path("data")

REQUIRED = {
    "season",
    "match_date",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
}

DESIRED = REQUIRED | {
    "match_time",
    "home_shots",
    "away_shots",
    "home_shots_target",
    "away_shots_target",
    "home_corners",
    "away_corners",
    "home_yellow",
    "away_yellow",
    "home_red",
    "away_red",
}


def inspect(path):
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        return {
            "path": str(path),
            "error": str(exc),
        }

    cols = set(df.columns)

    team_sample = set()

    if "home_team" in cols:
        team_sample |= set(
            df["home_team"]
            .dropna()
            .astype(str)
            .head(200)
        )

    if "away_team" in cols:
        team_sample |= set(
            df["away_team"]
            .dropna()
            .astype(str)
            .head(200)
        )

    la_liga_markers = {
        "Barcelona",
        "Real Madrid",
        "Atlético Madrid",
        "Atletico Madrid",
        "Sevilla",
        "Valencia",
        "Villarreal",
        "Real Sociedad",
        "Real Betis",
        "Athletic Bilbao",
        "Getafe",
        "Celta Vigo",
        "Osasuna",
    }

    marker_hits = sorted(
        team_sample & la_liga_markers
    )

    return {
        "path": str(path),
        "rows": len(df),
        "required": len(REQUIRED & cols),
        "required_total": len(REQUIRED),
        "desired": len(DESIRED & cols),
        "desired_total": len(DESIRED),
        "missing_required": sorted(
            REQUIRED - cols
        ),
        "la_liga_markers": marker_hits,
        "league_values": (
            sorted(
                df["league"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )[:20]
            if "league" in cols
            else []
        ),
    }


print("=" * 72)
print("LA LIGA HISTORICAL SOURCE AUDIT")
print("=" * 72)

results = []

for path in sorted(DATA.rglob("*.csv")):
    result = inspect(path)

    if "error" not in result:
        if (
            result["required"] >= 5
            or result["la_liga_markers"]
            or any(
                "liga" in value.lower()
                or "spain" in value.lower()
                for value in result["league_values"]
            )
        ):
            results.append(result)


results.sort(
    key=lambda x: (
        bool(x["la_liga_markers"]),
        x["required"],
        x["desired"],
        x["rows"],
    ),
    reverse=True,
)


if not results:
    print("No plausible historical source found.")

else:
    for result in results:
        print()
        print(result["path"])
        print("  rows:", result["rows"])
        print(
            "  required:",
            f'{result["required"]}/{result["required_total"]}',
        )
        print(
            "  desired:",
            f'{result["desired"]}/{result["desired_total"]}',
        )
        print(
            "  missing required:",
            result["missing_required"],
        )
        print(
            "  league values:",
            result["league_values"],
        )
        print(
            "  La Liga markers:",
            result["la_liga_markers"],
        )


print()
print("=" * 72)
print("VERDICT")
print("=" * 72)

strong = [
    r for r in results
    if r["required"] == r["required_total"]
    and (
        r["la_liga_markers"]
        or any(
            "liga" in value.lower()
            or "spain" in value.lower()
            for value in r["league_values"]
        )
    )
]

if strong:
    print(
        "LOCAL_CANDIDATE_FOUND:",
        len(strong),
    )

    for item in strong:
        print(" ", item["path"])

    print(
        "NEXT: normalize and validate local "
        "La Liga history."
    )

else:
    print("LOCAL_CANDIDATE_FOUND: 0")
    print(
        "NEXT: external historical La Liga "
        "ingestion is required."
    )
