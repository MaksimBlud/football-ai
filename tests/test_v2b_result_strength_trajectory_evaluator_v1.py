from __future__ import annotations

import pandas as pd
import pytest

import v2b_result_strength_trajectory_evaluator_v1 as mod


def _feature_payload():
    rows=[]
    calls=["UP"]*16+["DOWN"]*18
    leagues=["EPL"]*6+["LA_LIGA"]*9+["SERIE_A"]*7+["BUNDESLIGA"]*6+["LIGUE_1"]*6
    for i,(call,league) in enumerate(zip(calls,leagues),start=1):
        rows.append({
            "fixture_id":str(i),
            "league":league,
            "kickoff_utc":"2026-09-19T12:00:00+00:00",
            "home_team":f"H{i}",
            "away_team":f"A{i}",
            "stage_b_score":1.0 if call=="UP" else -1.0,
            "stage_b_call":call,
            "home_performance_residual_5":0.5 if call=="UP" else -0.5,
            "away_performance_residual_5":0.5 if call=="UP" else -0.5,
        })
    return {
        "experiment_id":mod.FEATURE_EXPERIMENT_ID,
        "research_only":True,
        "feature_freeze_only":True,
        "primary_mapping_id":mod.PRIMARY_MAPPING_ID,
        "eligible_fixture_sha256":mod.EXPECTED_FEATURE_COHORT_SHA256,
        "eligible_fixture_count":34,
        "stage_b_calls":{"UP":16,"DOWN":18,"NO_CALL":0},
        "direction_test_performed":False,
        "v2b_odds_read":False,
        "opening_lambda_read":False,
        "centre_delta_read":False,
        "rows":rows,
    }


def _market_rows(feature, *, concordant=True):
    rows=[]
    for row in feature["rows"]:
        call=row["stage_b_call"]
        if concordant:
            delta=0.2 if call=="UP" else -0.2
        else:
            delta=-0.2 if call=="UP" else 0.2
        rows.append({
            "fixture_id":row["fixture_id"],
            "league":row["league"],
            "kickoff_utc":row["kickoff_utc"],
            "home_team":row["home_team"],
            "away_team":row["away_team"],
            "centre_delta":delta,
            "movement_magnitude":abs(delta),
        })
    extras=[]
    for i in range(35,44):
        extras.append({
            "fixture_id":str(i),
            "league":"EPL",
            "kickoff_utc":"2026-09-20T12:00:00+00:00",
            "home_team":f"H{i}",
            "away_team":f"A{i}",
            "centre_delta":0.0,
            "movement_magnitude":0.0,
        })
    return pd.DataFrame(rows+extras)


def test_feature_freeze_contract_is_exact():
    frame=mod._validate_feature_freeze(_feature_payload())
    assert len(frame)==34
    assert (frame.stage_b_call=="UP").sum()==16
    assert (frame.stage_b_call=="DOWN").sum()==18


def test_perfect_consistency_is_promising():
    feature=_feature_payload()
    rows,report=mod.evaluate(feature,_market_rows(feature,concordant=True))
    assert len(rows)==34
    assert report["comparable_rows"]==34
    assert report["concordant_rows"]==34
    assert report["pooled_concordance"]==pytest.approx(1.0)
    assert report["call_group_mean_deltas_aligned"] is True
    assert report["classification"]=="PROMISING_DIRECTION_HYPOTHESIS"


def test_reversed_direction_is_not_promising():
    feature=_feature_payload()
    _,report=mod.evaluate(feature,_market_rows(feature,concordant=False))
    assert report["pooled_concordance"]==pytest.approx(0.0)
    assert report["classification"]=="WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS"


def test_zero_market_rows_are_not_direction_comparable():
    feature=_feature_payload()
    market=_market_rows(feature,concordant=True)
    market.loc[market.fixture_id.isin(["1","17"]),["centre_delta","movement_magnitude"]]=0.0
    _,report=mod.evaluate(feature,market)
    assert report["zero_observed_movement_rows"]==2
    assert report["comparable_rows"]==32
    assert report["concordant_rows"]==32


def test_market_identity_mismatch_fails_closed():
    feature=_feature_payload()
    market=_market_rows(feature)
    market.loc[market.fixture_id=="1","home_team"]="WRONG"
    with pytest.raises(RuntimeError,match="identity mismatch"):
        mod.evaluate(feature,market)


def test_missing_frozen_fixture_fails_closed():
    feature=_feature_payload()
    market=_market_rows(feature)
    market=market[market.fixture_id!="1"]
    with pytest.raises(RuntimeError):
        mod.evaluate(feature,market)
