from datetime import UTC, datetime

import pytest

import point_in_time_cross_league_replay_v1_evaluation as evaluation


def test_gate_closed_before_fixed_time():
    assert not evaluation.outcome_read_gate(datetime(2026, 9, 14, 22, 59, 59, tzinfo=UTC))["allowed"]


def test_gate_open_at_fixed_time():
    assert evaluation.outcome_read_gate(datetime(2026, 9, 14, 23, 0, 0, tzinfo=UTC))["allowed"]


def test_fixed_status_rule():
    assert evaluation.descriptive_status(-0.01, -0.01) == "EARLY_SIGNAL"
    assert evaluation.descriptive_status(0.01, 0.01) == "WARNING"
    assert evaluation.descriptive_status(-0.01, 0.01) == "INCONCLUSIVE"


def test_naive_time_rejected():
    with pytest.raises(ValueError):
        evaluation.outcome_read_gate(datetime(2026, 9, 14, 23, 0, 0))
