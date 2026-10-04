import numpy as np
import pandas as pd
import pytest

import cross_market_lead_lag_replication_v2 as experiment
import cross_market_lead_lag_replication_transport as transport


def test_replication_leagues_are_independent_from_v1():
    assert experiment.REPLICATION_LEAGUES == (
        "BUNDESLIGA",
        "LIGUE_1",
    )


def test_replication_inherits_v1_statistical_contract():
    assert experiment.MIN_ROWS_PER_LEAGUE == 40
    assert experiment.PERMUTATION_DRAWS == 10000
    assert experiment.BOOTSTRAP_DRAWS == 10000
    assert experiment.RANDOM_SEED == 20261004


def test_replication_temporal_scope_excludes_2026_27():
    assert experiment.REFERENCE_SEASONS == (
        "2019-2020",
        "2020-2021",
        "2021-2022",
        "2022-2023",
        "2023-2024",
    )
    assert experiment.VALIDATION_SEASON == "2024-2025"
    assert experiment.TEST_SEASON == "2025-2026"
    assert "2026-2027" not in experiment.ALLOWED_SEASONS


def test_transport_maps_complete_2025_26_bundesliga_to_new_mirror():
    spec = transport._mirror_spec(
        "https://www.football-data.co.uk/mmz4281/2526/D1.csv"
    )
    assert spec.repo == "yusufislamoruk/football-prediction-bot"
    assert spec.commit == "47ca08e08f46d16a8f6a0494777b1e16ae5562b3"
    assert spec.path == "data/raw/bundesliga/D1_2025-26.csv"
    assert spec.blob_sha == "361e63baa038b50f549f2bc75b0c03a655d15673"


def test_transport_maps_complete_2025_26_ligue1_to_new_mirror():
    spec = transport._mirror_spec(
        "https://football-data.co.uk/mmz4281/2526/F1.csv"
    )
    assert spec.path == "data/raw/ligue_1/F1_2025-26.csv"
    assert spec.blob_sha == "3979f0a22d5a60d3d331a31785f3c963da794e45"


def test_transport_maps_2019_20_to_old_pinned_mirror():
    d1 = transport._mirror_spec(
        "https://football-data.co.uk/mmz4281/1920/D1.csv"
    )
    f1 = transport._mirror_spec(
        "https://football-data.co.uk/mmz4281/1920/F1.csv"
    )
    assert d1.repo == "Emire221/kahin"
    assert d1.path == "data/raw_csv/D1_2019-2020.csv"
    assert d1.blob_sha == "a07e4ab36464bd1c4b62c2e98e4559aff4fdb4ef"
    assert f1.path == "data/raw_csv/F1_2019-2020.csv"
    assert f1.blob_sha == "4e2cd6384a05d10cd9ad1a4c1b4d087d60fddd45"


def test_replication_permutation_detects_match_specific_alignment():
    rows = []
    for league in experiment.REPLICATION_LEAGUES:
        for index in range(60):
            sign = 1.0 if index % 2 == 0 else -1.0
            lead = np.array(
                [0.02 * sign, -0.01 * sign, -0.01 * sign]
            )
            move = lead.copy()
            rows.append(
                {
                    "league": league,
                    "lead_home": lead[0],
                    "lead_draw": lead[1],
                    "lead_away": lead[2],
                    "move_home": move[0],
                    "move_draw": move[1],
                    "move_away": move[2],
                    "alignment_dot": float(np.dot(lead, move)),
                }
            )

    report = experiment._permutation_test(pd.DataFrame(rows))
    assert report["observed_mean_alignment_dot"] > 0.0
    assert report["one_sided_p"] < 0.01


def test_replication_bootstrap_positive_sample_has_positive_ci():
    frame = pd.DataFrame(
        [
            {"league": league, "alignment_dot": 0.001}
            for league in experiment.REPLICATION_LEAGUES
            for _ in range(50)
        ]
    )
    report = experiment._bootstrap_mean_alignment(frame)
    assert report["ci95_low"] > 0.0


def test_replication_split_requires_both_frozen_leagues():
    rows = []
    for _ in range(50):
        rows.append(
            {
                "league": "BUNDESLIGA",
                "season": experiment.VALIDATION_SEASON,
                "alignment_dot": 0.001,
                "positive_alignment": True,
                "alignment_cosine": 0.5,
                "gap_open_tv": 0.02,
                "gap_close_to_open_score_tv": 0.01,
                "gap_reduction_tv": 0.01,
                "open_to_close_move_tv": 0.01,
                "lead_home": 0.01,
                "lead_draw": -0.005,
                "lead_away": -0.005,
                "move_home": 0.005,
                "move_draw": -0.0025,
                "move_away": -0.0025,
                "ah_fit_abs_error": 0.0,
            }
        )

    with pytest.raises(RuntimeError, match="missing a frozen league"):
        experiment._split_report(
            pd.DataFrame(rows),
            experiment.VALIDATION_SEASON,
        )
