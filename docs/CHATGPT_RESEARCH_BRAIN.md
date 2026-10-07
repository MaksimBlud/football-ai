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

All prior research programs are **PROGRAM_DONE**. The currently active scientific program is:

- `multi_market_repricing_state` — **ACTIVE**. Issue #573 tests whether the joint Bet365 STANDARD/PRE-CLOSE state from 1X2 + O/U 2.5 + Asian Handicap predicts the later continuous 1X2 closing repricing vector better than an otherwise identical 1X2-only baseline. This is not the old `alignment_dot`: no synthetic score reconstruction is used, no match outcomes are used, and binary UP/DOWN is diagnostic only. Because historical closing movements through 2025/26 were already opened by earlier work, #573 is a preregistered retrospective falsification/representation test; a positive result may justify only a separately frozen prospective confirmation. Corner-market augmentation remains a separate later child/source-gated question and may not retune old corner cohorts.

Infrastructure live-proof Issues are not scientific programs.
