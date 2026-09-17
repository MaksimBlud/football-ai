import pytest

import totalcorner_corner_history as tc


def _payload():
    return {
        "success": 1,
        "data": [
            {
                "id": "12345",
                "h": "Home FC",
                "a": "Away FC",
                "l": "Test League",
                "start": "2025-05-10 15:00:00",
                "corner_list": [
                    ["0", "9.5", "1.90", "1.90", "2025-05-10 12:00:00", "0", "0"],
                    ["0", "10.0", "1.95", "1.85", "2025-05-10 14:59:59", "0", "0"],
                    ["1", "10.5", "1.80", "2.00", "2025-05-10 15:00:00", "0", "0"],
                    ["25", "6.0", "1.95", "1.85", "2025-05-10 15:25:00", "2", "1"],
                    ["0", "bad", "1.90", "1.90", "2025-05-10 13:00:00", "0", "0"],
                    ["0", "9.5", "1.00", "2.00", "2025-05-10 13:30:00", "0", "0"],
                ],
            }
        ],
    }


def test_normalize_corner_history_keeps_only_valid_prematch_rows():
    rows = tc.normalize_corner_history(_payload())
    assert len(rows) == 2
    assert [row["corner_line"] for row in rows] == [9.5, 10.0]
    assert rows[0]["match_id"] == "12345"
    assert rows[0]["source"] == "TOTALCORNER"
    assert all(row["observed_at"] < row["kickoff"] for row in rows)


def test_normalize_corner_history_accepts_camel_case_key():
    payload = _payload()
    match = payload["data"][0]
    match["cornerList"] = match.pop("corner_list")
    assert len(tc.normalize_corner_history(payload)) == 2


def test_normalize_corner_history_rejects_api_failure():
    with pytest.raises(ValueError, match="API failure"):
        tc.normalize_corner_history({"success": 0, "error": {"code": "NO_PERMISSION"}})


def test_fetch_refuses_network_without_explicit_token(monkeypatch):
    monkeypatch.delenv(tc.TOKEN_ENV, raising=False)
    called = False

    def forbidden_get(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("network must not be called")

    monkeypatch.setattr(tc.requests, "get", forbidden_get)
    with pytest.raises(RuntimeError, match=tc.TOKEN_ENV):
        tc.fetch_match_corner_history("12345")
    assert called is False


def test_fetch_rejects_non_numeric_match_id_before_network(monkeypatch):
    def forbidden_get(*args, **kwargs):
        raise AssertionError("network must not be called")

    monkeypatch.setattr(tc.requests, "get", forbidden_get)
    with pytest.raises(ValueError, match="numeric"):
        tc.fetch_match_corner_history("abc", token="dummy")
