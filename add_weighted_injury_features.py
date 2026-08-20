from pathlib import Path
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent

MATCHES_FILE = (
    ROOT / "data" / "features_with_elo.csv"
)

INJURY_FILE = (
    ROOT
    / "data"
    / "external"
    / "epl_injuries_safe_2019_2024.csv"
)

MAPPING_FILE = (
    ROOT
    / "data"
    / "external"
    / "player_mapping_tm.csv"
)

IMPORTANCE_FILE = (
    ROOT
    / "data"
    / "external"
    / "player_importance_history.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "features_with_weighted_injuries.csv"
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
    "Sheffield United": "Sheffield United",
    "Southampton Football Club": "Southampton",
    "Sunderland AFC": "Sunderland",
    "Tottenham Hotspur Football Club": "Tottenham",
    "Watford FC": "Watford",
    "West Bromwich Albion": "West Brom",
    "West Ham United Football Club": "West Ham",
    "Wolverhampton Wanderers Football Club": "Wolves",
}


# ============================================================
# LOAD MATCHES
# ============================================================

print("Загружаю матчи...")

matches = pd.read_csv(MATCHES_FILE)

matches["match_date"] = pd.to_datetime(
    matches["match_date"],
    errors="coerce",
).dt.normalize()

matches["season_start"] = pd.to_numeric(
    matches["season"].str.slice(0, 4),
    errors="coerce",
)


# ============================================================
# LOAD INJURIES
# ============================================================

print("Загружаю safe injury history...")

inj = pd.read_csv(INJURY_FILE)

inj["start_date"] = pd.to_datetime(
    inj["start_date"],
    errors="coerce",
).dt.normalize()

inj["end_date"] = pd.to_datetime(
    inj["end_date"],
    errors="coerce",
).dt.normalize()

inj["team_normalized"] = inj["team"].map(
    TEAM_MAP
)

inj["tm_player_id"] = pd.to_numeric(
    inj["tm_player_id"],
    errors="coerce",
).astype("Int64")


# ============================================================
# LOAD PLAYER -> TEAM MAPPING
#
# Исключаем multi-team player-season из denominator,
# чтобы трансферы не давали двойной состав.
# ============================================================

print("Загружаю roster mapping...")

mapping = pd.read_csv(MAPPING_FILE)

mapping["season"] = pd.to_numeric(
    mapping["season"],
    errors="coerce",
).astype("Int64")

mapping["tm_player_id"] = pd.to_numeric(
    mapping["tm_player_id"],
    errors="coerce",
).astype("Int64")

mapping["team_normalized"] = mapping["team"].map(
    TEAM_MAP
)


counts = (
    mapping
    .groupby(
        [
            "tm_player_id",
            "season",
        ]
    )
    ["team"]
    .nunique()
    .reset_index(
        name="team_count"
    )
)

mapping = mapping.merge(
    counts,
    on=[
        "tm_player_id",
        "season",
    ],
    how="left",
    validate="many_to_one",
)

mapping = mapping[
    mapping["team_count"] == 1
].copy()

mapping = mapping[
    mapping["season"].between(
        2019,
        2024,
    )
].copy()

mapping = mapping.dropna(
    subset=[
        "team_normalized",
        "tm_player_id",
    ]
)


rosters = (
    mapping
    .groupby(
        [
            "season",
            "team_normalized",
        ]
    )
    ["tm_player_id"]
    .apply(
        lambda s:
            sorted(
                set(
                    int(x)
                    for x in s.dropna()
                )
            )
    )
    .to_dict()
)


# ============================================================
# LOAD POINT-IN-TIME IMPORTANCE
# ============================================================

print("Загружаю point-in-time player importance...")

importance = pd.read_csv(
    IMPORTANCE_FILE,
    usecols=[
        "tm_player_id",
        "date",
        "minutes_prev_365d",
    ],
)

importance["tm_player_id"] = pd.to_numeric(
    importance["tm_player_id"],
    errors="coerce",
)

importance["date"] = pd.to_datetime(
    importance["date"],
    errors="coerce",
).dt.normalize()

importance["minutes_prev_365d"] = pd.to_numeric(
    importance["minutes_prev_365d"],
    errors="coerce",
).fillna(0.0)

