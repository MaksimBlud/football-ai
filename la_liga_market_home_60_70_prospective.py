"""Prospective validation core for LA_LIGA_MARKET_HOME_60_70_V1.

Research only. The candidate thresholds were frozen by the historical strategy
lab. This module adds only prospective operational semantics; it must not be
used to retune thresholds or activate production behavior.
"""
from __future__ import annotations

from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

CANDIDATE_ID = "LA_LIGA_MARKET_HOME_60_70_V1"
LEAGUE = "LA_LIGA"
LOWER = 0.60
UPPER = 0.70
IMPLEMENTATION_FREEZE_UTC = pd.Timestamp("2026-09-04T17:00:00Z")
EVALUATION_NOT_BEFORE_UTC = pd.Timestamp("2027-06-01T00:00:00Z")
LOCAL_TZ = ZoneInfo("Europe/Madrid")
PROB_TOL = 1e-8

LEDGER_REQUIRED = {
    "prediction_key",
    "league",
    "event_id",
    "home_team",
    "away_team",
    "kickoff_utc",
    "snapshot_time_utc",
    "market_home_prob",
    "market_draw_prob",
    "market_away_prob",
    "market_pick",
    "prediction_mode",
}
ODDS_REQUIRED = {
    "league",
    "event_id",
    "snapshot_time_utc",
    "commence_time_utc",
    "home_team",
    "away_team",
    "home_odds",
    "draw_odds",
    "away_odds",
}


