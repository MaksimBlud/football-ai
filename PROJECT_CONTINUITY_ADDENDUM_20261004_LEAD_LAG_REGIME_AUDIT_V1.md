# PROJECT_CONTINUITY ADDENDUM — 2026-10-04 — Lead-lag regime audit V1

## Context

Closed preregistered experiments:

- `CROSS_MARKET_LEAD_LAG_V1`;
- `CROSS_MARKET_LEAD_LAG_REPLICATION_V2`.

Both remain formally unsupported and `NO_BET`.

A post-hoc diagnostic was allowed only to explain the opened observation that all five
tested major leagues had positive mean alignment in 2025/26.

## Audit

`CROSS_MARKET_LEAD_LAG_REGIME_AUDIT_V1`

PR:

`#468`

First complete run:

- workflow `37179242297`;
- artifact `11294566849`;
- digest
  `sha256:6728bc542249bfdb5c872352da571ed760d120a887127347e57f3c7d25cceff3`;
- generating head
  `b6dd00db0be2901280e3dc8466f13d5f8736e982`.

Scope:

- EPL;
- La Liga;
- Serie A;
- Bundesliga;
- Ligue 1;
- seasons 2019/20–2025/26;
- 2,920 eligible rows;
- exact inherited `alignment_dot` statistic;
- no outcomes;
- no 2026/27;
- zero paid provider calls;
- zero Supabase writes.

## Main result

Diagnostic label:

`NO_BROAD_2025_26_REGIME_PATTERN`

2025/26 mean alignment:

**+0.00006992**

2019/20–2024/25 pooled mean:

**+0.00012761**

2025/26 minus prior:

**-0.00005769**

Bootstrap 95% CI:

**[-0.00010667, -0.00000829]**

2025/26 ranks only:

**6 / 7**

by pooled mean alignment.

Only Bundesliga has a positive 2025/26-minus-own-prior difference.

## Actual temporal pattern

Positive mean alignment leagues by season:

- 2019/20: 5/5;
- 2020/21: 5/5;
- 2021/22: 5/5;
- 2022/23: 5/5;
- 2023/24: 5/5;
- 2024/25: 3/5;
- 2025/26: 5/5.

Bootstrap CI for pooled mean is entirely positive in every listed season except 2024/25.

Therefore the opened “2025/26 new regime” explanation is rejected.

The anomalous period is **2024/25**, where the effect weakens and becomes cross-league
heterogeneous.

## Binding interpretation

Do not use this post-hoc audit to overturn V1/V2.

Still binding:

- no confirmed tradable lead-lag signal;
- no paid intraday collection justified by this evidence alone;
- no threshold/component selection from opened data;
- NO_BET;
- no production promotion.

## Current execution pointer

Next bounded zero-cost diagnostic:

`CROSS_MARKET_LEAD_LAG_2024_25_ANOMALY_AUDIT_V1`

Question:

> Is the 2024/25 weakening associated with an observable source/market-structure change
> rather than a newly emerging 2025/26 regime?

Freeze before comparison:

- source row and complete-market coverage;
- eligible half-goal AH share;
- AH-line distribution;
- opening 1X2 overround;
- opening O/U overround;
- opening AH overround;
- opening synthetic-gap magnitude;
- opening→closing 1X2 move magnitude;
- league composition / per-league cell sizes.

Diagnostic only. No outcomes. No new sign, threshold or betting rule.
