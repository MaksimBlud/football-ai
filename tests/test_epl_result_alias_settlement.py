import pandas as pd

import evaluate_league_predictions as evaluator


def _ledger(home_team: str, away_team: str, event_id: str) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "league": "EPL",
            "event_id": event_id,
            "home_team": home_team,
            "away_team": away_team,
            "kickoff_utc": "2026-09-05T14:00:00Z",
            "snapshot_time_utc": "2026-09-05T10:00:00Z",
            "market_home_prob": 0.40,
            "market_draw_prob": 0.35,
            "market_away_prob": 0.25,
            "market_pick": "H",
            "prediction_mode": "MARKET_ONLY",
            "structural_applied": False,
        }
    ])


def _result(home_team: str, away_team: str) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "league": "EPL",
            "match_date": "2026-09-05",
            "home_team": home_team,
            "away_team": away_team,
            "result": "D",
        }
    ])


def test_nottingham_result_alias_settles_against_market_identity():
    settled = evaluator.settle_predictions(
        _ledger("Nottingham Forest", "Tottenham Hotspur", "forest-spurs"),
        _result("Nottingham", "Tottenham"),
        league="EPL",
    )

    assert len(settled) == 1
    assert settled.iloc[0]["event_id"] == "forest-spurs"
    assert settled.iloc[0]["actual_result"] == "D"


def test_brighton_hove_result_alias_settles_against_market_identity():
    settled = evaluator.settle_predictions(
        _ledger("Brighton and Hove Albion", "Leeds United", "brighton-leeds"),
        _result("Brighton Hove", "Leeds"),
        league="EPL",
    )

    assert len(settled) == 1
    assert settled.iloc[0]["event_id"] == "brighton-leeds"
    assert settled.iloc[0]["actual_result"] == "D"
