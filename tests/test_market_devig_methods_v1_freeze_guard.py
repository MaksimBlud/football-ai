import market_devig_methods_v1_freeze_guard as guard


def _runtime_report():
    methods = {}
    for method in guard.METHODS:
        methods[method] = {
            "overall": {
                "logloss": 1.0,
                "brier": 0.6,
                "calibration": {
                    "favorite_calibration_gap_observed_minus_predicted": 0.01,
                    "draw_calibration_gap_observed_minus_predicted": -0.01,
                    "longshot_calibration_gap_observed_minus_predicted": 0.0,
                },
                "parameters": {
                    "mean_overround": 0.04,
                    **({"mean_k": 1.05} if method == "POWER" else {}),
                    **({"mean_z": 0.02} if method == "SHIN" else {}),
                },
            },
            "by_season": {
                season: {"logloss": 1.0, "brier": 0.6}
                for season in guard.HOLDOUT_SEASONS
            },
        }

    alternatives = {
        method: {
            "logloss": 1.0,
            "brier": 0.6,
            "delta_logloss_vs_multiplicative": 0.0,
            "delta_brier_vs_multiplicative": 0.0,
            "joint_season_wins": 0,
            "eligible": False,
        }
        for method in guard.ALTERNATIVES
    }

    bootstrap = {
        method: {
            metric: {
                "ci95_low": -0.001,
                "ci95_high": 0.001,
                "bootstrap_probability_candidate_better": 0.5,
                "mean_delta_candidate_minus_baseline": 0.0,
                "samples": 10000,
                "seed": 20260929,
            }
            for metric in ("logloss", "brier")
        }
        for method in guard.ALTERNATIVES
    }

    return {
        "experiment_id": "MARKET_DEVIG_METHODS_V1",
        "source_rows": 2660,
        "package_versions": {"pandas": "3.0.6", "numpy": "2.5.3"},
        "result": {
            "selected_on_discovery": "MULTIPLICATIVE",
            "discovery": {
                "baseline": {"matches": 1900, "logloss": 1.0, "brier": 0.6},
                "alternatives": alternatives,
            },
            "all_methods": methods,
            "overall_deltas_vs_multiplicative": {
                method: {"logloss": 0.0, "brier": 0.0}
                for method in guard.ALTERNATIVES
            },
            "alternative_bootstrap_all_2660": bootstrap,
            "robust_support": False,
            "interpretation": "KEEP_MULTIPLICATIVE",
            "active_method": "MULTIPLICATIVE",
        },
    }


def test_semantic_projection_keeps_decision_critical_fields():
    projected = guard.semantic_projection(_runtime_report())

    assert projected["source_rows"] == 2660
    assert projected["result"]["selected_on_discovery"] == "MULTIPLICATIVE"
    assert projected["result"]["mean_method_parameters"] == {
        "POWER_k": 1.05,
        "SHIN_z": 0.02,
        "market_overround": 0.04,
    }
    assert set(projected["result"]["holdout_method_metrics"]) == {
        "2024/2025",
        "2025/2026",
    }


def test_compare_accepts_roundoff_inside_tolerance():
    assert guard.compare(
        {"value": 1.0},
        {"value": 1.0 + 5e-13},
        atol=1e-12,
    ) == []


def test_compare_rejects_material_change():
    assert guard.compare(
        {"value": 1.0},
        {"value": 1.001},
        atol=1e-12,
    )
