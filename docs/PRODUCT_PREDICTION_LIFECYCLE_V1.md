# Product Prediction Lifecycle & Performance Ledger v1

Status: product contract

Schema version: `product-lifecycle.v1`

## Purpose

Product Decision Framework answers what Football AI shows before a match. The
lifecycle answers what happened to the immutable prediction afterwards and how
the forecast should be evaluated without hindsight.

The lifecycle is deliberately separate from research ledgers and from a future
betting/staking ledger.

## Source-of-truth inputs

Lifecycle v1 reads only already-durable project state:

- `product_prediction_snapshots` — immutable model prediction source;
- `odds_snapshots` — stored bookmaker observations;
- `league_finished_results` — canonical finished-result state already used by
  `evaluate_league_predictions.py`.

It does not call The Odds API, does not fetch a second results provider, does not
run model inference, and does not train or promote models.

## Append-only events

`product_prediction_lifecycle_events` contains three event types.

### `PREDICTION_REGISTERED`

Freezes the source prediction provenance. Two timestamps must remain distinct:

- `source_prediction_created_at_utc` — factual creation time copied from the
  immutable product snapshot;
- `recorded_at_utc` — time the lifecycle event was actually written.

The source prediction must have existed before kickoff.

Existing snapshots that predate Lifecycle v1 may be registered with
`legacy_source_snapshot_bootstrap`. This mode MUST NOT retroactively claim that
Product Decision Framework v1 existed at the original snapshot time;
`decision_at_registration` therefore remains `null`.

Future live registrations may freeze the then-current product decision under
`live_publish`.

### `MARKET_OBSERVED`

After kickoff, records the latest already-stored market snapshot whose
`snapshot_time_utc <= commence_time_utc`.

This is explicitly **not** called a closing line. Existing odds rows do not carry
an authoritative closing qualification. Lifecycle v1 therefore stores:

- `observation_role = latest_stored_pre_kickoff`;
- `minutes_before_kickoff`;
- `is_closing_qualified = false`;
- `clv = null`.

A later closing-price contract may enable CLV only when the source itself can
prove the closing qualification.

### `SETTLED`

Settles the immutable 1X2 probability vector against canonical
`league_finished_results` using the same result identity principles as the
canonical evaluator: league + local match date + normalized home/away teams.

Lifecycle v1 records:

- actual 1X2 outcome;
- model top pick and its probability;
- actual-outcome probability;
- correct/incorrect;
- multiclass Brier score;
- log loss.

The scoring definitions match the existing canonical evaluator:

`Brier = sum((p_i - y_i)^2)`

`LogLoss = -ln(p_actual)`

## No betting fiction

Product Decision Framework v1 returns `no_bet`. Therefore lifecycle settlement
MUST NOT transform a positive raw EV into a historical placed bet.

For v1:

- `bet_result = null`;
- `pnl = null`;
- `roi = null`;
- `clv = null` unless a future explicitly closing-qualified market source is
  introduced.

Forecast quality and betting performance are different datasets.

## Aggregate performance

`performance_summary()` reports only settled forecast quality:

- settled prediction count;
- accuracy;
- mean multiclass Brier;
- mean log loss;
- probability-bucket calibration (`N`, mean forecast probability, empirical hit
  rate).

When no official results are available, the honest summary is `N=0` with metric
values `null`. The lifecycle does not manufacture provisional results.

## Idempotency

Every event has a deterministic unique `event_key`. Re-running the advancement
pass must produce no duplicate event for an already-recorded fact.

## Security

The lifecycle table is internal:

- RLS enabled;
- no `anon` or `authenticated` table access;
- `service_role`: `SELECT + INSERT` only;
- no `UPDATE` or `DELETE` privilege.

Any future public trust/track-record endpoint should expose a reviewed aggregate,
not the raw internal lifecycle/provenance table.

## Operational command

`advance_product_lifecycle.py` is dry-run by default. Live writes require
`--publish`.

For the one-time bootstrap of durable snapshots that existed before Lifecycle v1:

```bash
python advance_product_lifecycle.py \
  --registration-mode legacy_source_snapshot_bootstrap \
  --publish
```

Future lifecycle automation should use `live_publish` and run after successful
product snapshot persistence. Result-source refresh remains a separate canonical
operation; this script never fetches external results itself.
