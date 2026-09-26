# CORNER_REGIME_ADJUSTED_DIRECTION_V2B_RESULTS

Status: **FINAL / STATISTICAL SAMPLE GATE PASSED / INDIVIDUAL DIRECTION DISCRIMINATION NOT CONFIRMED**

## Experiment identity

Experiment:

`CORNER_REGIME_ADJUSTED_DIRECTION_V2B`

Evaluator:

`CORNER_REGIME_ADJUSTED_DIRECTION_V2B_EVALUATOR`

V2B was created after fixture-metadata availability was observed but **before any V2B corner odds were opened**.

The operational metadata stopping rule was revised from historical V2:

- V2 historical pooled gate: 12 blocks / 80 metadata potential pairs;
- V2B pooled gate: **10 blocks / 74 metadata potential pairs**.

This methodological caveat is binding:

> V2B must not be described as a fully untouched prospective replication of the original V2 12/80 stopping rule.

However, before any V2B odds access:

- the exact 43-fixture cohort was frozen;
- exact fixture metadata was frozen;
- immutable selection hashes were computed;
- the acquisition plan was frozen;
- the statistical direction test remained unchanged from V1/V2.

## Frozen statistical contract

Unchanged direction score:

`-opening_lambda` / `-FAIR_CENTRE`

Regime block:

`(league, UTC kickoff date)`

Statistic:

- unordered within-block pairs;
- tied score/delta pairs omitted;
- concordant when score difference and `centre_delta` difference have the same sign.

Frozen sample gate:

- >=30 eligible normalized rows;
- >=4 leagues with comparable pairs;
- >=8 contributing regime blocks;
- >=40 actual comparable pairs.

Frozen confirmation gate:

- sample gate passes;
- observed concordance >=0.60;
- one-sided regime-preserving permutation p <0.10;
- 20,000 permutations;
- RNG seed `20260918`.

No threshold, sign, feature, regime definition or permutation setting was changed after V2B market data were opened.

## Immutable cohort provenance

Source metadata run:

`36218898253`

Source metadata artifact:

- ID `10898297066`;
- digest `sha256:eb163d097dc2713b8f8f03370eacead91a15d3a38c0757e48b301d82e799446c`.

Immutable V2B cohort lock:

