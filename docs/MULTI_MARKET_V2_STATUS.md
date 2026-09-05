# Multi-Market V2 — Status

Status: **SETTLEMENT FOUNDATION IMPLEMENTED / DURABLE CONTRACT ADDED / LIVE PERSISTENCE EXTERNALLY GATED / OOS EVALUATION NOT YET ACTIVE**

Multi-Market V2 extends the research-only Multi-Market V1 snapshot layer toward `Results → Settlement → OOS Evaluation`.

## Implemented

- Pure outcome classification for 1X2, Asian handicap, goal totals, match corner totals and home/away team corner totals.
- Integer, half and quarter-line handling with `WIN`, `LOSS`, `PUSH`, `HALF_WIN`, and `HALF_LOSS` classifications.
- Strict snapshot/result identity using exact league, league-local kickoff date, home team and away team.
- No fuzzy team matching and no +/- day matching.
- Snapshot time must be strictly before kickoff.
- Append-only settlement revision contract keyed by immutable `snapshot_key` plus an outcome fingerprint.
- `GOALS_ONLY` settlement can be created from the existing canonical `league_finished_results` contract.
- A later exact corner observation creates a new `GOALS_AND_CORNERS` revision rather than updating the earlier row.
- Corner observations must carry their own exact fixture identity; bare corner counts are rejected.
- Additive migration for `league_multi_market_settlements` with read/insert-only service-role policies.

## Current external blockers

1. `league_multi_market_snapshots` was previously proven absent from the live Supabase schema. The repository contains its additive migration, but no safe automatic migration-deployment path has been proven.
2. The Odds API quota was last proven below the Multi-Market safety threshold, so no paid Multi-Market collection should run until the quota gate passes.
3. Existing canonical finished results provide goals but not home/away corner outcomes. Corner settlement therefore remains `UNSETTLED_MISSING_OUTCOME` until a timestamp-safe canonical corner-result source is established.

## Not yet claimed

- No live settlement persistence proof until the required Supabase tables exist.
- No prospective OOS evaluator activation until durable point-in-time snapshots and corresponding settled outcomes exist.
- No AI probability edge claims or `Best Bets` from these markets.
- No production model change or promotion.

All Multi-Market V2 work remains research-only.
