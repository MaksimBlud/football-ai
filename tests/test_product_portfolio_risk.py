from copy import deepcopy

from product_portfolio_risk import (
    PORTFOLIO_RISK_SCHEMA_VERSION,
    STATUS_BLOCKED,
    STATUS_NO_ACTIONABLE_EXPOSURE,
    STATUS_UNSIZED,
    VIOLATION_CONFLICTING_MARKET,
    VIOLATION_DUPLICATE,
    VIOLATION_MALFORMED_BET,
    VIOLATION_SAME_FIXTURE,
    VIOLATION_UNAPPROVED_STAKE,
    VIOLATION_UNSUPPORTED_BET_STATUS,
    build_portfolio_risk_view,
)


def selection(code="HOME", label="Home", probability=0.6, ev=0.08):
    return {
        "code": code,
        "label": label,
        "probability": probability,
        "fair_odds": 1 / probability,
        "bookmaker_odds": 1.8,
        "raw_expected_value": ev,
    }


def match(
    match_id,
    *,
    event_id=None,
    league="EPL",
    home="Home FC",
    away="Away FC",
    main_market="1x2",
    main_selection=None,
    value_market=None,
    value_selection=None,
    bet_decision=None,
    alternatives=None,
):
    main_selection = main_selection or selection()
    item = {
        "match": {
            "product_match_id": match_id,
            "event_id": event_id or match_id,
            "league": league,
            "commence_time_utc": "2026-09-20T14:00:00+00:00",
            "home_team": home,
            "away_team": away,
        },
        "main_forecast": {
            "status": "model_forecast",
            "market": main_market,
            "selection": main_selection,
        },
        "alternatives": alternatives or [],
        "value_signal": {
            "status": "none",
            "market": None,
            "selection": None,
        },
        "bet_decision": bet_decision or {
            "status": "no_bet",
            "selection": None,
        },
    }
    if value_selection is not None:
        item["value_signal"] = {
            "status": "positive_raw_ev",
            "market": value_market or main_market,
            "selection": value_selection,
        }
    return item


def view(matches):
    return {"schema_version": "product-market-view.v1", "matches": matches}


def violation_codes(report):
    return {item["code"] for item in report["actionable_portfolio"]["violations"]}


def test_forecasts_and_value_signals_do_not_create_exposure():
    report = build_portfolio_risk_view(
        view(
            [
                match(
                    "event_1",
                    value_selection=selection(
                        code="AWAY", label="Away", probability=0.2, ev=0.25
                    ),
                )
            ]
        )
    )

    assert report["schema_version"] == PORTFOLIO_RISK_SCHEMA_VERSION
    assert report["status"] == STATUS_NO_ACTIONABLE_EXPOSURE
    assert report["signal_inventory"]["main_forecast_count"] == 1
    assert report["signal_inventory"]["value_signal_count"] == 1
    assert report["actionable_portfolio"]["position_count"] == 0
    assert report["actionable_portfolio"]["risk_slot_count"] == 0
    assert report["monetary_exposure"]["available"] is False
    assert report["monetary_exposure"]["total_stake"] is None


def test_same_fixture_visible_signals_are_clustered_not_aggregated():
    report = build_portfolio_risk_view(
        view(
            [
                match(
                    "event_1",
                    value_selection=selection(code="AWAY", probability=0.2, ev=0.3),
                )
            ]
        )
    )
    clusters = report["signal_inventory"]["same_fixture_signal_clusters"]

    assert len(clusters) == 1
    assert clusters[0]["product_match_id"] == "event_1"
    assert clusters[0]["signal_count"] == 2
    assert clusters[0]["correlation_status"] == "UNKNOWN_NOT_INDEPENDENT"
    assert clusters[0]["probability_or_ev_aggregation_allowed"] is False
    assert report["policy"]["raw_ev_aggregation_across_signals_allowed"] is False


def test_exact_duplicate_actionable_position_is_blocked():
    bet = {"status": "bet", "market": "1x2", "selection": selection()}
    first = match("event_1", bet_decision=deepcopy(bet))
    duplicate = match("event_1", bet_decision=deepcopy(bet))

    report = build_portfolio_risk_view(view([first, duplicate]))

    assert report["status"] == STATUS_BLOCKED
    assert VIOLATION_DUPLICATE in violation_codes(report)


