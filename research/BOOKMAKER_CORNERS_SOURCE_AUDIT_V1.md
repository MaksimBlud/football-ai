# BOOKMAKER_CORNERS_SOURCE_AUDIT_V1

## Purpose

Identify a reproducible historical source for **bookmaker corner line + price history** so the existing football-state corner signal can be tested against the market rather than against post-match corner counts.

This is a data-source audit only. No bookmaker-corners backtest is authorized by this document and `NO_BET` remains binding.

## Requirements

A qualifying source must provide, for a historical fixture:

- fixture identity and kickoff time;
- full-time corner total line;
- both Over and Under prices;
- timestamped price history before kickoff;
- enough historical depth to support at least a multi-season retrospective pilot;
- a reproducible machine-readable access path;
- no substitution of post-match corner counts for bookmaker prices.

## Source findings

### OddsPapi

Strengths:

- official `/v4/historical-odds` endpoint;
- corner markets are explicitly supported;
- timestamped snapshots and bookmaker filtering;
- historical endpoint is available on the free tier.

Blocking limitation:

- documentation states that all historical odds data are available **since January 2026**.

Decision: `SECONDARY_PROSPECTIVE_SOURCE`.

OddsPapi is useful for prospective collection from 2026 onward, but it is too shallow for the intended multi-season historical corner-market backtest.

### 7M

Observed strengths:

- public match pages expose a Corners tab;
- pages show Bet365/Crown opening line and prices and later price/line updates;
- played 2025/26 and 2026 fixtures visibly contain corner market histories.

Limitations:

- no documented public historical API was found in this audit;
- reproducible deep-season bulk extraction was not established;
- therefore website pages are suitable only as a manual cross-check, not as the primary bulk research feed.

Decision: `MANUAL_CROSSCHECK_ONLY`.

### TotalCorner

Observed/documented strengths:

- official JSON REST API;
- `/match/odds/{match_id}?columns=cornerList` returns full corner-line change history;
- documented `corner_list` entries contain match status, line, Over price, Under price, timestamp and home/away corner state;
- `/match/schedule` and `/league/schedule/{league_id}` provide match IDs for historical enumeration;
- match database is documented as going back to 2014, with odds-history density increasing in later seasons;
- website examples confirm real Bet365 corner histories on historical matches, including EPL 2023 and Serie A 2024;
- current pricing documents VIP at EUR 5/day or EUR 28/30 days;
- API rate limit is 30 requests/minute.

Access boundary:

- API requires VIP membership/token;
- free website browsing can be used to inspect coverage, but this project will **not** implement mass scraping around the paid API.

Decision: `PRIMARY_HISTORICAL_SOURCE_READY_FOR_TOKENED_PILOT`.

## Acquisition contract

When a TotalCorner token is intentionally provided later, the first live action must be a **small read-only pilot**, not a full historical sweep.

Pilot scope:

- leagues: EPL, La Liga, Serie A;
- 10 finished fixtures per league from a recent completed season;
- request only official TotalCorner API endpoints;
- collect `cornerList` only;
- retain only snapshots strictly before kickoff for pre-match research;
- persist raw responses separately from normalized rows;
- calculate and report coverage before any model evaluation.

Pilot acceptance gate:

- at least 8/10 fixtures per league have at least one valid pre-match corner snapshot;
- each accepted snapshot has finite line, Over price > 1, Under price > 1, and timestamp < kickoff;
- team/kickoff identity can be reconciled to the project fixture source;
- no outcome/model metric is computed during the acquisition pilot.

If the pilot passes, freeze a separate historical-corners experiment contract **before** expanding the download or opening any model-vs-market result.

## Safety

- research-only;
- no production `.pkl` changes;
- no model promotion;
- no Supabase writes during source qualification;
- no paid Odds API calls;
- no TotalCorner request without an explicitly supplied token;
- no automated scraping of TotalCorner website pages;
- `NO_BET` remains binding.
