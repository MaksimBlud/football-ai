# DataSportsAPI Free — original MARKET_ANCHOR_1X2_V2 statistics-source screen

**Checked:** 2026-11-20 21:50:45 UTC  
**Decision:** `HOLD_NO_INTEGRATION`  
**Scope:** public official documentation only; fixture statistics as lagged inputs for the unchanged original V2. No odds endpoint, account, key, authenticated request, or source download.

## What is technically available

The official Serie A page identifies league `195910`, 20 clubs and 380 fixtures per season, and states that the table and current-season statistics are available on all plans. The documentation describes fixtures, results, events, lineups and statistics as core data. The Free plan currently lists 1,000 requests/day during beta (100/day afterwards), 10 requests/minute, and only the last **7 days** of finished-match history; upcoming/live data are not history-limited.

The match-level statistics endpoint is fixture-scoped (`GET /v2/fixtures/{id}/statistics`). The public docs describe the endpoint as live match statistics. The separate Serie A season-statistics endpoint returns team season totals/averages; it is not documented as a per-match last-5/last-10 history. A Free key therefore cannot retrieve the current season's already-finished match-by-match history beyond seven days. The provider's public docs do not establish a one-call whole-round export of match-level statistics on Free.

## Rights and provenance

The Terms (last updated 16 November 2026) permit use in the customer's own apps, websites, products and analysis, including commercial use, and prohibit resale/redistribution of raw data as a competing feed. However, the same Terms say sports data comes from third-party sources, may be late/incomplete/wrong and may be corrected. The reviewed public material does not identify the upstream rights chain for Serie A match statistics, explicitly grant long-term private raw-response retention/archiving, or document per-fixture/per-stat first-observation and correction timestamps.

The fixture start time is not a statistic's observation time. The provider's live status/freshness measurements are aggregate/live pipeline measurements, not a historical first-observed timestamp contract for each of the frozen 19 inputs.

## Original V2 compatibility

- The current candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- The frozen 19-feature order, weights, scaler/imputer and training fingerprint are untouched.
- `active_lambda=0` remains the market; `shadow_lambda=1` remains research-only.
- No new provider is admitted by the frozen source contract.

A future-only capture could theoretically accumulate enough matches after many matchweeks if rights, private retention and observation-time semantics were resolved first. That does not make the present Free seven-day history sufficient to reconstruct the current last-10 match windows, and it is not a reason to relax the V2 contract.

## Decision

**HOLD / NO INTEGRATION.** The seven-day Free history is insufficient for immediate current-season rolling match features; current-season team aggregates are not a substitute for the original per-match rolling inputs. Upstream rights, private archive retention and per-stat observation timestamps are also unconfirmed. No adapter or workflow was added.

## Actions

- API account/key created: no.
- Authenticated API requests or source downloads: 0.
- Odds endpoints called: no.
- Supabase writes/DDL: 0.
- Model code, weights, candidate, production `.pkl`, schedules or other agents changed: no.
- Protected 2026/27 target outcomes opened: no.

## Official sources

- https://datasportsapi.com/terms/ (last updated 16 November 2026)
- https://datasportsapi.com/sports/football/serie-a/
- https://datasportsapi.com/docs/limits/
- https://datasportsapi.com/docs/
- https://datasportsapi.com/docs/reference/
