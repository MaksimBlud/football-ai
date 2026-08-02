
import pandas as pd


INPUT = "data/features_form.csv"
OUTPUT = "data/features_last5.csv"


def calculate_last5_form(df):

    print("Рассчитываю форму последних 5 матчей...")

    team_history = {}

    home_form = []
    away_form = []

    for _, row in df.iterrows():

        home = row["home_team"]
        away = row["away_team"]

        # текущая форма ДО этого матча
        home_last = team_history.get(home, [])[-5:]
        away_last = team_history.get(away, [])[-5:]

        home_form.append(sum(home_last))
        away_form.append(sum(away_last))

        # результат для истории
        if row["result"] == "HOME":
            home_points = 3
            away_points = 0

        elif row["result"] == "AWAY":
            home_points = 0
            away_points = 3

        else:
            home_points = 1
            away_points = 1

        team_history.setdefault(home, []).append(home_points)
        team_history.setdefault(away, []).append(away_points)

    df["home_last5_points"] = home_form
    df["away_last5_points"] = away_form

    return df


if __name__ == "__main__":

    df = pd.read_csv(INPUT)

    df = calculate_last5_form(df)

    df.to_csv(
        OUTPUT,
        index=False
    )

    print("Создан файл:", OUTPUT)