import numpy as np
import pandas as pd

from bookmaker_reconstruction_devig_v1 import METHODS, TEST_SEASON, VALIDATION_SEASON, power, proportional, shin


def test_all_devig_methods_return_valid_probabilities():
    q = np.array([[1/1.80, 1/3.60, 1/5.00], [1/2.50, 1/3.20, 1/3.10]], dtype=float)
    for fn in (proportional, power, shin):
        p = fn(q)
        assert p.shape == q.shape
        assert np.isfinite(p).all()
        assert (p > 0).all() and (p < 1).all()
        assert np.allclose(p.sum(axis=1), 1.0, atol=1e-10)


def test_proportional_is_current_market_baseline():
    q = np.array([[0.55, 0.30, 0.20]])
    assert np.allclose(proportional(q), q / q.sum(axis=1, keepdims=True))


def test_temporal_contract_keeps_2025_26_untouched_for_selection():
    assert VALIDATION_SEASON == "2024-2025"
    assert TEST_SEASON == "2025-2026"
    assert set(METHODS) == {"PROPORTIONAL", "POWER", "SHIN"}


def test_methods_are_not_identical_on_overround_market():
    q = np.array([[1/1.55, 1/4.50, 1/7.00]], dtype=float)
    a, b, c = proportional(q), power(q), shin(q)
    assert not np.allclose(a, b)
    assert not np.allclose(a, c)
