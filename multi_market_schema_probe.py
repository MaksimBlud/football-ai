"""Read-only live schema compatibility probe for Multi-Market V2.

The probe performs SELECT-only PostgREST requests against the exact columns
required by the repository schema contracts. It requests zero data rows: the
server still validates table/column compatibility while no snapshot, corner,
or settlement payload/outcome values are returned. It never creates, alters,
inserts, updates, deletes, or invokes an odds provider.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TABLE_COLUMNS = {
    "league_multi_market_snapshots": (
        "snapshot_key",
        "league",
        "event_id",
        "home_team",
        "away_team",
        "kickoff_utc",
        "snapshot_time_utc",
        "payload",
        "provider",
        "persisted_at_utc",
    ),
    "league_multi_market_settlements": (
        "settlement_key",
        "snapshot_key",
        "league",
        "event_id",
        "home_team",
        "away_team",
        "kickoff_utc",
        "snapshot_time_utc",
        "result_season",
        "result_match_date",
        "outcome_fingerprint",
        "outcome_completeness",
        "payload",
        "persisted_at_utc",
    ),
    "league_corner_results": (
        "corner_result_key",
        "league",
        "season",
        "match_date",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "home_corners",
        "away_corners",
        "source",
        "source_fingerprint",
        "source_fetched_at_utc",
        "payload",
        "persisted_at_utc",
    ),
}


def _safe_error(exc: Exception) -> dict[str, str]:
    message = str(exc).replace("\n", " ").strip()
    return {
        "type": type(exc).__name__,
        "message": message[:400],
    }


def probe_table(client: Any, table: str, columns: tuple[str, ...]) -> dict[str, Any]:
    """Validate table existence + required columns without returning a data row."""
    try:
        response = (
            client.table(table)
            .select(",".join(columns), count="exact")
            .limit(0)
            .execute()
        )
    except Exception as exc:  # provider-specific PostgREST exceptions vary
        return {
            "table": table,
            "status": "MISSING_OR_INCOMPATIBLE",
            "required_columns": list(columns),
            "error": _safe_error(exc),
        }

    count = getattr(response, "count", None)
    rows = list(getattr(response, "data", None) or [])
    return {
        "table": table,
        "status": "READY",
        "required_columns": list(columns),
        "row_count": int(count) if count is not None else None,
        "sample_rows_returned": len(rows),
        "zero_row_probe": True,
    }


def probe_schema(client: Any) -> dict[str, Any]:
    tables = [
        probe_table(client, table, columns)
        for table, columns in TABLE_COLUMNS.items()
    ]
    ready = [row["table"] for row in tables if row["status"] == "READY"]
    blocked = [
        row["table"]
        for row in tables
        if row["status"] != "READY"
    ]
    return {
        "schema_version": "MULTI_MARKET_SCHEMA_PROBE_V1",
        "research_only": True,
        "read_only": True,
        "zero_row_probe": True,
        "tables": tables,
        "ready_tables": ready,
        "blocked_tables": blocked,
        "all_ready": not blocked,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    from database import supabase

    result = probe_schema(supabase)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
