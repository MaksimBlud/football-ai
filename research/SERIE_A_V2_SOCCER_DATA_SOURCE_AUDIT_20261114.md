# Soccer Data free current-season source audit — original MARKET_ANCHOR_1X2_V2

**Audit date:** 2026-11-14  
**Decision:** HOLD — documentation-only candidate review; no source capture or inference approved.

## Why this provider is worth tracking

The official pricing and documentation describe a $0 Free plan with 50 requests/day, 10 requests/minute, current-season access, all match-stat endpoints, and no odds. The match-stat endpoint documents home/away corner kicks, yellow cards and red cards; the match endpoint supplies match identity and scores. This is a plausible *statistics-only* candidate for lagged current-form inputs, not an odds provider.

Official sources:
- Terms (last updated 30 October 2026): https://soccer-data.co/terms
- Pricing: https://soccer-data.co/pricing
- Rate limits and cache headers: https://soccer-data.co/docs/concepts/rate-limits
- Competition/season coverage: https://soccer-data.co/docs/concepts/coverage
- Match statistics schema: https://soccer-data.co/docs/reference/matches/stats
- Match list and score fields: https://soccer-data.co/docs/reference/matches

## Why the decision remains HOLD

### 1. Internal ML/inference permission is not explicit

The terms say the data belongs to Soccer Data or providers it licenses from; the customer receives a non-exclusive, non-transferable licence. They permit caching/storing and displaying data while the account and plan remain active, prohibit raw-data redistribution, and end the data licence when the account closes or terms end. The reviewed terms do not expressly mention internal ML training, frozen-feature inference, or long-term retention of derived model evidence after account termination.

This is an unresolved permission question, not a legal conclusion that ML use is prohibited. Written confirmation is required for internal model feature construction/inference, derived predictions, private raw-response retention, and the applicable upstream rights.

### 2. Upstream source and data corrections are not sufficiently documented

The terms state that data comes from third-party providers, but the reviewed pages do not name those providers by field or establish the upstream rights chain. They also warn that scores, events, lineups and statistics can arrive late, change after the event, or be wrong.

The API documents `X-Cache` and `X-Cache-Age` for stale responses, but the match-stat schema does not document a per-field upstream observation timestamp or correction history. A private raw-response capture timestamp plus SHA-256 can prove that the exact bytes were in the project's possession before a later quote; it cannot prove when an upstream provider first observed or corrected a field. If the source were ever authorized, the collector would need to retain exact response bytes, receipt time, response/cache headers, SHA-256 and parent-run evidence, and reject stale responses.

### 3. The Free plan does not satisfy the existing source archive contract

The Free plan is current-season-only. The official coverage guide says Serie A data is available from 2020/21, but exact season-by-season, per-match coverage requires the authenticated coverage endpoint. The Free plan does not provide the ten historical seasons required by the existing current-form archive contract (ten historical CSVs plus one current-season CSV). It therefore cannot replace the current source contract as-is.

The stats endpoint may return `404 STATS_NOT_AVAILABLE`; missing/null values must never be converted to zero. Exact 2026/27 Serie A coverage, red-card/second-yellow semantics, team aliases, and parity with the original Football-Data fields remain unverified.

### 4. Free request budget is modest

The project's metadata-only Serie A gate currently contains 110 canonical completed fixture identities (113 raw identity rows before the Atalanta alias normalization). At one match-stat request per fixture, 110 requests would require at least three UTC daily quota windows at 50 requests/day, before fixture-list or coverage calls. This is a planning estimate only; no provider account or request was made.

The Free plan excludes odds, so this provider cannot supply the market comparator. No paid odds source is proposed.

## Frozen original V2 contract preserved

- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`
- 19 original features, exact order pinned in the manifest and regression test.
- Weight matrix: 20 × 2.
- Training rows: 3,799; training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- `active_lambda=0` remains the de-vigged market; `shadow_residual_lambda=1` remains research-only.
- Stability gate remains FAILED; automatic promotion remains disabled.
- No refit, new model, legacy XGBoost, feature change, source substitution, or outcome-gate change.

## Conditions to reconsider

1. Written provider confirmation for internal ML feature use/inference and derived predictions.
2. Written confirmation that the licence covers the disclosed upstream providers and the exact Serie A fields.
3. Written retention terms for private raw archives and derived evidence, including what happens if the account or Free plan ends.
4. Authenticated, authorized coverage evidence for every required 2026/27 Serie A match and all required fields; missing values remain missing.
5. A source adapter that preserves the existing frozen feature order and source-before-quote proof without changing the model or its source contract.
6. Verified private storage; no raw source bytes in this public repository or public Actions artifacts.

## Safety and non-results

Documentation-only audit. No account/key creation, API request, data download, odds request, Supabase access/write/DDL, source archive, feature build, inference, target-outcome read, Brier/LogLoss calculation, production artifact change, schedule change, or main update occurred. This PR does not authorize capture or inference and does not establish model quality. Keep Draft / HUMAN-MERGE only.
