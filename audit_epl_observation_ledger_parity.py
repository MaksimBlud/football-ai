"""Read-only EPL durable-observation / canonical-ledger parity audit.

The EPL live cycle intentionally writes research-only durable observations
before canonical ledger rows. A historical partial run can therefore leave an
observation snapshot without an exact ledger snapshot. Such rows are not
canonical predictions and must never be retrospectively repaired after outcome
visibility merely to improve coverage.

This audit distinguishes:
- snapshot-level parity warnings on events that are otherwise represented in
  the canonical ledger; and
- event-level coverage failures where a post-ledger-era durable observation
  belongs to an event with no canonical ledger history at all.

No writes, model operations, provider calls, promotion, or outcome reads occur.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from database import supabase

OBSERVATION_TABLE = "league_structural_v2_observations"
LEDGER_TABLE = "league_prediction_ledger"
LEAGUE = "EPL"


@dataclass(frozen=True)
class EPLObservationLedgerParityReport:
    observation_rows: int
    ledger_rows: int
    orphan_snapshot_rows: int
    orphan_snapshot_events: int
    orphan_snapshots_on_covered_events: int
    post_ledger_events_without_any_ledger: int
    post_ledger_orphan_snapshots_without_any_ledger: int
    future_orphan_snapshot_rows: int
    critical_failures: int


def _timestamps(frame: pd.DataFrame, column: str, label: str) -> pd.Series:
    if column not in frame.columns:
        raise ValueError(f"{label} missing {column}")
    parsed = pd.to_datetime(frame[column], utc=True, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"{label} contains invalid {column}")
    return parsed


def audit_frames(
    observations: pd.DataFrame,
    ledger: pd.DataFrame,
    *,
    audited_at_utc: str | pd.Timestamp,
) -> EPLObservationLedgerParityReport:
    now = pd.to_datetime(audited_at_utc, utc=True, errors="coerce")
    if pd.isna(now):
        raise ValueError("Invalid audited_at_utc")

    observations = observations.copy()
    ledger = ledger.copy()

    if observations.empty:
        return EPLObservationLedgerParityReport(
            observation_rows=0,
            ledger_rows=len(ledger),
            orphan_snapshot_rows=0,
            orphan_snapshot_events=0,
            orphan_snapshots_on_covered_events=0,
            post_ledger_events_without_any_ledger=0,
            post_ledger_orphan_snapshots_without_any_ledger=0,
            future_orphan_snapshot_rows=0,
            critical_failures=0,
        )

    required_observation = {"league", "event_id", "snapshot_time_utc", "commence_time_utc"}
    missing = required_observation - set(observations.columns)
    if missing:
        raise ValueError("Observations missing parity columns: " + ", ".join(sorted(missing)))
    if set(observations["league"].astype(str)) != {LEAGUE}:
        raise ValueError("Observation parity input contains foreign league rows")

    observations["snapshot_time_utc"] = _timestamps(
        observations, "snapshot_time_utc", "Observations"
    )
    observations["commence_time_utc"] = _timestamps(
        observations, "commence_time_utc", "Observations"
    )

    if ledger.empty:
        orphan_events = int(observations["event_id"].astype(str).nunique())
        future_rows = int((observations["commence_time_utc"] > now).sum())
        return EPLObservationLedgerParityReport(
            observation_rows=len(observations),
            ledger_rows=0,
            orphan_snapshot_rows=len(observations),
            orphan_snapshot_events=orphan_events,
            orphan_snapshots_on_covered_events=0,
            post_ledger_events_without_any_ledger=0,
            post_ledger_orphan_snapshots_without_any_ledger=0,
            future_orphan_snapshot_rows=future_rows,
            critical_failures=0,
        )

    required_ledger = {"league", "event_id", "snapshot_time_utc"}
    missing = required_ledger - set(ledger.columns)
    if missing:
        raise ValueError("Ledger missing parity columns: " + ", ".join(sorted(missing)))
    if set(ledger["league"].astype(str)) != {LEAGUE}:
        raise ValueError("Ledger parity input contains foreign league rows")

    ledger["snapshot_time_utc"] = _timestamps(ledger, "snapshot_time_utc", "Ledger")
    first_ledger_snapshot = ledger["snapshot_time_utc"].min()

    ledger_exact = set(
        zip(
            ledger["event_id"].astype(str),
            ledger["snapshot_time_utc"],
        )
    )
    ledger_events = set(ledger["event_id"].astype(str))

    exact_keys = list(
        zip(
            observations["event_id"].astype(str),
            observations["snapshot_time_utc"],
        )
    )
    orphan_mask = pd.Series(
        [key not in ledger_exact for key in exact_keys],
        index=observations.index,
    )
    orphan = observations.loc[orphan_mask].copy()
    orphan_event_values = orphan["event_id"].astype(str)
    covered_mask = orphan_event_values.isin(ledger_events)

    post_ledger_orphan = orphan.loc[
        orphan["snapshot_time_utc"] >= first_ledger_snapshot
    ].copy()
    post_event_values = post_ledger_orphan["event_id"].astype(str)
    no_ledger_mask = ~post_event_values.isin(ledger_events)
    no_ledger = post_ledger_orphan.loc[no_ledger_mask]

    event_failures = int(no_ledger["event_id"].astype(str).nunique())
    return EPLObservationLedgerParityReport(
        observation_rows=len(observations),
        ledger_rows=len(ledger),
        orphan_snapshot_rows=len(orphan),
        orphan_snapshot_events=int(orphan_event_values.nunique()),
        orphan_snapshots_on_covered_events=int(covered_mask.sum()),
        post_ledger_events_without_any_ledger=event_failures,
        post_ledger_orphan_snapshots_without_any_ledger=len(no_ledger),
        future_orphan_snapshot_rows=int((orphan["commence_time_utc"] > now).sum()),
        critical_failures=event_failures,
    )


def load_frames(client=supabase) -> tuple[pd.DataFrame, pd.DataFrame]:
    observation_response = (
        client.table(OBSERVATION_TABLE)
        .select("league,event_id,snapshot_time_utc,commence_time_utc")
        .eq("league", LEAGUE)
        .execute()
    )
    ledger_response = (
        client.table(LEDGER_TABLE)
        .select("league,event_id,snapshot_time_utc")
        .eq("league", LEAGUE)
        .execute()
    )
    return (
        pd.DataFrame(observation_response.data or []),
        pd.DataFrame(ledger_response.data or []),
    )


def audit_live(client=supabase, *, audited_at_utc=None) -> EPLObservationLedgerParityReport:
    observations, ledger = load_frames(client)
    now = audited_at_utc or pd.Timestamp.now(tz="UTC")
    return audit_frames(observations, ledger, audited_at_utc=now)


def main() -> None:
    report = audit_live()
    row = asdict(report)
    print("EPL OBSERVATION / LEDGER PARITY AUDIT")
    print("Read-only: no writes, provider calls, outcomes, model operations, or promotion.")
    print()
    for key, value in row.items():
        print(f"{key}: {value}")
    if report.critical_failures:
        raise RuntimeError(
            "EPL observation/ledger parity has event-level canonical coverage failures"
        )
    print()
    print("PASS: EPL OBSERVATION / LEDGER PARITY AUDIT COMPLETE")


if __name__ == "__main__":
    main()
