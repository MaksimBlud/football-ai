import math

import pandas as pd

from historical_strategy_walk_forward import summary_table, walk_forward


def sample_frame():
    rows = []
    seasons = ["2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"]
    for season_index, season in enumerate(seasons):
        for i in range(60):
            # HOME 60–70% is profitable in the first three seasons and then weakens.
            won = i < (42 if season_index < 3 else 30)
            rows.append({
                "league": "EPL", "season": season, "market_pick": "H",
                "market_confidence": 0.65, "selected_odds": 1.60,
                "won": won, "profit": 0.60 if won else -1.0,
            })
        for i in range(60):
            # AWAY 40–50% is inferior in training but stronger later.
            won = i < (24 if season_index < 3 else 36)
            rows.append({
                "league": "EPL", "season": season, "market_pick": "A",
                "market_confidence": 0.45, "selected_odds": 2.20,
                "won": won, "profit": 1.20 if won else -1.0,
            })
    return pd.DataFrame(rows)


def test_walk_forward_uses_only_prior_seasons_for_selection():
    selections, bets = walk_forward(sample_frame())
    first = selections.iloc[0]
    assert first["test_season"] == "2023-2024"
    assert first["training_seasons"] == 3
    assert first["market_pick"] == "H"
    assert first["confidence_bucket"] == "60–70%"
    assert set(bets["walk_forward_test_season"].unique()) == {"2023-2024", "2024-2025"}


def test_walk_forward_summary_aggregates_only_test_results():
    selections, _ = walk_forward(sample_frame())
    summary = summary_table(selections)
    total = summary[summary["league"] == "ALL"].iloc[0]
    assert total["test_seasons"] == 2
    assert total["matches"] == 120
    assert math.isclose(total["profit"], -24.0)
    assert math.isclose(total["roi"], -0.20)


def test_walk_forward_does_not_emit_training_rows_as_bets():
    _, bets = walk_forward(sample_frame())
    assert not bets.empty
    assert set(bets["season"].unique()).isdisjoint({"2020-2021", "2021-2022", "2022-2023"})
