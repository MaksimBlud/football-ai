import math

import pandas as pd
import pytest

from market_model_incremental_audit import audit, paired_scores


def sample_frame():
    return pd.DataFrame([
        {"actual_result":"H","market_h_prob":0.60,"market_d_prob":0.25,"market_a_prob":0.15,"model_h_prob":0.75,"model_d_prob":0.15,"model_a_prob":0.10},
        {"actual_result":"A","market_h_prob":0.50,"market_d_prob":0.25,"market_a_prob":0.25,"model_h_prob":0.30,"model_d_prob":0.20,"model_a_prob":0.50},
        {"actual_result":"D","market_h_prob":0.45,"market_d_prob":0.30,"market_a_prob":0.25,"model_h_prob":0.30,"model_d_prob":0.50,"model_a_prob":0.20},
    ])


def test_better_model_has_negative_paired_score_deltas():
    scored = paired_scores(sample_frame())
    assert scored["brier_delta_model_minus_market"].mean() < 0
    assert scored["logloss_delta_model_minus_market"].mean() < 0


def test_audit_reports_paired_market_and_model_scores():
    result = audit(sample_frame(), simulations=1000, seed=7)
    assert result["matches"] == 3
    assert result["model_brier"] < result["market_brier"]
    assert result["model_logloss"] < result["market_logloss"]
    assert result["brier_delta_model_minus_market"]["mean"] < 0
    assert result["logloss_delta_model_minus_market"]["mean"] < 0


def test_invalid_probability_rows_are_rejected():
    frame = sample_frame()
    frame.loc[0, "model_h_prob"] = 0.90
    with pytest.raises(ValueError, match="sum to 1"):
        paired_scores(frame)


def test_invalid_actual_result_is_rejected():
    frame = sample_frame()
    frame.loc[0, "actual_result"] = "X"
    with pytest.raises(ValueError, match="H, D, or A"):
        paired_scores(frame)
