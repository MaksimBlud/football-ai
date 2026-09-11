# Turkey Super Lig Nested Historical Development V1

Date frozen: 2026-09-11
Protocol: `turkey_super_lig_nested_development_v1`
League: `TURKEY_SUPER_LIG`

## Scientific purpose

Test one already-existing football-only candidate family against the bookmaker 1X2 market using chronological nested historical development. This protocol may justify only a future prospective protocol freeze. It cannot itself make a Turkish model production-ready or retrospectively attach AI predictions to MARKET_ONLY evidence.

## Evidence boundary frozen before first model result

Historical source: repository-configured Football-Data `T1` seasons.

- current `2026-2027` is forbidden and must not be downloaded/read by this runner;
- `2022-2023` is structurally excluded before any model result;
- all other configured seasons from `2016-2017` through `2025-2026` must pass complete double-round-robin validation before admission;
- every admitted historical row is development-only;
- no untouched historical holdout is claimed;
- existing prospective `TURKEY_SUPER_LIG_MARKET_ONLY_V1` rows are excluded and immutable;
- no Supabase access, prospective result/score/outcome/settlement read, or paid Odds API access is permitted.

### Why 2022-2023 is excluded

This is not a post-result statistical choice. Before this protocol was frozen, official Turkish Football Federation material was checked and confirmed that Hatayspor and Gaziantep withdrew from the 2022-23 competition after the February 2023 earthquakes and remaining fixtures were handled administratively, including 3-0 technical results. That violates the ordinary observed-match evidence assumption used by the feature/model family. The whole season is therefore excluded rather than attempting a retrospective match-by-match reconstruction.

## Candidate family frozen before result

Reuse only the feature/model variants already present in `league_model_sweep.py`.

Feature sets:
- `core`
- `core_elo`
- `full_no_odds`

Models:
- `logistic_l2`
- `xgb_shallow`
- `xgb_base`
- `xgb_regularized`

Total candidates: 12.

Bookmaker odds are benchmark-only and are never model features.

Frozen hybrid alpha grid:
`0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50`.

## Chronological development design

Development OOS seasons:
- `2020-2021`
- `2021-2022`
- `2023-2024`
- `2024-2025`
- `2025-2026`

`2022-2023` is intentionally absent because of the frozen structural exclusion.

Nested outer tests begin only after at least two earlier clean OOS seasons exist:
- `2023-2024`
- `2024-2025`
- `2025-2026`

For every outer season, candidate and alpha selection may use only earlier development OOS seasons. The outer season itself is not used for selection.

## Frozen PASS gate

PASS requires **every** condition below:

1. concatenated selected-candidate outer hybrid strictly beats the market on accuracy, logloss and Brier;
2. hybrid strictly beats market accuracy in at least `2/3` outer seasons;
3. hybrid strictly beats market logloss in at least `2/3` outer seasons;
4. hybrid strictly beats market Brier in at least `2/3` outer seasons;
5. hybrid wins all three metrics simultaneously in at least `2/3` outer seasons;
6. the final development recipe selected using all five development OOS seasons strictly beats the market on all three metrics over those same development OOS rows.

Ties are not wins.

PASS status: `ELIGIBLE_FOR_FUTURE_PROTOCOL_FREEZE` only.

PASS does **not** mean:
- `MODEL_READY`
- `CALIBRATION_READY`
- `PROSPECTIVE_AI_READY`
- production promotion

FAIL status: `REJECTED_NO_FREEZE_RECOMMENDATION`.

A FAIL closes this exact V1 candidate/hybrid family. The gate, folds, candidate family, alpha grid, structural exclusion and evidence boundary must not be weakened, retuned or cherry-picked after seeing the result.

## Numerical hygiene

Probability vectors are normalized to the simplex before scoring. This only removes representation/roundoff drift; it does not change the model family, selection criteria, alpha grid or scientific gate.

## Safety

The runner may write research JSON only. It must not create a candidate `.pkl`, modify any production `.pkl`, access Supabase, spend The Odds API credits, read current 2026-27 source data, or mutate the Turkey prospective ledger.