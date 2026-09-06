"""Provider-free La Liga current-results synchronization.

This operational path deliberately preserves the existing La Liga result
normalization and legacy durable table as authority, then mirrors that full
immutable authority into the generic canonical results table. It never calls
The Odds API, never evaluates prospective research outcomes, and never touches
production model artifacts.
"""
from __future__ import annotations

import argparse
import json
from io import StringIO
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import requests

from football_data_current_results import (
    DEFAULT_MAX_ATTEMPTS,
    PublicResultsSourceUnavailable,
    _fetch_csv_response,
)
import la_liga_live_persistence as legacy
import la_liga_results_updater as updater

LEAGUE = "LA_LIGA"
OUTPUT = Path("artifacts/la_liga_results_status.json")


def fetch_normalized_results(
    *,
    get: Callable = requests.get,
    timeout: int = 30,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    """Fetch SP1 with bounded transient retries and legacy identity semantics."""
    if sleep is None:
        import time
        sleep = time.sleep

    response, attempts = _fetch_csv_response(
        updater.SOURCE_URL,
        get=get,
        timeout=timeout,
        max_attempts=max_attempts,
        sleep=sleep,
    )
    raw = pd.read_csv(StringIO(response.text))
    normalized = updater.normalize_source(raw)
    return {
        "frame": normalized,
        "source_url": updater.SOURCE_URL,
        "public_http_requests": int(attempts),
        "source_rows": int(len(raw)),
        "finished_rows": int(len(normalized)),
        "paid_provider_requests": 0,
    }


def persist_canonical_authority(client) -> dict[str, int]:
    """Lazy live dependency so unit tests never require Supabase credentials."""
    import persist_la_liga_finished_results as canonical_bridge
    return canonical_bridge.persist_authoritative_results(client)


def _live_client():
    from database import supabase
    return supabase


def sync_results(
    *,
    client=None,
    fetch_fn: Callable[..., dict[str, Any]] = fetch_normalized_results,
    bridge_fn: Callable[[Any], dict[str, int]] = persist_canonical_authority,
    write: bool = False,
) -> dict[str, Any]:
    """Sync current public results into legacy authority then canonical mirror."""
    try:
        provider = fetch_fn()
    except PublicResultsSourceUnavailable as exc:
        return {
            "league": LEAGUE,
            "status": "SOURCE_UNAVAILABLE",
            "source_url": exc.url,
            "http_status": int(exc.status_code),
            "public_http_requests": int(exc.attempts),
            "source_rows": 0,
            "finished_rows": 0,
            "legacy_inserted": 0,
            "legacy_unchanged": 0,
            "canonical_inserted": 0,
            "canonical_unchanged": 0,
            "canonical_conflicts": 0,
            "writes_performed": False,
            "paid_provider_requests": 0,
        }

    frame = provider["frame"]
    base = {
        "league": LEAGUE,
        "source_url": str(provider["source_url"]),
        "public_http_requests": int(provider["public_http_requests"]),
        "source_rows": int(provider["source_rows"]),
        "finished_rows": int(provider["finished_rows"]),
        "paid_provider_requests": 0,
    }
    if not write:
        return {
            **base,
            "status": "DRY_RUN",
            "legacy_inserted": 0,
            "legacy_unchanged": 0,
            "canonical_inserted": 0,
            "canonical_unchanged": 0,
            "canonical_conflicts": 0,
            "writes_performed": False,
        }

    if client is None:
        client = _live_client()
    legacy_metrics = legacy.persist_results(client, frame)
    bridge_metrics = bridge_fn(client)
    result = {
        **base,
        "status": "WRITTEN",
        "legacy_inserted": int(legacy_metrics.get("inserted", 0)),
        "legacy_unchanged": int(legacy_metrics.get("unchanged", 0)),
        "canonical_inserted": int(bridge_metrics.get("inserted", 0)),
        "canonical_unchanged": int(bridge_metrics.get("unchanged", 0)),
        "canonical_conflicts": int(bridge_metrics.get("conflicts", 0)),
    }
    result["writes_performed"] = bool(
        result["legacy_inserted"] or result["canonical_inserted"]
    )
    return result


def _write_status(path: str | Path | None, value: dict[str, Any]) -> None:
    if path is None:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--status-json", default=str(OUTPUT))
    args = parser.parse_args()

    try:
        result = sync_results(write=args.write)
    except Exception as exc:
        result = {
            "league": LEAGUE,
            "status": "FAILED",
            "error_type": type(exc).__name__,
            "error": str(exc)[:1000],
            "paid_provider_requests": 0,
        }
        _write_status(args.status_json, result)
        print(json.dumps(result, indent=2, sort_keys=True))
        raise

    _write_status(args.status_json, result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
