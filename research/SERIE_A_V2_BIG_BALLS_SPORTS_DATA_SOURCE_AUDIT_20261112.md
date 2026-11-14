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


## 8. Addendum — exact Serie A registry and measured-coverage page

A second pass checked the vendor's **league-specific endpoint registry** and its coverage page, not only the OpenAPI and product FAQ.

- The Serie A entry in https://bigballsdata.com/league-endpoints.json lists `GET /v1/matches/{id}/statistics` as Free.
- This means the OpenAPI, league-specific endpoint registry and FAQ all say the route is Free. The Serie A product-page plan matrix still places “Advanced match statistics: possession, shots, cards and xG” under Edge. The exact field entitlement is therefore still contradictory in the vendor's own public material; the endpoint registry is the most specific positive evidence, but written confirmation is still required before a request.
- The general coverage page says it was last refreshed 2026-11-06, with 59/148 endpoints confirmed serving. Soccer `team_stats` is labelled Partial. In the Serie A section, the currently listed confirmed endpoints are `/v1/matches`, `/v1/standings`, `/v1/stored/matches` and `/v1/leagues/{id}/xg-leaders`; the per-match statistics endpoint is not listed there. This does not prove the route returns no Serie A statistics, but it does mean the public measured-coverage page does not establish that it serves the required 2026/27 match rows.
- The Free `GET /v1/as-of/coverage` endpoint is not a workaround for this gap. Its documented relations are only `odds`, `player_props` and `player_availability`; it does not report `fixture_statistics`/team-stat coverage.

Additional official pages:
- https://bigballsdata.com/league-endpoints.json
- https://bigballsdata.com/coverage
- https://bigballsdata.com/openapi.json (`/v1/as-of/coverage`)

**Revised decision:** the route is listed as Free by the most specific registry, but the actual Serie A 2026/27 per-match statistics coverage remains unproven. Do not create an API key or make a request until the vendor confirms both Free-tier entitlement and measured coverage for all required fields. The source-before-quote and SHA design remains only a proposed design, not an implemented or tested integration.


## 9. Recheck of mutable official documentation — 2026-11-12 06:47 UTC

This recheck used only public provider documentation and terms. No account/key was created, no API or odds endpoint was called, no match payload or result was opened, and no dataset was downloaded.

### Rights clarification now visible in the current Terms

The current Terms page (effective 2026-08-10) expressly says that a customer may store API responses, use stored data as input to internal models including training/evaluation/backtesting, and publish or sell derived models, scores, predictions and aggregates. It prohibits redistributing the raw data feed or republishing raw field values. The provider's 2026-10-16 changelog says the Terms were updated to address storage, model use and derived outputs.

This is a positive provider-side grant for Big Balls data. It does **not** establish the upstream licence or field-level source lineage for the exact Serie A corners/cards rows, and it does not resolve the separate Football-Data training provenance of the already-frozen original candidate. Big Balls cannot grant rights in the candidate's pre-existing Football-Data training corpus.

Official pages:
- Terms: https://bigballsdata.com/legal/terms
- Changelog: https://bigballsdata.com/whats-new

### Free-plan and history limits remain contradictory

The current official pages now disagree on both request quota and history depth:

| Official page | Free quota | Free history | Other relevant statement |
|---|---:|---|---|
| Homepage / pricing | 1,000/day (2,000 with GitHub) | current + most-recent season | scores, standings, stats; odds are Edge+ |
| Soccer API page | 250/day (500 with GitHub) | current season only | 13-season archive exists, but Free is limited to current season |
| Serie A page | 1,000/day (2,000 with GitHub) | page's displayed cohort is 2025/26 | reports 4,591 finished matches and team stats on 4,210 (92%) |

The Serie A page's 92% figure is an aggregate across its displayed population; it is not a measured 2026/27 per-match field-completeness result. The page still displays a 2025/26 all-club snapshot, so it cannot establish current 2026/27 coverage by itself.

Official pages:
- Homepage: https://bigballsdata.com/
- Pricing: https://bigballsdata.com/pricing
- Soccer API: https://bigballsdata.com/soccer-api
- Serie A API: https://bigballsdata.com/serie-a-api

