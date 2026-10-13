import numpy as np

import market_anchor_v2_saved_cohort_replay as replay


def _score(field: str):
    y = np.asarray([replay.RESULT_TO_INT[row["result"]] for row in replay.TARGETS], dtype=int)
    p = np.asarray([row[field] for row in replay.TARGETS], dtype=float)
    onehot = np.eye(3)[y]
    return {
        "accuracy": float((p.argmax(axis=1) == y).mean()),
        "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
        "log_loss": float(-np.mean(np.log(p[np.arange(len(y)), y]))),
    }


def test_saved_serie_a_cohort_is_exactly_ten_unique_events():
    replay.validate_targets()
    assert len(replay.TARGETS) == 10
    assert len({row["event_id"] for row in replay.TARGETS}) == 10
    assert replay.PRIMARY_LEAGUE == "SERIE_A"
    assert replay.FROZEN_PARENT_REPLAY_EVENTS == 47


def test_frozen_recipe_identity_is_not_tuned_in_replay():
    assert replay.FEATURE_VARIANT == "ALL_FOOTBALL"
    assert replay.SHADOW_LAMBDA == 1.0
    assert replay.L2_PENALTY == 1.0
    assert replay.FROZEN_V2_COMMIT == "df19777087fb89af049eedce44ff93f0aa6e6360"
    assert replay.HISTORY_CUTOFF_DATE.strftime("%Y-%m-%d") == "2026-09-11"


def test_saved_market_and_old_model_metrics_are_frozen():
    market = _score("market")
    old = _score("old_model")
    assert abs(market["accuracy"] - 0.6) <= 1e-15
    assert abs(market["brier"] - 0.5662948173955555) <= 1e-15
    assert abs(market["log_loss"] - 0.9674878846519602) <= 1e-15
    assert abs(old["accuracy"] - 0.5) <= 1e-15
    assert abs(old["brier"] - 0.5265153874268573) <= 1e-15
    assert abs(old["log_loss"] - 0.906202231280792) <= 1e-15


def test_frozen_source_blob_pins_cover_every_restored_module():
    assert replay.EXPECTED_FROZEN_GIT_BLOBS == {
        "historical_football_signal_lab.py": "401b3a0893371bfa4a488ec92a4a54af2678c8f7",
        "market_anchor_1x2_v1.py": "58c35bf3768f7bf2b951f19a37b9a5f46b6b9801",
        "market_anchor_1x2_v2_shadow.py": "b2770d726ffafe7a3cef706b57d3391063cbfe1b",
    }


def test_saved_replay_report_is_provenance_locked():
    import json
    from pathlib import Path
    frozen = json.loads(
        Path("experiments/market_anchor_v2_saved_cohort_replay_report.json").read_text()
    )
    replay.assert_same_frozen_replay(frozen)
    assert frozen["candidate_artifact_sha256"] == (
        "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    )
    assert frozen["training_fingerprint_sha256"] == (
        "f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098"
    )


def test_provenance_and_outcome_tampering_are_rejected():
    import json
    from copy import deepcopy
    from pathlib import Path
    import pytest
    good = json.loads(
        Path("experiments/market_anchor_v2_saved_cohort_replay_report.json").read_text()
    )
    for key, replacement in [
        ("candidate_artifact_sha256", "0" * 64),
        ("training_fingerprint_sha256", "a" * 64),
        ("active_lambda", 1.0),
        ("stability_gate_passed", True),
        ("football_data_sha256", {}),
        ("production_promotion", True),
    ]:
        bad = deepcopy(good)
        bad[key] = replacement
        with pytest.raises(ValueError, match="provenance drift"):
            replay.assert_same_frozen_replay(bad)
    for changed_field in ("result", "event_id"):
        bad = deepcopy(good)
        bad["predictions"][0][changed_field] = "tampered"
        with pytest.raises(ValueError, match="event drift"):
            replay.assert_same_frozen_replay(bad)
    bad = deepcopy(good)
    bad["predictions"][0]["shadow_lambda_1"][0] += .01
    with pytest.raises(ValueError, match="probabilities drift"):
        replay.assert_same_frozen_replay(bad)


def test_candidate_export_cannot_target_production_paths():
    from pathlib import Path
    code = Path("market_anchor_v2_saved_cohort_replay.py").read_text()
    assert "save_research_candidate: bool = False" in code
    assert "--save-research-candidate" in code
    assert '"artifacts/market_anchor_v2_saved_cohort_replay/candidate_model.json"' in code
    assert "v2.validate_candidate_artifact(artifact)" in code
    assert "assert_same_frozen_replay(report)" in code
    assert 'if artifact["artifact_sha256"] != report["candidate_artifact_sha256"]:' in code
    for dangerous in ["joblib.dump(", "pickle.dump(", "os.system(", ".upsert(", "supabase.table(", "api.the-odds-api.com"]:
        assert dangerous not in code


def test_original_frozen_weights_restoration_does_not_read_mutable_2026_27():
    from pathlib import Path
    src = Path("market_anchor_v2_saved_cohort_replay.py").read_text()
    frozen_function = src.split(
        "def restore_frozen_candidate_from_training_history(", 1
    )[1].split("\ndef main()", 1)[0]
    assert "build_training_frame(_lab)" in frozen_function
    assert "build_target_features(" not in frozen_function
    assert "CURRENT_SEASON_CODE" not in frozen_function
    assert 'historical_hashes.get(season) != frozen_hashes.get(season)' in frozen_function
    assert 'model["artifact_sha256"]' not in frozen_function or (
        '("training_fingerprint_sha256", "artifact_sha256")' in frozen_function
    )
    assert '"replayed_september_target_fixtures": False' in frozen_function
    assert '"production_promotion": False' in frozen_function
    assert "--restore-candidate-only" in src
