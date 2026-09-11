# Continuity Addendum — Bundesliga prospective MARKET_ONLY capture ready

Date: 2026-09-11
Branch: `research/bundesliga-prospective-capture-v1`
Protocol: `BUNDESLIGA_MARKET_ONLY_V1`
Target: 100 prospective observations

## Frozen protocol

The Bundesliga capture contract was committed before any live Bundesliga fixture/snapshot values were inspected.

- league: `BUNDESLIGA` only
- evidence class: `MARKET_ONLY`
- first valid row starts at `1/100`
- canonical identity: league + normalized home team + normalized away team + UTC kickoff + protocol
- `captured_at_utc` must be strictly before kickoff
- source snapshot must be strictly before kickoff and no later than capture time
- source provenance is mandatory: `source_event_id` + exact `source_snapshot_time_utc`
- finite 1X2 decimal odds greater than 1.0 are mandatory
- result/outcome/score/winner/settlement fields are forbidden
- AI/model probability/version/artifact fields are forbidden
- duplicate canonical rows are idempotent only when provenance and market values are identical
- conflicting rewrites, non-contiguous counters and target overflow fail closed
- committed ledger is validated in CI
- no production `.pkl` dependency or write path
- no database client or paid odds-provider dependency in the capture tool

This is a separate contract from the frozen `NON_EPL_MARKET_ONLY_V1` used by Serie A and La Liga. Their ledger is checksum-protected by the Bundesliga regression suite and remains unchanged.

## First Bundesliga prospective observation — recorded before kickoff

A read-only live Supabase query was made only after the contract had been frozen. The query selected only future fixture identity, kickoff, source event/snapshot identity and 1X2 market prices. It did not select result, score, outcome, winner or settlement fields.

Database time at retrieval:

`2026-09-11T02:42:35.185104+00:00`

### Bundesliga — 1/100

- fixture: `Union Berlin` vs `FC Schalke 04`
- kickoff: `2026-09-11T18:30:00+00:00`
- source event: `115c6679a72c5a360640b6baaa16e78c`
- source snapshot: `2026-09-05T15:19:55.610317+00:00`
- captured at: `2026-09-11T02:42:35.185104+00:00`
- home odds: `2.01647058823529`
- draw odds: `3.69941176470588`
- away odds: `3.28294117647059`
- evidence class: `MARKET_ONLY`

The durable row is stored in `experiments/bundesliga_market_only_v1.csv`. It is immutable prospective market evidence and must never receive a retrospective AI prediction or be relabeled as prospective AI evidence.

## State

- `CAPTURE_READY=true` for Bundesliga prospective `MARKET_ONLY` research under `BUNDESLIGA_MARKET_ONLY_V1`.
- prospective count: `1/100`.
- `MODEL_READY=false`.
- `PROSPECTIVE_AI_READY=false`.

The next independent scientific task is Bundesliga league-specific historical AI readiness. A historical PASS could only make a future AI protocol eligible for freezing; it cannot modify this existing MARKET_ONLY row.

## Safety proof

- no paid Odds API request;
- no live score/result/outcome/settlement read;
- no Supabase write;
- no production `.pkl` modification;
- no model promotion;
- existing Serie A / La Liga prospective ledger unchanged.

Merge is allowed only after exact-head repository CI is green, followed by fresh-main and post-merge proof.
