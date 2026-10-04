import numpy as np
import pandas as pd
import pytest

import cross_market_score_coherence_v1 as experiment


def test_three_way_devig_normalizes_and_favors_short_price():
    p = experiment._three_way_devig(np.array([1.8, 3.6, 5.0]))
    assert np.isclose(p.sum(), 1.0, atol=1e-12)
    assert p[0] > p[1] > p[2]


def test_half_goal_line_contract_excludes_integer_and_quarter_lines():
    assert experiment._is_half_goal_line(-1.5)
    assert experiment._is_half_goal_line(-0.5)
    assert experiment._is_half_goal_line(0.5)
    assert experiment._is_half_goal_line(1.5)
    assert not experiment._is_half_goal_line(0.0)
    assert not experiment._is_half_goal_line(-1.0)
    assert not experiment._is_half_goal_line(-0.25)
    assert not experiment._is_half_goal_line(0.75)


def test_total_lambda_inverse_reproduces_over25_probability():
    expected_mu = 2.75
    p_over = experiment._over25_probability(expected_mu)
    recovered = experiment._infer_total_lambda(p_over)
    assert recovered == pytest.approx(expected_mu, abs=1e-9)


@pytest.mark.parametrize(
    "line,expected_min",
    [
        (0.5, 0),
        (-0.5, 1),
        (-1.5, 2),
        (1.5, -1),
    ],
)
def test_half_goal_cover_threshold(line, expected_min):
    assert experiment._minimum_cover_difference(line) == expected_min


def test_ah_inverse_recovers_known_home_share():
    mu = 2.8
    share = 0.61
    line = -0.5
    p = experiment._ah_home_cover_probability(mu, share, line)
    recovered, error, method = experiment._infer_home_share(mu, line, p)

    assert recovered == pytest.approx(share, abs=1e-8)
    assert error < 1e-9
    assert method in {"BRENT_ROOT", "BOUNDARY_ROOT"}


def test_reconstruction_returns_valid_synthetic_1x2():
    mu = 2.6
    share = 0.58
    line = -0.5
    p_over = experiment._over25_probability(mu)
    p_ah = experiment._ah_home_cover_probability(mu, share, line)

    result = experiment._reconstruct(p_over, line, p_ah)
    probabilities = np.array(
        [
            result["score_home_prob"],
            result["score_draw_prob"],
            result["score_away_prob"],
        ]
    )

    assert result["lambda_total"] == pytest.approx(mu, abs=1e-8)
    assert result["lambda_home"] + result["lambda_away"] == pytest.approx(
        mu,
        abs=1e-8,
    )
    assert np.isclose(probabilities.sum(), 1.0, atol=1e-12)
    assert (probabilities >= 0.0).all()


def test_outcome_error_uses_market_expected_brier_sharpness_control():
    frame = pd.DataFrame(
        [
            {
                "market_home_prob": 0.7,
                "market_draw_prob": 0.2,
                "market_away_prob": 0.1,
                "actual_index": 0,
            }
        ]
    )
    out = experiment._attach_outcome_errors(frame)
    expected = 1.0 - (0.7**2 + 0.2**2 + 0.1**2)
    realized = (0.7 - 1.0) ** 2 + 0.2**2 + 0.1**2

    assert out.iloc[0].expected_market_brier == pytest.approx(expected)
    assert out.iloc[0].market_brier == pytest.approx(realized)
    assert out.iloc[0].excess_brier == pytest.approx(realized - expected)


def test_tail_assignment_uses_frozen_train_thresholds_only():
    frame = pd.DataFrame(
        [
            {"league": "EPL", "score_gap_tv": 0.05},
            {"league": "EPL", "score_gap_tv": 0.15},
            {"league": "EPL", "score_gap_tv": 0.25},
        ]
    )
    thresholds = {
        "EPL": {
            "train_rows": 100,
            "low_q25": 0.10,
            "high_q75": 0.20,
        }
    }
    assigned = experiment._assign_tail(frame, thresholds)
    assert assigned["coherence_tail"].tolist() == ["LOW", "MID", "HIGH"]


def test_frozen_temporal_scope_excludes_2026_27():
    assert experiment.TRAIN_SEASONS == tuple(
        f"{year}-{year + 1}" for year in range(2016, 2024)
    )
    assert experiment.VALIDATION_SEASON == "2024-2025"
    assert experiment.TEST_SEASON == "2025-2026"
    assert "2026-2027" not in experiment.ALLOWED_SEASONS


def test_primary_contract_is_same_bookmaker_and_excess_brier():
    assert experiment.ONE_X_TWO_COLUMNS == ("B365H", "B365D", "B365A")
    assert experiment.TOTAL_COLUMNS == ("B365>2.5", "B365<2.5")
    assert experiment.AH_COLUMNS == ("B365AHH", "B365AHA")
    assert experiment.MIN_TAIL_ROWS_PER_LEAGUE == 15
    assert experiment.BOOTSTRAP_SAMPLES == 10000
