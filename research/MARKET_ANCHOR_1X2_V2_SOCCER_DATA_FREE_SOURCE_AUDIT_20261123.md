# Soccer Data free-plan audit — original MARKET_ANCHOR_1X2_V2

**Checked:** 2026-11-23 20:00 UTC  
**Provider:** [Soccer Data](https://soccer-data.co/)  
**Decision:** **HOLD — no integration, account, API key, request, download, feature calculation or inference.**

## Executive finding

Soccer Data is a technically promising candidate for current-season Serie A feature inputs. Its public match-statistics schema lists corners, yellow cards and red cards; match results provide goals, and standings provide points. The Free plan advertises all statistics endpoints for the current season, with 50 requests per day and no bookmaker odds.

This is closer to the original 19-feature contract than the previously screened SportAPI schema, but it does **not** establish complete Serie A 2026/27 coverage, rights for internal ML training/inference, upstream field rights or long-term private retention. It remains **HOLD_NO_INTEGRATION**. No API endpoint was called and no account/key was created.

## Free plan

Official pricing/docs state $0/month, 50 requests/day, 10/minute, current-season-only, all statistics endpoints, no odds and an API key requirement. The Free plan cannot replace the historical training corpus used by the original frozen candidate.

## Mapping to the unchanged 19 features

The reviewed match-statistics schema lists `corner_kicks`, `yellow_cards`, `red_cards` and home/away values. Match results expose goals and standings expose points. At schema level, the required feature families appear to exist without changing any feature or weight.

However:
- match statistics are available only for played matches;
- the API can return `404 STATS_NOT_AVAILABLE`;
- statistical depth varies by competition;
- the coverage endpoint reports per-season covered-event counts, but exact Serie A 2026/27 coverage was not retrieved because it requires an API key.

Schema-level field presence is **not** evidence that every required fixture has all 19 inputs. No completeness or full parity claim is made.

## Rights and retention

Terms last updated 30 October 2026 say data belongs to Soccer Data or third-party providers it licenses from. The licence is non-exclusive and non-transferable. It permits API calls, caching/storage while the account and plan are active, and showing data in one's own websites, apps and services. Raw-data redistribution is prohibited; the licence ends when the account is closed or the Terms end.

The reviewed Terms do not expressly address internal ML training or inference using derived statistics, or continued retention of derived model weights after account/plan termination. This is unresolved, not silently interpreted as permission or prohibition. Upstream provider identities and field-level rights are not identified. Written clarification is required before any account creation or data access.

## Source-before-quote and timestamps

The provider says statistics can arrive late, change after an event or be wrong. The Free plan uses a five-minute live-data cache. The reviewed documentation does not define per-field first-observed timestamps or correction history.

If written rights and coverage are later cleared, an authorized client could preserve exact response bytes, request parameters (excluding credentials), response headers, local receipt UTC time and SHA-256 privately before a later saved bookmaker quote. That proves project possession before the quote, not upstream first observation or correction time. No such capture occurred in this audit.

## Original model invariants and separate training-corpus blocker

This audit pins, without changing:
- candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`;
- 3,799 training rows;
- exact original 19-feature order and 20 × 2 weights;
- `active_lambda=0` (market anchor);
- `shadow_lambda=1` (research only);
- failed stability gate and no automatic promotion.

The original weights were trained on the Football-Data historical corpus. Soccer Data Free is current-season-only and does not resolve rights for that corpus or for inference using the frozen weights.

## Required clearance before reconsideration

1. Written permission for internal model training and inference, including inference with the existing frozen V2 weights.
2. Identification and confirmation of upstream rights for goals, points, corners and cards.
3. Per-season Serie A 2026/27 coverage with per-fixture completeness for every required field.
4. Written clarification of raw-response retention, private archival and derived-model retention after account/plan termination.
5. Clarification of provider observation/correction timestamps and stale-response semantics.
6. Separate resolution of Football-Data rights for the original historical training corpus and frozen candidate.

## Official documents reviewed

- [Pricing](https://soccer-data.co/pricing)
- [Terms of Service](https://soccer-data.co/terms)
- [Match statistics](https://soccer-data.co/docs/reference/matches/stats)
- [Match timeline](https://soccer-data.co/docs/reference/matches/timeline)
- [Coverage](https://soccer-data.co/docs/concepts/coverage)

**Bottom line:** Soccer Data is the strongest new schema-level free current-season candidate found in this pass, but it is not cleared for integration. Keep it on HOLD. No provider access or model operation is authorized by this audit.