def _timestamps(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    work = frame.copy()
    for column in columns:
        work[column] = pd.to_datetime(work[column], utc=True, errors="coerce")
    return work


def _exclude_identity_conflicts(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Exclude ambiguous provider revisions without choosing with later info."""
    if frame.empty:
        return frame.copy(), []
    work = frame.copy()
    event_kickoffs = work.groupby("event_id")["kickoff_utc"].nunique(dropna=True)
    conflict_events = set(event_kickoffs[event_kickoffs > 1].index.astype(str))

    pair_events = work.groupby(["home_team", "away_team"])["event_id"].nunique()
    ambiguous_pairs = set(pair_events[pair_events > 1].index.tolist())
    if ambiguous_pairs:
        pair_mask = pd.Series(
            list(zip(work["home_team"].astype(str), work["away_team"].astype(str))),
            index=work.index,
        ).isin(ambiguous_pairs)
        conflict_events.update(work.loc[pair_mask, "event_id"].astype(str).tolist())

    if not conflict_events:
        return work, []
    return work.loc[~work["event_id"].astype(str).isin(conflict_events)].copy(), sorted(conflict_events)


def build_canonical_decisions(
    ledger: pd.DataFrame,
    odds_snapshots: pd.DataFrame,
    *,
    now_utc: pd.Timestamp | str | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Build the latest durably observed pre-kickoff decision per fixture.

    The immutable prediction-ledger row is the durable pre-kickoff tag source.
    Exact offered odds are joined from the raw odds snapshot at the same
    provider event and snapshot timestamp.
    """
    missing = LEDGER_REQUIRED.difference(ledger.columns)
    if missing:
        raise ValueError(f"Prediction ledger missing columns: {sorted(missing)}")
    missing = ODDS_REQUIRED.difference(odds_snapshots.columns)
    if missing:
        raise ValueError(f"Odds snapshots missing columns: {sorted(missing)}")

    now = pd.Timestamp.now(tz="UTC") if now_utc is None else pd.Timestamp(now_utc)
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    else:
        now = now.tz_convert("UTC")

    work = _timestamps(ledger, ("kickoff_utc", "snapshot_time_utc"))
    work = work.loc[
        (work["league"].astype(str) == LEAGUE)
        & (work["prediction_mode"].astype(str) == "MARKET_ONLY")
    ].copy()
    work = work.dropna(subset=["kickoff_utc", "snapshot_time_utc"])
    work = work.loc[
        (work["snapshot_time_utc"] >= IMPLEMENTATION_FREEZE_UTC)
        & (work["kickoff_utc"] >= IMPLEMENTATION_FREEZE_UTC)
        & (work["snapshot_time_utc"] < work["kickoff_utc"])
    ].copy()

    if work.empty:
        empty_columns = list(LEDGER_REQUIRED) + [
            "home_odds", "draw_odds", "away_odds", "candidate_qualifies", "decision_status"
        ]
        return pd.DataFrame(columns=sorted(set(empty_columns))), {
            "candidate_id": CANDIDATE_ID,
            "eligible_events": 0,
            "qualifying_current": 0,
            "finalized_qualifying": 0,
            "conflict_events": [],
        }

    numeric_cols = ["market_home_prob", "market_draw_prob", "market_away_prob"]
    probs = work[numeric_cols].apply(pd.to_numeric, errors="coerce")
    valid = (~probs.isna().any(axis=1)) & np.isfinite(probs.to_numpy()).all(axis=1)
    work = work.loc[valid].copy()
    probs = probs.loc[valid]
    sums = probs.sum(axis=1)
    if (sums <= 0).any():
        raise ValueError("Non-positive market probability sum")
    normalized = probs.div(sums, axis=0)
    if not np.allclose(normalized.to_numpy(), probs.to_numpy(), atol=PROB_TOL, rtol=0):
        raise ValueError("Prediction ledger market probabilities are not normalized")

    work, conflict_events = _exclude_identity_conflicts(work)
    if work.empty:
        return work, {
            "candidate_id": CANDIDATE_ID,
            "eligible_events": 0,
            "qualifying_current": 0,
            "finalized_qualifying": 0,
            "conflict_events": conflict_events,
        }

    latest = (
        work.sort_values(["event_id", "snapshot_time_utc", "prediction_key"])
        .groupby("event_id", as_index=False)
        .tail(1)
        .copy()
    )

    odds = _timestamps(odds_snapshots, ("snapshot_time_utc", "commence_time_utc"))
    odds = odds.loc[odds["league"].astype(str) == LEAGUE].copy()
    join_keys = ["league", "event_id", "snapshot_time_utc"]
    if odds.duplicated(join_keys).any():
        duplicates = odds.loc[odds.duplicated(join_keys, keep=False), join_keys]
        raise RuntimeError(f"Ambiguous raw odds snapshot identity: {duplicates.to_dict(orient='records')[:3]}")

    raw_cols = join_keys + [
        "commence_time_utc", "home_team", "away_team", "home_odds", "draw_odds", "away_odds"
    ]
    merged = latest.merge(
        odds[raw_cols],
        on=join_keys,
        how="left",
        suffixes=("", "_raw"),
        validate="one_to_one",
    )
    if merged[["home_odds", "draw_odds", "away_odds"]].isna().any(axis=None):
        raise RuntimeError("Canonical ledger decision is missing exact raw offered odds")

    if not (
        (merged["home_team"].astype(str) == merged["home_team_raw"].astype(str))
        & (merged["away_team"].astype(str) == merged["away_team_raw"].astype(str))
    ).all():
        raise RuntimeError("Ledger/raw snapshot team identity mismatch")
    if not (
        pd.to_datetime(merged["kickoff_utc"], utc=True)
        == pd.to_datetime(merged["commence_time_utc"], utc=True)
    ).all():
        raise RuntimeError("Ledger/raw snapshot kickoff mismatch")

    raw_prices = merged[["home_odds", "draw_odds", "away_odds"]].apply(pd.to_numeric, errors="coerce")
    if raw_prices.isna().any(axis=None) or (raw_prices <= 1.0).any(axis=None):
        raise ValueError("Invalid offered 1X2 odds")
    implied = 1.0 / raw_prices
    raw_probs = implied.div(implied.sum(axis=1), axis=0)
    ledger_probs = merged[numeric_cols].astype(float)
    if not np.allclose(raw_probs.to_numpy(), ledger_probs.to_numpy(), atol=1e-6, rtol=0):
        raise RuntimeError("Ledger probabilities do not match exact raw offered odds")

    merged["candidate_qualifies"] = (
        (merged["market_pick"].astype(str) == "H")
        & (merged["market_home_prob"].astype(float) >= LOWER)
        & (merged["market_home_prob"].astype(float) < UPPER)
    )
    merged["decision_status"] = np.where(
        merged["kickoff_utc"] <= now,
        np.where(merged["candidate_qualifies"], "TAGGED_FINAL", "NOT_TAGGED_FINAL"),
        np.where(merged["candidate_qualifies"], "TAGGED_PROVISIONAL", "NOT_TAGGED_PROVISIONAL"),
    )
    merged["candidate_id"] = CANDIDATE_ID
    merged["implementation_freeze_utc"] = IMPLEMENTATION_FREEZE_UTC.isoformat()

    audit = {
        "candidate_id": CANDIDATE_ID,
        "eligible_events": int(len(merged)),
        "qualifying_current": int(merged["candidate_qualifies"].sum()),
        "finalized_qualifying": int(
            ((merged["candidate_qualifies"]) & (merged["kickoff_utc"] <= now)).sum()
        ),
        "conflict_events": conflict_events,
    }
    return merged.sort_values(["kickoff_utc", "home_team", "away_team"]).reset_index(drop=True), audit


def settlement_identity(frame: pd.DataFrame) -> pd.DataFrame:
    """Return outcome-free identities for final tagged fixtures."""
    if frame.empty:
        return pd.DataFrame(columns=["league", "match_date", "home_team", "away_team", "event_id"])
    tagged = frame.loc[frame["decision_status"] == "TAGGED_FINAL"].copy()
    if tagged.empty:
        return pd.DataFrame(columns=["league", "match_date", "home_team", "away_team", "event_id"])
    kickoff = pd.to_datetime(tagged["kickoff_utc"], utc=True)
    tagged["match_date"] = kickoff.dt.tz_convert(LOCAL_TZ).dt.date.astype(str)
    return tagged[["league", "match_date", "home_team", "away_team", "event_id"]].reset_index(drop=True)


def attach_results_for_explicit_evaluation(
    decisions: pd.DataFrame,
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Attach H/D/A outcomes only on the explicit post-gate evaluation path."""
    if decisions.empty:
        return decisions.copy()
    tagged = decisions.loc[decisions["decision_status"] == "TAGGED_FINAL"].copy()
    kickoff = pd.to_datetime(tagged["kickoff_utc"], utc=True)
    tagged["match_date"] = kickoff.dt.tz_convert(LOCAL_TZ).dt.date.astype(str)
    finished = results.copy()
    required = {"league", "match_date", "home_team", "away_team", "result"}
    missing = required.difference(finished.columns)
    if missing:
        raise ValueError(f"Finished results missing columns: {sorted(missing)}")
    finished = finished.loc[finished["league"].astype(str) == LEAGUE].copy()
    finished["match_date"] = pd.to_datetime(finished["match_date"], errors="coerce").dt.date.astype(str)
    keys = ["league", "match_date", "home_team", "away_team"]
    if finished.duplicated(keys).any():
        raise RuntimeError("Finished-result identity is not unique")
    return tagged.merge(finished[keys + ["result"]], on=keys, how="left", validate="one_to_one")


def descriptive_evaluation(settled: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Compute the preregistered descriptive report; no threshold tuning."""
    work = settled.loc[settled["result"].isin(["H", "D", "A"])].copy()
    if work.empty:
        summary = pd.DataFrame([{
            "candidate_id": CANDIDATE_ID,
            "count": 0,
            "wins": 0,
            "accuracy": np.nan,
            "market_expected_wins": 0.0,
            "actual_minus_expected_wins": 0.0,
            "flat_stake_profit": 0.0,
            "roi": np.nan,
            "average_odds": np.nan,
            "max_drawdown": 0.0,
            "binary_brier": np.nan,
        }])
        return summary, pd.DataFrame(), "INSUFFICIENT_FOR_DECISION"

    work = work.sort_values("kickoff_utc").copy()
    work["home_win"] = (work["result"] == "H").astype(int)
    work["unit_pnl"] = np.where(work["home_win"] == 1, work["home_odds"].astype(float) - 1.0, -1.0)
    work["cumulative_pnl"] = work["unit_pnl"].cumsum()
    running_peak = work["cumulative_pnl"].cummax().clip(lower=0.0)
    drawdown = running_peak - work["cumulative_pnl"]
    work["calendar_month"] = pd.to_datetime(work["kickoff_utc"], utc=True).dt.to_period("M").astype(str)

    count = len(work)
    wins = int(work["home_win"].sum())
    expected = float(work["market_home_prob"].astype(float).sum())
    profit = float(work["unit_pnl"].sum())
    summary = pd.DataFrame([{
        "candidate_id": CANDIDATE_ID,
        "count": count,
        "wins": wins,
        "accuracy": wins / count,
        "market_expected_wins": expected,
        "actual_minus_expected_wins": wins - expected,
        "flat_stake_profit": profit,
        "roi": profit / count,
        "average_odds": float(work["home_odds"].astype(float).mean()),
        "max_drawdown": float(drawdown.max()),
        "binary_brier": float(np.mean((work["home_win"] - work["market_home_prob"].astype(float)) ** 2)),
    }])
    monthly = work.groupby("calendar_month", as_index=False).agg(
        count=("home_win", "size"),
        wins=("home_win", "sum"),
        market_expected_wins=("market_home_prob", "sum"),
        flat_stake_profit=("unit_pnl", "sum"),
        average_odds=("home_odds", "mean"),
    )
    monthly["accuracy"] = monthly["wins"] / monthly["count"]
    monthly["roi"] = monthly["flat_stake_profit"] / monthly["count"]
    monthly["actual_minus_expected_wins"] = monthly["wins"] - monthly["market_expected_wins"]

    state = "DIRECTIONALLY_CONSISTENT" if (wins - expected) > 0 else "DIRECTIONALLY_INCONSISTENT"
    return summary, monthly, state
