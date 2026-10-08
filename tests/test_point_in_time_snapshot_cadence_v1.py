import csv
from pathlib import Path

from point_in_time_snapshot_cadence_v1 import (
    FROZEN_LEAGUES,
    audit_snapshot_sources,
    evaluate,
    policy_arithmetic,
)


def test_frozen_credit_arithmetic():
    report = policy_arithmetic()
    assert report["spendable_credits"] == 400
    assert report["full_sweep_cost_credits"] == 5
    assert report["P1_fixed_12h"] == {
        "spacing_hours": 12,
        "full_sweeps": 60,
        "credits": 300,
        "unused_spendable_credits": 100,
    }
    assert report["P2_fixed_9h"] == {
        "spacing_hours": 9,
        "full_sweeps": 80,
        "credits": 400,
        "unused_spendable_credits": 0,
    }


def test_missing_repository_snapshot_history_fails_closed(tmp_path: Path):
    result = evaluate(tmp_path)
    assert result["decision"] == "BLOCKED_BY_TIMESTAMP_COVERAGE"
    assert result["source_gate"]["available_league_count"] == 0
    assert result["source_gate"]["outcome_columns_loaded"] is False
    assert result["safety"]["paid_odds_api_calls"] == 0
    assert result["safety"]["supabase_reads"] == 0
    assert result["safety"]["supabase_writes"] == 0
    assert result["safety"]["match_outcomes_used"] is False


def _write_snapshot_rows(root: Path) -> None:
    path = root / "data" / "odds_snapshots" / "sample_h2h_snapshots.csv"
    path.parent.mkdir(parents=True)
    fieldnames = [
        "league",
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
        "FTHG",
    ]
    rows = [
        {
            "league": "EPL",
            "event_id": "e1",
            "snapshot_time_utc": "2026-08-01T00:00:00Z",
            "commence_time_utc": "2026-08-02T12:00:00Z",
            "FTHG": "3",
        },
        {
            "league": "LA_LIGA",
            "event_id": "l1",
            "snapshot_time_utc": "2026-08-03T00:00:00Z",
            "commence_time_utc": "2026-08-04T12:00:00Z",
            "FTHG": "1",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_snapshot_only_two_league_source_waits_for_complete_fixture_universe(
    tmp_path: Path,
):
    _write_snapshot_rows(tmp_path)
    source = audit_snapshot_sources(tmp_path)
    assert source["gate_passed"] is True
    assert source["available_leagues"] == ["EPL", "LA_LIGA"]
    assert source["complete_fixture_universe_available"] is False
    assert source["outcome_columns_loaded"] is False

    result = evaluate(tmp_path)
    assert result["decision"] == "WAITING_FOR_NEW_EVIDENCE"
    assert "missed fixtures" in result["interpretation_guard"]


def test_non_pre_kickoff_and_unknown_league_rows_are_not_eligible(tmp_path: Path):
    path = tmp_path / "data" / "sample_snapshot.csv"
    path.parent.mkdir(parents=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "league",
                "event_id",
                "snapshot_time_utc",
                "commence_time_utc",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "league": FROZEN_LEAGUES[0],
                "event_id": "late",
                "snapshot_time_utc": "2026-08-02T12:00:00Z",
                "commence_time_utc": "2026-08-02T12:00:00Z",
            }
        )
        writer.writerow(
            {
                "league": "OTHER",
                "event_id": "other",
                "snapshot_time_utc": "2026-08-01T00:00:00Z",
                "commence_time_utc": "2026-08-02T12:00:00Z",
            }
        )
    source = audit_snapshot_sources(tmp_path)
    assert source["available_league_count"] == 0
    assert source["malformed_or_non_pre_kickoff_rows"] == 1
