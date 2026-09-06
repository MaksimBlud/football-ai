"""Frozen row selection, readiness gate, and primary decision for EPL_AI_MARKET_PAIR_V1.

This module is outcome-free until a caller explicitly supplies a completed audit result.
It selects the preregistered paired evidence, decides whether target outcomes may be read,
and applies the preregistered primary decision rule without fitting, threshold search, or
subgroup selection.
"""
from __future__ import annotations

import pandas as pd

EXPERIMENT_ID = "EPL_AI_MARKET_PAIR_V1"
LEAGUE = "EPL"
FROZEN_MODEL_SHA256 = "1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5"
PRIMARY_COHORT_SIZE = 100
EVALUATION_DELAY_HOURS = 24
FIRST_PERMITTED_OUTCOME_READ_UTC = pd.Timestamp("2026-11-01T12:16:54.672903Z")
AUDIT_BOOTSTRAP_SIMULATIONS = 20000
AUDIT_BOOTSTRAP_SEED = 20260901

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
    """Select exactly one preregistered pair per unambiguous event."""
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
    """Return the frozen outcome-read gate and immutable first-100 cohort candidate.

    Outcomes remain forbidden until the first 100 eligible selected events exist, the
    latest kickoff among those 100 is at least 24 hours old, and the fixed 56-day
    wall-clock embargo from first live collection has elapsed. The effective opening
    instant is the later of those two timestamps.
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

    cohort_mature_at = cohort["kickoff_utc"].max() + pd.Timedelta(hours=EVALUATION_DELAY_HOURS)
    gate_opens_at = max(cohort_mature_at, FIRST_PERMITTED_OUTCOME_READ_UTC)
    if now < gate_opens_at:
        return {
            "open": False,
            "reason": "PREREGISTERED_GATE_NOT_REACHED",
            "required_events": PRIMARY_COHORT_SIZE,
            "eligible_events": PRIMARY_COHORT_SIZE,
            "cohort_mature_at_utc": cohort_mature_at.isoformat(),
            "fixed_wall_clock_gate_utc": FIRST_PERMITTED_OUTCOME_READ_UTC.isoformat(),
            "gate_opens_at_utc": gate_opens_at.isoformat(),
            "outcome_reads_allowed": False,
        }, cohort, excluded

    return {
        "open": True,
        "reason": "PREREGISTERED_GATE_OPEN",
        "required_events": PRIMARY_COHORT_SIZE,
        "eligible_events": PRIMARY_COHORT_SIZE,
        "cohort_mature_at_utc": cohort_mature_at.isoformat(),
        "fixed_wall_clock_gate_utc": FIRST_PERMITTED_OUTCOME_READ_UTC.isoformat(),
        "gate_opens_at_utc": gate_opens_at.isoformat(),
        "outcome_reads_allowed": True,
    }, cohort, excluded


def primary_decision_from_audit(result: dict) -> str:
    """Apply the frozen two-metric bootstrap-CI primary decision rule."""
    try:
        brier = result["brier_delta_model_minus_market"]
        logloss = result["logloss_delta_model_minus_market"]
        brier_low = float(brier["ci95_low"])
        brier_high = float(brier["ci95_high"])
        logloss_low = float(logloss["ci95_low"])
        logloss_high = float(logloss["ci95_high"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("audit result missing valid preregistered CI fields") from exc

    if brier_high < 0 and logloss_high < 0:
        return "PASS"
    if brier_low > 0 and logloss_low > 0:
        return "FAIL"
    return "INCONCLUSIVE"
