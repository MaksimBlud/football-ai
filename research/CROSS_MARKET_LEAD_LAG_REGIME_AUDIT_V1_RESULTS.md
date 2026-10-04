# CROSS-MARKET LEAD-LAG REGIME AUDIT V1 — Results

Status: **FINAL / POST-HOC / NO BROAD 2025/26 REGIME PATTERN / NO_BET**.

## Provenance

First complete frozen diagnostic run:

- workflow run: `37179242297`;
- artifact ID: `11294566849`;
- artifact digest:
  `sha256:6728bc542249bfdb5c872352da571ed760d120a887127347e57f3c7d25cceff3`;
- generating head:
  `b6dd00db0be2901280e3dc8466f13d5f8736e982`.

This audit is explicitly **post-hoc**. It was motivated by the already-opened V1/V2
observation that all five leagues were positive in 2025/26.

It cannot create confirmatory support, reopen V1/V2, authorize paid data collection,
enable betting, or promote anything to production.

## Scope

Exact inherited statistic:

`alignment_dot = dot(p_score_open - p_1x2_open, p_1x2_close - p_1x2_open)`.

Leagues:

- EPL;
- La Liga;
- Serie A;
- Bundesliga;
- Ligue 1.

Seasons:

- 2019/20 through 2025/26.

Total eligible rows:

**2,920**.

No match result was used.

No 2026/27 data were opened.

No paid provider request or Supabase write was made.

Production model hashes were verified unchanged by workflow.

## Season-by-season result

| Season | Rows | Mean alignment | Positive leagues | Permutation p | Bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|
| 2019/20 | 420 | +0.00024808 | 5/5 | 0.00010 | [+0.00019310, +0.00030643] |
| 2020/21 | 413 | +0.00018061 | 5/5 | 0.00010 | [+0.00013007, +0.00023231] |
| 2021/22 | 414 | +0.00012952 | 5/5 | 0.00030 | [+0.00008060, +0.00017900] |
| 2022/23 | 441 | +0.00007156 | 5/5 | 0.00010 | [+0.00002165, +0.00012569] |
| 2023/24 | 389 | +0.00009759 | 5/5 | 0.00020 | [+0.00005050, +0.00014650] |
| 2024/25 | 419 | +0.00003958 | 3/5 | 0.00150 | [-0.00000769, +0.00008732] |
| 2025/26 | 424 | +0.00006992 | 5/5 | 0.00010 | [+0.00002535, +0.00011566] |

This immediately changes the interpretation of the earlier V1/V2 pattern.

## 2025/26 is not an unusually strong season

The post-hoc question was whether 2025/26 represented a new broad positive market regime.

It does not.

2025/26 pooled mean alignment:

**+0.00006992**

Pooled 2019/20–2024/25 mean:

**+0.00012761**

Difference:

**-0.00005769**

League-stratified bootstrap 95% CI for
`2025/26 minus prior`:

**[-0.00010667, -0.00000829]**

Bootstrap probability that the difference is positive:

**1.14%**

Mean-alignment rank of 2025/26 among the seven seasons:

**6 / 7**

Thus 2025/26 is not the high-alignment outlier. It is materially below the preceding
six-season pooled mean.

Formal diagnostic label:

`NO_BROAD_2025_26_REGIME_PATTERN`

## Cross-league comparison

2025/26 minus each league's own 2019/20–2024/25 mean:

- Bundesliga: **+0.00002852**;
- EPL: **-0.00009456**;
- La Liga: **-0.00010253**;
- Ligue 1: **-0.00004917**;
- Serie A: **-0.00006257**.

Only:

**1 / 5 leagues**

had a positive 2025/26-minus-prior difference.

So the fact that all five leagues were positive in 2025/26 was visually striking, but it
did not mean the underlying effect had strengthened.

## What is actually unusual

The historically unusual season is **2024/25**, not 2025/26.

From 2019/20 through 2023/24:

- every season had positive pooled mean alignment;
- every season had positive mean alignment in all 5/5 leagues;
- every season had a bootstrap 95% CI entirely above zero;
- every season strongly rejected the shuffled match-link null.

2025/26 returns to the same broad sign pattern:

- 5/5 leagues positive;
- pooled bootstrap CI entirely above zero.

2024/25 is the only season with:

- only **3/5** leagues positive;
- pooled mean only **+0.00003958**;
- bootstrap CI crossing zero.

Yet even 2024/25 still has a low shuffled-link permutation p-value:

**0.00150**.

This means the 2024/25 issue is not simply “no match-specific structure at all.”
The effect becomes small and cross-league heterogeneous enough that its absolute pooled
mean is uncertain.

## 2024/25 league means

- EPL: **+0.00013573**;
- La Liga: **+0.00002825**;
- Ligue 1: **+0.00002323**;
- Bundesliga: **-0.00000053**;
- Serie A: **-0.00000645**.

So the instability is concentrated in the league magnitudes/signs rather than a universal
same-direction collapse.

## Component pattern

One useful descriptive observation is that DRAW lead→future-move correlation remains
positive in every audited season and is often the strongest component.

Pooled Pearson correlations by season:

- 2019/20: HOME +0.193 / DRAW +0.382 / AWAY +0.222;
- 2020/21: HOME +0.204 / DRAW +0.401 / AWAY +0.114;
- 2021/22: HOME +0.108 / DRAW +0.336 / AWAY +0.085;
- 2022/23: HOME +0.162 / DRAW +0.236 / AWAY +0.105;
- 2023/24: HOME +0.162 / DRAW +0.240 / AWAY +0.088;
- 2024/25: HOME +0.104 / DRAW +0.286 / AWAY +0.038;
- 2025/26: HOME +0.158 / DRAW +0.144 / AWAY +0.158.

This is descriptive only. Selecting DRAW now as a new signal would be post-hoc and is not
allowed by this audit.

## Binding interpretation

The result rejects the specific explanation:

> “A new 2025/26 market regime caused the lead-lag alignment to appear.”

Instead, the data show:

> broad positive historical match-specific alignment is visible in most seasons, while
> 2024/25 is an unusually weak and heterogeneous season.

This does **not** overturn the preregistered decisions:

- `CROSS_MARKET_LEAD_LAG_V1` remains formally unsupported;
- `CROSS_MARKET_LEAD_LAG_REPLICATION_V2` remains formally unsupported;
- `NO_BET` remains binding.

The post-hoc audit cannot retroactively replace the frozen validation logic.

## Next bounded research question

The useful next zero-cost step is not another threshold search and not paid intraday
collection.

It is a **2024/25 anomaly/source-stability audit**:

> Did the weakening in 2024/25 coincide with a measurable change in source coverage,
> market definitions, margin/overround, AH-line composition, synthetic-gap magnitude,
> opening→closing movement magnitude, or league composition?

This next block must remain diagnostic and post-hoc.

It must be frozen before comparing the 2024/25 source/market diagnostics with adjacent
seasons.

Do not optimize a trading rule from the anomaly audit.

## Safety

- research-only;
- post-hoc diagnostic;
- confirmatory support forbidden;
- NO_BET;
- no outcomes;
- no 2026/27 data;
- zero paid Odds API calls;
- zero Supabase writes;
- production hashes unchanged;
- no production promotion.
