"""Read-only temporal audit for raw odds snapshots versus canonical ledger.

Raw ``odds_snapshots`` is a provider-response archive and may contain rows at or
after kickoff. Those rows are diagnostic warnings, not canonical OOS evidence.
The canonical prediction ledger must remain strictly pre-kickoff.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

PAGE_SIZE = 1000


@dataclass(frozen=True)
class TemporalQualityReport:
    league: str
    raw_snapshot_rows: int
    raw_post_kickoff_rows: int
    raw_post_kickoff_events: int
    ambiguous_event_ids: int
    ledger_rows: int
    ledger_post_kickoff_rows: int
    archive_warnings: int
    critical_failures: int


def _utc(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True, errors="coerce")


def _ambiguous_event_ids(raw: pd.DataFrame) -> int:
    if raw.empty:
        return 0
    required = {"event_id", "home_team", "away_team", "commence_time_utc"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError("Raw snapshots missing audit columns: " + ", ".join(sorted(missing)))
    identities: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    for row in raw.to_dict(orient="records"):
        event_id = str(row.get("event_id") or "").strip()
        if not event_id:
            continue
        identities[event_id].add(
            (
                str(row.get("home_team") or ""),
                str(row.get("away_team") or ""),
                str(row.get("commence_time_utc") or ""),
            )
        )
    return sum(len(values) > 1 for values in identities.values())


def audit_frames(league: str, raw: pd.DataFrame, ledger: pd.DataFrame) -> TemporalQualityReport:
    raw = raw.copy()
    ledger = ledger.copy()
    for frame, name in ((raw, "raw"), (ledger, "ledger")):
        if not frame.empty:
            if "league" not in frame.columns:
                raise ValueError(f"{name} frame missing league")
            foreign = frame["league"].astype(str).ne(league)
            if foreign.any():
                raise ValueError(f"{name} frame contains foreign league rows")

    raw_post = pd.Series(False, index=raw.index)
    if not raw.empty:
        required = {"snapshot_time_utc", "commence_time_utc", "event_id"}
        missing = required - set(raw.columns)
        if missing:
            raise ValueError("Raw snapshots missing audit columns: " + ", ".join(sorted(missing)))
        snapshot_time = _utc(raw["snapshot_time_utc"])
        kickoff = _utc(raw["commence_time_utc"])
        if snapshot_time.isna().any() or kickoff.isna().any():
            raise ValueError("Raw snapshots contain invalid temporal values")
        raw_post = snapshot_time >= kickoff

    ledger_post = pd.Series(False, index=ledger.index)
    if not ledger.empty:
        required = {"snapshot_time_utc", "kickoff_utc"}
        missing = required - set(ledger.columns)
        if missing:
            raise ValueError("Ledger missing audit columns: " + ", ".join(sorted(missing)))
        snapshot_time = _utc(ledger["snapshot_time_utc"])
        kickoff = _utc(ledger["kickoff_utc"])
        if snapshot_time.isna().any() or kickoff.isna().any():
            raise ValueError("Ledger contains invalid temporal values")
        ledger_post = snapshot_time >= kickoff

    raw_post_rows = int(raw_post.sum())
    raw_post_events = int(raw.loc[raw_post, "event_id"].astype(str).nunique()) if raw_post_rows else 0
    ambiguous = _ambiguous_event_ids(raw)
    ledger_post_rows = int(ledger_post.sum())
    return TemporalQualityReport(
        league=league,
        raw_snapshot_rows=len(raw),
        raw_post_kickoff_rows=raw_post_rows,
        raw_post_kickoff_events=raw_post_events,
        ambiguous_event_ids=ambiguous,
        ledger_rows=len(ledger),
        ledger_post_kickoff_rows=ledger_post_rows,
        archive_warnings=raw_post_rows + ambiguous,
        critical_failures=ledger_post_rows,
    )


def _load_all(client: Any, table: str, *, order_by: str) -> list[dict]:
    rows: list[dict] = []
    start = 0
    while True:
        response = client.table(table).select("*").order(order_by, desc=False).range(start, start + PAGE_SIZE - 1).execute()
        batch = [dict(row) for row in (response.data or [])]
        rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            return rows
        start += PAGE_SIZE


def build_live_report(client: Any) -> list[dict]:
    raw = pd.DataFrame(_load_all(client, "odds_snapshots", order_by="snapshot_time_utc"))
    ledger = pd.DataFrame(_load_all(client, "league_prediction_ledger", order_by="snapshot_time_utc"))
    leagues = sorted(set(raw.get("league", pd.Series(dtype=str)).dropna().astype(str)) | set(ledger.get("league", pd.Series(dtype=str)).dropna().astype(str)))
    return [
        asdict(
            audit_frames(
                league,
                raw.loc[raw["league"].astype(str).eq(league)].copy() if not raw.empty else raw,
                ledger.loc[ledger["league"].astype(str).eq(league)].copy() if not ledger.empty else ledger,
            )
        )
        for league in leagues
    ]


def main() -> None:
    from database import supabase

    rows = build_live_report(supabase)
    print("RAW ODDS SNAPSHOT TEMPORAL QUALITY AUDIT")
    print("Read-only. Raw post-kickoff rows are archive warnings; canonical ledger leakage is critical.")
    total_critical = 0
    for row in rows:
        total_critical += int(row["critical_failures"])
        print(
            f"{row['league']}: raw={row['raw_snapshot_rows']} raw_post={row['raw_post_kickoff_rows']} "
            f"raw_post_events={row['raw_post_kickoff_events']} ambiguous_event_ids={row['ambiguous_event_ids']} "
            f"ledger={row['ledger_rows']} ledger_post={row['ledger_post_kickoff_rows']} "
            f"critical={row['critical_failures']}"
        )
    if total_critical:
        raise SystemExit(f"CRITICAL_TEMPORAL_LEAKAGE rows={total_critical}")
    print("PASS: canonical ledger remains strictly pre-kickoff")


if __name__ == "__main__":
    main()
