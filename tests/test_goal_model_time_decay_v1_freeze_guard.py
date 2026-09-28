import goal_model_time_decay_v1_freeze_guard as guard


def test_semantic_projection_extracts_selected_folds_from_runtime():
    report = {
        "experiment_id": "GOAL_MODEL_TIME_DECAY_V1",
        "source_rows": 3800,
        "feature_rows": 3800,
        "package_versions": {"xgboost": "3.4.1"},
        "result": {
            "outer_fold_count": 1,
            "outer_test_seasons": ["2025/2026"],
            "selection_counts": {"NONE": 1},
            "positive_folds": {"score_nll": 0},
            "pooled": {"score_nll": {"baseline": 1.0, "candidate": 1.0}},
            "paired_bootstrap": {"score_nll": {"ci95_low": 0.0}},
            "signal_supported": False,
            "interpretation": "NO_ROBUST_DECAY_SUPPORT",
            "folds": [
                {
                    "test_season": "2025/2026",
                    "selected_half_life_days": None,
                }
            ],
        },
    }

    projected = guard.semantic_projection(report)
    assert projected["result"]["selected_by_fold"] == [
        {
            "test_season": "2025/2026",
            "selected_half_life_days": None,
        }
    ]


def test_compare_accepts_numeric_roundoff_within_tolerance():
    errors = guard.compare(
        {"x": 1.0},
        {"x": 1.0 + 5e-13},
        atol=1e-12,
    )
    assert errors == []


def test_compare_rejects_material_numeric_change():
    errors = guard.compare(
        {"x": 1.0},
        {"x": 1.001},
        atol=1e-12,
    )
    assert errors
