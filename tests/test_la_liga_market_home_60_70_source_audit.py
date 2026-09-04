import pandas as pd
import pytest

from la_liga_market_home_60_70_source_audit import audit_recent_source_contract


def _rows():
    ledger = pd.DataFrame([
        {
            "prediction_key": "p1",
            "league": "LA_LIGA",
            "event_id": "e1",
            "home_team": "Home",
            "away_team": "Away",
            "kickoff_utc": "2026-09-05T18:00:00Z",
            "snapshot_time_utc": "2026-09-04T16:00:00Z",
            "market_home_prob": 0.60,
            "market_draw_prob": 0.25,
            "market_away_prob": 0.15,
            "prediction_mode": "MARKET_ONLY",
        }
    ])
    odds = pd.DataFrame([
        {
            "league": "LA_LIGA",
            "event_id": "e1",
            "home_team": "Home",
            "away_team": "Away",
            "commence_time_utc": "2026-09-05T18:00:00Z",
            "snapshot_time_utc": "2026-09-04T16:00:00Z",
            "home_odds": 1 / 0.60,
            "draw_odds": 1 / 0.25,
            "away_odds": 1 / 0.15,
        }
    ])
    return ledger, odds


def test_source_contract_passes_without_outcomes():
    ledger, odds = _rows()
    audit = audit_recent_source_contract(ledger, odds)
    assert audit["status"] == "PASS"
    assert audit["checked_rows"] == 1
    assert audit["outcomes_queried"] is False
    assert audit["prospective_rows_used"] is False


def test_source_contract_fails_on_missing_exact_snapshot():
    ledger, odds = _rows()
    odds["snapshot_time_utc"] = "2026-09-04T15:59:00Z"
    with pytest.raises(RuntimeError, match="MISSING_RAW_ROWS"):
        audit_recent_source_contract(ledger, odds)


def test_source_contract_rejects_probability_mismatch():
    ledger, odds = _rows()
    odds.loc[0, "home_odds"] = 2.5
    with pytest.raises(RuntimeError, match="PROBABILITY_MISMATCH"):
        audit_recent_source_contract(ledger, odds)
