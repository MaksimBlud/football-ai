import market_max_avg_spread_replication_v2_freeze_guard as guard


def sample_runtime():
    return {
        "experiment_id": "MARKET_MAX_AVG_SPREAD_REPLICATION_V2",
        "package_versions": {
            "pandas": "3.0.6",
            "numpy": "2.5.3",
            "requests": "2.32.5",
        },
        "result": {
            "eligible_leagues": [
                "LA_LIGA",
                "SERIE_A",
                "BUNDESLIGA",
                "LIGUE_1",
            ],
            "prepared_rows": 9798,
            "matched_rows": 4794,
            "matched_cell_count": 28,
            "raw_brier": {
                "breakdown": {
                    "pooled_high_minus_low": -0.15,
                    "negative_leagues": 4,
                    "league_count": 4,
                    "negative_cells": 28,
                    "negative_cell_fraction": 1.0,
                    "by_league": {
                        "LA_LIGA": {"high_minus_low": -0.18},
                    },
                },
                "bootstrap": {
                    "ci95_low": -0.17,
                    "ci95_high": -0.14,
                    "bootstrap_probability_negative": 1.0,
                },
                "supported": True,
            },
            "excess_brier": {
                "breakdown": {
                    "pooled_high_minus_low": -0.01,
                    "negative_leagues": 3,
                    "league_count": 4,
                    "negative_cells": 23,
                    "negative_cell_fraction": 23 / 28,
                    "by_league": {
                        "LA_LIGA": {"high_minus_low": -0.03},
                    },
                },
                "bootstrap": {
                    "ci95_low": -0.03,
                    "ci95_high": 0.004,
                    "bootstrap_probability_negative": 0.93,
                },
                "supported": False,
            },
            "favorite_probability_diagnostic": {
                "breakdown": {
                    "pooled_high_minus_low": 0.20,
                    "by_league": {
                        "LA_LIGA": {"high_minus_low": 0.21},
                    },
                }
            },
            "signals_supported": ["RAW_INVERSE_SPREAD_REPLICATION"],
            "interpretation": "RAW_ONLY_SPREAD_REPLICATION",
        },
    }


def test_projection_extracts_semantic_runtime_result():
    projected = guard.projection(sample_runtime())
    assert projected["result"]["raw_brier"]["supported"] is True
    assert projected["result"]["excess_brier"]["supported"] is False
    assert projected["result"]["raw_brier_by_league"]["LA_LIGA"] == -0.18
    assert projected["result"]["favorite_probability_diagnostic"]["by_league"]["LA_LIGA"] == 0.21


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
