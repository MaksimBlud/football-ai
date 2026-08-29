"""Persist current RPL MARKET_ONLY predictions to canonical ledger."""

from __future__ import annotations

import pandas as pd

from database import supabase
import persist_rpl_market_observations as observation_mirror
from league_prediction_ledger import TABLE, build_market_only_predictions, persist_predictions


OBSERVATION_TABLE = "league_structural_v2_observations"


def _observation_key_map() -> dict[tuple[str, str], str]:
    response = (
        supabase
        .table(OBSERVATION_TABLE)
        .select("observation_key,event_id,snapshot_time_utc,league")
        .eq("league", "RPL")
        .execute()
    )

    result: dict[tuple[str, str], str] = {}
    for row in response.data or []:
        snapshot = pd.to_datetime(
            row["snapshot_time_utc"], utc=True, errors="coerce"
        )
        if pd.isna(snapshot):
            continue
        result[(str(row["event_id"]), snapshot.isoformat())] = str(
            row["observation_key"]
        )
    return result


def build_current_predictions() -> pd.DataFrame:
    shadow = observation_mirror.load_market_shadow()
    if not (shadow["league"].astype(str) == "RPL").all():
        raise ValueError("Market shadow contains non-RPL rows")
    return build_market_only_predictions(
        shadow,
        observation_keys=_observation_key_map(),
    )


def persist_current_predictions() -> dict:
    predictions = build_current_predictions()
    if not (predictions["prediction_mode"] == "MARKET_ONLY").all():
        raise RuntimeError("Unexpected non-MARKET_ONLY RPL prediction")
    if predictions["structural_applied"].astype(bool).any():
        raise RuntimeError("Unexpected Structural V2 activation for RPL")
    if predictions["observation_key"].isna().any():
        raise RuntimeError("Unlinked RPL prediction observation_key")
    return persist_predictions(supabase, predictions)


def main() -> None:
    metrics = persist_current_predictions()
    print("RPL prediction ledger:", metrics)
    print("AI model used:", False)
    print("Structural V2 used:", False)


if __name__ == "__main__":
    main()
