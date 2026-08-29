from datetime import datetime, timezone

import pandas as pd

import export_rpl_upcoming_matches as fixture_export
import generate_rpl_market_shadow as market_shadow
from league_runtime_config import RPL_RUNTIME_CONFIG
from rpl_source_contract import RPL_SOURCE_CONTRACT, validate_rpl_source_contract


def sample_snapshots():
    return pd.DataFrame(
        [
            {
                "league": "RPL",
                "event_id": "rpl-1",
                "snapshot_time_utc": "2026-08-29T08:00:00Z",
                "commence_time_utc": "2026-08-30T14:00:00Z",
                "home_team": "Zenit",
                "away_team": "CSKA Moscow",
                "home_odds": 1.90,
                "draw_odds": 3.40,
                "away_odds": 4.10,
            },
            {
                "league": "RPL",
                "event_id": "rpl-1",
                "snapshot_time_utc": "2026-08-29T10:00:00Z",
                "commence_time_utc": "2026-08-30T14:00:00Z",
                "home_team": "Zenit",
                "away_team": "CSKA Moscow",
                "home_odds": 1.85,
                "draw_odds": 3.50,
                "away_odds": 4.20,
            },
        ]
    )


def test_verified_rpl_source_contract_is_explicit():
    validate_rpl_source_contract()
    assert RPL_SOURCE_CONTRACT.historical_competition_code == "RUS"
    assert RPL_SOURCE_CONTRACT.finished_results_competition_code == "RFPL"
    assert RPL_SOURCE_CONTRACT.historical_last_supported_season == "2025-2026"
    assert (
        RPL_SOURCE_CONTRACT.finished_results_access_status
        == "TOKEN_ACCESS_REQUIRES_LIVE_VERIFICATION"
    )


def test_fixture_export_is_rpl_scoped_and_uses_moscow_time():
    fixtures = fixture_export.prepare_upcoming_fixtures(
        sample_snapshots(),
        now=datetime(2026, 8, 29, 7, 0, tzinfo=timezone.utc),
    )
    assert len(fixtures) == 1
    row = fixtures.iloc[0]
    assert row["league"] == "RPL"
    assert row["event_id"] == "rpl-1"
    assert row["match_time"] == "17:00"
    assert row["home_team_model"] == "Zenit"
    assert row["away_team_model"] == "CSKA Moscow"


def test_market_shadow_uses_market_only_probabilities():
    fixtures = fixture_export.prepare_upcoming_fixtures(
        sample_snapshots(),
        now=datetime(2026, 8, 29, 7, 0, tzinfo=timezone.utc),
    )
    latest = market_shadow.build_market_shadow(
        fixtures,
        sample_snapshots(),
        previous_history=pd.DataFrame(columns=market_shadow.OUTPUT_COLUMNS),
    )
    assert len(latest) == 1
    row = latest.iloc[0]
    assert row["league"] == "RPL"
    assert row["market_shadow_status"] == "OK"
    assert row["market_pick"] in {"H", "D", "A"}
    assert abs(
        float(row["market_home_prob"])
        + float(row["market_draw_prob"])
        + float(row["market_away_prob"])
        - 1.0
    ) < 1e-9


def test_rpl_structural_remains_disabled():
    structural = RPL_RUNTIME_CONFIG.structural_v2
    assert structural.calibration_status == "CALIBRATION_REQUIRED"
    assert structural.structural_alpha is None
    assert structural.edge_threshold is None


def test_rpl_live_modules_do_not_import_production_model():
    for path in (
        "export_rpl_upcoming_matches.py",
        "generate_rpl_market_shadow.py",
    ):
        source = open(path, encoding="utf-8").read()
        assert "football_model_xgboost_elo.pkl" not in source
        assert "joblib.load" not in source
        assert "train_model" not in source
