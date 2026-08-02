import pandas as pd

from database import supabase


OUTPUT = "data/features_engineered.csv"
LAST_MATCHES = 5


def average(values):
    if not values:
        return 0.0

    return sum(values) / len(values)


def load_matches():
    print("Загружаю матчи из Supabase...")

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

        print("Загружено:", len(all_matches))

        if len(batch) < page_size:
            break

        start += page_size

    if not all_matches:
        raise RuntimeError("Таблица matches пустая")

    df = pd.DataFrame(all_matches)

    print("Всего матчей загружено:", len(df))

    return df


def points_for_result(result, venue):
    if result in ("D", "DRAW"):
        return 1

    if result in ("H", "HOME"):
        return 3 if venue == "home" else 0

    if result in ("A", "AWAY"):
        return 3 if venue == "away" else 0

    raise ValueError(f"Неизвестный результат матча: {result}")


def build_features(df):
    print("Сортирую матчи...")

    df["match_date"] = pd.to_datetime(
        df["match_date"],
        errors="coerce"
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
        "home_corners",
        "away_corners",
        "home_yellow",
        "away_yellow",
        "home_red",
        "away_red"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)

    team_history = {}
    feature_rows = []

    print("Рассчитываю признаки до каждого матча...")

    for _, row in df.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]

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

        feature_rows.append({
            "match_date": row["match_date"],
            "match_time": row["match_time"],
            "home_team": home_team,
            "away_team": away_team,

            "home_last5_points": home_last5_points,
            "away_last5_points": away_last5_points,
            "form_difference": (
                home_last5_points
                - away_last5_points
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

            "home_corners_last5": average([
                match["corners"]
                for match in home_history
            ]),
            "away_corners_last5": average([
                match["corners"]
                for match in away_history
            ]),

            "home_yellow_last5": average([
                match["yellow"]
                for match in home_history
            ]),
            "away_yellow_last5": average([
                match["yellow"]
                for match in away_history
            ]),

            "home_odds": row["home_odds"],
            "draw_odds": row["draw_odds"],
            "away_odds": row["away_odds"],

            "result": row["result"],
            "home_goals": row["home_goals"],
            "away_goals": row["away_goals"]
        })

        home_match = {
            "points": points_for_result(
                row["result"],
                "home"
            ),
            "goals_scored": row["home_goals"],
            "goals_conceded": row["away_goals"],
            "shots": row["home_shots"],
            "shots_target": row["home_shots_target"],
            "corners": row["home_corners"],
            "yellow": row["home_yellow"]
        }

        away_match = {
            "points": points_for_result(
                row["result"],
                "away"
            ),
            "goals_scored": row["away_goals"],
            "goals_conceded": row["home_goals"],
            "shots": row["away_shots"],
            "shots_target": row["away_shots_target"],
            "corners": row["away_corners"],
            "yellow": row["away_yellow"]
        }

        team_history.setdefault(
            home_team,
            []
        ).append(home_match)

        team_history.setdefault(
            away_team,
            []
        ).append(away_match)

    features = pd.DataFrame(feature_rows)

    odds_columns = [
        "home_odds",
        "draw_odds",
        "away_odds"
    ]

    for column in odds_columns:
        features[column] = pd.to_numeric(
            features[column],
            errors="coerce"
        )

    raw_home_probability = 1 / features["home_odds"]
    raw_draw_probability = 1 / features["draw_odds"]
    raw_away_probability = 1 / features["away_odds"]

    probability_sum = (
        raw_home_probability
        + raw_draw_probability
        + raw_away_probability
    )

    features["home_probability"] = (
        raw_home_probability / probability_sum
    )

    features["draw_probability"] = (
        raw_draw_probability / probability_sum
    )

    features["away_probability"] = (
        raw_away_probability / probability_sum
    )

    features["home_away_probability_difference"] = (
        features["home_probability"]
        - features["away_probability"]
    )

    return features


def save_features(df):
    df.to_csv(
        OUTPUT,
        index=False
    )

    print("Создан файл:", OUTPUT)
    print("Строк:", len(df))
    print("Колонок:", len(df.columns))


if __name__ == "__main__":
    matches = load_matches()
    features = build_features(matches)
    save_features(features)
