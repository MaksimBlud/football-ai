import math

import numpy as np
import pandas as pd
from scipy.stats import poisson

import corner_market_state_repricing_v1 as m


def _fair_prices_from_probability(p):
    return 1.0 / p, 1.0 / (1.0 - p)


def test_devig_probability():
    assert abs(m.devig_over_probability(2.0, 2.0) - 0.5) < 1e-12


def test_half_line_poisson_reconstruction_round_trip():
    lam = 10.2
    line = 9.5
    p = float(poisson.sf(9, lam))
    over, under = _fair_prices_from_probability(p)
    recovered = m.implied_poisson_centre(line, over, under)
    assert abs(recovered - lam) < 1e-8


def test_integer_line_poisson_reconstruction_round_trip():
    lam = 9.7
    line = 10.0
    p_over_win = float(poisson.sf(10, lam))
    p_under_win = float(poisson.cdf(9, lam))
    p = p_over_win / (p_over_win + p_under_win)
    over, under = _fair_prices_from_probability(p)
    recovered = m.implied_poisson_centre(line, over, under)
    assert abs(recovered - lam) < 1e-8


def test_quarter_line_fails_closed():
    try:
        m.implied_poisson_centre(9.25, 1.9, 1.9)
    except ValueError as exc:
        assert "unsupported" in str(exc)
    else:
        raise AssertionError("quarter line must fail closed")


def test_sample_gate_requires_all_five_leagues():
    rows = []
    for league in m.LEAGUES[:-1]:
        for idx in range(10):
            rows.append(
                {
                    "fixture_id": f"{league}-{idx}",
                    "league": league,
                    "opening_line": 9.5,
                    "opening_over_prob": 0.5,
                    "market_entropy": math.log(2.0),
                    "price_imbalance": 0.0,
                    "opening_lambda": 10.0,
                    "closing_lambda": 10.1,
                    "centre_delta": 0.1,
                    "movement_magnitude": 0.1,
                }
            )
    report = m.evaluate(pd.DataFrame(rows))
    assert report["verdict"] == "SAMPLE_TOO_SMALL"


def test_frozen_contract_constants():
    assert m.EXPERIMENT_ID == "CORNER_MARKET_STATE_REPRICING_V1"
    assert m.MOVEMENT_QUANTILE == 0.75
    assert m.LOGISTIC_C == 0.1
    assert m.MIN_TOTAL_ROWS == 40
    assert m.MIN_ROWS_PER_LEAGUE == 6
    assert set(m.FEATURES) == {
        "FULL_STATE",
        "OVER_LEVEL",
        "ENTROPY",
        "LINE_LEVEL",
        "PRICE_IMBALANCE",
        "FAIR_CENTRE",
    }
