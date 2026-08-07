VALUE_THRESHOLD = 0.05
SMALL_EDGE_THRESHOLD = 0.02


def classify_value(expected_roi):
    if expected_roi >= VALUE_THRESHOLD:
        return "VALUE"

    if expected_roi >= SMALL_EDGE_THRESHOLD:
        return "SMALL_EDGE"

    return "PASS"


def evaluate_market(
    name,
    model_probability,
    odds,
    group,
):
    model_probability = float(model_probability)
    odds = float(odds)

    if not 0.0 <= model_probability <= 1.0:
        raise ValueError(
            f"Вероятность рынка '{name}' должна быть от 0 до 1."
        )

    if odds <= 1.0:
        raise ValueError(
            f"Коэффициент рынка '{name}' должен быть больше 1."
        )

    raw_bookmaker_probability = 1.0 / odds

    expected_roi = (
        model_probability * odds
        - 1.0
    )

    edge_raw = (
        model_probability
        - raw_bookmaker_probability
    )

    return {
        "name": name,
        "group": group,
        "model_probability": model_probability,
        "bookmaker_probability_raw": (
            raw_bookmaker_probability
        ),
        "odds": odds,
        "edge_raw": edge_raw,
        "expected_roi": expected_roi,
        "status": classify_value(expected_roi),
    }


def calculate_market_values(markets):
    results = []

    for market in markets:
        results.append(
            evaluate_market(
                name=market["name"],
                group=market["group"],
                model_probability=(
                    market["model_probability"]
                ),
                odds=market["odds"],
            )
        )

    results.sort(
        key=lambda item: item["expected_roi"],
        reverse=True,
    )

    value_bets = [
        item
        for item in results
        if item["status"] != "PASS"
    ]

    return {
        "markets": results,
        "value_bets": value_bets,
        "best_market": (
            results[0]
            if results
            else None
        ),
    }
