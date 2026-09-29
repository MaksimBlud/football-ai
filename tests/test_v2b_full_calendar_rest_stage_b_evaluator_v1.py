from __future__ import annotations

import pandas as pd
import pytest

import v2b_full_calendar_rest_stage_b_evaluator_v1 as mod


LEAGUE_CALLS = [
    ("EPL", ["UP"] + ["DOWN"] * 8),
    ("LA_LIGA", ["DOWN"] * 8 + ["NO_CALL"]),
    ("SERIE_A", ["UP"] * 4 + ["DOWN"] + ["NO_CALL"] * 4),
    ("BUNDESLIGA", ["UP"] * 6 + ["NO_CALL"] * 2),
    ("LIGUE_1", ["UP"] * 6 + ["DOWN"] * 2),
]


def _feature_payload():
    rows=[]
    fixture=0
    for league,calls in LEAGUE_CALLS:
        for call in calls:
            fixture += 1
            score = 1.0 if call=="UP" else -1.0 if call=="DOWN" else 0.0
            rows.append({
                "fixture_id":str(fixture),
                "league":league,
                "kickoff_utc":"2026-09-19T14:00:00+00:00",
                "home_team":f"H{fixture}",
                "away_team":f"A{fixture}",
                "joint_full_rest_days":11.0+score,
                "stage_b_score":score,
                "stage_b_call":call,
            })
    assert fixture==43
    return {
        "experiment_id":mod.FEATURE_EXPERIMENT_ID,
        "research_only":True,
        "feature_freeze_only":True,
        "primary_mapping_id":mod.PRIMARY_MAPPING_ID,
        "eligible_fixture_sha256":mod.EXPECTED_FEATURE_COHORT_SHA256,
        "frozen_feature_sha256":mod.EXPECTED_FEATURE_SHA256,
        "locked_fixture_count":43,
        "stage_b_calls":{"UP":17,"DOWN":19,"NO_CALL":7},
        "market_rows_read":False,
        "v2b_odds_read":False,
        "opening_lambda_read":False,
        "fair_centre_read":False,
        "centre_delta_read":False,
        "direction_test_performed":False,
        "match_outcome_target_used":False,
        "threshold_fitted_to_outcomes":False,
        "rows":rows,
    }


def _market(feature, *, no_call_delta=0.0):
    rows=[]
    for row in feature["rows"]:
        call=row["stage_b_call"]
        if call=="UP":
            delta=0.2
        elif call=="DOWN":
            delta=-0.2
        else:
            delta=no_call_delta
        rows.append({
            "fixture_id":row["fixture_id"],
            "league":row["league"],
            "home_team":row["home_team"],
            "away_team":row["away_team"],
            "centre_delta":delta,
            "movement_magnitude":abs(delta),
        })
    return pd.DataFrame(rows)


def test_feature_contract_preserves_17_19_7():
    f=mod._validate_feature_freeze(_feature_payload())
    assert len(f)==43
    assert (f.stage_b_call=="UP").sum()==17
    assert (f.stage_b_call=="DOWN").sum()==19
    assert (f.stage_b_call=="NO_CALL").sum()==7


def test_perfect_called_rows_are_promising_and_no_call_excluded():
    feature=_feature_payload()
    _,r=mod.evaluate(feature,_market(feature))
    assert r["evaluated_rows"]==43
    assert r["comparable_rows"]==36
    assert r["concordant_rows"]==36
    assert r["pooled_concordance"]==pytest.approx(1.0)
    assert r["zero_observed_movement_rows"]==7
    assert r["balanced_direction_accuracy"]["recall_up"]==pytest.approx(1.0)
    assert r["balanced_direction_accuracy"]["recall_down"]==pytest.approx(1.0)
    assert r["classification"]=="PROMISING_DIRECTION_HYPOTHESIS"


def test_no_call_market_moves_remain_non_comparable():
    feature=_feature_payload()
    _,r=mod.evaluate(feature,_market(feature,no_call_delta=0.3))
    assert r["evaluated_rows"]==43
    assert r["comparable_rows"]==36
    assert r["confusion"]["NO_CALL"]["UP"]==7
    assert r["predicted_call_counts"]=={"UP":17,"DOWN":19,"NO_CALL":7}


def test_constant_direction_baseline_uses_same_comparable_subset():
    feature=_feature_payload()
    market=_market(feature)
    # Flip four frozen UP calls to observed DOWN.
    market.loc[market.fixture_id.isin(["1","19","20","21"]),"centre_delta"]=-0.2
    _,r=mod.evaluate(feature,market)
    # Comparable observations: 13 UP and 23 DOWN => constant DOWN = 23/36.
    assert r["constant_direction_baseline"]["direction"]=="DOWN"
    assert r["constant_direction_baseline"]["concordance"]==pytest.approx(23/36)
    assert r["pooled_concordance"]==pytest.approx(32/36)
    assert r["balanced_direction_accuracy"]["recall_up"]==pytest.approx(13/13)
    assert r["balanced_direction_accuracy"]["recall_down"]==pytest.approx(19/23)


def test_safety_flag_change_fails_closed():
    p=_feature_payload()
    p["threshold_fitted_to_outcomes"]=True
    with pytest.raises(RuntimeError,match="safety flag"):
        mod._validate_feature_freeze(p)


def test_identity_mismatch_fails_closed():
    feature=_feature_payload()
    market=_market(feature)
    market.loc[market.fixture_id=="1","home_team"]="WRONG"
    with pytest.raises(RuntimeError,match="identity mismatch"):
        mod.evaluate(feature,market)
