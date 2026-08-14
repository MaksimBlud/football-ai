import numpy as np
import pandas as pd

from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    log_loss,
)

INPUT = "data/goal_markets_oos_predictions.csv"


def clip(values):
    return np.clip(
        values,
        1e-6,
        1 - 1e-6,
    )


def metrics(y, p):
    p = clip(p)

    return {
        "accuracy": accuracy_score(
            y,
            (p >= 0.5).astype(int),
        ),
        "brier": brier_score_loss(
            y,
            p,
        ),
        "log_loss": log_loss(
            y,
            np.column_stack([
                1 - p,
                p,
            ]),
            labels=[0, 1],
        ),
        "mean_probability": float(
            np.mean(p)
        ),
        "actual_rate": float(
            np.mean(y)
        ),
    }


def evaluate_market(
    df,
    market_name,
    probability_column,
    actual_column,
):
    seasons = sorted(
        df["season"].unique()
    )

    rows = []

    print()
    print("=" * 85)
    print(market_name)
    print("=" * 85)

    # Первый OOS-сезон используется как
    # первоначальная calibration history.
    for test_season in seasons[1:]:
        train = df[
            df["season"] < test_season
        ].copy()

        test = df[
            df["season"] == test_season
        ].copy()

        if train.empty or test.empty:
            continue

        x_train = (
            train[probability_column]
            .to_numpy()
        )

        y_train = (
            train[actual_column]
            .astype(int)
            .to_numpy()
        )

        x_test = (
            test[probability_column]
            .to_numpy()
        )

        y_test = (
            test[actual_column]
            .astype(int)
            .to_numpy()
        )

        # RAW
        raw_prob = x_test

        # SIGMOID / PLATT
        sigmoid = LogisticRegression(
            random_state=42,
        )

        sigmoid.fit(
            x_train.reshape(-1, 1),
            y_train,
        )

        sigmoid_prob = (
            sigmoid.predict_proba(
                x_test.reshape(-1, 1)
            )[:, 1]
        )

        # ISOTONIC
        isotonic = IsotonicRegression(
            out_of_bounds="clip",
        )

        isotonic.fit(
            x_train,
            y_train,
        )

        isotonic_prob = isotonic.predict(
            x_test
        )

        methods = {
            "RAW": raw_prob,
            "SIGMOID": sigmoid_prob,
            "ISOTONIC": isotonic_prob,
        }

        season_text = []

        for method, probabilities in methods.items():
            result = metrics(
                y_test,
                probabilities,
            )

            rows.append({
                "market": market_name,
                "season": test_season,
                "method": method,
                "matches": len(test),
                **result,
            })

            season_text.append(
                f"{method}: "
                f"Brier={result['brier']:.4f}, "
                f"LL={result['log_loss']:.4f}"
            )

        print(
            f"{test_season}: "
            + " | ".join(season_text)
        )

    results = pd.DataFrame(rows)

    print()
    print("Средние walk-forward результаты:")

    summary = (
        results
        .groupby("method")
        .agg(
            seasons=("season", "nunique"),
            matches=("matches", "sum"),
            accuracy=("accuracy", "mean"),
            brier=("brier", "mean"),
            log_loss=("log_loss", "mean"),
            mean_probability=(
                "mean_probability",
                "mean",
            ),
            actual_rate=(
                "actual_rate",
                "mean",
            ),
        )
        .sort_values("brier")
    )

    print(
        summary.to_string(
            float_format=lambda x: f"{x:.5f}"
        )
    )

    print()
    print(
        "Лучший по Brier:",
        summary.index[0],
    )

    return results


print("Загружаю OOS-прогнозы...")

df = pd.read_csv(INPUT)

df = df.sort_values(
    ["season"]
).reset_index(drop=True)

print(
    "OOS матчей:",
    len(df),
)

print(
    "Сезоны:",
    sorted(df["season"].unique()),
)


over_results = evaluate_market(
    df=df,
    market_name="OVER_2_5",
    probability_column="over_probability",
    actual_column="actual_over",
)

btts_results = evaluate_market(
    df=df,
    market_name="BTTS_YES",
    probability_column="btts_probability",
    actual_column="actual_btts",
)

all_results = pd.concat(
    [
        over_results,
        btts_results,
    ],
    ignore_index=True,
)

OUTPUT = (
    "data/goal_calibration_walk_forward_results.csv"
)

all_results.to_csv(
    OUTPUT,
    index=False,
)

print()
print("Сохранено:", OUTPUT)
print()
print(
    "Production-калибраторы НЕ изменялись."
)
