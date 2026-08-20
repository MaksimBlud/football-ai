from pathlib import Path
from collections import defaultdict, deque

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent

INPUT_FILE = (
    ROOT
    / "data"
    / "features_with_elo.csv"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "features_with_rest_congestion.csv"
)


print("Загружаю features_with_elo.csv...")

df = pd.read_csv(INPUT_FILE)

df["match_date"] = pd.to_datetime(
    df["match_date"],
    errors="coerce",
)

df = df.sort_values(
    [
        "match_date",
        "match_time",
        "home_team",
        "away_team",
    ]
).reset_index(drop=True)


# ============================================================
# TEAM HISTORY
#
# Для каждого клуба храним даты ПРЕДЫДУЩИХ матчей.
# Текущий матч добавляется только ПОСЛЕ расчёта features,
# поэтому leakage здесь нет.
# ============================================================

team_dates = defaultdict(
    lambda: deque(maxlen=50)
)


rows = []


def rest_days(history, current_date):
    if not history:
        return np.nan

    delta = (
        current_date
        - history[-1]
    ).days

    return float(delta)


def count_recent(
    history,
    current_date,
    days,
):
    cutoff = (
        current_date
        - pd.Timedelta(days=days)
    )

    return int(
        sum(
            date >= cutoff
            for date in history
        )
    )


print(
    "Рассчитываю rest/congestion "
    "до каждого матча..."
)


for _, row in df.iterrows():

    current_date = row["match_date"]

    home = row["home_team"]
    away = row["away_team"]

    home_history = team_dates[home]
    away_history = team_dates[away]


    home_rest = rest_days(
        home_history,
        current_date,
    )

    away_rest = rest_days(
        away_history,
        current_date,
    )


    home_last7 = count_recent(
        home_history,
        current_date,
        7,
    )

    away_last7 = count_recent(
        away_history,
        current_date,
        7,
    )


    home_last14 = count_recent(
        home_history,
        current_date,
        14,
    )

    away_last14 = count_recent(
        away_history,
        current_date,
        14,
    )


    # congestion = лишние матчи сверх
    # одного обычного матча за 7 дней.
    home_congestion_7 = max(
        home_last7 - 1,
        0,
    )

    away_congestion_7 = max(
        away_last7 - 1,
        0,
    )


    # За 14 дней считаем нормой два матча.
    home_congestion_14 = max(
        home_last14 - 2,
        0,
    )

    away_congestion_14 = max(
        away_last14 - 2,
        0,
    )


    rows.append({
        "home_rest_days":
            home_rest,

        "away_rest_days":
            away_rest,

        "rest_days_difference":
            (
                home_rest - away_rest
                if (
                    not np.isnan(home_rest)
                    and not np.isnan(away_rest)
                )
                else np.nan
            ),

        "home_matches_last7":
            home_last7,

        "away_matches_last7":
            away_last7,

        "matches_last7_difference":
            home_last7
            - away_last7,

        "home_matches_last14":
            home_last14,

        "away_matches_last14":
            away_last14,

        "matches_last14_difference":
            home_last14
            - away_last14,

        "home_congestion_last7":
            home_congestion_7,

        "away_congestion_last7":
            away_congestion_7,

        "congestion_last7_difference":
            home_congestion_7
            - away_congestion_7,

        "home_congestion_last14":
            home_congestion_14,

        "away_congestion_last14":
            away_congestion_14,

        "congestion_last14_difference":
            home_congestion_14
            - away_congestion_14,
    })


    # Только теперь текущий матч становится историей.
    team_dates[home].append(
        current_date
    )

    team_dates[away].append(
        current_date
    )


features = pd.DataFrame(
    rows
)


result = pd.concat(
    [
        df.reset_index(drop=True),
        features,
    ],
    axis=1,
)


result.to_csv(
    OUTPUT_FILE,
    index=False,
)


new_cols = features.columns.tolist()


print()
print("=" * 100)
print("REST / CONGESTION FEATURES CREATED")
print("=" * 100)

print("Строк:", len(result))
print(
    "Новых признаков:",
    len(new_cols),
)

print()

for col in new_cols:

    filled = result[
        col
    ].notna().sum()

    print(
        f"{col:35} "
        f"{filled}/{len(result)}"
    )


print()
print("По сезонам — полная заполненность:")

complete = result[
    new_cols
].notna().all(
    axis=1
)

print(
    result.assign(
        complete=complete
    )
    .groupby("season")[
        "complete"
    ]
    .agg([
        "count",
        "sum",
        "mean",
    ])
    .to_string()
)


print()
print("=" * 100)
print("SANITY CHECK")
print("=" * 100)

print(
    result[
        [
            "season",
            "match_date",
            "home_team",
            "away_team",
            "home_rest_days",
            "away_rest_days",
            "home_matches_last7",
            "away_matches_last7",
            "home_matches_last14",
            "away_matches_last14",
        ]
    ]
    .tail(10)
    .to_string(index=False)
)


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
