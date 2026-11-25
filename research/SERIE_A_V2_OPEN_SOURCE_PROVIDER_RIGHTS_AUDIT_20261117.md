# Original frozen Serie A V2 — open-source provider rights and coverage audit (2026-11-17)

## Scope

This is a source-eligibility audit for the unchanged `MARKET_ANCHOR_1X2_V2` candidate only. It does not change the candidate, its 19-feature order, weights, scaler/imputer, lambda values, cohort, evaluation gate, workflows, schedules, or database.

This audit used public provider documentation and repository documentation only. It did not call a provider API, download match datasets, read any match outcomes, access Supabase, or run inference.

## Findings

### 1. Football-Data.co.uk — HOLD for the current daily automated workflow

The provider's current public fair-use guidance says its free CSV/Excel data is intended for private individuals for personal betting and/or academic research. The page says the files are updated at least twice weekly (Sunday and Wednesday); that is the publisher's update cadence, not a maximum download limit. Its data page explicitly excludes commercial/data-training products using automated bots/scrapers/AI and does not affirmatively grant the intended automated AI-model pipeline.

The current V2 source-capture design requests ten historical season CSVs plus the current-season CSV on a daily schedule. The official page does not state a maximum download frequency; the issue is that its private-individual/personal-betting-or-academic-research framing and AI/data-training restriction do not affirmatively authorize this daily automated model-data pipeline.

**Decision:** do not run or re-enable daily automated Football-Data capture under the current free terms. Keep live access held unless the owner obtains a provider-approved scope or the source policy changes. This is a conservative engineering gate, not legal advice.

Official references:
- https://football-data.co.uk/contact.php
- https://football-data.co.uk/data

### 2. OpenLigaDB — data licence is promising, feature coverage is insufficient

OpenLigaDB publishes its retrieved sports data under ODbL 1.0. The provider states that commercial use is allowed with attribution; redistribution of a modified database carries share-alike obligations. API access is governed separately by its API terms.

The API terms recommend caching, a few requests per day outside live matches, and polling `getlastchangedate` before retrieving full data. The provider also states that data is entered by registered users without editorial review and has no guaranteed accuracy, completeness, or timeliness. Its licence page explicitly says there is no public change history or immutable historical snapshot.

The documented API schema exposes fixtures/matches, match results/goals, league tables and related metadata; it does not expose the per-match corners/yellows/reds required to build the complete frozen V2 feature vector.

**Decision:** potentially useful for fixture/result identity or limited goal/points history, but not a substitute for the complete original 19-feature Serie A source. Do not feed it into V2 or claim source-before-quote from its mutable `lastUpdateDateTime` without an independently archived, server-timestamped capture.

Official references:
- https://www.openligadb.de/en/license
- https://www.openligadb.de/en/terms-of-use
- https://api.openligadb.de/index.html

### 3. open-matchday — reject as a complete V2 source under its published terms

The public repository advertises 2026/27 CSVs for 75 competitions and a daily 00:00 UTC rebuild. It reports uneven coverage: results/fixtures across its catalogue, but shots/fouls/cards and corner totals on only about 19% of result rows; its top-10 corner-half splits have broader coverage. It has no odds, xG, lineups, or play-by-play.

More importantly, the repository describes its compilation as informational, non-commercial use only and says upstream provider terms continue to apply. Its own generated league index lists Serie A specifically as `fixturedownload + ESPN + fd.co.uk`; the repository README says match statistics come from football-data.co.uk and may lag by a gameweek or two. Therefore the detailed Serie A stat feed is not a new independent source: it inherits the Football-Data restriction above, while ESPN/fixturedownload rights remain separately applicable. The repository does not grant rights that override those upstream providers.

**Decision:** HOLD. The aggregator is not an independently licensed full-coverage source for all 19 frozen V2 features. Its daily GitHub publication time and public CSV SHA alone do not cure upstream rights, per-match coverage gaps, or provider-level provenance.

References:
- https://github.com/oladeeayo/open-matchday
- https://github.com/oladeeayo/open-matchday/blob/master/DISCLAIMER.md

## Conclusion

No reviewed free source currently satisfies all four requirements at once:

