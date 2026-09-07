import numpy as np
import pandas as pd
import pytest

from historical_corners_early_drift import prefix_loss_comparison, summarize_early_drift


def test_prefix_does_not_read_later_outcomes():
    candidate = np.array([
        [0.70, 0.20, 0.10],
        [0.20, 0.60, 0.20],
        [0.10, 0.20, 0.70],
        [0.60, 0.20, 0.20],
    ])
    baseline = np.full((4, 3), 1.0 / 3.0)
    y_a = np.array([0, 1, 2, 0])
    y_b = np.array([0, 1, 0, 2])

    a = prefix_loss_comparison(y_a, candidate, baseline, prefixes=(2,))
    b = prefix_loss_comparison(y_b, candidate, baseline, prefixes=(2,))

    assert a.iloc[0].delta_brier == pytest.approx(b.iloc[0].delta_brier)
    assert a.iloc[0].delta_log_loss == pytest.approx(b.iloc[0].delta_log_loss)


def test_prefix_comparison_reports_full_season_direction_separately():
    candidate = np.array([
        [0.80, 0.10, 0.10],
        [0.80, 0.10, 0.10],
        [0.80, 0.10, 0.10],
        [0.80, 0.10, 0.10],
    ])
    baseline = np.full((4, 3), 1.0 / 3.0)
    y = np.array([0, 0, 1, 1])

    out = prefix_loss_comparison(y, candidate, baseline, prefixes=(2, 4))

    assert bool(out.iloc[0].candidate_brier_better) is True
    assert bool(out.iloc[0].brier_direction_agrees_with_full) is False
    assert bool(out.iloc[1].brier_direction_agrees_with_full) is True


def test_invalid_prefix_contract_is_rejected():
    candidate = np.full((3, 3), 1.0 / 3.0)
    baseline = np.full((3, 3), 1.0 / 3.0)
    y = np.array([0, 1, 2])
    with pytest.raises(ValueError, match="positive"):
        prefix_loss_comparison(y, candidate, baseline, prefixes=(0,))
    with pytest.raises(ValueError, match="unique"):
        prefix_loss_comparison(y, candidate, baseline, prefixes=(2, 2))


def test_summary_keeps_early_signal_and_direction_agreement_distinct():
    detail = pd.DataFrame([
        {
            "baseline": "GOALS10", "prefix_matches": 40,
            "delta_brier": -0.02, "delta_log_loss": -0.03,
            "candidate_brier_better": True, "candidate_log_loss_better": True,
            "brier_direction_agrees_with_full": True,
            "log_loss_direction_agrees_with_full": True,
        },
        {
            "baseline": "GOALS10", "prefix_matches": 40,
            "delta_brier": 0.01, "delta_log_loss": 0.02,
            "candidate_brier_better": False, "candidate_log_loss_better": False,
            "brier_direction_agrees_with_full": False,
            "log_loss_direction_agrees_with_full": False,
        },
    ])
    row = summarize_early_drift(detail).iloc[0]
    assert row.season_tests == 2
    assert row.brier_improvement_rate == pytest.approx(0.5)
    assert row.brier_direction_agreement_rate == pytest.approx(0.5)
    assert row.mean_delta_brier == pytest.approx(-0.005)
