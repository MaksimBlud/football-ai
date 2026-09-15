import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import market_anchor_1x2_v2_shadow as v2


ROOT = Path(__file__).resolve().parents[1]


def _artifact():
    features = list(v2.FEATURE_SETS[v2.FEATURE_VARIANT])
    body = {
        **v2.candidate_recipe(),
        "training_rows": 100,
        "training_fingerprint_sha256": "a" * 64,
        "imputer_medians": [0.0] * len(features),
        "scaler_mean": [0.0] * len(features),
        "scaler_scale": [1.0] * len(features),
        "weights": [[0.0, 0.0] for _ in range(len(features) + 1)],
    }
    body["artifact_sha256"] = v2._sha256_json(body)
    return body


def _row(**updates):
    row = {
        "experiment_id": v2.EXPERIMENT_ID,
        "evidence_class": v2.EVIDENCE_CLASS,
        "league": "SERIE_A",
        "event_id": "evt-1",
        "home_team": "Home",
        "away_team": "Away",
        "kickoff_utc": "2026-09-18T18:45:00Z",
        "capture_time_utc": "2026-09-18T17:00:00Z",
        "market_snapshot_time_utc": "2026-09-18T16:55:00Z",
        "incumbent_generated_at_utc": "2026-09-18T16:58:00Z",
        "candidate_generated_at_utc": "2026-09-18T16:59:00Z",
        "feature_history_cutoff_utc": "2026-09-18T16:50:00Z",
        "candidate_training_data_through_utc": "2026-06-30T23:59:59Z",
        "market_home_probability": 0.50,
        "market_draw_probability": 0.25,
        "market_away_probability": 0.25,
        "incumbent_home_probability": 0.48,
        "incumbent_draw_probability": 0.27,
        "incumbent_away_probability": 0.25,
        "candidate_home_probability": 0.49,
        "candidate_draw_probability": 0.26,
        "candidate_away_probability": 0.25,
        "candidate_artifact_sha256": "b" * 64,
        "incumbent_model_sha256": v2.INCUMBENT_MODEL_SHA256,
        "code_commit_sha": "c" * 40,
    }
    row.update(updates)
    return row


def test_protocol_is_frozen_to_v1_serie_a_selection():
    source = json.loads((ROOT / "experiments/market_anchor_1x2_v1_report.json").read_text())
    serie_a = next(x for x in source["league_reports"] if x["league"] == "SERIE_A")
    protocol = json.loads((ROOT / "experiments/market_anchor_1x2_v2_protocol.json").read_text())

    assert serie_a["selected_feature_variant"] == "ALL_FOOTBALL"
    assert serie_a["selected_lambda"] == 1.0
    assert protocol["candidate_recipe"]["feature_variant"] == serie_a["selected_feature_variant"]
    assert protocol["candidate_recipe"]["lambda"] == serie_a["selected_lambda"]
    assert protocol["candidate_recipe"]["use_opened_2026_27_outcomes_for_fit_or_selection"] is False
    assert protocol["primary_cohort"]["league"] == "SERIE_A"
    assert protocol["first_outcome_read_gate"]["completed_primary_events"] == 30
    assert protocol["decision_policy"]["automatic_promotion"] is False
    assert protocol["decision_policy"]["result"] == "NO_BET"


def test_candidate_recipe_refits_only_pre_2026_27_history():
    recipe = v2.candidate_recipe()
    assert recipe["primary_league"] == "SERIE_A"
    assert recipe["feature_variant"] == "ALL_FOOTBALL"
    assert recipe["lambda"] == 1.0
    assert recipe["l2_penalty"] == 1.0
    assert recipe["refit_seasons"][-1] == "2025-2026"
    assert "2026-2027" not in recipe["refit_seasons"]
    assert recipe["opened_2026_27_outcomes_used"] is False
    assert len(recipe["features"]) == 19


def test_serialized_candidate_validation_and_zero_residual_identity():
    artifact = _artifact()
    v2.validate_candidate_artifact(artifact)
    market = np.array([[0.50, 0.25, 0.25], [0.30, 0.30, 0.40]])
    features = pd.DataFrame(np.zeros((2, 19)), columns=artifact["features"])
    predicted = v2.predict_candidate(market, features, artifact)
    np.testing.assert_allclose(predicted, market, atol=1e-12)

    broken = dict(artifact)
    broken["lambda"] = 0.5
    with pytest.raises(ValueError, match="frozen recipe"):
        v2.validate_candidate_artifact(broken)


def test_shadow_capture_accepts_only_pre_kickoff_outcome_free_serie_a_rows():
    assert v2.validate_shadow_capture_rows([_row()])[0]["event_id"] == "evt-1"

    with pytest.raises(ValueError, match="outcome fields"):
        v2.validate_shadow_capture_rows([_row(result="H")])
    with pytest.raises(ValueError, match="only Serie A"):
        v2.validate_shadow_capture_rows([_row(league="EPL")])
    with pytest.raises(ValueError, match="pre-kickoff"):
        v2.validate_shadow_capture_rows([_row(capture_time_utc="2026-09-18T19:00:00Z")])
    with pytest.raises(ValueError, match="backfilled"):
        v2.validate_shadow_capture_rows([
            _row(kickoff_utc="2026-09-15T18:45:00Z", capture_time_utc="2026-09-15T17:00:00Z")
        ])


def test_shadow_capture_requires_frozen_training_and_incumbent_identity():
    with pytest.raises(ValueError, match="training cutoff"):
        v2.validate_shadow_capture_rows([_row(candidate_training_data_through_utc="2026-09-01T00:00:00Z")])
    with pytest.raises(ValueError, match="incumbent model sha"):
        v2.validate_shadow_capture_rows([_row(incumbent_model_sha256="d" * 64)])


def test_outcome_gate_is_count_based_and_no_automatic_promotion_exists():
    assert not v2.outcome_read_permitted(0)
    assert not v2.outcome_read_permitted(29)
    assert v2.outcome_read_permitted(30)
    assert v2.outcome_read_permitted(31)
    with pytest.raises(ValueError):
        v2.outcome_read_permitted(-1)


def test_v2_code_does_not_reference_production_pickle_paths():
    text = (ROOT / "market_anchor_1x2_v2_shadow.py").read_text()
    assert "football_model_xgboost_elo.pkl" not in text
    assert "joblib.dump" not in text
    assert "--production" not in text
