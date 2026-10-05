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

## Recipe registry

Supported deterministic families are no longer hard-coded in either GitHub Actions
workflow. The source of truth is:

`research/v5_recipe_registry.json`

Each recipe declares:

- `hypothesis_family`;
- a reviewed built-in deterministic handler;
- a per-family `max_iterations` runaway guard;
- the mandatory no-API/no-production safety contract.

At intake, V5 calls `research_agent_v5.py --supports-family`. V4 calls the same
registry check and automatically yields ownership when V5 supports the family.
The worker obtains its iteration budget from
`research_agent_v5.py --max-iterations`.

Adding a deterministic family therefore does **not** require another YAML routing edit.
A code change only needs to add the reviewed deterministic evaluator/handler and one
registry recipe with tests. Unknown or unsafe registry entries fail closed.


An open `[AGENT-RESEARCH]` Issue whose family is not registered is labeled
`research-v5-needs-recipe` and stops **without** invoking any model provider.
The legacy V4 model worker is no longer an automatic fallback. It can run an unsupported
family only when the Issue explicitly carries `research-v4-model-opt-in`.

Current registry recipes are:

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


## Adding the next no-API research family

The intended extension path is:

1. implement a deterministic Python evaluator that consumes only preregistered,
   allowed inputs and returns a machine-readable result;
2. add a small reviewed V5 handler that freezes the protocol before evaluation and
   writes only inside the current Issue sandbox;
3. register the family in `research/v5_recipe_registry.json`;
4. add unit/contract tests;
5. merge through normal research-infrastructure CI.

No provider key, quota configuration, V4 routing case or new workflow branch is needed.
The registry deliberately does not allow Issue text to name arbitrary Python modules,
shell commands or packages. Executable handlers remain repository-reviewed code.


## No-API default for new research Issues

The default intake policy is now fail-closed:

`new Issue -> V5 registry lookup -> supported: deterministic V5 / unsupported: needs-recipe`

An unsupported Issue does not silently consume Groq/Gemini quota. To use the old model
worker for a specific unsupported direction, add the explicit label
`research-v4-model-opt-in`. The V4 workflow listens for the label event and then applies
all existing V4 sandbox, quota and production-safety gates.

For the normal Football AI workflow, prefer adding a reviewed deterministic recipe instead
of opting back into V4.
