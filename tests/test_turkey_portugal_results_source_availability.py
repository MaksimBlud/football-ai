import update_turkey_portugal_results as results_sync
from football_data_current_results import PublicResultsSourceUnavailable
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
        "public_http_requests": 0,
        "paid_provider_requests": 0,
    }


def test_portugal_bounded_transient_outage_is_explicit_and_does_not_write(monkeypatch):
    url = "https://www.football-data.co.uk/mmz4281/2627/P1.csv"

    def unavailable(_runtime):
        raise PublicResultsSourceUnavailable(
            url=url,
            status_code=503,
            attempts=3,
            detail="temporarily unavailable",
        )

    writes = []
    monkeypatch.setattr(results_sync, "fetch_current_finished_results", unavailable)
    monkeypatch.setattr(results_sync.persistence, "persist_results", lambda *_args, **_kwargs: writes.append(1))

    result = results_sync.sync_results("PRIMEIRA_LIGA", write=True, client=object())

    assert result == {
        "status": "SOURCE_UNAVAILABLE",
        "source_url": url,
        "http_status": 503,
        "finished_rows": 0,
        "inserted": 0,
        "unchanged": 0,
        "conflicts": 0,
        "public_http_requests": 3,
        "paid_provider_requests": 0,
    }
    assert writes == []


def test_non_transient_provider_or_validation_error_still_fails_closed(monkeypatch):
    monkeypatch.setattr(
        results_sync,
        "fetch_current_finished_results",
        lambda _runtime: (_ for _ in ()).throw(ValueError("bad CSV schema")),
    )

    try:
        results_sync.sync_results("PRIMEIRA_LIGA", write=True, client=object())
    except ValueError as exc:
        assert str(exc) == "bad CSV schema"
    else:
        raise AssertionError("schema errors must not be converted into SOURCE_UNAVAILABLE")
