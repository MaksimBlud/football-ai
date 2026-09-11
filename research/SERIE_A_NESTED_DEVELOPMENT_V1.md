# Serie A Nested Historical Development V1

Status: FROZEN BEFORE FIRST RESULT
Date frozen: 2026-09-11
League: `SERIE_A`
Protocol: `serie_a_nested_development_v1`

## Purpose

Evaluate whether the already-completed Serie A historical record supports freezing a future league-specific AI prospective protocol. This is development research only. It does not create or promote a model, does not make Serie A prospective-AI-ready by itself, and cannot alter any already-recorded prospective `MARKET_ONLY` observation.

## Evidence boundary

- Historical source: the repository-configured public Football-Data Serie A (`I1`) seasons `2016-2017` through `2025-2026`.
- Every available completed historical season in this protocol is treated as **development evidence**. No season is described as untouched.
- Data later than `2025-2026` is forbidden and must fail closed.
- No current/prospective fixture result, score, settlement, or future-season outcome is read.
- No Supabase access is required.
- No paid Odds API request is permitted.
- La Liga is excluded from execution and its closed/rejected protocols remain closed.
- As in the pre-existing sweep family, fold metrics use only rows with the selected candidate features, target, and complete B365 1X2 benchmark prices. Individual historical rows with unavailable B365 prices are excluded from that fold rather than causing the whole season to be redefined or imputed.

## Frozen candidate family

The candidate family is inherited unchanged from the pre-existing `league_model_sweep.py` research family:

Feature sets:
- `core`
- `core_elo`
- `full_no_odds`

Model variants:
- `logistic_l2`
- `xgb_shallow`
- `xgb_base`
- `xgb_regularized`

Bookmaker 1X2 prices are benchmark-only and are not model input features.

Hybrid alpha grid is frozen at:

`0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50`

Hybrid probabilities use:

`alpha * AI + (1 - alpha) * MARKET`

## Chronological development protocol

Development OOS seasons:
- `2020-2021`
- `2021-2022`
- `2022-2023`
- `2023-2024`
- `2024-2025`
- `2025-2026`

For every OOS season, the candidate model is trained only on strictly earlier seasons.

Outer test seasons:
- `2022-2023`
- `2023-2024`
- `2024-2025`
- `2025-2026`

For each outer test season:
1. Candidate model/feature-set selection uses only earlier development-OOS seasons.
2. Candidate selection order is lower log loss, then lower Brier, then higher accuracy, then the fixed feature/model order above.
3. Alpha selection uses only the selected candidate's earlier OOS predictions.
4. Alpha selection order is lower log loss, then lower Brier, then higher accuracy, then lower alpha.
5. The selected recipe is evaluated once on that outer season.

After all outer folds, a final recipe is selected using all six development-OOS seasons. That final-development result is diagnostic evidence for whether a future protocol may be frozen; it is not a new untouched holdout.

## Fixed pass gate

V1 passes only if **all** conditions hold:

1. Concatenated outer hybrid predictions strictly beat market on all three metrics: higher accuracy, lower log loss, lower Brier.
2. Hybrid beats market on accuracy in at least `3/4` outer seasons.
3. Hybrid beats market on log loss in at least `3/4` outer seasons.
4. Hybrid beats market on Brier in at least `3/4` outer seasons.
5. Hybrid beats market on all three metrics simultaneously in at least `3/4` outer seasons.
6. The final recipe selected from all development-OOS predictions beats market on all three aggregate development metrics.

No metric may be removed, softened, substituted, or reweighted after results are observed.

## Outcomes

PASS:
- status `ELIGIBLE_FOR_FUTURE_PROTOCOL_FREEZE`
- permits only a separate future PR to freeze a prospective Serie A AI protocol
- does **not** set `MODEL_READY=true`
- does **not** set `PROSPECTIVE_AI_READY=true`
- creates no production or candidate `.pkl`

FAIL:
- status `REJECTED_NO_FREEZE_RECOMMENDATION`
- closes this exact V1 family
- no post-result alpha/feature/model/gate tuning is allowed under V1
- Serie A remains prospectively `MARKET_ONLY` under the already-frozen capture protocol

## Production and prospective safety

- Production `.pkl` files must remain byte-identical.
- No model/calibrator artifact is created.
- No automatic or manual production promotion occurs.
- The existing Serie A prospective row already recorded under `NON_EPL_MARKET_ONLY_V1` is immutable MARKET_ONLY evidence and can never be retrospectively converted into AI evidence.
