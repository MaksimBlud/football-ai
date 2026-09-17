# FIVE_DOLLAR_CORNERS_SOURCE_PILOT_V1_RESULTS

## Outcome

`SOURCE_QUALIFIED_FOR_BACKFILL`

The frozen acquisition-only pilot passed in all three target leagues.

## Exact execution

- PR: `#372`
- tested head: `a460b433f4d67a19d5beb6e2f10d22824c8ca2f2`
- workflow run: `35235009894`
- artifact id: `10503575942`
- artifact name: `five-dollar-corners-source-pilot-v1`
- artifact digest: `sha256:ed012ae16dc3835900e7696d572088056724990866485078fed250283b379fe0`
- merge commit: `5a7843f1517716e09cd3b173c8e178f0a69b9908`

Production `.pkl` hashes were verified unchanged.

## Frozen sample result

| League | Covered | Sample | Status |
|---|---:|---:|---|
| EPL | 5 | 5 | PASS |
| La Liga | 5 | 5 | PASS |
| Serie A | 5 | 5 | PASS |

Overall coverage: `15/15` fixtures with complete Bet365 full-time corner opening + closing market data.

Every accepted row contained:

- opening corner line;
- opening Over price;
- opening Under price;
- closing corner line;
- closing Over price;
- closing Under price.

The pilot used exactly `18/18` allowed provider requests: three league fixture-list calls plus fifteen per-fixture corner-odds calls.

## Observed examples

The source returned real line/price movement rather than only static corner counts.

Examples from the normalized artifact:

- Man Utd vs Man City: corner line `10.0`; opening `Over 1.90 / Under 1.90`; closing `Over 2.00 / Under 1.80`.
- Coventry vs Brighton: opening line `10.0` at `1.95 / 1.85`; closing line `9.5` at `1.80 / 2.00`.
- Sunderland vs Arsenal: opening line `9.5` at `1.95 / 1.85`; closing line `9.0` at `1.875 / 1.925`.
- Barcelona vs Racing Santander: line `11.5`; opening `1.975 / 1.825`; closing `2.00 / 1.80`.

These observations establish source capability only; they are not model-performance evidence.

## Research interpretation

The previous bookmaker-corners blocker was lack of a reproducible historical line+price source. That blocker is now removed for source qualification.

Current status becomes:

`CORNERS = SOURCE_QUALIFIED / BACKFILL_READY`

This supersedes the earlier temporary `COLLECT / EXTERNAL_CREDENTIAL_REQUIRED` state as a description of data availability.

It does **not** supersede the evidence limitation: CORNERS10 has still not been tested against this bookmaker-corner market, so no market-edge, profitability, or production claim is permitted yet.

## Next gate

Before any large paid historical download or CORNERS10-vs-market result is opened, freeze a separate historical-corners experiment contract covering:

- historical date/season scope;
- opening vs closing market baseline definition;
- line-movement handling;
- de-vig method;
- push/half/quarter-line settlement rules;
- point-in-time football features;
- validation and untouched OOT split;
- minimum sample/coverage gate;
- no post-OOT retuning.

Free-tier data can be used for additional source/format validation, but a multi-season backtest requires a plan/history window that actually covers the preregistered seasons.

## Safety

- research-only;
- no betting;
- no production promotion;
- no Supabase write in the pilot;
- no production `.pkl` change;
- API credential stayed in GitHub Secret and was not persisted;
- no model metric was computed during source qualification.
