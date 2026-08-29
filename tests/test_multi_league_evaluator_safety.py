import pandas as pd
import pytest

import evaluate_league_predictions as evaluator
from league_config import (
    get_league_config,
    is_collection_ready,
    is_operational_collection_ready,
)


def _ledger(league: str, kickoff: str = "2026-08-01T22:30:00Z") -> pd.DataFrame:
    return pd.DataFrame([
        {
            "league": league,
            "event_id": f"{league}-midnight",
            "home_team": "Alpha",
            "away_team": "Beta",
            "kickoff_utc": kickoff,
            "snapshot_time_utc": "2026-08-01T20:00:00Z",
            "market_home_prob": 0.60,
            "market_draw_prob": 0.25,
            "market_away_prob": 0.15,
            "market_pick": "H",
            "prediction_mode": "MARKET_ONLY",
            "structural_applied": False,
        }
    ])


def _results(league: str, match_date: str) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "league": league,
            "match_date": match_date,
            "home_team": "Alpha",
            "away_team": "Beta",
            "result": "H",
        }
    ])


@pytest.mark.parametrize(
    ("league", "expected_date"),
    [
        ("EPL", "2026-08-01"),
        ("LA_LIGA", "2026-08-02"),
        ("RPL", "2026-08-02"),
        ("SERIE_A", "2026-08-02"),
        ("BUNDESLIGA", "2026-08-02"),
        ("LIGUE_1", "2026-08-02"),
    ],
)
def test_settlement_uses_each_leagues_local_match_date(league, expected_date):
    settled = evaluator.settle_predictions(
        _ledger(league),
        _results(league, expected_date),
        league=league,
    )
    assert len(settled) == 1
    assert settled.iloc[0]["league"] == league


def test_generic_evaluator_rejects_foreign_ledger_rows():
    ledger = pd.concat([_ledger("SERIE_A"), _ledger("BUNDESLIGA")], ignore_index=True)
    with pytest.raises(ValueError, match="foreign league rows"):
        evaluator.evaluate_frames(
            "SERIE_A",
            ledger,
            _results("SERIE_A", "2026-08-02"),
        )


def test_generic_evaluator_rejects_foreign_result_rows():
    with pytest.raises(ValueError, match="foreign league rows"):
        evaluator.evaluate_frames(
            "SERIE_A",
            _ledger("SERIE_A"),
            _results("BUNDESLIGA", "2026-08-02"),
        )


def test_configured_timezones_are_distinct_and_resolved():
    expected = {
        "EPL": "Europe/London",
        "LA_LIGA": "Europe/Madrid",
        "RPL": "Europe/Moscow",
        "SERIE_A": "Europe/Rome",
        "BUNDESLIGA": "Europe/Berlin",
        "LIGUE_1": "Europe/Paris",
    }
    assert {league: get_league_config(league).timezone for league in expected} == expected


def test_rpl_registry_distinguishes_generic_and_operational_collection():
    assert is_collection_ready("RPL") is False
    assert is_operational_collection_ready("RPL") is True


def test_new_market_only_leagues_remain_structural_independent():
    from league_runtime_config import EPL_RUNTIME_CONFIG, RPL_RUNTIME_CONFIG
    from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
    from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
    from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG

    configs = [
        EPL_RUNTIME_CONFIG,
        RPL_RUNTIME_CONFIG,
        SERIE_A_RUNTIME_CONFIG,
        BUNDESLIGA_RUNTIME_CONFIG,
        LIGUE1_RUNTIME_CONFIG,
    ]
    for config in configs:
        structural = config.structural_v2
        assert structural.calibration_status == "CALIBRATION_REQUIRED"
        assert structural.structural_alpha is None
        assert structural.edge_threshold is None
