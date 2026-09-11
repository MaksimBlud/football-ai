# Continuity Addendum — Turkey Super Lig nested historical development V1 result

Date: 2026-09-11
PR: #251 — Preregister and run Turkey Super Lig nested historical development V1
Protocol: `turkey_super_lig_nested_development_v1`

## Final frozen-protocol verdict

`REJECTED_NO_FREEZE_RECOMMENDATION`

The preregistered Turkey Super Lig nested historical development V1 gate did not pass. This exact candidate/hybrid family is closed for the purpose of justifying a future prospective AI protocol. The gate, folds, alpha grid, candidate family, pre-result exclusion of 2022-23 and current-season boundary must not be weakened, retuned or cherry-picked after observing this result.

## Prospective collection state

The separate prospective protocol `TURKEY_SUPER_LIG_MARKET_ONLY_V1` was merged first in PR #250 and post-merge proven on `main`.

- `CAPTURE_READY=true`
- committed count: `0/100`
- no retrospective backfill
- no paid The Odds API request was triggered or scheduled by the capture work
- `MODEL_READY=false`
- `PROSPECTIVE_AI_READY=false`

Future MARKET_ONLY observations remain separate from this historical experiment and may never be retrospectively relabeled as prospective AI evidence.

## Frozen historical evidence boundary

- repository-configured Football-Data competition: `T1`;
- configured seasons: `2016-2017` through current `2026-2027`;
- current `2026-2027` was forbidden and was not downloaded/read;
- `2022-2023` was structurally excluded before the first model result because of the earthquake-related withdrawals and administrative fixture handling;
- the excluded `2022-2023` Football-Data source contained `342` rows and was not admitted to modeling;
- every other admitted season through `2025-2026` passed complete double-round-robin validation;
- admitted seasons: `2016-2017` through `2021-2022`, then `2023-2024` through `2025-2026`;
- all admitted history is development-only;
- `untouched_holdout_claimed=false`;
- development OOS seasons: `2020-2021`, `2021-2022`, `2023-2024`, `2024-2025`, `2025-2026`;
- nested outer tests: `2023-2024`, `2024-2025`, `2025-2026`;
- 12 preregistered candidates from the pre-existing feature/model family;
- frozen alpha grid: `0.05` through `0.50` in `0.05` increments;
- no Supabase access, prospective result/settlement read, paid Odds API call, model promotion or production artifact write was used by the runner.

Historical rows admitted to modeling: `3052`.
Trainable rows after warmup/PIT preparation: `2919`.

## Outer aggregate result

Across `998` selected-candidate outer match rows:

- hybrid accuracy: `0.5691382765531062`
- market accuracy: `0.5661322645290581`
- hybrid logloss: `0.9467083370925217`
- market logloss: `0.9457718021604828`
- hybrid Brier: `0.5603154082395855`
- market Brier: `0.5595864861495998`

Hybrid improved accuracy but lost logloss and Brier. Therefore `outer_aggregate_all_three=false`.

Outer season win counts:

- accuracy: `2/3`
- logloss: `1/3`
- Brier: `0/3`
- simultaneous all-three wins: `0/3`

Frozen requirement: at least `2/3` wins for each metric and at least `2/3` simultaneous all-three wins.

## Outer folds

### 2023-2024

- selected candidate: `core_elo::logistic_l2`
- selected alpha: `0.20`
- matches: `364`
- accuracy: hybrid `0.5576923076923077` vs market `0.5521978021978022` — win
- logloss: hybrid `0.9520511842371016` vs market `0.9499548927544096` — loss
- Brier: hybrid `0.5635540944618831` vs market `0.5620514055146418` — loss
- all-three win: false

### 2024-2025

- selected candidate: `core_elo::logistic_l2`
- selected alpha: `0.05`
- matches: `333`
- accuracy: hybrid `0.6066066066066066` vs market `0.6096096096096096` — loss
- logloss: hybrid `0.9206493945317099` vs market `0.9200277564508462` — loss
- Brier: hybrid `0.5397921526226342` vs market `0.5392919526643979` — loss
- all-three win: false

### 2025-2026

- selected candidate: `core_elo::logistic_l2`
- selected alpha: `0.05`
- matches: `301`
- accuracy: hybrid `0.5415282392026578` vs market `0.5348837209302325` — win
- logloss: hybrid `0.9690765480962531` vs market `0.9691941352007479` — win
- Brier: hybrid `0.5791039874273874` vs market `0.57905774529145` — loss
- all-three win: false

## Final development recipe

Selection over all five clean development OOS seasons chose:

- candidate: `core_elo::logistic_l2`
- alpha: `0.05`

Final development aggregate:

- hybrid accuracy: `0.5367647058823529`
- market accuracy: `0.5356334841628959`
- hybrid logloss: `0.9761062145517859`
- market logloss: `0.9760651271138038`
- hybrid Brier: `0.5805072453297118`
- market Brier: `0.5804180480536013`

Only accuracy improved. Logloss and Brier lost, therefore `final_development_recipe_all_three=false`.

## Frozen gate result

- `outer_aggregate_all_three=false`
- `outer_accuracy_wins_at_least_2_of_3=true`
- `outer_logloss_wins_at_least_2_of_3=false`
- `outer_brier_wins_at_least_2_of_3=false`
- `outer_all_three_wins_at_least_2_of_3=false`
- `final_development_recipe_all_three=false`

Overall PASS requires every condition, therefore V1 is rejected.

## Safety and reproducibility proof

First frozen historical CI run: `34559120816`.
Research artifact:

- artifact ID: `10183680764`
- ZIP SHA256: `d52cfc8d3b6e252cff7fc386edf04e4744e93534773e7ab2bc1b755e002adaa6`

The first historical calculation completed successfully on the preregistered implementation. A separate regression-test failure in the parallel contract job was limited to an over-specific assertion that mathematically equivalent alpha blends must select exactly `0.05`; floating-point scoring selected another grid member. The scientific selection implementation was not changed after the result. Only the regression assertion was corrected to verify membership in the frozen alpha grid and numerical equivalence.

Production state was identical before and after the historical run. In particular:

`football_model_xgboost_elo.pkl = 1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`

`production_unchanged=true`
`artifact_created=false`
`model_ready=false`
`prospective_ai_ready=false`

## Turkey Super Lig state after V1

- prospective MARKET_ONLY collection: `CAPTURE_READY=true`, currently `0/100`;
- exact `turkey_super_lig_nested_development_v1` family: CLOSED / REJECTED;
- `MODEL_READY=false`;
- `PROSPECTIVE_AI_READY=false`;
- no candidate `.pkl` created;
- no production promotion;
- do not rerun/tune/weaken/cherry-pick exact V1;
- any future Turkish AI attempt requires a genuinely new preregistered hypothesis with a defensible evidence boundary.
