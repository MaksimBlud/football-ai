# Continuity Addendum — Serie A nested historical development V1 result

Date: 2026-09-11
PR: #244 — Preregister and run Serie A nested historical development v1
Branch: `research/serie-a-nested-development-v1`
Protocol: `serie_a_nested_development_v1`

## Final frozen-protocol verdict

`REJECTED_NO_FREEZE_RECOMMENDATION`

The preregistered Serie A nested historical development V1 gate did **not** pass. This exact candidate/hybrid family is closed for the purpose of justifying a future prospective AI protocol. The gate must not be weakened, retuned, or cherry-picked after observing these results.

## Evidence boundary

- all completed Serie A history through `2025-2026` was treated as **development-only**;
- `untouched_holdout_claimed=false`;
- historical seasons used: `2016-2017` through `2025-2026`;
- chronological development OOS seasons: `2020-2021` through `2025-2026`;
- outer test seasons: `2022-2023`, `2023-2024`, `2024-2025`, `2025-2026`;
- 12 preregistered candidates were evaluated from the pre-existing feature/model family;
- frozen alpha grid: `0.05` through `0.50` in `0.05` increments;
- no prospective outcomes, Supabase reads, Odds API calls, model promotion, or production artifact writes were used by the protocol.

## Observed aggregate result

Outer aggregate, 1,500 matches:

- hybrid accuracy: `0.5346666666666666`
- market accuracy: `0.5346666666666666`
- hybrid logloss: `0.9735448623263311`
- market logloss: `0.9735370672578572`
- hybrid Brier: `0.5802401247506277`
- market Brier: `0.5802028865183466`

Therefore the outer aggregate hybrid did not strictly beat the market on any of the three required metrics.

Outer season win counts:

- accuracy: `1/4`
- logloss: `2/4`
- Brier: `2/4`
- simultaneous all-three wins: `0/4`

The preregistered requirement was at least `3/4` for each metric and at least `3/4` simultaneous all-three wins. All corresponding gate conditions are false.

## Final development recipe

Selection over all six development OOS seasons chose:

- candidate: `core_elo::logistic_l2`
- alpha: `0.05`

Final development aggregate:

- hybrid accuracy: `0.5388046387154326`
- market accuracy: `0.5383586083853702`
- hybrid logloss: `0.9682727501479561`
- market logloss: `0.9682598897748838`
- hybrid Brier: `0.5759181597040229`
- market Brier: `0.5758662201629372`

The hybrid improved accuracy slightly but was worse on logloss and Brier, so `final_development_recipe_all_three=false`.

## Per-season interpretation

- `2022-2023`: logloss and Brier improved, accuracy worsened; not an all-three win.
- `2023-2024`: accuracy improved, logloss and Brier worsened; not an all-three win.
- `2024-2025`: logloss and Brier improved, accuracy tied; not a strict all-three win.
- `2025-2026`: all three metrics worse than market.

These mixed folds are not sufficient evidence for a future Serie A prospective AI freeze under V1.

## Safety proof

Research artifact digest from the successful CI run:

`sha256:975f8fa141302cb68689f0dc926769b9d29a6176be895136b725fb0efea3c0b2`

Production model state was identical before and after the run. In particular:

`football_model_xgboost_elo.pkl = 1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`

`production_unchanged=true`

No candidate `.pkl` artifact was created: `artifact_created=false`.

## Serie A state after V1

- `MODEL_READY=false`
- `PROSPECTIVE_AI_READY=false`
- `CAPTURE_READY=true` only for the already frozen `NON_EPL_MARKET_ONLY_V1` market-only protocol
- current MARKET_ONLY prospective observation remains immutable and must not be retroactively given an AI prediction or relabeled as AI evidence
- exact `serie_a_nested_development_v1` family is closed/rejected

A future Serie A AI attempt requires a genuinely new preregistered hypothesis with a defensible evidence boundary. It must not reuse these observed development results as an untouched validation set or relax the V1 pass criteria.

## Next safe project step

Do not tune Serie A V1 after this rejection. Continue with the next independent non-EPL league/readiness block or a generalized multi-league research runner that preserves league-specific scientific gates and keeps La Liga and Serie A rejected families closed.
