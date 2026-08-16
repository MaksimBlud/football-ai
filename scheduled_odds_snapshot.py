from datetime import datetime, timezone

from database import supabase


TABLE = "odds_snapshots"

NO_FUTURE_MATCH_COOLDOWN_HOURS = 24


def parse_dt(value):
    if not value:
        return None

    value = str(value).replace(
        "Z",
        "+00:00",
    )

    dt = datetime.fromisoformat(value)

    if dt.tzinfo is None:
        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return dt.astimezone(
        timezone.utc
    )


now = datetime.now(
    timezone.utc
)

response = (
    supabase
    .table(TABLE)
    .select(
        "snapshot_time_utc,"
        "commence_time_utc"
    )
    .order(
        "snapshot_time_utc",
        desc=True,
    )
    .limit(100)
    .execute()
)

rows = response.data or []

if not rows:
    print(
        "В Supabase нет snapshots."
    )
    print(
        "Запускаю первый snapshot."
    )

    should_run = True

else:
    snapshot_times = [
        parse_dt(
            row["snapshot_time_utc"]
        )
        for row in rows
        if row.get(
            "snapshot_time_utc"
        )
    ]

    commence_times = [
        parse_dt(
            row["commence_time_utc"]
        )
        for row in rows
        if row.get(
            "commence_time_utc"
        )
    ]

    last_snapshot = max(
        snapshot_times
    )

    future_matches = [
        dt
        for dt in commence_times
        if dt > now
    ]

    if not future_matches:
        hours_since_snapshot = (
            now - last_snapshot
        ).total_seconds() / 3600

        should_run = (
            hours_since_snapshot
            >= NO_FUTURE_MATCH_COOLDOWN_HOURS
        )

        print(
            "Будущих матчей в последних "
            "snapshot-данных нет."
        )

        print(
            "Последний snapshot:",
            last_snapshot.isoformat(),
        )

        print(
            "После snapshot, часов:",
            round(
                hours_since_snapshot,
                2,
            ),
        )

        print(
            "Cooldown поиска нового тура:",
            NO_FUTURE_MATCH_COOLDOWN_HOURS,
            "час.",
        )

        if should_run:
            print(
                "Cooldown истёк. "
                "Разрешён поиск новых odds."
            )
        else:
            print(
                "Cooldown ещё не истёк."
            )

    else:
        nearest_match = min(
            future_matches
        )

        hours_to_match = (
            nearest_match - now
        ).total_seconds() / 3600

        hours_since_snapshot = (
            now - last_snapshot
        ).total_seconds() / 3600

        if hours_to_match > 72:
            required_interval = 12

        elif hours_to_match > 24:
            required_interval = 6

        else:
            required_interval = 4

        should_run = (
            hours_since_snapshot
            >= required_interval
        )

        print(
            "UTC now:",
            now.isoformat(),
        )

        print(
            "Последний snapshot:",
            last_snapshot.isoformat(),
        )

        print(
            "Ближайший kickoff:",
            nearest_match.isoformat(),
        )

        print(
            "До матча, часов:",
            round(
                hours_to_match,
                2,
            ),
        )

        print(
            "После snapshot, часов:",
            round(
                hours_since_snapshot,
                2,
            ),
        )

        print(
            "Требуемый интервал:",
            required_interval,
            "час.",
        )


if not should_run:
    print()
    print(
        "Новый snapshot пока НЕ нужен."
    )
    print(
        "The Odds API НЕ вызывается."
    )

    raise SystemExit(0)


print()
print(
    "Snapshot требуется."
)
print(
    "Запускаю save_odds_snapshot.py..."
)

import subprocess
import sys

result = subprocess.run(
    [
        sys.executable,
        "save_odds_snapshot.py",
    ],
    check=False,
)

raise SystemExit(
    result.returncode
)
