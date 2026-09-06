import pandas as pd
import pytest

import evaluate_league_predictions as evaluator


def _ledger():
    return pd.DataFrame([
        {
            "league": "EPL",
            "event_id": "brighton-leeds",
            "home_team": "Brighton",
            "away_team": "Leeds",
            "kickoff_utc": "2026-09-05T14:00:00Z",
            "snapshot_time_utc": "2026-09-05T10:00:00Z",
            "market_home_prob": 0.50,
            "market_draw_prob": 0.30,
            "market_away_prob": 0.20,
            "market_pick": "H",
            "prediction_mode": "MARKET_ONLY",
            "structural_applied": False,
        }
    ])


def _results(second_result="D"):
    return pd.DataFrame([
        {
            "league": "EPL",
            "match_date": "2026-09-05",
            "home_team": "Brighton",
            "away_team": "Leeds",
            "result": "D",
        },
        {
            "league": "EPL",
            "match_date": "2026-09-05",
            "home_team": "Brighton Hove",
            "away_team": "Leeds",
            "result": second_result,
        },
    ])


def test_alias_duplicate_results_with_same_outcome_settle_once():
    settled = evaluator.settle_predictions(_ledger(), _results(), league="EPL")

    assert len(settled) == 1
    assert settled.iloc[0]["actual_result"] == "D"


def test_alias_duplicate_results_with_conflicting_outcomes_fail_closed():
    with pytest.raises(ValueError, match="Conflicting finished-result fixture identity"):
        evaluator.settle_predictions(_ledger(), _results("H"), league="EPL")
