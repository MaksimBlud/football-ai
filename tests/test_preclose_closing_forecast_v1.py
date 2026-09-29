import numpy as np
import pandas as pd

import preclose_closing_forecast_v1 as experiment


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "season": ["2019/2020", "2019/2020", "2020/2021"],
            "_season_row": [0, 1, 0],
            "result": ["H", "D", "A"],
            "first_p_home": [0.50, 0.40, 0.30],
            "first_p_draw": [0.25, 0.30, 0.30],
            "first_p_away": [0.25, 0.30, 0.40],
            "first_overround": [0.05, 0.05, 0.05],
            "first_entropy": [1.04, 1.09, 1.09],
            "first_top_probability": [0.50, 0.40, 0.40],
            "first_second_probability": [0.25, 0.30, 0.30],
            "first_top_second_gap": [0.25, 0.10, 0.10],
            "first_home_away_gap": [0.25, 0.10, -0.10],
            "avg_p_home": [0.49, 0.41, 0.31],
            "avg_p_draw": [0.26, 0.30, 0.30],
            "avg_p_away": [0.25, 0.29, 0.39],
            "avg_overround": [0.04, 0.04, 0.04],
            "book_vs_avg_home": [0.01, -0.01, -0.01],
            "book_vs_avg_draw": [-0.01, 0.00, 0.00],
            "book_vs_avg_away": [0.00, 0.01, 0.01],
            "book_vs_avg_overround": [0.01, 0.01, 0.01],
            "close_p_home": [0.52, 0.39, 0.29],
            "close_p_draw": [0.24, 0.31, 0.30],
            "close_p_away": [0.24, 0.30, 0.41],
            "move_home": [0.02, -0.01, -0.01],
            "move_draw": [-0.01, 0.01, 0.00],
            "move_away": [-0.01, 0.00, 0.01],
        }
    )


def test_feature_sets_are_strictly_first_set_only():
    forbidden_fragments = ("close", "move_", "result", "goal")
    for features in experiment.FEATURES.values():
        for feature in features:
            assert not any(fragment in feature for fragment in forbidden_fragments)


def test_zero_candidate_reproduces_first_set_probabilities_exactly():
    frame = _frame()
    candidate = experiment.fit_candidate(frame, name="ZERO")
    predicted, delta = experiment.predicted_close(candidate, frame)

    expected = frame[experiment.FIRST_COLUMNS].to_numpy(dtype=float)
    assert np.allclose(predicted, expected, atol=1e-15)
    assert np.array_equal(delta, np.zeros_like(delta))


def test_mean_delta_uses_training_closing_targets_only():
    frame = _frame()
    candidate = experiment.fit_candidate(frame, name="MEAN_DELTA")
    expected = frame[experiment.TARGET_COLUMNS].to_numpy(dtype=float).mean(axis=0)
    assert np.allclose(candidate.mean_delta, expected, atol=1e-15)


def test_predicted_close_is_valid_simplex_after_large_delta():
    frame = _frame()
    candidate = experiment.Candidate(
        name="MEAN_DELTA",
        feature_variant=None,
        alpha=None,
        model=None,
        mean_delta=np.array([-1.0, 0.3, 0.7]),
    )
    predicted, _ = experiment.predicted_close(candidate, frame)

    assert np.isfinite(predicted).all()
    assert (predicted > 0).all()
    assert np.allclose(predicted.sum(axis=1), 1.0, atol=1e-12)


def test_candidate_grid_is_frozen():
    specs = experiment.candidate_specs()
    ids = [experiment.spec_id(spec) for spec in specs]

    assert ids[:2] == ["ZERO", "MEAN_DELTA"]
    assert len(ids) == 2 + (
        len(experiment.FEATURE_VARIANTS) * len(experiment.ALPHA_GRID)
    )
    assert "RIDGE_STATE_A0.01" in ids
    assert "RIDGE_STATE_PLUS_CONSENSUS_A100" in ids


def test_temporal_contract_has_two_post_selection_holdouts():
    assert experiment.DEVELOPMENT_SEASONS == [
        "2019/2020",
        "2020/2021",
        "2021/2022",
        "2022/2023",
    ]
    assert experiment.SELECTION_SEASON == "2023/2024"
    assert experiment.HOLDOUT_1 == "2024/2025"
    assert experiment.HOLDOUT_2 == "2025/2026"
    assert "2026/2027" not in experiment.SEASONS


def test_close_distance_metrics_reward_exact_close():
    frame = _frame()
    # Candidate mean delta is made row-invariant, so use a synthetic frame with
    # identical movement on all rows where it can be exact.
    frame.loc[:, "move_home"] = 0.02
    frame.loc[:, "move_draw"] = -0.01
    frame.loc[:, "move_away"] = -0.01
    frame["close_p_home"] = frame["first_p_home"] + 0.02
    frame["close_p_draw"] = frame["first_p_draw"] - 0.01
    frame["close_p_away"] = frame["first_p_away"] - 0.01

    zero = experiment.fit_candidate(frame, name="ZERO")
    mean = experiment.fit_candidate(frame, name="MEAN_DELTA")
    _, zero_metrics = experiment.per_match_metrics(frame, zero)
    _, mean_metrics = experiment.per_match_metrics(frame, mean)

    assert mean_metrics["close_mae"] < zero_metrics["close_mae"]
    assert (
        mean_metrics["close_cross_entropy"]
        < zero_metrics["close_cross_entropy"]
    )
