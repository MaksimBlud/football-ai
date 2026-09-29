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


## First frozen execution

First complete run:

- workflow run: 36578009799
- head: b2834c0f6cd452dfa18cb643ed8574a450d5e6b7
- artifact: 11037889167
- artifact digest: sha256:0c14a97bf297554634576d62197e809162a0e1a7369c9f54fc10b4a189fef785

Environment:

- pandas 3.0.6
- numpy 2.5.3
- scipy 1.16.2

The walk-forward evaluation covered 1,520 outer-OOS matches across 2022/23–2025/26.

Pooled results:

| Method | LogLoss | Brier | Accuracy |
| --- | ---: | ---: | ---: |
| RAW_MULTIPLICATIVE | **0.9652140** | **0.5739288** | **54.67%** |
| TEMPERATURE | 0.9655033 | 0.5741885 | 54.67% |
| CLASS_BIAS | 0.9671066 | 0.5750707 | 54.28% |
| TEMPERATURE_BIAS | 0.9674557 | 0.5752947 | 54.34% |

Candidate-minus-raw pooled deltas:

- TEMPERATURE: LogLoss +0.0002893, Brier +0.0002597, joint season wins 0/4.
- CLASS_BIAS: LogLoss +0.0018927, Brier +0.0011418, joint season wins 1/4.
- TEMPERATURE_BIAS: LogLoss +0.0022417, Brier +0.0013658, joint season wins 0/4.

Paired bootstrap:

- TEMPERATURE LogLoss 95% CI: [-0.0002107, +0.0007883]
- TEMPERATURE Brier 95% CI: [-0.0000694, +0.0005856]
- CLASS_BIAS LogLoss 95% CI: [+0.0001511, +0.0035917]
- CLASS_BIAS Brier 95% CI: [+0.0000641, +0.0021886]
- TEMPERATURE_BIAS LogLoss 95% CI: [+0.0004660, +0.0039880]
- TEMPERATURE_BIAS Brier 95% CI: [+0.0003441, +0.0023965]

Thus no candidate passed the preregistered support gate. The bias-containing models were
statistically worse on both proper scoring rules; temperature-only was also worse on the
point estimates and never produced a joint seasonal win.

Frozen interpretation:

KEEP_RAW_MULTIPLICATIVE

## Decision

Do not add an outcome-trained calibration layer on top of the current Football-Data average
1X2 multiplicative market probabilities from V1 evidence.

This closes the simple favorite/longshot sharpness and global HOME/DRAW/AWAY bias hypotheses
for this source. The next distinct question is whether disagreement between bookmakers,
rather than a deterministic transformation of their average price, contains incremental
information.
