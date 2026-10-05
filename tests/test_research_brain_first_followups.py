import numpy as np
import pandas as pd

import cross_market_lead_lag_temporal_stability_v1 as temporal
import kickoff_calendar_league_heterogeneity_v1 as heterogeneity


def test_kickoff_league_design_has_frozen_dimensions():
    frame = pd.DataFrame(
        {
            "p_market_over25": [0.45, 0.55, 0.50],
            "weekday": [0, 3, 6],
            "hour": [12.0, 18.0, 21.0],
            "slot": ["EARLY", "EVENING", "LATE"],
        }
    )
    baseline = heterogeneity._league_design(frame, False)
    calendar = heterogeneity._league_design(frame, True)
    assert baseline.shape == (3, 1)
    assert calendar.shape == (3, 12)
    assert np.isfinite(calendar).all()


def test_kickoff_pairwise_bootstrap_detects_clear_difference(monkeypatch):
    monkeypatch.setattr(heterogeneity, "BOOTSTRAP_DRAWS", 300)
    left = np.full(40, -0.05)
    right = np.full(40, 0.05)
    result = heterogeneity._pairwise_bootstrap_difference(left, right, seed=7)
    assert result["excludes_zero"] is True
    assert result["ci_high"] < 0.0


def test_between_season_stat_is_zero_for_equal_means():
    values = np.ones(len(temporal.SEASONS) * 3, dtype=float)
    seasons = np.repeat(np.arange(len(temporal.SEASONS)), 3)
    assert temporal._between_season_stat(values, seasons) == 0.0


def test_temporal_permutation_detects_large_frozen_season_shift(monkeypatch):
    monkeypatch.setattr(temporal, "PERMUTATION_DRAWS", 300)
    rows = []
    for league in temporal.LEAGUES:
        for season_index, season in enumerate(temporal.SEASONS):
            for _ in range(8):
                rows.append(
                    {
                        "league": league,
                        "season": season,
                        "alignment_dot": float(season_index),
                    }
                )
    frame = pd.DataFrame(rows)
    result = temporal._temporal_heterogeneity_permutation(frame)
    assert result["observed_between_season_variance"] > 0.0
    assert result["p_value"] < 0.05
