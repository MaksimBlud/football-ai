# Turkey Super Lig + Primeira Liga — MARKET_ONLY Status

Status: **IMPLEMENTATION COMPLETE / OPERATIONALLY WIRED / RESEARCH-ONLY / LIVE DATA QUOTA-GATED**

## Scope

The two leagues are registered as:

- `TURKEY_SUPER_LIG` — `soccer_turkey_super_league`, timezone `Europe/Istanbul`, Football-Data historical code `T1`;
- `PRIMEIRA_LIGA` — `soccer_portugal_primeira_liga`, timezone `Europe/Lisbon`, Football-Data historical code `P1`.

Both are `MARKET_ONLY`. Structural V2 remains `CALIBRATION_REQUIRED`; no alpha or edge threshold is guessed or inherited from another league.

## Canonical runtime source of truth

Each league has exactly one canonical runtime module:

- `turkey_super_lig_runtime_config.py`;
- `primeira_liga_runtime_config.py`.

The obsolete `turkey_runtime_config.py` and `primeira_runtime_config.py` modules were removed because they defined different data-path prefixes and could create a split-brain runtime if accidentally imported. Regression coverage now requires the legacy modules to remain absent and verifies the canonical path prefixes.

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

## Viewer and Multi-Market integration

Research Viewer support is complete for both leagues:

- the viewer operational metadata includes all nine operational leagues, including `TURKEY_SUPER_LIG` and `PRIMEIRA_LIGA`;
- MARKET_ONLY cards for both leagues are accepted without Structural V2 probabilities;
- Multi-Market snapshots attach using the league-aware identity `(league, event_id)` so an event-id collision across leagues cannot cross-match;
- the standalone Multi-Market viewer builds its league selector dynamically from the returned match payload and has no hardcoded league allow-list.

The Multi-Market collector is also league-dynamic. It reads `league` and `event_id` from canonical `odds_snapshots`, resolves the provider sport key through the central league registry, and therefore requires no Turkey/Portugal-specific market code. Handicap, total-goals and corner-market collection will become eligible automatically when the shared Multi-Market schema/quota gates are open and the leagues have future 1X2 event ids.

## CI and automation hardening

Turkey/Portugal focused PR validation now executes the complete `tests/test_turkey_portugal_*.py` suite rather than a fixed historical subset. It compiles the canonical runtime, operational and viewer modules and enforces the production `.pkl` artifact guard.

The MARKET_ONLY push-proof workflow is triggered by changes to either canonical runtime config in addition to the operational modules themselves. This ensures runtime-config changes receive an immediate post-merge live wiring check rather than waiting only for the scheduled cycle.

## Live proof — 2026-09-05

Post-merge read-only/bootstrap proof confirmed both provider sport keys are present and active:

- `TURKEY_SUPER_LIG`: catalog present, active;
- `PRIMEIRA_LIGA`: catalog present, active.

The provider reported `remaining=215`, `used=285`, `last_cost=0` on the zero-cost catalog check.

The dedicated operational cycle then ran for both leagues and correctly returned `BLOCKED_LOW_QUOTA` for both odds and results. It performed zero paid provider requests, inserted zero ledger/results rows, did not use Structural V2, and left the production model hash unchanged.

A second post-hardening push-proof repeated the same result for both leagues with `remaining=215`: snapshots and results were both `BLOCKED_LOW_QUOTA`, `paid requests=0`, ledger writes remained zero, `production_model_used=False`, `structural_v2_used=False`, and the production model hash stayed unchanged.

This is the expected fail-closed state. It proves operational wiring without consuming scarce quota or pretending that live snapshots already exist.

## Activation gate

Actual h2h snapshot/results collection starts automatically only when the zero-cost preflight observes at least 500 remaining requests. Until then the two-hour workflow remains safely blocked.

The first future run above the threshold will exercise the already-installed chain:

`provider h2h -> odds_snapshots -> MARKET_ONLY prediction ledger -> finished-result settlement`.

No code or registry activation change is required for that transition.

## Production isolation

This block does not train, calibrate, promote, or modify production models. All structural probabilities remain absent. Existing production `.pkl` artifacts and existing league pipelines are outside the write path.

## Closure

The Turkey Super Lig + Primeira Liga MARKET_ONLY implementation is considered operationally complete. Remaining blockers are external gates only: provider quota for live h2h/results collection and the shared Multi-Market schema/quota gates for additional markets.
