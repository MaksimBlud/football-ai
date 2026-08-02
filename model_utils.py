import pandas as pd

from database import supabase


LAST_MATCHES = 5
INITIAL_ELO = 1500.0
K_FACTOR = 20.0
HOME_ADVANTAGE = 80.0


FEATURES = [
    "home_odds",
    "draw_odds",
    "away_odds",
    "home_last5_points",
    "away_last5_points",
    "form_difference",
    "home_goals_scored_last5",
    "home_goals_conceded_last5",
    "away_goals_scored_last5",
    "away_goals_conceded_last5",
    "home_shots_last5",
    "away_shots_last5",
    "home_shots_target_last5",
    "away_shots_target_last5",
    "home_elo",
    "away_elo",
    "elo_difference",
]


def average(values):
    if not values:
        return 0.0

    return sum(values) / len(values)


def expected_score(team_rating, opponent_rating):
    return 1.0 / (
        1.0
        + 10 ** (
            (opponent_rating - team_rating) / 400.0
        )
    )


def result_points(result):
    if result == "H":
        return 3, 0

    if result == "D":
        return 1, 1

    if result == "A":
        return 0, 3

    raise ValueError(
        f"Неизвестный результат матча: {result}"
    )


def result_scores(result):
    if result == "H":
        return 1.0, 0.0

    if result == "D":
        return 0.5, 0.5

    if result == "A":
        return 0.0, 1.0

    raise ValueError(
        f"Неизвестный результат матча: {result}"
    )


def load_all_matches():
    all_matches = []
    page_size = 1000
    start = 0

    while True:
        response = (
            supabase
            .table("matches")
            .select("*")
            .range(start, start + page_size - 1)
            .execute()
        )

        batch = response.data or []

        if not batch:
            break

        all_matches.extend(batch)

        if len(batch) < page_size:
            break

        start += page_size

    if not all_matches:
        raise RuntimeError("Таблица matches пустая")

    df = pd.DataFrame(all_matches)

    df["match_date"] = pd.to_datetime(
        df["match_date"],
        errors="coerce"
    )

    df["match_time"] = (
        df["match_time"]
        .fillna("00:00")
        .astype(str)
    )

    df = df.sort_values(
        ["match_date", "match_time"]
    ).reset_index(drop=True)

    numeric_columns = [
        "home_goals",
        "away_goals",
        "home_shots",
        "away_shots",
        "home_shots_target",
        "away_shots_target",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)

    return df


def calculate_current_state(df):
    team_history = {}
    ratings = {}

    for _, row in df.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]
        result = row["result"]

        home_points, away_points = result_points(result)

        team_history.setdefault(
            home_team,
            []
        ).append({
            "points": home_points,
            "goals_scored": row["home_goals"],
            "goals_conceded": row["away_goals"],
            "shots": row["home_shots"],
            "shots_target": row["home_shots_target"],
        })

        team_history.setdefault(
            away_team,
            []
        ).append({
            "points": away_points,
            "goals_scored": row["away_goals"],
            "goals_conceded": row["home_goals"],
            "shots": row["away_shots"],
            "shots_target": row["away_shots_target"],
        })

        home_elo = ratings.get(
            home_team,
            INITIAL_ELO
        )

        away_elo = ratings.get(
            away_team,
            INITIAL_ELO
        )

        expected_home = expected_score(
            home_elo + HOME_ADVANTAGE,
            away_elo
        )

        expected_away = 1.0 - expected_home

        actual_home, actual_away = result_scores(
            result
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

    return team_history, ratings


def build_match_features(
    home_team,
    away_team,
    home_odds,
    draw_odds,
    away_odds,
):
    df = load_all_matches()

    known_teams = set(df["home_team"]) | set(df["away_team"])

    if home_team not in known_teams:
        raise ValueError(
            f"Команда не найдена: {home_team}"
        )

    if away_team not in known_teams:
        raise ValueError(
            f"Команда не найдена: {away_team}"
        )

    if home_team == away_team:
        raise ValueError(
            "Домашняя и гостевая команды должны отличаться"
        )

    odds = [home_odds, draw_odds, away_odds]

    if any(value <= 1 for value in odds):
        raise ValueError(
            "Коэффициенты должны быть больше 1"
        )

    team_history, ratings = calculate_current_state(df)

    home_history = team_history.get(
        home_team,
        []
    )[-LAST_MATCHES:]

    away_history = team_history.get(
        away_team,
        []
    )[-LAST_MATCHES:]

    home_last5_points = sum(
        match["points"]
        for match in home_history
    )

    away_last5_points = sum(
        match["points"]
        for match in away_history
    )

    home_elo = ratings.get(
        home_team,
        INITIAL_ELO
    )

    away_elo = ratings.get(
        away_team,
        INITIAL_ELO
    )

    values = {
        "home_odds": float(home_odds),
        "draw_odds": float(draw_odds),
        "away_odds": float(away_odds),

        "home_last5_points": home_last5_points,
        "away_last5_points": away_last5_points,
        "form_difference": (
            home_last5_points - away_last5_points
        ),

        "home_goals_scored_last5": average([
            match["goals_scored"]
            for match in home_history
        ]),
        "home_goals_conceded_last5": average([
            match["goals_conceded"]
            for match in home_history
        ]),
        "away_goals_scored_last5": average([
            match["goals_scored"]
            for match in away_history
        ]),
        "away_goals_conceded_last5": average([
            match["goals_conceded"]
            for match in away_history
        ]),

        "home_shots_last5": average([
            match["shots"]
            for match in home_history
        ]),
        "away_shots_last5": average([
            match["shots"]
            for match in away_history
        ]),

        "home_shots_target_last5": average([
            match["shots_target"]
            for match in home_history
        ]),
        "away_shots_target_last5": average([
            match["shots_target"]
            for match in away_history
        ]),

        "home_elo": home_elo,
        "away_elo": away_elo,
        "elo_difference": (
            home_elo
            + HOME_ADVANTAGE
            - away_elo
        ),
    }

    return pd.DataFrame(
        [values],
        columns=FEATURES
    )
