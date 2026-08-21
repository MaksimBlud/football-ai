from pathlib import Path
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent

INPUT_FILE = (
    ROOT
    / "experiments"
    / "challenger_walk_forward_predictions.csv"
)

OUTPUT_FILE = (
    ROOT
    / "experiments"
    / "value_edge_calibration.csv"
)


df = pd.read_csv(INPUT_FILE)


odds = df[
    [
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
].to_numpy(dtype=float)

book = 1.0 / odds

book = (
    book
    / book.sum(
        axis=1,
        keepdims=True,
    )
)


model = df[
    [
        "p_home",
        "p_draw",
        "p_away",
    ]
].to_numpy(dtype=float)

model = (
    model
    / model.sum(
        axis=1,
        keepdims=True,
    )
)


rows = []


for i, row in df.iterrows():

    actual = int(
        row["actual"]
    )

    for side_id, side in enumerate(
        [
            "HOME",
            "DRAW",
            "AWAY",
        ]
    ):

        mp = model[i, side_id]
        bp = book[i, side_id]

        rows.append({
            "season":
                row["season"],

            "side":
                side,

            "model_probability":
                mp,

            "book_probability":
                bp,

            "edge":
                mp - bp,

            "actual_win":
                int(
                    actual
                    == side_id
                ),

            "odds":
                odds[i, side_id],
        })


bets = pd.DataFrame(
    rows
)


# ============================================================
# EDGE BUCKETS
# ============================================================

bins = [
    -1.0,
    -0.10,
    -0.07,
    -0.05,
    -0.03,
    -0.02,
    -0.01,
     0.00,
     0.01,
     0.02,
     0.03,
     0.05,
     0.07,
     0.10,
     1.0,
]

labels = [
    "<-10%",
    "-10:-7%",
    "-7:-5%",
    "-5:-3%",
    "-3:-2%",
    "-2:-1%",
    "-1:0%",
    "0:1%",
    "1:2%",
    "2:3%",
    "3:5%",
    "5:7%",
    "7:10%",
    "10%+",
]


bets["edge_bucket"] = pd.cut(
    bets["edge"],
    bins=bins,
    labels=labels,
    include_lowest=True,
)


def summarize(group):

    n = len(group)

    actual_rate = (
        group[
            "actual_win"
        ].mean()
    )

    model_p = (
        group[
            "model_probability"
        ].mean()
    )

    book_p = (
        group[
            "book_probability"
        ].mean()
    )

    profit = np.where(
        group["actual_win"] == 1,
        group["odds"] - 1.0,
        -1.0,
    ).sum()

    return pd.Series({
        "bets":
            n,

        "avg_model_probability":
            model_p,

        "avg_book_probability":
            book_p,

        "avg_edge":
            group["edge"].mean(),

        "actual_win_rate":
            actual_rate,

        "model_calibration_error":
            actual_rate - model_p,

        "book_calibration_error":
            actual_rate - book_p,

        "roi":
            profit / n,
    })


summary = (
    bets
    .groupby(
        "edge_bucket",
        observed=True,
    )
    .apply(
        summarize,
        include_groups=False,
    )
    .reset_index()
)


print("=" * 125)
print("VALUE EDGE — CALIBRATION BY EDGE")
print("=" * 125)

print(
    summary.to_string(
        index=False,
        formatters={
            "avg_model_probability":
                lambda x: f"{x:.3%}",

            "avg_book_probability":
                lambda x: f"{x:.3%}",

            "avg_edge":
                lambda x: f"{x:+.3%}",

            "actual_win_rate":
                lambda x: f"{x:.3%}",

            "model_calibration_error":
                lambda x: f"{x:+.3%}",

            "book_calibration_error":
                lambda x: f"{x:+.3%}",

            "roi":
                lambda x: f"{x:+.2%}",
        },
    )
)


# ============================================================
# POSITIVE EDGE BY SIDE
# ============================================================

positive = bets[
    bets["edge"] > 0
].copy()


print()
print("=" * 125)
print("POSITIVE EDGE — BY SIDE")
print("=" * 125)


side_summary = (
    positive
    .groupby("side")
    .apply(
        summarize,
        include_groups=False,
    )
    .reset_index()
)

print(
    side_summary.to_string(
        index=False,
        formatters={
            "avg_model_probability":
                lambda x: f"{x:.3%}",

            "avg_book_probability":
                lambda x: f"{x:.3%}",

            "avg_edge":
                lambda x: f"{x:+.3%}",

            "actual_win_rate":
                lambda x: f"{x:.3%}",

            "model_calibration_error":
                lambda x: f"{x:+.3%}",

            "book_calibration_error":
                lambda x: f"{x:+.3%}",

            "roi":
                lambda x: f"{x:+.2%}",
        },
    )
)


# ============================================================
# LARGE EDGE ONLY
# ============================================================

print()
print("=" * 125)
print("EDGE >= 5% — BY SIDE")
print("=" * 125)


large = bets[
    bets["edge"] >= 0.05
].copy()


large_summary = (
    large
    .groupby("side")
    .apply(
        summarize,
        include_groups=False,
    )
    .reset_index()
)

print(
    large_summary.to_string(
        index=False,
        formatters={
            "avg_model_probability":
                lambda x: f"{x:.3%}",

            "avg_book_probability":
                lambda x: f"{x:.3%}",

            "avg_edge":
                lambda x: f"{x:+.3%}",

            "actual_win_rate":
                lambda x: f"{x:.3%}",

            "model_calibration_error":
                lambda x: f"{x:+.3%}",

            "book_calibration_error":
                lambda x: f"{x:+.3%}",

            "roi":
                lambda x: f"{x:+.2%}",
        },
    )
)


summary.to_csv(
    OUTPUT_FILE,
    index=False,
)


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print(
    "Production-файлы НЕ изменены."
)
