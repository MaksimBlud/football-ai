import math

import pandas as pd

from historical_strategy_lab import (
    CONFIDENCE_BUCKETS,
    evaluate,
    no_vig_probabilities,
    prepare_market_frame,
    segment_table,
)


def sample_frame():
    return pd.DataFrame(
        [
            {"league": "EPL", "season": "2024-2025", "result": "H", "market_home_odds": 1.50, "market_draw_odds": 4.00, "market_away_odds": 7.00},
            {"league": "EPL", "season": "2024-2025", "result": "D", "market_home_odds": 2.00, "market_draw_odds": 3.50, "market_away_odds": 4.00},
            {"league": "LA_LIGA", "season": "2024-2025", "result": "A", "market_home_odds": 4.00, "market_draw_odds": 3.50, "market_away_odds": 2.00},
        ]
    )


def test_no_vig_probabilities_sum_to_one():
    probabilities = no_vig_probabilities(2.0, 3.5, 4.0)
    assert math.isclose(sum(probabilities.values()), 1.0, rel_tol=1e-12)
    assert probabilities["H"] > probabilities["D"] > probabilities["A"]


def test_prepare_market_frame_uses_only_pre_match_market_and_flat_stake_profit():
    prepared = prepare_market_frame(sample_frame())
    assert list(prepared["market_pick"]) == ["H", "H", "A"]
    assert list(prepared["won"]) == [True, False, True]
    assert list(prepared["profit"]) == [0.5, -1.0, 1.0]


def test_evaluate_reports_probability_and_betting_metrics():
    metrics = evaluate(sample_frame())
    assert metrics.matches == 3
    assert metrics.wins == 2
    assert math.isclose(metrics.accuracy, 2 / 3)
    assert math.isclose(metrics.profit, 0.5)
    assert math.isclose(metrics.roi, 1 / 6)
    assert metrics.brier is not None and metrics.brier > 0
    assert metrics.log_loss is not None and metrics.log_loss > 0
    assert metrics.max_drawdown >= 0


def test_confidence_segments_preserve_all_rows():
    prepared = prepare_market_frame(sample_frame())
    table = segment_table(prepared, CONFIDENCE_BUCKETS, "market_confidence")
    assert int(table["matches"].sum()) == len(prepared)


def test_invalid_odds_are_excluded():
    frame = sample_frame()
    frame.loc[0, "market_home_odds"] = 1.0
    prepared = prepare_market_frame(frame)
    assert len(prepared) == 2
