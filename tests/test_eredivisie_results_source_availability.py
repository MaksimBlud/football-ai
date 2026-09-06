from pathlib import Path

import update_eredivisie_results as results_sync
from football_data_current_results import PublicResultsSourceUnavailable


def test_transient_public_source_outage_is_explicit_and_does_not_write(monkeypatch):
    url="https://www.football-data.co.uk/mmz4281/2627/N1.csv"
    def unavailable(_runtime):
        raise PublicResultsSourceUnavailable(url=url,status_code=503,attempts=3,detail="temporarily unavailable")
    writes=[]
    monkeypatch.setattr(results_sync,"fetch_current_finished_results",unavailable)
    monkeypatch.setattr(results_sync.persistence,"persist_results",lambda *_args,**_kwargs:writes.append(1))
    result=results_sync.sync_results(write=True,client=object())
    assert result=={"status":"SOURCE_UNAVAILABLE","source_url":url,"http_status":503,"inserted":0,"unchanged":0,"conflicts":0,"finished_rows":0,"public_http_requests":3,"paid_provider_requests":0}
    assert writes==[]


def test_non_transient_validation_error_still_fails_closed(monkeypatch):
    monkeypatch.setattr(results_sync,"fetch_current_finished_results",lambda _runtime:(_ for _ in ()).throw(ValueError("bad CSV schema")))
    try: results_sync.sync_results(write=True,client=object())
    except ValueError as exc: assert str(exc)=="bad CSV schema"
    else: raise AssertionError("schema errors must not become SOURCE_UNAVAILABLE")


def test_workflow_gates_evaluator_on_written_status():
    source=Path(".github/workflows/eredivisie-results.yml").read_text(encoding="utf-8")
    assert "--status-json artifacts/eredivisie_results_status.json" in source
    assert "SOURCE_UNAVAILABLE" in source
    assert 'if [ "$status" != "WRITTEN" ]; then' in source
    assert "SKIP evaluator: result status=$status" in source
    assert "evaluate_eredivisie_predictions.py" in source
