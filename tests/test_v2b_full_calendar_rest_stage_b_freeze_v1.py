from __future__ import annotations

import copy

import pytest

import v2b_full_calendar_rest_stage_b_freeze_v1 as mod


def _payload():
    # 43 deterministic feature-only rows with joint rest distribution whose median is 11.
    joint_values = [6]*4 + [7]*6 + [8]*2 + [9]*3 + [10]*4 + [11]*7 + [12]*3 + [13]*3 + [14]*7 + [15]*3 + [16]
    assert len(joint_values) == 43
    rows=[]
    leagues=["EPL"]*9+["LA_LIGA"]*9+["SERIE_A"]*9+["BUNDESLIGA"]*8+["LIGUE_1"]*8
    for i,(joint,league) in enumerate(zip(joint_values,leagues),start=1):
        home=joint//2
        away=joint-home
        rows.append({
            "fixture_id":str(i),
            "league":league,
            "kickoff_utc":"2026-09-19T14:00:00+00:00",
            "home_team":f"H{i}",
            "away_team":f"A{i}",
            "identity_status":"MATCHED",
            "full_calendar_feasible":True,
            "home_load":{"full_rest_days":home},
            "away_load":{"full_rest_days":away},
        })
    return {
        "experiment_id":mod.FEASIBILITY_EXPERIMENT_ID,
        "status":"FULL_43_RECONSTRUCTABLE_14D",
        "research_only":True,
        "source_feasibility_audit":True,
        "lookback_days":14,
        "locked_fixture_count":43,
        "identity_matched_fixture_count":43,
        "full_calendar_feasible_fixture_count":43,
        "market_rows_read":False,
        "v2b_odds_read":False,
        "centre_delta_read":False,
        "direction_test_performed":False,
        "match_outcome_target_used":False,
        "rows":rows,
    }


def test_feature_only_median_and_call_distribution_are_frozen():
    report=mod.freeze(_payload())
    assert report["cohort_median_joint_full_rest_days"]==11.0
    assert report["stage_b_calls"]=={"UP":17,"DOWN":19,"NO_CALL":7}
    assert report["direction_test_performed"] is False
    assert report["centre_delta_read"] is False


def test_mapping_orientation_is_deterministic():
    p=_payload()
    report=mod.freeze(p)
    by_id={r["fixture_id"]:r for r in report["rows"]}
    assert by_id["1"]["joint_full_rest_days"]==6.0
    assert by_id["1"]["stage_b_call"]=="DOWN"
    assert any(r["stage_b_call"]=="NO_CALL" for r in report["rows"])
    assert by_id["43"]["joint_full_rest_days"]==16.0
    assert by_id["43"]["stage_b_call"]=="UP"


def test_market_safety_flag_change_fails_closed():
    p=_payload()
    p["centre_delta_read"]=True
    with pytest.raises(RuntimeError,match="safety flag"):
        mod.freeze(p)


def test_missing_rest_fails_closed():
    p=_payload()
    p["rows"][0]["home_load"]["full_rest_days"]=None
    with pytest.raises(RuntimeError,match="invalid"):
        mod.freeze(p)


def test_feature_distribution_change_fails_closed():
    p=_payload()
    for row in p["rows"]:
        row["home_load"]["full_rest_days"] += 10
    with pytest.raises(RuntimeError,match="median changed"):
        mod.freeze(p)
