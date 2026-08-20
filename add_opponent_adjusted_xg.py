from pathlib import Path
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent

MATCHES_FILE = (
    ROOT
    / "data"
    / "features_with_elo.csv"
)

XG_FILE = (
    ROOT
    / "data"
    / "understat_xg.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "features_with_opponent_adjusted_xg.csv"
)


LAST_N = 10


TEAM_NAME_MAP = {
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Nottingham Forest": "Nott'm Forest",
    "Sheffield United": "Sheffield United",
    "Wolverhampton Wanderers": "Wolves",
    "West Bromwich Albion": "West Brom",
    "Newcastle United": "Newcastle",
    "Tottenham": "Tottenham",
}


def mean_or_nan(values):
    if not values:
        return np.nan
    return float(np.mean(values))


print("Загружаю features_with_elo.csv...")

matches = pd.read_csv(MATCHES_FILE)

matches["match_date"] = pd.to_datetime(
    matches["match_date"],
    errors="coerce",
).dt.normalize()


print("Загружаю Understat xG...")

xg = pd.read_csv(XG_FILE)

xg["match_date"] = pd.to_datetime(
    xg["match_date"],
    errors="coerce",
).dt.normalize()

xg["team"] = xg["team"].replace(
    TEAM_NAME_MAP
)

xg["season"] = (
    xg["season_start"].astype(str)
    + "/"
    + (xg["season_start"] + 1).astype(str)
)


# ============================================================
# СОБИРАЕМ MATCH-LEVEL ТАБЛИЦУ ИЗ UNDERSTAT
# ============================================================

home = xg[
    xg["venue"] == "h"
].copy()

away = xg[
    xg["venue"] == "a"
].copy()


home = home.rename(
    columns={
        "team": "home_team",
        "xg": "home_match_xg",
        "xga": "home_match_xga",
        "npxg": "home_match_npxg",
        "npxga": "home_match_npxga",
    }
)

away = away.rename(
    columns={
        "team": "away_team",
        "xg": "away_match_xg",
        "xga": "away_match_xga",
        "npxg": "away_match_npxg",
        "npxga": "away_match_npxga",
    }
)


understat_matches = home[
    [
        "season",
        "match_date",
        "home_team",
        "home_match_xg",
        "home_match_xga",
        "home_match_npxg",
        "home_match_npxga",
    ]
].merge(
    away[
        [
            "season",
            "match_date",
            "away_team",
            "away_match_xg",
            "away_match_xga",
            "away_match_npxg",
            "away_match_npxga",
        ]
    ],
    on=[
        "season",
        "match_date",
    ],
    how="inner",
)


# ============================================================
# ДОБАВЛЯЕМ ELO ОБЕИХ КОМАНД ИЗ НАШЕГО DATASET
# ============================================================

history = matches[
    [
        "season",
        "match_date",
        "home_team",
        "away_team",
        "home_elo",
        "away_elo",
    ]
].merge(
    understat_matches,
    on=[
        "season",
        "match_date",
        "home_team",
        "away_team",
    ],
    how="inner",
)


history = history.sort_values(
    [
        "match_date",
        "home_team",
        "away_team",
    ]
).reset_index(drop=True)


print(
    "Исторических матчей с xG + ELO:",
    len(history),
)


# ============================================================
# OPPONENT-ADJUSTED HISTORY
#
# Базовый ELO = 1500.
#
# Для атакующего xG:
# против более сильного соперника xG усиливаем.
#
# Для xGA:
# если соперник сильнее, допущенный xG штрафуем меньше.
# ============================================================

BASE_ELO = 1500.0
ELO_SCALE = 400.0


team_history = {}
feature_rows = []


def opponent_factor(opponent_elo):
    return float(
        np.exp(
            (opponent_elo - BASE_ELO)
            / ELO_SCALE
        )
    )


for _, row in history.iterrows():

    home_team = row["home_team"]
    away_team = row["away_team"]

    home_hist = team_history.get(
        home_team,
        []
    )[-LAST_N:]

    away_hist = team_history.get(
        away_team,
        []
    )[-LAST_N:]


    feature_rows.append({
        "season": row["season"],
        "match_date": row["match_date"],
        "home_team": home_team,
        "away_team": away_team,

        "home_adj_xg_last10":
            mean_or_nan([
                m["adj_xg"]
                for m in home_hist
            ]),

        "home_adj_xga_last10":
            mean_or_nan([
                m["adj_xga"]
                for m in home_hist
            ]),

        "away_adj_xg_last10":
            mean_or_nan([
                m["adj_xg"]
                for m in away_hist
            ]),

        "away_adj_xga_last10":
            mean_or_nan([
                m["adj_xga"]
                for m in away_hist
            ]),

        "home_opponent_elo_last10":
            mean_or_nan([
                m["opponent_elo"]
                for m in home_hist
            ]),

        "away_opponent_elo_last10":
            mean_or_nan([
                m["opponent_elo"]
                for m in away_hist
            ]),
    })


    away_strength = opponent_factor(
        float(row["away_elo"])
    )

    home_strength = opponent_factor(
        float(row["home_elo"])
    )


    team_history.setdefault(
        home_team,
        []
    ).append({
        "adj_xg":
            float(row["home_match_xg"])
            * away_strength,

        "adj_xga":
            float(row["home_match_xga"])
            / away_strength,

        "opponent_elo":
            float(row["away_elo"]),
    })


    team_history.setdefault(
        away_team,
        []
    ).append({
        "adj_xg":
            float(row["away_match_xg"])
            * home_strength,

        "adj_xga":
            float(row["away_match_xga"])
            / home_strength,

        "opponent_elo":
            float(row["home_elo"]),
    })


features = pd.DataFrame(
    feature_rows
)


features[
    "adj_xg_attack_difference"
] = (
    features["home_adj_xg_last10"]
    - features["away_adj_xg_last10"]
)


features[
    "adj_xg_defence_difference"
] = (
    features["away_adj_xga_last10"]
    - features["home_adj_xga_last10"]
)


features[
    "opponent_strength_difference"
] = (
    features["home_opponent_elo_last10"]
    - features["away_opponent_elo_last10"]
)


result = matches.merge(
    features,
    on=[
        "season",
        "match_date",
        "home_team",
        "away_team",
    ],
    how="left",
)


result.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 100)
print("OPPONENT-ADJUSTED XG CREATED")
print("=" * 100)

print("Строк:", len(result))

new_cols = [
    "home_adj_xg_last10",
    "home_adj_xga_last10",
    "away_adj_xg_last10",
    "away_adj_xga_last10",
    "home_opponent_elo_last10",
    "away_opponent_elo_last10",
    "adj_xg_attack_difference",
    "adj_xg_defence_difference",
    "opponent_strength_difference",
]

for col in new_cols:
    filled = result[col].notna().sum()

    print(
        f"{col:35} "
        f"{filled}/{len(result)}"
    )


print()
print("По сезонам:")

complete = result[
    new_cols
].notna().all(axis=1)

print(
    result.assign(
        complete=complete
    )
    .groupby("season")[
        "complete"
    ]
    .agg([
        "count",
        "sum",
        "mean",
    ])
    .to_string()
)


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
