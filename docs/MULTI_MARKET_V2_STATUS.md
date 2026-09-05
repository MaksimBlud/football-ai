# Multi-Market V2 — Status

Status: **SETTLEMENT + CANONICAL CORNER-OUTCOME + FROZEN OOS EVALUATOR FOUNDATIONS IMPLEMENTED / LIVE PERSISTENCE EXTERNALLY GATED / PROSPECTIVE OOS EVALUATION NOT YET ACTIVE**

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
- Canonical Football-Data `HC/AC` corner-result normalization with configured-source-only routing.
- Corner rows become canonical only after exact one-to-one reconciliation with `league_finished_results` on league/season/date/home/away and exact `FTHG/FTAG` agreement.
- Additive append-only migration for `league_corner_results`; no UPDATE/DELETE policy.
- Frozen outcome-agnostic OOS protocol `MULTI_MARKET_V2_OOS_PROTOCOL_V1`, preregistered before prospective evaluation activation.
- Exactly one latest strictly pre-kickoff snapshot per `(league,event_id)` is evaluated to prevent repeated-snapshot pseudo-replication.
- For duplicate settlement revisions, `GOALS_AND_CORNERS` is preferred over `GOALS_ONLY`; equal-completeness ambiguity fails closed.
- Exactly one canonical side per complementary market pair is scored: handicap HOME; goals/corners/team-corners OVER.
- Settlement soft targets are frozen as `WIN=1`, `HALF_WIN=.75`, `PUSH=.5`, `HALF_LOSS=.25`, `LOSS=0`.
- Soft LogLoss and Brier are reported per league/market, pooled micro, and macro over sample-ready cells.
- Sample readiness is frozen at 30 unique events / 30 usable observations per league/market cell; this is a descriptive reporting floor, not a betting/production activation threshold.
- `NOT_OFFERED`, `UNSETTLED_MISSING_OUTCOME`, `INVALID`, missing settlements and invalid probabilities are explicitly counted rather than silently coerced.

## Live zero-cost corner source proof

Post-merge workflow run `33966876668` on commit `e972872e51ebbf119e8e7d55ef17c64b17144040` audited only repository-configured 2026/27 Football-Data CSV contracts. Artifact `9969711424` (digest `sha256:1deef8862d084544720f9520dd773bb1d1d35874c57ea059184f2414c3d930cd`) reported complete valid `HC/AC` coverage on all finished rows for:

- La Liga: `31 / 31`, `SP1/2627`, zero corner anomalies, zero canonical identity duplicates.
- Eredivisie: `33 / 33`, `N1/2627`, zero corner anomalies, zero canonical identity duplicates.
- Turkey Super Lig: `27 / 27`, `T1/2627`, zero corner anomalies, zero canonical identity duplicates.
- Primeira Liga: `33 / 33`, `P1/2627`, zero corner anomalies, zero canonical identity duplicates.

EPL, Serie A, Bundesliga, Ligue 1 and RPL remain `SOURCE_NOT_CONFIGURED` for a repository-owned 2026/27 Football-Data CSV contract. No URL or season code is guessed for those leagues.

The source proof used zero The Odds API requests, zero Supabase operations and zero production-model operations.

## Current external blockers

1. `league_multi_market_snapshots` was previously proven absent from the live Supabase schema. The repository contains its additive migration, but no safe automatic migration-deployment path has been proven.
2. `league_corner_results` and `league_multi_market_settlements` are repository schema contracts only until their additive migrations are actually deployed and proven live.
3. The Odds API quota was last proven below the Multi-Market safety threshold, so no paid Multi-Market collection should run until the quota gate passes.
4. Corner-result source readiness currently applies only to La Liga, Eredivisie, Turkey Super Lig and Primeira Liga. The other five operational leagues remain gated until an explicit source contract is configured and audited.
5. The OOS evaluator contract is implemented, but prospective evaluation remains gated until durable pre-kickoff Multi-Market snapshots and matching immutable settlement rows actually exist live.

## Not yet claimed

- No live corner-result or settlement persistence proof until the required Supabase tables exist.
- No prospective OOS result has been inspected under `MULTI_MARKET_V2_OOS_PROTOCOL_V1` yet.
- No AI probability edge claims or `Best Bets` from these markets.
- No production model change or promotion.

All Multi-Market V2 work remains research-only.
