# Continuity Addendum — Primeira Liga prospective MARKET_ONLY capture V1

Date: 2026-09-11
Protocol: `PRIMEIRA_LIGA_MARKET_ONLY_V1`
League: `PRIMEIRA_LIGA`

## State

- `CAPTURE_READY=true`
- target: `100`
- committed count: `0/100`
- `MODEL_READY=false`
- `PROSPECTIVE_AI_READY=false`
- retrospective backfill forbidden

A read-only live Supabase audit performed before the contract was frozen found `0` rows and `0` unique events in `odds_snapshots` for `PRIMEIRA_LIGA`. Therefore no real observation was admissible and the canonical ledger intentionally starts at zero.

## Frozen contract

The contract was frozen before any Primeira Liga prospective observation in commit `2f1d0664f5c2af9cbcc73efe575699b09af6e07a`.

It requires exact league identity, strictly pre-kickoff capture and source snapshot timing, source event/snapshot provenance, valid 1X2 decimal odds, canonical fixture identity, contiguous numbering, exact-replay idempotence and fail-closed conflict/schema/target handling. Outcome/result/score/settlement fields and all AI/Structural probability or artifact fields are forbidden.

## Provider boundary

This capture tool has no Supabase client, no The Odds API client and no production model dependency. The existing Turkey/Portugal provider workflow remains manual `workflow_dispatch`; this work does not schedule or trigger a paid request.

## Isolation

Previously frozen prospective ledgers are checksum-protected by regression tests. Historical/model work for Portugal must be a separate preregistered protocol. MARKET_ONLY observations, once recorded, may never be retrospectively relabeled as prospective AI evidence.