### Current coverage page does not close the statistics-route gap

The current coverage page says its public endpoint list was last refreshed 2026-11-06 and that only endpoints confirmed serving at that refresh are listed. In the Serie A section it lists:
- `/v1/matches`
- `/v1/standings`
- `/v1/stored/matches`
- `/v1/leagues/{id}/xg-leaders`

It does not list `/v1/matches/{id}/statistics`. The dedicated Serie A page reports 92% team-stat coverage, and the OpenAPI/league registry previously reviewed list the statistics route as Free, but the public coverage inventory does not independently confirm that route serving the required 2026/27 rows. Absence from that list is not proof that the route is unavailable; it is a missing confirmation.

The changelog entry dated 2026-10-16 also says two stale claims about `GET /v1/matches/:id/statistics` were corrected. This makes the current endpoint contract and its measured coverage—not the marketing summary—the required authority for any future check.

Official page: https://bigballsdata.com/coverage

### Source-before-quote and original-candidate boundary

The stored-only statistics route and hourly ingestion model remain potentially compatible with an immutable post-match capture: preserve exact response bytes, UTC retrieval time, response metadata and SHA-256, then require the complete source archive to precede any later quote strictly. However, the statistics response still does not document a per-field upstream `as_of` timestamp. The separate stored-stats surface exposes `fetched_at`/as-of metadata but is documented as often empty for soccer team-stat rows. Local capture time proves when our copy was observed; it does not prove the upstream provider's original observation time or field-specific source lineage.

The current official pages therefore improve the rights picture but do not satisfy the remaining operational evidence:
1. written confirmation of the actual Free quota/history window and Free entitlement for the exact Serie A `corner_kicks`, `yellow_cards`, and `red_cards` fields;
2. a measured, season-specific 2026/27 per-match completeness result for those fields;
3. field/provider lineage and the licence applicable to each required field;
4. confirmation that immutable local capture time plus raw-response SHA is an acceptable source-before-quote attestation where the stats route has no upstream per-field timestamp; and
5. separate resolution of the original candidate's Football-Data training/inference rights.

### Revised disposition

**Big Balls remains `CONDITIONAL_CANDIDATE_NOT_APPROVED`.** The current Terms expressly permit internal model use of Big Balls data, but the Free plan/history pages conflict, the current public coverage inventory does not confirm the per-match statistics route for Serie A 2026/27, and upstream field lineage/source time remain unresolved. The frozen original candidate's Football-Data provenance is a separate unresolved gate.

No API key, API call, odds request, download, source archive, Supabase access/write, feature build, model inference, target-outcome read, refit, threshold change, production artifact change, or schedule change was performed. The original 19 features, candidate SHA, weights, scaler/imputer, `active_lambda=0`, `shadow_lambda=1`, and 30-event outcome gate remain unchanged.


## 10. Fresh mutable-documentation check — 2026-11-12 13:54 UTC

This check used only the provider's public Terms, pricing, Serie A page, coverage page, and generated league-endpoint registry. No account/key was created, no API/odds request was made, and no match payload or dataset was downloaded.

### The exact statistics-route Free entitlement is still contradictory

The current generated league-endpoint registry lists `GET /v1/matches/{id}/statistics` as **Free** for soccer and describes it as per-team post-match statistics:
https://bigballsdata.com/league-endpoints.json

The current Serie A page contradicts that in its own plan matrix: “Advanced match statistics: possession, shots, cards and xG” and the same `/v1/matches/{id}/statistics` route are marked **Edge**. The page's explanatory plan summary also says these capabilities start at Edge. Yet the FAQ says the route is Free except `expected_goals`, which is Solo+:
https://bigballsdata.com/serie-a-api

The Free plan summary on that page lists scores, schedules, standings, teams, players and final box scores; it does not explicitly list the advanced match-stat fields needed by the frozen feature contract. The current public pages therefore do not provide an unambiguous entitlement for `corner_kicks`, `yellow_cards`, and `red_cards`.

**Decision remains HOLD.** Do not create a key or test the endpoint until the provider confirms in writing that these exact fields are included on Free for Serie A. No paid tier is acceptable under the project constraints.

