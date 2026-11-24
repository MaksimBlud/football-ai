# Original MARKET_ANCHOR_1X2_V2 — 5DollarFootballAPI source audit

**Audit date:** 2026-11-11  
**Scope:** official public terms, pricing/eligibility pages, API documentation, Serie A coverage and data-quality pages only. No account was created, no key was requested, no API endpoint or odds endpoint was called, no match payload or quote was fetched, and no data archive was downloaded.

## Decision

**5DollarFootballAPI is the strongest no-cost source candidate found so far, but it is not approved for V2 ingestion yet.** A fresh review of its current pricing and documentation clarifies that the Free plan explicitly includes the top-five leagues (including Serie A) and the last three months of results; the dedicated Serie A page also claims free current-season fixtures, goals, corners, cards and odds. The data-quality table labels Italy Serie A “Pro” in its twelve-month coverage view, which is more plausibly a historical-depth distinction than a contradiction about current-season fixtures. However, the exact Free-plan entitlement for every required goals/corners/yellow/red field is not independently confirmed by an authenticated response. Terms explicitly permit models/internal tools and caching, subject to attribution for public display and no raw-feed redistribution.

No account, key, API call or data download was made. Do not create an account, self-attest for Community Access, call the API, or integrate until the owner authorizes the source and private-archive approach, and the remaining field-level rights/semantics questions are resolved. No paid plan is proposed or authorized.

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

## Free-plan access and the current-season versus historical-depth distinction

The public pages describe three relevant access levels:

| Access | Published price | Published limits/history |
|---|---:|---|
| Free | $0 | Top-five leagues (EPL, La Liga, Serie A, Bundesliga, Ligue 1); 60 requests/hour, 20/minute ceiling; last 3 months of results/odds |
| Community Access | $0 for eligible users | Top-five leagues plus one selected country pack; 300 requests/hour, 20/minute ceiling; last 12 months of results/odds; 12-month activation/renewal |
| Pro | $5/month | 137 competitions and broader coverage/history; paid and therefore not authorized |

Community Access is described for students, academic/non-profit researchers, early-career developers, or anyone for whom $5/month is a meaningful expense. It requires the account holder to select the applicable eligibility statement and a country pack. Eligibility must not be assumed or self-attested by this automation on the user's behalf.

**Clarified interpretation from the 2026-11-12 public-page review:**
- The pricing page explicitly lists Serie A among the Free plan's top-five leagues and says Free returns the last three months of results/odds.
- The dedicated Serie A page explicitly says Serie A fixtures, goals, corners, cards, odds and full statistics are included in Free.
- The data-quality table reports Italy Serie A as “Pro” in a table measuring the preceding twelve months and thirteen seasons. The API docs separately state that Free has three months of history, Pro twelve months, and Ultra full history. This likely describes the deeper historical archive rather than current-season access; the table does not define the Plan column clearly enough to treat this as settled.
- Community Access is a separate $0 plan for users who select an applicable eligibility statement, with top-five leagues plus one country pack, 300 requests/hour and twelve months of history. This automation must not self-attest or activate it.

**Remaining uncertainty:** no authenticated Free-plan response has been inspected, so the precise availability and completeness of the required goals/corners/yellow/red fields for current-season Serie A remains unverified. The 380 versus 385 finished-match counts were published at different refresh times (data-quality table 2026-11-11; dedicated Serie A page crawled 2026-11-12) and should not be treated as a stable contradiction. No paid plan or endpoint test is authorized.

No Pro, Ultra, Business, Edge, or other paid access may be used.

## Publicly documented Serie A coverage

The dedicated Serie A page reports:
- league id 3405541143;
- 4,803 fixtures on record and history since 2014;
- 385 finished matches in its last-12-month summary when reviewed 2026-11-12;
- 9.0 corners and 3.5 cards per match in that summary;
- an explicit claim that Serie A goals, corners, cards, odds and full statistics are available in the Free tier.

The data-quality page, generated 2026-11-11 05:05 UTC, reports the Italy Serie A row as:
- plan: **Pro** in its twelve-month/seasonal completeness table;
- 380 finished matches in the preceding 12 months;
- corners: 100%;
- half-time corners: 100%;
- corner line: 100%;
- odds: 100%;
- events: 100%;
- live stats: 100%;
- first season: 2014, 13 seasons.

The 380 versus 385 figures were refreshed on different dates and may simply reflect the five additional finished fixtures between page snapshots; this is not evidence of a data-quality defect. The data-quality HTML exposes a global cards aggregate but not a separate per-league cards percentage. Do not infer 100% card completeness from the global 99.8% figure or the Serie A average of 3.5 cards/match.

These are provider-published aggregate claims, not independently measured data quality. The exact 2026/27 per-match completeness and Free-plan field entitlement remain unverified because no authenticated endpoint was called.

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

