# MARKET_DEVIG_METHODS_V1

Status: **research-only preregistered historical market experiment**.

## Question

Football AI currently removes 1X2 bookmaker margin by proportional normalization:

`q_i = 1 / odds_i`

`p_i = q_i / sum(q)`

This experiment asks whether a different deterministic de-vig transform gives better
probability forecasts for EPL 1X2 outcomes.

The tested alternatives are:

- `ADDITIVE`
- `POWER`
- `SHIN`

The existing `MULTIPLICATIVE` method is the frozen baseline.

## Literature motivation

Štrumbelj (2014) reports that Shin probabilities can outperform basic normalization in
forecast accuracy. Shin's original model treats bookmaker prices as affected by informed
trading risk. Power and additive transformations are established alternative margin-removal
rules. This experiment treats the literature only as a source of hypotheses; the project
decision is made from Football AI data.

## Source contract

Source of truth: live Supabase `public.matches`.

The historical import code maps Football-Data:

- `AvgH -> home_odds`
- `AvgD -> draw_odds`
- `AvgA -> away_odds`

Only complete EPL seasons with valid average 1X2 odds are admitted:

- 2019/2020
- 2020/2021
- 2021/2022
- 2022/2023
- 2023/2024
- 2024/2025
- 2025/2026

Expected sample: exactly **2,660 matches**, 380 per season.

No 2026/2027 outcomes are used.

## Frozen transformations

Let `q_i = 1 / odds_i`, `S = sum(q)`, and `n = 3`.

### MULTIPLICATIVE

`p_i = q_i / S`

### ADDITIVE

`p_i = q_i - (S - 1) / n`

Rows yielding any non-positive probability are invalid for this method and fail closed.
No clipping is allowed.

### POWER

Solve `k` such that:

`sum(q_i ** k) = 1`

and return `p_i = q_i ** k`.

Bisection is deterministic and must converge before probabilities are accepted.

### SHIN

Use the standard Shin/Jullien-Salanié iterative solution:

`z <- (sum(sqrt(z^2 + 4(1-z)q_i^2/S)) - 2) / (n-2)`

until convergence, then:

`p_i = (sqrt(z^2 + 4(1-z)q_i^2/S) - z) / (2(1-z))`.

The implementation is regression-tested against the published Python `shin` example
for decimal odds `[2.6, 2.4, 4.3]`.

## Temporal evaluation

No method has parameters learned from match outcomes.

Nevertheless candidate selection is separated temporally:

### Discovery

2019/20–2023/24 (5 seasons, 1,900 matches).

Among ADDITIVE, POWER and SHIN, a method is discovery-eligible only if:

1. pooled LogLoss is lower than MULTIPLICATIVE;
2. pooled multiclass Brier is lower than MULTIPLICATIVE;
3. it improves both metrics in at least 3 of the 5 discovery seasons.

The eligible method with the lowest pooled LogLoss wins, with pooled Brier as tie-breaker.
If none qualify, selection is `MULTIPLICATIVE`.

### Validation

2024/25.

The selected alternative must beat MULTIPLICATIVE on both LogLoss and Brier.
Otherwise the active method fails closed to `MULTIPLICATIVE` before final test.

### Final temporal test

2025/26.

The frozen active method is evaluated once.

## Final support gate

`ROBUST_DEVIG_SUPPORT` requires all of the following:

- discovery selected a non-baseline method;
- validation improved both LogLoss and Brier;
- final 2025/26 improved both LogLoss and Brier;
- over all 2,660 matches, paired bootstrap 95% CI for candidate-minus-baseline is
  entirely below zero for both LogLoss and Brier.

Otherwise result is `KEEP_MULTIPLICATIVE`.

This is a research decision only. It does not modify production probabilities.

## Diagnostics

The report also includes:

- season-by-season LogLoss/Brier;
- mean overround;
- favorite probability calibration error;
- draw probability calibration error;
- longshot probability calibration error;
- method-specific parameters (`power k`, `Shin z`) summarized across rows;
- paired bootstrap deltas.

## Safety

The experiment:

- performs read-only Supabase access;
- performs no Odds API calls;
- performs no Supabase writes;
- creates no model artifact;
- modifies no production `.pkl`;
- makes no production promotion;
- writes only a JSON research report.