1. complete, reliable Serie A coverage for the original 19 frozen features;
2. explicit rights for the intended recurring automated capture and research/model use;
3. per-source provenance and an independently verifiable capture time before each saved quote;
4. exact immutable bytes/SHA and a no-backfill rule.

Therefore this audit authorizes **no** new provider calls, data download, workflow schedule change, Supabase operation, model inference, feature substitution, or contract change. The existing default-deny live-access hold remains appropriate. A source can be reconsidered only after its provider-specific rights, per-league/season field coverage, automation limits, and timestamp/provenance semantics are documented and reviewed.

## Frozen V2 invariants

- Candidate: `MARKET_ANCHOR_1X2_V2`, unchanged frozen SHA.
- Original 19 features and weights: unchanged.
- `active_lambda=0`: exact de-vigged market remains active.
- `shadow_lambda=1`: research-only.
- Stability/evaluation gates: unchanged; no quality claim.
- No protected target outcomes were read.
- No production `.pkl`, Supabase data/schema, workflow schedules, or other agents were changed.


## Official Football-Data.co.uk page recheck and correction — 2026-11-19

The current official page is `https://www.football-data.co.uk/data.php` (displayed “Updated: 16/11/26”). This is a static documentation read only; no CSV URL was requested or downloaded.

### Correct the earlier frequency wording

The page says the files are “at least updated twice weekly (Sunday nights and Wednesday nights)”. That is the publisher's update cadence. It does **not** state a maximum of two downloads per week. The earlier phrase “at most twice per week” in section 1 of this audit is therefore not supported by the current official page and must not be repeated as a provider rate limit.

The HOLD does not depend on that inferred limit. The same official page states that the free CSV/Excel data is intended for private individuals only and explicitly excludes “commercial or data training products using automated bots/scrapers/AI”. It also says the data are made available for league match prediction only. The existing project pattern—daily automated retrieval of ten historical season CSVs plus current-season CSV, immutable archival, and use in a trained AI candidate—does not have an affirmative permission grant under that wording.

### Correct source identity and implications for the frozen candidate

The historical files used by the original candidate are hosted at `football-data.co.uk` (CSV paths such as `/mmz4281/{season}/I1.csv`). This is **not** the separate `football-data.org` API. The latter's terms/attribution cannot be used as a licence for the former.

The Football-Data.co.uk page says match-statistics compilation uses multiple upstream sources (including Sportinglife, BBC, ESPN, Bundesliga.de, Gazzetta.it and Football.fr) and provides no field-level licence grant for automated AI training or raw archive retention. The candidate's frozen training corpus and all future automated capture based on these CSVs therefore remain a rights HOLD unless the provider gives written permission for this exact personal/project/AI use. This audit does not determine legal status; it records the provider's published restriction and the absence of a documented exception.

### Corrected disposition

- **No** claim that the provider caps downloads at two per week.
- **HOLD** automated daily downloads and AI training/inference use pending explicit written permission or a documented licence change.
- Do not delete, overwrite, or redistribute existing artifacts as part of this research run; no repository or artifact mutation beyond this documentation commit was performed.
- The existing default-deny live-access PR #781 remains the required operational protection. HUMAN-MERGE remains mandatory.
- No CSV request/download, source capture, quote access, API request, Supabase access/write/DDL, feature build, inference, target-outcome read, refit, threshold change, production artifact change or schedule change occurred.

Official source:
- Current Football-Data.co.uk data page, updated 2026-11-16: https://www.football-data.co.uk/data.php


## 2026-11-21 — separate contact-page frequency check (corrected distinction)

A fresh read of the provider's separate fair-data policy page, https://football-data.co.uk/contact.php (page updated **2026-11-20**), confirms the exact wording: free CSV/Excel use is intended for private individuals for personal betting and/or academic research only, via manual download or at most light automated download **twice per week maximum**. The same paragraph separately excludes commercial or AI data-training projects using automated bots/scrapers and says that permission requests for such usage will not receive a response; assume no permission is granted.

This must be distinguished from the data/download page, https://www.football-data.co.uk/data.php, which says files are published/updated at least twice weekly (Sunday and Wednesday). That is the provider's publication cadence, not the user's download allowance. The two statements are consistent and both apply.

