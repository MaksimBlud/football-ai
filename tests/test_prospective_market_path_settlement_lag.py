import pandas as pd

from prospective_market_path_settlement_lag import (
    SETTLEMENT_GRACE_HOURS,
    STATUS_AWAITING,
    STATUS_LATE,
    STATUS_PRESENT,
    audit_settlement_lag,
    summarize_settlement_lag,
)


def _path(kickoff="2026-09-12T18:00:00Z", event_id="e1", league="EPL"):
    return {
        "league": league,
        "event_id": event_id,
        "home_team": "Arsenal",
        "away_team": "Chelsea",
        "kickoff_utc": kickoff,
    }


def _identity(match_date="2026-09-12", league="EPL"):
    return {
        "league": league,
        "match_date": match_date,
        "home_team": "Arsenal",
        "away_team": "Chelsea",
    }


def test_result_identity_present_is_settled_without_result_value_column():
    paths = pd.DataFrame([_path()])
    results = pd.DataFrame([_identity()])
    audit = audit_settlement_lag(paths, results, now_utc=pd.Timestamp("2026-09-14T00:00:00Z"))
    assert audit.iloc[0].status == STATUS_PRESENT
    assert "result" not in results.columns


def test_missing_identity_within_eighteen_hour_grace_is_not_late():
    paths = pd.DataFrame([_path()])
    results = pd.DataFrame(columns=["league", "match_date", "home_team", "away_team"])
    now = pd.Timestamp("2026-09-13T10:00:00Z")
    assert (now - pd.Timestamp("2026-09-12T18:00:00Z")).total_seconds() / 3600 < SETTLEMENT_GRACE_HOURS
    audit = audit_settlement_lag(paths, results, now_utc=now)
    assert audit.iloc[0].status == STATUS_AWAITING


def test_missing_identity_after_grace_is_late():
    paths = pd.DataFrame([_path()])
    results = pd.DataFrame(columns=["league", "match_date", "home_team", "away_team"])
    audit = audit_settlement_lag(paths, results, now_utc=pd.Timestamp("2026-09-13T13:00:00Z"))
    assert audit.iloc[0].status == STATUS_LATE


def test_league_local_date_is_used_for_canonical_identity():
    paths = pd.DataFrame([_path(kickoff="2026-09-12T23:30:00Z", league="LA_LIGA")])
    results = pd.DataFrame([_identity(match_date="2026-09-13", league="LA_LIGA")])
    audit = audit_settlement_lag(paths, results, now_utc=pd.Timestamp("2026-09-14T20:00:00Z"))
    assert audit.iloc[0].status == STATUS_PRESENT


def test_ambiguous_provider_revisions_are_excluded_from_lag_alarm():
    paths = pd.DataFrame([
        _path(event_id="old"),
        _path(event_id="new"),
    ])
    results = pd.DataFrame(columns=["league", "match_date", "home_team", "away_team"])
    audit = audit_settlement_lag(paths, results, now_utc=pd.Timestamp("2026-09-14T00:00:00Z"))
    assert audit.empty


def test_summary_preserves_all_three_research_leagues():
    audit = pd.DataFrame([{"league": "EPL", "status": STATUS_LATE}])
    summary = summarize_settlement_lag(audit)
    assert summary["league"].tolist() == ["EPL", "LA_LIGA", "SERIE_A"]
    assert summary.loc[summary["league"] == "EPL", "settlement_late"].iloc[0] == 1
