from types import SimpleNamespace

import pandas as pd
import pytest

from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG
from football_data_current_results import (
    build_finished_frame,
    configured_current_csv_url,
    configured_latest_results_csv_url,
    fetch_current_finished_results,
)
from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


def _raw(rows):
    return pd.DataFrame(rows, columns=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"])


def test_current_urls_are_explicit_2627_contracts():
    assert configured_current_csv_url(SERIE_A_RUNTIME_CONFIG).endswith("/2627/I1.csv")
    assert configured_current_csv_url(BUNDESLIGA_RUNTIME_CONFIG).endswith("/2627/D1.csv")
    assert configured_current_csv_url(LIGUE1_RUNTIME_CONFIG).endswith("/2627/F1.csv")
    assert configured_current_csv_url(EREDIVISIE_RUNTIME_CONFIG).endswith("/2627/N1.csv")
    assert configured_current_csv_url(TURKEY_SUPER_LIG_RUNTIME_CONFIG).endswith("/2627/T1.csv")
    assert configured_current_csv_url(PRIMEIRA_LIGA_RUNTIME_CONFIG).endswith("/2627/P1.csv")
    assert configured_latest_results_csv_url(SERIE_A_RUNTIME_CONFIG).endswith("/2627/Latest_Results.csv")


def test_finished_frame_filters_unfinished_rows_and_applies_aliases():
    raw = _raw([
        ["29/08/2026", "Inter", "Milan", 2, 1, "H"],
        ["30/08/2026", "Roma", "Verona", None, None, None],
    ])
    frame = build_finished_frame(raw, SERIE_A_RUNTIME_CONFIG)
    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["league"] == "SERIE_A"
    assert row["season"] == "2026-2027"
    assert row["home_team"] == "Inter Milan"
    assert row["away_team"] == "AC Milan"
    assert int(row["home_goals"]) == 2
    assert int(row["away_goals"]) == 1
    assert row["result"] == "H"
    assert "source" not in frame.columns
    assert "source_competition" not in frame.columns


def test_finished_row_with_missing_goals_fails_closed():
    raw = _raw([["29/08/2026", "A", "B", None, 1, "A"]])
    with pytest.raises(ValueError, match="missing/non-numeric goals"):
        build_finished_frame(raw, BUNDESLIGA_RUNTIME_CONFIG)


def test_unexpected_nonblank_result_fails_closed():
    raw = _raw([["29/08/2026", "A", "B", 1, 1, "X"]])
    with pytest.raises(ValueError, match="Unexpected Football-Data full-time result"):
        build_finished_frame(raw, LIGUE1_RUNTIME_CONFIG)


def test_fetch_reports_zero_paid_provider_requests():
    csv = "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n29/08/2026,Inter,Milan,2,1,H\n"
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return SimpleNamespace(status_code=200, text=csv)

    result = fetch_current_finished_results(SERIE_A_RUNTIME_CONFIG, get=fake_get)
    assert result["paid_provider_requests"] == 0
    assert result["public_http_requests"] == 1
    assert result["source_rows"] == 1
    assert result["finished_rows"] == 1
    assert result["fallback_used"] is False
    assert result["source_url"] == configured_current_csv_url(SERIE_A_RUNTIME_CONFIG)
    assert calls == [(configured_current_csv_url(SERIE_A_RUNTIME_CONFIG), 30)]


def test_transient_503_is_retried_then_succeeds_without_fallback():
    csv = "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n29/08/2026,A,B,1,0,H\n"
    responses = [
        SimpleNamespace(status_code=503, text="temporary"),
        SimpleNamespace(status_code=503, text="temporary"),
        SimpleNamespace(status_code=200, text=csv),
    ]
    sleeps = []

    def fake_get(_url, timeout):
        assert timeout == 30
        return responses.pop(0)

    result = fetch_current_finished_results(
        TURKEY_SUPER_LIG_RUNTIME_CONFIG,
        get=fake_get,
        sleep=sleeps.append,
    )
    assert result["public_http_requests"] == 3
    assert result["paid_provider_requests"] == 0
    assert result["finished_rows"] == 1
    assert result["fallback_used"] is False
    assert sleeps == [1.0, 2.0]


def test_primary_availability_exhaustion_falls_back_to_official_latest_results():
    latest_csv = (
        "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
        "SP1,29/08/2026,Wrong,League,1,0,H\n"
        "I1,29/08/2026,Inter,Milan,2,1,H\n"
        "I1,30/08/2026,Roma,Verona,,,\n"
    )
    calls = []
    primary = configured_current_csv_url(SERIE_A_RUNTIME_CONFIG)
    latest = configured_latest_results_csv_url(SERIE_A_RUNTIME_CONFIG)

    def fake_get(url, timeout):
        calls.append((url, timeout))
        if url == primary:
            return SimpleNamespace(status_code=503, text="temporary")
        assert url == latest
        return SimpleNamespace(status_code=200, text=latest_csv)

    sleeps = []
    result = fetch_current_finished_results(
        SERIE_A_RUNTIME_CONFIG,
        get=fake_get,
        sleep=sleeps.append,
    )
    assert result["fallback_used"] is True
    assert result["source_url"] == latest
    assert result["primary_source_url"] == primary
    assert result["primary_unavailable_status"] == 503
    assert result["public_http_requests"] == 4
    assert result["paid_provider_requests"] == 0
    assert result["source_rows"] == 2
    assert result["finished_rows"] == 1
    assert result["frame"].iloc[0]["home_team"] == "Inter Milan"
    assert calls == [(primary, 30), (primary, 30), (primary, 30), (latest, 30)]
    assert sleeps == [1.0, 2.0]


def test_latest_results_missing_configured_division_fails_closed():
    latest_csv = "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\nSP1,29/08/2026,A,B,1,0,H\n"
    primary = configured_current_csv_url(SERIE_A_RUNTIME_CONFIG)

    def fake_get(url, timeout):
        if url == primary:
            return SimpleNamespace(status_code=503, text="temporary")
        return SimpleNamespace(status_code=200, text=latest_csv)

    with pytest.raises(ValueError, match="missing configured division I1"):
        fetch_current_finished_results(
            SERIE_A_RUNTIME_CONFIG,
            get=fake_get,
            sleep=lambda _seconds: None,
        )


def test_latest_results_without_div_column_fails_closed():
    latest_csv = "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n29/08/2026,A,B,1,0,H\n"
    primary = configured_current_csv_url(SERIE_A_RUNTIME_CONFIG)

    def fake_get(url, timeout):
        if url == primary:
            return SimpleNamespace(status_code=503, text="temporary")
        return SimpleNamespace(status_code=200, text=latest_csv)

    with pytest.raises(ValueError, match="division column: Div"):
        fetch_current_finished_results(
            SERIE_A_RUNTIME_CONFIG,
            get=fake_get,
            sleep=lambda _seconds: None,
        )


def test_primary_semantic_error_does_not_activate_fallback():
    bad_csv = "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n29/08/2026,A,B,1,0,X\n"
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return SimpleNamespace(status_code=200, text=bad_csv)

    with pytest.raises(ValueError, match="Unexpected Football-Data full-time result"):
        fetch_current_finished_results(SERIE_A_RUNTIME_CONFIG, get=fake_get)
    assert calls == [configured_current_csv_url(SERIE_A_RUNTIME_CONFIG)]


def test_transient_failures_stop_after_bounded_attempts_on_both_public_urls():
    calls = []
    sleeps = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return SimpleNamespace(status_code=503, text="temporary")

    with pytest.raises(RuntimeError, match=r"HTTP 503 after 3 attempt\(s\)"):
        fetch_current_finished_results(
            PRIMEIRA_LIGA_RUNTIME_CONFIG,
            get=fake_get,
            sleep=sleeps.append,
        )
    primary = configured_current_csv_url(PRIMEIRA_LIGA_RUNTIME_CONFIG)
    latest = configured_latest_results_csv_url(PRIMEIRA_LIGA_RUNTIME_CONFIG)
    assert calls == [(primary, 30)] * 3 + [(latest, 30)] * 3
    assert sleeps == [1.0, 2.0, 1.0, 2.0]


def test_permanent_http_error_fails_immediately_without_fallback_or_retry():
    calls = []
    sleeps = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return SimpleNamespace(status_code=404, text="not found")

    with pytest.raises(RuntimeError, match=r"HTTP 404 after 1 attempt\(s\)"):
        fetch_current_finished_results(
            SERIE_A_RUNTIME_CONFIG,
            get=fake_get,
            sleep=sleeps.append,
        )
    assert calls == [(configured_current_csv_url(SERIE_A_RUNTIME_CONFIG), 30)]
    assert sleeps == []


def test_invalid_retry_attempt_count_fails_closed_before_http():
    calls = []
    with pytest.raises(ValueError, match="max_attempts"):
        fetch_current_finished_results(
            SERIE_A_RUNTIME_CONFIG,
            get=lambda *_a, **_k: calls.append(1),
            max_attempts=0,
        )
    assert calls == []


def test_non_csv_runtime_contract_is_rejected_without_http(monkeypatch):
    from dataclasses import replace
    from league_runtime_config import FinishedResultsSourceConfig

    cfg = replace(
        SERIE_A_RUNTIME_CONFIG,
        finished_results_source=FinishedResultsSourceConfig(
            provider="THE_ODDS_API",
            competition_code="soccer_italy_serie_a",
            season="2026-2027",
            season_code="2026",
        ),
    )
    with pytest.raises(ValueError, match="provider is not FOOTBALL_DATA_CSV"):
        configured_current_csv_url(cfg)
