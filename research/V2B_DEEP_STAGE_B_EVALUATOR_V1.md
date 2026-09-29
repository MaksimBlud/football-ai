# V2B DEEP STAGE-B EVALUATOR V1

Status: **FROZEN EVALUATOR / OPENED-SAMPLE HYPOTHESIS GENERATION**

## Purpose

Evaluate the already-frozen territorial-depth mapping:

`POOLED_2025_DEEP_ENVIRONMENT_SIGN_V1`

against the already-opened V2B corner-market direction rows.

This is not independent confirmation. V2B market outcomes have already been opened in
earlier research. The important protection is narrower: the territorial-depth formula, baseline,
34-fixture membership and 28/6 calls were frozen before this territorial-depth-specific join.

## Frozen territorial-depth source

Use the final feature-freeze artifact generated from the final fresh-main PR #441 head:

- artifact ID `10981992759`;
- digest `sha256:48ba9a7a0097f9d3e7177a8c53eac9a0205045ae5dbe5cf93b9f1532f26a3297`;
- eligible fixture hash
  `sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1`;
- frozen feature hash
  `sha256:7d114e4fb36ef08dc9e2e7998bc4560ea1b10b28e6296743a68ca08bb073b483`;
- rows = 34;
- calls = 28 UP / 6 DOWN / 0 NO_CALL.

No mapping change is permitted.

## Opened market source

Use the already-existing V2B evaluator artifact:

- ID `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`;
- complete normalized market rows = 43.

Observed direction remains:

- centre_delta >0 -> UP;
- centre_delta <0 -> DOWN;
- centre_delta =0 -> ZERO.

ZERO rows remain in all-34 diagnostics and are excluded only from direction concordance.

## Frozen exploratory classification

Reuse the same consistency rule used by the prior CORNERS10 and result-strength
opened-sample Stage-B evaluations.

`PROMISING_DIRECTION_HYPOTHESIS` only if all are true:

1. pooled concordance among non-zero comparable rows is >0.60;
2. at least 3 leagues each have >=2 comparable rows and concordance >0.50;
3. frozen UP-call rows have mean centre_delta >0;
4. frozen DOWN-call rows have mean centre_delta <0.

Otherwise:

`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`.

## Call-imbalance diagnostics

Because the frozen deep calls are strongly imbalanced at 28 UP / 6 DOWN, raw hit rate
must not be interpreted alone.

The evaluator must additionally report, for context:

- observed UP/DOWN balance among non-zero movers;
- concordance of the constant majority-direction rule;
- Stage-B excess concordance over that constant rule;
- UP recall and DOWN recall;
- balanced direction accuracy;
- whether every comparable Stage-B call has the same sign.

These diagnostics do not replace or retune the frozen classification gate.

## Required diagnostics

Also report:

- all 34 frozen rows;
- ZERO movement count;
- call-group mean/median centre_delta;
- by-league concordance;
- confusion matrix including ZERO;
- Pearson/Spearman association of frozen Stage-B score with centre_delta.

## Prohibited after evaluation

Do not:

- move the 12.8561643836 baseline;
- use league-specific baselines;
- reverse the sign;
- switch to PPDA or fit tactical weights;
- change the five-match horizon;
- select a Stage-A threshold from the same V2B outcomes;
- exclude a league;
- call a result confirmation.

## Safety

- research-only;
- NO_BET;
- zero Odds API requests;
- no Supabase writes;
- no model training/promotion;
- production `.pkl` unchanged.
