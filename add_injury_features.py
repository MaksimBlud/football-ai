from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parent

MATCHES_FILE = (
    ROOT
    / "data"
    / "features_with_elo.csv"
)

INJURY_FILE = (
    ROOT
    / "data"
    / "external"
    / "epl_injuries_safe_2019_2024.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "features_with_injuries.csv"
)


TEAM_MAP = {
    "Arsenal Football Club": "Arsenal",
    "Aston Villa Football Club": "Aston Villa",
    "Association Football Club Bournemouth": "Bournemouth",
    "Brentford Football Club": "Brentford",
    "Brighton and Hove Albion Football Club": "Brighton",
    "Burnley FC": "Burnley",
    "Chelsea Football Club": "Chelsea",
    "Crystal Palace Football Club": "Crystal Palace",
    "Everton Football Club": "Everton",
    "Fulham Football Club": "Fulham",
    "Ipswich Town Football Club": "Ipswich",
    "Leeds United": "Leeds",
    "Leicester City Football Club": "Leicester",
    "Liverpool Football Club": "Liverpool",
    "Luton Town": "Luton",
    "Manchester City Football Club": "Man City",
    "Manchester United Football Club": "Man United",
    "Newcastle United Football Club": "Newcastle",
    "Norwich City": "Norwich",
    "Nottingham Forest Football Club": "Nott'm Forest",
    "Queens Park Rangers": "QPR",
    "Reading FC": "Reading",
    "Sheffield United": "Sheffield United",
    "Southampton Football Club": "Southampton",
    "Stoke City": "Stoke",
    "Sunderland AFC": "Sunderland",
    "Swansea City": "Swansea",
    "Tottenham Hotspur Football Club": "Tottenham",
    "Watford FC": "Watford",
    "West Bromwich Albion": "West Brom",
    "West Ham United Football Club": "West Ham",
    "Wolverhampton Wanderers Football Club": "Wolves",
    "Hull City": "Hull",
    "Cardiff City": "Cardiff",
}


print("Загружаю матчи...")

matches = pd.read_csv(MATCHES_FILE)

matches["match_date"] = pd.to_datetime(
    matches["match_date"],
    errors="coerce",
).dt.normalize()


print("Загружаю injury history...")

inj = pd.read_csv(INJURY_FILE)

inj["start_date"] = pd.to_datetime(
    inj["start_date"],
    errors="coerce",
).dt.normalize()

inj["end_date"] = pd.to_datetime(
    inj["end_date"],
    errors="coerce",
).dt.normalize()

inj["team_normalized"] = (
    inj["team"]
    .map(TEAM_MAP)
)


# ============================================================
# CHECK TEAM MAPPING
# ============================================================

unmapped_teams = (
    inj.loc[
        inj["team_normalized"].isna(),
        "team",
    ]
    .dropna()
    .unique()
)

if len(unmapped_teams):
    print()
    print("⚠️ Не сопоставлены team names:")

    for team in sorted(unmapped_teams):
        print(" -", team)


# ============================================================
# MATCH-LEVEL INJURY FEATURES
# ============================================================

rows = []


print()
print("Рассчитываю injury features до каждого матча...")


for _, match in matches.iterrows():

    date = match["match_date"]
    home = match["home_team"]
    away = match["away_team"]

    # Игрок считается unavailable,
    # если injury spell уже начался
    # и на дату матча ещё не закончился.
    active = inj[
        (inj["start_date"] <= date)
        &
        (
            inj["end_date"].isna()
            |
            (inj["end_date"] >= date)
        )
    ]

    home_active = active[
        active["team_normalized"] == home
    ]

    away_active = active[
        active["team_normalized"] == away
    ]


    home_players = int(
        home_active["tm_player_id"].nunique()
    )

    away_players = int(
        away_active["tm_player_id"].nunique()
    )


    # Сколько активных injury spells началось недавно.
    # Это безопасно: смотрим только назад от даты матча.
    home_recent7 = int(
        home_active[
            home_active["start_date"]
            >= date - pd.Timedelta(days=7)
        ]["tm_player_id"].nunique()
    )

    away_recent7 = int(
        away_active[
            away_active["start_date"]
            >= date - pd.Timedelta(days=7)
        ]["tm_player_id"].nunique()
    )


    home_recent14 = int(
        home_active[
            home_active["start_date"]
            >= date - pd.Timedelta(days=14)
        ]["tm_player_id"].nunique()
    )

    away_recent14 = int(
        away_active[
            away_active["start_date"]
            >= date - pd.Timedelta(days=14)
        ]["tm_player_id"].nunique()
    )


    rows.append({
        "home_injured_players":
            home_players,

        "away_injured_players":
            away_players,

        "injured_players_difference":
            home_players - away_players,

        "home_new_injuries_last7":
            home_recent7,

        "away_new_injuries_last7":
            away_recent7,

        "new_injuries_last7_difference":
            home_recent7 - away_recent7,

        "home_new_injuries_last14":
            home_recent14,

        "away_new_injuries_last14":
            away_recent14,

        "new_injuries_last14_difference":
            home_recent14 - away_recent14,
    })


features = pd.DataFrame(
    rows
)

result = pd.concat(
    [
        matches.reset_index(drop=True),
        features,
    ],
    axis=1,
)


result.to_csv(
    OUTPUT_FILE,
    index=False,
)


new_cols = features.columns.tolist()


print()
print("=" * 100)
print("INJURY FEATURES CREATED")
print("=" * 100)

print("Строк:", len(result))
print("Новых признаков:", len(new_cols))

print()

for col in new_cols:

    print(
        f"{col:35} "
        f"min={result[col].min():>5} "
        f"mean={result[col].mean():>7.3f} "
        f"max={result[col].max():>5}"
    )


print()
print("=" * 100)
print("SEASON COVERAGE / SIGNAL")
print("=" * 100)

season_stats = (
    result
    .groupby("season")
    .agg(
        matches=(
            "home_team",
            "size",
        ),

        avg_home_injured=(
            "home_injured_players",
            "mean",
        ),

        avg_away_injured=(
            "away_injured_players",
            "mean",
        ),

        matches_with_any_injury=(
            "home_injured_players",
            lambda s:
                int(
                    (
                        (s > 0)
                    ).sum()
                ),
        ),
    )
)

print(
    season_stats.to_string()
)


print()
print("=" * 100)
print("LATEST SAMPLE")
print("=" * 100)

print(
    result[
        [
            "season",
            "match_date",
            "home_team",
            "away_team",
            "home_injured_players",
            "away_injured_players",
            "home_new_injuries_last7",
            "away_new_injuries_last7",
        ]
    ]
    .tail(20)
    .to_string(index=False)
)


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
