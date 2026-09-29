# V2B FULL-CALENDAR REST STAGE-B EVALUATOR V1 — Results

Status: **FINAL OPENED-SAMPLE HYPOTHESIS GENERATION / WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS**

## Provenance

Workflow run:

`36589336181`

Authoritative evaluator artifact:

- ID `11042867553`;
- digest `sha256:f45c216801e991d1629ecba347cc522360aa55059b142dbe6b70cf11b570810b`;
- size 3,648 bytes.

Frozen full-calendar rest Stage-B source:

- artifact `11042123742`;
- digest `sha256:5157a50d2516aa7088eb1c89a0b95e8d31a8c328a6c0b8ee4488489ee8559918`;
- fixture identity hash
  `sha256:c2891591d871b3ad8432915761f90065f6941f9055204d4d0b5327d71e4e52ea`;
- frozen feature hash
  `sha256:d876b37f9315a535a0a92ef9ff2f06e62a3c70321c96982ba6395ec7be5feec6`;
- exact frozen calls = 17 UP / 19 DOWN / 7 NO_CALL.

Opened V2B market source:

- artifact `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`.

No provider request occurred during evaluation.

## Observed V2B movement

All evaluated rows:

**43**

Observed movement:

- UP = **9**;
- DOWN = **4**;
- ZERO = **30**.

Frozen NO_CALL rows:

**7**

Among those:

- observed UP = 1;
- observed DOWN = 0;
- ZERO = 6.

NO_CALL rows are retained but excluded from directional concordance.

## Direction-comparable subset

Rows with:

- frozen call UP or DOWN; and
- non-zero observed movement.

Comparable rows:

**12**

Observed directions in that subset:

- UP = **8**;
- DOWN = **4**.

Frozen-rule concordance:

**7 / 12 = 0.5833**

The preregistered exploratory gate required:

**> 0.60**

So the pooled concordance condition failed.

## Constant-direction comparison

On the exact same 12 comparable rows:

`always UP` would score:

**8 / 12 = 0.6667**

Frozen full-calendar rest Stage B:

**7 / 12 = 0.5833**

Stage-B excess vs constant-UP:

**-0.0833**

Therefore the frozen recovery mapping underperforms the trivial majority-direction rule.

## Direction discrimination

UP recall:

**5 / 8 = 0.625**

DOWN recall:

**2 / 4 = 0.500**

Balanced directional accuracy:

**0.5625**

Confusion among all 43 rows:

Frozen UP calls:

- observed UP = 5;
- observed DOWN = 2;
- ZERO = 10.

Frozen DOWN calls:

- observed UP = 3;
- observed DOWN = 2;
- ZERO = 14.

Frozen NO_CALL:

- observed UP = 1;
- observed DOWN = 0;
- ZERO = 6.

Unlike the earlier xG/deep mappings, this signal does produce both UP and DOWN comparable
calls. But the discrimination is still not good enough.

## Call-group movement

Frozen UP calls:

- rows = 17;
- zero movement = 10;
- mean centre_delta = **+0.100342**;
- median centre_delta = 0.

Frozen DOWN calls:

- rows = 19;
- zero movement = 14;
- mean centre_delta = **+0.026434**;
- median centre_delta = 0.

Frozen NO_CALL:

- rows = 7;
- zero movement = 6;
- mean centre_delta = **+0.116620**;
- median centre_delta = 0.

The frozen DOWN group has a **positive**, not negative, mean centre_delta.

Therefore the required sign-alignment condition failed.

## By-league diagnostics

Bundesliga:

- comparable = 2;
- concordant = 2;
- concordance = **1.00**.

EPL:

- comparable = 2;
- concordant = 2;
- concordance = **1.00**.

La Liga:

- comparable = 2;
- concordant = 0;
- concordance = **0.00**.

Ligue 1:

- comparable = 3;
- concordant = 1;
- concordance = **0.3333**.

Serie A:

- comparable = 3;
- concordant = 2;
- concordance = **0.6667**.

Leagues with >=2 comparable rows and concordance >0.50:

**3**

This league-support condition passes, but it does not overcome the failed pooled
concordance and failed sign alignment.

## Continuous relationship

Frozen stage_b_score vs centre_delta across all 43 rows:

- Pearson = **+0.102621**;
- Spearman = **+0.078583**.

Both are weak.

## Final classification

**`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`**

The exact mapping:

`JOINT_FULL_REST_COHORT_MEDIAN_SIGN_V1`

is closed on opened V2B.

## Important interpretation

The **source itself remains informative as calendar data**: full-calendar reconstruction
materially corrected league-only rest/load for 27/43 fixtures.

But the specific simple direction hypothesis:

> more aggregate rest -> UP, less aggregate rest -> DOWN

does not provide useful directional discrimination on this opened V2B sample.

Source feasibility and direction value are therefore separate conclusions:

- full-calendar load source = **feasible and materially different**;
- this exact directional mapping = **not supported**.

## Binding conclusion

Do not:

- move the 11-day median;
- use league-specific medians;
- reverse the sign;
- switch to home-away rest difference on this sample;
- switch to 7d/14d counts after seeing this result;
- reassign NO_CALL;
- weight cup/UEFA competitions;
- drop La Liga or Ligue 1;
- add FAIR_CENTRE post hoc;
- describe 7/12 as a directional edge.

Any further schedule-related direction research must be a genuinely new preregistered
mechanism or use unseen data.

## Next research implication

Reliable individual corner-market direction remains unresolved.

Closed opened-sample Stage-B mappings now include:

- scalar CORNERS10 football-gap;
- SHOTS10 same-family tuning;
- result/Elo residual mapping;
- absolute true-npxG environment;
- absolute deep/deep_allowed environment;
- joint full-calendar rest mapping.

The full-calendar **source** remains available for future unseen validation or a genuinely
different preregistered mechanism, but it should not be mined further on this opened V2B
sample.

The next bounded source family should therefore be different, such as travel/venue load
with independently audited distance provenance, or genuinely point-in-time squad
availability if the external source gate changes.

## Safety

- research-only;
- opened-sample hypothesis generation only;
- NO_BET;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.
