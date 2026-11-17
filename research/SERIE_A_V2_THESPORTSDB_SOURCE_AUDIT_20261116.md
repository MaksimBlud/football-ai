# Original MARKET_ANCHOR_1X2_V2 — TheSportsDB free-source audit

**Audit date:** 2026-11-16  
**Decision:** `HOLD — technically relevant free V1 candidate; not approved for ingestion or inference`  
**Scope:** official TheSportsDB terms, API documentation, pricing page, public Serie A 2026/27 season page, and the API-statistics example linked by the official docs. No account was created, no API key was requested, no project API integration or bulk download was performed, no Supabase access occurred, and no model feature was built.

## Executive result

TheSportsDB is a more relevant candidate than a fixtures-only API: its public V1 documentation lists an event-statistics endpoint and the public website has an Italian Serie A 2026/27 season page. The provider's terms say API-returned content may be copied and modified, but explicitly condition third-party content on permission or a legal basis. The documented sample identifies an `idApiFootball` upstream ID. No licence or written permission for that underlying third-party statistics feed was found.

**The free endpoint sample does not establish coverage of the original V2's six corner features or card features.** The documented `lookupeventstats.php` sample contains five shot-stat rows only. The docs list a free limit of 5 for this endpoint and 100 for premium; they do not provide a complete field dictionary or prove that all Serie A events carry all statistics.

## Positive evidence

- The official terms permit copying and modifying content returned by official API endpoints, subject to third-party rights.
- Free V1 access is documented with public key `123`, and a 30-requests/minute rate limit.
- The API documentation lists `lookupeventstats.php` for event statistics; the documented free limit is 5, premium 100.
- The public site has an Italian Serie A 2026/27 season page. Its page currently claims 380 events; this is a website catalogue claim, not proof that the free API exposes every event or its complete statistics.
- The event-statistics example linked from the official docs returns five rows: Shots on Goal, Shots off Goal, Total Shots, Blocked Shots, and Shots insidebox. The sample rows include an `idApiFootball` value, indicating an upstream third-party identifier.

## Blocking gaps

1. **Third-party data rights remain unresolved.** Terms allow use of API-returned content but say third-party content cannot be used unless the owner has granted permission or it is legally permitted. The official example exposes an API-Football upstream ID. No upstream licence, rights chain, or written confirmation for internal ML research/inference and private raw-response retention was located.
2. **Six frozen corner features are not evidenced.** The official event-statistics example contains only five shot metrics. The public API reference does not publish a complete free-tier field catalogue showing corners-for/against. Do not infer availability from the generic label “event statistics.”
3. **Card mapping is not evidenced for the free tier.** Event timeline and statistics endpoints are listed, but the reviewed documentation does not provide a stable free-tier yellow/red card schema or second-yellow semantics suitable for exact feature parity.
4. **Free result limits may constrain completeness.** The event-statistics endpoint is documented with a free limit of 5 versus 100 premium. The example itself contains exactly five statistic rows. The docs do not clarify whether this is a response-row cap or another endpoint limit; it must not be interpreted as full statistical coverage.
5. **Serie A coverage is only a website-level signal.** The 2026/27 season page exists and claims 380 events, but free API fixture coverage, historical season access, event-statistics availability per fixture, and completeness have not been verified.
6. **Source-before-quote is not established.** No per-field upstream observation or correction timestamp is documented. A future lawful private archive could prove when this project received a response using receipt time and SHA-256, but that does not prove when the upstream statistic was first observed or corrected.
7. **Free V1 is legacy.** The docs describe V1 as the older API and V2 as premium-only and the future development path. Long-term free-tier stability is therefore uncertain.
8. **No odds endpoint is documented.** This candidate cannot replace the existing bookmaker market source.

## Frozen V2 contract — unchanged

- Candidate artifact SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb9be93074f39e1a7a5098`.
- Training fingerprint SHA-256: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- 3,799 training rows; 19 original features in their original order; weight matrix 20×2.
- `active_lambda=0` remains market-only; `shadow_lambda=1` remains research-only.
- Stability gate remains failed; automatic promotion remains disabled.

The audit does not change the candidate, weights, scaler, imputer, training fingerprint, or cohort contract.

## What would be required before reconsideration

- Written confirmation from TheSportsDB identifying the upstream statistics provider and granting rights to the underlying match-statistics data for internal ML research, inference, private raw retention, and SHA/timestamp provenance.
- A complete free-tier field dictionary with corners, yellow cards, red cards and second-yellow semantics.
- Documented free-tier access to the complete Serie A 2026/27 event set and sufficient historical seasons.
- Evidence that the free endpoint limits do not silently omit required statistic fields or events.
- A defensible pre-quote capture process and permission for private retention.
- Only after those gates: separately owner-authorized, low-volume sampling, private raw archive, SHA-256, receipt time, source-before-quote checks, and feature parity tests against the unchanged 19-feature builder.

## Official sources

- [Terms of Use](https://api.thesportsdb.com/docs_terms_of_use.php)
- [API Documentation](https://api.thesportsdb.com/documentation)
- [Pricing](https://api.thesportsdb.com/docs_pricing.php?billing=monthly)
- [Serie A 2026/27 season page](https://www.thesportsdb.com/season/4332-italian-serie-a/2026-2027)
- [Documented event-statistics example](https://www.thesportsdb.com/api/v1/json/123/lookupeventstats.php?id=1032723)
- [Provider forum note on event statistics](https://api.thesportsdb.com/forum_topic.php?t=6393)

## Explicit non-actions

No account, API key, project integration, bulk data download, private data archive, Supabase read/write/DDL, protected 2026/27 result read, feature build, inference, model refit, production `.pkl` change, paid request, schedule change, promotion, or bet. One documentation-linked public event-statistics example response was inspected solely to verify the documented sample fields.
