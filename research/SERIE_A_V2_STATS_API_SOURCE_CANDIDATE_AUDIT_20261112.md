# Original MARKET_ANCHOR_1X2_V2 — Stats API source-candidate audit

**Audit date:** 2026-11-12  
**Scope:** official public product, coverage, documentation, provenance and FAQ pages only. No account, key, API request, dataset download, Supabase access, quote read, feature build, inference, or target-outcome analysis.  
**Decision:** `CONDITIONAL_CANDIDATE_NOT_APPROVED`; not a current-form source at this time.

## 1. Summary

Stats API (stats-api.com) is a new candidate worth recording because its public contract documents match-level statistics including corners and cards, per-match coverage flags, stable IDs, and ingestion provenance. It also advertises 200 free requests once per new account, without a card, expiry, or monthly reset.

The current public evidence does not establish a usable free 2026/27 Serie A current-form feed, a complete source-rights grant for model feature use/retention, or the source-observation timestamp required by this project's source-before-quote rule. Do not create an account or make API calls under this audit.

## 2. Documented schema potential

The public match-statistics contract describes per-team fields for:
- corners;
- shots and shots on target;
- possession;
- cards;
- passes and expected goals.

The match collection documents fixtures/results and stable match IDs. Each match/detail response is supposed to expose coverage flags, including whether team statistics are stored. Missing statistics are explicit; null must not be converted to zero.

At schema level, corners and cards could be relevant to the original 19-feature families. However, this audit did not inspect any match payload or current-season result. No claim is made about Serie A 2026/27 completeness, yellow/red definitions, second-yellow handling, or numerical parity with the frozen Football-Data source.

## 3. Coverage and free-plan limitations

The public site advertises **200 free requests once** per new account, shared across keys, with no card, expiry, or monthly reset. Paid plans are separate and are not authorized.

The public coverage page emphasizes that coverage varies by competition, season, and match. Its published league-specific historical guides include Serie A 2025/26, while the docs instruct clients to query the coverage endpoint and per-match flags for current-season availability. The reviewed public pages do not establish that a free account currently has complete 2026/27 Serie A team-stat coverage.

A one-time 200-request allowance is not a recurring free collection entitlement. It may be useful for a future bounded diagnostic only if rights and exact current-season coverage are first confirmed in writing; no request is authorized by this audit.

## 4. Provenance and source-before-quote

The public contract distinguishes Stats API ingestion time from upstream source time:

- a match `updated_at` value records when the normalized row last changed during Stats API ingestion, not a timestamp published by the original source;
- for the OpenFootball historical bootstrap, `source_updated_at` is null and `freshness_guaranteed` is false;
- `/coverage/summary` exposes dataset-level ingestion/retrieval information;
- ingestion runs record retrieved artifact SHA-256, byte count, and retrieval time.

These fields can help prove which artifact Stats API imported and when it retrieved it. They do **not** prove when the underlying football fact became current or when the upstream provider first observed a statistic. The public coverage page expressly warns that retrieval/success times do not establish when the facts became current.

Consequently, a local capture SHA plus Stats API ingestion timestamp would not yet satisfy the strict source-before-quote requirement. Require an immutable source release identity, exact upstream provider/rights lineage, and source-observed timestamp (or an explicitly approved substitute) for every relevant statistic before considering a future capture.

## 5. Rights gate

The reviewed public product, coverage, documentation and FAQ pages describe use cases for apps, research workflows and AI tools, but this audit did not locate a complete public data licence/terms grant that expressly resolves:
- private retention of raw match-stat responses;
- model feature construction and inference;
- AI model training or evaluation;
- retention after free-account expiry or service termination; and
- upstream provider rights for each enabled Serie A field.

The site distinguishes historical OpenFootball CC0 bootstrap data from separately enabled provider ingestion. The OpenFootball statement must not be generalized to other provider datasets or current-season match statistics.

**Binding decision:** do not download, retain, train on, build features from, or infer with Stats API data until the provider supplies written permission and identifies the upstream rights applicable to the exact Serie A fields. Public accessibility, an API key, or a free request allowance is not a licence.

## 6. V2 invariants and next admissible step

- Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original feature-builder Git blob remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- Original 19-feature order, rolling windows, weights, scaler, imputer, training fingerprint, and 20x2 matrix remain unchanged.
- `active_lambda=0`; `shadow_lambda=1` research-only; stability gate FAILED; NO_BET and no automatic promotion.
- No legacy XGBoost production model, production `.pkl`, paid odds API, Supabase write/DDL, or schedule change is involved.

Next admissible step: obtain written confirmation of source rights, current-season Serie A coverage, per-field upstream lineage, and source timestamp semantics. Only then may a bounded source-only concordance protocol be considered. Until then, Stats API is **not approved** for original V2 current-form capture or inference.

## 7. Actions taken

- Read only public Stats API product, coverage, documentation, match-endpoint guide, and FAQ pages.
- Did not create an account or API key, call an endpoint, or spend the 200-request allowance.
- Did not download or parse any match/season dataset.
- Did not read saved quotes, Supabase rows, or target outcomes.
- Did not calculate features, run inference, alter the frozen candidate, or change any workflow.
