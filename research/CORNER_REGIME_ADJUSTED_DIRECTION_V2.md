# CORNER_REGIME_ADJUSTED_DIRECTION_V2

Status: **PREREGISTERED / FUTURE-DATA BLOCK-LOCK CONTINUATION / MARKET-ONLY**

## Purpose

V1 ended with the binding verdict `SAMPLE_TOO_SMALL`:

- 46 eligible rows;
- 5 contributing leagues;
- 9 contributing league-day regime blocks;
- 30 comparable pairs versus the frozen minimum of 40;
- diagnostic observed concordance = 0.70;
- no permutation p-value was computed because the sample gate failed.

V2 does **not** retune the V1 direction hypothesis or statistical confirmation gate.

The only design change is prospective sample acquisition: before any new corner odds are opened, fixture metadata will be used to lock **whole future league-day blocks with enough potential pair density** so the next untouched sample has a materially better chance of satisfying the already-existing comparable-pair requirement.

Primary question remains:

> within matches exposed to the same league-day market regime, does lower opening FAIR_CENTRE identify the match whose reconstructed Bet365 corner-market centre subsequently moves farther upward relative to its contemporaneous peers?

## Evidence boundary

Opened data that must never be used for V2 feature/sign/threshold tuning:

1. original 55-row corner repricing discovery sample;
2. 50-row fresh repricing replication;
3. 46-row V1 regime-adjusted direction sample from PR #387.

These prior samples may be used only to:
- exclude their fixture IDs;
- preserve the already-defined FAIR_CENTRE representation;
- preserve the already-frozen direction score/statistical test;
- motivate the operational need for denser future league-day blocks.

V1's diagnostic 0.70 concordance is **not** a V2 target, effect-size prior, or threshold source.

## Future-only cutoff

V2 candidate fixtures must have:

`kickoff_utc >= 2026-09-19T00:00:00Z`

No fixture before this cutoff is eligible.

Leagues remain fixed:

- EPL
- LA_LIGA
- SERIE_A
- BUNDESLIGA
- LIGUE_1

## Metadata-only block construction

Before any V2 fixture odds endpoint is called:

1. read only fixture metadata;
2. keep finished fixtures at/after the future cutoff;
3. exclude every fixture ID from all three prior corner samples;
4. define metadata block:
   `regime_block = (league, UTC kickoff date)`;
5. discard metadata blocks containing fewer than 2 candidate fixtures because they cannot contribute a within-block pair;
6. keep every fixture in an included block; do not cherry-pick individual matches from the block;
7. sort candidate blocks by:
   - UTC kickoff date ascending;
   - fixed league order: EPL, LA_LIGA, SERIE_A, BUNDESLIGA, LIGUE_1.

For a metadata block containing `n` selected fixtures define:

`potential_pairs = n * (n - 1) / 2`

This uses fixture counts only. It does not inspect opening odds, closing odds, FAIR_CENTRE, centre_delta, match outcomes or football state.

## Frozen cohort-lock gate

The V2 cohort may be locked only when the deterministic metadata selection contains all of:

- all **5** leagues represented;
- at least **2 metadata blocks per league**;
- at least **12 metadata blocks pooled**;
- at least **80 potential unordered pairs pooled**.

The 80-pair metadata target is an operational 2x buffer over the unchanged 40-comparable-pair statistical minimum. It is not based on V1's observed 0.70 diagnostic effect.

Selection rule:

- traverse candidate blocks in frozen chronological/league order;
- include whole blocks;
- stop at the first block after which all cohort-lock conditions are satisfied;
- lock the exact selected fixture IDs and block membership immutably;
- do not later remove or replace fixtures because their odds are missing, tied or inconvenient.

If metadata inventory has not yet reached the lock gate:

`WAIT_FOR_COHORT`

No odds acquisition or statistical evaluation is allowed.

## Frozen market representation

Unchanged from V1:

