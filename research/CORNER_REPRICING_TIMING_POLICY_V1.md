# CORNER_REPRICING_TIMING_POLICY_V1

Status: **SECONDARY RETROSPECTIVE PORTABILITY AUDIT / ALREADY-OPENED DATA / RESEARCH-ONLY**

## Purpose

Test one practical use of the already replicated FAIR_CENTRE repricing-risk signal:

> can the frozen FAIR_CENTRE risk ranking be used as an execution-timing filter, marking high-risk matches as WAIT and the rest as STABLE_OPEN?

This block does **not** search for repricing direction and does not make a betting claim.

## Evidence boundary

All evaluation cohorts used here have already been opened in earlier research:

1. fresh 50-row repricing replication;
2. 46-row V1 regime-adjusted direction cohort;
3. 43-row V2B regime-adjusted direction cohort.

Therefore this block is **not an untouched prospective replication**.

It is a secondary portability audit of an already-frozen risk predictor and already-frozen high-risk ranking rule.

No threshold, feature, model family or cohort may be tuned from these opened rows and then described as prospective evidence.

## Frozen training source

Fit only on the original 55-row CORNER_MARKET_STATE_REPRICING_V1 discovery cohort.

Use the already-existing frozen function:

`corner_repricing_direction_replication_v1.fit_frozen_v1_predictor`

This fixes:

- primary feature = `opening_lambda` / FAIR_CENTRE only;
- material-move threshold = q75 of original-55 movement magnitude;
- LogisticRegression C = 0.1;
- median imputation;
- standard scaling.

The three later cohorts must never be used for fitting.

## Frozen timing policy

For each evaluation cohort independently:

1. compute the frozen model `risk_probability`;
2. within each league, rank by:
   - risk_probability descending;
   - fixture_id ascending as deterministic tie-break;
3. mark the top 25% per league using `ceil(n * 0.25)` as:
   `WAIT`;
4. mark all remaining rows:
   `STABLE_OPEN`.

This is exactly the same high-risk construction already used in the fresh replication. No new percentile search is allowed.

## Frozen material-move label

A row is `material_move = 1` when:

`movement_magnitude >= original_55_q75_threshold`

The threshold must come only from the original 55-row discovery cohort.

## Reported metrics

For WAIT and STABLE_OPEN separately, report:

- rows;
- mean movement magnitude;
- median movement magnitude;
- material-move count;
- material-move prevalence;
- non-zero movement prevalence.

For each cohort report:

- WAIT minus STABLE_OPEN mean movement magnitude;
- WAIT minus STABLE_OPEN material-move prevalence;
- WAIT / STABLE_OPEN material-move risk ratio when denominator is non-zero.

Also report a pooled descriptive view across the later cohorts.

## Interpretation rule

Because the cohorts are already opened, there is no confirmatory p-value gate in this block.

Operational portability is considered **descriptively consistent** only when the same frozen WAIT rule has:

- higher mean movement magnitude than STABLE_OPEN; and
- higher material-move prevalence than STABLE_OPEN

in **every** later cohort used in the audit.

If one or more cohorts reverse either relationship, the policy is classified:

`NOT_PORTABLE_AS_SIMPLE_WAIT_FILTER`

and must not be promoted to product/betting execution logic from this evidence.

No cohort may be excluded post hoc.

## Provenance

Original discovery artifact:

- artifact `10550262038`;
- digest `sha256:92177e4ddb39331b33e9c97fc75541b0371f744f17a9dd6a2355188839960b92`.

Fresh 50-row replication artifact:

- artifact `10551727936`;
- digest `sha256:ca3c0f96338cf213e1dc76dbf47e88d01f7ad551f18e83ef2c185d4bc9eb6ba3`.

V1 46-row direction artifact:

- artifact `10557706131`;
- digest `sha256:5ff43199cdf1bb73e6b87649c3e68aa57bac628c68888a06a809c5df473b8d1f`.

V2B 43-row evaluation artifact:

- artifact `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`.

## Safety

- offline-only;
- no provider calls;
- no new odds acquisition;
- no match outcomes;
- no football-state features;
- no Supabase writes;
- no betting/staking;
- no production promotion;
- no production .pkl changes;
- no retuning after seeing the audit result.
