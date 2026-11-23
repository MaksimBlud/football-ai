# SportAPI free current-season source audit — original MARKET_ANCHOR_1X2_V2

**Checked:** 2026-11-23 06:49 UTC  
**Provider:** [SportAPI.ai](https://sportapi.ai/) (Semalt LLC)  
**Decision:** **HOLD — no integration, account, API key, request, download, feature calculation or inference.**

## Executive finding

SportAPI is a technically plausible no-cost source candidate for current-season Serie A fixture metadata and some match statistics. Its official guide identifies Italian Serie A as league ID `3` and shows a 2026/27 standings example. The Free plan advertises all endpoints and leagues.

It is **not currently an acceptable full source for the frozen V2 contract**. The reviewed match-statistics schema does not document corners, while the original 19-feature model contains six corner-dependent features. Exact per-fixture 2026/27 completeness is not established. Legal rights for internal ML use, upstream field ownership and private raw-response retention are also unresolved.

No provider API endpoint was called. Only public official documentation and terms were reviewed.

## Free plan and availability

The official pricing/documentation pages state:
- $0 Free plan;
- all endpoints and leagues are advertised as included;
- through 30 November 2026: 2,000 requests/day and 14,000/month;
- from 1 December 2026: 1,000 requests/day and 7,000/month;
- an API key and account are required;
- no betting-odds endpoint is provided.

The official Serie A guide identifies Italy's Serie A as league ID `3` and shows a 2026/27 table. This proves a public product example exists, not complete per-match statistical coverage for every Serie A fixture.

## Mapping against the unchanged 19 features

The reviewed documentation describes:
- standings: played, wins, draws, losses, goals for/against and points;
- match events: goals, yellow cards, red cards and substitutions;
- fixture statistics: shots, shots on target/off target, fouls, passes, tackles, saves and yellow cards.

The reviewed fixture-statistics and event examples do **not** document corner totals. Therefore the following original V2 features cannot be shown to have a source mapping from this API:
- `diff_corners_for_5`;
- `diff_corners_for_10`;
- `diff_corners_against_5`;
- `diff_corners_against_10`;
- `diff_corners_for_venue5`;
- `diff_corners_against_venue5`.

No feature substitution, reweighting or change to the original contract is proposed. Missing corner data must not be silently replaced with a different statistic or presented as full 19-feature coverage.

The provider states that detailed statistics vary by competition. There is no reviewed per-fixture completeness matrix for Serie A 2026/27. The historical depth available to the Free plan is not clearly documented in the pages reviewed.

## Rights and storage

The Terms of Use, last updated 20 November 2026, say the data may be used in one's own websites, apps, analysis and products. They prohibit reselling, sublicensing or redistributing the raw data as a feed or competing API.

The reviewed Terms do not expressly resolve:
1. internal ML model training on derived historical statistics;
2. inference using those derived features;
3. long-term private retention of exact raw response bytes for reproducible research;
4. the upstream providers and field-level rights for the underlying scores, goals, corners and cards.

The provider says it collects sports data from public sources, but the reviewed legal pages do not identify the upstream sources or their field-level licences. The broad permission to use data in "analysis and products" is not silently treated as an explicit ML-training, inference or archival licence.

Written clarification is required before any account creation or data use.

## Source-before-quote and timestamps

The API documentation says `kickoff_utc` and `updated_at` are UTC. Its example fixture has kickoff `2026-10-10T11:30:00Z` and record `updated_at` `2026-10-11T01:43:09Z`.

The reviewed documentation does not define `updated_at` as a per-field first-observation timestamp or correction timestamp. It also does not document per-field correction history or provider first-observed time. ETag support is documented, but that is not a correction-history contract.

If written rights and feature coverage are later cleared, an authorized client could preserve the exact response bytes, request parameters (excluding credentials), response headers, local receipt UTC time and SHA-256 in private storage before any later market-quote read. That would prove the project possessed those exact bytes before the quote; it would not prove when an upstream provider first observed each field.

No such capture occurred in this audit.

## Frozen V2 invariants

This audit pins, without changing:
- candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`;
- 3,799 training rows;
- exact original 19-feature order and 20 × 2 weights;
- `active_lambda=0` (market anchor);
- `shadow_lambda=1` (research only);
- failed stability gate and no automatic promotion.

## Required clearance before reconsideration

1. Written permission for internal model training and inference using the Free-plan data.
2. Identification and confirmation of upstream rights for every required field.
3. Complete per-fixture 2026/27 Serie A coverage for the exact original 19-feature inputs, especially all corner fields and red-card handling.
4. Clear historical retention horizon on the Free plan.
5. Clarification of `updated_at`, first-observation and correction semantics.
6. Written permission to retain exact raw responses privately for the research/audit period.

## Official documents reviewed

- Terms: https://sportapi.ai/terms
- Pricing: https://sportapi.ai/pricing
- API documentation: https://sportapi.ai/docs
- Coverage: https://sportapi.ai/coverage
- Serie A guide: https://sportapi.ai/guides/serie-a-website
- Serie A example: https://serie-a.sportapi.ai/

**Bottom line:** keep SportAPI on HOLD. It is a free technical candidate for partial current-form inputs, not a cleared replacement for the complete original V2 source. No provider access or model operation is authorized by this audit.
