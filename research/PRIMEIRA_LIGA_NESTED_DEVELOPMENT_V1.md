# Primeira Liga Nested Historical Development V1

Date frozen: 2026-09-11
Protocol: `primeira_liga_nested_development_v1`
League: `PRIMEIRA_LIGA`

## Purpose

Test whether the pre-existing football-only candidate family, blended with the market by a frozen alpha grid, is robust enough to justify a future Primeira Liga prospective AI protocol. This is historical development research only; it cannot make the league AI-ready by itself.

## Evidence boundary

- source: public Football-Data `P1` CSVs only;
- configured seasons: `2016-2017` through current `2026-2027`;
- current `2026-2027` is forbidden and must not be downloaded/read;
- admitted seasons are `2016-2017` through `2025-2026`, but every admitted source must first pass strict complete double-round-robin validation;
- any missing, malformed or structurally incomplete admitted season fails closed; no post-result exclusion is permitted;
- all admitted historical data is development-only;
- no untouched historical holdout is claimed;
- Primeira prospective MARKET_ONLY ledger is not read or mutated;
- no Supabase access, paid Odds API request, model promotion or production model write is permitted.

## Frozen candidate family

Only the already existing family may be used:

Feature sets:
- `core`
- `core_elo`
- `full_no_odds`

Models:
- `logistic_l2`
- `xgb_shallow`
- `xgb_base`
- `xgb_regularized`

Total candidates: `12`.

Bookmaker 1X2 odds are benchmark/blending inputs only and are never model features.

## Frozen OOS structure

Development OOS seasons:
- `2020-2021`
- `2021-2022`
- `2022-2023`
- `2023-2024`
- `2024-2025`
- `2025-2026`

Nested outer test seasons:
- `2022-2023`
- `2023-2024`
- `2024-2025`
- `2025-2026`

Each outer fold selects candidate and alpha using only earlier OOS seasons. The first outer fold therefore has two earlier OOS seasons.

Candidate selection ordering is frozen as lowest logloss, then lowest Brier, then highest accuracy, then fixed feature/model order.

## Frozen market blend

`hybrid = (1 - alpha) * market + alpha * AI`

Alpha grid is frozen to:
`0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50`.

Probability vectors are renormalized to the simplex before scoring. Alpha selection ordering is lowest logloss, then lowest Brier, then highest accuracy, then lower alpha.

## Frozen acceptance gate

Strict PASS requires **all** of the following:

1. concatenated outer hybrid strictly beats the market on accuracy, logloss and Brier;
2. hybrid wins accuracy in at least `3/4` outer seasons;
3. hybrid wins logloss in at least `3/4` outer seasons;
4. hybrid wins Brier in at least `3/4` outer seasons;
5. hybrid wins all three metrics simultaneously in at least `3/4` outer seasons;
6. the final-development recipe selected across all six OOS seasons strictly beats the market on all three metrics.

Ties are not wins.

PASS status is only `ELIGIBLE_FOR_FUTURE_PROTOCOL_FREEZE`. It does **not** mean `MODEL_READY`, `CALIBRATION_READY` or `PROSPECTIVE_AI_READY`.

FAIL status is `REJECTED_NO_FREEZE_RECOMMENDATION` and closes this exact V1 candidate/blend family. After the first result, the gate, folds, candidate family, alpha grid and evidence boundary must not be weakened, retuned or cherry-picked.
