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


## 12. Current OpenAPI and plan recheck — 2026-11-15 01:56 UTC

This recheck read only the provider's public Terms, pricing page, Serie A page, licence notices and OpenAPI document. The OpenAPI currently advertises supported contract versions `2026-09-01` and `2026-11-09`. No account/key was created, no endpoint was called, and no match payload or source archive was accessed.

### More precise endpoint evidence

The current OpenAPI describes `GET /v1/matches/{id}/statistics` as a post-match team-stat endpoint:

- `x-bbs-min-plan: free`;
- factual box-score fields are available on Free;
- `expected_goals` is absent below Solo;
- data is persisted hourly in `fixture_statistics`;
- the endpoint is stored-only and does not fetch upstream on request;
- the provider says the upstream feed generally posts within about 30 minutes after full time for covered leagues;
- when statistics are not yet present, the endpoint returns `meta.available=false` and null home/away sides.

The current `FixtureTeamStatistics` schema explicitly includes nullable integer `corner_kicks`, `yellow_cards` and `red_cards`. It also states that all stat fields can be null where a league does not track a metric. Missing/null values must remain missing; they must never be converted to zero. Goals and points remain derived from the match score/linescore under the existing frozen builder's rules.

This is stronger structural evidence than the earlier generic field list. It is still not a measured 2026/27 Serie A field-completeness result.

### The plan conflict remains unresolved

The general pricing page currently says Free is one selected sport at a time and includes the current plus most-recent season, with 1,000 requests/day (2,000 with GitHub) and 100 requests/minute. The Serie A-specific page still says Free covers only the current season, while Solo/Trio reach five seasons and Edge/Pro reach the full archive. The Serie A plan matrix/FAQ and the OpenAPI Free entitlement for the team-stat endpoint also remain inconsistent.

Therefore the general pricing page does not prove that a Free Serie A key can retrieve every required historical row or every required team-stat field. No paid tier is considered.

Official references:
- Current pricing: https://bigballsdata.com/pricing
- Serie A coverage and plan page: https://bigballsdata.com/serie-a-api
- Current OpenAPI: https://bigballsdata.com/openapi.json

### Refined source-before-quote interpretation

The stored-only endpoint makes a local immutable capture timestamp useful evidence: if the exact raw response bytes are received at UTC time (T_s), hashed with SHA-256, and never overwritten, then that exact version was available to this project at (T_s). A later quote is admissible only if (T_s < T_q < T_k), with the parent capture run completed before (T_q), all hashes verified, and the feature rows restricted to completed matches before the target fixture.

The absent upstream per-field timestamp is therefore a freshness/correction limitation, not by itself a reason that local source-before-quote ordering is impossible. It prevents claims about the provider's original observation or correction instant. Any later corrected response must be a new immutable version with a new capture timestamp and hash; the earlier archived bytes must not be replaced.

### Upstream rights remain the decisive unresolved issue

The provider's Terms expressly grant storage and internal-model use for its API responses. Its licence-notices page also says football data is provided by the Football-Data.org API. The public pages do not map `corner_kicks`, `yellow_cards` and `red_cards` individually to their upstream source or state which upstream licence covers each field. The Football-Data.org attribution alone does not establish that Big Balls' internal-model grant supersedes or includes all upstream rights.

Written provider confirmation is still required for the exact Serie A fields and their upstream licence. The separate rights status of the original frozen training corpus must also be resolved independently.

### Decision

**`CONDITIONAL_CANDIDATE_NOT_APPROVED` remains unchanged.** The OpenAPI now gives a plausible Free endpoint and a workable local source-before-quote archive design, but the plan/season conflict, exact 2026/27 field coverage, upstream field-level rights, private raw-response retention, and original training-corpus rights remain unresolved.

No API key, endpoint probe, request, download, odds access, Supabase access/write/DDL, source capture, feature build, inference, target-outcome read, refit, threshold change, production artifact change or schedule change was performed. The original candidate SHA, ordered 19-feature contract, weights, scaler/imputer, training fingerprint, `active_lambda=0`, `shadow_lambda=1`, NO_BET and 30-primary-completed-forecast outcome gate remain unchanged.


## 13. Official documentation recheck — 2026-11-19

