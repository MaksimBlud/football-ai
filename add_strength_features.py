import pandas as pd


INPUT = "data/features_last5.csv"
OUTPUT = "data/features_strength.csv"


def average(values):
    if not values:
        return 0.0

    return sum(values) / len(values)


def add_strength(df):
    print("Добавляю признаки силы команд...")

    df = df.sort_values(
        ["match_date", "match_time"]
    ).reset_index(drop=True)

    team_history = {}

    home_goals_scored_last5 = []
    home_goals_conceded_last5 = []
    away_goals_scored_last5 = []
    away_goals_conceded_last5 = []

    for _, row in df.iterrows():
        home = row["home_team"]
        away = row["away_team"]

        home_history = team_history.get(home, [])[-5:]
        away_history = team_history.get(away, [])[-5:]

        home_goals_scored_last5.append(
            average([match["scored"] for match in home_history])
        )

        home_goals_conceded_last5.append(
            average([match["conceded"] for match in home_history])
        )

        away_goals_scored_last5.append(
            average([match["scored"] for match in away_history])
        )

        away_goals_conceded_last5.append(
            average([match["conceded"] for match in away_history])
        )

        home_goals = row["home_goals"]
        away_goals = row["away_goals"]

        team_history.setdefault(home, []).append({
            "scored": home_goals,
            "conceded": away_goals
        })

        team_history.setdefault(away, []).append({
            "scored": away_goals,
            "conceded": home_goals
        })

    df["form_difference"] = (
        df["home_last5_points"]
        - df["away_last5_points"]
    )

    df["home_goals_scored_last5"] = home_goals_scored_last5
    df["home_goals_conceded_last5"] = home_goals_conceded_last5
    df["away_goals_scored_last5"] = away_goals_scored_last5
    df["away_goals_conceded_last5"] = away_goals_conceded_last5

    df["attack_difference"] = (
        df["home_goals_scored_last5"]
        - df["away_goals_scored_last5"]
    )

    df["defence_difference"] = (
        df["away_goals_conceded_last5"]
        - df["home_goals_conceded_last5"]
    )

    df["over_2_5"] = (
        df["total_goals"] > 2.5
    ).astype(int)

    df["both_scored"] = (
        (df["home_goals"] > 0)
        & (df["away_goals"] > 0)
    ).astype(int)

    return df


if __name__ == "__main__":
    df = pd.read_csv(INPUT)

    df = add_strength(df)

    df.to_csv(
        OUTPUT,
        index=False
    )

    print("Создан файл:", OUTPUT)
