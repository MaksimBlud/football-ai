# FAVORITE_LONGSHOT_BIAS_V1

Status: **research-only preregistered historical bookmaker-bias experiment**.

## Question

Classic betting-market literature documents a favorite–longshot bias: longshots often deliver worse realized returns than favorites, even after allowing for the bookmaker's overall margin.

Football AI already tested de-vig formulas and global market calibration. This experiment asks a different economic question:

> Does Bet365 1X2 pricing produce systematically worse flat-bet returns on low-probability outcomes than on high-probability outcomes, and does that pattern survive temporal holdouts and cross-league replication?

A positive result would not itself create a betting strategy. Its project use would be as a **risk/edge-threshold modifier**: model edges in structurally overcharged probability regions may need stronger evidence before action.

## Source

Zero-cost Football-Data CSV files only.

Leagues:

- EPL — E0
- LA_LIGA — SP1
- SERIE_A — I1
- BUNDESLIGA — D1
- LIGUE_1 — F1

Seasons:

- 2019/2020
- 2020/2021
- 2021/2022
- 2022/2023
- 2023/2024
- 2024/2025
- 2025/2026

No 2026/2027 rows are used.

Primary Bet365 standard columns:

- B365H / B365D / B365A

Closing diagnostic columns:

- B365CH / B365CD / B365CA

`STANDARD` is only the Football-Data column label. It is **not** asserted to be a true opening timestamp.

## Availability gate

A league is eligible only when Bet365 standard H/D/A odds are finite and > 1 on at least 90% of rows in every one of the seven seasons.

At least 4 of 5 leagues must pass. Otherwise the experiment fails closed.

Closing diagnostics are evaluated only where all three Bet365 closing columns are valid; closing coverage does not determine the primary standard-price gate.

## Probability transform

For each Bet365 1X2 triplet:

`q_i = 1 / odds_i`

`p_i = q_i / sum(q)`

This is the project's existing multiplicative no-vig transform.

## Probability bands

Every offered side is assigned by its no-vig probability before outcomes are inspected:

- P60_PLUS: p >= 0.60
- P50_60: 0.50 <= p < 0.60
- P40_50: 0.40 <= p < 0.50
- P30_40: 0.30 <= p < 0.40
- P20_30: 0.20 <= p < 0.30
- P10_20: 0.10 <= p < 0.20
- P_LT10: p < 0.10

Primary FAVORITE cohort:

`p >= 0.50`

Primary LONGSHOT cohort:

`p <= 0.20`

Exactly p=0.20 is LONGSHOT; exactly p=0.50 is FAVORITE.

## Flat-bet return

For a unit stake on one offered side:

- if the side wins: return = odds - 1
- otherwise: return = -1

ROI is the arithmetic mean of unit-stake returns.

Average odds are not used for the primary economic test; Bet365 is a coherent bookmaker source.

## Calibration diagnostic

For each band/cohort report:

- number of offered sides;
- mean no-vig probability;
- observed win rate;
- calibration gap = observed win rate - mean no-vig probability;
- mean offered odds;
- flat-bet ROI.

## Temporal protocol

Discovery:

- 2019/20–2023/24.

Validation:

- 2024/25.

Final temporal test:

- 2025/26.

The probability cutoffs are frozen a priori and are not selected from any outcomes.

## Primary bias statistic

`bias_delta = ROI_LONGSHOT - ROI_FAVORITE`

The favorite–longshot hypothesis predicts:

`bias_delta < 0`

meaning longshots have worse realized returns than favorites.

## Support gate

`FAVORITE_LONGSHOT_BIAS_SUPPORTED` requires all of:

1. discovery pooled bias_delta < 0;
2. validation 2024/25 bias_delta < 0;
3. final 2025/26 bias_delta < 0;
4. pooled all-season bias_delta < 0 in at least 4 of 5 eligible leagues;
5. a 10,000-draw match-level stratified bootstrap 95% CI for pooled bias_delta lies entirely below zero.

Bootstrap resamples fixtures independently within each league-season and carries all three 1X2 side records from a sampled fixture together. This preserves within-match dependence.

## Secondary checks

Report but do not select on:

- standard-price ROI by all seven probability bands;
- no-vig calibration gap by all seven bands;
- the same FAVORITE-vs-LONGSHOT statistic at Bet365 closing prices where available;
- best-available Max odds ROI by the same probability cohorts only as a line-shopping diagnostic if source coverage is sufficient.

Secondary checks cannot rescue a failed primary gate.

## Interpretation

If supported, the result means price efficiency is probability-dependent in this historical Bet365 sample. It does **not** mean blindly betting favorites is profitable.

