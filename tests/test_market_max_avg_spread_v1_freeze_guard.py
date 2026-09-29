import market_max_avg_spread_v1_freeze_guard as guard


def test_compare_accepts_roundoff():
    assert guard.compare(
        {"x": 1.0},
        {"x": 1.0 + 5e-13},
        atol=1e-12,
    ) == []


def test_compare_rejects_material_change():
    assert guard.compare(
        {"x": 1.0},
        {"x": 1.1},
        atol=1e-12,
    )
