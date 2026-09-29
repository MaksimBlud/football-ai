# V2B DEEP STAGE-B EVALUATOR V1 — Results

Status: **FINAL OPENED-SAMPLE HYPOTHESIS GENERATION / WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS**

## Provenance

Workflow run:

`36579933258`

Authoritative evaluator artifact:

- ID `11039795640`;
- digest `sha256:6bb5aa4131189a518b3e57a2878c615d67a2afe0e75ceb1d4c57975d6ee382f3`;
- size 3,825 bytes.

Frozen territorial-depth Stage-B source:

- artifact `10981992759`;
- digest `sha256:48ba9a7a0097f9d3e7177a8c53eac9a0205045ae5dbe5cf93b9f1532f26a3297`;
- eligible fixture hash
  `sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1`;
- frozen feature hash
  `sha256:7d114e4fb36ef08dc9e2e7998bc4560ea1b10b28e6296743a68ca08bb073b483`;
- frozen calls = 28 UP / 6 DOWN / 0 NO_CALL.

Opened V2B market source:

- artifact `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`.

No provider request occurred during evaluation.

## Observed V2B movement

Evaluated rows:

**34**

Observed movement:

- UP = **7**;
- DOWN = **3**;
- ZERO = **24**.

Direction-comparable rows:

**10**

## Frozen-rule direction result

Concordant:

**6 / 10 = 0.60**

The frozen exploratory rule required:

**> 0.60**

Therefore the pooled concordance condition failed.

## Comparison with trivial constant direction

Among the 10 non-zero movers:

- observed UP = 7;
- observed DOWN = 3.

A constant rule:

`always UP`

would achieve:

**7 / 10 = 0.70**

The frozen deep Stage-B achieved:

**6 / 10 = 0.60**

Excess concordance vs constant-UP:

**-0.10**

Therefore this mapping is not merely non-superior to the trivial direction baseline;
it is worse on the opened V2B comparable rows.

## Direction discrimination

UP recall:

**6 / 7 = 0.8571**

DOWN recall:

**0 / 3 = 0.0000**

Balanced directional accuracy:

**0.4286**

Frozen DOWN calls among all 34 rows:

- observed DOWN = 0;
- observed UP = 1;
- observed ZERO = 5.

So none of the actual DOWN market movements were identified as DOWN.

## Call-group centre movement

Frozen UP calls:

- rows = 28;
- zero movement = 19;
- mean centre_delta = **+0.078142**;
- median centre_delta = 0.

Frozen DOWN calls:

- rows = 6;
- zero movement = 5;
- mean centre_delta = **+0.136056**;
- median centre_delta = 0.

The DOWN group moved **upward** on average, so the frozen sign-group condition failed.

## By-league diagnostics

- Bundesliga: 2/2 = **1.00**;
- EPL: 0/2 = **0.00**;
- La Liga: 2/2 = **1.00**;
- Ligue 1: 0/1 = **0.00**;
- Serie A: 2/3 = **0.6667**.

Leagues with >=2 comparable rows and concordance >0.50:

**3**

This league-support condition passes, but it does not overcome the failed pooled
concordance, zero DOWN recall, positive DOWN-group mean movement, or underperformance
versus always-UP.

## Continuous relationship

Frozen deep Stage-B score vs centre_delta:

- Pearson = **-0.005102**;
- Spearman = **+0.100145**.

There is effectively no useful continuous linear relationship and only a very weak
rank association.

## Final classification

**`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`**

The exact mapping:

`POOLED_2025_DEEP_ENVIRONMENT_SIGN_V1`

is closed on V2B.

## Binding conclusion

Do not:

- move the 12.8561643836 pooled baseline;
- switch to PPDA after seeing this result;
- reverse the sign;
- fit deep/PPDA weights;
- change the five-match horizon;
- remove unfavorable leagues;
- add a post-hoc FAIR_CENTRE threshold;
- describe 6/10 as a usable directional edge.

The deep/deep_allowed information family may contain football-state information, but
this simple absolute territorial-environment mapping does **not** provide useful corner
market direction discrimination.

## Research implication

Reliable individual corner-market direction remains unresolved.

The following opened-sample Stage-B mappings are now closed:

- scalar CORNERS10 football-gap;
- result/Elo residual mapping;
- absolute true-npxG environment mapping;
- absolute deep/deep_allowed environment mapping.

SHOTS10 same-family retuning was already closed.

The next direction research should not be another threshold or algebraic transformation
of these same opened football-state families.

Priority should shift to a genuinely different source dimension, especially:

1. cross-book / market microstructure already present in immutable raw V2B responses,
   if available at the same timestamp;
2. full-calendar competition load / travel, including cup and European fixtures;
3. genuinely point-in-time squad availability if a first-seen source becomes available.

Any new source should pass a source/time-provenance audit before a direction mapping is
defined.

## Safety

- research-only;
- opened-sample hypothesis generation only;
- NO_BET;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.
