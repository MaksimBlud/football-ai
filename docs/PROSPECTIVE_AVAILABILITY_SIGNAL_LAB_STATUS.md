# Prospective Availability Signal Lab — Status

Status: **OPERATIONAL IMPLEMENTATION CLOSED / ACTIVATION EXTERNALLY GATED / RESEARCH-ONLY**

Phase 1 froze the information-time contract before any availability outcome comparison. The implementation now includes provider bootstrap, immutable full-poll persistence, canonical fixture reconciliation, `COUNT_ONLY_V1` features, prospective readiness, explicit-only paired evaluation, and autonomous external activation monitoring for EPL, La Liga, and Serie A.

The collector remains research-only. It does not train or load a production model, does not modify market observations or prediction ledgers, and does not change any `.pkl` artifact. Scheduled collection is gated by repository variable `PROSPECTIVE_AVAILABILITY_ENABLED=true`; manual collector dispatch remains an explicit bootstrap/collection action and still passes the same global preflight.

Durable storage is additive: `prospective_availability_polls` stores complete provider states, including zero-item states, while `prospective_availability_observations` stores poll membership rows and state-level `first_seen_timestamp_utc`. A player disappearing from a later full poll is therefore represented without rewriting prior observations.

Prediction-time feature eligibility is frozen to the latest complete poll whose `observed_at_utc` is not later than the selected market row's `snapshot_time_utc`. The selected market row is frozen to the latest snapshot at or before kickoff minus six hours. `COUNT_ONLY_V1` contains only injury, suspension, and total unavailable-player counts for home/away teams plus their differences. Player-importance weighting remains disabled.

The evaluator was frozen before prospective availability outcomes were inspected. It mirrors the closed market-incremental model family: median imputation, standard scaling, and logistic regression. The frozen gate requires every research league independently to have at least 100 paired finished fixtures, at least four calendar months of coverage, and at least two valid expanding-window monthly evaluation blocks, with at least 60 prior training fixtures and 20 fixtures in each test block.

Autonomous readiness is now outcome-free: it uses only canonical settlement identity presence and never queries `result` values. Outcome scoring is a separate explicit action and can run only through manual `workflow_dispatch` with `evaluate=true`. That explicit path reloads outcome values and rechecks the frozen all-three-league readiness gate before any Brier/log-loss calculation. No scheduled path can score automatically when readiness is reached.

## Live activation audit — 2026-09-04

The connected GitHub Actions environment contains `SUPABASE_URL`, `SUPABASE_KEY`, and `API_FOOTBALL_KEY`; secret values were never printed. Read-only bootstrap audits established:

- `public.prospective_availability_polls` is absent from the connected Supabase PostgREST schema (`PGRST205`);
- `public.prospective_availability_observations` is absent from the connected Supabase PostgREST schema (`PGRST205`);
- the current API-Football key is on a free plan that rejects season 2026 for EPL, La Liga, and Serie A and reports access only to seasons 2022 through 2024;
- no `SUPABASE_ACCESS_TOKEN`, `SUPABASE_DB_PASSWORD`, `SUPABASE_PROJECT_REF`, `SUPABASE_DB_URL`, or `DATABASE_URL` is available in GitHub Actions;
- no alternate `SPORTMONKS_API_KEY` or `RAPIDAPI_KEY` is available;
- the connected PostgREST OpenAPI surface exposes `RPC_TOTAL=0`, so there is no discovered SQL/DDL/migration RPC that could safely apply the migration through the existing `SUPABASE_KEY`.

These findings make the activation boundary genuinely external: `supabase/migrations/202609030002_prospective_availability.sql` must be applied through Supabase database-management access, and a provider credential with current-season 2026 injury coverage must be supplied. The repository must not emulate either requirement through unsupported PostgREST writes or historical injury data.

The collector enforces a global provider preflight. Schema readiness, API key presence, and successful league/`coverage.injuries` resolution for **all three** leagues must pass before the first persistence path is entered. A partial provider failure therefore cannot create a partially activated research poll cycle.

A new scheduled read-only activation monitor continuously rechecks the two schema gates and three provider-coverage gates and writes `activation_readiness.json` as `BLOCKED` or `READY`. It never applies DDL, never changes `PROSPECTIVE_AVAILABILITY_ENABLED`, never writes prospective observations, and never activates collection automatically.

No outcome-based availability result has been inspected and no empirical conclusion is claimed. The implementation phase is formally closed in `docs/PROSPECTIVE_AVAILABILITY_SIGNAL_LAB_OPERATIONAL_CLOSURE.md`; the scientific block remains externally gated until the documented dependencies become available.
