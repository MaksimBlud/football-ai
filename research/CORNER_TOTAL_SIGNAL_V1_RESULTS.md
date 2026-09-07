# CORNER_TOTAL_SIGNAL_V1 — Results

Status: **HISTORICAL PRIMARY RESULT COMPLETE / NOT_PORTABLE_TOTAL_SIGNAL**

## What was tested

A fixed pre-match rule estimated total corners from each team's previous 10 EPL matches:

- expected home corners = average of home corners-for and away corners-against;
- expected away corners = average of away corners-for and home corners-against;
- expected total = sum of those two estimates.

The rule was frozen before the historical outcome metrics were queried.

Historical evidence used only EPL seasons 2016/2017 through 2025/2026. The current 2026/2027 season was excluded.

Source snapshot at evaluation:
- historical rows with corner outcomes: 3800;
- first date: 2016-08-13;
- last date: 2026-05-24;
- source MD5 over the fixed historical fields: `4854d62ace5e66dc68ff5e6bb6d9b737`.

## Primary held-out result

| Season | Eligible matches | Signal MAE | Baseline MAE | Delta MAE | AUC over 9.5 | 9.5 hit rate |
|---|---:|---:|---:|---:|---:|---:|
| 2019/2020 | 351 | 3.094587 | 3.031397 | +0.063190 | 0.503046 | 0.566952 |
| 2020/2021 | 370 | 2.743784 | 2.666183 | +0.077601 | 0.460814 | 0.508108 |
| 2021/2022 | 370 | 2.780541 | 2.716300 | +0.064240 | 0.513339 | 0.564865 |
| 2022/2023 | 370 | 2.752162 | 2.671879 | +0.080283 | 0.457996 | 0.486486 |
| 2023/2024 | 370 | 2.830135 | 2.849180 | -0.019045 | 0.557048 | 0.616216 |
| 2024/2025 | 370 | 2.805000 | 2.812114 | -0.007114 | 0.552615 | 0.572973 |
| 2025/2026 | 380 | 2.669737 | 2.646714 | +0.023023 | 0.492381 | 0.542105 |

Across 2581 held-out matches:
- weighted delta MAE = **+0.040076** (worse than baseline);
- MAE season wins = **2/7**;
- weighted AUC for Over 9.5 = about **0.5053**;
- AUC above 0.5 = **4/7 seasons**.

Frozen decision: **NOT_PORTABLE_TOTAL_SIGNAL**.

## Interpretation

Recent corner averages contain some local information in individual seasons, especially 2023/2024 and 2024/2025, but the fixed raw averaging rule does not transfer reliably across EPL seasons.

This does **not** invalidate `CORNERS10` as a portable football-state feature for 1X2. It answers a different question: the same information cannot simply be converted into a corner-total prediction by averaging four recent corner rates.

No weights, thresholds or windows were retuned after seeing this result.

## Next permitted step

A new experiment may test whether the raw corner-state score needs **out-of-sample calibration/shrinkage** rather than a different hand-picked formula. Such a V2 must be preregistered separately and trained only on seasons earlier than each held-out season.

No production model changes. No Odds API calls. No current-season outcome peeking.
