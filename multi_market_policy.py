"""Shared immutable policy constants for Multi-Market research workflows.

This module intentionally has no database, provider, pandas, or environment
side effects so safety/readiness code can import policy offline.
"""

START_MIN_REQUESTS_REMAINING = 500
HARD_RESERVE_REQUESTS = 100

CORNER_SOURCE_READY_LEAGUES = (
    "LA_LIGA",
    "EREDIVISIE",
    "TURKEY_SUPER_LIG",
    "PRIMEIRA_LIGA",
)