This recheck used only the provider's public static Terms, current Serie A plan page, coverage page, changelog, and OpenAPI document. No account or key was created; no API endpoint, match payload, odds, source archive, Supabase object, or target outcome was accessed.

### Free-tier entitlement: three current statements say Free, one Serie A matrix still says Edge

New official changelog entry dated **2026-11-11** says `GET /v1/matches/:id/statistics` is now available on the Free plan, correcting seven league data rows that had incorrectly shown Solo; `expected_goals` remains Solo+. The current OpenAPI independently marks `GET /v1/matches/{id}/statistics` as `x-bbs-min-plan: free`, says factual box-score fields are free, and marks only `data.home.expected_goals` / `data.away.expected_goals` as Solo+. The current Serie A FAQ likewise says the route is Free except for the `expected_goals` field.

However, the same current Serie A page's plan matrix (lines 957–958) and expanded plan explanation (line 982) still label “Advanced match statistics: possession, shots, cards and xG” / `/v1/matches/{id}/statistics` as Edge-only. This is a live internal documentation contradiction, not a resolved entitlement. The route-level OpenAPI/changelog/FAQ evidence is stronger and newer than the older matrix wording, but written confirmation remains prudent before relying on the Free entitlement.

### Current coverage still does not establish Serie A team-stat completeness

The public coverage page is updated on 2026-11-16, but its measured endpoint inventory explicitly says the last refresh was **2026-11-06**. It reports soccer `team_stats` as Partial and its Serie A confirmed-endpoint list still omits `/v1/matches/{id}/statistics`. This does not prove the route is empty; it means the published measured coverage does not prove that all 2026/27 Serie A matches have the corners/cards fields needed by the frozen 19-feature builder.

### Freshness semantics clarified

The OpenAPI still describes `/v1/matches/{id}/statistics` as stored-only and persisted hourly, with the upstream feed generally posting within about 30 minutes after full time. Its response schema contains the home/away statistic objects but no per-match or per-field `observed_at`, `source_updated_at`, revision, or correction timestamp.

The separate `/v1/stored/matches/{id}/stats` route documents per-row `as_of` and `freshness_basis=ingested_at`, but its own contract warns that soccer `team_stats` may be empty and points to `/v1/matches/{id}/statistics` for team-level soccer stats. Its ingestion timestamp is not an upstream value-change timestamp.

For a genuinely prospective cohort, a local immutable response archive can still establish that the exact bytes were in this project's possession before a later quote: capture UTC, response SHA-256, complete-manifest SHA-256, parent-run completion, quote time and kickoff must be recorded, with strict `source_capture_completed_at < quote_time < kickoff`. A later correction must create a new immutable archive version, never overwrite the earlier bytes. This proves project-availability time, not the provider's original observation/correction time.

### Decision remains HOLD

`CONDITIONAL_CANDIDATE_NOT_APPROVED` remains the correct disposition. The Nov 11 changelog improves the evidence for Free route entitlement but does not resolve:
1. the contradictory Edge-only Serie A plan matrix;
2. actual 2026/27 per-match completeness for corners/yellow/red cards;
3. upstream vendor and licence mapping for the exact required fields;
4. the independent private-storage requirement while the GitHub repository is public; or
5. the separate rights/provenance status of the frozen candidate's historical Football-Data training corpus.

No API key, request, download, odds access, Supabase read/write/DDL, source capture, feature build, inference, target-outcome read, refit, threshold change, production artifact change, schedule change or main update was performed.

The frozen candidate SHA, 19-feature order, weights, scaler/imputer, training fingerprint, `active_lambda=0`, `shadow_lambda=1`, NO_BET and 30-primary-completed-forecast outcome gate remain unchanged.

Official references:
- Terms (effective 2026-08-10): https://bigballsdata.com/legal/terms
- Serie A plan matrix and FAQ: https://bigballsdata.com/serie-a-api
- Current OpenAPI: https://bigballsdata.com/openapi.json
- Changelog (2026-11-11 Free endpoint clarification): https://bigballsdata.com/whats-new
- Coverage (measured refresh 2026-11-06): https://bigballsdata.com/coverage


## 14. Distinguish the Big Balls upstream from the original candidate's training source — 2026-11-19