The earlier 2026-11-19 correction in this audit correctly rejected an inference from the data-page publication cadence, but it did not account for the separate contact-page maximum. The correct conclusion is therefore stronger: the current daily automated collector exceeds the stated twice-weekly maximum **and** the project's automated AI/data-training purpose is outside the stated free-use scope. The default-deny hold remains required; no download, API request, source capture, quote access, or Supabase operation is authorized by this correction.

This records the provider's published wording as an engineering eligibility gate, not a legal opinion.

## 2026-11-21 — Soccer Data free API candidate (documentation-only audit; HOLD)

A new public candidate was reviewed from the provider's official Terms, pricing and API reference. No account was created, no key requested, no API endpoint called, no match dataset downloaded, and no outcome or Supabase data accessed.

### Published free-plan scope

The official pricing page states that Free provides **50 requests/day**, **10 requests/minute**, current-season data only, all stats endpoints, and no odds. The odds endpoints require Pro or Business. Coverage varies by competition and season and is intended to be checked through the provider's coverage endpoints. The provider's terms say it may change Free-plan features.

### Potential feature coverage — incomplete until verified

The documented played-match stats endpoint `GET /v1/matches/{match_id}/stats` lists `corner_kicks`, `yellow_cards`, `red_cards`, `shots_on_target`, and other team statistics. It returns 409 while a match is live, 404 when detailed statistics are unavailable, and null for unrecorded fields; null must never be treated as zero.

The documented `GET /v1/matches` endpoint exposes fixture identity/status/kickoff and, for finished matches, score fields in the same response. The reference documents no field-projection parameter. Therefore it is **not** an outcome-blind way to enumerate finished 2026/27 matches before the protected outcome gate. The stats endpoint itself does not document an upstream `updated_at` / `last_updated` field; `live.updated_at` applies only to the in-play clock, not the historical statistics payload.

Even after an authorized gate, the Free plan is current-season-only and has no odds. It cannot replace the original candidate's 2016–2026 training archive or the saved pre-match market source. At one stats request per match, 50/day would also require multiple UTC days to backfill 100 match records for a full last-10 view; actual Serie A event coverage and field completeness remain unverified because the coverage endpoint was not called.

### Terms and provenance blockers

The Terms of Service (last updated 2026-10-30) state that data belongs to Soccer Data or providers it licenses from; the user receives a non-exclusive, non-transferable licence. Caching and storage are allowed only while the account/plan remains active; the licence ends when the account closes. The terms allow showing data in one's own websites/apps, including paid ones, but prohibit reselling, sublicensing or redistributing raw data.

The published terms do **not expressly grant AI/ML training, model-development, derived-feature retention, or long-term private research-archive rights**, and they do not identify the upstream provider/field-level rights in the API terms. No assumption of training permission or upstream sublicensing is made.

### Decision

**HOLD — not approved for V2 capture.** It may be reconsidered only after written provider confirmation explicitly covers (a) the original V2's automated feature extraction/model-development use, (b) private raw-response and derived-feature retention for the intended duration, (c) the relevant upstream provider rights for Serie A 2026/27 team stats, and (d) whether a capture-time GitHub artifact SHA is sufficient provenance when the API does not expose a historical-stat update timestamp. Actual coverage must then be checked using the documented coverage endpoint without reading protected scores before the applicable gate.

No source capture, API request, paid request, odds request, Supabase operation, inference, protected-outcome read, refit, threshold tuning, promotion, schedule change, production artifact change, or main update was performed.

Official references:
- Terms of Service, last updated 2026-10-30: https://soccer-data.co/terms
- Free / paid plan limits: https://soccer-data.co/pricing
- List matches response fields and finished-match score exposure: https://soccer-data.co/docs/reference/matches/list
- Played-match team statistics fields and missing-value behavior: https://soccer-data.co/docs/reference/matches/stats
- Competition/season coverage endpoint documentation: https://soccer-data.co/docs/concepts/coverage



## New candidate — BALLDONTLIE Serie A API (2026-11-25)

