# PROJECT CONTINUITY ADDENDUM — 2026-09-10 — La Liga model/hybrid historical gates

This addendum is the newest execution-pointer override after `PROJECT_CONTINUITY.md` and earlier 2026-09-10 non-EPL readiness addendum.

## Status classification

- PR #240 non-EPL readiness + La Liga pure-AI candidate gate: `MERGED / CLOSED`.
- La Liga pure-AI v1 candidate: `CLOSED / REJECTED_NO_ARTIFACT`.
- Pre-existing La Liga AI+market hybrid diagnostic v1: `CLOSED / REJECTED` after PR #241 historical proof.
- La Liga `MODEL_READY`: false.
- La Liga `CALIBRATION_READY`: false.
- La Liga `PROVENANCE_READY`: false.
- La Liga `PROSPECTIVE_READY`: false.
- Existing non-EPL MARKET_ONLY collection paths: remain separate and unchanged.
- P0-A paid refresh: remains `MANUAL_PAID_GATE`.
- EPL prospective cohort: remains `TIME-FROZEN_GATE`; no outcomes were read here.

## PR #240 completion proof

PR #240 `Formalize non-EPL model readiness and La Liga candidate gate` was tested on exact head:

`071e9b8107d6d83efff4f1218ce87785ef156b4a`

All six exact-head PR workflows passed, including the dedicated Non-EPL Model Readiness workflow and its historical La Liga candidate proof. Fresh-main remained compatible and the exact tested head was merged as:

`d1a882007f1d9d8c46ffc020be8e84ab1b5c1e72`

Post-merge Non-EPL Model Readiness push workflow on that main SHA also passed.

No paid provider request, prospective outcome/settlement read, production `.pkl` mutation, model promotion, or MARKET_ONLY-to-AI backfill occurred.

## La Liga pure-AI v1 historical result

Research-only candidate builder result:

`REJECTED_NO_ARTIFACT`

Selected model/feature set:
- `xgb_shallow`
- `full_no_odds`
- selection seasons 2020-2021 through 2024-2025
- locked historical holdout 2025-2026

Selection result:
- rows: 1885
- accuracy: 0.5283819629
- logloss: 0.9876816273
- Brier: 0.5880179556

Temperature calibration selected on pre-holdout OOS predictions:
- temperature: 1.0550000000

2025-2026 historical holdout:
- raw AI accuracy: 0.5200000000
- raw AI logloss: 0.9773806623
- raw AI Brier: 0.5780842663
- calibrated AI accuracy: 0.5200000000
- calibrated AI logloss: 0.9777803053
- calibrated AI Brier: 0.5785206098
- market accuracy: 0.5466666667
- market logloss: 0.9673559414
- market Brier: 0.5736861605

Every strict gate condition failed: calibration did not improve logloss or Brier and calibrated AI did not beat market accuracy/logloss/Brier. Therefore no candidate model/calibrator/manifest was written.

Production model SHA remained unchanged:

`football_model_xgboost_elo.pkl = 1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`

## Pre-existing hybrid diagnostic v1 result

A secondary historical diagnostic was allowed because `league_model_diagnostics.py` and its alpha protocol already existed in commit:

`1084a5aa617c45fcd9c6e0583e2d7c4786bbea59` (2026-08-23)

This predates the 2026-09-10 pure-AI holdout reveal. PR #241 executes that algorithm unchanged; CI pins the exact diagnostic Git blob:

`915a3a283653897a2eab9e9501f6e03ca8ef1464`

Frozen protocol:
- winner comes from existing model sweep;
- alpha grid = 0.05, 0.10, ..., 0.50;
- alpha chosen only on 2020-2021 through 2024-2025;
- then evaluated once on 2025-2026;
- strict PASS requires hybrid to beat market on accuracy, logloss, and Brier.

Selected alpha:

`0.10`

Selection aggregate:
- hybrid accuracy: 0.5416445623
- market accuracy: 0.5411140584
- hybrid logloss: 0.9694705577
- market logloss: 0.9696723979
- hybrid Brier: 0.5759945383
- market Brier: 0.5761366284

Thus the frozen hybrid was slightly better than the market on all three selection metrics.

2025-2026 historical holdout:
- AI accuracy: 0.5200000000
- AI logloss: 0.9773806930
- AI Brier: 0.5780842674
- market accuracy: 0.5466666667
- market logloss: 0.9673559414
- market Brier: 0.5736861605
- hybrid accuracy: 0.5333333333
- hybrid logloss: 0.9668178330
- hybrid Brier: 0.5731802882

The hybrid improved market logloss and Brier but failed the frozen accuracy requirement, so:

`hybrid_beats_market_holdout = false`

The gate remains rejected. No candidate artifact was saved and no promotion occurred. Production artifacts remained unchanged.

## Interpretation boundary

The 2025-2026 La Liga season has now been observed by both the formal pure-AI gate and the pre-existing frozen hybrid diagnostic. It MUST NOT be reused as a supposedly fresh untouched holdout for any newly invented model, feature, calibration, alpha, threshold, or gate.

The small hybrid probability-quality improvement is diagnostic evidence only. It is not sufficient to relabel this experiment as a PASS because the preregistered gate required all three metrics. The accuracy condition must not be weakened after observing the result.

Any future La Liga model work must be explicitly framed as a new historical development protocol. It may use nested/rolling/expanding validation on earlier completed seasons for model development, while treating 2025-2026 only as already-observed benchmark context. A new confirmatory claim requires genuinely future/untouched evidence frozen before eligible fixtures.

## Safety proof

During this block:
- paid provider requests: 0;
- prospective outcome/result/settlement reads: 0;
- Supabase writes: 0;
- production `.pkl` changes: 0;
- production promotions: 0;
- retroactive AI backfill of MARKET_ONLY rows: 0.

## Current execution pointer override

1. Finish PR #241 exact-head CI after this continuity addendum commit; fresh-main check; exact-head merge; post-merge push proof.
2. After PR #241 is closed, mark the pre-existing La Liga pure-AI/hybrid v1 paths `CLOSED` and do not rerun them absent a regression or new external fact.
3. NEXT safe research item: design a **new preregistered La Liga historical development protocol** that does not claim 2025-2026 is untouched. Prefer nested/rolling walk-forward selection/calibration robustness using completed pre-2025-2026 seasons, with explicit complexity limits and a no-optional-stopping rule.
4. The purpose of that development protocol is to decide whether any fixed formula is strong enough to freeze for a genuinely future-only prospective shadow run. It must not create retrospective prospective evidence.
5. Do not activate La Liga AI prospective readiness until a separately frozen, provenance-complete future protocol exists. Do not promote any model without explicit user instruction.
6. If this development path cannot produce defensible evidence without reusing already-observed holdout information as confirmatory proof, close it fail-closed and move to the next league/research item rather than weakening gates.
