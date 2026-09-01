import math

import pandas as pd

from historical_frozen_team_concentration import team_concentration


def test_team_concentration_preserves_frozen_oos_membership_and_leave_one_out():
    rows = []
    for season in ["2016-2017", "2017-2018", "2018-2019", "2019-2020", "2020-2021"]:
        for team, profits in {
            "Alpha": [0.5, 0.5],
            "Beta": [0.5, -1.0],
            "Gamma": [0.5, 0.5],
        }.items():
            for profit in profits:
                rows.append({
                    "league": "LA_LIGA",
                    "season": season,
                    "home_team": team,
                    "market_pick": "H",
                    "market_confidence": 0.65,
                    "selected_odds": 1.5,
                    "profit": profit,
                    "won": profit > 0,
                })
            rows.append({
                "league": "LA_LIGA",
                "season": season,
                "home_team": team,
                "market_pick": "H",
                "market_confidence": 0.55,
                "selected_odds": 1.8,
                "profit": 10.0,
                "won": True,
            })
    frozen = pd.DataFrame([{
        "league": "LA_LIGA",
        "first_test_season": "2019-2020",
        "market_pick": "H",
        "confidence_bucket": "60–70%",
    }])

    summary, by_team, leave_one_out = team_concentration(pd.DataFrame(rows), frozen)
    row = summary.iloc[0]
    assert row["matches"] == 12
    assert math.isclose(row["profit"], 3.0)
    assert math.isclose(row["roi"], 3.0 / 12.0)
    assert row["home_teams"] == 3
    assert row["profitable_home_teams"] == 2
    assert bool(row["leave_one_team_out_all_positive"])
    assert set(by_team["home_team"]) == {"Alpha", "Beta", "Gamma"}
    beta_loo = leave_one_out[leave_one_out["excluded_home_team"] == "Beta"].iloc[0]
    assert math.isclose(beta_loo["remaining_profit"], 4.0)
    assert math.isclose(beta_loo["remaining_roi"], 0.5)


def test_missing_home_team_is_rejected():
    prepared = pd.DataFrame([{
        "league": "LA_LIGA", "season": "2019-2020", "market_pick": "H",
        "market_confidence": 0.65, "selected_odds": 1.5, "profit": 0.5, "won": True,
    }])
    frozen = pd.DataFrame([{
        "league": "LA_LIGA", "first_test_season": "2019-2020",
        "market_pick": "H", "confidence_bucket": "60–70%",
    }])
    try:
        team_concentration(prepared, frozen)
    except ValueError as exc:
        assert "home_team" in str(exc)
    else:
        raise AssertionError("expected ValueError")
