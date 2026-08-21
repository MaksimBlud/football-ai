from database import supabase
import numpy as np
import pandas as pd


TABLE = "odds_snapshots"

rows = []
offset = 0
page_size = 1000

while True:
    response = (
        supabase
        .table(TABLE)
        .select("*")
        .order("snapshot_time_utc", desc=False)
        .range(
            offset,
            offset + page_size - 1,
        )
        .execute()
    )

    batch = response.data or []
    rows.extend(batch)

    if len(batch) < page_size:
        break

    offset += page_size


df = pd.DataFrame(rows)

if df.empty:
    raise SystemExit("❌ odds_snapshots пуст.")


df["snapshot_time_utc"] = pd.to_datetime(
    df["snapshot_time_utc"],
    utc=True,
    errors="coerce",
)

df["commence_time_utc"] = pd.to_datetime(
    df["commence_time_utc"],
    utc=True,
    errors="coerce",
)


# ============================================================
# FAIR MARKET PROBABILITIES
# ============================================================

odds = df[
    [
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
].to_numpy(dtype=float)

raw = 1.0 / odds

probs = (
    raw
    / raw.sum(
        axis=1,
        keepdims=True,
    )
)

df["p_home"] = probs[:, 0]
df["p_draw"] = probs[:, 1]
df["p_away"] = probs[:, 2]


# ============================================================
# SNAPSHOT NUMBER
# ============================================================

df = df.sort_values(
    [
        "event_id",
        "snapshot_time_utc",
    ]
).copy()

df["snapshot_number"] = (
    df.groupby("event_id")
    .cumcount()
    + 1
)


# ============================================================
# FINAL SNAPSHOT PER EVENT
# ============================================================

final = (
    df.groupby("event_id")
    .tail(1)
    [
        [
            "event_id",
            "snapshot_number",
            "snapshot_time_utc",
            "p_home",
            "p_draw",
            "p_away",
        ]
    ]
    .rename(
        columns={
            "snapshot_number":
                "final_snapshot_number",

            "snapshot_time_utc":
                "final_snapshot_time",

            "p_home":
                "final_p_home",

            "p_draw":
                "final_p_draw",

            "p_away":
                "final_p_away",
        }
    )
)


work = df.merge(
    final,
    on="event_id",
    how="left",
    validate="many_to_one",
)


# ============================================================
# DISTANCE TO CURRENT FINAL SNAPSHOT
# ============================================================

work["abs_diff_home"] = (
    work["p_home"]
    - work["final_p_home"]
).abs()

work["abs_diff_draw"] = (
    work["p_draw"]
    - work["final_p_draw"]
).abs()

work["abs_diff_away"] = (
    work["p_away"]
    - work["final_p_away"]
).abs()


work["mae_to_final"] = (
    work[
        [
            "abs_diff_home",
            "abs_diff_draw",
            "abs_diff_away",
        ]
    ].mean(axis=1)
)


work["max_diff_to_final"] = (
    work[
        [
            "abs_diff_home",
            "abs_diff_draw",
            "abs_diff_away",
        ]
    ].max(axis=1)
)


work["hours_to_kickoff"] = (
    (
        work["commence_time_utc"]
        - work["snapshot_time_utc"]
    )
    .dt.total_seconds()
    / 3600
)


print("=" * 120)
print("LIVE MARKET SNAPSHOT CONVERGENCE")
print("=" * 120)

print(
    "Events:",
    work["event_id"].nunique(),
)

print(
    "Snapshots:",
    len(work),
)

print(
    "Max snapshot number:",
    work["snapshot_number"].max(),
)


# ============================================================
# BY SNAPSHOT NUMBER
# ============================================================

print()
print("=" * 120)
print("CONVERGENCE BY SNAPSHOT NUMBER")
print("=" * 120)

summary = (
    work.groupby("snapshot_number")
    .agg(
        events=(
            "event_id",
            "nunique",
        ),

        avg_hours_to_kickoff=(
            "hours_to_kickoff",
            "mean",
        ),

        mean_mae_to_final=(
            "mae_to_final",
            "mean",
        ),

        median_mae_to_final=(
            "mae_to_final",
            "median",
        ),

        mean_max_diff_to_final=(
            "max_diff_to_final",
            "mean",
        ),
    )
    .reset_index()
)

print(
    summary.to_string(
        index=False,
        formatters={
            "avg_hours_to_kickoff":
                lambda x: f"{x:.1f}",

            "mean_mae_to_final":
                lambda x: f"{x:.4%}",

            "median_mae_to_final":
                lambda x: f"{x:.4%}",

            "mean_max_diff_to_final":
                lambda x: f"{x:.4%}",
        },
    )
)


# ============================================================
# INFORMATION GAIN PER STEP
# ============================================================

work["previous_mae"] = (
    work.groupby("event_id")[
        "mae_to_final"
    ].shift(1)
)

work["improvement_vs_previous"] = (
    work["previous_mae"]
    - work["mae_to_final"]
)


print()
print("=" * 120)
print("INFORMATION GAIN PER SNAPSHOT")
print("=" * 120)

gain = (
    work[
        work["snapshot_number"] > 1
    ]
    .groupby("snapshot_number")
    .agg(
        events=(
            "event_id",
            "nunique",
        ),

        avg_improvement=(
            "improvement_vs_previous",
            "mean",
        ),

        median_improvement=(
            "improvement_vs_previous",
            "median",
        ),

        improved_events=(
            "improvement_vs_previous",
            lambda x:
                int(
                    (x > 0).sum()
                ),
        ),
    )
    .reset_index()
)

print(
    gain.to_string(
        index=False,
        formatters={
            "avg_improvement":
                lambda x: f"{x:+.4%}",

            "median_improvement":
                lambda x: f"{x:+.4%}",
        },
    )
)


# ============================================================
# PER EVENT
# ============================================================

print()
print("=" * 120)
print("PER EVENT — FIRST VS CURRENT FINAL")
print("=" * 120)

first = (
    work.groupby("event_id")
    .head(1)
)

cols = [
    "home_team",
    "away_team",
    "snapshot_number",
    "final_snapshot_number",
    "hours_to_kickoff",
    "mae_to_final",
    "max_diff_to_final",
]

print(
    first[cols]
    .sort_values(
        "max_diff_to_final",
        ascending=False,
    )
    .to_string(
        index=False,
        formatters={
            "mae_to_final":
                lambda x: f"{x:.3%}",

            "max_diff_to_final":
                lambda x: f"{x:.3%}",

            "hours_to_kickoff":
                lambda x: f"{x:.1f}",
        },
    )
)


print()
print("=" * 120)
print("IMPORTANT")
print("=" * 120)

print(
    "Последний snapshot здесь является "
    "текущим последним наблюдением, "
    "а НЕ настоящим closing odds."
)

print(
    "После kickoff этот же анализ можно "
    "повторить уже относительно финального "
    "pre-match snapshot."
)

print()
print("Supabase только прочитан.")
print("Production-файлы НЕ изменены.")
