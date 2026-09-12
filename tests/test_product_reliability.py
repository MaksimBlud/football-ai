import math
from datetime import datetime, timedelta, timezone

import pytest

from product_reliability import (
    EVIDENCE_ACCUMULATING_SAMPLE,
    EVIDENCE_ACCUMULATING_TIME,
    EVIDENCE_DESCRIPTIVE_ONLY,
    EVIDENCE_NO_DATA,
    EVIDENCE_REVIEWABLE,
    MIN_CALENDAR_MONTHS_FOR_REVIEW,
    MIN_SETTLED_FIXTURES_FOR_REVIEW,
    build_reliability_matrix,
    reliability_summary,
    settled_reliability_records,
    wilson_interval,
)


MODEL_A = "a" * 64
MODEL_B = "b" * 64
PROBS = (0.60, 0.25, 0.15)
OUTCOMES = ("HOME", "DRAW", "AWAY")


def _scoring(actual_outcome: str):
    actual_index = OUTCOMES.index(actual_outcome)
    one_hot = [0.0, 0.0, 0.0]
    one_hot[actual_index] = 1.0
    brier = sum((PROBS[i] - one_hot[i]) ** 2 for i in range(3))
    log_loss = -math.log(PROBS[actual_index])
    return brier, log_loss


def lifecycle_pair(
    snapshot_id: int,
    *,
    kickoff: datetime,
    model_sha: str = MODEL_A,
    league: str = "EPL",
    actual_outcome: str = "HOME",
):
    match_id = f"event_{snapshot_id}"
    brier, log_loss = _scoring(actual_outcome)
    correct = actual_outcome == "HOME"
    registration = {
        "event_type": "PREDICTION_REGISTERED",
        "source_prediction_snapshot_id": snapshot_id,
        "product_match_id": match_id,
        "event_id": str(snapshot_id),
        "league": league,
        "commence_time_utc": kickoff.isoformat(),
        "payload": {
            "registration_mode": "legacy_source_snapshot_bootstrap",
            "prediction": {
                "home_probability": PROBS[0],
                "draw_probability": PROBS[1],
                "away_probability": PROBS[2],
                "model_1x2_version": "MODEL_A_V1",
                "model_1x2_sha256": model_sha,
            },
            "decision_at_registration": None,
        },
    }
    settlement = {
        "event_type": "SETTLED",
        "source_prediction_snapshot_id": snapshot_id,
        "product_match_id": match_id,
        "event_id": str(snapshot_id),
        "league": league,
        "commence_time_utc": kickoff.isoformat(),
        "payload": {
            "settlement_scope": "1x2_model_probability",
            "actual_outcome": actual_outcome,
            "model_pick": "HOME",
            "model_pick_probability": PROBS[0],
            "prediction_correct": correct,
            "multiclass_brier": brier,
            "log_loss": log_loss,
        },
    }
    return registration, settlement


def event_series(
    count: int,
    *,
    model_sha: str = MODEL_A,
    league: str = "EPL",
    spacing_days: int = 1,
    start: datetime | None = None,
):
    start = start or datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    events = []
    for index in range(count):
        events.extend(
            lifecycle_pair(
                index + 1,
                kickoff=start + timedelta(days=index * spacing_days),
                model_sha=model_sha,
                league=league,
                actual_outcome="HOME" if index % 2 == 0 else "AWAY",
            )
        )
    return events


def test_exact_scope_with_no_settlements_is_honestly_no_data():
    report = reliability_summary([], league="EPL", model_1x2_sha256=MODEL_A)

    assert report["settled_predictions"] == 0
    assert report["evidence_gate"]["state"] == EVIDENCE_NO_DATA
    assert report["evidence_gate"]["reviewable"] is False
    assert report["metrics"]["accuracy"] is None
    assert report["reliability_verdict"]["status"] == "INCONCLUSIVE"


def test_sample_gate_is_frozen_at_one_hundred_settled_fixtures():
    assert MIN_SETTLED_FIXTURES_FOR_REVIEW == 100
    records = settled_reliability_records(event_series(99, spacing_days=2))
    report = reliability_summary(records, league="EPL", model_1x2_sha256=MODEL_A)

    assert report["settled_predictions"] == 99
    assert report["evidence_gate"]["state"] == EVIDENCE_ACCUMULATING_SAMPLE
    assert report["evidence_gate"]["sample_gate_passed"] is False


def test_hundred_matches_without_four_calendar_months_remain_accumulating():
    assert MIN_CALENDAR_MONTHS_FOR_REVIEW == 4
    records = settled_reliability_records(event_series(100, spacing_days=1))
    report = reliability_summary(records, league="EPL", model_1x2_sha256=MODEL_A)

    assert report["evidence_gate"]["sample_gate_passed"] is True
    assert report["evidence_gate"]["calendar_span_gate_passed"] is False
    assert report["evidence_gate"]["state"] == EVIDENCE_ACCUMULATING_TIME
    assert report["evidence_gate"]["reviewable"] is False


