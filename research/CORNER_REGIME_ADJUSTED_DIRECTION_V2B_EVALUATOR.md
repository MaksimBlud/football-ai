# CORNER_REGIME_ADJUSTED_DIRECTION_V2B_EVALUATOR

Status: **PREREGISTERED AFTER RAW ACQUISITION / BEFORE NORMALIZATION OR STATISTICAL EVALUATION**

## Purpose

This document freezes the V2B offline evaluation adapter after the exact 43-fixture raw odds artifact has been acquired but before those raw market values are normalized or used to compute any direction statistic.

The statistical method is not redesigned here.

V2B inherits the already-frozen V1/V2 evaluator contract exactly. This adapter exists only because V2B uses different immutable lock/acquisition-plan experiment IDs and provenance artifacts.

## Frozen raw acquisition provenance

Complete raw acquisition workflow run:

`36222282829`

Complete raw artifact:

`10899611444`

Digest:

`sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`

Locked raw responses:

**43 / 43**

Missing locked raw responses:

**0**

No statistical evaluation was performed during acquisition.

## Frozen lock provenance

Immutable V2B cohort lock:

- run `36219786013`;
- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`.

Frozen cohort identity:

- selected fixtures = 43;
- selected blocks = 10;
- metadata potential pairs = 74;
- `selection_sha256 = sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73`;
- `fixture_metadata_sha256 = sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb`.

## Frozen acquisition-plan provenance

Deterministic acquisition plan:

- run `36220204953`;
- artifact `10899305926`;
- digest `sha256:8fe2203443f4e59a5800fd7315df6d333a19771e9827d3cad64ef4f658119c56`.

Frozen batching:

- batch 1 = 30;
- batch 2 = 13;
- total = 43.

## Adapter boundary

The V2B evaluator may only:

1. verify the exact immutable V2B lock;
2. verify the exact immutable V2B acquisition plan;
3. verify the exact complete raw acquisition artifact digest;
4. confirm one raw response exists for every locked fixture ID;
5. reuse the already-existing Bet365 corner normalizer;
6. reuse the already-existing V1/V2 regime-adjusted direction evaluator unchanged;
7. persist normalized evaluation rows and the final report.

It may not:

- fetch any provider data;
- discover fixtures;
- replace/backfill an ineligible selected fixture;
- change the score sign;
- change the regime definition;
- search thresholds;
- inspect match outcomes;
- use football-state/CORNERS10;
- alter the sample after normalization;
- run any alternative statistical test as a substitute for the frozen one.

## Frozen market normalization

For every locked fixture with a structurally valid captured market:

- use the existing full-time Bet365 corner normalizer;
- proportional de-vig;
- integer/half-integer line handling already implemented in V1;
- Poisson-implied opening market centre;
- Poisson-implied closing market centre;
- `FAIR_CENTRE = opening_lambda`;
- `centre_delta = closing_lambda - opening_lambda`.

If a locked fixture cannot produce a structurally valid normalized row:

- mark it ineligible;
- do not replace it;
- do not backfill it;
- keep the original locked cohort identity in the report.

## Frozen direction statistic

Use exactly:

- direction score = `-opening_lambda`;
- regime block = `(league, UTC kickoff date)`;
- unordered within-block pairs;
- tied scores/deltas omitted;
- concordant when score and centre-delta differences have the same sign;
- 20,000 regime-preserving permutations;
- RNG seed `20260918`.

## Frozen statistical sample gate

The evaluator must require:

- >=30 eligible normalized rows;
- >=4 leagues with comparable pairs;
- >=8 contributing regime blocks;
- >=40 actual comparable pairs.

If that gate fails, verdict:

`SAMPLE_TOO_SMALL`

and the hypothesis must not be called confirmed.

## Frozen confirmation gate

Only if the sample gate passes:

- observed concordance >=0.60;
- one-sided permutation p <0.10.

Allowed final verdicts:

- `INDIVIDUAL_DIRECTION_DISCRIMINATION_REPLICATED`;
- `INDIVIDUAL_DIRECTION_DISCRIMINATION_NOT_CONFIRMED`;
- `SAMPLE_TOO_SMALL`.

## Important methodological note

The V2B operational metadata gate (10 blocks / 74 potential pairs) was revised after metadata availability was observed but before V2B odds were opened.

Therefore V2B must not be described as a fully untouched prospective replication of the original 12/80 metadata stopping rule.

However:

- the exact 43-fixture cohort was frozen before odds access;
- raw odds acquisition is now complete;
- the statistical direction gate itself remains unchanged from V1/V2;
- no normalized V2B market values or direction statistics had been inspected when this evaluator adapter was preregistered.

## Safety

- offline-only evaluation;
- no provider HTTP;
- no paid action;
- no match outcomes;
- no football-state features;
- no betting/staking;
- no production promotion;
- production `.pkl` hash guard required;
- no post-result retuning.

## Evaluation plumbing amendment after first execution attempt

Authoritative evaluator workflow attempt:

`36222975287`

The raw artifact digest verification succeeded, but the evaluator reported:

- captured raw responses = 0;
- missing locked responses = 43;
- status = `ACQUISITION_INCOMPLETE`;
- statistical_evaluation_performed = false;
- verdict = null.

Therefore this attempt did **not** normalize any market row and did **not** run the direction statistic.

Root cause was confirmed without inspecting market values:

the GitHub artifact ZIP stores captured files as:

`raw/odds/<fixture_id>.json`

while the inherited V2 loader only recognized archive names containing:

`/raw/odds/`

with a preceding path component.

The acquisition resume loader already normalizes archive member names with a synthetic leading slash, so the evaluator loader must use the same path-normalization rule.

Allowed fix before re-evaluation:

- normalize ZIP member names as `"/" + name.lstrip("/")`;
- keep the same `/raw/odds/` semantic match;
- add a regression test for root-level `raw/odds/<id>.json` artifact layout.

Forbidden changes remain:

- no normalizer change;
- no fixture change;
- no gate change;
- no score/sign change;
- no regime change;
- no permutation change;
- no result-dependent tuning.


