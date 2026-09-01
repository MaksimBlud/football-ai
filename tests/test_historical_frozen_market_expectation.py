import math

import numpy as np
import pandas as pd

from historical_frozen_market_expectation import (
    evaluate_frozen_market_expectation,
    poisson_binomial_upper_tail,
)


def test_poisson_binomial_matches_simple_binomial_case():
    probabilities = np.array([0.5, 0.5, 0.5])
    # P(X >= 2) = 4/8.
    assert math.isclose(poisson_binomial_upper_tail(probabilities, 2), 0.5)


def sample_prepared():
    return pd.DataFrame([
        {"league":"LA_LIGA","season":"2018-2019","market_pick":"H","market_confidence":0.65,"won":True},
        {"league":"LA_LIGA","season":"2019-2020","market_pick":"H","market_confidence":0.60,"won":True},
        {"league":"LA_LIGA","season":"2019-2020","market_pick":"H","market_confidence":0.69,"won":False},
        {"league":"LA_LIGA","season":"2020-2021","market_pick":"H","market_confidence":0.66,"won":True},
        {"league":"LA_LIGA","season":"2020-2021","market_pick":"A","market_confidence":0.65,"won":True},
        {"league":"EPL","season":"2019-2020","market_pick":"H","market_confidence":0.55,"won":False},
    ])


def sample_rules():
    return pd.DataFrame([
        {"league":"LA_LIGA","market_pick":"H","confidence_bucket":"60–70%","first_test_season":"2019-2020"},
        {"league":"EPL","market_pick":"H","confidence_bucket":"50–60%","first_test_season":"2019-2020"},
    ])


def test_evaluation_uses_only_frozen_test_rows():
    summary, by_season = evaluate_frozen_market_expectation(sample_prepared(), sample_rules())
    la = summary[summary["league"] == "LA_LIGA"].iloc[0]
    assert la["matches"] == 3
    assert la["wins"] == 2
    assert math.isclose(la["expected_wins"], 0.60 + 0.69 + 0.66)
    assert math.isclose(la["observed_accuracy"], 2 / 3)
    assert set(by_season[by_season["league"] == "LA_LIGA"]["season"]) == {"2019-2020", "2020-2021"}


def test_market_expectation_can_show_negative_excess():
    summary, _ = evaluate_frozen_market_expectation(sample_prepared(), sample_rules())
    epl = summary[summary["league"] == "EPL"].iloc[0]
    assert epl["matches"] == 1
    assert epl["wins"] == 0
    assert epl["excess_wins"] < 0
    assert epl["calibration_gap"] < 0


def test_invalid_observed_wins_are_rejected():
    try:
        poisson_binomial_upper_tail(np.array([0.5]), 2)
    except ValueError as exc:
        assert "observed_wins" in str(exc)
    else:
        raise AssertionError("expected ValueError")
