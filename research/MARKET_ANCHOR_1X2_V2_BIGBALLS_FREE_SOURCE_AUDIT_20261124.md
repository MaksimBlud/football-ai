# Big Balls Sports Data — Free Serie A source audit for original MARKET_ANCHOR_1X2_V2

**Original review:** 2026-11-24 12:52 UTC  
**Superseding official-source recheck:** 2026-11-26 12:49 UTC  
**Provider:** [Big Balls Sports Data](https://bigballsdata.com/)  
**Decision:** **HOLD — candidate only; no account, API key, request, download, integration, feature calculation or inference.**

## Executive finding

Big Balls Sports Data is a materially stronger free-source candidate than the previously reviewed options because its official Terms of Service explicitly permit storing API responses in the user's own systems and using stored data as input to internal models, including training, evaluation and backtesting. The same terms prohibit resale or redistribution of the raw feed. The provider's public Serie A page advertises a free tier and team-level football statistics including corners and cards.

However, this is **not yet a cleared source for the original frozen V2**:

1. The current OpenAPI, soccer-hub endpoint table and FAQ say `GET /v1/matches/{id}/statistics` is Free, but the dedicated Serie A page's plan matrix lists advanced match statistics as starting at Edge. This direct first-party conflict supersedes the earlier "Free confirmed" conclusion; do not assume Free entitlement. The separate Free season-depth conflict remains unresolved.
2. The global pricing page contradicts itself: its summary says Free covers the current season, while its Free-plan bullet says current plus most-recent season; the dedicated Serie A page says current season only. This conflict remains.
3. Published Serie A team-stat coverage is 4,210 / 4,591 finished matches (91.7%) across the provider's measured archive, not a current-2026/27 per-fixture completeness result.
4. The upstream provider/field-rights chain and the meaning of per-match first-observed/correction timestamps are not independently established.
5. No authenticated Free response was examined. No account, key, API call or download was made.

The audit therefore records a **conditional candidate, not permission to integrate**.

## Provider terms and data rights

The [official Terms of Service](https://bigballsdata.com/legal/terms), effective 2026-08-10, state:

- API responses may be stored in the user's own systems and kept there.
- Stored data may be used as input to internal models, including training, evaluation and backtesting.
- Derived models, scores, predictions and aggregates may be retained/published by the user.
- Raw data may not be resold or republished as an API, file, feed, export or bulk dataset.

This is a promising written provider-level grant for **private research storage and internal model use**. It is not permission to publish the raw archive. The terms describe data as belonging to the provider or providers it licenses from, but the reviewed public terms do not identify the upstream provider or document field-level rights for each required statistic. The terms also do not separately explain raw-archive retention if an account is later closed. Those points remain for written clarification before integration.

The project must keep any future raw archive private. No GitHub artifact containing raw source bytes may be uploaded while the repository is public.

## Free-plan scope and documentation conflicts

The public global pricing page advertises:

- $0 Free tier;
- 1,000 requests/day (2,000 with a linked GitHub account);
- 100 requests/minute;
- current plus most-recent season;
- scores, standings and statistics.

The dedicated [Serie A page](https://bigballsdata.com/serie-a-api) says Free covers the current season, while the global pricing page advertises current plus most-recent season. This season-depth conflict remains unresolved. The current [OpenAPI specification](https://bigballsdata.com/openapi.json), the [soccer-hub endpoint table](https://bigballsdata.com/soccer-api), and the Serie A FAQ say `/v1/matches/{id}/statistics` is Free (with `expected_goals` Solo+). However, the dedicated Serie A page's plan matrix lists advanced match statistics—possession, shots, cards and xG—as starting at Edge. These are contradictory first-party plan statements; Free entitlement for the required Serie A team-stat fields is therefore unresolved and remains HOLD. The endpoint is stored-only, with hourly persistence, and the documentation says the upstream feed generally posts within about 30 minutes after full time. It is a post-match source for lagged features, not a live pre-kickoff stats feed. Current-season per-fixture completeness and exact season depth also remain unverified.

Free odds are not available; odds require the paid Edge plan. This audit does not propose using provider odds. The original `active_lambda=0` remains the existing market anchor, and `shadow_lambda=1` remains research-only.

## Coverage and the unchanged 19-feature contract

The provider's Serie A page reports 4,210 of 4,591 finished matches with team statistics, or approximately 91.7%, across its measured archive. This is not broken down by season, fixture, or required field. The coverage page's last published refresh is 2026-11-06.

The public soccer field catalogue lists corners, yellow cards and red cards among team-level statistics. The Serie A page says match statistics are available, but it does not publish a current-season, per-field completeness matrix. Therefore no claim of exact original 19-feature parity is justified.

The unchanged original V2 feature families require:

- points and goals derived from completed match results;
- corners for and against over the original 5/10-match and venue-5 windows;
- yellow-card and red-card counts over the original 5/10-match windows.

No substitute feature, reweighting, imputer/scaler change or candidate modification is proposed. The frozen candidate remains pinned to the exact SHA below.

## Source-before-quote, raw preservation and SHA

The provider's soccer guide says freshness differs by dataset, response source/update metadata should be read when present, and completed results/player rows can be corrected after full time. The reviewed docs do not define a per-match first-observed timestamp or a per-field correction history.

If rights and Free-plan coverage are later confirmed, the only acceptable research capture would preserve, for every response:

1. exact response-body bytes;
2. canonical match ID, season, endpoint path and non-secret query parameters;
3. response headers and any provider source/update/confidence metadata;
4. local receipt timestamp in UTC;
5. SHA-256 of the exact body bytes;
6. a private immutable manifest linking the response to its receipt time.

A later quote may be considered only if the verified source archive's receipt/upload time is strictly earlier than the quote observation time, and the quote row's own persisted timestamp is before kickoff. This proves that the project possessed those exact bytes before the quote; it does **not** prove when the upstream provider first observed every field.

No API request or source capture occurred in this audit.

## Frozen candidate — unchanged

- Experiment: `MARKET_ANCHOR_1X2_V2`
- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`
- Training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`
- Training rows: 3,799
- Features: exact ordered 19
- Original weights: 20 × 2
- `active_lambda=0`
- `shadow_residual_lambda=1`
- Historical stability gate: FAILED
- Automatic promotion: false

No retraining, refit, threshold tuning, candidate change or production `.pkl` modification is authorized by this audit.

## Required clearance before reconsideration

1. Written confirmation that the Free plan selected for this account includes the Serie A match-statistics endpoint and the required season depth.
2. A provider-supplied or account-authorized sample response showing the exact fields for corners, yellow cards, red cards, final scores and canonical IDs, with no paid endpoint.
3. Current-season per-fixture and per-field completeness evidence for 2026/27.
4. Written clarification of the upstream sources/rights covering all required fields and the provider's authority to grant private retention and internal model use.
5. Explicit confirmation of raw-response retention if the account or Free plan later ends.
6. Documented source/update timestamp and correction semantics, plus a private archive design with receipt UTC and SHA-256.
7. Separate owner authorization before any account, key, API call or source capture.

## Official documents reviewed

- [Terms of Service](https://bigballsdata.com/legal/terms)
- [Global pricing](https://bigballsdata.com/)
- [Serie A API and plan matrix](https://bigballsdata.com/serie-a-api)
- [Soccer guide: freshness, corrections and timestamps](https://bigballsdata.com/docs/soccer)
- [Endpoint reference](https://bigballsdata.com/docs/endpoints)
- [Coverage](https://bigballsdata.com/coverage)
- [Changelog](https://bigballsdata.com/whats-new)

**Bottom line:** Big Balls Sports Data remains a technically promising candidate because its terms permit private response storage and internal model research, but the required Serie A statistics endpoint's Free entitlement is contradicted by the dedicated Serie A plan matrix. It remains **HOLD_NO_INTEGRATION** until endpoint/season entitlement, current-season field coverage, upstream rights and timestamp semantics are resolved. No provider access or model operation is authorized by this audit.

## Superseding official-document check — 2026-11-24 18:19 UTC

The current first-party [OpenAPI specification](https://bigballsdata.com/openapi.json) now resolves one earlier documentation conflict:

- `GET /v1/matches/{id}/statistics` declares `x-bbs-min-plan: free`.
- The `expected_goals` fields are explicitly Solo+; xG is not one of the original 19 features.
- The current [Serie A FAQ](https://bigballsdata.com/serie-a-api) says the statistics route is Free and only expected goals is Solo+.
- The endpoint description says the response is stored-only, persisted hourly, and upstream statistics usually arrive about 30 minutes after full time. It is a post-match source for lagged features, not a live current-match pre-kickoff statistic.
- The `FixtureTeamStatistics` schema documents `corner_kicks`, `yellow_cards` and `red_cards`; match scores can supply goals and the original 3/1/0 points. This documents the required feature families, but **does not establish exact 19-feature parity** because current-season per-fixture and per-field completeness is still unknown.
- The OpenAPI introduction describes aggregation from 19+ free-tier upstream sources and 10 MCP scrapers without naming the upstream source/rights chain for each field.

The Free endpoint entitlement is now documented, but the Free season-depth conflict (global pricing versus the Serie A page), current 2026/27 field completeness, upstream rights, account-closure retention, and upstream first-observation/correction semantics remain unresolved. Local receipt UTC plus SHA-256 would prove only that the project possessed those exact response bytes before a later quote. It would not prove when the upstream first observed or corrected each field.

No account/key was created, no provider/API request or data download was made, no Supabase access occurred for this provider audit, and no integration or inference is authorized. Decision remains **HOLD_NO_INTEGRATION**.


### Season-depth contradiction recheck — 2026-11-24

The current [global pricing page](https://bigballsdata.com/pricing) is internally inconsistent: its plan introduction says Free covers the current season, while the Free-tier bullet says current plus most-recent season. The dedicated [Serie A page](https://bigballsdata.com/serie-a-api) also describes Free as current-season access. Therefore the Free season-depth entitlement remains unresolved; no multi-season access is assumed.


## Offline private pre-quote archive gate — 2026-11-24

A pure-Python validation helper and synthetic regression suite now make the future receipt/SHA protocol executable without enabling any provider access:

- `market_anchor_v2_bigballs_archive_gate.py` validates already-present raw response bytes only; it performs no HTTP, storage, Supabase, feature calculation, inference, or outcome evaluation.
- Both the canonical match response and the stored post-match statistics response must be supplied as exact bytes with matching SHA-256 values, endpoint paths, source match identity, and matching home/away team IDs. The saved quote's match ID must equal the declared target match ID.
- The source match must be finished and carry both final scores. The statistics response must explicitly report `meta.available=true`; missing corner/card fields remain listed as missing and are never converted to zero or imputed by this gate.
- The source match kickoff must precede both local receipt times; both receipts must precede private archive creation; archive creation must strictly precede the quote snapshot; and the quote chronology must satisfy `snapshot_time <= created_at < target_kickoff`.
- The archive must identify the documented Free plan, zero paid provider calls/odds, private raw storage, no public raw-artifact upload, and the exact frozen candidate SHA.
- The current provider manifest is intentionally still `HOLD_NO_INTEGRATION`. Its false authorization flags cause the gate to reject a real bundle until written provider clarification and separate owner approval exist.
- The return value explicitly states that upstream first observation is NOT proven, and that no feature calculation, imputation, model inference, Supabase write, or bet occurred.

The synthetic fixtures are contract tests only. They do not represent a real provider response, prove Free-plan account entitlement, resolve season-depth/current-field coverage, or authorize source capture. The original 19-feature order, candidate, weights, `active_lambda=0`, and `shadow_residual_lambda=1` remain unchanged.


## Superseding first-party endpoint-plan conflict and rights-gate hardening — 2026-11-25 00:52 UTC

A fresh read of the current official pages found a direct plan conflict for the exact post-match statistics endpoint:

- The [OpenAPI operation](https://bigballsdata.com/openapi.json) says the route is Free and marks only the `expected_goals` field Solo+.
- The [soccer-hub endpoint table](https://bigballsdata.com/soccer-api) and its FAQ also say the route is Free.
- The [dedicated Serie A plan matrix](https://bigballsdata.com/serie-a-api) lists advanced match statistics (possession, shots, cards and xG) as starting at Edge, while that same page's FAQ says the route is Free.

This is not a resolved entitlement. The audit manifest now records the exact conflicting statements and keeps `HOLD_NO_INTEGRATION`; no Free key entitlement is assumed. The statistics route remains a stored, post-match dataset (not a pre-kickoff live feed), suitable only as a possible lagged input if rights and timing are later cleared.

The offline archive gate also had a caller-controlled rights-mapping weakness: a caller could pass a synthetic mapping with all approval booleans set to true even while the canonical repository manifest said HOLD. The gate now loads the canonical manifest itself, verifies its exact Git blob SHA-1, and rejects any decision other than `APPROVED`. The public validator no longer accepts caller-supplied rights flags. Synthetic positive-path tests patch only the internal manifest loader; the actual canonical manifest remains HOLD and is tested to fail closed. A future rights approval must change the manifest and its pinned blob SHA in a separately reviewed PR.

No provider account/key, API request, download, raw archive, odds endpoint, Supabase access/write/DDL, protected outcome read, feature calculation, inference, model refit, production `.pkl` change, schedule change or merge occurred.


## Superseding first-party terms, pricing and coverage recheck — 2026-11-26

The official pages were re-read on 2026-11-26. This updates the evidence, not the authorization decision.

### What is now clearer

- The current [Terms of Service](https://bigballsdata.com/legal/terms), effective 2026-08-10, explicitly permit storing API responses in the user's own systems and using stored responses as inputs to internal models, including training, evaluation and backtesting. Derived outputs may be published/sold. Raw-feed resale and republishing raw field values remain prohibited.
- The [global pricing page](https://bigballsdata.com/pricing) states Free is one selected sport at a time, 1,000 requests/day and 100/minute, with scores, standings and statistics. Its Free-plan bullet says current plus most-recent season.
- The [changelog](https://bigballsdata.com/whats-new) dates required sport selection for new Free keys to 2026-10-26 and says existing Free keys had a grace period through 2026-11-24. A football-only scope would be sufficient for this project, but no account or key was created.
- The [Serie A page](https://bigballsdata.com/serie-a-api) displays the 2026-27 season and a standings source timestamp of 2026-11-19 05:12 UTC. It also explicitly says Free covers the current season only.
- The public [licence notices](https://bigballsdata.com/attribution) identify Football-Data.org as a football-data source at a high level. They do not map individual required fields to upstream licensors or prove field-level sublicensing authority.

### Why the source remains HOLD

1. The Serie A capability matrix labels `GET /v1/matches/{id}/statistics` Edge-only, while the same page FAQ, the [OpenAPI](https://bigballsdata.com/openapi.json), and the [soccer endpoint guide](https://bigballsdata.com/soccer-api) describe the route as Free (with expected-goals fields restricted). The direct first-party contradiction is still unresolved; no Free entitlement is assumed.
2. Global pricing says current plus most-recent season, while the dedicated Serie A page says current season only. The 2026-27 current season is visible, but the prior-season scope is not safe to assume.
3. The page's aggregate historical team-stat coverage is not a 2026-27 per-fixture, per-field completeness matrix for corners, yellow cards and red cards. Exact 19-feature parity remains unverified.
4. The provider states that completed match/player rows can be corrected after full time and advises retaining the latest source date. It does not define per-match first-observation or per-field correction timestamps. A local receipt time and SHA can prove project possession before a quote, not upstream first observation.
5. Provider-level storage/internal-model rights are promising, but upstream rights for each required field, account-closure retention, and raw private storage remain unresolved. The attribution notice alone is not a field-level license.

The canonical rights manifest remains `HOLD_NO_INTEGRATION`; `integration_allowed`, `automated_capture_authorized` and `frozen_inference_authorized` remain false. No account/key, provider API request, source download, odds request, Supabase access/write/DDL, feature calculation, inference or protected outcome read occurred. The offline archive gate remains synthetic-only and fails closed against the canonical HOLD manifest.

**Decision:** Big Balls is the strongest documented free candidate reviewed so far for current-season lagged source statistics, but it is not cleared for capture or inference. Obtain written clarification of the Free statistics endpoint, season scope, field-level upstream rights and timestamp/correction semantics; only then may a separate owner-approved private capture be considered.


## Superseding official-plan scope correction — 2026-11-26 12:49 UTC

The first-party pages and changelog were re-read on 2026-11-26. This corrects two details in the earlier 08:55 UTC manifest review; it does **not** change the HOLD decision.

### Free sport scope dates

The current [changelog](https://bigballsdata.com/whats-new) distinguishes two dates:

- **2026-10-26:** new Free API keys require a sport selection at signup.
- **2026-11-24:** the grace period for existing Free keys to retain all-sports access ended.

The Free plan is one selected sport at a time. A single football scope is sufficient for this Serie A-only research candidate. No account or key was created.

### Season-depth wording

The current [global pricing page](https://bigballsdata.com/pricing) is internally inconsistent: its plan introduction says Free covers the current season, while the Free-plan bullet says current plus most-recent season. The [soccer hub](https://bigballsdata.com/soccer-api) and [dedicated Serie A page](https://bigballsdata.com/serie-a-api) both state that Free covers the current season only. The manifest now records all four statements separately and does not assume access to any prior season.

### Match-statistics endpoint entitlement

The endpoint conflict remains:

- Current [OpenAPI](https://bigballsdata.com/openapi.json) declares `x-bbs-min-plan: free` for `GET /v1/matches/{id}/statistics`, with `expected_goals` separately marked Solo+.
- The soccer hub FAQ and Serie A FAQ say the route is Free, and the changelog says this endpoint moved to Free on 2026-11-11.
- The dedicated Serie A capability matrix still places advanced match statistics (including cards) at Edge.

The endpoint remains **unresolved**. No Free entitlement is assumed until the provider reconciles its own plan matrix with its OpenAPI/FAQ statements.

### Rights, freshness and V2 implications

The [Terms of Service](https://bigballsdata.com/legal/terms) still permit private API-response storage and internal model training/evaluation/backtesting while prohibiting raw-feed resale and raw-field republication. The [licence notice](https://bigballsdata.com/attribution) names Football-Data.org for football data but does not map corners, yellow cards and red cards individually to upstream rights or establish sublicensing authority.

The Serie A page still shows a 2026-27 standings source timestamp of 2026-11-19 05:12 UTC. This is not a per-fixture completeness report for the 19 frozen V2 features. The statistics endpoint is stored-only, post-match, hourly persisted, and generally becomes available around 30 minutes after full time; it is a possible lagged input for a later fixture, not a live pre-kickoff statistic for the same fixture.

The canonical manifest was corrected to record the 2026-10-26 sport-selection date and 2026-11-24 existing-key grace end. Its exact Git blob SHA is repinned in the offline archive gate. The manifest remains `HOLD_NO_INTEGRATION`; automated capture, frozen inference and integration remain false.

No provider account/key, API request, source download, odds request, Supabase access/write/DDL, protected outcome read, feature calculation, inference, refit, production `.pkl` change, schedule change or merge occurred.


## 2026-11-26 21:48 UTC — exact OpenAPI endpoint recheck (documentation only)

A fresh review of the official OpenAPI, soccer hub, Serie A authority page and Terms of Service clarifies the candidate's technical coverage but does **not** clear the source.

- OpenAPI describes `GET /v1/matches/{id}/statistics` as **post-match, stored-only** team statistics, persisted hourly after the upstream feed posts following full time. Its `x-bbs-min-plan` is `free`; the response schema includes `corner_kicks`, `yellow_cards` and `red_cards`. Goals remain authoritative from the match linescore. The computed `expected_goals` field is Solo+, but xG is not part of the frozen 19-feature V2 contract.
- The dedicated Serie A page's capability matrix still says the same statistics endpoint starts at **Edge**, while its FAQ says the route is Free. This first-party conflict is unresolved; no authenticated Free response was reviewed.
- Free covers the current season only. The page's aggregate all-season team-stat coverage is not a current-2026/27 per-fixture completeness guarantee. Exact 19-feature parity therefore remains unverified.
- The separate `/v1/stored/matches/{id}/stats` route describes `as_of`/ `fetched_at` using provider ingestion time (`freshness_basis=ingested_at`), not an upstream first-observation or correction timestamp. Do not treat this as proof of when the upstream field first appeared. The main statistics route itself documents no per-field first-seen/correction timestamp.
- Local response receipt UTC plus SHA-256 could prove that the project possessed the exact response before a later quote, but not when the upstream provider first observed or corrected the field. The endpoint is post-match, so it can only be used as a lagged input to a later fixture, never as a same-match pre-kickoff statistic.
- The Terms of Service explicitly permit private API-response storage and internal model training/evaluation/backtesting, while prohibiting raw-feed resale and raw-field republication. Upstream field-level source rights and post-termination retention are still not independently established.

**Decision remains HOLD.** No account/key was created; no provider data endpoint was called; no source data was downloaded; no private archive, feature calculation or inference was performed; no Supabase access/write/DDL or paid call occurred. No V2 model, weights, features, lambda, production artifact or workflow schedule was changed.

Official evidence:
- OpenAPI: https://bigballsdata.com/openapi.json (operation `/v1/matches/{id}/statistics`, `FixtureTeamStatistics`, `/v1/stored/matches/{id}/stats`)
- Soccer hub: https://bigballsdata.com/soccer-api
- Serie A capability matrix and FAQ: https://bigballsdata.com/serie-a-api
- Terms: https://bigballsdata.com/legal/terms
