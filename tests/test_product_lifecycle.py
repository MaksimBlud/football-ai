import math

import pytest

from advance_product_lifecycle import build_lifecycle_pass, index_results
from product_lifecycle import (
    EVENT_MARKET_OBSERVED,
    EVENT_PREDICTION_REGISTERED,
    EVENT_SETTLED,
    REGISTRATION_MODE_LEGACY_BOOTSTRAP,
    REGISTRATION_MODE_LIVE,
    build_market_observed_event,
    build_prediction_registered_event,
    build_settled_event,
    performance_summary,
)


def prediction(**overrides):
    row = {
        "id": 101,
        "snapshot_schema_version": "product-prediction.v1",
        "run_id": "run-1",
        "generated_at_utc": "2026-09-12T12:00:00+00:00",
        "created_at": "2026-09-12T13:00:00+00:00",
        "league": "EPL",
        "event_id": "event-1",
        "commence_time_utc": "2026-09-12T14:00:00+00:00",
        "match_date": "2026-09-12",
        "match_time": "15:00",
        "home_team": "Liverpool",
        "away_team": "Fulham",
        "home_team_model": "Liverpool",
        "away_team_model": "Fulham",
        "home_probability": 0.675,
        "draw_probability": 0.157,
        "away_probability": 0.168,
        "model_1x2_version": "MODEL_V1",
        "model_1x2_sha256": "a" * 64,
        "publisher_version": "product-publisher.v1",
        "over_2_5_probability": None,
        "under_2_5_probability": None,
    }
    row.update(overrides)
    return row


def odds(**overrides):
    row = {
        "id": 501,
        "event_id": "event-1",
        "snapshot_time_utc": "2026-09-12T12:30:00+00:00",
        "commence_time_utc": "2026-09-12T14:00:00+00:00",
        "home_odds": 1.43,
        "draw_odds": 4.92,
        "away_odds": 6.42,
    }
    row.update(overrides)
    return row


def result(**overrides):
    row = {
        "league": "EPL",
        "match_date": "2026-09-12",
        "home_team": "Liverpool",
        "away_team": "Fulham",
        "home_goals": 2,
        "away_goals": 0,
        "result": "H",
        "persisted_at_utc": "2026-09-12T17:30:00+00:00",
    }
    row.update(overrides)
    return row


def test_legacy_registration_preserves_source_time_without_retroactive_decision():
    event = build_prediction_registered_event(
        prediction(),
        recorded_at_utc="2026-09-12T14:30:00+00:00",
        registration_mode=REGISTRATION_MODE_LEGACY_BOOTSTRAP,
        market_reference=odds(),
    )

    assert event["event_type"] == EVENT_PREDICTION_REGISTERED
    assert event["source_prediction_created_at_utc"] == "2026-09-12T13:00:00+00:00"
    assert event["recorded_at_utc"] == "2026-09-12T14:30:00+00:00"
    assert event["payload"]["decision_at_registration"] is None
    assert (
        event["payload"]["market_reference_at_registration"]["role"]
        == "latest_stored_observation_at_or_before_source_snapshot"
    )


def test_registration_rejects_post_kickoff_source_snapshot():
    with pytest.raises(ValueError, match="not pre-kickoff"):
        build_prediction_registered_event(
            prediction(created_at="2026-09-12T14:01:00+00:00"),
            recorded_at_utc="2026-09-12T14:30:00+00:00",
            registration_mode=REGISTRATION_MODE_LEGACY_BOOTSTRAP,
        )


def test_legacy_bootstrap_cannot_attach_current_decision_framework_retroactively():
    with pytest.raises(ValueError, match="must not retroactively"):
        build_prediction_registered_event(
            prediction(),
            recorded_at_utc="2026-09-12T14:30:00+00:00",
            registration_mode=REGISTRATION_MODE_LEGACY_BOOTSTRAP,
            decision_payload={"framework_version": "product-decision.v1"},
        )


def test_market_observation_is_pre_kickoff_but_not_fabricated_closing_line():
    event = build_market_observed_event(
        prediction(),
        odds(snapshot_time_utc="2026-09-12T13:50:00+00:00"),
        recorded_at_utc="2026-09-12T14:01:00+00:00",
    )

    assert event["event_type"] == EVENT_MARKET_OBSERVED
    assert event["payload"]["minutes_before_kickoff"] == pytest.approx(10.0)
    assert event["payload"]["is_closing_qualified"] is False
    assert event["payload"]["clv"] is None


def test_market_observation_cannot_be_finalized_before_kickoff_or_use_postkickoff_price():
    with pytest.raises(ValueError, match="only after kickoff"):
        build_market_observed_event(
            prediction(),
            odds(),
            recorded_at_utc="2026-09-12T13:59:00+00:00",
        )

    with pytest.raises(ValueError, match="after kickoff"):
        build_market_observed_event(
            prediction(),
            odds(snapshot_time_utc="2026-09-12T14:01:00+00:00"),
            recorded_at_utc="2026-09-12T14:30:00+00:00",
        )


