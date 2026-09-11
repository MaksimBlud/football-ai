"""Zero-provider-cost catch-up for the La Liga canonical prediction ledger.

The live cycle may persist immutable Structural V2 shadow observations before a
later ledger bridge fails. This recovery path reads only those already durable
Supabase observations, chooses the latest valid pre-kickoff market snapshot per
future provider event, and reuses the normal immutable MARKET_ONLY bridge.

No odds-provider client, key, result source, outcome, score, or production model
is used here.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from database import supabase
from la_liga_temporal_identity import canonical_observation_key_map
from persist_la_liga_prediction_ledger import (
    LEAGUE,
    OBSERVATION_TABLE,
    persist_current_predictions,
)


DURABLE_SELECT = (
    "observation_key,event_id,snapshot_time_utc,commence_time_utc,league,"
    "persisted_at_utc,payload"
)


def _payload(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise ValueError("La Liga durable observation payload is not an object")
    return value


def _utc(value: Any, *, field: str) -> pd.Timestamp:
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"Invalid La Liga durable {field}: {value!r}")
    return parsed


def load_latest_future_durable_shadow(
    client,
    *,
    as_of_utc: Any | None = None,
) -> pd.DataFrame:
    """Build a current MARKET_ONLY shadow from immutable durable observations."""

    response = (
        client
        .table(OBSERVATION_TABLE)
        .select(DURABLE_SELECT)
        .eq("league", LEAGUE)
        .execute()
    )
    rows = response.data or []

    if not rows:
        return pd.DataFrame()

    canonical_keys, _ = canonical_observation_key_map(rows, league=LEAGUE)
    now = (
        pd.Timestamp.now(tz="UTC")
        if as_of_utc is None
        else _utc(as_of_utc, field="as_of_utc")
    )

    candidates: list[dict[str, Any]] = []
    for row in rows:
        event_id = str(row.get("event_id") or "")
        snapshot = _utc(row.get("snapshot_time_utc"), field="snapshot_time_utc")
        kickoff = _utc(row.get("commence_time_utc"), field="commence_time_utc")
        identity = (event_id, snapshot.isoformat())

        if canonical_keys.get(identity) != str(row.get("observation_key") or ""):
            continue
        if kickoff <= now:
            continue
        if snapshot >= kickoff:
            raise ValueError(
                f"Canonical La Liga durable observation is not pre-kickoff: {event_id}"
            )

        payload = _payload(row.get("payload"))
        if payload.get("pre_kickoff_valid") is not True:
            raise ValueError(
                f"Canonical La Liga durable observation is not pre-kickoff valid: {event_id}"
            )
        if payload.get("research_only") is not True:
            raise ValueError(
                f"Canonical La Liga durable observation is not research-only: {event_id}"
            )
        if str(payload.get("league")) != LEAGUE:
            raise ValueError("Foreign league in La Liga durable observation payload")

        payload_snapshot = _utc(
            payload.get("snapshot_time_utc"),
            field="payload.snapshot_time_utc",
        )
        payload_kickoff = _utc(
            payload.get("commence_time_utc"),
            field="payload.commence_time_utc",
        )
        if payload_snapshot != snapshot or payload_kickoff != kickoff:
            raise ValueError(
                f"La Liga durable row/payload timestamp mismatch: {event_id}"
            )

        candidates.append(
            {
                "league": LEAGUE,
                "event_id": event_id,
                "home_team": str(payload.get("home_team") or ""),
                "away_team": str(payload.get("away_team") or ""),
                "commence_time_utc": kickoff.isoformat(),
                "snapshot_time_utc": snapshot.isoformat(),
                "market_home_probability": payload.get("market_home_probability"),
                "market_draw_probability": payload.get("market_draw_probability"),
                "market_away_probability": payload.get("market_away_probability"),
                "market_argmax": str(payload.get("market_argmax") or ""),
                "market_shadow_status": "OK",
                "market_only": True,
            }
        )

    if not candidates:
        return pd.DataFrame()

    frame = pd.DataFrame(candidates)
    if (frame["home_team"] == "").any() or (frame["away_team"] == "").any():
        raise ValueError("La Liga durable observation lacks team identity")

    frame["snapshot_time_utc"] = pd.to_datetime(
        frame["snapshot_time_utc"], utc=True, errors="raise"
    )
    frame = (
        frame.sort_values(
            ["event_id", "snapshot_time_utc"],
            ascending=[True, False],
            kind="mergesort",
        )
        .drop_duplicates(subset=["event_id"], keep="first")
        .sort_values(["commence_time_utc", "event_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    frame["snapshot_time_utc"] = frame["snapshot_time_utc"].map(
        lambda value: value.isoformat()
    )
    return frame


def catch_up(
    client=supabase,
    *,
    as_of_utc: Any | None = None,
) -> dict[str, int]:
    shadow = load_latest_future_durable_shadow(
        client,
        as_of_utc=as_of_utc,
    )
    if shadow.empty:
        return {
            "eligible": 0,
            "inserted": 0,
            "unchanged": 0,
            "conflicts": 0,
        }

    metrics = persist_current_predictions(
        client,
        shadow=shadow,
    )
    return {
        "eligible": len(shadow),
        **metrics,
    }


def main() -> None:
    print("La Liga zero-cost prediction-ledger catch-up:", catch_up())


if __name__ == "__main__":
    main()
