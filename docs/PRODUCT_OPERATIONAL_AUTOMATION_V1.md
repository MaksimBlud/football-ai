# Product Operational Automation v1

Version: `product-operational-automation.v1`

## Purpose

Operational Automation v1 connects already-approved durable product components
without adding a new forecasting or betting system.

The scheduled cycle is:

1. read already-produced outcome-free EPL AI rows from `epl_ai_market_pair_ledger`;
2. append a product prediction snapshot only when that event has a strictly newer
   model generation than the newest product snapshot;
3. reload Supabase so lifecycle facts use the real persisted snapshot id;
4. append missing lifecycle facts from stored odds and canonical
   `league_finished_results`;
5. recompute read-only Reliability and Production Readiness summaries;
6. emit a durable audit report.

## Prediction-source boundary

The automation does **not** run the production model. The separate frozen EPL AI
pair collector is responsible for producing pre-kickoff AI rows and already
verifies the frozen production-model SHA.

The product bridge additionally requires:

- `experiment_id = EPL_AI_MARKET_PAIR_V1`;
- `league = EPL`;
- non-empty provider `event_id`;
- `model_generated_at_utc < kickoff_utc`;
- exact frozen model SHA
  `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`.

A row that violates any invariant fails closed.

For each provider event the newest durable pair generation is compared with the
newest product generation. Equal or older generations are ignored. Therefore a
new run id cannot duplicate unchanged fixture predictions merely because another
fixture received a newer generation.

## Source states

- `NO_FUTURE_EVENTS` — no known future EPL odds events in the horizon.
- `COVERED` — every known future EPL odds event already has a product snapshot.
- `READY_TO_INGEST_PREDICTIONS` — a known future event lacks a product snapshot
  but an eligible durable pair-ledger row exists.
- `WAITING_FOR_PREDICTION_SOURCE` — at least one known future odds event has
  neither a product snapshot nor an eligible durable AI row.

`WAITING_FOR_PREDICTION_SOURCE` is intentional fail-closed behavior. The cycle
must never substitute bookmaker probability, fabricate a model forecast, or run
training to fill the gap.

## Lifecycle automation

Lifecycle advancement reuses `build_lifecycle_pass()`:

- registration only for a real persisted pre-kickoff product snapshot;
- market observation only from an already-stored snapshot at or before kickoff;
- settlement only from canonical `league_finished_results`;
- repeated runs are idempotent through immutable event keys.

No external result fetch is performed by this workflow.

Lifecycle source reads are paginated. This removes the old hidden 5000-row
boundary; `odds_snapshots` was already at 3926 rows when v1 was designed.

## Credentials and writes

GitHub Actions reuses the existing repository credential contract:

- `SUPABASE_URL`;
- private `SUPABASE_KEY`.

The cycle rejects a missing key and rejects an `sb_publishable_...` key. Public
web credentials are never a write fallback.

Writes remain append-only:

- `product_prediction_snapshots`: INSERT of a genuinely newer durable model
  generation;
- `product_prediction_lifecycle_events`: INSERT of missing lifecycle facts.

## Schedule

`.github/workflows/product-operational-automation.yml` supports manual dispatch
and runs at minute `37` every two hours.

The ordering is intentional:

- `:23` existing EPL AI pair collector;
- `:37` Product Operational Automation;
- `:47` older EPL durable live-cycle.

The new workflow receives no Odds API key.

## Explicit prohibitions

Operational Automation v1 never:

- calls The Odds API or another paid provider;
- runs model inference or training;
- changes production `.pkl` files;
- reads frozen prospective research target outcomes;
- changes a research gate;
- promotes a model or market;
- changes Decision Framework tiers;
- creates a bet or stake.

## Deployment boundary

This is repository/GitHub operational automation. It does not deploy Vercel.
The exact-main public web deployment remains the next separate product block so
the product runtime can be deployed atomically from the then-current `main`.
