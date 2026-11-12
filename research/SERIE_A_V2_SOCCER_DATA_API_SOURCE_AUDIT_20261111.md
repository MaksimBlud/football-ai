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


## 2026-11-12 official-docs follow-up — timeline timestamp and Free-tier constraints

A second read of the current official endpoint pages adds one useful provenance detail, but does not lift the HOLD:

- `GET /matches/{match_id}/timeline` documents `meta.last_updated` as the time the timeline last changed. It also exposes `coverage=full|none` and event types `goal`, `own_goal`, `penalty_scored`, `yellow_card`, `red_card`, `yellow_red_card`, and `corner_kick`. This is a candidate event-level timestamp for a future source-before-quote test, not yet an independently verified upstream observation timestamp.
- `GET /matches/{match_id}/stats` documents the exact named totals `corner_kicks`, `yellow_cards`, and `red_cards`, but the documented response has no `last_updated` field. Do not treat the stats endpoint alone as source-time proof.
- `GET /matches` returns competition/season IDs, status, kickoff, teams and finished score. Its `updated_at` is documented only inside the live clock; the finished-match row has no general source-update timestamp.
- The Free plan uses a five-minute cache. The provider documents `X-Cache: STALE` / `X-Cache-Age` when a fresh answer cannot be fetched. A future capture would need to preserve these response headers and reject stale responses, in addition to recording local request/response times and exact raw-body SHA-256.
- Free is 50 requests/day, current-season only, and has no odds. One list page plus a bounded number of timelines could fit the daily cap, but full-liga coverage of all recent matches for every club may exceed it; no batching claim is made without measured API usage. No paid plan or odds endpoint is proposed.
- The timeline event mapping still needs a preregistered parity check: in particular, how `yellow_red_card` maps to the original Football-Data yellow/red count definitions, how own goals are assigned to the scoring side, and whether all required events are covered for Serie A. Missing/partial timelines must remain missing, never become zero.
- Exact Serie A 2026/27 coverage still requires an authenticated coverage call. No account/key was created and no endpoint was called.

Official pages rechecked on 2026-11-12:
- Pricing/free plan and cache/retention terms: https://soccer-data.co/
- List matches: https://soccer-data.co/docs/reference/matches/list
- Match stats: https://soccer-data.co/docs/reference/matches/stats
- Match timeline and `meta.last_updated`: https://soccer-data.co/docs/reference/matches/timeline
- Pagination and fixed match ordering: https://soccer-data.co/docs/concepts/pagination

**Updated disposition:** Soccer Data is a more promising provenance candidate because the timeline exposes a documented last-change timestamp. It remains **HOLD** pending written inference/retention and upstream-rights clarification, exact Serie A coverage, event-definition parity, private archive approval, and a bounded read-only capture test. Free has no odds, so it cannot provide the market reference. No integration, inference, source download, account creation, or target-outcome access is authorized by this audit.


## 2026-11-12 follow-up — timeline endpoint may reconstruct the frozen goal/corner/card families, but remains HOLD

Official timeline reference: https://soccer-data.co/docs/reference/matches/timeline

- The documented timeline event types include `goal`, `own_goal`, `penalty_scored`, `corner_kick`, `yellow_card`, `red_card`, and `yellow_red_card`; the response also includes `meta.last_updated` and `meta.coverage` (`full`/`none`). The docs say shoot-out kicks use `period=penalties`, and own-goal events are attributed to the player's side even though the goal counts for the opponent. A parser could therefore structurally reconstruct the original goals/corners/cards history families from timeline events, provided the provider confirms category completeness and the yellow-red-card counting semantics.
- This improves structural field feasibility compared with relying only on `/matches/{id}/stats`, which documents possession/xG/shots/passes and does not document corners/cards as team-stat fields. It does **not** prove that every Serie A corner/card/goal is present in every `coverage=full` timeline: the docs define `full` as a timeline existing, not an event-category completeness guarantee.
- The public coverage guide's competition/season data types list fixtures, team_stats, xG, player_stats, lineups, standings and odds, but no separate timeline coverage metric. Exact Serie A 2026/27 timeline coverage therefore remains unverified without an authorized account/API response.
- Official terms last updated 2026-10-30 permit caching/storing data while the account and plan remain active and displaying it in the user's own services, while prohibiting raw-feed redistribution. The terms also say the feed is sourced from third parties and may be late, changed, incomplete or wrong; Free responses may be cached for up to five minutes and can be served stale. The terms do not expressly name internal ML training/inference or an independently verifiable per-field source-observation timestamp.
- Free remains 50 requests/day and current-season only. This may be enough for a limited current-season match-timeline capture in principle, but it cannot replace the original 2016/17–2025/26 historical training archive and no actual request/coverage measurement was made.
- `meta.last_updated` is a potentially useful upstream timeline-last-change timestamp and is stronger provenance evidence than local collector receipt alone. It is not yet proof that each feature field was observed at that time or that the provider's upstream source timestamp is independently auditable.

