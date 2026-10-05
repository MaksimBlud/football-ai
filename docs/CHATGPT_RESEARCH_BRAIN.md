# ChatGPT Research Brain + Research V5

## Goal

The Research Brain is the scientific planner. Research V5 remains the deterministic
execution engine.

The durable hierarchy is:

`Research Program -> child research Issue -> V5 deterministic execution -> result -> Research Brain -> next child Issue`.

A child Issue reaching `DONE` does **not** automatically end the parent program.

## Durable program registry

Source of truth:

`research/programs/registry.json`

Each program records:

- objective;
- `ACTIVE / PROGRAM_DONE / BLOCKED` status;
- completed child Issue numbers;
- active child Issue numbers, so the Brain cannot duplicate work while a child is running;
- current scientific frontier;
- allowed follow-up classes;
- explicit stop rules.

The registry has a fail-closed safety policy:

- model API fallback is off by default;
- paid data requires fresh user approval;
- production promotion is forbidden;
- frozen gates cannot be weakened post-hoc;
- at most one new child Issue per program per Brain cycle.

## Hourly Brain cycle

The scheduled ChatGPT Research Brain should, in one cycle, inspect **all ACTIVE programs**.

For each program:

1. Read the current registry entry.
2. Read all live open `[AGENT-RESEARCH]` Issues and relevant merged V5 results.
3. If a child Issue is still running, do not duplicate it.
4. If a child Issue has just reached `DONE`, interpret its result and update the
   program frontier.
5. If no child Issue is active, choose at most one genuinely independent,
   preregisterable next step from the program's allowed follow-up classes.
6. Create a new `[AGENT-RESEARCH]` Issue with:
   - `research_question`;
   - `hypothesis_family`;
   - `independent_information_justification`;
   - `research_program_id`;
   - parent Issue references where relevant.
7. Let V5 execute if the family is registered.
8. If V5 returns `research-v5-needs-recipe`, the Brain may implement a reviewed
   deterministic evaluator/recipe through branch -> tests -> PR -> CI -> exact-head merge,
   then wake the same Issue again.
9. Mark the parent `PROGRAM_DONE` only when its stop rules say no genuinely independent
   follow-up remains.

## What the Brain must not do

- Do not repeatedly transform a rejected statistic until something becomes significant.
- Do not weaken frozen validation/OOT gates.
- Do not inspect reserved outcomes before a preregistered gate.
- Do not use `research-v4-model-opt-in` automatically.
- Do not call paid Odds API or buy data without fresh explicit user approval.
- Do not change or promote production `.pkl` artifacts.
- Do not create duplicate child Issues while another child for the same program is active.

## Current portfolio

The initial ACTIVE programs are:

- `cross_market_lead_lag` — current frozen replication is negative and the broad
  2024/25 source/market anomaly audit did not explain the weakening; the Brain should
  decide whether a mechanistically independent zero-cost follow-up remains.
- `kickoff_calendar_context` — the pooled kickoff/day-of-week incremental OOS test is
  negative; the Brain may consider only preregistered heterogeneity/stability/mechanism
  checks that do not rescue the rejected pooled hypothesis post-hoc.

Infrastructure live-proof Issues are not scientific programs.


## First live Brain cycle

The first live Brain cycle opened one child per ACTIVE program, respecting the portfolio
limit:

- Issue #515: frozen temporal stability of cross-market lead-lag;
- Issue #516: preregistered league heterogeneity of kickoff/calendar context.

Both were initially fail-closed as `research-v5-needs-recipe`. The Brain then added
deterministic evaluators and V5 recipes rather than opting into V4/model APIs.
