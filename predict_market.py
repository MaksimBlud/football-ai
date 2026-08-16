import argparse

from value_utils import normalized_bookmaker_probabilities


OUTCOME_NAMES = {
    "home": "HOME",
    "draw": "DRAW",
    "away": "AWAY",
}


def predict_market(
    home_team,
    away_team,
    home_odds,
    draw_odds,
    away_odds,
):
    bookmaker = normalized_bookmaker_probabilities(
        home_odds=home_odds,
        draw_odds=draw_odds,
        away_odds=away_odds,
    )

    probabilities = {
        "home": bookmaker["home"],
        "draw": bookmaker["draw"],
        "away": bookmaker["away"],
    }

    best_side = max(
        probabilities,
        key=probabilities.get,
    )

    return {
        "home_team": home_team,
        "away_team": away_team,

        "prediction": OUTCOME_NAMES[
            best_side
        ],

        "home_probability": float(
            probabilities["home"]
        ),

        "draw_probability": float(
            probabilities["draw"]
        ),

        "away_probability": float(
            probabilities["away"]
        ),

        "bookmaker_margin": float(
            bookmaker["bookmaker_margin"]
        ),

        "probability_source": (
            "MARKET_NO_VIG"
        ),

        "odds": {
            "home": float(home_odds),
            "draw": float(draw_odds),
            "away": float(away_odds),
        },
    }


def print_result(result):
    print()
    print(
        result["home_team"],
        "-",
        result["away_team"],
    )

    print(
        "HOME:",
        f"{result['home_probability']:.2%}",
    )

    print(
        "DRAW:",
        f"{result['draw_probability']:.2%}",
    )

    print(
        "AWAY:",
        f"{result['away_probability']:.2%}",
    )

    print(
        "Prediction:",
        result["prediction"],
    )

    print(
        "Bookmaker margin:",
        f"{result['bookmaker_margin']:.2%}",
    )

    print(
        "Source:",
        result["probability_source"],
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "1X2 прогноз из нормализованных "
            "букмекерских коэффициентов."
        )
    )

    parser.add_argument(
        "--home",
        required=True,
    )

    parser.add_argument(
        "--away",
        required=True,
    )

    parser.add_argument(
        "--home-odds",
        required=True,
        type=float,
    )

    parser.add_argument(
        "--draw-odds",
        required=True,
        type=float,
    )

    parser.add_argument(
        "--away-odds",
        required=True,
        type=float,
    )

    args = parser.parse_args()

    result = predict_market(
        home_team=args.home,
        away_team=args.away,
        home_odds=args.home_odds,
        draw_odds=args.draw_odds,
        away_odds=args.away_odds,
    )

    print_result(result)


if __name__ == "__main__":
    main()
