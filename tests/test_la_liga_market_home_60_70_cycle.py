from pathlib import Path

import pandas as pd
import pytest

import la_liga_market_home_60_70_cycle as cycle


def test_default_runtime_does_not_load_result_values(monkeypatch, tmp_path):
    monkeypatch.setattr(cycle, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(cycle, "_client", lambda: object())
    monkeypatch.setattr(cycle, "load_ledger", lambda client: pd.DataFrame(columns=[
        "prediction_key", "league", "event_id", "home_team", "away_team", "kickoff_utc",
        "snapshot_time_utc", "market_home_prob", "market_draw_prob", "market_away_prob",
        "market_pick", "prediction_mode",
    ]))
    monkeypatch.setattr(cycle, "load_odds_snapshots", lambda client: pd.DataFrame(columns=[
        "league", "event_id", "snapshot_time_utc", "commence_time_utc", "home_team", "away_team",
        "home_odds", "draw_odds", "away_odds",
    ]))
    monkeypatch.setattr(cycle, "load_result_identities", lambda client: pd.DataFrame(columns=[
        "league", "match_date", "home_team", "away_team"
    ]))
    monkeypatch.setattr(
        cycle,
        "load_result_values",
        lambda client: (_ for _ in ()).throw(AssertionError("result values must not be queried")),
    )
    result = cycle.run(evaluate=False, now_utc="2026-09-05T00:00:00Z")
    assert result["status"] == "ACCUMULATING"
    assert result["outcome_values_queried"] is False


def test_explicit_evaluation_refuses_before_frozen_time_gate(monkeypatch, tmp_path):
    monkeypatch.setattr(cycle, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(cycle, "_client", lambda: object())
    monkeypatch.setattr(cycle, "load_ledger", lambda client: pd.DataFrame(columns=[
        "prediction_key", "league", "event_id", "home_team", "away_team", "kickoff_utc",
        "snapshot_time_utc", "market_home_prob", "market_draw_prob", "market_away_prob",
        "market_pick", "prediction_mode",
    ]))
    monkeypatch.setattr(cycle, "load_odds_snapshots", lambda client: pd.DataFrame(columns=[
        "league", "event_id", "snapshot_time_utc", "commence_time_utc", "home_team", "away_team",
        "home_odds", "draw_odds", "away_odds",
    ]))
    monkeypatch.setattr(cycle, "load_result_identities", lambda client: pd.DataFrame(columns=[
        "league", "match_date", "home_team", "away_team"
    ]))
    with pytest.raises(RuntimeError, match="PROSPECTIVE_EVALUATION_TIME_GATE"):
        cycle.run(evaluate=True, now_utc="2027-05-31T23:59:59Z")


def test_source_contract_separates_identity_and_outcome_queries():
    source = Path("la_liga_market_home_60_70_cycle.py").read_text()
    identity_function = source.split("def load_result_identities", 1)[1].split("def load_result_values", 1)[0]
    assert "result" not in identity_function.split("columns =", 1)[1].split("return", 1)[0]
    workflow = Path(".github/workflows/la-liga-market-home-60-70.yml").read_text()
    assert "--evaluate" in workflow
    assert "inputs.evaluate == true" in workflow
    assert "github.event_name == 'workflow_dispatch'" in workflow
