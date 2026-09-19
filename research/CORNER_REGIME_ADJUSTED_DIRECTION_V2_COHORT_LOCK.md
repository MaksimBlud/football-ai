# CORNER_REGIME_ADJUSTED_DIRECTION_V2_COHORT_LOCK

Status: **PREREGISTERED / OFFLINE-ONLY IMMUTABLE LOCK VALIDATOR / NO ODDS**

## Purpose

This block prepares the exact transition from a future V2 metadata planner result:

`COHORT_LOCKED`

to an immutable cohort manifest that can later be consumed by a separately authorized odds-acquisition PR.

It does **not** fetch fixture metadata, does **not** fetch odds and does **not** evaluate FAIR_CENTRE or direction statistics.

## Input boundary

Input must be an immutable metadata artifact produced by the already-frozen V2 metadata planner.

The artifact must contain exactly one `cohort_plan.json`.

Accepted source status:

`COHORT_LOCKED`

Rejected source status:

`WAIT_FOR_COHORT`

A WAIT artifact must fail closed and cannot be converted into a lock.

## Frozen validation contract

The validator must verify all of the following from the source plan:

- `experiment_id = CORNER_REGIME_ADJUSTED_DIRECTION_V2`;
- `metadata_live_experiment_id = CORNER_REGIME_ADJUSTED_DIRECTION_V2_METADATA_LIVE`;
- `research_only = true`;
- `metadata_only = true`;
- `odds_endpoint_used = false`;
- `market_prices_opened = false`;
- `match_outcome_used = false`;
- `football_state_used = false`;
- `paid_subscription_used = false`;
- future cutoff remains `2026-09-19T00:00:00Z`;
- total prior excluded fixture IDs = 151;
- metadata cohort gate remains:
  - >=2 blocks per league;
  - >=12 blocks pooled;
  - >=80 metadata potential pairs.

The validator must recompute the expected earliest qualifying prefix from `candidate_blocks` using the merged V2 planner logic and require exact equality with the source plan's:

- `selected_blocks`;
- `selected_fixture_ids`;
- `selected_block_count`;
- `selected_fixture_count`;
- `metadata_potential_pairs`;
- `blocks_by_league`.

No reorder, removal, replacement or backfill is allowed.

## Immutable lock manifest

For a valid COHORT_LOCKED source, emit a canonical JSON manifest containing at minimum:

- lock experiment ID;
- source metadata experiment IDs;
- source run/artifact provenance supplied explicitly by caller;
- frozen cutoff;
- lock gates;
- exact ordered selected blocks;
- exact ordered selected fixture IDs;
- selected counts;
- metadata potential pairs;
- prior excluded ID count;
- a deterministic `selection_sha256`.

`selection_sha256` must be computed from canonical JSON containing only the frozen selection identity:

- selected blocks;
- selected fixture IDs;
- cutoff;
- lock-gate constants.

The hash must be invariant to irrelevant source-plan key ordering.

## Fail-closed rules

Reject:

- WAIT_FOR_COHORT;
- missing or duplicate cohort_plan.json;
- wrong experiment IDs;
- any evidence that odds or market prices were opened;
- changed cutoff;
- changed 151-ID exclusion count;
- changed metadata lock gates;
- duplicate selected fixture IDs;
- selected fixture IDs not exactly equal to concatenated whole-block fixture IDs;
- selected blocks not equal to the deterministic earliest qualifying prefix;
- inconsistent selected counts/pair totals/league block counts.

## Authorization boundary

A valid immutable cohort lock still does **not** authorize odds acquisition.

The emitted manifest must contain:

- `odds_acquisition_authorized = false`;
- `betting_enabled = false`;
- `production_promotion_authorized = false`.

The next live-capable PR, if ever created, must explicitly consume this exact lock manifest and be separately reviewed/authorized.

## Safety

- research-only;
- offline-only;
- no provider HTTP calls;
- no odds;
- no market prices;
- no outcomes;
- no Supabase writes;
- no paid actions;
- no betting;
- no production promotion;
- production `.pkl` hash guard required in CI.

