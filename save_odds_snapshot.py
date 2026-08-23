"""Collect and persist one EPL h2h odds snapshot.

Importing this module is side-effect free.

External operations occur only from main():
- The Odds API read;
- local CSV write;
- Supabase upsert.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from fixture_identity import require_league
from league_config import EPL
from the_odds_service import (
    aggregate_event_h2h,
    get_epl_h2h_odds,
)


OUTPUT = Path(
    "data/odds_snapshots/epl_h2h_snapshots.csv"
)

SUPABASE_TABLE = "odds_snapshots"

DB_CONFLICT_TARGET = (
    "league,snapshot_time_utc,event_id"
)

DB_COLUMNS = [
    "league",
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


def build_snapshot_rows(
    events,
    snapshot_time_utc: str,
) -> pd.DataFrame:
    """Build league-aware EPL snapshot rows without external writes."""

    rows = []

    for event in events:
        aggregated = aggregate_event_h2h(
            event
        )

        if aggregated is None:
            continue

        rows.append({
            "league":
                EPL.identifier,

            "snapshot_time_utc":
                snapshot_time_utc,

            "event_id":
                aggregated[
                    "event_id"
                ],

            "commence_time_utc":
                aggregated[
                    "commence_time"
                ],

            "home_team":
                aggregated[
                    "home_team"
                ],

            "away_team":
                aggregated[
                    "away_team"
                ],

            "bookmakers_count":
                aggregated[
                    "bookmakers_count"
                ],

            "home_odds":
                aggregated[
                    "home_odds"
                ],

            "draw_odds":
                aggregated[
                    "draw_odds"
                ],

            "away_odds":
                aggregated[
                    "away_odds"
                ],

            "home_probability":
                aggregated[
                    "home_probability"
                ],

            "draw_probability":
                aggregated[
                    "draw_probability"
                ],

            "away_probability":
                aggregated[
                    "away_probability"
                ],
        })

    return pd.DataFrame(
        rows,
        columns=DB_COLUMNS,
    )


def normalize_local_history(
    frame: pd.DataFrame,
    *,
    source_path: Path,
) -> pd.DataFrame:
    """Normalize the known EPL local history.

    League-less data is accepted only for OUTPUT, the established
    EPL snapshot-history path.
    """

    source_path = Path(
        source_path
    )

    if "league" not in frame.columns:
        if source_path != OUTPUT:
            raise ValueError(
                "League-less local odds history is allowed "
                "only for the known legacy EPL snapshot path"
            )

        frame = require_league(
            frame,
            legacy_epl=True,
        )

    else:
        frame = require_league(
            frame,
            legacy_epl=False,
        )

    return frame


def merge_local_history(
    old_df: pd.DataFrame,
    new_df: pd.DataFrame,
    *,
    source_path: Path = OUTPUT,
) -> pd.DataFrame:
    """Merge local snapshot history using league-aware identity."""

    old_df = normalize_local_history(
        old_df,
        source_path=source_path,
    )

    new_df = require_league(
        new_df,
        legacy_epl=False,
    )

    combined = pd.concat(
        [
            old_df,
            new_df,
        ],
        ignore_index=True,
        sort=False,
    )

    combined = combined.drop_duplicates(
        subset=[
            "league",
            "snapshot_time_utc",
            "event_id",
        ],
        keep="last",
    )

    combined = combined.sort_values(
        [
            "snapshot_time_utc",
            "league",
            "commence_time_utc",
            "home_team",
        ]
    ).reset_index(
        drop=True
    )

    return combined


def save_local_history(
    new_df: pd.DataFrame,
    *,
    output_path: Path = OUTPUT,
) -> pd.DataFrame:
    """Persist local league-aware snapshot history."""

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if output_path.exists():
        old_df = pd.read_csv(
            output_path
        )

        combined = merge_local_history(
            old_df,
            new_df,
            source_path=output_path,
        )

    else:
        combined = (
            require_league(
                new_df,
                legacy_epl=False,
            )
            .drop_duplicates(
                subset=[
                    "league",
                    "snapshot_time_utc",
                    "event_id",
                ],
                keep="last",
            )
            .sort_values(
                [
                    "snapshot_time_utc",
                    "league",
                    "commence_time_utc",
                    "home_team",
                ]
            )
            .reset_index(
                drop=True
            )
        )

    combined.to_csv(
        output_path,
        index=False,
    )

    return combined


def build_db_rows(
    new_df: pd.DataFrame,
) -> list[dict]:
    """Convert snapshot rows to Supabase-safe records."""

    required = set(
        DB_COLUMNS
    )

    missing = required.difference(
        new_df.columns
    )

    if missing:
        raise ValueError(
            "Snapshot rows missing DB columns: "
            f"{sorted(missing)}"
        )

    normalized = require_league(
        new_df,
        legacy_epl=False,
    )

    return (
        normalized[
            DB_COLUMNS
        ]
        .where(
            pd.notna(
                normalized[
                    DB_COLUMNS
                ]
            ),
            None,
        )
        .to_dict(
            orient="records"
        )
    )


def save_supabase(
    new_df: pd.DataFrame,
    *,
    supabase_client=None,
) -> int:
    """Upsert league-aware EPL rows into Supabase."""

    if supabase_client is None:
        from database import (
            supabase as supabase_client,
        )

    db_rows = build_db_rows(
        new_df
    )

    response = (
        supabase_client
        .table(
            SUPABASE_TABLE
        )
        .upsert(
            db_rows,
            on_conflict=(
                DB_CONFLICT_TARGET
            ),
        )
        .execute()
    )

    return len(
        response.data or []
    )


def main() -> None:
    """Run one real EPL odds snapshot."""

    if not EPL.collection_ready:
        raise RuntimeError(
            "EPL odds collection is not enabled/ready"
        )

    result = get_epl_h2h_odds()

    events = result[
        "events"
    ]

    quota = result[
        "quota"
    ]

    snapshot_time = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    new_df = build_snapshot_rows(
        events,
        snapshot_time,
    )

    if new_df.empty:
        raise RuntimeError(
            "The Odds API не вернул "
            "пригодных EPL h2h odds."
        )

    combined = save_local_history(
        new_df
    )

    try:
        inserted_count = save_supabase(
            new_df
        )

    except Exception as exc:
        print()
        print(
            "ОШИБКА сохранения в Supabase:"
        )
        print(
            type(exc).__name__,
            str(exc)[:1000],
        )
        print()
        print(
            "Локальный CSV уже сохранён."
        )

        raise

    print()
    print(
        "=" * 72
    )
    print(
        "EPL ODDS SNAPSHOT СОХРАНЁН"
    )
    print(
        "=" * 72
    )

    print(
        "League:",
        EPL.identifier,
    )

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
        "DB conflict target:",
        DB_CONFLICT_TARGET,
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
    print(
        "Quota:"
    )

    print(
        " remaining:",
        quota[
            "remaining"
        ],
    )

    print(
        " used:",
        quota[
            "used"
        ],
    )

    print(
        " last_cost:",
        quota[
            "last_cost"
        ],
    )

    print()

    print(
        new_df[
            [
                "league",
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


if __name__ == "__main__":
    main()
