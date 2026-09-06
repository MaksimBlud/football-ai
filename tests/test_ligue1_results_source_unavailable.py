from pathlib import Path

import pytest

import update_ligue1_results as results
from football_data_current_results import PublicResultsSourceUnavailable


def test_ligue1_transient_public_results_outage_is_explicit_and_write_free(monkeypatch):
    def fail_fetch(_config):
        raise PublicResultsSourceUnavailable(
            url="https://www.football-data.co.uk/mmz4281/2627/F1.csv",
            status_code=503,
            attempts=3,
            detail="temporarily unavailable",
        )

    persisted = []
    monkeypatch.setattr(results, "fetch_current_finished_results", fail_fetch)
    monkeypatch.setattr(results.persistence, "persist_results", lambda *args, **kwargs: persisted.append(True))

    out = results.sync_results(write=True, client=object())

    assert out["status"] == "SOURCE_UNAVAILABLE"
    assert out["http_status"] == 503
    assert out["public_http_requests"] == 3
    assert out["paid_provider_requests"] == 0
    assert out["inserted"] == 0
    assert out["conflicts"] == 0
    assert persisted == []


def test_ligue1_permanent_or_schema_errors_still_fail(monkeypatch):
    monkeypatch.setattr(
        results,
        "fetch_current_finished_results",
        lambda _config: (_ for _ in ()).throw(ValueError("schema mismatch")),
    )

    with pytest.raises(ValueError, match="schema mismatch"):
        results.sync_results(write=True, client=object())


def test_status_json_records_failed_non_transient_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(results, "sync_results", lambda write=False: (_ for _ in ()).throw(ValueError("bad schema")))
    status = tmp_path / "status.json"
    monkeypatch.setattr("sys.argv", ["update_ligue1_results.py", "--write", "--status-json", str(status)])

    with pytest.raises(ValueError, match="bad schema"):
        results.main()

    text = status.read_text(encoding="utf-8")
    assert '"status": "FAILED"' in text
    assert '"error_type": "ValueError"' in text
    assert '"paid_provider_requests": 0' in text
