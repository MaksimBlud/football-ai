from pathlib import Path

import pandas as pd
import pytest

import update_serie_a_results as results_sync
from espn_current_results_fallback import ESPNResultsSourceUnavailable
from football_data_current_results import PublicResultsSourceUnavailable


def _frame():
    return pd.DataFrame([
        {
            "league": "SERIE_A",
            "season": "2026-2027",
            "match_date": pd.Timestamp("2026-09-06"),
            "home_team": "Bologna",
            "away_team": "Sassuolo",
            "home_goals": 2,
            "away_goals": 2,
            "result": "D",
        }
    ])


def _primary_provider():
    frame = _frame()
    return {
        "frame": frame,
        "source_url": "https://www.football-data.co.uk/mmz4281/2627/I1.csv",
        "public_http_requests": 1,
        "paid_provider_requests": 0,
        "source_rows": 1,
        "finished_rows": 1,
    }


def _fallback_provider():
    frame = _frame()
    return {
        "frame": frame,
        "source_url": "https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard?dates=x",
        "source_provider": "ESPN_SCOREBOARD_FALLBACK",
        "source_competition": "ita.1",
        "public_http_requests": 1,
        "paid_provider_requests": 0,
        "source_rows": 1,
        "finished_rows": 1,
    }


def _primary_unavailable(_runtime):
    raise PublicResultsSourceUnavailable(
        url="https://www.football-data.co.uk/mmz4281/2627/I1.csv",
        status_code=503,
        attempts=3,
        detail="temporarily unavailable",
    )


def test_primary_success_never_calls_fallback(monkeypatch):
    calls = []
    monkeypatch.setattr(
        results_sync.persistence,
        "persist_results",
        lambda *_args, **_kwargs: {"inserted": 0, "unchanged": 1, "conflicts": 0},
    )
    result = results_sync.sync_results(
        write=True,
        client=object(),
        fetch_fn=lambda _runtime: _primary_provider(),
        fallback_fn=lambda: calls.append("fallback"),
    )
    assert calls == []
    assert result["status"] == "WRITTEN"
    assert result["fallback_used"] is False
    assert result["source_provider"] == "FOOTBALL_DATA_CSV"
    assert result["paid_provider_requests"] == 0


def test_transient_primary_outage_uses_fallback_and_persists(monkeypatch):
    writes = []

    def persist(_client, frame, _config):
        writes.append(frame.copy())
        return {"inserted": 1, "unchanged": 0, "conflicts": 0}

    monkeypatch.setattr(results_sync.persistence, "persist_results", persist)
    result = results_sync.sync_results(
        write=True,
        client=object(),
        fetch_fn=_primary_unavailable,
        fallback_fn=_fallback_provider,
    )
    assert len(writes) == 1
    assert result["status"] == "WRITTEN"
    assert result["fallback_used"] is True
    assert result["source_provider"] == "ESPN_SCOREBOARD_FALLBACK"
    assert result["primary_public_http_requests"] == 3
    assert result["fallback_public_http_requests"] == 1
    assert result["public_http_requests"] == 4
    assert result["inserted"] == 1
    assert result["paid_provider_requests"] == 0


def test_both_public_sources_unavailable_is_explicit_and_does_not_write(monkeypatch):
    writes = []

    def fallback_unavailable():
        raise ESPNResultsSourceUnavailable(
            url="https://site.api.espn.com/scoreboard",
            status_code=503,
            attempts=3,
            detail="temporarily unavailable",
        )

    monkeypatch.setattr(
        results_sync.persistence,
        "persist_results",
        lambda *_args, **_kwargs: writes.append(1),
    )
    result = results_sync.sync_results(
        write=True,
        client=object(),
        fetch_fn=_primary_unavailable,
        fallback_fn=fallback_unavailable,
    )
    assert result["status"] == "SOURCE_UNAVAILABLE"
    assert result["primary_http_status"] == 503
    assert result["http_status"] == 503
    assert result["primary_public_http_requests"] == 3
    assert result["fallback_public_http_requests"] == 3
    assert result["public_http_requests"] == 6
    assert result["inserted"] == 0
    assert result["conflicts"] == 0
    assert result["paid_provider_requests"] == 0
    assert writes == []


def test_non_transient_validation_error_still_fails_closed():
    fallback_calls = []
    with pytest.raises(ValueError, match="bad CSV schema"):
        results_sync.sync_results(
            write=True,
            client=object(),
            fetch_fn=lambda _runtime: (_ for _ in ()).throw(ValueError("bad CSV schema")),
            fallback_fn=lambda: fallback_calls.append(1),
        )
    assert fallback_calls == []


def test_workflow_gates_evaluator_on_written_status():
    source = Path(".github/workflows/serie-a-results.yml").read_text(encoding="utf-8")
    assert "--status-json artifacts/serie_a_results_status.json" in source
    assert "SOURCE_UNAVAILABLE" in source
    assert 'if [ "$status" != "WRITTEN" ]; then' in source
    assert "SKIP evaluator: result status=$status" in source
    assert "evaluate_serie_a_predictions.py" in source
