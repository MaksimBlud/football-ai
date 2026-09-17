# FIVE_DOLLAR_CORNERS_BACKFILL_V1

## Purpose

Freeze the acquisition-only historical backfill needed by `CORNERS10_BET365_MARKET_V1`.

This block downloads and normalizes bookmaker corner-market history only. It must not compute model, target, calibration, ROI, betting or PASS/SKIP metrics.

## Provider

Official 5DollarFootballAPI endpoints only.

Authentication is supplied exclusively through the repository secret/environment variable:

`FIVE_DOLLAR_FOOTBALL_API_KEY`

The key must never be logged, written to artifacts, placed in URLs, or committed.

## Frozen leagues

- `EPL`: provider league id `4160026622`
- `LA_LIGA`: provider league id `4212821298`
- `SERIE_A`: provider league id `3405541143`

## Frozen historical window

Acquire finished league fixtures for:

- `2016-17`
- `2017-18`
- `2018-19`
- `2019-20`
- `2020-21`
- `2021-22`
- `2022-23`
- `2023-24`
- `2024-25`
- `2025-26`

`2026-27` is forbidden.

Each season is addressed by a fixed UTC window from July 1 of the first year through July 1 of the next year. The evaluator, not the acquisition layer, decides which rows belong to train/validation/OOT.

## Bulk endpoint

Use:

`GET /v1/leagues/{league_id}/fixtures`

with:

- `status=finished`
- `include=odds`
- `order=asc`
- fixed season `start_time` / `end_time`
- `per_page=50`
- full pagination until `pagination.has_more == false`

`include=odds` is required so the backfill does not perform one odds request per fixture.

## Mandatory preflight

Before a full backfill, make exactly one earliest-history probe for EPL `2016-17` using the same bulk endpoint with `include=odds` and `per_page=1`.

The full backfill may proceed only when the probe:

- returns HTTP success;
- returns API `success == 1`;
- contains at least one finished fixture from the requested historical window;
- exposes an inline odds object from which a Bet365 corner opening market can be parsed.

If the provider returns `403 insufficient_plan`, empty historical coverage, or no parseable inline odds, stop immediately with `HISTORY_ACCESS_REQUIRED` / `HISTORY_PREFLIGHT_FAILED` as applicable.

The runner must never silently fall back to the account's shorter current history window.

## Market normalization

For every returned fixture, retain fixture identity and Bet365 full-time `corner_line` market fields when present:

- fixture id;
- league / league id;
- kickoff UTC;
- home team;
- away team;
- opening line / Over / Under;
- closing line / Over / Under when available;
- source=`5DOLLARFOOTBALLAPI`;
- bookmaker=`bet365`.

The acquisition layer may retain integer, half and quarter lines. The frozen evaluator later admits only opening half-lines for V1.

A missing closing snapshot does not invalidate an opening market row for the primary V1 experiment; closing is diagnostic only.

## Persistence

Persist separately:

1. every raw provider page;
2. normalized market rows as JSONL;
3. a coverage report with page/request counts, fixture counts, valid opening-market counts and kickoff range per league/season;
4. provider errors without secret material.

Finished historical responses are immutable research inputs and should be reused rather than re-downloaded during analysis.

## Coverage checks

For every frozen league/season the report must show:

- number of finished fixtures returned;
- number with valid Bet365 opening corner line + Over/Under prices;
- opening-market coverage rate;
- earliest/latest kickoff.

The backfill runner does not relax the frozen model experiment's sample gates. If provider coverage is insufficient, the downstream evaluator must report `DATA_INSUFFICIENT` rather than alter the experiment.

## Request budget and pacing

- hard maximum: `300` provider requests for the entire backfill run;
- page size: `50` when `include=odds` is used;
- minimum pacing interval: `1.6` seconds between requests;
- no unbounded retry loop;
- HTTP/API errors fail closed for the affected run rather than producing a silently incomplete dataset.

## Authorization boundary

This contract does **not** authorize purchasing or upgrading a 5DollarFootballAPI plan.

The current source documentation states that the Free plan exposes only the latest three months, while the multi-season window required here needs historical access back to 2016. A plan change must be an explicit user action.

The runner and its tests may be merged and kept ready before that action, but the multi-season live backfill must not be initiated unless the account already exposes the frozen window.

## Safety

- acquisition-only;
- research-only;
- `NO_BET`;
- no model evaluation;
- no production `.pkl` changes;
- no production promotion;
- no Supabase writes;
- no The Odds API calls;
- no website scraping;
- no automatic subscription action;
- no `2026-27` data.
