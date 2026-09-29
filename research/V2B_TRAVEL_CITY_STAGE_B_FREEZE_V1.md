# V2B TRAVEL-CITY STAGE-B FREEZE V1

Status: **PREREGISTERED FEATURE FREEZE / NO DIRECTION TEST**.

## Purpose

Freeze exactly one simple total-corners direction hypothesis from the newly proven
travel-city source before any V2B market-direction artifact is joined.

The source-only audit established complete travel-city reconstruction for all 86 team-sides
in the exact 43-fixture frozen V2B cohort.

## Immutable source

Travel source artifact:

- artifact ID `11044402420`;
- digest `sha256:24eaa543e51f1d19ec34d5b348fa091b91d31e7eca2ceeac270338dbaab3ab04`;
- source status `FULL_43_TRAVEL_CITY_PROXY_FEASIBLE`;
- fixtures = 43;
- team-sides = 86;
- finite travel distances = 86/86;
- market direction not read.

Geographic contract:

- pinned openfootball/clubs commit
  `ae3800227c449447b3a337fc0aac79a8f02f4c8b`;
- GeoNames cities500 bulk source;
- city-centroid great-circle distance proxy.

## Why joint travel

The target is total-corners direction rather than team result.

For each fixture, sum the two teams' displacement from the host city of their latest
full-calendar prior match to the current target host city:

`joint_travel_city_km = home_travel_city_km + away_travel_city_km`.

This asks whether the combined travel burden of both teams is associated with lower or
higher total-corners market repricing.

No home/away weighting is introduced.

## Frozen baseline

Use the median of `joint_travel_city_km` across all 43 feature-only rows.

From the immutable source artifact:

`cohort_median_joint_travel_city_km = 600.4646884282998`.

No market field was used to obtain this value.

## Frozen mapping

Mapping ID:

`JOINT_TRAVEL_CITY_COHORT_MEDIAN_SIGN_V1`

Define:

`stage_b_score = cohort_median_joint_travel_city_km - joint_travel_city_km`

Call:

- score > 0 -> **UP**;
- score < 0 -> **DOWN**;
- score == 0 -> **NO_CALL**.

Frozen qualitative hypothesis:

- lower combined travel burden than the cohort median -> more sustainable match tempo -> UP;
- higher combined travel burden -> more fatigue/logistical drag -> DOWN.

This is a hypothesis, not an established causal relationship.

## Frozen feature-only distribution

Before any direction join:

- UP = **21**;
- DOWN = **21**;
- NO_CALL = **1**.

Joint travel range:

- minimum = **50.27342715180188 km**;
- maximum = **4601.79600941109 km**.

By league:

- EPL: 8 UP / 1 DOWN / 0 NO_CALL;
- La Liga: 3 UP / 6 DOWN / 0 NO_CALL;
- Serie A: 4 UP / 4 DOWN / 1 NO_CALL;
- Bundesliga: 4 UP / 4 DOWN / 0 NO_CALL;
- Ligue 1: 2 UP / 6 DOWN / 0 NO_CALL.

This heterogeneity is retained exactly. Do not add league-specific medians after outcomes
are opened.

## Explicitly not used

This mapping does not use:

- centre_delta;
- observed UP/DOWN;
- FAIR_CENTRE;
- opening or closing corner line;
- target match result;
- rest days;
- matches_7d / matches_14d;
- travel/rest interaction;
- competition-specific weights;
- league-specific thresholds;
- exact-stadium coordinates.

Travel/rest interaction remains a separate hypothesis family and may not be substituted
for this mapping after evaluation.

## Later evaluator requirements

A separate evaluator may join this exact frozen feature artifact to the already-opened V2B
market-direction artifact.

It must report:

- all 43 rows;
- the exact 21 UP / 21 DOWN / 1 NO_CALL split;
- ZERO market movement separately;
- comparable UP/DOWN rows only for directional concordance;
- constant-UP / constant-DOWN baseline on the same comparable subset;
- UP recall, DOWN recall and balanced directional accuracy;
- by-league diagnostics without excluding any league;
- continuous stage_b_score vs centre_delta correlation;
- mean centre_delta for frozen UP and DOWN groups.

Use the same opened-sample exploratory consistency gate as prior Stage-B work:

`PROMISING_DIRECTION_HYPOTHESIS` only if:

1. pooled non-zero-movement concordance > 0.60;
2. at least 3 leagues each have >=2 comparable rows and concordance > 0.50;
3. frozen UP-call mean centre_delta > 0;
4. frozen DOWN-call mean centre_delta < 0.

Otherwise:

`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`.

Any result remains hypothesis generation, not independent confirmation.

## Safety

- research-only;
- NO_BET;
- zero Odds API calls;
- no Supabase operations;
- no production model operations;
- no production `.pkl` changes;
- no automatic promotion.
