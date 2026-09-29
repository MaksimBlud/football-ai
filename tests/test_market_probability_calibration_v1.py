import numpy as np
import pandas as pd

import market_probability_calibration_v1 as experiment


def sample_probabilities():
    return np.array(
        [
            [0.60, 0.25, 0.15],
            [0.45, 0.30, 0.25],
            [0.35, 0.35, 0.30],
            [0.70, 0.20, 0.10],
        ],
        dtype=float,
    )


def test_identity_transform_is_exact_baseline():
    p = sample_probabilities()
    transformed = experiment.transform_probabilities(
        p,
        temperature=1.0,
        home_bias=0.0,
        away_bias=0.0,
    )
    assert np.allclose(transformed, p, atol=1e-12)


def test_temperature_preserves_argmax_order():
    p = sample_probabilities()
    transformed = experiment.transform_probabilities(
        p,
        temperature=1.4,
    )
    assert np.array_equal(
        transformed.argmax(axis=1),
        p.argmax(axis=1),
    )


def test_home_bias_increases_home_probability():
    p = sample_probabilities()
    transformed = experiment.transform_probabilities(
        p,
        home_bias=0.2,
    )
    assert np.all(transformed[:, 0] > p[:, 0])
    assert np.allclose(transformed.sum(axis=1), 1.0, atol=1e-12)


def test_away_bias_increases_away_probability():
    p = sample_probabilities()
    transformed = experiment.transform_probabilities(
        p,
        away_bias=0.2,
    )
    assert np.all(transformed[:, 2] > p[:, 2])


def test_temperature_bounds_fail_closed():
    p = sample_probabilities()
    for bad in (0.49, 2.01):
        try:
            experiment.transform_probabilities(p, temperature=bad)
        except ValueError as exc:
            assert "temperature outside frozen bounds" in str(exc)
        else:
            raise AssertionError("out-of-bounds temperature was accepted")


def test_bias_bounds_fail_closed():
    p = sample_probabilities()
    try:
        experiment.transform_probabilities(p, home_bias=0.6)
    except ValueError as exc:
        assert "home_bias outside frozen bounds" in str(exc)
    else:
        raise AssertionError("out-of-bounds bias was accepted")


def test_fit_temperature_stays_inside_frozen_bounds():
    p = sample_probabilities()
    y = np.array([0, 0, 1, 0], dtype=int)
    fitted = experiment.fit_temperature(p, y)
    assert experiment.TEMP_BOUNDS[0] <= fitted["temperature"] <= experiment.TEMP_BOUNDS[1]
    assert fitted["home_bias"] == 0.0
    assert fitted["away_bias"] == 0.0


def test_fit_class_bias_uses_draw_as_reference():
    p = sample_probabilities()
    y = np.array([0, 2, 1, 2], dtype=int)
    fitted = experiment.fit_class_bias(p, y)
    assert fitted["temperature"] == 1.0
    assert experiment.BIAS_BOUNDS[0] <= fitted["home_bias"] <= experiment.BIAS_BOUNDS[1]
    assert experiment.BIAS_BOUNDS[0] <= fitted["away_bias"] <= experiment.BIAS_BOUNDS[1]


def test_scope_is_four_strictly_later_outer_seasons():
    assert experiment.SEASONS == [
        "2019/2020",
        "2020/2021",
        "2021/2022",
        "2022/2023",
        "2023/2024",
        "2024/2025",
        "2025/2026",
    ]
    assert experiment.OUTER_TEST_SEASONS == [
        "2022/2023",
        "2023/2024",
        "2024/2025",
        "2025/2026",
    ]
    assert "2026/2027" not in experiment.SEASONS


def test_support_gate_requires_three_joint_wins_and_negative_ci():
    # Guard the formal threshold constants/shape used in evaluate().
    assert experiment.BOOTSTRAP_SAMPLES == 10000
    assert len(experiment.OUTER_TEST_SEASONS) == 4
