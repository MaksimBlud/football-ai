import numpy as np
import pandas as pd
import pytest

import kickoff_calendar_market_movement_v1 as mod


def test_devig_over_is_symmetric_at_equal_odds():
    assert mod._devig_over(1.91, 1.91) == pytest.approx(0.5)


def test_design_adds_only_frozen_calendar_columns():
    frame = pd.DataFrame(
        {
            "league": ["EPL", "LA_LIGA", "SERIE_A"],
            "weekday": [0, 2, 6],
            "hour": [12.5, 16.0, 20.75],
            "slot": ["EARLY", "AFTERNOON", "LATE"],
            "p_open_over25": [0.45, 0.5, 0.55],
        }
    )
    baseline = mod._design(frame, False)
    calendar = mod._design(frame, True)
    assert baseline.shape == (3, 3)
    assert calendar.shape == (3, 14)


def test_paired_bootstrap_is_zero_for_identical_losses(monkeypatch):
    monkeypatch.setattr(mod, "BOOTSTRAP_DRAWS", 100)
    frame = pd.DataFrame(
        {"league": [league for league in mod.LEAGUE_ORDER for _ in range(5)]}
    )
    report = mod._paired_bootstrap(frame, np.zeros(len(frame)))
    assert report["ci95_low"] == pytest.approx(0.0)
    assert report["ci95_high"] == pytest.approx(0.0)


def test_support_requires_both_splits_and_negative_oot_ci():
    validation = {"calendar_minus_baseline_mse": -0.001}
    test = {
        "calendar_minus_baseline_mse": -0.001,
        "bootstrap": {"ci95_high": -0.0001},
    }
    assert mod._supported(validation, test) is True
    test["bootstrap"]["ci95_high"] = 0.0001
    assert mod._supported(validation, test) is False


def test_source_gap_result_fails_closed_without_proxy():
    result = mod._source_gap_result(
        {"EPL": {"2025-2026": {"missing_required_columns": ["B365C>2.5"]}}},
        [
            {
                "league": "EPL",
                "season": "2025-2026",
                "missing": ["B365C>2.5"],
            }
        ],
    )
    assert result["decision"] == "BLOCKED_BY_OPEN_CLOSE_SOURCE_GAP"
    assert result["supported"] is False
    assert result["match_outcomes_used"] is False
