"""Manual metadata-only live inventory runner for corner direction V2.

Allowed network surface: 5DollarFootballAPI league fixture-list endpoints only.
This module cannot acquire V2 market prices or evaluate direction statistics.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import requests

import corner_market_state_repricing_v1 as market_v1
import corner_repricing_direction_replication_v1 as replication
import corner_regime_adjusted_direction_v1 as direction_v1
import corner_regime_adjusted_direction_v2 as v2

EXPERIMENT_ID = "CORNER_REGIME_ADJUSTED_DIRECTION_V2_METADATA_LIVE"
MAX_PAGES_PER_LEAGUE = 2
LIST_PER_PAGE = 50
MAX_METADATA_REQUESTS = 10
EXPECTED_DISCOVERY_IDS = 55
EXPECTED_REPLICATION_IDS = 50
EXPECTED_V1_DIRECTION_IDS = 46
EXPECTED_EXCLUDED_IDS = 151


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_selected_fixture_ids(artifact_zip: Path) -> set[str]:
    with zipfile.ZipFile(artifact_zip) as zf:
        names = [name for name in zf.namelist() if name.endswith("selected_fixtures.json")]
        if len(names) != 1:
            raise RuntimeError(
                "expected exactly one selected_fixtures.json in artifact, "
                f"got {len(names)}"
            )
        payload = json.loads(zf.read(names[0]).decode("utf-8"))

    if not isinstance(payload, dict):
        raise RuntimeError("selected_fixtures.json must be an object")

    fixture_ids: set[str] = set()
    for league in v2.LEAGUE_ORDER:
        rows = payload.get(league)
        if not isinstance(rows, list):
            raise RuntimeError(f"selected fixture artifact missing league {league}")
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError(f"{league}: selected fixture must be an object")
            fixture_id = str(row.get("fixture_id") or "").strip()
            if not fixture_id:
                raise RuntimeError(f"{league}: selected fixture missing fixture_id")
            if fixture_id in fixture_ids:
                raise RuntimeError(f"duplicate selected fixture ID {fixture_id}")
            fixture_ids.add(fixture_id)
    return fixture_ids


def load_all_prior_fixture_ids(
    pilot_zip: Path,
    screen_zip: Path,
    previous_replication_zip: Path,
    v1_direction_zip: Path,
) -> tuple[set[str], dict[str, int]]:
    discovery = market_v1.load_market_rows(pilot_zip, screen_zip)
    discovery_ids = set(discovery["fixture_id"].astype(str))
    replication_ids = direction_v1.load_previous_selected_fixture_ids(
        previous_replication_zip
    )
    direction_ids = load_selected_fixture_ids(v1_direction_zip)

    counts = {
        "discovery": len(discovery_ids),
        "replication": len(replication_ids),
        "v1_direction": len(direction_ids),
    }
    if counts["discovery"] != EXPECTED_DISCOVERY_IDS:
        raise RuntimeError(f"expected {EXPECTED_DISCOVERY_IDS} discovery IDs, got {counts['discovery']}")
    if counts["replication"] != EXPECTED_REPLICATION_IDS:
        raise RuntimeError(f"expected {EXPECTED_REPLICATION_IDS} replication IDs, got {counts['replication']}")
    if counts["v1_direction"] != EXPECTED_V1_DIRECTION_IDS:
        raise RuntimeError(f"expected {EXPECTED_V1_DIRECTION_IDS} V1 direction IDs, got {counts['v1_direction']}")

    if discovery_ids & replication_ids:
        raise RuntimeError("discovery and replication IDs overlap")
    if discovery_ids & direction_ids:
        raise RuntimeError("discovery and V1 direction IDs overlap")
    if replication_ids & direction_ids:
        raise RuntimeError("replication and V1 direction IDs overlap")

    all_ids = discovery_ids | replication_ids | direction_ids
    if len(all_ids) != EXPECTED_EXCLUDED_IDS:
        raise RuntimeError(
            f"expected {EXPECTED_EXCLUDED_IDS} unique excluded IDs, got {len(all_ids)}"
        )
    return all_ids, counts


@dataclass
class MetadataProviderClient:
    key: str
    request_count: int = 0
    last_request_at: float | None = None

    def get_fixture_page(self, league_id: str, page: int) -> dict[str, Any]:
        path = f"/v1/leagues/{league_id}/fixtures"
        retries = 0
        while True:
            if self.request_count >= MAX_METADATA_REQUESTS:
                raise RuntimeError("metadata provider request budget exceeded")

            now = time.monotonic()
            if self.last_request_at is not None:
                remaining = replication.REQUEST_INTERVAL_SECONDS - (
                    now - self.last_request_at
                )
                if remaining > 0:
                    time.sleep(remaining)

            response = requests.get(
                replication.BASE_URL + path,
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Accept": "application/json",
                },
                params={
                    "status": "finished",
                    "order": "desc",
                    "page": page,
                    "per_page": LIST_PER_PAGE,
                },
                timeout=45,
            )
            self.last_request_at = time.monotonic()
            self.request_count += 1

            if response.status_code == 429:
                if retries >= replication.MAX_RATE_LIMIT_RETRIES:
                    raise RuntimeError(
                        "provider rate limit remained active after bounded retries"
                    )
                wait_seconds = replication._header_wait_seconds(response.headers)
                if wait_seconds is None:
                    raise RuntimeError("provider 429 without usable reset header")
                retries += 1
                time.sleep(wait_seconds)
                continue

            response.raise_for_status()
            payload = response.json()
            if payload.get("success") != 1:
                raise RuntimeError(f"provider API failure: {payload.get('error')}")
            return payload


def _page_reaches_before_cutoff(data: list[Any]) -> bool:
    cutoff = pd.Timestamp(v2.FUTURE_CUTOFF_UTC)
    for raw in data:
        if not isinstance(raw, dict):
            continue
        kickoff = pd.to_datetime(raw.get("kickoff_utc"), utc=True, errors="coerce")
        if not pd.isna(kickoff) and kickoff < cutoff:
            return True
    return False


def fetch_future_fixture_metadata(
    output_dir: Path,
    *,
    key: str,
) -> tuple[list[dict[str, Any]], int]:
    client = MetadataProviderClient(key=key)
    rows: list[dict[str, Any]] = []

    for league, league_id in replication.LEAGUES.items():
        if league not in v2.LEAGUE_ORDER:
            raise RuntimeError(f"unexpected league {league}")

        for page in range(1, MAX_PAGES_PER_LEAGUE + 1):
            payload = client.get_fixture_page(league_id, page)
            _write_json(
                output_dir / "raw" / "fixtures" / f"{league}_page_{page}.json",
                payload,
            )
            data = payload.get("data")
            if not isinstance(data, list):
                raise RuntimeError(f"{league}: invalid fixture metadata payload")

            for raw in data:
                if not isinstance(raw, dict):
                    continue
                fixture = replication._fixture_from_raw(raw, league)
                if fixture is None:
                    continue
                rows.append({**fixture, "status": "finished"})

            pagination = payload.get("pagination")
            has_more = (
                bool(pagination.get("has_more"))
                if isinstance(pagination, dict)
                else page < MAX_PAGES_PER_LEAGUE
            )
            if not has_more or _page_reaches_before_cutoff(data):
                break

    return rows, client.request_count


def run(
    pilot_zip: Path,
    screen_zip: Path,
    previous_replication_zip: Path,
    v1_direction_zip: Path,
    output_dir: Path,
    *,
    key: str | None = None,
) -> dict[str, Any]:
    key_value = (key or os.getenv(replication.KEY_ENV, "")).strip()
    if not key_value:
        raise RuntimeError(f"{replication.KEY_ENV} is required")

    excluded_ids, prior_counts = load_all_prior_fixture_ids(
        pilot_zip,
        screen_zip,
        previous_replication_zip,
        v1_direction_zip,
    )
    fixture_rows, request_count = fetch_future_fixture_metadata(
        output_dir,
        key=key_value,
    )
    if request_count > MAX_METADATA_REQUESTS:
        raise RuntimeError("metadata provider request budget exceeded")

    plan = v2.plan_future_cohort(fixture_rows, excluded_ids=excluded_ids)
    if plan["status"] not in {"WAIT_FOR_COHORT", "COHORT_LOCKED"}:
        raise RuntimeError(f"unexpected V2 planner status {plan['status']}")

    _write_json(
        output_dir / "excluded_fixture_ids.json",
        {
            "fixture_ids": sorted(excluded_ids),
            "counts": prior_counts,
            "total": len(excluded_ids),
        },
    )
    _write_json(output_dir / "future_fixture_metadata.json", fixture_rows)

    report = {
        **plan,
        "metadata_live_experiment_id": EXPERIMENT_ID,
        "provider": "5DollarFootballAPI",
        "provider_requests": int(request_count),
        "provider_request_budget": MAX_METADATA_REQUESTS,
        "prior_excluded_counts": prior_counts,
        "total_prior_excluded_fixture_ids": len(excluded_ids),
        "live_fixture_metadata_rows": len(fixture_rows),
        "live_action_scope": "FIXTURE_METADATA_ONLY",
        "market_prices_opened": False,
    }
    _write_json(output_dir / "cohort_plan.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-zip", type=Path, required=True)
    parser.add_argument("--screen-zip", type=Path, required=True)
    parser.add_argument("--previous-replication-zip", type=Path, required=True)
    parser.add_argument("--v1-direction-zip", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/corner_regime_adjusted_direction_v2_metadata"),
    )
    args = parser.parse_args()

    report = run(
        args.pilot_zip,
        args.screen_zip,
        args.previous_replication_zip,
        args.v1_direction_zip,
        args.output_dir,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
