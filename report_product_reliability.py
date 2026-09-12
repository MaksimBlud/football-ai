"""Read-only Product Reliability / Calibration report.

This command reads immutable lifecycle events from Supabase and prints either the
full reliability matrix or one exact model/league slice. It performs no writes,
training, calibration fitting, model promotion, Odds API calls, or result fetches.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from product_lifecycle import LIFECYCLE_TABLE
from product_reliability import (
    build_reliability_matrix,
    reliability_summary,
    settled_reliability_records,
)


DEFAULT_PAGE_SIZE = 500


def fetch_lifecycle_events(
    client: Any,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> list[dict[str, Any]]:
    if page_size < 1:
        raise ValueError("page_size must be >= 1")

    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        response = (
            client.table(LIFECYCLE_TABLE)
            .select("*")
            .order("id")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        page = response.data or []
        rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--league", default=None)
    parser.add_argument("--model-sha256", default=None)
    args = parser.parse_args()
    if bool(args.league) != bool(args.model_sha256):
        parser.error("--league and --model-sha256 must be supplied together")
    return args


def main() -> None:
    args = parse_args()
    from database import supabase

    events = fetch_lifecycle_events(supabase)
    if args.league and args.model_sha256:
        records = settled_reliability_records(events)
        report = reliability_summary(
            records,
            league=args.league,
            model_1x2_sha256=args.model_sha256,
        )
    else:
        report = build_reliability_matrix(events)

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    print("PASS: READ-ONLY PRODUCT RELIABILITY REPORT COMPLETE")


if __name__ == "__main__":
    main()
