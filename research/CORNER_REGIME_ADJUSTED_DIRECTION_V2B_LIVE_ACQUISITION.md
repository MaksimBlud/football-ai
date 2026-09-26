# CORNER_REGIME_ADJUSTED_DIRECTION_V2B_LIVE_ACQUISITION

Status: **PREREGISTERED / CONTROLLED LIVE RAW-ODDS ACQUISITION / NO EVALUATION**

## Purpose

Fetch raw corner-odds responses only for the already-locked V2B cohort.

This block is not allowed to discover fixtures, alter the cohort, normalize markets or evaluate direction.

## Immutable inputs

Lock artifact:

- workflow run: `36219786013`;
- artifact ID: `10899325930`;
- digest: `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`.

Acquisition-plan artifact:

- workflow run: `36220204953`;
- artifact ID: `10899305926`;
- digest: `sha256:8fe2203443f4e59a5800fd7315df6d333a19771e9827d3cad64ef4f658119c56`.

Frozen identities:

- `selection_sha256 = sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73`;
- `fixture_metadata_sha256 = sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb`.

## Allowed provider surface

Only:

`GET /v1/fixtures/{fixture_id}/odds?market=corner`

for fixture IDs present in the immutable acquisition plan.

Forbidden:

- fixture-list endpoints;
- league fixture discovery;
- fixture reselection;
- fixture replacement;
- backfill;
- any non-corner market request;
- outcomes lookup for evaluation;
- statistical evaluation inside the live acquisition workflow.

## Frozen batching

Batch 1:

- first 30 locked fixture IDs.

Batch 2:

- remaining 13 locked fixture IDs.

Batch membership/order comes only from immutable plan artifact `10899305926`.

No code may construct a new fixture list.

## Resume semantics

If batch 1 or batch 2 is interrupted:

- preserve every successfully captured raw response;
- later resume may request only missing fixture IDs from the same locked cohort;
- existing raw responses must be reused without re-fetch unless the file is absent/corrupt;
- no partial acquisition may be statistically evaluated.

## Raw completeness

A raw odds response counts as captured when the provider request returns a successful JSON payload for the locked fixture ID.

Structural corner-market eligibility is intentionally **not** decided here.

The frozen offline evaluator will later decide whether the captured response contains a usable opening/closing corner market.

## Expected statuses

After batch 1:

`ACQUISITION_PARTIAL`

Expected captured locked responses:

**30**

Expected missing locked responses:

**13**

After batch 2 with batch-1 resume:

`ACQUISITION_COMPLETE`

Expected captured locked responses:

**43**

Expected missing locked responses:

**0**

## Safety

- Free provider key only;
- no paid subscription upgrade;
- no fixture discovery;
- no Supabase writes;
- no production model changes;
- no normalization/evaluation during acquisition;
- production `.pkl` hash guard required;
- raw artifacts uploaded even on a partial/failing run where possible.

## Authorization mechanism

Live acquisition may run only from a same-repository PR after exact-head CI is green and only when the PR body begins with the dedicated execution marker.

The marker must be removed immediately after the live acquisition workflow has been created/started.