This is an official-documentation-only plan/rights screen. No account, API key, trial, API request, match-data download, quote, Supabase row, or protected outcome was accessed.

### Free-tier entitlement

The official Serie A API documentation says its data catalogue reaches 2010-current, but the endpoint plan matrix is decisive:

| Endpoint | Free | ALL-STAR | GOAT |
|---|---:|---:|---:|
| Teams / rosters / players / standings | Yes | Yes | Yes |
| Matches | **No** | Yes | Yes |
| Match events / lineups | **No** | Yes | Yes |
| Player match stats | **No** | **No** | Yes |
| Team match stats | **No** | **No** | Yes |
| Betting odds | **No** | **No** | Yes |

- Free: **$0**, 5 requests/minute.
- ALL-STAR: **$9.99/month per league**; provides match identities/events/lineups, but not team match statistics.
- GOAT: **$39.99/month per league**; required for team/player match statistics.
- The 7-day GOAT trial requires a payment method and converts to paid access unless cancelled. It is not an acceptable workaround under the project's no-paid-access rule.

The documented team-match-stat response includes useful V2 ingredients such as shots, shots on target, fouls, yellow cards, red cards and corners (some fields may be null), but this endpoint is GOAT-only. The Free plan cannot even enumerate Serie A match rows through the Matches endpoint. Therefore the provider is **not a free source for the original 19-feature input contract**.

### Data-use terms — positive, but not sufficient

The official Terms of Service are marked **Last Updated: 2026-10-20**. Section 6 expressly permits lawful personal/commercial uses, caching, storage, archiving, analysis, publishing and AI model training/evaluation/backtesting for data lawfully obtained through the user's plan; it states no fixed retention/deletion deadline for lawfully obtained data. A separate licence or attribution is not required for the provider's own rights.

However, Sections 1, 8 and 11 say the service aggregates third-party data, does not guarantee its origin/accuracy/completeness, does not clear every third-party right, and makes the user responsible for obtaining any required third-party rights. The broad AI permission therefore does **not** resolve upstream league/vendor rights or data-quality/field-provenance risk.

The docs also do not establish a cryptographic per-match first-observed/correction timestamp for the historical team-stat payload. Any future authorized use would still require exact raw response bytes, a receipt UTC timestamp, SHA-256, a successful parent-workflow identity, private storage, and strict source-before-quote ordering.

### Decision

**HOLD_NO_FREE_TIER_ACCESS.** BALLDONTLIE has unusually explicit model-training and retention terms for lawfully obtained data, but the required Serie A match/team-stat endpoints are not included in Free. The necessary Team Match Stats endpoint is GOAT-only ($39.99/month per league), which is outside the user's no-paid-API constraint. Do not create an account, trial, key, or request; do not substitute another provider or alter the frozen feature contract.

Official references:
- Serie A API plan matrix and endpoint schema: https://seriea.balldontlie.io/
- Terms of Service (last updated 2026-10-20): https://www.balldontlie.io/terms.html

No paid request, free-tier request, trial, account/key creation, source capture, data download, quote read, Supabase access/write/DDL, protected-outcome read, inference/refit, threshold change, production `.pkl` change, main update, merge, schedule change, or promotion occurred. Original candidate SHA, 19 features/order, 20×2 weights, `active_lambda=0`, `shadow_lambda=1`, stability FAILED and prospective gate 0/30 / CLOSED remain unchanged.

## 2026-11-25 — Footiqo free-download and public-export rights audit (documentation-only; HOLD for automated V2 capture)

Official policy reviewed: https://footiqo.com/dataset-licence/ (last updated 2026-10-08). The policy explicitly applies to premium datasets, free downloadable samples, and CSV/Excel exports from public statistics tables.

### What the policy affirmatively permits
- A user who legitimately obtains data through the official download/export functions may download and retain it locally or in a private database for **personal, non-commercial research and internal analysis**.
- Statistical analysis, historical research, predictive-model development/testing, backtesting and machine-learning experiments are expressly listed as permitted activities.
- Automated processing of files that have already been legitimately downloaded is permitted within that non-commercial scope.

