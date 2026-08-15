from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from database import supabase
from the_odds_service import (
    get_epl_h2h_odds,
    aggregate_event_h2h,
)


OUTPUT = Path(
    "data/odds_snapshots/epl_h2h_snapshots.csv"
)

SUPABASE_TABLE = "odds_snapshots"

DB_COLUMNS = [
    "snapshot_time_utc",
    "event_id",
    "commence_time_utc",
    "home_team",
    "away_team",
    "bookmakers_count",
    "home_odds",
    "draw_odds",
    "away_odds",
    "home_probability",
    "draw_probability",
    "away_probability",
]


result = get_epl_h2h_odds()

events = result["events"]
quota = result["quota"]

snapshot_time = datetime.now(
    timezone.utc
).isoformat()

rows = []

for event in events:

    aggregated = aggregate_event_h2h(
        event
    )

    if aggregated is None:
        continue

    rows.append({
        "snapshot_time_utc": snapshot_time,
        "event_id": aggregated["event_id"],
        "commence_time_utc": aggregated[
            "commence_time"
        ],
        "home_team": aggregated["home_team"],
        "away_team": aggregated["away_team"],
        "bookmakers_count": aggregated[
            "bookmakers_count"
        ],
        "home_odds": aggregated["home_odds"],
        "draw_odds": aggregated["draw_odds"],
        "away_odds": aggregated["away_odds"],
        "home_probability": aggregated[
            "home_probability"
        ],
        "draw_probability": aggregated[
            "draw_probability"
        ],
        "away_probability": aggregated[
            "away_probability"
        ],
    })


if not rows:
    raise RuntimeError(
        "The Odds API не вернул пригодных EPL h2h odds."
    )


new_df = pd.DataFrame(rows)

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 1. ЛОКАЛЬНАЯ ИСТОРИЯ CSV
# ============================================================

if OUTPUT.exists():
    old_df = pd.read_csv(
        OUTPUT
    )

    combined = pd.concat(
        [
            old_df,
            new_df,
        ],
        ignore_index=True,
    )

else:
    combined = new_df.copy()


combined = combined.drop_duplicates(
    subset=[
        "snapshot_time_utc",
        "event_id",
    ],
    keep="last",
)


combined = combined.sort_values(
    [
        "snapshot_time_utc",
        "commence_time_utc",
        "home_team",
    ]
).reset_index(drop=True)


combined.to_csv(
    OUTPUT,
    index=False,
)


# ============================================================
# 2. ПОСТОЯННАЯ ИСТОРИЯ В SUPABASE
# ============================================================

db_rows = (
    new_df[DB_COLUMNS]
    .where(
        pd.notna(new_df[DB_COLUMNS]),
        None,
    )
    .to_dict(
        orient="records"
    )
)

inserted_count = 0

try:
    response = (
        supabase
        .table(SUPABASE_TABLE)
        .upsert(
            db_rows,
            on_conflict=(
                "snapshot_time_utc,event_id"
            ),
        )
        .execute()
    )

    inserted_count = len(
        response.data or []
    )

except Exception as e:
    print()
    print(
        "ОШИБКА сохранения в Supabase:"
    )
    print(
        type(e).__name__,
        str(e)[:1000],
    )
    print()
    print(
        "Локальный CSV уже сохранён."
    )
    raise


# ============================================================
# 3. ОТЧЁТ
# ============================================================

print()
print("=" * 72)
print("EPL ODDS SNAPSHOT СОХРАНЁН")
print("=" * 72)

print(
    "Snapshot UTC:",
    snapshot_time,
)

print(
    "Матчей в snapshot:",
    len(new_df),
)

print(
    "Всего строк локальной истории:",
    len(combined),
)

print(
    "Строк обработано Supabase:",
    inserted_count,
)

print(
    "Локальный файл:",
    OUTPUT,
)

print(
    "Supabase table:",
    SUPABASE_TABLE,
)

print()
print("Quota:")
print(
    " remaining:",
    quota["remaining"],
)
print(
    " used:",
    quota["used"],
)
print(
    " last_cost:",
    quota["last_cost"],
)

print()
print(
    new_df[
        [
            "home_team",
            "away_team",
            "bookmakers_count",
            "home_odds",
            "draw_odds",
            "away_odds",
            "home_probability",
            "draw_probability",
            "away_probability",
        ]
    ].to_string(
        index=False,
        formatters={
            "home_odds":
                lambda x: f"{x:.3f}",
            "draw_odds":
                lambda x: f"{x:.3f}",
            "away_odds":
                lambda x: f"{x:.3f}",
            "home_probability":
                lambda x: f"{x:.2%}",
            "draw_probability":
                lambda x: f"{x:.2%}",
            "away_probability":
                lambda x: f"{x:.2%}",
        },
    )
)
