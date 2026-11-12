# Footballdata.io — free Serie A source and rights audit

**Decision: HOLD — not an approved free source for original MARKET_ANCHOR_1X2_V2.**

Audit date: 2026-11-12  
Repository base: `40887ebb215730190d7a6c7a1693373ec4afcdfc`  
Scope: official public documentation only. No account, API key, API request, source download, Supabase access, odds read, feature build, inference, or target-outcome read.

## Executive result

Footballdata.io is not a viable *free* Serie A source under its published plan matrix. The free plan lists five competitions (World Cup, Premier League, La Liga, UEFA Champions League and UEFA Europa League); Italy Serie A is listed under Starter. The source's own pages also conflict on which plan includes match/team statistics: the homepage pricing bullets say Free includes Match Stats, while the data-access matrix labels Match Stats and Team Stats as Pro; the dedicated match-stats example reports `meta.plan = starter`. This ambiguity is not enough to authorize a free integration.

The terms allow API responses to be used for applications, analysis tools, prediction products and internal systems, but they restrict raw-data redistribution and say long-term storage, bulk replication, data warehousing or rebuilding a competing football database may require written permission or an enterprise agreement. The terms do not explicitly grant AI/ML training or long-term research-archive rights. The service also says it may rely on third-party data providers without identifying field-level upstream rights in the reviewed pages.

The public examples do not establish per-field upstream observation timestamps, correction history, or an auditable source-before-quote clock. Therefore SHA-256 of a later downloaded response would prove byte integrity, not that the underlying statistics were observed before the bookmaker quote.

## Official evidence

| Area | Published evidence | V2 decision |
|---|---|---|
| Free competition coverage | Free plan lists five competitions; Serie A appears under Starter | **FAIL** for free Serie A |
| Match statistics | Corners, shots, possession, fouls and cards are advertised, but plan access conflicts across pages | **UNVERIFIED** |
| Team form | Team stats/form are described as Pro in the pricing matrix | **FAIL** for free current-form use |
| Retention | Reasonable caching is allowed; long-term storage/bulk replication may need written permission or Enterprise | **HOLD** |
| AI/ML training | No explicit grant found in reviewed Terms | **HOLD** |
| Upstream rights | Third-party data providers are mentioned, but provider/field licence is not identified | **HOLD** |
| Source-before-quote | No field-level upstream observation or correction timestamp demonstrated | **FAIL** as provenance proof |
| Raw redistribution | Raw API data may not be redistributed as a standalone feed/database without written permission | Must remain private; no raw publication |

## Exact official pages reviewed

- Homepage, pricing and feature-access matrix: https://footballdata.io/
- Leagues by plan (the Free list excludes Italy Serie A; Serie A is in Starter): https://footballdata.io/leagues-by-plan/
- Match statistics endpoint overview: https://footballdata.io/football-match-stats-api/
- Team statistics endpoint overview: https://footballdata.io/football-team-stats-api/
- Terms of Service (last updated 2026-05-03): https://footballdata.io/terms/
- Privacy Policy (last updated 2026-05-03): https://footballdata.io/privacy/

Relevant terms sections: §6 (Free plan may be for testing/development/small or non-commercial use), §10 (commercial use may require a paid plan), §11 (permitted API-response uses and raw-data redistribution restriction), §12 (reasonable caching vs written permission/Enterprise for long-term storage, bulk replication or data warehousing), and §22 (third-party data providers).

## Binding V2 boundary

- Original candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- The 19-feature order, weights, scaler/imputer, training fingerprint and frozen contract are unchanged.
- `active_lambda=0` remains the market; `shadow_lambda=1` remains research-only.
- No integration, API key, source capture, archive, quote read, inference, outcome read, model refit, Supabase write/DDL, production `.pkl` change, schedule change, bet, or promotion is authorized by this audit.
- Do not treat API response SHA as source-time proof. A future candidate would need written scope for Serie A on a zero-cost plan, explicit AI/ML research and retention permission, field-level definitions/upstream lineage, and an upstream observation timestamp that can be proven strictly before each quote.

**Final status: `HOLD_NOT_FREE_FOR_SERIE_A_RIGHTS_AND_PROVENANCE_UNRESOLVED`.**
