"""Persist current La Liga MARKET_ONLY predictions to canonical ledger.

This is an additive research-only bridge from the existing La Liga market
shadow and immutable Structural V2 observations into the shared prediction
ledger. It does not replace La Liga's existing durable observations/results
or activate Structural V2.

The bridge is fail-closed: the complete current prediction plan is preflighted
against immutable ledger state before append, one non-deterministic write
failure may be replayed idempotently, and the whole plan is read-after-write
verified. Historical snapshot gaps are never backfilled by this module.

Durable Structural V2 observations are additionally canonicalized by temporal
identity. If an old market snapshot was later reconstructed with newer
structural history, the earliest actually persisted observation remains the
prospective observation for that snapshot. Market-state disagreement under the
same temporal identity is a hard conflict.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from database import supabase
from la_liga_temporal_identity import canonical_observation_key_map
from league_dual_write_guard import preflight_predictions
from league_prediction_ledger import (
    PredictionLedgerConflictError,
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
            "observation_key,event_id,snapshot_time_utc,league,"
            "persisted_at_utc,payload"
        )
        .eq("league", LEAGUE)
        .execute()
    )

    result, metrics = canonical_observation_key_map(
        response.data or [],
        league=LEAGUE,
    )

    if metrics.duplicate_temporal_rows:
        print(
            "La Liga temporal observation canonicalization:",
            {
                "input": metrics.input,
                "canonical": metrics.canonical,
                "duplicate_temporal_rows": metrics.duplicate_temporal_rows,
                "structural_drift_rows": metrics.structural_drift_rows,
            },
        )

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


def _persist_once_with_retry(
    client,
    predictions: pd.DataFrame,
) -> None:
    try:
        persist_predictions(
            client,
            predictions,
        )
    except PredictionLedgerConflictError:
        raise
    except Exception:
        # A first attempt may have committed a prefix before a transport
        # failure. The canonical ledger is append-only/idempotent, so one
        # immediate replay is safe; final state is verified below.
        persist_predictions(
            client,
            predictions,
        )


def persist_current_predictions(
    client=supabase,
    *,
    shadow: pd.DataFrame | None = None,
) -> dict[str, int]:
    predictions = build_current_predictions(
        client,
        shadow=shadow,
    )

    before = preflight_predictions(
        client,
        predictions,
    )

    _persist_once_with_retry(
        client,
        predictions,
    )

    verified = preflight_predictions(
        client,
        predictions,
    )

    if (
        verified["missing"] != 0
        or verified["present"] != len(predictions)
    ):
        raise RuntimeError(
            "La Liga ledger bridge read-after-write verification failed"
        )

    return {
        "inserted": before["missing"],
        "unchanged": before["present"],
        "conflicts": 0,
    }


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
