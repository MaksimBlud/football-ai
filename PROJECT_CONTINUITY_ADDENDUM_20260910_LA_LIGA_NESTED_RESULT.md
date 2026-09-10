# PROJECT CONTINUITY ADDENDUM — 2026-09-10 — La Liga nested development V1 result

This is the newest execution-pointer override after `PROJECT_CONTINUITY.md` and earlier 2026-09-10 addenda.

## Status classification

- PR #240 non-EPL readiness / La Liga pure-AI candidate gate: `MERGED / CLOSED`.
- PR #241 pre-existing La Liga hybrid diagnostic v1: `MERGED / CLOSED`.
- La Liga pure-AI v1: `CLOSED / REJECTED_NO_ARTIFACT`.
- La Liga frozen hybrid v1: `CLOSED / REJECTED`.
- La Liga nested historical development V1 candidate family: `CLOSED / REJECTED_NO_FREEZE_RECOMMENDATION` once PR #242 is merged.
- La Liga `MODEL_READY`: false.
- La Liga `CALIBRATION_READY`: false.
- La Liga `PROVENANCE_READY`: false.
- La Liga `PROSPECTIVE_READY`: false.
- P0-A paid refresh remains `MANUAL_PAID_GATE`.
- EPL prospective evaluation remains `TIME-FROZEN_GATE`.

## PR #241 completion proof

PR #241 `Run frozen La Liga hybrid diagnostic v1` was tested on exact head:

`95e4e273b98bb936dcaafb4d023fef2ca484b289`

All six exact-head workflows passed. Fresh `main` remained at PR #240 merge `d1a882007f1d9d8c46ffc020be8e84ab1b5c1e72`, so the exact tested head was merged as:

`53bba74724232b43db4cb3072712ac6e40f9d938`

Post-merge `La Liga Hybrid Diagnostic V1` push workflow run `34500280211` passed on that exact main SHA.

No paid provider request, prospective outcome/result/settlement read, Supabase write, production artifact mutation/promotion, or retrospective MARKET_ONLY-to-AI backfill occurred.

## New historical development V1 boundary

PR #242 introduces a new research-only nested chronological development protocol after the already-observed 2025-2026 results.

It does **not** reuse 2025-2026 as a fresh holdout. `2025-2026` is explicitly excluded from all V1 training, model selection, alpha selection, and evaluation. In the CI proof, 375 trainable rows from the observed 2025-2026 season were excluded and the maximum development OOS season was `2024-2025`.

The candidate space was frozen before execution to the already-existing:
- 3 feature sets: `core`, `core_elo`, `full_no_odds`;
- 4 model variants: `logistic_l2`, `xgb_shallow`, `xgb_base`, `xgb_regularized`;
- 12 model-feature combinations total;
- pre-existing alpha grid `0.05` through `0.50` in 0.05 increments.

No new feature family, model family, hyperparameter family, calibration family, alpha, or threshold was added after observing the result.

Nested outer seasons were fixed as:
- `2022-2023`;
- `2023-2024`;
- `2024-2025`.

Each outer recipe was selected only from earlier chronological OOS seasons.

## PR #242 first proof result

Initial tested head before this continuity-result commit:

`89ae639f48d5679470044ab6bb37209748fb61d1`

All six exact-head workflows passed, including dedicated `La Liga Nested Development V1` run `34500755975`. Both dedicated jobs passed: preregistered contract tests and the full completed-history development proof. Production `.pkl` diff guard passed.

Result:

`REJECTED_NO_FREEZE_RECOMMENDATION`

### Outer aggregate

Hybrid:
- accuracy: `0.5480176211`
- logloss: `0.9602850315`
- Brier: `0.5700374432`

Market:
- accuracy: `0.5488986784`
- logloss: `0.9600937214`
- Brier: `0.5700277067`

The nested hybrid is therefore slightly worse than market on **all three aggregate metrics**.

### Fold robustness

Metric wins versus market:
- accuracy: `1/3` outer seasons;
- logloss: `1/3`;
- Brier: `1/3`;
- all three metrics simultaneously: `0/3`.

Frozen minimum was at least `2/3` per metric and at least `2/3` all-three folds, plus aggregate wins on all three metrics. Every robustness requirement fails.

Per-fold behavior also shows instability:
- 2022-2023: `core_elo + logistic_l2`, alpha `0.15`; logloss/Brier improve slightly, accuracy worsens;
- 2023-2024: `full_no_odds + xgb_shallow`, alpha `0.15`; hybrid loses to market on all three metrics;
- 2024-2025: `full_no_odds + xgb_shallow`, alpha `0.10`; accuracy improves slightly, logloss/Brier worsen.

A final recipe selected over all five pre-2025-2026 development OOS seasons remains `full_no_odds + xgb_shallow + alpha 0.10` and slightly beats market on all three aggregate development metrics. That fact is **not** sufficient: the preregistered nested robustness gate fails, so no future-freeze recommendation is allowed.

## Decision

Do not tune La Liga V1 again after seeing this result. The exact candidate family is now scientifically closed unless a new external fact or regression invalidates the proof.

In particular:
- do not change the alpha grid;
- do not weaken the tri-metric gate;
- do not cherry-pick the aggregate five-season result over the nested failure;
- do not use 2025-2026 as a new untouched holdout;
- do not start a La Liga prospective AI shadow run from this family;
- do not create/promote a candidate artifact from this result.

The correct conclusion is that the currently bounded La Liga football-only + simple market-blend family does not demonstrate sufficiently stable historical incremental edge over the market.

## Safety proof

During PR #242 proof:
- paid provider requests: 0;
- prospective outcome/result/settlement reads: 0;
- Supabase writes: 0;
- production `.pkl` changes: 0;
- candidate model artifacts saved: 0;
- production promotions: 0;
- retrospective MARKET_ONLY-to-AI backfill: 0.

Production `football_model_xgboost_elo.pkl` remained:

`1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`

## Current execution pointer override

1. Finish PR #242 after this continuity commit: rerun exact-head full CI, fresh-main check, exact-head merge, and post-merge push proof.
2. Mark the bounded La Liga model-development V1 family `CLOSED`; do not rerun/tune it without a genuinely new preregistered hypothesis and a defensible evidence boundary.
3. NEXT safe non-EPL AI research item: **SERIE_A league-specific model readiness / historical candidate-development audit and implementation**, because the prior non-EPL readiness audit identified Serie A as the next closest league after La Liga: deep completed history and generic historical walk-forward exist, but no dedicated league-specific candidate/calibration/provenance path exists yet.
4. For Serie A, begin from fresh `main` and existing historical/PIT/normalization infrastructure; do not copy La Liga conclusions or force the EPL production model onto Serie A.
5. First establish the exact Serie A historical/OOS evidence boundary and dedicated readiness gaps. Only then add the smallest research-only pipeline required to test a preregistered candidate family.
6. Keep Serie A prospective readiness false until a valid candidate and separately frozen future-only protocol exist. No retroactive conversion of MARKET_ONLY rows into AI evidence.
7. P0-A remains behind `MANUAL_PAID_GATE`; no paid refresh is authorized by generic continuation.
