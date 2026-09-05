from datetime import datetime, timezone

from research_viewer import assemble_viewer_payload


def _ledger():
    return [{
        "prediction_key": "p1", "league": "EPL", "event_id": "e1",
        "home_team": "Home", "away_team": "Away",
        "kickoff_utc": "2026-09-06T14:00:00Z",
        "prediction_time_utc": "2026-09-05T10:00:00Z",
        "snapshot_time_utc": "2026-09-05T10:00:00Z",
        "hours_to_kickoff": 28.0,
        "market_home_prob": 0.5, "market_draw_prob": 0.3, "market_away_prob": 0.2,
        "market_pick": "H", "market_pick_probability": 0.5,
        "prediction_mode": "MARKET_ONLY",
    }]


def test_attaches_latest_valid_multi_market_card():
    rows = [
        {"league": "EPL", "event_id": "e1", "kickoff_utc": "2026-09-06T14:00:00Z",
         "snapshot_time_utc": "2026-09-05T09:00:00Z", "payload": {"card": {"total_goals": {"point": 2.5}}}},
        {"league": "EPL", "event_id": "e1", "kickoff_utc": "2026-09-06T14:00:00Z",
         "snapshot_time_utc": "2026-09-05T12:00:00Z", "payload": {"card": {"total_goals": {"point": 3.0}}}},
    ]
    payload = assemble_viewer_payload(_ledger(), [], multi_market_rows=rows, now=datetime(2026, 9, 5, tzinfo=timezone.utc))
    assert payload["matches"][0]["multi_market"]["total_goals"]["point"] == 3.0
    assert payload["matches"][0]["multi_market"]["snapshot_time_utc"].startswith("2026-09-05T12:00:00")


def test_ignores_post_kickoff_multi_market_snapshot():
    rows = [{"league": "EPL", "event_id": "e1", "kickoff_utc": "2026-09-06T14:00:00Z",
             "snapshot_time_utc": "2026-09-06T15:00:00Z", "payload": {"card": {"total_goals": {"point": 2.5}}}}]
    payload = assemble_viewer_payload(_ledger(), [], multi_market_rows=rows, now=datetime(2026, 9, 5, tzinfo=timezone.utc))
    assert payload["matches"][0]["multi_market"] is None
