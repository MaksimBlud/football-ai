# MARKET_PROBABILITY_CALIBRATION_V1

Status: **research-only historical temporal OOS experiment**.

## Question

MARKET_DEVIG_METHODS_V1 and MARKET_DEVIG_BOOKMAKER_TIMING_V1 both kept the existing multiplicative de-vig transform.

This experiment asks the next separate question:

> after multiplicative de-vig, does a small outcome-trained calibration layer improve the historical EPL 1X2 market prior?

This tests systematic favorite/longshot sharpness and HOME/DRAW/AWAY bias without changing the underlying odds source or margin-removal method.

## Frozen source

Source: live Supabase public.matches, using the same Football-Data average 1X2 odds contract as MARKET_DEVIG_METHODS_V1.

Seasons:

- 2019/2020
- 2020/2021
- 2021/2022
- 2022/2023
- 2023/2024
- 2024/2025
- 2025/2026

Expected rows: **2,660**, exactly 380 per season.

No 2026/2027 outcomes are used.

## Baseline

RAW_MULTIPLICATIVE

For each match:

q_i = 1 / odds_i

p_i = q_i / sum(q)

This is the current Football AI market-probability baseline.

## Frozen calibration candidates

All candidates operate only on the already de-vigged probability vector p.

### TEMPERATURE

p'_i = softmax(log(p_i) / T)

T is fitted only on training seasons by minimizing multiclass LogLoss.

Frozen bounds: 0.50 <= T <= 2.00

### CLASS_BIAS

p'_i = softmax(log(p_i) + b_i)

DRAW is the reference class: b_draw = 0.

Fitted parameters: b_home, b_away.

Frozen bounds: -0.50 <= b_home,b_away <= 0.50

This tests systematic HOME/DRAW/AWAY calibration bias without changing sharpness.

### TEMPERATURE_BIAS

p'_i = softmax(log(p_i) / T + b_i)

with the same frozen temperature and bias bounds.

This is the most flexible candidate and still has only three free parameters.

## Temporal walk-forward

No outer-season outcome may fit its own calibration.

Outer OOS seasons:

- 2022/2023
- 2023/2024
- 2024/2025
- 2025/2026

For each test season:

- train on every earlier season from 2019/20 onward;
- fit each candidate only on those earlier outcomes;
- score once on the current season.

No candidate selection is performed inside a fold.

## Metrics

Primary: multiclass LogLoss; multiclass Brier.

Diagnostics: accuracy; favorite calibration gap; draw calibration gap; longshot calibration gap; fitted parameter trajectory by season.

## Support gate

For each fixed candidate versus RAW_MULTIPLICATIVE:

1. pooled OOS LogLoss must be lower;
2. pooled OOS Brier must be lower;
3. candidate must beat baseline on both metrics in at least 3 of 4 OOS seasons;
4. paired bootstrap 95% CI of candidate-minus-baseline must be entirely below zero for both LogLoss and Brier.

A candidate satisfying all four is SUPPORTED.

If more than one candidate is supported, select the one with lowest pooled OOS LogLoss, then pooled Brier.

If none is supported: KEEP_RAW_MULTIPLICATIVE.

This is a research conclusion only and does not authorize production replacement.

## Safety

- read-only Supabase;
- zero Odds API calls;
- no Supabase writes;
- no .pkl writes;
- no production promotion;
- output only under artifacts/market_probability_calibration_v1/.