def test_exact_model_league_slice_becomes_reviewable_only_after_both_gates():
    records = settled_reliability_records(event_series(100, spacing_days=2))
    report = reliability_summary(records, league="EPL", model_1x2_sha256=MODEL_A)

    assert report["evidence_gate"]["sample_gate_passed"] is True
    assert report["evidence_gate"]["calendar_span_gate_passed"] is True
    assert report["evidence_gate"]["state"] == EVIDENCE_REVIEWABLE
    assert report["evidence_gate"]["reviewable"] is True
    assert report["reliability_verdict"]["status"] == "INCONCLUSIVE"
    assert report["reliability_verdict"]["claim"] is None
    assert not any(report["automatic_effects"].values())


def test_cross_model_pooling_is_descriptive_and_cannot_satisfy_current_model_gate():
    events = event_series(60, model_sha=MODEL_A, spacing_days=3)
    # Keep snapshot ids unique for the second model.
    start = datetime(2026, 1, 2, 12, tzinfo=timezone.utc)
    for index in range(60):
        registration, settlement = lifecycle_pair(
            1000 + index,
            kickoff=start + timedelta(days=index * 3),
            model_sha=MODEL_B,
        )
        events.extend((registration, settlement))

    matrix = build_reliability_matrix(events)
    assert matrix["overall_history"]["settled_predictions"] == 120
    assert (
        matrix["overall_history"]["evidence_gate"]["state"]
        == EVIDENCE_DESCRIPTIVE_ONLY
    )
    assert len(matrix["model_league_slices"]) == 2
    assert all(
        item["evidence_gate"]["state"] == EVIDENCE_ACCUMULATING_SAMPLE
        for item in matrix["model_league_slices"]
    )


def test_reliability_recomputes_scoring_metrics_from_frozen_probabilities():
    registration, settlement = lifecycle_pair(
        1,
        kickoff=datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
        actual_outcome="AWAY",
    )
    settlement["payload"]["multiclass_brier"] += 0.01

    with pytest.raises(ValueError, match="multiclass_brier disagrees"):
        settled_reliability_records([registration, settlement])


def test_reliability_rejects_settlement_without_registration():
    _registration, settlement = lifecycle_pair(
        1,
        kickoff=datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
    )
    with pytest.raises(ValueError, match="no PREDICTION_REGISTERED"):
        settled_reliability_records([settlement])


def test_multiple_settlement_facts_fail_closed_until_correction_contract_exists():
    registration, settlement = lifecycle_pair(
        1,
        kickoff=datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
    )
    duplicate = dict(settlement)
    duplicate["payload"] = dict(settlement["payload"])

    with pytest.raises(ValueError, match="multiple SETTLED facts"):
        settled_reliability_records([registration, settlement, duplicate])


def test_calibration_metrics_are_descriptive_and_use_wilson_uncertainty():
    events = []
    first = lifecycle_pair(
        1,
        kickoff=datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
        actual_outcome="HOME",
    )
    second = lifecycle_pair(
        2,
        kickoff=datetime(2026, 1, 2, 12, tzinfo=timezone.utc),
        actual_outcome="AWAY",
    )
    events.extend(first)
    events.extend(second)
    records = settled_reliability_records(events)
    report = reliability_summary(records, league="EPL", model_1x2_sha256=MODEL_A)

    assert report["metrics"]["accuracy"] == pytest.approx(0.5)
    assert report["metrics"]["top_pick_expected_calibration_error"] == pytest.approx(0.1)
    bucket = report["metrics"]["calibration"][0]
    assert bucket["bucket"] == "60-70%"
    assert bucket["n"] == 2
    assert bucket["mean_predicted_probability"] == pytest.approx(0.6)
    assert bucket["empirical_hit_rate"] == pytest.approx(0.5)
    assert bucket["mean_prediction_inside_hit_rate_wilson_95"] is True
    assert "descriptive_only" in bucket["interpretation"]


def test_wilson_interval_has_no_fake_value_for_empty_bucket():
    assert wilson_interval(0, 0) is None
    lower, upper = wilson_interval(5, 10)
    assert 0.0 < lower < 0.5 < upper < 1.0


def test_exact_filter_does_not_borrow_other_league_evidence():
    epl_events = event_series(80, model_sha=MODEL_A, league="EPL", spacing_days=3)
    la_liga_events = []
    for index in range(80):
        pair = lifecycle_pair(
            2000 + index,
            kickoff=datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
            + timedelta(days=index * 3),
            model_sha=MODEL_A,
            league="LA_LIGA",
        )
        la_liga_events.extend(pair)

    records = settled_reliability_records(epl_events + la_liga_events)
    report = reliability_summary(records, league="EPL", model_1x2_sha256=MODEL_A)

    assert report["settled_predictions"] == 80
    assert report["evidence_gate"]["state"] == EVIDENCE_ACCUMULATING_SAMPLE
