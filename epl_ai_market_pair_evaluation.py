"""Frozen row selection and evaluation gate for EPL_AI_MARKET_PAIR_V1.

This module is outcome-free. It selects the preregistered paired evidence and decides
whether the primary evaluation gate is open *before* any caller may join target results.
It performs no fitting, outcome reads, threshold search, or subgroup selection.
"""
from __future__ import annotations

import pandas as pd

EXPERIMENT_ID = "EPL_AI_MARKET_PAIR_V1"
LEAGUE = "EPL"
FROZEN_MODEL_SHA256 = "1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5"
PRIMARY_COHORT_SIZE = 100
EVALUATION_DELAY_HOURS = 24

REQUIRED_COLUMNS = {
    "pair_key",
    "experiment_id",
    "league",
    "event_id",
    "provider_home_team",
    "provider_away_team",
    "kickoff_utc",
    "market_snapshot_time_utc",
    "model_generated_at_utc",
    "model_artifact_sha256",
    "market_home_prob",
    "market_draw_prob",
    "market_away_prob",
    "model_home_prob",
    "model_draw_prob",
    "model_away_prob",
}


def select_frozen_evaluation_pairs(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    """Select exactly one preregistered pair per unambiguous event.

    Rules frozen before target outcomes are used:
    - only EPL_AI_MARKET_PAIR_V1 rows from the first live model SHA are eligible;
    - both market snapshot and model generation must be pre-kickoff;
    - any event_id carrying multiple kickoff/home/away identities is excluded entirely;
    - otherwise choose maximum market_snapshot_time_utc;
    - exact timestamp ties resolve by pair_key ascending.
    """
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"paired evidence missing columns: {sorted(missing)}")
    if frame.empty:
        return frame.copy(), []

    work = frame.copy()
    for column in ("kickoff_utc", "market_snapshot_time_utc", "model_generated_at_utc"):
        work[column] = pd.to_datetime(work[column], utc=True, errors="coerce")
    if work[["kickoff_utc", "market_snapshot_time_utc", "model_generated_at_utc"]].isna().any(axis=None):
        raise ValueError("paired evidence contains invalid timestamps")

    work = work.loc[
        (work["experiment_id"].astype(str) == EXPERIMENT_ID)
        & (work["league"].astype(str) == LEAGUE)
        & (work["model_artifact_sha256"].astype(str) == FROZEN_MODEL_SHA256)
        & (work["market_snapshot_time_utc"] < work["kickoff_utc"])
        & (work["model_generated_at_utc"] < work["kickoff_utc"])
    ].copy()
    if work.empty:
        return work, []

    identity = work.groupby("event_id").agg(
        kickoff_count=("kickoff_utc", "nunique"),
        home_count=("provider_home_team", "nunique"),
        away_count=("provider_away_team", "nunique"),
    )
    ambiguous_ids = sorted(identity.index[(identity > 1).any(axis=1)].astype(str))
    excluded = [
        {"event_id": event_id, "reason": "AMBIGUOUS_EVENT_IDENTITY"}
        for event_id in ambiguous_ids
    ]
    if ambiguous_ids:
        work = work.loc[~work["event_id"].astype(str).isin(ambiguous_ids)].copy()
    if work.empty:
        return work, excluded

    if work["pair_key"].duplicated().any():
        raise RuntimeError("duplicate pair_key in paired evidence")

    selected = (
        work.sort_values(
            ["event_id", "market_snapshot_time_utc", "pair_key"],
            ascending=[True, False, True],
        )
        .groupby("event_id", as_index=False, sort=False)
        .head(1)
        .sort_values(["kickoff_utc", "event_id", "pair_key"])
        .reset_index(drop=True)
    )
    return selected, excluded


def primary_evaluation_gate(
    frame: pd.DataFrame,
    *,
    now_utc: str | pd.Timestamp,
) -> tuple[dict[str, object], pd.DataFrame, list[dict[str, str]]]:
    """Return an outcome-free gate decision and the immutable primary cohort candidate.

    The primary cohort is the first 100 eligible selected events ordered by kickoff,
    event_id, then pair_key. No target outcome may be read until all 100 exist and the
    latest kickoff in that cohort is at least 24 hours in the past. This prevents both
    performance-based optional stopping and evaluation while fixture outcomes may still
    be settling into canonical result tables.
    """
    selected, excluded = select_frozen_evaluation_pairs(frame)
    cohort = selected.head(PRIMARY_COHORT_SIZE).copy().reset_index(drop=True)
    now = pd.to_datetime(now_utc, utc=True, errors="coerce")
    if pd.isna(now):
        raise ValueError("now_utc is invalid")

    if len(cohort) < PRIMARY_COHORT_SIZE:
        return {
            "open": False,
            "reason": "INSUFFICIENT_PREREGISTERED_EVENTS",
            "required_events": PRIMARY_COHORT_SIZE,
            "eligible_events": int(len(cohort)),
            "outcome_reads_allowed": False,
        }, cohort, excluded

    gate_opens_at = cohort["kickoff_utc"].max() + pd.Timedelta(hours=EVALUATION_DELAY_HOURS)
    if now < gate_opens_at:
        return {
            "open": False,
            "reason": "COHORT_NOT_MATURE",
            "required_events": PRIMARY_COHORT_SIZE,
            "eligible_events": PRIMARY_COHORT_SIZE,
            "gate_opens_at_utc": gate_opens_at.isoformat(),
            "outcome_reads_allowed": False,
        }, cohort, excluded

    return {
        "open": True,
        "reason": "PREREGISTERED_GATE_OPEN",
        "required_events": PRIMARY_COHORT_SIZE,
        "eligible_events": PRIMARY_COHORT_SIZE,
        "gate_opens_at_utc": gate_opens_at.isoformat(),
        "outcome_reads_allowed": True,
    }, cohort, excluded
