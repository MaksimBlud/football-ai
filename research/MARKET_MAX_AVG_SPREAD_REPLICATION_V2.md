# MARKET_MAX_AVG_SPREAD_REPLICATION_V2

Status: **research-only external cross-league replication**.

## Origin of the hypothesis

`MARKET_MAX_AVG_SPREAD_V1` was an EPL experiment whose preregistered HIGH-spread -> higher market-error direction failed. Post hoc, HIGH spread instead had much LOWER raw AVG_STANDARD Brier in all seven EPL seasons.

That inverse EPL observation is only a hypothesis generator. V2 tests it on leagues that were not used to discover it.

## Replication leagues

- LA_LIGA — Football-Data SP1
- SERIE_A — Football-Data I1
- BUNDESLIGA — Football-Data D1
- LIGUE_1 — Football-Data F1

EPL is excluded from every V2 support statistic.

Historical seasons: 2019/20–2025/26.

## Zero-cost source

Football-Data CSV only. No Odds API calls.

Required columns:

- AvgH / AvgD / AvgA
- MaxH / MaxD / MaxA

Closing prices are not needed for this replication.

A league-season is usable only when at least 90% of rows have valid Avg/Max odds and Max >= Avg for all H/D/A. A league is support-eligible only if all seven seasons pass this coverage gate.

## Frozen spread definition

For each outcome i:

`relative_gap_i = MaxOdds_i / AvgOdds_i - 1`

`spread = sqrt(mean(relative_gap_H^2, relative_gap_D^2, relative_gap_A^2))`

## Frozen thresholds transferred from EPL V1

No threshold is re-estimated on replication outcomes or replication spread distributions.

- LOW: spread <= 0.04177782395388535
- HIGH: spread >= 0.06264317681762262

Middle rows are excluded from HIGH-vs-LOW contrasts.

## Market probabilities

Avg odds are converted with the already-frozen MULTIPLICATIVE de-vig transform.

## Matched-cell coverage

A league-season cell enters a HIGH-vs-LOW contrast only if it contains at least **5 HIGH**
and **5 LOW** rows under the transferred EPL thresholds.

At least **20 matched league-season cells** across the eligible replication leagues are
required; otherwise V2 fails closed as `INSUFFICIENT_MATCHED_CELL_COVERAGE`.

## Primary replication metric: raw Brier

For each match:

`Brier = sum_i (p_i - y_i)^2`

The post-hoc EPL hypothesis predicts:

`mean Brier(HIGH) < mean Brier(LOW)`.

RAW_INVERSE_SPREAD_REPLICATION requires:

1. pooled HIGH-minus-LOW Brier < 0;
2. stratified bootstrap 95% CI entirely below zero;
3. negative HIGH-minus-LOW Brier in at least 3 eligible leagues;
4. negative effect in at least 60% of eligible league-season cells containing both groups.

## Primary confound-control metric: excess Brier

Raw Brier is mechanically affected by forecast sharpness/confidence. For a multinomial forecast p, its own expected Brier under perfect calibration is:

`expected_brier = 1 - sum_i p_i^2`

Define:

`excess_brier = realized_brier - expected_brier`

This centers each match against the uncertainty implied by that exact market probability vector and therefore controls the main favorite-strength/sharpness confound without fitting any outcome model.

The transferred hypothesis after confidence adjustment is:

`mean excess_brier(HIGH) < mean excess_brier(LOW)`.

CONFIDENCE_ADJUSTED_SPREAD_REPLICATION requires the same four gates as raw Brier.

## Additional diagnostic

Report HIGH-vs-LOW difference in market favorite probability `max(p)` for each league and pooled. This is diagnostic only and cannot define support.

## Bootstrap

10,000 stratified bootstrap draws.

Resampling is performed independently within each `(league, season, spread_group)` cell, preserving original HIGH/LOW sample sizes. The statistic is the pooled HIGH mean minus pooled LOW mean.

Fixed seed: 20260929.

## Interpretation

- `CONFIDENCE_ADJUSTED_SPREAD_REPLICATED` if excess-Brier gate passes.
- `RAW_ONLY_SPREAD_REPLICATION` if raw-Brier gate passes but excess-Brier gate fails.
- `NO_CROSS_LEAGUE_SPREAD_REPLICATION` if neither passes.
- `INSUFFICIENT_REPLICATION_COVERAGE` if fewer than 3 leagues pass the seven-season source gate.

Only the confidence-adjusted result would justify a later prospective/integration experiment. Raw-only support would be treated as evidence that EPL's apparent effect was mainly market-confidence composition.

## Safety

- research only;
- no EPL outcomes used in support statistics;
- zero paid Odds API calls;
- no Supabase reads or writes;
- no model training;
- no `.pkl` changes;
- no production promotion;
- JSON artifact only.
