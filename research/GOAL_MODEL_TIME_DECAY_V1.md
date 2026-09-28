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


## First frozen execution

First execution:

- workflow run: `36448380396`
- head: `efbc003eaca891aa7a3f1cf104c41f89de842487`
- artifact: `10981876417`
- artifact digest: `sha256:d1e81b25991ea460ccf3af12e1601ecfb0cc07edebd6223e64d577230625d439`

Environment:

- pandas `3.0.6`
- numpy `2.5.3`
- scikit-learn `1.9.1`
- xgboost `3.4.1`

The run used all 3,800 rows from the ten complete EPL seasons and produced six
outer historical OOS folds.

Nested selection chose:

- 2020/2021: half-life `1460` days;
- 2021/2022: `NONE`;
- 2022/2023: `NONE`;
- 2023/2024: `NONE`;
- 2024/2025: `NONE`;
- 2025/2026: `NONE`.

Therefore the fail-closed selector rejected decay in **5 of 6** outer folds.

Pooled selected-candidate minus uniform-baseline deltas:

| Metric | Baseline | Candidate | Delta |
| --- | ---: | ---: | ---: |
| Score NLL | 2.9998708814 | 3.0003089491 | +0.0004380678 |
| 1X2 LogLoss | 0.9946235955 | 0.9961418526 | +0.0015182571 |
| 1X2 Brier | 0.5928195644 | 0.5937755356 | +0.0009559712 |
| Over 2.5 LogLoss | 0.6879775507 | 0.6881029648 | +0.0001254141 |
| Over 2.5 Brier | 0.2472879475 | 0.2473571336 | +0.0000691861 |
| BTTS LogLoss | 0.6917430800 | 0.6908256088 | -0.0009174712 |
| BTTS Brier | 0.2492612878 | 0.2488173033 | -0.0004439845 |

For the two main 1X2 metrics the paired bootstrap showed a clear deterioration:

- 1X2 LogLoss delta 95% CI: `[+0.0005707, +0.0025053]`;
- 1X2 Brier delta 95% CI: `[+0.0003754, +0.0015507]`.

The only pooled improvement was BTTS, but it was generated by the single 2020/2021
fold in which decay was selected; the other five folds were exact baseline fallbacks.
That is not evidence for a general goal-model decay rule.

Frozen interpretation:

`NO_ROBUST_DECAY_SUPPORT`

## Decision

The Dixon–Coles-inspired **time-decay idea does not transfer to the current XGBoost
goal architecture as a general sample-weight rule** under this preregistered nested test.

Do not add exponential sample weighting to `train_goal_models_no_odds.py` from V1.

This negative result does not contradict the earlier simple Poisson attack/defence
diagnostic. It shows that the current XGBoost feature state (last-5 form, goals, shots,
shots on target, Elo and venue history) already absorbs enough recent-state information
that additional global recency weighting does not improve the main probabilistic targets.

The frozen compact result is stored in
`experiments/goal_model_time_decay_v1_report.json` and is checked against a fresh
runtime report by `goal_model_time_decay_v1_freeze_guard.py`.