### Freshness and measured coverage are not enough for source-before-quote

The Serie A page says its served sources were checked on **2026-11-10 16:01 UTC**. It gives a separate source-as-of time for standings and odds, but does not publish a per-match/per-field upstream observation timestamp for the required team-stat rows. Its general coverage page says the endpoint inventory was last refreshed **2026-11-06** and labels soccer `team_stats` as **Partial**:
https://bigballsdata.com/serie-a-api
https://bigballsdata.com/coverage

The dedicated page's public counts are also not a season-specific completeness proof for the 2026/27 required fields. The current page reports 4,941 Serie A matches across 13 seasons and 4,671 finished games in its archive summary; an earlier rendered section exposed a different finished-match/team-stat denominator. These aggregate figures cannot be used to infer that every 2026/27 match has complete goals, corners and card fields.

The Terms explicitly permit storing responses and using stored data in internal models, including training/evaluation/backtesting, and permit derived outputs; raw-field redistribution is prohibited. They also disclaim completeness, accuracy and uninterrupted availability, noting that upstream sources can degrade or fail and response confidence metadata is the quality signal:
https://bigballsdata.com/legal/terms

That is a positive provider-side use grant, but it does not resolve field-level upstream lineage or the missing upstream observation time. Local retrieval time + immutable raw-response SHA can prove when our archive existed; it cannot by itself prove when the upstream provider first observed each field.

### Quota page discrepancy

The current pricing and Serie A pages say Free is 1,000 requests/day (2,000 with GitHub), while the soccer API page still surfaced a 250/day (500 with GitHub) statement in the public search snapshot. Do not design a collector around the larger number until the provider confirms the applicable quota for a Serie A Free key.

### Revised disposition

`CONDITIONAL_CANDIDATE_NOT_APPROVED` remains unchanged. The next permissible step is written clarification from the provider, not an API call. Required answers remain:

1. Free entitlement for the exact Serie A corners/yellow/red fields;
2. current 2026/27 match-level completeness by required field;
3. upstream provider and licence for each field;
4. whether the provider can expose field-level `as_of`/fetched-at timestamps or formally accepts immutable capture-time + SHA as the source-before-quote proof;
5. the effective Free quota and current-season retention rules.

No source integration, feature build, inference, target-outcome read, refit, threshold change, production artifact change, Supabase access/write, schedule change or paid request occurred. The original candidate SHA, 19-feature contract, weights, scaler/imputer, `active_lambda=0`, `shadow_lambda=1`, NO_BET and the 30-event evaluation gate remain unchanged.



## 11. Fresh official-source recheck — 2026-11-14 08:45 UTC

This recheck used only public Big Balls terms, pricing, soccer hub, Serie A plan matrix, coverage page and licence notices. No account/key was created; no API, odds or match-data request was made; no match payload, result, Supabase row or source archive was accessed.

### Positive rights evidence, with an unresolved upstream boundary

The current Terms (effective 2026-08-10) expressly permit storing API responses and using stored data as input to internal models, including training, evaluation and backtesting. Derived models, scores, predictions and aggregates may be published or sold; raw feed/field redistribution is prohibited. The licence-notices page now explicitly lists “Football data provided by the Football-Data.org API”.

This is a positive provider-side internal-model grant, but the licence notice is not field-specific. It does not identify whether the exact Serie A `corner_kicks`, `yellow_cards` and `red_cards` values returned by `/v1/matches/{id}/statistics` are all sourced from Football-Data.org, another supplier, or a mixture, nor which upstream licence applies to each field. No written evidence was found that resolves the upstream rights for these exact fields.

Official pages:
- Terms: https://bigballsdata.com/legal/terms
- Licence notices: https://bigballsdata.com/attribution

### Free entitlement is still contradictory in the most relevant official page

The current soccer hub lists `GET /v1/matches/:id/statistics` as Free and says the `expected_goals` field is Solo+. The Serie A page's plan matrix is more restrictive: “Advanced match statistics: possession, shots, cards and xG” and the same endpoint are marked Edge-only; the expanded plan explanation repeats “Starts at Edge”. Its FAQ then says the route is Free except for `expected_goals`, which is Solo+.

