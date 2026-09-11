# Continuity Addendum — Ligue 1 nested historical development V1 result

Date: 2026-09-11
PR: #248 — Preregister and run Ligue 1 nested historical development V1
Branch: `research/ligue1-nested-development-v1`
Protocol: `ligue1_nested_development_v1`

## Final frozen-protocol verdict

`REJECTED_NO_FREEZE_RECOMMENDATION`

The preregistered Ligue 1 nested historical development V1 gate did **not** pass. This exact candidate/hybrid family is closed for the purpose of justifying a future prospective AI protocol. The gate, folds, alpha grid, candidate family and pre-result structural exclusion of 2019-20 must not be weakened, retuned or cherry-picked after observing these results.

## Evidence boundary

- configured Football-Data Ligue 1 `F1` seasons: `2016-2017` through `2025-2026`;
- `2019-2020` was structurally excluded **before any model result** and verified as the curtailed 279-match source season;
- every other configured season through `2025-2026` was admitted only after complete double-round-robin validation;
- all admitted historical data was treated as **development-only**;
- `untouched_holdout_claimed=false`;
- admitted historical seasons: `2016-2017`, `2017-2018`, `2018-2019`, `2020-2021` through `2025-2026`;
- chronological development OOS seasons: `2020-2021` through `2025-2026`;
- outer test seasons: `2022-2023`, `2023-2024`, `2024-2025`, `2025-2026`;
- 12 preregistered candidates from the pre-existing feature/model family;
- frozen alpha grid: `0.05` through `0.50` in `0.05` increments;
- probability vectors were numerically renormalized to the simplex before scoring only to remove floating-point roundoff;
- no prospective outcomes, Supabase reads, paid Odds API calls, model promotion or production artifact writes were used by this protocol;
- the existing Ligue 1 `LIGUE_1_MARKET_ONLY_V1` observation was not modified.

## Observed aggregate result

Outer aggregate across 1,278 selected-candidate match rows:

- hybrid accuracy: `0.5328638497652582`
- market accuracy: `0.5359937402190923`
- hybrid logloss: `0.9803446605598729`
- market logloss: `0.9799416408342757`
- hybrid Brier: `0.5838158287563486`
- market Brier: `0.5835287290756717`

The outer aggregate hybrid was worse than market on all three required metrics.

Outer season win counts:

- accuracy: `1/4`
- logloss: `1/4`
- Brier: `1/4`
- simultaneous all-three wins: `0/4`

The preregistered requirement was at least `3/4` for each metric and at least `3/4` simultaneous all-three wins. All corresponding outer robustness conditions are false.

## Outer folds

### 2022-2023

- selected candidate: `full_no_odds::xgb_shallow`
- selected alpha: `0.05`
- matches: `370`
- accuracy: hybrid `0.5486486486486486` vs market `0.5459459459459459` — win
- logloss: hybrid `0.976680388652246` vs market `0.9763137475919675` — loss
- Brier: hybrid `0.5804919850883123` vs market `0.5802399675337895` — loss
- all-three win: false

### 2023-2024

- selected candidate: `core_elo::logistic_l2`
- selected alpha: `0.05`
- matches: `301`
- accuracy: hybrid `0.5083056478405316` vs market `0.5149501661129569` — loss
- logloss: hybrid `1.0107924842841505` vs market `1.0098454188513382` — loss
- Brier: hybrid `0.6066848815680964` vs market `0.6060068692836843` — loss
- all-three win: false

### 2024-2025

- selected candidate: `core_elo::logistic_l2`
- selected alpha: `0.05`
- matches: `306`
- accuracy: hybrid `0.5392156862745098` vs market `0.5392156862745098` — tie, therefore not a win
- logloss: hybrid `0.9596834232885785` vs market `0.9601055473599049` — win
- Brier: hybrid `0.5674089418188433` vs market `0.567608151631045` — win
- all-three win: false

### 2025-2026

- selected candidate: `core_elo::logistic_l2`
- selected alpha: `0.05`
- matches: `301`
- accuracy: hybrid `0.53156146179402` vs market `0.5415282392026578` — loss
- logloss: hybrid `0.9754055385327313` vs market `0.9746629960491447` — loss
- Brier: hybrid `0.5817119904298171` vs market `0.5812782914209884` — loss
- all-three win: false

## Final development recipe

Selection over all six development OOS seasons chose:

- candidate: `core_elo::logistic_l2`
- alpha: `0.05`

Final development aggregate:

- hybrid accuracy: `0.5230084116773874`
- market accuracy: `0.5254824344383968`
- hybrid logloss: `0.986699533929697`
- market logloss: `0.9861043730789244`
- hybrid Brier: `0.5878845360866819`
- market Brier: `0.5874909375170225`

The final development recipe lost to market on all three metrics, so `final_development_recipe_all_three=false`.

## Frozen gate result

- `outer_aggregate_all_three=false`
- `outer_accuracy_wins_at_least_3_of_4=false`
- `outer_logloss_wins_at_least_3_of_4=false`
- `outer_brier_wins_at_least_3_of_4=false`
- `outer_all_three_wins_at_least_3_of_4=false`
- `final_development_recipe_all_three=false`

Overall PASS requires every condition, therefore V1 is rejected.

## Safety proof

Successful CI research artifact:

- artifact ID: `10182923802`
- ZIP SHA256: `71a89413ecdd43d706a536ebac1eaa272b1f7d54c5554079a4ad01fd56a0618b`

Historical rows admitted to modeling: `3198`
Structurally excluded 2019-20 source rows: `279`
Trainable rows after warmup/PIT preparation: `3089`

Production state was identical before and after the run. In particular:

`football_model_xgboost_elo.pkl = 1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`

`production_unchanged=true`

No candidate `.pkl` artifact was created: `artifact_created=false`.

## Ligue 1 state after V1

- `CAPTURE_READY=true` under `LIGUE_1_MARKET_ONLY_V1`;
- prospective MARKET_ONLY count remains `1/100`;
- `MODEL_READY=false`;
- `PROSPECTIVE_AI_READY=false`;
- the existing MARKET_ONLY observation remains immutable and must never receive a retrospective AI prediction or be relabeled as AI evidence;
- exact `ligue1_nested_development_v1` family is closed/rejected.

A future Ligue 1 AI attempt requires a genuinely new preregistered hypothesis with a defensible evidence boundary. The observed admitted historical development results cannot be reused as an untouched validation set, and the V1 gate cannot be relaxed.

## Next safe project step

Do not tune Ligue 1 V1 after this rejection. Preserve Ligue 1 prospective MARKET_ONLY collection and move to the next independent league/readiness block, most naturally Eredivisie, or to a genuinely new preregistered Ligue 1 hypothesis with a scientifically defensible new evidence boundary.
