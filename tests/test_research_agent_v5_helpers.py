import numpy as np
import pandas as pd
import pytest

from cross_market_lead_lag_anomaly_audit_v1 import _overround, _smd, _tv
from kickoff_calendar_context_v1 import _design, _devig_over, _slot


def test_overround_and_tv_helpers():
    assert _overround((2.0, 2.0)) == pytest.approx(0.0)
    assert _tv({"+0.5": 1.0}, {"+0.5": 0.5, "-0.5": 0.5}) == pytest.approx(0.5)


def test_smd_uses_reference_dispersion():
    target = pd.Series([3.0, 4.0, 5.0])
    reference = pd.Series([0.0, 1.0, 2.0, 3.0])
    value = _smd(target, reference)
    assert value is not None
    assert value > 1.0


@pytest.mark.parametrize(
    ("hour", "slot"),
    [(12.0, "EARLY"), (15.5, "AFTERNOON"), (18.0, "EVENING"), (21.0, "LATE")],
)
def test_kickoff_slots(hour, slot):
    assert _slot(hour) == slot


def test_market_devig_and_design_dimensions():
    assert _devig_over(2.0, 2.0) == pytest.approx(0.5)
    frame = pd.DataFrame(
        {
            "league": ["EPL", "LA_LIGA", "SERIE_A"],
            "weekday": [0, 1, 2],
            "hour": [12.0, 18.0, 21.0],
            "slot": ["EARLY", "EVENING", "LATE"],
            "p_market_over25": [0.45, 0.50, 0.55],
        }
    )
    baseline = _design(frame, False)
    calendar = _design(frame, True)
    assert baseline.shape == (3, 3)
    assert calendar.shape == (3, 14)
    assert np.isfinite(calendar).all()
