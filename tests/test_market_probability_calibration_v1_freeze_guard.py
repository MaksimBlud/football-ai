import market_probability_calibration_v1_freeze_guard as guard


def sample_report():
    return {
        "experiment_id": "MARKET_PROBABILITY_CALIBRATION_V1",
        "source_rows": 2660,
        "package_versions": {
            "pandas": "3.0.6",
            "numpy": "2.5.3",
            "scipy": "1.16.2",
        },
        "result": {
            "pooled_oos_matches": 1520,
            "outer_test_seasons": [
                "2022/2023",
                "2023/2024",
                "2024/2025",
                "2025/2026",
            ],
            "pooled_metrics": {
                "RAW_MULTIPLICATIVE": {
                    "logloss": 1.0,
                    "brier": 0.6,
                    "accuracy": 0.55,
                    "calibration": {"ignored": True},
                }
            },
            "candidate_decisions": {
                "TEMPERATURE": {
                    "pooled_delta_vs_raw": {
                        "logloss": 0.001,
                        "brier": 0.001,
                    },
                    "joint_season_wins": 0,
                    "paired_bootstrap": {
                        "logloss": {
                            "ci95_low": -0.001,
                            "ci95_high": 0.002,
                            "bootstrap_probability_candidate_better": 0.2,
                            "samples": 10000,
                            "seed": 20260929,
                        },
                        "brier": {
                            "ci95_low": -0.001,
                            "ci95_high": 0.002,
                            "bootstrap_probability_candidate_better": 0.2,
                            "samples": 10000,
                            "seed": 20260929,
                        },
                    },
                    "supported": False,
                }
            },
            "supported_candidates": [],
            "active_method": "RAW_MULTIPLICATIVE",
            "interpretation": "KEEP_RAW_MULTIPLICATIVE",
            "folds": [{"ignored": True}],
        },
    }


def test_projection_drops_nonsemantic_runtime_fields():
    projected = guard.projection(sample_report())
    assert "folds" not in projected["result"]
    assert "calibration" not in projected["result"]["pooled_metrics"]["RAW_MULTIPLICATIVE"]
    assert "samples" not in projected["result"]["candidate_decisions"]["TEMPERATURE"]["paired_bootstrap"]["logloss"]


def test_compare_accepts_small_roundoff():
    assert guard.compare(
        {"x": 1.0},
        {"x": 1.0 + 5e-13},
        atol=1e-12,
    ) == []


def test_compare_rejects_material_change():
    assert guard.compare(
        {"x": 1.0},
        {"x": 1.01},
        atol=1e-12,
    )
