# FIVE_DOLLAR_CORNERS_SOURCE_PILOT_V1

## Purpose

Qualify 5DollarFootballAPI as a historical bookmaker-corners source before any CORNERS10-vs-market experiment.

This pilot answers only one question: **does the Free-plan API return enough valid Bet365 pre-match corner line + price snapshots for EPL, La Liga and Serie A to justify a later historical backfill?**

No model metric, betting metric, profitability claim or production decision is permitted in this pilot.

## Frozen source

Provider: `https://api.5dollarfootballapi.com`

Authentication: `Authorization: Bearer <key>` using GitHub repository secret `FIVE_DOLLAR_FOOTBALL_API_KEY`.

The key must never be printed, persisted to artifacts, written to the repository or passed as a query parameter.

## Frozen leagues

- EPL: `4160026622`
- La Liga: `4212821298`
- Serie A: `3405541143`

These ids are the provider's published league ids.

## Frozen sample

For each league independently:

1. call `GET /v1/leagues/{id}/fixtures?status=finished&order=desc&per_page=5`;
2. select exactly the first five unique finished fixtures returned by the provider;
3. for each selected fixture call `GET /v1/fixtures/{id}/odds?market=corner`.

Maximum live request budget:

- 3 league-fixture requests;
- 15 per-fixture corner-odds requests;
- 18 provider requests total.

No pagination beyond the first fixture-list page is allowed in V1.

## Required corner payload

The pilot uses Bet365 only. A fixture is `covered=true` only when the `corner_line` market contains BOTH:

- `opening.line`, `opening.over`, `opening.under`;
- `closing.line`, `closing.over`, `closing.under`.

Every line must be finite. Every Over/Under price must be finite and > 1.0.

`inplay` is ignored.

The pilot must not use full-time corner counts or match outcomes as a substitute for missing bookmaker prices.

## Frozen gate

For each league:

- sample size must equal exactly 5 fixtures;
- `PASS` when at least 4/5 fixtures are covered;
- otherwise `FAIL`;
- fewer than 5 selected fixtures => `INSUFFICIENT_FIXTURES`.

Overall decision:

- `SOURCE_QUALIFIED_FOR_BACKFILL` only if all three leagues PASS;
- otherwise `SOURCE_NOT_QUALIFIED`.

This decision concerns source capability only. It does not prove CORNERS10 edge or bookmaker inefficiency.

## Persistence

The pilot must upload an artifact containing:

1. raw fixture-list response for each league;
2. raw corner-odds response (or sanitized error record) for every selected fixture;
3. normalized opening/closing corner rows;
4. `report.json` with per-league coverage and overall decision.

Raw and normalized data must remain separate.

## Free-tier safety

The provider currently documents Free-plan access to the top-five European leagues, Bet365 corner markets, a 3-month history window and 60 requests/hour.

V1 is intentionally capped at 18 provider requests, below that hourly allowance.

No automatic retry may increase the frozen request budget.

## Research safety

- acquisition-only;
- no CORNERS10 evaluation;
- no outcome metrics;
- no betting;
- no model training or promotion;
- no production `.pkl` change;
- no Supabase write;
- no paid Odds API request;
- no API request at all if `FIVE_DOLLAR_FOOTBALL_API_KEY` is absent;
- no plan purchase or upgrade action.
