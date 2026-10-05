import numpy as np
import pandas as pd
import pytest

from cross_market_lead_lag_anomaly_audit_v1 import (\n    REQUIRED_COLUMNS,\n    _coverage_cell,\n    _missing_required_columns,\n    _overround,\n    _smd,\n    _tv,\n)
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


def test_v5_anomaly_uses_v1_season_keyed_coverage():
    coverage = {
        "2024-2025": {
            "source_rows": 100,
            "complete_open_close_same_book_rows": 80,
            "half_goal_ah_rows": 60,
            "reconstructed_rows": 50,
        }
    }
    assert _coverage_cell(coverage, "2024-2025")["reconstructed_rows"] == 50
    with pytest.raises(RuntimeError, match="missing V1 coverage"):
        _coverage_cell(coverage, "2025-2026")


def test_v5_schema_audit_detects_all_nan_season_columns():
    row = {column: 2.0 for column in REQUIRED_COLUMNS}
    frame = pd.DataFrame([row])
    frame["B365CH"] = np.nan
    missing = _missing_required_columns(frame)
    assert "B365CH" in missing
    assert "B365H" not in missing
