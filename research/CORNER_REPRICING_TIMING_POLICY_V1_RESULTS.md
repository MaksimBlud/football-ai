# CORNER_REPRICING_TIMING_POLICY_V1_RESULTS

Status: **FINAL SECONDARY AUDIT / NOT_PORTABLE_AS_SIMPLE_WAIT_FILTER**

## Evidence boundary

This block reused already-opened market cohorts. It is not an untouched prospective replication.

The frozen FAIR_CENTRE repricing-risk predictor was fitted only on the original 55-row discovery cohort. The later 50-row, 46-row and 43-row cohorts were not used to fit the predictor or choose the existing top-25% high-risk rule.

No provider calls were made.

## Authoritative audit

Workflow run:

`36225197468`

Immutable result artifact:

- artifact ID `10900099199`;
- digest `sha256:2f3c41a393e7cfad67cc26f00bad1c5184372557244c1ae403451bb345617785`;
- size 7,724 bytes.

Training source:

**original 55 rows only**

Frozen material-move threshold:

`0.362835012901983`

Original-55 material-move prevalence:

`0.2545454545454545`

Frozen policy:

- rank the frozen FAIR_CENTRE risk probability within each league;
- top 25% per league = `WAIT`;
- remaining rows = `STABLE_OPEN`.

## Fresh 50-row replication cohort

WAIT:

- rows = 15;
- mean movement magnitude = `0.3249109562700314`;
- material moves = 8;
- material-move prevalence = **0.5333333333**;
- non-zero movement prevalence = 0.60.

STABLE_OPEN:

- rows = 35;
- mean movement magnitude = `0.09402670830058087`;
- material moves = 4;
- material-move prevalence = **0.1142857143**;
- non-zero movement prevalence = 0.3428571429.

WAIT minus STABLE_OPEN:

- mean movement magnitude = **+0.23088424797**;
- material-move prevalence = **+0.41904761905**;
- material-move risk ratio = **4.6666666667**.

This cohort is directionally consistent with the simple WAIT policy.

## V1 46-row regime-adjusted direction cohort

WAIT:

- rows = 14;
- mean movement magnitude = `0.13003621519617312`;
- material moves = 2;
- material-move prevalence = **0.1428571429**;
- non-zero movement prevalence = 0.3571428571.

STABLE_OPEN:

- rows = 32;
- mean movement magnitude = `0.15415346972079197`;
- material moves = 9;
- material-move prevalence = **0.28125**;
- non-zero movement prevalence = 0.40625.

WAIT minus STABLE_OPEN:

- mean movement magnitude = **-0.02411725452**;
- material-move prevalence = **-0.13839285714**;
- material-move risk ratio = **0.5079365079**.

This cohort reverses both required relationships.

It is therefore evidence against treating the frozen top-25% rule as a portable simple timing filter.

## V2B 43-row cohort

WAIT:

- rows = 13;
- mean movement magnitude = `0.21399814194321287`;
- material moves = 3;
- material-move prevalence = **0.2307692308**;
- non-zero movement prevalence = 0.4615384615.

STABLE_OPEN:

- rows = 30;
- mean movement magnitude = `0.07704824028074496`;
- material moves = 2;
- material-move prevalence = **0.0666666667**;
- non-zero movement prevalence = 0.2333333333.

WAIT minus STABLE_OPEN:

- mean movement magnitude = **+0.13694990166**;
- material-move prevalence = **+0.16410256410**;
- material-move risk ratio = **3.4615384615**.

This cohort is directionally consistent with the simple WAIT policy.

## Pooled descriptive view

Across all three later cohorts:

- rows = 139;
- WAIT rows = 42;
- STABLE_OPEN rows = 97.

WAIT:

- mean movement magnitude = **0.22562255243**;
- material-move prevalence = **0.3095238095**.

STABLE_OPEN:

- mean movement magnitude = **0.10861126835**;
- material-move prevalence = **0.1546391753**.

Pooled:

- WAIT minus STABLE mean movement magnitude = **+0.11701128408**;
- WAIT minus STABLE material-move prevalence = **+0.15488463427**;
- material-move risk ratio = **2.0015873016**.

The pooled descriptive effect is favorable, but it does not override the complete reversal in V1_46.

## Final classification

**`NOT_PORTABLE_AS_SIMPLE_WAIT_FILTER`**

`all_later_cohorts_directionally_consistent = false`

This classification follows the frozen descriptive portability rule: the same existing policy had to show higher mean movement magnitude and higher material-move prevalence in every later cohort.

It failed that requirement in V1_46.

## Interpretation

The previously replicated FAIR_CENTRE repricing-risk result remains valid as evidence that opening market state can carry information about future repricing magnitude.

What this secondary audit does **not** support is a simple product/execution rule:

> always wait on the top 25% FAIR_CENTRE-risk matches and treat the remaining 75% as stable.

The pooled average looks useful, but portability across windows is not good enough.

Do not:

- change the 25% cutoff using these opened cohorts;
- remove V1_46;
- weight cohorts after seeing results;
- turn the pooled risk ratio into a betting or execution claim;
- promote WAIT/STABLE_OPEN to production from this evidence.

## Safety

- research-only;
- secondary reuse of opened data;
- confirmatory replication = false;
- provider calls = 0;
- no new odds;
- no outcomes;
- no Supabase writes;
- no betting/staking;
- no production promotion;
- production `.pkl` hash guards passed.