## 2026-11-12 public-doc clarification addendum

The current pricing page now explicitly lists the top-five leagues, including Serie A, on the $0 Free plan, with three months of results/odds. The dedicated Serie A page says its goals/corners/cards/statistics and odds are included in Free. The “Pro” label on the data-quality table is attached to a twelve-month/13-season coverage view; the general docs say Free is limited to three months and Pro to twelve months. This makes the apparent Free-vs-Pro conflict more likely a history-depth distinction, but it does **not** prove the authenticated Free endpoint returns every required current-season field. The public pages remain mutable; the exact versions should be SHA-archived before any authorized use.

The API docs show fixture-level `goals`, `corners`, `cards.yellow` and `cards.red`, plus `kickoff_utc` and explicit `status=finished`. The docs do not show a per-fixture `updated_at` or upstream source-observed timestamp. The public status page measures live-stat age and event-capture delay, not a per-fixture historical-stat publication time. A future capture could prove **our collector received the exact raw response before the later quote** using local request/response timestamps plus raw-byte SHA-256; it could not claim the provider's upstream publication time without a provider attestation.

The original frozen feature builder needs exactly 19 differences over points, goals for/against, corners for/against, yellow and red cards, with 5/10-match and venue-5 windows. The documented fixture fields cover those raw-data families, but field-level compatibility is not proven. Required source-concordance checks remain: second-yellow/red semantics, null-versus-zero, corner/card completeness, team identity mapping, abandoned/postponed handling and regular-time-only results. No source response has been obtained, so no parity claim is made.

The Free three-month window may cover the current 2026/27 season's rolling form at this date, but coverage per team and all required fields must be measured without shortening the frozen windows or changing imputation. It cannot replace the original 2016–2026 training archive. Community Access may provide twelve months, but eligibility is a user attestation and must not be selected by automation.

## Final disposition

**Promote 5DollarFootballAPI to the first candidate for a future no-cost, current-season source-concordance test, but keep ingestion blocked.** Terms explicitly permit model/internal-tool use and caching, with public attribution and no raw-feed redistribution. The remaining blockers are authenticated field-level Free-plan confirmation, upstream field-rights/semantics clarification, a private raw-response archive, and the source-before-quote attestation policy. No account, key, API request, odds request, source download, Supabase write, inference, target-outcome read or production change occurred.

## Official documentation re-check — 2026-11-15/16 UTC

The provider's current October 2026 Terms now give a clearer contractual statement for the API customer's use: data may be used in commercial products, websites, apps, models and internal tools; responses may be cached; public-facing Free/Community/Education products require attribution; raw data may not be resold or redistributed as a competing feed. This is materially more explicit than a generic "no resale" clause. It does not, by itself, document the upstream source/rights chain for every competition.

Official references:
- Terms of Service (last updated October 2026): https://5dollarfootballapi.com/terms
- Data freshness & rights / API docs: https://5dollarfootballapi.com/docs
- Serie A product page: https://5dollarfootballapi.com/serie-a-api
- Machine-readable/HTML measured data quality: https://5dollarfootballapi.com/docs/data-quality
- Pricing: https://5dollarfootballapi.com/pricing

### Positive evidence

1. Terms §4 and the API docs' “data freshness and rights” section explicitly allow model/internal-tool use and response caching. Free-plan attribution is required only when displayed in a public-facing product; private/internal use is exempt.
2. The dedicated Serie A page explicitly says “Included in the free tier”, and its FAQ says odds and full statistics are included on Free. It currently shows Serie A fixtures, round 11, latest results dated 8 November 2026, and upcoming fixtures on 21–22 November.
3. The Serie A page describes goals, corners, cards (full-time/half-time), live statistics and fixture-level odds. The generic fixture response example documents UTC kickoff, status, goals, corners, yellow/red cards, statistics and event data.
4. The generic Free plan is documented as 60 requests/hour (also 20/minute), with no daily/monthly pool; Free history is only the last three months. Pro gives 12 months; Ultra gives full history.

### Blocking contradiction — plan entitlement

The dedicated Serie A page says Free, but the provider's measured data-quality table lists the exact same competition (Italy Serie A, league id 3405541143) as **Pro**, despite reporting 380 finished matches over the last 12 months and 100% coverage for corners, half-time corners, corner line, odds, events and live statistics. The pricing page says Free includes the top five leagues, while the data-quality table labels Serie A Pro. These first-party pages conflict; do not infer Free entitlement from the marketing page alone.

The documentation also clarifies that Free history is three months, not the full history back to 2014. “History since 2014” describes the provider's stored depth, not what a Free key can retrieve. As of 15 November 2026, the three-month window would nominally cover the 2026/27 season start, but actual Free-plan access and row completeness have not been verified.

### Source timestamp / provenance

