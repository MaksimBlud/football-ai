import numpy as np
import pandas as pd

import favorite_longshot_bias_v1 as experiment


def test_probability_bands_have_frozen_boundaries():
    assert experiment.assign_band(0.60) == "P60_PLUS"
    assert experiment.assign_band(0.50) == "P50_60"
    assert experiment.assign_band(0.40) == "P40_50"
    assert experiment.assign_band(0.30) == "P30_40"
    assert experiment.assign_band(0.20) == "P20_30"
    assert experiment.assign_band(0.10) == "P10_20"
    assert experiment.assign_band(0.099) == "P_LT10"


def test_primary_cohort_boundaries_are_inclusive():
    assert experiment.FAVORITE_MIN == 0.50
    assert experiment.LONGSHOT_MAX == 0.20


def test_normalized_inverse_probabilities_sum_to_one():
    odds = np.array([1.80, 3.80, 5.50], dtype=float)
    p = experiment.normalized_inverse_probabilities(odds)
    expected = (1.0 / odds) / (1.0 / odds).sum()
    assert np.allclose(p, expected, atol=1e-12)
    assert np.isclose(p.sum(), 1.0, atol=1e-12)


def test_prepare_side_records_preserves_fixture_level_returns():
    frame = pd.DataFrame(
        {
            "league": ["EPL"],
            "season": ["2025/2026"],
            "_season_row": [0],
            "FTR": ["H"],
            "B365H": [1.50],
            "B365D": [4.50],
            "B365A": [8.00],
        }
    )

    sides, fixtures = experiment.prepare_side_records(
        frame,
        odds_columns=experiment.STANDARD_COLUMNS,
    )

    assert len(sides) == 3
    assert len(fixtures) == 1
    assert sides["won"].tolist() == [1, 0, 0]
    assert np.isclose(sides.iloc[0]["net_return"], 0.50)
    assert sides["is_favorite"].sum() == 1
    assert sides["is_longshot"].sum() >= 1

    row = fixtures.iloc[0]
    assert row["favorite_count"] == 1
    assert np.isclose(row["favorite_return_sum"], 0.50)
    assert row["longshot_count"] >= 1


def test_line_shopping_uses_standard_probabilities_but_max_returns():
    frame = pd.DataFrame(
        {
            "league": ["EPL"],
            "season": ["2025/2026"],
            "_season_row": [0],
            "FTR": ["A"],
            "B365H": [1.50],
            "B365D": [4.50],
            "B365A": [8.00],
            "MaxH": [1.55],
            "MaxD": [4.80],
            "MaxA": [9.00],
        }
    )

    standard, _ = experiment.prepare_side_records(
        frame,
        odds_columns=experiment.STANDARD_COLUMNS,
    )
    best, _ = experiment.prepare_side_records(
        frame,
        odds_columns=experiment.MAX_COLUMNS,
        probability_columns=experiment.STANDARD_COLUMNS,
    )

    assert np.allclose(
        standard["probability"].to_numpy(),
        best["probability"].to_numpy(),
    )
    away = best[best["side"].eq("AWAY")].iloc[0]
    assert np.isclose(away["net_return"], 8.0)


def test_side_metrics_roi_is_mean_net_unit_return():
    rows = pd.DataFrame(
        {
            "won": [1, 0],
            "probability": [0.6, 0.6],
            "odds": [2.0, 2.0],
            "net_return": [1.0, -1.0],
        }
    )
    metrics = experiment.side_metrics(rows)
    assert metrics["offers"] == 2
    assert metrics["wins"] == 1
    assert np.isclose(metrics["roi"], 0.0)
    assert np.isclose(metrics["observed_win_rate"], 0.5)
    assert np.isclose(metrics["calibration_gap"], -0.1)


def test_bootstrap_is_match_level_and_returns_negative_bias_for_fixture_sample():
    fixtures = pd.DataFrame(
        {
            "league": ["EPL"] * 4,
            "season": ["2025/2026"] * 4,
            "favorite_return_sum": [0.8, 0.5, -1.0, 0.7],
            "favorite_count": [1, 1, 1, 1],
            "longshot_return_sum": [-2.0, -2.0, -2.0, -2.0],
            "longshot_count": [2, 2, 2, 2],
        }
    )

    result = experiment.bootstrap_bias_delta(fixtures)
    assert result["mean_bias_delta"] < 0.0
    assert result["bootstrap_probability_negative"] > 0.95


def test_scope_is_top_five_and_completed_seasons_only():
    assert set(experiment.LEAGUES) == {
        "EPL",
        "LA_LIGA",
        "SERIE_A",
        "BUNDESLIGA",
        "LIGUE_1",
    }
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
    assert experiment.BOOTSTRAP_SAMPLES == 10000
