import pandas as pd
import pytest

import audit_epl_observation_ledger_parity as audit


def _observation(event_id: str, snapshot: str, kickoff: str = "2026-09-06T15:00:00Z") -> dict:
    return {
        "league": "EPL",
        "event_id": event_id,
        "snapshot_time_utc": snapshot,
        "commence_time_utc": kickoff,
    }


def _ledger(event_id: str, snapshot: str) -> dict:
    return {
        "league": "EPL",
        "event_id": event_id,
        "snapshot_time_utc": snapshot,
    }


def test_exact_parity_is_clean():
    observations = pd.DataFrame([
        _observation("e1", "2026-09-05T10:00:00Z"),
    ])
    ledger = pd.DataFrame([
        _ledger("e1", "2026-09-05T10:00:00Z"),
    ])

    report = audit.audit_frames(
        observations,
        ledger,
        audited_at_utc="2026-09-06T06:00:00Z",
    )

    assert report.orphan_snapshot_rows == 0
    assert report.post_ledger_events_without_any_ledger == 0
    assert report.critical_failures == 0


def test_snapshot_gap_on_otherwise_covered_event_is_warning_only():
    observations = pd.DataFrame([
        _observation("e1", "2026-09-05T10:00:00Z"),
        _observation("e1", "2026-09-05T11:00:00Z"),
    ])
    ledger = pd.DataFrame([
        _ledger("e1", "2026-09-05T10:00:00Z"),
    ])

    report = audit.audit_frames(
        observations,
        ledger,
        audited_at_utc="2026-09-06T06:00:00Z",
    )

    assert report.orphan_snapshot_rows == 1
    assert report.orphan_snapshot_events == 1
    assert report.orphan_snapshots_on_covered_events == 1
    assert report.post_ledger_events_without_any_ledger == 0
    assert report.critical_failures == 0


def test_post_ledger_observation_event_without_any_ledger_is_critical():
    observations = pd.DataFrame([
        _observation("covered", "2026-09-05T10:00:00Z"),
        _observation("missing", "2026-09-05T12:00:00Z"),
    ])
    ledger = pd.DataFrame([
        _ledger("covered", "2026-09-05T10:00:00Z"),
    ])

    report = audit.audit_frames(
        observations,
        ledger,
        audited_at_utc="2026-09-06T06:00:00Z",
    )

    assert report.orphan_snapshot_rows == 1
    assert report.post_ledger_events_without_any_ledger == 1
    assert report.post_ledger_orphan_snapshots_without_any_ledger == 1
    assert report.critical_failures == 1


def test_pre_ledger_legacy_observation_without_event_coverage_is_not_retroactive_failure():
    observations = pd.DataFrame([
        _observation("legacy", "2026-09-04T10:00:00Z"),
        _observation("covered", "2026-09-05T10:00:00Z"),
    ])
    ledger = pd.DataFrame([
        _ledger("covered", "2026-09-05T10:00:00Z"),
    ])

    report = audit.audit_frames(
        observations,
        ledger,
        audited_at_utc="2026-09-06T06:00:00Z",
    )

    assert report.orphan_snapshot_rows == 1
    assert report.post_ledger_events_without_any_ledger == 0
    assert report.critical_failures == 0


def test_invalid_or_foreign_inputs_fail_closed():
    observations = pd.DataFrame([
        _observation("e1", "not-a-time"),
    ])
    ledger = pd.DataFrame([
        _ledger("e1", "2026-09-05T10:00:00Z"),
    ])
    with pytest.raises(ValueError, match="invalid snapshot_time_utc"):
        audit.audit_frames(
            observations,
            ledger,
            audited_at_utc="2026-09-06T06:00:00Z",
        )

    foreign = pd.DataFrame([
        {**_observation("e1", "2026-09-05T10:00:00Z"), "league": "LA_LIGA"},
    ])
    with pytest.raises(ValueError, match="foreign league"):
        audit.audit_frames(
            foreign,
            ledger,
            audited_at_utc="2026-09-06T06:00:00Z",
        )


def test_source_is_read_only_and_outcome_free():
    source = open("audit_epl_observation_ledger_parity.py", encoding="utf-8").read()
    forbidden = [
        ".insert(", ".upsert(", ".update(", ".delete(",
        "league_finished_results", "actual_result", "home_goals", "away_goals",
        "joblib.load", "football_model_xgboost_elo", "train_model",
    ]
    for token in forbidden:
        assert token not in source
