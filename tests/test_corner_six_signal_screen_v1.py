from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

import corner_six_signal_screen_v1 as mod


def _corner_frame():
    rows = []
    # Balanced synthetic examples across four cohorts.
    for cohort in mod.COHORT_ORDER:
        rows.extend(
            [
                {
                    "fixture_id": f"{cohort}-u",
                    "cohort": cohort,
                    "league": "EPL",
                    "opening_price_pressure": 0.04,
                    "centre_delta": 0.40,
                    "line_delta": 0.5,
                    "opening_lambda": 9.5,
                    "movement_magnitude": 0.40,
                    "material_move": 1,
                },
                {
                    "fixture_id": f"{cohort}-d",
                    "cohort": cohort,
                    "league": "EPL",
                    "opening_price_pressure": -0.03,
                    "centre_delta": -0.30,
                    "line_delta": -0.5,
                    "opening_lambda": 10.5,
                    "movement_magnitude": 0.30,
                    "material_move": 0,
                },
                {
                    "fixture_id": f"{cohort}-z",
                    "cohort": cohort,
                    "league": "EPL",
                    "opening_price_pressure": 0.01,
                    "centre_delta": 0.0,
                    "line_delta": 0.0,
                    "opening_lambda": 10.0,
                    "movement_magnitude": 0.0,
                    "material_move": 0,
                },
            ]
        )
    return pd.DataFrame(rows)


def test_direction_metrics_balanced_perfect_signal():
    frame = _corner_frame()
    result = mod._direction_metrics(
        frame,
        score_col="opening_price_pressure",
        target_col="centre_delta",
    )
    assert result["rows"] == 8
    assert result["accuracy"] == 1.0
    assert result["balanced_accuracy"] == 1.0
    assert result["recall_up"] == 1.0
    assert result["recall_down"] == 1.0


def test_signal_1_requires_cross_cohort_portability():
    result = mod.signal_1_opening_price_pressure(_corner_frame())
    assert result["supported"] is True
    assert result["positive_spearman_cohorts"] == 4


def test_signal_2_separates_line_move_hazard_and_direction():
    frame = _corner_frame()
    result = mod.signal_2_line_transition(frame)
    assert result["pooled_direction"]["balanced_accuracy"] == 1.0
    assert result["pooled_move_hazard"]["line_moves"] == 8


def test_market_feature_row_devigs_prices():
    row = pd.Series(
        {
            "B365H": 2.0,
            "B365D": 4.0,
            "B365A": 4.0,
            "B365>2.5": 1.8,
            "B365<2.5": 2.0,
            "AHh": -0.5,
            "B365AHH": 1.9,
            "B365AHA": 1.9,
        }
    )
    out = mod._market_feature_row(row)
    assert out is not None
    assert abs(out["p_home"] - 0.5) < 1e-12
    assert abs(out["p_draw"] - 0.25) < 1e-12
    assert abs(out["p_away"] - 0.25) < 1e-12
    assert out["p_over25"] > 0.5
    assert out["ah_line"] == -0.5
    assert abs(out["p_ah_home"] - 0.5) < 1e-12


def test_referee_shrinkage_moves_toward_league_mean():
    frame = pd.DataFrame(
        {
            "season": ["2024-2025"] * 4,
            "HC": [10, 9, 2, 2],
            "AC": [5, 4, 2, 2],
            "Referee": ["High", "High", "Low", "Low"],
        }
    )
    mean_value, biases, counts = mod._referee_bias_table(
        frame,
        seasons={"2024-2025"},
    )
    assert counts == {"High": 2, "Low": 2}
    assert biases["High"] > 0
    assert biases["Low"] < 0
    assert abs(biases["High"]) < abs((14.0 - mean_value))


def test_volatility_history_strictly_before_target():
    raw = pd.DataFrame(
        {
            "season": ["2025-2026"] * 3 + ["2026-2027"] * 2,
            "match_date": pd.to_datetime(
                ["2026-05-01", "2026-05-08", "2026-05-15", "2026-08-20", "2026-08-27"]
            ),
            "HomeTeam": ["Arsenal", "X", "Arsenal", "Arsenal", "Arsenal"],
            "AwayTeam": ["A", "Arsenal", "B", "C", "D"],
            "HC": [5, 4, 6, 7, 99],
            "AC": [3, 5, 2, 4, 99],
        }
    )
    values = mod._team_corner_environment_history(
        raw,
        "Arsenal",
        pd.Timestamp("2026-08-27"),
    )
    assert values == [8.0, 9.0, 8.0, 11.0]


def test_regime_change_capability_does_not_invent_schema():
    frames = {
        league: pd.DataFrame(
            columns=["Date", "HomeTeam", "AwayTeam", "Referee", "HC", "AC"]
        )
        for league in mod.LEAGUES
    }
    result = mod.signal_6_regime_change_capability(frames)
    assert result["explicit_regime_change_schema_detected"] is False
    assert result["supported"] is False
    assert result["verdict"] == "EXISTING_SOURCE_DATA_GAP_FOR_REGIME_CHANGE_SIGNAL"


def test_raw_corner_parser_uses_bet365_open_and_close():
    payload = {
        "success": 1,
        "data": {
            "fixture_id": 123,
            "bookmakers": [
                {
                    "slug": "bet365",
                    "name": "Bet 365",
                    "odds": {
                        "corner_line": {
                            "opening": {"line": 9.5, "over": 1.8, "under": 2.0},
                            "closing": {"line": 10.0, "over": 1.9, "under": 1.9},
                            "inplay": {"line": 11.5, "over": 2.0, "under": 1.8},
                        }
                    },
                }
            ],
        },
    }
    out = mod._raw_corner_row(payload)
    assert out["fixture_id"] == "123"
    assert out["opening_line"] == 9.5
    assert out["closing_line"] == 10.0
