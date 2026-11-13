# Original MARKET_ANCHOR_1X2_V2 — Live Football API source-candidate audit

**Audit date:** 2026-11-13  
**Scope:** official public terms, pricing, documentation, operator and Serie A pages only. No account, API key, endpoint call, dataset download, Supabase access, quote read, feature build, inference, or target-outcome analysis.  
**Decision:** `HOLD` — promising schema/coverage candidate, not approved for original V2 capture or inference.

## 1. Summary

Live Football API (`live-football-api.com`, operated by FORCESCRIPTS LTD) is a new candidate worth recording:

- its official Serie A page identifies the **2026/2027 season**, says every endpoint works for Serie A, and lists fixtures, goals, cards, match statistics and head-to-head;
- the documented `/live_match_details` response includes corners, shots, shots on target, an event timeline with yellow/red cards, a `last_updated` timestamp and a `stale` flag;
- new accounts receive 500 free credits without a card; each documented endpoint call costs one credit and the credits do not expire;
- the Terms permit using API data in one's own applications/products and explicitly permit resale/redistribution to end users.

These facts make the provider more promising than candidates that lack corners or an explicit redistribution clause. They do **not** establish that the full frozen V2 feature contract can be populated from completed 2026/27 Serie A fixtures, that the upstream data is licensed for this use, or that source-before-quote can be proven. No API call or free-credit use is authorized by this audit.

## 2. Documented coverage and request budget

The official Serie A page states:
- current season is 2026/2027;
- 96 past seasons are available through the fixtures/standings surface;
- every endpoint works for Serie A and 1,400+ leagues;
- match events and statistics include goals, cards, substitutions and match statistics.

The official docs show:
- `GET /league_fixtures` returns the full league schedule, played-match scores and upcoming kickoff times;
- `GET /team_matches` returns past results and upcoming fixtures for a team, but its documented example contains scores/fixtures rather than match statistics;
- `GET /live_match_details` returns an event timeline and match statistics.

The free allowance is **500 one-time credits**, one credit per endpoint request, with no card and no expiry. It is not a recurring monthly free quota. A possible bounded request plan might fit under 500 calls if one fixture-list request plus one detail request per already-completed match is sufficient; that is only a planning estimate. It is not evidence that completed-match detail calls work, that all matches have all fields, or that future collection is free after the one-time allowance.

No request-budget commitment or API call was made.

## 3. Mapping to the original 19-feature contract

The original frozen candidate requires 19 features in the exact order preserved in `research/source_rights/live_football_api.json`.

Potential documented mappings:
- points and goals for/against: derive from completed fixture scores;
- corners for/against: `stats[]` entries with `type="corners"`;
- yellow/red cards: event types `yellow_card` and `red_card`.

This is schema-level potential only. The following are unresolved:
1. `/live_match_details` is described as returning **real-time** match data. The public docs do not establish that it returns complete statistics/events for already-completed historical matches queried later.
2. The docs say events may include `is_second_yellow`, but do not define how second-yellow dismissals map to the original source's separate yellow-card and red-card totals. A count that differs from the original Football-Data convention would change the frozen features and is not acceptable.
3. The Serie A page's broad endpoint claim is not a per-match coverage ledger. No 2026/27 match payloads were retrieved, so no completeness or field parity is claimed.
4. No actual response was checked for nulls, missing event rows, corrections, or provider-side historical revisions.

Do not impute missing corners/cards as zero. Do not change the original feature order, feature builder, scaler, imputer, weights or candidate to accommodate this provider.

## 4. Source-before-quote, SHA and freshness

The documented detail response contains `last_updated` and `stale`, and the outer response includes a timestamp. The docs do not define `last_updated` as the upstream provider's first observation time or provide a per-field source timestamp/correction history.

A local immutable archive could record:
- exact response bytes;
- local UTC retrieval time;
- response `last_updated` and `stale`;
- SHA-256 of the exact response bytes;
- fixture identity and kickoff;
- later quote observation time and quote SHA.

