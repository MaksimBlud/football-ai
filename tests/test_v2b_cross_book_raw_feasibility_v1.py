from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

import v2b_cross_book_raw_feasibility_v1 as mod


def _zip(tmp_path: Path, counts: list[int]) -> Path:
    path = tmp_path / "raw.zip"
    with zipfile.ZipFile(path, "w") as zf:
        for i, count in enumerate(counts, start=1):
            books = []
            for j in range(count):
                slug = "bet365" if j == 0 else f"book{j+1}"
                books.append({
                    "name": slug,
                    "slug": slug,
                    "odds": {
                        "corner_line": {
                            "opening": {"line": 10, "over": 1.9, "under": 1.9},
                            "closing": {"line": 10.5, "over": 1.9, "under": 1.9},
                        }
                    },
                })
            payload = {"success": 1, "data": {"fixture_id": i, "bookmakers": books}}
            zf.writestr(f"raw/odds/{i}.json", json.dumps(payload))
    return path


def test_bookmaker_extraction():
    payload={"data":{"bookmakers":[{"slug":"bet365"},{"slug":"pinnacle"}]}}
    assert [b["slug"] for b in mod._bookmakers(payload)]==["bet365","pinnacle"]


def test_single_bookmaker_support_is_insufficient(tmp_path, monkeypatch):
    path=_zip(tmp_path,[1]*43)
    digest=mod._file_sha256(path)
    report=mod.audit(path,expected_digest=digest)
    assert report["captured_raw_responses"]==43
    assert report["bookmaker_count_distribution"]=={"1":43}
    assert report["fixtures_with_2plus_bookmakers"]==0
    assert report["cross_book_direction_feature_feasible"] is False
    assert report["status"]=="INSUFFICIENT_CROSS_BOOK_DIVERSITY"
    assert report["provider_requests"]==0


def test_full_two_bookmaker_support_is_feasible(tmp_path):
    path=_zip(tmp_path,[2]*43)
    report=mod.audit(path,expected_digest=mod._file_sha256(path))
    assert report["bookmaker_count_distribution"]=={"2":43}
    assert report["fixtures_with_2plus_bookmakers"]==43
    assert report["cross_book_direction_feature_feasible"] is True
    assert report["status"]=="FULL_43_CROSS_BOOK_FEASIBLE"


def test_wrong_fixture_count_fails_closed(tmp_path):
    path=_zip(tmp_path,[1]*42)
    with pytest.raises(RuntimeError,match="expected 43"):
        mod.audit(path,expected_digest=mod._file_sha256(path))


def test_digest_mismatch_fails_closed(tmp_path):
    path=_zip(tmp_path,[1]*43)
    with pytest.raises(RuntimeError,match="digest mismatch"):
        mod.audit(path,expected_digest="sha256:"+"0"*64)
