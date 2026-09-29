import numpy as np
import pandas as pd

import market_bookmaker_dispersion_v1 as experiment


def test_valid_mask_requires_all_three_decimal_odds_above_one():
    frame = pd.DataFrame(
        {
            "H": [2.0, 2.0, None],
            "D": [3.0, 1.0, 3.0],
            "A": [4.0, 4.0, 4.0],
        }
    )
    mask = experiment.valid_mask(frame, ("H", "D", "A"))
    assert mask.tolist() == [True, False, False]


def test_missing_triplet_fails_availability():
    frame = pd.DataFrame(
        {
            "season": experiment.SEASONS * 380,
            "H": [2.0] * (len(experiment.SEASONS) * 380),
            "D": [3.0] * (len(experiment.SEASONS) * 380),
        }
    )
    info = experiment.availability(frame, ("H", "D", "A"))
    assert info["columns_present"] is False
    assert info["eligible"] is False
    assert info["valid_rows_total"] == 0


def test_score_prefers_perfect_probabilities():
    frame = pd.DataFrame({"FTR": ["H", "D", "A"]})
    perfect = np.array(
        [
            [0.98, 0.01, 0.01],
            [0.01, 0.98, 0.01],
            [0.01, 0.01, 0.98],
        ],
        dtype=float,
    )
    weak = np.full((3, 3), 1.0 / 3.0)

    assert experiment.score(frame, perfect)["logloss"] < experiment.score(frame, weak)["logloss"]
    assert experiment.score(frame, perfect)["brier"] < experiment.score(frame, weak)["brier"]


def test_dispersion_zero_when_bookmakers_agree():
    matrix = np.array(
        [
            [0.50, 0.30, 0.20],
            [0.50, 0.30, 0.20],
            [0.50, 0.30, 0.20],
        ],
        dtype=float,
    )
    stacked = matrix[None, :, :]
    outcome_std = stacked.std(axis=1, ddof=0)
    dispersion = np.sqrt(np.mean(outcome_std**2, axis=1))
    assert np.allclose(dispersion, 0.0)


def test_dispersion_positive_when_bookmakers_disagree():
    stacked = np.array(
        [
            [
                [0.60, 0.25, 0.15],
                [0.50, 0.30, 0.20],
                [0.40, 0.35, 0.25],
            ]
        ],
        dtype=float,
    )
    outcome_std = stacked.std(axis=1, ddof=0)
    dispersion = np.sqrt(np.mean(outcome_std**2, axis=1))
    assert dispersion[0] > 0.0


def test_frozen_source_scope_and_thresholds():
    assert experiment.SEASONS == [
        "2019/2020",
        "2020/2021",
        "2021/2022",
        "2022/2023",
        "2023/2024",
        "2024/2025",
        "2025/2026",
    ]
    assert "2026/2027" not in experiment.SEASONS
    assert experiment.MIN_SEASON_COVERAGE == 0.90
    assert experiment.MIN_ELIGIBLE_BOOKMAKERS == 2
    assert experiment.BOOTSTRAP_SAMPLES == 10000


def test_benchmark_columns_are_standard_and_closing_average():
    assert experiment.BENCHMARK_COLUMNS == {
        "AVG_STANDARD": ("AvgH", "AvgD", "AvgA"),
        "AVG_CLOSING": ("AvgCH", "AvgCD", "AvgCA"),
    }
