from __future__ import annotations

import pandas as pd
import pytest

import v2b_deep_stage_b_freeze_v1 as mod


def _feasibility():
    rows=[]
    plan={"EPL":(6,3),"LA_LIGA":(9,0),"SERIE_A":(7,2),"BUNDESLIGA":(6,2),"LIGUE_1":(6,2)}
    fixture=0
    for league,(yes,no) in plan.items():
        for _ in range(yes):
            fixture+=1
            rows.append({
                "fixture_id":str(fixture),"league":league,
                "kickoff_utc":"2026-09-19T12:00:00+00:00",
                "home_team":f"H{fixture}","away_team":f"A{fixture}",
                "identity_status":"MATCHED","both_teams_have_tactical5":True,
                "home_deep_last5":7.0,"home_deep_allowed_last5":5.0,
                "away_deep_last5":6.0,"away_deep_allowed_last5":4.0,
            })
        for _ in range(no):
            fixture+=1
            rows.append({
                "fixture_id":str(fixture),"league":league,
                "kickoff_utc":"2026-09-19T12:00:00+00:00",
                "home_team":f"H{fixture}","away_team":f"A{fixture}",
                "identity_status":"MATCHED","both_teams_have_tactical5":False,
                "home_deep_last5":None,"home_deep_allowed_last5":None,
                "away_deep_last5":None,"away_deep_allowed_last5":None,
            })
    return {
        "experiment_id":mod.FEASIBILITY_EXPERIMENT_ID,
        "status":"PARTIAL_TACTICAL5_FEASIBLE",
        "research_only":True,
        "locked_fixture_count":43,
        "identity_matched_fixture_count":43,
        "tactical5_feasible_fixture_count":34,
        "market_rows_read":False,"v2b_odds_read":False,
        "opening_lambda_read":False,"fair_centre_read":False,
        "centre_delta_read":False,"direction_test_performed":False,
        "rows":rows,
    }


def _baseline(value=10.0):
    return {
        "source":"UNDERSTAT_PUBLIC_LEAGUE_HISTORY",
        "season_start":2025,
        "definition":"test",
        "pooled_team_match_rows":100,
        "pooled_total_deep_environment":value,
        "by_league":{},
    }


def test_exact_34_fixture_cohort():
    frame=mod._validate_feasibility(_feasibility())
    assert len(frame)==34
    assert {league:int((frame.league==league).sum()) for league in mod.EXPECTED_BY_LEAGUE}==mod.EXPECTED_BY_LEAGUE


def test_deep_mapping_crosses_attack_and_opponent_allowed():
    row=pd.Series({
        "home_deep_last5":8.0,"home_deep_allowed_last5":4.0,
        "away_deep_last5":6.0,"away_deep_allowed_last5":10.0,
    })
    r=mod.stage_b_components(row,12.0)
    assert r["expected_home_deep"]==pytest.approx(9.0)
    assert r["expected_away_deep"]==pytest.approx(5.0)
    assert r["joint_expected_deep"]==pytest.approx(14.0)
    assert r["stage_b_score"]==pytest.approx(2.0)
    assert r["stage_b_call"]=="UP"


def test_down_and_no_call_are_deterministic():
    row=pd.Series({
        "home_deep_last5":4.0,"home_deep_allowed_last5":4.0,
        "away_deep_last5":4.0,"away_deep_allowed_last5":4.0,
    })
    assert mod.stage_b_components(row,9.0)["stage_b_call"]=="DOWN"
    assert mod.stage_b_components(row,8.0)["stage_b_call"]=="NO_CALL"


def test_freeze_does_not_use_ppda_or_market_target():
    r=mod.freeze(_feasibility(),_baseline(10.0))
    assert r["eligible_fixture_count"]==34
    assert r["ppda_used_in_primary_mapping"] is False
    assert r["market_rows_read"] is False
    assert r["centre_delta_read"] is False
    forbidden={"ppda","ppda_allowed","centre_delta","opening_lambda","observed_direction"}
    assert not any(forbidden & set(row) for row in r["rows"])


def test_bad_baseline_fails_closed():
    with pytest.raises(RuntimeError,match="invalid pooled"):
        mod.freeze(_feasibility(),_baseline(0.0))
