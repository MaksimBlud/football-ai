# Research V5 recipe request — Issue #573

**Family:** `multi_market_1x2_repricing_vector_v1`

**Question:** Does the joint Bet365 pre-close market state from 1X2 + O/U 2.5 + Asian Handicap predict the subsequent continuous 1X2 closing repricing vector better than contemporaneous 1X2 market geometry alone, across the five major leagues, without using match outcomes?

**Decision:** `NEEDS_DETERMINISTIC_RECIPE`

## Required deterministic implementation

- Evaluator: Add a deterministic Python evaluator that consumes only preregistered allowed inputs and returns machine-readable results.
- Handler: Add a reviewed Research V5 handler that freezes the protocol before evaluation and writes only inside the current Issue sandbox.
- Registry: Register the family in research/v5_recipe_registry.json with a bounded max_iterations and the exact no-API safety contract.
- Tests: Add unit tests for the evaluator/handler and workflow contract tests covering fail-closed safety, temporal/OOS rules, and DONE/CONTINUE state.

## Safety

- model API: forbidden by default
- paid Odds API: forbidden
- Supabase writes: forbidden
- production operations: forbidden
- automatic promotion: forbidden
- outcomes read during scaffold: no

This scaffold is intake metadata only. It does not claim that the new hypothesis
family can already execute autonomously.
