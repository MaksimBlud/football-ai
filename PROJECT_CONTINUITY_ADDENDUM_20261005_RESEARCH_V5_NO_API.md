# PROJECT CONTINUITY — Research V5 no-API live proof (2026-10-05)

## Binding status

Research Orchestrator V5 Local is the active no-model-API execution path for the currently
registered families:

- `kickoff_calendar_context`;
- `cross_market_lead_lag_2024_25_anomaly_audit`;
- `cross_market_lead_lag_independent_replication`.

Infrastructure merges:

- PR #496 — add deterministic no-API Research V5;
- PR #497 — allow V5 to claim supported research Issues and route those families away
  from V4 model workers;
- PR #498 — let V5 reach DONE even when repository policy forbids `GITHUB_TOKEN`
  from creating pull requests.

Current infrastructure main:

`fc9d67b9a701a16bd5ec6246eac5a7b29a85aae6`

## Live proof

### Issue #482 — independent Bundesliga/Ligue 1 replication

Final:

- Issue: closed;
- label: `research-v5-done`;
- state: `DONE`;
- engine: `V5_DETERMINISTIC_NO_API`;
- model passes attempted: 0;
- Groq passes: 0;
- quota waits: 0;
- final research PR: #499.

Binding research decision:

`CLOSE_DIRECTION`

`LEAD_LAG_REPLICATION_NOT_SUPPORTED`

`NO_BET`.

### Issue #481 — 2024/25 lead-lag anomaly audit

The worker completed three autonomous deterministic iterations:

1. freeze diagnostic protocol;
2. execute source/market anomaly audit;
3. render final report and close.

Final:

- Issue: closed;
- label: `research-v5-done`;
- state: `DONE`;
- local passes: 3;
- local committed iterations: 3;
- model passes attempted: 0;
- Groq passes: 0;
- quota waits: 0;
- audited eligible rows: 2,920;
- final research PR: #501.

Binding diagnostic:

`NO_OBSERVABLE_SOURCE_MARKET_EXPLANATION`.

No broad 2024/25 source/schema, AH-composition, bookmaker-margin or structural-magnitude
shift was found under the frozen diagnostic rules.

### Issue #428 — kickoff/calendar context for O/U 2.5

The worker completed three autonomous deterministic iterations:

1. freeze temporal OOS protocol;
2. execute OOS evaluation;
3. render final report and close.

Final:

- Issue: closed;
- label: `research-v5-done`;
- state: `DONE`;
- local passes: 3;
- local committed iterations: 3;
- model passes attempted: 0;
- Groq passes: 0;
- quota waits: 0;
- reference rows: 5,695;
- validation rows: 1,140;
- OOT rows: 1,140;
- final research PR: #502.

Binding decision:

`NO_KICKOFF_CALENDAR_OOS_SIGNAL`.

Validation calendar-minus-baseline log loss:

`+0.0006880`

OOT calendar-minus-baseline log loss:

`+0.0014918`

OOT paired-bootstrap 95% CI:

`[-0.0014697, +0.0043883]`.

Calendar features therefore did not improve the frozen market-baseline model OOS.

## Operational behavior

For supported V5 families:

`Issue -> preregistration -> deterministic Python -> RESULT.json -> STATE.json -> commit -> continuation -> FINAL_REPORT.md -> DONE`

No LLM inference provider is required.

V5 workers share:

`research-v5-global-local`

so research Issues do not compete for Groq/Gemini quota.

V4 explicitly skips V5-owned supported hypothesis families. The live Issue-event runs
confirmed the V4 worker was skipped while V5 executed.

If GitHub Actions cannot create a final pull request because repository settings deny that
permission, V5 publishes the durable `agent/v5-issue-<N>` branch reference and still
finishes the Issue. A final PR can be opened separately without affecting research state.

## Safety proof

Every live V5 worker passed:

- issue-sandbox validation;
- production `.pkl` hash before/after comparison;
- state validation;
- branch persistence.

Across #428, #481 and #482:

- no Groq call;
- no Gemini call;
- no model API quota use;
- no paid Odds API;
- no Supabase write;
- no production model operation;
- no automatic promotion;
- no automatic research PR merge.

## Research PR validation

Final research PRs:

- #499 — independent replication;
- #501 — 2024/25 anomaly audit;
- #502 — kickoff calendar context.

All current-head PR validation suites completed successfully after the final branch states
were published. The research PRs remain unmerged, preserving the no-automatic-merge rule.

## Scope limitation

V5 is deterministic, not an unrestricted local-language-model researcher.

At this checkpoint it autonomously executes the registered hypothesis families above.
A genuinely new research family requires a deterministic handler/evaluator to be added to
the V5 registry before it can run unattended.

This is intentional: calculations, temporal/OOS gates and safety rules stay explicit and
reproducible instead of being delegated to a quota-limited model.

A local LLM can be added later as an optional planning layer for unsupported/new families,
but it is not required for the current autonomous research queue.

## Next logical step

Do not return the current three directions to Groq/Gemini.

For a new research direction:

1. define its frozen research contract;
2. add/register a deterministic V5 handler;
3. regression-test it;
4. then hand the Issue to V5 for autonomous execution to DONE.

Production remains untouched.
