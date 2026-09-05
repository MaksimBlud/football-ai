"""Manual-only read gate for the frozen Multi-Market V2 OOS evaluator.

Default/status mode is outcome-agnostic: it never selects settlement payloads,
result fields, or calls the evaluator. Full outcome rows are loaded only after
an explicit manual protocol acknowledgement. This module never writes to the
database and never calls an external provider.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from multi_market_oos_evaluator import PROTOCOL_VERSION, evaluate
from multi_market_schema_probe import probe_schema

SNAPSHOT_TABLE = "league_multi_market_snapshots"
SETTLEMENT_TABLE = "league_multi_market_settlements"
PAGE_SIZE = 1000
MANUAL_ACK = PROTOCOL_VERSION

OUTCOME_AGNOSTIC_COLUMNS = {
    SNAPSHOT_TABLE: "snapshot_key,league,event_id",
    SETTLEMENT_TABLE: "settlement_key,snapshot_key,league,event_id",
}


def _safe_error(exc: Exception) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc).replace("\n", " ")[:400]}


def outcome_agnostic_status(client: Any) -> dict[str, Any]:
    """Check only table reachability/identity columns; never read outcomes."""
    tables = []
    for table, columns in OUTCOME_AGNOSTIC_COLUMNS.items():
        try:
            response = client.table(table).select(columns, count="exact").limit(1).execute()
            count = getattr(response, "count", None)
            tables.append({
                "table": table,
                "status": "READY",
                "row_count": int(count) if count is not None else None,
            })
        except Exception as exc:
            tables.append({"table": table, "status": "MISSING_OR_INCOMPATIBLE", "error": _safe_error(exc)})
    blocked = [row["table"] for row in tables if row["status"] != "READY"]
    return {
        "schema_version": "MULTI_MARKET_V2_OOS_MANUAL_GATE_V1",
        "protocol_version": PROTOCOL_VERSION,
        "research_only": True,
        "read_only": True,
        "outcome_agnostic": True,
        "outcome_fields_read": False,
        "evaluator_called": False,
        "automatic_evaluation_active": False,
        "manual_evaluation_required": True,
        "status": "BLOCKED_SCHEMA" if blocked else "MANUAL_EVALUATION_REQUIRED",
        "blocked_tables": blocked,
        "tables": tables,
    }


def _load_all(client: Any, table: str, columns: str, order_column: str) -> list[dict]:
    rows: list[dict] = []
    start = 0
    while True:
        response = (
            client.table(table)
            .select(columns)
            .order(order_column)
            .range(start, start + PAGE_SIZE - 1)
            .execute()
        )
        batch = list(getattr(response, "data", None) or [])
        rows.extend(dict(row) for row in batch)
        if len(batch) < PAGE_SIZE:
            break
        start += PAGE_SIZE
    return rows


def manual_evaluate(client: Any, *, acknowledgement: str) -> dict[str, Any]:
    """Explicitly load immutable outcomes and invoke the frozen evaluator."""
    if acknowledgement != MANUAL_ACK:
        raise PermissionError(f"manual acknowledgement must equal {MANUAL_ACK}")

    schema = probe_schema(client)
    if not schema.get("all_ready"):
        return {
            "schema_version": "MULTI_MARKET_V2_OOS_MANUAL_GATE_V1",
            "protocol_version": PROTOCOL_VERSION,
            "research_only": True,
            "read_only": True,
            "manual_evaluation": True,
            "evaluator_called": False,
            "status": "BLOCKED_SCHEMA",
            "blocked_tables": list(schema.get("blocked_tables") or []),
        }

    snapshots = _load_all(client, SNAPSHOT_TABLE, "*", "snapshot_key")
    settlements = _load_all(client, SETTLEMENT_TABLE, "*", "settlement_key")
    result = evaluate(snapshots, settlements)
    return {
        "schema_version": "MULTI_MARKET_V2_OOS_MANUAL_GATE_V1",
        "protocol_version": PROTOCOL_VERSION,
        "research_only": True,
        "read_only": True,
        "manual_evaluation": True,
        "evaluator_called": True,
        "status": "EVALUATED_MANUALLY",
        "snapshot_rows_loaded": len(snapshots),
        "settlement_rows_loaded": len(settlements),
        "evaluation": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual-evaluate", action="store_true")
    parser.add_argument("--ack-protocol", default="")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    from database import supabase

    if args.manual_evaluate:
        result = manual_evaluate(supabase, acknowledgement=args.ack_protocol)
    else:
        result = outcome_agnostic_status(supabase)
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
