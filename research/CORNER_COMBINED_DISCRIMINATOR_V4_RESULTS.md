# CORNER_COMBINED_DISCRIMINATOR_V4 — Results

Status: **FINAL HISTORICAL FREE-DATA RESULT / NOT_PORTABLE_COMBINED_DISCRIMINATOR**

V4 was preregistered as the final feature-combination test in this corner block. It combines exactly three previously studied point-in-time signals: corner-state, all-shots pressure and shots-on-target pressure. Coefficients for every held-out season were fitted only on earlier seasons.

## Held-out result

| Season | Matches | Train matches | AUC >9.5 |
|---|---:|---:|---:|
| 2019/2020 | 351 | 983 | 0.495676 |
| 2020/2021 | 370 | 1334 | 0.514617 |
| 2021/2022 | 370 | 1704 | 0.456543 |
| 2022/2023 | 370 | 2074 | 0.485201 |
| 2023/2024 | 370 | 2444 | 0.495614 |
| 2024/2025 | 370 | 2814 | 0.553948 |
| 2025/2026 | 380 | 3184 | 0.509713 |

Across 2581 held-out matches:
- match-weighted AUC = **0.501691**;
- AUC > 0.50 in **3/7 seasons**.

Frozen decision: **NOT_PORTABLE_COMBINED_DISCRIMINATOR**.

The preregistered success rule required weighted AUC > 0.52 and at least 5/7 positive seasons. Neither condition passed.

## What this means

The free historical fields tested in this block do not provide a stable Over/Under 9.5 match selector.

The strongest defensible finding remains V2: recent corner-state contains a small, season-portable amount of information for the **expected numerical corner total after heavy shrinkage**, but that information does not translate into reliable match ranking around the 9.5 line.

V3 showed that simple shot pressure is also not a portable standalone discriminator. V4 confirms that combining these free signals does not solve the discrimination problem.

## Stop decision

Per the preregistered V4 stop rule:
- do not search more feature combinations, weights, windows or thresholds on these same held-out seasons;
- do not promote any corner-total model to production;
- do not claim bookmaker edge;
- the historical free-data corner block is complete.

The next meaningful corner evidence requires at least one genuinely new information source:
1. actual bookmaker corner lines/prices, or
2. richer event/territorial data not present in the current historical store.

Bookmaker corner acquisition remains behind the existing manual-only paid capability gate.
