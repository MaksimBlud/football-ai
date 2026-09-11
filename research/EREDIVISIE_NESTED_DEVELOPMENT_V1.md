# Eredivisie Nested Historical Development V1

Status: FROZEN BEFORE FIRST RESULT
Date frozen: 2026-09-11
League: `EREDIVISIE`
Protocol: `eredivisie_nested_development_v1`

## Purpose

Evaluate whether already-completed Eredivisie history supports freezing a future Eredivisie-specific AI prospective protocol. This is development research only. It cannot create or promote a production model and it cannot reinterpret, overwrite, or augment the already-existing prospective MARKET_ONLY observations or canonical prediction ledger.

## Existing prospective collection boundary

Eredivisie already has an operational MARKET_ONLY prospective loop. A read-only live audit performed before this AI protocol was frozen showed 391 durable Eredivisie observations and 391 canonical prediction-ledger rows; every row was MARKET_ONLY, every snapshot/prediction timestamp was before kickoff, Structural V2 had been applied to zero rows, all ledger rows were linked to observations, and all prediction keys were unique. Those prospective rows are excluded from this historical development protocol and can never be retrospectively relabeled as AI evidence.

## Historical evidence boundary

- Historical provider: repository-configured Football-Data Eredivisie `N1`.
- Runtime configuration contains seasons `2016-2017` through current `2026-2027`.
- `2026-2027` is current/prospective and is strictly forbidden to this historical-development runner; the runner must not download or inspect it.
- `2019-2020` is structurally excluded **before any model result is observed** because the Eredivisie season was officially terminated early and was not completed. It is not used for training, model selection, alpha selection, or evaluation.
- The runner may read the completed 2019-20 Football-Data source only to verify that it is an 18-team incomplete season, has valid played-match identities/results, contains fewer than the complete 306-match double round-robin, and fails the complete-double-round-robin validator. The exact observed row count is descriptive only and is not a tuning decision.
- Every other configured season through `2025-2026` must pass complete double-round-robin validation or the run fails closed.
- Every admitted historical season is **development-only**. No season is claimed untouched.
- Any historical data later than `2025-2026` is forbidden.
- No current/prospective score, result, outcome, settlement, or finished-result table may be read.
- No Supabase access is required or permitted by the runner.
- No paid Odds API request is permitted.
- Existing Eredivisie MARKET_ONLY prospective rows are excluded from model development and remain immutable market-only evidence.
- Previously rejected La Liga, Serie A, Bundesliga and Ligue 1 AI families remain closed and are not executed by this protocol.

Admitted historical seasons:
- `2016-2017`
- `2017-2018`
- `2018-2019`
- `2020-2021`
- `2021-2022`
- `2022-2023`
- `2023-2024`
- `2024-2025`
- `2025-2026`

## Frozen candidate family

Use only the already-existing `league_model_sweep.py` family that predates this Eredivisie result.

Feature sets:
- `core`
- `core_elo`
- `full_no_odds`

Model variants:
- `logistic_l2`
- `xgb_shallow`
- `xgb_base`
- `xgb_regularized`

Bookmaker 1X2 prices are benchmark-only and are never model features.

Hybrid alpha grid is frozen at:

`0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50`

Hybrid probabilities:

`alpha * AI + (1 - alpha) * MARKET`

Probability vectors are numerically renormalized to the simplex before scoring solely to remove floating-point roundoff. This does not change the scientific gate, candidate family, folds, or evidence boundary.

## Chronological development protocol

Development OOS seasons:
- `2020-2021`
- `2021-2022`
- `2022-2023`
- `2023-2024`
- `2024-2025`
- `2025-2026`

For every OOS season, models train only on strictly earlier **admitted** seasons. Because `2019-2020` is structurally excluded, it is absent from every training fold.

Outer test seasons:
- `2022-2023`
- `2023-2024`
- `2024-2025`
- `2025-2026`

For each outer season:
1. choose the candidate using only earlier development-OOS seasons;
2. candidate tie-break: lower logloss → lower Brier → higher accuracy → frozen feature/model order;
3. choose alpha using only that candidate's earlier development-OOS predictions;
4. alpha tie-break: lower logloss → lower Brier → higher accuracy → lower alpha;
5. evaluate selected candidate + alpha once on the outer season.

After all outer folds, choose one final development recipe using all six completed development-OOS seasons. This final aggregate remains development evidence, not an untouched validation result.

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

A FAIL closes this exact V1 candidate/hybrid family. The gate, alpha grid, folds, excluded season, or candidate family must not be weakened, retuned, or cherry-picked after observing results.

## Safety requirements

- completed historical data only;
- 2019-20 structural exclusion frozen before result;
- current 2026-27 source must not be downloaded/read;
- fail closed on missing/invalid admitted N1 seasons or chronology leakage;
- complete double-round-robin validation for every admitted season;
- no production `.pkl` writes;
- no candidate model artifact;
- no promotion;
- no paid API;
- no Supabase access;
- no Eredivisie prospective observation or prediction-ledger mutation;
- successful CI must publish only a research JSON proof and prove production artifacts unchanged.