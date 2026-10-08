"""Offline safety tests. No API, database or secrets required."""
from datetime import datetime, timezone

import pytest

from odds_h2h_batch_dry_run import (
    CANDIDATE_LEAGUES,
    HARD_RESERVE_CREDITS,
    plan_h2h_batches,
)


def t(hour=12, day=5):
    return datetime(2026, 10, day, hour, 0, tzinfo=timezone.utc)


def test_one_league_request_handles_all_events_and_preserves_no_paid_calls():
    r = plan_h2h_batches(now_utc=t(), provider_used=12, provider_remaining=488)
    assert r["mode"] == "OFFLINE_DRY_RUN_ONLY"
    assert r["paid_provider_requests"] == 0
    assert r["paid_collection_authorized"] is False
    assert r["max_planned_credits_this_slot"] == 1
    assert len(r["leagues"]) == 1
    assert r["leagues"][0]["reason"] == "DRY_RUN_ELIGIBLE"
    assert "ALL available fixtures" in r["leagues"][0]["request_scope"]


def test_no_provider_counters_means_no_budget_authorization():
    r = plan_h2h_batches(now_utc=t())
    assert r["max_planned_credits_this_slot"] == 0
    assert r["leagues"][0]["reason"] == "QUOTA_UNVERIFIED"


def test_worst_case_eight_league_window_uses_eight_credits_not_events():
    r = plan_h2h_batches(
        now_utc=t(), leagues=CANDIDATE_LEAGUES,
        provider_used=0, provider_remaining=500,
    )
    assert r["max_planned_credits_this_slot"] == 8
    assert r["paid_provider_credits"] == 0


def test_other_paid_consumers_count_toward_same_80_credit_cap():
    r = plan_h2h_batches(
        now_utc=t(), leagues=CANDIDATE_LEAGUES,
        provider_used=79, provider_remaining=421,
    )
    assert r["max_planned_credits_this_slot"] == 1
    assert r["leagues"][0]["reason"] == "DRY_RUN_ELIGIBLE"
    assert all(x["reason"] == "SHARED_BILLING_CYCLE_CAP_REACHED" or x["reason"] == "RESERVE_OR_SHARED_CAP_PROTECTED" for x in r["leagues"][1:])


def test_hard_reserve_is_protected_even_with_room_under_shared_cap():
    r = plan_h2h_batches(
        now_utc=t(), provider_used=10,
        provider_remaining=HARD_RESERVE_CREDITS,
    )
    assert r["max_planned_credits_this_slot"] == 0
    assert r["leagues"][0]["reason"] == "RESERVE_OR_SHARED_CAP_PROTECTED"


def test_no_duplicate_poll_in_same_48_hour_window():
    r = plan_h2h_batches(
        now_utc=t(), provider_used=10, provider_remaining=490,
        last_snapshots={"EPL": "2026-10-04T13:00:00Z"},
    )
    assert r["leagues"][0]["reason"] == "SNAPSHOT_RECENT"


def test_outside_slot_prevents_refresh():
    r = plan_h2h_batches(now_utc=t(day=6), provider_used=0, provider_remaining=500)
    assert r["leagues"][0]["reason"] == "OUTSIDE_MON_FRI_12UTC_SLOT"


def test_time_in_future_fails_closed():
    r = plan_h2h_batches(
        now_utc=t(), provider_used=0, provider_remaining=500,
        last_snapshots={"EPL": "2026-10-10T00:00:00Z"},
    )
    assert r["leagues"][0]["reason"] == "FUTURE_SNAPSHOT_TIMESTAMP"


@pytest.mark.parametrize("args", [
    {"leagues": ("EPL", "EPL")},
    {"leagues": ("NOT_A_REAL_LEAGUE",)},
    {"provider_used": -1, "provider_remaining": 500},
    {"provider_used": 2},
    {"last_snapshots": {"SERIE_A": "2026-10-01T00:00:00Z"}},
])
def test_invalid_input_fails_closed(args):
    with pytest.raises(ValueError):
        plan_h2h_batches(now_utc=t(), **args)


def test_naive_datetime_fails_closed():
    with pytest.raises(ValueError):
        plan_h2h_batches(now_utc=datetime(2026, 10, 5, 12))
