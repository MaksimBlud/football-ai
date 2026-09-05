from types import SimpleNamespace

import pandas as pd

import audit_multi_market_corner_outcomes as audit
from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
from league_runtime_config import LA_LIGA_RUNTIME_CONFIG, EPL_RUNTIME_CONFIG
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG
from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG


def test_configured_contracts_are_repo_owned_not_guessed():
    la = audit.configured_csv_contract(LA_LIGA_RUNTIME_CONFIG)
    assert la == {"contract_source": "finished_results_source", "competition_code": "SP1", "season_code": "2627"}
    assert audit.configured_csv_contract(SERIE_A_RUNTIME_CONFIG)["competition_code"] == "I1"
    assert audit.configured_csv_contract(BUNDESLIGA_RUNTIME_CONFIG)["competition_code"] == "D1"
    assert audit.configured_csv_contract(LIGUE1_RUNTIME_CONFIG)["competition_code"] == "F1"
    assert audit.configured_csv_contract(EREDIVISIE_RUNTIME_CONFIG)["season_code"] == "2627"
    assert audit.configured_csv_contract(TURKEY_SUPER_LIG_RUNTIME_CONFIG)["competition_code"] == "T1"
    assert audit.configured_csv_contract(PRIMEIRA_LIGA_RUNTIME_CONFIG)["competition_code"] == "P1"
    assert audit.configured_csv_contract(EPL_RUNTIME_CONFIG) is None


def _frame():
    return pd.DataFrame({
        "Date": ["01/09/2026", "02/09/2026", "03/09/2026"],
        "HomeTeam": ["Ath Madrid", "Real Madrid", "Barcelona"],
        "AwayTeam": ["Barcelona", "Valencia", "Sevilla"],
        "FTHG": [2, 1, None], "FTAG": [1, 1, None], "FTR": ["H", "D", ""],
        "HC": [7, 5, None], "AC": [3, 4, None],
    })


def test_complete_finished_corner_coverage_and_alias_diagnostics():
    contract = audit.configured_csv_contract(LA_LIGA_RUNTIME_CONFIG)
    result = audit.audit_frame(LA_LIGA_RUNTIME_CONFIG, _frame(), contract, "https://example.invalid/2627/SP1.csv")
    assert result["finished_rows"] == 2
    assert result["valid_corner_rows"] == 2
    assert result["corner_coverage_finished"] == 1.0
    assert result["status"] == "CORNER_OUTCOME_COVERAGE_COMPLETE"
    assert result["aliases_applied_finished"] == 1
    assert result["canonical_identity_duplicates_finished"] == 0


def test_partial_corner_coverage_is_not_promoted_to_complete():
    frame = _frame(); frame.loc[1, "HC"] = None
    result = audit.audit_frame(LA_LIGA_RUNTIME_CONFIG, frame, audit.configured_csv_contract(LA_LIGA_RUNTIME_CONFIG), "x")
    assert result["finished_rows"] == 2
    assert result["valid_corner_rows"] == 1
    assert result["corner_coverage_finished"] == 0.5
    assert result["status"] == "CORNER_OUTCOME_COVERAGE_PARTIAL"
    assert result["home_corner_diagnostics_finished"]["missing_or_non_numeric"] == 1


def test_negative_and_noninteger_corner_values_are_invalid():
    frame = _frame(); frame.loc[0, "HC"] = -1; frame.loc[1, "AC"] = 4.5
    result = audit.audit_frame(LA_LIGA_RUNTIME_CONFIG, frame, audit.configured_csv_contract(LA_LIGA_RUNTIME_CONFIG), "x")
    assert result["valid_corner_rows"] == 0
    assert result["home_corner_diagnostics_finished"]["negative"] == 1
    assert result["away_corner_diagnostics_finished"]["non_integer"] == 1


def test_missing_corner_columns_are_explicit():
    frame = _frame().drop(columns=["HC", "AC"])
    result = audit.audit_frame(LA_LIGA_RUNTIME_CONFIG, frame, audit.configured_csv_contract(LA_LIGA_RUNTIME_CONFIG), "x")
    assert result["status"] == "CORNER_COLUMNS_MISSING"
    assert result["valid_corner_rows"] == 0


class FakeResponse:
    def __init__(self, text): self.text = text
    def raise_for_status(self): return None


class FakeSession:
    def __init__(self, text): self.text = text; self.calls = []
    def get(self, url, timeout):
        self.calls.append((url, timeout)); return FakeResponse(self.text)


def test_run_audit_fetches_only_explicitly_configured_csv_leagues():
    session = FakeSession(_frame().to_csv(index=False))
    report = audit.run_audit(session=session)
    assert report["research_only"] is True
    assert report["odds_api_requests"] == 0
    assert report["supabase_operations"] == 0
    assert report["production_model_operations"] == 0
    assert report["configured_csv_leagues"] == 7
    assert len(session.calls) == 7
    urls = {url for url, _ in session.calls}
    for suffix in ("SP1.csv", "I1.csv", "D1.csv", "F1.csv", "N1.csv", "T1.csv", "P1.csv"):
        assert any(url.endswith(f"/2627/{suffix}") for url in urls)
    by_league = {item["league"]: item for item in report["leagues"]}
    for league in {"EPL", "RPL"}:
        assert by_league[league]["status"] == "SOURCE_NOT_CONFIGURED"
