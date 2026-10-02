from __future__ import annotations

import json
from pathlib import Path

import pytest

import v2b_corner_market_path_source_audit_v1 as mod


def _payload(fixture_id: int, *, bookmakers=1, timestamp=False, history=False):
    books=[]
    for i in range(bookmakers):
        corner={
            "opening":{"line":10.0,"over":1.9,"under":1.9},
            "closing":{"line":10.5,"over":1.9,"under":1.9},
            "inplay":{"line":11.0,"over":1.9,"under":1.9},
        }
        odds={"corner_line":corner}
        if history:
            odds["snapshot_history"]=[{"line":10.0},{"line":10.5}]
        book={"slug":f"book{i}","odds":odds}
        if timestamp:
            book["last_update"]="2026-09-01T00:00:00Z"
        books.append(book)
    return {"success":1,"data":{"fixture_id":fixture_id,"bookmakers":books}}


def _write_fixture_set(root: Path, *, timestamp=False, history=False, bookmakers=1):
    root.mkdir(parents=True,exist_ok=True)
    for i in range(mod.EXPECTED_RAW_FIXTURES):
        (root/f"{i}.json").write_text(
            json.dumps(_payload(i,bookmakers=bookmakers,timestamp=timestamp,history=history)),
            encoding="utf-8",
        )


def test_endpoint_only_payload_is_not_time_aligned_path(tmp_path):
    _write_fixture_set(tmp_path)
    report=mod.audit_raw_dir(tmp_path)
    assert report["status"]=="NO_TIME_ALIGNED_PATH_SOURCE"
    assert report["raw_fixture_count"]==43
    assert report["bookmaker_count_distribution"]=={"1":43}
    assert report["corner_state_presence"]=={"opening":43,"closing":43,"inplay":43}
    assert report["fixtures_with_time_like_fields"]==0
    assert report["fixtures_with_history_like_fields"]==0
    assert report["time_aligned_path_feasible"] is False
    assert report["cross_book_microstructure_feasible"] is False


def test_timestamped_history_allows_structural_path_flag(tmp_path):
    _write_fixture_set(tmp_path,timestamp=True,history=True)
    report=mod.audit_raw_dir(tmp_path)
    assert report["status"]=="TIME_ALIGNED_PATH_SOURCE_PRESENT"
    assert report["fixtures_with_time_like_fields"]==43
    assert report["fixtures_with_history_like_fields"]==43


def test_multiple_books_are_reported_separately(tmp_path):
    _write_fixture_set(tmp_path,bookmakers=2)
    report=mod.audit_raw_dir(tmp_path)
    assert report["fixtures_with_multiple_bookmakers"]==43
    assert report["cross_book_microstructure_feasible"] is True
    assert report["time_aligned_path_feasible"] is False


def test_wrong_raw_count_fails_closed(tmp_path):
    tmp_path.mkdir(exist_ok=True)
    (tmp_path/"1.json").write_text(json.dumps(_payload(1)),encoding="utf-8")
    with pytest.raises(RuntimeError,match="expected 43"):
        mod.audit_raw_dir(tmp_path)
