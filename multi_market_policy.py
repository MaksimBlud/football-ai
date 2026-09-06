"""Shared immutable policy constants for Multi-Market research workflows.

This module intentionally has no database, provider, pandas, or environment
side effects so safety/readiness code can import policy offline.
"""

# Preserve enough monthly quota for diagnostics/emergencies even while research
# collection is manually active.
HARD_RESERVE_CREDITS = 100

# Card V1 obtains spreads/totals once per league from the featured endpoint and
# corners/team-corners per event. With one EU region both calls cost at most two
# credits. The first collected event in a league therefore still needs at most
# four credits; subsequent events in the same league need at most two.
FEATURED_REQUEST_MAX_CREDITS = 2
EVENT_REQUEST_MAX_CREDITS = 2
FIRST_EVENT_MAX_CREDITS = FEATURED_REQUEST_MAX_CREDITS + EVENT_REQUEST_MAX_CREDITS
DEFAULT_MAX_CREDITS_PER_MANUAL_CYCLE = 4

# Readiness means there is enough quota for one complete first event without
# crossing the hard reserve. It does NOT activate collection.
MIN_COLLECTION_REMAINING_CREDITS = HARD_RESERVE_CREDITS + FIRST_EVENT_MAX_CREDITS

# Compatibility aliases for older reporting/tests. Values represent credits,
# not HTTP request counts.
START_MIN_REQUESTS_REMAINING = MIN_COLLECTION_REMAINING_CREDITS
HARD_RESERVE_REQUESTS = HARD_RESERVE_CREDITS

# Current-season public Football-Data CSV corner outcomes are only considered
# ready after the provider has actually published the canonical season source.
# Turkey 2026/27 (2627/T1.csv) is not published yet, so it must fail closed and
# cannot reach the paid Multi-Market provider until a later audited code change.
CORNER_SOURCE_READY_LEAGUES = (
    "EPL",
    "LA_LIGA",
    "SERIE_A",
    "BUNDESLIGA",
    "LIGUE_1",
    "EREDIVISIE",
    "PRIMEIRA_LIGA",
)

UNPUBLISHED_CURRENT_CORNER_SOURCE_LEAGUES = frozenset({"TURKEY_SUPER_LIG"})
