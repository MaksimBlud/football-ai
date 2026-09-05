from datetime import date

import pandas as pd

import audit_turkey_portugal_historical_market as audit
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG


def frame(rows=3):
    return pd.DataFrame({
        "Date": ["01/01/2020"] * rows,
        "HomeTeam": ["A"] * rows,
        "AwayTeam": ["B"] * rows,
        "AvgH": [2.0, 2.1, None][:rows],
        "AvgD": [3.0, 3.1, 3.2][:rows],
        "AvgA": [4.0, 4.1, 4.2][:rows],
    })


def test_audit_is_completed_seasons_only_and_reconciles_coverage(monkeypatch):
    source = frame()
    monkeypatch.setattr(audit, "fetch_frame", lambda session, code, competition: source.copy())
    result = audit.audit_league(
        PRIMEIRA_LIGA_RUNTIME_CONFIG,
        as_of=date(2026, 9, 5),
        session=object(),
    )
    assert result["completed_seasons"] == 10
    assert result["market_source"] == "FOOTBALL_DATA_AVERAGE"
    assert result["market_columns"] == ["AvgH", "AvgD", "AvgA"]
    assert result["rows"] == 30
    assert result["valid_market_rows"] == 20
    assert result["coverage"] == 2 / 3


def test_current_season_is_not_read(monkeypatch):
    calls = []
    source = frame(2)

    def fake_fetch(session, code, competition):
        calls.append(code)
        return source.copy()

    monkeypatch.setattr(audit, "fetch_frame", fake_fetch)
    audit.audit_league(
        PRIMEIRA_LIGA_RUNTIME_CONFIG,
        as_of=date(2026, 9, 5),
        session=object(),
    )
    assert "2627" not in calls
    assert len(calls) == 10


def test_no_result_columns_are_required(monkeypatch):
    source = frame(2)
    assert "FTR" not in source.columns
    monkeypatch.setattr(audit, "fetch_frame", lambda session, code, competition: source.copy())
    result = audit.audit_league(
        PRIMEIRA_LIGA_RUNTIME_CONFIG,
        as_of=date(2026, 9, 5),
        session=object(),
    )
    assert result["valid_market_rows"] == 20
