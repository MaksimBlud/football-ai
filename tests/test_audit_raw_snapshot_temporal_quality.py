import pandas as pd
import pytest

from audit_raw_snapshot_temporal_quality import audit_frames


def raw_row(event_id, snapshot, kickoff, home="A", away="B"):
    return {
        "league": "EPL",
        "event_id": event_id,
        "home_team": home,
        "away_team": away,
        "snapshot_time_utc": snapshot,
        "commence_time_utc": kickoff,
    }


def ledger_row(snapshot, kickoff):
    return {
        "league": "EPL",
        "snapshot_time_utc": snapshot,
        "kickoff_utc": kickoff,
    }


def test_raw_post_kickoff_rows_are_warnings_not_canonical_failures():
    raw = pd.DataFrame([
        raw_row("e1", "2026-09-01T10:00:00Z", "2026-09-01T12:00:00Z"),
        raw_row("e1", "2026-09-01T13:00:00Z", "2026-09-01T12:00:00Z"),
    ])
    ledger = pd.DataFrame([ledger_row("2026-09-01T11:00:00Z", "2026-09-01T12:00:00Z")])

    report = audit_frames("EPL", raw, ledger)

    assert report.raw_post_kickoff_rows == 1
    assert report.raw_post_kickoff_events == 1
    assert report.archive_warnings == 1
    assert report.ledger_post_kickoff_rows == 0
    assert report.critical_failures == 0


def test_canonical_ledger_post_kickoff_row_is_critical():
    raw = pd.DataFrame([raw_row("e1", "2026-09-01T10:00:00Z", "2026-09-01T12:00:00Z")])
    ledger = pd.DataFrame([ledger_row("2026-09-01T12:00:00Z", "2026-09-01T12:00:00Z")])

    report = audit_frames("EPL", raw, ledger)

    assert report.ledger_post_kickoff_rows == 1
    assert report.critical_failures == 1


def test_changed_kickoff_for_same_event_is_archive_warning():
    raw = pd.DataFrame([
        raw_row("e1", "2026-09-01T08:00:00Z", "2026-09-01T12:00:00Z"),
        raw_row("e1", "2026-09-01T09:00:00Z", "2026-09-01T14:00:00Z"),
    ])

    report = audit_frames("EPL", raw, pd.DataFrame())

    assert report.ambiguous_event_ids == 1
    assert report.archive_warnings == 1
    assert report.critical_failures == 0


def test_foreign_league_rows_fail_closed():
    raw = pd.DataFrame([raw_row("e1", "2026-09-01T08:00:00Z", "2026-09-01T12:00:00Z")])
    raw.loc[0, "league"] = "LA_LIGA"

    with pytest.raises(ValueError, match="foreign league"):
        audit_frames("EPL", raw, pd.DataFrame())


def test_invalid_temporal_values_fail_closed():
    raw = pd.DataFrame([raw_row("e1", "not-a-date", "2026-09-01T12:00:00Z")])

    with pytest.raises(ValueError, match="invalid temporal"):
        audit_frames("EPL", raw, pd.DataFrame())
