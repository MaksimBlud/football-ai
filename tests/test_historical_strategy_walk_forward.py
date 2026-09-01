import math

import pandas as pd

from historical_strategy_walk_forward import summary_table, walk_forward


def sample_frame():
    rows = []
    seasons = ["2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"]
    for season_index, season in enumerate(seasons):
        for i in range(20):
            won = i < (14 if season_index < 3 else 10)
            rows.append({
                "league": "EPL", "season": season, "market_pick": "H",
                "market_confidence": 0.65, "selected_odds": 1.60,
                "won": won, "profit": 0.60 if won else -1.0,
            })
        for i in range(20):
            won = i < (8 if season_index < 3 else 12)
            rows.append({
                "league": "EPL", "season": season, "market_pick": "A",
                "market_confidence": 0.45, "selected_odds": 2.20,
                "won": won, "profit": 1.20 if won else -1.0,
            })
    return pd.DataFrame(rows)


def test_walk_forward_evaluates_all_fixed_candidates_without_selection():
    evaluations = walk_forward(sample_frame())
    assert set(evaluations["test_season"].unique()) == {"2023-2024", "2024-2025"}
    # 3 picks × 5 confidence buckets × 2 unseen seasons.
    assert len(evaluations) == 30
    active = evaluations[evaluations["test_matches"] > 0]
    assert set(zip(active["market_pick"], active["confidence_bucket"])) == {
        ("H", "60–70%"), ("A", "40–50%")
    }


def test_training_fields_use_only_prior_seasons():
    evaluations = walk_forward(sample_frame())
    row = evaluations[
        (evaluations["test_season"] == "2023-2024")
        & (evaluations["market_pick"] == "H")
        & (evaluations["confidence_bucket"] == "60–70%")
    ].iloc[0]
    assert row["prior_seasons"] == 3
    assert row["training_matches"] == 60
    # First three seasons have 14/20 wins at 1.60: +2.4 units each season.
    assert math.isclose(row["training_profit"], 7.2)
    assert math.isclose(row["training_positive_season_share"], 1.0)
    # Test season is deliberately weaker and must not affect training metrics.
    assert row["test_matches"] == 20
    assert math.isclose(row["test_profit"], -4.0)


def test_summary_aggregates_only_unseen_test_results_per_candidate():
    evaluations = walk_forward(sample_frame())
    summary = summary_table(evaluations)
    home = summary[
        (summary["league"] == "EPL")
        & (summary["market_pick"] == "H")
        & (summary["confidence_bucket"] == "60–70%")
    ].iloc[0]
    away = summary[
        (summary["league"] == "EPL")
        & (summary["market_pick"] == "A")
        & (summary["confidence_bucket"] == "40–50%")
    ].iloc[0]
    assert home["matches"] == 40
    assert math.isclose(home["profit"], -8.0)
    assert math.isclose(home["roi"], -0.20)
    assert away["matches"] == 40
    # 12/20 wins at 2.20 => +6.4 units per test season.
    assert math.isclose(away["profit"], 12.8)
    assert math.isclose(away["roi"], 0.32)


def test_empty_candidates_remain_visible_with_zero_matches():
    summary = summary_table(walk_forward(sample_frame()))
    draw = summary[
        (summary["league"] == "EPL")
        & (summary["market_pick"] == "D")
        & (summary["confidence_bucket"] == "≥70%")
    ].iloc[0]
    assert draw["test_seasons"] == 2
    assert draw["matches"] == 0
    assert math.isnan(draw["roi"])
