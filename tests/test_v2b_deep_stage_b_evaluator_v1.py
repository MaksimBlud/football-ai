from __future__ import annotations

import pandas as pd
import pytest

import v2b_deep_stage_b_evaluator_v1 as mod


def _feature_payload():
    rows=[]
    calls=["UP"]*28+["DOWN"]*6
    leagues=["EPL"]*6+["LA_LIGA"]*9+["SERIE_A"]*7+["BUNDESLIGA"]*6+["LIGUE_1"]*6
    for i,(call,league) in enumerate(zip(calls,leagues),start=1):
        rows.append({
            "fixture_id":str(i),
            "league":league,
            "kickoff_utc":"2026-09-19T12:00:00+00:00",
            "home_team":f"H{i}",
            "away_team":f"A{i}",
            "joint_expected_deep":13.5,
            "stage_b_score":0.2 if call=="UP" else -0.2,
            "stage_b_call":call,
        })
    return {
        "experiment_id":mod.FEATURE_EXPERIMENT_ID,
        "research_only":True,
        "feature_freeze_only":True,
        "primary_mapping_id":mod.PRIMARY_MAPPING_ID,
        "eligible_fixture_sha256":mod.EXPECTED_FEATURE_COHORT_SHA256,
        "frozen_feature_sha256":mod.EXPECTED_FEATURE_SHA256,
        "eligible_fixture_count":34,
        "stage_b_calls":{"UP":28,"DOWN":6,"NO_CALL":0},
        "market_rows_read":False,
        "v2b_odds_read":False,
        "opening_lambda_read":False,
        "fair_centre_read":False,
        "centre_delta_read":False,
        "direction_test_performed":False,
        "rows":rows,
    }


def _market(feature, *, zeros=False):
    rows=[]
    for row in feature["rows"]:
        call=row["stage_b_call"]
        delta=0.2 if call=="UP" else -0.2
        if zeros:
            delta=0.0
        rows.append({
            "fixture_id":row["fixture_id"],
            "league":row["league"],
            "home_team":row["home_team"],
            "away_team":row["away_team"],
            "centre_delta":delta,
            "movement_magnitude":abs(delta),
        })
    for i in range(35,44):
        rows.append({
            "fixture_id":str(i),
            "league":"EPL",
            "home_team":f"H{i}",
            "away_team":f"A{i}",
            "centre_delta":0.0,
            "movement_magnitude":0.0,
        })
    return pd.DataFrame(rows)


def test_feature_contract_is_exact():
    f=mod._validate_feature_freeze(_feature_payload())
    assert len(f)==34
    assert (f.stage_b_call=="UP").sum()==28
    assert (f.stage_b_call=="DOWN").sum()==6


def test_perfect_direction_mapping_is_promising():
    feature=_feature_payload()
    _,r=mod.evaluate(feature,_market(feature))
    assert r["comparable_rows"]==34
    assert r["concordant_rows"]==34
    assert r["pooled_concordance"]==pytest.approx(1.0)
    assert r["call_group_mean_deltas_aligned"] is True
    assert r["classification"]=="PROMISING_DIRECTION_HYPOTHESIS"


def test_zero_moves_are_retained_but_not_comparable():
    feature=_feature_payload()
    _,r=mod.evaluate(feature,_market(feature,zeros=True))
    assert r["evaluated_rows"]==34
    assert r["zero_observed_movement_rows"]==34
    assert r["comparable_rows"]==0
    assert r["classification"]=="WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS"


def test_majority_baseline_and_balanced_accuracy_are_reported():
    feature=_feature_payload()
    market=_market(feature)
    # Flip three frozen-UP rows to DOWN; all six frozen-DOWN rows stay correct.
    market.loc[market.fixture_id.isin(["1","2","3"]),"centre_delta"]=-0.2
    _,r=mod.evaluate(feature,market)
    assert r["constant_direction_baseline"]["direction"]=="UP"
    assert r["constant_direction_baseline"]["concordance"]==pytest.approx(25/34)
    assert r["balanced_direction_accuracy"]["recall_up"]==pytest.approx(25/25)
    assert r["balanced_direction_accuracy"]["recall_down"]==pytest.approx(6/9)


def test_identity_mismatch_fails_closed():
    feature=_feature_payload()
    market=_market(feature)
    market.loc[market.fixture_id=="1","home_team"]="WRONG"
    with pytest.raises(RuntimeError,match="identity mismatch"):
        mod.evaluate(feature,market)
