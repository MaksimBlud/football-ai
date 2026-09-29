import numpy as np

import market_devig_methods_v1 as experiment
from league_historical_market import no_vig_probabilities


def test_multiplicative_matches_current_project_normalization():
    odds = np.array([1.80, 3.60, 4.80], dtype=float)
    p, details = experiment.multiplicative_probabilities(odds)

    current = no_vig_probabilities(
        home_odds=np.array([odds[0]]),
        draw_odds=np.array([odds[1]]),
        away_odds=np.array([odds[2]]),
    )
    expected = current[
        [
            "market_home_probability",
            "market_draw_probability",
            "market_away_probability",
        ]
    ].iloc[0].to_numpy(dtype=float)

    assert np.allclose(p, expected, atol=1e-12)
    assert details["overround"] > 0.0


def test_additive_matches_closed_form_without_clipping():
    odds = np.array([1.40, 4.20, 9.00], dtype=float)
    q = 1.0 / odds
    booksum = float(q.sum())
    expected = q - (booksum - 1.0) / 3.0

    p, _ = experiment.additive_probabilities(odds)

    assert np.allclose(p, expected, atol=1e-12)
    assert np.isclose(p.sum(), 1.0)


def test_power_probabilities_sum_to_one_and_k_exceeds_one():
    p, details = experiment.power_probabilities(
        np.array([1.40, 4.20, 9.00], dtype=float)
    )

    assert np.isclose(p.sum(), 1.0, atol=1e-12)
    assert details["k"] > 1.0
    assert details["iterations"] <= experiment.MAX_ITERATIONS


def test_shin_matches_published_reference_example():
    p, details = experiment.shin_probabilities(
        np.array([2.6, 2.4, 4.3], dtype=float)
    )
    expected = np.array(
        [
            0.37299406033208965,
            0.4047794109200184,
            0.2222265287474275,
        ],
        dtype=float,
    )

    assert np.allclose(p, expected, atol=2e-12)
    assert np.isclose(details["z"], 0.01694251276407055, atol=2e-12)
    assert details["iterations"] <= experiment.MAX_ITERATIONS


def test_all_methods_preserve_outcome_ordering():
    odds = np.array([1.40, 4.20, 9.00], dtype=float)
    expected_order = np.argsort(odds)

    for method in experiment.METHODS:
        p, _ = experiment.TRANSFORMS[method](odds)
        probability_order = np.argsort(-p)
        assert np.array_equal(probability_order, expected_order)


def test_discovery_selection_fails_closed_without_joint_season_robustness():
    reports = {
        method: {"by_season": {}}
        for method in experiment.METHODS
    }

    for season in experiment.DISCOVERY_SEASONS:
        reports["MULTIPLICATIVE"]["by_season"][season] = {
            "matches": 380,
            "logloss": 1.000,
            "brier": 0.600,
        }
        for method in experiment.ALTERNATIVES:
            reports[method]["by_season"][season] = {
                "matches": 380,
                "logloss": 1.001,
                "brier": 0.601,
            }

    selected, summary = experiment.select_discovery_method(reports)

    assert selected == "MULTIPLICATIVE"
    assert all(
        not summary["alternatives"][method]["eligible"]
        for method in experiment.ALTERNATIVES
    )


def test_discovery_selection_requires_three_joint_season_wins():
    reports = {
        method: {"by_season": {}}
        for method in experiment.METHODS
    }

    for index, season in enumerate(experiment.DISCOVERY_SEASONS):
        reports["MULTIPLICATIVE"]["by_season"][season] = {
            "matches": 380,
            "logloss": 1.000,
            "brier": 0.600,
        }

        # POWER wins only two seasons and loses three by a tiny amount.
        reports["POWER"]["by_season"][season] = {
            "matches": 380,
            "logloss": 0.980 if index < 2 else 1.002,
            "brier": 0.580 if index < 2 else 0.602,
        }

        # Other alternatives are clearly worse.
        for method in ("ADDITIVE", "SHIN"):
            reports[method]["by_season"][season] = {
                "matches": 380,
                "logloss": 1.010,
                "brier": 0.610,
            }

    selected, summary = experiment.select_discovery_method(reports)

    assert summary["alternatives"]["POWER"]["joint_season_wins"] == 2
    assert summary["alternatives"]["POWER"]["eligible"] is False
    assert selected == "MULTIPLICATIVE"


def test_experiment_scope_excludes_open_season():
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