Decision remains **HOLD / not approved** pending written provider confirmation of model-use scope and private retention, exact Serie A 2026/27 timeline coverage, event-category completeness (especially corners and `yellow_red_card`), and the meaning/source of `meta.last_updated`. No account/key, API call, source download, odds request, Supabase access, model inference, or target-outcome read was performed. No original V2 feature, weight, scaler/imputer, candidate SHA, lambda or gate was changed.

## 2026-11-12 recheck — cache headers, Free-plan boundaries and source-before-quote

Official pages were re-read on 2026-11-12. The Terms of Service page states **last updated 2026-10-30**. No account was created, no key was requested, and no API endpoint or API tester was called.

### Newly pinned response-cache semantics

The official Rate Limits documentation defines these response headers:

- `X-Cache: MISS`: fetched fresh from the source;
- `X-Cache: HIT`: served from Soccer Data's cache;
- `X-Cache: STALE`: an older copy was served because a fresh answer could not be fetched;
- `X-Cache-Age`: age in seconds for a STALE response.

The docs say stale fallback can be up to 15 minutes for data that changes during a match and up to **6 hours for data that does not**, including finished-match statistics. Finished-match stats are cached longer, but no maximum age for ordinary HIT responses is documented. A future adapter must therefore reject `X-Cache: STALE`, preserve the exact cache headers, response bytes and local request/response timestamps, and never infer an upstream update timestamp from `HIT` alone.

The timeline endpoint does expose `meta.last_updated`, `meta.coverage` and `meta.reason`. For timeline-backed event fields, a strict chain can require:
`meta.last_updated <= response_received_at_utc < quote_time_utc < kickoff_utc`.
For the aggregate stats endpoint, the reviewed schema does **not** document `meta.last_updated`; it exposes the required totals but only the HTTP cache headers. Such a capture can prove that the exact response bytes were received and archived before a later quote, but cannot claim the upstream provider's original observation time. Preserve the raw response SHA-256, parent run ID/SHA and archive creation time; reject STALE, missing/null required stats and any equal or reversed timestamps.

### Feature coverage and limits

- `GET /matches/{match_id}/stats` documents `corner_kicks`, `yellow_cards` and `red_cards` in `overview`, split home/away and full-match/half. Missing periods are `null`, never zero; detailed stats may return 404 when not collected.
- `GET /matches/{match_id}` documents normal-time `score.home/away` and separate extra-time/penalty fields. The original Serie A league-only feature contract must not accidentally ingest cup shootouts or extra-time results.
- `GET /matches/{match_id}/timeline` documents `goal`, `own_goal`, `penalty_scored`, `corner_kick`, `yellow_card`, `red_card` and `yellow_red_card`, with team identity and event order. Timeline coverage is explicitly `full` or `none`; `none` must be rejected, not treated as zero events.
- The public Free plan is **$0, 50 requests/day, 10 requests/minute, current season only, all stats endpoints, no odds and no webhooks**. Each paginated page is a separate request; `per_page=100` is documented for match lists. The Free plan's live cache is normally five minutes; finished-match stats are cached longer. Odds endpoints are Pro/Business only and are outside this task.

### Rights interpretation — still HOLD

The Terms grant a non-exclusive, non-transferable licence to use the data in the user's own websites, apps and products (including paid products), and permit caching/storage **while the account is open and the plan active**. The licence ends when the account or terms end. Raw feed resale, sublicensing and redistribution as a standalone feed/dataset are prohibited.

This is materially promising for a free internal source and own-product feature pipeline, but the terms do not explicitly name ML model training/inference or the long-term retention of derived feature evidence after account closure. They also say the data belongs to Soccer Data or providers it licenses, while the documentation does not identify the upstream provider separately for each field. Written confirmation is still required for:
1. frozen-model feature engineering/inference in this prediction product;
2. private retention of raw response archives and derived feature snapshots for reproducible research while the Free account remains active;
3. what must be deleted when the account/plan ends, and whether hashes/derived non-raw records may be retained;
4. the provider's authority to grant these uses for the underlying Serie A feed.

Exact Serie A 2026/27 `team_stats` and timeline coverage, completed-event counts and null rates still require an authenticated coverage call. No key exists in this audit and no call was made. The Free plan is current-season only and cannot replace the 2016/17–2025/26 historical training archive; it could only be considered as a separately preregistered current-season input supplement under the unchanged 19-feature contract.

**Decision remains HOLD.** Soccer Data is the strongest currently documented free candidate, but no ingestion, archive, feature build, inference or evaluation is authorized until written ML/retention rights, exact Serie A coverage and private-storage gates pass. Do not call odds endpoints, create an account/key, or use any paid plan.

### Betting-product licensing clause

The same Terms also state that if data (including odds) is used in a betting, gaming or trading product, the customer is responsible for obtaining any licences required in every territory where the product is offered. Because the original V2 project is a 1X2 prediction product, its intended product classification and any applicable territory-specific permissions must be reviewed before using this feed in the site. The Free plan excludes odds endpoints; this audit does not propose or call them. This clause is an additional reason to keep the source on HOLD until the provider's written clarification and the project's legal position are documented.