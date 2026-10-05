import numpy as np
import pandas as pd
import pytest

import favourite_longshot_bias_v1 as mod


def test_multiplicative_probabilities_sum_to_one():
    p = mod._multiplicative((1.60, 4.00, 6.00))
    assert p is not None
    assert float(p.sum()) == pytest.approx(1.0)
    assert np.all(p > 0.0)
    assert np.all(p < 1.0)


@pytest.mark.parametrize(
    ("p", "label"),
    [
        (0.00, "0-20%"),
        (0.199999, "0-20%"),
        (0.20, "20-30%"),
        (0.30, "30-40%"),
        (0.60, "60-70%"),
        (0.80, "80%+"),
        (1.00, "80%+"),
    ],
)
def test_frozen_bin_boundaries(p, label):
    assert mod._bin_label(p) == label


def test_residual_slope_positive_for_classic_favourite_longshot_direction():
    frame = pd.DataFrame(
        {
            "probability": [0.10, 0.15, 0.20, 0.65, 0.75, 0.85],
            "calibration_residual": [-0.05, -0.04, -0.03, 0.02, 0.04, 0.06],
        }
    )
    slope = mod._residual_slope(frame)
    assert slope is not None
    assert slope > 0.0


def test_bin_report_has_calibration_and_return_fields():
    frame = pd.DataFrame(
        {
            "probability": [0.10, 0.15, 0.65, 0.70],
            "won": [0, 0, 1, 1],
            "raw_odds": [9.0, 7.0, 1.6, 1.45],
            "flat_return": [-1.0, -1.0, 0.6, 0.45],
        }
    )
    report = {row["bin"]: row for row in mod._bin_report(frame)}
    assert report["0-20%"]["calibration_gap_realized_minus_implied"] < 0.0
    assert report["60-70%"]["calibration_gap_realized_minus_implied"] > 0.0
    assert "frequency_ci95_low" in report["0-20%"]
    assert "flat_stake_return" in report["60-70%"]


def test_slope_bootstrap_is_deterministic_and_positive(monkeypatch):
    monkeypatch.setattr(mod, "BOOTSTRAP_DRAWS", 200)
    rows = []
    for league in mod.LEAGUE_ORDER:
        for fixture in range(20):
            for p, residual in ((0.15, -0.04), (0.35, -0.01), (0.70, 0.04)):
                rows.append(
                    {
                        "league": league,
                        "fixture_key": f"{league}-{fixture}",
                        "probability": p,
                        "calibration_residual": residual,
                    }
                )
    frame = pd.DataFrame(rows)
    first = mod._slope_bootstrap(frame)
    second = mod._slope_bootstrap(frame)
    assert first == second
    assert first["slope"] > 0.0
    assert first["ci95_low"] > 0.0


def _supported_horizon():
    return {
        "residual_slope": {
            "slope": 0.10,
            "ci95_low": 0.02,
            "ci95_high": 0.18,
        },
        "regions": {
            "longshot_p_lt_0_30": {"gap": -0.02},
            "favourite_p_ge_0_60": {"gap": 0.02},
        },
        "by_bookmaker": {
            "BET365": {"residual_slope": 0.08},
            "PINNACLE": {"residual_slope": 0.06},
        },
        "by_league": {
            "EPL": {"residual_slope": 0.04},
            "LA_LIGA": {"residual_slope": 0.06},
            "SERIE_A": {"residual_slope": -0.01},
        },
    }


def test_formal_gate_requires_validation_and_untouched_test():
    validation = {"closing": _supported_horizon()}
    test = {"closing": _supported_horizon()}
    gate = mod._formal_gate(validation, test)
    assert gate["supported"] is True

    test["closing"]["residual_slope"]["ci95_low"] = -0.001
    gate = mod._formal_gate(validation, test)
    assert gate["supported"] is False
    assert gate["gates"]["test_closing_slope_ci_above_zero"] is False


def test_source_gap_fails_closed_and_does_not_promote():
    result = mod._source_gap_result(
        {"included_bookmakers": ["BET365"]},
        "FEWER_THAN_TWO_FROZEN_BOOKMAKERS_HAVE_VALIDATION_TEST_COVERAGE",
    )
    assert result["decision"] == "BLOCKED_BY_SOURCE_GAP"
    assert result["supported"] is False
    assert result["production_promotion"] is False