Any future Football AI use must be a separate frozen experiment testing whether probability-band-aware edge thresholds improve OOS decisions relative to a single global edge threshold.

## Safety

- research only;
- zero paid Odds API calls;
- no Supabase reads/writes;
- no model training;
- no production .pkl changes;
- no production promotion;
- JSON research artifact only.

## First frozen execution

Authoritative first successful run:

- workflow run: 36587443157
- head: c0afe33eb87c5213b60540a097b91232846ad6de
- artifact: 11042317813
- artifact digest: sha256:842ae1eeef126730b587e7a1df798c74d280e6ee10613b6913f3ec9c7715c8a8

Environment:

- pandas 3.0.6
- numpy 2.5.3
- requests 2.32.5

All five leagues passed the primary Bet365 standard-price coverage gate.

Primary sample:

- 12,454 fixtures;
- 37,362 offered 1X2 sides.

### Frozen primary result

Discovery 2019/20–2023/24:

- FAVORITE ROI: -2.6493%;
- LONGSHOT ROI: -8.9648%;
- LONGSHOT minus FAVORITE: **-6.3155 pp**.

Validation 2024/25:

- FAVORITE ROI: -3.3290%;
- LONGSHOT ROI: -18.4687%;
- LONGSHOT minus FAVORITE: **-15.1397 pp**.

Final temporal test 2025/26:

- FAVORITE ROI: -5.1813%;
- LONGSHOT ROI: -15.0701%;
- LONGSHOT minus FAVORITE: **-9.8888 pp**.

Overall:

- FAVORITE: 6,197 offers, 3,986 wins, mean no-vig p 62.85%, ROI **-3.0910%**;
- LONGSHOT: 6,771 offers, 917 wins, mean no-vig p 14.53%, ROI **-11.1712%**;
- pooled LONGSHOT-minus-FAVORITE ROI delta: **-8.0802 pp**.

Match-level stratified bootstrap:

- 95% CI: **[-14.6717 pp, -1.4531 pp]**;
- probability delta < 0: 99.11%.

Cross-league direction:

- EPL: +2.6272 pp;
- La Liga: -15.7747 pp;
- Serie A: -15.0291 pp;
- Bundesliga: -4.2517 pp;
- Ligue 1: -9.2057 pp.

The required negative direction appears in **4/5 leagues**, so the preregistered cross-league gate passes even though EPL is an exception.

Frozen interpretation:

`FAVORITE_LONGSHOT_BIAS_SUPPORTED`

### Calibration pattern

The economic return pattern is consistent with a probability-dependent calibration pattern:

- overall FAVORITE observed win rate is about +1.47 pp above the no-vig probability;
- overall LONGSHOT observed win rate is about -0.99 pp below the no-vig probability.

Probability-band diagnostics are not monotonic at the extreme tail: P_LT10 had a small positive realized ROI (+0.23%) on only 1,083 offers. This was not a selected threshold and does not overturn the frozen FAVORITE-vs-LONGSHOT result. It must not be turned into a post-hoc betting rule.

### Closing-price diagnostic

At Bet365 closing prices the same direction is stronger overall:

- FAVORITE ROI: -2.6283%;
- LONGSHOT ROI: -12.5423%;
- delta: **-9.9139 pp**.

The closing diagnostic is negative in all five leagues. It is descriptive only and is not treated as information available earlier than close.

### Best-price / line-shopping diagnostic

Using Football-Data Max odds for settlement prices while keeping cohort membership frozen from Bet365 standard probabilities:

- FAVORITE ROI: +0.7518%;
- LONGSHOT ROI: -2.8315%;
- delta: **-3.5833 pp**.

This shows that price shopping materially reduces the bookmaker drag, but does not remove the pooled FAVORITE-vs-LONGSHOT return gap. Max columns are not a coherent single-book source and this diagnostic is not a production strategy.

## Decision for Football AI

Do **not** interpret the result as 'bet favorites'. Favorites were still negative at the primary Bet365 standard prices.

The actionable research implication is narrower: a model edge should not automatically face the same acceptance hurdle at every market probability. A +3 pp model-minus-market edge at p=0.65 and a +3 pp edge at p=0.15 may have different economic reliability because the low-probability region historically carries a much larger realized pricing drag.

The next safe experiment should compare a frozen **single global edge threshold** with a **probability-band-aware edge threshold** using already-existing OOS model-vs-market predictions. That experiment must be selected on earlier seasons and evaluated on later untouched seasons; V1 itself does not authorize any production threshold change.
