"""Persist current La Liga MARKET_ONLY predictions to canonical ledger.

This is an additive research-only bridge from the existing La Liga market
shadow and immutable Structural V2 observations into the shared prediction
ledger. It does not replace La Liga's existing durable observations/results
or activate Structural V2.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from database import supabase
from league_prediction_ledger import (
    TABLE,
    build_market_only_predictions,
    persist_predictions,
)


LEAGUE = "LA_LIGA"
OBSERVATION_TABLE = "la_liga_structural_v2_observations"
MARKET_SHADOW_PATH = Path(
    "experiments/la_liga_market_shadow.csv"
)


def load_market_shadow(
    path: Path = MARKET_SHADOW_PATH,
) -> pd.DataFrame:
    frame = pd.read_csv(path)

    if frame.empty:
        raise ValueError(
            "La Liga market shadow is empty"
        )

    if not (
        frame["league"].astype(str) == LEAGUE
    ).all():
        raise ValueError(
            "Foreign league in La Liga market shadow"
        )

    return frame


def observation_key_map(client) -> dict[tuple[str, str], str]:
    response = (
        client
        .table(OBSERVATION_TABLE)
        .select(
            "observation_key,event_id,snapshot_time_utc,league"
        )
        .eq("league", LEAGUE)
        .execute()
    )

    result: dict[tuple[str, str], str] = {}

    for row in response.data or []:
        if str(row.get("league")) != LEAGUE:
            raise ValueError(
                "Foreign league in La Liga durable observations"
            )

        snapshot = pd.to_datetime(
            row.get("snapshot_time_utc"),
            utc=True,
            errors="coerce",
        )

        if pd.isna(snapshot):
            continue

        result[
            (
                str(row["event_id"]),
                snapshot.isoformat(),
            )
        ] = str(row["observation_key"])

    return result


def build_current_predictions(
    client,
    *,
    shadow: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if shadow is None:
        shadow = load_market_shadow()
    else:
        shadow = shadow.copy()

        if shadow.empty:
            raise ValueError(
                "La Liga market shadow is empty"
            )

        if not (
            shadow["league"].astype(str) == LEAGUE
        ).all():
            raise ValueError(
                "Foreign league in La Liga market shadow"
            )

    predictions = build_market_only_predictions(
        shadow,
        observation_keys=observation_key_map(client),
    )

    if not (
        predictions["league"].astype(str) == LEAGUE
    ).all():
        raise RuntimeError(
            "Unexpected league in La Liga prediction ledger"
        )

    if not (
        predictions["prediction_mode"] == "MARKET_ONLY"
    ).all():
        raise RuntimeError(
            "Unexpected La Liga prediction mode"
        )

    if predictions[
        "structural_applied"
    ].astype(bool).any():
        raise RuntimeError(
            "Unexpected La Liga Structural V2 activation"
        )

    if predictions[
        "observation_key"
    ].isna().any():
        raise RuntimeError(
            "Unlinked La Liga observation_key"
        )

    return predictions


def persist_current_predictions(
    client=supabase,
    *,
    shadow: pd.DataFrame | None = None,
) -> dict[str, int]:
    predictions = build_current_predictions(
        client,
        shadow=shadow,
    )

    return persist_predictions(
        client,
        predictions,
    )


def ledger_count(client=supabase) -> int:
    response = (
        client
        .table(TABLE)
        .select(
            "prediction_key",
            count="exact",
        )
        .eq("league", LEAGUE)
        .execute()
    )

    if response.count is not None:
        return int(response.count)

    return len(response.data or [])


def main() -> None:
    metrics = persist_current_predictions()

    print(
        "La Liga prediction ledger:",
        metrics,
    )
    print(
        "Structural V2 used:",
        False,
    )


if __name__ == "__main__":
    main()
