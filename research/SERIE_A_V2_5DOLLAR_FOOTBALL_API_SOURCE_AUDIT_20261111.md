# Original MARKET_ANCHOR_1X2_V2 — 5DollarFootballAPI source audit

**Audit date:** 2026-11-11  
**Scope:** official public terms, pricing/eligibility pages, API documentation, Serie A coverage and data-quality pages only. No account was created, no key was requested, no API endpoint or odds endpoint was called, no match payload or quote was fetched, and no data archive was downloaded.

## Decision

**5DollarFootballAPI is the strongest new no-cost source candidate found in this audit, but it is not approved for V2 ingestion yet.** Its published terms explicitly permit use in models and internal tools and permit caching; its fixture schema exposes goals, corners and yellow/red cards. However, its own public pages conflict on whether the full Serie A statistics feed is available on a $0 plan, and the reviewed response examples do not expose a per-fixture source-observed timestamp or named upstream provider for each statistic.

Do not create an account, activate Community Access, call the API, or integrate it until the plan/coverage and upstream-rights questions are resolved by the owner/provider. No paid plan is proposed or authorized.

## Official pages reviewed

- Terms (last updated October 2026): https://5dollarfootballapi.com/terms
- Main product and pricing claims: https://5dollarfootballapi.com/
- Community Access eligibility and limits: https://5dollarfootballapi.com/community
- Serie A page: https://5dollarfootballapi.com/serie-a-api
- API documentation: https://5dollarfootballapi.com/docs
- Data quality by competition: https://5dollarfootballapi.com/docs/data-quality
- Machine-readable data quality: https://5dollarfootballapi.com/docs/data-quality.json
- Status and freshness: https://5dollarfootballapi.com/status

The pages are mutable. This audit records the reviewed URLs and date; it does not claim immutable upstream page-byte hashes. Any later authorized test must archive the exact documentation/terms versions and their SHA-256 values before relying on them.

## Rights: materially promising, with an upstream-rights caveat

The Terms of Service state that users may use data in their own commercial products, explicitly including **websites, apps, models and internal tools**, display scores/statistics/odds to end users, and cache API responses. Free and Community Access require visible attribution when data is displayed in a public-facing product. Raw data may not be resold or redistributed as a competing feed.

This is materially clearer for model use than the sources rejected in earlier audits. However:
- the Terms do not name the upstream data provider(s) or identify which provider supplies each field;
- the main site says it is not affiliated with API-Football, SportMonks or football-data.org, but that statement does not identify the actual upstream rights chain;
- the Terms provide the API operator's grant, but the reviewed pages do not independently establish the scope of every upstream licence or the right to retain a private research archive after plan expiry.

Before integration, obtain written confirmation that the provider's upstream rights allow the specific Serie A match-stat fields, derived rolling features, frozen-model inference, private research retention and the intended project use. Do not redistribute raw responses.

## Free-plan access and a material Serie A plan contradiction

The public pages describe three relevant access levels:

| Access | Published price | Published limits/history |
|---|---:|---|
| Free | $0 | 60 requests/hour, 20/minute ceiling; last 3 months of results/odds in the general API docs |
| Community Access | $0 for eligible users | Top-five leagues plus one selected country pack; 300 requests/hour, 20/minute ceiling; last 12 months of results/odds; 12-month activation/renewal |
| Pro | $5/month | 137 competitions and broader access; paid and therefore not authorized |

Community Access is described for students, academic/non-profit researchers, early-career developers, or anyone for whom $5/month is a meaningful expense. It requires the account holder to select the applicable eligibility statement and a country pack. Eligibility must not be assumed or self-attested by this automation on the user's behalf.

**The key unresolved contradiction:**
- The dedicated Serie A page says Serie A is included in the free tier and that full statistics are included.
- The Community Access page says the top five leagues are included at $0.
- The machine-readable/data-quality page labels **Italy Serie A (league id 3405541143) as “Pro”**, not Free or Community.
- The general API docs say Free history is three months, Pro is twelve months and Ultra is full history; the Community page separately advertises twelve months.

These statements are not safely reconcilable from the public documentation alone. A free account must not be assumed to return the full Serie A stats payload simply because the marketing page says “free”.

No Pro, Ultra, Business, Edge, or other paid access may be used.

## Publicly documented Serie A coverage

The dedicated Serie A page reports:
- league id 3405541143;
- 4,803 fixtures on record and history since 2014;
- 385 finished matches in its last-12-month summary;
- 9.0 corners and 3.5 cards per match in that summary;
- a claim that Serie A is available on the free tier with full statistics.

The data-quality page, generated 2026-11-11 05:05 UTC, reports the Italy Serie A row as:
- plan: **Pro**;
- 380 finished matches in the preceding 12 months;
- corners: 100%;
- half-time corners: 100%;
- corner line: 100%;
- odds: 100%;
- events: 100%;
- live stats: 100%;
- first season: 2014, 13 seasons.

The 380 versus 385 finished-match figures are also not reconciled on the reviewed pages. The data-quality HTML exposes a per-competition cards aggregate globally, but its visible competition table does not provide a separate per-league cards percentage. Do not infer 100% card completeness from the global 99.8% figure or from the Serie A average of 3.5 cards/match.

These are provider-published aggregate claims, not independently measured data quality. The exact 2026/27 per-match completeness and Free/Community access remain unverified because no authenticated endpoint was called.

## Schema compatibility with the frozen 19-feature contract — documentation only

The original candidate remains unchanged:
- Candidate SHA-256: a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6.
- Exactly 19 original features and their order, windows, weights, scaler and imputer remain frozen.
- No refit, threshold change, adapter, feature calculation or inference is proposed by this audit.

