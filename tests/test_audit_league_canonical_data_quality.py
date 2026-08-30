import pandas as pd
import pytest

import audit_league_canonical_data_quality as audit


def ledger_frame():
    return pd.DataFrame([
        {
            "league": "EPL", "event_id": "event-1", "home_team": "Alpha", "away_team": "Beta",
            "kickoff_utc": "2026-08-01T14:00:00Z", "snapshot_time_utc": "2026-08-01T13:00:00Z",
            "market_home_prob": 0.60, "market_draw_prob": 0.25, "market_away_prob": 0.15,
            "market_pick": "H", "prediction_mode": "MARKET_ONLY", "structural_applied": False,
        }
    ])


def result_frame():
    return pd.DataFrame([
        {"league": "EPL", "match_date": "2026-08-01", "home_team": "Alpha", "away_team": "Beta", "result": "H"}
    ])


def test_clean_canonical_state_has_no_critical_failures():
    report = audit.audit_frames("EPL", ledger_frame(), result_frame())
    assert report.settled_fixtures == 1
    assert report.duplicate_prediction_rows == 0
    assert report.duplicate_result_identities == 0
    assert report.missing_event_ids == 0
    assert report.unlinked_finished_results == 0
    assert report.critical_failures == 0


def test_duplicate_prediction_identity_is_reported():
    ledger = pd.concat([ledger_frame(), ledger_frame()], ignore_index=True)
    report = audit.audit_frames("EPL", ledger, result_frame())
    assert report.duplicate_prediction_rows == 2
    assert report.critical_failures == 2


def test_unlinked_finished_result_is_diagnostic_not_critical():
    results = pd.concat([
        result_frame(),
        pd.DataFrame([{"league": "EPL", "match_date": "2026-08-02", "home_team": "Gamma", "away_team": "Delta", "result": "D"}]),
    ], ignore_index=True)
    report = audit.audit_frames("EPL", ledger_frame(), results)
    assert report.unlinked_finished_results == 1
    assert report.critical_failures == 0


def test_post_kickoff_prediction_fails_closed():
    ledger = ledger_frame()
    ledger.loc[0, "snapshot_time_utc"] = "2026-08-01T15:00:00Z"
    with pytest.raises(ValueError, match="non-pre-kickoff"):
        audit.audit_frames("EPL", ledger, result_frame())


def test_foreign_league_row_fails_closed():
    ledger = ledger_frame()
    ledger.loc[0, "league"] = "SERIE_A"
    with pytest.raises(ValueError, match="foreign league"):
        audit.audit_frames("EPL", ledger, result_frame())


def test_source_is_read_only_and_model_free():
    source = open("audit_league_canonical_data_quality.py", encoding="utf-8").read()
    forbidden = [
        ".insert(", ".upsert(", ".update(", ".delete(",
        "joblib.load", "football_model_xgboost_elo", "train_model",
    ]
    for token in forbidden:
        assert token not in source
