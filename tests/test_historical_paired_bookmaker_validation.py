import math

import pandas as pd

from historical_paired_bookmaker_validation import (
    price_selected_rows,
    reference_mask,
)


def sample_frame():
    return pd.DataFrame([
        {
            "FTR": "H",
            "B365H": 1.50, "B365D": 4.00, "B365A": 7.00,
            "B365CH": 1.55, "B365CD": 4.10, "B365CA": 7.20,
            "PSH": 1.60, "PSD": 4.20, "PSA": 7.50,
            "PSCH": 1.58, "PSCD": 4.15, "PSCA": 7.30,
        },
        {
            "FTR": "A",
            "B365H": 1.55, "B365D": 4.00, "B365A": 6.50,
            "B365CH": 1.60, "B365CD": 4.00, "B365CA": 6.40,
            "PSH": 2.20, "PSD": 3.40, "PSA": 3.20,
            "PSCH": 2.10, "PSCD": 3.45, "PSCA": 3.30,
        },
        {
            "FTR": "H",
            "B365H": 2.20, "B365D": 3.30, "B365A": 3.40,
            "B365CH": 2.15, "B365CD": 3.35, "B365CA": 3.50,
            "PSH": 2.10, "PSD": 3.40, "PSA": 3.60,
            "PSCH": 2.05, "PSCD": 3.45, "PSCA": 3.70,
        },
    ])


def test_reference_mask_uses_only_bet365_standard_membership():
    frame = sample_frame()
    mask = reference_mask(frame, pick="H", bucket="60–70%")
    assert list(mask) == [True, True, False]
    # Changing Pinnacle prices must not alter membership.
    changed = frame.copy()
    changed.loc[:, ["PSH", "PSD", "PSA"]] = [10.0, 2.0, 1.30]
    assert list(reference_mask(changed, pick="H", bucket="60–70%")) == list(mask)


def test_other_provider_only_prices_same_reference_rows():
    frame = sample_frame()
    mask = reference_mask(frame, pick="H", bucket="60–70%")
    metrics = price_selected_rows(frame, mask, ("PSH", "PSD", "PSA"), pick="H")
    assert metrics["reference_selected_matches"] == 2
    assert metrics["priced_matches"] == 2
    assert metrics["wins"] == 1
    # Same two fixtures: +0.60 for first home win and -1 for second loss.
    assert math.isclose(metrics["profit"], -0.40)
    assert math.isclose(metrics["roi"], -0.20)


def test_missing_provider_price_reduces_coverage_without_reselection():
    frame = sample_frame()
    frame.loc[1, "PSH"] = None
    mask = reference_mask(frame, pick="H", bucket="60–70%")
    metrics = price_selected_rows(frame, mask, ("PSH", "PSD", "PSA"), pick="H")
    assert metrics["reference_selected_matches"] == 2
    assert metrics["priced_matches"] == 1
    assert math.isclose(metrics["price_coverage"], 0.5)
    assert metrics["wins"] == 1
    assert math.isclose(metrics["roi"], 0.60)
