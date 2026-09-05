"""Shared immutable policy constants for Multi-Market research workflows.

This module intentionally has no database, provider, pandas, or environment
side effects so safety/readiness code can import policy offline.
"""

# Preserve enough monthly quota for diagnostics/emergencies even while research
# collection is manually active.
HARD_RESERVE_CREDITS = 100

# Card V1 consumes four event market keys in one EU region. The Odds API bills
# event odds by unique markets returned x regions, so four credits is the
# conservative maximum cost of one current event request.
EVENT_REQUEST_MAX_CREDITS = 4
DEFAULT_MAX_CREDITS_PER_MANUAL_CYCLE = 4

# Readiness means there is enough quota for one worst-case current event request
# without crossing the hard reserve. It does NOT activate collection.
MIN_COLLECTION_REMAINING_CREDITS = HARD_RESERVE_CREDITS + EVENT_REQUEST_MAX_CREDITS

# Compatibility aliases for older reporting/tests. Values now represent credits,
# not HTTP request counts.
START_MIN_REQUESTS_REMAINING = MIN_COLLECTION_REMAINING_CREDITS
HARD_RESERVE_REQUESTS = HARD_RESERVE_CREDITS

# Current-season public Football-Data CSV corner outcomes have been live-audited
# with complete HC/AC coverage for finished rows in these seven leagues.
CORNER_SOURCE_READY_LEAGUES = (
    "LA_LIGA",
    "SERIE_A",
    "BUNDESLIGA",
    "LIGUE_1",
    "EREDIVISIE",
    "TURKEY_SUPER_LIG",
    "PRIMEIRA_LIGA",
)
