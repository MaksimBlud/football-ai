import copy

import pytest

from market_anchor_1x2_v1_freeze_guard import FreezeMismatch, assert_reports_equivalent


BASE = {
    "experiment_id": "MARKET_ANCHOR_1X2_V1",
    "residual_accepted": True,
    "active_mode": "RESIDUAL",
    "test_n": 1140,
    "metric": 0.5834232552235167,
    "leagues": [
        {"league": "EPL", "lambda": 0.0},
        {"league": "SERIE_A", "lambda": 1.0},
    ],
}


def test_last_bit_float_drift_is_allowed():
    actual = copy.deepcopy(BASE)
    actual["metric"] = BASE["metric"] + 2.0e-16
    assert_reports_equivalent(BASE, actual)


def test_material_float_change_is_rejected():
    actual = copy.deepcopy(BASE)
    actual["metric"] = BASE["metric"] + 2.0e-12
    with pytest.raises(FreezeMismatch, match="float mismatch"):
        assert_reports_equivalent(BASE, actual)


def test_selection_change_is_rejected_exactly():
    actual = copy.deepcopy(BASE)
    actual["active_mode"] = "MARKET_FALLBACK"
    with pytest.raises(FreezeMismatch, match="value/type mismatch"):
        assert_reports_equivalent(BASE, actual)


def test_integer_count_change_is_rejected_exactly():
    actual = copy.deepcopy(BASE)
    actual["test_n"] = 1139
    with pytest.raises(FreezeMismatch, match="integer/type mismatch"):
        assert_reports_equivalent(BASE, actual)


def test_list_order_and_structure_are_frozen():
    actual = copy.deepcopy(BASE)
    actual["leagues"].reverse()
    with pytest.raises(FreezeMismatch):
        assert_reports_equivalent(BASE, actual)


def test_missing_key_is_rejected():
    actual = copy.deepcopy(BASE)
    del actual["residual_accepted"]
    with pytest.raises(FreezeMismatch, match="key mismatch"):
        assert_reports_equivalent(BASE, actual)
