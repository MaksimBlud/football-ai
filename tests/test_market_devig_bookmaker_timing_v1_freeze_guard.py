import market_devig_bookmaker_timing_v1_freeze_guard as guard


def test_compare_accepts_roundoff():
    assert guard.compare(
        {"x": 1.0},
        {"x": 1.0 + 5e-13},
        atol=1e-12,
    ) == []


def test_compare_rejects_material_change():
    assert guard.compare(
        {"x": 1.0},
        {"x": 1.001},
        atol=1e-12,
    )


def test_projection_preserves_source_decision_shape():
    availability = {
        source: {
            "eligible": source != "PINNACLE_STANDARD",
            "valid_rows_total": 2660 if source != "PINNACLE_STANDARD" else 2490,
            "by_season": {
                guard.TEST_SEASON: {
                    "coverage": 1.0 if source != "PINNACLE_STANDARD" else 0.5526315789473685
                }
            },
        }
        for source in guard.SOURCES
    }

    source_reports = {}
    for source in guard.SOURCES:
        if source in {"PINNACLE_STANDARD", "PINNACLE_CLOSING"}:
            source_reports[source] = {
                "interpretation": "SOURCE_UNAVAILABLE",
            }
        else:
            source_reports[source] = {
                "selected_on_discovery": "POWER" if source == "AVG_CLOSING" else "MULTIPLICATIVE",
                "robust_support": False,
                "interpretation": "KEEP_SOURCE_MULTIPLICATIVE",
                "discovery": {
                    "alternatives": {
                        "POWER": {
                            "delta_logloss_vs_multiplicative": -0.0001,
                            "delta_brier_vs_multiplicative": -0.0002,
                            "joint_season_wins": 3,
                        }
                    }
                },
                "validation": {
                    "baseline": {"logloss": 1.0, "brier": 0.6},
                    "candidate": {"logloss": 1.001, "brier": 0.601},
                    "passed": False,
                },
                "test": {
                    "baseline": {"logloss": 1.0, "brier": 0.6},
                    "candidate": {"logloss": 1.001, "brier": 0.601},
                    "passed": False,
                },
                "selected_bootstrap": {
                    "logloss": {
                        "ci95_low": -0.001,
                        "ci95_high": 0.001,
                        "bootstrap_probability_candidate_better": 0.4,
                    },
                    "brier": {
                        "ci95_low": -0.001,
                        "ci95_high": 0.001,
                        "bootstrap_probability_candidate_better": 0.4,
                    },
                },
            }

    common = {
        source: {
            "logloss": 1.0,
            "brier": 0.6,
            "accuracy": 0.55,
            "mean_overround": 0.04,
        }
        for source in (
            "AVG_STANDARD",
            "BET365_STANDARD",
            "AVG_CLOSING",
            "BET365_CLOSING",
        )
    }

    report = {
        "experiment_id": "MARKET_DEVIG_BOOKMAKER_TIMING_V1",
        "source_rows": 2660,
        "package_versions": {
            "pandas": "3.0.6",
            "numpy": "2.5.3",
            "requests": "2.32.5",
        },
        "result": {
            "availability": availability,
            "source_reports": source_reports,
            "common_fixture_diagnostic": {
                "common_rows": 2660,
                "by_source": common,
            },
            "supported_sources": [],
            "interpretation": "NO_SOURCE_SPECIFIC_DEVIG_SUPPORT",
        },
    }

    projected = guard.semantic_projection(report)

    assert projected["result"]["availability"]["PINNACLE_STANDARD"]["eligible"] is False
    assert projected["result"]["source_decisions"]["AVG_CLOSING"]["selected"] == "POWER"
    assert projected["result"]["common_fixture_multiplicative"]["common_rows"] == 2660
