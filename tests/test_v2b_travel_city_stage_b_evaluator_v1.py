from __future__ import annotations

import pandas as pd
import pytest

import v2b_travel_city_stage_b_evaluator_v1 as mod


LEAGUE_SIZES = [
    ("EPL", 9),
    ("LA_LIGA", 9),
    ("SERIE_A", 9),
    ("BUNDESLIGA", 8),
    ("LIGUE_1", 8),
]


def _feature_payload():
    rows = []
    fixture = 0
    calls = ["UP"] * 21 + ["DOWN"] * 21 + ["NO_CALL"]
    call_index = 0

    for league, size in LEAGUE_SIZES:
        for _ in range(size):
            call = calls[call_index]
            call_index += 1
            fixture += 1
            score = 1.0 if call == "UP" else -1.0 if call == "DOWN" else 0.0
            rows.append(
                {
                    "fixture_id": str(fixture),
                    "league": league,
                    "home_team": f"H{fixture}",
                    "away_team": f"A{fixture}",
                    "joint_travel_city_km": 600.0 - score,
                    "stage_b_score": score,
                    "stage_b_call": call,
                }
            )

    assert fixture == 43
    return {
        "experiment_id": mod.FEATURE_EXPERIMENT_ID,
        "research_only": True,
        "feature_freeze_only": True,
        "primary_mapping_id": mod.PRIMARY_MAPPING_ID,
        "eligible_fixture_sha256": mod.EXPECTED_FEATURE_COHORT_SHA256,
        "frozen_feature_sha256": mod.EXPECTED_FEATURE_SHA256,
        "locked_fixture_count": 43,
        "stage_b_calls": {"UP": 21, "DOWN": 21, "NO_CALL": 1},
        "market_rows_read": False,
        "v2b_odds_read": False,
        "opening_lambda_read": False,
        "fair_centre_read": False,
        "centre_delta_read": False,
        "direction_test_performed": False,
        "match_outcome_target_used": False,
        "threshold_fitted_to_outcomes": False,
        "rest_feature_used": False,
        "travel_rest_interaction_used": False,
        "league_specific_threshold_used": False,
        "rows": rows,
    }


def _market(feature, *, no_call_delta=0.0):
    rows = []
    for row in feature["rows"]:
        call = row["stage_b_call"]
        if call == "UP":
            delta = 0.2
        elif call == "DOWN":
            delta = -0.2
        else:
            delta = no_call_delta
        rows.append(
            {
                "fixture_id": row["fixture_id"],
                "league": row["league"],
                "home_team": row["home_team"],
                "away_team": row["away_team"],
                "centre_delta": delta,
                "movement_magnitude": abs(delta),
            }
        )
    return pd.DataFrame(rows)


def test_feature_contract_preserves_21_21_1():
    frame = mod._validate_feature_freeze(_feature_payload())
    assert len(frame) == 43
    assert (frame.stage_b_call == "UP").sum() == 21
    assert (frame.stage_b_call == "DOWN").sum() == 21
    assert (frame.stage_b_call == "NO_CALL").sum() == 1


def test_perfect_called_rows_are_promising_and_no_call_excluded():
    feature = _feature_payload()
    _, report = mod.evaluate(feature, _market(feature))

    assert report["evaluated_rows"] == 43
    assert report["comparable_rows"] == 42
    assert report["concordant_rows"] == 42
    assert report["pooled_concordance"] == pytest.approx(1.0)
    assert report["zero_observed_movement_rows"] == 1
    assert report["balanced_direction_accuracy"]["recall_up"] == pytest.approx(1.0)
    assert report["balanced_direction_accuracy"]["recall_down"] == pytest.approx(1.0)
    assert report["classification"] == "PROMISING_DIRECTION_HYPOTHESIS"


def test_no_call_move_remains_non_comparable():
    feature = _feature_payload()
    _, report = mod.evaluate(
        feature,
        _market(feature, no_call_delta=0.3),
    )
    assert report["comparable_rows"] == 42
    assert report["confusion"]["NO_CALL"]["UP"] == 1
    assert report["predicted_call_counts"] == {
        "UP": 21,
        "DOWN": 21,
        "NO_CALL": 1,
    }


def test_constant_direction_baseline_uses_same_comparable_subset():
    feature = _feature_payload()
    market = _market(feature)

    # Flip six frozen UP calls to observed DOWN.
    market.loc[
        market.fixture_id.isin(["1", "2", "3", "4", "5", "6"]),
        "centre_delta",
    ] = -0.2

    _, report = mod.evaluate(feature, market)

    # Comparable observations: 15 UP and 27 DOWN => constant DOWN 27/42.
    assert report["constant_direction_baseline"]["direction"] == "DOWN"
    assert report["constant_direction_baseline"]["concordance"] == pytest.approx(27 / 42)
    assert report["pooled_concordance"] == pytest.approx(36 / 42)


def test_safety_flag_change_fails_closed():
    payload = _feature_payload()
    payload["travel_rest_interaction_used"] = True
    with pytest.raises(RuntimeError, match="safety flag"):
        mod._validate_feature_freeze(payload)


def test_identity_mismatch_fails_closed():
    feature = _feature_payload()
    market = _market(feature)
    market.loc[market.fixture_id == "1", "home_team"] = "WRONG"
    with pytest.raises(RuntimeError, match="identity mismatch"):
        mod.evaluate(feature, market)