The public fixture response example exposes UTC kickoff and match/status fields but no per-fixture source-ingestion/observed timestamp. The provider publishes measured freshness separately on its status page. Therefore any future prospective capture must preserve the exact raw response bytes, record our own captured_at_utc at receipt, and SHA-256 the bytes. It must never relabel local capture time as the provider's upstream observation time. The frozen V2 source-before-quote gate must compare this local capture timestamp strictly against the independently sourced quote snapshot time and kickoff. No historical pre-kickoff claims can be reconstructed from a response downloaded after the fact.

### Decision

**HOLD — no account, API key, request, data download or integration.**

Before any live capture, require written provider confirmation of all three:
- Italy Serie A is included in the actual Free plan for the current account/key (the measured coverage table currently says Pro);
- the Free plan exposes the required fixture/statistics fields and the full current-season window;
- the provider has authority to grant the stated internal ML/caching permissions for the supplied Serie A data, including any upstream data partners.

If these points are confirmed, the existing offline adapter can be evaluated for prospective 2026/27 collection only. It must store raw bytes, local capture time, response SHA, provider/endpoint/plan metadata and page completeness; then enforce source capture < quote snapshot < kickoff. No paid upgrade, no odds endpoint use, no backfilled historical inference and no production writes.

No API calls, credentials, Supabase operations, protected outcome reads, model inference or production changes were made during this audit.


## Official endpoint-schema re-check — 2026-11-21 UTC

