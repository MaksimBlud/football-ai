import update_turkey_portugal_results as results_sync
from multi_market_policy import CORNER_SOURCE_READY_LEAGUES, UNPUBLISHED_CURRENT_CORNER_SOURCE_LEAGUES


def test_turkey_current_corner_source_is_explicitly_unpublished():
    assert "TURKEY_SUPER_LIG" in UNPUBLISHED_CURRENT_CORNER_SOURCE_LEAGUES
    assert "TURKEY_SUPER_LIG" not in CORNER_SOURCE_READY_LEAGUES
    assert "PRIMEIRA_LIGA" in CORNER_SOURCE_READY_LEAGUES


def test_turkey_results_sync_does_not_request_unpublished_current_csv(monkeypatch):
    def forbidden_fetch(_runtime):
        raise AssertionError("unpublished Turkey current-season CSV must not be requested")

    monkeypatch.setattr(results_sync, "fetch_current_finished_results", forbidden_fetch)
    result = results_sync.sync_results("TURKEY_SUPER_LIG", write=True, client=object())

    assert result == {
        "status": "SOURCE_NOT_PUBLISHED",
        "finished_rows": 0,
        "inserted": 0,
        "unchanged": 0,
        "conflicts": 0,
        "paid_provider_requests": 0,
    }