- run `36219786013`;
- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`.

Frozen cohort:

- selected regime blocks = **10**;
- selected fixtures = **43**;
- metadata potential pairs = **74**;
- 2 selected blocks in each of all five leagues.

Immutable hashes:

- `selection_sha256 = sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73`;
- `fixture_metadata_sha256 = sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb`.

## Immutable acquisition-plan provenance

Offline acquisition-plan run:

`36220204953`

Artifact:

- ID `10899305926`;
- digest `sha256:8fe2203443f4e59a5800fd7315df6d333a19771e9827d3cad64ef4f658119c56`.

Frozen batching:

- batch 1 = 30 fixture IDs;
- batch 2 = 13 fixture IDs;
- total planned raw-odds requests = 43;
- no fixture discovery;
- no reselection;
- no replacement;
- no backfill.

## Raw acquisition provenance

Authoritative acquisition run:

`36222282829`

Batch 1 raw artifact:

- ID `10898524057`;
- digest `sha256:5a15902ea9b73cc778bd8a116010f83edf24af38973dcf45de619e4a729f0fee`;
- 30 locked raw responses;
- status `ACQUISITION_PARTIAL`;
- no normalization or evaluation.

Complete raw artifact after batch 2:

- ID `10899611444`;
- digest `sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`;
- captured locked raw responses = **43 / 43**;
- missing locked responses = **0**;
- total provider odds requests = **43 = 30 + 13**;
- no statistical evaluation during acquisition.

## First evaluator execution attempt — plumbing failure only

First evaluator workflow attempt:

`36222975287`

Artifact:

- ID `10899821631`;
- digest `sha256:ae0f6e2b88cd5df211699c56d9c513539cac2999915b60e87d78c74c189a5f1c`.

The immutable lock, plan and raw artifact digests all verified successfully.

However, the inherited raw-artifact loader required archive names containing:

`/raw/odds/`

while the GitHub artifact stored files at archive root as:

`raw/odds/<fixture_id>.json`

Therefore the loader reported:

- captured raw responses = 0;
- missing locked responses = 43;
- status = `ACQUISITION_INCOMPLETE`;
- statistical evaluation performed = false;
- verdict = null.

This run is **not a statistical result**.

No market normalization, FAIR_CENTRE reconstruction, concordance calculation or permutation test occurred.

The only allowed amendment was then made:

- normalize archive member paths with a synthetic leading slash;
- add regression coverage for root-level `raw/odds/<id>.json`;
- leave all statistical/sample rules unchanged.

The path amendment was committed before the second evaluation execution.

## Authoritative V2B evaluation

Authoritative successful evaluation workflow run:

`36223204711`

Immutable result artifact:

- ID `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`;
- size 4,120 bytes.

Evaluation completeness:

- locked fixtures = **43**;
- captured raw responses = **43**;
- eligible normalized rows = **43**;
- ineligible selected fixture IDs = **0**;
- missing locked fixture IDs = **0**.

Rows by league:

- EPL = 9;
- La Liga = 9;
- Serie A = 9;
- Bundesliga = 8;
- Ligue 1 = 8.

Statistical structure:

- contributing leagues = **5**;
- contributing regime blocks = **9**;
- actual comparable pairs = **42**;
- concordant pairs = **25**.

Therefore the frozen sample gate **passed**:

- eligible rows 43 >= 30;
- leagues 5 >= 4;
- contributing blocks 9 >= 8;
- actual comparable pairs 42 >= 40.

Observed concordance:

`25 / 42 = 0.5952380952380952`

Frozen concordance threshold:

`>= 0.60`

Permutation test:

- permutations = 20,000;
- seed = `20260918`;
- one-sided p-value = **0.207939603019849**.

Frozen p-value threshold:

`< 0.10`

## Final verdict

**`INDIVIDUAL_DIRECTION_DISCRIMINATION_NOT_CONFIRMED`**

`direction_discrimination_confirmed = false`

This is not a `SAMPLE_TOO_SMALL` result.

The actual comparable-pair sample gate passed.

The individual direction hypothesis was not confirmed because:

1. observed concordance was **0.595238**, slightly below the frozen 0.60 threshold;
2. permutation p-value was **0.207940**, materially above the frozen 0.10 threshold.

## League diagnostics

These are diagnostics only and do not replace the pooled frozen test.

- Bundesliga: 5 / 7 concordant = **0.7143**;
- EPL: 0 / 7 concordant = **0.0000**;
- La Liga: 6 / 7 concordant = **0.8571**;
- Ligue 1: 6 / 9 concordant = **0.6667**;
- Serie A: 8 / 12 concordant = **0.6667**.

The large cross-league heterogeneity, especially EPL, is descriptive and must not be used for post-hoc league exclusion or threshold tuning on this opened sample.

## Movement diagnostics

Across 43 eligible rows:

- positive centre movement = 9;
- negative centre movement = 4;
- zero centre movement = 30;
- positive share among non-zero moves = **0.6923076923**.

Regime-adjusted score diagnostic:

- top-score mean = `0.1254125270951466`;
- bottom-score mean = `-0.021595804500027557`;
- top-minus-bottom = `0.14700833159517418`.

These are diagnostics only.

They do not overturn the frozen direction verdict.

## Binding interpretation

The V2B result provides a sufficiently large actual within-regime comparison sample to test the frozen individual direction hypothesis.

That hypothesis was **not confirmed**.

Do not:

- lower the 0.60 concordance threshold;
- raise the 0.10 p-value threshold;
- reverse the sign;
- exclude EPL post hoc;
- select only leagues with favorable concordance;
- change regime definitions using this opened sample;
- rerun a tuned version and call it replication.

The separately replicated corner **repricing magnitude/risk** result via `FAIR_CENTRE` remains valid and is not contradicted by this direction result.

Current evidence therefore supports the distinction:

> FAIR_CENTRE contains replicated information about **whether a material repricing is more likely**, but V2B does not confirm that FAIR_CENTRE reliably identifies **which direction the repricing will take after controlling league-day regime**.

## Safety

- research-only;
- no match outcomes used;
- no football-state/CORNERS10 features;
- no betting/staking enabled;
- no production promotion;
- no Supabase writes;
- production `.pkl` hash guards passed;
- no additional provider requests were made during evaluation.

