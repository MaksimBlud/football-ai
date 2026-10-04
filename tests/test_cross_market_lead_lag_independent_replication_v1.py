import numpy as np
import pandas as pd
import pytest

import cross_market_lead_lag_independent_replication_v1 as experiment
import cross_market_lead_lag_independent_replication_transport as transport


def _row(league: str, alignment: float = 0.001) -> dict:
    sign = 1.0 if alignment >= 0 else -1.0
    lead = np.array([0.02, -0.01, -0.01])
    move = sign * lead
    return {
        "league": league,
        "season": experiment.VALIDATION_SEASON,
        "alignment_dot": float(alignment),
        "positive_alignment": bool(alignment > 0),
        "alignment_cosine": float(sign),
        "gap_open_tv": 0.02,
        "gap_close_to_open_score_tv": 0.01,
        "gap_reduction_tv": 0.01,
        "open_to_close_move_tv": 0.01,
        "lead_home": float(lead[0]),
        "lead_draw": float(lead[1]),
        "lead_away": float(lead[2]),
        "move_home": float(move[0]),
        "move_draw": float(move[1]),
        "move_away": float(move[2]),
        "ah_fit_abs_error": 0.0,
    }


def test_replication_scope_is_frozen_and_independent():
    assert experiment.LEAGUE_IDS == ("BUNDESLIGA", "LIGUE_1")
    assert experiment.PARENT_EXPERIMENT_ID == "CROSS_MARKET_LEAD_LAG_V1"
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


def test_primary_statistical_contract_matches_parent_v1():
    assert experiment.MIN_ROWS_PER_LEAGUE == 40
    assert experiment.PERMUTATION_DRAWS == 10000
    assert experiment.BOOTSTRAP_DRAWS == 10000
    assert experiment.RANDOM_SEED == 20261004
    assert experiment.CLOSING_1X2_COLUMNS == (
        "B365CH",
        "B365CD",
        "B365CA",
    )


def test_outcome_columns_are_forbidden():
    assert {"FTR", "FTHG", "FTAG"}.issubset(experiment.OUTCOME_COLUMNS)


def test_permutation_detects_perfect_match_specific_alignment():
    rows = []
    for league in experiment.LEAGUE_IDS:
        for index in range(50):
            sign = 1.0 if index % 2 == 0 else -1.0
            lead = np.array([0.02 * sign, -0.01 * sign, -0.01 * sign])
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


def test_bootstrap_positive_alignment_has_positive_ci():
    frame = pd.DataFrame(
        [
            {"league": league, "alignment_dot": 0.001}
            for league in experiment.LEAGUE_IDS
            for _ in range(50)
        ]
    )
    report = experiment._bootstrap_mean_alignment(frame)
    assert report["ci95_low"] > 0.0


def test_split_report_requires_both_frozen_leagues():
    frame = pd.DataFrame([_row("BUNDESLIGA") for _ in range(50)])
    with pytest.raises(RuntimeError, match="missing a frozen league"):
        experiment._split_report(frame, experiment.VALIDATION_SEASON)


def test_split_report_marks_sample_gate_false_below_40():
    rows = []
    rows.extend(_row("BUNDESLIGA") for _ in range(39))
    rows.extend(_row("LIGUE_1") for _ in range(50))
    report = experiment._split_report(
        pd.DataFrame(rows),
        experiment.VALIDATION_SEASON,
    )
    assert report["rows_ok"] is False
    assert report["by_league"]["BUNDESLIGA"]["rows"] == 39


def test_replication_requires_both_leagues_positive():
    rows = []
    rows.extend(_row("BUNDESLIGA", 0.001) for _ in range(50))
    rows.extend(_row("LIGUE_1", -0.001) for _ in range(50))
    report = experiment._split_report(
        pd.DataFrame(rows),
        experiment.VALIDATION_SEASON,
    )
    assert report["positive_mean_alignment_leagues"] == 1


def test_transport_is_restricted_to_preregistered_d1_f1_seasons():
    assert len(transport._BLOB_SHAS) == 14
    assert set(comp for comp, _ in transport._BLOB_SHAS) == {"D1", "F1"}
    assert transport._MIRROR_COMMIT == (
        "97c22f31564baafbd18ef818bb2df9fcb49319bc"
    )
    assert transport._mirror_spec(
        "https://www.football-data.co.uk/mmz4281/2526/D1.csv"
    ).blob_sha == "e8b2bffe7a16a794feb6985fe5ea50dcdd2f4137"


def test_transport_rejects_unregistered_league_or_season():
    with pytest.raises(RuntimeError, match="unexpected historical source URL"):
        transport._mirror_spec(
            "https://www.football-data.co.uk/mmz4281/2627/D1.csv"
        )
    with pytest.raises(RuntimeError, match="unexpected historical source URL"):
        transport._mirror_spec(
            "https://www.football-data.co.uk/mmz4281/2526/E0.csv"
        )
