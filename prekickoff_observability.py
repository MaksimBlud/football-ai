"""Read-only, outcome-free diagnostics for canonical pre-kickoff state.

Deliberately never reads results or settlement tables, so it is safe while
prospective experiments remain behind an evaluation gate.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

PROB_COLS = ["p_home", "p_draw", "p_away"]


def _fair_probabilities(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    odds_cols = ["home_odds", "draw_odds", "away_odds"]
    if not set(odds_cols).issubset(work.columns):
        raise ValueError("snapshots require decimal odds columns")
    odds = work[odds_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(odds).all() or (odds <= 1.0).any():
        raise ValueError("invalid decimal odds")
    raw = 1.0 / odds
    work[PROB_COLS] = raw / raw.sum(axis=1, keepdims=True)
    return work


def analyze_market_movement(frame: pd.DataFrame, *, league: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    required = {"league", "event_id", "snapshot_time_utc", "commence_time_utc",
                "home_odds", "draw_odds", "away_odds"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("snapshots missing columns: " + ", ".join(sorted(missing)))
    work = frame.copy()
    if set(work["league"].dropna().astype(str)) != {league}:
        raise ValueError("snapshot league mismatch")
    work["snapshot_time_utc"] = pd.to_datetime(work["snapshot_time_utc"], utc=True, errors="coerce")
    work["commence_time_utc"] = pd.to_datetime(work["commence_time_utc"], utc=True, errors="coerce")
    if work[["snapshot_time_utc", "commence_time_utc"]].isna().any().any():
        raise ValueError("invalid snapshot timestamps")
    work = work[work["snapshot_time_utc"] < work["commence_time_utc"]].copy()
    if work.empty:
        return pd.DataFrame()
    work = _fair_probabilities(work).sort_values(["event_id", "snapshot_time_utc"])
    rows = []
    for event_id, group in work.groupby("event_id", sort=True):
        first, last = group.iloc[0], group.iloc[-1]
        a = first[PROB_COLS].to_numpy(dtype=float)
        b = last[PROB_COLS].to_numpy(dtype=float)
        delta = b - a
        rows.append({"league": league, "event_id": str(event_id), "snapshots": int(len(group)),
                     "first_snapshot_utc": first["snapshot_time_utc"],
                     "latest_pre_kickoff_utc": last["snapshot_time_utc"],
                     "home_move": float(delta[0]), "draw_move": float(delta[1]),
                     "away_move": float(delta[2]), "max_abs_move": float(np.abs(delta).max()),
                     "favorite_changed": bool(int(np.argmax(a)) != int(np.argmax(b)))})
    return pd.DataFrame(rows)


def build_prekickoff_lineage(*, league: str, event_id: str,
                             snapshots: pd.DataFrame, ledger: pd.DataFrame) -> dict:
    if not event_id:
        raise ValueError("event_id is required")
    for label, frame in (("snapshots", snapshots), ("ledger", ledger)):
        if frame.empty:
            continue
        if not {"league", "event_id"}.issubset(frame.columns):
            raise ValueError(f"{label} missing league/event_id")
        if set(frame["league"].astype(str)) != {league}:
            raise ValueError(f"{label} contains foreign league rows")
        if set(frame["event_id"].astype(str)) != {event_id}:
            raise ValueError(f"{label} contains foreign event rows")
    ledger_pre_kickoff = True
    if not ledger.empty:
        if not {"snapshot_time_utc", "kickoff_utc"}.issubset(ledger.columns):
            raise ValueError("ledger missing temporal columns")
        snap = pd.to_datetime(ledger["snapshot_time_utc"], utc=True, errors="coerce")
        kick = pd.to_datetime(ledger["kickoff_utc"], utc=True, errors="coerce")
        ledger_pre_kickoff = bool(snap.notna().all() and kick.notna().all() and (snap < kick).all())
    return {"league": league, "event_id": event_id, "snapshot_rows": int(len(snapshots)),
            "ledger_rows": int(len(ledger)), "ledger_pre_kickoff": ledger_pre_kickoff,
            "prediction_modes": sorted(set(ledger["prediction_mode"].astype(str)))
                if not ledger.empty and "prediction_mode" in ledger.columns else [],
            "outcome_reads": 0, "research_only": True}
