#!/usr/bin/env python3
"""Deterministic all-leagues prospective odds capture completeness gate.

This module is deliberately network-free.  It compares an explicit expected
fixture manifest with the canonical provider event IDs actually captured for
those fixtures.  Raw odds row counts are never used because one provider event
may legitimately create multiple perspective rows.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "all_leagues_capture_completeness_v1"
MANIFEST_SCHEMA_VERSION = "all_leagues_capture_manifest_v1"

LEAGUES = (
    "epl",
    "serie_a",
    "la_liga",
    "bundesliga",
    "ligue_1",
    "eredivisie",
    "turkey_super_lig",
    "primeira_liga",
)


class GateInputError(ValueError):
    """Raised when the completeness manifest is malformed or ambiguous."""


def _canonical_event_ids(values: Any, *, field: str, league: str) -> list[str]:
    if not isinstance(values, list):
        raise GateInputError(f"{league}.{field} must be a JSON list")

    canonical: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise GateInputError(
                f"{league}.{field}[{index}] must be a non-empty string event ID"
            )
        event_id = value.strip()
        if not event_id:
            raise GateInputError(
                f"{league}.{field}[{index}] must be a non-empty string event ID"
            )
        if event_id in seen:
            raise GateInputError(f"duplicate {league}.{field} event ID: {event_id}")
        seen.add(event_id)
        canonical.append(event_id)

    return sorted(canonical)


def evaluate_league_coverage(
    league: str,
    expected_event_ids: Iterable[str],
    captured_event_ids: Iterable[str],
) -> dict[str, Any]:
    """Evaluate one league from already validated canonical IDs."""
    expected = sorted(expected_event_ids)
    captured = sorted(captured_event_ids)
    expected_set = set(expected)
    captured_set = set(captured)

    captured_expected = sorted(expected_set & captured_set)
    missing = sorted(expected_set - captured_set)
    unexpected = sorted(captured_set - expected_set)

    counts = {
        "EXPECTED": len(expected),
        "CAPTURED": len(captured_expected),
        "MISSING": len(missing),
        "UNEXPECTED": len(unexpected),
    }
    return {
        "league": league,
        "EXPECTED": expected,
        "CAPTURED": captured_expected,
        "MISSING": missing,
        "UNEXPECTED": unexpected,
        "counts": counts,
        "complete": not missing and not unexpected,
    }


def evaluate_all_leagues(
    manifest: Mapping[str, Any], *, require_all_leagues: bool = True
) -> dict[str, Any]:
    """Validate and evaluate a manifest without touching network or storage."""
    if not isinstance(manifest, Mapping):
        raise GateInputError("manifest must be a JSON object")
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise GateInputError(
            f"schema_version must be {MANIFEST_SCHEMA_VERSION!r}"
        )

    raw_leagues = manifest.get("leagues")
    if not isinstance(raw_leagues, list):
        raise GateInputError("manifest.leagues must be a JSON list")

    allowed = set(LEAGUES)
    by_league: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(raw_leagues):
        if not isinstance(entry, Mapping):
            raise GateInputError(f"manifest.leagues[{index}] must be an object")
        league = entry.get("league")
        if not isinstance(league, str) or league not in allowed:
            raise GateInputError(
                f"manifest.leagues[{index}].league must be one of {list(LEAGUES)!r}"
            )
        if league in by_league:
            raise GateInputError(f"duplicate league entry: {league}")

        expected = _canonical_event_ids(
            entry.get("expected_event_ids"), field="expected_event_ids", league=league
        )
        captured = _canonical_event_ids(
            entry.get("captured_event_ids"), field="captured_event_ids", league=league
        )
        by_league[league] = evaluate_league_coverage(league, expected, captured)

    if require_all_leagues:
        missing_leagues = [league for league in LEAGUES if league not in by_league]
        if missing_leagues:
            raise GateInputError(
                "all-leagues manifest is missing league(s): " + ", ".join(missing_leagues)
            )

    ordered = [by_league[league] for league in LEAGUES if league in by_league]
    totals = {
        key: sum(item["counts"][key] for item in ordered)
        for key in ("EXPECTED", "CAPTURED", "MISSING", "UNEXPECTED")
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "league_count": len(ordered),
        "complete": bool(ordered) and all(item["complete"] for item in ordered),
        "totals": totals,
        "leagues": ordered,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="exit 2 when any expected fixture is missing or any captured event is unexpected",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = evaluate_all_leagues(manifest)
    except (OSError, json.JSONDecodeError, GateInputError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True))
        return 3

    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if args.require_complete and not result["complete"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
