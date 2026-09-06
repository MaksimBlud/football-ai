# Prospective CORNERS10 Incremental V1 — Status

Status: **ACTIVE_EXTERNALLY_GATED / PREREGISTERED / RESEARCH-ONLY**

The evaluation protocol is frozen before prospective corner capability is approved and before this block is allowed to inspect future outcomes.

The block asks one narrow question: whether the previously retained `CORNERS10` football-state signal adds prospective 1X2 predictive information beyond the same-row market baseline. Historical evidence did not show incremental market value, so this is a confirmation attempt rather than a continuation of historical tuning.

## Current gate

Collection/evaluation is not activated by this document. Provider corner capability must first be demonstrated by the separately preregistered capability probe and then accepted through a separate reviewed capability attestation. There is no automatic gate bypass.

Until that happens:

- no sample is eligible for this block;
- no outcome scoring is allowed;
- no provider call is allowed from the evaluator;
- no Supabase write is allowed from the evaluator;
- no production model or `.pkl` may change.

## Frozen evaluation

The machine-readable source of truth is `research/prospective_corners10_incremental_v1.json`. It freezes EPL, La Liga and Serie A, a 10-match prior-only corner state, same-row `MARKET_MODEL` versus `MARKET_CORNERS10`, expanding monthly walk-forward evaluation, Brier/log-loss primary metrics, readiness floors, and PASS/FAIL/INCONCLUSIVE rules.

Evaluation requires an explicit manual action after every league passes the frozen readiness gate. A result can close or advance research, but cannot promote production automatically.
