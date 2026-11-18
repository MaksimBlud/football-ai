# Original MARKET_ANCHOR_1X2_V2 — Soccer Data free-plan source audit

**Audit date:** 2026-11-18  
**Decision:** **HOLD — plausible current-season statistics supplement; not a historical-source replacement and not yet cleared for model use.**  
**Scope:** official public documentation only. No account, API key, provider API request, source download, Supabase access for this provider audit, odds request, feature calculation, inference, or protected outcome read was performed. A separate project-level check used only read-only, strictly pre-kickoff odds aggregates and did not access this provider.

## What is technically promising

The provider's current pricing page advertises a Free plan at $0 with 50 requests/day, all statistics endpoints, current-season data only, and no odds endpoint. The match-statistics endpoint documents team-level fields including corners, yellow cards and red cards. The match list provides score fields for completed matches; its score breakdown remains null until full time.

This is a plausible source for a future **current-season supplement** to the original frozen V2 input history. It is not a replacement for the historical 2016–2026 source data used to construct the frozen feature context: the Free plan is current-season only. The provider's coverage API can describe competition/season availability, but exact Serie A 2026/27 Free-account coverage was not queried and is not proven by the public catalogue alone.

## Free-plan constraints

- $0/month; 50 requests per UTC day and 10 requests/minute.
- All listed statistics endpoints are available on Free, but only for the current season.
- Pre-match and in-play odds are not included on Free. No odds endpoint is needed or proposed for this audit.
- Match statistics are requested per match ID; exact Serie A coverage and completeness must be checked before any future use.
- Missing statistics are represented as null, not zero. A missing corner/card field must never be silently converted to a real zero.
- Free responses can be cached; stale responses are marked with X-Cache and X-Cache-Age. Documentation allows stale static data up to six hours old. A future capture must explicitly reject or account for stale responses rather than treating every successful HTTP response as a fresh source observation.

## Rights assessment

The Terms of Service, last updated 30 October 2026, state that the provider or its upstream licensors own the data and grant a non-exclusive, non-transferable licence. While the account and plan remain active, the terms allow the customer to cache/store received data and display it in the customer's own websites, apps and services, including paid services. They prohibit reselling or redistributing the raw feed as data and prohibit exposing an API key or proxying the provider API to others.

The reviewed terms do **not explicitly address internal AI/ML model training or inference**, nor do they identify the upstream providers or field-level rights for Serie A scores, corners and cards. Permission to display data in an app is not silently treated as permission to train or infer a model from it. Written provider clarification is required before model use.

The general storage clause is limited to the period while the account and plan remain active. Any future raw-response archive must be private; the project repository is public and must not be used to publish raw source bytes.

## Provenance and source-before-quote

The documentation describes response caching and stale-response headers, but the reviewed pages do not document per-match first-observation timestamps or per-field correction timestamps. The API's receipt time and exact raw response bytes could be recorded by a future authorized client, with a SHA-256 calculated over the bytes actually stored.

That would prove the project possessed those exact bytes before a later quote if the archive was completed first. It would **not** prove when the provider or upstream source first observed a field, nor when a later correction was made. A response marked stale, missing, or with ambiguous cache age cannot be silently promoted to a fresh source archive.

No source-before-quote evidence exists now because no account or API request was made.

## Original V2 invariants

This audit pins, but does not change:

- candidate SHA-256: a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6;
- training fingerprint: f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098;
- exact original 19-feature order and 20 × 2 weights;
- active_lambda = 0 (market anchor);
- shadow residual lambda = 1 (research only);
- failed stability gate and no automatic promotion.

No refit, feature substitution, threshold tuning, model-contract change, production .pkl change, or evaluation-gate change is proposed.

## Required clearance before reconsideration

1. Written confirmation that internal model training, feature derivation and inference are permitted under the Free plan.
2. Written identification/confirmation of upstream rights for Serie A scores, corners, yellow cards and red cards.
3. Exact Serie A 2026/27 Free-plan coverage and per-match completeness, including null semantics for red cards and venue-specific inputs.
4. Confirmation of how corrections to completed-match statistics are timestamped and how response Date/cache-age headers should be interpreted.
5. Confirmation that raw response bytes may be retained privately for the required research/audit period; the public repository and public Actions artifacts are not acceptable raw-source storage.
6. Only after all gates: a separately reviewed source adapter that records request parameters (excluding credentials), receipt time, response headers, exact bytes and SHA-256, then completes source verification before any saved-quote reader.

## Official documents reviewed

- Terms of Service: https://soccer-data.co/terms
- Pricing: https://soccer-data.co/pricing
- Match statistics: https://soccer-data.co/docs/reference/matches/stats
- Match list/results: https://soccer-data.co/docs/reference/matches/list
- Coverage: https://soccer-data.co/docs/concepts/coverage
- Rate limits and stale responses: https://soccer-data.co/docs/concepts/rate-limits
- Introduction and data model: https://soccer-data.co/docs/introduction

**Bottom line:** retain Soccer Data as a possible no-cost current-season supplement, but keep it on HOLD. The Free plan cannot replace the historical archive, and AI-use rights, upstream field rights, exact Serie A coverage and first-observation/correction provenance are not yet proven. No integration or live access is authorized by this audit.