def test_settlement_matches_canonical_brier_and_log_loss_without_betting_pnl():
    event = build_settled_event(
        prediction(),
        result(),
        recorded_at_utc="2026-09-12T18:00:00+00:00",
    )

    p = (0.675, 0.157, 0.168)
    expected_brier = (p[0] - 1) ** 2 + p[1] ** 2 + p[2] ** 2

    assert event["event_type"] == EVENT_SETTLED
    assert event["payload"]["actual_outcome"] == "HOME"
    assert event["payload"]["prediction_correct"] is True
    assert event["payload"]["multiclass_brier"] == pytest.approx(expected_brier)
    assert event["payload"]["log_loss"] == pytest.approx(-math.log(0.675))
    assert event["payload"]["pnl"] is None
    assert event["payload"]["roi"] is None
    assert event["payload"]["clv"] is None


def test_settlement_rejects_result_identity_or_score_disagreement():
    with pytest.raises(ValueError, match="fixture identity"):
        build_settled_event(
            prediction(),
            result(away_team="Everton"),
            recorded_at_utc="2026-09-12T18:00:00+00:00",
        )

    with pytest.raises(ValueError, match="disagrees"):
        build_settled_event(
            prediction(),
            result(result="A"),
            recorded_at_utc="2026-09-12T18:00:00+00:00",
        )


def test_performance_summary_uses_settled_events_only_and_exposes_calibration():
    settled_a = build_settled_event(
        prediction(id=1),
        result(),
        recorded_at_utc="2026-09-12T18:00:00+00:00",
    )
    settled_b = build_settled_event(
        prediction(
            id=2,
            event_id="event-2",
            home_team="Arsenal",
            away_team="Everton",
            home_probability=0.60,
            draw_probability=0.25,
            away_probability=0.15,
        ),
        result(
            home_team="Arsenal",
            away_team="Everton",
            home_goals=0,
            away_goals=1,
            result="A",
        ),
        recorded_at_utc="2026-09-12T18:00:00+00:00",
    )

    summary = performance_summary([settled_a, settled_b])
    assert summary["settled_predictions"] == 2
    assert summary["accuracy"] == pytest.approx(0.5)
    assert summary["mean_multiclass_brier"] is not None
    assert summary["mean_log_loss"] is not None
    assert sum(bucket["n"] for bucket in summary["calibration"]) == 2
    assert summary["betting_pnl_available"] is False
    assert summary["clv_available"] is False


def test_empty_performance_summary_is_honest_n_zero():
    summary = performance_summary([])
    assert summary["settled_predictions"] == 0
    assert summary["accuracy"] is None
    assert summary["calibration"] == []


def test_lifecycle_pass_is_idempotent_and_uses_latest_time_bounded_odds():
    odds_rows = [
        odds(id=1, snapshot_time_utc="2026-09-12T12:00:00+00:00", home_odds=1.40),
        odds(id=2, snapshot_time_utc="2026-09-12T12:50:00+00:00", home_odds=1.42),
        odds(id=3, snapshot_time_utc="2026-09-12T13:50:00+00:00", home_odds=1.45),
        odds(id=4, snapshot_time_utc="2026-09-12T14:05:00+00:00", home_odds=1.50),
    ]
    built = build_lifecycle_pass(
        [prediction()],
        odds_rows,
        [result()],
        now_utc="2026-09-12T18:00:00+00:00",
        registration_mode=REGISTRATION_MODE_LEGACY_BOOTSTRAP,
    )
    events = built["events"]
    assert built["counts"] == {
        "registered": 1,
        "market_observed": 1,
        "settled": 1,
        "skipped_non_pre_kickoff": 0,
    }
    registered = next(e for e in events if e["event_type"] == EVENT_PREDICTION_REGISTERED)
    market = next(e for e in events if e["event_type"] == EVENT_MARKET_OBSERVED)
    assert registered["payload"]["market_reference_at_registration"]["snapshot_id"] == 2
    assert market["source_odds_snapshot_id"] == 3

    rerun = build_lifecycle_pass(
        [prediction()],
        odds_rows,
        [result()],
        existing_event_keys={event["event_key"] for event in events},
        now_utc="2026-09-12T18:05:00+00:00",
        registration_mode=REGISTRATION_MODE_LEGACY_BOOTSTRAP,
    )
    assert rerun["events"] == []
    assert rerun["counts"]["registered"] == 0
    assert rerun["counts"]["market_observed"] == 0
    assert rerun["counts"]["settled"] == 0


def test_live_registration_freezes_decision_framework_only_at_live_registration():
    built = build_lifecycle_pass(
        [prediction(commence_time_utc="2026-09-13T14:00:00+00:00")],
        [odds()],
        [],
        now_utc="2026-09-12T13:30:00+00:00",
        registration_mode=REGISTRATION_MODE_LIVE,
    )
    event = built["events"][0]
    decision = event["payload"]["decision_at_registration"]
    assert decision["framework_version"] == "product-decision.v1"
    assert decision["main_forecast"]["market"] == "1x2"
    assert decision["bet_decision"]["status"] == "no_bet"


def test_conflicting_canonical_results_are_rejected():
    with pytest.raises(ValueError, match="conflicting canonical results"):
        index_results([result(), result(home_goals=0, away_goals=1, result="A")])
