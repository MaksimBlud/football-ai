# La Liga Nested Historical Development V1

## Status

PREREGISTERED / HISTORICAL-DEVELOPMENT-ONLY / RESEARCH-ONLY.

This protocol is created after the already-observed 2025-2026 La Liga pure-AI and pre-existing hybrid results. Therefore it makes **no claim** that 2025-2026 is untouched. The season is explicitly excluded from all training, selection, alpha selection, and evaluation performed by this protocol.

The only valid purpose of this block is to decide whether an existing limited recipe family is robust enough to justify a **separate future-only protocol freeze**. Even a PASS here is not prospective evidence and does not make `PROSPECTIVE_READY=true`.

## Why this is not a rerun of the closed gates

The pure-AI v1 and frozen hybrid v1 paths are CLOSED after PR #240/#241. Their 2025-2026 gates are not rerun or reinterpreted.

This is a new development protocol with a different evidence boundary:

- development data ends at 2024-2025;
- 2025-2026 is excluded rather than reused as a fresh holdout;
- evaluation uses nested chronological walk-forward checks inside the pre-2025-2026 development window;
- no metric or threshold from the failed 2025-2026 result is relaxed.

## Fixed candidate complexity

To avoid post-holdout feature/model proliferation, this protocol may use only the feature/model families that already existed in `league_model_sweep.py`:

Feature sets:
- `core`
- `core_elo`
- `full_no_odds`

Models:
- `logistic_l2`
- `xgb_shallow`
- `xgb_base`
- `xgb_regularized`

Total model-feature variants: **12**.

No new feature set, model family, hyperparameter variant, injury source, market-history feature, threshold, calibration family, or stacking model may be added inside V1 after results are observed.

Hybrid weights use only the pre-existing frozen grid from `league_model_diagnostics.py`:

`0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50`

Pure market (`alpha=0`) remains the benchmark, not an AI candidate.

## Data boundary

Input is the point-in-time La Liga feature/Elo historical dataset produced by the existing completed-history pipeline.

Required OOS development seasons:
- 2020-2021
- 2021-2022
- 2022-2023
- 2023-2024
- 2024-2025

Observed/non-fresh season:
- 2025-2026 — must be present only so its explicit exclusion can be proven; it is excluded before target construction for the development frame.

Any season later than 2025-2026 causes fail-closed rejection of the run.

## Prediction cache / temporal rule

For every one of the 12 model-feature variants and every OOS development season, the model is fitted only on seasons lexically earlier than that OOS season. The resulting OOS probabilities are cached once and reused by the nested procedure.

This prevents later outer-fold results from contaminating earlier predictions and avoids unnecessary repeated model fitting.

## Nested outer protocol

Outer test seasons are fixed as:
- 2022-2023
- 2023-2024
- 2024-2025

For each outer season:

1. Inner OOS seasons are all fixed development OOS seasons earlier than the outer season.
2. Rank all 12 model-feature variants on inner OOS predictions by:
   - lower logloss;
   - then lower Brier;
   - then higher accuracy.
3. For the selected model-feature variant, rank the frozen alpha grid on the same inner OOS seasons by:
   - lower logloss;
   - then lower Brier;
   - then higher accuracy;
   - then lower alpha as the final deterministic tie-breaker.
4. Apply that selected fixed recipe to the chronological outer OOS predictions for the outer season.
5. Compare hybrid against normalized bookmaker-market probabilities on accuracy, logloss, and Brier.

No result from the current or later outer season may influence the recipe selected for that outer season.

## Fixed development gate

V1 is `ELIGIBLE_FOR_FUTURE_PROTOCOL_FREEZE` only if **all** of the following are true:

1. Across all concatenated outer OOS predictions, hybrid strictly beats market on:
   - accuracy;
   - logloss;
   - Brier.
2. Hybrid beats market on each individual metric in at least **2 of 3** outer seasons.
3. Hybrid beats market on **all three metrics simultaneously** in at least **2 of 3** outer seasons.
4. A final recipe selected using all pre-2025-2026 OOS development seasons also beats market on all three aggregate development metrics.

Otherwise status is:

`REJECTED_NO_FREEZE_RECOMMENDATION`

A rejection is a valid scientific result. No criterion may be weakened and V1 may not be rerun with new candidates/weights after seeing the result.

## What PASS would and would not mean

PASS would mean only that this limited historical recipe family has enough pre-2025-2026 nested robustness to justify a separate future-only freeze step.

PASS would **not**:
- turn historical rows into prospective evidence;
- validate the already-observed 2025-2026 season anew;
- activate `PROSPECTIVE_READY` automatically;
- create or promote a production model;
- allow retroactive AI backfill of MARKET_ONLY rows.

The next step after PASS must be a separate provenance-complete future protocol frozen before its first eligible fixture.

## What REJECT means

If V1 rejects, this exact La Liga candidate family is CLOSED. Do not expand/tune it opportunistically inside V1. Move to the next defensible roadmap item/league unless a separately preregistered materially different research hypothesis is justified without treating already-observed evidence as confirmation.

## Safety invariants

- paid provider requests = 0
- prospective outcome/result/settlement reads = 0
- Supabase writes = 0
- production `.pkl` changes = 0
- candidate model artifacts saved = 0
- production promotions = 0
- MARKET_ONLY-to-AI retroactive backfill = 0
