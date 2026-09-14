import json
from pathlib import Path

import pandas as pd

from point_in_time_cross_league_replay_v1_eval43 import evaluate

RESULTS = Path("experiments/point_in_time_cross_league_replay_v1_eval43_results.csv")
REPORT = Path("experiments/point_in_time_cross_league_replay_v1_eval43_report.json")


def test_eval43_report_recomputes_from_frozen_results():
    frame = pd.read_csv(RESULTS)
    expected = json.loads(REPORT.read_text(encoding="utf-8"))
    actual = evaluate(frame)

    assert actual["n"] == 43
    assert actual["rollover_next_sample_n"] == 4
    assert actual["status"] == "WARNING"
    assert actual["bet_decision"] == "NO_BET"
    assert actual["model_correct_n"] == 17
    assert actual["market_correct_n"] == 21
    assert actual["disagreement_n"] == 10
    assert actual["disagreement_ai_correct_market_wrong"] == 0
    assert actual["disagreement_market_correct_ai_wrong"] == 4
    assert actual["disagreement_both_wrong"] == 6

    for key in (
        "model_brier",
        "market_brier",
        "delta_brier_ai_minus_market",
        "model_log_loss",
        "market_log_loss",
        "delta_log_loss_ai_minus_market",
        "model_accuracy",
        "market_accuracy",
    ):
        assert abs(actual[key] - expected[key]) < 1e-12


def test_eval43_results_match_frozen_identity_count():
    frame = pd.read_csv(RESULTS)
    assert len(frame) == 43
    assert not frame.duplicated(["league", "event_id"]).any()
    assert set(frame["result"]) <= {"H", "D", "A"}
    assert frame["home_goals"].notna().all()
    assert frame["away_goals"].notna().all()
