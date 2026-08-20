from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parent
EXP = ROOT / "experiments"


checks = []


def add_check(name, verdict, metric, details):
    checks.append({
        "name": name,
        "verdict": verdict,
        "metric": metric,
        "details": details,
    })


# ============================================================
# 1. CHALLENGER VS BOOKMAKER
# ============================================================

path = EXP / "challenger_vs_bookmaker.csv"

if path.exists():
    df = pd.read_csv(path)

    model_ll = (
        df["model_logloss"] * df["matches"]
    ).sum() / df["matches"].sum()

    book_ll = (
        df["bookmaker_logloss"] * df["matches"]
    ).sum() / df["matches"].sum()

    edge = book_ll - model_ll

    verdict = (
        "PROMOTE"
        if edge > 0
        else "REJECT"
    )

    add_check(
        "Challenger vs bookmaker",
        verdict,
        edge,
        f"LogLoss edge={edge:+.6f}",
    )

else:
    add_check(
        "Challenger vs bookmaker",
        "HOLD",
        None,
        "result file missing",
    )


# ============================================================
# 2. RAW XG NESTED
# ============================================================

path = EXP / "nested_xg_blend_results.csv"

if path.exists():
    df = pd.read_csv(path)

    edge = df["edge"].mean()

    positive = int(
        (df["edge"] > 0).sum()
    )

    total = len(df)

    verdict = (
        "PROMOTE"
        if (
            edge > 0
            and positive >= 3
        )
        else "REJECT"
    )

    add_check(
        "Nested XG LAST10",
        verdict,
        edge,
        (
            f"mean edge={edge:+.6f}, "
            f"positive seasons={positive}/{total}"
        ),
    )

else:
    add_check(
        "Nested XG LAST10",
        "HOLD",
        None,
        "result file missing",
    )


# ============================================================
# 3. OPPONENT-ADJUSTED XG NESTED
# ============================================================

path = (
    EXP
    / "nested_adjusted_xg_blend_results.csv"
)

if path.exists():
    df = pd.read_csv(path)

    edge = df["edge"].mean()

    positive = int(
        (df["edge"] > 0).sum()
    )

    total = len(df)

    verdict = (
        "PROMOTE"
        if (
            edge > 0
            and positive >= 3
        )
        else "REJECT"
    )

    add_check(
        "Nested adjusted XG",
        verdict,
        edge,
        (
            f"mean edge={edge:+.6f}, "
            f"positive seasons={positive}/{total}"
        ),
    )

else:
    add_check(
        "Nested adjusted XG",
        "HOLD",
        None,
        "result file missing",
    )


# ============================================================
# 4. FEATURE GROUP SIGNAL
# ============================================================

path = EXP / "feature_group_signal_results.csv"

if path.exists():
    df = pd.read_csv(path)

    best = df.sort_values(
        "blend_logloss_edge",
        ascending=False,
    ).iloc[0]

    edge = float(
        best["blend_logloss_edge"]
    )

    alpha = float(
        best["best_model_weight"]
    )

    verdict = (
        "PROMOTE"
        if (
            edge > 0
            and alpha > 0
        )
        else "REJECT"
    )

    add_check(
        "Independent feature groups",
        verdict,
        edge,
        (
            f"best={best['group']}, "
            f"alpha={alpha:.2f}, "
            f"edge={edge:+.6f}"
        ),
    )

else:
    add_check(
        "Independent feature groups",
        "HOLD",
        None,
        "result file missing",
    )


# ============================================================
# 5. REST / CONGESTION SIGNAL
# ============================================================

path = EXP / "rest_congestion_signal_results.csv"

if path.exists():
    df = pd.read_csv(path)

    best = df.sort_values(
        "blend_logloss_edge",
        ascending=False,
    ).iloc[0]

    edge = float(
        best["blend_logloss_edge"]
    )

    alpha = float(
        best["best_model_weight"]
    )

    verdict = (
        "PROMOTE"
        if (
            edge > 0
            and alpha > 0
        )
        else "REJECT"
    )

    add_check(
        "Rest / congestion",
        verdict,
        edge,
        (
            f"best={best['feature_set']}, "
            f"alpha={alpha:.2f}, "
            f"edge={edge:+.6f}"
        ),
    )

else:
    add_check(
        "Rest / congestion",
        "HOLD",
        None,
        "result file missing",
    )


# ============================================================
# 6. WEIGHTED INJURY SIGNAL
# ============================================================

path = EXP / "weighted_injury_signal_results.csv"

if path.exists():
    df = pd.read_csv(path)

    best = df.sort_values(
        "blend_logloss_edge",
        ascending=False,
    ).iloc[0]

    edge = float(
        best["blend_logloss_edge"]
    )

    alpha = float(
        best["best_model_weight"]
    )

    verdict = (
        "PROMOTE"
        if (
            edge > 0
            and alpha > 0
        )
        else "REJECT"
    )

    add_check(
        "Weighted injuries",
        verdict,
        edge,
        (
            f"best={best['feature_set']}, "
            f"alpha={alpha:.2f}, "
            f"edge={edge:+.6f}"
        ),
    )

else:
    add_check(
        "Weighted injuries",
        "HOLD",
        None,
        "result file missing",
    )


# ============================================================
# MARKET MOVEMENT PREDICTABILITY
# ============================================================

path = EXP / "market_movement_predictability.csv"

