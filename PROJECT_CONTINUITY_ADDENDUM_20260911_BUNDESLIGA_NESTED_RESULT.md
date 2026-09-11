# Continuity Addendum — Bundesliga nested historical development V1 result

Date: 2026-09-11
PR: #246 — Preregister and run Bundesliga nested historical development V1
Branch: `research/bundesliga-nested-development-v1`
Protocol: `bundesliga_nested_development_v1`

## Final frozen-protocol verdict

`REJECTED_NO_FREEZE_RECOMMENDATION`

The preregistered Bundesliga nested historical development V1 gate did **not** pass. This exact candidate/hybrid family is closed for the purpose of justifying a future prospective AI protocol. The gate, folds, alpha grid and candidate family must not be weakened, retuned or cherry-picked after observing these results.

## Evidence boundary

- all completed Bundesliga history through `2025-2026` was treated as **development-only**;
- `untouched_holdout_claimed=false`;
- historical seasons used: `2016-2017` through `2025-2026`;
- chronological development OOS seasons: `2020-2021` through `2025-2026`;
- outer test seasons: `2022-2023`, `2023-2024`, `2024-2025`, `2025-2026`;
- 12 preregistered candidates were evaluated from the pre-existing feature/model family;
- frozen alpha grid: `0.05` through `0.50` in `0.05` increments;
- probability rows were numerically renormalized to the simplex before scoring to eliminate float roundoff only; scientific criteria were unchanged;
- no prospective outcomes, live database reads, paid Odds API calls, model promotion or production artifact writes were used by the protocol;
- the existing Bundesliga `BUNDESLIGA_MARKET_ONLY_V1` observation was not modified.

## Observed aggregate result

Outer aggregate across 1,209 selected-candidate match rows:

- hybrid accuracy: `0.5318444995864351`
- market accuracy: `0.533498759305211`
- hybrid logloss: `0.9721518956247652`
- market logloss: `0.9711402729148371`
- hybrid Brier: `0.5776571651371644`
- market Brier: `0.5770129664807924`

The outer aggregate hybrid was worse than market on all three required metrics.

Outer season win counts:

- accuracy: `1/4`
- logloss: `1/4`
- Brier: `1/4`
- simultaneous all-three wins: `0/4`

The preregistered requirement was at least `3/4` for each metric and at least `3/4` simultaneous all-three wins. All corresponding outer robustness conditions are false.

## Outer folds

### 2022-2023

- selected candidate: `full_no_odds::logistic_l2`
- selected alpha: `0.30`
- matches: `306`
- accuracy: hybrid `0.5294117647058824` vs market `0.5326797385620915` — loss
- logloss: hybrid `0.9940161506136219` vs market `0.9966179592135102` — win
- Brier: hybrid `0.5930885732679055` vs market `0.5947783787223133` — win
- all-three win: false

### 2023-2024

- selected candidate: `full_no_odds::logistic_l2`
- selected alpha: `0.30`
- matches: `301`
- accuracy: hybrid `0.5282392026578073` vs market `0.5382059800664452` — loss
- logloss: hybrid `0.9516659470337178` vs market `0.9470595097486042` — loss
- Brier: hybrid `0.563667503700385` vs market `0.5600693571616203` — loss
- all-three win: false

### 2024-2025

- selected candidate: `full_no_odds::logistic_l2`
- selected alpha: `0.20`
- matches: `296`
- accuracy: hybrid `0.5101351351351351` vs market `0.5135135135135135` — loss
- logloss: hybrid `0.990800954678907` vs market `0.9897243114085231` — loss
- Brier: hybrid `0.5913680423391685` vs market `0.591247506787197` — loss
- all-three win: false

### 2025-2026

- selected candidate: `full_no_odds::logistic_l2`
- selected alpha: `0.15`
- matches: `306`
- accuracy: hybrid `0.5588235294117647` vs market `0.5490196078431373` — win
- logloss: hybrid `0.9523992388250562` vs market `0.9513731562857881` — loss
- Brier: hybrid `0.5627240198844535` vs market `0.5621449479463795` — loss
- all-three win: false

## Final development recipe

Selection over all six development OOS seasons chose:

- candidate: `full_no_odds::logistic_l2`
- alpha: `0.15`

Final development aggregate:

- hybrid accuracy: `0.526578073089701`
- market accuracy: `0.5249169435215947`
- hybrid logloss: `0.9785095218018424`
- market logloss: `0.9789475788887106`
- hybrid Brier: `0.5817461529560743`
- market Brier: `0.5819194906912054`

This final development recipe strictly improved all three aggregate metrics, so `final_development_recipe_all_three=true`. However, this is development evidence only and cannot override the failed nested outer robustness gate. It must not be cherry-picked into a prospective AI claim.

## Frozen gate result

- `outer_aggregate_all_three=false`
- `outer_accuracy_wins_at_least_3_of_4=false`
- `outer_logloss_wins_at_least_3_of_4=false`
- `outer_brier_wins_at_least_3_of_4=false`
- `outer_all_three_wins_at_least_3_of_4=false`
- `final_development_recipe_all_three=true`

Overall PASS requires every condition, therefore V1 is rejected.

## Safety proof

Successful CI research artifact digest:

`sha256:60faf95131d6e0e3718fe0cf744d0ea60442d61ee76073fcbc25832a8727d552`

Historical rows: `3060`
Trainable rows after warmup/PIT preparation: `2955`

Production state was identical before and after the run. In particular:

`football_model_xgboost_elo.pkl = 1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`

`production_unchanged=true`

No candidate `.pkl` artifact was created: `artifact_created=false`.

## Bundesliga state after V1

- `CAPTURE_READY=true` under `BUNDESLIGA_MARKET_ONLY_V1`;
- prospective MARKET_ONLY count remains `1/100`;
- `MODEL_READY=false`;
- `PROSPECTIVE_AI_READY=false`;
- the existing MARKET_ONLY observation remains immutable and must never receive a retrospective AI prediction or be relabeled as AI evidence;
- exact `bundesliga_nested_development_v1` family is closed/rejected.

A future Bundesliga AI attempt requires a genuinely new preregistered hypothesis with a defensible evidence boundary. The observed 2016-17 through 2025-26 development results cannot be reused as an untouched validation set, and the V1 gate cannot be relaxed.

## Next safe project step

Do not tune Bundesliga V1 after this rejection. Preserve Bundesliga prospective MARKET_ONLY collection and move to the next independent league/readiness block or a genuinely new preregistered Bundesliga hypothesis whose evidence boundary is scientifically defensible.
