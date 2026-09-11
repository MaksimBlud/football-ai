# Continuity Addendum — Eredivisie nested historical development V1 result

Date: 2026-09-11
PR: #249 — Preregister and run Eredivisie nested historical development V1
Branch: `research/eredivisie-nested-development-v1`
Protocol: `eredivisie_nested_development_v1`

## Final frozen-protocol verdict

`REJECTED_NO_FREEZE_RECOMMENDATION`

The preregistered Eredivisie nested historical development V1 gate did **not** pass. This exact candidate/hybrid family is closed for the purpose of justifying a future prospective AI protocol. The gate, folds, alpha grid, candidate family, pre-result structural exclusion of 2019-20, and the current-season boundary must not be weakened, retuned or cherry-picked after observing these results.

## Existing prospective collection state

Before the AI protocol was frozen, a read-only live Supabase audit confirmed:

- durable Eredivisie observations: `391`;
- canonical prediction-ledger rows: `391`;
- MARKET_ONLY observations/predictions: `391/391`;
- Structural V2 applied rows: `0`;
- all observation snapshot timestamps strictly before kickoff: true;
- all ledger snapshot timestamps strictly before kickoff: true;
- all prediction timestamps strictly before kickoff: true;
- unlinked ledger rows: `0`;
- distinct prediction keys: `391/391`.

Therefore Eredivisie was already collection-ready before this AI-readiness experiment. These prospective rows remain immutable MARKET_ONLY evidence and were not read or used by the historical runner.

## Historical evidence boundary

- repository-configured Football-Data Eredivisie `N1` seasons: `2016-2017` through current `2026-2027`;
- current `2026-2027` was explicitly forbidden and not downloaded/read by the historical runner;
- `2019-2020` was structurally excluded **before any model result** because the season was terminated early;
- the N1 source verified the excluded 2019-20 season as an incomplete 18-team source with `232` played matches;
- every other configured season through `2025-2026` was admitted only after complete double-round-robin validation;
- all admitted historical data was treated as **development-only**;
- `untouched_holdout_claimed=false`;
- admitted historical seasons: `2016-2017`, `2017-2018`, `2018-2019`, `2020-2021` through `2025-2026`;
- chronological development OOS seasons: `2020-2021` through `2025-2026`;
- outer test seasons: `2022-2023`, `2023-2024`, `2024-2025`, `2025-2026`;
- 12 preregistered candidates from the pre-existing feature/model family;
- frozen alpha grid: `0.05` through `0.50` in `0.05` increments;
- no live database access, current/prospective outcomes, paid Odds API calls, model promotion or production artifact writes were used by this runner.

## Observed aggregate result

Outer aggregate across 1,209 selected-candidate match rows:

- hybrid accuracy: `0.554177005789909`
- market accuracy: `0.5566583953680728`
- hybrid logloss: `0.9400719103432634`
- market logloss: `0.940211529452053`
- hybrid Brier: `0.5572137375893917`
- market Brier: `0.5572485889004546`

Hybrid improved logloss and Brier slightly, but lost accuracy. Because the preregistered aggregate condition requires strict wins on **all three**, `outer_aggregate_all_three=false`.

Outer season win counts:

- accuracy: `0/4`
- logloss: `2/4`
- Brier: `2/4`
- simultaneous all-three wins: `0/4`

The preregistered requirement was at least `3/4` for each metric and at least `3/4` simultaneous all-three wins.

## Outer folds

### 2022-2023

- selected candidate: `full_no_odds::xgb_shallow`
- selected alpha: `0.05`
- matches: `301`
- accuracy: hybrid `0.5647840531561462` vs market `0.5681063122923588` — loss
- logloss: hybrid `0.9299808173017047` vs market `0.9295559482391965` — loss
- Brier: hybrid `0.551244500561618` vs market `0.5509447631206004` — loss
- all-three win: false

### 2023-2024

- selected candidate: `core_elo::logistic_l2`
- selected alpha: `0.05`
- matches: `301`
- accuracy: hybrid `0.5780730897009967` vs market `0.5780730897009967` — tie, therefore not a win
- logloss: hybrid `0.9095572135176498` vs market `0.9105330084056534` — win
- Brier: hybrid `0.5368967531667491` vs market `0.5374237263488565` — win
- all-three win: false

### 2024-2025

- selected candidate: `core_elo::logistic_l2`
- selected alpha: `0.05`
- matches: `306`
- accuracy: hybrid `0.5392156862745098` vs market `0.5424836601307189` — loss
- logloss: hybrid `0.94979378940494` vs market `0.9493624012485933` — loss
- Brier: hybrid `0.563916913094732` vs market `0.5636277379145148` — loss
- all-three win: false

### 2025-2026

- selected candidate: `core_elo::logistic_l2`
- selected alpha: `0.05`
- matches: `301`
- accuracy: hybrid `0.5348837209302325` vs market `0.5382059800664452` — loss
- logloss: hybrid `0.97079432814109` vs market `0.9712427520776168` — win
- Brier: hybrid `0.5766854351041463` vs market `0.5768921622873805` — win
- all-three win: false

## Final development recipe

Selection over all six development OOS seasons chose:

- candidate: `core_elo::logistic_l2`
- alpha: `0.05`

Final development aggregate:

- hybrid accuracy: `0.5552486187845304`
- market accuracy: `0.5569060773480663`
- hybrid logloss: `0.9402917940987324`
- market logloss: `0.940301750427855`
- hybrid Brier: `0.5569598783357825`
- market Brier: `0.556902664138635`

Only logloss improved. Accuracy and Brier lost, therefore `final_development_recipe_all_three=false`.

## Frozen gate result

- `outer_aggregate_all_three=false`
- `outer_accuracy_wins_at_least_3_of_4=false`
- `outer_logloss_wins_at_least_3_of_4=false`
- `outer_brier_wins_at_least_3_of_4=false`
- `outer_all_three_wins_at_least_3_of_4=false`
- `final_development_recipe_all_three=false`

Overall PASS requires every condition, therefore V1 is rejected.

## Safety proof

Successful first frozen CI research artifact:

- artifact ID: `10183237793`
- ZIP SHA256: `de1d24f025cbb89be186f8c55caf63d33885fe2ff86eef6583eb84599a3a05fe`

Historical rows admitted to modeling: `2754`
Structurally excluded 2019-20 source rows: `232`
Trainable rows after warmup/PIT preparation: `2660`

Production state was identical before and after the run. In particular:

`football_model_xgboost_elo.pkl = 1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`

`production_unchanged=true`

No candidate `.pkl` artifact was created: `artifact_created=false`.

## Eredivisie state after V1

- existing prospective MARKET_ONLY collection is `CAPTURE_READY=true` / operational;
- live read-only audit found 391 durable observations and 391 canonical MARKET_ONLY prediction rows;
- `MODEL_READY=false`;
- `PROSPECTIVE_AI_READY=false`;
- exact `eredivisie_nested_development_v1` family is closed/rejected;
- existing prospective MARKET_ONLY rows must never receive retrospective AI predictions or be relabeled as AI evidence.

A future Eredivisie AI attempt requires a genuinely new preregistered hypothesis with a defensible new evidence boundary. Do not retune V1 after observing this result.

## Next safe project step

Preserve the existing Eredivisie MARKET_ONLY live collection. After merge/post-merge proof, move to the next independent league/readiness block rather than tuning Eredivisie V1.