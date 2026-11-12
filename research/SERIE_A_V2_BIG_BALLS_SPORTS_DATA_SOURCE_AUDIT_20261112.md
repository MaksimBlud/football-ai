# Original MARKET_ANCHOR_1X2_V2 — Big Balls Sports Data source audit

**Audit date:** 2026-11-12  
**Scope:** research-only review of the official Big Balls Sports Data terms, Serie A product page, league endpoint registry and OpenAPI contract.  
**Verdict:** `CONDITIONAL_CANDIDATE_NOT_APPROVED`. No account, key, API request, download, odds request, Supabase access/write or model integration was performed.

## 1. Why this source is worth investigating

Big Balls Sports Data documents a current-season Serie A API and terms that expressly permit storing API responses and using stored data as input to internal models, including training, evaluation and backtesting. It also says derived models, scores, predictions and aggregates may be published or sold, while raw feed redistribution is prohibited.

Official terms (effective 2026-08-10): https://bigballsdata.com/legal/terms  
Relevant clauses: Usage rights and Acceptable use.

The Serie A page currently lists 20 clubs and 11 matches played for each club in the 2026-27 table, with the table source timestamp 2026-11-10 16:00 UTC:
https://bigballsdata.com/serie-a-api

This is potentially useful for the next prospective fixtures only. It is not a replacement historical training source: the Free tier is documented as current-season only.

## 2. Exact compatibility with the frozen 19 features

The frozen candidate remains:
- candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- feature builder Git blob: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`;
- original feature order, weights, scaler and imputer unchanged;
- `active_lambda=0`, `shadow_lambda=1` research-only.

The 19 frozen features use only rolling team-match history:
- points: last 5, last 10, venue-specific last 5;
- goals for/against: last 5, last 10 and venue-specific last 5;
- corners for/against: last 5, last 10 and venue-specific last 5;
- yellow cards: last 5 and last 10;
- red cards: last 5 and last 10.

The original feature builder computes means over the last 5/10 observations and the last 5 observations at the relevant venue. It does not require a new feature or a new fitted parameter.

The Big Balls OpenAPI documents per-team post-match statistics at `GET /v1/matches/{id}/statistics`, including:
- `corner_kicks`;
- `yellow_cards`;
- `red_cards`;
- team shots/fouls/other fields.

The match object separately carries home/away score and UTC kickoff. Points can be derived from the final score using the original 3/1/0 rule. Thus the documented field families are structurally capable of feeding the original `TeamMatch` inputs without changing the 19-feature contract.

OpenAPI: https://bigballsdata.com/openapi.json  
Endpoint description: `/v1/matches/{id}/statistics` and schema `FixtureTeamStatistics`.

**Window sufficiency, not coverage proof:** if all 11 current-season matches per club have complete team-stat rows, the current season alone is long enough for the next fixtures' last-10 and venue-last-5 windows. The public table establishes 11 played matches per club; it does **not** establish that the per-match statistics endpoint has complete coverage for those 11 fixtures. That coverage remains unverified.

## 3. Free-plan and endpoint-entitlement conflict — blocker

The official sources disagree:
- The OpenAPI marks `GET /v1/matches/{id}/statistics` as `x-bbs-min-plan: free` and says factual box-score fields are free; xG is omitted below Solo.
- The Serie A plan matrix places “Advanced match statistics: possession, shots, cards and xG” under Edge.
- The Serie A FAQ says the statistics route is Free, with only `expected_goals` requiring Solo+.
- Free is limited to the current season. Historical seasons require a paid plan.

Because these statements are inconsistent, no request may be made until the provider confirms in writing that the Serie A team-stat fields required here are actually available on Free. No paid plan is considered.

## 4. Source-before-quote and SHA feasibility

The OpenAPI describes `/v1/matches/{id}/statistics` as **stored-only**: it never fetches upstream on request; upstream statistics are persisted hourly and generally arrive within about 30 minutes after full time. This is useful for a strict pre-quote archive design:

1. request only completed prior fixtures;
2. capture the exact raw response bytes and a UTC capture timestamp;
3. hash every response and the complete manifest with SHA-256;
4. finish the source archive and its parent run before the future quote timestamp;
5. admit a future quote only when `source_capture_completed_at < quote_time < kickoff`, all hashes match, and every feature row belongs to a completed earlier fixture;
6. never update an archived response in place; corrections become a new version with a new hash and a later observation time.

**Remaining provenance limitation:** the `/v1/matches/{id}/statistics` response schema does not document a per-field `as_of` or upstream `fetched_at` timestamp. A separate `/v1/stored/matches/{id}/stats` route documents `as_of`, `oldest_as_of`, `freshness_unknown_records` and per-row `fetched_at`, but its own documentation warns that soccer team-stat rows are often empty and points to the statistics route for team-level values. The API capture timestamp plus immutable SHA can prove that our copy existed before a quote; it does not independently prove the upstream provider's original observation time. Written clarification is required before treating that as sufficient for the project's source-before-quote standard.

## 5. Upstream lineage is not field-specific

The OpenAPI describes a gateway aggregating 19+ upstream sources and says customers do not see vendor identities in the source-tier label. The public licence-notices page lists “Football data provided by the Football-Data.org API”, but does not map that notice to the Serie A team-stat fields returned by `/v1/matches/{id}/statistics`.

Sources:
- https://bigballsdata.com/openapi.json
- https://bigballsdata.com/attribution

The API terms are favourable for internal model use, but field-level upstream lineage and the licence applicable to the corner/card statistics are not established by the public pages reviewed. Do not assume the generic attribution notice resolves that gap.

## 6. Frozen-cohort boundary

The existing `MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY_V1` policy explicitly freezes `FOOTBALL_DATA_CSV`, the I1 season files, the feature-input gate and its source-before-quote rules. This audit does not amend that policy.

If Big Balls is later approved, it must be introduced only as a separately versioned prospective source cohort using the exact same original 19-feature builder and frozen candidate SHA. Do not mix Big Balls rows into the existing Football-Data cohort, backfill earlier quotes, refit weights, alter imputer/scaler values, or change the original training fingerprint.

The current candidate's stability gate remains FAILED. This source audit is not evidence of model quality and cannot open the 30-primary-completed-forecast target-outcome gate.

## 7. Decision and exact blockers

| Requirement | Current evidence | Decision |
|---|---|---|
| Contract permits internal model use | Explicit in Terms | Conditional pass |
| Free Serie A team-stat entitlement | OpenAPI/FAQ vs plan matrix conflict | Blocked |
| Required goals/corners/cards fields | Documented in match and stats schemas | Structural pass only |
| Current-season window length | 11 matches per club on 2026-11-10 | Potentially sufficient |
| Actual per-match stat coverage | No measured 2026-27 coverage for required fields | Blocked |
| Per-field upstream observation time | Not documented on statistics endpoint | Blocked |
| Upstream licence/field lineage | Generic attribution only | Blocked |
| Historical 2016/17–2025/26 on Free | Free is current-season only | Not available |

**No integration is approved.** Before any free API request, obtain written confirmation of (a) Free-tier access to Serie A `corner_kicks`, `yellow_cards`, `red_cards`; (b) measured per-match coverage for 2026/27; (c) the upstream source/licence for those fields; and (d) whether our own pre-quote capture timestamp and SHA are acceptable in lieu of upstream per-field timestamps.

No The Odds API or other paid odds source is involved. The model continues to use only already-saved, strictly pre-kickoff market snapshots. No production artifact, Supabase object, schedule, model weight or threshold is changed.
