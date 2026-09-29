from __future__ import annotations

import math

import pandas as pd
import pytest

import v2b_travel_venue_feasibility_v1 as mod


def test_nonleague_latest_host_uses_frozen_fixture_orientation():
    load = {
        "full_previous_match_date": "2026-09-16",
        "league_previous_match_date": "2026-09-13",
        "nonleague_events_14d": [
            {
                "date": "2026-09-16",
                "fixture_label": "Manchester United vs Brighton & Hove Albion",
            }
        ],
    }
    assert mod._nonleague_latest_host(load) == "Manchester United"


def test_nonleague_latest_host_is_none_when_league_is_latest():
    load = {
        "full_previous_match_date": "2026-09-13",
        "league_previous_match_date": "2026-09-13",
        "nonleague_events_14d": [],
    }
    assert mod._nonleague_latest_host(load) is None


def test_understat_schedule_parses_home_and_away():
    payload = {
        "dates": [
            {
                "datetime": "2026-09-12 15:00:00",
                "isResult": True,
                "h": {"title": "Arsenal"},
                "a": {"title": "Everton"},
            }
        ]
    }
    rows = mod._understat_schedule(payload)
    assert rows == [
        {
            "match_date": pd.Timestamp("2026-09-12"),
            "home": "Arsenal",
            "away": "Everton",
            "is_result": True,
        }
    ]


def test_league_latest_host_resolves_target_alias():
    schedules = {
        "EPL": [
            {
                "match_date": pd.Timestamp("2026-09-12"),
                "home": "Manchester City",
                "away": "Everton",
                "is_result": True,
            }
        ]
    }
    resolved, host = mod._league_latest_host(
        league="EPL",
        target_name="Man City",
        previous_date="2026-09-12",
        schedules=schedules,
    )
    assert resolved == "Manchester City"
    assert host == "Manchester City"


def test_haversine_zero_for_same_venue():
    assert mod.haversine_km(51.5, -0.1, 51.5, -0.1) == pytest.approx(0.0)


def test_haversine_is_symmetric_and_positive():
    london_to_madrid = mod.haversine_km(51.5074, -0.1278, 40.4168, -3.7038)
    madrid_to_london = mod.haversine_km(40.4168, -3.7038, 51.5074, -0.1278)
    assert london_to_madrid > 1000
    assert london_to_madrid == pytest.approx(madrid_to_london)


def test_current_home_venue_prefers_nonended_statement():
    resolver = mod.WikidataResolver.__new__(mod.WikidataResolver)
    entity = {
        "claims": {
            "P115": [
                {
                    "rank": "normal",
                    "mainsnak": {
                        "datavalue": {
                            "value": {"id": "QOLD"}
                        }
                    },
                    "qualifiers": {
                        "P582": [
                            {
                                "datavalue": {
                                    "value": {
                                        "time": "+2020-01-01T00:00:00Z"
                                    }
                                }
                            }
                        ]
                    },
                },
                {
                    "rank": "preferred",
                    "mainsnak": {
                        "datavalue": {
                            "value": {"id": "QNEW"}
                        }
                    },
                    "qualifiers": {
                        "P580": [
                            {
                                "datavalue": {
                                    "value": {
                                        "time": "+2021-01-01T00:00:00Z"
                                    }
                                }
                            }
                        ]
                    },
                },
            ]
        }
    }
    assert resolver._current_home_venue_qid(entity) == "QNEW"


def test_coordinate_parser_accepts_wikidata_p625():
    entity = {
        "claims": {
            "P625": [
                {
                    "rank": "preferred",
                    "mainsnak": {
                        "datavalue": {
                            "value": {
                                "latitude": 51.555,
                                "longitude": -0.108611,
                            }
                        }
                    },
                }
            ]
        }
    }
    assert mod.WikidataResolver._coordinate(entity) == (51.555, -0.108611)


def test_scope_is_exact_43_fixture_source_audit():
    assert mod.EXPECTED_FIXTURES == 43
    assert mod.EXPECTED_TEAM_SIDES == 86
    assert mod.SEASON == 2026
    assert mod.EXPERIMENT_ID == "V2B_TRAVEL_VENUE_FEASIBILITY_V1"
