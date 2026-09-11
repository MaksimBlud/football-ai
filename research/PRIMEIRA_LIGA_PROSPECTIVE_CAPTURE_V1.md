# Primeira Liga Prospective Capture V1

Date frozen: 2026-09-11
Protocol: `PRIMEIRA_LIGA_MARKET_ONLY_V1`
League: `PRIMEIRA_LIGA`
Target: 100 immutable prospective MARKET_ONLY observations

## Purpose

Create a league-specific prospective evidence ledger for Portugal's Primeira Liga without modifying any previously frozen league protocol and without enabling AI/model semantics.

## Frozen evidence rules

An observation is admissible only when all of the following are true before it is appended:

- `league` is exactly `PRIMEIRA_LIGA`;
- evidence class is MARKET_ONLY; no AI or Structural V2 probability is permitted;
- capture time is strictly before kickoff;
- source market snapshot is strictly before kickoff and no later than capture time;
- `source_event_id` and exact `source_snapshot_time_utc` are mandatory provenance;
- 1X2 decimal odds are finite and strictly greater than 1.0;
- outcome/result/score/winner/settlement fields are forbidden;
- model probability/version/artifact fields are forbidden;
- canonical identity is league + normalized home + normalized away + UTC kickoff + protocol;
- observation numbers are contiguous from 1 to 100;
- exact replay is idempotent only when all stable market/provenance values are identical;
- conflicting rewrites, malformed schema, duplicate keys, non-contiguous sequence and target overflow fail closed.

The committed ledger may validly contain zero rows. `0/100` means capture-ready but no admissible prospective evidence has yet been recorded; retrospective backfill is forbidden.

## Paid-provider boundary

This protocol contains no Supabase or The Odds API client and authorizes no provider request. The existing Turkey/Portugal provider workflow remains manual `workflow_dispatch`; this protocol neither schedules nor triggers it. Paid requests remain governed by the project's existing budget and authorization rules.

At freeze time a read-only Supabase audit found zero `odds_snapshots` rows for `PRIMEIRA_LIGA`, therefore the correct initial state is `0/100`.

## Immutability and separation

All previously frozen prospective ledgers, including Serie A/La Liga, Bundesliga, Ligue 1, Eredivisie and Turkey Super Lig, must remain byte-for-byte unchanged by this work. Any later Primeira Liga historical/model study must use a separate preregistered protocol. MARKET_ONLY rows may never be retrospectively given AI predictions or relabeled as prospective AI evidence.

## Readiness meaning

`CAPTURE_READY=true` means only that clean pre-match MARKET_ONLY evidence can be appended when an admissible source snapshot already exists. It does **not** imply `MODEL_READY`, `CALIBRATION_READY` or `PROSPECTIVE_AI_READY`.