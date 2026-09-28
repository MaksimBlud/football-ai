# V2B CORNERS10 DIRECTION HYPOTHESIS V1 RESULTS

Status: **FINAL OPENED-SAMPLE HYPOTHESIS GENERATION / WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS**

## Provenance

Workflow run:

`36427498130`

Immutable artifact:

- artifact ID `10971841803`;
- digest `sha256:4bf2ef0c7defa48c6fef5cc96b56e08309a6cacdd0aed872e88759590264a4f1`;
- size 2,647 bytes.

Frozen feasibility source:

- run `36227211286`;
- artifact `10900784704`;
- digest `sha256:66c83b96f8c1143397aca660701d0a7f5950c3b59a1bd0158bbefe6501d7ecfb`;
- exact CORNERS10-feasible subset = **31 / 43** V2B fixtures.

Frozen opened-market source:

- run `36223204711`;
- artifact `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`.

No Odds API calls were made.

## Frozen signal

For each of the 31 eligible fixtures:

`corners10_total = 0.5 * (home_corners_for_10 + home_corners_against_10 + away_corners_for_10 + away_corners_against_10)`

`football_gap = corners10_total - opening_lambda`

Predicted direction:

- UP if football_gap > 0;
- DOWN if football_gap < 0.

Observed direction:

- UP if centre_delta > 0;
- DOWN if centre_delta < 0;
- ZERO if centre_delta = 0.

No fitted weights, threshold search, league exclusion or sign reversal were allowed.

## Result

Evaluated rows:

**31**

Football-gap sign:

- positive = 20;
- negative = 11;
- zero = 0.

Observed market movement:

- zero movement rows = **21**;
- therefore only **10** rows were direction-comparable.

Comparable direction result:

- comparable rows = **10**;
- concordant rows = **8**;
- pooled concordance = **0.80**.

By league:

- Bundesliga: 2 / 2 = 1.00;
- EPL: 1 / 2 = 0.50;
- La Liga: 2 / 2 = 1.00;
- Ligue 1: 1 / 1 = 1.00;
- Serie A: 2 / 3 = 0.6667.

Leagues with >=2 comparable rows and concordance >0.50:

**3**

## Why the classification is still weak/inconsistent

The preregistered exploratory rule also required the mean centre movement to align with football-gap sign.

Positive football-gap rows:

- rows = 20;
- mean centre_delta = **+0.1325740621**.

Negative football-gap rows:

- rows = 11;
- mean centre_delta = **+0.0320757777**.

The negative-gap group did **not** have negative mean movement.

Continuous association was also weak:

- Pearson correlation = **-0.1388936099**;
- Spearman correlation = **0.0131111223**.

Therefore:

`sign_group_mean_deltas_aligned = false`

Final classification:

**`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`**

## Interpretation

The 8/10 directional agreement among non-zero market movers is interesting but too sparse and internally inconsistent to treat as a reliable mechanism.

Most eligible fixtures did not move at all:

**21 / 31**

The continuous football_gap-to-centre_delta relationship is approximately absent, and the negative-gap group moved slightly upward on average.

Therefore this opened-sample result does **not** justify:

- a direction rule;
- a betting rule;
- exclusion of EPL;
- tuning a football-gap threshold;
- changing the scalar CORNERS10 formula;
- claiming 80% predictive accuracy.

If this mechanism is pursued later, it must first be converted into a new preregistered hypothesis and tested on a future unseen market cohort.

## Safety

- research-only;
- opened-sample hypothesis generation only;
- confirmatory replication = false;
- zero Odds API calls;
- no Supabase writes;
- no betting/staking;
- no production promotion;
- production .pkl hash guard passed.
