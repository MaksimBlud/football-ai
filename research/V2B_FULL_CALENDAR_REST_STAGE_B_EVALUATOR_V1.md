# V2B FULL-CALENDAR REST STAGE-B EVALUATOR V1

Status: **FROZEN EVALUATOR / OPENED-SAMPLE HYPOTHESIS GENERATION**

## Purpose

Evaluate the already-frozen mapping:

`JOINT_FULL_REST_COHORT_MEDIAN_SIGN_V1`

against the already-opened V2B corner-market direction rows.

This is not independent confirmation. The market sample was opened earlier. The
protection is that the full-calendar source, 11-day feature-only median, sign orientation,
43-fixture cohort and exact 17/19/7 calls were frozen before this join.

## Frozen feature source

Use the final feature-freeze artifact:

- artifact ID `11042123742`;
- digest `sha256:5157a50d2516aa7088eb1c89a0b95e8d31a8c328a6c0b8ee4488489ee8559918`;
- fixture identity hash
  `sha256:c2891591d871b3ad8432915761f90065f6941f9055204d4d0b5327d71e4e52ea`;
- frozen feature hash
  `sha256:d876b37f9315a535a0a92ef9ff2f06e62a3c70321c96982ba6395ec7be5feec6`;
- rows = 43;
- calls = 17 UP / 19 DOWN / 7 NO_CALL.

No feature, threshold, sign or league-specific rule may change.

## Opened market source

Use the already-existing normalized V2B market artifact:

- artifact ID `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`;
- market rows = 43.

Observed direction:

- centre_delta > 0 -> UP;
- centre_delta < 0 -> DOWN;
- centre_delta = 0 -> ZERO.

## Comparable subset

All 43 feature rows remain in diagnostics.

Directional concordance uses only rows where:

- frozen call is UP or DOWN; and
- observed centre_delta is non-zero.

The seven frozen NO_CALL rows remain visible but are never reassigned.

ZERO market movements also remain visible but are not direction-comparable.

## Frozen exploratory classification

Reuse the exact Stage-B consistency gate used by earlier opened-sample hypotheses.

`PROMISING_DIRECTION_HYPOTHESIS` only if all are true:

1. pooled concordance among non-zero comparable rows is >0.60;
2. at least 3 leagues each have >=2 comparable rows and concordance >0.50;
3. frozen UP-call rows have mean centre_delta >0;
4. frozen DOWN-call rows have mean centre_delta <0.

Otherwise:

`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`.

## Mandatory diagnostics

Because this mapping has both signs and NO_CALL, report:

- all 43 rows;
- exact 17/19/7 call distribution;
- ZERO movement rows;
- number of direction-comparable rows;
- raw concordance;
- constant-UP / constant-DOWN context via the majority-direction baseline on the exact
  same comparable subset;
- Stage-B excess over that constant rule;
- UP recall;
- DOWN recall;
- balanced direction accuracy;
- confusion matrix including ZERO and NO_CALL;
- call-group mean/median centre_delta;
- by-league concordance;
- Pearson/Spearman association between frozen score and centre_delta.

## Prohibited after evaluation

Do not:

- move the 11-day median threshold;
- use league-specific medians;
- reverse the sign;
- switch to home-away rest difference;
- switch to 7d/14d count features;
- reassign NO_CALL;
- weight competitions;
- add travel;
- add FAIR_CENTRE;
- exclude a league;
- call this independent confirmation.

## Safety

- research-only;
- NO_BET;
- zero Odds API requests;
- no Supabase writes;
- no model training/promotion;
- production `.pkl` unchanged.
