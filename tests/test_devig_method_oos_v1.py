import numpy as np
import pandas as pd
import pytest

import devig_method_oos_v1 as mod


@pytest.mark.parametrize(
    "fn_name",
    ["_multiplicative", "_additive", "_power", "_shin"],
)
def test_all_methods_sum_to_one(fn_name):
    fn = getattr(mod, fn_name)
    p = fn((1.60, 4.00, 6.00))
    assert p is not None
    assert np.all(p > 0)
    assert np.all(p < 1)
    assert float(p.sum()) == pytest.approx(1.0, abs=1e-10)


def test_all_methods_agree_when_book_is_already_fair():
    odds = (2.0, 4.0, 4.0)
    expected = np.array([0.5, 0.25, 0.25])
    for method in mod.METHODS:
        p = mod.TRANSFORMS[method](odds)
        assert p is not None
        assert p == pytest.approx(expected, abs=1e-9)


def test_additive_fails_closed_when_probability_turns_nonpositive():
    # Large overround plus a very long price can make the standard additive
    # transform invalid. The evaluator must report invalid coverage, not clip it.
    assert mod._additive((1.20, 5.0, 100.0)) is None


def test_shin_fails_closed_for_underround():
    assert mod._shin((4.0, 4.0, 4.0)) is None


def test_validation_winner_is_selected_without_test_data():
    frame = pd.DataFrame(
        {
            "common_valid": [True, True, True],
            "multiplicative_valid": [True, True, True],
            "additive_valid": [True, True, True],
            "power_valid": [True, True, True],
            "shin_valid": [True, True, True],
            "outcome_index": [0, 1, 2],
            "multiplicative_p": [
                np.array([0.55, 0.25, 0.20]),
                np.array([0.45, 0.30, 0.25]),
                np.array([0.45, 0.30, 0.25]),
            ],
            "additive_p": [
                np.array([0.60, 0.22, 0.18]),
                np.array([0.40, 0.35, 0.25]),
                np.array([0.40, 0.25, 0.35]),
            ],
            "power_p": [
                np.array([0.56, 0.24, 0.20]),
                np.array([0.44, 0.31, 0.25]),
                np.array([0.44, 0.29, 0.27]),
            ],
            "shin_p": [
                np.array([0.57, 0.24, 0.19]),
                np.array([0.43, 0.32, 0.25]),
                np.array([0.43, 0.27, 0.30]),
            ],
        }
    )
    assert mod._validation_winner(frame) == "additive"


def test_cluster_bootstrap_zero_for_identical_losses(monkeypatch):
    monkeypatch.setattr(mod, "BOOTSTRAP_DRAWS", 100)
    rows = []
    for league in mod.LEAGUE_ORDER:
        for fixture in range(4):
            for bookmaker in ("BET365", "PINNACLE"):
                p = np.array([0.5, 0.3, 0.2])
                rows.append(
                    {
                        "league": league,
                        "fixture_key": f"{league}-{fixture}",
                        "bookmaker": bookmaker,
                        "common_valid": True,
                        "outcome_index": fixture % 3,
                        "multiplicative_p": p,
                        "shin_p": p.copy(),
                    }
                )
    frame = pd.DataFrame(rows)
    result = mod._paired_cluster_bootstrap(frame, "shin")
    assert result["mean_delta"] == pytest.approx(0.0)
    assert result["ci95_low"] == pytest.approx(0.0)
    assert result["ci95_high"] == pytest.approx(0.0)


def test_confirmation_gate_requires_two_bookmakers():
    rows = []
    p_base = np.array([0.50, 0.30, 0.20])
    p_alt = np.array([0.60, 0.25, 0.15])
    for league in mod.LEAGUE_ORDER:
        for fixture in range(20):
            rows.append(
                {
                    "league": league,
                    "fixture_key": f"{league}-{fixture}",
                    "bookmaker": "BET365",
                    "common_valid": True,
                    "outcome_index": 0,
                    "multiplicative_p": p_base,
                    "shin_p": p_alt,
                    "shin_valid": True,
                }
            )
    closing = pd.DataFrame(rows)
    opening = closing.copy()
    result = mod._confirmation_gate(closing, opening, "shin", ["BET365"])
    assert result["confirmed"] is False
    assert result["gate"]["at_least_two_bookmakers"] is False


def test_source_gap_result_is_fail_closed():
    result = mod._source_gap_result(
        {
            "included_bookmakers": ["BET365"],
            "excluded_bookmakers": ["PINNACLE"],
        },
        "FEWER_THAN_TWO_FROZEN_BOOKMAKERS_HAVE_VALIDATION_TEST_COLUMNS",
    )
    assert result["decision"] == "BLOCKED_BY_SOURCE_GAP"
    assert result["supported"] is False
    assert result["production_promotion"] is False
