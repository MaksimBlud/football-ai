# Research V5 recipe request — Issue #513

**Family:** `cross_market_lead_lag_temporal_stability_v1`

**Question:** Is the frozen cross-market lead-lag alignment temporally stable across fixed seasons, or does the 2024/25 validation failure versus positive 2025/26 OOT indicate a non-stationary effect that should be treated as unreliable rather than rescued?

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
