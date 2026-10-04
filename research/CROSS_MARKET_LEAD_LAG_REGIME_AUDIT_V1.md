# CROSS_MARKET_LEAD_LAG_REGIME_AUDIT_V1

Status: **POST-HOC REGIME-STABILITY DIAGNOSTIC / OUTCOME-FREE / NO_BET**.

## Why this audit exists

Two preregistered experiments are now closed:

### CROSS_MARKET_LEAD_LAG_V1

EPL / La Liga / Serie A.

- validation 2024/25 passed the frozen permutation gate;
- OOT 2025/26 had positive mean alignment in 3/3 leagues and permutation p = 0.00020;
- but the OOT bootstrap 95% CI crossed zero;
- formal decision remained `NO_OPEN_TO_CLOSE_CROSS_MARKET_LEAD_SIGNAL`.

### CROSS_MARKET_LEAD_LAG_REPLICATION_V2

Bundesliga / Ligue 1.

- validation 2024/25 failed;
- untouched 2025/26 passed its OOT gate in both 2/2 leagues;
- but validation failure means the formal replication decision remained
  `LEAD_LAG_REPLICATION_NOT_SUPPORTED`.

The striking post-hoc observation is that **all five leagues are positive in 2025/26**,
whereas earlier seasons are inconsistent.

This audit is motivated by that opened result. It therefore cannot provide confirmatory
support for the lead-lag hypothesis.

Its only purpose is to diagnose temporal regime stability using the **already-frozen**
statistic without retuning anything.

## Immutable statistic

For every eligible match:

`alignment_dot = dot(p_score_open - p_1x2_open, p_1x2_close - p_1x2_open)`.

Same bookmaker:

**Bet365**

Opening inputs:

- 1X2: `B365H/B365D/B365A`;
- O/U 2.5: `B365>2.5/B365<2.5`;
- AH: half-goal only, line `AHh` then `B365AH`,
  prices `B365AHH/B365AHA`.

Closing target:

- `B365CH/B365CD/B365CA`.

The Poisson/Skellam reconstruction, no-vig transforms, line restriction and sign are copied
unchanged from V1/V2.

## Scope

Leagues:

- EPL;
- La Liga;
- Serie A;
- Bundesliga;
- Ligue 1.

Seasons:

- 2019/20;
- 2020/21;
- 2021/22;
- 2022/23;
- 2023/24;
- 2024/25;
- 2025/26.

No 2026/27 data.

No football outcome field is used.

## Source provenance

Use the exact pinned transports already frozen by V1 and V2:

- E0/SP1/I1 from `cross_league_direct_markets_transport.py`;
- D1/F1 from `cross_market_lead_lag_replication_transport.py`.

No new source choice may be made after the audit runs.

## Season-by-season diagnostics

For each season, pooled across all five leagues, report:

- eligible rows;
- mean alignment_dot;
- median alignment_dot;
- positive-alignment rate;
- number of leagues with positive mean alignment;
- per-league mean alignment;
- mean opening synthetic gap TV;
- mean opening→closing move TV;
- mean gap-reduction TV;
- HOME/DRAW/AWAY lead→future-move Pearson and Spearman correlations.

## Same-season shuffled null

For each season independently:

- keep each match's future 1X2 move fixed;
- permute opening lead vectors within the same league;
- recompute pooled mean alignment;
- 10,000 draws;
- seed `20261004`.

This is descriptive here. No season-level p-value can create a new support decision.

## Same-season bootstrap

For each season:

- resample matches with replacement within each league;
- preserve original league sample sizes;
- 10,000 draws;
- seed `20261004`;
- report 95% CI for pooled mean alignment.

Again, this is descriptive.

## 2025/26 exceptionality diagnostics

Because the question was motivated after observing the V1/V2 OOT pattern, these are
explicitly post-hoc.

Report:

1. rank of 2025/26 pooled mean alignment among all seven seasons;
2. rank of its positive-league count among all seven seasons;
3. mean alignment in 2025/26 minus pooled mean alignment across all 2019/20–2024/25 rows;
4. a league-stratified bootstrap CI for that 2025/26-minus-prior difference;
5. for each league, 2025/26 alignment minus that league's own 2019/20–2024/25 mean;
6. number of leagues where that within-league difference is positive.

No threshold is fitted.

No season is dropped.

No alternative starting year is selected after seeing results.

## Interpretation labels

The audit may use only descriptive labels:

### `BROAD_2025_26_POSITIVE_REGIME_PATTERN`

Use if:

- 2025/26 has positive pooled mean;
- at least 4/5 leagues have positive mean;
- 2025/26 pooled mean is above the pooled pre-2025/26 mean.

### `NO_BROAD_2025_26_REGIME_PATTERN`

Otherwise.

These labels are diagnostic only.

Neither label changes the formal V1/V2 decisions.

## What this audit cannot authorize

It cannot authorize:

- paid timestamped collection;
- a betting rule;
- live signal activation;
- production feature addition;
- threshold selection;
- league selection;
- retrospective reclassification of V1/V2.

If 2025/26 is clearly exceptional, the only legitimate conclusion is that a **new future
prospective sample** would be needed to test whether that regime persists.

## Safety

- research-only;
- post-hoc diagnostic;
- outcome-free;
- no 2026/27 data;
- zero paid Odds API calls;
- no Supabase writes;
- no production model operations;
- no production `.pkl` changes;
- no automatic promotion.
