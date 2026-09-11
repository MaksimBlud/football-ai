# Continuity Addendum — Primeira Liga nested historical development V1 result

Date: 2026-09-11
PR: #253 — Preregister and run Primeira Liga nested historical development V1
Protocol: `primeira_liga_nested_development_v1`

## Final frozen-protocol verdict

`REJECTED_NO_FREEZE_RECOMMENDATION`

The preregistered Primeira Liga nested historical development V1 gate did not pass. This exact candidate/hybrid family is closed for the purpose of justifying a future prospective AI protocol. The evidence boundary, folds, candidate family, alpha grid and strict gate must not be weakened, retuned or cherry-picked after observing this result.

## Prospective collection state

The separate prospective protocol `PRIMEIRA_LIGA_MARKET_ONLY_V1` was merged first in PR #252 and post-merge proven on `main`.

- `CAPTURE_READY=true`
- committed count: `0/100`
- no retrospective backfill
- no paid The Odds API request was triggered or scheduled by the capture work
- `MODEL_READY=false`
- `PROSPECTIVE_AI_READY=false`

Future MARKET_ONLY observations remain separate from this historical experiment and may never be retrospectively relabeled as prospective AI evidence.

## Frozen historical evidence boundary

- repository-configured Football-Data competition: `P1`;
- configured seasons: `2016-2017` through current `2026-2027`;
- current `2026-2027` was forbidden and was not downloaded/read;
- admitted completed seasons: `2016-2017` through `2025-2026`;
- every admitted season passed strict complete double-round-robin validation;
- no season was structurally excluded after preregistration;
- all admitted history is development-only;
- `untouched_holdout_claimed=false`;
- development OOS seasons: `2020-2021` through `2025-2026`;
- nested outer tests: `2022-2023`, `2023-2024`, `2024-2025`, `2025-2026`;
- 12 preregistered candidates from the pre-existing feature/model family;
- frozen alpha grid: `0.05` through `0.50` in `0.05` increments;
- no Supabase access, prospective result/settlement read, paid Odds API call, model promotion or production artifact write was used by the runner.

Historical rows admitted to modeling: `3060`.
Trainable rows after warmup/PIT preparation: `2960`.

## Outer aggregate result

Across `1203` selected-candidate outer match rows:

- hybrid accuracy: `0.5793848711554447`
- market accuracy: `0.5818786367414797`
- hybrid logloss: `0.9102162151515959`
- market logloss: `0.9097212873819859`
- hybrid Brier: `0.5346202927094035`
- market Brier: `0.5342769781090395`

Hybrid lost all three aggregate metrics, therefore `outer_aggregate_all_three=false`.

Outer season win counts:

- accuracy: `1/4`
- logloss: `2/4`
- Brier: `2/4`
- simultaneous all-three wins: `1/4`

Frozen requirement: at least `3/4` wins for each metric and at least `3/4` simultaneous all-three wins.

## Outer folds

### 2022-2023

- selected candidate: `full_no_odds::xgb_shallow`
- selected alpha: `0.15`
- matches: `300`
- accuracy: hybrid `0.6333333333333333` vs market `0.6333333333333333` — tie, not a win
- logloss: hybrid `0.873955268927781` vs market `0.8742907084290715` — win
- Brier: hybrid `0.5064384153023136` vs market `0.5066165954435374` — win
- all-three win: false

### 2023-2024

- selected candidate: `core_elo::xgb_shallow`
- selected alpha: `0.20`
- matches: `301`
- accuracy: hybrid `0.5714285714285714` vs market `0.5780730897009967` — loss
- logloss: hybrid `0.9181783755648802` vs market `0.914865478908978` — loss
- Brier: hybrid `0.5389008576454849` vs market `0.5366655905851244` — loss
- all-three win: false

### 2024-2025

- selected candidate: `core_elo::logistic_l2`
- selected alpha: `0.15`
- matches: `301`
- accuracy: hybrid `0.5448504983388704` vs market `0.5548172757475083` — loss
- logloss: hybrid `0.9337621957428575` vs market `0.9332432156456776` — loss
- Brier: hybrid `0.5523328157050498` vs market `0.5520123677250097` — loss
- all-three win: false

### 2025-2026

- selected candidate: `core_elo::xgb_shallow`
- selected alpha: `0.15`
- matches: `301`
- accuracy: hybrid `0.5681063122923588` vs market `0.5614617940199336` — win
- logloss: hybrid `0.9148485521109851` vs market `0.9163680369795887` — win
- Brier: hybrid `0.5407154546850745` vs market `0.5417214637234645` — win
- all-three win: true

## Final development recipe

Selection over all six development OOS seasons chose:

- candidate: `full_no_odds::xgb_shallow`
- alpha: `0.15`

Final development aggregate:

- hybrid accuracy: `0.5637472283813747`
- market accuracy: `0.5665188470066519`
- hybrid logloss: `0.9184141399496597`
- market logloss: `0.9190034290467597`
- hybrid Brier: `0.5407208262208815`
- market Brier: `0.5411170805830284`

Logloss and Brier improved, but accuracy lost, therefore `final_development_recipe_all_three=false`.

## Frozen gate result

- `outer_aggregate_all_three=false`
- `outer_accuracy_wins_at_least_3_of_4=false`
- `outer_logloss_wins_at_least_3_of_4=false`
- `outer_brier_wins_at_least_3_of_4=false`
- `outer_all_three_wins_at_least_3_of_4=false`
- `final_development_recipe_all_three=false`

Overall PASS requires every condition, therefore V1 is rejected.

## Safety and reproducibility proof

First frozen historical CI run: `34560090228`.
Research artifact:

- artifact ID: `10184008756`
- ZIP SHA256: `3736a475bc3ba828185eaed6e7fe6c9af36d18a1b94652b6d36e04da22a80294`

Production state was identical before and after the historical run. In particular:

`football_model_xgboost_elo.pkl = 1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`

`production_unchanged=true`
`artifact_created=false`
`model_ready=false`
`prospective_ai_ready=false`

## Primeira Liga state after V1

- prospective MARKET_ONLY collection: `CAPTURE_READY=true`, currently `0/100`;
- exact `primeira_liga_nested_development_v1` family: CLOSED / REJECTED;
- `MODEL_READY=false`;
- `PROSPECTIVE_AI_READY=false`;
- no candidate `.pkl` created;
- no production promotion;
- do not rerun/tune/weaken/cherry-pick exact V1;
- any future Portuguese AI attempt requires a genuinely new preregistered hypothesis with a defensible evidence boundary.