- Bet365 full-time corner market;
- proportional de-vig of Over/Under prices;
- integer and half-integer lines only;
- Poisson-implied opening and closing market centre;
- `centre_delta = closing_lambda - opening_lambda`;
- `FAIR_CENTRE = opening_lambda`.

Quarter-lines and malformed markets are excluded at normalization, not approximated.

No match outcomes, goals, CORNERS10, team form, injuries, xG, 1X2, totals, handicaps or ROI variables are allowed.

## Frozen direction score

Exactly one score:

`direction_score = -opening_lambda`

Higher score = lower opening FAIR_CENTRE.

Frozen hypothesis remains:

> lower opening FAIR_CENTRE is associated with a stronger upward closing repricing relative to matches in the same league-day regime block.

No feature search, sign flip, model fitting, league-specific refit or threshold search is allowed.

## Frozen primary statistic

Unchanged from V1.

For every unordered pair of eligible matches inside the same regime block:

- omit score ties;
- omit centre_delta ties;
- otherwise call the pair concordant when the match with lower opening FAIR_CENTRE has the larger centre_delta.

`concordance = concordant_pairs / comparable_pairs`

## Frozen regime-preserving permutation test

Unchanged from V1:

- 20,000 permutations;
- RNG seed `20260918`;
- shuffle centre_delta independently only inside each regime block;
- opening scores remain fixed.

One-sided p-value:

`p = (1 + count(permuted_concordance >= observed)) / (20000 + 1)`

## Frozen statistical sample gate

Unchanged from V1.

Evaluation is confirmatory only when all are true:

- at least **30** eligible rows;
- at least **4** leagues contribute a comparable pair;
- at least **8** regime blocks contribute a comparable pair;
- at least **40** comparable pairs.

Otherwise:

`SAMPLE_TOO_SMALL`

The metadata 80-potential-pair lock does not replace this statistical gate.

## Frozen confirmation gate

Unchanged from V1.

Direction discrimination is confirmed only if:

- statistical sample gate passes;
- pooled concordance >= **0.60**;
- one-sided regime-preserving permutation p < **0.10**.

Verdicts:

- `INDIVIDUAL_DIRECTION_DISCRIMINATION_REPLICATED`
- `INDIVIDUAL_DIRECTION_DISCRIMINATION_NOT_CONFIRMED`
- `SAMPLE_TOO_SMALL`

No post-result gate change is allowed.

## Acquisition safety

V2 odds acquisition is not authorized by this preregistration alone.

Required order:

1. metadata-only cohort planner;
2. immutable cohort lock artifact;
3. offline validation of exact selected IDs/block counts/potential pairs;
4. separate explicit live marker before any odds request;
5. odds acquisition may resume only against the exact locked fixture IDs;
6. partial acquisition must preserve raw responses and resume only missing selected IDs;
7. no fixture-list reselection after odds have been opened.

No paid subscription or provider-plan upgrade is allowed.

## Diagnostics only

If/when V2 reaches evaluation, report but do not gate on:

- movement sign counts;
- per-league concordance;
- per-block concordance;
- per-block medians;
- top-minus-bottom regime-adjusted residual spread;
- V1 vs V2 descriptive effect-size comparison.

These cannot replace the frozen primary gate.

## Safety

- research-only;
- `NO_BET`;
- future data only;
- no match outcomes;
- no CORNERS10/football-state;
- no ROI optimization;
- no production promotion;
- no production `.pkl` changes;
- no Supabase writes;
- no paid provider action;
- no automatic live odds collection;
- no reuse of V1 diagnostic effect size for threshold tuning.

## Immediate implementation scope

This PR should initially implement only:

- deterministic metadata block planner;
- prior-fixture exclusion contract;
- immutable cohort-lock report schema;
- offline regression tests;
- dedicated offline CI;
- production `.pkl` hash guard.

It must **not** perform a live provider call.

