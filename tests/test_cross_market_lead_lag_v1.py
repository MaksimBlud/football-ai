import numpy as np
import pandas as pd
import pytest

import cross_market_lead_lag_v1 as experiment


def test_alignment_dot_positive_when_close_moves_toward_opening_score_signal():
    p_open = np.array([0.50, 0.30, 0.20])
    p_score = np.array([0.56, 0.27, 0.17])
    p_close = np.array([0.53, 0.285, 0.185])

    lead = p_score - p_open
    move = p_close - p_open

    assert float(np.dot(lead, move)) > 0.0


def test_alignment_dot_negative_when_close_moves_against_signal():
    p_open = np.array([0.50, 0.30, 0.20])
    p_score = np.array([0.56, 0.27, 0.17])
    p_close = np.array([0.47, 0.315, 0.215])

    lead = p_score - p_open
    move = p_close - p_open

    assert float(np.dot(lead, move)) < 0.0


def test_gap_reduction_is_positive_when_close_moves_toward_score():
    p_open = np.array([0.50, 0.30, 0.20])
    p_score = np.array([0.56, 0.27, 0.17])
    p_close = np.array([0.53, 0.285, 0.185])

    gap_open = 0.5 * np.abs(p_score - p_open).sum()
    gap_close = 0.5 * np.abs(p_score - p_close).sum()

    assert gap_open - gap_close > 0.0


def test_outcome_columns_are_explicitly_forbidden_from_v1_logic():
    assert {"FTR", "FTHG", "FTAG"}.issubset(experiment.OUTCOME_COLUMNS)


def test_temporal_scope_is_frozen_and_excludes_2026_27():
    assert experiment.REFERENCE_SEASONS == (
        "2019-2020",
        "2020-2021",
        "2021-2022",
        "2022-2023",
        "2023-2024",
    )
    assert experiment.VALIDATION_SEASON == "2024-2025"
    assert experiment.TEST_SEASON == "2025-2026"
    assert "2026-2027" not in experiment.ALLOWED_SEASONS


def test_closing_target_is_bet365_only():
    assert experiment.CLOSING_1X2_COLUMNS == (
        "B365CH",
        "B365CD",
        "B365CA",
    )


def test_primary_gates_are_frozen():
    assert experiment.MIN_ROWS_PER_LEAGUE == 40
    assert experiment.PERMUTATION_DRAWS == 10000
    assert experiment.BOOTSTRAP_DRAWS == 10000
    assert experiment.RANDOM_SEED == 20261004


def test_permutation_test_detects_perfect_match_specific_alignment():
    rows = []
    for league in experiment.LEAGUE_IDS:
        for index in range(50):
            sign = 1.0 if index % 2 == 0 else -1.0
            lead = np.array([0.02 * sign, -0.01 * sign, -0.01 * sign])
            move = lead.copy()
            rows.append(
                {
                    "league": league,
                    "lead_home": lead[0],
                    "lead_draw": lead[1],
                    "lead_away": lead[2],
                    "move_home": move[0],
                    "move_draw": move[1],
                    "move_away": move[2],
                    "alignment_dot": float(np.dot(lead, move)),
                }
            )

    frame = pd.DataFrame(rows)
    report = experiment._permutation_test(frame)

    assert report["observed_mean_alignment_dot"] > 0.0
    assert report["one_sided_p"] < 0.01


def test_bootstrap_positive_alignment_has_positive_ci():
    rows = []
    for league in experiment.LEAGUE_IDS:
        for _ in range(50):
            rows.append(
                {
                    "league": league,
                    "alignment_dot": 0.001,
                }
            )

    report = experiment._bootstrap_mean_alignment(
        pd.DataFrame(rows)
    )
    assert report["ci95_low"] > 0.0


def test_split_report_requires_all_three_frozen_leagues():
    rows = []
    for league in ("EPL", "LA_LIGA"):
        for _ in range(50):
            rows.append(
                {
                    "league": league,
                    "season": experiment.VALIDATION_SEASON,
                    "alignment_dot": 0.001,
                    "positive_alignment": True,
                    "alignment_cosine": 0.5,
                    "gap_open_tv": 0.02,
                    "gap_close_to_open_score_tv": 0.01,
                    "gap_reduction_tv": 0.01,
                    "open_to_close_move_tv": 0.01,
                    "lead_home": 0.01,
                    "lead_draw": -0.005,
                    "lead_away": -0.005,
                    "move_home": 0.005,
                    "move_draw": -0.0025,
                    "move_away": -0.0025,
                    "ah_fit_abs_error": 0.0,
                }
            )

    with pytest.raises(RuntimeError, match="missing a frozen league"):
        experiment._split_report(
            pd.DataFrame(rows),
            experiment.VALIDATION_SEASON,
        )
