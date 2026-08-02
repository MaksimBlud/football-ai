import pandas as pd


INPUT = "data/features_engineered.csv"
OUTPUT = "data/features_with_elo.csv"

INITIAL_ELO = 1500.0
K_FACTOR = 20.0
HOME_ADVANTAGE = 80.0


def expected_score(
    team_rating,
    opponent_rating
):
    return 1.0 / (
        1.0
        + 10 ** (
            (opponent_rating - team_rating) / 400.0
        )
    )


def actual_scores(result):
    if result in ("H", "HOME"):
        return 1.0, 0.0

    if result in ("D", "DRAW"):
        return 0.5, 0.5

    if result in ("A", "AWAY"):
        return 0.0, 1.0

    raise ValueError(
        f"Неизвестный результат матча: {result}"
    )


def add_elo_features(df):
    print("Рассчитываю рейтинг Эло...")

    df["match_date"] = pd.to_datetime(
        df["match_date"],
        errors="coerce"
    )

    df = df.sort_values(
        ["match_date", "match_time"]
    ).reset_index(drop=True)

    ratings = {}

    home_elo_before = []
    away_elo_before = []
    elo_difference = []

    for _, row in df.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]

        home_elo = ratings.get(
            home_team,
            INITIAL_ELO
        )

        away_elo = ratings.get(
            away_team,
            INITIAL_ELO
        )

        home_elo_before.append(home_elo)
        away_elo_before.append(away_elo)

        elo_difference.append(
            home_elo
            + HOME_ADVANTAGE
            - away_elo
        )

        expected_home = expected_score(
            home_elo + HOME_ADVANTAGE,
            away_elo
        )

        expected_away = 1.0 - expected_home

        actual_home, actual_away = actual_scores(
            row["result"]
        )

        ratings[home_team] = (
            home_elo
            + K_FACTOR
            * (actual_home - expected_home)
        )

        ratings[away_team] = (
            away_elo
            + K_FACTOR
            * (actual_away - expected_away)
        )

    df["home_elo"] = home_elo_before
    df["away_elo"] = away_elo_before
    df["elo_difference"] = elo_difference

    return df


if __name__ == "__main__":
    df = pd.read_csv(INPUT)

    df = add_elo_features(df)

    df.to_csv(
        OUTPUT,
        index=False
    )

    print("Создан файл:", OUTPUT)
    print("Матчей:", len(df))
