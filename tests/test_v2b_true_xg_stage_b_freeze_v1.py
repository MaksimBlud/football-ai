from __future__ import annotations

import pandas as pd
import pytest

import v2b_true_xg_stage_b_freeze_v1 as mod


def _feasibility():
    rows=[]
    plan={
        "EPL":(6,3),
        "LA_LIGA":(9,0),
        "SERIE_A":(7,2),
        "BUNDESLIGA":(6,2),
        "LIGUE_1":(6,2),
    }
    fixture=0
    for league,(yes,no) in plan.items():
        for _ in range(yes):
            fixture+=1
            rows.append({
                "fixture_id":str(fixture),
                "league":league,
                "kickoff_utc":"2026-09-19T12:00:00+00:00",
                "home_team":f"H{fixture}",
                "away_team":f"A{fixture}",
                "understat_home_team":f"H{fixture}",
                "understat_away_team":f"A{fixture}",
                "identity_status":"MATCHED",
                "both_teams_have_xg5":True,
                "home_npxg_last5":1.4,
                "home_npxga_last5":1.1,
                "away_npxg_last5":1.3,
                "away_npxga_last5":1.2,
            })
        for _ in range(no):
            fixture+=1
            rows.append({
                "fixture_id":str(fixture),
                "league":league,
                "kickoff_utc":"2026-09-19T12:00:00+00:00",
                "home_team":f"H{fixture}",
                "away_team":f"A{fixture}",
                "understat_home_team":f"H{fixture}",
                "understat_away_team":f"A{fixture}",
                "identity_status":"MATCHED",
                "both_teams_have_xg5":False,
                "home_npxg_last5":None,
                "home_npxga_last5":None,
                "away_npxg_last5":None,
                "away_npxga_last5":None,
            })
    return {
        "experiment_id":mod.FEASIBILITY_EXPERIMENT_ID,
        "status":"PARTIAL_XG5_FEASIBLE",
        "research_only":True,
        "source_feasibility_audit":True,
        "locked_fixture_count":43,
        "identity_matched_fixture_count":43,
        "xg5_feasible_fixture_count":34,
        "market_rows_read":False,
        "v2b_odds_read":False,
        "centre_delta_read":False,
        "direction_test_performed":False,
        "rows":rows,
    }


def _baseline(value=2.5):
    return {
        "source":"UNDERSTAT_PUBLIC_LEAGUE_HISTORY",
        "season_start":2025,
        "definition":"test",
        "pooled_team_match_rows":100,
        "pooled_total_npxg_environment":value,
        "by_league":{},
    }


def test_exact_34_fixture_cohort_is_frozen():
    eligible=mod._validate_feasibility(_feasibility())
    assert len(eligible)==34
    assert {
        league:int((eligible.league==league).sum())
        for league in mod.EXPECTED_BY_LEAGUE
    }==mod.EXPECTED_BY_LEAGUE


def test_mapping_uses_cross_attack_defence_and_single_baseline():
    row=pd.Series({
        "home_npxg_last5":1.6,
        "home_npxga_last5":1.0,
        "away_npxg_last5":1.4,
        "away_npxga_last5":1.2,
    })
    r=mod.stage_b_components(row,2.4)
    assert r["expected_home_npxg"]==pytest.approx(1.4)
    assert r["expected_away_npxg"]==pytest.approx(1.2)
    assert r["joint_expected_npxg"]==pytest.approx(2.6)
    assert r["stage_b_score"]==pytest.approx(0.2)
    assert r["stage_b_call"]=="UP"


def test_mapping_down_and_no_call_are_deterministic():
    row=pd.Series({
        "home_npxg_last5":1.0,
        "home_npxga_last5":1.0,
        "away_npxg_last5":1.0,
        "away_npxga_last5":1.0,
    })
    assert mod.stage_b_components(row,2.2)["stage_b_call"]=="DOWN"
    assert mod.stage_b_components(row,2.0)["stage_b_call"]=="NO_CALL"


def test_freeze_has_no_market_direction_inputs():
    r=mod.freeze(_feasibility(),_baseline(2.5))
    assert r["eligible_fixture_count"]==34
    assert r["market_rows_read"] is False
    assert r["v2b_odds_read"] is False
    assert r["opening_lambda_read"] is False
    assert r["fair_centre_read"] is False
    assert r["centre_delta_read"] is False
    assert r["direction_test_performed"] is False
    forbidden={"opening_lambda","fair_centre","centre_delta","observed_direction"}
    assert not any(forbidden & set(row) for row in r["rows"])


def test_invalid_baseline_fails_closed():
    with pytest.raises(RuntimeError,match="invalid pooled"):
        mod.freeze(_feasibility(),_baseline(0.0))
