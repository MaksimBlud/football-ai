import ast
import hashlib
from pathlib import Path

import pytest

from total_goals_inference_contract import (
    BUNDLE_VERSION,
    TOTAL_GOALS_ARTIFACTS,
    TOTAL_GOALS_FEATURES,
    TotalGoalsContractError,
    bundle_sha256_from_hashes,
    inspect_artifact_bundle,
    validate_feature_order,
    validate_history_cutoff,
    validate_prediction_window,
)


EXPECTED_FEATURES = (
    "home_last5_points",
    "away_last5_points",
    "form_difference",
    "home_goals_scored_last5",
    "home_goals_conceded_last5",
    "away_goals_scored_last5",
    "away_goals_conceded_last5",
    "home_shots_last5",
    "away_shots_last5",
    "home_shots_target_last5",
    "away_shots_target_last5",
    "home_elo",
    "away_elo",
    "elo_difference",
    "home_venue_win_rate",
    "away_venue_win_rate",
    "home_venue_goals_scored",
    "away_venue_goals_scored",
)


def _artifact_lifecycle_no_odds_features() -> tuple[str, ...]:
    tree = ast.parse(Path("artifact_lifecycle.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "NO_ODDS_FEATURES" for target in node.targets):
                return tuple(ast.literal_eval(node.value))
    raise AssertionError("NO_ODDS_FEATURES assignment not found")


def test_feature_contract_matches_artifact_lifecycle_and_recovered_training_order():
    assert TOTAL_GOALS_FEATURES == EXPECTED_FEATURES
    assert TOTAL_GOALS_FEATURES == _artifact_lifecycle_no_odds_features()
    assert validate_feature_order(EXPECTED_FEATURES) == EXPECTED_FEATURES


def test_feature_contract_rejects_reordering_or_odds_injection():
    with pytest.raises(TotalGoalsContractError):
        validate_feature_order(reversed(EXPECTED_FEATURES))
    with pytest.raises(TotalGoalsContractError):
        validate_feature_order(("home_odds", *EXPECTED_FEATURES))


def test_prediction_window_requires_strictly_future_utc_targets():
    as_of = "2026-09-14T10:00:00Z"
    validate_prediction_window(
        as_of_utc=as_of,
        commence_times_utc=["2026-09-14T10:00:01Z", "2026-09-15T18:30:00+00:00"],
    )

    for kickoff in ("2026-09-14T10:00:00Z", "2026-09-14T09:59:59Z"):
        with pytest.raises(TotalGoalsContractError):
            validate_prediction_window(as_of_utc=as_of, commence_times_utc=[kickoff])

    with pytest.raises(TotalGoalsContractError):
        validate_prediction_window(as_of_utc=as_of, commence_times_utc=[])


def test_temporal_contract_rejects_naive_or_non_utc_timestamps():
    with pytest.raises(TotalGoalsContractError):
        validate_prediction_window(
            as_of_utc="2026-09-14T10:00:00",
            commence_times_utc=["2026-09-14T11:00:00Z"],
        )
    with pytest.raises(TotalGoalsContractError):
        validate_prediction_window(
            as_of_utc="2026-09-14T10:00:00Z",
            commence_times_utc=["2026-09-14T13:00:00+02:00"],
        )


def test_history_must_be_strictly_before_as_of():
    as_of = "2026-09-14T10:00:00Z"
    validate_history_cutoff(
        as_of_utc=as_of,
        observation_times_utc=["2026-09-01T12:00:00Z", "2026-09-14T09:59:59Z"],
    )
    with pytest.raises(TotalGoalsContractError):
        validate_history_cutoff(
            as_of_utc=as_of,
            observation_times_utc=["2026-09-14T10:00:00Z"],
        )


def test_bundle_hash_matches_documented_payload_contract():
    component_hashes = {
        name: hashlib.sha256(name.encode("utf-8")).hexdigest()
        for name in TOTAL_GOALS_ARTIFACTS
    }
    payload = BUNDLE_VERSION + "\n"
    payload += "".join(f"{name}:{component_hashes[name]}\n" for name in TOTAL_GOALS_ARTIFACTS)
    expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert bundle_sha256_from_hashes(component_hashes) == expected


def test_bundle_hash_fails_closed_on_incomplete_or_invalid_identity():
    hashes = {
        name: "a" * 64
        for name in TOTAL_GOALS_ARTIFACTS
    }
    incomplete = dict(hashes)
    incomplete.pop(TOTAL_GOALS_ARTIFACTS[-1])
    with pytest.raises(TotalGoalsContractError):
        bundle_sha256_from_hashes(incomplete)

    invalid = dict(hashes)
    invalid[TOTAL_GOALS_ARTIFACTS[0]] = "not-a-sha"
    with pytest.raises(TotalGoalsContractError):
        bundle_sha256_from_hashes(invalid)


def test_artifact_bundle_inspection_hashes_real_files_without_loading_them(tmp_path):
    for index, name in enumerate(TOTAL_GOALS_ARTIFACTS):
        (tmp_path / name).write_bytes(f"artifact-{index}".encode("utf-8"))

    report = inspect_artifact_bundle(tmp_path)
    assert report["feature_names"] == list(EXPECTED_FEATURES)
    assert report["feature_count"] == 18
    assert set(report["artifacts"]) == set(TOTAL_GOALS_ARTIFACTS)
    assert len(report["bundle_sha256"]) == 64


def test_artifact_bundle_inspection_rejects_missing_file(tmp_path):
    for name in TOTAL_GOALS_ARTIFACTS[:-1]:
        (tmp_path / name).write_bytes(b"artifact")
    with pytest.raises(TotalGoalsContractError):
        inspect_artifact_bundle(tmp_path)
