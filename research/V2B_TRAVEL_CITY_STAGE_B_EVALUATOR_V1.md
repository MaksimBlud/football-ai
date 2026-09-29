# V2B TRAVEL-CITY STAGE-B EVALUATOR V1

Status: **FROZEN EVALUATOR / OPENED-SAMPLE HYPOTHESIS GENERATION**.

## Purpose

Evaluate the already-frozen mapping:

`JOINT_TRAVEL_CITY_COHORT_MEDIAN_SIGN_V1`

against the already-opened V2B corner-market direction rows.

This is not independent confirmation. The protection is that the travel source, feature-only
median, sign orientation, exact 43-fixture cohort and 21/21/1 calls were frozen before this
join.

## Frozen feature source

Use the feature-freeze artifact:

- artifact ID `11046080870`;
- digest `sha256:f9908bca9f20d7726cbd27d7f3a96329a4e0bb9af0b0deda97d336b15b440192`;
- fixture hash
  `sha256:a73b44ee30f216e77425f1e014391c89deacd8e02493008368aa8c74f52d4f3e`;
- frozen feature hash
  `sha256:a16154b7fac0c8b12868569fd5a5b96d48813fb8a5192480dc4dd77f3638eb18`;
- rows = 43;
- calls = 21 UP / 21 DOWN / 1 NO_CALL.

No threshold, sign or league-specific rule may change.

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

The one frozen NO_CALL row remains visible but is never reassigned.

ZERO market movements remain visible but are not direction-comparable.

## Frozen exploratory classification

Reuse the exact Stage-B consistency gate already used for opened V2B hypotheses.

`PROMISING_DIRECTION_HYPOTHESIS` only if all are true:

1. pooled concordance among non-zero comparable rows is >0.60;
2. at least 3 leagues each have >=2 comparable rows and concordance >0.50;
3. frozen UP-call rows have mean centre_delta >0;
4. frozen DOWN-call rows have mean centre_delta <0.

Otherwise:

`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`.

## Mandatory diagnostics

Report:

- all 43 rows;
- exact 21 UP / 21 DOWN / 1 NO_CALL split;
- ZERO movement rows;
- number of direction-comparable rows;
- pooled concordance;
- constant-UP / constant-DOWN majority baseline on the exact same comparable subset;
- Stage-B excess over that baseline;
- UP recall;
- DOWN recall;
- balanced directional accuracy;
- confusion matrix including ZERO and NO_CALL;
- call-group mean/median centre_delta;
- by-league concordance;
- Pearson/Spearman association between frozen score and centre_delta.

## Prohibited after evaluation

Do not:

- move the 600.464688 km median;
- reverse the sign;
- switch to away-only or max-team travel;
- add rest or travel/rest interaction;
- add league-specific thresholds;
- reassign NO_CALL;
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
