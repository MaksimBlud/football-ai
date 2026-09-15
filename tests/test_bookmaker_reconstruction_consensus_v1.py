import numpy as np
import pandas as pd

from bookmaker_reconstruction_consensus_v1 import (
    BASELINE_SOURCE,
    SOURCES,
    TEST_SEASON,
    VALIDATION_SEASON,
    common_source_frame,
    coverage_report,
    fair_probabilities,
    raw_source_frame,
    source_available,
    source_dispersion,
)


def test_raw_source_frame_keeps_sources_independent_and_date():
    raw = pd.DataFrame([{
        "Date": "17/08/2025",
        "FTR": "H",
        "B365H": 1.80, "B365D": 3.60, "B365A": 5.00,
        "PSH": 1.84, "PSD": 3.70, "PSA": 5.10,
        "AvgH": 1.82, "AvgD": 3.65, "AvgA": 5.05,
    }])
    frame = raw_source_frame(raw, "EPL", VALIDATION_SEASON)
    assert frame.loc[0, "B365_home_odds"] == 1.80
    assert frame.loc[0, "PS_home_odds"] == 1.84
    assert frame.loc[0, "AVG_home_odds"] == 1.82
    assert frame.loc[0, "match_date"] == pd.Timestamp("2025-08-17")


def test_each_source_maps_to_valid_fair_probabilities():
    frame = pd.DataFrame([{
        "result": "H",
        "B365_home_odds": 1.80, "B365_draw_odds": 3.60, "B365_away_odds": 5.00,
        "PS_home_odds": 1.84, "PS_draw_odds": 3.70, "PS_away_odds": 5.10,
        "AVG_home_odds": 1.82, "AVG_draw_odds": 3.65, "AVG_away_odds": 5.05,
    }])
    for source in SOURCES:
        p = fair_probabilities(frame, source)
        assert np.isfinite(p).all()
        assert np.allclose(p.sum(axis=1), 1.0)
        assert (p > 0).all() and (p < 1).all()


def test_coverage_report_preserves_missing_source_information_before_common_filter():
    frame = pd.DataFrame([
        {
            "league": "EPL", "season": TEST_SEASON, "match_date": pd.Timestamp("2025-08-01"), "result": "H",
            "B365_home_odds": 2.0, "B365_draw_odds": 3.5, "B365_away_odds": 4.0,
            "PS_home_odds": 2.1, "PS_draw_odds": 3.4, "PS_away_odds": 4.1,
            "AVG_home_odds": 2.05, "AVG_draw_odds": 3.45, "AVG_away_odds": 4.05,
        },
        {
            "league": "EPL", "season": TEST_SEASON, "match_date": pd.Timestamp("2025-09-01"), "result": "D",
            "B365_home_odds": 2.0, "B365_draw_odds": 3.5, "B365_away_odds": 4.0,
            "PS_home_odds": np.nan, "PS_draw_odds": np.nan, "PS_away_odds": np.nan,
            "AVG_home_odds": 2.05, "AVG_draw_odds": 3.45, "AVG_away_odds": 4.05,
        },
    ])
    assert source_available(frame, "B365").sum() == 2
    assert source_available(frame, "PS").sum() == 1
    assert len(common_source_frame(frame)) == 1
    report = coverage_report(frame)
    pooled = report["pooled_by_season"][TEST_SEASON]
    assert pooled["total_matches"] == 2
    assert pooled["source_available"] == {"B365": 2, "PS": 1, "AVG": 2}
    assert pooled["common_all_sources"] == 1
    assert pooled["common_all_sources_fraction"] == 0.5
    assert len(report["test_monthly"]) == 2


def test_dispersion_is_zero_when_sources_identical():
    frame = pd.DataFrame([{
        "B365_home_odds": 2.0, "B365_draw_odds": 3.5, "B365_away_odds": 4.0,
        "PS_home_odds": 2.0, "PS_draw_odds": 3.5, "PS_away_odds": 4.0,
        "AVG_home_odds": 2.0, "AVG_draw_odds": 3.5, "AVG_away_odds": 4.0,
    }])
    assert np.allclose(source_dispersion(frame), 0.0)


def test_temporal_and_baseline_contract():
    assert BASELINE_SOURCE == "B365"
    assert VALIDATION_SEASON == "2024-2025"
    assert TEST_SEASON == "2025-2026"
    assert set(SOURCES) == {"B365", "PS", "AVG"}
