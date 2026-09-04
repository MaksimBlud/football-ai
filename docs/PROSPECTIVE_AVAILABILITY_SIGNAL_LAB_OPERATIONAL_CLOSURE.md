# Prospective Availability Signal Lab — Operational Closure

Status: **OPERATIONAL IMPLEMENTATION CLOSED / RESEARCH-ONLY / EXTERNALLY GATED**

Date: **2026-09-04**

This closure means the engineering, information-time safety, collection contract, feature contract, readiness monitoring, explicit evaluation gate, and external activation monitoring for `PROSPECTIVE_AVAILABILITY_SIGNAL_LAB` are complete. It does **not** claim an availability research result and it does **not** claim live collection is activated.

## Frozen research contract

The block uses only point-in-time availability observations first seen before the selected prediction cutoff. Historical injury start/end dates are not accepted as substitutes for publication-time evidence. The feature family remains `COUNT_ONLY_V1`: home/away injury counts, suspension counts, total unavailable-player counts, and their differences. Player-importance weighting remains disabled.

The market cutoff remains kickoff minus six hours. The paired comparison remains `MARKET_MODEL` versus `MARKET_AVAILABILITY` with the preregistered model family. The frozen readiness gate remains at least 100 paired finished fixtures, four calendar months, and two valid expanding monthly evaluation blocks in each of EPL, La Liga, and Serie A, with at least 60 prior training fixtures and 20 fixtures per scored test block.

## Operational guarantees

The implementation is fail-closed:

- the provider/schema global preflight must pass for all three leagues before the collector enters any persistence path;
- immutable full-poll snapshots represent both unavailable-player states and zero-item states without rewriting prior observations;
- prediction-time features use only the latest complete poll observed not later than the selected market snapshot timestamp;
- the scheduled readiness path uses canonical settlement identity presence only and does not query `result` values;
- outcome evaluation can run only through manual `workflow_dispatch` with `evaluate=true`;
- the explicit evaluation path reloads outcome values, rechecks the frozen all-three-league readiness gate, and refuses scoring if the gate is not satisfied;
- no scheduled path can expose Brier, log loss, paired deltas, or any other outcome comparison;
- production `.pkl` artifacts remain outside the research contour.

## External activation boundary

The connected environment was audited on 2026-09-04. The two additive Supabase tables required by the block are absent from PostgREST, and the available API-Football free-plan credential does not provide 2026 injury coverage for EPL, La Liga, or Serie A. No database-management credential, alternate provider key, or DDL-capable PostgREST RPC is available in the connected GitHub Actions environment.

The required migration is already present at `supabase/migrations/202609030002_prospective_availability.sql`. Applying it requires external Supabase database-management access. Current-season injury collection requires a provider credential with 2026 coverage. The repository must not emulate either dependency through unsupported writes or retrospective injury data.

A dedicated read-only activation monitor now checks the schema and provider gates on a schedule and writes `activation_readiness.json` with `BLOCKED` or `READY`. It never applies DDL, never enables `PROSPECTIVE_AVAILABILITY_ENABLED`, and never starts collection. External gate readiness therefore remains observable without silently changing activation state.

## Production isolation

No prediction ledger, live selection rule, production inference path, calibrator, threshold, or production model artifact is modified by this block. Even a future positive research result requires a separate explicit production-promotion decision.

## Closure decision

No additional availability feature engineering, player-importance weighting, cutoff tuning, model-family tuning, or retrospective injury reconstruction is permitted while the block is externally gated or later accumulating its prospective sample. Infrastructure changes are justified only to repair a concrete operational failure without changing the frozen hypothesis.

The implementation phase is therefore **CLOSED**. The scientific experiment remains **ACTIVE_EXTERNALLY_GATED** until the schema and provider dependencies pass; after activation it may accumulate genuine prospective data, and outcome evaluation remains a single explicit preregistered action after the frozen readiness gate is satisfied.
