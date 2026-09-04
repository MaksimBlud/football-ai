# Prospective Availability Signal Lab — Status

Status: **TECHNICAL CONTOUR COMPLETE / ACTIVATION GATED / WAITING FOR PROSPECTIVE SAMPLE**

Phase 1 froze the information-time contract before any availability outcome comparison. The operational implementation now completes the provider bootstrap, immutable full-poll persistence contract, canonical fixture reconciliation, COUNT_ONLY_V1 feature semantics, prospective readiness gates, and the autonomous paired evaluation cycle for EPL, La Liga, and Serie A.

The collector remains research-only. It does not train or load a production model, does not modify market observations or prediction ledgers, and does not change any `.pkl` artifact. Scheduled collection is additionally gated by repository variable `PROSPECTIVE_AVAILABILITY_ENABLED=true`; manual workflow dispatch remains available for bootstrap verification.

Durable storage is additive: `prospective_availability_polls` stores complete provider states, including zero-item states, while `prospective_availability_observations` stores poll membership rows and state-level `first_seen_timestamp_utc`. A player disappearing from a later full poll is therefore represented without rewriting prior observations.

Prediction-time feature eligibility is frozen to the latest complete poll whose `observed_at_utc` is not later than the selected market row's `snapshot_time_utc`. The selected market row is itself frozen to the latest snapshot at or before kickoff minus six hours. COUNT_ONLY_V1 contains only injury, suspension, and total unavailable-player counts for home/away teams plus their differences. Player-importance weighting remains disabled.

The Phase 4 evaluator was frozen before prospective availability outcomes were inspected. It mirrors the closed market-incremental model family: median imputation, standard scaling, and logistic regression. It refuses to calculate any outcome score until every research league independently has at least 100 paired finished fixtures, at least four calendar months of coverage, and at least two valid expanding-window monthly evaluation blocks, with at least 60 prior training fixtures and 20 fixtures in each test block.

## Live activation audit — 2026-09-04

The connected GitHub Actions environment contains `SUPABASE_URL`, `SUPABASE_KEY`, and `API_FOOTBALL_KEY`; secret values were never printed. Read-only bootstrap audits established the following external gates:

- `public.prospective_availability_polls` is absent from the connected Supabase PostgREST schema (`PGRST205`).
- `public.prospective_availability_observations` is absent from the connected Supabase PostgREST schema (`PGRST205`).
- the current API-Football key is on a free plan that rejects season 2026 for EPL, La Liga, and Serie A and reports access only to seasons 2022 through 2024;
- no `SUPABASE_ACCESS_TOKEN`, `SUPABASE_DB_PASSWORD`, `SUPABASE_PROJECT_REF`, `SUPABASE_DB_URL`, or `DATABASE_URL` is available in GitHub Actions;
- no alternate `SPORTMONKS_API_KEY` or `RAPIDAPI_KEY` is available;
- the connected PostgREST OpenAPI surface exposes `RPC_TOTAL=0`, so there is no read-only-discovered SQL/DDL/migration RPC that could safely apply the migration through the existing `SUPABASE_KEY`.

These findings make the remaining activation boundary genuinely external to the repository: the additive migration `202609030002_prospective_availability.sql` must be applied through Supabase database-management access, and a provider credential with current-season 2026 injury coverage must be supplied. The repository must not emulate either requirement through unsupported PostgREST writes or historical injury data.

The collector now also enforces a global provider preflight. Schema readiness, API key presence, and successful league/`coverage.injuries` resolution for **all three** EPL, La Liga, and Serie A must pass before the first persistence path is entered. A partial provider failure therefore cannot create a partially activated research poll cycle.

Once activation passes, the four-hour collector accumulates immutable prospective availability states automatically. The weekly research cycle tracks coverage/readiness automatically and emits no outcome scores while the frozen sample gate is unmet. When all three leagues become ready, it runs only the pre-registered paired `MARKET_MODEL` versus `MARKET_AVAILABILITY` comparison and writes research artifacts; no production promotion is automatic.

No outcome-based availability result has been inspected and no empirical conclusion is currently claimed. The implementation is complete; the remaining state is intentionally time-dependent prospective accumulation plus the two documented external activation dependencies, not unfinished feature development.
