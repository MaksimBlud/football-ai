import pandas as pd

from historical_cross_bookmaker_validation import _evaluate


def test_provider_evaluation_applies_fixed_home_60_70_rule():
    frame = pd.DataFrame({
        "FTR": ["H", "A", "H"],
        "PSH": [1.50, 1.55, 2.20], "PSD": [4.0, 4.0, 3.4], "PSA": [7.0, 6.0, 3.2],
    })
    result = _evaluate(frame, ("PSH", "PSD", "PSA"), pick="H", bucket="60–70%")
    assert result["matches"] == 2
    assert result["wins"] == 1
    assert result["profit"] < 0


def test_missing_provider_columns_returns_zero_coverage():
    frame = pd.DataFrame({"FTR": ["H"]})
    result = _evaluate(frame, ("PSH", "PSD", "PSA"), pick="H", bucket="60–70%")
    assert result["matches"] == 0
    assert result["roi"] is None
