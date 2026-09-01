import math

import pandas as pd

from historical_market_timing_audit import audit_frame


def test_audit_reports_standard_and_closing_coverage_without_opening_claim():
    frame = pd.DataFrame({
        "B365H": [2.0, 1.8], "B365D": [3.5, 3.6], "B365A": [4.0, 4.5],
        "B365CH": [1.9, 1.9], "B365CD": [3.6, 3.5], "B365CA": [4.2, 4.2],
    })
    rows = audit_frame(frame, league="EPL", season="2024-2025")
    bet365 = next(row for row in rows if row["provider"] == "BET365")
    assert bet365["standard_columns"] == "B365H/B365D/B365A"
    assert bet365["closing_columns"] == "B365CH/B365CD/B365CA"
    assert bet365["standard_valid_rows"] == 2
    assert bet365["closing_valid_rows"] == 2
    assert bet365["paired_valid_rows"] == 2
    assert bet365["mean_abs_no_vig_probability_delta"] > 0
    assert 0 <= bet365["argmax_change_rate"] <= 1


def test_missing_closing_columns_are_reported_not_inferred():
    frame = pd.DataFrame({"PSH": [2.0], "PSD": [3.5], "PSA": [4.0]})
    rows = audit_frame(frame, league="LA_LIGA", season="2018-2019")
    pinnacle = next(row for row in rows if row["provider"] == "PINNACLE")
    assert pinnacle["standard_present"] is True
    assert pinnacle["closing_present"] is False
    assert pinnacle["paired_valid_rows"] == 0
    assert pinnacle["mean_abs_no_vig_probability_delta"] is None
    assert pinnacle["argmax_change_rate"] is None
