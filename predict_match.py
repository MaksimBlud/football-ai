import argparse
from pathlib import Path

import joblib

from model_utils import build_match_features
from value_utils import calculate_1x2_value


MODEL_PATH = Path("football_model_xgboost_elo.pkl")

OUTCOME_NAMES = {
    0: "HOME",
    1: "DRAW",
    2: "AWAY",
}


def predict_match(
    home_team,
    away_team,
    home_odds,
    draw_odds,
    away_odds,
):
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Модель не найдена: {MODEL_PATH}"
        )

    model = joblib.load(MODEL_PATH)

    features = build_match_features(
        home_team=home_team,
        away_team=away_team,
        home_odds=home_odds,
        draw_odds=draw_odds,
        away_odds=away_odds,
    )

    probabilities = model.predict_proba(features)[0]
    prediction = int(model.predict(features)[0])

    value_analysis = calculate_1x2_value(
        home_team=home_team,
        away_team=away_team,
        home_probability=float(probabilities[0]),
        draw_probability=float(probabilities[1]),
        away_probability=float(probabilities[2]),
        home_odds=home_odds,
        draw_odds=draw_odds,
        away_odds=away_odds,
    )

    result = {
        "home_team": home_team,
        "away_team": away_team,
        "prediction": OUTCOME_NAMES[prediction],
        "home_probability": float(probabilities[0]),
        "draw_probability": float(probabilities[1]),
        "away_probability": float(probabilities[2]),
        "home_last5_points": int(features.iloc[0]["home_last5_points"]),
        "away_last5_points": int(features.iloc[0]["away_last5_points"]),
        "home_elo": float(features.iloc[0]["home_elo"]),
        "away_elo": float(features.iloc[0]["away_elo"]),
        "bookmaker_margin": float(
            value_analysis["bookmaker_margin"]
        ),
        "value_outcomes": value_analysis["outcomes"],
        "best_value": value_analysis["best_outcome"],
    }

    return result


def print_result(result):
    print()
    print(
        f"Прогноз: {result['home_team']} — "
        f"{result['away_team']}"
    )
    print()

    print(
        f"Победа {result['home_team']}: "
        f"{result['home_probability']:.2%}"
    )

    print(
        f"Ничья: "
        f"{result['draw_probability']:.2%}"
    )

    print(
        f"Победа {result['away_team']}: "
        f"{result['away_probability']:.2%}"
    )

    print()
    print("Данные модели:")
    print(
        f"Форма за 5 матчей: "
        f"{result['home_team']} {result['home_last5_points']} — "
        f"{result['away_last5_points']} {result['away_team']}"
    )
    print(
        f"Эло: "
        f"{result['home_team']} {result['home_elo']:.1f} — "
        f"{result['away_elo']:.1f} {result['away_team']}"
    )

    print()
    print(
        "Наиболее вероятный исход:",
        result["prediction"]
    )


def main():
    parser = argparse.ArgumentParser(
        description="Прогноз футбольного матча"
    )

    parser.add_argument(
        "--home",
        required=True,
        help="Домашняя команда",
    )

    parser.add_argument(
        "--away",
        required=True,
        help="Гостевая команда",
    )

    parser.add_argument(
        "--home-odds",
        type=float,
        required=True,
        help="Коэффициент на победу хозяев",
    )

    parser.add_argument(
        "--draw-odds",
        type=float,
        required=True,
        help="Коэффициент на ничью",
    )

    parser.add_argument(
        "--away-odds",
        type=float,
        required=True,
        help="Коэффициент на победу гостей",
    )

    args = parser.parse_args()

    try:
        result = predict_match(
            home_team=args.home,
            away_team=args.away,
            home_odds=args.home_odds,
            draw_odds=args.draw_odds,
            away_odds=args.away_odds,
        )

        print_result(result)

    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
    ) as error:
        raise SystemExit(
            f"Ошибка: {error}"
        ) from error


if __name__ == "__main__":
    main()
