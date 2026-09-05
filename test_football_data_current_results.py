from types import SimpleNamespace

import pandas as pd
import pytest

from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
from football_data_current_results import (
    fetch_current_results,
    normalize_current_results,
    source_url,
)
from league_runtime_config import EPL_RUNTIME_CONFIG
from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG


def test_explicit_current_source_contracts_use_2627_csv_codes():
    assert source_url(SERIE_A_RUNTIME_CONFIG).endswith("/2627/I1.csv")
    assert source_url(BUNDESLIGA_RUNTIME_CONFIG).endswith("/2627/D1.csv")
    assert source_url(LIGUE1_RUNTIME_CONFIG).endswith("/2627/F1.csv")


def test_non_csv_finished_source_is_rejected_without_guessing():
    with pytest.raises(ValueError, match="not FOOTBALL_DATA_CSV"):
        source_url(EPL_RUNTIME_CONFIG)


def test_current_normalization_filters_unfinished_rows_and_applies_aliases():
    raw = pd.DataFrame([
        {"Date":"04/09/2026","HomeTeam":"Inter","AwayTeam":"Roma","FTHG":2,"FTAG":1,"FTR":"H"},
        {"Date":"05/09/2026","HomeTeam":"Milan","AwayTeam":"Verona","FTHG":None,"FTAG":None,"FTR":"nan"},
    ])
    result = normalize_current_results(raw, SERIE_A_RUNTIME_CONFIG)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["league"] == "SERIE_A"
    assert row["season"] == "2026-2027"
    assert row["home_team"] == "Inter Milan"
    assert row["away_team"] == "AS Roma"
    assert row["home_goals"] == 2
    assert row["away_goals"] == 1
    assert row["source"] == "football-data-csv"
    assert row["source_competition"] == "I1"


class FakeResponse:
    text = "Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n04/09/2026,Genoa,Como,1,4,A\n"
    def raise_for_status(self): pass


class FakeSession:
    def __init__(self): self.calls = []
    def get(self, url, timeout):
        self.calls.append((url, timeout))
        return FakeResponse()


def test_fetch_is_public_csv_only_and_reports_zero_odds_api_usage():
    session = FakeSession()
    frame, report = fetch_current_results(SERIE_A_RUNTIME_CONFIG, session=session)
    assert len(frame) == 1
    assert session.calls == [(source_url(SERIE_A_RUNTIME_CONFIG), 30)]
    assert report["provider"] == "FOOTBALL_DATA_CSV"
    assert report["odds_api_requests"] == 0
    assert report["odds_api_credits"] == 0