### What it does not permit by default
- Automated scraping/crawling, automated bulk extraction of match records, automated access to CSV/Excel export endpoints, and automated downloading of free or premium files require separate written authorisation.
- The provider says it does not currently offer a public API.
- Commercial use, public data feeds, redistribution or publication of substantial underlying data require separate written permission.
- The policy grants only rights Footiqo is entitled to provide; it does not override upstream/third-party data rights.

The official product page advertises a free Big Five 2025/26 historical sample and says public league tables may be exported manually. It does not establish a free, automated 2026/27 match-statistics feed, per-fixture first-observed/correction timestamps, or complete 19-feature coverage for each Serie A fixture.

Official references:
- https://footiqo.com/dataset-licence/
- https://footiqo.com/premium/premium-football-database/
- https://footiqo.com/product/free-big-five-football-database-2025-26-season/
- https://footiqo.com/database/leagues/italy-serie-a/

**Decision: HOLD_NO_AUTOMATED_CAPTURE.** Footiqo is a possible manual-export source for private, non-commercial exploratory research only, if the file is legitimately obtained and upstream rights are confirmed. It is not approved for this project's recurring automated source capture, commercial/public product use, or current-form inference. No account, email request, API call, automated export, dataset download, source archive, feature calculation, inference, odds read, Supabase access, or protected-outcome use was performed for this audit.

A manually obtained file would still need its exact original bytes, SHA-256, receipt timestamp, source URL/export method, upstream-rights evidence, and archive-before-quote chronology. A local receipt timestamp and hash prove which bytes the project received and when; they do not prove when an upstream statistic was first observed or last corrected.


## 2026-11-25 — API-Football / API-Sports Free-plan screen (documentation-only; HOLD)

Official sources reviewed:
- https://www.api-football.com/
- https://www.api-football.com/news/post/how-to-get-all-data-from-a-league-with-api-football (published 2026-10-26)
- https://www.api-football.com/documentation-v3
- https://www.api-football.com/terms

### Technical fit
- Official pricing advertises a Free plan at $0, 100 requests/day and 10 requests/minute, with the statistics endpoint exposed; free plans are explicitly limited by available seasons.
- Official documentation lists per-fixture statistics including shots on goal, shots off goal, total shots, corner kicks, yellow cards and red cards. The fixtures endpoint also exposes goals/results, so several original V2 feature families are technically represented.
- The 2026-10-26 official league-data guide states that the Free plan covers seasons from Year-4 through Year-2. In 2026 this means 2022, 2023 and 2024; it explicitly says a 2021 season is unavailable on Free. Therefore the Free plan does **not** provide the current 2026/27 season required for lagged current-form features. Exact Serie A per-season coverage remains unverified because no account or API request was used.
- The API changelog documents batching up to 20 fixture IDs in one fixtures request, which could reduce quota use if a permitted season were available. That does not overcome the season restriction or rights issue.

### Rights and provenance
- The Terms say the data is obtained from partners, prohibit resale, provide the feed "as is", and state that no licence is granted for use/publication of data in user applications or products; necessary permissions must be obtained from competent rights holders. Third-party league/federation/event-organizer rights remain the user's responsibility.
- The reviewed Terms do not expressly grant AI/ML training or evaluation rights, nor do they establish a clear private raw-response retention term for this use.
- The docs describe update frequencies but do not provide per-match first-observed or per-field correction timestamps. A future local receipt time + SHA-256 could prove project possession before a later quote, not upstream first publication.

**Decision: HOLD_NO_2026_27_FREE_SEASON_AND_UNCLEAR_DATA_RIGHTS.** The Free plan cannot supply the 2026/27 lagged statistics needed for the original frozen V2 candidate, and the terms do not clearly authorize model research/use or the necessary retention/publication scope. No paid plan is considered.

No account/key was created; no API request, data download, source archive, Supabase access, feature calculation, inference, protected 2026/27 outcome read, refit, threshold change, production `.pkl` change, or schedule change occurred. The original candidate SHA, 19-feature order, 20×2 weights, scaler/imputer, `active_lambda=0`, `shadow_lambda=1`, FAILED historical stability and CLOSED 0/30 prospective outcome gate remain unchanged.
