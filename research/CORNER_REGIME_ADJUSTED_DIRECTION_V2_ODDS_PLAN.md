# CORNER_REGIME_ADJUSTED_DIRECTION_V2_ODDS_PLAN

Status: **PREREGISTERED / OFFLINE-ONLY ACQUISITION PLAN / NO LIVE ODDS**

## Purpose

Prepare the deterministic acquisition plan that may be used **only after** a future immutable V2 cohort lock exists.

This block does not fetch provider data and does not authorize a live odds request.

It answers only:

> given an already validated immutable V2 cohort lock, what exact fixture IDs would a later live acquisition be permitted to request, and how should those requests be deterministically batched without reselection?

## Required source

Input must be an immutable cohort-lock manifest produced by:

`CORNER_REGIME_ADJUSTED_DIRECTION_V2_COHORT_LOCK`

Required source properties include:

- `lock_status = IMMUTABLE_COHORT_LOCKED`;
- `immutable = true`;
- `research_only = true`;
- `offline_only = true`;
- `odds_acquisition_authorized = false`;
- `betting_enabled = false`;
- `production_promotion_authorized = false`;
- valid deterministic `selection_sha256`;
- future cutoff and lock gates unchanged;
- exact selected blocks and ordered selected fixture IDs.

A current `WAIT_FOR_COHORT` metadata artifact is not an acceptable input.

## Integrity validation

Before building an acquisition plan, recompute the lock's `selection_sha256` from:

- future cutoff;
- frozen metadata lock gate;
- selected blocks;
- selected fixture IDs.

Reject any mismatch.

Also reject:

- duplicate selected fixture IDs;
- fixture IDs not equal to ordered concatenation of whole selected blocks;
- count mismatches;
- altered lock gates;
- altered future cutoff;
- altered statistical gate;
- any source manifest that claims odds acquisition was already authorized.

## Frozen batching rule

Operational batching is deterministic and does not alter sample membership.

Maximum odds requests per future live run:

**30**

Reason: the earlier V1 acquisition encountered a bounded provider-rate-limit wait and a 75-minute CI timeout. A smaller per-run cap is an operational safety choice made before any V2 odds are opened.

Batching rule:

1. preserve exact ordered `selected_fixture_ids`;
2. split sequentially into chunks of at most 30 IDs;
3. never reorder, replace, drop or backfill fixture IDs;
4. every selected fixture ID must appear in exactly one batch;
5. total planned odds requests = selected fixture count.

If a later live run partially completes, resume semantics must use the same acquisition plan and request only missing IDs from the same locked cohort.

## Output plan

Emit a canonical JSON plan containing:

- acquisition-plan experiment ID;
- source lock provenance and `selection_sha256`;
- exact selected fixture count;
- exact ordered selected fixture IDs;
- deterministic batches;
- maximum requests per run;
- total planned requests;
- explicit authorization flags.

The output must include:

- `live_odds_acquisition_authorized = false`;
- `requires_explicit_live_authorization = true`;
- `fixture_reselection_allowed = false`;
- `betting_enabled = false`;
- `production_promotion_authorized = false`.

## Authorization boundary

This plan is **not** a live-capable implementation.

A later odds-acquisition PR may be created only after:

1. an authoritative future metadata run returns `COHORT_LOCKED`;
2. the immutable lock manifest is created and recorded;
3. this offline acquisition plan is generated from that exact lock;
4. the live PR consumes the exact lock/plan and adds a separately controlled execution marker.

No odds endpoint, provider HTTP call, Supabase write, paid action or market-price read is allowed in this block.

## Safety

- research-only;
- offline-only;
- no provider network transport;
- no odds;
- no outcomes;
- no Supabase writes;
- no paid action;
- no betting;
- no production promotion;
- production `.pkl` hash guard required in CI.

