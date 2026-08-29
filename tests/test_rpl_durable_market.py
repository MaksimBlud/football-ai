from datetime import datetime, timezone

import pandas as pd

import export_rpl_upcoming_matches as fixture_export
import generate_rpl_market_shadow as market_shadow
import persist_rpl_market_observations as observation_writer
import rpl_snapshot_readiness as readiness
from league_prediction_ledger import build_market_only_predictions
from league_runtime_config import RPL_RUNTIME_CONFIG


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


def current_shadow():
    fixtures = fixture_export.prepare_upcoming_fixtures(
        sample_snapshots(),
        now=datetime(2026, 8, 29, 7, 0, tzinfo=timezone.utc),
    )
    return market_shadow.build_market_shadow(
        fixtures,
        sample_snapshots(),
        previous_history=pd.DataFrame(columns=market_shadow.OUTPUT_COLUMNS),
        generated_at_utc=datetime(2026, 8, 29, 11, 0, tzinfo=timezone.utc),
    )


def test_snapshot_readiness_accepts_valid_pre_kickoff_rpl_data():
    result = readiness.audit_snapshot_readiness(sample_snapshots())
    assert result["ready"] is True
    assert result["reason"] == "READY"
    assert result["unique_events"] == 1
    assert result["post_kickoff_rows"] == 0
    assert result["normalized_teams"] == ["CSKA Moscow", "Zenit"]


def test_snapshot_readiness_rejects_post_kickoff_row():
    rows = sample_snapshots()
    rows.loc[0, "snapshot_time_utc"] = "2026-08-30T14:00:00Z"
    result = readiness.audit_snapshot_readiness(rows)
    assert result["ready"] is False
    assert result["post_kickoff_rows"] == 1


def test_rpl_aliases_are_not_guessed_before_real_snapshot_verification():
    assert dict(RPL_RUNTIME_CONFIG.aliases) == {}
    assert readiness.normalize_rpl_team(" Zenit ") == "Zenit"


def test_market_shadow_converts_to_generic_durable_observation_contract():
    observations = observation_writer.build_market_only_observations(current_shadow())
    assert len(observations) == 1
    row = observations.iloc[0]
    assert row["league"] == "RPL"
    assert row["prediction_source"] == "MARKET_ONLY"
    assert bool(row["research_only"]) is True
    assert bool(row["pre_kickoff_valid"]) is True
    assert bool(row["correction_enabled"]) is False
    assert float(row["realized_correction_weight"]) == 0.0
    assert row["market_argmax"] == row["shadow_argmax"]


def test_rpl_market_shadow_builds_canonical_prediction_ledger_rows():
    shadow = current_shadow()
    snapshot = pd.to_datetime(shadow.iloc[0]["snapshot_time_utc"], utc=True)
    keys = {("rpl-1", snapshot.isoformat()): "rpl-observation-key"}
    predictions = build_market_only_predictions(shadow, observation_keys=keys)
    assert len(predictions) == 1
    row = predictions.iloc[0]
    assert row["league"] == "RPL"
    assert row["prediction_mode"] == "MARKET_ONLY"
    assert bool(row["structural_applied"]) is False
    assert row["observation_key"] == "rpl-observation-key"


def test_rpl_durable_modules_do_not_load_or_train_production_model():
    for path in (
        "rpl_snapshot_readiness.py",
        "persist_rpl_market_observations.py",
        "persist_rpl_prediction_ledger.py",
    ):
        source = open(path, encoding="utf-8").read()
        assert "football_model_xgboost_elo.pkl" not in source
        assert "joblib.load" not in source
        assert "train_model" not in source
