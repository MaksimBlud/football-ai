from datetime import datetime, timezone

import pytest

from research_viewer import ACTIVE_LEAGUES, assemble_viewer_payload


def _row(**overrides):
    row = {
        "prediction_key": "EPL:event-1:pred-1",
        "league": "EPL",
        "event_id": "event-1",
        "home_team": "Alpha",
        "away_team": "Beta",
        "kickoff_utc": "2026-08-30T15:00:00Z",
        "prediction_time_utc": "2026-08-30T12:00:00Z",
        "snapshot_time_utc": "2026-08-30T12:00:00Z",
        "hours_to_kickoff": 3.0,
        "market_home_prob": 0.50,
        "market_draw_prob": 0.28,
        "market_away_prob": 0.22,
        "market_pick": "H",
        "market_pick_probability": 0.50,
        "structural_status": None,
        "structural_home_prob": None,
        "structural_draw_prob": None,
        "structural_away_prob": None,
        "structural_pick": None,
        "structural_pick_probability": None,
        "structural_score": None,
        "structural_applied": False,
        "prediction_mode": "MARKET_ONLY",
        "observation_key": "obs-1",
    }
    row.update(overrides)
    return row


def test_viewer_keeps_latest_eligible_snapshot_not_latest_prediction_timestamp():
    rows = [
        _row(
            prediction_key="older-snapshot",
            snapshot_time_utc="2026-08-30T10:00:00Z",
            prediction_time_utc="2026-08-30T14:30:00Z",
        ),
        _row(
            prediction_key="latest-snapshot",
            snapshot_time_utc="2026-08-30T14:00:00Z",
            prediction_time_utc="2026-08-30T14:10:00Z",
        ),
        _row(
            prediction_key="bad-post-snapshot",
            snapshot_time_utc="2026-08-30T16:00:00Z",
            prediction_time_utc="2026-08-30T14:20:00Z",
        ),
    ]
    payload = assemble_viewer_payload(
        rows,
        [],
        now=datetime(2026, 8, 30, 13, 0, tzinfo=timezone.utc),
    )
    assert payload["summary"]["predictions"] == 1
    assert payload["matches"][0]["prediction_key"] == "latest-snapshot"
    assert payload["matches"][0]["status"] == "UPCOMING"


def test_viewer_matches_finished_result_using_normalized_team_names():
    payload = assemble_viewer_payload(
        [_row(home_team="Manchester City", away_team="Leeds United")],
        [{
            "league": "EPL",
            "season": "2026-27",
            "match_date": "2026-08-30",
            "home_team": "Man City",
            "away_team": "Leeds",
            "home_goals": 2,
            "away_goals": 1,
            "result": "H",
        }],
        now=datetime(2026, 8, 30, 18, 0, tzinfo=timezone.utc),
    )
    card = payload["matches"][0]
    assert card["status"] == "SETTLED"
    assert card["result"] == {"home_goals": 2, "away_goals": 1, "result": "H"}


def test_viewer_uses_league_local_match_date_for_settlement():
    payload = assemble_viewer_payload(
        [_row(
            league="LA_LIGA",
            prediction_key="LA_LIGA:event-1:pred-1",
            kickoff_utc="2026-08-30T22:30:00Z",
            prediction_time_utc="2026-08-30T20:00:00Z",
            snapshot_time_utc="2026-08-30T20:00:00Z",
        )],
        [{
            "league": "LA_LIGA",
            "season": "2026-27",
            "match_date": "2026-08-31",
            "home_team": "Alpha",
            "away_team": "Beta",
            "home_goals": 0,
            "away_goals": 0,
            "result": "D",
        }],
        now=datetime(2026, 8, 31, 1, 0, tzinfo=timezone.utc),
    )
    assert payload["matches"][0]["status"] == "SETTLED"


def test_viewer_rejects_duplicate_finished_result_identity():
    result = {
        "league": "EPL",
        "season": "2026-27",
        "match_date": "2026-08-30",
        "home_team": "Alpha",
        "away_team": "Beta",
        "home_goals": 1,
        "away_goals": 0,
        "result": "H",
    }
    with pytest.raises(ValueError, match="Duplicate canonical finished-result identity"):
        assemble_viewer_payload([_row()], [result, dict(result)])


def test_viewer_exposes_structural_shadow_without_applying_it():
    payload = assemble_viewer_payload(
        [_row(
            structural_status="SHADOW",
            structural_home_prob=0.56,
            structural_draw_prob=0.25,
            structural_away_prob=0.19,
            structural_pick="H",
            structural_pick_probability=0.56,
            structural_score=0.8,
            structural_applied=False,
        )],
        [],
        now=datetime(2026, 8, 30, 13, 0, tzinfo=timezone.utc),
    )
    structural = payload["matches"][0]["structural"]
    assert structural["applied"] is False
    assert structural["max_abs_delta"] == 0.06
    assert payload["matches"][0]["prediction_mode"] == "MARKET_ONLY"


def test_viewer_contract_lists_all_operational_leagues():
    payload = assemble_viewer_payload([], [])
    assert tuple(payload["active_leagues"]) == ACTIVE_LEAGUES
    assert payload["summary"]["awaiting_result"] == 0
