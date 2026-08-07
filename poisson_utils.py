from math import exp, factorial


MAX_GOALS = 10


def poisson_probability(goals, expected_goals):
    return (
        exp(-expected_goals)
        * expected_goals ** goals
        / factorial(goals)
    )


def calculate_markets(
    expected_home_goals,
    expected_away_goals,
    max_goals=MAX_GOALS,
):
    score_probabilities = []

    home_win_probability = 0.0
    draw_probability = 0.0
    away_win_probability = 0.0

    over_2_5_probability = 0.0
    btts_probability = 0.0

    for home_goals in range(max_goals + 1):
        home_probability = poisson_probability(
            home_goals,
            expected_home_goals,
        )

        for away_goals in range(max_goals + 1):
            away_probability = poisson_probability(
                away_goals,
                expected_away_goals,
            )

            probability = (
                home_probability * away_probability
            )

            score_probabilities.append({
                "home_goals": home_goals,
                "away_goals": away_goals,
                "probability": probability,
            })

            if home_goals > away_goals:
                home_win_probability += probability
            elif home_goals == away_goals:
                draw_probability += probability
            else:
                away_win_probability += probability

            if home_goals + away_goals >= 3:
                over_2_5_probability += probability

            if home_goals > 0 and away_goals > 0:
                btts_probability += probability

    total_probability = sum(
        item["probability"]
        for item in score_probabilities
    )

    if total_probability <= 0:
        raise ValueError(
            "Не удалось рассчитать вероятности."
        )

    score_probabilities = [
        {
            **item,
            "probability": (
                item["probability"]
                / total_probability
            ),
        }
        for item in score_probabilities
    ]

    score_probabilities.sort(
        key=lambda item: item["probability"],
        reverse=True,
    )

    return {
        "home_win_probability": (
            home_win_probability
            / total_probability
        ),
        "draw_probability": (
            draw_probability
            / total_probability
        ),
        "away_win_probability": (
            away_win_probability
            / total_probability
        ),
        "over_2_5_probability": (
            over_2_5_probability
            / total_probability
        ),
        "under_2_5_probability": (
            1.0
            - over_2_5_probability
            / total_probability
        ),
        "btts_yes_probability": (
            btts_probability
            / total_probability
        ),
        "btts_no_probability": (
            1.0
            - btts_probability
            / total_probability
        ),
        "top_scores": score_probabilities[:5],
    }
