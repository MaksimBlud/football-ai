# Turkey Super Lig + Primeira Liga — MARKET_ONLY Status

Status: **IMPLEMENTATION COMPLETE / RESEARCH-ONLY / LIVE DATA QUOTA-GATED**

## Scope

The two leagues are registered as:

- `TURKEY_SUPER_LIG` — `soccer_turkey_super_league`, timezone `Europe/Istanbul`, Football-Data historical code `T1`;
- `PRIMEIRA_LIGA` — `soccer_portugal_primeira_liga`, timezone `Europe/Lisbon`, Football-Data historical code `P1`.

Both are `MARKET_ONLY`. Structural V2 remains `CALIBRATION_REQUIRED`; no alpha or edge threshold is guessed or inherited from another league.

## Operational foundation

The implementation provides:

- h2h odds normalization into the canonical `odds_snapshots` schema;
- adaptive 12h/6h/4h/2h collection cadence;
- zero-cost `/sports` quota preflight before any paid provider request;
- frozen collection start floor of 500 remaining requests;
- canonical append-only `league_prediction_ledger` MARKET_ONLY bridge;
- The Odds API score parsing and canonical `league_finished_results` settlement;
- a two-hour scheduled matrix workflow for both leagues;
- production `.pkl` hash protection and dedicated PR validation.

`collection_enabled` remains false because these leagues do not use the generic collector. `operational_collection_enabled` is true because the dedicated quota-safe workflow is installed and live-proven.

## Live proof — 2026-09-05

Post-merge read-only/bootstrap proof confirmed both provider sport keys are present and active:

- `TURKEY_SUPER_LIG`: catalog present, active;
- `PRIMEIRA_LIGA`: catalog present, active.

The provider reported `remaining=215`, `used=285`, `last_cost=0` on the zero-cost catalog check.

The dedicated operational cycle then ran for both leagues and correctly returned `BLOCKED_LOW_QUOTA` for both odds and results. It performed zero paid provider requests, inserted zero ledger/results rows, did not use Structural V2, and left the production model hash unchanged.

This is the expected fail-closed state. It proves operational wiring without consuming scarce quota or pretending that live snapshots already exist.

## Activation gate

Actual h2h snapshot/results collection starts automatically only when the zero-cost preflight observes at least 500 remaining requests. Until then the two-hour workflow remains safely blocked.

The first future run above the threshold will exercise the already-installed chain:

`provider h2h -> odds_snapshots -> MARKET_ONLY prediction ledger -> finished-result settlement`.

No code or registry activation change is required for that transition.

## Production isolation

This block does not train, calibrate, promote, or modify production models. All structural probabilities remain absent. Existing production `.pkl` artifacts and existing league pipelines are outside the write path.
