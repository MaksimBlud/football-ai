"""Outcome-free source-contract audit for LA_LIGA_MARKET_HOME_60_70_V1."""
from __future__ import annotations

import numpy as np
import pandas as pd

from la_liga_market_home_60_70_prospective import IMPLEMENTATION_FREEZE_UTC, LEAGUE


def audit_recent_source_contract(
    ledger: pd.DataFrame,
    odds_snapshots: pd.DataFrame,
    *,
    max_rows: int = 100,
) -> dict:
    """Verify historical ledger rows reproduce exact raw no-vig probabilities.

    Only rows observed before the prospective implementation freeze are used,
    so this diagnostic cannot inspect prospective outcomes or tune the candidate.
    """
    ledger_required = {
        "prediction_key", "league", "event_id", "home_team", "away_team", "kickoff_utc",
        "snapshot_time_utc", "market_home_prob", "market_draw_prob", "market_away_prob",
        "prediction_mode",
    }
    odds_required = {
        "league", "event_id", "home_team", "away_team", "commence_time_utc", "snapshot_time_utc",
        "home_odds", "draw_odds", "away_odds",
    }
    missing = ledger_required.difference(ledger.columns)
    if missing:
        raise ValueError(f"Source audit ledger missing columns: {sorted(missing)}")
    missing = odds_required.difference(odds_snapshots.columns)
    if missing:
        raise ValueError(f"Source audit odds missing columns: {sorted(missing)}")

    work = ledger.copy()
    work["snapshot_time_utc"] = pd.to_datetime(work["snapshot_time_utc"], utc=True, errors="coerce")
    work["kickoff_utc"] = pd.to_datetime(work["kickoff_utc"], utc=True, errors="coerce")
    work = work.loc[
        (work["league"].astype(str) == LEAGUE)
        & (work["prediction_mode"].astype(str) == "MARKET_ONLY")
        & (work["snapshot_time_utc"] < IMPLEMENTATION_FREEZE_UTC)
        & (work["snapshot_time_utc"] < work["kickoff_utc"])
    ].dropna(subset=["snapshot_time_utc", "kickoff_utc"])
    work = work.sort_values("snapshot_time_utc").tail(max_rows).copy()
    if work.empty:
        raise RuntimeError("SOURCE_CONTRACT_AUDIT_NO_PREFREEZE_LEDGER_ROWS")

    odds = odds_snapshots.copy()
    odds["snapshot_time_utc"] = pd.to_datetime(odds["snapshot_time_utc"], utc=True, errors="coerce")
    odds["commence_time_utc"] = pd.to_datetime(odds["commence_time_utc"], utc=True, errors="coerce")
    odds = odds.loc[odds["league"].astype(str) == LEAGUE].copy()
    keys = ["league", "event_id", "snapshot_time_utc"]
    if odds.duplicated(keys).any():
        raise RuntimeError("SOURCE_CONTRACT_AUDIT_AMBIGUOUS_RAW_SNAPSHOT")

    raw_columns = keys + [
        "home_team", "away_team", "commence_time_utc", "home_odds", "draw_odds", "away_odds"
    ]
    merged = work.merge(
        odds[raw_columns],
        on=keys,
        how="left",
        suffixes=("", "_raw"),
        validate="many_to_one",
    )
    if merged[["home_odds", "draw_odds", "away_odds"]].isna().any(axis=None):
        missing_count = int(merged[["home_odds", "draw_odds", "away_odds"]].isna().any(axis=1).sum())
        raise RuntimeError(f"SOURCE_CONTRACT_AUDIT_MISSING_RAW_ROWS count={missing_count}")
    if not (
        (merged["home_team"].astype(str) == merged["home_team_raw"].astype(str))
        & (merged["away_team"].astype(str) == merged["away_team_raw"].astype(str))
    ).all():
        raise RuntimeError("SOURCE_CONTRACT_AUDIT_TEAM_MISMATCH")
    if not (
        pd.to_datetime(merged["kickoff_utc"], utc=True)
        == pd.to_datetime(merged["commence_time_utc"], utc=True)
    ).all():
        raise RuntimeError("SOURCE_CONTRACT_AUDIT_KICKOFF_MISMATCH")

    prices = merged[["home_odds", "draw_odds", "away_odds"]].apply(pd.to_numeric, errors="coerce")
    if prices.isna().any(axis=None) or (prices <= 1.0).any(axis=None):
        raise RuntimeError("SOURCE_CONTRACT_AUDIT_INVALID_RAW_ODDS")
    implied = 1.0 / prices
    raw_probs = implied.div(implied.sum(axis=1), axis=0).to_numpy(dtype=float)
    ledger_probs = merged[["market_home_prob", "market_draw_prob", "market_away_prob"]].apply(
        pd.to_numeric, errors="coerce"
    ).to_numpy(dtype=float)
    if not np.isfinite(ledger_probs).all():
        raise RuntimeError("SOURCE_CONTRACT_AUDIT_INVALID_LEDGER_PROBABILITY")
    difference = np.abs(raw_probs - ledger_probs)
    max_abs_difference = float(difference.max())
    if max_abs_difference > 1e-6:
        raise RuntimeError(
            f"SOURCE_CONTRACT_AUDIT_PROBABILITY_MISMATCH max_abs_difference={max_abs_difference:.12g}"
        )

    return {
        "status": "PASS",
        "checked_rows": int(len(merged)),
        "unique_events": int(merged["event_id"].astype(str).nunique()),
        "first_snapshot_utc": merged["snapshot_time_utc"].min().isoformat(),
        "last_snapshot_utc": merged["snapshot_time_utc"].max().isoformat(),
        "max_probability_abs_difference": max_abs_difference,
        "outcomes_queried": False,
        "prospective_rows_used": False,
    }
