# CROSS_MARKET_SCORE_COHERENCE_V1

Status: **PREREGISTERED HISTORICAL TEMPORAL-OOT / RESEARCH-ONLY / NO_BET**.

## Purpose

Test whether static disagreement between three bookmaker market families carries information
that is not already explained by the sharpness of the 1X2 probability vector.

This is deliberately different from `LA_LIGA_MULTIMARKET_ANCHOR_V5`.

V5 fed O/U and Asian-handicap prices directly into a multiclass model and asked whether
they improved 1X2 outcome prediction. It failed untouched OOT and stays closed.

V1 here instead reconstructs one **structural score model** from O/U 2.5 + Asian Handicap
and compares the 1X2 probabilities implied by that score model with the bookmaker's actual
1X2 probabilities.

Primary question:

> when O/U + AH imply a materially different 1X2 distribution from the quoted 1X2 market,
> is the quoted 1X2 market less reliable than its own probability sharpness would suggest?

## Frozen scope

Leagues:

- EPL;
- La Liga;
- Serie A.

Seasons:

- train/reference: 2016-17 through 2023-24;
- validation: 2024-25;
- untouched final OOT: 2025-26;
- 2026-27 outcomes forbidden.

Historical transport reuses the already-proven pinned Football-Data byte-identical mirror
fallback from `cross_league_direct_markets_transport.py` when the official host is
unreachable from GitHub Actions.

No paid provider request and no Supabase write is allowed.

## Same-bookmaker market contract

To avoid creating artificial cross-market disagreement by mixing bookmakers, V1 uses only
Bet365 rows where all of the following are simultaneously valid:

### 1X2

- `B365H`
- `B365D`
- `B365A`

The three-way probability vector is multiplicative no-vig normalization:

`p_i = (1 / odds_i) / sum_j(1 / odds_j)`.

### O/U 2.5

- `B365>2.5`
- `B365<2.5`

The Over probability is two-way multiplicative de-vig.

### Asian Handicap

- `B365AHH`
- `B365AHA`
- line: first finite value from `AHh`, then `B365AH`.

To avoid push/conditional-price ambiguity in the inverse score reconstruction, the primary
coherence sample includes **half-goal handicap lines only**:

- line must be an exact 0.5-step;
- integer handicap lines are excluded;
- quarter lines are excluded.

This restriction is frozen before outcome evaluation.

## Structural score reconstruction

Assume independent Poisson home and away goals with rates:

- `lambda_home > 0`;
- `lambda_away > 0`.

This assumption is a structural diagnostic, not a claim that Poisson is the final football
model.

### Step 1 — infer total intensity

Let `p_over25` be the no-vig Bet365 O/U probability.

Find `mu = lambda_home + lambda_away` satisfying:

`P(Poisson(mu) > 2) = p_over25`.

Use a deterministic scalar root on `mu in [0.05, 8.0]`.

Rows whose quoted probability is outside the attainable bracket fail closed.

### Step 2 — infer home share from Asian Handicap

Let `h` be the Bet365/Football-Data handicap line and `p_ah_home` the no-vig home-cover
probability.

For a half-goal line there is no push.

With `D = home_goals - away_goals`, home covers when:

`D + h > 0`.

Holding `mu` fixed, solve for the home share:

`s in [0.02, 0.98]`

where:

- `lambda_home = mu * s`;
- `lambda_away = mu * (1-s)`.

The target equation is the Skellam home-cover probability.

If an exact bracketed root does not exist, use bounded deterministic minimization and retain
the absolute AH fit residual. This is important: O/U and AH can themselves be inconsistent,
and that inconsistency must not be silently discarded.

## Synthetic 1X2

From the reconstructed Poisson/Skellam score model:

- HOME = `P(D > 0)`;
- DRAW = `P(D = 0)`;
- AWAY = `P(D < 0)`.

The synthetic vector is normalized only for numerical roundoff.

## Primary coherence feature

`score_gap_tv` is the total-variation distance between:

