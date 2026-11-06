# Original V2 secondary evaluator — read-only runner

## Scope

This runner is a separate, research-only path for the frozen old-season-only
`MARKET_ANCHOR_1X2_V2` candidate. It does not change the original frozen
prospective cohort or its eligibility. The comparator is the de-vigged market
versus the exact original lambda-1 shadow. `active_lambda=0` remains the market;
`shadow_residual_lambda=1` remains research-only.

## Execution safety

- Manual dispatch on `main` only; no schedule and no paid-odds workflow trigger.
- The source-rights check runs before any GitHub or Supabase request.
- GitHub forward/source artifacts must be from exact successful `main` workflows,
  with the frozen code blobs, ZIP SHA-256, and source-before-quote timestamps.
- Only source archives created before the saved quote and completed source
  workflows before the quote can be admitted.
- Supabase first reads only `match_date, home_team, away_team` for the frozen
  Serie A 2026/27 identity gate.
- The lazy outcome callback is invoked only after both frozen gates pass:
  at least 30 completed primary fixture identities and at least 30 unique
  eligible completed forecasts.
- After the gate, the outcome query selects only exact fixture identity,
  `result`, and `persisted_at_utc`; every persistence timestamp must be
  strictly after kickoff and no later than the runner's captured evaluation
  time. Future-dated persistence is rejected. The report contains aggregate
  metrics, not outcomes.
- No Supabase writes/DDL, paid calls, model refit, production artifact changes,
  bets, publication, or promotion.

## Current evidence boundary

The existing Nov 5 Original Forward artifact has zero eligible rows, so it is
not an evaluation sample. The runner deliberately ignores artifacts created
before the secondary protocol freeze at 2026-11-06 02:46:10 UTC. Until new
source-before-quote forecasts exist, the runner returns without reading
completed-fixture metadata or target outcomes.

A successful offline test does not establish runtime or predictive quality.
Brier/LogLoss are reported only after both gates; no superiority claim is
permitted by this secondary protocol.
