"""Persist current EPL MARKET_ONLY predictions to canonical ledger."""

from __future__ import annotations

import pandas as pd

from database import supabase

import persist_epl_market_observations as observation_mirror

from league_prediction_ledger import (
    TABLE,
    build_market_only_predictions,
    persist_predictions,
)


OBSERVATION_TABLE = (
    "league_structural_v2_observations"
)


def _observation_key_map() -> dict[
    tuple[str, str],
    str,
]:
    response = (
        supabase
        .table(OBSERVATION_TABLE)
        .select(
            "observation_key,"
            "event_id,"
            "snapshot_time_utc,"
            "league"
        )
        .eq(
            "league",
            "EPL",
        )
        .execute()
    )

    rows = response.data or []

    result: dict[
        tuple[str, str],
        str,
    ] = {}

    for row in rows:
        snapshot = pd.to_datetime(
            row["snapshot_time_utc"],
            utc=True,
            errors="coerce",
        )

        if pd.isna(snapshot):
            continue

        key = (
            str(row["event_id"]),
            snapshot.isoformat(),
        )

        result[key] = str(
            row["observation_key"]
        )

    return result


def build_current_predictions():
    # IMPORTANT:
    # use the serialized persisted shadow boundary,
    # not an in-memory pre-CSV representation.
    shadow = (
        observation_mirror
        .load_market_shadow()
    )

    return build_market_only_predictions(
        shadow,
        observation_keys=(
            _observation_key_map()
        ),
    )


def main() -> None:
    before = (
        supabase
        .table(TABLE)
        .select(
            "prediction_key",
            count="exact",
        )
        .eq(
            "league",
            "EPL",
        )
        .execute()
    )

    before_count = (
        before.count
        if before.count is not None
        else len(before.data or [])
    )

    predictions = (
        build_current_predictions()
    )

    print(
        "current canonical predictions:",
        len(predictions),
    )

    print(
        "MARKET_ONLY:",
        int(
            (
                predictions[
                    "prediction_mode"
                ]
                == "MARKET_ONLY"
            ).sum()
        ),
    )

    print(
        "Structural V2 applied:",
        int(
            predictions[
                "structural_applied"
            ].sum()
        ),
    )

    print(
        "linked observation keys:",
        int(
            predictions[
                "observation_key"
            ].notna().sum()
        ),
    )

    result = persist_predictions(
        supabase,
        predictions,
    )

    after = (
        supabase
        .table(TABLE)
        .select(
            "prediction_key",
            count="exact",
        )
        .eq(
            "league",
            "EPL",
        )
        .execute()
    )

    after_count = (
        after.count
        if after.count is not None
        else len(after.data or [])
    )

    print(
        "ledger rows before:",
        before_count,
    )

    print(
        "ledger rows after:",
        after_count,
    )

    print(
        "inserted:",
        result["inserted"],
    )

    print(
        "unchanged:",
        result["unchanged"],
    )

    print(
        "conflicts:",
        result["conflicts"],
    )

    print(
        "AI model used:",
        False,
    )

    print(
        "Structural V2 used:",
        False,
    )

    print(
        "PASS: EPL PREDICTION LEDGER COMPLETE"
    )


if __name__ == "__main__":
    main()
