# Product Reliability / Calibration Layer v1

Version: `product-reliability.v1`

## Purpose

This layer turns immutable settled product predictions into empirical evidence
about forecast quality. It is deliberately separate from model training,
calibration fitting, Product Decision ranking, model promotion, and betting.

The layer answers two different questions:

1. What do the settled forecasts currently look like? (descriptive metrics)
2. Is there enough prospective evidence to begin a formal reliability review?
   (evidence gate)

It does **not** answer "is this model reliable?" with a PASS/FAIL verdict in v1.

## Source of truth

Only immutable `product_prediction_lifecycle_events` are accepted.

A settled forecast is usable only when:

- a `PREDICTION_REGISTERED` fact exists for the source prediction snapshot;
- exactly one `SETTLED` fact exists for that source prediction snapshot;
- registration and settlement agree on product match identity and league;
- the settlement scope is `1x2_model_probability`;
- the source model provenance is read from the frozen registration payload.

Multiple settlement facts for one source prediction fail closed. A future result
correction needs a separate explicit correction contract; v1 never silently
chooses a convenient result.

## Primary reliability scope

A product reliability claim must be scoped to:

`exact model_1x2_sha256 × league × 1X2`

Cross-model or cross-league aggregates may be shown descriptively but are never
eligible for a reliability claim.

This avoids making a current model look stronger by pooling outcomes generated
by older/different model artifacts.

## Pre-registered evidence gate

The gate is fixed before the first Product Lifecycle settlement is available:

- at least **100 settled fixtures** for the exact model/league scope;
- evidence spanning at least **4 calendar months** from first to last kickoff.

These are evidence-readiness guardrails, not a statistical guarantee of quality.
The statuses are:

- `NO_SETTLED_DATA` — no settled predictions;
- `ACCUMULATING_SAMPLE` — fewer than 100 settled predictions;
- `ACCUMULATING_TIME` — sample count reached 100 but four calendar months have
  not elapsed across the sample;
- `REVIEWABLE` — both gates are satisfied;
- `DESCRIPTIVE_ONLY` — scope mixes model artifacts and/or leagues.

`REVIEWABLE` means only that the sample is eligible for a formal review. It does
not mean PASS, promotion, or high confidence.

## Metrics

For the settled 1X2 probability vector the layer reports:

- accuracy of the top model pick;
- mean multiclass Brier score;
- mean multiclass log loss;
- Brier skill versus a uniform 1X2 baseline;
- log-loss improvement versus a uniform 1X2 baseline;
- top-pick calibration buckets in 10 percentage-point ranges;
- empirical hit rate per bucket;
- 95% Wilson interval for the bucket hit rate;
- weighted top-pick expected calibration error (ECE).

Brier/log-loss definitions are inherited from Product Lifecycle / canonical
prediction evaluation. They are proper scoring-rule metrics over the full 1X2
probability vector.

The calibration buckets are descriptive. v1 intentionally defines **no**
post-outcome bucket sample threshold or bucket PASS/FAIL rule.

## No post-outcome tuning

`product-reliability.v1` deliberately has no Brier/ECE/log-loss PASS threshold.
Such a threshold must be pre-registered in a later research/review contract; it
must not be chosen after looking at the product settlement sample.

Therefore every v1 slice returns:

`reliability_verdict.status = INCONCLUSIVE`

Even after the evidence gate becomes `REVIEWABLE`.

## Relationship to Product Decision Framework

Reliability v1 does not alter Product Decision Framework v1.

It cannot:

- change `decision_tier`;
- change forecast ranking;
- change model probabilities;
- promote a model or market;
- make a value signal become the main forecast;
- create a betting recommendation.

A later version may consume a formally reviewed reliability result, but that
integration requires its own regression contract and must preserve `forecast !=
value` semantics.

## Legacy bootstrap predictions

Legacy product snapshots registered by
`legacy_source_snapshot_bootstrap` remain valid forecast-quality observations if
and when they settle because their original pre-kickoff model probabilities and
model artifact provenance were frozen in `PREDICTION_REGISTERED`.

They do not receive a retroactive Product Decision Framework version.
Reliability is about the frozen probability forecast, not about reconstructing a
historical product recommendation that did not exist at publication time.

## Operational report

`report_product_reliability.py` is read-only.

Without filters it prints:

- descriptive overall history;
- every exact model-SHA/league slice.

With both `--league` and `--model-sha256`, it prints one exact primary slice.
The two arguments must be supplied together.

The report never:

- writes to Supabase;
- calls The Odds API;
- fetches a second result source;
- trains or calibrates a model;
- changes production `.pkl` artifacts;
- promotes a model;
- creates a bet.