The Big Balls licence notice attributes its football feed to the **Football-Data.org API**. The original frozen V2 candidate's ten historical training/source CSVs are instead downloaded from **Football-Data.co.uk** at `https://www.football-data.co.uk/mmz4281/{season}/I1.csv`. These are separate services and separate terms. Big Balls' internal-model grant must not be treated as a licence for the already-trained candidate's Football-Data.co.uk corpus.

The current official Football-Data.co.uk data page (displayed updated **2026-11-16**) says its free CSV/Excel data is intended for private individuals only and explicitly excludes commercial or data-training products using automated bots/scrapers/AI; it also says the data are provided for league match prediction only. It says the files are **at least** updated twice weekly; that is an update cadence, not a maximum download quota. The exact page is https://www.football-data.co.uk/data.php.

Accordingly, even if Big Balls' Free route entitlement and its own storage/internal-model terms are later confirmed in writing, that does not clear the original candidate's historical training corpus. The frozen candidate's existing training-data rights and any continuing use of its learned weights remain a separate **HOLD** pending explicit provider permission or a documented legal/rights determination. No retraining, refit, substitute source, candidate/weight change, or production promotion is authorized by this audit.

This is a correction/clarification only. No Football-Data.co.uk CSV was requested or downloaded; no Big Balls key or endpoint was used; no quote, Supabase object, outcome, feature, or inference was accessed.


## 15. Fresh official documentation recheck — 2026-11-19 06:00 UTC

This recheck used only public static terms, pricing, the public Serie A page, the generated league endpoint registry and the published OpenAPI schema. No account/key was created or used; no API endpoint, match-data response, odds, Supabase object, feature build, inference or target outcome was accessed.

### What is now clearer

