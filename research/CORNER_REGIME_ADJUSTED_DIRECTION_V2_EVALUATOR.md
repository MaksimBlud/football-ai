# CORNER_REGIME_ADJUSTED_DIRECTION_V2_EVALUATOR

Status: **PREREGISTERED / OFFLINE-ONLY FROZEN EVALUATOR / NO LIVE ACQUISITION**

## Purpose

Prepare the deterministic offline evaluator for the future V2 locked cohort.

This block does not fetch provider data and cannot open market prices itself.

It answers only after acquisition is complete:

> given the exact immutable V2 cohort lock, the exact offline acquisition plan, and one raw odds response for every locked fixture ID, what is the frozen V1/V2 regime-adjusted direction verdict?

## Required inputs

1. immutable V2 cohort lock manifest;
2. deterministic V2 offline odds-acquisition plan generated from that lock;
3. immutable raw-odds artifact containing exactly one raw odds JSON response for every locked fixture ID.

The evaluator must reject any lock/acquisition-plan mismatch.

## Acquisition completeness gate

Before any market normalization or direction statistic is allowed:

- enumerate exact locked fixture IDs;
- enumerate raw odds files in the acquisition artifact;
- reject duplicate raw files;
- reject raw odds files for non-locked fixture IDs;
- require one raw odds file for every locked fixture ID.

If any locked fixture raw response is missing:

`ACQUISITION_INCOMPLETE`

In that state:

- do not call the corner market normalizer;
- do not reconstruct FAIR_CENTRE;
- do not calculate centre_delta;
- do not calculate concordance;
- do not run permutations;
- do not produce a direction verdict.

This prevents a partial provider run from silently becoming a smaller post-hoc evaluation sample.

## Market normalization

Only after raw acquisition is complete:

- use the existing 5Dollar Bet365 full-time corner normalizer;
- use exact `selected_fixture_metadata` from the immutable lock;
- keep every locked fixture selected;
- a selected fixture whose captured raw response lacks a structurally valid Bet365 opening+closing full-time corner market may become ineligible at normalization;
- do not replace or backfill an ineligible selected fixture.

Use unchanged V1 representation:

- proportional de-vig;
- integer/half-integer corner lines only;
- Poisson-implied opening and closing market centre;
- `FAIR_CENTRE = opening_lambda`;
- `centre_delta = closing_lambda - opening_lambda`.

No outcomes or football-state features are allowed.

## Frozen direction evaluation

Use exactly the already-merged V1 regime-adjusted evaluator:

- direction score = `-opening_lambda`;
- regime block = league + UTC kickoff date;
- within-block unordered pairwise concordance;
- ties omitted;
- 20,000 regime-preserving permutations;
- RNG seed `20260918`.

Statistical sample gate remains:

- >=30 eligible normalized rows;
- >=4 leagues with comparable pairs;
- >=8 contributing regime blocks;
- >=40 actual comparable pairs.

Confirmation gate remains:

- sample gate passes;
- observed concordance >=0.60;
- one-sided permutation p <0.10.

Allowed final direction verdicts after complete acquisition:

- `INDIVIDUAL_DIRECTION_DISCRIMINATION_REPLICATED`;
- `INDIVIDUAL_DIRECTION_DISCRIMINATION_NOT_CONFIRMED`;
- `SAMPLE_TOO_SMALL`.

No other threshold or metric may replace the frozen gate.

## Output

If acquisition is incomplete, output a report with:

- `status = ACQUISITION_INCOMPLETE`;
- missing locked fixture IDs;
- captured locked raw-response count;
- `statistical_evaluation_performed = false`.

If acquisition is complete, output:

- source lock/acquisition identities;
- raw artifact provenance;
- locked fixture count;
- raw response count;
- eligible normalized row count;
- ineligible selected fixture IDs;
- frozen regime-adjusted direction report;
- final frozen verdict;
- `statistical_evaluation_performed = true`.

Persist normalized evaluation rows separately from the raw odds artifact.

## Safety

- research-only;
- offline-only;
- no provider HTTP transport;
- no odds endpoint;
- no match outcomes;
- no CORNERS10/football-state;
- no Supabase writes;
- no paid action;
- no betting;
- no production promotion;
- no post-result retuning;
- production `.pkl` hash guard required in CI.

