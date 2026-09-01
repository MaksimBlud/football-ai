import math

import pandas as pd

from historical_frozen_closing_comparison import compare_rule


def test_compare_rule_keeps_selection_on_standard_prices_only():
    frame = pd.DataFrame({
        "FTR": ["H", "A", "H"],
        "B365H": [1.50, 1.55, 2.20], "B365D": [4.0, 4.0, 3.4], "B365A": [7.0, 6.0, 3.2],
        "B365CH": [1.40, 1.70, 1.90], "B365CD": [4.2, 3.8, 3.5], "B365CA": [8.0, 5.0, 4.2],
    })
    result = compare_rule(frame, pick="H", confidence_bucket="60–70%")
    assert result["matches"] == 2
    assert result["wins"] == 1
    assert math.isclose(result["standard_profit"], -0.5)
    assert math.isclose(result["closing_profit"], -0.6)
    assert result["mean_closing_odds"] != result["mean_standard_odds"]


def test_missing_explicit_closing_columns_are_rejected():
    frame = pd.DataFrame({"FTR": ["H"], "B365H": [1.5], "B365D": [4.0], "B365A": [7.0]})
    try:
        compare_rule(frame, pick="H", confidence_bucket="60–70%")
    except ValueError as exc:
        assert "B365CH" in str(exc)
    else:
        raise AssertionError("expected ValueError")
