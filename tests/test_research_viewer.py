from datetime import datetime, timezone

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


def test_viewer_keeps_latest_pre_kickoff_prediction_only():
    rows = [
        _row(prediction_key="old", prediction_time_utc="2026-08-30T10:00:00Z"),
        _row(prediction_key="latest", prediction_time_utc="2026-08-30T14:00:00Z"),
        _row(prediction_key="bad-post", prediction_time_utc="2026-08-30T16:00:00Z"),
    ]
    payload = assemble_viewer_payload(
        rows,
        [],
        now=datetime(2026, 8, 30, 13, 0, tzinfo=timezone.utc),
    )
    assert payload["summary"]["predictions"] == 1
    assert payload["matches"][0]["prediction_key"] == "latest"
    assert payload["matches"][0]["status"] == "UPCOMING"


def test_viewer_matches_canonical_finished_result_by_league_identity_and_date():
    payload = assemble_viewer_payload(
        [_row()],
        [{
            "league": "EPL",
            "season": "2026-27",
            "match_date": "2026-08-30",
            "home_team": "Alpha",
            "away_team": "Beta",
            "home_goals": 2,
            "away_goals": 1,
            "result": "H",
        }],
        now=datetime(2026, 8, 30, 18, 0, tzinfo=timezone.utc),
    )
    card = payload["matches"][0]
    assert card["status"] == "SETTLED"
    assert card["result"] == {"home_goals": 2, "away_goals": 1, "result": "H"}


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
