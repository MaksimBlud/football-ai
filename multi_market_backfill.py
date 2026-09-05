"""Schema-gated Multi-Market V2 corner/settlement backfill.

Default execution is read-only/dry-run. The orchestrator never calls The Odds
API and never imports or invokes the prospective OOS evaluator. A write path
exists only behind explicit ``write=True`` / ``--write`` and remains guarded by
an exact live schema probe.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from io import StringIO
import json
from pathlib import Path
from typing import Any, Callable, Iterable

import pandas as pd
import requests

import league_supabase_persistence as league_persistence
from audit_multi_market_corner_outcomes import CONFIGS, URL, configured_csv_contract
from multi_market_corner_results import (
    normalize_corner_source_frame,
    persist_corner_results,
    reconcile_with_finished_results,
    settlement_corner_outcome,
)
from multi_market_schema_probe import probe_schema
from multi_market_settlement_persistence import (
    SettlementIdentityError,
    build_settlement_record,
    match_finished_result,
    persist_settlement_records,
)

SNAPSHOT_TABLE = "league_multi_market_snapshots"
CORNER_TABLE = "league_corner_results"
PAGE_SIZE = 1000
OUTPUT = Path("artifacts/multi_market_v2_backfill_status.json")
CONFIG_BY_LEAGUE = {config.identity.identifier: config for config in CONFIGS}


def _rows(response: Any) -> list[dict]:
    return [dict(row) for row in (getattr(response, "data", None) or [])]


def load_paginated_rows(
    client: Any,
    table: str,
    *,
    order_by: str,
    page_size: int = PAGE_SIZE,
) -> list[dict]:
    if page_size <= 0:
        raise ValueError("page_size must be positive")
    rows: list[dict] = []
    start = 0
    while True:
        response = (
            client.table(table)
            .select("*")
            .order(order_by, desc=False)
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = _rows(response)
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size
    return rows


def load_snapshots(client: Any) -> list[dict]:
    return load_paginated_rows(client, SNAPSHOT_TABLE, order_by="snapshot_time_utc")


def load_corner_results(client: Any) -> list[dict]:
    return load_paginated_rows(client, CORNER_TABLE, order_by="match_date")


def fetch_configured_corner_frame(
    config: Any,
    *,
    session: requests.Session,
) -> tuple[pd.DataFrame, str] | None:
    """Fetch only an explicit repository-owned Football-Data current-season contract."""
    contract = configured_csv_contract(config)
    if contract is None:
        return None
    url = URL.format(
        season_code=contract["season_code"],
        competition_code=contract["competition_code"],
    )
    response = session.get(url, timeout=30)
    response.raise_for_status()
    if not response.text.strip():
        raise ValueError("empty Football-Data CSV response")
    return pd.read_csv(StringIO(response.text)), url


def _identity(row: dict) -> tuple[str, str, str, str, str]:
    date_value = row.get("match_date")
    if hasattr(date_value, "isoformat"):
        date_text = date_value.isoformat()
    else:
        date_text = str(date_value or "")[:10]
    return (
        str(row.get("league") or ""),
        str(row.get("season") or ""),
        date_text,
        str(row.get("home_team") or ""),
        str(row.get("away_team") or ""),
    )


def _persist_in_chunks(
    records: list[dict],
    persist_fn: Callable[[Any, Iterable[dict]], dict],
    client: Any,
    *,
    chunk_size: int = 100,
) -> dict[str, int]:
    totals = {"inserted": 0, "unchanged": 0, "conflicts": 0}
    for start in range(0, len(records), chunk_size):
        metrics = persist_fn(client, records[start : start + chunk_size])
        for key in totals:
            totals[key] += int(metrics.get(key, 0))
    return totals


def run_backfill(
    client: Any,
    *,
    write: bool = False,
    probe_fn: Callable[[Any], dict] = probe_schema,
    snapshot_loader: Callable[[Any], list[dict]] = load_snapshots,
    corner_loader: Callable[[Any], list[dict]] = load_corner_results,
    results_loader: Callable[[Any, Any], pd.DataFrame] = league_persistence.fetch_results,
    corner_fetcher: Callable[..., tuple[pd.DataFrame, str] | None] = fetch_configured_corner_frame,
    corner_persist: Callable[[Any, Iterable[dict]], dict] = persist_corner_results,
    settlement_persist: Callable[[Any, Iterable[dict]], dict] = persist_settlement_records,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    schema = probe_fn(client)
    if schema.get("all_ready") is not True:
        return {
            "schema_version": "MULTI_MARKET_V2_BACKFILL_STATUS_V1",
            "research_only": True,
            "status": "NOOP_SCHEMA_BLOCKED",
            "write_requested": bool(write),
            "writes_performed": 0,
            "football_data_fetches": 0,
            "the_odds_api_requests": 0,
            "oos_evaluation_invoked": False,
            "schema": schema,
        }

    snapshots = snapshot_loader(client)
    existing_corners = corner_loader(client)
    leagues = sorted({str(row.get("league") or "") for row in snapshots if row.get("league")})
    unknown = [league for league in leagues if league not in CONFIG_BY_LEAGUE]
    if unknown:
        raise ValueError("unknown snapshot leagues: " + repr(unknown))

    finished_by_league: dict[str, list[dict]] = {}
    for league in leagues:
        frame = results_loader(client, CONFIG_BY_LEAGUE[league])
        finished_by_league[league] = frame.to_dict(orient="records")

    owned_session = session is None
    if session is None:
        session = requests.Session()
        session.headers.update({"User-Agent": "football-ai-multi-market-backfill/1.0"})

    fetched = 0
    generated_corners: list[dict] = []
    corner_status: dict[str, dict[str, Any]] = {}
    try:
        for league in leagues:
            config = CONFIG_BY_LEAGUE[league]
            contract = configured_csv_contract(config)
            if contract is None:
                corner_status[league] = {"status": "SOURCE_NOT_CONFIGURED", "generated": 0}
                continue
            try:
                source = corner_fetcher(config, session=session)
                fetched += 1
                if source is None:
                    corner_status[league] = {"status": "SOURCE_NOT_CONFIGURED", "generated": 0}
                    continue
                frame, url = source
                normalized = normalize_corner_source_frame(config, frame, source_url=url)
                reconciled = reconcile_with_finished_results(
                    normalized,
                    finished_by_league[league],
                )
                generated_corners.extend(reconciled)
                corner_status[league] = {"status": "RECONCILED", "generated": len(reconciled)}
            except Exception as exc:
                # Fail closed for corner enrichment, while retaining goals-only settlement ability.
                corner_status[league] = {
                    "status": "CORNER_ENRICHMENT_BLOCKED",
                    "generated": 0,
                    "error": f"{type(exc).__name__}: {exc}"[:500],
                }
    finally:
        if owned_session:
            session.close()

    corner_metrics = {"inserted": 0, "unchanged": 0, "conflicts": 0}
    if write and generated_corners:
        corner_metrics = _persist_in_chunks(generated_corners, corner_persist, client)

    # Existing and newly reconciled rows are equally canonical for settlement projection.
    corners_by_identity: dict[tuple[str, str, str, str, str], dict] = {}
    for record in [*existing_corners, *generated_corners]:
        key = _identity(record)
        previous = corners_by_identity.get(key)
        if previous is not None:
            comparable = (
                previous.get("home_corners"), previous.get("away_corners")
            )
            incoming = (record.get("home_corners"), record.get("away_corners"))
            if comparable != incoming:
                raise ValueError(f"conflicting canonical corner outcomes for {key!r}")
        corners_by_identity[key] = record

    settlements: list[dict] = []
    settlement_skips: dict[str, int] = defaultdict(int)
    for snapshot in snapshots:
        league = str(snapshot.get("league") or "")
        try:
            result = match_finished_result(snapshot, finished_by_league.get(league, []))
        except SettlementIdentityError:
            settlement_skips["NO_EXACT_FINISHED_RESULT"] += 1
            continue
        key = _identity(result)
        corner = corners_by_identity.get(key)
        corner_outcome = settlement_corner_outcome(corner) if corner is not None else None
        settlements.append(
            build_settlement_record(snapshot, result, corner_outcome=corner_outcome)
        )

    settlement_metrics = {"inserted": 0, "unchanged": 0, "conflicts": 0}
    if write and settlements:
        settlement_metrics = _persist_in_chunks(settlements, settlement_persist, client)

    writes = int(corner_metrics["inserted"]) + int(settlement_metrics["inserted"])
    return {
        "schema_version": "MULTI_MARKET_V2_BACKFILL_STATUS_V1",
        "research_only": True,
        "status": "WRITE_COMPLETE" if write else "DRY_RUN_READY",
        "write_requested": bool(write),
        "writes_performed": writes,
        "football_data_fetches": fetched,
        "the_odds_api_requests": 0,
        "oos_evaluation_invoked": False,
        "snapshot_rows": len(snapshots),
        "leagues": leagues,
        "finished_rows_by_league": {k: len(v) for k, v in finished_by_league.items()},
        "corner_status": corner_status,
        "generated_corner_rows": len(generated_corners),
        "existing_corner_rows": len(existing_corners),
        "corner_persistence": corner_metrics,
        "settlement_rows_built": len(settlements),
        "settlement_skips": dict(settlement_skips),
        "settlement_persistence": settlement_metrics,
        "schema": schema,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    from database import supabase

    result = run_backfill(supabase, write=args.write)
    text = json.dumps(result, indent=2, sort_keys=True, default=str)
    print(text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
