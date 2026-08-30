"""Read-only lineage tracer for one canonical league event."""

from __future__ import annotations

import json

import pandas as pd

from database import supabase
from evaluate_league_predictions import settle_predictions
from league_config import get_league_config


SNAPSHOT_TABLE = "odds_snapshots"
LEDGER_TABLE = "league_prediction_ledger"
RESULT_TABLE = "league_finished_results"
GENERIC_OBSERVATION_TABLE = "league_structural_v2_observations"
LA_LIGA_OBSERVATION_TABLE = "la_liga_structural_v2_observations"


def _rows(response) -> list[dict]:
    return list(getattr(response, "data", None) or [])


def observation_table(league: str) -> str:
    return LA_LIGA_OBSERVATION_TABLE if league == "LA_LIGA" else GENERIC_OBSERVATION_TABLE


def build_lineage(
    *,
    league: str,
    event_id: str,
    snapshots: pd.DataFrame,
    observations: pd.DataFrame,
    ledger: pd.DataFrame,
    results: pd.DataFrame,
) -> dict:
    if not event_id:
        raise ValueError("event_id is required")
    for label, frame in (("snapshots", snapshots), ("observations", observations), ("ledger", ledger)):
        if not frame.empty:
            if "league" not in frame.columns or "event_id" not in frame.columns:
                raise ValueError(f"{label} missing league/event_id")
            if set(frame["league"].astype(str)) != {league}:
                raise ValueError(f"{label} contains foreign league rows")
            if set(frame["event_id"].astype(str)) != {event_id}:
                raise ValueError(f"{label} contains foreign event rows")

    settled = pd.DataFrame()
    if not ledger.empty and not results.empty:
        settled = settle_predictions(ledger, results, league=league)

    ledger_pre_kickoff = True
    if not ledger.empty:
        snapshot_time = pd.to_datetime(ledger["snapshot_time_utc"], utc=True, errors="coerce")
        kickoff = pd.to_datetime(ledger["kickoff_utc"], utc=True, errors="coerce")
        ledger_pre_kickoff = bool((snapshot_time < kickoff).all())

    return {
        "league": league,
        "event_id": event_id,
        "snapshot_rows": len(snapshots),
        "observation_rows": len(observations),
        "ledger_rows": len(ledger),
        "settled_rows": len(settled),
        "ledger_pre_kickoff": ledger_pre_kickoff,
        "latest_snapshot_utc": (
            str(pd.to_datetime(snapshots["snapshot_time_utc"], utc=True).max())
            if not snapshots.empty else None
        ),
        "latest_ledger_snapshot_utc": (
            str(pd.to_datetime(ledger["snapshot_time_utc"], utc=True).max())
            if not ledger.empty else None
        ),
        "actual_result": (
            str(settled.iloc[-1]["actual_result"]) if not settled.empty else None
        ),
        "prediction_mode": (
            sorted(set(ledger["prediction_mode"].astype(str)))
            if not ledger.empty and "prediction_mode" in ledger.columns else []
        ),
        "structural_applied": (
            bool(ledger["structural_applied"].fillna(False).astype(bool).any())
            if not ledger.empty and "structural_applied" in ledger.columns else False
        ),
        "research_only": True,
    }


def load_lineage(league: str, event_id: str) -> dict:
    get_league_config(league)
    snapshots = pd.DataFrame(_rows(
        supabase.table(SNAPSHOT_TABLE).select("*").eq("league", league).eq("event_id", event_id).execute()
    ))
    observations = pd.DataFrame(_rows(
        supabase.table(observation_table(league)).select("*").eq("league", league).eq("event_id", event_id).execute()
    ))
    ledger = pd.DataFrame(_rows(
        supabase.table(LEDGER_TABLE).select("*").eq("league", league).eq("event_id", event_id).execute()
    ))
    results = pd.DataFrame(_rows(
        supabase.table(RESULT_TABLE).select("*").eq("league", league).execute()
    ))
    return build_lineage(
        league=league,
        event_id=event_id,
        snapshots=snapshots,
        observations=observations,
        ledger=ledger,
        results=results,
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--league", required=True)
    parser.add_argument("--event-id", required=True)
    args = parser.parse_args()
    print(json.dumps(load_lineage(args.league, args.event_id), indent=2, sort_keys=True))
    print("PASS: READ-ONLY CANONICAL LINEAGE TRACE COMPLETE")


if __name__ == "__main__":
    main()
