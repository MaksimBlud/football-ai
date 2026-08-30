"""Generic read-only market movement analysis from canonical odds snapshots."""

from __future__ import annotations

import numpy as np
import pandas as pd

from database import supabase
from league_config import get_league_config


TABLE = "odds_snapshots"
PROB_COLS = ["p_home", "p_draw", "p_away"]


def _fair_probabilities(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    direct = ["home_probability", "draw_probability", "away_probability"]
    odds_cols = ["home_odds", "draw_odds", "away_odds"]
    if set(direct).issubset(work.columns):
        probs = work[direct].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        sums = probs.sum(axis=1, keepdims=True)
        if not np.isfinite(probs).all() or (probs < 0).any() or (sums <= 0).any():
            raise ValueError("Invalid direct market probabilities")
        probs = probs / sums
    elif set(odds_cols).issubset(work.columns):
        odds = work[odds_cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(odds).all() or (odds <= 1.0).any():
            raise ValueError("Invalid decimal odds")
        raw = 1.0 / odds
        probs = raw / raw.sum(axis=1, keepdims=True)
    else:
        raise ValueError("Snapshots need probability or decimal-odds columns")
    work[PROB_COLS] = probs
    return work


def analyze_snapshots(frame: pd.DataFrame, *, league: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    required = {"league", "event_id", "home_team", "away_team", "snapshot_time_utc", "commence_time_utc"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Snapshots missing columns: " + ", ".join(sorted(missing)))

    work = frame.copy()
    observed = set(work["league"].dropna().astype(str))
    if observed != {league}:
        raise ValueError(f"Snapshot league mismatch for {league}: {sorted(observed)}")
    work["snapshot_time_utc"] = pd.to_datetime(work["snapshot_time_utc"], utc=True, errors="coerce")
    work["commence_time_utc"] = pd.to_datetime(work["commence_time_utc"], utc=True, errors="coerce")
    if work[["snapshot_time_utc", "commence_time_utc"]].isna().any().any():
        raise ValueError("Snapshots contain invalid timestamps")
    work = work[work["snapshot_time_utc"] < work["commence_time_utc"]].copy()
    if work.empty:
        return pd.DataFrame()
    work = _fair_probabilities(work).sort_values(["event_id", "snapshot_time_utc"])

    rows = []
    for event_id, group in work.groupby("event_id"):
        first = group.iloc[0]
        last = group.iloc[-1]
        first_probs = first[PROB_COLS].to_numpy(dtype=float)
        last_probs = last[PROB_COLS].to_numpy(dtype=float)
        delta = last_probs - first_probs
        first_pick = ("H", "D", "A")[int(np.argmax(first_probs))]
        last_pick = ("H", "D", "A")[int(np.argmax(last_probs))]
        rows.append({
            "league": league,
            "event_id": event_id,
            "home_team": last["home_team"],
            "away_team": last["away_team"],
            "kickoff_utc": last["commence_time_utc"],
            "snapshots": len(group),
            "first_snapshot_utc": first["snapshot_time_utc"],
            "latest_pre_kickoff_utc": last["snapshot_time_utc"],
            "latest_hours_to_kickoff": float((last["commence_time_utc"] - last["snapshot_time_utc"]).total_seconds() / 3600),
            "home_move": float(delta[0]),
            "draw_move": float(delta[1]),
            "away_move": float(delta[2]),
            "max_abs_move": float(np.abs(delta).max()),
            "first_market_pick": first_pick,
            "latest_market_pick": last_pick,
            "favorite_changed": bool(first_pick != last_pick),
        })
    return pd.DataFrame(rows).sort_values(["kickoff_utc", "event_id"]).reset_index(drop=True)


def load_snapshots(league: str) -> pd.DataFrame:
    get_league_config(league)
    rows = []
    offset = 0
    page_size = 1000
    while True:
        response = (
            supabase.table(TABLE)
            .select("*")
            .eq("league", league)
            .order("snapshot_time_utc", desc=False)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        batch = list(getattr(response, "data", None) or [])
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return pd.DataFrame(rows)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--league", required=True)
    args = parser.parse_args()
    movement = analyze_snapshots(load_snapshots(args.league), league=args.league)
    print(f"{args.league} MARKET MOVEMENT")
    print("events:", len(movement))
    if not movement.empty:
        print("mean max abs move:", float(movement["max_abs_move"].mean()))
        print("median max abs move:", float(movement["max_abs_move"].median()))
        print("favorite changes:", int(movement["favorite_changed"].sum()))
        print(movement.to_string(index=False))
    print("PASS: READ-ONLY MARKET MOVEMENT ANALYSIS COMPLETE")


if __name__ == "__main__":
    main()
