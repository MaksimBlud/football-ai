import argparse
import pandas as pd

from database import supabase


OFFICIAL_FILE = (
    "data/pl_official_history_2016_2026.csv"
)

NAME_MAP = {
    "Cardiff City": "Cardiff",
    "Huddersfield Town": "Huddersfield",
    "Hull City": "Hull",
    "Leeds United": "Leeds",
    "Norwich City": "Norwich",
    "Stoke City": "Stoke",
    "Swansea City": "Swansea",
    "West Bromwich Albion": "West Brom",
}

STAT_COLUMNS = [
    "home_shots",
    "away_shots",
    "home_shots_target",
    "away_shots_target",
    "home_corners",
    "away_corners",
    "home_yellow",
    "away_yellow",
    "home_red",
    "away_red",
]


parser = argparse.ArgumentParser()

parser.add_argument(
    "--apply",
    action="store_true",
    help="Реально записать изменения в Supabase.",
)

args = parser.parse_args()


print("Загружаю Official...")

official = pd.read_csv(
    OFFICIAL_FILE
)

official["home_team"] = (
    official["home_team"]
    .replace(NAME_MAP)
)

official["away_team"] = (
    official["away_team"]
    .replace(NAME_MAP)
)

official["match_date"] = (
    pd.to_datetime(
        official["match_date"]
    )
    .dt.date
    .astype(str)
)


print("Загружаю Supabase...")

rows = []
start = 0
page_size = 1000

while True:
    end = start + page_size - 1

    result = (
        supabase
        .table("matches")
        .select("*")
        .range(start, end)
        .execute()
    )

    batch = result.data or []
    rows.extend(batch)

    if len(batch) < page_size:
        break

    start += page_size


db = pd.DataFrame(rows)

db["match_date"] = (
    pd.to_datetime(
        db["match_date"]
    )
    .dt.date
    .astype(str)
)


KEY = [
    "season",
    "match_date",
    "home_team",
    "away_team",
]

merged = official.merge(
    db,
    on=KEY,
    how="inner",
    suffixes=(
        "_official",
        "_db",
    ),
)

if len(merged) != 3800:
    raise RuntimeError(
        f"Ожидалось 3800 совпадений, "
        f"получено {len(merged)}."
    )


updates = []

for _, row in merged.iterrows():
    payload = {}

    for column in STAT_COLUMNS:
        official_value = row[
            f"{column}_official"
        ]

        db_value = row[
            f"{column}_db"
        ]

        if pd.isna(official_value):
            continue

        if official_value != db_value:
            payload[column] = int(
                official_value
            )

    if payload:
        updates.append(
            {
                "id": int(row["id"]),
                "season": row["season"],
                "match_date": row["match_date"],
                "home_team": row["home_team"],
                "away_team": row["away_team"],
                "payload": payload,
            }
        )


print()
print("=" * 80)
print("OFFICIAL HISTORY UPDATE")
print("=" * 80)

print(
    "Матчей будет обновлено:",
    len(updates),
)

print(
    "Режим:",
    "APPLY" if args.apply else "DRY-RUN",
)

print()


if not args.apply:
    for item in updates[:20]:
        print(
            item["id"],
            "|",
            item["season"],
            "|",
            item["home_team"],
            "—",
            item["away_team"],
            "|",
            item["payload"],
        )

    print()
    print(
        "DRY-RUN завершён. "
        "Supabase НЕ изменялся."
    )

else:
    for index, item in enumerate(
        updates,
        start=1,
    ):
        (
            supabase
            .table("matches")
            .update(
                item["payload"]
            )
            .eq(
                "id",
                item["id"],
            )
            .execute()
        )

        print(
            f"[{index}/{len(updates)}] "
            f"{item['home_team']} — "
            f"{item['away_team']}"
        )

    print()
    print(
        "Готово. Supabase обновлён."
    )
