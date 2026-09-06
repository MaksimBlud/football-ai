"""Read-only observation / canonical-ledger parity health audit for live leagues.

Snapshot-level gaps are diagnostics only when the event already has canonical
ledger history. A post-ledger-era observation event with no canonical ledger
history is critical. Historical gaps are never repaired here.

The audit performs no writes, provider calls, outcome reads, model operations,
training, promotion, or Structural V2 activation. All durable reads use the
same deterministic PostgREST pagination primitive as generic persistence so
health reporting remains complete after a league exceeds the server row cap.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from database import supabase
from league_supabase_persistence import _fetch_league_rows

GENERIC_OBSERVATION_TABLE = "league_structural_v2_observations"
LA_LIGA_OBSERVATION_TABLE = "la_liga_structural_v2_observations"
LEDGER_TABLE = "league_prediction_ledger"
LEAGUES = (
    "EPL",
    "LA_LIGA",
    "BUNDESLIGA",
    "SERIE_A",
    "LIGUE_1",
    "EREDIVISIE",
    "RPL",
)


@dataclass(frozen=True)
class LeagueParityReport:
    league: str
    observation_rows: int
    ledger_rows: int
    orphan_snapshot_rows: int
    orphan_snapshot_events: int
    orphan_snapshots_on_covered_events: int
    post_ledger_events_without_any_ledger: int
    post_ledger_orphan_snapshots_without_any_ledger: int
    future_orphan_snapshot_rows: int
    critical_failures: int


@dataclass(frozen=True)
class MultiLeagueParityReport:
    leagues: tuple[LeagueParityReport, ...]
    total_orphan_snapshot_rows: int
    total_critical_failures: int


def _timestamps(frame: pd.DataFrame, column: str, label: str) -> pd.Series:
    if column not in frame.columns:
        raise ValueError(f"{label} missing {column}")
    parsed = pd.to_datetime(frame[column], utc=True, errors="coerce")
    if parsed.isna().any():
        raise ValueError(f"{label} contains invalid {column}")
    return parsed


def audit_frames(
    league: str,
    observations: pd.DataFrame,
    ledger: pd.DataFrame,
    *,
    audited_at_utc: str | pd.Timestamp,
) -> LeagueParityReport:
    if league not in LEAGUES:
        raise ValueError(f"Unsupported parity league: {league}")

    now = pd.to_datetime(audited_at_utc, utc=True, errors="coerce")
    if pd.isna(now):
        raise ValueError("Invalid audited_at_utc")

    observations = observations.copy()
    ledger = ledger.copy()

    if observations.empty:
        return LeagueParityReport(
            league=league,
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

    required_observation = {
        "league",
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
    }
    missing = required_observation - set(observations.columns)
    if missing:
        raise ValueError(
            f"{league} observations missing parity columns: "
            + ", ".join(sorted(missing))
        )
    if set(observations["league"].astype(str)) != {league}:
        raise ValueError(f"{league} observation input contains foreign league rows")

    observations["snapshot_time_utc"] = _timestamps(
        observations, "snapshot_time_utc", f"{league} observations"
    )
    observations["commence_time_utc"] = _timestamps(
        observations, "commence_time_utc", f"{league} observations"
    )

    if ledger.empty:
        orphan_events = int(observations["event_id"].astype(str).nunique())
        future_rows = int((observations["commence_time_utc"] > now).sum())
        return LeagueParityReport(
            league=league,
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
        raise ValueError(
            f"{league} ledger missing parity columns: "
            + ", ".join(sorted(missing))
        )
    if set(ledger["league"].astype(str)) != {league}:
        raise ValueError(f"{league} ledger input contains foreign league rows")

    ledger["snapshot_time_utc"] = _timestamps(
        ledger, "snapshot_time_utc", f"{league} ledger"
    )
    first_ledger_snapshot = ledger["snapshot_time_utc"].min()

    ledger_exact = set(
        zip(ledger["event_id"].astype(str), ledger["snapshot_time_utc"])
    )
    ledger_events = set(ledger["event_id"].astype(str))

    observation_exact = list(
        zip(
            observations["event_id"].astype(str),
            observations["snapshot_time_utc"],
        )
    )
    orphan_mask = pd.Series(
        [key not in ledger_exact for key in observation_exact],
        index=observations.index,
    )
    orphan = observations.loc[orphan_mask].copy()
    orphan_events = orphan["event_id"].astype(str)
    covered_mask = orphan_events.isin(ledger_events)

    post_ledger_orphan = orphan.loc[
        orphan["snapshot_time_utc"] >= first_ledger_snapshot
    ].copy()
    post_event_values = post_ledger_orphan["event_id"].astype(str)
    no_ledger_mask = ~post_event_values.isin(ledger_events)
    no_ledger = post_ledger_orphan.loc[no_ledger_mask]
    event_failures = int(no_ledger["event_id"].astype(str).nunique())

    return LeagueParityReport(
        league=league,
        observation_rows=len(observations),
        ledger_rows=len(ledger),
        orphan_snapshot_rows=len(orphan),
        orphan_snapshot_events=int(orphan_events.nunique()),
        orphan_snapshots_on_covered_events=int(covered_mask.sum()),
        post_ledger_events_without_any_ledger=event_failures,
        post_ledger_orphan_snapshots_without_any_ledger=len(no_ledger),
        future_orphan_snapshot_rows=int((orphan["commence_time_utc"] > now).sum()),
        critical_failures=event_failures,
    )


def _observation_table(league: str) -> str:
    return (
        LA_LIGA_OBSERVATION_TABLE
        if league == "LA_LIGA"
        else GENERIC_OBSERVATION_TABLE
    )


def load_frames(client, league: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    observation_rows = _fetch_league_rows(
        client,
        _observation_table(league),
        league,
        order_fields=("snapshot_time_utc", "event_id", "observation_key"),
    )
    ledger_rows = _fetch_league_rows(
        client,
        LEDGER_TABLE,
        league,
        order_fields=("snapshot_time_utc", "event_id", "prediction_key"),
    )
    return pd.DataFrame(observation_rows), pd.DataFrame(ledger_rows)


def audit_live(client=supabase, *, audited_at_utc=None) -> MultiLeagueParityReport:
    now = audited_at_utc or pd.Timestamp.now(tz="UTC")
    reports = []
    for league in LEAGUES:
        observations, ledger = load_frames(client, league)
        reports.append(
            audit_frames(
                league,
                observations,
                ledger,
                audited_at_utc=now,
            )
        )
    result = tuple(reports)
    return MultiLeagueParityReport(
        leagues=result,
        total_orphan_snapshot_rows=sum(r.orphan_snapshot_rows for r in result),
        total_critical_failures=sum(r.critical_failures for r in result),
    )


def main() -> None:
    report = audit_live()
    print("MULTI-LEAGUE OBSERVATION / LEDGER PARITY AUDIT")
    print("Read-only: no writes, provider calls, outcomes, model operations, or promotion.")
    print()
    for league_report in report.leagues:
        row = asdict(league_report)
        print(league_report.league)
        for key, value in row.items():
            if key != "league":
                print(f"  {key}: {value}")
    print()
    print("total_orphan_snapshot_rows:", report.total_orphan_snapshot_rows)
    print("total_critical_failures:", report.total_critical_failures)
    if report.total_critical_failures:
        raise RuntimeError(
            "Multi-league observation/ledger parity has event-level canonical coverage failures"
        )
    print("PASS: MULTI-LEAGUE OBSERVATION / LEDGER PARITY AUDIT COMPLETE")


if __name__ == "__main__":
    main()