The current Serie A page also states:
- Free: current season only;
- Solo/Trio: up to five seasons;
- Edge/Pro: all available history;
- Free request allowance: 1,000/day (2,000 with GitHub).

The public documentation therefore does not unambiguously authorize a Free key to retrieve the exact team-stat fields needed by the frozen V2 features. The most specific Serie A plan matrix says those advanced statistics are Edge-only; the more general soccer hub and FAQ disagree. A paid plan is outside project constraints and is not an option.

Official pages:
- Soccer hub: https://bigballsdata.com/soccer-api
- Serie A plan matrix and FAQ: https://bigballsdata.com/serie-a-api
- Pricing: https://bigballsdata.com/pricing

### Coverage and freshness still do not prove the required 2026/27 rows

The current Serie A page says its served sources were checked on 2026-11-14 08:38 UTC and displays 11 matches played for each of the 20 clubs. That is useful schedule/standings context, but the freshness section does not expose a separate per-match team-stat source timestamp or a field-completeness denominator for the 2026/27 corners/cards required here.

The general coverage page says its endpoint inventory was last refreshed 2026-11-06, only 59/148 endpoints were confirmed serving at that refresh, and soccer `team_stats` is Partial. The Serie A confirmed endpoint list includes `/v1/matches`, `/v1/standings`, `/v1/stored/matches` and `/v1/leagues/{id}/xg-leaders`, but does not list `/v1/matches/{id}/statistics`. Its absence is not proof of unavailability; it is a missing independent confirmation.

The soccer hub documents 40 team-stat fields, including Won Corners, Yellow Cards and Red Cards, but its general schema is not a measured Serie A 2026/27 completeness report. The Serie A page's own FAQ says missing/null values must not be converted to zero. The documentation also warns that source corrections can change completed match/player rows after the final whistle.

Official pages:
- Coverage: https://bigballsdata.com/coverage
- Soccer hub stats: https://bigballsdata.com/soccer-api
- Serie A freshness/FAQ: https://bigballsdata.com/serie-a-api

### Updated feature and provenance interpretation

The 19-feature mapping remains structurally plausible: scores can supply 3/1/0 points and goals; the required per-team match-stat fields would supply corners and cards. However, the Free plan's current-season-only scope and 11 matches per club do not prove that every team has the complete last-10 and venue-last-5 history needed for all frozen features. No per-match 2026/27 field coverage was measured, and no values were fetched.

The statistics endpoint still lacks documented per-field upstream observation/correction timestamps. A local UTC response-received timestamp plus immutable raw-response SHA can prove when our copy existed before a later quote; it cannot prove the original upstream observation time. Because the vendor also documents post-match corrections, any future approved adapter must preserve each response version immutably and reject missing fields rather than fill them with zero.

The original candidate's Football-Data training provenance is a separate unresolved rights gate. Big Balls' current internal-model grant cannot retroactively license the existing Football-Data training corpus or independently authorize this project's frozen-candidate inference.

### Revised disposition

**`CONDITIONAL_CANDIDATE_NOT_APPROVED` remains unchanged.** The public Terms grant internal model use for Big Balls data, but:
1. the Serie A plan matrix says the required advanced statistics route starts at Edge while the soccer hub/FAQ say Free;
2. per-match 2026/27 corners/cards completeness is not measured publicly;
3. upstream provider and licence are not mapped to each required field;
4. no upstream per-field observation/correction timestamp is documented;
5. private raw-data retention is not available in the current public GitHub repository; and
6. the frozen original candidate's separate Football-Data rights remain unresolved.

The next permissible step is written provider clarification and a separately approved private-storage design—not an API key, endpoint probe, or data request. No API key, request, download, odds access, Supabase access/write, source capture, feature build, inference, target-outcome read, refit, threshold change, production artifact change, or schedule change was performed.

The original candidate SHA, ordered 19-feature contract, weights, scaler/imputer, training fingerprint, `active_lambda=0`, `shadow_lambda=1`, NO_BET and the 30-primary-completed-forecast outcome gate remain unchanged.