importance = importance.dropna(
    subset=[
        "tm_player_id",
        "date",
    ]
)

importance["tm_player_id"] = (
    importance["tm_player_id"]
    .astype(int)
)


# ============================================================
# PLAYER LOOKUP
# ============================================================

player_history = {}

for player_id, group in importance.groupby(
    "tm_player_id",
    sort=False,
):
    group = group.sort_values(
        "date"
    )

    player_history[int(player_id)] = (
        group["date"]
        .values
        .astype("datetime64[D]"),
        group["minutes_prev_365d"]
        .to_numpy(dtype=float),
    )


def importance_before(player_id, date):
    data = player_history.get(
        int(player_id)
    )

    if data is None:
        return 0.0

    dates, values = data

    target = np.datetime64(
        date,
        "D",
    )

    pos = np.searchsorted(
        dates,
        target,
        side="right",
    ) - 1

    if pos < 0:
        return 0.0

    return float(
        values[pos]
    )


# ============================================================
# INDEX INJURIES BY TEAM
# ============================================================

injury_by_team = {
    team: group.copy()
    for team, group in inj.dropna(
        subset=["team_normalized"]
    ).groupby(
        "team_normalized"
    )
}


def active_injured_players(
    team,
    date,
):
    group = injury_by_team.get(team)

    if group is None:
        return set()

    active = group[
        (group["start_date"] <= date)
        &
        (
            group["end_date"].isna()
            |
            (group["end_date"] >= date)
        )
    ]

    return set(
        int(x)
        for x in active[
            "tm_player_id"
        ].dropna()
    )


# ============================================================
# MATCH FEATURES
# ============================================================

print("Рассчитываю weighted injury features...")

rows = []


for i, match in matches.iterrows():

    season = match["season_start"]
    date = match["match_date"]

    home = match["home_team"]
    away = match["away_team"]


    # Данные weighted injury считаем валидными
    # только для сезонов 2019-2024.
    if (
        pd.isna(season)
        or int(season) < 2019
        or int(season) > 2024
    ):
        rows.append({
            "home_missing_minutes365": np.nan,
            "away_missing_minutes365": np.nan,
            "missing_minutes365_difference": np.nan,

            "home_missing_minutes_share": np.nan,
            "away_missing_minutes_share": np.nan,
            "missing_minutes_share_difference": np.nan,

            "home_key_players_injured": np.nan,
            "away_key_players_injured": np.nan,
            "key_players_injured_difference": np.nan,

            "home_weighted_injury_count": np.nan,
            "away_weighted_injury_count": np.nan,
            "weighted_injury_count_difference": np.nan,
        })
        continue


    season = int(season)

    home_roster = rosters.get(
        (season, home),
        [],
    )

    away_roster = rosters.get(
        (season, away),
        [],
    )


    home_importance = {
        player:
            importance_before(
                player,
                date,
            )
        for player in home_roster
    }

    away_importance = {
        player:
            importance_before(
                player,
                date,
            )
        for player in away_roster
    }


    home_total = sum(
        home_importance.values()
    )

    away_total = sum(
        away_importance.values()
    )


    home_injured = (
        active_injured_players(
            home,
            date,
        )
        &
        set(home_roster)
    )

    away_injured = (
        active_injured_players(
            away,
            date,
        )
        &
        set(away_roster)
    )


    home_missing = sum(
        home_importance.get(
            player,
            0.0,
        )
        for player in home_injured
    )

    away_missing = sum(
        away_importance.get(
            player,
            0.0,
        )
        for player in away_injured
    )


    home_share = (
        home_missing / home_total
        if home_total > 0
        else 0.0
    )

    away_share = (
        away_missing / away_total
        if away_total > 0
        else 0.0
    )


    # ========================================================
    # KEY PLAYER = верхний квартиль игроков клуба
    # по minutes_prev_365d на дату матча.
    # ========================================================

    home_positive = [
        value
        for value in home_importance.values()
        if value > 0
    ]

    away_positive = [
        value
        for value in away_importance.values()
        if value > 0
    ]


    home_threshold = (
        np.quantile(
            home_positive,
            0.75,
        )
        if home_positive
        else np.inf
    )

    away_threshold = (
        np.quantile(
            away_positive,
            0.75,
        )
        if away_positive
        else np.inf
    )


    home_key = sum(
        home_importance.get(
            player,
            0.0,
        ) >= home_threshold
        for player in home_injured
    )

    away_key = sum(
        away_importance.get(
            player,
            0.0,
        ) >= away_threshold
        for player in away_injured
    )


    # Нормируем individual importance
    # относительно максимума внутри состава.
    home_max = (
        max(home_positive)
        if home_positive
        else 0.0
    )

    away_max = (
        max(away_positive)
        if away_positive
        else 0.0
    )


    home_weighted_count = sum(
        (
            home_importance.get(
                player,
                0.0,
            )
            / home_max
        )
        if home_max > 0
        else 0.0
        for player in home_injured
    )

    away_weighted_count = sum(
        (
            away_importance.get(
                player,
                0.0,
            )
            / away_max
        )
        if away_max > 0
        else 0.0
        for player in away_injured
    )


    rows.append({
        "home_missing_minutes365":
            home_missing,

        "away_missing_minutes365":
            away_missing,

        "missing_minutes365_difference":
            home_missing - away_missing,

        "home_missing_minutes_share":
            home_share,

        "away_missing_minutes_share":
            away_share,

        "missing_minutes_share_difference":
            home_share - away_share,

        "home_key_players_injured":
            int(home_key),

        "away_key_players_injured":
            int(away_key),

        "key_players_injured_difference":
            int(home_key - away_key),

        "home_weighted_injury_count":
            float(home_weighted_count),

        "away_weighted_injury_count":
            float(away_weighted_count),

        "weighted_injury_count_difference":
            float(
                home_weighted_count
                - away_weighted_count
            ),
    })


    if (
        (i + 1) % 500 == 0
    ):
        print(
            f"Обработано: "
            f"{i + 1}/{len(matches)}"
        )


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


