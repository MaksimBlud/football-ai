"""Audit whether the immutable V2B raw corner artifact supports a true time-aligned path.

Research-only, zero-provider-call source audit.

The audit inspects payload structure only. It does not evaluate market direction, does not
compute opening->closing changes, and does not use outcomes.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPERIMENT_ID = "V2B_CORNER_MARKET_PATH_SOURCE_AUDIT_V1"
EXPECTED_RAW_FIXTURES = 43
EXPECTED_RAW_ARTIFACT_ID = "10899611444"
EXPECTED_RAW_ARTIFACT_DIGEST = (
    "sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57"
)

TIME_TOKENS = ("time", "date", "timestamp", "updated", "created")
PATH_TOKENS = ("history", "historical", "snapshot", "timeline", "sequence", "previous")


def _walk_keys(value: Any, path: str = "") -> tuple[set[str], set[str]]:
    time_paths: set[str] = set()
    path_paths: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            current = f"{path}/{key}"
            lower = str(key).lower()
            if any(token in lower for token in TIME_TOKENS):
                time_paths.add(current)
            if any(token in lower for token in PATH_TOKENS):
                path_paths.add(current)
            child_time, child_path = _walk_keys(child, current)
            time_paths.update(child_time)
            path_paths.update(child_path)
    elif isinstance(value, list):
        for child in value:
            child_time, child_path = _walk_keys(child, f"{path}[]")
            time_paths.update(child_time)
            path_paths.update(child_path)
    return time_paths, path_paths


def audit_raw_dir(raw_dir: Path) -> dict[str, Any]:
    files = sorted(raw_dir.glob("*.json"))
    if len(files) != EXPECTED_RAW_FIXTURES:
        raise RuntimeError(
            f"expected {EXPECTED_RAW_FIXTURES} raw fixture payloads, found {len(files)}"
        )

    bookmaker_counts: dict[int, int] = {}
    bookmaker_slugs: dict[str, int] = {}
    corner_state_presence = {"opening": 0, "closing": 0, "inplay": 0}
    fixtures_with_corner_line = 0
    fixtures_with_multiple_bookmakers = 0
    fixtures_with_time_like_fields = 0
    fixtures_with_history_like_fields = 0
    all_time_paths: set[str] = set()
    all_history_paths: set[str] = set()
    rows: list[dict[str, Any]] = []

    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError(f"{path.name}: payload is not an object")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise RuntimeError(f"{path.name}: missing data object")
        fixture_id = str(data.get("fixture_id") or path.stem)
        bookmakers = data.get("bookmakers")
        if not isinstance(bookmakers, list):
            raise RuntimeError(f"{path.name}: bookmakers is not a list")

        count = len(bookmakers)
        bookmaker_counts[count] = bookmaker_counts.get(count, 0) + 1
        fixtures_with_multiple_bookmakers += int(count > 1)

        has_corner_line = False
        fixture_states: set[str] = set()
        for bookmaker in bookmakers:
            if not isinstance(bookmaker, dict):
                continue
            slug = str(bookmaker.get("slug") or bookmaker.get("name") or "UNKNOWN")
            bookmaker_slugs[slug] = bookmaker_slugs.get(slug, 0) + 1
            odds = bookmaker.get("odds")
            if not isinstance(odds, dict):
                continue
            corner = odds.get("corner_line")
            if not isinstance(corner, dict):
                continue
            has_corner_line = True
            for state in corner_state_presence:
                if isinstance(corner.get(state), dict):
                    fixture_states.add(state)

        fixtures_with_corner_line += int(has_corner_line)
        for state in fixture_states:
            corner_state_presence[state] += 1

        time_paths, history_paths = _walk_keys(payload)
        fixtures_with_time_like_fields += int(bool(time_paths))
        fixtures_with_history_like_fields += int(bool(history_paths))
        all_time_paths.update(time_paths)
        all_history_paths.update(history_paths)

        rows.append(
            {
                "fixture_id": fixture_id,
                "bookmaker_count": count,
                "bookmaker_slugs": sorted(
                    {
                        str(bookmaker.get("slug") or bookmaker.get("name") or "UNKNOWN")
                        for bookmaker in bookmakers
                        if isinstance(bookmaker, dict)
                    }
                ),
                "corner_line_present": has_corner_line,
                "corner_states_present": sorted(fixture_states),
                "time_like_field_paths": sorted(time_paths),
                "history_like_field_paths": sorted(history_paths),
            }
        )

    time_aligned_path_feasible = (
        fixtures_with_time_like_fields == EXPECTED_RAW_FIXTURES
        and fixtures_with_history_like_fields == EXPECTED_RAW_FIXTURES
    )
    cross_book_microstructure_feasible = fixtures_with_multiple_bookmakers > 0

    if time_aligned_path_feasible:
        status = "TIME_ALIGNED_PATH_SOURCE_PRESENT"
    else:
        status = "NO_TIME_ALIGNED_PATH_SOURCE"

    return {
        "experiment_id": EXPERIMENT_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "source_feasibility_only": True,
        "source_raw_artifact_id": EXPECTED_RAW_ARTIFACT_ID,
        "source_raw_artifact_digest": EXPECTED_RAW_ARTIFACT_DIGEST,
        "raw_fixture_count": len(files),
        "fixtures_with_corner_line": fixtures_with_corner_line,
        "bookmaker_count_distribution": {
            str(key): bookmaker_counts[key] for key in sorted(bookmaker_counts)
        },
        "bookmaker_slug_counts": dict(sorted(bookmaker_slugs.items())),
        "fixtures_with_multiple_bookmakers": fixtures_with_multiple_bookmakers,
        "corner_state_presence": corner_state_presence,
        "fixtures_with_time_like_fields": fixtures_with_time_like_fields,
        "fixtures_with_history_like_fields": fixtures_with_history_like_fields,
        "time_like_field_paths": sorted(all_time_paths),
        "history_like_field_paths": sorted(all_history_paths),
        "time_aligned_path_feasible": time_aligned_path_feasible,
        "cross_book_microstructure_feasible": cross_book_microstructure_feasible,
        "status": status,
        "interpretation": (
            "Named opening/closing/inplay endpoints without timestamps are not a "
            "time-aligned pre-move path. Closing and inplay must not be repurposed as "
            "pre-move trajectory features."
        ),
        "market_direction_evaluated": False,
        "opening_closing_delta_computed": False,
        "outcomes_read": False,
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = audit_raw_dir(args.raw_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
