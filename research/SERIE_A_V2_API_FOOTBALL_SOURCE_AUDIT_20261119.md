# Original MARKET_ANCHOR_1X2_V2 — API-Football free-plan source and rights audit

**Audit date:** 2026-11-19  
**Decision:** **HOLD — technically relevant current-season supplement; model-use rights, private retention, exact Serie A 2026/27 coverage and source-time provenance are not cleared.**  
**Scope:** official public API-Football terms, pricing, documentation and coverage page only. No account, API key, API request, source download, odds request, Supabase access, feature calculation, inference or protected 2026/27 outcome read was performed.

## Executive result

API-Football is a technically relevant candidate for a future current-season statistics supplement:

- The current pricing page advertises a $0 Free plan with 100 requests/day. It lists Statistics among the Free-plan endpoints and says all plans include all competitions/endpoints, while Free plans are limited by available seasons.
- The official fixture-statistics documentation lists corners, yellow cards and red cards, alongside shots, fouls and possession. The fixture endpoint provides match identities, kickoff and score/result fields.
- The official coverage page lists Italy Serie A, but its public table is not season-specific. The page's detailed coverage timestamp is 2026-09-11; the exact Serie A 2026/27 Free-account statistics coverage is not established by the page.

This is a **candidate mapping**, not proof of complete frozen 19-feature coverage. The documented raw fields could support the 9 result/points/goals-derived inputs, 6 corner inputs, 2 yellow-card inputs and 2 red-card inputs if per-match values are available. The rolling last-5/last-10 and venue-specific semantics still require exact parity tests against the original feature builder.

The Free plan cannot be treated as a replacement for the original 2016–2026 training archive: the provider explicitly limits Free-plan season availability, and the actual accessible season range was not checked.

## Free-plan and technical constraints

- Public pricing: $0/month and 100 requests/day.
- Statistics is listed as an included endpoint on the Free plan.
- The pricing page says all competitions/endpoints are included but Free plans are limited in available seasons.
- The fixture-statistics endpoint documents Corner Kicks, Yellow Cards and Red Cards. It is a match-statistics endpoint for ongoing or completed fixtures, not a source of pre-match statistics for the target fixture.
- The provider says not every league tracks every statistic; unavailable values can be null. Null must never be converted to a real zero.
- The coverage object returned by the leagues endpoint is the documented way to check competition/season coverage. No API call was made, so Serie A 2026/27 Free-plan coverage and field completeness remain unverified.
- The 100-request daily ceiling requires a request-budget design before any authorized sampling. No assumption is made that every statistics call can be batched or that all Serie A fields fit within the quota.

## Rights assessment — not cleared

The current public Terms of Service state that the data is obtained from partners, prohibit reselling it to third parties, and say the provider does not grant a license for use and publication of the data in user applications, websites or products. The terms place responsibility on the user to obtain any required authorization from competent authorities and warn that some sports data may be subject to third-party intellectual-property or commercial restrictions.

The reviewed terms do **not explicitly grant**:
- internal ML/model training or feature derivation;
- model inference using retained match statistics;
- private raw-response retention for a research audit period;
- the required upstream rights for Serie A scores, corners, yellow cards and red cards.

The terms also do not identify the upstream provider for each field. Silence is not treated as permission. Written clarification from API-Football and, where applicable, the relevant upstream rights holders is required before account creation, automated access, data retention, feature engineering or inference for this project.

The terms page was last updated 2025-05-21. A future review must re-check the live terms before any use.

## Source-before-quote and SHA

The reviewed public documentation describes update frequency and coverage, but does not document a per-match first-observation timestamp or per-field correction timestamp suitable for reconstructing when an upstream statistic was first observed.

If rights are later cleared, a project-side capture could record:
- exact request parameters, excluding credentials;
- UTC request-start and response-receipt times;
- response status and relevant headers;
- exact response bytes retained in private storage;
- SHA-256 over the exact bytes stored;
- source fixture ID, event identity and competition/season;
- the successful capture workflow run and commit SHA.

That evidence could prove that the project possessed those exact bytes before a later bookmaker quote. It would **not** prove when API-Football or its upstream provider first observed or corrected each field. No source-before-quote evidence exists now because no account or API request was made.

## Original V2 invariants

This audit pins, but does not change:

- candidate SHA-256: a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6;
- training fingerprint: f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098;
- 3,799 training rows;
- exact original 19-feature order and 20 × 2 weights;
- active_lambda = 0 (market anchor);
- shadow residual lambda = 1 (research only);
- failed stability gate and no automatic promotion.

No feature substitution, refit, threshold tuning, candidate or contract change, production .pkl change, Supabase write or evaluation-gate change is proposed.

## Required clearance before reconsideration

1. Written confirmation that internal non-commercial ML research, feature derivation, inference and private raw-response retention are permitted.
2. Written identification/confirmation of upstream rights for Serie A scores, corners, yellow cards and red cards.
3. Exact Free-plan Serie A 2026/27 season coverage, including fixture statistics and per-match field completeness.
4. Documented null semantics, correction policy and any source timestamps available for the required 19 raw inputs.
5. Confirmation of the accessible historical seasons; Free must not be assumed to cover 2016–2026.
6. A request-budget plan under 100 requests/day, with no paid upgrade, overage, or fallback billing.
7. Only after all gates: a separately reviewed V2-only adapter that archives exact bytes privately with SHA-256 and receipt time, completes source verification before any saved-quote reader, and passes exact 19-feature parity tests.

## Official documents reviewed

- Terms of Service: https://www.api-football.com/terms
- Pricing: https://www.api-football.com/pricing/
- Current documentation: https://www.api-football.com/documentation-v3
- Fixture statistics field reference: https://www.api-football.com/documentation-v3
- Coverage: https://www.api-football.com/coverage/
- API-Football guide to fixture statistics and coverage: https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide
- API-Sports quota/call optimization guide, 2026-07-27: https://www.api-football.com/news/post/how-to-optimize-api-sports-calls-and-quota-usage

**Bottom line:** retain API-Football as a possible free current-season supplement, but keep it on HOLD. The documented statistics are technically relevant, yet the provider does not clearly grant the model-use/private-retention rights required here; exact Serie A 2026/27 Free coverage, historical-season scope, upstream rights and first-observation/correction provenance remain unproven. No integration or live access is authorized by this audit.
