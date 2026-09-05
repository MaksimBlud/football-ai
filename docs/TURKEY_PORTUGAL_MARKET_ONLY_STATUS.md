# Turkey Super Lig + Primeira Liga — MARKET_ONLY Status

Status: **IMPLEMENTATION IN REVIEW / RESEARCH-ONLY / LIVE ACTIVATION QUOTA-GATED**

## Scope

The two leagues are registered as:

- `TURKEY_SUPER_LIG` — `soccer_turkey_super_league`, timezone `Europe/Istanbul`, Football-Data historical code `T1`;
- `PRIMEIRA_LIGA` — `soccer_portugal_primeira_liga`, timezone `Europe/Lisbon`, Football-Data historical code `P1`.

Both start as `MARKET_ONLY`. Structural V2 is `CALIBRATION_REQUIRED`; no alpha or edge threshold is guessed or inherited from another league.

## Operational foundation

The implementation provides:

- h2h odds normalization into the canonical `odds_snapshots` schema;
- adaptive 12h/6h/4h/2h collection cadence;
- zero-cost `/sports` quota preflight before any paid provider request;
- frozen collection start floor of 500 remaining requests;
- canonical append-only `league_prediction_ledger` MARKET_ONLY bridge;
- The Odds API score parsing and canonical `league_finished_results` settlement;
- two-hour scheduled matrix workflow for both leagues;
- production `.pkl` hash protection and dedicated PR validation.

## Current activation gate

The last known provider quota before this block was `remaining=215`, below the frozen 500-request start floor. Therefore the operational cycle must report `BLOCKED_LOW_QUOTA` and perform zero paid odds/scores requests until quota recovers.

Central `collection_enabled` / `operational_collection_enabled` flags remain false until a real post-merge live snapshot + ledger + settlement proof is obtained. This prevents registry state from overstating operational readiness.

## Production isolation

This block does not train, calibrate, promote, or modify production models. All structural probabilities remain absent. Existing production `.pkl` artifacts and existing league pipelines are outside the write path.
