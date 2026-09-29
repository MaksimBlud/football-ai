import market_bookmaker_dispersion_v1_freeze_guard as guard


def sample_runtime():
    by = {
        season: {"coverage": 1.0}
        for season in (
            "2019/2020","2020/2021","2021/2022",
            "2022/2023","2023/2024","2024/2025","2025/2026"
        )
    }
    return {
        "experiment_id": "MARKET_BOOKMAKER_DISPERSION_V1",
        "source_rows": 2660,
        "package_versions": {
            "pandas": "3.0.6",
            "numpy": "2.5.3",
            "scipy": "1.16.2",
        },
        "result": {
            "bookmaker_availability": {
                name: {
                    "eligible": name == "BET365",
                    "valid_rows_total": 2660 if name == "BET365" else 2000,
                    "by_season": by,
                }
                for name in guard.BOOKMAKERS
            },
            "eligible_bookmakers": ["BET365"],
            "common_rows": 0,
            "signals_supported": [],
            "interpretation": "INSUFFICIENT_SOURCE_DIVERSITY",
        },
    }


def test_projection_compacts_runtime_availability():
    projected = guard.projection(sample_runtime())
    assert projected["result"]["eligible_bookmakers"] == ["BET365"]
    assert projected["result"]["availability_summary"]["BET365"]["eligible"] is True


def test_compare_accepts_roundoff():
    assert guard.compare({"x": 1.0}, {"x": 1.0 + 5e-13}, atol=1e-12) == []


def test_compare_rejects_material_change():
    assert guard.compare({"x": 1.0}, {"x": 1.1}, atol=1e-12)
