# Multi-Market V2 — Status

Status: **SETTLEMENT + CANONICAL CORNER-OUTCOME + FROZEN OOS EVALUATOR FOUNDATIONS IMPLEMENTED / LIVE SCHEMA PROVEN ABSENT / PROSPECTIVE OOS EVALUATION NOT ACTIVE**

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
- Read-only live schema probe validates exact required columns with bounded `SELECT ... LIMIT 1`; it cannot create or mutate schema.

## Live zero-cost corner source proof

Post-merge workflow run `33966876668` on commit `e972872e51ebbf119e8e7d55ef17c64b17144040` audited only repository-configured 2026/27 Football-Data CSV contracts. Artifact `9969711424` (digest `sha256:1deef8862d084544720f9520dd773bb1d1d35874c57ea059184f2414c3d930cd`) reported complete valid `HC/AC` coverage on all finished rows for:

- La Liga: `31 / 31`, `SP1/2627`, zero corner anomalies, zero canonical identity duplicates.
- Eredivisie: `33 / 33`, `N1/2627`, zero corner anomalies, zero canonical identity duplicates.
- Turkey Super Lig: `27 / 27`, `T1/2627`, zero corner anomalies, zero canonical identity duplicates.
- Primeira Liga: `33 / 33`, `P1/2627`, zero corner anomalies, zero canonical identity duplicates.

EPL, Serie A, Bundesliga, Ligue 1 and RPL remain `SOURCE_NOT_CONFIGURED` for a repository-owned 2026/27 Football-Data CSV contract. No URL or season code is guessed for those leagues.

The source proof used zero The Odds API requests, zero Supabase operations and zero production-model operations.

## Live Supabase schema proof — 2026-09-05

Post-merge read-only workflow run `33967488303` on commit `f4e53534ffc6bf4799455983d47005e30bf9268c` probed the exact repository-required columns for all three Multi-Market persistence tables. Artifact `9969892388` has digest `sha256:e533ab3e55118b06b03012d9d56f1bee74516c49886e1cb65460d56ca9eefa56`.

The result is unambiguous: `all_ready=false`, `ready_tables=[]`, and all three tables are blocked:

- `league_multi_market_snapshots` — absent from live schema / PostgREST cache (`PGRST205`).
- `league_multi_market_settlements` — absent from live schema / PostgREST cache (`PGRST205`).
- `league_corner_results` — absent from live schema / PostgREST cache (`PGRST205`).

The probe performed bounded SELECT-only requests and no writes, DDL, migration execution, paid provider requests, or production-model operations.

Repository search also found no proven automated migration deployment path: no `SUPABASE_ACCESS_TOKEN`, no `SUPABASE_DB_PASSWORD`, and no `supabase db push` workflow/command contract. Existing runtime GitHub workflows expose only the application Supabase URL/key for normal data access. Those credentials must not be repurposed into an invented DDL path.

## Current external blockers

1. All three required Multi-Market persistence tables are freshly proven absent from live Supabase. Repository migrations exist, but no safe automated migration-deployment credential/path is established.
2. Paid Multi-Market collection remains separately quota-gated. The readiness workflow uses only The Odds API zero-cost `/sports` preflight; paid event-market calls must not run unless the configured reserve threshold passes.
3. Corner-result source readiness currently applies only to La Liga, Eredivisie, Turkey Super Lig and Primeira Liga. The other five operational leagues remain gated until an explicit source contract is configured and audited.
4. The OOS evaluator contract is implemented and frozen, but prospective evaluation remains inactive until durable pre-kickoff Multi-Market snapshots and matching immutable settlement rows actually exist live.

## Required external schema action

The repository-owned additive migrations are, in dependency order:

1. `supabase/migrations/202609050001_league_multi_market_snapshots.sql`
2. `supabase/migrations/202609050002_league_multi_market_settlements.sql`
3. `supabase/migrations/202609050003_league_corner_results.sql`

They must be applied through an authenticated, reviewed Supabase migration/DDL channel outside the current runtime-key workflow. After deployment, the read-only schema probe is the required verification gate; no collection or persistence process should infer success merely because a migration command returned zero.

## Not yet claimed

- No live Multi-Market snapshot, corner-result, or settlement persistence proof exists yet.
- No prospective OOS result has been inspected under `MULTI_MARKET_V2_OOS_PROTOCOL_V1` yet.
- No AI probability edge claims or `Best Bets` from these markets.
- No production model change or promotion.

All Multi-Market V2 work remains research-only.
