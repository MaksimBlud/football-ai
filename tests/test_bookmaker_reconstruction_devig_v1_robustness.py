import numpy as np

from bookmaker_reconstruction_devig_v1_robustness import (
    ALL_ALLOWED_SEASONS,
    BASELINE_METHOD,
    CANDIDATE_METHOD,
    PRIOR_SEASONS,
    TEST_SEASON,
    VALIDATION_SEASON,
    paired_bootstrap,
)


def test_fixed_candidate_contract_is_not_reselected():
    assert BASELINE_METHOD == "PROPORTIONAL"
    assert CANDIDATE_METHOD == "POWER"
    assert VALIDATION_SEASON == "2024-2025"
    assert TEST_SEASON == "2025-2026"
    assert PRIOR_SEASONS == tuple(f"{year}-{year + 1}" for year in range(2016, 2024))
    assert "2026-2027" not in ALL_ALLOWED_SEASONS


def test_paired_bootstrap_is_deterministic_and_detects_clear_negative_delta():
    values = np.array([-0.1, -0.2, -0.05, -0.3, -0.1], dtype=float)
    a = paired_bootstrap(values, reps=1000, seed=7)
    b = paired_bootstrap(values, reps=1000, seed=7)
    assert a == b
    assert a["observed_delta"] < 0
    assert a["bootstrap_ci95_high"] < 0
    assert a["bootstrap_probability_better_than_proportional"] > 0.99


def test_paired_bootstrap_rejects_bad_inputs():
    for values in (np.array([]), np.array([np.nan])):
        try:
            paired_bootstrap(values, reps=10)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")
