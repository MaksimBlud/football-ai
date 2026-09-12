import pytest

from publish_product_predictions import (
    build_snapshot_rows,
    fixture_kickoff_utc,
    resolve_event_ids,
)


def prediction():
    return {
        "match_date": "2026-09-13",
        "match_time": "15:00",
        "home_team": "Manchester United",
        "away_team": "Arsenal",
        "home_team_model": "Man United",
        "away_team_model": "Arsenal",
        "prediction": "HOME",
        "prediction_strength": "MEDIUM",
        "model_agreement": "true",
        "home_probability": "0.55",
        "draw_probability": "0.25",
        "away_probability": "0.20",
        "expected_home_goals": "1.7",
        "expected_away_goals": "1.1",
        "expected_total_goals": "2.8",
        "over_2_5_probability": "0.60",
        "under_2_5_probability": "0.40",
        "btts_yes_probability": "0.52",
        "btts_no_probability": "0.48",
        "top_score": "2:1",
        "top_score_probability": "0.11",
    }


def fixture(**overrides):
    row = {
        "match_date": "2026-09-13",
        "match_time": "15:00",
        "home_team": "Manchester United",
        "away_team": "Arsenal",
        "home_team_model": "Man United",
        "away_team_model": "Arsenal",
        "match_datetime_uk": "2026-09-13T15:00:00",
        "league": "EPL",
    }
    row.update(overrides)
    return row


def test_naive_uk_fixture_time_is_converted_with_london_dst():
    assert fixture_kickoff_utc(fixture()) == "2026-09-13T14:00:00+00:00"


def test_explicit_utc_kickoff_takes_precedence():
    row = fixture(commence_time_utc="2026-09-13T14:05:00Z")
    assert fixture_kickoff_utc(row) == "2026-09-13T14:05:00+00:00"


def test_snapshot_builder_keeps_model_output_separate_from_market_price():
    rows = build_snapshot_rows(
        [prediction()],
        [fixture()],
        league="EPL",
        run_id="run-1",
        generated_at_utc="2026-09-12T07:00:00+00:00",
        model_1x2_version="production-1x2",
        model_1x2_sha256="abc123",
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["snapshot_schema_version"] == "product-prediction.v1"
    assert row["home_probability"] == pytest.approx(0.55)
    assert row["commence_time_utc"] == "2026-09-13T14:00:00+00:00"
    assert row["event_id"] is None
    assert "home_odds" not in row
    assert row["model_1x2_sha256"] == "abc123"


def test_missing_exact_fixture_is_rejected():
    bad_fixture = fixture(match_time="17:30")
    with pytest.raises(ValueError, match="no exact fixture row"):
        build_snapshot_rows(
            [prediction()],
            [bad_fixture],
            league="EPL",
            run_id="run-1",
            generated_at_utc="2026-09-12T07:00:00+00:00",
        )


def test_event_id_can_be_resolved_from_stored_odds_without_api_call():
    rows = build_snapshot_rows(
        [prediction()],
        [fixture()],
        league="EPL",
        run_id="run-1",
        generated_at_utc="2026-09-12T07:00:00+00:00",
    )
    odds = [
        {
            "league": "EPL",
            "event_id": "odds-event-1",
            "commence_time_utc": "2026-09-13T14:00:00+00:00",
            "home_team": "Manchester United",
            "away_team": "Arsenal",
        }
    ]

    assert resolve_event_ids(rows, odds) == 1
    assert rows[0]["event_id"] == "odds-event-1"


def test_ambiguous_stored_event_ids_are_not_guessed():
    rows = build_snapshot_rows(
        [prediction()],
        [fixture()],
        league="EPL",
        run_id="run-1",
        generated_at_utc="2026-09-12T07:00:00+00:00",
    )
    odds = [
        {
            "league": "EPL",
            "event_id": event_id,
            "commence_time_utc": "2026-09-13T14:00:00+00:00",
            "home_team": "Manchester United",
            "away_team": "Arsenal",
        }
        for event_id in ("event-a", "event-b")
    ]

    assert resolve_event_ids(rows, odds) == 0
    assert rows[0]["event_id"] is None
