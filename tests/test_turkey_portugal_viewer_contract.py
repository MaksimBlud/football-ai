from datetime import datetime, timezone

from research_viewer import ACTIVE_LEAGUES, assemble_viewer_payload


def _market_only_row(league: str, event_id: str):
    return {
        "prediction_key": f"{league}:{event_id}:pred-1",
        "league": league,
        "event_id": event_id,
        "home_team": "Alpha",
        "away_team": "Beta",
        "kickoff_utc": "2026-09-06T18:00:00Z",
        "prediction_time_utc": "2026-09-06T12:00:00Z",
        "snapshot_time_utc": "2026-09-06T12:00:00Z",
        "hours_to_kickoff": 6.0,
        "market_home_prob": 0.48,
        "market_draw_prob": 0.29,
        "market_away_prob": 0.23,
        "market_pick": "H",
        "market_pick_probability": 0.48,
        "structural_status": "CALIBRATION_REQUIRED",
        "structural_home_prob": None,
        "structural_draw_prob": None,
        "structural_away_prob": None,
        "structural_pick": None,
        "structural_pick_probability": None,
        "structural_score": None,
        "structural_applied": False,
        "prediction_mode": "MARKET_ONLY",
        "observation_key": f"{league}:{event_id}:obs-1",
    }


def test_active_leagues_include_turkey_and_portugal():
    assert "TURKEY_SUPER_LIG" in ACTIVE_LEAGUES
    assert "PRIMEIRA_LIGA" in ACTIVE_LEAGUES
    assert len(ACTIVE_LEAGUES) == 9


def test_viewer_accepts_turkey_and_portugal_market_only_cards():
    payload = assemble_viewer_payload(
        [
            _market_only_row("TURKEY_SUPER_LIG", "turkey-event"),
            _market_only_row("PRIMEIRA_LIGA", "portugal-event"),
        ],
        [],
        now=datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc),
    )

    assert {card["league"] for card in payload["matches"]} == {
        "TURKEY_SUPER_LIG",
        "PRIMEIRA_LIGA",
    }
    assert all(card["prediction_mode"] == "MARKET_ONLY" for card in payload["matches"])
    assert all(card["structural"] is None for card in payload["matches"])


def test_viewer_attaches_multi_market_by_league_and_event_id():
    row = _market_only_row("TURKEY_SUPER_LIG", "shared-event")
    multi_rows = [
        {
            "league": "PRIMEIRA_LIGA",
            "event_id": "shared-event",
            "kickoff_utc": "2026-09-06T18:00:00Z",
            "snapshot_time_utc": "2026-09-06T11:00:00Z",
            "payload": {"card": {"total_goals": {"point": 2.5}}},
        },
        {
            "league": "TURKEY_SUPER_LIG",
            "event_id": "shared-event",
            "kickoff_utc": "2026-09-06T18:00:00Z",
            "snapshot_time_utc": "2026-09-06T11:30:00Z",
            "payload": {"card": {"total_goals": {"point": 3.0}}},
        },
    ]

    payload = assemble_viewer_payload(
        [row],
        [],
        multi_market_rows=multi_rows,
        now=datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc),
    )

    assert payload["matches"][0]["multi_market"]["total_goals"]["point"] == 3.0
