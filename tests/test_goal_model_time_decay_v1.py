import ast
from pathlib import Path

import numpy as np
import pandas as pd

import goal_model_time_decay_v1 as experiment


def _literal_assignment(path: str, name: str):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in {path}")


def test_experiment_excludes_open_2026_2027_season():
    assert "2026/2027" not in experiment.EXPERIMENT_SEASONS
    assert experiment.EXCLUDED_SEASONS == ["2026/2027"]
    assert experiment.EXPERIMENT_SEASONS[-1] == "2025/2026"


def test_research_architecture_mirrors_current_goal_training_contract():
    production_features = _literal_assignment(
        "train_goal_models_no_odds.py",
        "FEATURES",
    )
    production_params = _literal_assignment(
        "train_goal_models_no_odds.py",
        "common_params",
    )

    assert experiment.FEATURES == production_features

    research_params = dict(experiment.MODEL_PARAMS)
    research_params.pop("n_jobs")
    assert research_params == production_params


def test_no_decay_weights_are_exactly_one():
    dates = pd.Series(
        pd.to_datetime(
            ["2024-01-01", "2025-01-01", "2025-12-31"]
        )
    )
    weights = experiment.temporal_weights(
        dates,
        pd.Timestamp("2026-01-01"),
        None,
    )
    assert np.array_equal(weights, np.ones(3))


def test_half_life_ratio_is_preserved_after_mean_one_normalization():
    cutoff = pd.Timestamp("2026-01-01")
    dates = pd.Series(
        [
            cutoff,
            cutoff - pd.Timedelta(days=365),
        ]
    )
    weights = experiment.temporal_weights(
        dates,
        cutoff,
        365,
    )

    assert np.isclose(weights.mean(), 1.0)
    assert np.isclose(weights[1] / weights[0], 0.5)


def test_temporal_weights_reject_future_training_rows():
    cutoff = pd.Timestamp("2026-01-01")
    dates = pd.Series([cutoff + pd.Timedelta(days=1)])

    try:
        experiment.temporal_weights(dates, cutoff, 365)
    except ValueError as exc:
        assert "after the evaluation cutoff" in str(exc)
    else:
        raise AssertionError("future training row was accepted")


def test_selection_fails_closed_when_decay_does_not_jointly_improve():
    rows = {
        "NONE": {"score_nll": 2.90, "logloss_1x2": 1.00},
        "180": {"score_nll": 2.89, "logloss_1x2": 1.01},
        "365": {"score_nll": 2.91, "logloss_1x2": 0.99},
        "730": {"score_nll": 2.90, "logloss_1x2": 1.00},
        "1460": {"score_nll": 2.92, "logloss_1x2": 1.02},
    }
    assert experiment.select_half_life(rows) is None


def test_selection_chooses_lowest_score_nll_among_joint_improvements():
    rows = {
        "NONE": {"score_nll": 2.90, "logloss_1x2": 1.00},
        "180": {"score_nll": 2.88, "logloss_1x2": 0.99},
        "365": {"score_nll": 2.86, "logloss_1x2": 0.995},
        "730": {"score_nll": 2.87, "logloss_1x2": 0.98},
        "1460": {"score_nll": 2.91, "logloss_1x2": 0.97},
    }
    assert experiment.select_half_life(rows) == 365


def test_candidate_label_is_stable():
    assert experiment.candidate_label(None) == "NONE"
    assert experiment.candidate_label(365) == "365"