That would prove when this project received a specific byte sequence and whether its local capture preceded a quote. It would **not** prove when the upstream source first observed or corrected the underlying statistic. The API key is documented in the query string, so any future adapter would also need strict URL/query redaction from logs and artifacts.

Until the provider documents upstream source identity, observation/correction semantics, and completed-match retention, source-before-quote is not established.

## 5. Rights and retention

The Terms of Service (effective 2026-01-01):
- Section 5 permits reselling, sublicensing or redistributing API access/data to third parties, including inside one's own commercial product/service;
- Section 6 licenses returned API data for use in one's own applications, products or services, including resale/redistribution to end users;
- Section 9 disclaims guarantees of completeness, accuracy and timeliness.

The pricing page also claims that all plans include a commercial-use licence and that new accounts receive 500 free credits.

However, the reviewed public Terms do not expressly resolve:
- internal machine-learning feature construction and inference;
- model training/evaluation rights;
- long-term private retention of raw response bytes and derived feature archives;
- the upstream provider(s) supplying the data and whether their rights cover every Serie A field;
- source correction and historical revision obligations.

The operator's About page identifies FORCESCRIPTS LTD but does not identify the upstream football-data provider. A broad right to redistribute API output is not proof that every upstream field is licensed for this particular research and retention use.

**Require written provider confirmation** for these points before account creation, data capture or inference.

## 6. Binding disposition and next admissible step

**HOLD — no ingestion, no inference, no evaluation.**

A bounded source-only test may be considered only after written confirmation of:
1. rights to retain raw response bytes privately and use the derived fields for internal model feature construction/inference;
2. upstream provider identity and rights for Serie A fixtures, scores, corners and card events;
3. availability of complete `/live_match_details` for already-completed 2026/27 Serie A fixtures, including all fields needed by the 19 frozen features;
4. the exact yellow/red/second-yellow counting convention and correction policy;
5. the meaning of `last_updated`, `stale`, and any upstream observation timestamp.

If cleared, the first test must be source-only: a small, predeclared set of completed fixtures; exact response bytes and SHA-256; strict local retrieval timestamp; completeness/null checks; no quote reads; no model inference; no outcome evaluation. It must not alter the original V2 candidate or production artifacts.

## 7. V2 invariants and activity

- Original candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original 19-feature order, frozen weights, scaler, imputer, training fingerprint and 20x2 matrix unchanged.
- `active_lambda=0`; `shadow_lambda=1` research-only; stability gate FAILED; NO_BET; no automatic promotion.
- No legacy XGBoost production model or production `.pkl` is involved.
- No account or API key created; API requests = 0; free credits spent = 0; paid requests = 0.
- No data downloaded, no Supabase access/write/DDL, no quote read, no target-outcome read, no feature calculation, no inference, and no schedule or main-branch change.

## 8. Official sources reviewed (2026-11-13)

1. Terms of Service — https://www.live-football-api.com/terms  
   Effective 2026-01-01; sections 5–6 cover resale/redistribution and use in one's own products; section 9 disclaims completeness, accuracy and timeliness guarantees.
2. Pricing — https://www.live-football-api.com/pricing  
   500 free credits for new accounts, one credit per endpoint call, no expiry, and commercial-use claim.
3. API Documentation — https://www.live-football-api.com/docs  
   `/live_match_details` schema includes `last_updated`, `stale`, event types and corners/shots/SOT; `/league_fixtures` and `/team_matches` provide fixture/result history.
4. Serie A API — https://www.live-football-api.com/serie-a-api  
   Identifies 2026/2027 and claims Serie A support for all endpoints, including match events/statistics.
5. About — https://www.live-football-api.com/about  
   Identifies FORCESCRIPTS LTD as the operator; does not identify the upstream data provider.

This is an official-documentation audit only. No live response, actual field completeness, source timestamp, or model-quality result is asserted.
