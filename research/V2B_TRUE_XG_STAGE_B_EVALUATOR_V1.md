# V2B TRUE XG STAGE-B EVALUATOR V1

Status: **FROZEN EVALUATOR / OPENED-SAMPLE HYPOTHESIS GENERATION**

## Purpose

Evaluate the already-frozen true-xG mapping:

`POOLED_2025_NPXG_ENVIRONMENT_SIGN_V1`

against the already-opened V2B corner-market direction rows.

This is not independent confirmation. V2B market outcomes have already been opened in
earlier research. The important protection is narrower: the true-xG formula, baseline,
34-fixture membership and 30/4 calls were frozen before this true-xG-specific join.

## Frozen true-xG source

Use the final feature-freeze artifact generated from the final PR #436 head:

- artifact ID `10979252403`;
- digest `sha256:b5372b78a0d78b20cb921a79cf1a0e4e82211f8cc70cfe9b396cb0e11689b880`;
- eligible fixture hash
  `sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1`;
- frozen feature hash
  `sha256:f4128f41a541788a4690bd8f1065cef468622494fe56de2a561a4ba07b59b0a5`;
- rows = 34;
- calls = 30 UP / 4 DOWN / 0 NO_CALL.

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

Because the frozen xG calls are strongly imbalanced at 30 UP / 4 DOWN, raw hit rate
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

- move the 2.8041087623 baseline;
- use league-specific baselines;
- reverse the sign;
- tune xG/npxG weights;
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
