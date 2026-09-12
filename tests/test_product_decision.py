import pytest

from product_decision import DECISION_FRAMEWORK_VERSION, build_product_decision


def selection(code, probability, *, ev=None):
    return {
        "code": code,
        "label": code,
        "probability": probability,
        "fair_odds": None if probability is None else 1 / probability,
        "bookmaker_odds": None,
        "raw_expected_value": ev,
    }


def market(
    *,
    label,
    tier,
    confidence,
    display,
    selections=None,
    main=True,
    value=False,
    bet=False,
):
    return {
        "readiness": {
            "label": label,
            "decision_tier": tier,
            "decision_confidence": confidence,
            "eligible_for_main_forecast": main,
            "eligible_for_value": value,
            "eligible_for_bet_recommendation": bet,
        },
        "display_selection": display,
        "selections": selections if selections is not None else ([display] if display else []),
    }


def test_framework_version_and_policy_are_explicit():
    decision = build_product_decision({})
    assert decision["framework_version"] == DECISION_FRAMEWORK_VERSION == "product-decision.v1"
    assert decision["policy"]["forecast_order"] == "decision_tier_then_model_probability"
    assert decision["policy"]["value_is_independent"] is True
    assert decision["policy"]["positive_ev_implies_bet"] is False


def test_higher_tier_beats_higher_probability_from_lower_tier():
    one_x_two = selection("HOME", 0.67)
    total = selection("OVER_2_5", 0.72)
    decision = build_product_decision(
        {
            "1x2": market(
                label="Исход матча",
                tier=2,
                confidence="operational",
                display=one_x_two,
            ),
            "total_goals": market(
                label="Тотал голов",
                tier=1,
                confidence="provisional",
                display=total,
            ),
        }
    )

    assert decision["main_forecast"]["market"] == "1x2"
    assert decision["main_forecast"]["selection"]["probability"] == pytest.approx(0.67)
    assert decision["alternatives"][0]["market"] == "total_goals"
    assert decision["alternatives"][0]["selection"]["probability"] == pytest.approx(0.72)


def test_same_tier_uses_higher_model_probability():
    first = selection("HOME", 0.61)
    second = selection("OVER_2_5", 0.69)
    decision = build_product_decision(
        {
            "1x2": market(
                label="Исход матча",
                tier=2,
                confidence="operational",
                display=first,
            ),
            "total_goals": market(
                label="Тотал голов",
                tier=2,
                confidence="operational",
                display=second,
            ),
        }
    )

    assert decision["main_forecast"]["market"] == "total_goals"
    assert decision["alternatives"][0]["market"] == "1x2"


def test_value_is_generic_but_never_overrides_forecast():
    home = selection("HOME", 0.675, ev=-0.03)
    away = selection("AWAY", 0.168, ev=0.08)
    total = selection("OVER_2_5", 0.80)
    decision = build_product_decision(
        {
            "1x2": market(
                label="Исход матча",
                tier=2,
                confidence="operational",
                display=home,
                selections=[home, away],
                value=True,
            ),
            "total_goals": market(
                label="Тотал голов",
                tier=1,
                confidence="provisional",
                display=total,
            ),
        }
    )

    assert decision["main_forecast"]["selection"]["code"] == "HOME"
    assert decision["value_signal"]["selection"]["code"] == "AWAY"
    assert decision["value_signal"]["selection"]["raw_expected_value"] == pytest.approx(0.08)


def test_alternatives_are_cross_market_not_second_selection_same_market():
    home = selection("HOME", 0.55)
    draw = selection("DRAW", 0.30)
    total = selection("UNDER_2_5", 0.62)
    decision = build_product_decision(
        {
            "1x2": market(
                label="Исход матча",
                tier=2,
                confidence="operational",
                display=home,
                selections=[home, draw],
            ),
            "total_goals": market(
                label="Тотал голов",
                tier=1,
                confidence="provisional",
                display=total,
            ),
        }
    )

    codes = [item["selection"]["code"] for item in decision["alternatives"]]
    assert codes == ["UNDER_2_5"]
    assert "DRAW" not in codes


def test_research_only_market_cannot_enter_forecast_or_value_without_eligibility():
    research = selection("CORNERS_OVER", 0.91, ev=0.75)
    decision = build_product_decision(
        {
            "corners_total": market(
                label="Тотал угловых",
                tier=0,
                confidence="unavailable",
                display=research,
                main=False,
                value=False,
            )
        }
    )

    assert decision["main_forecast"]["status"] == "unavailable"
    assert decision["alternatives"] == []
    assert decision["value_signal"]["status"] == "none"
    assert decision["confidence"]["level"] == "unavailable"
    assert decision["bet_decision"]["status"] == "no_bet"


def test_positive_ev_never_creates_bet_recommendation_in_v1():
    pick = selection("HOME", 0.62, ev=0.40)
    decision = build_product_decision(
        {
            "1x2": market(
                label="Исход матча",
                tier=2,
                confidence="operational",
                display=pick,
                selections=[pick],
                value=True,
                bet=True,
            )
        }
    )

    assert decision["value_signal"]["status"] == "positive_raw_ev"
    assert decision["bet_decision"]["status"] == "no_bet"
    assert decision["bet_decision"]["selection"] is None


def test_confidence_is_readiness_state_not_calibration_claim():
    pick = selection("HOME", 0.80)
    decision = build_product_decision(
        {
            "1x2": market(
                label="Исход матча",
                tier=2,
                confidence="operational",
                display=pick,
            )
        }
    )

    assert decision["confidence"]["level"] == "operational"
    assert decision["confidence"]["model_probability"] == pytest.approx(0.80)
    assert decision["confidence"]["is_empirical_calibration_claim"] is False
