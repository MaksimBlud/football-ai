import numpy as np
import pandas as pd
import pytest

import bookmaker_margin_structure_v1 as mod


def test_multiplicative_probabilities_sum_to_one():
    p = mod._multiplicative((1.7, 3.8, 5.5))
    assert p is not None
    assert float(p.sum()) == pytest.approx(1.0)
    assert np.all(p > 0.0)
    assert np.all(p < 1.0)


def test_allocation_tilt_zero_under_uniform_margin():
    consensus = np.array([0.50, 0.30, 0.20])
    implied_sum = 1.06
    q = consensus * implied_sum
    odds = tuple(float(1.0 / value) for value in q)
    result = mod._allocation_tilt(odds, consensus)
    assert result is not None
    tilt, overround, fair = result
    assert tilt == pytest.approx(np.zeros(3), abs=1e-12)
    assert overround == pytest.approx(0.06)
    assert fair == pytest.approx(consensus, abs=1e-12)


def test_rank_indices_identify_favourite_and_longshot():
    fav, mid, long = mod._rank_indices(np.array([0.60, 0.25, 0.15]))
    assert fav == 0
    assert mid == 1
    assert long == 2


def test_paired_metric_is_bet365_minus_pinnacle():
    frame = pd.DataFrame(
        {
            "league": ["EPL", "EPL"],
            "fixture_key": ["x", "x"],
            "bookmaker": ["BET365", "PINNACLE"],
            "overround": [0.06, 0.03],
        }
    )
    paired = mod._paired_metric(frame, "overround")
    assert len(paired) == 1
    assert paired.iloc[0]["delta"] == pytest.approx(0.03)


def test_bootstrap_zero_for_identical_pair_difference(monkeypatch):
    monkeypatch.setattr(mod, "BOOTSTRAP_DRAWS", 100)
    rows = []
    for league in mod.LEAGUE_ORDER:
        for fixture in range(5):
            rows.extend(
                [
                    {
                        "league": league,
                        "fixture_key": f"{league}-{fixture}",
                        "bookmaker": "BET365",
                        "fl_allocation_contrast": 0.01,
                    },
                    {
                        "league": league,
                        "fixture_key": f"{league}-{fixture}",
                        "bookmaker": "PINNACLE",
                        "fl_allocation_contrast": 0.01,
                    },
                ]
            )
    report = mod._bootstrap_delta(pd.DataFrame(rows), "fl_allocation_contrast")
    assert report["mean_delta_bet365_minus_pinnacle"] == pytest.approx(0.0)
    assert report["ci95_low"] == pytest.approx(0.0)
    assert report["ci95_high"] == pytest.approx(0.0)


def _metric_report(mean, low, high):
    return {
        "rows": 100,
        "mean_delta_bet365_minus_pinnacle": mean,
        "ci95_low": low,
        "ci95_high": high,
        "draws": 100,
    }


def _split(sign=1.0):
    closing_mean = 0.01 * sign
    opening_mean = 0.008 * sign
    return {
        "closing": {
            "paired": {
                "fl_allocation_contrast": _metric_report(
                    closing_mean,
                    0.002 * sign if sign > 0 else -0.02,
                    0.02 * sign if sign > 0 else -0.002,
                ),
                "alt_fl_allocation_contrast": _metric_report(
                    0.009 * sign,
                    0.001 * sign if sign > 0 else -0.02,
                    0.02 * sign if sign > 0 else -0.001,
                ),
            },
            "by_league": {
                "fl_allocation_contrast": {
                    "EPL": 0.01 * sign,
                    "LA_LIGA": 0.02 * sign,
                    "SERIE_A": -0.001 * sign,
                }
            },
        },
        "opening": {
            "paired": {
                "fl_allocation_contrast": _metric_report(
                    opening_mean,
                    -0.001,
                    0.02,
                )
            }
        },
    }


def test_formal_gate_requires_stable_allocation_not_just_overround():
    validation = _split(1.0)
    test = _split(1.0)
    gate = mod._formal_gate(validation, test)
    assert gate["supported"] is True
    assert gate["gates"]["oot_allocation_ci_excludes_zero"] is True

    test["closing"]["paired"]["fl_allocation_contrast"]["ci95_low"] = -0.001
    gate = mod._formal_gate(validation, test)
    assert gate["supported"] is False
    assert gate["gates"]["oot_allocation_ci_excludes_zero"] is False


def test_source_gap_result_fails_closed():
    result = mod._source_gap_result(
        {"validation_test_column_gate_passed": False},
        "MISSING_FROZEN_BOOKMAKER_OR_CONSENSUS_COLUMNS",
    )
    assert result["decision"] == "BLOCKED_BY_SOURCE_GAP"
    assert result["supported"] is False
    assert result["production_promotion"] is False
