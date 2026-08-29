from datetime import datetime, timezone

import pandas as pd

import evaluate_serie_a_predictions as evaluator
import scheduled_serie_a_odds_snapshot as scheduler
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
import update_serie_a_results as results


def test_runtime_contract():
    cfg = SERIE_A_RUNTIME_CONFIG
    assert cfg.identity.identifier == "SERIE_A"
    assert cfg.identity.timezone == "Europe/Rome"
    assert cfg.identity.odds_sport_key == "soccer_italy_serie_a"
    assert cfg.historical_source.competition_code == "I1"
    assert cfg.structural_v2.calibration_status == "CALIBRATION_REQUIRED"
    assert cfg.structural_v2.structural_alpha is None
    assert cfg.structural_v2.edge_threshold is None


def test_scheduler_intervals():
    assert scheduler.required_interval_hours(100) == 12
    assert scheduler.required_interval_hours(48) == 6
    assert scheduler.required_interval_hours(12) == 4
    assert scheduler.required_interval_hours(3) == 2


def test_scheduler_collects_without_existing_state():
    due, reason = scheduler.should_collect([], now=datetime(2026, 8, 29, tzinfo=timezone.utc))
    assert due is True
    assert reason == "NO_EXISTING_SERIE_A_SNAPSHOTS"


def test_finished_result_uses_rome_fixture_date():
    event = {
        "completed": True,
        "commence_time": "2026-08-29T22:30:00Z",
        "home_team": "Inter Milan",
        "away_team": "AC Milan",
        "scores": [
            {"name": "Inter Milan", "score": "2"},
            {"name": "AC Milan", "score": "1"},
        ],
    }
    row = results.build_finished_row(event)
    assert row["match_date"] == "2026-08-30"
    assert row["result"] == "H"
    assert row["league"] == "SERIE_A"


def test_evaluator_settles_in_rome_timezone():
    ledger = pd.DataFrame([
        {
            "league": "SERIE_A",
            "event_id": "event-1",
            "home_team": "Inter Milan",
            "away_team": "AC Milan",
            "kickoff_utc": "2026-08-29T22:30:00Z",
            "snapshot_time_utc": "2026-08-29T18:00:00Z",
            "market_home_prob": 0.55,
            "market_draw_prob": 0.25,
            "market_away_prob": 0.20,
            "market_pick": "H",
            "prediction_mode": "MARKET_ONLY",
            "structural_applied": False,
        }
    ])
    finished = pd.DataFrame([
        {
            "league": "SERIE_A",
            "match_date": "2026-08-30",
            "home_team": "Inter Milan",
            "away_team": "AC Milan",
            "result": "H",
        }
    ])
    settled = evaluator.settle_serie_a_predictions(ledger, finished)
    assert len(settled) == 1
    assert bool(settled.iloc[0]["prediction_correct"]) is True


def test_operational_sources_do_not_reference_production_model():
    paths = [
        "save_serie_a_odds_snapshot.py",
        "export_serie_a_upcoming_matches.py",
        "generate_serie_a_market_shadow.py",
        "persist_serie_a_market_observations.py",
        "persist_serie_a_prediction_ledger.py",
        "serie_a_live_cycle.py",
        "scheduled_serie_a_odds_snapshot.py",
        "serie_a_scores_service.py",
        "update_serie_a_results.py",
        "evaluate_serie_a_predictions.py",
    ]
    forbidden = ("football_model_xgboost_elo.pkl", "joblib.load", "train_model_xgboost_elo")
    for path in paths:
        source = open(path, encoding="utf-8").read()
        for token in forbidden:
            assert token not in source
