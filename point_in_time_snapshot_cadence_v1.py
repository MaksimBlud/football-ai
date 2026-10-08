"""Outcome-free source and quota audit for Issue #594.

The evaluator is deliberately inert: it reads repository files only. It never
imports provider or database clients and never reads match outcomes.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FROZEN_LEAGUES = ("EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA", "LIGUE_1")
REQUIRED_COLUMNS = {
    "league",
    "event_id",
    "commence_time_utc",
    "snapshot_time_utc",
}
MONTH_DAYS = 30
MONTHLY_ALLOWANCE = 500
HARD_RESERVE = 100
SPENDABLE_CREDITS = MONTHLY_ALLOWANCE - HARD_RESERVE
CREDITS_PER_LEAGUE_BATCH = 1
CREDITS_PER_FULL_SWEEP = len(FROZEN_LEAGUES)

WORKFLOW_PATHS = {
    "EPL": ".github/workflows/odds-snapshots.yml",
    "LA_LIGA": None,
    "SERIE_A": ".github/workflows/serie-a-odds-snapshots.yml",
    "BUNDESLIGA": ".github/workflows/bundesliga-odds-snapshots.yml",
    "LIGUE_1": ".github/workflows/ligue1-odds-snapshots.yml",
}
COLLECTOR_PATHS = {
    "EPL": "save_epl_odds_snapshot_with_bookmakers.py",
    "LA_LIGA": "save_la_liga_odds_snapshot.py",
    "SERIE_A": "save_serie_a_odds_snapshot.py",
    "BUNDESLIGA": "save_bundesliga_odds_snapshot.py",
    "LIGUE_1": "save_ligue1_odds_snapshot.py",
}


def _utc(value: str) -> datetime:
    text = str(value).strip().replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def policy_arithmetic() -> dict[str, Any]:
    """Return the frozen 30-day credit arithmetic without external data."""

    p1_sweeps = (MONTH_DAYS * 24) // 12
    p2_sweeps = SPENDABLE_CREDITS // CREDITS_PER_FULL_SWEEP
    return {
        "planning_days": MONTH_DAYS,
        "monthly_allowance_credits": MONTHLY_ALLOWANCE,
        "hard_reserve_credits": HARD_RESERVE,
        "spendable_credits": SPENDABLE_CREDITS,
        "league_batch_cost_credits": CREDITS_PER_LEAGUE_BATCH,
        "full_sweep_cost_credits": CREDITS_PER_FULL_SWEEP,
        "P0_current_adaptive": {
            "status": "REQUIRES_TIMESTAMP_REPLAY",
            "interval_hours": [12, 6, 4, 2],
            "no_future_fixture_cooldown_hours": 24,
        },
        "P1_fixed_12h": {
            "spacing_hours": 12,
            "full_sweeps": p1_sweeps,
            "credits": p1_sweeps * CREDITS_PER_FULL_SWEEP,
            "unused_spendable_credits": (
                SPENDABLE_CREDITS - p1_sweeps * CREDITS_PER_FULL_SWEEP
            ),
        },
        "P2_fixed_9h": {
            "spacing_hours": 9,
            "full_sweeps": p2_sweeps,
            "credits": p2_sweeps * CREDITS_PER_FULL_SWEEP,
            "unused_spendable_credits": (
                SPENDABLE_CREDITS - p2_sweeps * CREDITS_PER_FULL_SWEEP
            ),
        },
        "P3_event_windows": {
            "status": "REQUIRES_TIMESTAMP_REPLAY",
            "windows_hours_before_kickoff": [72, 48, 24, 12, 6, 3, 1],
        },
    }


def audit_workflows(root: Path) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for league in FROZEN_LEAGUES:
        workflow_rel = WORKFLOW_PATHS[league]
        collector_rel = COLLECTOR_PATHS[league]
        collector_exists = (root / collector_rel).is_file()
        if workflow_rel is None:
            rows[league] = {
                "collector_path": collector_rel,
                "collector_exists": collector_exists,
                "workflow_path": None,
                "workflow_exists": False,
                "activation": "MANUAL_COLLECTOR_ONLY",
            }
            continue
        workflow = root / workflow_rel
        text = workflow.read_text(encoding="utf-8") if workflow.is_file() else ""
        scheduled = "schedule:" in text
        dispatch = "workflow_dispatch:" in text
        rows[league] = {
            "collector_path": collector_rel,
            "collector_exists": collector_exists,
            "workflow_path": workflow_rel,
            "workflow_exists": workflow.is_file(),
            "activation": (
                "SCHEDULED"
                if scheduled
                else "MANUAL_WORKFLOW"
                if dispatch
                else "UNKNOWN_OR_MISSING"
            ),
        }
    return rows


def audit_snapshot_sources(root: Path) -> dict[str, Any]:
    files = sorted((root / "data").glob("**/*snapshot*.csv")) if (root / "data").is_dir() else []
    by_league: dict[str, dict[str, Any]] = {
        league: {
            "usable_rows": 0,
            "unique_events": 0,
            "first_snapshot_utc": None,
            "last_snapshot_utc": None,
            "first_kickoff_utc": None,
            "last_kickoff_utc": None,
        }
        for league in FROZEN_LEAGUES
    }
    event_ids: dict[str, set[str]] = {league: set() for league in FROZEN_LEAGUES}
    malformed_rows = 0
    eligible_files: list[str] = []

    for path in files:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])):
                continue
            eligible_files.append(str(path.relative_to(root)))
            for row in reader:
                league = str(row.get("league") or "").strip()
                if league not in by_league:
                    continue
                try:
                    snapshot = _utc(row["snapshot_time_utc"])
                    kickoff = _utc(row["commence_time_utc"])
                except (KeyError, TypeError, ValueError):
                    malformed_rows += 1
                    continue
                if not row.get("event_id") or snapshot >= kickoff:
                    malformed_rows += 1
                    continue
                item = by_league[league]
                item["usable_rows"] += 1
                event_ids[league].add(str(row["event_id"]))
                for key, value in (
                    ("first_snapshot_utc", snapshot),
                    ("last_snapshot_utc", snapshot),
                    ("first_kickoff_utc", kickoff),
                    ("last_kickoff_utc", kickoff),
                ):
                    current = item[key]
                    if current is None:
                        item[key] = value
                    elif key.startswith("first_") and value < current:
                        item[key] = value
                    elif key.startswith("last_") and value > current:
                        item[key] = value

    available = []
    for league, item in by_league.items():
        item["unique_events"] = len(event_ids[league])
        for key in (
            "first_snapshot_utc",
            "last_snapshot_utc",
            "first_kickoff_utc",
            "last_kickoff_utc",
        ):
            if item[key] is not None:
                item[key] = item[key].isoformat()
        if item["usable_rows"] > 0:
            available.append(league)

    gate_passed = len(available) >= 2
    return {
        "eligible_files": eligible_files,
        "available_leagues": available,
        "available_league_count": len(available),
        "required_minimum_leagues": 2,
        "gate_passed": gate_passed,
        "complete_fixture_universe_available": False,
        "malformed_or_non_pre_kickoff_rows": malformed_rows,
        "by_league": by_league,
        "outcome_columns_loaded": False,
        "limitation": (
            "Snapshot-only files cannot prove which fixtures were missed. A complete "
            "timestamp-safe fixture universe is required for empirical policy coverage."
        ),
    }


def evaluate(root: Path | str | None = None) -> dict[str, Any]:
    root_path = Path("." if root is None else root)
    source = audit_snapshot_sources(root_path)
    arithmetic = policy_arithmetic()
    workflows = audit_workflows(root_path)

    if not source["gate_passed"]:
        decision = "BLOCKED_BY_TIMESTAMP_COVERAGE"
        interpretation = (
            "The quota arithmetic is reproducible, but fresh main does not contain "
            "timestamp-safe snapshot metadata for at least two frozen leagues. "
            "P1 costs 300 credits per 30 days (12-hour sweeps); P2 costs the full "
            "400-credit spendable budget (9-hour sweeps). No empirical coverage "
            "winner can be claimed."
        )
    elif not source["complete_fixture_universe_available"]:
        decision = "WAITING_FOR_NEW_EVIDENCE"
        interpretation = (
            "At least two leagues have pre-kickoff snapshot rows, but a snapshot-only "
            "sample cannot reveal missed fixtures. Freeze or provide a complete "
            "timestamp-safe fixture universe before comparing coverage policies."
        )
    else:
        decision = "NO_SUPPORTED_CADENCE_CHANGE"
        interpretation = (
            "No candidate is promoted automatically; full deterministic policy replay "
            "is required under the frozen gate."
        )

    return {
        "schema_version": "POINT_IN_TIME_SNAPSHOT_CADENCE_V1",
        "decision": decision,
        "interpretation_guard": interpretation,
        "source_gate": source,
        "policy_arithmetic": arithmetic,
        "workflow_audit": workflows,
        "safety": {
            "match_outcomes_used": False,
            "reserved_2026_27_outcomes_used": False,
            "paid_odds_api_calls": 0,
            "supabase_reads": 0,
            "supabase_writes": 0,
            "production_model_operations": 0,
            "production_schedule_changes": 0,
            "automatic_promotion": False,
        },
    }


if __name__ == "__main__":
    import json

    print(json.dumps(evaluate(), indent=2, sort_keys=True))
