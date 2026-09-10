# La Liga Hybrid Diagnostic V1

## Status

Historical-only, research-only secondary diagnostic. This block does not create a candidate model, does not promote production artifacts, does not read prospective outcomes, and does not spend paid provider credits.

## Why this block exists

PR #240 established the first formal La Liga candidate gate and the fixed pure-AI candidate was rejected on the completed 2025-2026 historical holdout. The result was `REJECTED_NO_ARTIFACT`; therefore MODEL_READY, CALIBRATION_READY, PROVENANCE_READY, and PROSPECTIVE_READY remain fail-closed.

The next safe question is narrower: does the already-defined AI signal add incremental probability quality when blended with the market consensus?

## Frozen implementation provenance

The diagnostic implementation in `league_model_diagnostics.py`, together with the supporting sweep in `league_model_sweep.py`, was introduced in commit `1084a5aa617c45fcd9c6e0583e2d7c4786bbea59` on 2026-08-23, before the 2026-09-10 pure-AI candidate rejection was observed.

This execution must not alter that diagnostic algorithm. CI verifies the current Git blob hash for `league_model_diagnostics.py` is exactly:

`915a3a283653897a2eab9e9501f6e03ca8ef1464`

## Frozen protocol

- League: `LA_LIGA`.
- Data: completed historical seasons only.
- Model/feature winner: selected by the existing `league_model_sweep.py` procedure.
- Selection seasons: 2020-2021 through 2024-2025.
- Secondary historical holdout: 2025-2026.
- Market odds are benchmark / blend inputs, not AI training features.
- Hybrid alpha grid is fixed at 0.05, 0.10, ..., 0.50; alpha=0 is excluded because it is the pure-market benchmark.
- Alpha is selected on the selection seasons by probability quality first: logloss, then Brier, then accuracy.
- The selected alpha is then evaluated once on 2025-2026.
- Strict pass requires the hybrid to beat the market on all three holdout metrics: accuracy, logloss, and Brier.
- Regardless of pass/fail, this diagnostic writes reports only. It saves no candidate model and performs no promotion.

## Interpretation boundary

The 2025-2026 outcomes are no longer a pristine unseen holdout for newly invented post-rejection tuning because the pure-AI v1 result has now been observed. This secondary analysis is allowed only because its implementation and alpha protocol predate that reveal and are executed unchanged.

A positive result would establish retrospective incremental historical evidence for the pre-existing hybrid protocol. It would not by itself make the league prospective-ready and would not justify retroactive AI predictions. Any future prospective experiment must still be frozen before its first eligible future fixture and must preserve model/code/formula provenance.

A negative result closes this pre-existing hybrid path without weakening its gate. Further model work must use a newly preregistered historical development protocol and may not reinterpret the already-observed 2025-2026 season as a fresh holdout.

## Safety invariants

- `prospective_outcomes_read = false`
- paid provider requests = 0
- production `.pkl` changes = 0
- candidate artifact creation = false
- production promotion = false
- MARKET_ONLY observations are not relabeled or backfilled as AI evidence