1. **The non-xG statistics route is declared Free by the machine-readable gateway registry.** The current generated [league endpoint registry](https://bigballsdata.com/league-endpoints.json) lists `GET /v1/matches/{id}/statistics` as `plan: free` for Serie A (and the other football league pages). The current [OpenAPI](https://bigballsdata.com/openapi.json) likewise declares `x-bbs-min-plan: free`; its field-entitlement list puts only `data.home.expected_goals` and `data.away.expected_goals` at Solo. The endpoint description says factual box-score fields are Free and xG is omitted below Solo. The generated registry is described by the Serie A page as using the same registry enforced by the gateway.

2. **The human-facing plan matrix is still inconsistent.** The [Serie A page](https://bigballsdata.com/serie-a-api) matrix shows the combined row “Advanced match statistics: possession, shots, cards and xG” only at Edge, while its FAQ says the statistics route is Free and xG is Solo+. The route-level machine registry and OpenAPI agree on Free for the route, but the combined marketing row still conflicts. Treat the route as a strong Free candidate, not as a permission to call it; obtain written confirmation if the entitlement distinction is material.

3. **Current-season fixtures/standings are present, but field-level match-stat completeness is not established.** The Serie A page was checked at 2026-11-19 05:54 UTC and showed 2026/27 standings with 11 matches per club (table source 05:12 UTC). It reports 4,941 served Serie A matches across 13 seasons, with Free covering the current season only. This is evidence of current-season league coverage, not evidence that every 2026/27 match has the required per-team corners/cards fields. The page's freshness panel does not publish a 2026/27 per-match completeness denominator for `fixture_statistics`.

4. **The endpoint can supply the relevant field family after a match, but it is not a pre-match feed for that same match.** The OpenAPI describes `GET /v1/matches/{id}/statistics` as post-match team statistics, persisted hourly; the upstream normally posts within roughly 30 minutes after full time. Its schema includes `corner_kicks`, `yellow_cards` and `red_cards`; match goals remain authoritative in the linescore. These can only be used as lagged inputs for a later fixture after the response has been captured and frozen.

5. **No provider-origin observation/correction timestamp is exposed for this statistics object.** `FixtureTeamStatistics` has no `observed_at`, `source_updated_at`, revision or per-field timestamp. The route's custom metadata only documents `expected_goals_source`; the shared `ResponseMeta` provides an opaque source-tier label, confidence/cache fields and request id, but no source observation time. The OpenAPI explicitly says the source label is opaque and does not disclose vendor identity. A local capture timestamp plus raw-response SHA can prove that this project's exact bytes existed before a later quote; it cannot prove when the upstream first observed or last corrected those values.

### Upstream rights remain a hard HOLD

- Big Balls' [Terms of Service](https://bigballsdata.com/legal/terms), effective 2026-08-10, allow storing responses and using stored data in internal models (including training/evaluation/backtesting); derived outputs may be published/sold, while raw feed and raw field-value redistribution are prohibited.
- Big Balls' [licence notices](https://bigballsdata.com/attribution) attribute football data to the Football-Data.org API. Its OpenAPI source field is only an opaque tier label (for example `aggregator-free` or `mixed`), not a vendor/field-level provenance map.
- The public [Football-Data.org terms](https://www.football-data.org/about) remain dated 2018-06-01. They require a single application, fair use and attribution, but do not expressly document the specific stored-data/ML-training grant described in Big Balls' own terms.

Therefore Big Balls' own internal-model grant is positive evidence, but it does not by itself prove the upstream licence for the exact Serie A corners/cards fields. Written confirmation from Big Balls that the upstream grant covers these exact fields and this internal model use remains required. This is not a finding that the upstream use is prohibited; it is an unresolved rights question.

### Decision

`CONDITIONAL_CANDIDATE_NOT_APPROVED` / **HOLD remains correct**. The plan-tier question is now substantially narrowed in favour of Free for non-xG statistics by the generated gateway registry and OpenAPI, but no API call or data capture is authorized until all of the following are resolved:

1. written field-level upstream rights confirmation for the required Serie A fields and internal-model use;
2. a measured 2026/27 per-match completeness audit for corners/yellow/red cards;
3. a documented private retention path for raw responses and SHA-256 manifests (the GitHub repository is public);
4. immutable capture records with `source_capture_completed_at < quote_time < kickoff`, exact response SHA-256, manifest SHA-256, parent-run identity and no overwrite on later corrections; and
5. separate rights clearance for the original candidate's historical Football-Data.co.uk training corpus and the continued use of its learned weights.

No API key, request, data download, quote read, Supabase read/write/DDL, inference, target-outcome read, model refit, threshold change, production artifact change, schedule change or main update was performed. The frozen candidate, 19-feature order, weights, scaler/imputer, training fingerprint, `active_lambda=0` and `shadow_lambda=1` remain unchanged.


## 16. Official plan-entitlement and current-season feasibility recheck — 2026-11-21 01:49 UTC

This recheck used only public Big Balls documentation, changelog, OpenAPI/coverage pages, the public Football-Data.org terms, and the published Serie A calendar/table. No account/key was created; no authenticated API request, match-stat payload, odds, source archive, Supabase object, feature build, inference, or target outcome was accessed.

### The Free route entitlement is now more strongly supported

The provider's official changelog dated **2026-11-11** states that `GET /v1/matches/:id/statistics` is available on the Free plan and that the earlier Solo classification on seven league data rows was incorrect; `expected_goals` remains Solo+. The current OpenAPI and generated league-endpoint registry also classify the route as Free, while the route schema exposes factual team-stat fields including `corner_kicks`, `yellow_cards`, and `red_cards`.

This supersedes the earlier conclusion that route entitlement itself was wholly unresolved. The older Serie A marketing matrix still labels a combined “advanced match statistics” row Edge, and the public Free-history wording is inconsistent between the homepage/pricing and soccer/Serie A pages. The current evidence therefore supports **Free access to non-xG match statistics at the route level**, but it does not prove the actual entitlement of a particular account or the completeness of the required Serie A rows. Do not use a paid tier.

Official references:
- Changelog, 2026-11-11: https://bigballsdata.com/whats-new
- OpenAPI: https://bigballsdata.com/openapi.json
- Generated league endpoint registry: https://bigballsdata.com/league-endpoints.json
- Serie A page: https://bigballsdata.com/serie-a-api
- Pricing: https://bigballsdata.com/pricing
- Soccer API page: https://bigballsdata.com/soccer-api

### Current-season history window is plausible, not yet measured

The official Lega calendar places the 2026/27 opening round on **22–24 August 2026**. The public Big Balls Serie A page checked on **2026-11-21** shows round 11, with all 20 clubs at 11 matches played and latest completed fixtures on 7–8 November. This implies **110 completed fixtures** through that round (20 clubs × 11 appearances ÷ 2).

The Free history is described as current-season on the soccer page and current + most-recent season on the general pricing page; the dedicated Serie A page has also shown a stale 2025/26 panel. If the Free match-list route returns all 110 2026/27 fixtures with the required statistics, the documented 100-row page limit means at most two pages are needed. The original last-10 and venue-last-5 rolling windows would then be long enough in principle.

This is a **date/window feasibility estimate only**. It is not an authenticated Free-key response, does not establish that every match has a statistics row, and does not establish non-null corners/cards for every required fixture.

### Remaining blockers — HOLD is unchanged

1. **Upstream rights / field lineage:** Big Balls' licence notice attributes football data to Football-Data.org API, but the public response's source label is opaque and does not map each required field to a vendor/licence. Football-Data.org's public Terms remain dated 2018-06-01 and require one application, fair use and attribution, but do not expressly document the same internal-model/storage grant. Obtain written field-level confirmation that the upstream rights cover Serie A corners/yellow/red cards and internal-model use.
2. **Measured completeness:** the public coverage page (last endpoint refresh 2026-11-06) labels soccer team statistics Partial and does not provide a 2026/27 per-fixture completeness matrix for corners/yellow/red cards. The Serie A aggregate team-stat percentage is not a current-season field-level denominator.
3. **Upstream observation/correction time:** the statistics response has no per-match/per-field upstream observation, revision or correction timestamp. A local capture timestamp + exact raw-response SHA can prove when our immutable copy existed, not when the upstream first observed or corrected each field. Any future cohort must preserve exact response bytes, response/manifest SHA-256, UTC capture time and authenticated parent-run completion, with strict `source_capture_completed_at < quote_time < kickoff`; corrections must create a new immutable version.
4. **Private retention:** the repository is public. Raw responses and manifests must not be committed or uploaded as public GitHub Actions artifacts. A verified private retention destination is not yet approved/implemented.
5. **Original candidate training provenance:** Big Balls' terms do not clear the frozen candidate's separate Football-Data.co.uk training corpus or the continued use of its learned weights. That remains an independent rights HOLD.

### Decision

**`CONDITIONAL_CANDIDATE_NOT_APPROVED` / HOLD.** The 2026-11-11 changelog materially improves the Free-tier entitlement evidence, and the current-season window is nominally sufficient by date. Neither finding authorizes an account/key, request, download, source capture, feature construction or inference. Written upstream rights, measured per-match completeness, private retention, source-time semantics, and separate original-training-corpus rights remain unresolved.

The original candidate SHA, ordered 19-feature contract, weights, scaler/imputer, training fingerprint, `active_lambda=0`, `shadow_lambda=1`, NO_BET and the 30-primary-completed-forecast outcome gate remain unchanged. No paid API, Supabase write/DDL, target-outcome read, refit, threshold change, production artifact change, schedule change or main update occurred.


## 17. Current Football-Data.co.uk rights clarification — 2026-11-21 02:09 UTC

The official fair-data policy page https://football-data.co.uk/contact.php is visibly updated **2026-11-20**. It states that free CSV/Excel use is intended for private individuals for personal betting and/or academic research only, via manual download or at most light automated download **twice per week maximum**. It separately excludes commercial or AI data-training projects using automated bots/scrapers; requests for permission for such usage will not receive a response, and users should assume no permission is granted.

The separate data/download page's “at least updated twice weekly” wording is a publication cadence, not permission to download more frequently. Both statements can be true: files are refreshed at least twice weekly, while automated downloads for permitted private/academic use are capped at twice weekly. The daily automated collector and the frozen candidate's AI/model-training use remain outside the stated free-use scope.

This is distinct from Football-Data.org, the upstream attribution named by Big Balls. Big Balls' terms for its own API responses do not clear the original candidate's separate Football-Data.co.uk training corpus or the continued use of its learned weights. Written permission or a separately documented rights determination is required before treating the original frozen weights as cleared for continued AI use. This records provider wording, not a legal conclusion.

No CSV was downloaded or opened, no Big Balls key/request was made, and no source/quote/Supabase data, feature, inference, target outcome, model artifact, or production file was accessed or changed. The original candidate SHA, 19-feature order, weights, scaler/imputer, training fingerprint, `active_lambda=0`, `shadow_lambda=1`, NO_BET and 30-primary-completed-forecast outcome gate remain unchanged.
