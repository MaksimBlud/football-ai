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

## First frozen execution

First complete execution after the protocol was frozen:

- workflow run: `36512919586`
- head: `893498d7b2b910cf858ca1b0ee57148b441a12f8`
- artifact: `11009388000`
- artifact digest: `sha256:dd3f8e6b86946da7e8a7ae7011d00fb0df0fdbf4555cb9f6f913603b7a9353dd`

Environment:

- pandas `3.0.6`
- numpy `2.5.3`

Observed mean historical overround: **4.4562%**.

### Discovery result — 2019/20 to 2023/24

Baseline MULTIPLICATIVE:

- LogLoss: `0.9575651997`
- Brier: `0.5664664060`

Alternatives:

| Method | Δ LogLoss | Δ Brier | joint season wins | Eligible |
| --- | ---: | ---: | ---: | --- |
| ADDITIVE | +0.0001922 | -0.0000670 | 2/5 | no |
| POWER | +0.0000645 | -0.0000887 | 2/5 | no |
| SHIN | +0.0000644 | -0.0000829 | 2/5 | no |

All three alternatives failed the preregistered discovery gate because none improved
both proper scoring rules and none reached three joint season wins.

Frozen discovery selection:

`MULTIPLICATIVE`

### Temporal holdouts

Even though discovery already failed closed, every deterministic method was retained as
a diagnostic on the two later seasons.

#### 2024/25

| Method | LogLoss | Brier |
| --- | ---: | ---: |
| MULTIPLICATIVE | **0.9705521** | **0.5788986** |
| ADDITIVE | 0.9707309 | 0.5793523 |
| POWER | 0.9710260 | 0.5795112 |
| SHIN | 0.9706346 | 0.5792037 |

#### 2025/26

| Method | LogLoss | Brier |
| --- | ---: | ---: |
| MULTIPLICATIVE | **1.0152524** | **0.6100247** |
| ADDITIVE | 1.0163601 | 0.6112641 |
| POWER | 1.0167239 | 0.6114091 |
| SHIN | 1.0160282 | 0.6109019 |

Thus every alternative was worse than MULTIPLICATIVE on both primary metrics in both
holdout seasons.

### Full 2,660-match diagnostic

Relative to MULTIPLICATIVE:

- ADDITIVE: LogLoss `+0.0003210`, Brier `+0.0001940`
- POWER: LogLoss `+0.0003240`, Brier `+0.0002220`
- SHIN: LogLoss `+0.0001686`, Brier `+0.0001097`

Paired bootstrap intervals crossed zero for all three alternatives, but their bootstrap
probability of being better than MULTIPLICATIVE was only approximately 24–33%, depending
on method and metric. There is therefore no evidence supporting replacement of the current
method.

Overall calibration also explains the direction. MULTIPLICATIVE's average favorite
forecast was slightly **below** the observed favorite rate, whereas Shin/Power/Additive
shifted additional probability toward favorites and away from longshots. That correction
is not helpful on this stored EPL average-odds sample.

Mean fitted diagnostic parameters:

- POWER `k = 1.04920`
- SHIN `z = 0.02249`

These parameters are descriptive only.

## Decision

Frozen interpretation:

`KEEP_MULTIPLICATIVE`

Active method remains:

`MULTIPLICATIVE`

Do not replace the current de-vig logic in `league_historical_market.py`,
`feature_engineering.py`, or `market_anchor_1x2_v1.py` from V1 evidence.

This result is specific to the stored Football-Data **average 1X2 odds** sample. It does
not prove that Shin/Power cannot outperform on a single bookmaker, a sharper bookmaker,
a closing-only line, a different league, or a different market. Those are separate
hypotheses requiring separately frozen experiments.
