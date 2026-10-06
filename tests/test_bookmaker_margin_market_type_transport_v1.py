import bookmaker_margin_market_type_transport_v1 as mod


def _report(mean=0.02, low=0.01, high=0.03):
    metric = {"rows": 100, "mean": mean, "ci95_low": low, "ci95_high": high, "draws": 5000}
    return {
        "paired": {
            "ah_allocation_delta": metric,
            "ah_overround_delta": metric,
            "x1_allocation_delta": metric,
            "ah_minus_x1_allocation_delta": metric,
        },
        "by_league": {
            "ah_allocation_delta": {"EPL": 0.01, "LA_LIGA": 0.02, "SERIE_A": -0.01}
        },
    }


def test_half_goal_gate_rejects_push_lines():
    assert mod._half_goal(-0.5) == -0.5
    assert mod._half_goal(1.5) == 1.5
    assert mod._half_goal(0.0) is None
    assert mod._half_goal(-1.0) is None


def test_half_goal_gate_rejects_non_finite_lines():
    assert mod._half_goal(float("nan")) is None
    assert mod._half_goal(float("inf")) is None
    assert mod._half_goal(float("-inf")) is None


def test_market_type_gate_passes_complete_transport():
    gate = mod._formal_gate(_report(), _report(), True)
    assert gate["supported"] is True


def test_market_type_gate_rejects_test_ci_crossing_zero():
    gate = mod._formal_gate(_report(), _report(low=-0.01), True)
    assert gate["supported"] is False
    assert gate["gates"]["test_ci_excludes_zero"] is False