The current official [League fixtures endpoint documentation](https://5dollarfootballapi.com/docs/league-fixtures) now provides a sufficiently explicit *request-level* season contract for the offline adapter:

- `GET /v1/leagues/{id}/fixtures` is described as the bulk entry point for a league's fixtures/results; it supports a `season` parameter, described as the season listed for the league (examples `2026` or `26/27`) and says this parameter selects that season's kickoff window.
- The endpoint supports pagination, with `per_page` up to 100, and no 24-hour span cap for the league-specific route.
- Its published fixture example includes `id`, `league.id`, `kickoff_utc`, `status`, `status_reason`, `status_code`, `goals`, `corners`, and `cards.home/away.yellow/red`.
- The published fixture example does **not** document a per-fixture `league_season_id`. The season is instead pinned by the request URL's `season` parameter. A client must not require an undocumented field when the published response schema does not promise it.

The generic [List fixtures documentation](https://5dollarfootballapi.com/docs/fixtures) independently states that Free history is limited to three months and its response example also shows the exact raw families needed by the frozen 19 features: goals, corners, yellow cards and red cards. The original candidate's 19 features use points derived from goals plus goals-for/against, corners-for/against, yellow cards and red cards (5/10-match and venue-5 windows); they do not require shots, possession or xG. This improves the *documented schema-family fit*, but does not establish authenticated Free-plan completeness or source parity.

The dedicated [Serie A page](https://5dollarfootballapi.com/serie-a-api) continues to claim Free access and shows 2026/27 round-11 results and upcoming fixtures dated 21–22 November 2026. This remains a provider-published claim, not an authenticated Free-key response. The measured data-quality page's Pro label and the missing upstream-rights/retention details remain unresolved.

### Adapter consequence

The offline-only [PR #800](https://github.com/MaksimBlud/football-ai/pull/800) was updated on 2026-11-21 to:
- require the exact Serie A league-fixtures endpoint and `season=2026` in every captured page URL;
- stop requiring undocumented `league_season_id` in each fixture or capture manifest;
- retain an optional fixture/manifest season-id cross-check if both values are supplied;
- use synthetic fixtures matching the published response shape, without a per-fixture season id.

This is a schema-compatibility correction only. It does not activate the source, weaken any rights gate, or change the original V2 feature/model contract.

### Disposition unchanged

**HOLD — no account, key, API request, odds request, data download, Supabase operation, source archive, feature calculation, inference, or target-outcome read.** Before any use, written confirmation is still required for actual Free-plan Serie A access and completeness, upstream rights for internal model use, and private raw-response retention. The provider's published terms permit model/internal use and caching, but do not identify the upstream rights chain or a durable private-retention term. Local receipt time and raw-byte SHA can prove what this collector received before a later quote; they cannot substitute for a provider-guaranteed upstream observation timestamp.

The existing adapter remains offline-only and the original `active_lambda=0`, `shadow_lambda=1`, 19 features, weights, scaler/imputer and evaluation gate remain unchanged.


## Current-season Free-window sufficiency check — 2026-11-21 UTC

A date-window calculation improves the practical feasibility assessment without changing the HOLD decision:

- The official [Lega Serie A calendar](https://www.legaseriea.it/serie-a/news/le-date-della-stagione-2026-2027) says the 2026/27 season starts on the weekend of 23 August 2026; its [first-round announcement](https://www.legaseriea.it/serie-a/news/ecco-la-prima-giornata-della-serie-a-enilive-2026-27) lists matches on 22–24 August.
- The provider's [Serie A page](https://5dollarfootballapi.com/serie-a-api), crawled 2026-11-21, shows round 11 and all 20 teams at 11 played; its latest listed results are 7–8 November and upcoming fixtures 21–22 November. That implies 110 completed league fixtures through round 11 (20 teams × 11 appearances / 2).
- The Free plan publishes a three-month results window. On 2026-11-21, a three-calendar-month lookback begins around 2026-08-21, so the published season start and all 11 rounds nominally fit inside that window. This is enough in principle for the original model's last-10 team windows and venue-specific last-5 windows, provided every match and required statistic is returned.
- The league-fixtures endpoint permits `per_page=100`, has no 24-hour span cap, and paginates the season-scoped result set. A 110-fixture round-11 corpus would therefore require two pages at most, below the Free plan's published 60 requests/hour.
- The 19 frozen features require goals (for/against and derived points), corners (for/against), and yellow/red cards. The provider's public Serie A page says goals, corners and cards are present on every fixture and claims full statistics on Free.

This is a **published-plan feasibility estimate, not a measured Free-key result**. It does not prove that the actual account/key receives all 110 fixtures, all required fields, or complete/consistent card/corner values. The separate measured data-quality table still labels Italy Serie A Pro. No authenticated response has been captured, and no upstream observation timestamp is documented.

**Disposition remains HOLD.** The source is now the strongest no-cost candidate for a narrowly scoped, authorized conformance test because its published three-month window nominally covers the 2026/27 10-match feature history at round 11 and the request count is small. Before any account/key or capture, still require written confirmation of Free-plan Serie A entitlement and required-field completeness, upstream rights for internal model use, and private raw-response retention. No API key, API/odds request, download, inference, or Supabase operation was performed for this calculation.

## Official-plan re-check — 2026-11-24 UTC (public pages only)

The provider now documents a second **$0 Community Access** route more explicitly. This is a possible free entitlement path, not an authorization to use it:

- The [Community Access page](https://5dollarfootballapi.com/community) describes a $0 plan for users who truthfully select one of the published eligibility categories (student; academic/non-profit research; early-career developer; or someone for whom US$5/month is a meaningful expense).
- It adds the top-five leagues plus one selected country pack, 12 months of results/odds history, 300 requests/hour with a 20/minute ceiling, and a 12-month activation/renewal period.
- The page says the account holder selects the applicable eligibility statement and country pack. **This automation must not select a category, self-attest, create an account, or activate Community Access on the user's behalf.**
- The page permits model/internal-tool use and response caching, with attribution for public-facing products and no raw-feed resale/redistribution. The provider's [Terms](https://5dollarfootballapi.com/terms) state the same general use restrictions.

The [pricing page](https://5dollarfootballapi.com/pricing) distinguishes Free (last 3 months) from Community (last 12 months). The [Italy Serie A data-quality page](https://5dollarfootballapi.com/docs/data-quality/3405541143), freshly recounted on 2026-11-24, labels Italy Serie A as Pro and Ultra for its 12-month/13-season table; it reports 380/380 finished matches in the last 12 months with 100% corners, half-time corners, corner lines, odds, events, live statistics and cards. Its season table reports 110/110 finished 2026/27 fixtures through 2026-11-09 with 100% for those fields. These are aggregate provider-published completeness figures, not match-level outcomes and not an authenticated Community response. The dedicated [Serie A page](https://5dollarfootballapi.com/serie-a-api) continues to claim the league and full statistics are in Free. The plan/coverage distinction therefore remains unverified for an actual account.

### Implication for the frozen 19 features

The unchanged original `ALL_FOOTBALL` feature set contains 19 differences over points, goals for/against, corners for/against, yellow cards and red cards (5-match, 10-match and venue-5 windows). The existing offline adapter maps only these documented raw families. The public fixture schema documents goals, corners and yellow/red totals; no shots, possession or xG are required by this feature set. This is schema-family compatibility only: exact card semantics (especially second-yellow/red treatment), null-versus-zero behavior, team-side mapping and actual Community/Italy entitlement remain unverified.

### Decision remains HOLD

Community Access is a plausible no-cost route only if the account holder independently and truthfully qualifies, selects Italy, and later verifies that the activated account actually returns the required Serie A fixtures/fields. No such eligibility or activation is assumed here. The provider still has not publicly identified the upstream rights chain for these fields or documented a durable private research-archive retention term. The current adapter's pinned rights manifest therefore remains HOLD; its Community-plan rejection remains intentional until separate eligibility and entitlement approval are recorded.

No account/key was created, no eligibility statement was selected, no API or odds endpoint was called, no provider data was downloaded or archived, no feature calculation/inference was run, no Supabase operation occurred, and no 2026/27 match-level outcome was accessed. No paid plan or paid request is proposed.
