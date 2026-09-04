"""Outcome-free sample-growth monitor for PROSPECTIVE_MARKET_PATH_V1.

This module never reads result values. It derives the same preregistered readiness
counts from canonical settled fixture identities only.
"""
from __future__ import annotations

import pandas as pd

from prospective_market_path import (
    LEAGUES,
    MIN_FIXTURES_PER_LEAGUE,
    MIN_MONTHS_PER_LEAGUE,
    MIN_TEST_BLOCKS,
    MIN_TRAIN,
    MIN_TEST,
)
from prospective_market_path_settlement_lag import STATUS_PRESENT


def settled_identity_sample(paths: pd.DataFrame, settlement_audit: pd.DataFrame) -> pd.DataFrame:
    required_paths = {"league", "event_id", "kickoff_utc"}
    missing_paths = required_paths - set(paths.columns)
    if missing_paths:
        raise ValueError("paths missing columns: " + ", ".join(sorted(missing_paths)))
    required_audit = {"league", "event_id", "status"}
    missing_audit = required_audit - set(settlement_audit.columns)
    if missing_audit:
        raise ValueError("settlement audit missing columns: " + ", ".join(sorted(missing_audit)))
    if paths.empty or settlement_audit.empty:
        return pd.DataFrame(columns=["league", "event_id", "kickoff_utc", "month"])

    present = settlement_audit[settlement_audit["status"].astype(str).eq(STATUS_PRESENT)][["league", "event_id"]].drop_duplicates()
    sample = paths.merge(present, on=["league", "event_id"], how="inner", validate="one_to_one").copy()
    if sample.empty:
        return pd.DataFrame(columns=["league", "event_id", "kickoff_utc", "month"])
    sample["kickoff_utc"] = pd.to_datetime(sample["kickoff_utc"], utc=True, errors="coerce")
    sample = sample.dropna(subset=["kickoff_utc"])
    sample["month"] = sample["kickoff_utc"].dt.tz_localize(None).dt.to_period("M").astype(str)
    return sample


def readiness_without_outcomes(sample: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for league in LEAGUES:
        frame = sample[sample["league"].astype(str).eq(league)].sort_values("kickoff_utc").copy() if not sample.empty else pd.DataFrame()
        fixtures = int(frame["event_id"].nunique()) if not frame.empty else 0
        months = sorted(frame["month"].unique()) if not frame.empty else []
        valid_blocks = 0
        for month in months:
            test = frame[frame["month"].eq(month)]
            start = pd.Period(month, freq="M").start_time.tz_localize("UTC")
            train = frame[pd.to_datetime(frame["kickoff_utc"], utc=True) < start]
            if len(train) >= MIN_TRAIN and len(test) >= MIN_TEST:
                valid_blocks += 1
        rows.append({
            "league": league,
            "settled_fixtures": fixtures,
            "calendar_months": len(months),
            "valid_test_blocks": valid_blocks,
            "min_fixtures_required": MIN_FIXTURES_PER_LEAGUE,
            "min_months_required": MIN_MONTHS_PER_LEAGUE,
            "min_test_blocks_required": MIN_TEST_BLOCKS,
            "fixtures_remaining": max(0, MIN_FIXTURES_PER_LEAGUE - fixtures),
            "months_remaining": max(0, MIN_MONTHS_PER_LEAGUE - len(months)),
            "test_blocks_remaining": max(0, MIN_TEST_BLOCKS - valid_blocks),
            "ready": bool(fixtures >= MIN_FIXTURES_PER_LEAGUE and len(months) >= MIN_MONTHS_PER_LEAGUE and valid_blocks >= MIN_TEST_BLOCKS),
        })
    return pd.DataFrame(rows)
