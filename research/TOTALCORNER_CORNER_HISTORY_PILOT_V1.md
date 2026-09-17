# TOTALCORNER_CORNER_HISTORY_PILOT_V1

## Purpose

Freeze a small acquisition-only pilot for TotalCorner before any broad historical download or model-vs-market corner evaluation.

This pilot answers only one question: **does the official TotalCorner API provide enough valid pre-match bookmaker corner line+price history for EPL, La Liga and Serie A to justify a larger historical research download?**

No predictive/model metric is permitted in this pilot. `NO_BET` remains binding.

## Frozen leagues

- EPL: TotalCorner league id `1`
- Serie A: TotalCorner league id `3`
- La Liga: TotalCorner league id `5`

These ids come from TotalCorner's public main-league list / API documentation.

## Frozen historical window

Schedule dates:

- `2025-05-23`
- `2025-05-24`
- `2025-05-25`

These dates cover the closing weekend of the completed 2024/25 season for the target leagues while remaining entirely historical.

The runner must enumerate every page returned by `/match/schedule` for these dates, filter by the frozen league ids, sort deterministically by kickoff then numeric match id, and select the first 10 unique fixtures per league.

If fewer than 10 fixtures are found for any league, the pilot fails closed with `INSUFFICIENT_FIXTURES` and no coverage decision is made for that league.

## Official endpoints only

- schedule enumeration: `GET https://api.totalcorner.com/v1/match/schedule`
- corner history: `GET https://api.totalcorner.com/v1/match/odds/{match_id}?columns=cornerList`

Every request requires `TOTALCORNER_TOKEN`.

No website scraping, HTML parsing, browser automation, or unofficial endpoint is allowed.

## Snapshot validity

A normalized snapshot is valid only when:

- timestamp is strictly before kickoff;
- corner line is finite;
- Over odds > 1.0;
- Under odds > 1.0;
- fixture identity is present;
- source is `TOTALCORNER`.

In-play snapshots at or after kickoff are discarded by the already-merged parser.

For each fixture, `covered=true` when at least one valid pre-match snapshot exists.

## Frozen gate

For each league independently:

- sample size = exactly 10 fixtures;
- `PASS` when at least 8/10 fixtures are covered;
- otherwise `FAIL`.

Overall pilot decision:

- `SOURCE_QUALIFIED` only if all 3 leagues PASS;
- otherwise `SOURCE_NOT_QUALIFIED`.

This decision concerns **data availability only**. It is not evidence of model edge, profitable betting, market inefficiency, or production readiness.

## Persistence contract

The pilot must persist:

1. the raw schedule responses;
2. the raw odds response for every selected fixture;
3. normalized valid pre-match snapshots;
4. a summary report containing selected fixtures, per-league coverage and the overall source decision.

Raw and normalized data must remain separate.

## Request budget and pacing

- exactly 30 odds-history requests maximum (10 per league);
- schedule requests are paginated only for the three frozen dates;
- client pacing must respect TotalCorner's documented 30 requests/minute limit;
- no retries that cause the odds-history budget to exceed 30 successful fixture requests;
- HTTP/API failures must be recorded and fail closed for the affected fixture.

## Safety

- research-only;
- acquisition-only;
- no model evaluation;
- no betting;
- no production promotion;
- no production `.pkl` change;
- no Supabase write;
- no paid Odds API request;
- no request at all without an explicitly supplied `TOTALCORNER_TOKEN`;
- no automatic purchase/subscription action.
