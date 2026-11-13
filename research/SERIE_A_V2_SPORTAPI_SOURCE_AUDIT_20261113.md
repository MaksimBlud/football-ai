# SportAPI source-rights and frozen-feature coverage audit

**Review date:** 2026-11-13 UTC  
**Decision:** `HOLD — NOT APPROVED FOR ORIGINAL V2 INGESTION OR INFERENCE`  
**Scope:** free-tier Serie A source candidate for the unchanged `MARKET_ANCHOR_1X2_V2` 19-feature contract.

## Executive finding

SportAPI is a plausible free API candidate on plan breadth: its official pricing says every plan includes all endpoints and leagues, its football coverage page lists Serie A, and its current Free limits are 2,000 requests/day and 14,000/month through 2026-11-30, changing to 1,000/day and 7,000/month from 2026-12-01. No account or API key was created and no endpoint was called.

It is **not currently a usable complete source for the frozen V2 feature contract**. The official OpenAPI `GET /fixtures/{id}/stats` schema has shots, shots on target/off target, fouls, passes, tackles, saves and yellow cards, but no corners. The `/fixtures/{id}/events` schema has generic event records; the official documentation describes goals, assists, yellow/red cards and substitutions. A search of the published OpenAPI document found no `corner` field or event description. Six frozen V2 corner features cannot be sourced from the documented contract.

The official Terms, last updated 2026-10-22, permit use of data in one's own websites, apps, analysis and products, and prohibit reselling or redistributing raw data as a competing feed/API. They do not expressly settle model-training permission, long-term private raw-response retention, or field-level upstream rights. Those remain unconfirmed rather than assumed.

## Frozen V2 feature coverage

The exact candidate SHA remains:

`a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`

The exact 19-feature order is copied into `research/source_rights/sportapi.json` and regression-checked against the frozen candidate JSON. Six unsupported features are:

1. `diff_corners_for_5`
2. `diff_corners_for_10`
3. `diff_corners_against_5`
4. `diff_corners_against_10`
5. `diff_corners_for_venue5`
6. `diff_corners_against_venue5`

Goals and points appear derivable from fixture scores/results; cards appear in documented event families and yellow-card team statistics. This does not establish full Serie A completeness, exact event semantics, or the necessary source rights. Six systematically unavailable corner inputs would be a material coverage defect; do not silently substitute another source, alter feature definitions, or treat median-imputation as evidence of full source coverage.

## Provenance assessment

The API documents `kickoff_utc` and fixture-level `updated_at` as UTC. It does not document `updated_at` as a per-field source-observation timestamp, nor provide per-field correction history. The Terms also warn that public-source data may be late, incomplete or wrong.

If a future written approval and complete schema are obtained, a local immutable capture could prove what bytes the project actually possessed before a later quote:

- raw response bytes and SHA-256;
- trusted retrieval timestamp;
- authenticated parent GitHub Actions run ID, exact commit SHA, workflow path and completion time;
- private archive ID/SHA and creation time;
- strict `source_archive_created_at < quote_snapshot_time < kickoff_utc`;
- exact frozen candidate SHA and original feature-builder parity.

That would prove project possession of the captured bytes before the quote, not the provider's unrecorded per-field upstream observation time. No backfill may be represented as prospective.

## Required conditions to reconsider HOLD

Obtain written provider confirmation of all of the following before any API account/key or ingestion:

1. permission for internal ML feature construction, model inference, and model training/evaluation using the Free-plan data;
2. permission and retention limits for privately storing raw responses and hashes for reproducibility/audit, without raw redistribution;
3. upstream rights for Serie A and attribution/provenance for the exact score, card and corner fields;
4. a documented Serie A corner endpoint/schema (including home/away semantics and correction behavior) covering all six frozen corner inputs;
5. meaning and update/correction semantics of `updated_at`, or an explicit acceptance that only local retrieval-time evidence is available;
6. the Free plan's actual Serie A access and historical depth, verified without exceeding its request budget.

Until every required flag is true and a private archive is independently verified, `approval_status` stays `HOLD`. The adapter must remain offline-only; no network client, Supabase access, model inference or target-outcome reader is added.

## Safety and model contract

- Original 19 features, weights, scaler, imputer, candidate SHA and training fingerprint are unchanged.
- `active_lambda=0` remains the market; `shadow_lambda=1` remains research-only.
- Original stability gate remains failed; NO_BET and the separate 30-primary-completed-event target-outcome gate remain unchanged.
- No paid plan, The Odds API request, provider request, account/key, data download, Supabase read/write/DDL, target-outcome read, inference, refit, production `.pkl` change, schedule change or promotion occurred.

## Official references

- Terms (last updated 2026-10-22): https://sportapi.ai/terms
- Pricing: https://sportapi.ai/pricing
- API documentation: https://sportapi.ai/docs
- OpenAPI 3.1 schema: https://sportapi.ai/api/openapi.json
- Football API and Serie A coverage listing: https://sportapi.ai/football-api/
- Coverage: https://sportapi.ai/coverage
