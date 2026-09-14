import json
from pathlib import Path

import pytest

from point_in_time_cross_league_replay_v1_freeze_guard import (
    EXPECTED_COHORT_INVENTORY_SHA256,
    EXPECTED_FULL_MANIFEST_SHA256,
    EXPECTED_FULL_REPLAY_CSV_SHA256,
    EXPECTED_PREDICTIONS_CANONICAL_SHA256,
    canonical_predictions_sha256,
    validate_frozen_predictions,
)

FROZEN = Path("experiments/point_in_time_cross_league_replay_v1_predictions.json")


def test_committed_probability_vectors_are_exactly_frozen():
    payload = validate_frozen_predictions(FROZEN)
    assert payload["total_events"] == 47
    assert payload["cohort_inventory_sha256"] == EXPECTED_COHORT_INVENTORY_SHA256
    assert payload["full_replay_csv_sha256"] == EXPECTED_FULL_REPLAY_CSV_SHA256
    assert payload["full_manifest_sha256"] == EXPECTED_FULL_MANIFEST_SHA256
    assert payload["predictions_canonical_sha256"] == EXPECTED_PREDICTIONS_CANONICAL_SHA256
    assert canonical_predictions_sha256(payload["predictions"]) == EXPECTED_PREDICTIONS_CANONICAL_SHA256


def test_frozen_probability_change_fails_closed(tmp_path):
    payload = json.loads(FROZEN.read_text(encoding="utf-8"))
    payload["predictions"][0]["model_home_prob"] += 0.001
    payload["predictions"][0]["model_away_prob"] -= 0.001
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RuntimeError, match="probability vectors changed"):
        validate_frozen_predictions(changed)


def test_replay_can_never_be_relabeled_prospective(tmp_path):
    payload = json.loads(FROZEN.read_text(encoding="utf-8"))
    payload["prospective"] = True
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(RuntimeError, match="never be relabeled prospective"):
        validate_frozen_predictions(changed)


def test_no_outcome_values_are_stored_in_frozen_prediction_rows():
    payload = json.loads(FROZEN.read_text(encoding="utf-8"))
    forbidden = {
        "result",
        "outcome",
        "home_goals",
        "away_goals",
        "score",
        "settlement",
    }
    for row in payload["predictions"]:
        assert forbidden.isdisjoint(row)
