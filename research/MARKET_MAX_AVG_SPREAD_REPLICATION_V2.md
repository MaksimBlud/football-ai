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

## First successful execution

The initial workflow attempt failed before replication scoring because the EPL-specific
multiplicative helper required a strictly positive overround. Some non-EPL Football-Data
average triplets have sum(1/odds) <= 1. The frozen probability transform itself is still
q/sum(q), so the runner was corrected to apply that transform without the EPL-specific
positive-overround gate. No replication result had been produced before this correction.

First successful run:

- workflow run: 36585543053
- head: dd5ba26b860b86ff393f24eba3261efa856ad620
- artifact: 11041980670
- artifact digest: sha256:a098303910b0ed5a0dca06e3f1db042575f9aa2754b322a74e9600776968df7f

All four replication leagues passed the frozen source gate:

- La Liga: 2,660 valid rows;
- Serie A: 2,659 valid rows;
- Bundesliga: 2,142 valid rows;
- Ligue 1: 2,337 valid rows.

Prepared replication sample: **9,798 matches**.

All 28 league-season cells contained both transferred EPL HIGH and LOW groups with at
least five rows. The HIGH-vs-LOW comparison used **4,794 matches**.

### Raw Brier replication

The raw inverse spread effect reproduced very strongly:

- pooled HIGH-minus-LOW Brier: **-0.1590802**;
- 95% bootstrap CI: **[-0.1770875, -0.1405501]**;
- negative effect in **4/4 leagues**;
- negative effect in **28/28 league-season cells**;
- bootstrap probability negative: **1.0000**.

By league:

- Bundesliga: -0.1871532;
- La Liga: -0.1805605;
- Ligue 1: -0.1264940;
- Serie A: -0.1494525.

Therefore:

RAW_INVERSE_SPREAD_REPLICATION = true.

### Confidence/sharpness control

The HIGH spread group also had much stronger favorites.

Pooled HIGH-minus-LOW favorite probability:

**+0.2079960**, or about **+20.8 percentage points**.

By league the difference was:

- Bundesliga: +23.62 pp;
- La Liga: +20.85 pp;
- Ligue 1: +18.88 pp;
- Serie A: +20.53 pp.

After centering each realized Brier loss by the market's own expected Brier
`1 - sum(p_i^2)`, the apparent spread effect shrank dramatically:

- pooled HIGH-minus-LOW excess Brier: **-0.0136906**;
- 95% bootstrap CI: **[-0.0310142, +0.0046143]**;
- negative in 3/4 leagues;
- negative in 23/28 cells;
- bootstrap probability negative: 0.9338.

The confidence-adjusted preregistered gate therefore **did not pass**.

By league excess-Brier deltas:

- Bundesliga: -0.0071216;
- La Liga: -0.0373977;
- Ligue 1: +0.0020940;
- Serie A: -0.0115287.

Frozen interpretation:

RAW_ONLY_SPREAD_REPLICATION

## Decision

The EPL post-hoc raw effect is real and externally reproducible, but the evidence does not
support Max-vs-Avg spread as an independent uncertainty signal after controlling for the
sharpness/confidence of the market probability vector.

Operationally, HIGH Max-vs-Avg spread is largely a proxy for **strong-favorite market
structure**. Football AI already has the market probability itself, so adding spread as a
standalone confidence signal would mostly duplicate information already present in the
market prior.

Do not promote Max-vs-Avg spread from V2.

The next literature-driven research block should therefore move away from deterministic
transformations of the same 1X2 price vector and toward information that can add genuinely
orthogonal state: time-aligned market movement, cross-market structure, or football-state
information not already encoded by the market prior.
