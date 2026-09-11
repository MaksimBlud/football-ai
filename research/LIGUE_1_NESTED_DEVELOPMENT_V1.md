# Ligue 1 Nested Historical Development V1

Status: FROZEN BEFORE FIRST RESULT
Date frozen: 2026-09-11
League: `LIGUE_1`
Protocol: `ligue1_nested_development_v1`

## Purpose

Evaluate whether already-completed Ligue 1 history supports freezing a future Ligue 1-specific AI prospective protocol. This is development research only. It cannot create/promote a production model and cannot alter the already-recorded `LIGUE_1_MARKET_ONLY_V1` observation.

## Evidence boundary

- Historical source: repository-configured Football-Data Ligue 1 `F1`, configured seasons `2016-2017` through `2025-2026`.
- Every historical season admitted to this protocol is **development-only**. No season is claimed untouched.
- `2019-2020` is excluded **before any model result is observed** because Ligue 1 was structurally curtailed and that source season is not a complete double round-robin. It is not used for training, model selection, alpha selection, or evaluation.
- Every other configured season through `2025-2026` must pass complete double-round-robin validation or the run fails closed.
- Any historical data later than `2025-2026` is forbidden and must fail closed.
- No current/prospective score, result, outcome or settlement may be read.
- No Supabase access is required or permitted by the runner.
- No paid Odds API request is permitted.
- Existing Ligue 1 MARKET_ONLY prospective rows are excluded from model development and remain immutable market-only evidence.
- Previously rejected La Liga, Serie A and Bundesliga AI families remain closed and are not executed by this protocol.

## Frozen candidate family

Use only the already-existing `league_model_sweep.py` family that predates this Ligue 1 result.

Feature sets:
- `core`
- `core_elo`
- `full_no_odds`

Model variants:
- `logistic_l2`
- `xgb_shallow`
- `xgb_base`
- `xgb_regularized`

Bookmaker 1X2 prices are benchmark-only, never model features.

Hybrid alpha grid is frozen at:

`0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50`

Hybrid probabilities:

`alpha * AI + (1 - alpha) * MARKET`

Probability vectors are numerically renormalized to the simplex before scoring to remove floating-point roundoff only. This does not change the scientific gate, candidate family, folds, or evidence boundary.

## Chronological development protocol

Development OOS seasons:
- `2020-2021`
- `2021-2022`
- `2022-2023`
- `2023-2024`
- `2024-2025`
- `2025-2026`

For every OOS season, models train only on strictly earlier **admitted** seasons. Because `2019-2020` is structurally excluded, it is absent from all training folds.

Outer test seasons:
- `2022-2023`
- `2023-2024`
- `2024-2025`
- `2025-2026`

For each outer season:
1. choose candidate using only earlier development-OOS seasons;
2. candidate tie-break: lower logloss → lower Brier → higher accuracy → frozen feature/model order;
3. choose alpha using only that selected candidate's earlier development-OOS predictions;
4. alpha tie-break: lower logloss → lower Brier → higher accuracy → lower alpha;
5. evaluate selected candidate+alpha once on the outer season.

After all outer folds, choose one final development recipe using all six completed development-OOS seasons. This final aggregate is development evidence only, not an untouched validation result.

## Frozen gate

PASS requires **all** conditions:

1. Concatenated outer hybrid strictly beats market on accuracy, logloss and Brier.
2. Hybrid beats market on accuracy in at least `3/4` outer seasons.
3. Hybrid beats market on logloss in at least `3/4` outer seasons.
4. Hybrid beats market on Brier in at least `3/4` outer seasons.
5. Hybrid strictly beats market on all three simultaneously in at least `3/4` outer seasons.
6. The final recipe selected across all development OOS seasons strictly beats market on all three aggregate development metrics.

A tie is not a win.

PASS status is only:

`ELIGIBLE_FOR_FUTURE_PROTOCOL_FREEZE`

It does **not** mean `MODEL_READY=true`, `CALIBRATION_READY=true`, or `PROSPECTIVE_AI_READY=true`, and it creates no candidate `.pkl`.

FAIL status is:

`REJECTED_NO_FREEZE_RECOMMENDATION`

A FAIL closes this exact V1 candidate/hybrid family. The gate, alpha grid, folds, excluded season, or candidate family must not be weakened or retuned after observing results.

## Safety requirements

- completed historical data only;
- structural exclusion of `2019-2020` is frozen before results;
- fail closed on missing/invalid required F1 seasons or chronology leakage;
- complete double-round-robin structural validation for every admitted configured season;
- no production `.pkl` writes;
- no candidate model artifact;
- no promotion;
- no paid API;
- no Supabase access;
- no Ligue 1 prospective ledger mutation;
- successful CI must publish only a research JSON proof and prove production artifacts unchanged.
