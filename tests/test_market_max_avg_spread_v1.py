import numpy as np
import pandas as pd

import market_max_avg_spread_v1 as experiment


def test_spread_valid_requires_max_at_least_avg():
    frame = pd.DataFrame(
        {
            "AvgH": [2.0, 2.0],
            "AvgD": [3.0, 3.0],
            "AvgA": [4.0, 4.0],
            "MaxH": [2.2, 1.9],
            "MaxD": [3.3, 3.2],
            "MaxA": [4.4, 4.2],
        }
    )
    mask = experiment.spread_valid_mask(frame)
    assert mask.tolist() == [True, False]


def test_rms_spread_zero_when_max_equals_avg():
    avg = np.array([[2.0, 3.0, 4.0]], dtype=float)
    maximum = avg.copy()
    gaps = maximum / avg - 1.0
    spread = np.sqrt(np.mean(gaps**2, axis=1))
    assert np.allclose(spread, 0.0)


def test_rms_spread_positive_for_wider_best_prices():
    avg = np.array([[2.0, 3.0, 4.0]], dtype=float)
    maximum = np.array([[2.2, 3.3, 4.4]], dtype=float)
    gaps = maximum / avg - 1.0
    spread = np.sqrt(np.mean(gaps**2, axis=1))
    assert spread[0] > 0.0


def test_brier_loss_is_lower_for_better_probability():
    frame = pd.DataFrame({"FTR": ["H"]})
    good = np.array([[0.8, 0.1, 0.1]])
    weak = np.array([[0.4, 0.3, 0.3]])
    assert experiment.brier_losses(frame, good)[0] < experiment.brier_losses(frame, weak)[0]


def test_thresholds_use_discovery_only():
    rows = []
    for season in experiment.SEASONS:
        for index in range(4):
            rows.append(
                {
                    "season": season,
                    "market_spread": (
                        float(index + 1)
                        if season in experiment.DISCOVERY_SEASONS
                        else 1000.0 + index
                    ),
                }
            )
    data = pd.DataFrame(rows)
    thresholds = experiment.freeze_thresholds(data)
    assert thresholds["discovery_rows"] == 20
    assert thresholds["high_q75"] < 1000.0


def test_assign_groups_uses_frozen_thresholds():
    data = pd.DataFrame(
        {
            "market_spread": [0.01, 0.02, 0.03, 0.04],
        }
    )
    grouped = experiment.assign_groups(
        data,
        {"low_q25": 0.015, "high_q75": 0.035},
    )
    assert grouped["spread_group"].astype(object).tolist() == [
        "LOW",
        pd.NA,
        pd.NA,
        "HIGH",
    ]


def test_frozen_temporal_scope():
    assert experiment.DISCOVERY_SEASONS == [
        "2019/2020",
        "2020/2021",
        "2021/2022",
        "2022/2023",
        "2023/2024",
    ]
    assert experiment.VALIDATION_SEASON == "2024/2025"
    assert experiment.TEST_SEASON == "2025/2026"
    assert "2026/2027" not in experiment.SEASONS
    assert experiment.BOOTSTRAP_SAMPLES == 10000
