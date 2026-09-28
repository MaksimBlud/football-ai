from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import v2b_result_strength_trajectory_freeze_v1 as mod


def _feasibility():
    rows = []
    plan = {
        "EPL": (6, 3),
        "LA_LIGA": (9, 0),
        "SERIE_A": (7, 2),
        "BUNDESLIGA": (6, 2),
        "LIGUE_1": (6, 2),
    }
    fixture = 0
    for league, (eligible, ineligible) in plan.items():
        for _ in range(eligible):
            fixture += 1
            rows.append(
                {
                    "fixture_id": str(fixture),
                    "league": league,
                    "source_identity_status": "MATCHED",
                    "home_prior_top_flight_corner_matches": 5,
                    "away_prior_top_flight_corner_matches": 6,
                }
            )
        for _ in range(ineligible):
            fixture += 1
            rows.append(
                {
                    "fixture_id": str(fixture),
                    "league": league,
                    "source_identity_status": "MATCHED",
                    "home_prior_top_flight_corner_matches": 4,
                    "away_prior_top_flight_corner_matches": 20,
                }
            )
    return {
        "experiment_id": mod.EXPECTED_FEASIBILITY_EXPERIMENT,
        "research_only": True,
        "direction_test_performed": False,
        "v2b_odds_read": False,
        "locked_fixture_count": 43,
        "rows": rows,
    }


def test_five_match_eligibility_is_frozen_at_34():
    eligible = mod._validate_feasibility(_feasibility())
    assert len(eligible) == 34
    by_league = {
        league: sum(row["league"] == league for row in eligible)
        for league in mod.EXPECTED_BY_LEAGUE
    }
    assert by_league == mod.EXPECTED_BY_LEAGUE


@pytest.mark.parametrize(
    ("home", "away", "score", "call"),
    [
        (0.2, 0.1, 0.3, "UP"),
        (-0.2, -0.1, -0.3, "DOWN"),
        (0.2, -0.2, 0.0, "NO_CALL"),
    ],
)
def test_stage_b_mapping_is_fixed_sign_of_joint_residual(home, away, score, call):
    observed_score, observed_call = mod.stage_b_mapping(home, away)
    assert observed_score == pytest.approx(score)
    assert observed_call == call


def test_trajectory_snapshot_does_not_depend_on_target_result():
    base = pd.DataFrame(
        [
            ("X", "2026-01-01", "A", "B", "H"),
            ("X", "2026-01-02", "C", "A", "A"),
            ("X", "2026-01-03", "A", "D", "D"),
            ("X", "2026-01-04", "E", "A", "H"),
            ("X", "2026-01-05", "A", "F", "H"),
            ("X", "2026-01-06", "B", "C", "D"),
            ("X", "2026-01-07", "D", "E", "A"),
            ("X", "2026-01-08", "F", "B", "H"),
            ("X", "2026-01-09", "C", "D", "H"),
            ("X", "2026-01-10", "E", "F", "D"),
            ("X", "2026-01-11", "A", "B", "H"),
        ],
        columns=["league", "match_date", "home_team", "away_team", "result"],
    )
    base["match_date"] = pd.to_datetime(base["match_date"])

    first = mod.add_team_strength_trajectory(base.copy())
    changed = base.copy()
    changed.loc[10, "result"] = "A"
    second = mod.add_team_strength_trajectory(changed)

    cols = [
        "home_elo_level",
        "away_elo_level",
        "home_elo_delta_5",
        "away_elo_delta_5",
        "home_performance_residual_5",
        "away_performance_residual_5",
    ]
    for col in cols:
        left = first.loc[10, col]
        right = second.loc[10, col]
        if pd.isna(left) or pd.isna(right):
            assert pd.isna(left) and pd.isna(right)
        else:
            assert left == pytest.approx(right)


def test_preregistration_forbids_market_direction_inputs():
    source = Path("v2b_result_strength_trajectory_freeze_v1.py").read_text(
        encoding="utf-8"
    )
    assert '"direction_test_performed": False' in source
    assert '"v2b_odds_read": False' in source
    assert '"opening_lambda_read": False' in source
    assert '"centre_delta_read": False' in source
