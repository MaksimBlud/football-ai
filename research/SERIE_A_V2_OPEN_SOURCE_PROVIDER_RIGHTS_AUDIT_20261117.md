# Original frozen Serie A V2 — open-source provider rights and coverage audit (2026-11-17)

## Scope

This is a source-eligibility audit for the unchanged `MARKET_ANCHOR_1X2_V2` candidate only. It does not change the candidate, its 19-feature order, weights, scaler/imputer, lambda values, cohort, evaluation gate, workflows, schedules, or database.

This audit used public provider documentation and repository documentation only. It did not call a provider API, download match datasets, read any match outcomes, access Supabase, or run inference.

## Findings

### 1. Football-Data.co.uk — HOLD for the current daily automated workflow

The provider's current public fair-use guidance says its free CSV/Excel data is intended for private individuals for personal betting and/or academic research, and limits automated downloads to light use (at most twice per week). Its data page also excludes commercial/data-training products using heavy repeated automated downloads.

The current V2 source-capture design requests ten historical season CSVs plus the current-season CSV on a daily schedule. That is not the documented light twice-weekly pattern. The provider's public guidance is not an affirmative grant for this daily, repeated AI-model data pipeline.

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
