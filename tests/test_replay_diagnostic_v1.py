import math

import pytest

import replay_diagnostic_v1 as replay


def test_frozen_inventory_and_eligibility_are_fail_closed():
    replay.validate_preregistered_contract()
    assert sum(replay.CURRENT_ROUND_EVENT_COUNTS.values()) == 57
    assert sum(v["replay_eligible_events"] for v in replay.ELIGIBILITY.values()) == 0
    assert replay.ELIGIBILITY["EPL"]["prospective_ai_events"] == 10
    assert all(
        replay.ELIGIBILITY[league]["prospective_ai_events"] == 0
        for league in replay.SCOPE_LEAGUES
        if league != "EPL"
    )


def test_inventory_hash_is_sha256_shape():
    assert len(replay.INVENTORY_SHA256) == 64
    int(replay.INVENTORY_SHA256, 16)


def test_pooled_metrics_use_ai_minus_market_deltas():
    rows = [
        {"outcome": 0, "ai_probs": [0.7, 0.2, 0.1], "market_probs": [0.5, 0.3, 0.2]},
        {"outcome": 2, "ai_probs": [0.1, 0.2, 0.7], "market_probs": [0.3, 0.3, 0.4]},
    ]
    result = replay.evaluate_pooled(rows)
    assert result.n == 2
    assert result.delta_brier == pytest.approx(result.ai_brier - result.market_brier)
    assert result.delta_logloss == pytest.approx(result.ai_logloss - result.market_logloss)
    assert result.delta_brier < 0
    assert result.delta_logloss < 0
    assert result.status == "EARLY_SIGNAL"


def test_warning_when_ai_is_worse_on_both_proper_scores():
    rows = [
        {"outcome": 0, "ai_probs": [0.2, 0.4, 0.4], "market_probs": [0.7, 0.2, 0.1]},
        {"outcome": 2, "ai_probs": [0.5, 0.3, 0.2], "market_probs": [0.1, 0.2, 0.7]},
    ]
    assert replay.evaluate_pooled(rows).status == "WARNING"


def test_rejects_invalid_probability_vectors_and_empty_sample():
    with pytest.raises(ValueError):
        replay.evaluate_pooled([])
    with pytest.raises(ValueError):
        replay.evaluate_pooled([
            {"outcome": 0, "ai_probs": [0.8, 0.8, -0.6], "market_probs": [0.5, 0.3, 0.2]}
        ])


def test_logloss_is_finite_for_zero_probability_after_clipping():
    result = replay.evaluate_pooled([
        {"outcome": 0, "ai_probs": [0.0, 0.5, 0.5], "market_probs": [0.5, 0.25, 0.25]}
    ])
    assert math.isfinite(result.ai_logloss)
