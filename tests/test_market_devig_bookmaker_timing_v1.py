import numpy as np
import pandas as pd

import market_devig_bookmaker_timing_v1 as experiment


def _base_rows():
    rows = []
    for season in experiment.SEASONS:
        for index in range(10):
            rows.append(
                {
                    "season": season,
                    "_season_row": index,
                    "FTR": "H" if index % 3 == 0 else ("D" if index % 3 == 1 else "A"),
                    "AvgH": 1.80,
                    "AvgD": 3.50,
                    "AvgA": 4.50,
                    "B365H": 1.82,
                    "B365D": 3.45,
                    "B365A": 4.40,
                    "PSH": 1.85,
                    "PSD": 3.40,
                    "PSA": 4.30,
                    "AvgCH": 1.79,
                    "AvgCD": 3.55,
                    "AvgCA": 4.60,
                    "B365CH": 1.80,
                    "B365CD": 3.50,
                    "B365CA": 4.50,
                    "PSCH": 1.83,
                    "PSCD": 3.45,
                    "PSCA": 4.40,
                }
            )
    return pd.DataFrame(rows)


def test_source_availability_requires_minimum_coverage_each_season():
    frame = _base_rows()
    info = experiment.source_availability(frame, "PINNACLE_CLOSING")
    assert info["eligible"] is True

    # Destroy two of ten rows in one season -> 80%, below the frozen 90% gate.
    mask = frame["season"].eq("2023/2024")
    bad_index = frame.index[mask][:2]
    frame.loc[bad_index, "PSCH"] = np.nan
    info = experiment.source_availability(frame, "PINNACLE_CLOSING")
    assert info["eligible"] is False
    assert info["by_season"]["2023/2024"]["coverage"] == 0.8


def test_missing_source_columns_fail_closed():
    frame = _base_rows().drop(columns=["PSCH", "PSCD", "PSCA"])
    info = experiment.source_availability(frame, "PINNACLE_CLOSING")
    assert info["columns_present"] is False
    assert info["eligible"] is False
    assert info["valid_rows_total"] == 0


def test_source_frame_uses_exact_price_columns():
    frame = _base_rows()
    local = experiment.source_frame(frame, "BET365_STANDARD")

    assert set(
        ["season", "_season_row", "result", "home_odds", "draw_odds", "away_odds"]
    ).issubset(local.columns)
    assert np.isclose(local.iloc[0]["home_odds"], 1.82)
    assert np.isclose(local.iloc[0]["draw_odds"], 3.45)
    assert np.isclose(local.iloc[0]["away_odds"], 4.40)


def test_selection_fails_closed_without_three_joint_wins():
    reports = {
        method: {"by_season": {}}
        for method in experiment.METHODS
    }

    for index, season in enumerate(experiment.DISCOVERY_SEASONS):
        reports["MULTIPLICATIVE"]["by_season"][season] = {
            "matches": 380,
            "logloss": 1.0,
            "brier": 0.6,
        }

        # SHIN wins two seasons only.
        reports["SHIN"]["by_season"][season] = {
            "matches": 380,
            "logloss": 0.98 if index < 2 else 1.002,
            "brier": 0.58 if index < 2 else 0.602,
        }

        for method in ("ADDITIVE", "POWER"):
            reports[method]["by_season"][season] = {
                "matches": 380,
                "logloss": 1.01,
                "brier": 0.61,
            }

    selected, summary = experiment.select_method(reports)

    assert summary["alternatives"]["SHIN"]["joint_season_wins"] == 2
    assert summary["alternatives"]["SHIN"]["eligible"] is False
    assert selected == "MULTIPLICATIVE"


def test_closing_sources_are_diagnostic_labels_not_production_activation():
    assert "AVG_CLOSING" in experiment.SOURCE_COLUMNS
    assert "BET365_CLOSING" in experiment.SOURCE_COLUMNS
    assert "PINNACLE_CLOSING" in experiment.SOURCE_COLUMNS
    assert experiment.TEST_SEASON == "2025/2026"
    assert "2026/2027" not in experiment.SEASONS
