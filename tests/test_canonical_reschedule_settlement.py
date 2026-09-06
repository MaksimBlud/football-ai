import pandas as pd

import evaluate_league_predictions as evaluator


def _row(*, kickoff: str, snapshot: str, event_id: str = "event-1") -> dict:
    return {
        "league": "LA_LIGA",
        "event_id": event_id,
        "home_team": "Alpha",
        "away_team": "Beta",
        "kickoff_utc": kickoff,
        "snapshot_time_utc": snapshot,
        "market_home_prob": 0.50,
        "market_draw_prob": 0.30,
        "market_away_prob": 0.20,
        "market_pick": "H",
        "prediction_mode": "MARKET_ONLY",
        "structural_applied": False,
    }


def _result() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "league": "LA_LIGA",
            "match_date": "2026-09-13",
            "home_team": "Alpha",
            "away_team": "Beta",
            "result": "H",
        }
    ])


def test_rescheduled_event_id_is_excluded_from_automatic_settlement():
    ledger = pd.DataFrame([
        _row(kickoff="2026-09-13T12:00:00Z", snapshot="2026-09-05T10:00:00Z"),
        _row(kickoff="2026-09-13T19:00:00Z", snapshot="2026-09-06T10:00:00Z"),
    ])

    validated = evaluator._validate_ledger(ledger)
    assert evaluator.ambiguous_event_ids(validated) == {"event-1"}

    settled = evaluator.settle_predictions(ledger, _result(), league="LA_LIGA")
    assert settled.empty


def test_repeated_snapshots_for_one_fixture_identity_remain_eligible():
    ledger = pd.DataFrame([
        _row(kickoff="2026-09-13T19:00:00Z", snapshot="2026-09-05T10:00:00Z"),
        _row(kickoff="2026-09-13T19:00:00Z", snapshot="2026-09-06T10:00:00Z"),
    ])

    validated = evaluator._validate_ledger(ledger)
    assert evaluator.ambiguous_event_ids(validated) == set()

    settled = evaluator.settle_predictions(ledger, _result(), league="LA_LIGA")
    latest = evaluator.latest_pre_kickoff(settled)
    assert len(settled) == 2
    assert len(latest) == 1
    assert latest.iloc[0]["snapshot_time_utc"] == pd.Timestamp("2026-09-06T10:00:00Z")
