# Original MARKET_ANCHOR_1X2_V2 — SoccersAPI free Serie A source audit

**Audit date:** 2026-11-18  
**Decision:** **HOLD — promising technical coverage, unresolved rights and free-plan scope**  
**Scope:** documentation-only source audit for the frozen original V2. No account, API request, download, Supabase access, odds request, feature calculation, inference, or outcome read was performed.

## Why this candidate is worth keeping

SoccersAPI's current public documentation describes a free API plan with three leagues and 100 requests/day. Its v2.2 fixture detail operation explicitly lists the stats include as available on the Free plan. The fixture schedule operation also supports stats include within the leagues covered by the account. The public Italy page lists Serie A, shows a 2026/27 current-season table (11 rounds / 100 matches on the page checked), and marks the Serie A archive with match statistics.

The documented team-stat payload examples expose goals, corners, yellow cards, red cards, shots, shots on target, fouls and possession. Those fields are technically relevant to the original V2's frozen 19-feature vector:
- 9 result/points/goals-derived features;
- 6 corner features;
- 2 yellow-card features;
- 2 red-card features.

This makes SoccersAPI a more promising current-season technical candidate than sources that omit red cards or corners. It is not yet a qualified source: no actual Serie A response was requested, no per-match completeness was measured, and the 19-feature mapping has not been parity-tested against the original feature builder.

## Free-plan and coverage ambiguity

The pricing/home pages advertise a free plan with three leagues and 100 requests/day. The Italy page separately says the free key reaches all 31 Italian competitions. These statements do not clearly establish whether a free account can select Serie A while retaining the required fixture/statistics operations, or whether the country page describes the overall catalogue rather than the account entitlement.

The fixture docs state that fixtures match detail is available on Free and that the stats include is also available on Free. The fixture schedule docs support stats include for a league within the account's plan scope. The standalone stats match route has a different plan matrix; do not substitute it or assume all statistics endpoints are free. Any future integration must use only the exact Free-plan operation confirmed by the provider and must fail closed on a plan-denied response.

The public Italy page was last updated 2026-11-07 and showed 11 rounds / 100 Serie A matches. It does not prove that every one of those matches has complete corners, yellow cards and red cards, or that the free account can retrieve those fields for all of them.

## Rights are not cleared

The SoccersAPI Terms of Service last updated 2025-02-22 state that:
- the data/material is protected by copyright;
- copyright/proprietary notices must be retained on copies;
- public or commercial use of the material is prohibited unless authorized;
- data obtained through the service remains SoccersAPI intellectual property;
- attribution is required in publications or distributions.

The terms do not explicitly grant the project a right to retain raw API responses privately for model training or internal noncommercial ML experiments. They also do not identify upstream field-level rights. This audit therefore does not interpret silence as permission. Written provider clarification is required before account creation, automated access, raw-data retention, feature engineering, or inference for this project.

No redistribution of raw data, source artifacts or derived datasets is proposed. No public or commercial use is authorized by this audit.

## Provenance and source-before-quote

The docs expose match IDs and kickoff timestamps, but the reviewed documentation does not establish per-match first-observation or per-field correction timestamps. The event guide explicitly warns that event attribution can be corrected or backfilled during and shortly after a match and does not promise a fixed maximum attribution delay.

If rights are later cleared, a future capture could record the exact response bytes, request parameters (excluding credentials), client receipt time, response metadata, and SHA-256 before any quote read. That would prove the project possessed those bytes before a later quote; it would not prove when SoccersAPI or its upstream provider first observed each field. No source-before-quote evidence exists now because no API call or source capture was made.

## Frozen V2 invariants

This audit pins, but does not alter:
- candidate SHA-256: a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6;
- training fingerprint: f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098;
- 19 original features and their frozen order;
- 20 × 2 weight matrix;
- active_lambda=0 (market anchor);
- shadow_lambda=1 (research only);
- failed stability gate and no automatic promotion.

No historical refit, threshold tuning, source substitution, production .pkl change, or evaluation-contract change is proposed.

## Required clearance before any implementation

1. Written confirmation that internal noncommercial model research, feature derivation and private raw-response retention are permitted under the free plan.
2. Confirmation that the free three-league entitlement can include Italy Serie A and that fixture-level include=stats is available for it.
3. Confirmation of upstream provider identity/rights for scores, corners and cards.
4. A real per-match coverage report for Serie A 2026/27, including null/missing semantics for corners, yellow cards and red cards.
5. A documented response/correction-time policy sufficient to define the project receipt-time evidence.
6. Only after all of the above: a separately reviewed, secret-safe, source-before-quote capture adapter. No odds endpoint is needed; the existing saved pre-match market remains the comparator.

## Official documents reviewed

- Pricing: https://soccersapi.com/pricing
- Terms (last updated 2025-02-22): https://soccersapi.com/terms
- Italy coverage: https://soccersapi.com/our-football-api-data/italy
- Fixture match detail / Free-plan stats include: https://docs.soccersapi.com/fixtures/info/
- Fixture schedule / stats include: https://docs.soccersapi.com/fixtures/schedule/
- Dataset include guide: https://docs.soccersapi.com/guides/match-events-and-dataset-includes/
- Stats field example: https://docs.soccersapi.com/livescores/live/

**Bottom line:** SoccersAPI merits a written rights/plan clarification request, not an integration. The free documentation is technically promising, but rights, league entitlement, and actual 19-feature coverage are not yet proven.
