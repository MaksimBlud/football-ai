import pandas as pd

from historical_lineup_strength_capability import source_capability


def test_football_data_team_level_schema_fails_closed_for_lineup_strength():
    frame = pd.DataFrame(
        [{"Date": "01/08/2020", "HomeTeam": "A", "AwayTeam": "B", "FTHG": 1, "FTAG": 0}]
    )
    capability = source_capability(frame)
    assert capability["lineup_pair_detected"] is False
    assert capability["lineup_strength_pair_detected"] is False
    assert capability["status"] == "DATA_GAP"
    assert capability["experiment_ready"] is False


def test_lineup_identity_is_not_mislabeled_as_strength():
    frame = pd.DataFrame(
        [{"HomeLineup": "p1,p2", "AwayLineup": "p3,p4"}]
    )
    capability = source_capability(frame)
    assert capability["lineup_pair_detected"] is True
    assert capability["lineup_strength_pair_detected"] is False
    assert capability["status"] == "LINEUP_IDENTITY_ONLY_PLAYER_STRENGTH_SOURCE_REQUIRED"
    assert capability["experiment_ready"] is False


def test_strength_schema_still_requires_temporal_provenance():
    frame = pd.DataFrame(
        [{"HomeLineupStrength": 77.2, "AwayLineupStrength": 74.1}]
    )
    capability = source_capability(frame)
    assert capability["lineup_strength_pair_detected"] is True
    assert capability["status"] == "STRENGTH_SCHEMA_DETECTED_TEMPORAL_PROVENANCE_REQUIRED"
    assert capability["experiment_ready"] is False


def test_team_strength_like_columns_do_not_trigger_lineup_detection():
    frame = pd.DataFrame(
        [{"HomeTeamStrength": 77.2, "AwayTeamStrength": 74.1}]
    )
    capability = source_capability(frame)
    assert capability["lineup_pair_detected"] is False
    assert capability["lineup_strength_pair_detected"] is False
    assert capability["status"] == "DATA_GAP"
