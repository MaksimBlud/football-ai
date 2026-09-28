# V2B RESULT STRENGTH TRAJECTORY EVALUATOR V1

Status: **FROZEN EVALUATION CONTRACT / OPENED-SAMPLE HYPOTHESIS GENERATION**

## Purpose

Evaluate the already-frozen Stage-B mapping:

`JOINT_PERFORMANCE_RESIDUAL_5_SIGN_V1`

against the already-opened V2B market-direction rows.

This is not a confirmatory replication because the V2B market sample was opened
before this Stage-B family was proposed. The purpose is hypothesis generation only.

## Frozen Stage-B source

Feature artifact:

- ID `10975465958`;
- digest `sha256:d30f4231e7e0a9149d0869ac6d775eac9d2182316593610f2b42637afc26dbe3`;
- exact eligible fixtures = 34;
- eligible identity hash =
  `sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1`;
- frozen calls = 16 UP / 18 DOWN / 0 NO_CALL.

The mapping may not be refit or changed in this evaluator.

## Opened market source

V2B evaluator artifact:

- ID `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`;
- complete normalized V2B rows = 43.

Only `centre_delta` and movement magnitude are used as target diagnostics after
the exact 34 frozen fixture IDs are joined.

## Frozen target definition

Observed market direction:

- `centre_delta > 0` -> UP;
- `centre_delta < 0` -> DOWN;
- `centre_delta = 0` -> ZERO.

A row is direction-comparable iff:

- frozen Stage-B call is UP or DOWN;
- observed centre movement is non-zero.

ZERO rows remain in the all-34 diagnostics and are never silently discarded.

## Frozen exploratory consistency gate

This evaluator reuses the same fixed consistency rule previously used for the
opened-sample CORNERS10 direction hypothesis.

Classification is `PROMISING_DIRECTION_HYPOTHESIS` iff all are true:

1. pooled concordance among non-zero direction-comparable rows is **> 0.60**;
2. at least **3 leagues** each have >=2 comparable rows and concordance >0.50;
3. frozen UP-call rows have mean `centre_delta > 0`;
4. frozen DOWN-call rows have mean `centre_delta < 0`.

Otherwise:

`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`.

This is an exploratory classification, not a statistical confirmation test.

## Required diagnostics

Report:

- all 34 frozen rows;
- observed UP / DOWN / ZERO counts;
- comparable and concordant rows;
- pooled concordance;
- by-league rows, zero movement, comparable rows and concordance;
- UP/DOWN group mean and median centre_delta;
- confusion matrix including ZERO;
- Pearson and Spearman association of frozen continuous Stage-B score with centre_delta.

## Explicit prohibitions

After the evaluation opens:

- do not reverse the mapping sign;
- do not fit weights to Elo/residual components;
- do not threshold Stage-B score;
- do not exclude a league;
- do not choose a Stage-A FAIR_CENTRE threshold on this same sample;
- do not combine Stage A + Stage B by searching this V2B outcome set;
- do not call the result independent confirmation.

Any Stage-A/Stage-B combined protocol must be frozen for a genuinely new unseen
market cohort.

## Safety

- research-only;
- NO_BET;
- no Odds API calls;
- no Supabase writes;
- no model training/promotion;
- production .pkl unchanged;
- no real staking.
