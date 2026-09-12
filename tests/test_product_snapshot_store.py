from datetime import datetime, timezone

import pytest

from product_snapshot_store import (
    build_product_view_from_snapshot_rows,
    prediction_identity,
    select_latest_odds_by_event,
    select_latest_prediction_snapshots,
)


def prediction_snapshot(**overrides):
    row = {
        "snapshot_schema_version": "product-prediction.v1",
        "run_id": "run-a",
        "generated_at_utc": "2026-09-12T06:00:00+00:00",
        "league": "EPL",
        "event_id": "event-1",
        "commence_time_utc": "2026-09-13T14:00:00+00:00",
        "match_date": "2026-09-13",
        "match_time": "15:00",
        "home_team": "Arsenal",
        "away_team": "Coventry City",
        "home_team_model": "Arsenal",
        "away_team_model": "Coventry City",
        "prediction": "HOME",
        "prediction_strength": "MEDIUM",
        "model_agreement": True,
        "home_probability": 0.60,
        "draw_probability": 0.24,
        "away_probability": 0.16,
        "expected_home_goals": 1.8,
        "expected_away_goals": 0.9,
        "expected_total_goals": 2.7,
        "over_2_5_probability": 0.58,
        "under_2_5_probability": 0.42,
        "btts_yes_probability": 0.51,
        "btts_no_probability": 0.49,
        "top_score": "2:1",
        "top_score_probability": 0.12,
    }
    row.update(overrides)
    return row


def odds_snapshot(**overrides):
    row = {
        "event_id": "event-1",
        "snapshot_time_utc": "2026-09-12T05:45:00+00:00",
        "commence_time_utc": "2026-09-13T14:00:00+00:00",
        "home_team": "Arsenal",
        "away_team": "Coventry City",
        "home_odds": 1.90,
        "draw_odds": 4.00,
        "away_odds": 7.00,
    }
    row.update(overrides)
    return row


def test_prediction_identity_prefers_provider_event_id():
    assert prediction_identity(prediction_snapshot()) == ("event_id", "event-1")


def test_prediction_identity_has_safe_fixture_fallback():
    identity = prediction_identity(prediction_snapshot(event_id=None))
    assert identity[:4] == ("fixture", "EPL", "Arsenal", "Coventry City")
    assert identity[4] == "2026-09-13T14:00:00+00:00"


def test_latest_prediction_snapshot_wins_without_mutating_history():
    older = prediction_snapshot(home_probability=0.55)
    newer = prediction_snapshot(
        run_id="run-b",
        generated_at_utc="2026-09-12T07:00:00+00:00",
        home_probability=0.61,
    )
    selected = select_latest_prediction_snapshots([older, newer])
    assert len(selected) == 1
    assert selected[0]["run_id"] == "run-b"
    assert selected[0]["home_probability"] == pytest.approx(0.61)


def test_unknown_snapshot_schema_is_not_exposed():
    selected = select_latest_prediction_snapshots(
        [prediction_snapshot(snapshot_schema_version="future.v9")]
    )
    assert selected == []


def test_latest_market_price_is_selected_independently():
    older = odds_snapshot(home_odds=1.80)
    newer = odds_snapshot(
        snapshot_time_utc="2026-09-12T05:55:00+00:00",
        home_odds=1.90,
    )
    selected = select_latest_odds_by_event([older, newer])
    assert selected["event-1"]["home_odds"] == pytest.approx(1.90)


def test_product_view_joins_model_and_market_only_by_event_id():
    payload = build_product_view_from_snapshot_rows(
        [prediction_snapshot()],
        [odds_snapshot()],
    )

    item = payload["matches"][0]
    home = item["markets"]["1x2"]["selections"][0]

    assert home["probability"] == pytest.approx(0.60)
    assert home["bookmaker_odds"] == pytest.approx(1.90)
    assert home["raw_expected_value"] == pytest.approx(0.14)
    assert item["main_forecast"]["status"] == "model_forecast"
    assert item["value_signal"]["status"] == "positive_raw_ev"
    assert payload["data_source"]["join"] == "event_id"


def test_different_event_id_never_cross_matches_same_teams():
    payload = build_product_view_from_snapshot_rows(
        [prediction_snapshot(event_id="model-event")],
        [odds_snapshot(event_id="market-event")],
    )

    item = payload["matches"][0]
    home = item["markets"]["1x2"]["selections"][0]
    assert home["bookmaker_odds"] is None
    assert home["raw_expected_value"] is None
    assert item["main_forecast"]["status"] == "model_forecast"
    assert item["value_signal"]["status"] == "none"


def test_timezone_naive_snapshot_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        select_latest_prediction_snapshots(
            [prediction_snapshot(generated_at_utc="2026-09-12T07:00:00")]
        )
