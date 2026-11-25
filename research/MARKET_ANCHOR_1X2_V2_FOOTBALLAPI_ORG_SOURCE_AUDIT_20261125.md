# MARKET_ANCHOR_1X2_V2 — footballapi.org source audit

**Decision: `HOLD_WRONG_LEAGUE_AND_UNPROVEN_RETENTION_RIGHTS`.**

This is an offline documentation audit of the distinct provider at `footballapi.org` (operated by DeveloperData.net), not API-Football / API-Sports. No account, key, API request, source download, Supabase access, feature build, or inference was performed.

## Relevance to the frozen candidate

The original candidate in this repository is the Serie A frozen V2 candidate:

- experiment: `MARKET_ANCHOR_1X2_V2`;
- candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- frozen features: 19;
- original weight matrix: 20×2;
- `active_lambda=0` (market);
- `shadow_lambda=1` (research only).

The complimentary Football API key reads **only the current Premier League season**. It does not provide Serie A under the free plan. Membership is paid and is excluded by the project constraints. This league mismatch alone prevents this source from feeding the original Serie A V2 candidate.

## What the documented match-stat endpoint appears to cover

The official `GET /v1/matches/{match_id}/stats` documentation describes per-side fields including corners, expected goals, fouls, offsides, yellow/red cards, shots, shots on target and possession. These field families overlap some inputs used by football-history feature builders, but this audit did not establish an exact one-to-one mapping for all 19 frozen V2 features. No feature contract is changed.

The complimentary key is documented at 50 calls/day and 10 calls/minute. This is not a reason to batch-download or reconstruct a historical collection.

## Rights and retention

The official Terms of Use (last updated 2026-10-21) say that API data may be used in one's own work, apps and sites and shown to one's own users. They also prohibit reselling, redistributing or republishing the data itself, bulk downloading it to rebuild the collection, and using it to build a competing product.

The published terms do **not clearly specify**:
- whether raw match-stat responses may be retained indefinitely in a private research archive;
- whether those responses may be used to train or evaluate a private machine-learning model;
- whether a response's `request_id` or other metadata provides an upstream first-seen or correction timestamp;
- whether derived 19-feature rows may be retained under the same conditions.

The example match-stat response documents `kickoff_utc`, `match_status`, statistics and a request ID, but no per-field first-seen/correction time. A local receipt timestamp and SHA-256 could prove when this project possessed a response; it would not independently prove when the provider first published or corrected each field.

The terms therefore do not provide enough explicit clearance for the required private raw archive, frozen-model training/inference use and source-before-quote provenance contract.

## Binding decision

- **HOLD**: no integration, account/key creation, API request, capture, or inference.
- Do not use the complimentary EPL feed as a substitute for Serie A.
- Do not buy the paid membership.
- Reconsider only if a genuinely free Serie A feed is documented and the provider clarifies private retention, ML research use, bulk limits and source publication/correction chronology.
- Keep the original candidate, 19-feature order, weights, scaler/imputer, training fingerprint, lambdas and both outcome gates unchanged.

## Audit provenance

Official pages reviewed:
- https://footballapi.org/
- https://footballapi.org/key
- https://footballapi.org/documentation/match-stats
- https://footballapi.org/terms

This audit used public documentation only. It did not call the API or inspect any match-result payloads.
