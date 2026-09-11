# Ligue 1 Prospective MARKET_ONLY Capture V1

Date frozen: 2026-09-11
League: `LIGUE_1`
Protocol: `LIGUE_1_MARKET_ONLY_V1`
Target: `100` prospective observations

## Purpose

Create a league-specific, research-only prospective market ledger for Ligue 1 without broadening or modifying the already-frozen EPL, Serie A, La Liga, or Bundesliga protocols.

This protocol is frozen before inspecting any live Ligue 1 future fixture values for the first observation.

## Evidence class

Every row is **MARKET_ONLY** evidence. It records pre-kickoff market information only.

A row captured under this protocol:

- is not an AI prediction;
- does not imply `MODEL_READY`;
- does not imply `PROSPECTIVE_AI_READY`;
- must never be backfilled with an AI prediction after kickoff;
- must never be retrospectively relabeled as prospective AI evidence.

Any future Ligue 1 AI protocol must be separately preregistered and must begin with genuinely future predictions created after that AI protocol is frozen.

## Frozen capture contract

A valid observation must contain exactly the admissible provenance/market information required by the capture tool:

- league = `LIGUE_1`;
- source event id;
- source market snapshot time in UTC;
- home and away teams;
- kickoff time in UTC;
- capture time in UTC;
- decimal 1X2 odds: home, draw, away.

Timing rules:

1. `captured_at_utc < commence_time_utc`;
2. `source_snapshot_time_utc < commence_time_utc`;
3. `source_snapshot_time_utc <= captured_at_utc`.

Outcome/result/score/settlement fields are forbidden. AI/model probability, model version, and model artifact fields are forbidden.

All decimal odds must be finite and strictly greater than `1.0`.

## Identity and immutability

Canonical key:

`LIGUE_1|normalized_home|normalized_away|kickoff_utc|LIGUE_1_MARKET_ONLY_V1`

The committed ledger is:

`experiments/ligue1_market_only_v1.csv`

Observation numbers must be contiguous from `1` through at most `100`.

An exact duplicate capture is idempotent and returns `UNCHANGED`. A same-key capture with any different frozen value is a conflicting rewrite and must fail closed. Corrupt sequence numbers, schema changes, duplicate canonical keys, protocol changes, target changes, or attempts to append beyond `100/100` must fail closed.

## Live-source boundary

The capture tool itself has no Supabase or Odds API dependency.

After this contract is committed, a separate operator step may perform a **read-only** live query to discover an admissible future Ligue 1 fixture and its already-existing market snapshot. Such a query may read only fixture identity, kickoff, snapshot timestamp, and market odds required by this protocol. It must not read score, result, outcome, settlement, or any prospective evaluation field.

No paid Odds API request is authorized by this protocol.

## Safety boundary

This protocol must not:

- create or mutate any `.pkl` artifact;
- promote a model;
- alter existing EPL/non-EPL/Bundesliga prospective ledgers;
- use a production AI model;
- use future outcomes;
- write to Supabase;
- spend Odds API credits.

CI must revalidate the committed Ligue 1 ledger and prove production artifacts are unchanged.

## Scientific status

`CAPTURE_READY=true` only after the capture implementation and regression contract pass CI.

Even if a valid `1/100` MARKET_ONLY observation is captured, Ligue 1 remains `MODEL_READY=false` and `PROSPECTIVE_AI_READY=false` until a separate league-specific preregistered AI-readiness protocol passes its own frozen gate.