result = result.drop(
    columns=[
        "season_start",
    ]
)


result.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

cols = features.columns.tolist()

print()
print("=" * 110)
print("WEIGHTED INJURY FEATURES CREATED")
print("=" * 110)

print("Строк:", len(result))
print("Новых признаков:", len(cols))


print()
print("Заполненность:")

for col in cols:
    print(
        f"{col:40} "
        f"{result[col].notna().sum():4}"
        f"/{len(result)}"
    )


print()
print("=" * 110)
print("2019/20-2024/25 SIGNAL SUMMARY")
print("=" * 110)

valid = result[
    result["season"].isin([
        "2019/2020",
        "2020/2021",
        "2021/2022",
        "2022/2023",
        "2023/2024",
        "2024/2025",
    ])
]


summary = (
    valid
    .groupby("season")
    .agg(
        matches=(
            "home_team",
            "size",
        ),

        avg_home_missing_share=(
            "home_missing_minutes_share",
            "mean",
        ),

        avg_away_missing_share=(
            "away_missing_minutes_share",
            "mean",
        ),

        avg_home_key_injured=(
            "home_key_players_injured",
            "mean",
        ),

        avg_away_key_injured=(
            "away_key_players_injured",
            "mean",
        ),

        max_home_missing_share=(
            "home_missing_minutes_share",
            "max",
        ),

        max_away_missing_share=(
            "away_missing_minutes_share",
            "max",
        ),
    )
)

print(
    summary.to_string()
)


print()
print("=" * 110)
print("TOP HIGH-IMPACT INJURY MATCHES")
print("=" * 110)

sample = (
    valid
    .assign(
        max_missing_share=lambda x:
            x[
                [
                    "home_missing_minutes_share",
                    "away_missing_minutes_share",
                ]
            ].max(axis=1)
    )
    .sort_values(
        "max_missing_share",
        ascending=False,
    )
    [
        [
            "season",
            "match_date",
            "home_team",
            "away_team",
            "home_missing_minutes_share",
            "away_missing_minutes_share",
            "home_key_players_injured",
            "away_key_players_injured",
            "home_weighted_injury_count",
            "away_weighted_injury_count",
        ]
    ]
    .head(25)
)


print(
    sample.to_string(
        index=False,
    )
)


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
