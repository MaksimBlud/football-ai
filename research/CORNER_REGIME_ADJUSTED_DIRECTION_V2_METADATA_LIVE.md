# CORNER_REGIME_ADJUSTED_DIRECTION_V2_METADATA_LIVE

Status: **PREREGISTERED / METADATA-ONLY LIVE INVENTORY CHECK / NO ODDS**

## Purpose

Operationalize the already-merged `CORNER_REGIME_ADJUSTED_DIRECTION_V2` cohort planner against the live Free provider fixture inventory without opening any V2 corner market.

This step answers only:

> has enough future fixture metadata accumulated to produce the frozen V2 `COHORT_LOCKED` selection?

It does **not** evaluate FAIR_CENTRE, opening/closing odds, centre_delta, concordance, permutation p-value or match outcomes.

## Frozen source and cutoff

Source:
- 5DollarFootballAPI fixture-list endpoint only.

Leagues:
- EPL;
- La Liga;
- Serie A;
- Bundesliga;
- Ligue 1.

Future cutoff remains exactly:

`2026-09-19T00:00:00Z`

The already-merged V2 metadata planner and lock gate remain unchanged.

## Prior-fixture exclusion

Before planning, exclude every fixture ID from:

1. original 55-row corner repricing discovery sample;
2. fresh 50-row repricing replication;
3. final 46-row regime-adjusted direction V1 sample.

Expected total excluded fixture IDs:

`55 + 50 + 46 = 151`

The runner must fail closed if these counts or uniqueness assumptions do not hold.

## Provider request boundary

Allowed endpoint shape only:

`/v1/leagues/{league_id}/fixtures`

Forbidden:
- any `/odds` endpoint;
- any match result/outcome endpoint;
- any Supabase write;
- any paid subscription or provider-plan change.

Frozen request cap:

- maximum **2 fixture-list pages per league**;
- maximum **10 provider HTTP attempts pooled**.

Page size remains 50.

The runner should stop paging a league when:
- provider pagination says `has_more=false`; or
- the current descending-time page already reaches fixtures before the V2 future cutoff, because later pages cannot add eligible V2 fixtures.

No odds request is allowed regardless of planner result.

## Frozen outputs

Persist:
- raw fixture-list responses;
- excluded fixture ID counts;
- normalized future fixture metadata;
- V2 `cohort_plan.json`.

Allowed planner status:
- `WAIT_FOR_COHORT`;
- `COHORT_LOCKED`.

If `WAIT_FOR_COHORT`:
- no additional live action is authorized;
- do not loosen the lock gate;
- future metadata checks may be repeated later using the same contract.

If `COHORT_LOCKED`:
- the exact selected block membership and fixture IDs become the candidate immutable V2 cohort;
- this metadata artifact must be reviewed/recorded before a separate odds-acquisition PR is allowed;
- odds acquisition remains unauthorized by this workflow.

## Workflow safety

Live metadata execution must be:
- manual `workflow_dispatch` only;
- repository-owned workflow;
- using the existing secret `FIVE_DOLLAR_FOOTBALL_API_KEY`;
- no key logging;
- production `.pkl` hashes checked before/after;
- artifact uploaded even for `WAIT_FOR_COHORT`.

No automatic schedule is added.


### Pre-live trigger amendment

The connected GitHub tool available in this chat does not expose a `workflow_dispatch` action.

Before the first live metadata request, the execution trigger is therefore expanded without changing the provider/data contract:

- keep manual `workflow_dispatch` support;
- additionally allow one explicit same-repository pull-request marker:
  `[run-v2-metadata]`;
- the marker may be added only after the exact PR head has passed the dedicated offline contract and all required repository validations;
- only the repository's own PR head may receive secrets;
- editing a PR without the marker must not start the live metadata job;
- the marker must be removed immediately after the authorized live run starts so later PR events cannot repeat it accidentally.

This trigger amendment changes **only how the metadata-only workflow is started**. It does not change:
- endpoint allow-list;
- 10-request cap;
- cutoff;
- 151-ID exclusion;
- V2 cohort lock;
- statistical gates;
- prohibition on odds access.


## Interpretation

This live metadata check cannot produce a direction result.

A `COHORT_LOCKED` status means only that the future fixture structure satisfies:
- all five leagues;
- >=2 metadata blocks per league;
- >=12 blocks pooled;
- >=80 metadata potential pairs.

The unchanged statistical confirmation gate is still applied only after a later separately authorized odds-acquisition/evaluation stage.

## Safety

- research-only;
- metadata-only;
- Free provider only;
- no odds;
- no outcomes;
- no betting;
- no production promotion;
- no production `.pkl` changes;
- no Supabase writes;
- no automatic live collection.
