VALUE_THRESHOLD = 0.05
SMALL_EDGE_THRESHOLD = 0.02


def normalized_bookmaker_probabilities(
    home_odds,
    draw_odds,
    away_odds,
):
    odds = [
        float(home_odds),
        float(draw_odds),
        float(away_odds),
    ]

    if any(odd <= 1.0 for odd in odds):
        raise ValueError(
            "Все коэффициенты должны быть больше 1."
        )

    raw_probabilities = [
        1.0 / odd
        for odd in odds
    ]

    margin_sum = sum(raw_probabilities)

    return {
        "home": raw_probabilities[0] / margin_sum,
        "draw": raw_probabilities[1] / margin_sum,
        "away": raw_probabilities[2] / margin_sum,
        "bookmaker_margin": margin_sum - 1.0,
    }


def value_status(edge):
    if edge >= VALUE_THRESHOLD:
        return "VALUE"

    if edge >= SMALL_EDGE_THRESHOLD:
        return "SMALL_EDGE"

    return "PASS"


def evaluate_outcome(
    name,
    model_probability,
    bookmaker_probability,
    odds,
):
    model_probability = float(model_probability)
    bookmaker_probability = float(
        bookmaker_probability
    )
    odds = float(odds)

    edge = (
        model_probability
        - bookmaker_probability
    )

    expected_roi = (
        model_probability * odds
        - 1.0
    )

    return {
        "name": name,
        "model_probability": model_probability,
        "bookmaker_probability": bookmaker_probability,
        "edge": edge,
        "expected_roi": expected_roi,
        "odds": odds,
        "status": value_status(edge),
    }


def calculate_1x2_value(
    home_team,
    away_team,
    home_probability,
    draw_probability,
    away_probability,
    home_odds,
    draw_odds,
    away_odds,
):
    bookmaker = normalized_bookmaker_probabilities(
        home_odds=home_odds,
        draw_odds=draw_odds,
        away_odds=away_odds,
    )

    outcomes = [
        evaluate_outcome(
            name=f"Победа {home_team}",
            model_probability=home_probability,
            bookmaker_probability=bookmaker["home"],
            odds=home_odds,
        ),
        evaluate_outcome(
            name="Ничья",
            model_probability=draw_probability,
            bookmaker_probability=bookmaker["draw"],
            odds=draw_odds,
        ),
        evaluate_outcome(
            name=f"Победа {away_team}",
            model_probability=away_probability,
            bookmaker_probability=bookmaker["away"],
            odds=away_odds,
        ),
    ]

    outcomes.sort(
        key=lambda item: item["expected_roi"],
        reverse=True,
    )

    return {
        "bookmaker_margin": bookmaker["bookmaker_margin"],
        "outcomes": outcomes,
        "best_outcome": outcomes[0],
    }
