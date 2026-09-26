# CORNER_REGIME_ADJUSTED_DIRECTION_V2B_ACQUISITION_RESULTS

Status: **ACQUISITION_COMPLETE / 43 LOCKED FIXTURES / RAW ODDS ONLY / NOT YET EVALUATED**

## Provenance

Controlled live-acquisition PR:

- PR #416;
- merged as `5902c6fb99e34b03f97e20638ac824c25b6b6cd7`;
- final PR head `c846ec72d895b85d207cc7e452d63b0f653917a0`.

Authoritative acquisition workflow run:

`36222282829`

Source immutable cohort lock:

- run `36219786013`;
- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`.

Source deterministic acquisition plan:

- run `36220204953`;
- artifact `10899305926`;
- digest `sha256:8fe2203443f4e59a5800fd7315df6d333a19771e9827d3cad64ef4f658119c56`.

Frozen cohort identity:

- `selection_sha256 = sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73`;
- `fixture_metadata_sha256 = sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb`;
- selected fixture count = **43**;
- selected regime blocks = **10**;
- metadata potential pairs = **74**.

## Batch 1

Frozen batch size:

**30**

Result:

- status = `ACQUISITION_PARTIAL`;
- captured locked raw responses = 30;
- missing locked fixtures = 13;
- provider HTTP requests in batch 1 = 30;
- fixture discovery = false;
- normalization = false;
- statistical evaluation = false.

Immutable batch-1 artifact:

- artifact ID `10898524057`;
- digest `sha256:5a15902ea9b73cc778bd8a116010f83edf24af38973dcf45de619e4a729f0fee`;
- size 11,372 bytes.

Batch 1 was not evaluated.

## Batch 2

Frozen batch size:

**13**

Batch 2 consumed the immutable raw artifact from batch 1 as same-run resume input and requested only the 13 remaining locked fixture IDs.

Result:

- status = `ACQUISITION_COMPLETE`;
- acquisition_complete = true;
- captured locked raw responses = **43**;
- missing locked fixtures = **0**;
- provider HTTP requests in batch 2 = **13**;
- fixture discovery = false;
- normalization = false;
- statistical evaluation = false;
- match outcomes used = false;
- football-state used = false;
- paid subscription used = false.

Immutable complete raw artifact:

- artifact ID `10899611444`;
- digest `sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`;
- size 15,623 bytes;
- artifact contains 43 raw odds responses + acquisition report.

## Total provider use

Across the two frozen batches:

- batch 1 requests = 30;
- batch 2 requests = 13;
- total raw-odds requests = **43**.

There were:

- no fixture-list requests;
- no fixture discovery;
- no reselection;
- no replacement;
- no backfill;
- no normalization during acquisition;
- no direction statistic during acquisition.

Production `.pkl` before/after hash guards passed in both live jobs.

## Current interpretation

The V2B raw acquisition phase is complete.

This does **not** yet mean the direction signal is confirmed or rejected.

At this point:

- all 43 locked fixtures have raw corner-odds responses;
- no market values have been used for statistical interpretation;
- no normalized V2B evaluation rows have been inspected;
- no V2B direction verdict has been produced.

The next step must be an offline-only evaluation path that:

1. verifies this exact raw artifact digest;
2. verifies the immutable V2B lock and acquisition-plan identities;
3. normalizes the 43 locked raw responses using the already-frozen Bet365 corner normalizer;
4. never replaces structurally ineligible selected fixtures;
5. applies the unchanged V1/V2 regime-adjusted direction statistic;
6. preserves the unchanged >=40 actual comparable-pair gate;
7. produces one of the frozen final verdicts only after complete acquisition.

No additional provider odds requests are needed for the locked cohort.

