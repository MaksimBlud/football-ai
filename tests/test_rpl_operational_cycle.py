from datetime import datetime, timezone

import pandas as pd
import pytest

import evaluate_rpl_predictions as rpl_eval
import scheduled_rpl_odds_snapshot as scheduler
import update_rpl_results as results


def test_snapshot_scheduler_intervals():
    assert scheduler.required_interval_hours(100.0) == 12
    assert scheduler.required_interval_hours(48.0) == 6
    assert scheduler.required_interval_hours(12.0) == 4
    assert scheduler.required_interval_hours(2.0) == 2


def test_snapshot_scheduler_first_run_is_due():
    due, reason = scheduler.should_collect(
        [],
        now=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )
    assert due is True
    assert reason == "NO_EXISTING_RPL_SNAPSHOTS"


def test_snapshot_scheduler_respects_nearest_kickoff_interval():
    rows = [
        {
            "snapshot_time_utc": "2030-01-01T10:00:00Z",
            "commence_time_utc": "2030-01-01T20:00:00Z",
        }
    ]
    due, reason = scheduler.should_collect(
        rows,
        now=datetime(2030, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    assert due is False
    assert reason == "NEAREST_KICKOFF_INTERVAL_4H"


def test_finished_score_payload_is_parsed_in_moscow_timezone():
    event = {
        "completed": True,
        "commence_time": "2030-08-28T21:30:00Z",
        "home_team": "Alpha",
        "away_team": "Beta",
        "scores": [
            {"name": "Alpha", "score": "2"},
            {"name": "Beta", "score": "1"},
        ],
    }
    row = results.build_finished_row(event)
    assert row is not None
    assert row["league"] == "RPL"
    assert row["match_date"] == "2030-08-29"
    assert row["match_time"] == "00:30"
    assert row["result"] == "H"
    assert row["home_goals"] == 2
    assert row["away_goals"] == 1


def test_unfinished_score_event_is_ignored():
    assert results.build_finished_row(
        {
            "completed": False,
            "commence_time": "2030-08-28T12:00:00Z",
            "home_team": "Alpha",
            "away_team": "Beta",
            "scores": [],
        }
    ) is None


def test_rpl_evaluator_uses_moscow_fixture_date():
    ledger = pd.DataFrame([
        {
            "league": "RPL",
            "event_id": "event-1",
            "home_team": "Alpha",
            "away_team": "Beta",
            "kickoff_utc": "2030-08-28T21:30:00Z",
            "snapshot_time_utc": "2030-08-28T20:00:00Z",
            "market_home_prob": 0.60,
            "market_draw_prob": 0.25,
            "market_away_prob": 0.15,
            "market_pick": "H",
            "prediction_mode": "MARKET_ONLY",
            "structural_applied": False,
        }
    ])
    finished = pd.DataFrame([
        {
            "league": "RPL",
            "match_date": "2030-08-29",
            "home_team": "Alpha",
            "away_team": "Beta",
            "result": "H",
        }
    ])

    settled = rpl_eval.settle_rpl_predictions(ledger, finished)
    assert len(settled) == 1
    assert bool(settled.loc[0, "prediction_correct"]) is True
    assert settled.loc[0, "actual_result_probability"] == pytest.approx(0.60)


def test_rpl_evaluator_rejects_foreign_league():
    ledger = pd.DataFrame([
        {
            "league": "EPL",
            "event_id": "event-1",
            "home_team": "Alpha",
            "away_team": "Beta",
            "kickoff_utc": "2030-08-28T21:30:00Z",
            "snapshot_time_utc": "2030-08-28T20:00:00Z",
            "market_home_prob": 0.60,
            "market_draw_prob": 0.25,
            "market_away_prob": 0.15,
            "market_pick": "H",
            "prediction_mode": "MARKET_ONLY",
            "structural_applied": False,
        }
    ])
    finished = pd.DataFrame([
        {
            "league": "RPL",
            "match_date": "2030-08-29",
            "home_team": "Alpha",
            "away_team": "Beta",
            "result": "H",
        }
    ])
    with pytest.raises(ValueError, match="non-RPL ledger"):
        rpl_eval.settle_rpl_predictions(ledger, finished)


def test_operational_sources_do_not_load_production_model():
    for path in (
        "rpl_live_cycle.py",
        "scheduled_rpl_odds_snapshot.py",
        "update_rpl_results.py",
        "evaluate_rpl_predictions.py",
    ):
        source = open(path, encoding="utf-8").read()
        assert "football_model_xgboost_elo.pkl" not in source
        assert "joblib.load" not in source
        assert "train_model" not in source
