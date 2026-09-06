import pandas as pd
import pytest

import audit_league_canonical_data_quality as audit


def ledger_frame(*, league="EPL", kickoff="2026-08-01T14:00:00Z", home="Alpha", away="Beta"):
    return pd.DataFrame([
        {
            "league": league, "event_id": "event-1", "home_team": home, "away_team": away,
            "kickoff_utc": kickoff, "snapshot_time_utc": "2026-08-01T13:00:00Z" if league == "EPL" else "2026-08-30T08:00:00Z",
            "market_home_prob": 0.60, "market_draw_prob": 0.25, "market_away_prob": 0.15,
            "market_pick": "H", "prediction_mode": "MARKET_ONLY", "structural_applied": False,
        }
    ])


def result_frame():
    return pd.DataFrame([
        {"league": "EPL", "match_date": "2026-08-01", "home_team": "Alpha", "away_team": "Beta", "result": "H"}
    ])


def la_liga_ledger():
    return ledger_frame(
        league="LA_LIGA",
        kickoff="2026-08-30T18:00:00Z",
        home="Real Madrid",
        away="Málaga",
    )


def test_clean_canonical_state_has_no_critical_failures():
    report = audit.audit_frames("EPL", ledger_frame(), result_frame())
    assert report.settled_fixtures == 1
    assert report.duplicate_prediction_rows == 0
    assert report.duplicate_result_identities == 0
    assert report.alias_duplicate_result_rows == 0
    assert report.post_ledger_alias_duplicate_result_rows == 0
    assert report.alias_conflicting_result_rows == 0
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


def test_pre_ledger_la_liga_alias_duplicates_are_visible_legacy_warning():
    results = pd.DataFrame([
        {"league": "LA_LIGA", "match_date": "2026-08-15", "home_team": "Alaves", "away_team": "Getafe", "result": "H"},
        {"league": "LA_LIGA", "match_date": "2026-08-15", "home_team": "Alavés", "away_team": "Getafe", "result": "H"},
        {"league": "LA_LIGA", "match_date": "2026-08-16", "home_team": "Espanol", "away_team": "Levante", "result": "H"},
        {"league": "LA_LIGA", "match_date": "2026-08-16", "home_team": "Espanyol", "away_team": "Levante", "result": "H"},
        {"league": "LA_LIGA", "match_date": "2026-08-20", "home_team": "Vallecano", "away_team": "Alaves", "result": "D"},
        {"league": "LA_LIGA", "match_date": "2026-08-20", "home_team": "Rayo Vallecano", "away_team": "Alavés", "result": "D"},
    ])

    report = audit.audit_frames("LA_LIGA", la_liga_ledger(), results)

    assert report.alias_duplicate_result_rows == 6
    assert report.pre_ledger_alias_duplicate_result_rows == 6
    assert report.post_ledger_alias_duplicate_result_rows == 0
    assert report.alias_conflicting_result_rows == 0
    assert report.critical_failures == 0


def test_post_ledger_la_liga_alias_duplicate_is_critical():
    ledger = la_liga_ledger()
    results = pd.DataFrame([
        {"league": "LA_LIGA", "match_date": "2026-08-31", "home_team": "Alaves", "away_team": "Getafe", "result": "H"},
        {"league": "LA_LIGA", "match_date": "2026-08-31", "home_team": "Alavés", "away_team": "Getafe", "result": "H"},
    ])

    report = audit.audit_frames("LA_LIGA", ledger, results)

    assert report.alias_duplicate_result_rows == 2
    assert report.pre_ledger_alias_duplicate_result_rows == 0
    assert report.post_ledger_alias_duplicate_result_rows == 2
    assert report.critical_failures == 2


def test_conflicting_pre_ledger_alias_duplicate_is_critical():
    results = pd.DataFrame([
        {"league": "LA_LIGA", "match_date": "2026-08-15", "home_team": "Espanol", "away_team": "Levante", "result": "H"},
        {"league": "LA_LIGA", "match_date": "2026-08-15", "home_team": "Espanyol", "away_team": "Levante", "result": "D"},
    ])

    report = audit.audit_frames("LA_LIGA", la_liga_ledger(), results)

    assert report.alias_conflicting_result_rows == 2
    assert report.critical_failures == 2


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
