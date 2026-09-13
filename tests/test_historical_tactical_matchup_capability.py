import pandas as pd

from historical_tactical_matchup_capability import source_capability


def test_standard_match_stats_are_not_relabelled_as_tactical_matchup():
    frame = pd.DataFrame(
        [{"HS": 10, "AS": 7, "HST": 4, "AST": 2, "HC": 6, "AC": 3, "HF": 9, "AF": 11}]
    )
    capability = source_capability(frame)
    assert capability["explicit_tactical_schema_detected"] is False
    assert capability["status"] == "TEAM_STATS_ONLY_NOT_TACTICAL_MATCHUP"
    assert capability["experiment_ready"] is False


def test_single_tactical_dimension_is_insufficient():
    frame = pd.DataFrame([{"HomeFormation": "4-3-3", "AwayFormation": "4-4-2"}])
    capability = source_capability(frame)
    assert capability["formation_columns"] == ("HomeFormation", "AwayFormation")
    assert capability["explicit_tactical_schema_detected"] is False
    assert capability["status"] == "PARTIAL_TACTICAL_SCHEMA_INSUFFICIENT"
    assert capability["experiment_ready"] is False


def test_formation_plus_dynamic_tactical_field_still_requires_temporal_provenance():
    frame = pd.DataFrame(
        [{
            "HomeFormation": "4-3-3",
            "AwayFormation": "4-4-2",
            "HomePossession": 58.0,
            "AwayPossession": 42.0,
        }]
    )
    capability = source_capability(frame)
    assert capability["explicit_tactical_schema_detected"] is True
    assert capability["status"] == "TACTICAL_SCHEMA_DETECTED_TEMPORAL_PROVENANCE_REQUIRED"
    assert capability["experiment_ready"] is False


def test_empty_schema_fails_closed():
    capability = source_capability(pd.DataFrame([{"HomeTeam": "A", "AwayTeam": "B"}]))
    assert capability["status"] == "DATA_GAP"
    assert capability["experiment_ready"] is False
