"""Synthetic and fail-closed tests for frozen product 1X2 market comparisons."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import math

import pytest

from product_market_benchmark import (
    MARKET_ROLE, MODES, SCHEMA, build_product_market_benchmark,
)

SHA = "a" * 64
OTHER_SHA = "b" * 64
ODDS = (2.4, 3.3, 3.1)
MODEL = (0.60, 0.25, 0.15)
OUTCOMES = ("HOME", "DRAW", "AWAY")
KICKOFF = datetime(2026, 10, 10, 15, tzinfo=timezone.utc)


def pair(id=1, *, mode="live_publish", outcome="HOME", sha=SHA, odds=ODDS):
    kickoff = KICKOFF + timedelta(days=id)
    created = kickoff - timedelta(hours=5)
    snapshot_time = created - timedelta(hours=1)
    actual = OUTCOMES.index(outcome)
    brier = sum((p - int(i == actual)) ** 2 for i, p in enumerate(MODEL))
    reg = {
        "event_type": "PREDICTION_REGISTERED",
        "source_prediction_snapshot_id": id,
        "product_match_id": "event_" + str(id),
        "league": "EPL", "commence_time_utc": kickoff.isoformat(),
        "source_prediction_created_at_utc": created.isoformat(),
        "payload": {
            "registration_mode": mode,
            "prediction": {
                "home_probability": MODEL[0],
                "draw_probability": MODEL[1],
                "away_probability": MODEL[2],
                "model_1x2_sha256": sha,
            },
            "market_reference_at_registration": {
                "role": MARKET_ROLE,
                "snapshot_time_utc": snapshot_time.isoformat(),
                "age_seconds_at_prediction_record": 3600,
                "is_closing_qualified": False,
                "home_odds": odds[0], "draw_odds": odds[1], "away_odds": odds[2],
            },
        },
    }
    settlement = {
        "event_type": "SETTLED",
        "source_prediction_snapshot_id": id,
        "product_match_id": "event_" + str(id),
        "league": "EPL", "commence_time_utc": kickoff.isoformat(),
        "payload": {
            "settlement_scope": "1x2_model_probability",
            "model_pick": "HOME",
            "model_pick_probability": MODEL[0],
            "actual_outcome": outcome,
            "prediction_correct": outcome == "HOME",
            "multiclass_brier": brier,
            "log_loss": -math.log(MODEL[actual]),
        },
    }
    return [reg, settlement]


def test_empty_returns_explicit_unknown_not_fake_model_success():
    result = build_product_market_benchmark([], model_sha256=SHA)
    assert result["schema_version"] == SCHEMA
    assert result["overall"]["settled_fixtures"] == 0
    assert result["overall"]["model_accuracy"] is None
    assert result["overall"]["market_accuracy"] is None
    assert result["verdict"] == "DESCRIPTIVE_ONLY_INCONCLUSIVE"
    assert result["reviewable"] is False
    assert result["roi"] is None
    assert result["clv"] is None
    assert result["no_bet"] is True


def test_market_no_vig_scores_and_paired_accuracy_are_recalculated():
    events = pair(1, mode=MODES[0], outcome="HOME") + pair(2, mode=MODES[1], outcome="DRAW")
    output = build_product_market_benchmark(events, model_sha256=SHA)
    assert output["overall"]["settled_fixtures"] == 2
    assert output["overall"]["model_correct"] == 1
    assert output["overall"]["market_correct"] == 1
    assert output["overall"]["model_pick_counts"] == {"HOME": 2, "DRAW": 0, "AWAY": 0}
    assert output["overall"]["actual_outcome_counts"] == {"HOME": 1, "DRAW": 1, "AWAY": 0}
    assert output["by_registration_mode"][MODES[0]]["settled_fixtures"] == 1
    assert output["by_registration_mode"][MODES[1]]["settled_fixtures"] == 1
    market = tuple(1.0 / n for n in ODDS)
    market = tuple(p / sum(market) for p in market)
    assert math.isclose(output["overall"]["mean_market_probabilities"]["DRAW"], market[1])
    assert math.isclose(output["overall"]["model_brier"], ((.4 ** 2 + .25 ** 2 + .15 ** 2) + (.6 ** 2 + .75 ** 2 + .15 ** 2)) / 2)
    assert output["source"].startswith("immutable PRODUCT")
    assert output["is_closing_line"] is False
    assert output["is_prospective_research"] is False
    assert output["promotion"] is False and output["training_performed"] is False
    assert output["provider_calls"] == 0
    assert "fixture_ids" not in output and "source_prediction_snapshot_ids" not in output


def test_report_refuses_to_pool_two_model_artifacts():
    events = pair(1) + pair(2, sha=OTHER_SHA)
    with pytest.raises(ValueError, match="cannot pool"):
        build_product_market_benchmark(events)
    a = build_product_market_benchmark(events, model_sha256=SHA)
    assert a["overall"]["settled_fixtures"] == 1
    assert a["model_sha256"] == SHA


def test_duplicate_fixture_and_scoring_tamper_fail_closed():
    a, b = pair()
    c, d = pair(2)
    c["product_match_id"] = a["product_match_id"]
    d["product_match_id"] = a["product_match_id"]
    with pytest.raises(ValueError, match="duplicate settled fixture"):
        build_product_market_benchmark([a, b, c, d], model_sha256=SHA)
    bad = deepcopy([a, b])
    bad[1]["payload"]["prediction_correct"] = False
    with pytest.raises(ValueError, match="settlement prediction_correct disagrees"):
        build_product_market_benchmark(bad, model_sha256=SHA)


@pytest.mark.parametrize("tamper", [
    lambda r: r["payload"].pop("market_reference_at_registration"),
    lambda r: r["payload"]["market_reference_at_registration"].update(role="closing_line"),
    lambda r: r["payload"]["market_reference_at_registration"].update(is_closing_qualified=True),
    lambda r: r["payload"]["market_reference_at_registration"].update(home_odds=1.0),
    lambda r: r["payload"]["market_reference_at_registration"].update(draw_odds=float("nan")),
    lambda r: r["payload"]["market_reference_at_registration"].update(age_seconds_at_prediction_record=-1),
    lambda r: r["payload"]["market_reference_at_registration"].update(age_seconds_at_prediction_record=0),
    lambda r: r["payload"]["market_reference_at_registration"].update(snapshot_time_utc="2026-10-12T00:00:00"),
    lambda r: r["payload"]["market_reference_at_registration"].update(snapshot_time_utc="2030-10-12T00:00:00Z"),
    lambda r: r["payload"].update(registration_mode="unknown"),
    lambda r: r.update(source_prediction_created_at_utc="2026-10-01T00:00:00"),
])
def test_unqualified_market_price_or_provenance_fails(tamper):
    rows = pair()
    tamper(rows[0])
    with pytest.raises((ValueError, TypeError)):
        build_product_market_benchmark(rows, model_sha256=SHA)


def test_rejects_bad_scope_and_artifact_hash():
    with pytest.raises(ValueError):
        build_product_market_benchmark([], league="SERIE_A", model_sha256=SHA)
    with pytest.raises(ValueError):
        build_product_market_benchmark([], model_sha256="not-a-sha")


def test_preserves_hundred_and_four_month_rules_and_no_automatic_promotion():
    assert build_product_market_benchmark(pair(), model_sha256=SHA)["sample_gate_minimum"] == 100
    assert build_product_market_benchmark(pair(), model_sha256=SHA)["calendar_gate_months"] == 4
    assert build_product_market_benchmark(pair(), model_sha256=SHA)["reviewable"] is False
