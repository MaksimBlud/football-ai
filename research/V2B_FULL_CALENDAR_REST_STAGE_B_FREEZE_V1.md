# V2B FULL-CALENDAR REST STAGE-B FREEZE V1

Status: **PREREGISTERED FEATURE FREEZE / NO DIRECTION TEST**

## Purpose

Freeze one simple direction hypothesis from the new full-calendar congestion source
before any V2B market-direction outcome is read.

The upstream source feasibility already established that all 43 V2B fixtures can be
reconstructed across league + relevant cup/UEFA load for the exact prior 14-day window.

## Immutable upstream artifact

Full-calendar feasibility artifact:

- ID `11041563442`;
- digest `sha256:93a2f808b7542a5f9c6429e2808e6f462f044404f3219adef5a1b80d880cf68c`;
- exact locked fixtures = 43;
- full-calendar feasible = 43/43;
- market direction not opened.

## Why aggregate rest, not home-away rest difference

The target is the **direction of a total-corners market**, not 1X2.

A home-minus-away recovery difference is naturally an asymmetry/team-strength feature.
For total corners, the primary preregistered hypothesis instead asks whether the two teams
jointly arrive more or less recovered than the feature-only cohort norm.

No match outcome or corner-market direction is used to choose this orientation.

## Frozen primary mapping

Mapping ID:

`JOINT_FULL_REST_COHORT_MEDIAN_SIGN_V1`

For every frozen fixture:

`joint_full_rest_days = home_full_rest_days + away_full_rest_days`

The baseline is the median of this quantity across **all 43 frozen feature-only rows**.

The immutable source produces:

`cohort_median_joint_full_rest_days = 11.0`

Then:

`stage_b_score = joint_full_rest_days - 11.0`

Call:

- score > 0 -> **UP**;
- score < 0 -> **DOWN**;
- score == 0 -> **NO_CALL**.

Interpretation frozen before outcomes:

- greater joint recovery than the cohort median -> more sustainable attacking tempo -> UP;
- lower joint recovery / greater short-turnaround pressure -> DOWN.

This is a hypothesis, not an established causal claim.

## Frozen feature-only call distribution

Before any direction join:

- UP = **17**;
- DOWN = **19**;
- NO_CALL = **7**.

The seven exact-median fixtures remain NO_CALL. They may not be reassigned after outcome
inspection.

## Explicitly not used

The primary mapping does not use:

- home-away rest difference;
- matches in prior 7d;
- matches in prior 14d;
- non-league match counts as a separate weight;
- competition-specific weights;
- travel;
- league-specific thresholds;
- FAIR_CENTRE;
- opening corner line;
- centre_delta.

Those fields cannot replace the frozen primary mapping after direction is opened.

## Later evaluator requirements

A separate evaluator may join this exact feature artifact to the already-opened V2B
market-direction artifact.

It must report:

- all 43 rows;
- seven frozen NO_CALL rows separately;
- zero market movement separately;
- comparable UP/DOWN rows only for directional concordance;
- constant-UP / constant-DOWN baselines on the comparable subset;
- UP and DOWN recall;
- balanced directional accuracy;
- by-league diagnostics;
- continuous score vs centre_delta correlation.

No threshold, sign, window, league set or feature choice may be altered after opening
direction.

Any V2B evaluation remains hypothesis generation. Confirmation requires unseen data.

## Safety

- research-only;
- NO_BET;
- zero Odds API calls;
- no Supabase writes;
- no production model changes;
- no automatic promotion.
