"""Persist current Serie A MARKET_ONLY predictions to the canonical ledger."""

from __future__ import annotations

import pandas as pd

from database import supabase
from league_prediction_ledger import TABLE, build_market_only_predictions, persist_predictions
import persist_serie_a_market_observations as observation_mirror

OBSERVATION_TABLE = "league_structural_v2_observations"


def _observation_key_map() -> dict[tuple[str, str], str]:
    response = (
        supabase.table(OBSERVATION_TABLE)
        .select("observation_key,event_id,snapshot_time_utc,league")
        .eq("league", "SERIE_A")
        .execute()
    )
    result: dict[tuple[str, str], str] = {}
    for row in response.data or []:
        snapshot = pd.to_datetime(row["snapshot_time_utc"], utc=True, errors="coerce")
        if pd.isna(snapshot):
            continue
        result[(str(row["event_id"]), snapshot.isoformat())] = str(row["observation_key"])
    return result


def build_current_predictions() -> pd.DataFrame:
    shadow = observation_mirror.load_market_shadow()
    if not (shadow["league"].astype(str) == "SERIE_A").all():
        raise ValueError("Market shadow contains non-Serie-A rows")
    return build_market_only_predictions(shadow, observation_keys=_observation_key_map())


def persist_current_predictions() -> dict:
    predictions = build_current_predictions()
    if not (predictions["prediction_mode"] == "MARKET_ONLY").all():
        raise RuntimeError("Unexpected non-MARKET_ONLY Serie A prediction")
    if predictions["structural_applied"].astype(bool).any():
        raise RuntimeError("Unexpected Structural V2 activation for Serie A")
    if predictions["observation_key"].isna().any():
        raise RuntimeError("Unlinked Serie A prediction observation_key")
    return persist_predictions(supabase, predictions)


def main() -> None:
    print("Serie A prediction ledger:", persist_current_predictions())
    print("AI model used:", False)
    print("Structural V2 used:", False)


if __name__ == "__main__":
    main()
