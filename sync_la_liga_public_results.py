"""Provider-free La Liga current-results synchronization.

Football-Data remains the primary source. If it is transiently unavailable
after bounded retries, a keyless ESPN scoreboard fallback may supply finished
scores. Existing La Liga identity/persistence rules remain authoritative. This
path never calls The Odds API, never evaluates prospective research outcomes,
and never touches production model artifacts.
"""
from __future__ import annotations

import argparse
import json
from io import StringIO
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import requests

from espn_current_results_fallback import (
    ESPNResultsSourceUnavailable,
    PROVIDER as ESPN_PROVIDER,
    fetch_football_data_like_results,
)
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
    """Fetch primary SP1 with bounded transient retries and legacy identity semantics."""
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
        "source_provider": "FOOTBALL_DATA_CSV",
        "public_http_requests": int(attempts),
        "source_rows": int(len(raw)),
        "finished_rows": int(len(normalized)),
        "paid_provider_requests": 0,
    }


def fetch_espn_normalized_results() -> dict[str, Any]:
    """Fetch zero-cost fallback, then reuse the existing La Liga normalizer."""
    provider = fetch_football_data_like_results(league=LEAGUE)
    raw = provider["frame"]
    normalized = updater.normalize_source(raw)
    if not normalized.empty:
        normalized = normalized.copy()
        normalized["source"] = ESPN_PROVIDER
        normalized["source_competition"] = provider["source_competition"]
    return {
        **provider,
        "frame": normalized,
        "finished_rows": int(len(normalized)),
    }


def persist_canonical_authority(client) -> dict[str, int]:
    """Lazy live dependency so unit tests never require Supabase credentials."""
    import persist_la_liga_finished_results as canonical_bridge
    return canonical_bridge.persist_authoritative_results(client)


def _live_client():
    from database import supabase
    return supabase


def _unavailable_result(
    primary: PublicResultsSourceUnavailable,
    fallback: ESPNResultsSourceUnavailable,
) -> dict[str, Any]:
    return {
        "league": LEAGUE,
        "status": "SOURCE_UNAVAILABLE",
        "source_url": fallback.url,
        "source_provider": ESPN_PROVIDER,
        "http_status": fallback.status_code,
        "public_http_requests": int(primary.attempts + fallback.attempts),
        "primary_source_url": primary.url,
        "primary_http_status": int(primary.status_code),
        "primary_public_http_requests": int(primary.attempts),
        "fallback_used": True,
        "fallback_public_http_requests": int(fallback.attempts),
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


def sync_results(
    *,
    client=None,
    fetch_fn: Callable[..., dict[str, Any]] = fetch_normalized_results,
    fallback_fn: Callable[..., dict[str, Any]] = fetch_espn_normalized_results,
    bridge_fn: Callable[[Any], dict[str, int]] = persist_canonical_authority,
    write: bool = False,
) -> dict[str, Any]:
    """Sync current results, using ESPN only after transient primary exhaustion."""
    primary_error: PublicResultsSourceUnavailable | None = None
    try:
        provider = fetch_fn()
        fallback_used = False
    except PublicResultsSourceUnavailable as exc:
        primary_error = exc
        try:
            provider = fallback_fn()
            fallback_used = True
        except ESPNResultsSourceUnavailable as fallback_exc:
            return _unavailable_result(exc, fallback_exc)

    frame = provider["frame"]
    base = {
        "league": LEAGUE,
        "source_url": str(provider["source_url"]),
        "source_provider": str(provider.get("source_provider") or "FOOTBALL_DATA_CSV"),
        "public_http_requests": int(provider["public_http_requests"] + (primary_error.attempts if primary_error else 0)),
        "primary_public_http_requests": int(primary_error.attempts if primary_error else provider["public_http_requests"]),
        "fallback_used": bool(fallback_used),
        "fallback_public_http_requests": int(provider["public_http_requests"] if fallback_used else 0),
        "source_rows": int(provider["source_rows"]),
        "finished_rows": int(provider["finished_rows"]),
        "paid_provider_requests": 0,
    }
    if primary_error is not None:
        base["primary_source_url"] = primary_error.url
        base["primary_http_status"] = int(primary_error.status_code)

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
