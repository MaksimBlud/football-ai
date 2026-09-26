# CORNER_REGIME_ADJUSTED_DIRECTION_V2B_ODDS_PLAN

Status: **PREREGISTERED / OFFLINE-ONLY / EXACT 43-FIXTURE LOCK CONSUMER**

## Purpose

Build the deterministic acquisition plan for the already-locked V2B cohort.

This block performs no provider HTTP request and does not authorize live odds access.

The only acceptable source lock is the immutable V2B cohort lock produced from:

- lock workflow run `36219786013`;
- lock artifact `10899325930`;
- artifact digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`.

Expected immutable identities:

- `selection_sha256 = sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73`;
- `fixture_metadata_sha256 = sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb`.

## Required lock properties

The acquisition-plan builder must fail closed unless the source manifest has:

- `lock_experiment_id = CORNER_REGIME_ADJUSTED_DIRECTION_V2B_COHORT_LOCK`;
- `lock_status = IMMUTABLE_COHORT_LOCKED`;
- `immutable = true`;
- `research_only = true`;
- `offline_only = true`;
- `odds_acquisition_authorized = false`;
- `betting_enabled = false`;
- `production_promotion_authorized = false`;
- exactly 10 selected blocks;
- exactly 43 selected fixture IDs;
- exactly 74 metadata potential pairs;
- metadata gate 2 blocks/league, 10 pooled blocks, 74 potential pairs;
- unchanged downstream statistical gate.

The builder must recompute and verify:

- `selection_sha256`;
- `fixture_metadata_sha256`.

## Deterministic batching

Operational request cap remains:

**30 odds requests per live run/batch**

The locked 43 fixture IDs must be split sequentially, preserving exact order:

- batch 1 = first **30** fixture IDs;
- batch 2 = remaining **13** fixture IDs.

No fixture may be:

- reordered for membership purposes;
- removed;
- replaced;
- backfilled;
- rediscovered from provider metadata.

Every locked fixture appears exactly once in the acquisition plan.

## Resume rule

If a later live provider run is partial:

`REQUEST_ONLY_MISSING_IDS_FROM_SAME_LOCKED_COHORT`

A resume may not rebuild or reselect the cohort.

## Output plan

The offline plan must contain:

- source lock workflow/artifact provenance;
- source lock artifact digest;
- source selection hash;
- source fixture-metadata hash;
- exact ordered 43 fixture IDs;
- exact immutable fixture metadata;
- deterministic batches;
- total planned requests = 43;
- batch count = 2;
- max requests per batch = 30.

Authorization flags must remain:

- `live_odds_acquisition_authorized = false`;
- `requires_explicit_live_authorization = true`;
- `fixture_reselection_allowed = false`;
- `betting_enabled = false`;
- `production_promotion_authorized = false`.

## Safety

- offline-only;
- no provider HTTP;
- no odds endpoint;
- no market prices;
- no outcomes;
- no Supabase writes;
- no paid action;
- no betting;
- no production promotion.

Only after this exact plan is materialized immutably may a separate live-capable odds-acquisition PR be created.

