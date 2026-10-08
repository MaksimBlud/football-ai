"""Offline, zero-request proposal for economical league-wide The Odds API H2H polling.

This is NOT an API client or an acquisition scheduler. Existing paid collectors
remain manual-only until a separate explicit approval and reviewed activation.
There are deliberately no HTTP, database, credential or model imports.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone, timedelta

from multi_market_policy import HARD_RESERVE_CREDITS

# Eight operational MARKET_ONLY leagues; the public site's default scope is EPL.
CANDIDATE_LEAGUES = (
    "EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA", "LIGUE_1",
    "EREDIVISIE", "TURKEY_SUPER_LIG", "PRIMEIRA_LIGA",
)
DEFAULT_LEAGUES = ("EPL",)
DAYS_UTC = frozenset({0, 4})  # Monday / Friday
SLOT_UTC_HOUR = 12
MIN_GAP_HOURS = 48
MAX_SHARED_BILLING_CYCLE_CREDITS = 80
CREDITS_PER_H2H_LEAGUE_BATCH = 1


def _utc(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timestamps must have an explicit UTC offset")
    return dt.astimezone(timezone.utc)


def plan_h2h_batches(
    *,
    now_utc: datetime,
    leagues: tuple[str, ...] = DEFAULT_LEAGUES,
    last_snapshots: dict[str, str | datetime] | None = None,
    provider_used: int | None = None,
    provider_remaining: int | None = None,
) -> dict:
    """Evaluate one offline slot using actual provider billing-cycle counters.

    Counters must be sourced from provider headers, NOT estimated by counting
    GitHub jobs. Other provider consumers share these counters. This planner
    never creates authorization or performs a request.
    """
    now = _utc(now_utc)
    if not leagues or len(set(leagues)) != len(leagues):
        raise ValueError("expected nonempty, unique league list")
    if any(league not in CANDIDATE_LEAGUES for league in leagues):
        raise ValueError("unknown league; fail closed")
    if (provider_used is None) != (provider_remaining is None):
        raise ValueError("provider used and remaining must both be supplied")
    if provider_used is not None and (provider_used < 0 or provider_remaining < 0):
        raise ValueError("provider counters cannot be negative")
    latest = last_snapshots or {}
    if any(league not in leagues for league in latest):
        raise ValueError("snapshot refers to league outside this plan")

    slot = now.weekday() in DAYS_UTC and now.hour == SLOT_UTC_HOUR
    quota_known = provider_used is not None
    billing_cycle_room = (
        max(0, MAX_SHARED_BILLING_CYCLE_CREDITS - provider_used)
        if quota_known else 0
    )
    reserve_room = (
        max(0, provider_remaining - HARD_RESERVE_CREDITS)
        if quota_known else 0
    )
    affordable = min(billing_cycle_room, reserve_room)
    rows = []
    for league in leagues:
        last = _utc(latest[league]) if league in latest else None
        if last is not None and last > now:
            reason = "FUTURE_SNAPSHOT_TIMESTAMP"
        elif not slot:
            reason = "OUTSIDE_MON_FRI_12UTC_SLOT"
        elif last is not None and now - last < timedelta(hours=MIN_GAP_HOURS):
            reason = "SNAPSHOT_RECENT"
        elif not quota_known:
            reason = "QUOTA_UNVERIFIED"
        elif provider_used >= MAX_SHARED_BILLING_CYCLE_CREDITS:
            reason = "SHARED_BILLING_CYCLE_CAP_REACHED"
        elif affordable < CREDITS_PER_H2H_LEAGUE_BATCH:
            reason = "RESERVE_OR_SHARED_CAP_PROTECTED"
        else:
            reason = "DRY_RUN_ELIGIBLE"
            affordable -= CREDITS_PER_H2H_LEAGUE_BATCH
        rows.append({
            "league": league,
            "reason": reason,
            "would_cost_at_most_credits": (
                CREDITS_PER_H2H_LEAGUE_BATCH if reason == "DRY_RUN_ELIGIBLE" else 0
            ),
            "request_scope": "single region=uk; single market=h2h; ALL available fixtures",
        })
    return {
        "schema_version": "WEBSITE_H2H_BATCH_BUDGET_DRY_RUN_V1",
        "as_of_utc": now.isoformat(),
        "mode": "OFFLINE_DRY_RUN_ONLY",
        "paid_collection_authorized": False,
        "paid_provider_requests": 0,
        "paid_provider_credits": 0,
        "slot": "Monday/Friday 12:00–12:59 UTC",
        "monthly_plan_note": "provider billing-cycle counter; not assumed calendar month",
        "shared_billing_cycle_cap_credits": MAX_SHARED_BILLING_CYCLE_CREDITS,
        "hard_reserve_credits": HARD_RESERVE_CREDITS,
        "provider_counters_verified_by_caller": quota_known,
        "max_planned_credits_this_slot": sum(
            row["would_cost_at_most_credits"] for row in rows
        ),
        "leagues": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline preview only; never calls paid or free provider endpoints."
    )
    parser.add_argument("--now-utc", default=datetime.now(timezone.utc).isoformat())
    parser.add_argument("--leagues", default="EPL", help="comma-separated league IDs")
    parser.add_argument("--provider-used", type=int, default=None)
    parser.add_argument("--provider-remaining", type=int, default=None)
    parser.add_argument(
        "--last-snapshot", action="append", default=[],
        metavar="LEAGUE=UTC_TIMESTAMP",
    )
    args = parser.parse_args()
    snapshots = {}
    for item in args.last_snapshot:
        league, sep, timestamp = item.partition("=")
        if not sep or not timestamp or league in snapshots:
            parser.error("last-snapshot must be unique LEAGUE=UTC_TIMESTAMP")
        snapshots[league] = timestamp
    report = plan_h2h_batches(
        now_utc=_utc(args.now_utc),
        leagues=tuple(x.strip() for x in args.leagues.split(",")),
        provider_used=args.provider_used,
        provider_remaining=args.provider_remaining,
        last_snapshots=snapshots,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
