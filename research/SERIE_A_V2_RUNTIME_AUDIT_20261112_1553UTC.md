# Original MARKET_ANCHOR_1X2_V2 runtime audit — 2026-11-12 15:53 UTC

Repository: `MaksimBlud/football-ai`  
Main SHA: `40887ebb215730190d7a6c7a1693373ec4afcdfc`  
Frozen candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`

## Actual main-branch runtime

### Current-form source capture

[GitHub Actions run 43232728352](https://github.com/MaksimBlud/football-ai/actions/runs/43232728352) completed successfully on main.

- 19 source-capture tests passed.
- Feature-input metadata gate: 110 completed primary fixture identities.
- 10 frozen historical CSVs plus one gated current-season CSV: 11 source files.
- 3,910 historical match rows.
- Candidate SHA matched the frozen V2 candidate.
- 0 paid provider calls; 0 Supabase writes; target outcomes not scored.
- Public artifact ID: `13951945358`, 439,426 bytes.
- GitHub artifact ZIP SHA-256: `e7bb6e90466c278882225766424b17c229cab46da35dd80a4418e627c8ccb1e8`.

### Current-form forward preview

[GitHub Actions run 43232894044](https://github.com/MaksimBlud/football-ai/actions/runs/43232894044) completed successfully.

- 53 tests passed.
- Exact source artifact and successful parent run were verified.
- Source artifact ID `13951945358`, SHA-256 above.
- Parent source run ID `43232728352`, head SHA main `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Source age at verification: 48 seconds.
- 0 saved quotes, 0 current-form shadow forecasts.
- 0 target outcomes read/scored; 0 paid calls; 0 production/Supabase writes.
- Public forward artifact ID: `13951795906`, ZIP SHA-256 `5b522ac1c95cee939f2120f584c131c8a51ae3cfd7b6ead882ec09e534037d65`.

This is a real source-archive and parent-provenance runtime proof, **not a prospective forecast** and not model-quality evidence. Because the repository is public, these artifacts are public. Provider AI-use/retention rights and private storage remain unresolved.

### Free historical V2 diagnostic

