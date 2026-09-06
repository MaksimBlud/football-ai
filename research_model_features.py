"""Pure snapshot-based mirror of the current production football feature state.

This module intentionally performs no database reads. The formulas mirror ``model_utils``
so prospective research can freeze one historical DataFrame before inference instead of
calling ``load_all_matches`` a second time.
"""
from __future__ import annotations

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
    "home_venue_win_rate",
    "away_venue_win_rate",
    "home_venue_goals_scored",
    "away_venue_goals_scored",
]


def average(values):
    return sum(values) / len(values) if values else 0.0


def expected_score(team_rating, opponent_rating):
    return 1.0 / (1.0 + 10 ** ((opponent_rating - team_rating) / 400.0))


def result_points(result):
    if result == "H":
        return 3, 0
    if result == "D":
        return 1, 1
    if result == "A":
        return 0, 3
    raise ValueError(f"Unknown match result: {result}")


def result_scores(result):
    if result == "H":
        return 1.0, 0.0
    if result == "D":
        return 0.5, 0.5
    if result == "A":
        return 0.0, 1.0
    raise ValueError(f"Unknown match result: {result}")


def calculate_current_state(df):
    team_history = {}
    home_venue_history = {}
    away_venue_history = {}
    ratings = {}

    for _, row in df.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]
        result = row["result"]
        home_points, away_points = result_points(result)

        home_match = {
            "points": home_points,
            "win": 1 if result == "H" else 0,
            "goals_scored": row["home_goals"],
            "goals_conceded": row["away_goals"],
            "shots": row["home_shots"],
            "shots_target": row["home_shots_target"],
        }
        team_history.setdefault(home_team, []).append(home_match)
        home_venue_history.setdefault(home_team, []).append(home_match)

        away_match = {
            "points": away_points,
            "win": 1 if result == "A" else 0,
            "goals_scored": row["away_goals"],
            "goals_conceded": row["home_goals"],
            "shots": row["away_shots"],
            "shots_target": row["away_shots_target"],
        }
        team_history.setdefault(away_team, []).append(away_match)
        away_venue_history.setdefault(away_team, []).append(away_match)

        home_elo = ratings.get(home_team, INITIAL_ELO)
        away_elo = ratings.get(away_team, INITIAL_ELO)
        expected_home = expected_score(home_elo + HOME_ADVANTAGE, away_elo)
        expected_away = 1.0 - expected_home
        actual_home, actual_away = result_scores(result)
        ratings[home_team] = home_elo + K_FACTOR * (actual_home - expected_home)
        ratings[away_team] = away_elo + K_FACTOR * (actual_away - expected_away)

    return team_history, home_venue_history, away_venue_history, ratings
