# CORNER_TOTAL_CALIBRATED_V2 — Results

Status: **HISTORICAL PRIMARY RESULT COMPLETE / PORTABLE_CALIBRATED_TOTAL_SIGNAL**

## What changed from V1

Nothing about the underlying football signal changed. V2 uses the exact V1 raw 10-match corner-state score and fits only a straight calibration line on seasons strictly earlier than each held-out season.

This tests whether V1 failed because the raw score was too extreme rather than because it contained zero information.

## Held-out result

| Season | Matches | Train matches | Slope | Intercept | Calibrated MAE | Baseline MAE | Delta MAE | AUC >9.5 | Hit rate >9.5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019/2020 | 351 | 983 | 0.028101 | 10.008626 | 3.024665 | 3.024099 | +0.000565 | 0.503308 | 0.547009 |
| 2020/2021 | 370 | 1334 | 0.095006 | 9.373887 | 2.665271 | 2.671385 | -0.006113 | 0.460223 | 0.551351 |
| 2021/2022 | 370 | 1704 | 0.080301 | 9.487303 | 2.710288 | 2.712958 | -0.002671 | 0.513399 | 0.589189 |
| 2022/2023 | 370 | 2074 | 0.081541 | 9.494730 | 2.673643 | 2.674005 | -0.000362 | 0.458319 | 0.535135 |
| 2023/2024 | 370 | 2444 | 0.056646 | 9.716895 | 2.843303 | 2.851267 | -0.007965 | 0.556879 | 0.616216 |
| 2024/2025 | 370 | 2814 | 0.172648 | 8.577459 | 2.794719 | 2.811908 | -0.017189 | 0.552330 | 0.578378 |
| 2025/2026 | 380 | 3184 | 0.237031 | 7.891858 | 2.629694 | 2.649736 | -0.020042 | 0.492677 | 0.560526 |

Across 2581 held-out matches:
- weighted delta MAE ≈ **-0.007791**;
- calibrated MAE wins = **6/7 seasons**;
- weighted AUC for Over 9.5 ≈ **0.50527**;
- weighted 9.5 hit rate ≈ **0.56838**.

Frozen primary decision: **PORTABLE_CALIBRATED_TOTAL_SIGNAL**.

## Interpretation

There is a small but repeatable amount of information in the 10-match corner-state score for predicting the numerical total of match corners.

However the fitted slopes are only about 0.03 to 0.24. In plain language, the raw recent-corner signal must be shrunk heavily toward the league mean. Treating the raw score as a direct forecast, as V1 did, overreacts to recent corner numbers.

The Over/Under ranking result remains weak. Weighted AUC is only about 0.505, so V2 is **not** evidence of a useful betting selector for Over 9.5 and is not evidence of bookmaker edge.

## Decision

1. Keep V2 as evidence that recent corner state contains a small season-portable signal for expected corner count.
2. Do not use V2 as a betting/Over-Under model yet.
3. Do not change production `.pkl` models.
4. The next justified research step is to test a new preregistered mechanism aimed at match-to-match discrimination, such as shot/territorial pressure, rather than retuning V2.
5. Bookmaker corner-market comparison remains blocked until real corner-market prices are available through the existing manual-only capability gate.
