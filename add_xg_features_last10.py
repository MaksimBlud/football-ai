import pandas as pd


MATCHES_INPUT = "data/features_with_elo.csv"
XG_INPUT = "data/understat_xg.csv"
OUTPUT = "data/features_with_xg_last10.csv"
LAST_MATCHES = 10


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


def average(values):
    if not values:
        return 0.0

    return sum(values) / len(values)


print("Загружаю основные признаки...")

matches = pd.read_csv(MATCHES_INPUT)

matches["match_date"] = pd.to_datetime(
    matches["match_date"],
    errors="coerce",
).dt.normalize()

print("Загружаю xG Understat...")

xg = pd.read_csv(XG_INPUT)

xg["match_date"] = pd.to_datetime(
    xg["match_date"],
    errors="coerce",
).dt.normalize()

xg["team"] = xg["team"].replace(TEAM_NAME_MAP)

xg["season"] = (
    xg["season_start"].astype(str)
    + "/"
    + (xg["season_start"] + 1).astype(str)
)

xg = xg.sort_values(
    ["match_date", "team"]
).reset_index(drop=True)

team_history = {}
feature_rows = []

print("Рассчитываю xG-признаки до каждого матча...")

for _, row in xg.iterrows():
    team = row["team"]

    history = team_history.get(
        team,
        [],
    )[-LAST_MATCHES:]

    feature_rows.append({
        "season": row["season"],
        "match_date": row["match_date"],
        "team": team,
        "venue": row["venue"],

        "xg_last5": average([
            match["xg"]
            for match in history
        ]),

        "xga_last5": average([
            match["xga"]
            for match in history
        ]),

        "npxg_last5": average([
            match["npxg"]
            for match in history
        ]),

        "npxga_last5": average([
            match["npxga"]
            for match in history
        ]),
    })

    team_history.setdefault(
        team,
        [],
    ).append({
        "xg": float(row["xg"]),
        "xga": float(row["xga"]),
        "npxg": float(row["npxg"]),
        "npxga": float(row["npxga"]),
    })

xg_features = pd.DataFrame(feature_rows)

home_xg = xg_features[
    xg_features["venue"] == "h"
].copy()

home_xg = home_xg.rename(columns={
    "team": "home_team",
    "xg_last5": "home_xg_last5",
    "xga_last5": "home_xga_last5",
    "npxg_last5": "home_npxg_last5",
    "npxga_last5": "home_npxga_last5",
})

home_xg = home_xg.drop(
    columns=["venue"]
)

away_xg = xg_features[
    xg_features["venue"] == "a"
].copy()

away_xg = away_xg.rename(columns={
    "team": "away_team",
    "xg_last5": "away_xg_last5",
    "xga_last5": "away_xga_last5",
    "npxg_last5": "away_npxg_last5",
    "npxga_last5": "away_npxga_last5",
})

away_xg = away_xg.drop(
    columns=["venue"]
)

result = matches.merge(
    home_xg,
    on=[
        "season",
        "match_date",
        "home_team",
    ],
    how="left",
)

result = result.merge(
    away_xg,
    on=[
        "season",
        "match_date",
        "away_team",
    ],
    how="left",
)

xg_columns = [
    "home_xg_last5",
    "home_xga_last5",
    "home_npxg_last5",
    "home_npxga_last5",
    "away_xg_last5",
    "away_xga_last5",
    "away_npxg_last5",
    "away_npxga_last5",
]

for column in xg_columns:
    result[column] = pd.to_numeric(
        result[column],
        errors="coerce",
    )

result["xg_attack_difference"] = (
    result["home_xg_last5"]
    - result["away_xg_last5"]
)

result["xg_defence_difference"] = (
    result["away_xga_last5"]
    - result["home_xga_last5"]
)

result.to_csv(
    OUTPUT,
    index=False,
)

print("Создан файл:", OUTPUT)
print("Строк:", len(result))
print("Колонок:", len(result.columns))

print("\nЗаполненность xG-признаков:")

for column in xg_columns:
    print(
        column,
        result[column].notna().sum(),
        "из",
        len(result),
    )