def test_two_different_markets_on_same_fixture_are_blocked_until_covariance_exists():
    first = match(
        "event_1",
        bet_decision={"status": "bet", "market": "1x2", "selection": selection()},
    )
    second = match(
        "event_1",
        main_market="total_goals",
        main_selection=selection(code="OVER_2_5", label="Over 2.5", probability=0.65),
        bet_decision={
            "status": "bet",
            "market": "total_goals",
            "selection": selection(code="OVER_2_5", label="Over 2.5", probability=0.65),
        },
    )

    report = build_portfolio_risk_view(view([first, second]))

    assert report["status"] == STATUS_BLOCKED
    assert VIOLATION_SAME_FIXTURE in violation_codes(report)
    assert report["policy"]["same_fixture_covariance_model_available"] is False
    assert report["policy"]["max_actionable_risk_slots_per_fixture"] == 1


def test_conflicting_selections_same_market_are_blocked():
    home = match(
        "event_1",
        bet_decision={"status": "bet", "market": "1x2", "selection": selection("HOME")},
    )
    away = match(
        "event_1",
        main_selection=selection("AWAY", "Away", 0.25),
        bet_decision={
            "status": "bet",
            "market": "1x2",
            "selection": selection("AWAY", "Away", 0.25),
        },
    )

    report = build_portfolio_risk_view(view([home, away]))

    assert report["status"] == STATUS_BLOCKED
    codes = violation_codes(report)
    assert VIOLATION_CONFLICTING_MARKET in codes
    assert VIOLATION_SAME_FIXTURE in codes


def test_unapproved_stake_or_kelly_input_is_blocked():
    report = build_portfolio_risk_view(
        view(
            [
                match(
                    "event_1",
                    bet_decision={
                        "status": "bet",
                        "market": "1x2",
                        "selection": {**selection(), "stake_units": 2.0},
                        "kelly_fraction": 0.25,
                    },
                )
            ]
        )
    )

    assert report["status"] == STATUS_BLOCKED
    assert VIOLATION_UNAPPROVED_STAKE in violation_codes(report)
    violation = next(
        item
        for item in report["actionable_portfolio"]["violations"]
        if item["code"] == VIOLATION_UNAPPROVED_STAKE
    )
    assert violation["fields"] == ["kelly_fraction", "stake_units"]
    assert report["policy"]["kelly_sizing_enabled"] is False


def test_distinct_fixtures_form_only_an_unsized_structural_portfolio():
    first = match(
        "event_1",
        home="Arsenal",
        away="Chelsea",
        bet_decision={"status": "bet", "market": "1x2", "selection": selection()},
    )
    second = match(
        "event_2",
        home="Liverpool",
        away="Fulham",
        bet_decision={
            "status": "bet",
            "market": "1x2",
            "selection": selection("AWAY", "Away", 0.3),
        },
    )

    report = build_portfolio_risk_view(view([first, second]))

    assert report["status"] == STATUS_UNSIZED
    assert report["actionable_portfolio"]["position_count"] == 2
    assert report["actionable_portfolio"]["risk_slot_count"] == 2
    assert report["actionable_portfolio"]["violations"] == []
    concentration = report["actionable_portfolio"]["concentration"]
    assert concentration["league_position_counts"] == {"EPL": 2}
    assert concentration["team_position_counts"]["Arsenal"] == 1
    assert concentration["league_money_cap_defined"] is False
    assert report["monetary_exposure"]["bankroll_fraction"] is None


def test_unsupported_bet_status_fails_closed():
    report = build_portfolio_risk_view(
        view([match("event_1", bet_decision={"status": "recommended"})])
    )

    assert report["status"] == STATUS_BLOCKED
    assert VIOLATION_UNSUPPORTED_BET_STATUS in violation_codes(report)
    assert report["actionable_portfolio"]["position_count"] == 0


def test_malformed_bet_decision_fails_closed():
    report = build_portfolio_risk_view(
        view([match("event_1", bet_decision={"status": "bet", "selection": selection()})])
    )

    assert report["status"] == STATUS_BLOCKED
    assert VIOLATION_MALFORMED_BET in violation_codes(report)


def test_portfolio_layer_has_no_automatic_product_or_model_effects():
    report = build_portfolio_risk_view(view([match("event_1")]))

    assert not any(report["automatic_effects"].values())
    assert report["policy"]["forecast_is_position"] is False
    assert report["policy"]["value_signal_is_position"] is False
    assert report["policy"]["stake_sizing_policy_defined"] is False
    assert report["policy"]["bankroll_policy_defined"] is False
