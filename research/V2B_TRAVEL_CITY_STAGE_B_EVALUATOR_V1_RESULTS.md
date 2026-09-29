# V2B TRAVEL-CITY STAGE-B EVALUATOR V1 — Results

Status: **FINAL OPENED-SAMPLE EVALUATION / WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS**.

## Provenance

First successful evaluator workflow run:

`36595762437`

Authoritative evaluator artifact:

- ID `11046326009`;
- digest `sha256:cf01a7bf151172c70f2478cc9f0d2b44efc8ca66011bda3346cd7fe8e0f1de5c`;
- generating head `fcbebc147a623397ce0a3aa9eea66ce3db3db957`.

Frozen travel-city Stage-B source:

- artifact ID `11046080870`;
- digest `sha256:f9908bca9f20d7726cbd27d7f3a96329a4e0bb9af0b0deda97d336b15b440192`;
- exact calls = 21 UP / 21 DOWN / 1 NO_CALL;
- threshold and sign frozen before market join.

Opened V2B market source:

- artifact ID `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`.

## Observed V2B movement

All evaluated rows:

**43**

Observed movement:

- UP = **9**;
- DOWN = **4**;
- ZERO = **30**.

The single frozen NO_CALL row had ZERO movement.

## Direction-comparable subset

Comparable means:

- frozen call is UP or DOWN; and
- observed centre_delta is non-zero.

Comparable rows:

**13**

Concordant rows:

**4**

Pooled concordance:

**4 / 13 = 30.77%**

The frozen exploratory gate required >60%.

This condition fails by a large margin.

## Constant-direction baseline

On those exact 13 comparable rows:

- observed UP = 9;
- observed DOWN = 4.

A constant-UP rule therefore scores:

**9 / 13 = 69.23%**

Frozen travel-city Stage B scores:

**4 / 13 = 30.77%**

Stage-B excess concordance over the same-subset constant-UP baseline:

**-38.46 percentage points**

## Direction discrimination

UP recall:

**3 / 9 = 33.33%**

DOWN recall:

**1 / 4 = 25.00%**

Balanced directional accuracy:

**29.17%**

Confusion among all 43 rows:

Frozen UP calls:

- observed UP = 3;
- observed DOWN = 3;
- ZERO = 15.

Frozen DOWN calls:

- observed UP = 6;
- observed DOWN = 1;
- ZERO = 14.

Frozen NO_CALL:

- observed UP = 0;
- observed DOWN = 0;
- ZERO = 1.

## Sign-alignment gate

Frozen hypothesis required:

- UP-call mean centre_delta > 0;
- DOWN-call mean centre_delta < 0.

Observed UP group:

- rows = 21;
- mean centre_delta = **+0.0536345**;
- mean joint travel = **336.96 km**.

Observed DOWN group:

- rows = 21;
- mean centre_delta = **+0.0903839**;
- mean joint travel = **1270.82 km**.

The DOWN group therefore moved **UP on average**, not DOWN.

`call_group_mean_deltas_aligned = false`

The required sign-alignment gate fails.

## By-league diagnostics

| League | Comparable | Concordant | Concordance |
| --- | ---: | ---: | ---: |
| Bundesliga | 2 | 2 | 100.0% |
| EPL | 2 | 0 | 0.0% |
| La Liga | 2 | 0 | 0.0% |
| Ligue 1 | 3 | 1 | 33.3% |
| Serie A | 4 | 1 | 25.0% |

Only **1** league has at least two comparable rows and concordance >50%.

The frozen gate required at least 3.

## Continuous relationship

Frozen travel score versus centre_delta across all 43 fixtures:

- Pearson = **+0.0045**;
- Spearman = **-0.2196**.

There is no useful monotonic or linear relationship in this opened sample.

## Final classification

`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`

The exact mapping:

`JOINT_TRAVEL_CITY_COHORT_MEDIAN_SIGN_V1`

is closed on opened V2B.

## Important interpretation

The **travel source remains useful as data infrastructure**:

- 43/43 fixtures reconstructed;
- 86/86 team-side travel-city distances available;
- source is zero-cost and point-in-time reconstructable.

But the simple hypothesis:

> lower combined travel -> UP, higher combined travel -> DOWN

does not predict individual total-corners market direction on this sample.

Source feasibility and directional value are separate conclusions.

## Binding decision

Do not:

- change the 600.464688 km threshold;
- reverse the sign because DOWN performed badly;
- switch to away-only travel;
- select only Bundesliga;
- exclude EPL / La Liga / Ligue 1 / Serie A;
- add rest or travel/rest interaction as a rescue on this opened sample;
- combine with FAIR_CENTRE post hoc;
- describe the travel source itself as a directional edge.

Any future travel-related direction test requires unseen data or a genuinely distinct
mechanism frozen independently of this opened result.

## Research implication

The latest sequence is now clear:

- full-calendar schedule source materially improves schedule reconstruction, but the simple
  joint-rest direction mapping failed;
- travel-city source is fully reconstructable, but the simple joint-travel direction
  mapping failed even more strongly.

Therefore further opened-sample threshold engineering on schedule/travel should stop.

The next literature-driven work should move to a different information family rather than
retune these same features. Strong candidates are time-aligned market-path structure or
cross-market relationships, evaluated under the same freeze-before-outcome discipline.

## Safety

- research-only;
- opened-sample hypothesis generation only;
- NO_BET;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- no promotion;
- production `.pkl` unchanged.