if path.exists():
    df = pd.read_csv(path)

    summary = (
        df.groupby("model")
        .apply(
            lambda g: (
                g["edge_vs_open"]
                * g["matches"]
            ).sum()
            / g["matches"].sum()
        )
    )

    best_model = summary.idxmax()
    best_edge = float(summary.max())

    verdict = (
        "PROMOTE"
        if (
            best_model != "zero"
            and best_edge > 0
        )
        else "REJECT"
    )

    add_check(
        "Market movement predictability",
        verdict,
        best_edge,
        (
            f"best={best_model}, "
            f"edge={best_edge:+.6f}"
        ),
    )

else:
    add_check(
        "Market movement predictability",
        "HOLD",
        None,
        "result file missing",
    )


# ============================================================
# NESTED CLOSING SEGMENTS
# ============================================================

path = EXP / "nested_closing_edge_segments.csv"

if path.exists():
    df = pd.read_csv(path)

    valid = df.dropna(
        subset=["test_edge"]
    )

    if len(valid):
        total = valid[
            "test_matches"
        ].sum()

        edge = (
            (
                valid["test_edge"]
                * valid["test_matches"]
            ).sum()
            / total
        )

        positive = int(
            (
                valid["test_edge"] > 0
            ).sum()
        )

        verdict = (
            "PROMOTE"
            if (
                edge > 0
                and positive
                >= max(
                    2,
                    len(valid) - 1,
                )
            )
            else "REJECT"
        )

        add_check(
            "Nested closing segments",
            verdict,
            float(edge),
            (
                f"edge={edge:+.6f}, "
                f"positive={positive}/{len(valid)}"
            ),
        )

    else:
        add_check(
            "Nested closing segments",
            "HOLD",
            None,
            "no valid outer tests",
        )

else:
    add_check(
        "Nested closing segments",
        "HOLD",
        None,
        "result file missing",
    )


# ============================================================
# VALUE BET BACKTEST
# ============================================================

path = EXP / "value_bet_backtest_results.csv"

if path.exists():
    df = pd.read_csv(path)

    eligible = df[
        df["bets"] >= 50
    ].copy()

    if eligible.empty:
        eligible = df.copy()

    best = eligible.sort_values(
        "roi",
        ascending=False,
    ).iloc[0]

    roi = float(
        best["roi"]
    )

    positive = int(
        best["positive_seasons"]
    )

    seasons = int(
        best["season_count"]
    )

    verdict = (
        "PROMOTE"
        if (
            roi > 0
            and positive >= max(
                2,
                seasons - 1,
            )
        )
        else "REJECT"
    )

    add_check(
        "Value betting",
        verdict,
        roi,
        (
            f"threshold={best['threshold']:.1%}, "
            f"ROI={roi:+.2%}, "
            f"positive={positive}/{seasons}"
        ),
    )

else:
    add_check(
        "Value betting",
        "HOLD",
        None,
        "result file missing",
    )


# ============================================================
# MARKET CALIBRATION
# ============================================================

path = EXP / "market_calibrated_meta_model_results.csv"

if path.exists():
    df = pd.read_csv(path)

    candidates = []

    meta_edge = (
        (
            df["meta_edge_vs_book"]
            * df["matches"]
        ).sum()
        / df["matches"].sum()
    )

    meta_positive = int(
        (
            df["meta_edge_vs_book"] > 0
        ).sum()
    )

    candidates.append(
        (
            "meta",
            float(meta_edge),
            meta_positive,
        )
    )

    for alpha in [5, 10, 20]:

        col = f"blend_{alpha}_edge"

        edge = (
            (
                df[col]
                * df["matches"]
            ).sum()
            / df["matches"].sum()
        )

        positive = int(
            (
                df[col] > 0
            ).sum()
        )

        candidates.append(
            (
                f"blend_{alpha}%",
                float(edge),
                positive,
            )
        )

    best_name, best_edge, best_positive = max(
        candidates,
        key=lambda x: x[1],
    )

    verdict = (
        "PROMOTE"
        if (
            best_edge > 0
            and best_positive >= max(
                2,
                len(df) - 1,
            )
        )
        else "REJECT"
    )

    add_check(
        "Market calibration",
        verdict,
        best_edge,
        (
            f"best={best_name}, "
            f"edge={best_edge:+.6f}, "
            f"positive={best_positive}/{len(df)}"
        ),
    )

else:
    add_check(
        "Market calibration",
        "HOLD",
        None,
        "result file missing",
    )


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 110)
print("FOOTBALL AI — RESEARCH PROMOTION GATE")
print("=" * 110)

print(
    f"{'CHECK':<34}"
    f"{'VERDICT':<12}"
    f"DETAILS"
)

print("-" * 110)

for check in checks:
    print(
        f"{check['name']:<34}"
        f"{check['verdict']:<12}"
        f"{check['details']}"
    )


promote = sum(
    c["verdict"] == "PROMOTE"
    for c in checks
)

reject = sum(
    c["verdict"] == "REJECT"
    for c in checks
)

hold = sum(
    c["verdict"] == "HOLD"
    for c in checks
)


print()
print("=" * 110)
print("FINAL RESEARCH VERDICT")
print("=" * 110)

print("PROMOTE:", promote)
print("REJECT: ", reject)
print("HOLD:   ", hold)

print()


if promote > 0:
    print(
        "⚠️ Есть кандидаты PROMOTE."
    )
    print(
        "Перед изменением production "
        "нужна отдельная финальная проверка."
    )

elif hold > 0:
    print(
        "⚠️ HOLD — не хватает результатов "
        "для полного решения."
    )

else:
    print(
        "❌ NO PROMOTION"
    )
    print(
        "Ни одна текущая экспериментальная "
        "ветка не прошла promotion gate."
    )
    print(
        "Production baseline оставляем без изменений."
    )


print()
print(
    "Важно: PASSED = код успешно выполнился."
)
print(
    "PROMOTE/REJECT = научный результат эксперимента."
)
