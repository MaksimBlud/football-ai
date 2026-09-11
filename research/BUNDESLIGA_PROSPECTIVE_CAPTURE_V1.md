# Bundesliga Prospective MARKET_ONLY Capture V1

Status: FROZEN BEFORE FIRST BUNDESLIGA CAPTURE
Date frozen: 2026-09-11
League: `BUNDESLIGA`
Protocol: `BUNDESLIGA_MARKET_ONLY_V1`
Target: 100 prospective observations

## Purpose

Create a durable, fail-closed pre-match market-only evidence stream for Bundesliga without changing the already frozen `NON_EPL_MARKET_ONLY_V1` contract used by Serie A and La Liga.

This protocol is collection infrastructure only. It does not make Bundesliga model-ready or prospective-AI-ready, and it does not authorize model promotion.

## Frozen evidence rules

- League must be exactly `BUNDESLIGA`.
- Evidence class is `MARKET_ONLY` only.
- Every row must be captured strictly before kickoff.
- Every source market snapshot must be strictly before kickoff and no later than `captured_at_utc`.
- Immutable source provenance is mandatory: `source_event_id` and exact `source_snapshot_time_utc`.
- Finite positive decimal 1X2 prices greater than `1.0` are mandatory.
- Outcome, result, score, winner and settlement fields are forbidden at capture time.
- AI/model probability, model version and model artifact fields are forbidden.
- Canonical fixture identity is `league + normalized home team + normalized away team + UTC kickoff + protocol`.
- The first valid row is observation `1/100`; counters must remain contiguous.
- Duplicate canonical rows are idempotent only when all stable market values and provenance are identical.
- Any conflicting rewrite fails closed.
- Existing malformed or non-contiguous ledger state fails closed.
- The committed ledger must be revalidated in CI.
- The protocol itself has no database client or paid odds-provider dependency.
- No paid API authorization is created by this protocol.
- No production `.pkl` dependency or write path is permitted.

## Separation from existing protocols

`NON_EPL_MARKET_ONLY_V1` remains frozen for `SERIE_A` and `LA_LIGA` only. This protocol does not broaden, rewrite or reinterpret it. Their existing rows and counters remain immutable.

Bundesliga gets its own ledger:

`experiments/bundesliga_market_only_v1.csv`

No Bundesliga row captured under this protocol may later receive a retrospective AI prediction or be relabeled as prospective AI evidence.

## Live-data rule

A live read-only source may be consulted only after this document is committed. Such a query may retrieve future fixture identity, kickoff, market snapshot time, source event id and 1X2 prices. It must not retrieve score, result, outcome, winner or settlement fields.

If no valid future Bundesliga fixture with admissible pre-match source provenance exists at capture time, the protocol remains `CAPTURE_READY=true` at `0/100`; no row may be invented and no paid API call may be substituted without explicit authorization.

## CI gate

Before merge, CI must prove:

1. valid pre-match Bundesliga MARKET_ONLY rows are accepted;
2. non-Bundesliga rows fail closed;
3. post-kickoff captures and snapshots fail closed;
4. forbidden outcome and AI fields fail closed;
5. missing provenance fails closed;
6. duplicates are idempotent and conflicts fail closed;
7. sequence corruption and target overflow fail closed;
8. the committed Bundesliga ledger is valid when present;
9. existing Serie A / La Liga prospective ledger is untouched;
10. no production `.pkl` changes occur.

## Scientific status

A successful capture implementation means only:

`CAPTURE_READY=true` for Bundesliga `MARKET_ONLY` prospective research.

It does not imply:

- `MODEL_READY=true`
- `CALIBRATION_READY=true`
- `PROSPECTIVE_AI_READY=true`

Those statuses require a separate league-specific preregistered AI-readiness protocol and independent evidence gate.
