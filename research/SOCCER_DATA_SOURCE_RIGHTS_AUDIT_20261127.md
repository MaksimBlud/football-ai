# Original MARKET_ANCHOR_1X2_V2 — Soccer Data free-source rights and coverage audit

**Audit date:** 2026-11-27 UTC  
**Decision:** **HOLD_NO_INTEGRATION**  
**Scope:** official public product, pricing, terms and documentation pages only. No account or API key was created; no API or odds endpoint was called; no match payload or dataset was downloaded; no Supabase access, feature calculation, inference or protected-outcome read occurred.

## Executive finding

Soccer Data is a new current-season source candidate worth recording. Its public Free plan claims 50 requests per day, all statistics endpoints and current-season-only access. The match-stat endpoint documents per-match team statistics including corner kicks, yellow cards and red cards. The product page says the Free tier does not include pre-match or live odds.

This could only be a **lagged current-form source for future Serie A fixtures**, not a replacement for the frozen 2016/17–2025/26 V2 training source. The docs say Serie A data begins in 2020/21 generally, but Free access is limited to the current season. No authenticated response was inspected, so Serie A 2026/27 field coverage and exact definitions remain unverified.

The source is **not approved** for V2 ingestion. The Terms permit caching/storing and displaying data while the account and plan remain active, but the licence ends when the account or Terms end. They prohibit raw-feed redistribution, do not explicitly grant internal model inference or training, and do not identify the upstream data providers. The stats endpoint does not document a per-match source-observation or per-field correction timestamp.

## Official pages reviewed

- Home and product claims: https://soccer-data.co/
- Pricing: https://soccer-data.co/pricing
- Terms of Service, last updated 2026-10-30: https://soccer-data.co/terms
- API documentation: https://soccer-data.co/docs
- Coverage model: https://soccer-data.co/docs/concepts/coverage
- Match-stat endpoint: https://soccer-data.co/docs/reference/matches/stats

The pages are mutable. This audit records URLs and the review date; it does not claim immutable upstream page-byte hashes.

## Free-plan and technical fit

| Item | Official documentation claim | V2 interpretation |
|---|---|---|
| Price | $0/month | No paid plan needed for this audit |
| Request allowance | 50 requests/day | A per-match stats endpoint is request-limited |
| Statistics | All stats endpoints | Coverage still varies by competition/season |
| History | Current season only | Could only supply lagged 2026/27 form |
| Cache | Free tier reads a 5-minute cache | Response may be stale; exact bytes must be preserved |
| Odds | Free excludes odds and webhooks | No odds use; retain existing separately authorized market data only |
| Match stats | One match ID per `/matches/{match_id}/stats` call | No bulk match-stats endpoint is documented |

The match-stat endpoint documents `corner_kicks`, `yellow_cards`, `red_cards`, shots and other team statistics. It returns 409 while a match is live and may return 404 if stats were never collected or are not yet available. A null field is explicitly not a zero. The coverage API reports `team_stats` availability and covered-event counts per competition/season, but that does not prove every required field is present or semantically identical for each Serie A 2026/27 match.

The 50-request daily allowance and per-match endpoint may require several days to collect enough historical current-season fixtures for all rolling/venue windows. Do not assume a bulk route or silently fill missing match statistics.

## Rights and retention

The Terms state that football data belongs to Soccer Data or providers it licenses and grant a non-exclusive, non-transferable licence. While the account and plan are active, the user may call the API within plan limits, cache/store received data, and display it in their own websites, apps and services. Raw-feed resale, sublicensing and redistribution are prohibited. When the account is closed or the Terms end, the licence ends.

The reviewed Terms do **not explicitly state** that:
- internal machine-learning inference or model training is permitted;
- a private raw archive may be retained after account termination;
- the API operator has the right to sublicense every upstream field for this project's intended use.

The Terms say the data comes from third-party providers but do not identify them. They also warn that scores, events, lineups and statistics can arrive late, change after an event or be wrong. Written confirmation is required before source integration.

## Source-before-quote and SHA

The match-stats endpoint documentation does not expose a source-observation timestamp or per-field correction timestamp. The Free plan's five-minute cache is not a provenance timestamp.

If the owner later authorizes a minimal Free-tier test, the capture must:
1. preserve the exact response bytes privately;
2. record the match ID, endpoint, API/schema version and request identifier if supplied;
3. record local timezone-aware UTC receipt time immediately after the successful response;
4. calculate SHA-256 over the exact raw response bytes;
5. prove the source receipt and successful source-capture run completed strictly before the target quote's snapshot/persistence time and kickoff;
6. reject missing fields rather than substituting zero or silently changing frozen V2 imputation semantics.

That would prove the exact bytes were in this project's possession before the quote. It would not reconstruct the provider's upstream first-seen or correction history. No such capture has been performed.

## Frozen V2 invariants

- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Exactly 19 ordered features; 20×2 weight matrix.
- `active_lambda=0`; `shadow_residual_lambda=1`.
- Historical stability gate remains FAILED.
- Separate prospective outcome-read gate remains 30 completed primary Serie A forecasts; no outcomes are opened by this audit.
- No refit, feature selection, threshold tuning, production promotion, betting or legacy XGBoost work.

## Requirements before reconsideration

1. Written confirmation that the Free plan permits internal V2 inference and the intended research use.
2. Written confirmation of upstream provider identity and field-level rights.
3. Written confirmation of private raw-response retention and what happens to archived bytes if the account or plan ends.
4. An owner-authorized, minimal Free-tier response test proving Serie A 2026/27 availability and exact goals/corners/yellow/red field semantics.
5. A match-level coverage and missingness audit before feature calculation.
6. A source-capture design recording exact bytes, SHA-256, local UTC receipt time and strict source-before-quote chronology.
7. A request-budget plan that stays within the Free allowance; no paid upgrade and no paid odds request.

Until every requirement is established, keep this source at **HOLD_NO_INTEGRATION**. Do not create an account, self-activate a plan, request a key, call the API, download data, calculate V2 features or run inference from this source.

## Actions taken

- Read only public official product, pricing, Terms and documentation pages.
- Did not create an account or API key.
- Did not call any endpoint, including the odds endpoints.
- Did not download any match data or archive.
- Did not access Supabase, read protected outcomes, calculate features or run inference.
- Did not change the frozen candidate, weights, protocol, production artifacts, workflows or schedules.
