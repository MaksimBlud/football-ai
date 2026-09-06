from multi_market_sampling_plan import plan_collection
from multi_market_policy import HARD_RESERVE_CREDITS


def _event(league, event_id, kickoff):
    return {
        "league": league,
        "event_id": event_id,
        "home_team": f"{event_id}-H",
        "away_team": f"{event_id}-A",
        "commence_time_utc": kickoff,
    }


def test_live_style_195_credit_window_plans_all_19_ready_events_for_50_credits():
    events = [
        _event("EREDIVISIE", "ned-1", "2026-09-06T10:15:00Z"),
        _event("EREDIVISIE", "ned-2", "2026-09-06T12:30:00Z"),
        _event("EREDIVISIE", "ned-3", "2026-09-06T13:30:00Z"),
        _event("EREDIVISIE", "ned-4", "2026-09-06T14:45:00Z"),
        _event("RPL", "rpl-1", "2026-09-06T11:00:00Z"),
        _event("RPL", "rpl-2", "2026-09-06T12:00:00Z"),
        _event("RPL", "rpl-3", "2026-09-06T15:30:00Z"),
        _event("RPL", "rpl-4", "2026-09-06T17:45:00Z"),
        _event("EPL", "epl-1", "2026-09-06T13:00:00Z"),
        _event("EPL", "epl-2", "2026-09-06T15:30:00Z"),
        _event("LIGUE_1", "fra-1", "2026-09-06T13:00:00Z"),
        _event("LIGUE_1", "fra-2", "2026-09-06T15:00:00Z"),
        _event("LIGUE_1", "fra-3", "2026-09-06T18:45:00Z"),
        _event("SERIE_A", "ita-1", "2026-09-06T13:00:00Z"),
        _event("SERIE_A", "ita-2", "2026-09-06T15:00:00Z"),
        _event("SERIE_A", "ita-3", "2026-09-06T17:00:00Z"),
        _event("SERIE_A", "ita-4", "2026-09-06T18:45:00Z"),
        _event("BUNDESLIGA", "ger-1", "2026-09-06T13:30:00Z"),
        _event("BUNDESLIGA", "ger-2", "2026-09-06T15:30:00Z"),
        _event("LA_LIGA", "esp-1", "2026-09-06T14:15:00Z"),
        _event("LA_LIGA", "esp-2", "2026-09-06T16:30:00Z"),
        _event("LA_LIGA", "esp-3", "2026-09-06T18:00:00Z"),
        _event("LA_LIGA", "esp-4", "2026-09-06T19:00:00Z"),
    ]
    plan = plan_collection(events, remaining_credits=195)
    assert plan["source_events"] == 23
    assert plan["eligible_events"] == 19
    assert plan["skipped_no_corner_source"] == 4
    assert plan["planned_events"] == 19
    assert plan["planned_leagues"] == ["EREDIVISIE", "EPL", "LIGUE_1", "SERIE_A", "BUNDESLIGA", "LA_LIGA"]
    assert plan["planned_credits_worst_case"] == 50
    assert plan["worst_case_remaining_credits"] == 145
    assert plan["hard_reserve_preserved"] is True
    assert plan["plan_complete_for_eligible_window"] is True
    assert plan["paid_provider_requests"] == 0
    assert plan["writes_performed"] is False


def test_explicit_credit_cap_stops_before_crossing_cap_and_keeps_league_batching():
    events = [
        _event("LA_LIGA", "la-1", "1"),
        _event("EPL", "epl-1", "2"),
        _event("LA_LIGA", "la-2", "3"),
        _event("LA_LIGA", "la-3", "4"),
        _event("EPL", "epl-2", "5"),
    ]
    plan = plan_collection(events, remaining_credits=195, max_paid_credits=8)
    assert [(row["league"], row["event_id"]) for row in plan["events"]] == [
        ("LA_LIGA", "la-1"),
        ("LA_LIGA", "la-2"),
        ("LA_LIGA", "la-3"),
    ]
    assert plan["planned_credits_worst_case"] == 8
    assert plan["worst_case_remaining_credits"] == 187
    assert plan["plan_complete_for_eligible_window"] is False


def test_hard_reserve_cannot_be_crossed_even_when_requested_cap_is_large():
    events = [_event("LA_LIGA", f"la-{i}", str(i)) for i in range(1, 20)]
    plan = plan_collection(events, remaining_credits=HARD_RESERVE_CREDITS + 5, max_paid_credits=999)
    assert plan["available_headroom_credits"] == 5
    assert plan["effective_max_paid_credits"] == 5
    assert plan["planned_events"] == 1
    assert plan["planned_credits_worst_case"] == 4
    assert plan["worst_case_remaining_credits"] == HARD_RESERVE_CREDITS + 1
    assert plan["hard_reserve_preserved"] is True


def test_rpl_only_window_produces_zero_credit_plan():
    plan = plan_collection([_event("RPL", "rpl-1", "1")], remaining_credits=195)
    assert plan["eligible_events"] == 0
    assert plan["skipped_no_corner_source"] == 1
    assert plan["planned_events"] == 0
    assert plan["planned_credits_worst_case"] == 0
    assert plan["worst_case_remaining_credits"] == 195


def test_invalid_credit_values_fail_closed():
    for kwargs in ({"remaining_credits": -1}, {"remaining_credits": 195, "max_paid_credits": -1}):
        try:
            plan_collection([], **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid credit input must fail closed")
