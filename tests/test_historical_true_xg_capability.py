import pandas as pd

from historical_true_xg_capability import source_capability


def test_shots_are_not_synthesized_into_true_xg():
    frame = pd.DataFrame([{"HS": 14, "AS": 8, "HST": 6, "AST": 3}])
    capability = source_capability(frame)
    assert capability["true_xg_pair_detected"] is False
    assert capability["true_xg_columns"] is None
    assert capability["status"] == "TRUE_XG_DATA_GAP"
    assert capability["experiment_ready"] is False


def test_explicit_xg_schema_still_requires_temporal_provenance():
    frame = pd.DataFrame([{"HxG": 1.4, "AxG": 0.8}])
    capability = source_capability(frame)
    assert capability["true_xg_pair_detected"] is True
    assert capability["true_xg_columns"] == ("HxG", "AxG")
    assert capability["status"] == "TRUE_XG_SCHEMA_DETECTED_TEMPORAL_PROVENANCE_REQUIRED"
    assert capability["experiment_ready"] is False


def test_partial_xg_pair_fails_closed():
    frame = pd.DataFrame([{"HxG": 1.4, "HS": 14, "AS": 8}])
    capability = source_capability(frame)
    assert capability["true_xg_pair_detected"] is False
    assert capability["status"] == "TRUE_XG_DATA_GAP"
