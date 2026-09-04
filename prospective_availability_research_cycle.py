"""Explicit evaluation gate for prospective availability research.

Scheduled/default execution is outcome-free. Outcome values are queried only
when an operator explicitly passes ``--evaluate`` after the frozen readiness
gate is satisfied.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from league_runtime_config import EPL_RUNTIME_CONFIG, LA_LIGA_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from prospective_availability_evaluation import (
    MARKET_COLUMNS,
    MIN_CALENDAR_MONTHS_PER_LEAGUE,
    MIN_EVALUATION_BLOCKS_PER_LEAGUE,
    MIN_PAIRED_MATCHES_PER_LEAGUE,
    MIN_TEST_MATCHES_PER_BLOCK,
    MIN_TRAIN_MATCHES_PER_LEAGUE,
    RESEARCH_LEAGUES,
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


def _db():
    from database import supabase
    return supabase


def _persistence():
    import prospective_availability_persistence as availability_persistence
    return availability_persistence


def _fetch_league_rows(table: str, columns: str, league: str, order_column: str | None = None) -> list[dict]:
    supabase = _db()
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


def load_finished_result_identities() -> pd.DataFrame:
    frames = []
    columns = "league,match_date,home_team,away_team"
    for league in RUNTIMES:
        frame = pd.DataFrame(_fetch_league_rows("league_finished_results", columns, league, "match_date"))
        if not frame.empty:
            frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_finished_results_for_explicit_evaluation() -> pd.DataFrame:
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


def attach_settlement_identity(frame: pd.DataFrame, identities: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        work = frame.copy()
        work["settled"] = False
        return work
    work = frame.copy()
    work["match_date"] = _local_match_dates(work)
    keys = ["league", "match_date", "home_team", "away_team"]
    if identities.empty:
        work["settled"] = False
        return work
    finished = identities.copy()
    finished["match_date"] = pd.to_datetime(finished["match_date"], errors="coerce").dt.date.astype(str)
    if finished.duplicated(keys).any():
        raise RuntimeError("Finished-result identity is not unique")
    finished["settled"] = True
    merged = work.merge(finished[keys + ["settled"]], on=keys, how="left", validate="many_to_one")
    merged["settled"] = merged["settled"].fillna(False).astype(bool)
    return merged


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


def identity_only_readiness(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"league", "commence_time_utc", "availability_covered", "settled"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Identity-only readiness frame missing columns: {sorted(missing)}")
    work = frame.loc[
        frame["availability_covered"].astype(bool) & frame["settled"].astype(bool)
    ].copy()
    work["commence_time_utc"] = pd.to_datetime(work["commence_time_utc"], utc=True, errors="coerce")
    work = work.dropna(subset=["commence_time_utc"])
    work["calendar_month"] = work["commence_time_utc"].dt.to_period("M").astype(str)
    rows = []
    for league in RESEARCH_LEAGUES:
        group = work.loc[work["league"].astype(str) == league].copy()
        month_counts = group.groupby("calendar_month").size().sort_index()
        eligible_blocks = 0
        cumulative = 0
        for count in month_counts.tolist():
            if cumulative >= MIN_TRAIN_MATCHES_PER_LEAGUE and count >= MIN_TEST_MATCHES_PER_BLOCK:
                eligible_blocks += 1
            cumulative += int(count)
        matches = len(group)
        months = int(group["calendar_month"].nunique())
        rows.append({
            "league": league,
            "paired_finished_matches": matches,
            "calendar_months": months,
            "eligible_evaluation_blocks": eligible_blocks,
            "ready": bool(
                matches >= MIN_PAIRED_MATCHES_PER_LEAGUE
                and months >= MIN_CALENDAR_MONTHS_PER_LEAGUE
                and eligible_blocks >= MIN_EVALUATION_BLOCKS_PER_LEAGUE
            ),
        })
    return pd.DataFrame(rows)


def _load_paired() -> pd.DataFrame:
    supabase = _db()
    persistence = _persistence()
    status, detail = persistence.check_schema(supabase)
    if status != "PASS":
        raise RuntimeError(detail)
    market = load_market_snapshots()
    if market.empty:
        raise RuntimeError("No market snapshots available for prospective availability")
    polls = persistence.fetch_polls(supabase)
    observations = persistence.fetch_observations(supabase)
    return build_paired_research_frame(market, polls, observations)


def run_readiness_only() -> dict:
    paired = _load_paired()
    paired = attach_settlement_identity(paired, load_finished_result_identities())
    state = identity_only_readiness(paired)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    state.to_csv(OUTPUT_DIR / "readiness.csv", index=False)
    paired.drop(columns=["settled"], errors="ignore").to_csv(
        OUTPUT_DIR / "paired_coverage_without_outcomes.csv", index=False
    )
    print(state.to_string(index=False))
    print("READ_ONLY_AVAILABILITY_READINESS: result values not queried; no outcome scores; no Supabase writes")
    print("OUTCOME_EVALUATION_GATED: explicit --evaluate required after frozen readiness")
    return {"status": "ACCUMULATING", "readiness": state.to_dict(orient="records")}


def run_explicit_evaluation() -> dict:
    paired = _load_paired()
    paired = attach_results(paired, load_finished_results_for_explicit_evaluation())
    state = readiness(paired)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    state.to_csv(OUTPUT_DIR / "readiness.csv", index=False)
    paired.drop(columns=["result"], errors="ignore").to_csv(
        OUTPUT_DIR / "paired_coverage_without_outcomes.csv", index=False
    )
    print(state.to_string(index=False))
    if not bool(state["ready"].all()):
        raise RuntimeError("EXPLICIT_EVALUATION_REFUSED: all three leagues must pass the frozen readiness gate")
    detail_results = run_preregistered_evaluation(paired)
    paired_results = paired_incremental(detail_results)
    detail_results.to_csv(OUTPUT_DIR / "evaluation_detail.csv", index=False)
    paired_results.to_csv(OUTPUT_DIR / "evaluation_paired_incremental.csv", index=False)
    print(paired_results.to_string(index=False))
    print("SCORED_RESEARCH_ONLY_EXPLICIT: no production activation or writes")
    return {"status": "SCORED_RESEARCH_ONLY_EXPLICIT", "blocks": len(paired_results)}


def run(*, evaluate: bool = False) -> dict:
    return run_explicit_evaluation() if evaluate else run_readiness_only()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prospective Availability Signal Lab cycle")
    parser.add_argument("--evaluate", action="store_true", help="Explicitly run preregistered outcome evaluation after readiness.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run(evaluate=args.evaluate)
