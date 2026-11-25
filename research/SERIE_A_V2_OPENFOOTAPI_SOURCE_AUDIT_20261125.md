# Original MARKET_ANCHOR_1X2_V2 — OpenFootAPI source audit

**Audit date:** 2026-11-25  
**Decision:** `HOLD_NO_FULL_19_FEATURE_COVERAGE`  
**Scope:** official OpenFootAPI documentation, pricing, coverage page and Terms of Service only. No account/key was created, no API request or data download was made, no Supabase access occurred, and no feature or inference was run.

## Executive result

OpenFootAPI is a **better rights/provenance candidate than several previously reviewed feeds**, but its free Starter plan is not a complete source for the unchanged original V2.

Positive findings from the provider's published Terms of Service:

- Internal statistical research, model training, evaluation and validation on data lawfully received are expressly permitted.
- There is no maximum retention period for responses received while access is valid; exact responses, normalized fields, derived aggregates, hashes and audit records may be retained.
- Every response carries `meta.sources`, and each `/v1/competitions` entry carries the applicable source licence.
- Upstream licence conditions remain binding; OpenFootAPI does not grant a right to redistribute an underlying provider feed.

Free Starter is $0/month, has no card requirement, 5,000 authenticated requests/month and a 60 requests/minute limit. It documents fixtures, scores, schedules, standings/form tables and team search across 120 competitions. Developer is $14/month and adds live events/commentary, lineups, xG/shot maps, SSE, webhooks and derived context. No paid plan or trial was used.

The public coverage page lists 2026/27 entries for the Premier League, La Liga, Bundesliga, Serie A and Ligue 1. That does not mean all fields are included in the free plan.

## Why the free plan cannot feed all 19 frozen features

The free Starter feature list does not include match events, lineups, xG or a match-level team-statistics endpoint. The public API reference documents events (goals, cards, substitutions, penalties and VAR), but not corner events or a match-level corner-count field. The Developer plan adds events/lineups/xG, but it is paid and still does not document a corner-count endpoint.

The original V2 contract must not be reduced or imputed to compensate for missing source fields. Therefore this candidate cannot presently provide complete, source-backed values for the unchanged 19-feature input contract.

A subset of results/standings may be useful for independent identity or goal/points reconciliation, but that is not authorization to run V2 or to mix partial features into a full prediction.

## Rights and source provenance

Official Terms of Service (effective 2026-09-07) state that internal statistical research, model training, evaluation and validation are permitted for data lawfully received. Exact responses and audit records may be retained without a maximum period. The same terms say source licences attach independently and that access through the API is not a licence to redistribute the underlying provider feed.

The docs advertise `meta.sources` on responses and a licence field for each competition in `/v1/competitions`. The docs do not expose the actual per-competition licence values for every top-five competition without an API response; those values must be checked before any future capture. The docs identify OpenFootball CC0-1.0 as the archive source for Premier League, La Liga, Serie A and Ligue 1, but the exact competition metadata still needs to be preserved from any lawfully obtained response.

The docs provide UTC timestamps and a `fetched_at`/freshness signal for the live endpoint, but do not document per-field upstream first-seen or correction timestamps. A private raw-response archive with a local receipt timestamp and SHA-256 could prove that this project possessed a particular response before a later quote. It cannot prove when the upstream provider first published or corrected a field.

The free plan is described as suitable for side-projects and testing; commercial use is expressly listed under Pro. Commercial rights for the free plan are therefore **not treated as granted**.

## Frozen V2 invariants

- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`
- Exactly 19 original features; 20×2 original weight matrix.
- `active_lambda=0` remains the market.
- `shadow_lambda=1` remains research-only.
- Historical stability remains FAILED.
- Prospective outcome gate remains CLOSED at 0/30.
- No model, scaler, imputer, weights, feature order, threshold or production artifact is changed by this audit.

## Decision and non-actions

**HOLD.** Do not create an account/key, call the API, download data, build features or run inference for V2 on this evidence. Revisit only if the provider documents a free, lawful source for all missing frozen feature families and the exact per-competition upstream licence metadata is verified.

No API request, account/key creation, raw-data capture, odds read, Supabase access/write/DDL, protected 2026/27 outcome read, feature build, inference, refit, production `.pkl` change, threshold tuning, schedule change, main update, merge, promotion or bet occurred.
