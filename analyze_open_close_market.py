from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss


ROOT = Path(__file__).resolve().parent

DATA_DIR = (
    ROOT
    / "data"
    / "external"
    / "football_data_odds"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "open_close_market_analysis.csv"
)

OUTPUT_FILE.parent.mkdir(
    exist_ok=True
)


SEASONS = {
    "2019/2020": "1920",
    "2020/2021": "2021",
    "2021/2022": "2122",
    "2022/2023": "2223",
    "2023/2024": "2324",
    "2024/2025": "2425",
}


MARKETS = {
    "pinnacle": {
        "open": [
            "PSH",
            "PSD",
            "PSA",
        ],
        "close": [
            "PSCH",
            "PSCD",
            "PSCA",
        ],
    },

    "bet365": {
        "open": [
            "B365H",
            "B365D",
            "B365A",
        ],
        "close": [
            "B365CH",
            "B365CD",
            "B365CA",
        ],
    },

    "average": {
        "open": [
            "AvgH",
            "AvgD",
            "AvgA",
        ],
        "close": [
            "AvgCH",
            "AvgCD",
            "AvgCA",
        ],
    },

    "maximum": {
        "open": [
            "MaxH",
            "MaxD",
            "MaxA",
        ],
        "close": [
            "MaxCH",
            "MaxCD",
            "MaxCA",
        ],
    },
}


TARGET_MAP = {
    "H": 0,
    "D": 1,
    "A": 2,
}


def odds_to_probs(df, cols):
    odds = (
        df[cols]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
        .to_numpy(
            dtype=float
        )
    )

    valid = (
        np.isfinite(odds).all(axis=1)
        & (odds > 1.0).all(axis=1)
    )

    probs = np.full(
        odds.shape,
        np.nan,
        dtype=float,
    )

    implied = (
        1.0
        / odds[valid]
    )

    probs[valid] = (
        implied
        / implied.sum(
            axis=1,
            keepdims=True,
        )
    )

    return probs, valid


def multiclass_brier(
    y_true,
    probs,
):
    onehot = np.eye(3)[
        y_true
    ]

    return float(
        np.mean(
            np.sum(
                (
                    probs
                    - onehot
                ) ** 2,
                axis=1,
            )
        )
    )


rows = []


print("=" * 120)
print(
    "FOOTBALL AI — "
    "OPENING VS CLOSING MARKET"
)
print("=" * 120)


for season, code in SEASONS.items():

    path = (
        DATA_DIR
        / f"EPL_{code}.csv"
    )

    df = pd.read_csv(
        path
    )

    y = (
        df["FTR"]
        .map(TARGET_MAP)
    )

    print()
    print("=" * 120)
    print(season)
    print("=" * 120)

    for market_name, spec in MARKETS.items():

        open_probs, open_valid = (
            odds_to_probs(
                df,
                spec["open"],
            )
        )

        close_probs, close_valid = (
            odds_to_probs(
                df,
                spec["close"],
            )
        )

        valid = (
            y.notna().to_numpy()
            & open_valid
            & close_valid
        )

        yy = (
            y.to_numpy()[valid]
            .astype(int)
        )

        po = open_probs[
            valid
        ]

        pc = close_probs[
            valid
        ]

        if len(yy) == 0:
            print(
                f"{market_name:<10} "
                "NO VALID ROWS"
            )
            continue

        open_ll = log_loss(
            yy,
            po,
            labels=[
                0,
                1,
                2,
            ],
        )

        close_ll = log_loss(
            yy,
            pc,
            labels=[
                0,
                1,
                2,
            ],
        )

        open_acc = accuracy_score(
            yy,
            np.argmax(
                po,
                axis=1,
            ),
        )

        close_acc = accuracy_score(
            yy,
            np.argmax(
                pc,
                axis=1,
            ),
        )

        open_brier = (
            multiclass_brier(
                yy,
                po,
            )
        )

        close_brier = (
            multiclass_brier(
                yy,
                pc,
            )
        )

        ll_edge = (
            open_ll
            - close_ll
        )

        brier_edge = (
            open_brier
            - close_brier
        )

        print(
            f"{market_name:<10} "
            f"N={len(yy):>3} | "
            f"OPEN LL={open_ll:.6f} | "
            f"CLOSE LL={close_ll:.6f} | "
            f"EDGE={ll_edge:+.6f}"
        )

        rows.append({
            "season": season,
            "market": market_name,
            "matches": len(yy),

            "open_accuracy":
                open_acc,

            "close_accuracy":
                close_acc,

            "open_logloss":
                open_ll,

            "close_logloss":
                close_ll,

            "logloss_edge":
                ll_edge,

            "open_brier":
                open_brier,

            "close_brier":
                close_brier,

            "brier_edge":
                brier_edge,
        })


result = pd.DataFrame(
    rows
)

result.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("=" * 120)
print(
    "OVERALL WEIGHTED RESULTS"
)
print("=" * 120)


summary_rows = []

for market, group in result.groupby(
    "market"
):

    n = group[
        "matches"
    ].sum()

    def weighted(col):
        return float(
            (
                group[col]
                * group["matches"]
            ).sum()
            / n
        )

    row = {
        "market": market,
        "matches": n,

        "open_accuracy":
            weighted(
                "open_accuracy"
            ),

        "close_accuracy":
            weighted(
                "close_accuracy"
            ),

        "open_logloss":
            weighted(
                "open_logloss"
            ),

        "close_logloss":
            weighted(
                "close_logloss"
            ),

        "logloss_edge":
            weighted(
                "logloss_edge"
            ),

        "open_brier":
            weighted(
                "open_brier"
            ),

        "close_brier":
            weighted(
                "close_brier"
            ),

        "brier_edge":
            weighted(
                "brier_edge"
            ),
    }

    summary_rows.append(
        row
    )


summary = (
    pd.DataFrame(
        summary_rows
    )
    .sort_values(
        "logloss_edge",
        ascending=False,
    )
)


print(
    summary.to_string(
        index=False
    )
)


print()
print("=" * 120)
print(
    "SEASON CONSISTENCY"
)
print("=" * 120)


for market in sorted(
    result["market"].unique()
):

    g = result[
        result["market"]
        == market
    ]

    positive = int(
        (
            g["logloss_edge"]
            > 0
        ).sum()
    )

    total = len(g)

    print(
        f"{market:<10}: "
        f"closing better "
        f"{positive}/{total} seasons"
    )


print()
print("=" * 120)
print("VERDICT")
print("=" * 120)


best = summary.iloc[0]

if (
    best["logloss_edge"] > 0
):
    print(
        "✅ Closing market содержит "
        "измеримый дополнительный signal."
    )

    print(
        f"Лучший источник: "
        f"{best['market']}"
    )

    print(
        f"LogLoss improvement: "
        f"{best['logloss_edge']:+.6f}"
    )

else:
    print(
        "❌ Closing market не оказался "
        "лучше opening market."
    )


print()
print(
    "Сохранено:"
)

print(
    OUTPUT_FILE
)

print()
print(
    "Production-файлы НЕ изменены."
)
