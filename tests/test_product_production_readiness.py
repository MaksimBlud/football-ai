import pytest

from product_markets import build_product_market_view, fixture_key
from product_production_readiness import (
    PRODUCTION_READINESS_VERSION,
    STATUS_BLOCKED,
    STATUS_OPERATIONAL,
    STATUS_PROVISIONAL,
    STATUS_RESEARCH_ONLY,
    STATUS_REVIEWABLE,
    build_production_readiness_view,
    evaluate_scope_readiness,
)


def observation(**overrides):
    value = {
        "fixture_count": 10,
        "stable_identity_count": 10,
        "complete_model_probability_count": 10,
        "complete_bookmaker_price_count": 10,
        "stable_identity_complete": True,
        "model_probability_complete": True,
        "bookmaker_price_complete": True,
    }
    value.update(overrides)
    return value


def reviewable_reliability():
    return {
        "attached": True,
        "state": "REVIEWABLE",
        "reviewable": True,
        "verdict": "INCONCLUSIVE",
        "settled_predictions": 100,
    }


def prediction(**overrides):
    row = {
        "league": "EPL",
        "event_id": "fixture-1",
        "commence_time_utc": "2026-09-13T15:30:00+00:00",
        "match_date": "2026-09-13",
        "match_time": "16:30",
        "home_team": "Manchester United",
        "away_team": "Manchester City",
        "home_team_model": "Manchester United",
        "away_team_model": "Manchester City",
        "home_probability": 0.405,
        "draw_probability": 0.239,
        "away_probability": 0.356,
        "over_2_5_probability": None,
        "under_2_5_probability": None,
    }
    row.update(overrides)
    return row


def test_existing_epl_1x2_baseline_remains_operational_without_fake_reliability_pass():
    result = evaluate_scope_readiness(
        league="EPL",
        market="1x2",
        observation=observation(),
        reliability={
            "attached": False,
            "state": "NOT_ATTACHED",
            "reviewable": False,
            "verdict": None,
        },
    )

    assert result["status"] == STATUS_OPERATIONAL
    assert result["approved_operational_scope"] is True
    assert result["reliability"]["reviewable"] is False
    assert result["reliability"]["verdict"] is None
    assert result["automatic_effects"]["promotes_market"] is False
    assert result["automatic_effects"]["changes_decision_tier"] is False


def test_existing_operational_scope_fails_closed_when_live_price_gate_regresses():
    result = evaluate_scope_readiness(
        league="EPL",
        market="1x2",
        observation=observation(
            complete_bookmaker_price_count=0,
            bookmaker_price_complete=False,
        ),
        reliability={"attached": False, "state": "NOT_ATTACHED", "reviewable": False},
    )

    assert result["status"] == STATUS_BLOCKED
    assert "live_price_coverage" in result["open_gates"]
    assert result["approved_operational_scope"] is True


def test_new_1x2_scope_with_all_objective_gates_is_only_reviewable_until_approved():
    result = evaluate_scope_readiness(
        league="LA_LIGA",
        market="1x2",
        observation=observation(),
        reliability=reviewable_reliability(),
    )

    assert result["status"] == STATUS_REVIEWABLE
    assert result["approved_operational_scope"] is False
    assert result["open_gates"] == []
    assert "Explicit approval" in result["reason"]
    assert result["automatic_effects"]["promotes_market"] is False


def test_new_1x2_scope_without_empirical_review_stays_provisional():
    result = evaluate_scope_readiness(
        league="LA_LIGA",
        market="1x2",
        observation=observation(),
        reliability={
            "attached": True,
            "state": "ACCUMULATING_SAMPLE",
            "reviewable": False,
            "verdict": "INCONCLUSIVE",
        },
    )

    assert result["status"] == STATUS_PROVISIONAL
    assert "empirical_reliability" in result["open_gates"]


def test_total_goals_cannot_become_reviewable_before_price_settlement_and_lifecycle_contracts():
    result = evaluate_scope_readiness(
        league="EPL",
        market="total_goals",
        observation=observation(),
        reliability=reviewable_reliability(),
    )

    assert result["status"] == STATUS_PROVISIONAL
    assert "bookmaker_price_contract" in result["open_gates"]
    assert "settlement_contract" in result["open_gates"]
    assert "lifecycle_contract" in result["open_gates"]


@pytest.mark.parametrize("market", ["handicap", "corners_total"])
def test_research_only_market_cannot_be_promoted_by_good_observed_numbers(market):
    result = evaluate_scope_readiness(
        league="EPL",
        market=market,
        observation=observation(),
        reliability=reviewable_reliability(),
    )

    assert result["status"] == STATUS_RESEARCH_ONLY
    assert result["approved_operational_scope"] is False
    assert result["automatic_effects"]["promotes_market"] is False


def test_live_product_view_exposes_four_epl_scope_states_without_reading_outcomes():
    row = prediction()
    odds = {
        fixture_key(row): {
            "home_odds": 3.12,
            "draw_odds": 3.85,
            "away_odds": 2.10,
        }
    }
    product_view = build_product_market_view([row], odds_by_fixture=odds)
    readiness = product_view["production_readiness"]

    assert readiness["schema_version"] == PRODUCTION_READINESS_VERSION
    assert readiness["policy"]["reads_research_outcomes"] is False
    assert readiness["policy"]["reviewable_auto_promotes_to_operational"] is False

    by_market = {scope["market"]: scope for scope in readiness["scopes"]}
    assert by_market["1x2"]["status"] == STATUS_OPERATIONAL
    assert by_market["1x2"]["observation"]["fixture_count"] == 1
    assert by_market["1x2"]["observation"]["bookmaker_price_complete"] is True
    assert by_market["1x2"]["reliability"]["state"] == "NOT_ATTACHED"

    assert by_market["total_goals"]["status"] == STATUS_PROVISIONAL
    assert by_market["total_goals"]["observation"]["model_probability_complete"] is False
    assert by_market["handicap"]["status"] == STATUS_RESEARCH_ONLY
    assert by_market["corners_total"]["status"] == STATUS_RESEARCH_ONLY

    assert readiness["status_counts"] == {
        "RESEARCH_ONLY": 2,
        "PROVISIONAL": 1,
        "REVIEWABLE": 0,
        "OPERATIONAL": 1,
        "BLOCKED": 0,
    }


def test_external_reliability_attachment_can_make_unapproved_scope_reviewable_but_not_operational():
    row = prediction(league="LA_LIGA", event_id="laliga-1")
    odds = {
        fixture_key(row): {
            "home_odds": 2.10,
            "draw_odds": 3.30,
            "away_odds": 3.50,
        }
    }
    product_view = build_product_market_view([row], odds_by_fixture=odds)
    readiness = build_production_readiness_view(
        product_view,
        reliability_by_scope={
            "LA_LIGA": {
                "1x2": {
                    "settled_predictions": 100,
                    "evidence_gate": {"state": "REVIEWABLE", "reviewable": True},
                    "reliability_verdict": {"status": "INCONCLUSIVE"},
                }
            }
        },
    )

    one_x_two = next(scope for scope in readiness["scopes"] if scope["market"] == "1x2")
    assert one_x_two["status"] == STATUS_REVIEWABLE
    assert one_x_two["approved_operational_scope"] is False
    assert one_x_two["reliability"]["verdict"] == "INCONCLUSIVE"
