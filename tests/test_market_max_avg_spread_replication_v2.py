import numpy as np
import pandas as pd

import market_max_avg_spread_replication_v2 as experiment


def test_epl_is_not_a_replication_league():
    assert "EPL" not in experiment.LEAGUES
    assert set(experiment.LEAGUES) == {
        "LA_LIGA",
        "SERIE_A",
        "BUNDESLIGA",
        "LIGUE_1",
    }


def test_thresholds_are_exactly_transferred_from_epl_v1():
    assert experiment.LOW_SPREAD_THRESHOLD == 0.04177782395388535
    assert experiment.HIGH_SPREAD_THRESHOLD == 0.06264317681762262


def test_valid_spread_mask_requires_coherent_max_prices():
    frame = pd.DataFrame(
        {
            "AvgH": [2.0, 2.0],
            "AvgD": [3.0, 3.0],
            "AvgA": [4.0, 4.0],
            "MaxH": [2.2, 1.9],
            "MaxD": [3.3, 3.2],
            "MaxA": [4.4, 4.2],
            "FTR": ["H", "D"],
        }
    )
    assert experiment.valid_spread_mask(frame).tolist() == [True, False]


def test_expected_brier_formula_controls_probability_sharpness():
    sharp = np.array([0.8, 0.1, 0.1])
    flat = np.array([1 / 3, 1 / 3, 1 / 3])
    sharp_expected = 1.0 - np.sum(sharp**2)
    flat_expected = 1.0 - np.sum(flat**2)
    assert sharp_expected < flat_expected


def test_matched_cells_require_minimum_rows_in_both_groups():
    rows = []
    for i in range(5):
        rows.append(
            {
                "league": "LA_LIGA",
                "season": "2019/2020",
                "spread_group": "HIGH",
            }
        )
        rows.append(
            {
                "league": "LA_LIGA",
                "season": "2019/2020",
                "spread_group": "LOW",
            }
        )
    for i in range(5):
        rows.append(
            {
                "league": "SERIE_A",
                "season": "2019/2020",
                "spread_group": "HIGH",
            }
        )
    rows.append(
        {
            "league": "SERIE_A",
            "season": "2019/2020",
            "spread_group": "LOW",
        }
    )
    frame = pd.DataFrame(rows)
    matched, coverage = experiment.matched_cells(frame)
    assert set(matched["league"]) == {"LA_LIGA"}
    coverage_by_league = {row["league"]: row for row in coverage}
    assert coverage_by_league["LA_LIGA"]["eligible"] is True
    assert coverage_by_league["SERIE_A"]["eligible"] is False


def test_support_gate_requires_negative_ci_and_cross_league_consistency():
    good = {
        "pooled_high_minus_low": -0.02,
        "negative_leagues": 3,
        "negative_cell_fraction": 0.70,
    }
    good_bootstrap = {"ci95_high": -0.001}
    assert experiment.support_decision(good, good_bootstrap) is True

    weak_ci = {"ci95_high": 0.001}
    assert experiment.support_decision(good, weak_ci) is False

    too_few_leagues = dict(good)
    too_few_leagues["negative_leagues"] = 2
    assert experiment.support_decision(
        too_few_leagues,
        good_bootstrap,
    ) is False


def test_scope_is_frozen_to_seven_completed_seasons():
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
    assert experiment.MIN_GROUP_ROWS_PER_CELL == 5
    assert experiment.MIN_MATCHED_CELLS == 20
    assert experiment.BOOTSTRAP_SAMPLES == 10000
