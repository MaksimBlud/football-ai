# Turkey Super Lig Prospective Capture V1

Date frozen: 2026-09-11
Protocol: `TURKEY_SUPER_LIG_MARKET_ONLY_V1`
League: `TURKEY_SUPER_LIG`
Target: 100 immutable prospective MARKET_ONLY observations

## Purpose

Create a league-specific prospective evidence ledger for the Turkish Super Lig without changing any previously frozen league protocol and without enabling AI/model semantics.

## Frozen evidence rules

An observation is admissible only when all of the following are true before it is appended:

- `league` is exactly `TURKEY_SUPER_LIG`;
- the evidence class is MARKET_ONLY; no AI or Structural V2 probability is permitted;
- capture time is strictly before kickoff;
- the source market snapshot is strictly before kickoff and is no later than capture time;
- `source_event_id` and exact `source_snapshot_time_utc` are mandatory provenance;
- 1X2 decimal odds are finite and strictly greater than 1.0;
- outcome/result/score/winner/settlement fields are forbidden;
- model probability/version/artifact fields are forbidden;
- canonical fixture identity is league + normalized home + normalized away + UTC kickoff + protocol;
- observation numbers are contiguous from 1 to 100;
- replay of the same canonical fixture is idempotent only when all stable market/provenance values are identical;
- any conflicting rewrite, malformed ledger, duplicate key, non-contiguous sequence or target overflow fails closed.

The committed ledger may validly contain zero rows. `0/100` means the protocol is capture-ready but has not yet received an admissible prospective snapshot; it is not evidence and must not be backfilled retrospectively.

## Paid-provider boundary

This protocol itself has no Supabase or The Odds API client dependency and authorizes no provider request. The existing Turkey/Portugal market-only workflow remains manual `workflow_dispatch`; this freeze does not schedule or trigger it. A paid h2h request remains outside this protocol and requires the project's existing budget/authorization rules.

At freeze time, a read-only live Supabase audit found zero rows in `odds_snapshots` for `TURKEY_SUPER_LIG`/`SUPER_LIG`, so the correct initial ledger state is `0/100`.

## Immutability and separation

Previously frozen Serie A/La Liga, Bundesliga and Ligue 1 prospective ledgers must not be changed by this work. Future Turkish historical/model research is a separate protocol. Existing MARKET_ONLY rows, once captured, may never receive retrospective AI predictions or be relabeled as prospective AI evidence.

## Readiness meaning

`CAPTURE_READY=true` under this protocol means only that clean pre-match MARKET_ONLY evidence can be appended when an admissible source snapshot already exists. It does **not** mean `MODEL_READY`, `CALIBRATION_READY` or `PROSPECTIVE_AI_READY`.