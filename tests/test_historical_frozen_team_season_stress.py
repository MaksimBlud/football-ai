import math

import pandas as pd

from historical_frozen_team_season_stress import team_season_stress


def sample_frames():
    rows = []
    for season, season_bonus in [("2019-2020", 0.0), ("2020-2021", 0.2), ("2021-2022", -0.1)]:
        for team, profits in {
            "Alpha": [0.5 + season_bonus, 0.5],
            "Beta": [0.4, -0.2 + season_bonus],
            "Gamma": [0.6, 0.3],
        }.items():
            for profit in profits:
                rows.append({
                    "league": "LA_LIGA",
                    "season": season,
                    "home_team": team,
                    "market_pick": "H",
                    "market_confidence": 0.65,
                    "selected_odds": 1.5,
                    "won": profit > 0,
                    "profit": profit,
                })
            rows.append({
                "league": "LA_LIGA",
                "season": season,
                "home_team": team,
                "market_pick": "H",
                "market_confidence": 0.55,
                "selected_odds": 1.8,
                "won": True,
                "profit": 5.0,
            })
    frozen = pd.DataFrame([{
        "league": "LA_LIGA",
        "first_test_season": "2019-2020",
        "market_pick": "H",
        "confidence_bucket": "60–70%",
    }])
    return pd.DataFrame(rows), frozen


def test_combined_stress_enumerates_all_season_team_pairs_without_other_bucket_rows():
    prepared, frozen = sample_frames()
    summary, details = team_season_stress(prepared, frozen)
    row = summary.iloc[0]
    assert row["base_matches"] == 18
    assert row["seasons"] == 3
    assert row["home_teams"] == 3
    assert row["combinations"] == 9
    assert len(details) == 9
    assert bool(row["all_combinations_positive"])
    assert details["remaining_matches"].eq(8).all()
    assert math.isclose(row["min_remaining_roi"], details["remaining_roi"].min())
    assert math.isclose(row["max_remaining_roi"], details["remaining_roi"].max())


def test_missing_required_prepared_column_is_rejected_by_frozen_membership_helper():
    prepared, frozen = sample_frames()
    prepared = prepared.drop(columns=["home_team"])
    try:
        team_season_stress(prepared, frozen)
    except ValueError as exc:
        assert "home_team" in str(exc)
    else:
        raise AssertionError("expected ValueError")
