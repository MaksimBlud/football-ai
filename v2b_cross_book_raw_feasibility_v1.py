"""Audit bookmaker diversity in the immutable raw V2B corner-odds artifact.

Research-only source feasibility. Reads only the already-acquired raw responses
and reports whether cross-book microstructure can be reconstructed without any
new provider requests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

EXPERIMENT_ID = "V2B_CROSS_BOOK_RAW_FEASIBILITY_V1"
EXPECTED_RAW_ARTIFACT_ID = "10899611444"
EXPECTED_RAW_ARTIFACT_DIGEST = (
    "sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57"
)
EXPECTED_LOCKED_FIXTURES = 43


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _load_raw_payloads(raw_zip: Path) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(raw_zip) as zf:
        for name in zf.namelist():
            normalized = "/" + name.lstrip("/")
            if "/raw/odds/" not in normalized or not name.endswith(".json"):
                continue
            fixture_id = Path(name).stem
            if fixture_id in payloads:
                raise RuntimeError(f"duplicate raw response for fixture {fixture_id}")
            payload = json.loads(zf.read(name).decode("utf-8"))
            if not isinstance(payload, dict):
                raise RuntimeError(f"raw response {fixture_id} must be a JSON object")
            payloads[fixture_id] = payload
    return payloads


def _bookmakers(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    books = data.get("bookmakers")
    if not isinstance(books, list):
        return []
    return [item for item in books if isinstance(item, dict)]


def audit(raw_zip: Path, *, expected_digest: str = EXPECTED_RAW_ARTIFACT_DIGEST) -> dict[str, Any]:
    actual_digest = _file_sha256(raw_zip)
    if actual_digest != expected_digest:
        raise RuntimeError(
            f"raw artifact digest mismatch: expected {expected_digest}, got {actual_digest}"
        )

    payloads = _load_raw_payloads(raw_zip)
    if len(payloads) != EXPECTED_LOCKED_FIXTURES:
        raise RuntimeError(
            f"expected {EXPECTED_LOCKED_FIXTURES} raw responses, got {len(payloads)}"
        )

    bookmaker_count_distribution: Counter[int] = Counter()
    slug_counts: Counter[str] = Counter()
    name_counts: Counter[str] = Counter()
    fixtures_with_2plus: list[str] = []
    fixtures_without_books: list[str] = []
    fixtures_with_corner_opening = 0
    fixtures_with_corner_closing = 0
    fixtures_with_corner_inplay = 0
    rows: list[dict[str, Any]] = []

    for fixture_id in sorted(payloads):
        payload = payloads[fixture_id]
        books = _bookmakers(payload)
        bookmaker_count_distribution[len(books)] += 1
        if not books:
            fixtures_without_books.append(fixture_id)
        if len(books) >= 2:
            fixtures_with_2plus.append(fixture_id)

        slugs: list[str] = []
        names: list[str] = []
        opening = closing = inplay = False
        for book in books:
            slug = str(book.get("slug") or "").strip()
            name = str(book.get("name") or "").strip()
            if slug:
                slug_counts[slug] += 1
                slugs.append(slug)
            if name:
                name_counts[name] += 1
                names.append(name)

            odds = book.get("odds")
            if not isinstance(odds, dict):
                continue
            corner_line = odds.get("corner_line")
            if not isinstance(corner_line, dict):
                continue
            opening = opening or isinstance(corner_line.get("opening"), dict)
            closing = closing or isinstance(corner_line.get("closing"), dict)
            inplay = inplay or isinstance(corner_line.get("inplay"), dict)

        fixtures_with_corner_opening += int(opening)
        fixtures_with_corner_closing += int(closing)
        fixtures_with_corner_inplay += int(inplay)
        rows.append(
            {
                "fixture_id": fixture_id,
                "bookmaker_count": len(books),
                "bookmaker_slugs": slugs,
                "bookmaker_names": names,
                "has_corner_opening": opening,
                "has_corner_closing": closing,
                "has_corner_inplay": inplay,
            }
        )

    multi_book_feasible = len(fixtures_with_2plus) == EXPECTED_LOCKED_FIXTURES
    partial_multi_book_support = len(fixtures_with_2plus) > 0

    if multi_book_feasible:
        status = "FULL_43_CROSS_BOOK_FEASIBLE"
    elif partial_multi_book_support:
        status = "PARTIAL_CROSS_BOOK_SUPPORT"
    else:
        status = "INSUFFICIENT_CROSS_BOOK_DIVERSITY"

    return {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "source_feasibility_audit": True,
        "source_raw_artifact_id": EXPECTED_RAW_ARTIFACT_ID,
        "source_raw_artifact_digest": actual_digest,
        "locked_fixture_count": EXPECTED_LOCKED_FIXTURES,
        "captured_raw_responses": len(payloads),
        "status": status,
        "bookmaker_count_distribution": {
            str(k): int(v) for k, v in sorted(bookmaker_count_distribution.items())
        },
        "unique_bookmaker_slugs": sorted(slug_counts),
        "bookmaker_slug_fixture_counts": dict(sorted(slug_counts.items())),
        "unique_bookmaker_names": sorted(name_counts),
        "bookmaker_name_fixture_counts": dict(sorted(name_counts.items())),
        "fixtures_with_2plus_bookmakers": len(fixtures_with_2plus),
        "fixture_ids_with_2plus_bookmakers": fixtures_with_2plus,
        "fixtures_without_bookmakers": len(fixtures_without_books),
        "fixture_ids_without_bookmakers": fixtures_without_books,
        "fixtures_with_corner_opening": fixtures_with_corner_opening,
        "fixtures_with_corner_closing": fixtures_with_corner_closing,
        "fixtures_with_corner_inplay": fixtures_with_corner_inplay,
        "cross_book_direction_feature_feasible": multi_book_feasible,
        "partial_cross_book_support": partial_multi_book_support,
        "market_direction_evaluated": False,
        "centre_delta_read": False,
        "match_outcome_used": False,
        "football_state_used": False,
        "provider_requests": 0,
        "supabase_operations": 0,
        "production_model_operations": 0,
        "interpretation": (
            "Existing immutable V2B raw responses do not support a cross-book "
            "microstructure feature unless at least two bookmakers are present "
            "within the same stored fixture response."
        ),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-odds-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = audit(args.raw_odds_zip)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
