import numpy as np
import pandas as pd

from bookmaker_reconstruction_full_coverage_v1 import (
    BASELINE_SOURCE,
    CANDIDATE_SOURCE,
    FINAL_SEASON,
    SEASONS,
    pair_mask,
    paired_bootstrap,
)


def test_fixed_full_coverage_comparison_contract():
    assert BASELINE_SOURCE == "B365"
    assert CANDIDATE_SOURCE == "AVG"
    assert SEASONS[0] == "2016-2017"
    assert SEASONS[-1] == "2025-2026"
    assert FINAL_SEASON == "2025-2026"
    assert "2026-2027" not in SEASONS


def test_pair_mask_requires_b365_and_avg_but_not_ps():
    frame = pd.DataFrame([
        {
            "B365_home_odds": 2.0, "B365_draw_odds": 3.5, "B365_away_odds": 4.0,
            "AVG_home_odds": 2.1, "AVG_draw_odds": 3.4, "AVG_away_odds": 4.1,
            "PS_home_odds": np.nan, "PS_draw_odds": np.nan, "PS_away_odds": np.nan,
        },
        {
            "B365_home_odds": 2.0, "B365_draw_odds": 3.5, "B365_away_odds": 4.0,
            "AVG_home_odds": np.nan, "AVG_draw_odds": np.nan, "AVG_away_odds": np.nan,
            "PS_home_odds": 2.0, "PS_draw_odds": 3.5, "PS_away_odds": 4.0,
        },
    ])
    assert pair_mask(frame).tolist() == [True, False]


def test_paired_bootstrap_is_deterministic():
    values = np.array([-0.1, -0.05, 0.02, -0.03, -0.04], dtype=float)
    a = paired_bootstrap(values, reps=1000, seed=11)
    b = paired_bootstrap(values, reps=1000, seed=11)
    assert a == b
    assert a["observed_delta"] < 0
