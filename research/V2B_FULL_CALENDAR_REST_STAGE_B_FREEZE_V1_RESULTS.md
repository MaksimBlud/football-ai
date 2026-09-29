# V2B FULL-CALENDAR REST STAGE-B FREEZE V1 — Results

Status: **FEATURE COHORT FROZEN / NO DIRECTION TEST**

## Provenance

Workflow run:

`36588058549`

Authoritative feature-freeze artifact:

- ID `11042123742`;
- digest `sha256:5157a50d2516aa7088eb1c89a0b95e8d31a8c328a6c0b8ee4488489ee8559918`;
- size 2,899 bytes;
- generating head `15cde5751662a48442d7772c50187e47c6819d54`.

Immutable upstream full-calendar feasibility source:

- artifact `11041563442`;
- digest `sha256:93a2f808b7542a5f9c6429e2808e6f462f044404f3219adef5a1b80d880cf68c`;
- exact fixtures = 43;
- full-calendar reconstruction = 43/43.

No market-direction artifact was read.

## Frozen primary mapping

`JOINT_FULL_REST_COHORT_MEDIAN_SIGN_V1`

`joint_full_rest_days = home_full_rest_days + away_full_rest_days`

Feature-only cohort median:

**11.0 days**

`stage_b_score = joint_full_rest_days - 11.0`

Call:

- score > 0 -> **UP**;
- score < 0 -> **DOWN**;
- score == 0 -> **NO_CALL**.

Frozen interpretation:

- more aggregate recovery than the frozen cohort median -> UP;
- less aggregate recovery / more short-turnaround pressure -> DOWN.

This orientation was fixed before opening V2B direction and is a hypothesis, not a causal
claim.

## Frozen calls

Across all 43 rows:

- UP = **17**;
- DOWN = **19**;
- NO_CALL = **7**.

Score range:

- minimum = **-5.0**;
- maximum = **+5.0**.

Exact fixture identity hash:

`sha256:c2891591d871b3ad8432915761f90065f6941f9055204d4d0b5327d71e4e52ea`

Frozen feature hash:

`sha256:d876b37f9315a535a0a92ef9ff2f06e62a3c70321c96982ba6395ec7be5feec6`

## Calls by league

EPL:

- UP = 1;
- DOWN = 8;
- NO_CALL = 0.

La Liga:

- UP = 0;
- DOWN = 8;
- NO_CALL = 1.

Serie A:

- UP = 4;
- DOWN = 1;
- NO_CALL = 4.

Bundesliga:

- UP = 6;
- DOWN = 0;
- NO_CALL = 2.

Ligue 1:

- UP = 6;
- DOWN = 2;
- NO_CALL = 0.

This strong league heterogeneity is retained exactly as frozen.

Do not introduce league-specific centering or thresholds after seeing this distribution.

## Why this is not post-outcome tuning

The threshold is the median of a single preregistered feature:

`home_full_rest_days + away_full_rest_days`

computed across the complete 43-row feature-only cohort.

At freeze time:

- market rows read = false;
- V2B odds read = false;
- opening lambda read = false;
- FAIR_CENTRE read = false;
- centre_delta read = false;
- direction test performed = false;
- threshold fitted to outcomes = false.

## Explicitly closed degrees of freedom

After this freeze, do not:

- change 11.0 to another threshold;
- use a league-specific median;
- switch from joint rest to home-away rest difference;
- switch to matches_7d or matches_14d;
- weight cup/UEFA competitions differently;
- reassign the 7 NO_CALL rows;
- add travel;
- combine with FAIR_CENTRE before evaluating the primary mapping.

## Next permitted block

A separate evaluator may join this exact immutable feature artifact to the already-opened
V2B market-direction artifact.

Required diagnostics:

1. preserve all 43 rows;
2. keep the exact 17 UP / 19 DOWN / 7 NO_CALL split;
3. report NO_CALL separately;
4. report ZERO market movement separately;
5. evaluate direction only on frozen UP/DOWN rows with non-zero observed movement;
6. compare with constant-UP and constant-DOWN baselines on that same comparable subset;
7. report UP recall, DOWN recall and balanced accuracy;
8. report by-league diagnostics without excluding any league;
9. report continuous stage_b_score vs centre_delta association.

Any V2B result remains opened-sample hypothesis generation only.

## Safety

- research-only;
- NO_BET;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.
