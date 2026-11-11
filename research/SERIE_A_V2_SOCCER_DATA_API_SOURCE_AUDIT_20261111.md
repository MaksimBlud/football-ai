# Original MARKET_ANCHOR_1X2_V2 — Soccer Data API current-season source audit

**Audit date:** 2026-11-11  
**Scope:** official public terms, pricing, API documentation and coverage schema only. No account was created, no API key was requested, and no API endpoint was called. No match payload, quote, Supabase row, target outcome or model inference was accessed.

## Decision

`soccer-data.co` is a **potential free current-season source for a separately gated V2 source-concordance test**. It is not approved for automatic collection, archival, feature building or inference yet.

Unlike the previously audited open-matchday compilation, Soccer Data publishes terms that permit using the data in one's own websites, apps, analysis and products, and permit caching/storing while the account and plan remain active. However, the free plan is limited to the current season, the API's upstream field provenance is not documented in the reviewed pages, exact Serie A 2026/27 coverage has not been verified, and a private archive is required. These gaps prevent integration now.

## Pinned official documentation reviewed

- Terms: https://soccer-data.co/terms (last updated 2026-10-30).
- Pricing and plan scope: https://soccer-data.co/ (reviewed 2026-11-11).
- API reference: https://soccer-data.co/docs/reference.
- Match identity and score: https://soccer-data.co/docs/reference/matches/show.
- Match statistics: https://soccer-data.co/docs/reference/matches/stats.
- Match timeline: https://soccer-data.co/docs/reference/matches/timeline.
- Competition coverage: https://soccer-data.co/docs/reference/coverage/leagues.
- Season-by-season coverage: https://soccer-data.co/docs/reference/coverage/league.
- Coverage concepts: https://soccer-data.co/docs/concepts/coverage.

The pages are mutable. Any later test must preserve exact page bodies, retrieval timestamps and SHA-256 values in a research manifest. This audit does not claim immutable upstream byte hashes because no raw page snapshots were archived in this repository.

## Rights and plan limits

The current terms say:

- API data belongs to Soccer Data or providers from whom it licenses the data.
- The account receives a non-exclusive, non-transferable licence.
- Data may be used in the user's own websites, apps, analysis and products, including paid products.
- API responses may be cached and stored while the account is open and the plan is active.
- Raw data may not be resold, sublicensed or redistributed as a data feed, API, bulk dataset or file.
- When the account or terms end, the data licence ends.

The Free plan is advertised as $0, 50 requests/day, all statistics endpoints, **current season only**, no odds and no webhooks. Pro is advertised at $19/month and adds five years of history and odds; Business is $79/month and adds ten years of history. No paid plan is proposed or authorized here.

The terms are materially more permissive for own-product use than the non-commercial-only open-matchday compilation, but they do not explicitly answer whether this project's frozen-model inference and long-term research archive are within the intended licence. Written provider clarification should be obtained before automated capture or model use. The API also does not identify the underlying provider separately for each returned field in the documentation reviewed.

## Frozen V2 feature compatibility — schema level only

The original candidate remains unchanged:

- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original feature-builder Git blob: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- Exactly 19 original features; no order, window, weight, scaler or imputer changes are proposed.

Potential field mapping from the official docs:

| Frozen V2 input family | Documented Soccer Data field | Assessment |
|---|---|---|
| Points and goals for/against | Finished match `score.home`, `score.away`, `score.winner` | Derivable only from completed regular-time score; cup/extra-time semantics must be excluded or reconciled with the original league-only contract |
| Corners for/against | `overview.corner_kicks.all.home/away` | Exact named stat exists; per-match null/coverage and provider definition still need measurement |
| Yellow cards | `overview.yellow_cards.all.home/away`; timeline `yellow_card` | Plausible; team-stat/timeline parity and double-booking semantics need validation |
| Red cards | `overview.red_cards.all.home/away`; timeline `red_card`, `yellow_red_card` | Plausible; second-yellow treatment must be reconciled with the frozen source definition |

The stats endpoint explicitly says missing periods are null, never zero, and returns 404 when detailed statistics were not collected. The existing V2 adapter must continue to reject unavailable required values; no null-to-zero conversion or new imputation is permitted.

The timeline endpoint documents `coverage=full|none`, `meta.reason`, and `meta.last_updated`. It includes goal, yellow/red card, second-yellow/red, and corner-kick event types. The stats endpoint documents the required team totals but does not document a per-field source timestamp in its response example. A capture would therefore need to preserve the exact response bytes, HTTP ETag/cache headers where available, retrieval time, and archive creation time; that proves our observation was archived before a later quote, not when the upstream provider originally observed the event.

## Coverage and historical limitations

The public coverage documentation supports querying, by competition, whether `team_stats` exists, how many seasons are loaded, and how many finished matches are covered. A season-level endpoint is documented as well.

However, exact Serie A coverage counts and per-season field completeness require an authenticated API call. No key exists in this audit and no request was made. The provider says coverage depth differs by competition and that a missing stat may return null or no detailed-stats response.

The Free plan includes the current season only. It cannot replace the 2016/17–2025/26 historical input archive used by the original candidate. It could at most be considered for a separate, preregistered current-season lagged-input supplement after rights, coverage, and source-parity gates pass. It must not silently replace the existing historical source or change the current-form contract.

## Required gates before any future integration

1. Obtain written confirmation that frozen-model inference, derived team-form features, private retention and the proposed research use are permitted under the provider's licence.
2. Confirm that the provider's upstream rights permit the provider to grant that use; record the provider's answer and applicable terms version.
3. With an authorized key, make a bounded, read-only coverage check for Serie A 2026/27 only. Record competition/season IDs, `team_stats` coverage, completed match counts, and per-match null rates for corners/yellows/reds. Do not request odds endpoints.
4. Compare a preregistered sample of provider match statistics against an independently licensed source to test exact definitions, team identity and red-card treatment. No thresholds may be tuned on outcomes.
5. Store only in an approved **private** archive. The football-ai repository is public, and raw source payloads must not be uploaded as public GitHub Actions artifacts. No Supabase write or DDL is authorized in this task.
6. For every future quote, require the exact source response SHA and private archive parent run to be completed strictly before the quote and before kickoff. Reject equal timestamps, stale responses, missing coverage, conflicting fixture identity and same-UTC-day historical matches under the unchanged V2 date rule.
7. Keep all source access and inference behind the existing default-deny rights gates. Do not enable any workflow merely because the Free plan exists.

## V2 contract and explicit non-results

- Original 19 features, order, weights, scaler/imputer, training fingerprint and candidate SHA: unchanged.
- `active_lambda=0`: market remains the active reference.
- `shadow_lambda=1`: research only.
- Stability gate: FAILED.
- Prospective 30-primary-completed-event outcome-read gate: still closed in the available evidence.
- Brier/LogLoss superiority over market: not established.
- No model inference, training/refit, threshold tuning, bet, promotion or production change.

No account, API key, API request, odds endpoint, dataset download, source archive, Supabase access/write, target-outcome read or workflow schedule change was performed.

## Final disposition

**Retain Soccer Data as a promising but unapproved free current-season candidate only.** Its documented schema contains plausible corners and card fields and its terms permit own-product analysis, but the free tier does not supply the required historical seasons, exact Serie A field coverage is unverified, and private-retention/model-inference scope needs written confirmation. Do not integrate it into original V2 yet.
