"""Autonomous research-only readiness/evaluation cycle for prospective availability."""
from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from database import supabase
from league_runtime_config import EPL_RUNTIME_CONFIG, LA_LIGA_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
import prospective_availability_persistence as availability_persistence
from prospective_availability_evaluation import (
    MARKET_COLUMNS,
    build_paired_research_frame,
    paired_incremental,
    readiness,
    run_preregistered_evaluation,
)

OUTPUT_DIR = Path("artifacts/prospective_availability_signal_lab")
PAGE_SIZE = 1000
RUNTIMES = {
    "EPL": EPL_RUNTIME_CONFIG,
    "LA_LIGA": LA_LIGA_RUNTIME_CONFIG,
    "SERIE_A": SERIE_A_RUNTIME_CONFIG,
}


def _fetch_league_rows(table: str, columns: str, league: str, order_column: str | None = None) -> list[dict]:
    rows = []
    start = 0
    while True:
        query = supabase.table(table).select(columns).eq("league", league)
        if order_column is not None:
            query = query.order(order_column, desc=False)
        response = query.range(start, start + PAGE_SIZE - 1).execute()
        page = list(response.data or [])
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        start += PAGE_SIZE
    return rows


def load_market_snapshots() -> pd.DataFrame:
    frames = []
    columns = (
        "league,event_id,snapshot_time_utc,commence_time_utc,home_team,away_team,"
        "home_odds,draw_odds,away_odds"
    )
    for league in RUNTIMES:
        frame = pd.DataFrame(_fetch_league_rows("odds_snapshots", columns, league, "snapshot_time_utc"))
        if frame.empty:
            continue
        odds = frame[["home_odds", "draw_odds", "away_odds"]].apply(pd.to_numeric, errors="coerce")
        implied = 1.0 / odds
        sums = implied.sum(axis=1)
        finite = pd.Series(np.isfinite(implied.to_numpy()).all(axis=1), index=implied.index)
        valid = (~implied.isna().any(axis=1)) & finite & (sums > 0)
        frame = frame.loc[valid].copy()
        implied = implied.loc[valid]
        probabilities = implied.div(implied.sum(axis=1), axis=0)
        frame.loc[:, list(MARKET_COLUMNS)] = probabilities.to_numpy()
        frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_finished_results() -> pd.DataFrame:
    frames = []
    columns = "league,match_date,home_team,away_team,result"
    for league in RUNTIMES:
        frame = pd.DataFrame(_fetch_league_rows("league_finished_results", columns, league, "match_date"))
        if not frame.empty:
            frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _local_match_dates(frame: pd.DataFrame) -> pd.Series:
    kickoff = pd.to_datetime(frame["commence_time_utc"], utc=True, errors="coerce")
    values = []
    for league, timestamp in zip(frame["league"].astype(str), kickoff):
        if pd.isna(timestamp):
            values.append(None)
            continue
        timezone = ZoneInfo(RUNTIMES[league].identity.timezone)
        values.append(timestamp.tz_convert(timezone).date().isoformat())
    return pd.Series(values, index=frame.index, dtype="object")


def attach_results(frame: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    work = frame.copy()
    work["match_date"] = _local_match_dates(work)
    if results.empty:
        work["result"] = pd.NA
        return work
    finished = results.copy()
    finished["match_date"] = pd.to_datetime(finished["match_date"], errors="coerce").dt.date.astype(str)
    keys = ["league", "match_date", "home_team", "away_team"]
    if finished.duplicated(keys).any():
        raise RuntimeError("Finished-result identity is not unique")
    return work.merge(finished[keys + ["result"]], on=keys, how="left", validate="many_to_one")


def run() -> dict:
    status, detail = availability_persistence.check_schema(supabase)
    if status != "PASS":
        raise RuntimeError(detail)
    market = load_market_snapshots()
    if market.empty:
        raise RuntimeError("No market snapshots available for prospective evaluation")
    polls = availability_persistence.fetch_polls(supabase)
    observations = availability_persistence.fetch_observations(supabase)
    paired = build_paired_research_frame(market, polls, observations)
    paired = attach_results(paired, load_finished_results())
    state = readiness(paired)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    state.to_csv(OUTPUT_DIR / "readiness.csv", index=False)
    paired.drop(columns=["result"], errors="ignore").to_csv(
        OUTPUT_DIR / "paired_coverage_without_outcomes.csv", index=False
    )
    print(state.to_string(index=False))
    if not bool(state["ready"].all()):
        print("WAIT: PROSPECTIVE_SAMPLE_NOT_READY; no outcome scores computed")
        return {"status": "WAIT", "readiness": state.to_dict(orient="records")}
    detail_results = run_preregistered_evaluation(paired)
    paired_results = paired_incremental(detail_results)
    detail_results.to_csv(OUTPUT_DIR / "evaluation_detail.csv", index=False)
    paired_results.to_csv(OUTPUT_DIR / "evaluation_paired_incremental.csv", index=False)
    print(paired_results.to_string(index=False))
    return {"status": "SCORED_RESEARCH_ONLY", "blocks": len(paired_results)}


if __name__ == "__main__":
    run()
