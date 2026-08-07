import argparse
import joblib
import numpy as np

from model_utils import build_match_features
from poisson_utils import calculate_markets


HOME_MODEL_PATH = "home_goals_model.pkl"
AWAY_MODEL_PATH = "away_goals_model.pkl"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Прогноз ожидаемых голов"
    )

    parser.add_argument("--home", required=True)
    parser.add_argument("--away", required=True)

    parser.add_argument(
        "--home-odds",
        type=float,
        required=True,
    )

    parser.add_argument(
        "--draw-odds",
        type=float,
        required=True,
    )

    parser.add_argument(
        "--away-odds",
        type=float,
        required=True,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    home_model = joblib.load(HOME_MODEL_PATH)
    away_model = joblib.load(AWAY_MODEL_PATH)

    features = build_match_features(
        home_team=args.home,
        away_team=args.away,
        home_odds=args.home_odds,
        draw_odds=args.draw_odds,
        away_odds=args.away_odds,
    )

    expected_home_goals = float(
        home_model.predict(features)[0]
    )

    expected_away_goals = float(
        away_model.predict(features)[0]
    )

    expected_home_goals = max(
        0.0,
        expected_home_goals,
    )

    expected_away_goals = max(
        0.0,
        expected_away_goals,
    )

    print(
        f"\nПрогноз голов: "
        f"{args.home} — {args.away}\n"
    )

    print(
        f"Ожидаемые голы {args.home}: "
        f"{expected_home_goals:.2f}"
    )

    print(
        f"Ожидаемые голы {args.away}: "
        f"{expected_away_goals:.2f}"
    )

    print(
        "Ожидаемый общий тотал: "
        f"{expected_home_goals + expected_away_goals:.2f}"
    )

    print(
        "Приблизительный счёт: "
        f"{int(np.rint(expected_home_goals))}:"
        f"{int(np.rint(expected_away_goals))}"
    )

    markets = calculate_markets(
        expected_home_goals,
        expected_away_goals,
    )

    print("\nВероятности исходов:")

    print(
        f"Победа {args.home}: "
        f"{markets['home_win_probability']:.2%}"
    )

    print(
        "Ничья: "
        f"{markets['draw_probability']:.2%}"
    )

    print(
        f"Победа {args.away}: "
        f"{markets['away_win_probability']:.2%}"
    )

    print("\nТотал 2.5:")

    print(
        "ТБ 2.5: "
        f"{markets['over_2_5_probability']:.2%}"
    )

    print(
        "ТМ 2.5: "
        f"{markets['under_2_5_probability']:.2%}"
    )

    print("\nОбе забьют:")

    print(
        "Да: "
        f"{markets['btts_yes_probability']:.2%}"
    )

    print(
        "Нет: "
        f"{markets['btts_no_probability']:.2%}"
    )

    print("\nСамые вероятные счета:")

    for score in markets["top_scores"]:
        print(
            f"{score['home_goals']}:"
            f"{score['away_goals']} — "
            f"{score['probability']:.2%}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Ошибка:", error)
        raise SystemExit(1)
