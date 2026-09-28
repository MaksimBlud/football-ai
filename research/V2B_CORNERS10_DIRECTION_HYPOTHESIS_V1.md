# V2B CORNERS10 DIRECTION HYPOTHESIS V1

Status: **PREREGISTERED OPENED-SAMPLE HYPOTHESIS GENERATION / 31 FIXED ELIGIBLE FIXTURES / NO CONFIRMATION CLAIM**

## Purpose

Explore one independent football-state mechanism for the sign of corner-market repricing on the already-opened V2B cohort.

The question is:

> when a leakage-safe CORNERS10 football-state estimate of expected total corners is above the Bet365 opening FAIR_CENTRE, does the market centre tend to move upward, and vice versa?

This is **hypothesis generation only**. The V2B market sample is already opened and its final direction verdict is already known.

No result from this block may be described as independent confirmation.

## Frozen fixture subset

Use only the exact V2B fixtures classified as CORNERS10-feasible by the already-merged feasibility audit:

- source audit: `V2B_CORNERS10_REPLAY_FEASIBILITY`;
- workflow run `36227211286`;
- artifact `10900784704`;
- digest `sha256:66c83b96f8c1143397aca660701d0a7f5950c3b59a1bd0158bbefe6501d7ecfb`;
- feasible fixtures = **31 / 43**.

The other 12 V2B fixtures remain explicitly ineligible.

No replacement, backfill or lower-division history is allowed.

## Football-history source

Use exactly the same zero-cost Football-Data source/identity contract as the feasibility audit:

- previous top-flight season = 2025/26;
- current top-flight season = 2026/27;
- EPL, La Liga, Serie A, Bundesliga, Ligue 1;
- only matches strictly before the target fixture;
- continuous history across the season boundary;
- canonical team aliases and exact deterministic fixture identity;
- no fuzzy matching.

## Frozen CORNERS10 state

For each eligible target fixture, compute the last-10 prior top-flight means:

- `home_corners_for_10`;
- `home_corners_against_10`;
- `away_corners_for_10`;
- `away_corners_against_10`.

No target-match corner outcome may enter these features.

## Frozen scalar total construction

Define a single symmetric football-only total expectation:

`home_expected = 0.5 * (home_corners_for_10 + away_corners_against_10)`

`away_expected = 0.5 * (away_corners_for_10 + home_corners_against_10)`

`corners10_total = home_expected + away_expected`

Equivalent:

`corners10_total = 0.5 * (home_for10 + home_against10 + away_for10 + away_against10)`

No weights are fitted.

No alternative formula may be substituted after results are viewed.

## Frozen market comparison

Use the already-opened immutable V2B evaluation artifact:

- workflow run `36223204711`;
- artifact `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`.

Use only:

- `fixture_id`;
- `league`;
- `opening_lambda`;
- `centre_delta`.

Define:

`football_gap = corners10_total - opening_lambda`

Predicted direction:

- `UP` when `football_gap > 0`;
- `DOWN` when `football_gap < 0`;
- `TIE` when exactly zero.

Observed direction:

- `UP` when `centre_delta > 0`;
- `DOWN` when `centre_delta < 0`;
- `ZERO` when exactly zero.

## Frozen descriptive outputs

Primary exploratory diagnostic:

- among rows with non-zero `football_gap` and non-zero `centre_delta`, count:
  - comparable rows;
  - concordant rows;
  - concordance rate.

Also report:

- all 31 eligible rows;
- rows with zero observed movement;
- rows with positive/negative football gap;
- mean and median `centre_delta` by football-gap sign;
- mean movement magnitude by football-gap sign;
- per-league comparable/concordant diagnostics;
- Pearson and Spearman correlation between continuous `football_gap` and `centre_delta` as descriptive diagnostics only.

No threshold search.

No p-value gate.

No league exclusion.

No sign reversal after viewing results.

## Interpretation rule

This block has no PASS/FAIL confirmation verdict.

Allowed research classifications:

- `PROMISING_DIRECTION_HYPOTHESIS` only when:
  - pooled comparable concordance is > 0.60; and
  - at least 3 leagues with >=2 comparable rows have concordance > 0.50; and
  - the sign of mean `centre_delta` is positive for positive football-gap rows and negative for negative football-gap rows;
- otherwise `WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`.

This classification is exploratory and cannot enable betting, production or a direction rule.

Any promising result must be preregistered again and tested on a new unseen market cohort.

## Safety

- research-only;
- opened-sample hypothesis generation;
- zero Odds API calls;
- public Football-Data result source only;
- no Supabase writes;
- no production `.pkl` changes;
- no betting/staking;
- no production promotion;
- no result-dependent feature/weight/threshold search.
