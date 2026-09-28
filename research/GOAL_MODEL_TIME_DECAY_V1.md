# GOAL_MODEL_TIME_DECAY_V1

Status: **research-only historical nested OOS experiment**.

This protocol tests one specific hypothesis derived from the Dixon–Coles literature:
older matches should contribute less to estimation of current scoring strength.

No production promotion is authorized by this experiment.

## Question

Does exponential recency weighting improve the **existing football-only XGBoost goal
architecture** when every other part of the pipeline is held fixed?

The experiment does **not** change:

- the current goal feature set;
- the current XGBoost hyperparameters;
- the independent-Poisson market conversion;
- production inference;
- any production `.pkl`.

Only XGBoost `sample_weight` changes.

## Source and frozen scope

Source of truth: live Supabase `public.matches`.

Included complete EPL seasons:

- 2016/2017
- 2017/2018
- 2018/2019
- 2019/2020
- 2020/2021
- 2021/2022
- 2022/2023
- 2023/2024
- 2024/2025
- 2025/2026

Explicitly excluded:

- 2026/2027

The experiment fails closed if the ten included seasons are not exactly 380 matches each
or if required outcomes are incomplete.

## Model contract

The feature list and XGBoost parameters mirror `train_goal_models_no_odds.py`.
A regression test parses that file statically and fails if the research mirror drifts.

Two regressors are fitted exactly as in the current architecture:

- home goals;
- away goals.

The baseline uses uniform weights.

Decay candidates use:

`raw_weight = 0.5 ** (age_days / half_life_days)`

The weights are then normalized to mean 1. This preserves relative recency weighting
without changing total effective sample-weight scale.

Frozen candidate grid:

- NONE
- 180 days
- 365 days
- 730 days
- 1460 days

## Nested temporal selection

Outer historical OOS tests start at 2020/2021 and continue through 2025/2026.

For every outer test season:

1. only earlier seasons may be used;
2. inner expanding-season OOS folds start at 2019/2020;
3. every half-life candidate is evaluated on those earlier inner folds;
4. selection fails closed to `NONE` unless a decay candidate beats `NONE` on **both**
   inner score NLL and inner 1X2 LogLoss;
5. among eligible decay candidates, the lowest inner score NLL wins, with 1X2 LogLoss
   as the tie-breaker;
6. baseline and the selected candidate are then refit on all seasons before the outer test
   and evaluated once on that outer season.

Therefore an outer season cannot influence its own half-life selection.

Because the time-decay hypothesis has already been explored descriptively on historical
2025/2026 outcomes with a different Poisson attack/defence model, this V1 result must be
described as **historical nested OOS evidence**, not as pristine untouched or prospective
evidence.

## Metrics

Primary structural metric:

- exact independent-Poisson score negative log-likelihood.

Primary downstream 1X2 metrics:

- multiclass LogLoss;
- multiclass Brier.

Diagnostics:

- home-goals MAE / RMSE;
- away-goals MAE / RMSE;
- Over 2.5 LogLoss / Brier;
- BTTS LogLoss / Brier.

Paired bootstrap intervals are calculated on pooled per-match loss deltas with a fixed seed.

## Interpretation gate

`HISTORICAL_NESTED_OOS_SUPPORT` requires pooled selected-candidate improvement over
uniform-weight baseline on all three:

- score NLL;
- 1X2 LogLoss;
- 1X2 Brier.

Otherwise the result is `NO_ROBUST_DECAY_SUPPORT`.

This is an evidence label only. It is **not** a promotion gate and does not authorize
betting or production replacement.

## Safety

The runner:

- performs read-only Supabase access;
- performs no Supabase writes;
- creates no model artifact;
- performs no production promotion;
- does not touch production `.pkl`;
- writes only a research JSON report under
  `artifacts/goal_model_time_decay_v1/`.

