import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import la_liga_market_anchor_prospective_20260915 as freeze_mod
import evaluate_la_liga_market_anchor_prospective_20260915 as eval_mod


def test_target_manifest_is_exactly_three_and_outcome_free():
    freeze_mod.validate_targets()
    assert len(freeze_mod.TARGETS) == 3
    assert {row["event_id"] for row in freeze_mod.TARGETS} == eval_mod.EXPECTED_EVENT_IDS
    for row in freeze_mod.TARGETS:
        assert not (freeze_mod.FORBIDDEN_OUTCOME_KEYS & {str(k).lower() for k in row})
        assert pd.Timestamp(row["market_snapshot_time_utc"]) < pd.Timestamp(row["kickoff_utc"])
        assert row["bookmakers_count"] == 19


def test_prediction_runner_fails_closed_at_first_kickoff(tmp_path):
    with pytest.raises(RuntimeError, match="first kickoff"):
        freeze_mod.run(tmp_path, now_utc=freeze_mod.FIRST_KICKOFF)


def _synthetic_freeze():
    predictions = []
    for row in freeze_mod.TARGETS:
        p = list(row["market"])
        predictions.append({
            "event_id": row["event_id"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
            "kickoff_utc": row["kickoff_utc"],
            "market_snapshot_time_utc": row["market_snapshot_time_utc"],
            "bookmakers_count": row["bookmakers_count"],
            "market_probabilities": p,
            "active_lambda_0_probabilities": p,
            "shadow_lambda_1_probabilities": p,
            "feature_min_prior_matches": 30,
        })
    report = {
        "experiment_id": freeze_mod.EXPERIMENT_ID,
        "evidence_class": freeze_mod.EVIDENCE_CLASS,
        "outcomes_available_to_runner": False,
        "active_lambda": 0.0,
        "shadow_lambda": 1.0,
        "predictions": predictions,
    }
    report["freeze_sha256"] = eval_mod._sha256_json(report)
    return report


def test_evaluator_fails_closed_before_outcome_gate():
    freeze = _synthetic_freeze()
    outcomes = {event_id: "H" for event_id in eval_mod.EXPECTED_EVENT_IDS}
    with pytest.raises(RuntimeError, match="outcome gate"):
        eval_mod.evaluate(freeze, outcomes, now_utc=eval_mod.EVALUATION_NOT_BEFORE - pd.Timedelta(seconds=1))


def test_evaluator_requires_all_three_exact_event_ids():
    freeze = _synthetic_freeze()
    with pytest.raises(ValueError, match="exactly the three"):
        eval_mod.evaluate(
            freeze,
            {next(iter(eval_mod.EXPECTED_EVENT_IDS)): "H"},
            now_utc=eval_mod.EVALUATION_NOT_BEFORE,
        )


def test_lambda_zero_baseline_must_equal_market():
    freeze = _synthetic_freeze()
    freeze["predictions"][0]["active_lambda_0_probabilities"] = [0.2, 0.3, 0.5]
    body = dict(freeze)
    body.pop("freeze_sha256")
    freeze["freeze_sha256"] = eval_mod._sha256_json(body)
    with pytest.raises(ValueError, match="must equal market"):
        eval_mod.validate_freeze(freeze)


def test_scoring_prefers_perfect_probabilities():
    y = np.array([0, 1, 2])
    perfectish = np.array([[0.98, 0.01, 0.01], [0.01, 0.98, 0.01], [0.01, 0.01, 0.98]])
    flat = np.full((3, 3), 1 / 3)
    assert eval_mod.score(y, perfectish)["brier"] < eval_mod.score(y, flat)["brier"]
    assert eval_mod.score(y, perfectish)["log_loss"] < eval_mod.score(y, flat)["log_loss"]