[GitHub Actions run 43243852372](https://github.com/MaksimBlud/football-ai/actions/runs/43243852372) completed successfully on main at 15:04 UTC.

- 53 offline/source diagnostic tests passed.
- Historical source: Football-Data CSV, 3,800 rows.
- 0 quoted fixtures; 0 feature rows; 0 V2 previews.
- `eligible_for_frozen_prospective_cohort=false`; `no_bet=true`.
- 0 paid provider requests; 0 Supabase writes.
- Mode: `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`.
- Public diagnostic artifact ID: `13954739310`, 425,066 bytes.
- ZIP SHA-256: `b81100b497ce689aa339da25853999c2ffe306eb7fc3541fc0fb22f2c4ccbb95`.

The diagnostic still publishes a public artifact on main; the default-deny workflow hold has not yet been integrated into main.

## Fresh Supabase read-only, pre-match-only counts

Project: `besxwboamipygwvrsblz`.

Strict odds condition: `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= now()`.

- 3,915 pre-match snapshot rows across 327 events.
- First snapshot: 2026-08-15 12:23:35 UTC.
- Latest snapshot: 2026-10-13 14:48:53 UTC.
- New rows in the last seven days: 0.
- Exact frozen candidate SHA in `product_prediction_snapshots`, with `generated_at_utc < commence_time_utc`: 0 rows / 0 events.

For the separate feature-input gate, only `match_date, home_team, away_team` identity metadata was counted from `league_finished_results` for `SERIE_A / 2026-2027`: 113 rows / 113 unique fixture identities, 2026-08-22 through 2026-11-08. No score, result, or settlement columns were selected. This metadata/input gate does not open the prospective outcome-evaluation gate.

## Live-access hold and CI

[PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN, non-draft, mergeable, and HUMAN-MERGE only.

- Exact head: `27da7c204d402b76f1f0a52fc1a3bef845fcc5d2`.
- Base main: `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- 43 commits ahead / 0 behind.
- 8/8 exact-head workflows SUCCESS.
- Frozen V2 tests: 103 PASS.
- Recovery offline tests PASS; candidate rebuild, proof, and archive upload SKIPPED under default deny; production pickle hashes unchanged.

The PR gates all five original/current-form source/quote/recovery workflows, their live credential bindings, and every artifact upload. The same current-form and diagnostic workflows still ran on main before the hold is manually merged. No merge or main write was performed.

## Scientific status

- Original candidate, 19-feature contract, weights, scaler, imputer and training fingerprint unchanged.
- `active_lambda=0` remains the market baseline; `shadow_lambda=1` remains research-only.
- Prospective V2 forecasts: 0.
- Protected outcome gate: CLOSED (0/30 eligible completed primary forecasts).
- Brier / LogLoss comparison: not available.
- No claim of V2 superiority or production readiness.

No paid API calls, Supabase writes/DDL, production `.pkl` changes, model refits, promotions, bets, or protected target-outcome reads were performed.


## Additional free-source screen — SportAPI (documentation-only, no calls)

Official sources checked 2026-11-12:
- Terms: https://sportapi.ai/terms (updated 2026-10-22).
- API field reference: https://sportapi.ai/docs.
- Serie A coverage listing: https://sportapi.ai/football-api/.

The terms allow data use in one's own websites, apps, analysis and products, but prohibit raw-data-feed/API redistribution. They do not expressly settle long-term retention, AI-model training, or frozen-model inference. The terms also disclaim accuracy/completeness guarantees and warn that data may be late, incomplete or wrong.

The English pricing/docs pages are inconsistent about the Free quota: the site says 1,000/day and 7,000/month, while the pricing FAQ says 2,000/day and 14,000/month through 2026-11-30, then 1,000/day and 7,000/month from 2026-12-01. Use the lower published ceiling until the provider clarifies.

The documented match-stat endpoint supplies shots, shots on target, shots off target, fouls, passes, pass accuracy, tackles, saves and yellow cards; the events endpoint supplies goals, cards and substitutions. The documented payloads do not supply corners, and the API explicitly says it does not provide possession or xG. The frozen original candidate requires six distinct corners-derived inputs among its 19 features (`diff_corners_for_5/10`, `diff_corners_against_5/10`, and venue-specific corners for/against). Therefore SportAPI cannot currently supply the unchanged original 19-feature contract. Its fixture example has `updated_at`, but the stats response example has no field-level source timestamp; this does not establish when each statistic was first observed.

**Decision: HOLD / not a complete V2 source.** No API key/account was created and no request was made. Do not mix partial SportAPI fields into the frozen candidate or substitute/impute missing corner features from another provider. Reconsider only after explicit provider clarification on retention/AI inference and documented complete corners coverage with a reliable observation clock.


## Further source screens — API-Football and Stats API (no accounts or calls)

### API-Football

Official sources:
- [Terms of service](https://www.api-football.com/terms).
- [Pricing](https://www.api-football.com/pricing).
- [Official API-Football guide to statistics](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginner-s-guide).

The documented `/fixtures/statistics` family includes the exact broad categories the frozen V2 needs, including corners, shots, possession and cards. The provider says not every league tracks every statistic and values may be null. Its Free plan is $0 with 100 requests/day, but free access is limited by available seasons.

The decisive blocker is rights: the official terms say the data is obtained from partners, do not grant a licence for use and publication in applications/websites/products, and require users to obtain any necessary third-party authorizations. Betting-platform use may require additional rights-holder licences. No retention/ML-inference grant for this project's use was found.

**Decision: HOLD pending written permission and per-season coverage proof.** No account/key was created and no API request was made.

### Stats API (stats-api.com; distinct from TheStatsAPI)

Official sources:
- [Pricing](https://stats-api.com/pricing).
- [Coverage/source policy](https://stats-api.com/coverage).
- [Football AI / model-research use case](https://stats-api.com/use-cases/betting-models).
- [FAQ](https://stats-api.com/faq).

The published contract includes corners, shots, possession, cards and xG where available, with per-match coverage flags and source/ingestion timestamps. However, the coverage page explicitly says there is no promised maximum age or freshness guarantee; `source_updated_at` can be null. Coverage varies by league and match, and the current public pages do not establish complete Serie A 2026/27 statistics.

The free allowance is a one-time grant, not a recurring free tier: the home page says 200 requests once, while the pricing page says 500 requests once. Both say no monthly reset or expiry. That conflict must be clarified; even the larger allowance is not a sustainable season-long collection budget for the complete frozen feature history. No sufficiently clear data-retention licence or written AI-training/inference permission was found in the reviewed public terms.

**Decision: HOLD.** Do not spend a one-time quota or create an account until rights, current Serie A coverage, quota amount and freshness semantics are clarified. No account/key or API calls were made.

These sources do not justify substituting, blending, imputing or refitting any of the original 19 frozen V2 features.


### API-Football / API-Sports

Official sources:
- [Terms](https://www.api-football.com/terms).
- [Free and paid plans](https://www.api-football.com/pricing).
- [Official endpoint guide](https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginner-s-guide).

This is a technically stronger candidate than SportAPI for the feature schema: the documented fixture-statistics endpoint includes corners, shots, possession, yellow/red cards, and other match statistics. The provider explicitly says fields can be null when a competition does not track them. The Free plan is $0 with 100 requests/day, but free access is limited by season availability.

The rights blocker is material: the provider says its data comes from partners, it does not grant a licence for use/publication in user applications, websites or products, and third-party league/federation/event-organizer authorizations remain the user's responsibility. Betting-platform use may require additional licences. The reviewed terms do not establish this project's right to retain the raw statistics for an ongoing model pipeline or to perform frozen-model inference.

**Decision: HOLD pending written provider and relevant rights-holder permission plus exact Serie A season/field coverage.** No account/key was created and no API call was made.

### Source-screen conclusion

- SportAPI: broad free access, but no corners; cannot fill the original 19-feature contract.
- API-Football: documented corners and other required statistics, but 100 requests/day, free-season limits, and unresolved use/retention/betting-product rights.
- Stats API: broad normalized statistics and ingestion metadata, but only a one-time 200/500-request free grant, no freshness guarantee, variable match coverage, and unresolved retention/AI rights.
- Football-Data.co.uk: source policy update 2026-11-10 caused the project to withdraw its automated source-capture permission and keep inference blocked; its current main-branch workflow is not yet protected by the pending hold PR.

No candidate is currently cleared for automated collection, long-term archival, or original V2 inference. Do not blend providers or silently fill missing frozen features.


## Latest recheck — 2026-11-12 17:56 UTC

Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; the workflow hold is still absent from all five main V2 source/forward/recovery YAMLs. This is a fresh read of actual completed GitHub Actions jobs and read-only Supabase aggregates, not a new source collection or inference run initiated by this audit.

### New original-V2 forward run

[Original V2 Forward-Only run 43261918181](https://github.com/MaksimBlud/football-ai/actions/runs/43261918181) completed SUCCESS on main at 2026-11-12 16:45 UTC:

- 71 tests PASS.
- Real source archive attestation: artifact `13954739310`, created by successful main diagnostic run `43243852372`; exact ZIP SHA was verified.
- 10 frozen historical CSVs / 3,800 historical matches verified; frozen candidate SHA matched.
- `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`, `v2_diagnostic_previews_captured=0`.
- 0 paid provider calls; 0 Supabase writes; no target outcomes read/scored.
- Small public report artifact `13963024080`, 1,459 bytes, ZIP SHA-256 `f7cd7ec7d7b20138dbfad18d510464026308e1a5d89e530b801a6bcfd01c56b2`.

### New current-form forward run

[Current-Form Forward-Only run 43262798305](https://github.com/MaksimBlud/football-ai/actions/runs/43262798305) completed SUCCESS on main at 2026-11-12 16:49 UTC:

- 53 tests PASS.
- Source artifact `13951945358` SHA-256 `e7bb6e90466c278882225766424b17c229cab46da35dd80a4418e627c8ccb1e8` and successful parent run `43232728352` / main SHA were verified.
- Source age at verification: 10,123 seconds; verification status `VERIFIED`; candidate SHA matched.
- `quotes_seen=0`, `v2_current_form_shadow_captured=0`; target outcomes not read/scored; 0 paid calls; 0 production/Supabase writes.
- It nevertheless uploaded public artifact `13963944149`, 440,582 bytes, ZIP SHA-256 `469e665853c5f4a81774641fbb7f41b3d1961df91a75cb2f9a767e280ac4867c`.

The source capture and forward runs are real provenance/runtime observations only. They do not authorize use of Football-Data bytes under the unresolved source-rights hold and are not model-quality evidence. The diagnostic source archive `13954739310` and current-form source archive `13951945358` remain public Actions artifacts; this audit did not download, unpack, delete or alter them.

### Fresh Supabase pre-match-only aggregate

Read-only SQL selected only pre-match quote timestamps, event identities and counts; no score, result, settlement or target-outcome fields were selected:

- Strict `snapshot_time_utc < commence_time_utc`: **3,915** snapshots across **327** unique events.
- Latest strict pre-match snapshot: **2026-10-13 14:48:53 UTC**.
- Latest stored kickoff among those rows: **2026-10-25 19:45 UTC**; **0** rows are for future kickoffs as of this audit.
- `product_prediction_snapshots` for exact frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, filtered to `generated_at_utc < commence_time_utc`: **0** rows.

### Exact #781 verification

Current PR API HEAD `27da7c204d402b76f1f0a52fc1a3bef845fcc5d2`; base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; compare **43 ahead / 0 behind**. All **8/8** exact-HEAD PR workflow runs completed SUCCESS. Frozen V2 Shadow Tests: **103 passed**, compile PASS, production `*.pkl` diff guard PASS. Recovery: **49 passed**; candidate rebuild, checksum proof and archive upload were SKIPPED; production pickle hash comparison PASS. PR remains OPEN, Ready for review, mergeable and HUMAN-MERGE only. The hold is not active on main until owner merge and fresh-main runtime proof.

### Source candidate note

PR #802 (Footballdata.io free Serie A audit) remains Draft and its exact HEAD has **6/6** PR validation workflows SUCCESS. Its documented decision remains HOLD: free plan does not include Serie A, and required statistics, AI/ML retention rights and source-before-quote provenance are not established. No account, key or provider request was made.

No model weights, 19-feature contract, scaler/imputer, production `.pkl`, Supabase data/schema, schedules or other agents were changed. No paid API call, target-outcome read, promotion or bet occurred.


## Additional free-source screen — Footiqo (2026-11-12, documentation-only)

Official pages reviewed:
- Terms of Use (updated 2026-10-08): https://footiqo.com/terms-of-use/
- Dataset Licence & Data Access Policy (updated 2026-10-08): https://footiqo.com/dataset-licence/
- Free football data overview: https://footiqo.com/football-data/
- Serie A database schema: https://footiqo.com/es/base-de-datos/ligas/italia-serie-a/

### Rights and access

The published licence permits personal, non-commercial research and internal analytics, including local/private storage, statistical analysis, predictive-model development/testing, machine-learning experiments, derived features/probabilities, and retention of privately developed models/results. It expressly excludes redistribution and substantial publication of the underlying dataset.

The same policy prohibits automated scraping/crawling, bulk extraction, automated CSV/Excel export access, and automated downloads of free or premium dataset files unless Footiqo separately authorizes the arrangement in writing. Manual exports through the normal website UI are permitted. Footiqo states that it has no public API. The policy also reserves third-party rights and says sources/methodologies and field coverage vary by competition, season and match; it does not guarantee complete field coverage.

### Frozen 19-feature compatibility

The public Serie A database documents match-level goals, corners and yellow-card fields for the current and previous seasons. The visible corners/cards export schema does not expose red-card fields. The frozen original candidate requires red-card rolling features (diff_red_5 and diff_red_10) as part of its unchanged 19-feature contract. No zero-fill, substitution, feature drop or refit is permitted.

The reviewed public pages expose match date/kickoff and statistical fields, but no field-level source-observation timestamp or revision history. A local manual-export timestamp and SHA would prove which bytes were retained, not when each upstream statistic first became observable. Source-before-quote therefore remains unproven without a provider-side observation clock or a genuinely pre-quote archived export.

The public policy also prohibits placing substantial underlying data in public repositories/file-sharing/public databases. Public GitHub Actions artifacts are therefore not an admissible storage target for Footiqo data. Its standard permission is personal/non-commercial/private; public or commercial product use and automated capture require separate written permission.

### Decision

**HOLD — not an admissible automated source for the unchanged original V2 contract.**

Potentially useful only as a manually exported, private, non-commercial research source after:
1. red-card coverage is documented for the exact required seasons/matches;
2. third-party/upstream rights are clarified for those fields;
3. a defensible source-observation timestamp is available before each quote;
4. any automated access or public-product use is explicitly authorized in writing.

No account/key was created; no file was downloaded or exported; no scraping/API request occurred; no Footiqo data was added to the candidate or any artifact.

Process incident: the public Serie A page is a mixed match-results/statistics view, and the page retrieval returned current-season 2026/27 match rows containing result/stat fields. This was an unintended retrieval exposure and should not have been opened under the strict no-read boundary. No row-level values were deliberately selected, copied into an analysis dataset, aggregated, scored, or used; no model evaluation was performed. Treat all returned row content as quarantined and excluded from feature building, model evaluation, and the preregistered 30-forecast outcome gate. No Supabase target-outcome rows were queried. Do not reopen this page.


## Fresh exact-main runtime and pre-match-only database recheck — 2026-11-12 21:55 UTC

### Main and live-workflow status

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- The four original/current-form source/forward/diagnostic workflow files still have their scheduled triggers and artifact-upload steps; none has `MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED`. PR #781 is not merged, so its default-deny hold is not active on main.
- No workflow settings, schedules, credentials, branch settings, or other agents were changed in this audit.

### Actual GitHub Actions runs on unchanged main

- Current-Form Source Capture [#43232728352](https://github.com/MaksimBlud/football-ai/actions/runs/43232728352), SUCCESS at 2026-11-12 14:01:06 UTC: the metadata-only feature-input gate counted 110 primary-event identities; 110 prior-day current-season rows plus 10 historical CSVs were captured (11 files total). Source ZIP SHA-256 `e7bb6e90466c278882225766424b17c229cab46da35dd80a4418e627c8ccb1e8`, artifact ID `13951945358`. The run reports 0 paid calls, 0 Supabase writes, and no target-outcome scoring.
- Current-Form Forward-Only Preview [#43262798305](https://github.com/MaksimBlud/football-ai/actions/runs/43262798305), SUCCESS at 2026-11-12 16:49:56 UTC: exact source SHA and successful parent run verified; `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes not read/scored, 0 paid calls, 0 Supabase writes. Forward ZIP SHA-256 `469e665853c5f4a81774641fbb7f41b3d1961df91a75cb2f9a767e280ac4867c`.
- Original Forward-Only Preview [#43261918181](https://github.com/MaksimBlud/football-ai/actions/runs/43261918181), SUCCESS at 2026-11-12 16:45:02 UTC: source artifact ID `13954739310`, SHA-256 `f7cd7ec7d7b20138dbfad18d510464026308e1a5d89e530b801a6bcfd01c56b2`; 10 historical source CSVs / 3,800 verified historical rows; `quotes_seen=0`, `v2_diagnostic_previews_captured=0`, 0 paid calls, 0 Supabase writes.
- Free Real-Quote Diagnostic [#43243852372](https://github.com/MaksimBlud/football-ai/actions/runs/43243852372), SUCCESS: original 19-feature diagnostic reported zero fixture rows and zero rows with all 19 features observed; no forecasts or quality metrics.
- These are real source-integrity/runtime checks and public artifact creation on main, not prospective V2 predictions or model-quality evidence. Logs only were read; no Actions artifacts were downloaded or opened.

### Supabase — aggregate pre-match rows only

Read-only aggregate query used only `odds_snapshots` rows satisfying `snapshot_time_utc < commence_time_utc`, plus exact-candidate pre-match prediction metadata.

| Measure | Result |
|---|---:|
| All odds snapshots | 3,966 |
| Strict pre-match snapshots | 3,915 |
| Unique events with strict pre-match snapshots | 327 |
| Strict pre-match snapshots in last 7 days | 0 |
| Upcoming events with a strict pre-match quote | 0 |
| Latest strict pre-match snapshot | 2026-10-13 14:48:53 UTC |
| Exact frozen-candidate pre-match predictions | 0 |

The exact candidate filter was SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6` and `generated_at_utc < commence_time_utc`. No score, result, settlement, or target-outcome columns/rows were queried. No Supabase write or DDL occurred.

### Current direct-main hold PR

- [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) current GitHub API HEAD: `27da7c204d402b76f1f0a52fc1a3bef845fcc5d2`; base main: `40887ebb215730190d7a6c7a1693373ec4afcdfc`; **43 ahead / 0 behind**, OPEN, Ready for review, mergeable.
- Exact HEAD Actions: **8/8 SUCCESS**. Frozen V2 suite [#43242070289](https://github.com/MaksimBlud/football-ai/actions/runs/43242070289): **103 passed** and production `.pkl` hash guard PASS. Recovery [#43242070506](https://github.com/MaksimBlud/football-ai/actions/runs/43242070506): offline tests and production hash guard PASS; candidate rebuild/proof/upload SKIPPED.
- The PR description has been refreshed with the current exact SHA, run links, and latest main-runtime evidence. No code, model, source archive, production artifact, or database file changed.
- HUMAN-MERGE remains mandatory. After owner merge, read fresh main and prove every live source/quote/inference/recovery step and public upload is skipped before considering any further work.

### Frozen original candidate

Candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features, 3,799 training rows, unchanged 20x2 weight matrix (19 features plus intercept), `active_lambda=0`, `shadow_lambda=1`, stability gate FAILED. No refit, weight/feature/scaler/imputer change, production `.pkl` change, promotion, bet, or outcome evaluation occurred.