- actual Bet365 no-vig 1X2;
- synthetic 1X2 implied by Bet365 O/U 2.5 + AH.

Formula:

`0.5 * sum_i |p_1x2_i - p_score_i|`.

This feature uses no match result.

Secondary feature-only diagnostics:

- `ah_fit_abs_error`;
- `lambda_home`;
- `lambda_away`;
- `lambda_total`;
- quoted handicap line.

No alternative gap metric may replace `score_gap_tv` after results are opened.

## Feature-only thresholds

For each league independently, compute on **train/reference seasons only**:

- LOW threshold = 25th percentile of `score_gap_tv`;
- HIGH threshold = 75th percentile of `score_gap_tv`.

Validation and OOT use those unchanged league-specific train thresholds.

Rows between the thresholds are retained for continuous diagnostics but are not part of the
HIGH-vs-LOW primary contrast.

This thresholding uses feature values only, not outcomes.

## Outcome error metric

For realized 1X2 outcome one-hot vector `y`:

`market_brier = sum_i (p_market_i - y_i)^2`.

To avoid rediscovering the strong-favorite/sharpness confound already seen in the
Max-vs-Avg experiment, the primary target is:

`expected_market_brier = 1 - sum_i p_market_i^2`

`excess_brier = market_brier - expected_market_brier`.

If the 1X2 vector were perfectly calibrated conditional on itself, expected excess Brier
would be zero regardless of whether the match has a 70% favorite or three near-equal
outcomes.

Primary hypothesis:

`mean excess_brier(HIGH coherence gap) > mean excess_brier(LOW coherence gap)`.

Raw Brier HIGH-vs-LOW is diagnostic only and cannot establish support by itself.

## Validation gate

The hypothesis is validation-admissible only if, in 2024-25:

1. pooled HIGH-minus-LOW excess Brier is positive;
2. at least 2 of 3 leagues have positive HIGH-minus-LOW excess Brier;
3. every league has at least 15 HIGH and 15 LOW validation rows.

No threshold or sign may change after validation.

## Final untouched OOT gate

V1 is `CROSS_MARKET_COHERENCE_SUPPORTED` only if the validation gate passes and, in
untouched 2025-26:

1. pooled HIGH-minus-LOW excess Brier is positive;
2. at least 2 of 3 leagues have positive HIGH-minus-LOW excess Brier;
3. every league has at least 15 HIGH and 15 LOW OOT rows;
4. a stratified-by-league bootstrap with 10,000 draws has a 95% CI for pooled
   HIGH-minus-LOW excess Brier entirely above zero.

Otherwise:

`NO_INDEPENDENT_CROSS_MARKET_COHERENCE_SIGNAL`.

If validation fails, OOT may still be reported under the frozen code path, but it cannot
rescue the experiment.

## Secondary diagnostics

Report, without changing the primary decision:

- raw Brier HIGH-minus-LOW;
- log loss of actual Bet365 1X2;
- log loss of synthetic score-model 1X2;
- Brier of actual Bet365 1X2;
- Brier of synthetic score-model 1X2;
- correlation of `score_gap_tv` with market excess Brier;
- correlation of `score_gap_tv` with `ah_fit_abs_error`;
- coverage by league/season;
- distribution of handicap lines;
- reconstruction residual distribution.

The synthetic score model is **not** allowed to replace the bookmaker market merely because
one secondary metric looks favorable.

## Interpretation boundary

A positive result would mean:

> static disagreement among same-bookmaker 1X2, O/U and AH markets contains an uncertainty
> signal beyond simple 1X2 probability sharpness.

It would not mean:

- profitable betting;
- a direction to bet;
- that O/U or AH should replace 1X2;
- that the Poisson model is production-ready;
- that the signal is prospective;
- that production promotion is authorized.

A positive V1 would require a separate fresh replication or prospective experiment.

## Safety

- research-only;
- `NO_BET`;
- no production promotion;
- no production `.pkl` changes;
- no Supabase writes;
- no paid Odds API calls;
- no 2026-27 outcome access;
- no post-OOT threshold/sign changes.
