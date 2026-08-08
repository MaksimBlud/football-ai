import pandas as pd

from predict_match_no_odds import predict_match_no_odds
from goal_prediction_no_odds import predict_goal_markets_no_odds


INPUT = "data/upcoming_matches.csv"
OUTPUT = "data/upcoming_round_predictions.csv"

MATCHES_PER_ROUND = 10

# Эти коэффициенты нужны только потому, что текущая
# goal-модель технически ожидает их на входе.
# В таблице тура они НЕ трактуются как реальные odds.
print("Загружаю ближайшие матчи...")

df = pd.read_csv(INPUT)

if df.empty:
    raise RuntimeError(
        "Файл upcoming_matches.csv пуст."
    )

df["match_date"] = pd.to_datetime(
    df["match_date"],
    errors="coerce",
)

df = df.dropna(
    subset=[
        "match_date",
        "match_time",
        "home_team",
        "away_team",
        "home_team_model",
        "away_team_model",
    ]
)

df = df.sort_values(
    [
        "match_date",
        "match_time",
        "home_team",
    ]
).reset_index(drop=True)

round_df = df.head(
    MATCHES_PER_ROUND
).copy()

results = []

print()
print("1X2: модель без букмекерских коэффициентов.")
print("Goal markets: предварительный расчёт.")
print()

for _, row in round_df.iterrows():
    home_team = row["home_team_model"]
    away_team = row["away_team_model"]

    print(
        f"Прогнозирую: "
        f"{row['home_team']} — {row['away_team']}"
    )

    match_result = predict_match_no_odds(
        home_team=home_team,
        away_team=away_team,
    )

    goal_result = predict_goal_markets_no_odds(
        home_team=home_team,
        away_team=away_team,
    )

    probabilities = {
        "HOME": match_result["home_probability"],
        "DRAW": match_result["draw_probability"],
        "AWAY": match_result["away_probability"],
    }

    poisson_probabilities = {
        "HOME": goal_result["home_win_probability"],
        "DRAW": goal_result["draw_probability"],
        "AWAY": goal_result["away_win_probability"],
    }

    confidence = max(probabilities.values())

    poisson_prediction = max(
        poisson_probabilities,
        key=poisson_probabilities.get,
    )

    model_agreement = (
        match_result["prediction"]
        == poisson_prediction
    )

    selected_poisson_probability = (
        poisson_probabilities[
            match_result["prediction"]
        ]
    )

    probability_difference = abs(
        confidence
        - selected_poisson_probability
    )

    # После калибровки 1X2 абсолютные вероятности
    # классификатора и Poisson нельзя сравнивать напрямую.
    # Poisson используем только для проверки направления.
    #
    # Walk-forward calibration:
    # CAL >= 60% -> hit rate около 71.7%
    # CAL >= 50% -> hit rate около 61.9%

    if (
        model_agreement
        and confidence >= 0.60
    ):
        prediction_strength = "STRONG"

    elif (
        model_agreement
        and confidence >= 0.50
    ):
        prediction_strength = "MEDIUM"

    else:
        prediction_strength = "WEAK"

    top_score = goal_result["top_scores"][0]

    results.append({
        "match_date": row["match_date"].date().isoformat(),
        "match_time": row["match_time"],

        "home_team": row["home_team"],
        "away_team": row["away_team"],

        "home_team_model": home_team,
        "away_team_model": away_team,

        "prediction": match_result["prediction"],

        "home_probability": match_result["home_probability"],
        "draw_probability": match_result["draw_probability"],
        "away_probability": match_result["away_probability"],

        "confidence": confidence,

        "poisson_prediction": poisson_prediction,
        "model_agreement": model_agreement,
        "poisson_selected_probability": (
            selected_poisson_probability
        ),
        "model_probability_difference": (
            probability_difference
        ),

        "prediction_strength": (
            prediction_strength
        ),

        "expected_home_goals": (
            goal_result["expected_home_goals"]
        ),
        "expected_away_goals": (
            goal_result["expected_away_goals"]
        ),
        "expected_total_goals": (
            goal_result["expected_total_goals"]
        ),

        "over_2_5_probability": (
            goal_result["over_2_5_probability"]
        ),
        "under_2_5_probability": (
            goal_result["under_2_5_probability"]
        ),

        "btts_yes_probability": (
            goal_result["btts_yes_probability"]
        ),
        "btts_no_probability": (
            goal_result["btts_no_probability"]
        ),

        "top_score": (
            f"{top_score['home_goals']}:"
            f"{top_score['away_goals']}"
        ),

        "top_score_probability": (
            top_score["probability"]
        ),

        "odds_used_for_1x2": False,
        "goal_markets_preliminary": True,
    })


results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    "confidence",
    ascending=False,
).reset_index(drop=True)

results_df.to_csv(
    OUTPUT,
    index=False,
)

print()
print("Готово.")
print("Матчей спрогнозировано:", len(results_df))
print("Создан файл:", OUTPUT)

print()
print(
    results_df[
        [
            "home_team",
            "away_team",
            "prediction",
            "confidence",
            "expected_total_goals",
            "over_2_5_probability",
            "btts_yes_probability",
            "top_score",
        ]
    ].to_string(
        index=False,
        formatters={
            "confidence": lambda x: f"{x:.1%}",
            "expected_total_goals": lambda x: f"{x:.2f}",
            "over_2_5_probability": lambda x: f"{x:.1%}",
            "btts_yes_probability": lambda x: f"{x:.1%}",
        },
    )
)
