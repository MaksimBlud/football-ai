from __future__ import annotations

import pytest

import v2b_travel_city_stage_b_freeze_v1 as mod


def _source_payload():
    rows = []
    for index in range(43):
        fixture_id = f"F{index:02d}"
        joint = mod.EXPECTED_BASELINE + (index - 21) * 10.0
        home_km = max(0.0, joint * 0.4)
        away_km = joint - home_km
        league = (
            "EPL"
            if index < 9
            else "LA_LIGA"
            if index < 18
            else "SERIE_A"
            if index < 27
            else "BUNDESLIGA"
            if index < 35
            else "LIGUE_1"
        )
        home_team = f"Home {index}"
        away_team = f"Away {index}"
        rows.extend(
            [
                {
                    "fixture_id": fixture_id,
                    "league": league,
                    "side": "home",
                    "team": home_team,
                    "current_venue_host": home_team,
                    "travel_city_km_since_previous_match": home_km,
                },
                {
                    "fixture_id": fixture_id,
                    "league": league,
                    "side": "away",
                    "team": away_team,
                    "current_venue_host": home_team,
                    "travel_city_km_since_previous_match": away_km,
                },
            ]
        )

    return {
        "experiment_id": mod.SOURCE_EXPERIMENT_ID,
        "status": mod.EXPECTED_SOURCE_STATUS,
        "research_only": True,
        "source_feasibility_audit": True,
        "locked_fixture_count": 43,
        "team_side_count": 86,
        "travel_distance_resolved_team_sides": 86,
        "geographic_precision": "CLUB_HOME_CITY_CENTROID_PROXY",
        "market_rows_read": False,
        "v2b_odds_read": False,
        "opening_lambda_read": False,
        "fair_centre_read": False,
        "centre_delta_read": False,
        "direction_test_performed": False,
        "match_outcome_target_used": False,
        "threshold_fitted_to_outcomes": False,
        "rows": rows,
    }


def test_source_contract_accepts_exact_complete_feature_only_payload():
    rows = mod._validate_source(_source_payload())
    assert len(rows) == 86


def test_source_safety_change_fails_closed():
    payload = _source_payload()
    payload["centre_delta_read"] = True
    with pytest.raises(RuntimeError, match="safety flag"):
        mod._validate_source(payload)


def test_fixture_rows_require_one_home_and_one_away():
    payload = _source_payload()
    rows = payload["rows"][:-1]
    with pytest.raises(RuntimeError, match="missing home/away"):
        mod._fixture_rows(rows)


def test_fixture_rows_require_home_team_to_match_current_host():
    payload = _source_payload()
    payload["rows"][0]["team"] = "Wrong Home"
    with pytest.raises(RuntimeError, match="home row team"):
        mod._fixture_rows(payload["rows"])


def test_freeze_has_balanced_21_21_1_calls():
    report = mod.freeze(_source_payload())

    assert report["primary_mapping_id"] == (
        "JOINT_TRAVEL_CITY_COHORT_MEDIAN_SIGN_V1"
    )
    assert report["cohort_median_joint_travel_city_km"] == pytest.approx(
        mod.EXPECTED_BASELINE
    )
    assert report["stage_b_calls"] == {
        "UP": 21,
        "DOWN": 21,
        "NO_CALL": 1,
    }
    assert report["market_rows_read"] is False
    assert report["centre_delta_read"] is False
    assert report["direction_test_performed"] is False
    assert report["rest_feature_used"] is False
    assert report["travel_rest_interaction_used"] is False


def test_mapping_orientation_low_travel_up_high_travel_down():
    report = mod.freeze(_source_payload())
    by_id = {
        row["fixture_id"]: row
        for row in report["rows"]
    }

    assert by_id["F00"]["stage_b_call"] == "UP"
    assert by_id["F21"]["stage_b_call"] == "NO_CALL"
    assert by_id["F42"]["stage_b_call"] == "DOWN"
    assert by_id["F00"]["stage_b_score"] > 0
    assert by_id["F42"]["stage_b_score"] < 0


def test_scope_is_exact_frozen_v2b_cohort():
    assert mod.EXPECTED_FIXTURES == 43
    assert mod.EXPECTED_TEAM_SIDES == 86
    assert mod.EXPECTED_SOURCE_ARTIFACT_ID == "11044402420"
    assert mod.EXPECTED_CALLS == {
        "UP": 21,
        "DOWN": 21,
        "NO_CALL": 1,
    }
