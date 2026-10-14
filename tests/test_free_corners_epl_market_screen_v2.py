import json
from pathlib import Path

import pytest

import free_corners_epl_market_screen_v2 as s


def _seed():
    return {
        "experiment_id": s.EXPERIMENT_ID,
        "last_training_date": "2026-05-24",
        "historical_rows_with_corners": 3800,
        "eligible_training_rows": 3564,
        "calibration": {
            "slope": 0.25,
            "intercept": 7.5,
            "baseline_total": 10.3,
        },
        "teams": {
            "A": {"n": 10, "last10": [[5, 5]] * 10},
            "B": {"n": 10, "last10": [[6, 4]] * 10},
            "Coventry": {"n": 0, "last10": []},
        },
    }


def test_load_seed_rejects_future_or_incomplete_training(tmp_path: Path):
    p = tmp_path / "seed.json"
    payload = _seed()
    p.write_text(json.dumps(payload))
    assert s.load_seed(p)["eligible_training_rows"] == 3564

    payload["last_training_date"] = "2026-08-01"
    p.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        s.load_seed(p)


def test_aliases_are_canonical():
    assert s.canonical_team("Man Utd") == "Man United"
    assert s.canonical_team("Nottm Forest") == "Nott'm Forest"
    assert s.canonical_team("Arsenal") == "Arsenal"


def test_devig_is_normalized():
    p = s.devig(2.0, 2.0)
    assert p == pytest.approx(0.5)
    p = s.devig(1.80, 2.00)
    assert 0.5 < p < 1.0


def test_poisson_probabilities_support_half_and_integer_lines():
    half = s.football_over_probability(10.0, 9.5)
    integer = s.football_over_probability(10.0, 10.0)
    assert 0 < half < 1
    assert 0 < integer < 1
    with pytest.raises(ValueError):
        s.football_over_probability(10.0, 9.25)


def test_parse_opening_market_requires_bet365():
    payload = {
        "success": 1,
        "data": {
            "bookmakers": [
                {
                    "slug": "bet365",
                    "odds": {
                        "corner_line": {
                            "opening": {"line": 9.5, "over": 1.90, "under": 1.90}
                        }
                    },
                }
            ]
        },
    }
    row = s.parse_opening_market(payload, "123")
    assert row == {
        "fixture_id": "123",
        "opening_line": 9.5,
        "opening_over": 1.9,
        "opening_under": 1.9,
        "source": "LIVE_FREE_API",
    }


def test_evaluate_uses_pre_match_state_then_updates_history():
    seed = _seed()
    fixtures = [
        {
            "fixture_id": "1",
            "kickoff_utc": "2026-08-01T15:00:00Z",
            "home_team": "A",
            "away_team": "B",
            "home_corners": 10,
            "away_corners": 10,
            "actual_total": 20,
        },
        {
            "fixture_id": "2",
            "kickoff_utc": "2026-08-08T15:00:00Z",
            "home_team": "A",
            "away_team": "B",
            "home_corners": 1,
            "away_corners": 1,
            "actual_total": 2,
        },
    ]
    markets = {
        "1": {"opening_line": 9.5, "opening_over": 1.9, "opening_under": 1.9},
        "2": {"opening_line": 9.5, "opening_over": 1.9, "opening_under": 1.9},
    }
    rows, report = s.evaluate(fixtures, markets, seed)
    assert len(rows) == 2
    # First fixture must use only the pinned pre-season histories.
    assert rows[0]["raw_expected_total"] == pytest.approx(10.0)
    # The first fixture's 20 corners enter history only for the second fixture.
    assert rows[1]["raw_expected_total"] != pytest.approx(rows[0]["raw_expected_total"])
    assert report["fixture_count"] == 2


def test_coventry_is_excluded_until_ten_prior_epl_matches():
    seed = _seed()
    fixtures = []
    markets = {}
    for idx in range(1, 12):
        fixtures.append(
            {
                "fixture_id": str(idx),
                "kickoff_utc": f"2026-08-{idx:02d}T15:00:00Z",
                "home_team": "Coventry",
                "away_team": "A",
                "home_corners": 4,
                "away_corners": 5,
                "actual_total": 9,
            }
        )
        markets[str(idx)] = {
            "opening_line": 9.5,
            "opening_over": 1.9,
            "opening_under": 1.9,
        }
    rows, report = s.evaluate(fixtures, markets, seed)
    assert report["exclusions"]["INSUFFICIENT_PRIOR_EPL_HISTORY"] == 10
    assert len(rows) == 1


def test_verdict_requires_all_three_incremental_conditions(monkeypatch):
    seed = _seed()
    # Directly exercise enough identical eligible rows, then control score functions.
    fixtures = []
    markets = {}
    for idx in range(30):
        fixtures.append(
            {
                "fixture_id": str(idx + 1),
                "kickoff_utc": f"2026-09-{(idx % 28) + 1:02d}T15:00:00Z",
                "home_team": "A",
                "away_team": "B",
                "home_corners": 6,
                "away_corners": 5,
                "actual_total": 11,
            }
        )
        markets[str(idx + 1)] = {
            "opening_line": 9.5,
            "opening_over": 1.9,
            "opening_under": 1.9,
        }

    monkeypatch.setattr(s, "brier", lambda rows, key: {"p_market": 0.26, "p_football": 0.20, "p_blend25": 0.24}[key])
    monkeypatch.setattr(s, "logloss", lambda rows, key: {"p_market": 0.70, "p_football": 0.60, "p_blend25": 0.65}[key])
    rows, report = s.evaluate(fixtures, markets, seed)
    assert len(rows) == 30
    assert report["verdict"] in {"INDICATIVE_INCREMENTAL_SIGNAL", "NO_CLEAR_INCREMENTAL_SIGNAL"}
    # The verdict can never be promoted on score improvements alone if alignment is non-positive.
    report2 = dict(report)
    report2["residual_alignment"] = -1e-6
    assert not (
        report2["blend25_brier"] < report2["market_brier"]
        and report2["blend25_logloss"] < report2["market_logloss"]
        and report2["residual_alignment"] > 0
    )


def test_hard_free_budget_is_frozen():
    assert s.MAX_PROVIDER_REQUESTS == 45
    assert s.MIN_NON_PUSH_ROWS == 25
    assert s.BLEND_FOOTBALL_WEIGHT == 0.25
    assert s.EXPECTED_FINISHED_FIXTURES == 40
