# Frozen point-in-time 1X2 snapshot cadence protocol

Status: **PREREGISTERED / OUTCOME-FREE / SOURCE-GATED / RESEARCH ONLY / NO_BET**.

Fixed leagues: EPL, La Liga, Serie A, Bundesliga and Ligue 1. Fixed market: grouped pre-match H2H only. Fixed 30-day allowance: 500 credits, 100-credit hard reserve, 400 spendable; one league-wide batch is the planning unit and costs one credit. No paid provider call is permitted to verify that assumption.

Compare exactly P0 current 12h/6h/4h/2h adaptive logic, P1 full five-league sweep every 12h, P2 full sweep every 9h and P3 T-72/T-48/T-24/T-12/T-6/T-3/T-1 league windows. Before comparison, require repository timestamp provenance for league, event_id, snapshot_time_utc and commence_time_utc. Snapshot-only rows cannot prove missed-fixture coverage; fail closed without a complete timestamp-safe fixture universe.

Use only source coverage, scheduled opportunities, freshness and deterministic credit arithmetic. Do not load outcomes, 2026/27 reserved targets, odds values for performance, ROI, CLV or betting fields. No API/network call, Supabase read/write, production workflow/schedule change, .pkl operation, deployment or automatic promotion.
