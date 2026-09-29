# V2B CROSS-BOOK RAW FEASIBILITY V1

Status: **SOURCE FEASIBILITY ONLY / NO DIRECTION TEST**

## Purpose

Audit the immutable raw V2B corner-odds artifact to determine whether a genuinely
cross-book market-microstructure Stage-B feature can be reconstructed without any new
provider request.

This block does not evaluate direction and does not use centre_delta.

## Immutable source

Complete raw V2B acquisition artifact:

- artifact ID `10899611444`;
- digest `sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`;
- locked raw responses = 43.

The raw artifact was acquired in the earlier controlled V2B acquisition and is already
paid for. This audit is offline-only.

## Cross-book feasibility rule

For a fixture to contain a true cross-book state, its stored raw response must contain
at least **two distinct bookmaker entries** in `data.bookmakers`.

Primary cohort feasibility requires this for all 43 locked responses.

The audit records:

- bookmaker count per fixture;
- unique bookmaker slugs and names;
- fixtures with >=2 bookmakers;
- presence of corner opening/closing/inplay structures.

It does not:

- infer missing bookmakers;
- treat opening/closing within one bookmaker as cross-book data;
- treat aggregates as independent bookmakers;
- request new odds;
- inspect direction outcome.

## Interpretation

Possible statuses:

- `FULL_43_CROSS_BOOK_FEASIBLE`;
- `PARTIAL_CROSS_BOOK_SUPPORT`;
- `INSUFFICIENT_CROSS_BOOK_DIVERSITY`.

If only one bookmaker exists in the raw artifact, the existing V2B data cannot support
a cross-book Stage-B experiment. A future cross-book experiment would require a
different source/acquisition contract frozen before outcomes.

## Safety

- research-only;
- NO_BET;
- provider requests = 0;
- no Supabase writes;
- no production model changes;
- no model promotion.
