import favorite_longshot_bias_v1_freeze_guard as guard


def sample_runtime():
    return {
        "experiment_id": "FAVORITE_LONGSHOT_BIAS_V1",
        "source_rows": 100,
        "package_versions": {
            "pandas": "3.0.6",
            "numpy": "2.5.3",
            "requests": "2.32.5",
        },
        "result": {
            "eligible_leagues": ["EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA"],
            "standard": {
                "side_offers": 300,
                "fixtures": 100,
                "temporal": {
                    split: {
                        "favorite": {"roi": -0.03},
                        "longshot": {"roi": -0.10},
                        "bias_delta_longshot_minus_favorite": -0.07,
                    }
                    for split in ("discovery", "validation", "test")
                } | {
                    "overall": {
                        "favorite": {
                            "offers": 50,
                            "wins": 30,
                            "mean_probability": 0.6,
                            "observed_win_rate": 0.6,
                            "calibration_gap": 0.0,
                            "mean_odds": 1.6,
                            "roi": -0.03,
                        },
                        "longshot": {
                            "offers": 60,
                            "wins": 8,
                            "mean_probability": 0.14,
                            "observed_win_rate": 0.133,
                            "calibration_gap": -0.007,
                            "mean_odds": 7.0,
                            "roi": -0.10,
                        },
                        "bias_delta_longshot_minus_favorite": -0.07,
                    }
                },
                "by_league": {
                    "EPL": {
                        "bias_delta_longshot_minus_favorite": -0.01,
                    }
                },
                "negative_bias_leagues": 4,
                "bootstrap": {
                    "mean_bias_delta": -0.07,
                    "ci95_low": -0.12,
                    "ci95_high": -0.02,
                    "bootstrap_probability_negative": 0.99,
                    "samples": 10000,
                    "seed": 20260929,
                },
                "bands": {
                    "P60_PLUS": {
                        "offers": 10,
                        "wins": 7,
                        "mean_probability": 0.7,
                        "observed_win_rate": 0.7,
                        "calibration_gap": 0.0,
                        "mean_odds": 1.4,
                        "roi": -0.02,
                    }
                },
            },
            "closing_diagnostic": {
                "overall": {
                    "favorite": {"roi": -0.02},
                    "longshot": {"roi": -0.11},
                    "bias_delta_longshot_minus_favorite": -0.09,
                },
                "by_league": {
                    "EPL": {
                        "bias_delta_longshot_minus_favorite": -0.01,
                    }
                },
            },
            "max_line_shopping_diagnostic": {
                "overall": {
                    "favorite": {"roi": 0.01},
                    "longshot": {"roi": -0.03},
                    "bias_delta_longshot_minus_favorite": -0.04,
                }
            },
            "supported": True,
            "interpretation": "FAVORITE_LONGSHOT_BIAS_SUPPORTED",
        },
    }


def test_projection_extracts_semantic_runtime_result():
    p = guard.projection(sample_runtime())
    assert p["result"]["standard"]["temporal"]["discovery"]["bias_delta"] == -0.07
    assert p["result"]["standard"]["by_league"]["EPL"] == -0.01
    assert p["result"]["closing_diagnostic"]["overall"]["bias_delta"] == -0.09
    assert p["result"]["max_line_shopping_diagnostic"]["overall"]["bias_delta"] == -0.04


def test_compare_accepts_roundoff():
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
