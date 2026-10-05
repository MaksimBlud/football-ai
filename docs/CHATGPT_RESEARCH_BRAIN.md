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

The initial ACTIVE programs are:

- `cross_market_lead_lag` — **PROGRAM_DONE** after failed independent replication, completed regime/anomaly diagnostics, and duplicate detection for the attempted temporal-stability follow-up. Further zero-cost steps would be cosmetic restatements; paid intraday data still requires explicit user approval.
- `kickoff_calendar_context` — **PROGRAM_DONE** after the negative pooled OOS test,
  negative preregistered league heterogeneity, and the negative outcome-free
  opening-to-closing market-movement mechanism. Remaining zero-cost variants would
  be threshold/weekday/league mining or cosmetic restatements of the rejected signal.
- `corner_market_direction` — **PROGRAM_DONE**. Issue #522 found an encouraging
  same-sample continuous rank association, but binary direction stayed below always-UP.
  The independent zero-cost Bundesliga/Ligue 1 transport in Issue #528 failed after removing
  the mechanical opening-line component (residual Spearman 0.0503; permutation p=0.4125),
  produced opposing league-held-out signs, and again lost to always-UP. Cross-league transfer
  is unsupported, the decision remains NO_BET, and further free variants would retune or
  threshold-mine already-opened movements.

- `bookmaker_market_microstructure_1_price_formation` — **ACTIVE**. Issue #532 did not establish a stable bookmaker-specific price component; Issue #553 now performs the one independent cross-bookmaker/cross-league transport allowed by the remaining frontier.
- `bookmaker_market_microstructure_2_devig` — **PROGRAM_DONE** after the original comparison (#533) and independent Bundesliga/Ligue 1 transport (#540) both failed their frozen confirmation gates. No de-vig winner is promoted.
- `bookmaker_market_microstructure_3_favourite_longshot` — **PROGRAM_DONE** after the original audit (#534) and independent Bundesliga/Ligue 1 transport (#542) both failed their frozen stability gates. No betting or calibration rule is supported.
- `bookmaker_market_microstructure_4_margin_structure` — **ACTIVE**. The supported 1X2 bookmaker-margin heterogeneity from #535 is being tested on the independent Asian Handicap representation in #548.

Infrastructure live-proof Issues are not scientific programs.
