import pandas as pd
import pytest

import v2b_corners10_direction_hypothesis_v1 as audit


def _history_row(date, home_key, away_key, hc, ac):
    return {
        "match_date": pd.Timestamp(date),
        "home_key": home_key,
        "away_key": away_key,
        "HC": hc,
        "AC": ac,
    }


def test_team_last10_uses_only_prior_rows_and_correct_role():
    rows = []
    for i in range(12):
        if i % 2 == 0:
            rows.append(_history_row(f"2026-08-{i+1:02d}", "a", f"x{i}", 6+i, 3))
        else:
            rows.append(_history_row(f"2026-08-{i+1:02d}", f"x{i}", "a", 4, 5+i))
    rows.append(_history_row("2026-09-19", "a", "target", 99, 99))
    history = pd.DataFrame(rows).sort_values("match_date")

    corners_for, corners_against, n = audit._team_last10(
        history,
        team_key="a",
        target_date=pd.Timestamp("2026-09-19"),
    )

    expected = history.iloc[2:12]
    ef, ea = [], []
    for row in expected.itertuples(index=False):
        if row.home_key == "a":
            ef.append(float(row.HC)); ea.append(float(row.AC))
        else:
            ef.append(float(row.AC)); ea.append(float(row.HC))

    assert n == 10
    assert corners_for == pytest.approx(sum(ef) / 10)
    assert corners_against == pytest.approx(sum(ea) / 10)
    assert corners_for < 99
    assert corners_against < 99


def test_scalar_total_formula_is_symmetric():
    home_for = 6.0
    home_against = 4.0
    away_for = 5.0
    away_against = 5.0
    home_expected = 0.5 * (home_for + away_against)
    away_expected = 0.5 * (away_for + home_against)
    total = home_expected + away_expected
    assert total == pytest.approx(
        0.5 * (home_for + home_against + away_for + away_against)
    )
    assert total == pytest.approx(10.0)


def test_validate_feasibility_freezes_exact_eligible_subset(monkeypatch):
    monkeypatch.setattr(audit, "EXPECTED_LOCKED", 2)
    monkeypatch.setattr(audit, "EXPECTED_FEASIBLE", 1)
    report = {
        "experiment_id": audit.feasibility.EXPERIMENT_ID,
        "status": "PARTIAL_REPLAY_FEASIBLE",
        "locked_fixture_count": 2,
        "matched_fixture_count": 2,
        "corners10_feasible_fixture_count": 1,
        "direction_test_performed": False,
        "v2b_odds_read": False,
        "rows": [
            {
                "fixture_id": "1",
                "league": "EPL",
                "kickoff_date": "2026-09-19",
                "canonical_home_team": "A",
                "canonical_away_team": "B",
                "source_identity_status": "MATCHED",
                "both_teams_have_corners10": True,
            },
            {
                "fixture_id": "2",
                "league": "EPL",
                "kickoff_date": "2026-09-19",
                "canonical_home_team": "C",
                "canonical_away_team": "D",
                "source_identity_status": "MATCHED",
                "both_teams_have_corners10": False,
            },
        ],
    }
    eligible = audit._validate_feasibility(report)
    assert eligible["fixture_id"].tolist() == ["1"]


def test_evaluate_uses_fixed_sign_rule_without_threshold_search(monkeypatch):
    monkeypatch.setattr(audit, "EXPECTED_LOCKED", 4)
    monkeypatch.setattr(audit, "EXPECTED_FEASIBLE", 4)

    feasibility_report = {
        "experiment_id": audit.feasibility.EXPERIMENT_ID,
        "status": "PARTIAL_REPLAY_FEASIBLE",
        "locked_fixture_count": 4,
        "matched_fixture_count": 4,
        "corners10_feasible_fixture_count": 4,
        "direction_test_performed": False,
        "v2b_odds_read": False,
        "rows": [
            {
                "fixture_id": str(i),
                "league": "EPL",
                "kickoff_date": "2026-09-19",
                "canonical_home_team": f"H{i}",
                "canonical_away_team": f"A{i}",
                "source_identity_status": "MATCHED",
                "both_teams_have_corners10": True,
            }
            for i in range(1, 5)
        ],
    }

    corners = pd.DataFrame(
        [
            {"fixture_id": "1", "league": "EPL", "kickoff_date": "2026-09-19", "corners10_total": 11.0},
            {"fixture_id": "2", "league": "EPL", "kickoff_date": "2026-09-19", "corners10_total": 8.0},
            {"fixture_id": "3", "league": "EPL", "kickoff_date": "2026-09-19", "corners10_total": 12.0},
            {"fixture_id": "4", "league": "EPL", "kickoff_date": "2026-09-19", "corners10_total": 7.0},
        ]
    )
    for col in (
        "home_corners_for_10", "home_corners_against_10",
        "away_corners_for_10", "away_corners_against_10",
        "home_expected_corners", "away_expected_corners",
    ):
        corners[col] = 5.0

    monkeypatch.setattr(audit, "build_corners10_rows", lambda eligible, histories: corners)

    market = pd.DataFrame(
        [
            {"fixture_id": "1", "league": "EPL", "opening_lambda": 10.0, "centre_delta": 0.4},
            {"fixture_id": "2", "league": "EPL", "opening_lambda": 9.0, "centre_delta": -0.2},
            {"fixture_id": "3", "league": "EPL", "opening_lambda": 10.0, "centre_delta": -0.3},
            {"fixture_id": "4", "league": "EPL", "opening_lambda": 8.0, "centre_delta": 0.0},
        ]
    )

    rows, report = audit.evaluate(feasibility_report, market, {})
    assert rows["football_gap"].tolist() == pytest.approx([1.0, -1.0, 2.0, -1.0])
    assert report["comparable_rows"] == 3
    assert report["concordant_rows"] == 2
    assert report["pooled_concordance"] == pytest.approx(2 / 3)
    assert report["zero_observed_movement_rows"] == 1


def test_no_confirmatory_or_provider_odds_behavior_exposed():
    assert audit.EXPERIMENT_ID == "V2B_CORNERS10_DIRECTION_HYPOTHESIS_V1"
    assert audit.EXPECTED_LOCKED == 43
    assert audit.EXPECTED_FEASIBLE == 31
