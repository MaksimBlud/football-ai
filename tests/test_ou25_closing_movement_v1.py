import numpy as np
import pandas as pd

import ou25_closing_movement_v1 as exp


def test_paired_prices_never_cross_provider_families():
    row = pd.Series(
        {
            "B365>2.5": 1.90,
            "B365<2.5": 1.95,
            "B365C>2.5": np.nan,
            "B365C<2.5": 1.85,
            "P>2.5": 1.91,
            "P<2.5": 1.99,
            "PC>2.5": 1.80,
            "PC<2.5": 2.10,
            "Avg>2.5": 1.92,
            "Avg<2.5": 1.98,
            "AvgC>2.5": 1.82,
            "AvgC<2.5": 2.08,
        }
    )
    paired = exp._paired_prices(row)
    assert paired == (1.91, 1.99, 1.80, 2.10, "PINNACLE")


def test_paired_prices_respects_frozen_priority():
    row = pd.Series(
        {
            "B365>2.5": 1.90,
            "B365<2.5": 2.00,
            "B365C>2.5": 1.80,
            "B365C<2.5": 2.10,
            "P>2.5": 1.91,
            "P<2.5": 1.99,
            "PC>2.5": 1.79,
            "PC<2.5": 2.11,
        }
    )
    assert exp._paired_prices(row)[-1] == "BET365"


def test_zero_movement_baseline_is_exact_opening_probability():
    actual = np.array([0.40, 0.50, 0.60])
    opening = actual.copy()
    scores = exp._scores(actual, opening)
    assert scores["rmse"] == 0.0
    assert scores["mae"] == 0.0


def test_direction_accuracy_excludes_exact_zero_movements():
    opening = np.array([0.50, 0.50, 0.50])
    actual = np.array([0.50, 0.55, 0.45])
    predicted = np.array([0.60, 0.60, 0.40])
    result = exp._direction_accuracy(opening, actual, predicted)
    assert result["n"] == 2
    assert result["accuracy"] == 1.0


def test_feature_contract_excludes_closing_and_same_match_outcomes():
    forbidden_tokens = ("closing", "FTHG", "FTAG", "FTR", "HC", "AC", "result", "cards")
    for feature in exp.FEATURES:
        assert all(token.lower() not in feature.lower() for token in forbidden_tokens)
    assert "opening_logit" in exp.FEATURES


def test_market_rows_target_is_closing_minus_opening_logit():
    raw = pd.DataFrame(
        [
            {
                "match_date": pd.Timestamp("2025-08-01"),
                "HomeTeam": "A",
                "AwayTeam": "B",
                "_season": "2025-2026",
                "B365>2.5": 2.00,
                "B365<2.5": 2.00,
                "B365C>2.5": 1.80,
                "B365C<2.5": 2.10,
            }
        ]
    )
    frame = exp._market_rows(raw)
    assert len(frame) == 1
    row = frame.iloc[0]
    assert np.isclose(row["movement_logit"], row["closing_logit"] - row["opening_logit"])
    assert row["price_source"] == "BET365"
