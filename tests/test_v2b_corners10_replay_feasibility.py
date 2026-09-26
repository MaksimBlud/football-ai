import pandas as pd

import v2b_corners10_replay_feasibility as audit
from league_runtime_config import EPL_RUNTIME_CONFIG


def _row(date, home, away, hc=5, ac=4):
    return {
        "Date": date,
        "HomeTeam": home,
        "AwayTeam": away,
        "FTR": "H",
        "FTHG": 2,
        "FTAG": 1,
        "HC": hc,
        "AC": ac,
    }


def _lock_row(home, away, kickoff="2026-09-19T14:00:00+00:00"):
    return {
        "fixture_id": "1",
        "league": "EPL",
        "kickoff_utc": kickoff,
        "home_team": home,
        "away_team": away,
    }


def test_locked_identity_aliases_are_deterministic():
    assert audit._canonical_lock_team("Man Utd", "EPL") == "Man United"
    assert audit._canonical_lock_team("Nottm Forest", "EPL") == "Nott'm Forest"
    assert audit._canonical_lock_team("Athletic Club", "LA_LIGA") == "Athletic Bilbao"
    assert audit._canonical_lock_team("Atletico Madrid", "LA_LIGA") == "Atlético Madrid"
    assert audit._canonical_lock_team("Roma", "SERIE_A") == "AS Roma"
    assert audit._canonical_lock_team("Borussia Dortmund", "BUNDESLIGA") == "Dortmund"
    assert audit._canonical_lock_team("PSG", "LIGUE_1") == "Paris SG"


def test_continuous_previous_season_history_makes_corners10_feasible(monkeypatch):
    monkeypatch.setattr(audit, "CONFIGS", {"EPL": EPL_RUNTIME_CONFIG})
    monkeypatch.setattr(audit, "EXPECTED_LOCKED_FIXTURES", 1)
    monkeypatch.setattr(audit, "_validate_lock", lambda lock: [_lock_row("Tottenham", "Aston Villa")])

    previous = []
    for i in range(10):
        previous.append(_row(f"{1+i:02d}/05/2026", "Tottenham", f"X{i}"))
        previous.append(_row(f"{1+i:02d}/05/2026", f"Y{i}", "Aston Villa"))
    current = [_row("19/09/2026", "Tottenham", "Aston Villa")]

    report = audit.audit_from_frames(
        {},
        {
            ("EPL", audit.PREVIOUS_SEASON): pd.DataFrame(previous),
            ("EPL", audit.CURRENT_SEASON): pd.DataFrame(current),
        },
    )

    assert report["status"] == "FULL_43_REPLAY_FEASIBLE"
    assert report["matched_fixture_count"] == 1
    assert report["corners10_feasible_fixture_count"] == 1
    row = report["rows"][0]
    assert row["home_prior_top_flight_corner_matches"] == 10
    assert row["away_prior_top_flight_corner_matches"] == 10
    assert row["both_teams_have_corners10"] is True


def test_promoted_team_without_ten_top_flight_matches_is_partial(monkeypatch):
    monkeypatch.setattr(audit, "CONFIGS", {"EPL": EPL_RUNTIME_CONFIG})
    monkeypatch.setattr(audit, "EXPECTED_LOCKED_FIXTURES", 1)
    monkeypatch.setattr(audit, "_validate_lock", lambda lock: [_lock_row("Tottenham", "Hull")])

    previous = []
    for i in range(10):
        previous.append(_row(f"{1+i:02d}/05/2026", "Tottenham", f"X{i}"))
    current = [
        _row("15/08/2026", "Hull", "A"),
        _row("22/08/2026", "B", "Hull"),
        _row("29/08/2026", "Hull", "C"),
        _row("12/09/2026", "D", "Hull"),
        _row("19/09/2026", "Tottenham", "Hull"),
    ]

    report = audit.audit_from_frames(
        {},
        {
            ("EPL", audit.PREVIOUS_SEASON): pd.DataFrame(previous),
            ("EPL", audit.CURRENT_SEASON): pd.DataFrame(current),
        },
    )

    assert report["status"] == "PARTIAL_REPLAY_FEASIBLE"
    assert report["matched_fixture_count"] == 1
    assert report["corners10_feasible_fixture_count"] == 0
    row = report["rows"][0]
    assert row["home_prior_top_flight_corner_matches"] == 10
    assert row["away_prior_top_flight_corner_matches"] == 4
    assert row["fail_reason"] == "INSUFFICIENT_PRIOR_TOP_FLIGHT_HISTORY"


def test_unmatched_source_identity_fails_closed(monkeypatch):
    monkeypatch.setattr(audit, "CONFIGS", {"EPL": EPL_RUNTIME_CONFIG})
    monkeypatch.setattr(audit, "EXPECTED_LOCKED_FIXTURES", 1)
    monkeypatch.setattr(audit, "_validate_lock", lambda lock: [_lock_row("Tottenham", "Aston Villa")])

    previous = []
    for i in range(10):
        previous.append(_row(f"{1+i:02d}/05/2026", "Tottenham", f"X{i}"))
        previous.append(_row(f"{1+i:02d}/05/2026", f"Y{i}", "Aston Villa"))
    current = [_row("19/09/2026", "Tottenham", "Different Team")]

    report = audit.audit_from_frames(
        {},
        {
            ("EPL", audit.PREVIOUS_SEASON): pd.DataFrame(previous),
            ("EPL", audit.CURRENT_SEASON): pd.DataFrame(current),
        },
    )

    assert report["status"] == "IDENTITY_OR_SOURCE_GAPS"
    assert report["matched_fixture_count"] == 0
    assert report["rows"][0]["fail_reason"] == "SOURCE_FIXTURE_NOT_FOUND"
