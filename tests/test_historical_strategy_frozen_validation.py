import math

import pandas as pd

from historical_strategy_frozen_validation import frozen_validation


def sample_frame():
    rows = []
    seasons = ["2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"]
    for season_index, season in enumerate(seasons):
        for i in range(60):
            won = i < (42 if season_index < 3 else 36)
            rows.append({
                "league": "EPL", "season": season, "market_pick": "H",
                "market_confidence": 0.65, "selected_odds": 1.60,
                "won": won, "profit": 0.60 if won else -1.0,
            })
        for i in range(60):
            won = i < (24 if season_index < 3 else 45)
            rows.append({
                "league": "EPL", "season": season, "market_pick": "A",
                "market_confidence": 0.45, "selected_odds": 2.20,
                "won": won, "profit": 1.20 if won else -1.0,
            })
    return pd.DataFrame(rows)


def test_frozen_validation_selects_once_from_initial_window():
    summary, by_season = frozen_validation(sample_frame())
    row = summary.iloc[0]
    assert row["market_pick"] == "H"
    assert row["confidence_bucket"] == "60–70%"
    assert row["first_test_season"] == "2023-2024"
    assert row["test_seasons"] == 2
    assert set(by_season["market_pick"].unique()) == {"H"}


def test_frozen_validation_keeps_rule_even_if_alternative_improves_later():
    summary, _ = frozen_validation(sample_frame())
    row = summary.iloc[0]
    assert row["test_matches"] == 120
    assert row["test_wins"] == 72
    assert math.isclose(row["test_profit"], -4.8)
    assert math.isclose(row["test_roi"], -0.04)
