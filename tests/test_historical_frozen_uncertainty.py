import math

import pandas as pd

from historical_frozen_uncertainty import uncertainty_report


def sample_frame():
    return pd.DataFrame([
        {"league":"LA_LIGA","season":"2019-2020","matches":10,"wins":8,"profit":2.0,"roi":0.20},
        {"league":"LA_LIGA","season":"2020-2021","matches":10,"wins":8,"profit":1.0,"roi":0.10},
        {"league":"LA_LIGA","season":"2021-2022","matches":10,"wins":7,"profit":0.5,"roi":0.05},
        {"league":"EPL","season":"2019-2020","matches":10,"wins":5,"profit":-2.0,"roi":-0.20},
        {"league":"EPL","season":"2020-2021","matches":10,"wins":6,"profit":1.0,"roi":0.10},
        {"league":"EPL","season":"2021-2022","matches":10,"wins":5,"profit":-1.0,"roi":-0.10},
    ])


def test_uncertainty_report_is_deterministic_for_fixed_seed():
    first, _ = uncertainty_report(sample_frame(), samples=2000, seed=123)
    second, _ = uncertainty_report(sample_frame(), samples=2000, seed=123)
    pd.testing.assert_frame_equal(first, second)


def test_positive_league_has_positive_leave_one_out_results():
    summary, loo = uncertainty_report(sample_frame(), samples=5000, seed=123)
    la = summary[summary["league"] == "LA_LIGA"].iloc[0]
    assert la["matches"] == 30
    assert math.isclose(la["profit"], 3.5)
    assert math.isclose(la["roi"], 3.5 / 30)
    assert bool(la["leave_one_season_out_all_positive"])
    assert (loo[loo["league"] == "LA_LIGA"]["roi"] > 0).all()


def test_mixed_league_is_not_misreported_as_robust():
    summary, _ = uncertainty_report(sample_frame(), samples=5000, seed=123)
    epl = summary[summary["league"] == "EPL"].iloc[0]
    assert epl["roi"] < 0
    assert not bool(epl["leave_one_season_out_all_positive"])
    assert 0.0 <= epl["bootstrap_nonpositive_share"] <= 1.0


def test_missing_columns_are_rejected():
    frame = sample_frame().drop(columns=["profit"])
    try:
        uncertainty_report(frame, samples=100, seed=1)
    except ValueError as exc:
        assert "profit" in str(exc)
    else:
        raise AssertionError("expected ValueError")
