# Research Orchestrator V5 Local

Status: **NO-API AUTONOMOUS RESEARCH ENGINE**.

## Purpose

V5 removes model-provider quota from the critical path.

The worker is a deterministic Python state machine running on GitHub-hosted Actions.
It does not require Groq, Gemini, Cerebras, OpenRouter or another LLM API key.

For supported hypothesis families:

1. freeze the next research contract before calculation;
2. run reproducible Python research;
3. write issue-scoped evidence and `STATE.json`;
4. commit the iteration to `agent/v5-issue-<N>`;
5. redispatch itself on `CONTINUE`;
6. create a final PR and close the Issue on `DONE`.

## Supported families

Initial V5 handlers:

- `kickoff_calendar_context`;
- `cross_market_lead_lag_2024_25_anomaly_audit`;
- `cross_market_lead_lag_independent_replication`.

The independent-replication handler can consume canonical frozen research already merged
on `main`; it fails closed if the canonical safety contract does not match.

The other two handlers use three deterministic phases:

`PREREGISTRATION -> RESULT.json -> FINAL_REPORT.md/DONE`.

## No model quota

V5 uses no LLM inference endpoint. Public pinned GitHub/Football-Data reads are data
transports, not model APIs, and remain zero-cost.

A transient public-source failure does not spend model quota: the Issue receives
`research-v5-waiting` and the scheduled sweep retries it.

## Safety

Every V5 iteration:

- writes only under the current Issue sandbox;
- snapshots production `.pkl` hashes before and after;
- runs the existing sandbox validator;
- validates `STATE.json`;
- never writes Supabase;
- never calls paid Odds API;
- never promotes a research model;
- never auto-merges the final research PR.

V4 detects V5-owned Issues and skips its model worker, so a migrated Issue cannot
accidentally consume Groq/Gemini quota in parallel.

## Queue and autonomy

Workers share the concurrency group:

`research-v5-global-local`

so one research Issue is executed at a time.

A `CONTINUE` state immediately dispatches the next V5 iteration. A scheduled sweep at
minutes 11 and 41 recovers any Issue left in `research-v5-waiting`.

No user computer needs to remain online.