The documented fixture response includes:
- goals.home/away — possible goals-for/goals-against and match-points inputs;
- corners.home/away — possible corner-for/corner-against inputs;
- cards.home.yellow/red and cards.away.yellow/red — possible yellow/red inputs;
- kickoff_utc, stable fixture id and explicit fixture status;
- an event timeline with goal, corner, yellow-card, red-card and period-score events.

This covers the **families** of raw inputs used by the original feature builder at schema level. It does not prove exact source parity. A future compatibility test must reconcile:
1. whether a second yellow is represented as a yellow plus a red, a distinct event, or both, without double counting;
2. whether fixture card totals use the same red-card and yellow-card definitions as the original HR/AR/HY/AY source columns;
3. corner totals, abandoned/postponed fixture identity and full-time settlement;
4. null/zero semantics and exact team-side mapping;
5. regular-time-only score semantics.

The documented fixture status is finished only when the feed confirms the full-time mark (FT-90); extra time and penalties are excluded. Unknown is used when a fixture is not confirmed, including postponed/cancelled/untracked cases. A future adapter must accept only confirmed completed league fixtures for historical feature inputs and must never convert missing statistics to zero.

No new field mapping may alter the original 19 features or the frozen feature builder. The provider can only be considered as a source adapter feeding the unchanged original contract.

## Source-before-quote, freshness and SHA requirements

The API is read-only and uses UTC ISO-8601 kickoff timestamps. The public docs describe measured data freshness, per-match update ages for live statistics, result-settlement completeness and event-capture delay. They also report that source events can be retracted or have their minute revised.

The reviewed fixture-response examples do **not** document a per-fixture source_observed_at_utc, updated_at, ETag, or named upstream source for every statistic. A global status-page freshness measurement is not a per-fixture source timestamp.

If written rights and plan access are later confirmed, a bounded read-only capture must:
1. save the exact raw response bytes and response headers, with request id if returned;
2. record local captured_at_utc, API endpoint/parameters, fixture id, league/season, kickoff_utc, HTTP status and API plan;
3. compute SHA-256 over the exact response bytes before parsing or normalization;
4. record the parent capture run id, created/completed timestamps and artifact SHA;
5. require captured_at_utc < quote_snapshot_time_utc < kickoff_utc for any later quote association, with strict inequalities and UTC normalization;
6. reject stale/unknown responses, mismatched fixture/team identity, missing required fields and any source capture created at or after the quote;
7. keep raw payloads and manifests in an approved private archive, not a public GitHub Actions artifact or public repository.

This proves that the exact response we captured was observed before the later quote; it does not prove the provider's original upstream observation time. If the frozen V2 source-before-quote policy requires upstream publication time rather than our own pre-quote retrieval time, the provider must expose or attest that timestamp before integration.

The API also serves bookmaker odds. This audit did not call any odds endpoint. The model's active market reference remains the existing market data; active_lambda=0 is unchanged and shadow_lambda=1 remains research-only.

## Historical-window limitation

The provider advertises history since 2014 for Serie A, but the public plan documentation restricts queryable history:
- Free: last 3 months;
- Community Access: last 12 months;
- full historical seasons: Ultra.

Therefore Free/Community cannot replace the original 2016/17–2025/26 historical training archive. No training/refit is authorized anyway. A 3- or 12-month window may be enough for some current-season lagged form, but must not silently truncate the original last-5/last-10/venue-5 history. The unchanged feature builder must fail closed or use only a fully contract-compatible, legally approved history source; no shorter-window substitution or imputation is permitted.

## Required gates before any future use

1. Written confirmation of the upstream provider(s), upstream rights and permission for frozen-model inference, derived features and private retention.
2. Written clarification that the Free or Community Access plan actually grants Italy Serie A and its fixture goals/corners/cards/events payloads, resolving the Pro-vs-free discrepancy.
3. Confirm the applicable free-plan history window, request limits, attribution requirement and what happens to cached data when the 12-month Community term expires.
4. If the owner qualifies and elects Community Access, the owner—not this automation—must activate it. Do not assume eligibility.
5. Only after authorization, make a minimal read-only Serie A coverage request (no odds endpoint) and record the returned league/season IDs, per-match availability, card/corner null rates and exact raw-response SHA. Do not fetch protected target outcomes for prospective evaluation.
6. Compare a preregistered sample of source statistics against an independently licensed reference, especially second-yellow/red-card treatment and corners. No thresholds or definitions may be tuned on prospective outcomes.
7. Preserve the source response and parent-run SHA in a private archive. The current repository is public, so public artifacts are not an acceptable raw-data store.
8. Keep all source access and inference behind the existing default-deny rights and private-storage gates. A free plan or successful API response alone does not authorize activation.

## Original V2 contract and explicit non-results

- Original candidate SHA, 19 features/order, weights, scaler/imputer and training fingerprint: unchanged.
- active_lambda=0: market remains the active reference.
- shadow_lambda=1: research only.
- Stability gate: FAILED.
- Prospective target-outcome gate: 0/30 in the available verified evidence.
- Brier/LogLoss superiority over market: not established.
- No training/refit, threshold tuning, inference, bet, promotion or production change performed.

No account/key, API request, odds request, data download, source archive, Supabase read/write, target-outcome read, workflow schedule change, production artifact change, or main update was performed.

## Final disposition

**Keep 5DollarFootballAPI as a high-priority no-cost candidate for a future source-concordance test, but do not integrate it yet.** Its Terms explicitly permit models/internal tools and caching, and its documented schema covers goals, corners and cards. The plan/coverage contradiction for Italy Serie A and the missing per-fixture source timestamp/upstream provenance prevent a defensible source-before-quote approval today.
