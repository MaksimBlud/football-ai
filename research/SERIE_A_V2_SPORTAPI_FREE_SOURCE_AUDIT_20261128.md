# MARKET_ANCHOR_1X2_V2 — SportAPI.ai Free Source Audit

**Reviewed:** 2026-11-28  
**Decision:** `HOLD_INCOMPLETE_FEATURE_COVERAGE_AND_UPSTREAM_RIGHTS`  
**Scope:** official public documentation only. No account/key, API call, dataset download, quote read, Supabase access, inference, or outcome access.

## 1. Free-plan claim

The official API documentation states that, as of **2026-11-28**, the Free limit remains **2,000 requests/day and 14,000/month through 2026-11-30**; it drops to **1,000/day and 7,000/month from 2026-12-01**. The provider claims all endpoints and leagues are included and lists Italy's Serie A. Data endpoints require an API key. The provider describes historical results, but the reviewed pages do not establish the exact historical season depth or authenticated Serie A 2026/27 per-match statistics completeness.

Official pages:
- [Football API and free plan](https://sportapi.ai/football-api)
- [API documentation](https://sportapi.ai/docs)
- [Terms of Use, last updated 2026-11-27](https://sportapi.ai/terms)
- [Competition coverage](https://sportapi.ai/coverage)

## 2. Frozen 19-feature compatibility

The original V2 feature builder is pinned to `historical_football_signal_lab.py` Git blob `401b3a0893371bfa4a488ec92a4a54af2678c8f7`. Its `ALL_FOOTBALL` feature set contains exactly 19 features. Six are corner-derived:

- `diff_corners_for_5`
- `diff_corners_for_10`
- `diff_corners_against_5`
- `diff_corners_against_10`
- `diff_corners_for_venue5`
- `diff_corners_against_venue5`

SportAPI documents fixture scores/results, goal events, yellow/red card events, and team-match statistics. Its published team-stat list is shots, shots on target, fouls, passes, pass accuracy, tackles, saves and yellow cards. **Corners are not in the documented field list or endpoint summary.**

Therefore six of the original 19 features have no documented source in this candidate. This is not a licence to substitute fields, change the feature order, alter medians, or impute missing corners differently. The original candidate cannot be run on an incomplete vector.

The provider also says detailed data depends on the underlying source and is not guaranteed for every competition. No authenticated Serie A 2026/27 response was obtained.

## 3. Rights and retention

The Terms say the data may be used in the user's own websites, apps, analysis and products, and prohibit reselling or redistributing the raw data feed. They identify league/club names and logos as belonging to their owners and state that SportAPI is not affiliated with or endorsed by those owners.

The reviewed Terms do not expressly resolve:
- internal ML training/evaluation rights for this exact use;
- long-term private retention of raw API responses and derived features;
- rights in the upstream provider's Serie A statistics at field level.

This is recorded as an engineering eligibility hold, not a legal conclusion.

## 4. Source-before-quote and SHA

The documentation example includes a fixture `updated_at` field, but does not document a per-match first-observed timestamp, per-field correction timestamp, or immutable upstream revision history for the statistics payload.

If a future authorized source is reconsidered, the project would still need to preserve the exact response bytes, local UTC receipt time, SHA-256, source endpoint/fixture identity, and parent-workflow completion evidence before the saved quote. A local receipt timestamp proves when this project received bytes; it does not prove when the provider first observed or last corrected each statistic.

No source-before-quote proof exists for SportAPI in this audit.

## 5. Frozen candidate remains untouched

- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`
- Training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`
- Training rows: 3,799
- Features: 19
- Weight matrix: 20×2
- `active_lambda=0`: market remains active
- `shadow_lambda=1`: research only
- Historical stability: FAILED
- Prospective outcome gate: CLOSED, 0/30

## 6. Decision

**HOLD — NO INTEGRATION.** SportAPI is a potentially useful free source for some match inputs, but the documented coverage is incomplete for the frozen 19-feature V2 contract and upstream rights/retention/provenance remain unresolved. Do not call the API, create a key, download data, or substitute missing features. Reconsider only after written rights clarification, authenticated per-season Serie A field coverage including corners, and a documented source-observation/correction contract.

No model code, weights, feature order, production artifact, workflow schedule, main branch, Supabase object, or other agent setting was changed.
