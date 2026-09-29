import preclose_closing_forecast_v1_freeze_guard as guard


def test_compare_accepts_roundoff_inside_tolerance():
    assert guard.compare(
        {"x": 1.0},
        {"x": 1.0 + 5e-13},
        atol=1e-12,
    ) == []


def test_compare_rejects_material_numeric_change():
    assert guard.compare(
        {"x": 1.0},
        {"x": 1.001},
        atol=1e-12,
    )


def test_projection_keeps_selected_candidate_and_two_holdouts():
    report = {
        "experiment_id": "1X2_PRECLOSE_CLOSING_FORECAST_V1",
        "source_rows": 2660,
        "package_versions": {
            "pandas": "3.0.6",
            "numpy": "2.5.3",
            "requests": "2.32.5",
            "scikit_learn": "1.9.1",
        },
        "result": {
            "selected_candidate": {
                "candidate_id": "RIDGE_STATE_PLUS_CONSENSUS_A0.01",
                "spec": {
                    "name": "RIDGE",
                    "feature_variant": "STATE_PLUS_CONSENSUS",
                    "alpha": 0.01,
                },
                "close_mae": 0.01,
                "close_cross_entropy": 0.9,
                "outcome_logloss": 0.95,
            },
            "validation_zero": {
                "close_mae": 0.011,
                "close_cross_entropy": 0.901,
                "outcome_logloss": 0.949,
            },
            "validation_passed": True,
            "holdouts": {},
            "paired_bootstrap_760_holdout_matches": {
                "close_mae": {
                    "mean_delta_candidate_minus_zero": -0.0001,
                    "ci95_low": -0.0002,
                    "ci95_high": 0.0001,
                    "bootstrap_probability_candidate_better": 0.7,
                },
                "close_cross_entropy": {
                    "mean_delta_candidate_minus_zero": -0.0001,
                    "ci95_low": -0.0002,
                    "ci95_high": -0.00001,
                    "bootstrap_probability_candidate_better": 0.99,
                },
            },
            "robust_support": False,
            "interpretation": "NO_ROBUST_PRECLOSE_TO_CLOSE_SIGNAL",
        },
    }

    for season in guard.HOLDOUTS:
        report["result"]["holdouts"][season] = {
            "zero": {
                "close_mae": 0.02,
                "close_cross_entropy": 1.0,
            },
            "candidate": {
                "close_mae": 0.019,
                "close_cross_entropy": 0.999,
                "direction_accuracy": 0.55,
                "actual_mean_max_abs_move": 0.025,
                "actual_argmax_change_rate": 0.04,
            },
            "delta_candidate_minus_zero": {
                "close_mae": -0.001,
                "close_cross_entropy": -0.001,
                "outcome_logloss": -0.001,
                "outcome_brier": -0.001,
                "max_move_mae": -0.005,
            },
            "passed_primary_gate": True,
        }

    projected = guard.semantic_projection(report)

    assert (
        projected["result"]["selected_candidate"]["candidate_id"]
        == "RIDGE_STATE_PLUS_CONSENSUS_A0.01"
    )
    assert set(projected["result"]["holdouts"]) == {
        "2024/2025",
        "2025/2026",
    }
    assert projected["result"]["robust_support"] is False
