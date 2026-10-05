# Research V5 recipe request — Issue #522

**Family:** `corner_cross_market_match_shape_direction_v1`

**Question:** Автономно довести до DONE направление CROSS_MARKET_MATCH_SHAPE_CORNER_GAP_V1: проверить, является ли расхождение между cross-market match-shape expectation и opening corner FAIR_CENTRE переносимым Stage-B сигналом направления рынка угловых, не ретюня уже открытые 194 corner-market матча и не собирая новые prospective матчи. Production не трогать.

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
