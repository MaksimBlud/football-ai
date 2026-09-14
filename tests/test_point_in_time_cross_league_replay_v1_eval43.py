from datetime import UTC, datetime

import pandas as pd
import pytest

import point_in_time_cross_league_replay_v1_eval43 as ev


def _synthetic_frame():
    freeze = ev.load_and_validate_freeze()
    rows = []
    for index, item in enumerate(freeze["included"]):
        disagree = index < 10
        rows.append({
            "league": item["league"],
            "event_id": item["event_id"],
            "result": "H",
            "model_home_prob": 0.60,
            "model_draw_prob": 0.25,
            "model_away_prob": 0.15,
            "market_home_prob": 0.20 if disagree else 0.55,
            "market_draw_prob": 0.20 if disagree else 0.25,
            "market_away_prob": 0.60 if disagree else 0.20,
        })
    return pd.DataFrame(rows)


def test_eval43_freeze_is_exact_and_outcome_blind():
    freeze = ev.load_and_validate_freeze()
    assert freeze["outcome_fields_read_before_freeze"] is False
    assert freeze["included_total"] == 43
    assert freeze["rollover_total"] == 4
    assert freeze["included_league_counts"] == ev.EXPECTED_COUNTS
    assert len(ev.expected_identities()) == 43


def test_four_future_events_are_rollover_only():
    freeze = ev.load_and_validate_freeze()
    rolled = {(row["home_team"], row["away_team"]) for row in freeze["rollover_next_sample"]}
    assert rolled == {
        ("Torino", "AS Roma"),
        ("Como", "Parma"),
        ("Inter Milan", "Udinese"),
        ("Villarreal", "Real Betis"),
    }


def test_gate_fails_before_freeze_cutoff_and_opens_after():
    with pytest.raises(RuntimeError, match="before frozen cutoff"):
        ev.require_gate_open(datetime(2026, 9, 14, 15, 17, 17, tzinfo=UTC))
    ev.require_gate_open(datetime(2026, 9, 14, 15, 17, 18, tzinfo=UTC))


def test_evaluator_uses_exact_43_and_predeclared_disagreement_slice():
    report = ev.evaluate(_synthetic_frame())
    assert report["n"] == 43
    assert report["rollover_next_sample_n"] == 4
    assert report["disagreement_n"] == 10
    assert report["disagreement_ai_correct_market_wrong"] == 10
    assert report["model_correct_n"] == 43
    assert report["market_correct_n"] == 33
    assert report["model_accuracy"] == 1.0
    assert report["market_accuracy"] == 33 / 43
    assert report["delta_brier_ai_minus_market"] < 0
    assert report["delta_log_loss_ai_minus_market"] < 0
    assert report["status"] == "EARLY_SIGNAL"
    assert report["bet_decision"] == "NO_BET"


def test_evaluator_rejects_rollover_event():
    frame = _synthetic_frame()
    freeze = ev.load_and_validate_freeze()
    frame.loc[0, "league"] = freeze["rollover_next_sample"][0]["league"]
    frame.loc[0, "event_id"] = freeze["rollover_next_sample"][0]["event_id"]
    with pytest.raises(ValueError, match="identities differ"):
        ev.evaluate(frame)
