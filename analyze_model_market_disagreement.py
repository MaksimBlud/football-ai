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
    / "model_market_disagreement.csv"
)


df = pd.read_csv(INPUT_FILE)


# ============================================================
# MODEL
# ============================================================

model_proba = df[
    ["p_home", "p_draw", "p_away"]
].to_numpy(dtype=np.float64)

model_proba = (
    model_proba
    / model_proba.sum(
        axis=1,
        keepdims=True,
    )
)


# ============================================================
# BOOKMAKER
# ============================================================

odds = df[
    ["home_odds", "draw_odds", "away_odds"]
].to_numpy(dtype=np.float64)

book_proba = 1.0 / odds

book_proba = (
    book_proba
    / book_proba.sum(
        axis=1,
        keepdims=True,
    )
)


actual = df[
    "actual"
].to_numpy(dtype=int)

model_pred = np.argmax(
    model_proba,
    axis=1,
)

book_pred = np.argmax(
    book_proba,
    axis=1,
)


# ============================================================
# DISAGREEMENT
# ============================================================

disagree = (
    model_pred
    != book_pred
)

disagree_count = int(
    disagree.sum()
)

agree_count = int(
    (~disagree).sum()
)


model_correct_disagree = int(
    (
        disagree
        & (model_pred == actual)
    ).sum()
)

book_correct_disagree = int(
    (
        disagree
        & (book_pred == actual)
    ).sum()
)

both_wrong_disagree = int(
    (
        disagree
        & (model_pred != actual)
        & (book_pred != actual)
    ).sum()
)


# ============================================================
# PROBABILITY DIFFERENCE
# ============================================================

model_selected_prob = model_proba[
    np.arange(len(df)),
    model_pred,
]

book_prob_for_model_pick = book_proba[
    np.arange(len(df)),
    model_pred,
]

edge = (
    model_selected_prob
    - book_prob_for_model_pick
)


out = df.copy()

out["model_pred"] = model_pred
out["book_pred"] = book_pred

out["model_selected_prob"] = (
    model_selected_prob
)

out["book_prob_for_model_pick"] = (
    book_prob_for_model_pick
)

out["model_edge"] = edge

out["disagree"] = disagree

out["model_correct"] = (
    model_pred == actual
)

out["book_correct"] = (
    book_pred == actual
)

out.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ============================================================
# EDGE BUCKETS
# ============================================================

bins = [
    -1.0,
    0.00,
    0.02,
    0.05,
    0.10,
    1.0,
]

labels = [
    "<=0",
    "0-2%",
    "2-5%",
    "5-10%",
    "10%+",
]

out["edge_bucket"] = pd.cut(
    out["model_edge"],
    bins=bins,
    labels=labels,
    include_lowest=True,
)


bucket_rows = []

for bucket, part in out[
    out["disagree"]
].groupby(
    "edge_bucket",
    observed=False,
):

    if len(part) == 0:
        continue

    bucket_rows.append({
        "edge_bucket":
            str(bucket),

        "matches":
            len(part),

        "model_accuracy":
            float(
                part["model_correct"].mean()
            ),

        "book_accuracy":
            float(
                part["book_correct"].mean()
            ),

        "model_minus_book":
            float(
                part["model_correct"].mean()
                - part["book_correct"].mean()
            ),

        "avg_model_edge":
            float(
                part["model_edge"].mean()
            ),
    })


bucket_df = pd.DataFrame(
    bucket_rows
)


# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 100)
print("MODEL VS MARKET DISAGREEMENT ANALYSIS")
print("=" * 100)

print()
print("Всего матчей:", len(df))
print("Совпали прогнозы:", agree_count)
print("Разошлись прогнозы:", disagree_count)

print()

if disagree_count > 0:

    print(
        "На матчах, где прогнозы РАЗОШЛИСЬ:"
    )

    print(
        "MODEL правильный:",
        model_correct_disagree,
        f"({model_correct_disagree / disagree_count:.4f})",
    )

    print(
        "BOOKMAKER правильный:",
        book_correct_disagree,
        f"({book_correct_disagree / disagree_count:.4f})",
    )

    print(
        "Оба ошиблись:",
        both_wrong_disagree,
        f"({both_wrong_disagree / disagree_count:.4f})",
    )

    print(
        "Разница MODEL - BOOK:",
        round(
            (
                model_correct_disagree
                - book_correct_disagree
            )
            / disagree_count,
            4,
        ),
    )


print()
print("=" * 100)
print("DISAGREEMENT BY MODEL EDGE")
print("=" * 100)

print(
    bucket_df.to_string(
        index=False
    )
)


print()
print("=" * 100)
print("BY MODEL PICK")
print("=" * 100)

label_map = {
    0: "HOME",
    1: "DRAW",
    2: "AWAY",
}

for cls in [0, 1, 2]:

    part = out[
        out["disagree"]
        & (out["model_pred"] == cls)
    ]

    if part.empty:
        continue

    print()
    print(label_map[cls])

    print(
        "Матчей:",
        len(part),
    )

    print(
        "MODEL accuracy:",
        round(
            part["model_correct"].mean(),
            4,
        ),
    )

    print(
        "BOOK accuracy:",
        round(
            part["book_correct"].mean(),
            4,
        ),
    )

    print(
        "Средний edge:",
        round(
            part["model_edge"].mean(),
            4,
        ),
    )


print()
print("Сохранено:")
print(OUTPUT_FILE)

print()
print("Production-файлы НЕ изменены.")
