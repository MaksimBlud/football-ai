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

All registered scientific research programs are **PROGRAM_DONE**.

Latest closed program:

- `multi_market_repricing_state` — **PROGRAM_DONE** after Issue #573. The zero-cost five-league source gate passed, and the direct 1X2 + O/U 2.5 + Asian Handicap representation showed a small pooled 2025/26 improvement, but it failed the frozen stability contract: validation MAE worsened and 2025/26 MSE worsened in 3 of 5 leagues. Final decision: **NO_STABLE_MULTI_MARKET_REPRICING_SIGNAL / NO_BET**.
- Per the preregistered stop rule, corners must not be used as a post-hoc rescue on the same opened history, and the representation must not be retuned by league, feature subset, Ridge alpha, AH scope, target coordinates or sign rules.
- A future restart would require genuinely new prospectively frozen information or a new independent research question, not another transformation of the rejected #573 statistic.

Infrastructure live-proof Issues are not scientific programs.
