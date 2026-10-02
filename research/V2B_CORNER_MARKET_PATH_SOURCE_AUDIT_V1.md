# V2B CORNER MARKET-PATH SOURCE AUDIT V1

Status: **SOURCE FEASIBILITY ONLY / NO DIRECTION TEST**

## Purpose

Determine whether the already-paid immutable V2B raw corner-odds artifact contains enough
temporal structure to support a genuine pre-move market-path Stage B.

This block does not evaluate direction and does not compute opening-to-closing movement.

## Immutable source

Raw V2B acquisition artifact:

- artifact ID `10899611444`;
- digest `sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`;
- 43 locked raw responses.

No new provider request is permitted.

## What counts as a usable time-aligned path

A true path requires repeated market observations with explicit observation time, so that
features can be restricted to information available before a frozen decision time.

Named endpoints such as `opening`, `closing`, and `inplay` are not enough by
themselves when they have no timestamps or intermediate history.

In particular:

- `closing` is future information relative to an earlier pre-move decision;
- `inplay` is post-kickoff information;
- neither may be repurposed as a pre-move path feature.

## Structural audit

For every one of the 43 raw responses report:

- bookmaker count and identity;
- presence of `corner_line`;
- presence of named `opening / closing / inplay` states;
- any timestamp/date/update fields anywhere in the payload;
- any history/snapshot/timeline/sequence fields anywhere in the payload.

Also report whether multiple bookmakers exist, because cross-book microstructure requires
more than one bookmaker in the same fixture payload.

## Success semantics

`TIME_ALIGNED_PATH_SOURCE_PRESENT` requires temporal/history structure in every locked
payload.

Otherwise:

`NO_TIME_ALIGNED_PATH_SOURCE`.

This is a source conclusion, not a statement about whether market-path signals work in
general.

## Safety

- research-only;
- source-feasibility only;
- no direction statistic;
- no opening/closing delta;
- no target outcomes;
- zero provider calls;
- no Supabase writes;
- no production model changes.
