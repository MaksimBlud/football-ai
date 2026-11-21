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
