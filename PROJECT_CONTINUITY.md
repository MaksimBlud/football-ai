## 2026-11-05 12:20 UTC — gate-open market-only outcome binding fix

**Main remains** `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This is a documentation-only follow-up in PR #697; no merge or main write.

### Gate-open evaluator defect found and fixed

Reviewing the actual PR #701 live bridge exposed a dormant defect that closed-gate tests could not reach: `run_live_evaluation()` invoked `_read_exact_completed_outcomes(client, identities)`, while the exact reader requires the frozen forecast-to-kickoff map as a third argument. Once the 30-event gate opened, this would have raised a `TypeError` instead of checking post-kickoff result persistence.

Fixed in PR #701:
- Exact new HEAD: `1a01f9f82dcd2c6be2061aea1eb5164d0af47f73`.
- The bridge now builds `selected_rows, kickoff_by_identity` using the existing `_forecast_kickoff_lookup` helper and passes that same mapping into `_read_exact_completed_outcomes`.
- Added a dynamic synthetic 30-row bridge regression that invokes the lazy callback and verifies exact identity-to-kickoff binding.
- Exact-head CI: **6/6 SUCCESS**. Targeted Research PR Validation [run 42026189766](https://github.com/MaksimBlud/football-ai/actions/runs/42026189766) includes **20 passed** in the prospective-evaluation workflow tests. The production `.pkl` diff guard passed.
- Two intermediate CI failures were test-fixture-only (missing `source_artifact_id`, then an invalid synthetic hour 24); both fixtures were corrected. No production guard was weakened.

### Correct evaluation path without reviving the legacy model

The live orchestration in #701 uses `evaluate_live_market_only_prospective_cohort`, not the full three-way incumbent evaluator. It first reads the identity-only completed-fixture gate (`match_date,home_team,away_team`), then runs source/archive SHA preflight on the same immutable identity snapshot. The lazy result callback is invoked only if at least **30 unique eligible completed prospective Serie A forecasts** match that gate. The post-gate reader selects exactly `match_date,home_team,away_team,result,persisted_at_utc` for those identities and requires `persisted_at_utc > kickoff_utc`.

The market-only path compares only the exact lambda-zero de-vigged market against the original V2 lambda-one shadow and reports Brier/LogLoss plus descriptive paired bootstrap uncertainty. It always keeps `review_signal=false`; it cannot promote, bet, tune, or alter the frozen model. The full three-way review remains blocked because no non-legacy frozen incumbent is pinned. Do not revive or load the old XGBoost model to fill that gap.

No eligible quote-backed forecasts exist in the latest Nov 4 main forward artifacts (`quotes_seen=0`, `v2_current_form_shadow_captured=0`), so the target-outcome gate remains closed. The 100-fixture feature-input metadata gate in the Nov 4 source archive is a separate lagged-input gate and does not count toward the 30 prospective forecast outcome gate.

#701 remains stacked on the older #699 base SHA `b1ca50494d529f3fd84dcb2e1435f078c4876099`; after #699 is manually integrated, rebase #701 onto the resulting main and rerun exact-head CI. No PR was merged here.

---

## 2026-11-05 11:57 UTC — Run 11: exact source-before-quote recheck and rights-gated CLI

**Main remains** `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Documentation-only update to PR #697; no merge or main change.

### Read-only pre-match quote/source pairing

A fresh SQL recheck selected only pre-match quote metadata and source-observation metadata; no score, result, settlement, or protected target-outcome columns were read.

- `public.odds_snapshots`: **3,966** rows total; **3,915** satisfy `snapshot_time_utc < commence_time_utc`; **0** strict pre-match quotes in the last seven days; **0** future fixtures with a saved strict pre-match quote.
- Latest saved strict pre-match quote remains Serie A **2026-10-13 14:48:53 UTC**; latest EPL quote **2026-10-09 15:25:57 UTC**.
- Structural source tables contain **2,387** rows in `league_structural_v2_observations` and **749** in `la_liga_structural_v2_observations`. Latest source snapshot is **2026-10-13 14:48:53 UTC**; latest persisted source observation is **2026-10-22 12:28:06 UTC**; none persisted in the last seven days.
- Strict source-before-quote join unions both structural tables and requires exact `league + event_id + commence_time_utc`, `source.snapshot_time_utc < quote.snapshot_time_utc`, and `source.persisted_at_utc <= quote.snapshot_time_utc`. Result: **2,935 / 3,915** quote rows have a qualifying earlier persisted observation; **980** do not. No rows had an earlier source-observation timestamp but source persistence after the quote snapshot.
- Per league qualifying rows / strict pre-match quotes: Bundesliga **359/394**; EPL **478/1,135**; Eredivisie **370/410**; La Liga **682/798**; Ligue 1 **352/387**; Primeira Liga **0/9**; RPL **138/153**; Serie A **556/620**; Turkey Super Lig **0/9**.

**Correction to the previous 11:14 entry:** its **2,268** generic-table-only count is not reproducible under the explicit quote-snapshot persistence anchor. Re-running that generic table alone yields **2,266**; the complete union including the dedicated La Liga observation table yields **2,935**. These are DB pairing diagnostics only, not proof of raw CSV provenance, GitHub parent-run identity, or archive SHA. Those independent attestations remain mandatory.

### Latest real main workflow evidence

No scheduled run for any of the four V2 source/forward workflows was found for **2026-11-05**. The latest verified main runs remain on November 4:

- Current-Form Source Capture [run 41836971469](https://github.com/MaksimBlud/football-ai/actions/runs/41836971469), artifact **13327281383**, ZIP SHA-256 `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`. It captured 10 old-season CSVs plus the 2026/27 current-season CSV; the feature-input metadata gate counted 100 completed prior-day fixtures. This is the feature-input gate, **not** the separate 30-prospective-forecast outcome gate.
- Current-Form Forward [run 41866116572](https://github.com/MaksimBlud/football-ai/actions/runs/41866116572), artifact **13342406844**, ZIP SHA-256 `f0893c5fdcbd2515c10915830802f77782441e5638bda62fa7d2dff882d6fc20`. It verified the source artifact and parent run, but `quotes_seen=0` and `v2_current_form_shadow_captured=0`; target outcomes were not read.
- Original Forward [run 41864632742](https://github.com/MaksimBlud/football-ai/actions/runs/41864632742), artifact **13341622767**, ZIP SHA-256 `738553a86e392361ce1b27ab0226a2b0fa2f540a6ac9579b5da2d8d81858a215`. Real historical source attestation verified 10 pre-prospective CSVs / 3,800 historical results, but `quotes_seen=0` and `v2_diagnostic_previews_captured=0`.
- Free Diagnostic [run 41847314320](https://github.com/MaksimBlud/football-ai/actions/runs/41847314320), artifact **13332260799**, ZIP SHA-256 `72a32dc61d6e230be46bc5fe69a52e97142a79816af33c66f58066e0ceb6e8d8`; 3,800 history rows, `diagnostic_scored=0`.

The Nov 4 current-form source artifact predates #699's new exact fixture-identity/SHA gate attestation; it is not admissible to the new #701 evaluator. No new quote-backed V2 forecast exists.

### New stacked PR #715 — source-rights gate on the standalone frozen-shadow CLI

[PR #715](https://github.com/MaksimBlud/football-ai/pull/715) is a draft stacked on #699 at base `a6725ca49e90d551baa7e9f647151f7e524e42c7`, current head `0039b51e1d6de2a70ef17065d831052fec837c05`.

- The CLI now calls `require_personal_research_inference_scope()` before importing the database client, reading saved quotes, reading external feature JSON, or running inference. A denied scope returns `RESEARCH_SCOPE_BLOCKED` with zero DB reads/writes and no inference.
- The source-rights manifest records the official Football-Data page update date **2026-11-04** and review time **2026-11-05T10:54:00Z**. It permits only the project's narrow personal/academic frozen-weight research interpretation; it is **not** a provider-issued AI-inference licence. AI training, commercial use, and public-product use remain false/blocked.
- The preceding commit `acb0d600784f562d0924f29e3cd7cd3403dc61d1` ran [shadow tests 42020206874](https://github.com/MaksimBlud/football-ai/actions/runs/42020206874): **327 passed**, production `.pkl` diff guard passed. The current head's CLI source blob is identical to that tested commit (`3bcbc69fe87a21eba1eccc6cef824ba284e2b6c9)); current head only reverts the temporary workflow base-filter edit. Nevertheless, the exact current head has **no check-runs**. Do not describe #715 as exact-head CI complete; rebase onto main after #699 and rerun full CI.

### PR overlap and integration order

The exact changed-file lists confirm workflow overlap: #699 overlaps #705 in three source/forward workflow files and one source test; #699 overlaps #714 in the free-diagnostic workflow; #705 and #714 overlap in the diagnostic workflow and budget tests; #704 overlaps #699 in five V2 workflows. #714 is stacked on #705. Preserve the manual integration sequence: #706 first for the stronger `.pkl` diff guard; integrate/retest #704 and #705 without losing either dependency-lock or shared-budget changes; then #714; rebase #699 onto the resulting main and rerun all exact-head checks; finally rebase #701 and #715. #703 and #712 also overlap source scripts/workflows and require rebasing against the integrated source pipeline.

No merge, main write, Supabase write/DDL, paid provider request, production `.pkl` change, target-outcome read, model refit, or schedule change occurred in this audit.

---

## 2026-11-05 11:14 UTC — Run 11 follow-up: policy-date attestation, exact CI, and corrected provenance count

**Main remains** `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This is a documentation-only update to PR #697; no main update or merge.

### Correction to the preceding source-before-quote summary

The per-league counts already recorded in the 09:56 UTC entry sum to **2,268**, not 2,768. The latter figure in the prior chat summary was an arithmetic error. Recomputed from the same read-only SQL result:

- 3,915 strict pre-kickoff quote rows.
- 2,268 have a same-league/event structural observation with both `source.snapshot_time_utc < quote.snapshot_time_utc` and `source.persisted_at_utc <= quote.created_at`.
- 0 have an observation timestamp before quote but persistence after quote under that same join.
- 1,647 have no qualifying match under those conditions.

This join is a database diagnostic only; it does not replace authenticated raw-source CSV SHA, GitHub parent-run identity, or source-artifact-before-quote proof.

### Official Football-Data policy refresh and #699 change

The official fair-use page currently displays **Updated: 04/11/26** and limits free CSV/Excel use to private personal betting and/or academic research, with no more than two light automated download sessions per week. It excludes commercial and AI data-training projects. The page does not expressly grant frozen-weight AI inference; the project's narrow personal/academic inference treatment remains an operational interpretation, not a provider-issued AI-inference licence. AI training, commercial use, and public-product publication remain false/blocked.

- Official page: https://football-data.co.uk/contact.php
- Policy page update date: `2026-11-04`.
- Manifest review timestamp: `2026-11-05T10:54:00Z`.
- No source download was initiated.

Updated the existing #699 branch (no new PR, no main change):
- Exact HEAD: `a6725ca49e90d551baa7e9f647151f7e524e42c7`.
- Manifest now records the official page-update date and current review timestamp.
- Rights helper rejects a missing, malformed, noncanonical, or later-than-review page-update date.
- Both original and current-form forward readers pin the new rights-helper and rights-manifest blob SHAs.
- Regression test suite includes future and noncanonical policy-date failures.
- Exact-head CI: **7/7 SUCCESS**; Original V2 Shadow Tests **325 passed**; `git diff --exit-code -- '*.pkl'` succeeded. Targeted Research PR Validation also completed successfully.
- Intermediate HEAD `d8bd85dd...` had one test-only assertion mismatch; CI exposed it (324 passed, 1 failed). The test was corrected to use a valid ISO week-date spelling that exercises the canonical-format guard; final HEAD `a6725ca...` passed all seven checks.

#699 is still 151 commits ahead of main with 27 changed files. It must be reviewed as a complete diff and rebased after #705/#714; do not merge its current old-main base directly.

### Fresh main / live runtime and pre-match database state

A paginated Actions query for main SHA `40887...` and runs created on 2026-11-05 returned 133 runs across two pages. None was one of the four V2 workflows (Current-Form Source Capture, Free Real-Quote Diagnostic, Original Forward-Only, Current-Form Forward-Only). This is absence of run records for that date, not proof that workflows are disabled; cron declarations were not changed and no manual dispatch was attempted.

Latest actual Nov 4 main runs remain:
- Current-Form Source Capture #41836971469, artifact #13327281383, ZIP SHA-256 `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`: 3,900 historical rows plus 100 current-season rows, 11 CSV members. This V1-era main artifact predates #699's identity-SHA attestation and is not admissible to the new evaluator.
- Current-Form Forward #41837103174 verified that artifact/parent, but `quotes_seen=0` and `v2_current_form_shadow_captured=0`; no outcomes read.
- Free Diagnostic #41847314320 reported 3,800 historical rows and `diagnostic_scored=0`.
- Original Forward #41864632742 verified historical artifact #13332260799 (3,800 historical results), but `quotes_seen=0` and `v2_diagnostic_previews_captured=0`.

Fresh read-only Supabase pre-match aggregates: 3,966 odds rows, 3,915 strictly before kickoff, zero strict pre-kickoff quotes in the preceding seven days, and zero future events with saved strict pre-kickoff quotes. Latest strict Serie A quote remains 2026-10-13 14:48:53 UTC; latest EPL quote 2026-10-09 15:25:57 UTC. No result/score/settlement fields were selected.

### Current exact-head PR and HUMAN-MERGE state

- #706 `caab7c07ad720866616ce9fa62664b0d398e5fe0`: 6/6 SUCCESS; fail-closed production-`.pkl` diff guard.
- #704 `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: 16/16 SUCCESS; pinned V2 research CI dependencies.
- #705 `8cf5ded4dfc18820e10f59f8ccd2a462479ccfe5`: 8/8 SUCCESS; shared two-session-per-rolling-seven-day source budget. Its inherited `.pkl` diff guard is not sufficient alone, so #706 must precede it.
- #714 `ea4880dca6b7d41434160a298798b0312744ae56`: offline push validation and budget tests SUCCESS (76 + 23 tests); live download job intentionally SKIPPED. It remains stacked on #705 and needs rebase/full CI after #705.
- #699 `a6725ca49e90d551baa7e9f647151f7e524e42c7`: 7/7 SUCCESS, but requires rebase after #705/#714.
- #701 remains dependent on #699; its existing 6/6 result is on the previous base and must be repeated after rebase.
- #712's existing offline cache tests do not replace the required fresh post-#699 identity-attested source artifact; #711 is an overlapping draft alternative. Choose only one cache consumer after dependencies are integrated.

Authoritative order remains HUMAN-MERGE #706 → #704 → rebase/revalidate #705 → HUMAN-MERGE #705 → rebase/revalidate #714 → HUMAN-MERGE #714 → rebase/revalidate #699 → then #701 and one selected cache consumer. No merge is authorized by this note.

### Frozen scientific state

Original candidate SHA `a9d5abc2...`, 19 features, 20 x 2 weight matrix, `active_lambda=0`, `shadow_residual_lambda=1`; original weights and contract unchanged. The stability gate remains FAILED. Eligible prospective completed primary forecasts remain **0/30**; Brier and LogLoss are unavailable; V2 superiority over market is not established.

No paid odds request, Football-Data download, Supabase write/DDL, target-outcome read, production `.pkl` change, refit, weight/feature/lambda/threshold change, promotion, bet, main update, merge, schedule change, or other-agent setting change occurred.

---

## 2026-11-05 09:56 UTC — Run 11: exact scheduled-run and database source-before-quote audit

**Main remains** `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This is a documentation-only update to PR #697; no main update or merge.

### Scheduled original-V2 workflows: no Nov 5 schedule records

Re-read the four main workflow files and their cron declarations:
- Current-Form Source Capture: `.github/workflows/serie-a-v2-current-form-source-capture.yml`, 05:50 UTC.
- Free Real-Quote Diagnostic: `.github/workflows/serie-a-v2-free-real-quote-diagnostic.yml`, 06:13 UTC.
- Original Forward-Only Preview: `.github/workflows/serie-a-v2-forward-preview.yml`, 08:08 UTC.
- Current-Form Forward-Only Preview: `.github/workflows/serie-a-v2-current-form-forward-preview.yml`, 08:18 UTC.

Queried the GitHub Actions API for `event=schedule` and the full UTC date 2026-11-05 at 09:56 UTC: 36 scheduled runs were returned. The only run matching the V2/source-capture/forward-preview name filter was the unrelated `Multi-Market V2 Cycle` (#41986565483). No schedule-event record was present for any of the four workflows above. This is an observed absence of run records, **not** proof that workflows are disabled. No manual dispatch was attempted; the current continuity policy explicitly says not to dispatch source workflows while the shared public-source budget guard is not on main.

### Read-only Supabase pre-match source-before-quote screen

Queried only `public.odds_snapshots` and `public.league_structural_v2_observations`; no results, scores, settlement or target-outcome columns/tables were read. The query admitted only quotes with `snapshot_time_utc < commence_time_utc`, then looked for a same-league/same-event structural observation satisfying both `source.snapshot_time_utc < quote.snapshot_time_utc` and `source.persisted_at_utc <= quote.created_at`.

- 3,915 strictly pre-kickoff quote rows across nine leagues.
- Zero quote rows in the preceding seven days; zero rows for future kickoffs.
- Latest strict pre-kickoff quote: Serie A, 2026-10-13 14:48:53 UTC.
- Structural-observation relation before quote (row counts): Bundesliga 359/394; EPL 478/1,135; Eredivisie 371/410; La Liga 13/798; Ligue 1 352/387; Primeira Liga 0/9; RPL 138/153; Serie A 557/620; Turkey Super Lig 0/9.

**Interpretation limit:** this is a database-level timestamp/identity join against `league_structural_v2_observations`; it is not proof that the original Football-Data CSV archive preceded each quote, and it does not attest raw-source SHA. The authoritative original-V2 source proof remains the GitHub source-artifact/parent-run/SHA verifier. These counts must not be promoted into model eligibility or used to tune the frozen contract.

### Exact PR/CI state at this audit

- #705 HEAD `8cf5ded4dfc18820e10f59f8ccd2a462479ccfe5`: 8/8 SUCCESS.
- #714 HEAD `ea4880dca6b7d41434160a298798b0312744ae56`: 3 checks total; `budget-tests` and `validate-free-diagnostic` SUCCESS, live `free-diagnostic` intentionally SKIPPED. This is not a full six-workflow CI result; it remains stacked on #705.
- #699 HEAD `b1ca50494d529f3fd84dcb2e1435f078c4876099`: 7/7 SUCCESS.
- #701 HEAD `8c059bababce9c1b735f14ec555d44d19b3392c4`: 6/6 SUCCESS.
- #697 prior HEAD `cf85105b2316aa9098e7f05a243b24029af9be25`: 7/7 SUCCESS before this documentation commit.
- #703 HEAD `f12abfd3a8fc37fb3aff6d394ec3966bc1311b51`: 7/7 SUCCESS on Nov 1; not a new run in this audit.
- #711 remains draft with no check-runs on its current head; #712 has only its targeted offline source-reuse check, not full required CI.

No source download, manual workflow dispatch, paid request, Supabase write/DDL, production `.pkl` change, candidate/feature/weight/lambda/threshold change, model training/refit, protected outcome read, promotion, bet, merge, schedule change, or other-agent setting change was performed.

---

## 2026-11-05 09:07 UTC — Run 11: evaluator persistence-clock regression and exact-head CI

**Main remains** `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This update is documentation-only on PR #697; no main update or merge.

### Original V2 evaluator follow-up

PR #701 remains stacked on #699 and now has exact HEAD `8c059bababce9c1b735f14ec555d44d19b3392c4`, with **6/6 SUCCESS**:
- Research PR Validation #41999436433 — 79 evaluator tests and 11 live-runner tests passed.
- Serie A, Bundesliga, Ligue 1, Product, and Eredivisie checks all SUCCESS.
- The follow-up corrected the evaluator documentation to state that the post-gate outcome query selects exactly `match_date,home_team,away_team,result,persisted_at_utc`.
- Added synthetic regressions for result persistence one hour before kickoff, exactly at kickoff, and for an offsetless persistence timestamp. All fail closed; no outcome query occurs below the existing 30-eligible-completed-primary-forecast gate.
- The first draft test asserted the wrong error wording; exact-head CI caught it. The expectation was corrected to the existing fail-closed runtime message, then all 6 checks passed.
- The change modifies only the prospective evaluator documentation and runner tests. It does not change the evaluator implementation, frozen candidate, 19 features, weights, lambdas, selection policy, or 30-event gate.

The market-only evaluator remains distinct from the three-way review path: it compares only de-vigged market (`active_lambda=0`) with the original V2 research shadow (`shadow_lambda=1`), keeps `review_signal=false`, and cannot promote or publish. The separately pinned incumbent remains unavailable; no legacy XGBoost model is used.

### Current pre-match data and workflow state

The Nov 5 schedule-event audit still shows no run for the four main V2 scheduled workflows (Source Capture 05:50 UTC, Free Diagnostic 06:13 UTC, Original Forward 08:08 UTC, Current-Form Forward 08:18 UTC). Latest verifiable main V2 runs remain Nov 4. This is an observed absence of run records, not proof that the workflows are disabled.

Read-only Supabase aggregate queries on pre-match tables only:
- `odds_snapshots`: 3,915 strictly pre-kickoff rows across nine leagues; zero in the last seven days; zero future events with a saved strict pre-kickoff quote.
- `league_structural_v2_observations`: 2,387 strictly pre-kickoff observations across seven leagues; zero in the last seven days; zero future events with a saved pre-kickoff observation.
- Latest strict Serie A quote remains 2026-10-13 14:48:53 UTC.

No results, scores, settlements, or protected target outcomes were queried. The prospective cohort remains **0/30**; Brier Score and LogLoss are unavailable.

### HUMAN-MERGE integration order

- #705 `8cf5ded4...`: 8/8 SUCCESS; shared two-session rolling-week download budget and source-capture push isolation.
- #714 `ea4880dc...`: offline Free Diagnostic push validation 2/2 SUCCESS (the live download job was intentionally skipped); still stacked on #705 and needs rebase/full exact-head validation after #705.
- #699 `b1ca5049...`: 7/7 SUCCESS on its current head, but must be rebased after #705/#714 to preserve shared-budget and offline-push changes.
- #701 `8c059bababce9c1b735f14ec555d44d19b3392c4`: 6/6 SUCCESS, but remains stacked on #699 and must be retargeted/revalidated after #699 is integrated.
- #709's source-capture offline-push delta is already present in #705; do not merge it separately without a new unique-delta review.
- #704/#706/#712 remain dependent on the final source/evaluator integration and require exact-head rebase CI.

No PR was merged, no main change, no schedule or other-agent setting change, no source download, no paid request, no Supabase write/DDL, no production `.pkl` change, no model training/refit, no weight/feature/lambda/threshold change, no promotion, and no bet occurred.
## 2026-11-05 08:40 UTC — Run 11: fresh schedule, pre-match data, evaluator provenance, and stacked-PR audit

**Main remains** `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This entry updates documentation PR #697 only; no main update or merge.

### Main V2 workflows and actual Nov 4 runs

Re-read the four main workflow files and their cron declarations:
- Current-Form Source Capture: `.github/workflows/serie-a-v2-current-form-source-capture.yml`, 05:50 UTC.
- Free Real-Quote Diagnostic: `.github/workflows/serie-a-v2-free-real-quote-diagnostic.yml`, 06:13 UTC.
- Original Forward-Only Preview: `.github/workflows/serie-a-v2-forward-preview.yml`, 08:08 UTC.
- Current-Form Forward-Only Preview: `.github/workflows/serie-a-v2-current-form-forward-preview.yml`, 08:18 UTC.

The GitHub Actions API schedule-event listing was queried directly. As of 08:18 UTC on Nov 5, no Nov 5 scheduled run for these four workflows was present; their latest verifiable runs remain Nov 4. This is an observed absence at that timestamp, not evidence that a workflow is disabled.

Actual Nov 4 run logs:
- Source Capture [#41836971469](https://github.com/MaksimBlud/football-ai/actions/runs/41836971469), artifact **13327281383**, ZIP SHA-256 `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`. Log: 19 tests passed; ten historical CSVs (3,800 rows) plus 100 2026/27 prior-day rows; 3,900 combined history rows; metadata-only feature-input gate passed; no paid calls, Supabase writes, or target-outcome scoring.
- Free Diagnostic [#41847314320](https://github.com/MaksimBlud/football-ai/actions/runs/41847314320), artifact **13332260799**, ZIP SHA-256 `72a32dc61d6e230be46bc5fe69a52e97142a79816af33c66f58066e0ceb6e8d8`. Log: 53 tests passed, 10 public CSV requests, 3,800 historical rows, zero quoted fixtures and zero scored diagnostics; mode `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`; no paid calls or Supabase writes.
- Original Forward [#41864632742](https://github.com/MaksimBlud/football-ai/actions/runs/41864632742), artifact **13341622767**, ZIP SHA-256 `738553a86e392361ce1b27ab0226a2b0fa2f540a6ac9579b5da2d8d81858a215`. Log: 71 tests passed, historical source verified, `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`, `v2_diagnostic_previews_captured=0`.
- Current-Form Forward [#41866116572](https://github.com/MaksimBlud/football-ai/actions/runs/41866116572), artifact **13342406844**, ZIP SHA-256 `f0893c5fdcbd2515c10915830802f77782441e5638bda62fa7d2dff882d6fc20`. Log: 53 tests passed; verified source artifact #13327281383 and successful main parent; `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`.

### Read-only Supabase pre-match audit

Only `public.odds_snapshots` pre-match quote timestamps and kickoff timestamps were queried. No finished-results, score, settlement, or target-outcome table was queried.

- 3,966 rows total; 3,915 satisfy `snapshot_time_utc < commence_time_utc`.
- Zero strictly pre-match rows in the last seven days.
- Zero future events with a strictly pre-match saved quote.
- Latest strict pre-match quote by league: BUNDESLIGA 2026-09-11 15:49:52Z; EPL 2026-10-09 15:25:57Z; EREDIVISIE 2026-09-11 15:50:20Z; LA_LIGA 2026-09-11 15:45:28Z; LIGUE_1 2026-09-11 15:49:24Z; PRIMEIRA_LIGA 2026-09-11 16:06:24Z; RPL 2026-09-05 15:07:55Z; SERIE_A 2026-10-13 14:48:53Z; TURKEY_SUPER_LIG 2026-09-11 16:06:26Z.

The source archive is intact, but no fresh market quote exists to create a new quote-backed original-V2 shadow forecast.

### New exact-head PR results and integration order

- #705 `8cf5ded4...`: **8/8 SUCCESS**. Shared two-session-per-rolling-week public-source budget, 170-hour per-workflow slot, common concurrency and marker-before-download. It preserves existing schedules; no source download is run by push validation.
- #714 `ea4880dc...`: stacked on #705; offline push validation now has exact branch-scoped CI **2/2 SUCCESS**: 76 Free Diagnostic offline tests and 23 budget tests; live download job intentionally skipped on push. No secrets are placed in the push-only validation job.
- #699 `b1ca5049...`: **7/7 SUCCESS**. Source rights, source-before-quote, identity SHA and clock guards. It modifies the same current-form/source/forward workflows as #705, so it must be rebased onto the budget/offline-push result before integration.
- #701 `227b8b1b...`: now a one-commit stack on #699 `b1ca5049...` (ahead 1, behind 0); **6/6 SUCCESS** on exact head. The previous stale-main dependency that caused `_current_gate_freshness` ImportError is removed.
- #701's new outcome provenance rule preserves the metadata-only pre-gate query (`match_date,home_team,away_team`). Only after the frozen 30-eligible-completed-primary-forecast gate does the lazy outcome reader select exact identity, H/D/A and `persisted_at_utc`; each row must be persisted strictly after the forecast-bound `kickoff_utc`. Synthetic regression rejects a row persisted at/before kickoff. No protected production outcomes were read during this work.
- #701 Research CI: 79 prospective runner tests and 22 bridge/workflow tests passed; production-`.pkl` no-change guard passed.
- #704 `cc4918ca...`: **16/16 SUCCESS** (pinned V2 research dependencies); overlaps the same V2 workflow YAMLs and must be rebased after #705/#714/#699.
- #706 `caab7c07...`: **6/6 SUCCESS** (fail-closed production-`.pkl` guard); it shares `research-pr-validation.yml` with #701 and must be rebased after #701 to preserve the evaluator tests.
- #709 `268f3fdc...`: 7/7 on its branch, but its offline source-capture push validation/test is already present in #705; do not merge separately without a new unique-delta review.
- #712 `4b9b1281...`: only one offline-source-reuse check is verified on this exact head; rebase after #705/#699 and require full exact-head CI plus a fresh post-#699 source artifact.
- #707 `a2872bb5...`: 8/8 synthetic runtime/PR validation only; it is not a historical candidate replay or real prospective forecast.
- #697 documentation branch before this update: `daf04a39...`, 7/7 SUCCESS.

Recommended HUMAN-MERGE sequence: #705, then #714; rebase/revalidate #699 preserving the shared budget and offline push jobs; then #704 and #712 after source-chain integration; rebase/revalidate #701 on the final #699 main SHA; then #706 so its fail-closed pickle guard preserves the evaluator CI. #709 is not a separate merge candidate while its unique delta remains covered by #705. No PR was merged.

### Scientific status and prohibited operations

- Original candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 frozen features; original weights unchanged.
- `active_lambda=0` remains the market; `shadow_lambda=1` remains research-only.
- Prospective eligible completed forecasts: **0/30**. Brier Score and LogLoss remain uncomputed; no superiority claim is justified.
- No target outcomes were read, no source/paid-provider request was made in this run, no Supabase write/DDL, no production `.pkl` change, no training/refit, no weight/contract/threshold change, no promotion, bet, merge, schedule change, or other-agent setting change.

## 2026-11-05 07:51 UTC — Run 11: fresh original-V2 source, forward and pre-match audit

**Main remains** `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This entry is being added only to documentation PR #697; no main update or merge was made.

### Main workflows and verified live runs

Re-read current main workflow files and cron expressions:
- Current-Form Source Capture: `.github/workflows/serie-a-v2-current-form-source-capture.yml`, daily 05:50 UTC.
- Free Real-Quote Diagnostic: `.github/workflows/serie-a-v2-free-real-quote-diagnostic.yml`, daily 06:13 UTC.
- Original Forward-Only Preview: `.github/workflows/serie-a-v2-forward-preview.yml`, daily 08:08 UTC.
- Current-Form Forward-Only Preview: `.github/workflows/serie-a-v2-current-form-forward-preview.yml`, daily 08:18 UTC.

At 07:51 UTC the first two scheduled times had elapsed. The available GitHub connector did not expose a scheduled-workflow run listing for 2026-11-05, so no status or request count is inferred for those two slots. Last fully verifiable main runs are 2026-11-04:

- Source Capture run [#41836971469](https://github.com/MaksimBlud/football-ai/actions/runs/41836971469), artifact **13327281383**, 438,212 bytes, ZIP SHA-256 `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`. Log: 19 tests passed; ten old-season files plus one 2026/27 CSV; 100 completed prior-day current-season rows; metadata-only feature-input gate passed; no paid provider calls, Supabase writes or target-outcome evaluation.
- Current-Form Forward run [#41866116572](https://github.com/MaksimBlud/football-ai/actions/runs/41866116572), artifact **13342406844**, SHA-256 `f0893c5fdcbd2515c10915830802f77782441e5638bda62fa7d2dff882d6fc20`. 53 tests passed. It authenticated source artifact #13327281383 and its successful main parent, verified source/archive/parent timestamps, then reported `quotes_seen=0`, `rows=[]`, `v2_current_form_shadow_captured=0`, and no target outcomes read/scored.
- Free Diagnostic run [#41847314320](https://github.com/MaksimBlud/football-ai/actions/runs/41847314320), artifact **13332260799**, SHA-256 `72a32dc61d6e230be46bc5fe69a52e97142a79816af33c66f58066e0ceb6e8d8`. 53 tests passed; ten public CSV requests; 3,800 old-season rows; zero quoted fixtures and zero scored diagnostics; no paid provider request or Supabase write. Report mode was `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`.
- Original Forward run [#41864632742](https://github.com/MaksimBlud/football-ai/actions/runs/41864632742), artifact **13341622767**, SHA-256 `738553a86e392361ce1b27ab0226a2b0fa2f540a6ac9579b5da2d8d81858a215`. 71 tests passed; it verified the 3,800-row historical source artifact, but `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`, and `v2_diagnostic_previews_captured=0`. No Supabase writes or paid calls.

Artifact #13327281383 was downloaded and independently inspected in this run. Its ZIP digest matches GitHub. All 11 CSV member SHA-256 values match the manifest; all ten old-season files contain 380 rows each (**3,800 old-season rows total**) and the 2026/27 file contains **100** prior-day rows. Every source-observation timestamp precedes archive creation. The forward log's `historical_match_rows=3900` is the combined 3,800 old-season + 100 current-season total; the manifest correctly distinguishes them. The feature-source gate read only `match_date,home_team,away_team` and passed at 100 identities. This is a **feature-input gate**, not the separate prospective evaluation gate.

### Read-only Supabase pre-match audit

Only pre-match snapshot/observation metadata and model-SHA/time metadata were queried. No finished-results or target-outcome table was queried.

- `odds_snapshots`: **3,966** rows total; **3,915** satisfy `snapshot_time_utc < commence_time_utc`; **0** strict pre-match rows in the last seven days; **0** future events with a strict pre-match quote.
- Latest strict pre-match snapshot by league: BUNDES 2026-09-11 15:49:52Z; EPL 2026-10-09 15:25:57Z; EREDIVISIE 2026-09-11 15:50:20Z; LA_LIGA 2026-09-11 15:45:28Z; LIGUE1 2026-09-11 15:49:24Z; PRIMEIRA 2026-09-11 16:06:24Z; RPL 2026-09-05 15:07:55Z; SERIE_A 2026-10-13 14:48:53Z; TURKEY 2026-09-11 16:06:26Z.
- `league_structural_v2_observations`: **2,387** rows, all strictly pre-match; **0** in the last seven days and **0** future-event observations.
- `product_prediction_snapshots`: no rows match frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.

Thus the source archive is intact and timestamped, but there is no current market quote with which to produce a new prospective V2 shadow. Evaluation remains **0/30 eligible completed forecasts**; no Brier Score or LogLoss can be calculated.

### Open-PR state and integration findings

Exact current PR metadata/heads were re-read; no PR was merged:
- #706 `caab7c07...`: 6/6 workflow runs SUCCESS (fail-closed production-`.pkl` diff guard).
- #704 `cc4918ca...`: 14 workflow-run records returned for the exact head; all SUCCESS. It overlaps source/forward workflow files and must be rebased after those workflow changes.
- #705 `8cf5ded4...`: 8/8 SUCCESS; shared two-session rolling-week budget, 170-hour per-workflow slots. Its current source-capture workflow already has a secret-free offline push-validation job.
- #714 `00daa9dd...`: stacked on #705; no checks yet. It is still needed because #705's Free Diagnostic job retains Supabase secrets in the job environment on push, even though its budget/download steps are skipped.
- #699 `b1ca5049...`: 7/7 SUCCESS; contains source-rights, identity-SHA and clock guards. Its workflow files still need careful reconciliation with #705/#714's shared budget/concurrency and offline-push behavior.
- #701 `499c95ce...`: 5/6; Research PR Validation failed with `ImportError: cannot import name '_current_gate_freshness'` from `serie_a_v2_current_form_forward_capture.py`. The function exists in #699's branch, not current main. Rebase/stack only after #699 is integrated.
- #712 `4b9b1281...`: no exact-head checks returned; waits for #705/#699 and a fresh post-#699 source artifact.
- #707 `a2872bb5...`: 8/8 SUCCESS, but this is synthetic runtime/PR validation; the main-only manual recovery/replay path was not dispatched. No training/replay success is claimed.
- #697 documentation branch `74de56a9...`: 7/7 SUCCESS before this entry; this commit triggers fresh exact-head documentation CI.
- #709 `268f3fdc...`: 7/7 on its own branch, but its source-capture offline-push split and test are already present in #705's current branch. Do not merge #709 separately without a fresh unique-delta comparison.

A separate evaluator review found one additional post-gate provenance requirement not yet implemented in #701: `_read_exact_completed_outcomes` currently selects `match_date,home_team,away_team,result` but not `persisted_at_utc`. After the existing 30-forecast gate only, the live outcome loader should also select `persisted_at_utc` and require it to be strictly later than that forecast's `kickoff_utc`; add synthetic regressions for before/equal/offsetless timestamps. This must remain lazy: no result or persistence timestamp may be queried before the 30 eligible completed forecasts exist. This is evaluator hardening, not a model/feature/weight change.

### Rights and security boundaries

The current official Football-Data policy says free CSV data is for personal/academic research, permits at most two automated downloads per week, and is not intended for commercial or AI data-training projects: https://football-data.co.uk/contact.php. The repository's frozen-weight inference interpretation remains conditional and is **not** a provider-issued AI-inference licence. No training, refit, commercial use or public-product use is authorized by that manifest. #705's frequency guard is not a licence and is not active on main until HUMAN-MERGE.

Supabase Advisor still reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No DDL or policy changes were made; enabling RLS without reviewed policies could break application access.

No main update, PR merge, schedule change, paid request, Supabase write/DDL, production `.pkl` change, target-outcome read, model refit, candidate/weight/feature/lambda change, promotion or bet occurred in this run.


## 2026-11-05 06:48 UTC — fresh pre-match database audit and prospective-gate code review

Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This is a read-only V2 audit plus a documentation update on this existing PR branch; no main update or merge occurred.

### Fresh Supabase pre-match-only audit

Read-only SQL selected only timestamp, event identity, league and probability/odds fields from pre-match observation tables. No result, score, settlement or post-match table rows were queried.

- `public.odds_snapshots`, Serie A: **625** rows; **620** strictly pre-kickoff; **0** captured in the last seven days; **0** future fixtures with a saved quote; latest snapshot **2026-10-13 14:48:53.042620 UTC**.
- `public.league_structural_v2_observations`, Serie A: **630** rows; **630** strictly pre-kickoff; **0** captured in the last seven days; latest observation **2026-10-13 14:48:53.042620 UTC**.
- Across every league in both queried pre-match tables, there are **0** observations from the preceding seven days and **0** future fixtures with a saved snapshot.
- No new quote or source row was written.

### Latest V2 workflow evidence

The latest scheduled V2 source/diagnostic runs visible on main remain the Nov 4 runs:
- Current-Form Source Capture **#41836971469**, created 2026-11-04 13:18:57 UTC.
- Free Real-Quote Diagnostic **#41847314320**, created 2026-11-04 14:24:55 UTC.
- Current-Form Forward **#41866116572** and Original Forward **#41864632742** both completed Nov 4 and produced **zero** eligible shadow forecasts. No newer Nov 5 V2 source/diagnostic scheduled run was present in the retrieved schedule-run history at 06:48 UTC.
- The separate Nov 5 Serie A Results Sync run was not inspected for logs, artifacts or result rows; protected outcome data were not opened.

### Exact current PR checks and dependencies

| PR | Exact HEAD prefix | Checks | Current disposition |
|---|---|---:|---|
| #706 | `caab7c07` | 6/6 SUCCESS | Fail-closed pickle diff guard; ready for HUMAN-MERGE |
| #704 | `cc4918ca` | 16/16 SUCCESS | Pinned original-V2 CI dependencies; ready for HUMAN-MERGE |
| #705 | `8cf5ded4` | 8/8 SUCCESS | Re-run exact-head CI after #706/#704 integration |
| #699 | `b1ca5049` | 7/7 SUCCESS | Consolidated rights/clock/identity/source guards; must preserve #705 offline-push changes |
| #707 | `a2872bb5` | 8/8 SUCCESS | Synthetic frozen-runtime proof only; recovery/training dispatch remains rights-blocked |
| #702 | `3935fc60` | 8/8 SUCCESS | Manual-only offline feature preview; no new real archive attested |
| #714 | `00daa9dd` | 0 checks | Stacked on #705; must run full CI after its base is integrated |
| #709 | `268f3fdc` | 7/7 SUCCESS | Source-capture push isolation; overlaps #699 workflow changes and needs rebase |
| #712 | `4b9b1281` | 1/1 SUCCESS | Dedicated offline test only; full CI still absent |
| #701 | `499c95ce` | 5/6 SUCCESS | Targeted research test fails because main lacks `_current_gate_freshness`; #699 supplies it |
| #697 | `da6e923e` | 7/7 SUCCESS before this documentation commit | Continuity record |

The exact #701 failing log is run **#41872721087**, job **126723879288**: `ImportError: cannot import name '_current_gate_freshness'` from `serie_a_v2_current_form_forward_capture`. This is a dependency on #699, not evidence that the evaluator's tests themselves are scientifically invalid.

### Additional post-gate outcome provenance review

Code-only review of #701 found that the live pre-gate query is correctly identity-only (`match_date,home_team,away_team`), and the outcome loader is lazy: the market-only path does not invoke it until at least **30 unique eligible completed primary-cohort forecasts** pass the frozen checks. It keeps `active_lambda=0` as the market and `shadow_lambda=1` as research-only.

A separate hardening gap remains for after the gate opens: `_read_exact_completed_outcomes()` currently selects fixture identity plus `result`, but does not select/validate the existing `persisted_at_utc` field from `league_finished_results` against each forecast's kickoff. The table schema exposes `persisted_at_utc` and `source_updated_at_utc`. Before any future Brier/LogLoss run, a follow-up should prove each exact result row was persisted after its kickoff (and retain exact identity/alias checks). This is a post-gate provenance check only; no outcomes were read in this audit, and the 30-event gate must not be weakened or moved.

### Scientific status

- Original frozen candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 inputs and original weights unchanged.
- `active_lambda=0`; `shadow_lambda=1`; no production promotion or betting.
- Real eligible prospective forecasts remain **0/30**; Brier and LogLoss remain unavailable.
- No paid requests, CSV downloads, Supabase writes/DDL, production `.pkl` changes, model refits, threshold tuning, protected outcome reads or merges occurred.

## 2026-11-05 04:54 UTC — byte-level source proof, live Supabase identity SHA, and frozen runtime smoke

Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This entry records read-only evidence and a synthetic runtime attestation; no main change or merge occurred.

### Existing current-form source artifact — independently rehashed

- Downloaded existing GitHub artifact **#13327281383**, parent Source Capture run **#41836971469**. ZIP SHA-256 recomputed from the downloaded bytes: `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`, matching GitHub's artifact digest.
- ZIP contains 12 members: ten frozen historical CSVs, `serie_a_2627.csv`, and the V1 manifest. All **11/11 CSV member SHA-256** values match the manifest; all **11/11 source-observed timestamps** precede archive creation `2026-11-04T13:19:45.149891Z`.
- Historical source: 10 × 380 rows = 3,800. Current-season CSV: 100 rows; SHA-256 `4138a4f01e96312a7a5dc07450c7a520c3861a479620fe3d102f12d42a6678ba`. Its 100 canonical fixture identities independently hash to `f85872547e745eae8854ee245902c1e522657fb3a687032be83b000199f2a99e`.
- The existing V1 archive predates #699 and lacks its rights/identity attestation. It is **not admissible** to the post-#699 evaluator; do not backfill or relabel it.

### Read-only Supabase — pre-match data only

Checked at `2026-11-05T04:54:06Z`:

- Serie A `odds_snapshots`: 625 total; 620 strictly before kickoff; zero strict pre-kickoff snapshots in the preceding seven days; zero future events with a saved strict pre-kickoff quote. Latest strict quote: `2026-10-13T14:48:53.042620Z`.
- `league_finished_results` query selected only `match_date,home_team,away_team` for Serie A 2026/27. It returned 103 raw rows/tuples, 2026-08-22 through 2026-11-02. Applying the existing V2-local `Atalanta BC -> Atalanta` alias yields 100 canonical identities. A read-only SQL SHA-256 and an independent CSV identity SHA both equal `f85872547e745eae8854ee245902c1e522657fb3a687032be83b000199f2a99e`.
- No score, result, or settlement columns were selected.

### Actual forward runtime

- Current-Form Forward run **#41866116572** on main SHA `40887ebb...`: SUCCESS; 53 tests passed; source artifact #13327281383 and parent verified; `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `supabase_writes=0`, `paid_provider_calls=0`.
- Original Forward run **#41864632742**: SUCCESS; source archive SHA verified; 3,800 frozen historical rows; `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `target_outcomes_read=false`, `supabase_writes=0`, `paid_provider_calls=0`.
- Therefore there is still no real-match V2 forecast and no admissible outcome score.

### Original candidate — synthetic runtime attestation

PR #707's prior exact HEAD `3a79d333eb246d92aea88b569c8cb5b4474b9fbd`, workflow run **#41701270604**, completed SUCCESS. The runtime report proves: candidate SHA `a9d5abc2...`; frozen code commit `df197770...`; 19 features; weights shape 20×2; `active_lambda=0` returns the synthetic market vector exactly; `shadow_lambda=1` output is finite and sums to one; stability gate remains false; zero real events scored; no training, target-outcome reads, production `.pkl` changes, or promotion. This is a **synthetic smoke test only**, not forecast-quality evidence.

### Rights and PR queue corrections

- The source-rights manifest on #699/#707 branches says `CONDITIONAL_RESEARCH_ONLY`: frozen-weight inference is limited to the project's narrow personal-betting/academic research interpretation; it is not a provider-issued AI-inference licence. AI training/replay, commercial use, and public-product use are false; authorization is null; the automated download ceiling is two sessions per rolling seven days.
- #707's rights-gate note incorrectly said the overall `rights_status` was `NOT_GRANTED`. Updated that note to distinguish conditional inference from ungranted AI-training permission and added a manifest/document consistency regression. New #707 HEAD is `a2872bb546d9b3093aa8baf5178ae440f45e7f2e`; CI has not yet appeared on this new HEAD. Do not dispatch its training/recovery path: `require_ai_model_training_permission()` must fail before artifact listing/download/extraction under the current manifest.
- Exact open-PR status at this audit: #706 `caab7c07...` 6/6 SUCCESS; #704 `cc4918ca...` 16/16 SUCCESS; #705 `8cf5ded4...` 8/8 SUCCESS but must be revalidated after #706 and #704; #714 `00daa9dd...` has no CI; #699 `b1ca5049...` 7/7 SUCCESS; #702 `3935fc60...` 8/8 SUCCESS; #701 `499c95ce...` 5/6 because main lacks `_current_gate_freshness`, which #699 supplies; #712 `4b9b1281...` has only one check on its current HEAD; #711 remains draft with no CI.
- #699's consolidated branch already contains the substantive historical/current URL, redirect/byte-bound, clock, identity-SHA, rights, and workflow-dependency-trigger protections. Its historical loader blob is `d3b717ea03570413f1d0b6b6f9821b2be0db16a3`; the narrower #700 redirect PR is overlapping and should not be merged separately without a fresh diff. #696/#698 and narrower #682/#683/#692/#695/#686 fixes are likewise substantially covered by #699.
- Safe integration order remains: #706 → #704 → rebase/revalidate #705 → HUMAN-MERGE #705 → rebase/revalidate #714 → HUMAN-MERGE #714 → rebase/revalidate consolidated #699 → HUMAN-MERGE #699. Then rebase #701/#702 and run #702 only after a new rights/identity-attested archive exists.

The unguarded main source-capture and free-diagnostic crons remain at 05:50 and 06:13 UTC. The previously paginated 14 automated sessions (Oct 29–Nov 4) still exceed the manifest's two-session weekly ceiling; no new source download was initiated. The next scheduled attempts are not made safe until the budget/rights changes are integrated. Do not alter schedules or weaken the budget/freshness gates.

Prospective evaluation remains **0/30**. Brier/LogLoss are not available. No paid API calls, Supabase writes/DDL, production `.pkl` changes, model/weight/lambda changes, protected target-outcome reads, merges, or promotions occurred.

## 2026-11-05 03:55 UTC — source-budget and fail-closed integration re-audit

Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Full seven-day pagination found 14 scheduled Football-Data download sessions (one Current-Form Source Capture and one Free Real-Quote Diagnostic daily, Oct 29–Nov 4); the unchanged Nov 5 05:50/06:13 UTC cron attempts remain unguarded on main because #705 is open. No download was initiated in this audit. The provider's two-automated-sessions/week limit is already exceeded; the technical #705 budget is not a licence, and the separate source-rights basis must be resolved before any further CSV request.

Integration order is now explicitly **#706 → update/revalidate #705 → HUMAN-MERGE #705 → rebase/revalidate #714 → #714 → rebase/revalidate #699**. #706 exact HEAD `caab7c07` is 6/6 SUCCESS and fixes the fail-open `.pkl` diff guard still visible in #705's current validation log. #705 exact HEAD `8cf5ded4` is 8/8 SUCCESS but must be rerun after #706. #714 exact HEAD `00daa9dd` has no CI yet. #699 exact HEAD `b1ca5049` is 7/7 SUCCESS but must preserve the budget/offline-push changes when rebased. #701 is 5/6 because its only failure is the missing main helper supplied by #699; #702 is 8/8 and manual-only; #712 has only one dedicated check on its current HEAD. #694 is already an ancestor of #699; #709 is superseded by #705.

Fresh main runtime remains source-verified but forecast-empty: Current-Form Source Capture #41836971469 and Current-Form Forward #41866116572 succeeded; Original Forward #41864632742 succeeded. Both forward reports have zero quotes and zero V2 shadows. Read-only Supabase confirms 625 Serie A odds snapshots / 620 strictly pre-kickoff / zero recent or future quotes. The 30-primary-completed-forecast gate remains CLOSED; no Brier/LogLoss result exists. Full evidence and artifact digests are in `PROJECT_CONTINUITY_ADDENDUM_20261102_V2_RUNTIME_AUDIT.md`.

## 2026-11-04 20:56 UTC — independent byte-level and canonical identity recheck of current-form source

This follow-up independently downloaded the existing main Current-Form Source Capture artifact and recomputed its archive and member hashes. Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no workflow was dispatched and no source request was made.

- Source artifact #13327281383, parent run #41836971469, ZIP SHA-256 `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`; independently downloaded bytes match GitHub's artifact digest.
- The ZIP contains ten historical Serie A CSVs (380 rows each, 3,800 total) plus `serie_a_2627.csv` (100 rows) and the manifest. All eleven CSV member SHA-256 values independently match their manifest entries. The current-season CSV SHA-256 is `4138a4f01e96312a7a5dc07450c7a520c3861a479620fe3d102f12d42a6678ba`.
- Each source member's observed timestamp is strictly before archive creation `2026-11-04T13:19:45.149891Z`; the current CSV observation is `13:19:45.080488Z`. This proves source-before-archive, not source-before-quote: the associated forward run saw zero quotes.
- A new identity-only Supabase query selected only `match_date,home_team,away_team` for Serie A 2026/27. It returned 103 raw rows and 100 canonical identities. Recomputed the exact #699 tab/newline SHA algorithm on both the database identity set and the archived CSV identity set, using the existing Serie A aliases plus V2-local `Atalanta BC -> Atalanta`: both independently yield `f85872547e745eae8854ee245902c1e522657fb3a687032be83b000199f2a99e`. The 103-versus-100 difference is therefore three alias-labelled duplicate rows, not three missing fixtures. This confirms exact 100/100 identity-set parity.
- Important admission boundary: this archive was created by pre-#699 main code. Its manifest stores only the count gate, not the new identity-list/SHA and source-rights attestation. The independent parity audit does not retroactively upgrade its provenance. Do not admit this V1 archive into #701/#712's post-#699 evaluator/cache chain; a fresh source capture after approved #699 integration must carry the full rights and identity attestation.
- Current-Form Forward #41866116572 succeeded and reverified this source artifact/parent, with source age 10,843 seconds, but `quotes_seen=0`, `v2_current_form_shadow_captured=0`, no rows, no outcomes, no writes and no paid calls. Its artifact #13342406844 SHA-256 is `f0893c5fdcbd2515c10915830802f77782441e5638bda62fa7d2dff882d6fc20`; its nested source ZIP digest matches #13327281383.
- Original Forward #41864632742 also succeeded, but `quotes_seen=0`, `future_quotes_checked=0`, `rows=[]`, and zero diagnostic previews. Its artifact #13341622767 SHA-256 is `738553a86e392361ce1b27ab0226a2b0fa2f540a6ac9579b5da2d8d81858a215`.
- Read-only Serie A odds state: 625 snapshots, 620 strictly before kickoff, zero future events with a saved strict pre-kickoff quote; latest strict pre-kickoff snapshot `2026-10-13T14:48:53.042620Z`. No product prediction snapshot carries the frozen V2 candidate SHA. The separate 30-primary-completed-forecast outcome gate remains closed; no target outcomes were read.

Interpretation: the source bytes and current-season fixture identity coverage are now independently verified, correcting the earlier uncertainty around 103 raw metadata rows versus 100 source rows. This still does not produce a quote-level source-before-quote proof or any V2 forecast. The old archive remains inadmissible to the post-#699 evaluator until a new identity/right-attested capture exists. No candidate, weights, feature definitions, lambdas, production artifact, schedule, Supabase data, or main ref was changed.


## 2026-11-04 18:02 UTC — original frozen forward run rehashed; historical source attested, zero quotes

The main `Serie A V2 Original Forward-Only Preview` workflow was re-read at blob `48ce3b0d8e31c4cf293b94500e9c320047311467`. Its schedule is 08:08 UTC; manual dispatch is supported; the only `workflow_run` wake-up is a successful main `workflow_dispatch` of `Serie A Odds Snapshots`. It does not schedule or invoke the paid odds collector. It reads saved odds/source artifacts only.

Main run [#41864632742](https://github.com/MaksimBlud/football-ai/actions/runs/41864632742) completed SUCCESS on main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. All eleven job steps succeeded, including original V2/source-before-quote regression tests, real historical source attestation, and the read-only original forward preview. Artifact #13341622767 (`serie-a-v2-original-forward-source-checked`) was independently downloaded and rehashed: SHA-256 `738553a86e392361ce1b27ab0226a2b0fa2f540a6ac9579b5da2d8d81858a215`, matching GitHub's artifact digest.

The artifact's `serie_a_v2_real_source_attestation.json` verifies historical-only source artifact #13332260799, SHA-256 `72a32dc61d6e230be46bc5fe69a52e97142a79816af33c66f58066e0ceb6e8d8`, parent run #41847314320 on the exact main SHA, 10 pre-prospective CSVs / 3,800 historical rows, original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, and `source_archive_sha256_verified=true`. The referenced source artifact #13332260799 was independently downloaded and rehashed; its ZIP SHA-256 matches exactly. Its report records 10 public CSV requests, zero quotes, zero diagnostic previews, zero scored rows, no 2026/27 public-results download, no Supabase writes, and no outcome reads.

The original forward report itself is explicit: `quotes_seen=0`, `future_quotes_checked=0`, `rows=[]`, `v2_diagnostic_previews_captured=0`, `eligible_for_frozen_prospective_cohort=false`, `independent_incumbent_asof_verified=false`, `uses_original_frozen_v2=true`, paid calls 0, Supabase writes 0, and `uses_2026_27_results=false`. Thus the run proves original-candidate and historical-source archive attestation in the live workflow, but **does not prove quote-level source-before-quote inference** and creates no forecast. Do not count it toward the 30-event gate.

The separate Current-Form Forward run #41866116572 is documented immediately below: it also verified its newer source artifact but saw zero quotes and captured zero V2 forecasts. No source refresh, paid request, outcome read, write, or schedule change was made in this audit.

## 2026-11-04 17:55 UTC — latest forward artifact rehashed; source verified but no quote or V2 forecast

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original 19-feature contract, weights, `active_lambda=0`, and `shadow_lambda=1` are unchanged.

**New main-only runtime evidence:** Current-Form Forward-Only Preview [run #41866116572](https://github.com/MaksimBlud/football-ai/actions/runs/41866116572) completed SUCCESS on the exact main SHA. Its artifact is #13342406844, ZIP SHA-256 `f0893c5fdcbd2515c10915830802f77782441e5638bda62fa7d2dff882d6fc20` (independently downloaded and rehashed). The report's `as_of_utc` is `2026-11-04T16:20:29.049189Z`; it independently verifies source artifact #13327281383, SHA-256 `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`, whose nested ZIP bytes were also independently rehashed. The source manifest records 10 frozen historical CSVs / 3,900 rows, current-season CSV / 100 rows, feature-input identity gate count 100, source observation `13:19:45.080488Z`, archive creation `13:19:46Z`, and successful main parent run #41836971469 completed `13:19:49Z`. The forward verifier reported source age 10,843 seconds.

**Critical interpretation:** the forward artifact reports `quotes_seen=0`, `rows=[]`, `v2_current_form_shadow_captured=0`, `eligible_for_current_form_forward_shadow=false`, `target_outcomes_read=false`, `target_outcomes_scored=false`, paid calls 0, and writes 0. Thus this is real source-artifact/parent attestation proof, **not** a quote-level source-before-quote proof and **not** a V2 inference. No prediction or quality claim is made.

**Later identity-only Supabase read (17:54 UTC):** `odds_snapshots` has 3,915 strictly pre-match snapshots out of 3,966 total; zero strict pre-match snapshots/events in the last seven days and zero future events with a strict pre-match quote. A separate Serie A 2026/27 query selected only `match_date, home_team, away_team` and returned 103 raw provider-label tuples through 2026-11-02. A fresh 19:56 UTC metadata-only recheck applying the frozen V2-local alias `Atalanta BC -> Atalanta` yields **100 canonical fixture identities**; exactly three raw rows carry the alias label. The 13:19 source artifact manifest reports 100 completed current-season rows, so raw 103 versus source 100 is **not evidence of three missing fixtures**. The earlier independent byte/identity audit in the 15:12 section recorded the same canonical-set SHA-256 on metadata and source CSV (`f85872547e745eae8854ee245902c1e522657fb3a687032be83b000199f2a99e`). This recheck confirms the canonical count, not a new byte-level digest recomputation. The old artifact still lacks the post-#699 rights/identity attestation and must not be admitted to the prospective evaluator; after #699 is manually integrated, a fresh archive must persist the gate/source identity digests and pass the live verifier. No score/result columns were selected and no protected outcomes were read. No source refresh was initiated because the shared source budget is not yet on main and the current #705 budget reservation must be integrated first.

**Open-PR exact-head state:** #705 remains open at `97a94f5ba3aa921175071e490a9c698aaf0a414b`, with 8/8 exact-head checks SUCCESS. Its source-capture workflow already contains push-only offline validation and main-only non-push capture; its diagnostic workflow also skips source requests on push. This makes #709's two-file source-capture push-isolation change redundant if #705 is manually merged; a supersession note was added to #709, and #709 should not be merged separately. #699 remains open at `09c95fde22091311cbe56da236e76360aad33f72`, with 7/7 exact-head checks SUCCESS. #701 remains open at `499c95cea970d42ee6512b77986af6143295e653`; five of six PR workflows succeeded, while Research PR Validation failed because `_current_gate_freshness` is supplied by #699 and is absent from main. Do not duplicate that helper: integrate #705, then #699, then rebase #701 and rerun exact-head CI. HUMAN-MERGE only; main was not changed.

## 2026-11-04 15:12 UTC — source identity parity, actual forward runs, and push-trigger guards

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The frozen original candidate and protocol remain unchanged: candidate blob `ac1303f6b096664983fbf52443bd0a381b23ba21`, candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, protocol blob `65729e9639720e67624c1481190aa22ae606f151`; 19 features, 20×2 weights, active lambda 0, shadow lambda 1, stability gate FAILED.

New exact main evidence:
- Source Capture #41836971469 succeeded. Artifact #13327281383 was created 2026-11-04 13:19:46 UTC; ZIP SHA-256 `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`. The current-season CSV member SHA-256 is `4138a4f01e96312a7a5dc07450c7a520c3861a479620fe3d102f12d42a6678ba`. Source observed at 13:19:45.080 UTC; 100 completed prior-day rows plus 10 historical season files / 3,800 historical rows.
- Current-Form Forward #41837103174 succeeded and verified the exact source artifact/parent run, but the artifact report contains zero saved quotes and zero V2 current-form shadow forecasts.
- Free Real-Quote Diagnostic #41847314320 succeeded. Artifact #13332260799 ZIP SHA-256 `72a32dc61d6e230be46bc5fe69a52e97142a79816af33c66f58066e0ceb6e8d8`; it contains 10 historical season files / 3,800 rows, zero quoted fixtures, zero diagnostic previews and zero scored forecasts. It is not a current-season source or a V2 forecast.

Independent source identity parity was recomputed without selecting any Supabase score/result/settlement fields. Supabase query selected only `match_date, home_team, away_team`: 103 raw rows canonicalize to 100 unique identities. The archived current-season CSV contains the same 100 canonical fixture identities. Both independently produce SHA-256 `f85872547e745eae8854ee245902c1e522657fb3a687032be83b000199f2a99e`. Canonicalization used the existing Serie A runtime aliases (Inter→Inter Milan, Milan→AC Milan, Roma→AS Roma, Verona→Hellas Verona) plus the V2-local Atalanta BC→Atalanta alias. This is an independent audit result only: the Nov 4 V1 archive manifest does not persist the identity-set SHA/rights attestation required by the newer #699 reader, so do not pass that old artifact to the prospective evaluator as a fully attested V2 source.

Read-only Supabase state: Serie A odds snapshots 625 total / 620 strictly pre-match / 63 event identities; zero future events have a saved strictly pre-kickoff quote; latest strict pre-match snapshot 2026-10-13 14:48:53 UTC. Product prediction snapshots: 40 total, zero rows with the original V2 candidate SHA. The prospective evaluation gate remains 0/30; no Brier/LogLoss and no V2-over-market claim.

New branch safety fixes:
- #705 HEAD `97a94f5ba3aa921175071e490a9c698aaf0a414b`: 8/8 exact-head CI SUCCESS. Budget tests 23 passed; original V2 shadow tests 86 passed; CI confirms no production .pkl changes. The branch now requires main for the free diagnostic secret-bearing job, restricts the current-form forward reader to schedule/manual/approved workflow_run events (not direct push), and bootstraps its 170-hour diagnostic cooldown from the real Nov 4 diagnostic artifact.
- #699 HEAD `09c95fde22091311cbe56da236e76360aad33f72`: 7/7 exact-head CI SUCCESS. Original V2 shadow tests 321 passed; current-form dependency-trigger tests 13 passed; CI confirms no production .pkl changes. Its forward job now also excludes direct push and unapproved parent events.
- #705 and #699 remain separate, open, HUMAN-MERGE PRs. Do not merge #699 without rebasing its download-capable workflows onto #705's budget marker/shared concurrency and offline-only push validation. Preserve #699's rights gate, identity SHA, diagnostic-triggered freshness preflight and explicit forward event allowlist. The source workflow integration must apply the 170-hour reservation to every download-capable event, including its diagnostic-triggered workflow_run path.
- #701 HEAD `99e67b61f474aa5de51d7b829405a23a44cbc4fe` has 6/6 exact-head CI SUCCESS; the targeted run passed 79 prospective evaluator/runner tests and 17 artifact/workflow bridge tests, and the no-production-`.pkl` guard passed. Its workflow now excludes push-triggered evaluator runs. The market-only prospective evaluator is separate from the full three-way evaluator and calls the lazy outcome loader only after 30 eligible completed primary forecasts. The full three-way path remains blocked until a frozen incumbent reference is pinned. #702 remains 7/7 CI SUCCESS and manual-only; it is a zero-credit event-metadata/19-feature readiness probe, not a probability generator. It was not dispatched.

Operational constraint remains: source freshness limit is 24 hours, but #705's per-workflow download cooldown is 170 hours. The Nov 4 source observation reaches 24 hours on Nov 5 around 13:19:45 UTC; the next allowed source attempt is Nov 11 15:19:46 UTC, with the unchanged 05:50 UTC cron first occurring after that on Nov 12. The Nov 4 diagnostic attempt similarly moves its next allowed slot to Nov 11 16:25:54 UTC. Do not weaken the 24-hour source-before-quote rule, exceed the provider's conditional download policy, change schedules, or create a paid request to bridge this gap.

No prospective target outcomes were read or scored; the Supabase feature-gate query selected identity metadata only. No paid provider request, workflow dispatch, Supabase write/DDL, production .pkl change, weight/contract change, promotion, merge or bet occurred. Main remains unchanged. Detailed artifact and SQL evidence is recorded in [PROJECT_CONTINUITY_ADDENDUM_20261102_V2_RUNTIME_AUDIT.md](PROJECT_CONTINUITY_ADDENDUM_20261102_V2_RUNTIME_AUDIT.md).

## 2026-11-04 14:24 UTC — latest #705 budget-bootstrap regression and freshness limitation

PR #705 was updated with an offline regression using both the actual Nov 3 and Nov 4 legacy source artifacts. The test now proves that the bootstrap chooses the newest authenticated source artifact/parent rather than the older Nov 3 example:

- New exact HEAD: f518e7ec44b180595c9365cc354d34844f07e174.
- Source artifact #13327281383, created 2026-11-04T13:19:46Z, parent run #41836971469, is selected over source artifact #13231843819 from Nov 3.
- The calculated 170-hour next source slot is 2026-11-11T15:19:46Z; unchanged 05:50 UTC cron first falls after it on Nov 12.
- Focused budget tests: 22 passed in run #41845396377.
- Exact-head CI: 8/8 SUCCESS — Budget #41845396377, Research #41845396419, Serie A #41845396358, Frozen V2 Shadow #41845396424 (86 passed), Bundesliga #41845396884, Ligue 1 #41845396817, Eredivisie #41845396449, Product #41845396469. Research log explicitly prints PASS: no .pkl changes in PR.
- No source network request was made by this test change; main remains unchanged.

PR #705 is still open and HUMAN-MERGE only. Main still has the unchanged daily source-capture cron at 05:50 UTC; because #705 is not merged, the next scheduled slot on 2026-11-05 05:50 UTC is not yet budget-guarded. Do not dispatch anything manually. The Nov 4 source archive was created before #705 existed on main.

**Operational freshness conflict:** the source-before-quote contract requires the source observation to be no older than 24 hours at quote time, so the Nov 4 observation reaches its 24-hour age limit around 2026-11-05 13:19:45 UTC. After #705 is merged, the next source-capture slot under the 170-hour budget is not until Nov 12 05:50 UTC. Thus, even if future quotes appear, the existing Nov 4 archive cannot support new current-form V2 forecasts after its 24-hour limit, and the budget will block another source capture for roughly a week. Do not weaken the frozen 24-hour contract or exceed the provider's conditional download policy to bridge this gap; record it as an operational constraint requiring an authorized source-use resolution. Current future strict pre-match quotes remain zero, so no forecast is presently possible anyway.

The #699 current exact HEAD remains 8f767e0877a87d002209b80c19ce6dbdb2a3050b with 7/7 SUCCESS and its rights/identity guards. Its workflow files still omit #705's shared 170-hour marker/concurrency/push protections; the integrated rebase must preserve #705's offline push jobs, shared concurrency group and marker-before-download in both workflows while retaining #699's rights checks, identity-set SHA and diagnostic-triggered freshness preflight. #709 remains redundant. No main merge, schedule change, new public-source request, paid call, Supabase write/DDL, protected target-outcome read, production .pkl change, refit, promotion or bet occurred.

---

## 2026-11-04 14:12 UTC — exact #699 head correction

A final GitHub PR metadata re-read found that #699's current branch ref resolves to `8f767e0877a87d002209b80c19ce6dbdb2a3050b`, not the earlier `f11b3e1a5fc62f7415ae72944b058b05e3fddd94` cited in the stale PR body/earlier audit note. The branch was re-read at its actual head ref `research/v2-source-capture-guards-integrated-20261026`; the rights and identity protections remain present:

- `market_anchor_v2_source_rights.py`: blob `9fd3a12013af3e0fbe080ffc5a608f50fe21e1bb`.
- `research/source_rights/football_data_co_uk.json`: blob `ca57046b1408bca39381850e3e3a4b3d70830c6c`.
- Current-form source capture: blob `59ac00c5c1975b850e475102867b7734068c2c5f`, including `require_personal_research_inference_scope()`, frozen candidate preflight, identity-set SHA/coverage attestation, exact URL and bounded no-redirect stream checks.
- Current-form forward reader: blob `3c397abc02d4f8b7532a526d0af2f6d751b3cf4a`, including the rights guard and identity-set verification.
- Frozen candidate JSON remains byte-identical to main: `ac1303f6b096664983fbf52443bd0a381b23ba21`; original feature builder `401b3a0893371bfa4a488ec92a4a54af2678c8f7` and core shadow module `b2770d726ffafe7a3cef706b57d3391063cbfe1b` are also identical.
- Wrapper `serie_a_v2_frozen_shadow_preview.py` differs by guard hardening, but its inference body from `previews = []` to the next function is byte-identical to main.

Exact current #699 HEAD `8f767e0877a87d002209b80c19ce6dbdb2a3050b` has **7/7 SUCCESS**: Shadow #41804425498, Research #41804425514, Serie A #41804425523, Bundesliga #41804425224, Ligue 1 #41804425479, Eredivisie #41804425488, Product #41804425268. The PR diff is 27 files and 141 commits ahead of main (not 136); inspect the complete diff before any HUMAN-MERGE. The earlier `f11b3e1...` note was a stale intermediate snapshot, not the current PR head.

PR #713 remains closed unmerged as superseded; #699 itself contains the rights helper and manifest, so no rebase after #713 is required. The correct integration order remains #705 first, then rebase/review the current #699 branch against resulting main and rerun exact-head CI. #705's current-form source workflow already has offline-only push validation; #709 remains a duplicate.

This correction does not change the 4 Nov runtime conclusion: source artifact #13327281383 was produced by pre-#699 main and lacks the identity-set SHA/rights guard, so it is not eligible for #701/#702/#712. No new source call, manual dispatch, outcome read, paid call, Supabase write/DDL, model change, main update, or merge occurred.

---

## 2026-11-04 13:54 UTC — fresh main source-capture and forward-only runtime proof

This entry supersedes the earlier 11:54 UTC statement that no 2026-11-04 V2 scheduled runs were yet visible. Fresh GitHub Actions API evidence now confirms two successful main-only runs on unchanged main `40887ebb215730190d7a6c7a1693373ec4afcdfc`.

### Actual current-form source archive

[Current-Form Source Capture run 41836971469](https://github.com/MaksimBlud/football-ai/actions/runs/41836971469) completed SUCCESS on 2026-11-04:

- Created 13:18:57 UTC; completed 13:19:49 UTC.
- Exact main SHA: `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Source archive artifact ID `13327281383`, 438,212 bytes, GitHub artifact ZIP SHA-256 `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`.
- The live step passed its 19 focused tests and reported 100 completed primary-event identities, 100 current-season completed prior-day rows, 10 frozen historical files plus one current-season CSV (11 source files total), exact frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, zero paid calls, zero Supabase writes, and no target-outcome scoring.
- The 30-event feature-input gate is passed (100 canonical identities). The separate prospective evaluation gate remains closed.

The 2026/27 CSV is admitted only after the metadata-only feature-input gate and is used as lagged historical features for later fixtures. This is not a prospective target-outcome evaluation. The run did not call the evaluator or read target outcomes for scoring.

### Independent forward consumer proof

[Current-Form Forward-Only Preview run 41837103174](https://github.com/MaksimBlud/football-ai/actions/runs/41837103174) completed SUCCESS:

- Created 13:19:52 UTC; completed 13:20:32 UTC.
- Exact main SHA remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- 53 focused regression tests passed.
- The consumer independently verified source artifact `13327281383` and its exact ZIP digest `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`, candidate SHA, parent workflow path/run/head, source observation at `2026-11-04T13:19:45.080488Z`, artifact creation at `13:19:46Z`, parent completion at `13:19:49Z`, and source age 42 seconds at verification.
- Verified source metadata: 100 feature-gate identities, 100 current-season rows, 3,900 historical-plus-current match rows, 10 frozen historical CSVs, 11 total source files.
- `quotes_seen=0`; `v2_current_form_shadow_captured=0`; every reported quote-block counter is zero. Target outcomes were neither read nor scored. Paid calls and Supabase/production writes were zero.
- Forward artifact ID `13327081347`, 439,365 bytes, ZIP SHA-256 `784a94b80a3827a2aa21c9500899f810586d4e70019951b9f767a7bf7fe5b14f`.

This is a genuine source-archive creation and independent source-verification runtime proof, but **not** a source-before-quote forecast pair: there were no saved quotes, therefore no V2 preview and no prospective evaluation progress.

### Important integration limitation of the new archive

Both runs executed the pre-#699 main code. Main's current-form source-capture blob was `9f48a4a6e78d5d7ffa193ec6f24b394162f36ab4`; it uses the metadata count gate but does not yet carry #699's canonical gate-identity list/count/SHA attestation or call `require_personal_research_inference_scope()`. The 4 November archive must therefore **not** be treated as the post-#699 identity-attested source artifact required by #701/#702 or the strict reuse chain in #712. Do not reuse it for those gates. Wait for the approved #705/#699 integration and a fresh source capture produced by the integrated exact code.

The separate 30-eligible-prospective-forecast outcome gate remains **0/30**. No Brier/LogLoss or V2-over-market claim is possible.

### Read-only Supabase audit, 2026-11-04

Only strict pre-match odds and fixture identity metadata were queried:

- `public.odds_snapshots`, SERIE_A, filtered by `snapshot_time_utc < commence_time_utc`: 620 rows / 63 events; latest admissible snapshot `2026-10-13 14:48:53.04262+00`; zero future-kickoff rows and zero strictly pre-match rows in the preceding seven days.
- `public.product_prediction_snapshots`, SERIE_A, filtered by the frozen V2 candidate SHA and `generated_at_utc < commence_time_utc`: **0** rows.
- `public.league_finished_results`: selected only `match_date, home_team, away_team` for SERIE_A 2026/27 before 2026-11-04. Result: 103 raw metadata rows, 100 canonical identities after the existing `Atalanta BC → Atalanta` alias, latest fixture date 2026-11-02. No score, result, or settlement column was selected.
- No Supabase write or DDL was performed.

### Exact PR integration status and corrections

- #699 current exact HEAD `f11b3e1a5fc62f7415ae72944b058b05e3fddd94`: 7/7 exact-head CI SUCCESS, including 314 frozen-V2 shadow tests. Compare against main shows 136 commits ahead and 27 changed files; review the complete 27-file diff and do not merge blindly. It contains the conditional personal/academic research rights helper/manifest and source/clock/identity/redirect guards; it does not grant a provider-issued AI-inference licence, AI training, commercial use, or public-product use.
- #713 is closed unmerged as superseded; its own closure record confirms #699 already contains the rights helper. Ignore any stale #699 body sentence that says to rebase after #713.
- #705 current HEAD `8b139335e6722b7c4f5286962486bca84bced20d`: 8/8 exact-head CI SUCCESS, 22 budget tests. Direct inspection of its current-form source workflow confirms an offline-only `validate-source-capture` push job and a non-push/main-only capture job; #709 duplicates this isolation and must not be merged independently.
- #705's bootstrap selects the latest authenticated legacy source artifact for each exact workflow path. The new source artifact `13327281383` at `2026-11-04T13:19:46Z` supersedes the Nov 3 source artifact as the bootstrap anchor. Under the 170-hour per-workflow guard, the next source-capture slot is no earlier than `2026-11-11T15:19:46Z`; with the unchanged 05:50 UTC cron, the next scheduled eligible slot is 2026-11-12 05:50 UTC, assuming no newer attempt. The diagnostic bootstrap remains based on artifact `13236383688` at `2026-11-03T14:05:06Z`; its 170-hour slot opens 2026-11-10 16:05:06Z, so the unchanged 06:13 UTC schedule first falls after it on 2026-11-11. These limits apply only after #705 is manually merged and do not retroactively undo earlier source requests. Provider wording does not specify whether "twice per week" is counted per session or per CSV file; the budget is a guard, not a licence.
- #712 remains unintegrated at `4b9b1281a8ab81988ea713eb5974d1e55dbba81d`; its latest dedicated source-reuse run passed 53 tests, but the current pre-#699 archive is not an eligible producer for its identity-attested consumer.
- Original Forward Preview schedule remains `08:08 UTC`. No Nov 4 run was visible in the queried main scheduled-run results by 13:54 UTC; treat that as not yet observed, not as proof that the workflow is disabled or failed (GitHub schedule dispatch can be delayed).

HUMAN-MERGE only. No main update, PR merge, schedule change, manual source dispatch, paid call, Supabase write/DDL, production `.pkl` change, protected target-outcome evaluation, model refit, promotion, or bet occurred.

---

## 2026-11-04 11:54 UTC — Research Brain exact-head and pre-match audit

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main ref was changed. Original candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features and original weights/protocol unchanged; `active_lambda=0), `shadow_lambda=1) research-only. Candidate JSON, protocol, historical feature builder, and core `market_anchor_1x2_v2_shadow.py` blobs match between main and #699. The #699 shadow-preview diff is guard-only; the complete inference body from `previews = []` onward is byte-identical.

Current exact PR heads:
- #705 `8b139335e6722b7c4f5286962486bca84bced20d`: 8/8 SUCCESS; 22 budget tests. Its branch already combines the shared 170-hour download budget and offline-only push validation for Current-Form Source Capture.
- #699 `8f767e0877a87d002209b80c19ce6dbdb2a3050b`: 7/7 SUCCESS; 320 frozen V2 shadow tests. It must be rebased after #705 and preserve the budget/offline-push guards; its current workflow branch would otherwise permit capture on push.
- #709 `268f3fdc82036fca0e44dc0aef20d39423cfda2d`: 7/7 SUCCESS but superseded by #705 for the same workflow; do not merge independently because it lacks the budget guard.
- #712 `4b9b1281a8ab81988ea713eb5974d1e55dbba81d`: one dedicated offline run #41817875512 SUCCESS, 53 tests; no full PR-validation set on this current HEAD, and GitHub reports mergeable=false. Its older 9/9 claim is for a prior SHA. Rebase after #705/#699 and preserve the source-rights gate before archive use.
- #704 14 observed check runs all SUCCESS; #701 6/6; #702 7/7; #706 6/6. #711 remains the overlapping draft alternative to #712; #707 candidate rebuild/refit remains excluded.

Read-only Supabase: Serie A 2026/27 metadata query selected only `match_date,home_team,away_team`: 103 raw rows, 100 canonical identities after the existing Atalanta alias, 3 alias duplicates, through 2026-11-02. This is the feature-input gate only. Across all leagues, 3,966 odds snapshots include 3,915 strictly pre-match rows but **zero future-kickoff pre-match rows**; Serie A's latest strict pre-match snapshot remains 2026-10-13 14:48:53 UTC. The 40 product prediction snapshots are all `EPL_AI_MARKET_PAIR_V1`; none uses the frozen V2 candidate SHA. Prospective evaluation remains 0/30; no Brier/LogLoss or superiority claim.

Last verifiable main V2 workflow runs remain 2026-11-03 and recorded zero quotes/zero previews. The GitHub connector does not expose repository-wide scheduled-run discovery for 2026-11-04, so today's schedule status is unknown. No target outcomes, protected current-season CSV member, new public CSV download, paid provider call, Supabase write/DDL, production artifact, or schedule was touched. Source rights remain conditional personal/academic research interpretation, not a provider-issued AI-inference licence; training/commercial/public-product use remains blocked.

Detailed evidence, exact SHAs, workflow blobs, SQL scope, CI run IDs, and merge order are in [`PROJECT_CONTINUITY_ADDENDUM_20261102_V2_RUNTIME_AUDIT.md`](PROJECT_CONTINUITY_ADDENDUM_20261102_V2_RUNTIME_AUDIT.md). HUMAN-MERGE only; no main merge or production change.

---

## 2026-11-04 08:15 UTC — rights, evaluator, and pre-match data audit

Fresh main is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This is an update to the existing documentation branch only. Main, model artifacts, schedules, and Supabase were not changed.

### Original source rights and #699

The current official Football-Data fair-use page (updated 03/11/26) says the free CSV/Excel data is intended for private personal betting and/or academic research only, permits at most light automated downloads twice per week, and excludes commercial use and AI data-training projects. It does not expressly define frozen-weight inference. The project manifest therefore records an operational, conditional personal/academic research interpretation, explicitly not a provider-issued AI-inference licence.

Latest #699 exact HEAD: `f11b3e1a5fc62f7415ae72944b058b05e3fddd94`; exact CI **7/7 SUCCESS**. The branch contains:
- `market_anchor_v2_source_rights.py`;
- `research/source_rights/football_data_co_uk.json`;
- guard-before-external-I/O calls in current-form source capture, current-form forward, original forward, free diagnostic, and real-source attestation;
- `SOURCE_RIGHTS_BLOCKED_NO_NETWORK_NO_INFERENCE` reports when the requested use falls outside the configured scope;
- a separate explicit-written-permission + evidence SHA path for any AI training/recovery, which remains denied by the current manifest;
- regression tests for research scope, policy freshness, two-session download cap, evidence SHA, no legacy XGBoost dependency, and guard-before-I/O order.

The manifest permits only frozen-weight, noncommercial personal/academic research inference; AI model training, commercial use, and public product publication remain false. It records a maximum of two automated source sessions per rolling seven days. The core frozen candidate and protocol are not changed by #699.

### Exact open V2 PR heads and CI

- #705 `8b139335e6722b7c4f5286962486bca84bced20d`: **8/8 SUCCESS** — shared two-session rolling-week download budget; push validation offline; original cron expressions preserved.
- #699 `f11b3e1a5fc62f7415ae72944b058b05e3fddd94`: **7/7 SUCCESS** — source, clock, identity, outcome, and rights guards; V2 shadow suite **314 passed**; no `.pkl` changes.
- #704 `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: **14/14 SUCCESS** — pinned CI dependencies.
- #706 `caab7c07ad720866616ce9fa62664b0d398e5fe0`: **6/6 SUCCESS** — fail-closed production `.pkl` diff guard.
- #712 `1c0f5a424dd51abc0f1a7dedfb7f8ff1047b3339`: **8/8 SUCCESS** — reuse verified historical CSVs; rebase after #705/#699 and preserve rights/source-before-quote guards.
- #701 `0dbb1106e98f4c83f2bce79d9fb7dd634087e367`: **6/6 SUCCESS** — prospective evaluator; 30 eligible completed primary forecasts required before outcome loading; legacy XGBoost evidence rejected. Rebase after #699 and preserve the rights helper before enabling the evaluator.
- #702 `3935fc601eff30d2ca0a7670dae797d0cb365228`: **7/7 SUCCESS** — manual-only zero-credit fixture/feature-readiness preview; keep undispatched until the integrated source/rights gates are verified.
- #697 remains documentation-only and HUMAN-MERGE only.
- #707 remains excluded because it refits/reconstructs a candidate; #711 is a draft alternative to #712 and must not be merged alongside it.
- A temporary duplicate rights PR #713 was closed as superseded after inspection of #699's latest exact HEAD; it changed no main or production state.

Recommended manual integration order: **#705 → rebase/revalidate #699 → #704/#706 → #712 → #701/#702**. Re-run CI on every exact resulting HEAD. HUMAN-MERGE only.

### Current original V2 contract

Frozen candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; candidate Git blob `ac1303f6b096664983fbf52443bd0a381b23ba21); protocol blob `65729e9639720e67624c1481190aa22ae606f151). The original model implementation and feature-builder blobs remain unchanged. Contract: 19 features, 20×2 weights, 3,799 training rows, `active_lambda=0` (market), `shadow_lambda=1` (research). Stability gate remains failed. No refit, weight changes, promotion, production `.pkl` changes, or bets.

### Verified runtime and pre-match database state

Last verifiable main workflow runs remain on 2026-11-03:
- Source Capture #41640753996: 19 tests; 98 metadata-only gate identities; 100 current-season CSV rows; 10 historical CSVs; 11 files total; artifact #13231843819; ZIP digest `4e6fb5531a2206a353fe00fa1ebb0b4d20b3c6ae41ab49a7c672f8dab6d29cd8`.
- Free Real-Quote Diagnostic #41650074683: 53 tests; zero quotes and zero scored diagnostics.
- Original Forward #41670482076: 71 tests; 3,800 historical rows; zero quotes, zero previews, zero forecasts; no target outcomes read/scored.
- Current-Form Forward #41672409582: 53 tests; source artifact verified; zero quotes and zero shadow captures; target outcomes not read.

The available GitHub connector did not expose a list of scheduled workflow runs for 2026-11-04; no status is inferred for today's scheduled slots.

Read-only Supabase pre-match checks:
- `public.odds_snapshots`: 3,966 rows total; 3,915 strictly pre-match; zero new strictly pre-match rows in the last seven days; latest strict pre-match snapshot 2026-10-13 14:48:53 UTC; zero future events with a strict pre-match quote.
- `public.product_prediction_snapshots`: 40 rows total; zero strictly pre-match predictions for the frozen V2 candidate SHA; zero matching events.

No target scores/results/settlement were selected. No Supabase writes or DDL were executed.

### Supabase security advisory

The connected project reports RLS disabled on five public tables: `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. The latter two have 184 and 40 rows respectively. This is a critical exposure to anon/authenticated roles. No automatic remediation was applied; enabling RLS without deliberate policies may block application access. User approval and policy design are required.

## 2026-11-04 06:12 UTC — exact GitHub API metadata redirects blocked in all three V2 readers

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` still has its last mainline entry dated 2026-10-18. This update is documentation-only on the existing continuity PR branch. No main ref or production state was changed.

### New source-provenance fixes and exact-head CI

A code review found that three V2 metadata readers allowlisted the GitHub API request URL but relied on Requests' default redirect-following behavior. Their metadata responses could therefore be accepted without proving that the final response remained on the exact GitHub API URL. All three helpers now:
- pass `allow_redirects=False`;
- require `response.url == requested_url`;
- require HTTP 200 before parsing JSON;
- reject redirects/errors without parsing their response bodies.

**PR #699 — original and current-form forward readers**
- Exact HEAD: `f11b3e1a5fc62f7415ae72944b058b05e3fddd94`.
- Files changed by this incremental fix: `serie_a_v2_forward_capture.py`, `serie_a_v2_current_form_forward_capture.py`, and their two test files.
- Six focused regressions cover 302 rejection, unexpected response URL rejection, and valid exact-200 behavior for both readers.
- Exact-head CI: **7/7 SUCCESS**. Original V2 Frozen Shadow Tests [#41783044006](https://github.com/MaksimBlud/football-ai/actions/runs/41783044006) — **314 passed**. Research [#41783043965](https://github.com/MaksimBlud/football-ai/actions/runs/41783043965) — SUCCESS; production artifact guard printed `PASS: no .pkl changes in PR`. Serie A [#41783044027](https://github.com/MaksimBlud/football-ai/actions/runs/41783044027), Bundesliga [#41783044028](https://github.com/MaksimBlud/football-ai/actions/runs/41783044028), Product [#41783044011](https://github.com/MaksimBlud/football-ai/actions/runs/41783044011), Eredivisie [#41783044021](https://github.com/MaksimBlud/football-ai/actions/runs/41783044021), Ligue 1 [#41783044123](https://github.com/MaksimBlud/football-ai/actions/runs/41783044123) — all SUCCESS.

**PR #701 — prospective evaluator metadata reader**
- Exact HEAD: `0dbb1106e98f4c83f2bce79d9fb7dd634087e367`.
- `market_anchor_1x2_v2_prospective_evaluation.py` now applies the same exact-URL/no-redirect/HTTP-200 rule.
- Three focused regressions cover 302 rejection, unexpected response URL rejection, and valid exact-200 behavior. The tests extract only the helper AST so the lightweight artifact-contract job does not import the model/scikit-learn dependency stack.
- Exact-head CI: **6/6 SUCCESS**. Research [#41783608344](https://github.com/MaksimBlud/football-ai/actions/runs/41783608344) — the forward-artifact bridge/contract step **17 passed**, and the production artifact guard printed `PASS: no .pkl changes in PR`. Serie A [#41783608357](https://github.com/MaksimBlud/football-ai/actions/runs/41783608357), Bundesliga [#41783608458](https://github.com/MaksimBlud/football-ai/actions/runs/41783608458), Ligue 1 [#41783608368](https://github.com/MaksimBlud/football-ai/actions/runs/41783608368), Product [#41783608342](https://github.com/MaksimBlud/football-ai/actions/runs/41783608342), Eredivisie [#41783608449](https://github.com/MaksimBlud/football-ai/actions/runs/41783608449) — all SUCCESS.

Both are transport/provenance-only changes. The frozen candidate, original 19-feature order, weights, protocol, `active_lambda=0`, `shadow_lambda=1`, evaluation gate and protected-outcome behavior are unchanged. No live evaluation, outcome read, source download, Supabase write/DDL, or production artifact change was performed.

### Re-read open V2 PRs and merge dependencies

- #705 HEAD `8b139335e6722b7c4f5286962486bca84bced20d`: **8/8 SUCCESS**. Its 170-hour-per-approved-workflow shared source budget and push-only offline validation are still not active on main. It remains first in the HUMAN-MERGE order.
- #699 HEAD `f11b3e1a5fc62f7415ae72944b058b05e3fddd94`: **7/7 SUCCESS**. It shares source/workflow paths with #705; rebase and rerun exact-head CI after #705 lands.
- #712 HEAD `1c0f5a424dd51abc0f1a7dedfb7f8ff1047b3339`: **8/8 SUCCESS**. It reuses verified historical CSVs; rebase after #705/#699 and retain the producer-to-consumer manifest round-trip test.
- #701 HEAD `0dbb1106e98f4c83f2bce79d9fb7dd634087e367`: **6/6 SUCCESS**. It shares the source-rights helper with #699 and must be rebased/revalidated after #699. It retains the 30-primary-completed-forecast gate and rejects legacy XGBoost incumbent evidence.
- #706 HEAD `ab3e7c3c42a7495be3bac0ba493a20cc684bfb1b`: all 7 reported checks SUCCESS; production-pickle diff guard remains separate.
- #704 HEAD `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: all 14 reported dependency/league checks SUCCESS; rebase after the source workflow integration.
- #707 HEAD `3a79d333eb246d92aea88b569c8cb5b4474b9fbd`: CI 8/8 SUCCESS, but **excluded from this V2 recovery path**. Its saved-cohort replay hardcodes a 10-event post-outcome diagnostic from the 2026-09-11 market-only ledger and refits a research candidate from historical inputs. That is not the frozen prospective V2 protocol and conflicts with the current instruction not to open protected 2026/27 outcomes or refit/change the original weights. Do not execute or merge #707 under this scope.
- #711 remains the overlapping draft alternative to #712; do not merge both. HUMAN-MERGE only.

### Fresh strict pre-match state and scientific status

A new read-only aggregate against `public.odds_snapshots` selected only quote/kickoff timestamps and event IDs:
- 3,966 total rows;
- 3,915 satisfy strict `snapshot_time_utc < commence_time_utc`;
- 0 strict pre-match rows in the last seven days;
- 0 future events with a saved strict pre-match quote;
- latest strict pre-match quote: `2026-10-13 14:48:53.042620 UTC`.

No result, score, goal, or settlement columns were selected. Main Original Forward run [#41670482076](https://github.com/MaksimBlud/football-ai/actions/runs/41670482076) still reports zero quotes and zero forecasts; Current-Form Forward [#41672409582](https://github.com/MaksimBlud/football-ai/actions/runs/41672409582) reports zero quotes and zero shadow captures. No new source/quote pair exists.

The original candidate remains SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features, 20x2 weights, 3,799 training rows, `active_lambda=0`, `shadow_lambda=1`, stability gate FAILED. Candidate JSON and protocol blobs are identical between main and the #699 branch. Eligible completed prospective forecasts remain **0/30**; Brier and LogLoss are not available, and no V2-over-market claim is justified.

The rights manifest remains conditional personal/academic research inference only, not a provider-issued AI-inference licence; AI training, commercial use and public product publication remain disallowed. The provider's current fair-use page is updated 03/11/26 and limits automated free-data sessions to twice per week: [Football-Data fair data usage policy](https://football-data.co.uk/contact.php). No new public CSV download was initiated.

HUMAN-MERGE only. No merge, main mutation, production `.pkl` change, Supabase write/DDL, paid API call, source download, target-outcome read, refit, threshold tuning, promotion, bet, schedule change, or other-agent setting change occurred.


---

## 2026-11-04 05:02 UTC — rights gate added before original source-archive attestation

Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc` (last main commit 2026-10-18 08:20:05 UTC). This iteration changed only the existing research branch for PR #699 and this continuity-document branch; no main update or merge occurred.

### New PR #699 hardening — exact-head CI PASS

PR #699 now points to exact HEAD `e2d8da77039a19a26a2bec31832ed49e75aa24f7`, three commits ahead of prior HEAD `f15ff20d7626e2b54ad921bf48bb29493239589c`, zero commits behind main.

The original source-attestation entry point `serie_a_v2_attest_real_source.py` previously discovered and downloaded the GitHub historical-source artifact before the separate forward-capture script applied the personal/academic research-scope guard. It now calls `require_personal_research_inference_scope()` immediately after repository-scope validation and before reading `GITHUB_TOKEN`, discovering artifacts, verifying parent runs, or downloading/extracting the archive. If the scope check fails, it writes the explicit `SOURCE_RIGHTS_BLOCKED_NO_NETWORK_NO_INFERENCE` report and returns without archive access.

New regressions:
- `test_main_blocks_before_github_archive_discovery_when_research_scope_is_denied` proves the entry point writes a blocked report and never calls archive discovery/download when the scope check denies use.
- `test_live_v2_entrypoints_check_research_scope_before_external_reads` now includes the original source-attestation entry point and verifies the rights guard precedes token/archive access.

Exact-head GitHub Actions on `e2d8da77039a19a26a2bec31832ed49e75aa24f7`: **7/7 SUCCESS**:
- Original V2 Frozen Shadow Tests [#41776554362](https://github.com/MaksimBlud/football-ai/actions/runs/41776554362) — SUCCESS, **308 passed**.
- Research PR Validation [#41776554283](https://github.com/MaksimBlud/football-ai/actions/runs/41776554283) — SUCCESS; final production `.pkl` diff guard printed `PASS: no .pkl changes in PR`.
- Serie A [#41776554202](https://github.com/MaksimBlud/football-ai/actions/runs/41776554202) — SUCCESS.
- Bundesliga [#41776554189](https://github.com/MaksimBlud/football-ai/actions/runs/41776554189) — SUCCESS.
- Ligue 1 [#41776554188](https://github.com/MaksimBlud/football-ai/actions/runs/41776554188) — SUCCESS.
- Product [#41776554186](https://github.com/MaksimBlud/football-ai/actions/runs/41776554186) — SUCCESS.
- Eredivisie [#41776554171](https://github.com/MaksimBlud/football-ai/actions/runs/41776554171) — SUCCESS.

The three-file diff from the previous #699 HEAD is limited to the original source-attestation entry point and its two regression files. No candidate, 19-feature contract, weights, lambdas, workflow schedule, or production artifact changed. PR #699 remains open for HUMAN-MERGE.

### Fresh main-only runtime and read-only pre-match state

Actual main runs were re-read from GitHub Actions logs:
- Source Capture [#41640753996](https://github.com/MaksimBlud/football-ai/actions/runs/41640753996): SUCCESS, 19 tests; candidate SHA verified; 98 identity-gate fixtures, 100 completed current-season CSV rows, ten historical CSVs, 11 source files, zero paid calls and zero Supabase writes. Artifact #13231843819; ZIP SHA-256 `4e6fb5531a2206a353fe00fa1ebb0b4d20b3c6ae41ab49a7c672f8dab6d29cd8`.
- Current-Form Forward [#41640881317](https://github.com/MaksimBlud/football-ai/actions/runs/41640881317): SUCCESS, 53 tests; exact source artifact and parent verified at 33 seconds of source age, but `quotes_seen=0`, `v2_current_form_shadow_captured=0`; no target outcomes read/scored.
- Free Real-Quote Diagnostic [#41650074683](https://github.com/MaksimBlud/football-ai/actions/runs/41650074683): SUCCESS, 53 tests; `quoted_fixtures=0`, `diagnostic_scored=0`; no paid calls or Supabase writes.
- Original Forward [#41670482076](https://github.com/MaksimBlud/football-ai/actions/runs/41670482076): SUCCESS, 71 tests; `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`; no target outcomes read/scored.
- Current-Form Forward [#41672409582](https://github.com/MaksimBlud/football-ai/actions/runs/41672409582): SUCCESS, 53 tests; source artifact verified but age was 11,616 seconds, `quotes_seen=0`, `v2_current_form_shadow_captured=0`; no target outcomes read/scored.

Read-only Supabase:
- `odds_snapshots`: 3,966 total; 3,915 with `snapshot_time_utc < commence_time_utc`; zero strict pre-match rows in the last seven days; zero future events with a strict pre-match quote; latest strict pre-match snapshot `2026-10-13T14:48:53.042620Z`.
- Serie A 2026/27 identity-only query selected only `match_date, home_team, away_team`: 103 raw rows, 100 canonical fixture identities after the frozen Atalanta alias normalization, latest identity date 2026-11-02. No score/result/settlement fields were selected.
- These 100 current identities do not make the old main archive eligible: artifact #13231843819 has the pre-#699 numeric gate only (98) and lacks the new digest-bound identity-set attestation. A fresh post-#699 source archive is required; do not backfill or infer a forecast from the old artifact.

### Remaining integration and source-download guard

- PR #705 remains open at `8b139335e6722b7c4f5286962486bca84bced20d`, exact CI **8/8 SUCCESS**. Its 170-hour-per-workflow shared budget and offline-only push behavior are not active on main.
- Main's unchanged schedules are next due 2026-11-04 05:50 UTC (Current-Form Source Capture) and 06:13 UTC (Free Real-Quote Diagnostic). If #705 is not manually merged first, those workflows are not protected by its new marker budget.
- #705 bootstraps from Nov 3 artifacts: Source Capture #13231843819 created 13:02:59 UTC → next budget slot 2026-11-10 15:02:59 UTC; Diagnostic #13236383688 created 14:05:06 UTC → next slot 2026-11-10 16:05:06 UTC. The unchanged daily cron times next fall after both slots on Nov 11.
- The rate budget is not a data-use licence. The source-rights manifest remains conditional personal/academic research inference, explicitly not a provider-issued AI-inference licence; AI training, commercial use and public product use remain disallowed. No new public Football-Data download was initiated in this iteration.

Integration order remains HUMAN-MERGE: #705 first; rebase and merge #699 after it with exact-head CI; then #704 if desired; then rebase/retest #712. #702 requires a fresh post-#699 identity-attested source archive and remains manual-only. #701 remains the separate 30-eligible-completed-forecast evaluator. Do not merge overlapping #700/#703/#709/#711 independently where their changes are already consolidated or superseded.

No merge, main mutation, Supabase write/DDL, paid provider request, source download, production `.pkl` change, target-outcome read, model refit, threshold tuning, promotion, or schedule change occurred. The original candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features and frozen weights remain unchanged; active lambda remains 0 and shadow lambda 1 research-only. The prospective evaluation cohort remains 0/30; no Brier/LogLoss result exists.

---

## 2026-11-04 04:01 UTC — independently reconstructed gate-time identity SHA

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This is a read-only evidence reconstruction plus a documentation-only update on this PR branch; no main mutation occurred.

### Source artifact and identity-only reconstruction

Downloaded the actual GitHub artifact #13231843819 from Source Capture run #41640753996 and independently recomputed the ZIP SHA-256:

- ZIP SHA-256: `4e6fb5531a2206a353fe00fa1ebb0b4d20b3c6ae41ab49a7c672f8dab6d29cd8` (matches GitHub artifact digest).
- Current-season CSV SHA-256: `4138a4f01e96312a7a5dc07450c7a520c3861a479620fe3d102f12d42a6678ba` (matches the manifest and recomputed bytes).
- The manifest's identity-only feature gate ran at `2026-11-03T13:02:46.498639Z` and recorded 98 canonical completed primary identities. It separately recorded 100 completed prior-day CSV rows; these are different counts and must not be conflated.

I parsed only the CSV identity columns `Date, HomeTeam, AwayTeam` (no FTR, goals, score, or result fields). There are 100 pre-gate-day identity rows and 100 unique canonical identities. Their sorted identity-set SHA-256 is `f85872547e745eae8854ee245902c1e522657fb3a687032be83b000199f2a99e`.

A retrospective, identity-only Supabase reconstruction using only `match_date, home_team, away_team, persisted_at_utc`, with `persisted_at_utc <= 2026-11-03T13:02:46.498639Z`, returns 101 raw rows, 98 canonical identities, and SHA-256 `08ba05a619ed01139cd89970a0780f212f66342cb8a2f8d9606dab1a15127745`. Removing the two CSV identities that were persisted after that gate time yields exactly the same 98-identity count and SHA-256.

Those two rows were persisted later on 2026-11-03:
- `2026-11-02 Atalanta — Parma`: `19:25:30.287934Z`.
- `2026-11-02 Sassuolo — Fiorentina`: `19:25:30.690599Z`.

The current Supabase identity set now contains 103 raw rows / 100 canonical identities and has SHA-256 `f85872547e745eae8854ee245902c1e522657fb3a687032be83b000199f2a99e`, matching the 100-identity CSV set. This resolves the 98-versus-100 count difference: the two additional fixtures were in the CSV but were not yet persisted in Supabase when the source gate ran.

Important limitation: main's original manifest did not preserve the gate identity list or its SHA at capture time. The above is a retrospective reconstruction from persistence timestamps, not a contemporaneous identity attestation. PR #699 remains necessary: its source-capture path records the gate identity list/SHA, the source identity list/SHA, covered/missing counts, and fails if any gate identity is missing. It deliberately permits extra source identities while proving complete coverage of the gate set.

No protected outcome columns were selected from Supabase. No CSV result/statistics columns were read in this identity comparison.

### Fresh strict pre-match quote audit

The read-only `odds_snapshots` query used only rows satisfying `snapshot_time_utc < commence_time_utc`:

- 3,915 strict pre-match rows / 327 distinct events across the stored leagues.
- Zero strict pre-match rows in the last seven days.
- Zero future events with a strict pre-match quote.
- Latest strict Serie A quote: `2026-10-13 14:48:53.042620Z`.
- `product_prediction_snapshots`: 40 rows, all `EPL_AI_MARKET_PAIR_V1`; zero original V2 candidate-SHA snapshots.

The real main Original Forward run #41670482076 and Current-Form Forward run #41672409582 still report zero quotes and zero V2 shadow captures. The prospective outcome gate remains 0/30; no target outcomes were read.

### Exact-head PR state and integration constraints

Exact current PR heads were re-read with their associated GitHub Actions runs:

- #705 `8b139335e6722b7c4f5286962486bca84bced20d`: 8/8 SUCCESS. It is the first HUMAN-MERGE priority because the 170-hour source-download budget and offline push validation are not yet on main.
- #706 `caab7c07ad720866616ce9fa62664b0d398e5fe0`: 6/6 SUCCESS.
- #699 `f15ff20d7626e2b54ad921bf48bb29493239589c`: 7/7 SUCCESS; adds a regression test for 31 source identities against 30 gate identities, proving all gate identities are covered while extra source identities remain allowed.
- #701 `268885f437379a1610c0c56abb883cf7963f9d9c`: 6/6 SUCCESS; its market-only evaluator preserves the same 30-event lazy outcome gate and does not require an unpinned incumbent.
- #702 `3935fc601eff30d2ca0a7670dae797d0cb365228`: 7/7 SUCCESS.
- #712 `1c0f5a424dd51abc0f1a7dedfb7f8ff1047b3339`: 8/8 SUCCESS; retain after #699/#704 dependency review and rebase.

PR #709 duplicates the offline push-validation change already present in #705 and should not be merged separately. PR #711 remains a draft alternative that overlaps #712; do not merge both.

No new source download was initiated. No paid-provider request, Supabase write/DDL, target-outcome read, production `.pkl` change, model/weight/feature-contract change, schedule change, or merge occurred. The only write in this iteration is this continuity-document commit on PR #697's existing branch.

## 2026-11-03 17:55 UTC — latest main V2 runs and corrected identity reconciliation

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This is a read-only audit plus a documentation update on this PR branch; no main mutation occurred.

### New main-only runtime evidence

- Current-Form Source Capture [run #41640753996](https://github.com/MaksimBlud/football-ai/actions/runs/41640753996) SUCCESS. Artifact #13231843819, 438,212 bytes, GitHub ZIP SHA-256 `4e6fb5531a2206a353fe00fa1ebb0b4d20b3c6ae41ab49a7c672f8dab6d29cd8`. The report records the frozen candidate SHA, 10 historical CSVs / 3,800 historical rows, 100 completed prior-day current-season rows, 98 canonical feature-input identities, 11 source files, zero paid-provider calls, zero Supabase writes, and no target-outcome scoring.
- Current-Form Forward [run #41640881317](https://github.com/MaksimBlud/football-ai/actions/runs/41640881317) SUCCESS. It verified the exact source artifact and successful main parent: source observed 13:02:58.382703Z, archive created 13:02:59Z, parent completed 13:03:01Z, verification 13:03:31Z (33 seconds after observation). Source provenance passed, but `quotes_seen=0` and `v2_current_form_shadow_captured=0`. Artifact #13232322438 SHA-256 `c93efaaa1b505bf6a5fe372e1cc9c4f4d44f060d9c144b824ac31c9a99452ce9`.
- Free Real-Quote Diagnostic [run #41650074683](https://github.com/MaksimBlud/football-ai/actions/runs/41650074683) SUCCESS: 53 tests, 3,800 historical rows, 19 frozen features, 10 public CSV requests, but `quoted_fixtures=0` and `diagnostic_scored=0`. Artifact #13236383688 SHA-256 `8386044e795e208e112e9af8d9ebcb0d5a77cf8f00f51147c70df8d01785c143`.
- Original Forward [run #41670482076](https://github.com/MaksimBlud/football-ai/actions/runs/41670482076) SUCCESS: 71 tests, real historical source attestation passed, but `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`. Artifact #13248390793 SHA-256 `712895e8167ea0ca5db4b1039bb42f36ed1182ca55cc19f75138286366755fba`.
- Current-Form Forward [run #41672409582](https://github.com/MaksimBlud/football-ai/actions/runs/41672409582) SUCCESS: 53 tests; verified source artifact #13231843819 and candidate SHA, source age 11,616 seconds at verification, but again `quotes_seen=0` and `v2_current_form_shadow_captured=0`. Its artifact #13249097138 SHA-256 `45c0b1e8729bc733807ee46ad9bb5f68036a0ac7bfaf90c904b6e8a14f9bbb97`.

The successful source/parent chain is real, but there is no actual quote to pair with it. Therefore there is still no genuine source-before-quote forecast observation and no model-quality evidence.

### Correction: 101 raw identities versus 98 canonical identities

The earlier 17:01 note described the raw/canonical count difference as unresolved. That was incorrect. A fresh identity-only query selected only `match_date, home_team, away_team` and returned 101 raw rows. The V2 source-capture code canonicalizes `Atalanta BC → Atalanta`; three duplicate fixture identities collapse:

- 2026-08-23: Atalanta / Sassuolo and Atalanta BC / Sassuolo.
- 2026-08-31: Atalanta / Bologna and Atalanta BC / Bologna.
- 2026-09-05: AS Roma / Atalanta and AS Roma / Atalanta BC.

After that frozen alias normalization, the 101 raw rows produce 98 unique canonical identities, matching the Source Capture's 98-event feature-input gate. This is not a three-event shortfall. However, main's current manifest still does not carry a digest-bound exact identity set; PR #699 adds that stronger parity proof. No score, goals, result, or settlement columns were selected.

### Fresh read-only pre-match Supabase audit

- `odds_snapshots`: 3,966 rows; 3,915 satisfy strict `snapshot_time_utc < commence_time_utc`; 327 distinct events; zero strict pre-match rows in the last seven days; zero future events with a strict pre-match quote. Latest strict Serie A quote: 2026-10-13 14:48:53.042620Z.
- `product_prediction_snapshots`: 40 rows; zero rows with frozen V2 candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; latest generated record 2026-10-09 15:29:33Z.
- `league_finished_results` identity-only Serie A 2026/27 metadata: 101 raw rows, 98 canonical identities, 2026-08-22 through 2026-11-01. No outcomes were selected.

The 30-eligible-completed-forecast evaluation gate remains 0/30 and CLOSED. PR #701's market-only path keeps the outcome loader lazy and does not require an incumbent; the full three-way path remains blocked until a separately frozen incumbent is pinned. No Brier/LogLoss values exist.

### Current PR and source-use state

- #705 HEAD `8b139335e6722b7c4f5286962486bca84bced20d`: exact-head CI 8/8 SUCCESS. It applies 170 hours per approved source-workflow path (at most two sessions per rolling week), keeps existing cron expressions, and makes push validation offline. It is not merged, so the guard is not active on main. If it remains unmerged, the next unchanged main schedules are 2026-11-04 05:50 UTC (Current-Form Source Capture) and 06:13 UTC (Free Real-Quote Diagnostic). Manual merge is required to activate the budget.
- #699 HEAD `fecf8dd01ad6ea3b9eabd0dfb31167f397ae4e3a`: exact-head CI 7/7 SUCCESS; rebase after #705 before manual merge.
- #712 HEAD `331e7934f92763d8df2c6c35e01b6b26a80bcf5d`: exact-head CI 9/9 SUCCESS; overlaps source-capture files and depends on the #699 identity-attested producer, so rebase/review after #699. #711 is an overlapping draft alternative; do not merge both.
- #701 HEAD `04233460becc99dcbac0beb83a4e105bb8d64e3c`: exact-head CI 6/6 SUCCESS; no live forecasts exist to evaluate.
- #707 HEAD `dfbeed39507fea3cff3c46ef6c64bc25461385a6`: exact-head CI 7/7 SUCCESS; its explicit rights gate blocks AI model-training recovery without written/open-license evidence. It does not itself grant AI inference rights.

The official Football-Data fair-use policy states that free CSV/Excel data are intended for private personal betting or academic research, limits light automated downloading to twice weekly, and excludes commercial/AI data-training use absent permission: https://football-data.co.uk/contact.php. The 170-hour budget is a frequency guard, not a licence. No new public-source request was initiated by this audit; the already scheduled Nov 3 main runs above are recorded as historical evidence. Do not initiate further live downloads until the intended AI use is confirmed as permitted or appropriate rights are obtained.

HUMAN-MERGE only. No PR was merged; main, original weights, 19-feature contract, schedules, production `.pkl`, and Supabase schema/data were not changed. No paid provider calls, Supabase writes/DDL, protected outcome reads, refit, threshold tuning, promotion, or betting action occurred.

## 2026-11-03 17:01 UTC — Original V2 live audit, current gate drift, and push-trigger isolation

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The main copy of this file is still stale at its 2026-10-18 top entry; this PR carries the current continuity update.

### Frozen candidate and real main workflows

- The original `MARKET_ANCHOR_1X2_V2` candidate remains present on main: artifact SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; exact frozen feature list has 19 entries; `active_lambda=0`, `shadow_residual_lambda=1`, `stability_gate_passed=false`, `research_only=true`, `automatic_promotion=false`. No weights or feature definitions changed.
- Main Source Capture #41640753996 SUCCESS created artifact #13231843819 at 2026-11-03 13:02:59 UTC. ZIP SHA-256: `4e6fb5531a2206a353fe00fa1ebb0b4d20b3c6ae41ab49a7c672f8dab6d29cd8`. The run manifest reports 10 historical CSVs / 3,800 historical rows, 100 completed current-season CSV rows, and a 98-identity feature-input gate. Paid calls and Supabase writes: 0.
- Main Original Forward #41670482076 SUCCESS (2026-11-03 16:04 UTC): source attestation verified ten historical files / 3,800 rows; `quotes_seen=0`, forecasts 0, no target-outcome reads/scoring, paid calls 0, Supabase writes 0.
- Main Current-Form Forward #41672409582 SUCCESS (2026-11-03 16:16 UTC): 53 tests passed; verified the exact Source Capture artifact and candidate SHA; `quotes_seen=0`, `v2_current_form_shadow_captured=0`, no target-outcome reads/scoring, paid calls 0, Supabase writes 0. This verifies the source archive path, not model quality.

### Fresh read-only Supabase metadata

- Strict pre-match `odds_snapshots` (`snapshot_time_utc < commence_time_utc`): 3,915 rows / 327 distinct events; latest pre-match snapshot 2026-10-13 14:48:53 UTC; zero future events with a strict pre-match quote.
- `product_prediction_snapshots`: 40 pre-match rows, all `EPL_AI_MARKET_PAIR_V1`; zero rows with the original V2 candidate SHA.
- Identity-only `league_finished_results` query for `league='SERIE_A'`, `season='2026-2027'`, `match_date < current_date`, selecting/counting only fixture identities: 101 unique identities, 2026-08-22 through 2026-11-01. No score/result fields were selected.
- The Nov 3 source archive records a 98-identity gate, while the live metadata-only gate is now 101. The old main forward reader verified archive provenance/age but did not prove current identity-set parity. No protected 2026/27 source CSV member was opened to investigate the three-identity difference.

### New #699 exact-head safeguards

PR #699 current HEAD: `fecf8dd01ad6ea3b9eabd0dfb31167f397ae4e3a`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, exact CI **7/7 SUCCESS**. Original V2 shadow job: **289 tests passed**, production `.pkl` no-change guard passed.

- Current-Form Forward Preview now accepts a Source Capture `workflow_run` parent only for `schedule` or `workflow_dispatch`; offline push validation cannot fan out into the secret-bearing forward reader.
- Current-Form Source Capture live job now accepts only direct `schedule` / `workflow_dispatch` or a successful main Free Real-Quote Diagnostic whose parent event was `schedule` / `workflow_dispatch`; push is excluded.
- Diagnostic-triggered source reuse rereads current identity-only gate rows, passes `current_gate_identities` to archive verification, and requires both `fresh_for_new_quote` and `fresh_for_current_feature_gate`. Target outcomes remain unread.
- The new checks are static workflow-contract tests; the model, 19 features, weights, lambdas, gate threshold, and cron expressions are unchanged.

### Integration order and blockers

- PR #705 exact HEAD `8b139335e6722b7c4f5286962486bca84bced20d`: **8/8 SUCCESS**, mergeable, HUMAN-MERGE only. It adds the shared two-per-rolling-week public-source budget (170 hours per approved workflow path), bootstrap from the actual Nov 3 artifacts, and offline-only push validation. Merge #705 first; then rebase #699 and rerun exact-head CI. The Nov 3 source/diagnostic sessions happened before the guard is active on main.
- PR #712 exact HEAD `331e7934f92763d8df2c6c35e01b6b26a80bcf5d`: **9/9 SUCCESS**, offline/mock-only historical source reuse. Rebase only after #705/#699 integration and a normal post-#699 source capture with the identity-set SHA. #711 is a draft overlapping alternative; do not merge both. #709's push isolation is already present in #705; do not merge #709 separately.
- The official Football-Data fair-use page says free files are intended for private personal betting/academic research, allows at most light automated downloads twice weekly, and excludes commercial/data-training AI use. Intended AI-inference rights are not established by the rate limit. No new live Football-Data download was manually initiated; do not treat #705's 170-hour budget as a licence. Confirm permitted use or obtain rights before further live capture.
- Prospective evaluator #701 remains separate from the 98/101 feature-input gate: the 30-primary-completed-forecast outcome gate is still CLOSED at 0/30. No Brier/LogLoss comparison or superiority claim is available.

No main merge, Supabase writes/DDL, paid API calls, production `.pkl` changes, outcome reads, schedule changes, or other-agent changes occurred. HUMAN-MERGE remains mandatory.


## 2026-11-03 15:23 UTC — fresh main source archive verified; no saved quotes; V2 cohort still empty

Audit against unchanged main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The scheduled main workflows were read from GitHub Actions; no manual workflow dispatch, paid odds request, Supabase write/DDL, production artifact change, or target-outcome query was initiated by this audit.

### New main-only source and forward evidence

- Current-Form Source Capture [run #41640753996](https://github.com/MaksimBlud/football-ai/actions/runs/41640753996) completed SUCCESS at 2026-11-03 13:03:01Z on main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`. It passed 19 source-capture/feature-manifest tests and reported candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 98 identity-gate events, 100 completed prior-day current-season CSV rows, 10 historical-season files, 11 source files total, `feature_source_gate_passed=true`, `paid_provider_calls=0`, `supabase_writes=0`, and `target_outcomes_scored=false`. Artifact #13231843819 is 438,212 bytes; GitHub ZIP SHA-256 `4e6fb5531a2206a353fe00fa1ebb0b4d20b3c6ae41ab49a7c672f8dab6d29cd8`.
- Current-Form Forward [run #41640881317](https://github.com/MaksimBlud/football-ai/actions/runs/41640881317) completed SUCCESS at 13:03:39Z. It independently verified source artifact #13231843819 against the successful main parent run #41640753996: exact ZIP SHA above, 98 identity-gate fixtures, 100 current-season history rows, 3,900 historical rows, source observed at 13:02:58.382703Z, archive created at 13:02:59Z, parent completed at 13:03:01Z, source age 33 seconds at verification, `fresh_for_new_quote=true`, and `status=VERIFIED`. However, `quotes_seen=0` and `v2_current_form_shadow_captured=0`; all blocked counters were zero. Target outcomes remained unread/unscored, paid calls 0, production/Supabase writes 0. Forward artifact #13232322438 is 439,372 bytes; ZIP SHA-256 `c93efaaa1b505bf6a5fe372e1cc9c4f4d44f060d9c144b824ac31c9a99452ce9`.
- Free Real-Quote Diagnostic [run #41650074683](https://github.com/MaksimBlud/football-ai/actions/runs/41650074683) completed SUCCESS at 14:05:09Z. It passed 53 tests, processed 3,800 historical rows and 19 frozen features, but had `quoted_fixtures=0`, `diagnostic_scored=0`, `feature_rows_with_all_19_observed=0`, `public_http_requests=10`, `paid_provider_requests=0`, `supabase_writes=0`, and zero source-observed-after-quote violations. Artifact #13236383688 is 425,071 bytes; ZIP SHA-256 `8386044e795e208e112e9af8d9ebcb0d5a77cf8f00f51147c70df8d01785c143`.

The new source archive is a real successful main artifact and its parent-before-quote chain is independently verified by the forward workflow. This is a source-pipeline proof, not a prediction-quality result: there were no saved quotes, no forward shadow forecasts, and no outcome reads.

### Fresh read-only Supabase pre-match audit

Only pre-match quote timestamps, fixture IDs, kickoff timestamps, model SHA, and prediction capture timestamps were selected. No result/score columns or target outcomes were queried.

- `odds_snapshots`: 3,966 total; 3,915 satisfy strict `snapshot_time_utc < commence_time_utc`; zero strict pre-match rows in the last seven days; latest strict pre-match quote remains 2026-10-13 14:48:53Z; zero future events have a strict pre-match quote.
- `product_prediction_snapshots`: 40 rows total; zero use the frozen original V2 candidate SHA; zero original-candidate pre-match rows. All 40 rows are pre-match records for other model SHA values.
- Prospective original V2 eligible forecasts remain 0/30. The protected outcome gate remains CLOSED; no target outcomes were read or scored.

### Download-budget bootstrap update

The two scheduled public-source workflows also ran again on main on 2026-11-03. Their newest legacy artifacts are now Source Capture #13231843819 (created 13:02:59Z) and Free Diagnostic #13236383688 (created 14:05:06Z). PR #705's dynamic legacy-artifact bootstrap should therefore use these timestamps—not the Nov 2 artifacts previously listed—and, at 170 hours per workflow path, the next allowed times are 2026-11-10 15:02:59Z and 16:05:06Z respectively. The current main workflows ran before that guard is integrated; HUMAN-MERGE is still required. The provider policy allows at most light automated downloading twice per week, while the current wording does not specify whether a session or each file is counted. Do not treat the rate guard as a data-use licence.

### Integration state

- Main remains unchanged at `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- #705 remains HUMAN-MERGE only at exact HEAD `8b139335e6722b7c4f5286962486bca84bced20d`; the refreshed bootstrap test now separately proves both Nov 3 main-artifact slots (22 tests), and all 8 exact-head CI checks are SUCCESS. The current slots are Nov 10 15:02:59Z (Source Capture) and 16:05:06Z (Free Diagnostic).
- #699 must still be rebased after #705; #712 remains dependent on the identity-attested producer/consumer integration and must not reuse this pre-identity-attestation main artifact.
- #701's market-only evaluator still requires 30 unique eligible completed prospective forecasts before its lazy outcome loader can run. Current cohort is 0/30.
- Original frozen V2 candidate, 19 features, original weights, `active_lambda=0`, and `shadow_residual_lambda=1` remain unchanged.

---

## 2026-11-02 18:56 UTC — latest main-only V2 forward runs; zero quotes; recovery source-code mismatch

Audit against unchanged main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No workflow was dispatched. Only read-only GitHub Actions metadata/logs and pre-match Supabase data were inspected; no target outcomes, scores, goals, settlements, or result columns were queried.

### New main-only runtime evidence

- Current-Form Source Capture [run #41456825300](https://github.com/MaksimBlud/football-ai/actions/runs/41456825300) SUCCESS; artifact `13147815874`, size 437,965 bytes, ZIP SHA-256 `67cd15e2e6319196eb13e83b4b65059302c0256b718e876756567efec81614f3`. The run reported 10 frozen historical CSVs / 3,800 rows, one 2026/27 CSV with 98 completed prior-day rows through 2026-11-01, and feature-input gate count 90. The archive was created at 13:53:57Z; source observation was 13:53:55.657Z.
- Current-Form Forward [run #41500098611](https://github.com/MaksimBlud/football-ai/actions/runs/41500098611) SUCCESS on the same main SHA; 53 tests passed. It verified source artifact #13147815874 and parent run #41456825300, with source age 16,205 seconds at verification. `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes read/scored false, paid calls 0, Supabase writes 0. Its report artifact is #13168611787, ZIP SHA-256 `d553efb56a9f937ce2d8b922f2055bcad8f77367bf22790467fa62e58f5ad507`.
- Original Forward [run #41498178161](https://github.com/MaksimBlud/football-ai/actions/runs/41498178161) SUCCESS; 71 tests passed. It attested historical-only diagnostic artifact #13155539394 and reported `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, paid calls 0 and Supabase writes 0. Its output artifact #13166733478 has digest `a095fd8d3352e441592f47d4382bafa7e828210232a00a948c6e4142810e295e`.
- Free Real-Quote Diagnostic [run #41473879081](https://github.com/MaksimBlud/football-ai/actions/runs/41473879081) SUCCESS; 53 tests passed, but report mode was `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`. Artifact #13155539394 has GitHub digest `a2c5e7a6e35faeea4829342c732625292bea2ef897c7ec24f18b41eb40a335b5`.

### Fresh read-only Supabase pre-match/identity audit

- `public.odds_snapshots`: 3,966 rows; 3,915 satisfy strict `snapshot_time_utc < commence_time_utc`; zero strictly pre-match rows in the last seven days; zero future events with a strictly pre-match quote. Latest Serie A strict pre-match snapshot remains 2026-10-13 14:48:53 UTC.
- The metadata-only Serie A 2026/27 query selected only `match_date, home_team, away_team`: 93 raw/exact fixture identity rows through 2026-10-29. The Source Capture's frozen feature-input gate reported 90 after its V2-local canonicalization; this is not a quality/evaluation gate.
- `product_prediction_snapshots` has zero rows with frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- No target outcomes were selected.

### Recovery compatibility blocker

The latest Free Diagnostic artifact #13155539394 is ZIP-integrity verified, but its parent run #41473879081 used main's pre-#699 `serie_a_v2_live_diagnostic_report.py` blob `fae3698769f857fbcb6c8d3ea7826eb81135fec4`. PR #707's recovery contract requires the integrated #699 loader blob `932e58a4f93b0d471ac4b4e0c81fa01f923e46d5`. Therefore the existing artifact must remain rejected for candidate recovery despite its correct ZIP/member hashes. Do not bypass this source-code provenance check. Recovery remains pending #705 manual merge, #699 rebase/manual merge, a fresh post-#699 main diagnostic artifact, then the main-only recovery path.

### Open-PR reconciliation

- #705 current HEAD `e368326ad52f728f1c3975989aa7a60de2be50c3`: exact-head CI 8/8 SUCCESS. Its current code uses a **170-hour cooldown per approved workflow path**, not an 85-hour global cooldown; only two workflow paths are allowlisted, so the guard permits at most two sessions per rolling 168 hours. The Source Capture push path already runs offline validation only, making #709 functionally superseded; a clarification was added to #709. #705 remains HUMAN-MERGE only.
- #699 `5a1d1bda1c62d36fd092d9e9018a7d2d923e4513`: 7/7 CI SUCCESS, but must be rebased after #705 and rerun exact-head CI.
- #701 `04233460becc99dcbac0beb83a4e105bb8d64e3c`: 6/6 CI SUCCESS. Its separate market-vs-shadow evaluator uses the frozen 30-eligible-completed-forecast gate and lazy outcome loading; it remains unusable for live quality metrics until eligible prospective forecasts exist.
- #702 `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`: 7/7 CI SUCCESS, manual-only; requires #699 and a fresh identity-attested source archive. Its current-source completeness caveat remains.
- #707 `cdc93ca0aab9dc75434238bec75ea8759d77ffbd`: 7/7 CI SUCCESS; actual recovery has not been run.
- #704 `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: exact-head checks successful on its current base, but workflow overlap requires rebase after #699/#705.
- #706 `28104a5b943b697d581d578e133585701a395c43`: 6/6 CI SUCCESS; preserve its fail-closed production-`.pkl` diff guard when integrating evaluator CI.

### Scientific and safety state

Original candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features and weights unchanged; `active_lambda=0`, `shadow_lambda=1`, NO_BET. Feature-input gate is 90, but prospective forecasts remain zero and the separate 30-primary-completed-forecast outcome gate is CLOSED. No new Brier/LogLoss exists; no V2-over-market claim is justified. No PR was merged, main was not changed, Supabase remained read-only, production `.pkl` was not touched, and no paid provider call or protected outcome read occurred.

The Football-Data twice-weekly automated-download guidance remains a source-use blocker, not a license grant. The cap limits workflow sessions, not CSV files per session; whether the provider counts individual CSV files separately and whether its terms authorize this model-training use remain unresolved. Do not initiate additional manual source downloads.

---

## 2026-11-02 04:54 UTC — Football-Data publication freshness and fair-use audit; V2 evaluator bridge rechecked

Read-only review against unchanged main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No GitHub workflow was dispatched, no public CSV was downloaded, and no Supabase write/DDL or target-outcome query was performed.

### Correction to the 90-vs-93 current-form source discrepancy

The official Football-Data all-data page and Italy-specific page both report **Last updated: 29/10/26**:
- https://football-data.co.uk/downloadm.php
- https://football-data.co.uk/italym.php

This explains the prior comparison: Supabase and the current Football-Data CSV contain 90 canonical Serie A 2026/27 identities through 2026-10-29, while the secondary fixture index reports three further completed fixtures dated 2026-10-31. The discrepancy is therefore consistent with the provider's publication lag; it is **not evidence that the CSV is corrupted or incomplete relative to the provider's 2026-10-29 release**. It does mean the current-form input is not current through 2026-10-31 and must not be described as such.

The source manifest's `source_observed_at_utc` records when the CSV was fetched, not the provider page's last-publication date. A fresh archive timestamp can therefore coexist with several-day-old source content. Preserve the frozen 24-hour source/quote rule; do not silently redefine it. A separate descriptive provider-publication date and latest fixture date should be recorded in a future source-manifest change, without changing the 19 features, weights, or eligibility thresholds.

### Provider fair-use constraint — new acquisition blocker

Football-Data's own contact/fair-use page states that its free files are intended for private/academic research and that automated downloads should be light, with a maximum frequency of **twice per week**; it also disclaims use for commercial or automated AI/data-training products without permission:
- https://football-data.co.uk/contact.php

Current main schedules are daily:
- Current-Form Source Capture: `50 5 * * *` UTC; downloads ten frozen historical CSVs plus current-season `2627/I1.csv`.
- Free Real-Quote Diagnostic: `13 6 * * *` UTC; downloads the ten historical CSVs again.

This is not only a schedule-level concern; the configured runs actually executed on 2026-11-01:
- Source Capture #41304706414 completed SUCCESS and logged `source_file_count=11` (ten frozen historical CSVs plus current-season CSV); its source job reported 19 tests passed.
- Free Real-Quote Diagnostic #41310276961 completed SUCCESS and logged `public_http_requests=10`, `paid_provider_requests=0`, and 53 tests passed.
- Current-Form Forward #41319862002 then logged `quotes_seen=0` and `v2_current_form_shadow_captured=0`; it read no target outcomes and made no Supabase writes.

If both scheduled workflows execute, the current design therefore requests 21 CSV downloads per day from this provider, far above its published twice-weekly automated-download guidance. This is a material source-use/compliance blocker, not a model-performance issue. No manual dispatch or extra source download was made in this audit. Do not add further manual fetches. Before relying on this pipeline for continued research, add a tested provider-compliant reuse/conditional-fetch guard (or obtain explicit permission); keep the existing cron expressions unchanged unless the owner separately authorizes a schedule change. Any guard must fail closed and must not relabel cached old bytes as newly observed content.

### Fresh Supabase pre-match/identity audit

Read-only queries selected only fixture identity and timestamp metadata from the current-season result table, and aggregate pre-match quote timestamps from odds:
- Serie A 2026/27: **93 raw rows**, **90 canonical identities** after the frozen V2-local `Atalanta BC → Atalanta` alias; three raw alias rows; latest fixture date **2026-10-29**; latest persistence **2026-10-30 05:33:49 UTC**; all 93 rows have NULL `source_updated_at_utc`.
- `odds_snapshots`: **3,966** total; **3,915** satisfy strict `snapshot_time_utc < commence_time_utc`; zero strict pre-match rows in the last seven days; zero future events with a saved strict pre-match quote. Latest Serie A strict pre-match quote remains **2026-10-13 14:48:53 UTC**.
- `public.matches`: zero future fixture metadata rows.
- Original V2 candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`: zero matching rows in `product_prediction_snapshots`.

No scores, goals, H/D/A outcomes, settlements, or protected target-outcome columns were selected.

### Exact PR/code reconciliation

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- #699 remains open at `5a1d1bda1c62d36fd092d9e9018a7d2d923e4513`, **7/7 exact-head CI SUCCESS**. Direct branch inspection confirms its current code already has the core #700 public-source protections: exact HTTPS host/path allowlist, redirects disabled, exact final-URL check, bounded streamed CSV reads and response close. #700's redirect-only change is therefore superseded by the more complete #699 branch; do not merge #700 as a duplicate.
- #699 also already streams and caps both current-form and original GitHub artifact ZIP reads. #703 adds defensive handling for missing/malformed headers and further negative tests; retain only those unique cases after #699 is merged/rebased, not its stale overlapping file versions.
- #701 is open at `c3c3f4150c9c5475636441bbf50209d1f5c05d7a`, **6/6 exact-head CI SUCCESS**. Its market-only evaluator reads completed fixture identities first, then invokes the exact-result loader only when at least **30 unique eligible completed prospective forecasts** exist. The supplementary market-only path always returns `review_signal=false`; the full three-way evaluator remains blocked because no permitted frozen incumbent SHA is pinned. This is not a live quality result.
- #702 is open at `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`, **7/7 exact-head CI SUCCESS**, manual-only, and depends on #699 plus a new identity-attested source archive. Its one documented `/events` request is intended to be zero-credit and checks `x-requests-last: 0`; no such request was made here.
- #697 documentation update is being extended with this audit only; HUMAN-MERGE remains required.

### Scientific state

No new pre-kickoff odds, no eligible original V2 prospective forecasts, and no outcomes were read. The 30-primary-completed-forecast outcome gate remains CLOSED; no new Brier/LogLoss exists. Frozen candidate, 19-feature contract, weights, `active_lambda=0`, `shadow_lambda=1`, NO_BET, and all production artifacts remain unchanged.

## 2026-11-02 02:56 UTC — current-form source freshness cross-check; Supabase identity set may lag

Read-only audit against unchanged main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No workflow was dispatched or rerun in this audit.

### Exact original-V2 runtime state on main

- Current-Form Source Capture [run #41304706414](https://github.com/MaksimBlud/football-ai/actions/runs/41304706414) completed 2026-11-01 12:05:19Z. Artifact **13082408243**, ZIP SHA-256 `09fd39e2e7371f6db887963b5da85e4bb3bb6008314cc97b2a31eabf41d115fe`, 11 CSVs, 3,800 frozen old-season rows and **90** current-season completed rows. The source observation was 12:05:13Z. This is the main-era V1 manifest, not the new #699 identity-attested manifest.
- Its workflow_run child, Current-Form Forward [run #41304789997](https://github.com/MaksimBlud/football-ai/actions/runs/41304789997), completed 12:06:04Z: 53 tests passed; source artifact and parent were verified; `quotes_seen=0`, `v2_current_form_shadow_captured=0`, no target outcomes read, no paid calls, no Supabase writes.
- Later scheduled Current-Form Forward [run #41319862002](https://github.com/MaksimBlud/football-ai/actions/runs/41319862002) also completed SUCCESS, but again saw zero quotes and zero shadow captures. Original Forward [run #41318729126](https://github.com/MaksimBlud/football-ai/actions/runs/41318729126) completed SUCCESS with 71 tests, zero saved quotes and zero forecasts. Free Real-Quote Diagnostic [run #41310276961](https://github.com/MaksimBlud/football-ai/actions/runs/41310276961) completed SUCCESS with 53 tests and public-source-only requests; it made zero paid-provider requests and recorded no Supabase writes.

### Read-only Supabase pre-match/identity metadata

The Serie A 2026/27 query selected only `match_date,home_team,away_team` plus source/persistence timestamps; no score, goal, result, or settlement columns were selected:

- 93 raw rows; 90 canonical fixture identities after the V2-local `Atalanta BC → Atalanta` alias.
- Latest identity date: **2026-10-29**.
- `source_updated_at_utc` is NULL for all 93 rows.
- Latest `persisted_at_utc`: **2026-10-30 05:33:49 UTC**; zero rows persisted in the last 24 hours.
- `odds_snapshots`: 3,966 rows / 3,915 strictly pre-match (`snapshot_time_utc < commence_time_utc)); latest snapshot **2026-10-13 14:48:53 UTC**; zero future events with a strictly pre-match quote and zero fresh future pre-match rows in the last 24 hours.
- `product_prediction_snapshots`: 40 rows total; zero rows carry the frozen original V2 candidate SHA.

### Independent public completeness discrepancy (not admitted as model input)

A secondary public Serie A index reports **93 completed matches through 2026-10-31**, with its page updated 2026-11-01 07:15 ET ([StatsNext](https://statsnext.com/serie-a)); another public match index lists three completed Matchday-10 fixtures dated 2026-10-31 ([GioScore](https://gioscore.com/football/tournament/italy/serie-a/384)). These are only a cross-check, not approved V2 feature sources or an authoritative canonical identity feed. No scorelines from these pages are used here.

This differs from the 90 canonical identities through 2026-10-29 in the current Football-Data archive/Supabase metadata. It is a **source-completeness discrepancy requiring a fresh capture and independent fixture-identity audit**, not proof of the exact missing rows. The Nov 1 12:05Z source capture preceded the StatsNext page's reported 07:15 ET (12:15Z UTC) update by about ten minutes; the existing archive should not be treated as current at the 2026-11-02 audit.

### Implication for PR #699 and next proof

PR #699's new identity SHA proves that the current CSV covers the identities read from Supabase; its code deliberately rejects missing gate identities but permits a CSV superset. It does **not**, by itself, prove that Supabase's gate identity set is complete against an independent fixture schedule. The PR remains useful for source-before-quote, identity, SHA, UTC-clock, URL and outcome guards, but no model-quality or source-completeness claim should rely on the 90-row parity alone.

After HUMAN-MERGE of #699, the next scheduled/free source capture must be checked for its current CSV row count, full source identity set, gate identity count/SHA, and raw/member SHA values. If the source now contains additional completed fixtures, preserve the full source set and document the independent identity reconciliation; do not change the frozen 19 features/weights or evaluation gate. A real forecast still requires a new strictly pre-kickoff saved quote. The 30-completed-prospective-forecast evaluation gate remains CLOSED.

No main change/merge, production `.pkl` change, Supabase write/DDL, paid request, protected target-outcome scoring, bet, promotion, or schedule/agent-setting change occurred.

---

## 2026-11-01 22:58 UTC — exact evaluator-head refresh and alternate pre-match source audit

Read-only refresh against unchanged main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no source capture or quote workflow was dispatched in this audit.

### Additional existing-source feasibility

Only pre-match timestamp and fixture metadata fields were queried:
- `public.odds_snapshots`: 3,966 total / 3,915 strictly pre-match (`snapshot_time_utc < commence_time_utc`); zero future strict pre-match rows. Latest Serie A quote remains 2026-10-13 14:48:53 UTC.
- `public.league_multi_market_snapshots`: 2 rows, both strictly pre-match; latest 2026-09-06 03:09:57 UTC; zero future strict pre-match rows.
- `public.league_h2h_bookmaker_snapshots`: 0 rows.
- `public.matches`: 0 fixture-metadata rows dated on/after 2026-11-01.

These alternative existing tables do not provide a fresh fixture/quote source for original V2. No score, result, settlement, or protected target-outcome column was selected.

### Exact current evaluator PR state

PR #701 advanced beyond the earlier documented HEAD `74322b4f4df331657dcc3fddd66a9867b5033570`. Current exact HEAD is `86f4710eb11b2ea881ba6a2d6364ad8b889d2eb8`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The two-commit delta adds a regression test rejecting conflicting H/D/A labels across raw Atalanta / Atalanta BC aliases for the same gated fixture; evaluator logic and frozen model contract are unchanged.

All six workflows associated with exact HEAD `86f4710...` completed SUCCESS: Research #41309990641, Serie A #41309990727, Bundesliga #41309990581, Ligue 1 #41309990518, Eredivisie #41309990722, Product #41309990544. The Research log confirms 79 evaluator tests, 6 live-runner tests, and `PASS: no .pkl changes in PR`. PR #701's description was updated to record this exact SHA/CI. These are synthetic/regression checks only; no live target outcomes or Brier/LogLoss were read/computed.

### Binding execution state

- PR #699 remains open at exact HEAD `5a1d1bda1c62d36fd092d9e9018a7d2d923e4513`; all 7 exact-head required checks are SUCCESS. It carries the source/clock/identity/outcome guards and main-ref guards for secret-bearing V2 workflows. HUMAN-MERGE only.
- PR #702 remains manual-only and blocked until #699 is manually merged, a fresh source capture is produced on resulting main, and #702 itself is reviewed/merged before dispatch.
- PRs #700, #703, and #704 retain overlapping workflow/source files and must be rebased/reconciled after #699; preserve only unique strict Content-Length / streamed-chunk regressions from #700/#703 and rerun exact-head CI. Do not merge stale bases.
- No future saved Serie A odds, no eligible prospective V2 forecast, and the 30-completed-prospective-forecast outcome gate remains CLOSED.

No PR was merged; main, production `.pkl`, original 19 features/weights/lambdas, Supabase, schedules, and other agents were not changed. No paid API call, Supabase write/DDL, target-outcome read, bet, or promotion occurred.

---
## 2026-11-01 18:54 UTC — fresh pre-match data and security audit; no prospective quote

This is a read-only refresh against unchanged `main` **40887ebb215730190d7a6c7a1693373ec4afcdfc**. It adds no new model/runtime claim.

### Verified Actions artifacts

- Current-form Source Capture run **41304706414**: SUCCESS on main; artifact **13082408243**, 437,021 bytes, GitHub digest `sha256:09fd39e2e7371f6db887963b5da85e4bb3bb6008314cc97b2a31eabf41d115fe`.
- Current-form Forward run **41319862002**: SUCCESS on main; artifact **13089345402**, 438,202 bytes, digest `sha256:0511879f1a3e425ee97326158bb366912e771d2084653d010f7926ac15251a02`. Its actual output was `quotes_seen=0`, `v2_current_form_shadow_captured=0`, no rows, no target-outcome reads/scoring, no paid calls, no Supabase writes, `no_bet=true`; 53 tests passed.
- Original old-season Forward run **41318729126**: SUCCESS on main; artifact **13088352792**, 1,459 bytes, digest `sha256:fb2331e0fbb7a19c3979277814762935a7be0098caf34c149c13c154279c0c11`; 71 tests passed. This is source-checked diagnostic evidence, not a prospective forecast.
- These are the last specific run artifacts independently inspected in this audit. Do not infer that a new quote or a new prediction exists from a successful workflow alone.

### Read-only Supabase pre-match audit

All odds queries apply the strict predicate `snapshot_time_utc < commence_time_utc`; no outcome columns were selected.

- Across nine leagues: **3,966** odds snapshots, **3,915** strictly pre-match; **0** strictly pre-match snapshots in the last seven days; **0** future events with a saved strictly pre-match quote.
- `SERIE_A`: **625** total snapshots, **620** strictly pre-match; latest strict pre-match snapshot remains **2026-10-13 14:48:53 UTC**.
- `league_structural_v2_observations`: **630** Serie A observations across **63** events; all 630 satisfy the strict pre-match timestamp condition; latest snapshot is also **2026-10-13 14:48:53 UTC**.
- Serie A 2026-2027 feature-input metadata query selected only `match_date, home_team, away_team`: **93** raw rows, **90** unique identities after the frozen V2-local `Atalanta BC → Atalanta` alias (3 alias rows), latest date **2026-10-29**. This is only the feature-input gate, never the 30-forecast outcome gate.
- `product_prediction_snapshots` contains **40** pre-kickoff EPL rows for `EPL_AI_MARKET_PAIR_V1`; no original Serie A V2 incumbent is present.

No protected 2026/27 target outcomes were selected or read.

### Workflow and PR safety state

- Main's `serie-a-v2-forward-preview.yml` and `serie-a-v2-current-form-forward-preview.yml` currently lack a job-level `github.ref == 'refs/heads/main'` guard for manual dispatch. The main current-form source-capture and free-diagnostic workflows also lack that guard.
- PR **#699**, exact HEAD `5a1d1bda1c62d36fd092d9e9018a7d2d923e4513`, adds main-ref guards to all four secret-bearing V2 workflows and broadens frozen-dependency triggers. Its exact-head CI is **7/7 SUCCESS**, including **286 Frozen V2 Shadow tests** and the production `*.pkl` diff guard. It remains open; HUMAN-MERGE only.
- PR **#697**, exact HEAD `22764eaaca2a942cb1e555ecb3ab0690a242eba8`, has **7/7 SUCCESS** and remains documentation-only.
- PRs **#700**, **#703**, and **#698** remain open with successful CI on their current heads, but overlap files changed by #699. Rebase and compare after #699 is manually merged; do not merge stale bases or duplicate overlapping changes.
- PR **#701** has 6/6 successful runs on its current HEAD; #702 has 7/7. #702's live fixture preview remains blocked until #699 is manually merged, a fresh post-merge source artifact is captured, and #702 itself is manually merged and dispatched.
- No PR was merged and main was not changed.

### Separate Supabase security finding

Security Advisor observed at **2026-11-01 18:54 UTC**:
- ERROR: RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`.
- INFO: RLS enabled but no policies on `public.competitions`, `public.match_stats`, `public.matches`, and `public.standings`.

No DDL or policy change was attempted. Enabling RLS without correctly scoped policies could break the application; this remains a separate owner-controlled security task.

### Scientific status

The original candidate remains SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 frozen features and weights unchanged, `active_lambda=0`, `shadow_lambda=1` research-only. There are still **0** admissible prospective V2 forecasts and therefore **0/30** eligible completed forecasts. No Brier/LogLoss comparison or superiority claim is permitted.

---

## 2026-11-01 15:11 UTC — second source-verified current-form forward runtime; still no quote

On unchanged main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, the scheduled Current-Form Forward-Only Preview run **#41319862002** completed SUCCESS at 15:11:15 UTC. Its uploaded artifact is **13089345402**, 438,202 bytes, digest `sha256:0511879f1a3e425ee97326158bb366912e771d2084653d010f7926ac15251a02`.

The real job log reports:
- Latest verified current-form source artifact **13082408243**, ZIP SHA-256 `09fd39e2e7371f6db887963b5da85e4bb3bb6008314cc97b2a31eabf41d115fe`, 11 source CSVs, 3,890 total historical/current rows, and **90** canonical feature-input gate identities.
- Original frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original 19-feature contract unchanged.
- Source observation at 12:05:13.677 UTC, source archive at 12:05:15 UTC, authenticated parent run **#41304706414** completed at 12:05:19 UTC. Forward verification at 15:11:06.952 UTC measured source age **11,153 seconds (3h 05m 53s)**, below the fixed 24-hour maximum.
- Forward regression suite: **53 passed**. Actual output: `quotes_seen=0`, `v2_current_form_shadow_captured=0`, no rows, `target_outcomes_read=false`, `target_outcomes_scored=false`, `paid_provider_calls=0`, `supabase_writes=0`, `no_bet=true`.

This is a second real source-artifact/parent verification on main, not a forecast, not a 19-feature vector calculation, and not a source-before-quote observation: no future saved quote existed to test.

The separate Original Forward run **#41318729126** completed SUCCESS at 14:58:02 UTC with **71 tests passed**. It independently attested the free historical artifact **13084892998** from diagnostic parent run **#41310276961**: ten frozen pre-prospective CSVs / 3,800 historical rows, zero quotes checked, zero V2 diagnostic previews, zero paid calls, zero Supabase writes.

Read-only Supabase audit (identity metadata only for the feature gate; odds rows strictly filtered by `snapshot_time_utc < commence_time_utc`):
- Serie A 2026-2027: **93 raw identity rows**, **90** identities after the frozen V2-local `Atalanta BC → Atalanta` alias; latest metadata date 2026-10-29. This is only the feature-input gate, not the prospective outcome gate.
- `odds_snapshots`: 3,966 total / 3,915 strictly pre-kickoff across nine leagues; **zero** strict pre-match snapshots in the last seven days and **zero** future events with saved pre-match quotes. Latest Serie A pre-match snapshot remains 2026-10-13 14:48:53 UTC.
- `league_structural_v2_observations`: Serie A 630 strictly pre-match observations; zero in the last seven days and zero future events.

### Corrected source-integrity overlap audit — 2026-11-01 16:49 UTC

This correction supersedes the merge-order recommendation immediately above. The previous note incorrectly said that PR #699 still followed redirects for the ten historical CSV downloads. A direct read of the #699 branch files at the verified commit below disproves that statement.

Verified PR #699 commit: `58bdb5bfc88f1b33f3e9843b164b8c036306e882`. Its exact-head CI set completed **7/7 SUCCESS**:
- Frozen V2 Shadow #41313954700 — **271 passed**; production `*.pkl` diff guard passed.
- Research #41313954608
- Serie A #41313954674
- Bundesliga #41313954809
- Product #41313954562
- Ligue 1 #41313955074
- Eredivisie #41313954847

The #699 diff already includes these substantive protections:
- Historical Football-Data CSVs: exact approved HTTPS host/path, `allow_redirects=False`, HTTP 200 and exact final URL checks before body consumption, bounded streaming at 5 MB per file / 10 MB aggregate, actual byte checks, and response closure.
- Original and current-form GitHub artifact downloads: streaming, actual archive-size caps, and response cleanup. The current-form reader also validates ZIP member names and aggregate/member uncompressed sizes.
- Current-form source workflow: guarded `workflow_run` after the free diagnostic, restricted to successful main-branch scheduled/manual diagnostic runs; it checks the existing source archive against the current metadata-only fixture identity set and captures a new archive only when freshness or gate coverage fails.

There are, however, smaller unique hardening deltas in the overlapping PRs:
- **#700** adds strict ASCII-decimal `Content-Length` parsing for historical CSVs. #699's historical parser currently uses `int(declared_length)`; it already has the redirect and streaming/aggregate-size guards. The #700 branch also uses a 2 MB per-file cap and lacks #699's 10 MB aggregate cap, so do not merge its older whole-file diff ahead of #699. After #699 is integrated, rebase #700 and retain only the unique strict-header validation/tests if still useful.
- **#703** adds ASCII-only `Content-Length` validation and rejects non-bytes chunks in the GitHub artifact stream readers. #699 already bounds those streams and adds current-form ZIP expansion checks, but the stricter header/chunk-type checks are unique. Rebase #703 after #699 and rerun exact-head CI; do not merge its stale overlapping diff as-is.
- **#704** changes the same workflows for Python dependency locks; rebase it after #699 and rerun exact-head CI. Its pins are version locks, not hash-enforced supply-chain locks.
- **#701** is the separate lazy outcome evaluator; **#702** is the free fixture/19-feature-readiness preview. Review both against the resulting main and their exact tested heads before manual integration.

**Correct HUMAN-MERGE sequence:** #699 first; then rebase/reconcile #700 and #703 to preserve only their unique strict-header/chunk-type regressions; then rebase #704. Re-run all required CI on every resulting exact HEAD. Do not merge any PR automatically. The earlier recommendation to merge #700/#703 before #699 is superseded.

### Main-ref guard audit for secret-bearing forward workflows — 2026-11-01 17:01 UTC

A fresh comparison of the live `main` workflows with the #699 branch found a separate reason not to dispatch these workflows from a feature ref while #699 remains unmerged:

- On current `main`, `.github/workflows/serie-a-v2-forward-preview.yml` has `workflow_dispatch`, a read-only schedule, and a `workflow_run` after the paid `Serie A Odds Snapshots` workflow's manual dispatch. Its job condition restricts the `workflow_run` case to a successful main/manual collector run, but does not independently require `github.ref == 'refs/heads/main'`. The job receives `SUPABASE_URL` and `SUPABASE_KEY`.
- On current `main`, `.github/workflows/serie-a-v2-current-form-forward-preview.yml` likewise has a manual dispatch and read-only schedule plus successful source-capture/manual-collector workflow-run triggers. Its job condition checks the workflow-run provenance but does not independently require the main ref; the job also receives Supabase credentials.
- The #699 branch adds an explicit `github.ref == 'refs/heads/main'` guard to both forward-preview jobs and regression-tests that secret-bearing V2 workflows cannot run from a feature ref. It also constrains the free diagnostic and source-capture job entry points to the intended main-ref/event combinations.

Until #699 is manually merged, **do not dispatch either secret-bearing forward workflow from a feature branch**. Scheduled main runs and the guarded workflow-run paths are distinct from a feature-ref manual dispatch. The paid `Serie A Odds Snapshots` collector remains manual-only; no paid call or cron was introduced by this audit.

This is a current-main security gap, not evidence of a model defect. No workflow was dispatched from a feature ref, no secret was read or exposed, no main change/merge occurred, and no Supabase write/DDL or target-outcome read occurred. HUMAN-MERGE only.

### Independent artifact byte verification and current pre-match audit — 2026-11-01 16:49 UTC

I independently downloaded and rehashed the actual GitHub artifacts:
- Current-form source artifact #13082408243: ZIP SHA-256 `09fd39e2e7371f6db887963b5da85e4bb3bb6008314cc97b2a31eabf41d115fe`, matching the GitHub artifact digest. Its manifest lists 11 CSVs; all 11 raw-file SHA-256 values match. The ten frozen seasons contain 380 rows each; the 2026/27 CSV contains 90 completed prior-day rows. Total: 3,890 CSV rows.
- Current-form forward artifact #13089345402: ZIP SHA-256 `0511879f1a3e425ee97326158bb366912e771d2084653d010f7926ac15251a02`, matching GitHub. Its JSON reports the source artifact as verified and fresh at forward time (11,153 seconds old), but `quotes_seen=0`, `v2_current_form_shadow_captured=0`, no rows, and no target-outcome reads/scoring.
- Original forward artifact #13088352792: ZIP SHA-256 `fb2331e0fbb7a19c3979277814762935a7be0098caf34c149c13c154279c0c11`, matching GitHub. Its JSON reports 71 tests passed in the job log, 3,800 frozen historical rows attested, zero quotes checked and zero forecasts created.

At the current audit time, the 2026/27 source observation `2026-11-01T12:05:13.677283Z` is still within the frozen 24-hour maximum. This does not create a quote-backed vector: no eligible saved future quote exists.

Fresh read-only Supabase queries selected only pre-match odds timing and fixture identity metadata:
- `odds_snapshots`: 3,966 rows; 3,915 satisfy `snapshot_time_utc < commence_time_utc`; zero strict pre-kickoff rows in the last seven days; zero future events with a saved strict pre-kickoff quote. Latest strict pre-kickoff snapshot remains `2026-10-13T14:48:53.042620Z`.
- `league_structural_v2_observations`: Serie A 630 rows / 63 events, all strictly pre-kickoff; zero in the last seven days and zero future events.
- `league_finished_results` feature-input identity query selected only `match_date, home_team, away_team`: 93 raw Serie A 2026/27 rows, 90 canonical identities after the V2-local Atalanta alias. This is the lagged feature-input gate only, not the prospective outcome gate.
- `product_prediction_snapshots`: 40 EPL rows; zero rows with the frozen V2 candidate SHA, zero future original-V2 pre-kickoff rows.

No quote payloads/prices/probabilities or protected target outcomes were selected. No Supabase writes/DDL, paid provider calls, production artifact changes, schedule changes, or main changes occurred. The 30-eligible-completed-prospective-forecast outcome gate remains CLOSED. HUMAN-MERGE only.

## 2026-11-01 12:06 UTC — fresh current-form source and paired forward runtime proof

A new successful run on unchanged main `40887ebb215730190d7a6c7a1693373ec4afcdfc`
provides the first fresh November 1 current-form archive and its paired
source-verified forward run:

- Current-Form Source Capture run **#41304706414** completed SUCCESS at
  12:05:19 UTC; artifact **13082408243**, 437,021 bytes, GitHub digest and
  independently recomputed ZIP SHA-256
  `09fd39e2e7371f6db887963b5da85e4bb3bb6008314cc97b2a31eabf41d115fe`.
- Downloaded the artifact and independently verified all **11/11 CSV
  byte hashes** against the manifest. It contains ten frozen historical
  seasons / **3,800** historical rows and current `2627/I1.csv` /
  **90** completed prior-day rows. The current CSV SHA-256 is
  `32ca618587c90db25f16ea647cb55060f519c03830a1e8ec4a6c4204e27d5135`.
- The manifest records the unchanged candidate SHA
  `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`,
  original feature-builder blob `401b3a0893371bfa4a488ec92a4a54af2678c8f7`,
  19 features, metadata-only input gate (only
  `match_date, home_team, away_team`), 90 completed identities, no same-day
  rows, no paid calls, no Supabase writes, and no target-outcome reads.
- Independent source↔Supabase identity parity was recomputed from the
  downloaded CSV and a separate read-only metadata query. Both produce
  **90 canonical identities** and exact sorted tab/newline SHA-256
  `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`.
  The Supabase query returned 93 raw rows; three Atalanta/Atalanta BC alias
  duplicates collapse under the frozen V2-local alias.
- Paired Current-Form Forward-Only run **#41304789997** completed SUCCESS
  at 12:06:04 UTC; artifact **13082817502**, 438,196 bytes, SHA-256
  `44e054d41f553f84fff8f1ba509f9da2d0cad13c218878ad6b400f558ec458ae`.
  It independently verified source artifact 13082408243 and parent run
  41304706414. Source observation was 12:05:13.677 UTC, archive creation
  12:05:15 UTC, parent completion 12:05:19 UTC, and forward verification
  12:05:59.096 UTC (source age 45 seconds): all source/parent clocks
  precede the forward verification time.
- Forward regression suite: **53 passed**. Real output:
  `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `rows=[]`,
  `eligible_for_current_form_forward_shadow=false`,
  `active_lambda=0`, `shadow_residual_lambda=1`,
  `target_outcomes_read=false`, `paid_provider_calls=0`,
  `production_or_supabase_writes=0`. Thus this is source/runtime proof,
  **not** a forecast or feature-vector calculation: no future fixture
  with a saved eligible pre-kickoff quote was available.

The feature-input gate is satisfied, but the independent 30 eligible
completed prospective-forecast outcome gate remains CLOSED. No 2026/27
target outcomes were read. The 13:14 UTC free diagnostic later produced a
separate historical-only archive; it does not replace this current-form
archive or create quotes.

No model, 19-feature definition, weights, candidate SHA, lambda semantics,
schedule, production artifact, or Supabase data/schema changed. HUMAN-MERGE
only; this documentation update remains on PR #697.

## 2026-11-01 — cross-table pre-kickoff source audit

A final read-only schema/metadata audit checked the other existing Supabase
market/fixture tables so that the absence of quotes is not inferred from
`odds_snapshots` alone. No payloads, prices, probabilities, scores, goals,
results, or settlements were selected.

- `matches`: zero future fixture rows from 2026-11-01 onward across all
  leagues. This table cannot currently supply an upcoming-fixture list.
- `league_h2h_bookmaker_snapshots`: Serie A has 630 rows / 63 events, all
  strictly pre-kickoff, but zero rows in the last 7 days and zero future events
  with a saved strict pre-kickoff snapshot. Latest source snapshot remains
  `2026-10-13T14:48:53.042620Z`; latest persistence time is
  `2026-10-22T12:28:06.802262Z`.
- `league_structural_v2_observations`: Serie A has 630 strictly pre-kickoff
  rows / 63 events, zero in the last 7 days and zero future events. Its latest
  observation is also `2026-10-13T14:48:53.042620Z`. These are structural
  observation rows, not a pinned incumbent artifact or a valid replacement
  comparator for the original MARKET_ANCHOR_1X2_V2.
- `league_multi_market_snapshots`: only two rows, both Eredivisie; no Serie A
  rows.
- The separate `odds_snapshots` audit also reports zero future events with a
  strict pre-kickoff snapshot across all nine leagues.

Therefore there is no hidden alternate Supabase table containing newer
Serie A pre-match quotes or future fixtures. The manual-only free fixture
discovery preview in PR #702 is still the only prepared path to discover
upcoming events; it must wait for a fresh source archive and manual integration
of the source/identity guards. No paid endpoint, cron, or schedule change is
authorized or required.


## 2026-11-01 — lazy exact outcome reader and zero future quotes

### Exact pre-kickoff market availability

A second read-only query used the database's current clock and the strict condition
`snapshot_time_utc < commence_time_utc`. Across all nine tracked leagues,
there are **zero future events with a saved strict pre-kickoff snapshot** and
zero associated rows. This confirms that there is no usable future market
observation waiting in the database for the V2 forward runner.

The prior aggregate remains 3,966 `odds_snapshots` rows / 3,915 strict
pre-kickoff rows. Serie A's last strict pre-kickoff snapshot remains
`2026-10-13T14:48:53.042620Z`. Do not treat a historical pre-kickoff snapshot
for an already-started fixture as a current quote.

### Exact lazy outcome reader added before any prospective outcome access

PR [#701](https://github.com/MaksimBlud/football-ai/pull/701) final HEAD is
`74322b4f4df331657dcc3fddd66a9867b5033570`; exact-head CI is **6/6 SUCCESS**
(Research #41309415355, Serie A #41309415356, Bundesliga #41309415147,
Eredivisie #41309415138, Ligue 1 #41309415184, Product #41309415166).
Research log: 79 evaluator tests, 5 live-runner tests, and
`PASS: no .pkl changes in PR`.

The new `evaluate_live_market_only_from_supabase()` wrapper keeps the outcome
reader lazy behind the unchanged 30-unique-eligible-completed-prospective-
forecast gate. Below 30 it makes zero result-column queries. At/above 30 it
queries only exact fixture identities and selects exactly
`match_date,home_team,away_team,result`; it does not select goal/score fields
or unrelated fixtures. It canonicalizes known aliases and rejects conflicting
duplicate H/D/A labels. The supplementary path compares only the exact
de-vigged market with the frozen lambda-one V2 shadow and always keeps
`review_signal=false`; the original full three-way evaluator remains
unchanged and requires a separately pinned non-legacy incumbent.

All new tests are synthetic regression tests. No target outcome has been read
and the actual prospective cohort still contains **0 eligible completed V2
forecasts**. The 90 completed metadata identities are feature-input history,
not 90 prospective forecasts. The full evaluation gate remains closed.

### No admissible Serie A incumbent

The read-only ledger audit remains unchanged:
- 630 `league_prediction_ledger` rows / 63 Serie A events are `MARKET_ONLY`;
  the source-before-prediction row count is 0.
- `product_prediction_snapshots` contains 40 EPL-only records for
  `EPL_AI_MARKET_PAIR_V1`; no Serie A rows exist.
- `FROZEN_INCUMBENT_REFERENCE=None` remains correct. Do not infer an incumbent
  from market-only ledger rows or import the legacy XGBoost model.

### Superseding current integration order

1. HUMAN-MERGE PR #699 first (exact HEAD `fa10c4c8...`, 7/7 CI); it consolidates
   the source clock, feature-gate clock, exact historical URL/redirect,
   dependency-trigger and bounded artifact-download guards also represented
   by open PRs #680, #683, #686, #698, #700 and #703. Do not merge those
   overlapping branches independently without a new diff review.
2. HUMAN-MERGE PR #701 after #699 (or independently only if its base remains
   clean); it contains the pure 30-event evaluator, supplementary market-only
   diagnostic, and lazy exact Supabase outcome reader.
3. PR #702 remains manual-only and must not be run until a new source archive
   is verified and the source/identity guard integration is present.
4. PR #697 is documentation-only. PR #704's version pins are not hash-enforced
   and its workflow edits overlap #699; reconcile after #699 before merge.

No merge, main change, schedule change, paid provider request, Supabase
write/DDL, production artifact change, or protected target-outcome read.
HUMAN-MERGE remains mandatory.

## 2026-11-01 — exact artifact digest, live identity audit, and market-only evaluator

### Repository and frozen candidate

- Main observed for this audit: `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Original candidate remains `MARKET_ANCHOR_1X2_V2`, SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original feature-builder Git blob remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`; 19-feature order/weights/scaler/imputer unchanged.
- `active_lambda=0` remains the exact de-vigged market; `shadow_residual_lambda=1` remains research-only; NO_BET; no promotion.

### Independently downloaded and re-hashed source artifact

GitHub Actions run [#41196139664](https://github.com/MaksimBlud/football-ai/actions/runs/41196139664) completed successfully and produced artifact `13040356986`, created `2026-10-31T11:16:52Z`, size 437,016 bytes.

The artifact ZIP was downloaded from the GitHub artifact connector and SHA-256 recomputed locally from the exact bytes. The result matches the GitHub artifact metadata digest:

```
feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a
```

This is the authoritative ZIP digest. It supersedes an earlier mis-transcribed ZIP digest ending `...626ade6`; do not use that earlier value as the archive SHA.

The ZIP contains 11 CSVs plus the manifest: 10 historical seasons (380 rows each) and the 2026/27 file (90 rows), 3,890 match rows total. Independently recomputed SHA-256 for all 11 CSVs matches the corresponding `source_files[].csv_sha256` values in the manifest (11/11). The current-season CSV SHA is `32ca618587c90db25f16ea647cb55060f519c03830a1e8ec4a6c4204e27d5135`.

Manifest timing/provenance:
- Current CSV observed: `2026-10-31T11:16:50.931690Z`.
- Archive created: `2026-10-31T11:16:50.986952Z`.
- Successful parent workflow completed: `2026-10-31T11:16:55Z`, run #41196139664, main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Manifest: 90 completed prior-day rows, 10 historical files, 11 source files, 19 features, feature-input gate passed, paid calls 0, Supabase writes 0, target outcomes read/scored false.

At the automation start time `2026-11-01T12:47:42Z`, the verified source observation was 25h30m51s old, beyond the frozen 24-hour maximum. Do not use this archive for a new quote/forecast until a fresh source capture is independently verified. The available Actions evidence does not establish a newer successful source-capture artifact; absence of a verified reference is not proof that no scheduled run occurred.

### Actual forward artifacts — no prospective quote or forecast

[Current-form Forward #41210600837](https://github.com/MaksimBlud/football-ai/actions/runs/41210600837) succeeded and produced artifact `13045987954`, ZIP SHA-256 `32623b30e1ef5a6706db7bc09cc6fd801b408ccfa2b64b911fcde2914d4b64c0`. Its embedded JSON reports `quotes_seen=0`, `rows=[]`, `v2_current_form_shadow_captured=0`, `source_artifacts_used=[]`, `target_outcomes_read=false`, `paid_provider_calls=0`, and `production_or_supabase_writes=0`.

[Original Forward #41210303100](https://github.com/MaksimBlud/football-ai/actions/runs/41210303100) succeeded and produced artifact `13045239180`, ZIP SHA-256 `764060555f19a6d8ea4efc8bd06768bccbeaf77e5846230a8ceb7156b1ed1b02`. Its JSON reports `future_quotes_checked=0`, `quotes_seen=0`, `rows=[]`, `v2_diagnostic_previews_captured=0`, `protected_2026_27_results_read=false`, paid calls 0, Supabase writes 0. The attached old-season source attestation identifies artifact `13042322093`, SHA `8c39e6db1f95727a2d6c62513b68c929bcb8560df2ca329eb735dd8229fa470b`, 10 verified old-season files / 3,800 matches, and no 2026/27 target-result read.

Both workflow artifacts are real successful executions, but neither contains a prospective V2 forecast.

### Read-only Supabase identity and market audit

Only pre-match market metadata and identity-only fixture fields were selected; no goal, score, result, settlement, or target-outcome columns were queried.

For Serie A 2026/27 before 2026-11-01:
- Raw identity metadata rows: 93.
- Canonical unique identities: 90.
- Three duplicate groups are solely the known `Atalanta BC -> Atalanta` alias on 2026-08-23, 2026-08-31, and 2026-09-05.
- Source-capture identity-set SHA-256 (the exact `newline + tab` serialization used by PR #699): `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`.
- Prospective evaluator identity-set SHA-256 (its separate compact-JSON serialization): `09442a8a74c0471e3b6ae161d39cd73e1015fc5d541c994a09134555cc720c93`.
- The exact 90 canonical fixture identities from the CSV match the 90 canonical Supabase metadata identities after applying the runtime/V2 alias map. Both sets independently produce the source-capture tab/newline SHA `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811` and the prospective-evaluator compact-JSON SHA `09442a8a74c0471e3b6ae161d39cd73e1015fc5d541c994a09134555cc720c93`. This is exact set parity, not count-only parity; the new source/identity attestation from PR #699 is still required for future admissibility.

Across nine leagues, `odds_snapshots` has 3,966 rows, 3,915 strictly pre-kickoff rows and zero new strictly pre-kickoff rows since 2026-10-25. Serie A has 625 total / 620 strictly pre-kickoff rows; its latest verified pre-kickoff snapshot is `2026-10-13T14:48:53.042620Z`. No future fixture has a new saved pre-kickoff quote in the queried window.

Incumbent audit:
- `league_prediction_ledger`: 630 Serie A rows across 63 events are `MARKET_ONLY`; all are market snapshots, and `prediction_time_utc < snapshot_time_utc < kickoff_utc` count is 0. This is not a model incumbent.
- `product_prediction_snapshots`: only 40 EPL records for `EPL_AI_MARKET_PAIR_V1`, SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`; no Serie A incumbent rows.
- Therefore `FROZEN_INCUMBENT_REFERENCE` remains `None`; do not invent or import a legacy/XGBoost comparator.

### PR #701 — supplementary market-only diagnostic, exact-head proof

PR [#701](https://github.com/MaksimBlud/football-ai/pull/701) now has final HEAD `78cb2ce71cd87785480e35834db972ca0b96bf05`, exact-head required CI 6/6 SUCCESS (Research #41308672471, Serie A #41308672476, Bundesliga #41308672481, Ligue 1 #41308672508, Product #41308672540, Eredivisie #41308672469).

The existing full three-way `evaluate_after_gate()` remains unchanged and still requires a separately pinned non-legacy incumbent before its outcome callback. A separate `evaluate_market_only_after_gate()` / `evaluate_live_market_only_prospective_cohort()` path now supports the requested market-vs-shadow diagnostic after the **same 30 unique eligible completed prospective forecasts** gate. It scores only the exact de-vigged market and frozen V2 lambda-one shadow, rejects unpinned incumbent evidence, and always returns `review_signal=false`; it cannot promote, publish, bet, or alter the frozen candidate/policy. Below 30 it returns no metrics and does not invoke the outcome callback.

Exact Research log: 79 evaluator tests passed, 3 live-runner tests passed, and `PASS: no .pkl changes in PR`. These are synthetic/regression checks only; no live target outcomes were read and no live Brier/LogLoss has been produced. The 90 metadata identities are feature-input history, not 90 prospective V2 forecasts: the prospective outcome gate remains closed at 0 eligible forecasts.

### Integration state and next actions

- PR #699 remains the first integration candidate; its source/clock/identity guards include the bounded source/archive handling also covered by overlapping #700/#703. Do not merge overlapping duplicates independently without a fresh diff comparison.
- PR #701 contains the evaluator and supplementary market-only path.
- PR #702 remains the manual-only 19-feature readiness preview; do not run it against a stale source archive.
- PR #697 documentation branch is being updated by this entry.
- No PR was merged, no main ref changed, no schedule or other agent was modified, no paid provider call, no Supabase write/DDL, no production `.pkl` change, and no target outcomes were read.

HUMAN-MERGE remains mandatory.

# Football AI — Project Continuity

## 2026-11-01 — Exact-head source/transport guard consolidation and live-data audit

- Main remains exactly `40887ebb215730190d7a6c7a1693373ec4afcdfc`; the latest main commit is still the Oct 18 current-form preregistration. No main mutation or merge occurred.
- PR #699 was extended to exact HEAD `5a1d1bda1c62d36fd092d9e9018a7d2d923e4513`. It now includes strict ASCII-decimal Content-Length validation for historical Football-Data CSV and both original/current-form GitHub artifact ZIP readers, plus explicit rejection of non-`bytes` stream chunks. New malformed-header and non-byte regression cases are included.
- Exact HEAD CI is **7/7 SUCCESS**: Frozen V2 Shadow #41333735544 (**286 passed**, production `.pkl` diff guard PASS), Research #41333735522, Serie A #41333735604, Bundesliga #41333735595, Ligue 1 #41333735538, Eredivisie #41333735548, Product #41333735584. No `.pkl` files changed.
- PR #699 still requires HUMAN-MERGE. Its branch keeps the candidate JSON, original feature-builder Git blob `401b3a0893371bfa4a488ec92a4a54af2678c8f7`, `market_anchor_1x2_v2_shadow.py`, current-form policy and parent protocol byte-identical to main. PR #700/#703 are overlapping guard work; do not merge them separately without a fresh diff.
- Real main runtime on 2026-11-01: Current-Form Source Capture #41304706414 SUCCESS; artifact 13082408243, GitHub digest `09fd39e2e7371f6db887963b5da85e4bb3bb6008314cc97b2a31eabf41d115fe`, 11 CSV (10 frozen historical + 2026/27 current form), 3,800 historical rows + 90 current-season rows, candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. The successful parent run is main SHA `40887ebb...`.
- Current-Form Forward #41319862002 SUCCESS; it independently verified the source artifact and parent, source age 11,153 seconds at verification, but `quotes_seen=0` and `v2_current_form_shadow_captured=0`. It read/scored no target outcomes and made no writes. Original Forward #41318729126 also returned zero quotes/zero previews.
- Free diagnostic #41310276961 SUCCESS but had zero quoted fixtures, zero scored rows and zero feature rows; it therefore does **not** prove a new 19-feature vector was computed for a future event. No paid provider request occurred.
- Read-only Supabase audit at 2026-11-01 17:49:39Z: 3,966 odds snapshots, 3,915 strictly pre-kickoff; zero new in seven days and zero future events with strict pre-kickoff quotes. Latest strict pre-kickoff Serie A snapshot remains 2026-10-13 14:48:53Z. Current-form identity metadata: 93 raw rows, 90 canonical identities after the V2 Atalanta BC alias, through 2026-10-29. The metadata query selected only `match_date,home_team,away_team`.
- No original V2 candidate-SHA rows were found in `product_prediction_snapshots`; `model_artifact_bundles` is empty. The market-only prospective evaluator in #701 remains the allowed pairwise path after 30 eligible completed prospective forecasts; below 30 it must not invoke the outcome loader. The full three-way review remains blocked because no non-legacy incumbent is pinned. No target outcomes were read in this audit.
- Scientific state remains unchanged: original 19 features/weights frozen; active lambda 0 is market, shadow lambda 1 research-only; stability gate failed; no claim of V2 superiority. Outcome-read gate CLOSED at zero eligible prospective forecasts.



## 2026-11-01 03:50 UTC — independently reverified current-form archive and metadata identity parity

Fresh GitHub and Supabase reads still show main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No V2 PR was merged.

**Actual main source artifact re-download and byte verification:**
- Current-Form Source Capture run `41196139664` completed SUCCESS on the exact main SHA; job ran 19 source-gate tests successfully.
- Downloaded artifact `13040356986`: **437,016 bytes**, SHA-256 `feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a`, matching GitHub's artifact digest.
- ZIP contains ten frozen historical-season CSVs, current `serie_a_2627.csv`, and manifest. Recomputed every CSV byte digest: **11/11 match the manifest**.
- Current CSV SHA-256: `32ca618587c90db25f16ea647cb55060f519c03830a1e8ec4a6c4204e27d5135`; 90 completed prior-day rows dated 2026-08-22 through 2026-10-29.
- Independently recomputed canonical identities from the downloaded CSV and a fresh Supabase query that selected only `match_date,home_team,away_team`. Applied the exact Serie A runtime aliases plus V2-local `Atalanta BC → Atalanta`; sorted tab-delimited identity SHA-256 is **`95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811` on both sides**, with **90/90 identities** and matching date range. No score/result/settlement column was selected or inspected.
- The source run recorded observation at 11:16:50.931690 UTC, uploaded the archive at 11:16:52 UTC, and completed at 11:16:55 UTC. The later current-form forward run `41210600837` verified this exact source artifact and successful parent on main at 14:33 UTC. Its artifact `13045987954` digest is `32623b30e1ef5a6706db7bc09cc6fd801b408ccfa2b64b911fcde2914d4b64c0`; report: 53 tests passed, source VERIFIED, age 11,770 seconds, 90 feature-input identities, **0 quotes seen and 0 shadow previews**. This proves source-before-forward and artifact integrity, not a source-before-quote forecast because no quote was available.
- The old-main manifest records the 90-event count but does not persist the full identity list/SHA. PR #699 adds that durable attestation and exact source coverage check; its new contract has not yet run on main. Independently observed parity does not substitute for post-merge runtime proof.

**Fresh pre-match-only database check:** Serie A `odds_snapshots` = 625 total, 620 strictly pre-kickoff, 5 at/after kickoff, 0 in the last seven days, and 0 future events with a saved strictly pre-kickoff quote. Latest pre-kickoff snapshot remains 2026-10-13 14:48:53.042620 UTC. `league_prediction_ledger` has 630 rows, all 630 strictly before kickoff, across 63 event identities; latest timestamp is the same. No target outcomes were read.

**Binding gates remain separate:** feature-input metadata gate = 90/30, passed; prospective target-outcome evaluation gate = CLOSED, eligible completed prospective forecasts = 0; non-legacy frozen incumbent = unpinned; Brier/LogLoss and superiority claims unavailable. Original candidate SHA, 19 features/weights, `active_lambda=0`, and research-only `shadow_lambda=1` remain unchanged.

**Next safe order:** HUMAN-MERGE #699 at its exact tested HEAD; verify fresh main and a new source artifact with persisted identity list/count/SHA. Then rebase/retest #694's per-quote current-gate freshness guard and #703/#704. Keep #702 main-only/manual-only until the new post-#699 archive is verified. No manual workflow dispatch was made from the old main.

No main mutation or merge, paid request, Supabase write/DDL, production `.pkl` change, model/feature/weight/lambda change, target-outcome read, or schedule/other-agent-setting change occurred.

## 2026-11-01 02:56 UTC — exact-head V2 refresh; no new admissible quote

Fresh GitHub reads confirm `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no V2 PR has been merged. This entry refreshes exact open-PR heads and real main-run evidence without changing the frozen model or either gate.

**Open V2 PRs and exact-head CI:**
- #699 `fa10c4c8ce3971c3da965e07c28af867f3a3abb3`: 7/7 required checks SUCCESS; Original V2 Shadow run #41258862831 = **263 passed**; production `git diff --exit-code -- '*.pkl'` passed. This remains the first HUMAN-MERGE dependency.
- #703 `f12abfd3a8fc37fb3aff6d394ec3966bc1311b51`: 7/7 SUCCESS; Shadow run #41254780590 = **105 passed**; production `.pkl` diff guard passed. It is a stricter follow-up to the streamed readers (ASCII/decimal Content-Length validation, bytes-only chunks, early stop and cleanup); rebase and rerun after #699, do not merge against the stale base.
- #701 `fcbdae8a603ecad799065469d78e9deb390adb4a`: 6/6 SUCCESS; evaluator-specific suite **74 passed**. `FROZEN_INCUMBENT_REFERENCE` remains unpinned, so the evaluator must remain fail-closed.
- #702 `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`: 7/7 returned required checks SUCCESS; manual fixture/feature preview suite **22 passed**. It remains main-only/manual-only and must not be dispatched until #699 is merged and a fresh post-merge Source Capture proves the persisted identity contract.
- #704 `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: 7 distinct required check names succeeded in both recorded check sets; pinned Python 3.11 and 3.12 Original V2 suites each report **87 passed**. Rebase and rerun after #699.
- #697 documentation branch before this refresh: `19cfb3f5c955e3f68952ad1c7b85d3030c9ce155`, 7/7 SUCCESS.

**Latest real Original V2 main workflows (all on old main SHA above):**
- Current-Form Source Capture #41196139664: SUCCESS, 19 tests passed; artifact #13040356986, ZIP SHA-256 `feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a`. Its old-main manifest still has count-only gate evidence, not the persisted identity-list/SHA contract from #699.
- Original Forward-Only #41210303100: SUCCESS, 71 tests passed; `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`.
- Current-Form Forward-Only #41210600837: SUCCESS, 53 tests passed; source archive and parent verified, feature-input count 90, `quotes_seen=0`, `v2_current_form_shadow_captured=0`.
- Free Real-Quote Diagnostic #41200476529: SUCCESS, 53 tests passed; no admissible quote or scored forecast. No paid provider request or Supabase write occurred.

**Fresh read-only pre-kickoff odds check:** Serie A `odds_snapshots` = 625 total, 620 strictly before kickoff, 5 at/after kickoff, zero strict pre-kickoff snapshots in the last 24 hours or 7 days, zero future events with a strict pre-kickoff quote; latest strict pre-kickoff snapshot remains `2026-10-13T14:48:53.042620Z`. This run did not query score/result/settlement columns. The last independent source-to-gate identity parity proof remains 90/90 with SHA-256 `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811` (31-Oct audit); it is not post-#699 runtime proof.

**Scientific state:** original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features and weights unchanged; `active_lambda=0` remains market, `shadow_lambda=1` research-only. Feature-input gate last verified at 90 and passed; eligible prospective forecasts remain 0; the separate 30-eligible-completed-forecast outcome gate remains CLOSED; no frozen non-legacy incumbent is registered; Brier/LogLoss and any superiority claim remain unavailable. No target outcomes were read.

**Next:** HUMAN-MERGE #699 at its exact SHA; then verify the new main, run a fresh Source Capture and independently check persisted gate identities/count/SHA. Only after that, rebase #703/#704 and separately HUMAN-MERGE #702 before any manual zero-credit `/events` probe. Do not use paid odds, old XGBoost, synthetic quotes, outcome peeks, or a gate/protocol change.

No main mutation, merge, Supabase write/DDL, paid request, production `.pkl` change, model/feature/weight/lambda change, schedule change, or other-agent setting change occurred in this audit.

## 2026-10-31 19:48 UTC — corrected PR overlap audit and fresh pre-match database check

A fresh GitHub/Supabase pass confirms main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no V2 PR was merged. The exact main Original Forward workflow still has no `github.ref == 'refs/heads/main'` condition on its job-level `if` for `workflow_dispatch`. Do not dispatch that workflow from a feature branch. PR #699 contains the missing main-ref guard in Original Forward and the current-form source/forward workflows; it remains the first HUMAN-MERGE dependency.

**Correction to the 18:53 overlap note above:** exact source comparison shows PR #703 is **not a duplicate** of #699. Main's original `serie_a_v2_forward_capture.get_archive()` eagerly reads `response.content`. PR #699 changes both original/current-form readers to streaming, applies a declared-length check, caps decoded chunks, and closes the response. PR #703 then adds independent stricter validation to both readers: robust header access, integer Content-Length parsing with negative-value rejection, explicit bytes-only chunk validation, and 12 additional offline regressions (including early stop and response cleanup). PR #703 exact HEAD `e7362b83d1112ce52172d722c7f9decc3e69586e` has **7/7** exact-head checks SUCCESS; its dedicated Original V2 Shadow Tests run #41187160599 reports **99 passed**, and `git diff --exit-code -- '*.pkl'` passed. Keep #703 open as a genuine follow-up; after #699 is manually merged, rebase #703 onto resulting main and rerun exact-head CI. Do not drop or independently merge it against the stale base.

The overlapping source-URL changes in #683/#700 are present in #699: the integration branch pins the exact approved historical/current-season HTTPS endpoints, disables redirects before reading, and verifies the final response URL. #698's current-form trigger/path-filter changes overlap the #699 workflow/test contract; re-check its residual diff after #699 rather than stacking it blindly. PR #704 remains an independent dependency-lock change (two Python lock files plus a contract test), but its five workflow edits overlap #699 and require rebase plus fresh exact-head CI after #699. PR #701 evaluator and #702 manual fixture preview remain independent scopes.

Exact-head status re-read:
- #699 `53b7b184005e8516bfff8c1483e5ab9a4c41e73e`: **7/7 SUCCESS**, dedicated frozen V2 suite **257 passed**.
- #697 before this documentation correction: `33172119d00e1a1de47e509ca20b3c5fdb2468b6`, **7/7 SUCCESS**.
- #701 `fcbdae8a603ecad799065469d78e9deb390adb4a`: **6/6 SUCCESS**, evaluator suite **74 passed**, incumbent remains unpinned/fail-closed.
- #702 `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`: **7/7 SUCCESS**, 22 offline fixture/feature tests.
- #703 `e7362b83d1112ce52172d722c7f9decc3e69586e`: **7/7 SUCCESS**, 99 frozen-V2 tests.
- #704 `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: all **8 distinct required check names** succeeded (two complete check sets are present in the API response); rebase/CI still required after #699.

Fresh read-only Supabase check at approximately 2026-10-31 19:48 UTC selected only pre-match timestamps, kickoff metadata, model provenance metadata, and completed-fixture identities:
- `odds_snapshots` for `SERIE_A`: 625 total, 620 strictly pre-kickoff, 0 future strictly pre-kickoff, 0 strictly pre-kickoff in the last 7 days; latest snapshot remains `2026-10-13T14:48:53.042620Z`.
- `league_prediction_ledger` for `SERIE_A`: 630 rows, all 630 `MARKET_ONLY` and strictly pre-kickoff, 0 future pre-kickoff; latest timestamp unchanged at `2026-10-13T14:48:53.042620Z`.
- `public.matches` contains 0 future Serie A fixture identities.
- `product_prediction_snapshots` contains only 40 strictly pre-kickoff EPL `EPL_AI_MARKET_PAIR_V1` rows; no Serie A incumbent.
- The identity-only 2026/27 completed metadata query returns 93 raw rows and 93 raw distinct tuples; after the exact V2-local `Atalanta BC → Atalanta` canonicalization this is 90 unique primary identities, from 2026-08-22 through 2026-10-29. No score/result columns were selected.

No new pre-match quote, future Serie A fixture identity, or eligible prospective forecast appeared. The actual 31-Oct source/original-forward/current-form-forward runs and their verified artifact digests are already recorded in the 16:53 UTC section below; this check does not create new runtime proof. Frozen candidate SHA, original 19 features/weights, `active_lambda=0`, `shadow_lambda=1`, NO_BET and both gates remain unchanged. No target outcomes, paid provider calls, Supabase writes/DDL, production `.pkl` changes, main mutation, merge, or schedule change occurred. HUMAN-MERGE only.

---

## 2026-10-31 18:53 UTC — exact integration-branch audit and duplicate-PR map

Fresh GitHub read confirms `main` is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main change or PR merge occurred. The Original Forward workflow on main still lacks a job-level `github.ref == 'refs/heads/main'` guard for `workflow_dispatch`. Do not dispatch it from a feature branch. The integration branch in PR #699 adds that guard; the same main-ref guard is present in its current-form source-capture and current-form forward workflows.

A code-level review of PR #699 branch HEAD `53b7b184005e8516bfff8c1483e5ab9a4c41e73e` confirms that it is an integration superset for several previously separate source-integrity changes:

- Current-form source capture verifies the exact frozen candidate before querying/downloading, uses the approved current-season HTTPS URL with redirects disabled, streams under the existing byte cap, checks real UTC offsets and gate → source-observation → archive time order, and persists the sorted gate identity list/count/SHA plus current-CSV identity count/SHA and full gate coverage.
- Historical Football-Data source capture disables redirects, requires the exact approved final URL before reading bytes, streams with bounded per-file/total byte limits, and closes responses on failure.
- Both original and current-form forward readers stream GitHub artifact ZIPs, validate declared Content-Length and actual decoded chunk totals against their existing caps, stop on overflow, and close responses.
- The exact #699 branch contains negative regressions for redirected historical URLs and for declared/streamed artifact overflow, including early-stop and response-close behavior.

This means the code/test scope of open PR #683 (historical source URL redirect attestation) and PR #703 (bounded GitHub artifact downloads) is already present in #699's current integration branch. Do not merge #683 or #703 independently on top of the same main base; after #699 is manually merged, re-check their diffs and close/retire any remaining duplicate scope rather than applying it twice. PR #704's two dependency lock files and dependency-lock contract test are not in #699's changed-file set and remain a separate follow-up requiring rebase and exact-head CI after #699. PR #701 evaluator and #702 manual fixture preview are separate scopes.

Exact #699 head CI was re-read from GitHub check-runs: **7/7 completed SUCCESS** on `53b7b184005e8516bfff8c1483e5ab9a4c41e73e`; its dedicated Original V2 Shadow Tests run #41194794442 reports **257 passed**, including the production `*.pkl` diff guard. PR remains open/mergeable and HUMAN-MERGE only. This is branch evidence, not main/runtime proof.

Fresh read-only pre-match Supabase audit at 2026-10-31 18:53 UTC:
- `odds_snapshots`: all nine stored leagues have zero future strictly pre-kickoff snapshots and zero strictly pre-kickoff snapshots in the preceding seven days. Serie A remains 625 total / 620 strictly pre-kickoff; latest is `2026-10-13T14:48:53.042620Z`.
- `league_prediction_ledger`: 630 Serie A rows, all `MARKET_ONLY` and strictly pre-kickoff; latest timestamp is unchanged at `2026-10-13T14:48:53.042620Z`.
- `product_prediction_snapshots`: only 40 EPL `EPL_AI_MARKET_PAIR_V1` rows; no Serie A incumbent.
- `model_artifact_bundles`: zero registered bundles.

The actual 31-Oct Current-Form Forward artifact #13045987954 was downloaded again and independently rehashed: outer ZIP SHA-256 `32623b30e1ef5a6706db7bc09cc6fd801b408ccfa2b64b911fcde2914d4b64c0`; nested source ZIP #13040356986 SHA-256 `feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a`. Its report confirms zero quotes/zero shadows and no target-outcome reads. The nested old-main manifest remains schema `SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1` without persisted gate identity SHA; it is not the post-#699 runtime proof. Current-season CSV metadata-only rows remain 90 completed identities through 2026-10-29 and contain no future fixture identities.

No model feature, weight, candidate SHA, lambda, gate, production artifact, schedule, Supabase data/schema, or other agent was changed. No paid provider calls or protected target outcomes were accessed.

---

## 2026-10-31 — current free Serie A source contains completed history but no future fixture identities

Independently downloaded the actual GitHub Actions artifact from Current-Form Source Capture run [#41196139664](https://github.com/MaksimBlud/football-ai/actions/runs/41196139664), artifact `13040356986`. The 437,016-byte ZIP SHA-256 recomputed from the downloaded bytes is `feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a`, matching the GitHub artifact digest. The current member `serie_a_2627.csv` is 42,883 bytes with SHA-256 `32ca618587c90db25f16ea647cb55060f519c03830a1e8ec4a6c4204e27d5135`.

For the fixture-availability check, inspected only the CSV identity columns `Date`, `HomeTeam`, and `AwayTeam`; no score/result/settlement columns were accessed. The member contains **90 identity rows**, from 2026-08-22 through 2026-10-29, and **zero same-day or future fixture identities on/after 2026-10-31**. The manifest reports 90 completed prior-day rows, zero incomplete/same-day rows, the identity-only feature-input gate passed at 90 (minimum 30), source observation `2026-10-31T11:16:50.931690Z`, and archive creation `2026-10-31T11:16:50.986952Z`. It still uses the old-main schema `SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1` and does not persist the new #699 gate/source identity digests or full identity list.

A separate read-only Supabase query against `public.matches` selected only `league, season, match_date, home_team, away_team` for Serie A dates on/after 2026-10-31 and returned **zero rows**. Thus neither the current free Football-Data CSV nor `public.matches` currently supplies future Serie A fixture identities for the 19-feature readiness preview. This confirms why the reviewed free, manual-only `/events` fixture path in #702 is still needed; it must remain blocked until #699 is human-merged, a new post-merge source archive persists and verifies the identity set, and #702 is separately human-merged before its manual dispatch.

The source ZIP/member hashes and no-future-fixture finding are source/identity evidence only. No 2026/27 target scores/results were inspected, no future probabilities or forecasts were generated, and no provider request, paid call, Supabase write/DDL, model/weight/feature change, schedule change, main mutation, or merge occurred. Original candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original 19 features, frozen weights, `active_lambda=0`, and research-only `shadow_lambda=1` are unchanged. HUMAN-MERGE only.

## 2026-10-31 15:06 UTC — prospective evaluator gate-clock hardening

PR #701 now has exact HEAD `fcbdae8a603ecad799065469d78e9deb390adb4a` against unchanged main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The public `read_completed_fixture_gate(client)` samples the actual UTC clock internally; it no longer accepts caller-supplied `captured_at`, preventing normal callers from backdating or future-dating the date-only completed-fixture cutoff. The timestamp-controlled implementation is private and used only by deterministic offline tests. Frozen query contract, identity canonicalization/digest, 30-event threshold, lazy outcome callback, original V2 candidate/weights/lambdas, and the outcome embargo are unchanged.

The evaluator-specific suite is now **74 passed** (one new regression proving internal clock use and rejection of a caller timestamp); all **6/6** exact-head PR validations succeeded: Research #41212958180, Serie A #41212958159, Bundesliga #41212958265, Ligue 1 #41212958237, Eredivisie #41212958266, Product #41212958347. PR #701 remains open/HUMAN-MERGE. `FROZEN_INCUMBENT_REFERENCE` remains unpinned, so even after the 30-forecast gate the evaluator must continue to fail closed until a separately approved non-legacy incumbent reference exists. No outcomes were read/scored and no Supabase writes/DDL or production changes occurred.

## 2026-10-31 14:56 UTC — independent live identity parity for current-form source archive

On unchanged main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, the free Current-Form Source Capture run [#41196139664](https://github.com/MaksimBlud/football-ai/actions/runs/41196139664) completed SUCCESS at 2026-10-31 11:16:55 UTC. Its source artifact is ID `13040356986`, 437,016 bytes, GitHub SHA-256 `feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a`. The ZIP was downloaded independently and its digest matches the GitHub artifact digest. Manifest SHA-256: `4038e73c83a7c7f3fab66acf83eb73768b161f064cde67a191ac36cfb8f8a22a`. All 11 CSV byte hashes match the manifest; current `2627/I1.csv` raw-byte SHA-256 is `32ca618587c90db25f16ea647cb55060f519c03830a1e8ec4a6c4204e27d5135`.

**New independent identity-parity proof:** a fresh Supabase read-only query selected exactly `match_date, home_team, away_team` from `public.league_finished_results` for Serie A 2026/27, before the UTC capture date. It returned 93 raw rows, which canonicalize under the exact V2 runtime aliases (including V2-local `Atalanta BC → Atalanta`) to 90 unique fixture identities; the three extra rows are alias duplicates. Independently computed SHA-256 using the source-capture contract's sorted tab/newline serialization (`date\thome\taway`, newline between identities) is `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`.

The downloaded current-season CSV was independently parsed from its raw ZIP bytes: 90 rows, 90 unique canonical identities, and the **same** SHA-256 `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`. This establishes actual 90/90 source-to-gate identity coverage independently of the manifest's row count. It does **not** prove the new #699 persisted-identity manifest contract has run live: the artifact still declares schema `SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1` and does not persist either gate/source identity digest or the full identity list. Keep #699 required before claiming the new contract is live.

The source run reports 19 tests passed, 10 historical CSVs plus one current CSV, 3,800 historical rows plus 90 current rows, feature-input gate passed (90 ≥ 30), zero paid calls, zero Supabase writes, and no target-outcome read/scoring. The original frozen candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original feature-builder blob remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.

The actual Current-Form Forward run [#41196202296](https://github.com/MaksimBlud/football-ai/actions/runs/41196202296) completed SUCCESS at 11:17:36 UTC with 53 tests passed. It authenticated the just-created source artifact and parent run (source age 41 seconds at verification), but `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, `paid_provider_calls=0`, and `production_or_supabase_writes=0`. This is live source-provenance verification, not a forecast or model-quality result.

Read-only market audit at this run: 3,966 total `public.odds_snapshots`; 3,915 strictly pre-kickoff and 51 at/after kickoff. Serie A: 625 total, 620 strictly pre-kickoff, 5 at/after kickoff, zero future pre-kickoff snapshots, zero new snapshots in 24 hours or 7 days; latest Serie A snapshot remains 2026-10-13 14:48:53.042620 UTC. `public.model_artifact_bundles` contains 0 rows. No new prospective quote exists to exercise source-before-quote forecasting.

**Do not compare identity digests across the two separate contracts:** #699's source-capture identity helper hashes sorted tab/newline-delimited fixture tuples; #701's completed-outcome evaluator helper hashes compact JSON fixture tuples. They intentionally have distinct serializers/query-contract contexts. The `95e3...` value above is specifically the #699 source-capture identity digest.

The feature-input gate is open at 90 identities; the separate evaluation gate remains CLOSED (0 eligible prospective forecasts, no pinned non-legacy frozen incumbent). `active_lambda=0` remains market, `shadow_lambda=1` remains research-only. No protected target outcomes were read, and no model/feature/weight/production artifact was changed. HUMAN-MERGE only; main remains unchanged.

## 2026-10-31 11:00 UTC — original V2 legacy-model isolation regression

This entry supersedes only the #699 HEAD/test-count details in the 09:10 UTC audit above; main and the frozen model contract remain unchanged.

- **PR #699** now has exact HEAD `53b7b184005e8516bfff8c1483e5ab9a4c41e73e`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, remains open/mergeable, and has **7/7 exact-head CI SUCCESS**. HUMAN-MERGE remains mandatory.
- Added `tests/test_serie_a_v2_no_legacy_xgboost_dependency.py`. Its AST import-closure check follows the original V2 local runtime dependencies and rejects XGBoost, joblib/pickle imports, pickle model IO, and production `.pkl` paths. The documented `market_anchor_1x2_v1.py` dependency is the research-only residual helper used by V2; it is not the retired XGBoost production model.
- Exact Original V2 Shadow Tests run [41194794442](https://github.com/MaksimBlud/football-ai/actions/runs/41194794442): **257 passed**; the production `*.pkl` diff guard passed. Exact-head Research PR Validation [41194794598](https://github.com/MaksimBlud/football-ai/actions/runs/41194794598) also completed SUCCESS.
- Read-only Supabase identity recheck still yields 93 raw rows, 90 canonical identities, 3 alias duplicates, 0 reversed duplicates, and SHA-256 `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`.
- Latest odds recheck at 2026-10-31 11:00 UTC: Serie A 625 snapshots, 620 strictly pre-kickoff, 5 at/after kickoff, 0 future pre-kickoff rows, 0 new snapshots in 24h/7d; latest snapshot remains 2026-10-13 14:48:53.042620 UTC. Model artifact bundles: 0.
- No new 2026-10-31 original/current-form V2 source/forward scheduled run was visible by 11:00 UTC. The 2026-10-30 source run was delayed about 5h52; this is a delay observation, not proof of a disabled workflow. No schedule changes were made.
- No new prospective forecast, target-outcome read, or Brier/LogLoss evaluation. The 30-primary-completed-prospective-event outcome gate remains CLOSED; no permitted frozen incumbent is registered.

No merge, main mutation, Supabase write/DDL, paid provider request, production artifact change, refit, threshold change, promotion, or other-agent/schedule change occurred.

## 2026-10-31 09:10 UTC — exact V2 source/forward audit, identity SHA, and bounded-download regression follow-up

This entry supersedes the older 02:48/03:00 UTC audit below. Default branch is still `main` at `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main mutation occurred.

### Exact V2 PR state

- **#699** HEAD `e760994249b488a3693116974963509b85788bb6`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, 7/7 required CI SUCCESS. Exact Original V2 Shadow Tests run [41166528822](https://github.com/MaksimBlud/football-ai/actions/runs/41166528822): **256 passed**, production `*.pkl` diff guard passed. This consolidated branch contains the current-form metadata-only identity allowlist, strict canonical date/team validation, C0/C1 control-character rejection, gate identity SHA/count/list, current-source coverage comparison, verified frozen-candidate preflight, gate/source/archive clock ordering, exact HTTPS URL and no-redirect checks, bounded historical CSV streaming, main-only workflow guards, and expanded dependency-trigger tests. It also contains the redirect-hardening code proposed separately in #700 and the overlapping current-form source/forward guard work from #698/#694/#695/#680/#688. Do not merge those overlapping changes independently.
- **#703** was extended with two missing negative regressions: both original and current-form GitHub ZIP readers now prove that a non-`bytes` stream chunk is rejected and the response is closed. New exact HEAD `e7362b83d1112ce52172d722c7f9decc3e69586e`; 7/7 CI SUCCESS. Original V2 Shadow Tests [41187160599](https://github.com/MaksimBlud/football-ai/actions/runs/41187160599): **99 passed**; production `*.pkl` diff guard passed. It remains open and unmerged. After #699 is manually merged, rebase/review #703 and retain its non-bytes guard/tests without weakening #699's stricter Content-Length validation or bounded ZIP-member checks.
- **#704** HEAD `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`, 7/7 CI SUCCESS. It pins exact package versions separately for Python 3.11 and 3.12 across the five original V2 research workflows. The lock files explicitly do **not** enforce package hashes. Rebase/re-run exact CI after #699 because both PRs touch the same workflows.
- **#702** HEAD `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`, 7/7 CI SUCCESS; its offline feature-preview suite has 22 tests. It is manual-only, no-odds/no-probability. It depends on #699 and a new successful post-#699 main source archive with persisted gate identities/count/SHA before any manual dispatch.
- **#701** HEAD `4ea2f9e60fc073d1850ae2b999f518db5d501a3f`, 6/6 CI SUCCESS; evaluator suite 73 tests. It remains fail-closed because `FROZEN_INCUMBENT_REFERENCE=None`; no market substitution or legacy XGBoost incumbent is permitted.
- **#697** is this documentation branch. Main's own `PROJECT_CONTINUITY.md` remains the older 2026-10-18 version until a human merges the documentation PR.

HUMAN-MERGE remains mandatory. No PR was merged.

### Live metadata and pre-match market state

The read-only Serie A 2026/27 metadata query selected exactly `match_date, home_team, away_team` from `public.league_finished_results`, with date cutoff exclusive 2026-10-31. No score, result, settlement, or target-outcome fields were selected.

- Raw metadata rows: **93**.
- Canonical unique fixture identities: **90**.
- Independently recomputed SHA-256 using the V2 alias `Atalanta BC -> Atalanta`, sorted identity tuples, tab separators and newline separators: `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`.
- The digest matches the source-capture branch's `_fixture_identity_sha256` serialization. This is a live metadata digest, not yet a persisted SHA in a new main source archive.

Read-only `odds_snapshots` audit:

- All leagues: **3,966** snapshots; **3,915** strictly before kickoff.
- Serie A: **625** snapshots; **620** strictly before kickoff.
- Future fixtures with saved strictly pre-kickoff quotes: **0**.
- Latest Serie A strictly pre-kickoff quote: **2026-10-13 14:48:53.042620 UTC**.

`public.model_artifact_bundles` currently contains **0** registered bundles.

### Actual main runtime and schedule lag

The latest confirmed main source/forward runs are still from 2026-10-30:

- Source Capture [41049950849](https://github.com/MaksimBlud/football-ai/actions/runs/41049950849), scheduled event, created 11:42:02 UTC, completed 11:43:04 UTC. It ran 19 tests and captured 90 current-season completed rows, 10 old-season CSVs, 11 files total. Artifact 12973598320, ZIP SHA-256 `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`. Paid calls 0; Supabase writes 0; target outcomes scored false.
- Current-Form Forward [41077147924](https://github.com/MaksimBlud/football-ai/actions/runs/41077147924), scheduled event, created 15:03:21 UTC. It ran 53 tests, authenticated the source artifact and successful parent run, but `quotes_seen=0` and `v2_current_form_shadow_captured=0`. It read no target outcomes and made no writes.
- Original Forward [41076521488](https://github.com/MaksimBlud/football-ai/actions/runs/41076521488), scheduled event, created 14:59:20 UTC. It ran 71 tests, verified 10 historical source CSVs / 3,800 historical rows, but `quotes_seen=0` and `forecasts_created=0`.

All three 2026-10-30 scheduled runs started roughly 5h52–6h51 after their declared cron times. No 2026-10-31 source/forward run was present in the latest Actions run inventory at this audit. This is an observed scheduling delay, not proof that the workflows are disabled. Schedules were not changed.

Crucially, main's current source-capture script blob `9f48a4a6e78d5d7ffa193ec6f24b394162f36ab4` still lacks persisted gate identity SHA/list, current-CSV gate coverage, candidate preflight and strict offset checks. The Oct30 archive therefore cannot substitute for the required post-#699 source archive. After manual #699 merge: verify the new main SHA, run a fresh successful source capture, and verify its manifest's gate identity count/list/SHA and CSV coverage before using it in any forward preview.

### Frozen model and scientific blockers

Original candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with **19 unchanged features**, original frozen weights, `active_lambda=0`, and `shadow_lambda=1` research-only.

The 90-event feature-input gate is separate from the outcome-read gate, which requires **30 unique eligible completed prospective forecasts**. Current eligible prospective forecasts remain **0**. The preregistered historical stability gate remains FAILED: only 2/6 prior seasons dual-metric wins; bootstrap probability better than market is 0.6831 for Brier and 0.6317 for LogLoss, below the required 0.95, with both 95% CI upper bounds still positive. No independent prospective Brier/LogLoss result exists. The evaluator requires market, frozen incumbent and V2 shadow; incumbent is unpinned and no model artifact bundle is registered. No target outcomes were read or scored.

No Supabase write/DDL, paid provider call, protected target-outcome read, production `.pkl` change, model refit, threshold tuning, promotion, publication, bet, merge, main mutation, schedule change, or other-agent setting change occurred.


## 2026-10-31 03:00 UTC — evaluator identity sanitization hardening

A real identity-validation gap was found in the prospective evaluator branch: its metadata-gate adapter and forecast identity canonicalizer did not reject C0/C1 control characters, unlike the stricter source-capture canonicalizer in #699. This could allow malformed team labels into the canonical identity/digest path.

The gap is fixed on **PR #701**:
- Gate metadata adapter rejects control characters before canonical alias mapping and checks the canonical result again.
- Forecast identity canonicalizer applies the same non-empty, C0/C1 control-character checks before and after the existing Serie A/V2-local alias mapping.
- Four parameterized regression cases cover NUL and U+0085 in both the read-only metadata gate and forecast identity.
- The forecast tests assert the lazy outcome callback is not invoked on malformed identity input.

Exact PR #701 HEAD: `4ea2f9e60fc073d1850ae2b999f518db5d501a3f`; base main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. All **6/6** exact-head workflow runs completed SUCCESS. Research run [41162279737](https://github.com/MaksimBlud/football-ai/actions/runs/41162279737) reports **73 passed** in `tests/test_market_anchor_1x2_v2_prospective_evaluator.py`. PR remains open, mergeable and HUMAN-MERGE only.

This hardening changes no feature, weight, candidate SHA, lambda, cohort boundary, comparator, threshold or outcome gate. No target outcomes were read. The evaluator still blocks on the unpinned non-legacy frozen incumbent; do not use the legacy XGBoost model or silently substitute market probabilities.


## 2026-10-31 02:48 UTC — exact-head PR audit and fresh pre-match-only database recheck

This is a read-only continuity refresh. Default branch remains `main` at `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no PR was merged and no main ref was changed.

### Current V2 PRs and exact-head workflow evidence

- **#699** `3e02ad265306a5dd9347b7ac4b310adb746ca68d`: 7/7 workflow runs completed SUCCESS. Original V2 shadow run [41111939589](https://github.com/MaksimBlud/football-ai/actions/runs/41111939589) ran **236 tests**, including the source/clock/identity/outcome guards. The main-ref guards remain absent from current main; do not manually dispatch secret-bearing V2 workflows from a feature ref. HUMAN-MERGE only.
- **#697** `7a3a4f7c732d541325bc32e26dd9ba32e6764292`: 7/7 documentation PR workflow runs completed SUCCESS. This continuity update is being added to that same documentation branch, not to main.
- **#701** `7ee3eda3f396735e00737d8e8e42e0c8c146c57f`: 6/6 workflow runs completed SUCCESS. Targeted evaluator run [40675684714](https://github.com/MaksimBlud/football-ai/actions/runs/40675684714) reports **69 passed**. The evaluator still fails closed without the third, frozen-incumbent vector; it must not substitute the market for that vector or revive the legacy XGBoost model.
- **#702** `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`: the current exact-head workflow-run API returns **7 completed runs, all SUCCESS**; dedicated offline fixture/feature contract run [41147422466](https://github.com/MaksimBlud/football-ai/actions/runs/41147422466) reports **22 passed**. Do not describe this as 8/8 without separate check-run evidence. Live dispatch remains blocked pending #699, a new post-#699 main source archive, and HUMAN-MERGE.
- **#703** `078a04c6b5bfdf6c61a8b368f9ca6c28fb4f487c`: 7/7 workflow runs completed SUCCESS. Original V2 shadow run [41157687503](https://github.com/MaksimBlud/football-ai/actions/runs/41157687503) reports **97 passed**, including bounded GitHub artifact ZIP download regressions. #703 and #699 both touch the forward readers; merge #699 first, then rebase/review #703 and rerun exact-head CI before considering its manual merge.

The three PRs #657, #659 and #660 remain merged. Overlapping older guard PRs must not be merged separately when their changes are already represented in #699.

### Fresh Supabase read-only audit (2026-10-31 02:48 UTC)

The current feature-input query selected only `match_date, home_team, away_team` from `public.league_finished_results` for Serie A 2026/27, dates 2026-07-01 through 2026-10-30. It did not select scores, results, settlement, or target-outcome columns.

- Raw metadata rows: **93**.
- Canonical identities after the existing four Serie A aliases plus V2-local `Atalanta BC -> Atalanta`: **90**.
- Independently recomputed canonical identity-set SHA-256: `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`.
- This matches the previously verified current CSV identity-set SHA; it is a re-confirmation, not a new source archive or a new prediction.

Pre-match odds query used only league, snapshot timestamp and kickoff timestamp:

- All leagues: **3,966** snapshots, **3,915** strictly pre-kickoff.
- Serie A: **625** snapshots, **620** strictly pre-kickoff.
- All leagues: **0** strictly pre-kickoff snapshots in the last 24 hours or 7 days; **0** future fixtures with a saved strictly pre-kickoff quote.
- Latest Serie A snapshot: **2026-10-13 14:48:53.042620 UTC**.

Additional read-only registry checks:

- `public.model_artifact_bundles`: **0** registered bundles.
- `public.league_prediction_ledger`: **630** Serie A rows, all `MARKET_ONLY / CALIBRATION_REQUIRED`; **0** future strictly pre-kickoff rows.

### Runtime state — no new execution inferred

The latest verified main-branch source/forward executions remain:

- Source Capture [run 41049950849](https://github.com/MaksimBlud/football-ai/actions/runs/41049950849): SUCCESS, 19 tests, 90 metadata-gate events, 90 current-season completed rows, 10 historical CSVs, 11 source files; source artifact 12973598320, ZIP SHA-256 `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`.
- Current-Form Forward [run 41077147924](https://github.com/MaksimBlud/football-ai/actions/runs/41077147924): SUCCESS, 53 tests, source artifact/parent verified, 0 quotes, 0 V2 shadow forecasts, target outcomes not read or scored.
- Original Forward [run 41076521488](https://github.com/MaksimBlud/football-ai/actions/runs/41076521488): SUCCESS, 71 tests, 3,800 old-season source rows verified, 0 quotes, 0 prospective forecasts.

No new main-branch source or forward run is claimed in this refresh. The next source capture must be a new successful run on the post-#699 main SHA and its manifest must contain the gate identity list/count/SHA; the older artifact is not a substitute.

### Scientific blockers remain binding

The frozen candidate remains SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with 19 unchanged features/weights, `active_lambda=0`, `shadow_lambda=1` research-only, and `stability_gate_passed=false`. The 90-event feature-input gate is separate from the 30 eligible completed prospective-forecast outcome gate. There are still zero eligible prospective forecasts and no registered frozen incumbent bundle. The preregistered review signal requires V2 shadow Brier **and** LogLoss to beat both the de-vigged market and the frozen incumbent; no substitute comparator, threshold change, outcome read, or superiority claim is allowed.

No Supabase write/DDL, paid provider call, target-outcome read, production `.pkl` change, model refit, threshold tuning, publication, bet, merge, main mutation, schedule change, or other-agent setting change occurred.


## 2026-10-30 15:48 UTC — fresh original/current-form forward runs and pre-match-only registry audit

Fresh GitHub API reads confirm `main=40887ebb215730190d7a6c7a1693373ec4afcdfc`; PR #699/#697/#701/#702 remain open and no merge was performed.

### New actual main-branch runtime

- Original V2 Forward-Only [run 41076521488](https://github.com/MaksimBlud/football-ai/actions/runs/41076521488): SUCCESS; **71 tests passed**. The actual original old-season source attestation verified 10 pre-prospective CSVs / 3,800 historical rows, artifact **12978111278**, ZIP SHA-256 `dd9c9fd43b61f78075bee68b016507d5d766733099e532b79131d566125716da`, and frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. The original forward report says `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `supabase_writes=0`; no original-cohort forecast was produced. Uploaded output artifact **12988120716**, 1,457 bytes, independently recomputed SHA-256 `0283dd379d41843a12f4b287ace9f9f2e8f1a8a695fc1bad7633904a46443c59`.
- Current-Form Forward-Only [run 41077147924](https://github.com/MaksimBlud/football-ai/actions/runs/41077147924): SUCCESS; **53 tests passed**. Runtime verified current source artifact **12973598320**, source ZIP SHA-256 `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`, frozen candidate SHA unchanged, feature-input metadata gate count **90**, 90 completed current-season CSV rows, 10 old-season CSVs / 11 total, and 3,890 historical-plus-current rows. Gate check time `11:42:40.932700Z` precedes current CSV observation `11:42:59.273193Z`, which precedes archive creation `11:42:59.333069Z`; authenticated parent run 41049950849 completed at `11:43:04Z`. At forward verification `15:03:57.744812Z`, source age was 12,058 seconds (within the unchanged 24-hour limit). The report says `quotes_seen=0`, empty `rows`, `v2_current_form_shadow_captured=0`, and both target-outcome flags false. This verifies the source/archive path, **not** a per-quote source-before-quote prediction.
- Downloaded the current-form forward artifact **12987716790** (438,195 bytes); recomputed outer ZIP SHA-256 `90ad2e9e026762db807b42f5165697e03a7257bdc6a331101a6b27df0a07376a`, matching GitHub's digest. Its nested source ZIP recomputed to `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`; all 11 CSV byte hashes match the manifest. Current CSV `serie_a_2627.csv`: 90 completed rows, SHA-256 `32ca618587c90db25f16ea647cb55060f519c03830a1e8ec4a6c4204e27d5135`. The manifest contains the 90-count metadata gate but **does not itself contain the canonical gate-identity-set SHA**; the prior independent read-only 90/90 parity hash remains external evidence. PR #699's gate-identity attestation is still required to move that identity proof into the trusted manifest/runtime.

### Fresh pre-match-only Supabase checks

- Read-only `public.odds_snapshots` query selected only league, snapshot timestamp and kickoff timestamp, with strict predicate `snapshot_time_utc < commence_time_utc`. It again returns **3,966** rows, **3,915** strictly pre-match, **0** strictly pre-match rows in the last 7 days, and **0** future fixtures with a saved strictly pre-match quote. Latest Serie A pre-match snapshot remains **2026-10-13 14:48:53 UTC**. No new quote is available; no provider call was made.
- `public.model_artifact_bundles` remains empty. A separate query against `public.product_prediction_snapshots` was restricted to rows where `generated_at_utc < commence_time_utc` and non-null 1X2 artifact SHA. It found only **40 EPL** rows for `EPL_AI_MARKET_PAIR_V1`, SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`, latest generated `2026-10-09 15:29:33Z`; **no Serie A frozen incumbent** was found. Do not use the EPL artifact or revive/execute the legacy XGBoost model as the required Serie A incumbent.

### Review and scientific state

- PR #699 remains open, mergeable, HUMAN-MERGE only, exact HEAD `3e772c859bf3538a492aaffc314be533285d7db0`, base main above, **7/7 exact-head checks SUCCESS**, including **229 Original V2 shadow tests** and production `*.pkl` diff guard. Its latest change enumerates all four secret-bearing original V2 workflows and enforces a `refs/heads/main` job guard. Main's current original forward workflow does not yet have that guard; the #699 branch does. Do not dispatch secret-bearing V2 jobs from non-main refs.
- PR #697 remains documentation-only; this entry records the later 15:00/15:04 UTC live runs. PR #701 remains **6/6** CI and fail-closed without an eligible frozen incumbent. PR #702 remains **7/7** mocked contract CI; its live zero-credit `/events` probe has not been run and is sequenced after #699 plus a fresh SHA-attested source capture.
- Original frozen candidate, 19-feature order/weights, `active_lambda=0`, `shadow_lambda=1`, NO_BET and the 30-eligible-completed-prospective-forecast target-outcome gate are unchanged. Both forward runs captured zero forecasts; no Brier/LogLoss or superiority claim is available.

No merge/main mutation, Supabase write/DDL, paid provider call, production `.pkl` change, target-outcome read, model refit, threshold tuning, bet or publication occurred. No schedule or other-agent setting was changed.


## 2026-10-30 13:54 UTC — independent byte-level source and identity parity proof

A second, independent verification was completed after the runtime logs above. Both GitHub artifacts were downloaded read-only and inspected locally; no Supabase data was written.

- Source artifact **12973598320**: ZIP size 437,016 bytes; recomputed SHA-256 `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`, exactly matching GitHub's artifact digest. The ZIP contains 11 CSV files plus the manifest. Recomputed SHA-256 for **all 11/11 CSV byte streams** matches each manifest entry. Current-season CSV SHA-256: `32ca618587c90db25f16ea647cb55060f519c03830a1e8ec4a6c4204e27d5135`.
- The current-season CSV was read for identity fields only (`Date, HomeTeam, AwayTeam`); no score, goal, result or settlement columns were loaded for this check. It contains 90 rows, 90 unique canonical fixture identities, no exact duplicates and no reversed duplicates. Using the existing four Serie A aliases plus the V2-local `Atalanta BC -> Atalanta` alias, its canonical sorted `date<TAB>home<TAB>away` identity SHA-256 is `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`.
- An independent read-only Supabase query selected exactly `match_date, home_team, away_team` from the Serie A 2026/27 completed-fixture metadata before the 2026-10-30 UTC cutoff. It returned 93 raw rows, 90 unique identities after the same aliases, and 3 duplicate rows after canonicalization. Its independently computed sorted identity SHA-256 is **the same** `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`. Therefore current CSV coverage matches the metadata-only 90/90 gate identity set exactly.
- Current-Form Forward artifact **12974157310**: recomputed ZIP SHA-256 `80df126dc31e3de9280a396fe48e2e4f04a6f600db8bafc75a2f547f98f9b394`, exactly matching GitHub's artifact digest. Its nested source ZIP was independently hashed as `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`, matching the original source artifact byte-for-byte. The JSON report contains `quotes_seen=0`, an empty `rows` array, `v2_current_form_shadow_captured=0`, and both target-outcome flags false.

This establishes byte integrity and exact source identity parity for the current 90-event feature-input gate. It does **not** establish a source-before-quote prediction because there were no saved quotes to test; it does not open the separate 30-eligible-completed-prospective-forecast outcome gate; it is not a model-quality result. Frozen candidate, original 19 features/weights, active lambda 0, shadow lambda 1, NO_BET and all embargoes remain unchanged.

## 2026-10-30 13:48 UTC — fresh source/forward runtime, all-league pre-match quote audit, and exact guard review

Fresh GitHub reads confirm `main=40887ebb215730190d7a6c7a1693373ec4afcdfc`; no PR was merged. All evidence below is read-only or GitHub Actions artifact metadata. No target outcomes were selected.

### New current-form source and forward runs on the unchanged main

- Current-Form Source Capture [run 41049950849](https://github.com/MaksimBlud/football-ai/actions/runs/41049950849): SUCCESS; 19 tests passed. Runtime JSON reports candidate `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, feature-input gate count **90**, completed current-season CSV rows **90**, ten old-season CSVs / eleven total source files, 3,890 historical-plus-current rows, zero paid calls, zero Supabase writes, and no target outcomes read/scored. GitHub artifact **12973598320**, upload digest `sha256:02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`. This digest is taken from the GitHub Actions upload log/metadata; this cycle did not independently re-download and recompute this new ZIP.
- Current-Form Forward-Only [run 41050080529](https://github.com/MaksimBlud/football-ai/actions/runs/41050080529): SUCCESS; **53 tests passed**. It independently verified the source artifact metadata and parent run: source artifact ID 12973598320, source ZIP digest above, source observation `11:42:59.273193Z`, archive upload `11:43:01Z`, successful parent completion `11:43:04Z`, forward verification `11:43:43.900741Z`, source age 44 seconds. Runtime report: `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, paid calls 0, writes 0. All per-quote block counters are zero because no quotes were returned; this is **not** a quote-level source-before-quote pass and **not** a forecast.
- Free Real-Quote Diagnostic [run 41057970063](https://github.com/MaksimBlud/football-ai/actions/runs/41057970063): SUCCESS; **53 tests passed**, ten public CSV requests, 3,800 historical rows, zero quoted fixtures, zero diagnostics scored, zero paid provider requests. Mode remains `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`. Artifact 12978111278, upload digest `dd9c9fd43b61f78075bee68b016507d5d766733099e532b79131d566125716da`.

### Read-only saved-odds audit (timestamps and 1X2 snapshot metadata only)

Query predicate is strictly `snapshot_time_utc < commence_time_utc`; no scores, results, settlements or outcome fields were selected. Across nine stored league groups: **3,966** rows total, **3,915** strictly pre-match, **51** not strictly pre-match, **0** rows in the last seven days, and **0** future events with a saved strictly pre-match quote.

| League | Rows | Strictly pre-match | Last 7 days | Future pre-match |
|---|---:|---:|---:|---:|
| Bundesliga | 404 | 394 | 0 | 0 |
| EPL | 1,151 | 1,135 | 0 | 0 |
| Eredivisie | 412 | 410 | 0 | 0 |
| La Liga | 806 | 798 | 0 | 0 |
| Ligue 1 | 394 | 387 | 0 | 0 |
| Primeira Liga | 9 | 9 | 0 | 0 |
| RPL | 156 | 153 | 0 | 0 |
| Serie A | 625 | 620 | 0 | 0 |
| Turkey Super Lig | 9 | 9 | 0 | 0 |

Serie A's latest strictly pre-match snapshot remains **2026-10-13 14:48:53 UTC**. The V2 current-form source is now at 90 completed identities/rows, but there is still no later saved quote to consume. No provider call was made.

A separate read-only check of `public.product_prediction_snapshots` found **zero Serie A rows satisfying generated_at_utc < commence_time_utc**. `public.model_artifact_bundles` also remains empty. This does not prove no prediction exists in every possible legacy table; it means no eligible frozen incumbent was identified from these pre-match product snapshots or the artifact registry.

### Exact guard review and remaining comparator blocker

- PR #699 remains open, mergeable, HUMAN-MERGE only, at exact HEAD `3e772c859bf3538a492aaffc314be533285d7db0`, base `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Exact-head API returns **7/7 SUCCESS**: Research PR Validation 41011507144; Bundesliga 41011507165; Serie A Frozen V2 Shadow Tests 41011507232 (**229 tests**); Eredivisie 41011507201; Ligue 1 41011507225; Serie A 41011507249; Product 41011507270. The PR body still mentions an older exact SHA in one section; use the API HEAD above, not stale prose.
- Re-read the four secret-bearing V2 main-branch workflows on current main: original forward preview, current-form source capture, current-form forward preview, and free real-quote diagnostic. Their current-main job guards do not all require `github.ref == refs/heads/main` before Supabase secrets are exposed. PR #699 adds the main-ref guard to all four and includes exact-head regressions. Do not run manual dispatch from a non-main ref. This is a security reason to prioritize manual review/merge of #699.
- The frozen parent protocol explicitly requires three comparators: de-vigged market, frozen production incumbent, and lambda-one V2 shadow. PR #701 correctly sets `FROZEN_INCUMBENT_REFERENCE=None` because the policy does not pin an incumbent model version/artifact SHA. Do not substitute the market or revive/execute the legacy XGBoost model. Until a valid pre-existing incumbent reference is identified or the owner separately resolves the preregistered comparator requirement, the evaluator must remain closed; no Brier/LogLoss claim is possible.
- PR #697 documentation itself remains the only change in that PR; this section records this later checkpoint. PR #699/#701/#702 remain unmerged. The original candidate SHA, 19-feature order/weights, `active_lambda=0`, `shadow_lambda=1`, NO_BET and all evaluation gates remain unchanged.

No PR merge, main write, Supabase write/DDL, paid request, production `.pkl` change, model refit, threshold tuning, target-outcome read, betting or publication occurred.

# Football AI — Project Continuity

## 2026-10-30 — Original V2 guard integration review and current-source coverage gap

- Fresh default-branch audit: `main=40887ebb215730190d7a6c7a1693373ec4afcdfc`; no V2 PR in this cycle was merged. PR #699 remains HUMAN-MERGE only. Its latest exact head is `3e772c859bf3538a492aaffc314be533285d7db0`; exact-head CI is **7/7 SUCCESS**, including **229 Original V2 tests** and the production `*.pkl` diff guard. A new regression now asserts that all four original V2 workflows carrying Supabase secrets are restricted to `refs/heads/main`.
- Real on-main source run #40868280531 / artifact #12894054589 was downloaded and independently inspected. ZIP SHA-256: `b4b1144ca28414ccf7a5a7a5c02fde4611e8e0f1a37997012de031a38baa14b0`. It contains ten frozen historical CSVs plus `serie_a_2627.csv`; all 11 source files are present. The manifest's feature-input gate count at capture time was 80, current-season completed CSV rows were 88 through **2026-10-28**, and archive creation time was `2026-10-29T11:49:49.284743Z`. It records zero paid calls, zero Supabase writes and no target-outcome reads.
- A fresh read-only metadata-only query of `public.league_finished_results` selected only `match_date, home_team, away_team` for Serie A 2026/27. It returned 93 raw rows and **90 canonical unique fixture identities** after the V2-local `Atalanta BC -> Atalanta` normalization, latest date **2026-10-29**. The archived CSV ends on Oct 28, so the two Oct 29 gate fixtures are absent from that archive. Do not reuse the 80-identity manifest as proof of current 90-identity coverage. After #699 is merged, a new source capture must prove the complete gate identity SHA and full current-source coverage; it must fail closed until the public CSV includes all gate fixtures.
- Latest verified main runtime: Original Forward-Only run #40898762675 passed 71 tests and independently verified its historical source ZIP, but captured `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`. Current-Form Forward-Only run #40899523036 passed 53 tests, verified artifact #12894054589 (source age 12,315 seconds at run time), but `quotes_seen=0` and `v2_current_form_shadow_captured=0`. Free Real-Quote Diagnostic run #40877079065 passed 53 tests; no paid credentials or target outcomes were used.
- Fresh read-only `public.odds_snapshots` audit: Serie A has 620 strictly pre-match rows; latest snapshot is **2026-10-13 14:48:53 UTC** and there are zero future pre-match rows. Across the queried leagues, future pre-match row count is zero. No new prospective V2 quote/forecast exists.
- CI count correction from exact-head API re-audit: PR #702 head `b91773b6677bd2be7df67d5b2c69c27b9a202397` currently has **7 returned workflow runs, all SUCCESS**, including the dedicated zero-credit fixture contract run with 18 tests passed. The earlier 04:52 note's 8/8 count is superseded; no eighth run reference was found.
- The frozen candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 original features, unchanged weights, `active_lambda=0` market fallback and `shadow_lambda=1` research-only. PR #701's evaluator keeps the outcome callback closed until 30 eligible completed prospective forecasts and a valid frozen incumbent reference; `public.model_artifact_bundles` currently has zero rows and the evaluator's incumbent reference remains unset. No Brier/LogLoss claim is available.
- Security note from Supabase advisor: RLS remains disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No DDL was run; enabling RLS without explicit policies would block access.
- No paid requests, Supabase writes/DDL, production `.pkl` changes, target-outcome reads, refit, threshold tuning, bets, publication or promotion occurred. No main-branch change or PR merge was performed.

## 2026-10-30 04:52 UTC — fresh runtime, all-league quote audit, and free-source odds check

Fresh GitHub read confirms main is still exactly 40887ebb215730190d7a6c7a1693373ec4afcdfc (2026-10-18 commit); no V2 PR has been merged. Main branch protection remains disabled (protected=false). HUMAN-MERGE is still required.

### Exact open V2 review heads

- #699: ab888b32e6ea5a231d271b00e4db42fab186986b, 7/7 exact-head CI SUCCESS, Original V2 Shadow Tests 228 passed; production *.pkl diff guard passed. Consolidated source/clock/identity/URL/outcome/workflow-secret guard PR.
- #697: d6866f4b10c0062a0064f52e16a8446545e01a2f, 7/7 exact-head CI SUCCESS (documentation only).
- #702: b91773b6677bd2be7df67d5b2c69c27b9a202397, 8/8 exact-head CI SUCCESS, including mocked zero-credit /events contract suite (18 passed); no live provider request.
- #701: 7ee3eda3f396735e00737d8e8e42e0c8c146c57f, 6/6 CI SUCCESS; still fail-closed because no registered eligible incumbent exists.
- #694/#700/#686/#680 overlap the consolidated #699 guards; do not merge them separately. #657/#659/#660 remain confirmed merged.

### Actual main-branch V2 runtime (old main code, not #699 guards)

- Current-form Source Capture run 40868280531: SUCCESS, 19 tests passed, 80 completed-primary feature-gate identities, 88 completed prior-day current-season CSV rows, 10 historical CSVs + 1 current CSV, no paid calls, no Supabase writes, no target outcomes read/scored. Artifact 12894054589, 436,766 bytes, ZIP SHA-256 b4b1144ca28414ccf7a5a7a5c02fde4611e8e0f1a37997012de031a38baa14b0. Independent re-download verification recomputed the ZIP SHA-256 and matched it exactly; all 11 CSV byte hashes (including the current-season CSV) also matched the manifest. The manifest's UTC order is gate check 11:49:31.742325 < latest source observation 11:49:49.220206 < declared archive time 11:49:49.284743; target-outcome gate closed, paid_provider_calls=0, supabase_writes=0.
- Original Forward-Only run 40898762675: SUCCESS, 71 tests passed; source attestation verified 10 historical CSVs / 3,800 historical rows; quotes_seen=0, future_quotes_checked=0, v2_diagnostic_previews_captured=0.
- Current-Form Forward-Only run 40899523036: SUCCESS, 53 tests passed; verified artifact 12894054589 and parent run 40868280531, source age 12,315 seconds, 88 current-season history rows, captured gate count 80; quotes_seen=0, v2_current_form_shadow_captured=0, target outcomes unread/unscored.
- These are genuine runtime checks on old main; they do not exercise the new gate-identity SHA, bounded source capture, clock rollback, or main-ref secret guards in #699.

### Fresh read-only Supabase quote audit

Only quote timestamps, kickoff timestamps, league and aggregate counts were selected. All nine stored league groups have 0 snapshots in the last 24 hours, 0 in the last 7 days, and 0 future strictly pre-kickoff snapshots:

| League | Stored snapshots | Latest snapshot UTC |
|---|---:|---|
| Bundesliga | 404 | 2026-09-11 15:49:52 |
| EPL | 1,151 | 2026-10-09 15:25:57 |
| Eredivisie | 412 | 2026-09-11 15:50:20 |
| La Liga | 806 | 2026-09-11 15:45:28 |
| Ligue 1 | 394 | 2026-09-11 15:49:24 |
| Primeira Liga | 9 | 2026-09-11 16:06:24 |
| RPL | 156 | 2026-09-05 15:07:55 |
| Serie A | 625 | 2026-10-13 14:48:53 |
| Turkey Super Lig | 9 | 2026-09-11 16:06:26 |

Total: 3,966 snapshots. The Serie A 2026/27 identity-only query returned 91 raw rows / 88 V2-alias-normalized fixture identities through 2026-10-28; it selected only match_date, home_team, away_team. This does not replace the runtime SHA/coverage attestation required from a fresh #699 source archive.

### Free-source check: Football-Data CSV does not provide upcoming odds in this archive

Downloaded the existing source artifact 12894054589 and inspected only Date, Time, HomeTeam, AwayTeam plus bookmaker 1X2 odds columns in serie_a_2627.csv; no score, goals, result, settlement or target-outcome columns were read. The file has 88 rows, latest date 2026-10-28, and zero rows dated after 2026-10-30; therefore this archived CSV contains no future fixture rows or future market odds to seed new prospective quotes. This is a bounded observation about this artifact, not a claim that no other free source exists. PR #702's free /events probe returns fixture metadata only, not odds.

### Scientific and security blockers

- public.model_artifact_bundles remains 0. public.league_prediction_ledger has 630 Serie A MARKET_ONLY rows, latest 2026-10-13 14:48:53 UTC, and 0 future strict pre-match rows; the ledger has no model-artifact SHA identifying a distinct frozen V2 incumbent. Do not substitute market or the prohibited legacy XGBoost model for the required incumbent.
- The preregistered outcome gate remains CLOSED until 30 eligible prospective V2 forecasts have completed. No target outcomes were read; no Brier/LogLoss can be reported.
- Supabase Security Advisor still reports RLS disabled on five public tables: teams, predictions, match_statistics, league_prediction_ledger, and epl_ai_market_pair_ledger. Critical access-control issue; no DDL was run. Enabling RLS without reviewed policies may block application access.
- The trusted-main auto-merge workflow's code restricts candidates to draft PRs authored by github-actions[bot] with the draft(agents): staged title and allowlisted change sets; owner-authored V2 PRs #699/#697/#702/#701 are not eligible. No merge was attempted.

Next permitted proof remains: HUMAN-MERGE #699 at its exact tested HEAD; verify the resulting main SHA; run a fresh source capture on main; verify the new gate-identity SHA and complete CSV coverage; then run both forward-only readers. Existing stale October 13 quotes must remain blocked. No paid API call, Supabase write/DDL, protected outcome read, production .pkl change, model/weight change, schedule change, or other-agent setting change occurred in this audit.


## 2026-10-30 01:59 UTC — V2 source/archive hardening, exact-head CI, and live-data checkpoint

Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No merge or main mutation.

### Exact-head original V2 guard PR

PR [#699](https://github.com/MaksimBlud/football-ai/pull/699) is open and mergeable at HEAD `38d6100ab893981e2f59f5a0306563de680f0da0` (76 commits, 23 files). This remains branch-only code; no post-merge runtime proof yet.

New protections now include:
- Both GitHub Actions artifact ZIP readers stream 64-KiB chunks, enforce declared and actual compressed-download limits, stop at the first excess chunk, and close responses.
- The current-form ZIP reader now validates every ZIP member's uncompressed size **before reading/decompressing the manifest or any CSV**: 5 MB per historical CSV, 10 MB aggregate historical CSVs, 2 MB current CSV, 3 MB manifest, and 16 MB total uncompressed archive. Duplicate/unexpected members and invalid sizes fail closed.
- The ten historical Football-Data CSV downloads now receive the remaining aggregate byte budget. Content-Length is rejected before body read if it exceeds that remaining budget; otherwise actual streamed bytes are stopped at the first aggregate overrun. The old post-download aggregate check remains as defense-in-depth.
- All eleven source CSVs remain bounded and source URLs/status/final URL are checked. Observation time is sampled only after the complete response body. The feature-input gate stores the canonical identity list, count and SHA-256, and the verifier recomputes both gate digest and source coverage.
- Job-level `github.ref == refs/heads/main` guards precede secret-bearing environment variables on all three source/forward workflows.

**Exact-head CI: 7/7 SUCCESS** on `38d6100ab893981e2f59f5a0306563de680f0da0`:
- Original V2 Shadow Tests [#40988923958](https://github.com/MaksimBlud/football-ai/actions/runs/40988923958): **225 passed**; production `*.pkl` hash/diff guard passed.
- Research [#40988924014](https://github.com/MaksimBlud/football-ai/actions/runs/40988924014).
- Serie A [#40988923786](https://github.com/MaksimBlud/football-ai/actions/runs/40988923786).
- Bundesliga [#40988923841](https://github.com/MaksimBlud/football-ai/actions/runs/40988923841).
- Ligue 1 [#40988923967](https://github.com/MaksimBlud/football-ai/actions/runs/40988923967).
- Eredivisie [#40988923971](https://github.com/MaksimBlud/football-ai/actions/runs/40988923971).
- Product [#40988923807](https://github.com/MaksimBlud/football-ai/actions/runs/40988923807).

The 225 tests establish code/contract regression behavior only. They do **not** prove a live prospective prediction or model superiority.

### Actual main-branch runtime evidence (old code path, not the unmerged guards)

- Source Capture [#40868280531](https://github.com/MaksimBlud/football-ai/actions/runs/40868280531): SUCCESS, 19 tests, feature-input gate count 80, current-season CSV 88 completed rows, ten historical CSVs / eleven source files, artifact `12894054589`, ZIP SHA-256 `b4b1144ca28414ccf7a5a7a5c02fde4611e8e0f1a37997012de031a38baa14b0`. No paid calls, Supabase writes or target-outcome scoring.
- Original Forward-Only [#40898762675](https://github.com/MaksimBlud/football-ai/actions/runs/40898762675): SUCCESS, 71 tests, 3,800 historical rows / ten pre-prospective CSVs, but `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`.
- Current-Form Forward-Only [#40899523036](https://github.com/MaksimBlud/football-ai/actions/runs/40899523036): SUCCESS, 53 tests, verified artifact `12894054589` and parent run `40868280531`, source age 12,315 seconds, but `quotes_seen=0` and `v2_current_form_shadow_captured=0`. No target outcomes were read/scored.
- The captured archive's gate set was 80 identities. A fresh metadata-only query selecting only `match_date,home_team,away_team` now returns 91 raw Serie A 2026/27 rows / **88 canonical identities** after V2-local `Atalanta BC → Atalanta`, latest date 2026-10-28. The old archive does not prove coverage of the later 88-identity set; only a new post-merge capture can do so.

### Fresh pre-kickoff data audit

Read-only Supabase query restricted to strictly pre-kickoff rows:
- 3,915 strictly pre-kickoff snapshots.
- Latest strictly pre-kickoff snapshot: `2026-10-13T14:48:53.042620Z`.
- Zero strictly pre-kickoff snapshots in the last 24 hours or 7 days.
- Zero future events with a saved snapshot strictly before kickoff.

No score/result/settlement columns were selected. No Supabase writes or DDL.

### Remaining scientific blockers

- PR [#702](https://github.com/MaksimBlud/football-ai/pull/702) is open, mergeable, 7/7 CI SUCCESS. It is a free fixture/feature-readiness preview only; no live request has been made.
- PR [#701](https://github.com/MaksimBlud/football-ai/pull/701) is open with 6/6 CI SUCCESS. Its evaluator keeps `FROZEN_INCUMBENT_REFERENCE = None`; the frozen current-form policy requires de-vigged market, frozen production incumbent, and lambda-1 shadow. Do not substitute the prohibited legacy XGBoost model or weaken the preregistered comparator contract. The 30-eligible-completed-prospective-forecast outcome gate remains CLOSED; no target outcomes have been read.
- PRs [#694](https://github.com/MaksimBlud/football-ai/pull/694) and [#700](https://github.com/MaksimBlud/football-ai/pull/700) remain open with 7/7 CI but their guard changes are consolidated in #699; do not merge them separately without a fresh overlap review.
- PRs #657, #659 and #660 are verified merged.
- Supabase Security Advisor reports RLS disabled on `teams`, `predictions`, `match_statistics`, `league_prediction_ledger`, and `epl_ai_market_pair_ledger`. No DDL was run; policies must be designed before RLS can safely be enabled.

Original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features/weights, `active_lambda=0` market and `shadow_lambda=1` research-only remain unchanged. No old XGBoost restoration, paid odds call, production `.pkl` change, outcome read, threshold tuning, bet, publication, promotion, schedule change or other-agent setting change.

HUMAN-MERGE only. The next runtime proof requires manual merge of #699, then a fresh main-branch source capture and forward run; the stale October 13 quotes must remain blocked.

## 2026-10-30 00:06 UTC — all source CSVs bounded; exact-head proof

Fresh `main` is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main mutation.

- PR #699 now bounds **all eleven source CSV downloads**. The current-season CSV is streamed with a **2,000,000-byte** actual-body cap. The ten frozen historical CSVs are streamed with a **5,000,000-byte per-file** cap and **10,000,000-byte aggregate** cap. Both paths precheck declared Content-Length, enforce the actual streamed/decompressed byte count before joining the body, verify direct HTTP 200/exact approved HTTPS final URL, and close responses on success/failure. Source observation timestamps are recorded only after body completion.
- Maximum raw source bytes are 12,000,000 (10 MB historical + 2 MB current), below the current-form forward reader's **16,000,000-byte** archive limit, leaving manifest/ZIP overhead headroom.
- New regression coverage includes historical declared-size rejection before body read, actual streamed overrun/early stop, aggregate over-budget rejection before persisting the offending CSV, and cleanup.
- Exact PR #699 HEAD: `32251b847b01c0891ea6f94ec3a16471ee6cc95a`; **7/7 required CI checks SUCCESS**. Original V2 shadow run [#40977305620](https://github.com/MaksimBlud/football-ai/actions/runs/40977305620) reports **214 passed**, including both source-capture suites; the production `*.pkl` diff guard passed. This is branch CI proof only, not live post-merge proof.
- Main-ref security guard remains important: current `main` still lacks job-level main-ref guards on the original-forward and current-form source-capture manual-dispatch jobs. PR #699 adds the guard before secret-bearing `env` for all three V2 workflows. Do not manually dispatch those two main workflows from a feature branch before merge.
- Fresh read-only odds audit at approximately `2026-10-29T23:58Z`: 3,966 snapshots; latest `2026-10-13T14:48:53.042620Z`; zero in last 24h/7d and zero future strict pre-kickoff observations. Metadata-only Serie A query: 91 raw rows, 88 canonical identities through 2026-10-28. No scores/results/settlement fields were selected.
- `public.model_artifact_bundles` still has 0 registered bundles; PR #701 remains correctly blocked by the missing pinned non-legacy incumbent. PR #702 remains manual-only; no free-fixture provider request was made.
- The latest real main source/forward runs remain #40868280531, #40898762675 and #40899523036; no new quote, forecast, Brier or LogLoss result exists. After HUMAN-MERGE, rerun source capture and forward verification on the exact resulting main SHA.

**Remaining separate hardening scope:** GitHub artifact ZIP readers still read the ZIP response body before applying their existing archive-size checks; this is distinct from the now-bounded Football-Data CSV paths and should be reviewed separately. No paid request, Supabase write/DDL, protected target-outcome read, production artifact change, or schedule change occurred.

## 2026-10-29 23:58 UTC — bounded current-form source body and fresh pre-match data audit

Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main mutation.

- On the integrated V2 guard branch in [PR #699](https://github.com/MaksimBlud/football-ai/pull/699), current-season Football-Data capture now requests `stream=True`, checks direct HTTP 200 and the exact approved final URL before body consumption, validates any declared Content-Length, enforces the **2,000,000-byte limit on the actual streamed/decompressed body before buffering**, and closes the response on every path. The source-observation clock remains sampled only after the complete body is consumed.
- Added regressions for an over-limit Content-Length (zero body consumption), an over-limit streamed body (stop at the first over-limit chunk), and response cleanup. Existing source-capture clock/identity tests now use the streamed response contract.
- Exact PR #699 HEAD: `3ae327a2fb80be7d168c7a5bafbbc5daf3029ed5`; **7/7 required CI checks SUCCESS**. Original V2 shadow workflow [#40976486733](https://github.com/MaksimBlud/football-ai/actions/runs/40976486733) ran **211 tests PASS**, including `tests/test_serie_a_v2_current_form_source_capture.py`; its `git diff --exit-code -- '*.pkl'` guard passed. This is branch CI proof, not post-merge runtime proof.
- Fresh read-only Supabase odds aggregate at approximately `2026-10-29T23:58Z`: **3,966** snapshots; latest `2026-10-13T14:48:53.042620Z`; **0** snapshots in the last 24 hours, **0** in the last 7 days, and **0** future strictly pre-kickoff snapshots.
- Fresh metadata-only Serie A 2026/27 query selected only `match_date, home_team, away_team`: **91** raw rows, **88** canonical identities after the V2 Atalanta alias, latest date **2026-10-28**. No score/result/settlement columns were selected.
- No fresh quote or new forecast exists. The latest on-main source/forward runs remain the October 29 runs recorded below; a fresh live proof of PR #699's new guard still requires HUMAN-MERGE followed by new source capture and forward verification on the resulting exact main SHA.
- **Secret-boundary finding on current main:** the original forward workflow and current-form source-capture workflow both expose `workflow_dispatch` but lack a job-level main-ref guard before their Supabase secret-bearing `env`; do not manually dispatch either from a feature branch. PR #699 adds guards before `env` for all three V2 workflows and its contract test checks the ordering. Main remains exposed until that PR is manually merged.

**Superseded scope note (2026-10-30 00:05 UTC):** the historical CSV download path was subsequently bounded in PR #699; see the newer entry at the top of this file. GitHub artifact ZIP downloads are a separate path and are not covered by the CSV streaming fix. No paid request, Supabase write/DDL, protected target-outcome read, production artifact change, or schedule change occurred.

## 2026-10-29 22:57 UTC — source/forward runtime rechecked; source-clock regression fixed on #699

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No main mutation or merge.

- **Current-form source capture:** [run #40868280531](https://github.com/MaksimBlud/football-ai/actions/runs/40868280531) SUCCESS; 19 tests passed. Source artifact `12894054589`, GitHub digest `sha256:b4b1144ca28414ccf7a5a7a5c02fde4611e8e0f1a37997012de031a38baa14b0`, created `2026-10-29T11:49:51Z`. Safe log summary: 80 metadata-only feature-gate identities, 88 completed prior-day current-season source rows, ten frozen historical CSVs, 3,800 historical rows, 11 source files, candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, no target-outcome scoring, paid calls or Supabase writes.
- **Original old-season forward:** [run #40898762675](https://github.com/MaksimBlud/football-ai/actions/runs/40898762675) SUCCESS; 71 tests passed; verified source artifact `12899100578` / parent `40877079065`; `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`. Output artifact `12908850341`, SHA-256 `579272f55c137a1c085d99ac3177fea8b468addfbe93e9581bb158e35240f704`.
- **Current-form forward:** [run #40899523036](https://github.com/MaksimBlud/football-ai/actions/runs/40899523036) SUCCESS; 53 tests passed. It verified source artifact `12894054589` and parent run `40868280531`; at verification `15:15:04Z`, source age was 12,315 seconds and within the fixed 24-hour limit. `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, no paid calls or writes. Output artifact `12909131392`, SHA-256 `39c9216878a629701272a4a6fa92007b62b1eb64d9c4a9299e047ba1c8ec5817`.
- **Fresh read-only Supabase check at 22:53 UTC:** `public.odds_snapshots` 3,966 rows; latest snapshot `2026-10-13T14:48:53.042620Z`; zero rows in 24 hours, zero in 7 days, zero future strictly pre-kickoff rows. `public.league_finished_results` metadata-only aggregate (only date/team identity columns) returned 91 raw Serie A 2026/27 rows, 88 canonical identities, dates `2026-08-22` through `2026-10-28`. No score/result fields were selected.
- **PR #699 timestamp-order correction:** current branch head `2eeaedd7f43b3f823df0b2b08424e395cadd2787`. Current-form source capture now consumes `response.content` before sampling the source-observation clock, preventing slow body downloads from understating source age or crossing the UTC-day cutoff after the clock was sampled. Regressions cover offsetless clock rejection after body consumption and a body-completion-at-midnight boundary. Exact-head CI: **7/7 SUCCESS**; Original V2 Shadow Tests **209 passed** and `git diff --exit-code -- '*.pkl'` passed. Details in [PR #699](https://github.com/MaksimBlud/football-ai/pull/699).
- PR #702 remains a manual-only free fixture/feature-readiness probe; its exact head `b890514dda0c9a388c6855fa0d843a21a62a7306` has 7/7 CI SUCCESS, but no live `/events` request was dispatched. No paid odds call or cron.

Scientific status remains unchanged: no fresh admissible saved quote, no new eligible prospective V2 forecast, no pinned non-legacy incumbent. The separate 30-primary-completed-prospective-forecast outcome gate remains CLOSED; no Brier/LogLoss comparison or superiority claim. Original 19 features/weights and candidate SHA remain frozen; `active_lambda=0` market, `shadow_lambda=1` research-only.

No merge/main change, Supabase write/DDL, paid request, target-outcome read, production `.pkl` change, schedule change, refit, promotion or bet occurred in this iteration. HUMAN-MERGE only.

---
## 2026-10-29 19:56 UTC — later metadata reveals source-gate drift

This update supersedes the earlier 2026-10-29 15:55 UTC statement that the archived 80-identity source matched the current metadata gate. A later read-only audit recorded on PR #694 at 2026-10-29 18:52:22 UTC found a changed metadata set.

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main mutation.
- Source capture run [40868280531](https://github.com/MaksimBlud/football-ai/actions/runs/40868280531) completed SUCCESS at 2026-10-29 11:49:54 UTC. Source artifact `12894054589` SHA-256 `b4b1144ca28414ccf7a5a7a5c02fde4611e8e0f1a37997012de031a38baa14b0`; all 11 CSV byte hashes matched the manifest. At capture, the manifest recorded 80 completed current-season rows and 80 feature-input-gate identities.
- A later metadata-only query selecting exactly `match_date, home_team, away_team`, with the same V2-local alias normalization and no score/result fields, returned 88 canonical identities through 2026-10-28: 3 dated 2026-10-27 and 5 dated 2026-10-28.
- Therefore the artifact's captured gate set is behind the later observed metadata set by eight identities. Do not use that artifact for any new forward inference unless the live gate/source coverage is re-established; do not weaken the fixed freshness or source-before-quote rules.
- Latest confirmed current-form forward run [40899523036](https://github.com/MaksimBlud/football-ai/actions/runs/40899523036) completed SUCCESS at 2026-10-29 15:15:14 UTC, but captured zero quotes and zero shadow forecasts. The latest 100 repository workflow runs inspected at 19:56 UTC showed no newer V2 source-capture or forward-preview run. This is a safe no-quote runtime result, not prediction-quality evidence.
- PR #694 current HEAD `2fd95bb07befb00b6efb4a14815ad925d50cac71` has 7/7 successful exact-head CI checks; its Original V2 suite reported 109 passing tests. PR #699 HEAD `e50ad26c3d6b4c9bac8d584dead0ab043b4f3792` is a descendant of #694 (compare: 35 commits ahead, 0 behind) and also has 7/7 successful checks. Treat #699 as the integrated review target; do not merge overlapping #694 separately. HUMAN-MERGE only.
- No fresh admissible saved odds, new eligible forecasts, target-outcome reads/scoring, paid calls, Supabase writes/DDL, production `.pkl` changes, or model/contract changes occurred in this audit.

The frozen candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original 19 features/weights and `active_lambda=0` / `shadow_lambda=1` semantics remain unchanged. The 30-primary-completed-forecast outcome gate stays closed, and no Brier/LogLoss superiority claim is permitted.

## 2026-10-29 15:55 UTC — latest original and current-form forward runtime — source attested, zero quotes, no outcomes

Fresh read-only check of `main`: `40887ebb215730190d7a6c7a1693373ec4afcdfc`; PR #697 remains documentation-only and unmerged.

- **Original old-season-only forward:** [run #40898762675](https://github.com/MaksimBlud/football-ai/actions/runs/40898762675) completed SUCCESS on that exact main SHA at 2026-10-29 15:10:42 UTC. The job ran **71 tests**, independently attested source artifact `12899100578` from free diagnostic run `40877079065` (10 pre-prospective CSVs / 3,800 historical results; source ZIP SHA-256 `fda6c48dc59c2ca5b82310756a37742d69023a8e6c1a38d795a240d9390c3d4b)), then reported `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`, `paid_provider_calls=0`, and `supabase_writes=0`. Its uploaded output artifact is `12908850341`, GitHub SHA-256 `579272f55c137a1c085d99ac3177fea8b468addfbe93e9581bb158e35240f704`.
- **Current-form forward-only:** [run #40899523036](https://github.com/MaksimBlud/football-ai/actions/runs/40899523036) completed SUCCESS at 2026-10-29 15:15:14 UTC on the same main SHA. **53 tests passed**. It verified source artifact `12894054589` (SHA-256 `b4b1144ca28414ccf7a5a7a5c02fde4611e8e0f1a37997012de031a38baa14b0`), successful source parent run `40868280531`, current-season input rows 88, feature-input gate count 80, 10 historical CSVs / 3,888 combined historical rows as reported by runtime, and source observation `2026-10-29T11:49:49.220206Z`. At verification it was 12,315 seconds old and remained inside the fixed 24-hour limit. Output artifact `12909131392` has GitHub SHA-256 `39c9216878a629701272a4a6fa92007b62b1eb64d9c4a9299e047ba1c8ec5817`. It reported `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, zero paid calls and zero production/Supabase writes.
- **Fresh read-only odds audit (2026-10-29, approximately 15:55 UTC):** `public.odds_snapshots` has 3,966 rows; latest `snapshot_time_utc=2026-10-13T14:48:53.042620Z`; 0 rows in the previous 24 hours, 0 in the previous 7 days, and 0 future events with a saved snapshot strictly before kickoff. The query selected only counts/timestamps and did not inspect scores or results.

These are successful source/runtime and regression proofs, **not** prospective model-performance evidence. No new eligible quote or forecast exists; the source-before-quote and 30-completed-prospective-forecast outcome gates remain closed. The incumbent remains unpinned, so no Brier/LogLoss comparison is available. No model/weight/feature/lambda changes, paid calls, Supabase writes/DDL, production `.pkl` changes, schedule changes, outcome reads or merges occurred.

---

## 2026-10-29 — Fresh verified current-form source archive; no admissible quotes

Fresh main re-check: `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No main mutation or merge.

**Current-form source capture:** [run 40868280531](https://github.com/MaksimBlud/football-ai/actions/runs/40868280531) completed SUCCESS on the exact main SHA. Artifact `12894054589`, ZIP SHA-256 `b4b1144ca28414ccf7a5a7a5c02fde4611e8e0f1a37997012de031a38baa14b0`; downloaded bytes independently hash to the same digest. The archive has ten frozen historical CSVs (3,800 completed rows) plus the current `2627/I1.csv` source (88 rows), with manifest SHA-256 `d2fa45e92d662ab8a79421475361ac694cace2deb75fbe799b6c04baaabe9691`. After downloading the artifact, the ZIP digest was independently recomputed and all 11 raw CSV byte streams were SHA-256 checked against the manifest: **11/11 matched**, including current-season source SHA `d2fa45e92d662ab8a79421475361ac694cace2deb75fbe799b6c04baaabe9691`; the current-season CSV was not parsed or inspected for target outcomes. The feature-input gate used only `match_date,home_team,away_team`, counted 80 unique completed primary fixture identities, and did not select score/result columns. Manifest records 19 frozen features and candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.

**Current-form forward preview:** [run 40868414740](https://github.com/MaksimBlud/football-ai/actions/runs/40868414740) completed SUCCESS. Artifact `12894613085`, ZIP SHA-256 `37f0c83da317d90621bb967508dab3f8568f34edeba01d77d41059e2f9cca00d`; local hash matches GitHub's artifact digest. The report independently verifies source artifact `12894054589` and its digest, source parent run `40868280531`, current source age 45 seconds at verification, and `fresh_for_new_quote=true`. It also reports `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, `paid_provider_calls=0`, and `production_or_supabase_writes=0`. Thus source provenance is live-proven, but there was no eligible saved quote and no new forecast.

**Original old-season-only forward workflow check (2026-10-29):** the main-branch Actions run listing for 08:00–14:00 UTC contains no run of `.github/workflows/serie-a-v2-forward-preview.yml`, either on `schedule` or `workflow_run`. The latest confirmed original-forward success remains [run 40711770789](https://github.com/MaksimBlud/football-ai/actions/runs/40711770789), created 2026-10-28 15:01:37 UTC on main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Its downloaded artifact `12826501542` independently hashes to GitHub's digest `79a1cd9211e051851f621f9d971041f3a049e673f792c25f2c1aa6f941e197c4`; its report has `quotes_seen=0`, `rows=[]`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`, no paid calls and no Supabase writes. This is a missing run in the queried window, not proof of a schedule configuration defect; schedule was not changed. The separate current-form source/preview pair above did run successfully, but it also found zero saved quotes.

**Independent free diagnostic:** [run 40877079065](https://github.com/MaksimBlud/football-ai/actions/runs/40877079065) completed SUCCESS; 53 offline tests passed, artifact `12899100578`, ZIP SHA-256 `fda6c48dc59c2ca5b82310756a37742d69023a8e6c1a38d795a240d9390c3d4b`, locally re-hashed to the same digest. The report shows 3,800 old-season history rows, zero source-observed-after-quote cases, zero paid provider requests, and zero Supabase writes. It is a diagnostic only, not a prediction-quality evaluation.

The saved quote table remains stale (last observed snapshot 2026-10-13 14:48:53 UTC in the prior metadata-only audit); no target outcomes were opened. The 30-primary-completed-forecast outcome gate remains CLOSED, the frozen incumbent is still unpinned, and no Brier/LogLoss comparison is authorized yet. No model weights/features/lambdas, production artifact, schedule, or Supabase data changed.


## 2026-10-29 — Original V2 forward-capture timing regression fixed; exact-head CI verified

Main was re-read and remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main write occurred in this iteration.

PR [#702](https://github.com/MaksimBlud/football-ai/pull/702) currently has HEAD `b890514dda0c9a388c6855fa0d843a21a62a7306` (base is the unchanged main above); this HEAD includes the earlier response-body-completion clock fix from `ce589718afb2aebf02ee36872f17169e83bb2a9d` plus rejection of duplicate JSON object keys. The clock fix timestamps the response only after bounded body consumption and JSON parsing, and fails closed on clock rollback. Regressions cover a kickoff during body download, source freshness crossing 24 hours during download, and ambiguous duplicate JSON keys.

Exact-head GitHub Actions evidence: **7/7 SUCCESS** on current HEAD `b890514dda0c9a388c6855fa0d843a21a62a7306`: [Research #40845825232](https://github.com/MaksimBlud/football-ai/actions/runs/40845825232), [Serie A #40845825199](https://github.com/MaksimBlud/football-ai/actions/runs/40845825199), [Bundesliga #40845825279](https://github.com/MaksimBlud/football-ai/actions/runs/40845825279), [Ligue 1 #40845825395](https://github.com/MaksimBlud/football-ai/actions/runs/40845825395), [Eredivisie #40845825250](https://github.com/MaksimBlud/football-ai/actions/runs/40845825250), [Product #40845825370](https://github.com/MaksimBlud/football-ai/actions/runs/40845825370), and [dedicated free-fixture tests #40845825309](https://github.com/MaksimBlud/football-ai/actions/runs/40845825309). The dedicated mocked-provider run passed **17 tests**. CI did not call The Odds API. PR remains open for HUMAN-MERGE; no model weights, feature order, candidate SHA, lambdas, evaluation gate, schedule, production artifact, or Supabase data were changed.

Fresh read-only Supabase checks (metadata only; no score/result columns selected):
- `public.odds_snapshots`: 3,966 rows across 9 leagues; no rows in the previous 24 hours or 7 days; zero rows for future fixtures where snapshot time is strictly before kickoff. Latest Serie A snapshot is `2026-10-13T14:48:53Z`.
- `public.league_finished_results`: 83 Serie A 2026/27 metadata rows through 2026-10-25; 80 unique fixture identities after the existing V2-only `Atalanta BC -> Atalanta` alias. The query selected only `match_date, home_team, away_team` and aggregate counts, not outcomes.
- These data confirm the source-input gate is open but do not create any new prospective quote or forecast.

Existing main forward workflows: original forward run [40711770789](https://github.com/MaksimBlud/football-ai/actions/runs/40711770789) and current-form forward run [40712651474](https://github.com/MaksimBlud/football-ai/actions/runs/40712651474) completed successfully on main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`, with artifacts `12826501542` and `12825974332`. In this iteration, artifact `12825974332` was downloaded and its outer ZIP SHA-256 independently recomputed as `3659cc9e56f34da38abe86844a63b02686abd91153662a73bc2f5af3a171608e`, matching GitHub metadata. Its forecast report states `quotes_seen=0`, `rows=[]`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, `paid_provider_calls=0`, and `production_or_supabase_writes=0`. The embedded source ZIP for artifact `12812553701` independently hashes to `fb5f38f6c569de63dce7d9c1c58533ea873665e132d51bfc878ead7a684df6df`, matching its GitHub digest. The report verified that source archive at `2026-10-28T15:07:31.916110Z`: 11 source files, 10 old-season CSVs / 3,800 historical rows, 80 current-season prior-day rows, feature-input gate count 80, and source age 12,312 seconds (`fresh_for_new_quote=true` at that time). At the current audit time `2026-10-29T12:54:41Z`, the latest verified source observation `2026-10-28T11:42:18.949888Z` is 90,742 seconds old (>86,400 seconds), so this archive is now stale and cannot support a new quote. No newer successful source capture was verified in this audit; do not infer that a new forecast exists.

Scientific status remains unchanged: frozen original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features and weights unchanged; `active_lambda=0` market-only, `shadow_lambda=1` research-only. No fresh admissible odds, no new eligible prospective forecasts, no pinned frozen incumbent, no Brier/LogLoss evaluation. Target-outcome gate remains closed; no target outcomes were read.

Open review targets: [#699](https://github.com/MaksimBlud/football-ai/pull/699) source/clock/identity guards; [#701](https://github.com/MaksimBlud/football-ai/pull/701) evaluator that intentionally refuses outcome access while the incumbent reference is unpinned; [#702](https://github.com/MaksimBlud/football-ai/pull/702) free fixture metadata preview. No PR was merged.

---

## 2026-10-28 16:52 UTC — source-fixture feasibility cross-check: no Serie A future-fixture feed in current stores

Fresh read-only verification against unchanged `main` `40887ebb215730190d7a6c7a1693373ec4afcdfc` adds an independent source-feasibility check beyond the earlier quote-count audit.

- Downloaded current-form source artifact **12812553701** and independently recomputed ZIP SHA-256: `fb5f38f6c569de63dce7d9c1c58533ea873665e132d51bfc878ead7a684df6df`, matching GitHub's artifact digest.
- The archived `serie_a_2627.csv` is 38,144 bytes, SHA-256 `6cf59ded608d3d23da083b1f8510d2ca22b219f0927f64addeaadfde1b495e11`, with **80 rows** and latest fixture date **2026-10-25**; there are **zero future fixture rows** available in that CSV. This check is about row count/date/team metadata, not target-outcome evaluation.
- The current-form forward artifact **12825974332** was downloaded and its ZIP SHA-256 independently recomputed as `3659cc9e56f34da38abe86844a63b02686abd91153662a73bc2f5af3a171608e`, matching GitHub metadata. Its report at `2026-10-28T15:07:31Z` verifies source artifact #12812553701 (age 12,312 seconds), but records `quotes_seen=0`, `rows=[]`, and `v2_current_form_shadow_captured=0`.
- A read-only schema/metadata audit of `public.matches` found rows only for EPL seasons 2016/17–2026/27; the 2026/27 EPL partition has 80 rows through 2026-10-25 and zero future-dated rows. The query selected only league, season, date aggregates and counts; no scores or result fields. This table is not a Serie A future-fixture source.
- Read-only `public.odds_snapshots` aggregate remains 3,966 rows, latest snapshot `2026-10-13T14:48:53.042620Z`, zero snapshots in the last 24 hours or seven days, and zero future events with a saved quote strictly before kickoff.

**Newly narrowed blocker:** the verified current-form archive is intact, but the archived Football-Data CSV has no upcoming Serie A fixture rows, the existing `public.matches` table is EPL-only, and no saved admissible Serie A quote exists. Thus this run cannot compute a source-backed feature vector for an upcoming Serie A fixture without another independently approved free fixture source or a genuinely new permitted quote. Do not fabricate a quote, use stale October 13 prices, call the paid provider, add a paid schedule, relax the 24-hour gates, or read target outcomes for scoring.

No target outcomes were scored, no Supabase writes/DDL, paid requests, production `.pkl` changes, refit, promotion, schedule changes, or merges occurred. Frozen candidate SHA and 19-feature/weight contract remain unchanged; `active_lambda=0` is the market and `shadow_lambda=1` is research-only. The 30-eligible-prospective-forecast outcome gate remains closed and the incumbent reference remains unpinned.

---

## 2026-10-28 13:53 UTC — no verified zero-cost source for new pre-kickoff quotes; paid collector intentionally not dispatched

Fresh read-only audit of current `main` (`40887ebb215730190d7a6c7a1693373ec4afcdfc`) and the current-form source artifact confirms the source archive is healthy but cannot supply a new quote cohort by itself.

- Supabase `public.odds_snapshots` read-only aggregate: **3,966** rows; latest `snapshot_time_utc=2026-10-13T14:48:53.042620Z`; **0** rows in the last 24 hours, **0** in the last 7 days, and **0** future events with a saved snapshot strictly before `commence_time_utc`. The same result grouped by all nine stored leagues shows zero rows in the last 24 hours and zero future pre-kickoff rows for every league.
- Independently downloaded source artifact #12812553701 (parent run #40681895214) hashes to ZIP SHA-256 `fb5f38f6c569de63dce7d9c1c58533ea873665e132d51bfc878ead7a684df6df`; the manifest has 11 source entries and all **11/11** CSV SHA-256 values match. The current-season CSV was inspected only for fixture dates/team identities and pre-match odds fields: it has **0 rows dated 2026-10-28 or later**. No score/result columns were selected for this check.
- The only existing `Serie A Odds Snapshots` workflow at `.github/workflows/serie-a-odds-snapshots.yml` has **workflow_dispatch only** (no schedule), requires `THE_ODDS_API_KEY`, and runs `odds_api_budget_guard.py --max-cost 1` before `scheduled_serie_a_odds_snapshot.py`. It was not dispatched because paid The Odds API requests are prohibited. No new free pre-kickoff quote path is evidenced by the repository or saved data.
- Current-form source capture #40681895214 completed SUCCESS at 11:42:25 UTC on exact main SHA; forward preview #40682031414 completed SUCCESS at 11:43:13 UTC but found `quotes_seen=0` and captured zero new shadow forecasts. Free diagnostic #40690314722 completed SUCCESS at 12:45:21 UTC but does not create quote data. These are source/infrastructure proofs, not model-performance evidence.

**Blocker/action:** do not invoke the paid/manual quote workflow, add a paid schedule, relax source/quote freshness, scrape an unapproved source, or fabricate quotes. Continue only free source verification and frozen V2 regression/audit work until a genuinely admissible pre-kickoff quote is available under existing authorization. No target outcomes were read, no Supabase writes/DDL occurred, no model/weight/production artifact changed, no merge or schedule change occurred. The 30-eligible-prospective-forecast outcome gate remains CLOSED; incumbent reference remains unpinned, so no Brier/LogLoss claim is available.

---

## 2026-10-28 11:43 UTC — fresh source archive independently byte-verified; forward preview still has no quotes

**Source of truth re-read:** `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The previously missing scheduled source-capture did run successfully later that morning; do not treat the earlier 05:50/08:18 absence window as the latest runtime state.

- Source Capture [run #40681895214](https://github.com/MaksimBlud/football-ai/actions/runs/40681895214) completed SUCCESS at 2026-10-28 11:42:25 UTC on the exact main SHA. Its source artifact is [#12812553701](https://github.com/MaksimBlud/football-ai/actions/runs/40681895214/artifacts/12812553701), 435,794 bytes, ZIP SHA-256 `fb5f38f6c569de63dce7d9c1c58533ea873665e132d51bfc878ead7a684df6df`.
- Independently downloaded that artifact and recomputed SHA-256: exact ZIP digest match. Inspected the embedded manifest and recomputed every listed CSV SHA-256: **11/11 CSV hashes match**. The archive contains ten frozen historical-season CSVs plus `serie_a_2627.csv`; the ten historical files total 3,800 completed rows, and the current-season source contains 80 prior-day rows.
- Manifest clocks are ordered: current source observed at `2026-10-28T11:42:18.949888Z`, archive created at `2026-10-28T11:42:19.025465Z`; the parent source workflow completed at `11:42:25Z`. Frozen candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; feature-builder blob remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`. The gate selected only `match_date,home_team,away_team`; it passed 80 completed fixture identities. The manifest explicitly records no target outcomes scored, no paid provider calls, and no Supabase writes.
- Forward Preview [run #40682031414](https://github.com/MaksimBlud/football-ai/actions/runs/40682031414) completed SUCCESS at 11:43:13 UTC, 53 tests passed, and verified source artifact #12812553701 and its exact digest. The source was fresh (48 seconds old at verification), parent run was successful and completed before the forward preview, and every blocker counter was zero. However `quotes_seen=0`, `v2_current_form_shadow_captured=0`; no prospective prediction was created. Artifact #12812339141 has ZIP SHA-256 `16a43caf5d004cb122f63484e5206563953355ab8f853437c19141cbd2866707`.
- Fresh read-only Supabase query: `odds_snapshots` still has 3,966 rows, latest snapshot `2026-10-13T14:48:53.042620Z`, zero rows in the last 24 hours and zero future pre-kickoff snapshots. `league_prediction_ledger` has 630 Serie A rows and zero future pre-kickoff rows. The 83 raw current-season metadata rows canonicalize to 80 fixtures under the existing V2-local Atalanta alias.

**Interpretation:** source capture is now proven fresh and byte-integral; the source-before-quote guard path executes. The remaining immediate blocker is lack of any saved eligible pre-kickoff quote, not source capture. The separate 30-eligible-prospective-forecast outcome gate remains CLOSED; `FROZEN_INCUMBENT_REFERENCE` remains unpinned, so no target outcomes may be read/scored and no Brier/LogLoss claim is available. No code/model/weight/production changes, paid calls, database writes/DDL, schedule changes, merges or promotions occurred in this audit. HUMAN-MERGE only.

---

## 2026-10-28 09:49 UTC — canonical fixture identity reconciled; scheduled source/forward runs absent

**Fresh source of truth:** `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Current-form source workflow blob `9722416862b42d55ff7181003353c39620f23cf2` declares `05:50 UTC` daily; forward-preview workflow blob `6ebbcaff290a78e9ccffa4ac9a09bc0982eaff35` declares `08:18 UTC` daily and listens for successful source-capture completion.

**Scheduled runtime evidence:** latest known successful source capture remains [#40493535578](https://github.com/MaksimBlud/football-ai/actions/runs/40493535578), created 2026-10-27 11:05:44 UTC and completed 11:06:34 UTC; artifact `12730175586`, ZIP SHA-256 `f0fb3565d2e5f44faadf488820c36327cb9d0d7b83b3da826af9b877f0804986`. Latest known current-form forward preview remains [#40522068472](https://github.com/MaksimBlud/football-ai/actions/runs/40522068472), completed 2026-10-27 14:33:05 UTC; artifact `12740943343`, SHA-256 `d23b1f70e6da5845e9dc6c18e54174b1da9aa4a9e21402ca94ab7cb0d2ae3bd8`. Fresh GitHub Actions API window for 2026-10-28 05:45–06:00 UTC returned 12 runs but no source-capture run. The 08:10–08:30 UTC window returned zero runs, so no forward-preview run is recorded around its expected 08:18 UTC schedule. This does not prove either workflow is disabled; no schedule or setting was changed.

**Identity discrepancy resolved by canonicalization:** fresh read-only Supabase query at 2026-10-28 09:49 UTC selected only `match_date, home_team, away_team` from `public.league_finished_results` for Serie A 2026/27. It returned **83 raw rows**. Applying the existing V2-local `Atalanta BC → Atalanta` alias yields **80 canonical fixture identities**, exactly matching the last archive's `current_season_history_rows=80` and `feature_input_gate_count=80`. Three duplicate alias pairs account for the difference: 2026-08-23 Atalanta–Sassuolo, 2026-08-31 Atalanta–Bologna, and 2026-09-05 AS Roma–Atalanta. Each appears once under `Atalanta` and once under `Atalanta BC`. Thus 83 vs 80 is not evidence of three missing fixtures; it is raw-row count versus canonical identity count. At the 09:49 UTC audit, the last source observation was still within the 24-hour freshness window; that window reaches its limit at approximately 2026-10-28 11:06:31 UTC if no newer source observation is captured. The missed scheduled run means a fresh capture is still needed before that cutoff. PR #699's identity-set digest/fail-closed comparison remains useful to verify exact coverage after HUMAN-MERGE.

**Quote availability:** fresh read-only query at 2026-10-28 09:49 UTC returned 3,966 rows in `public.odds_snapshots`, latest `snapshot_time_utc=2026-10-13 14:48:53.04262+00`, zero snapshots in the prior 24 hours, and zero future events with a saved snapshot strictly before kickoff. Per-league counts and latest timestamps were checked; all nine listed leagues have zero snapshots in the prior 24 hours. The source/forward pipeline has no new eligible quotes, so no new V2 shadow forecast is available. No target outcomes were read or scored.

**Next:** HUMAN-MERGE only for #699/#701/#697. After any authorized merge, verify the actual main workflow runs and new artifact SHA/identity set; do not change schedules, dispatch paid collectors, write Supabase, or loosen the source/quote-age gates. The prospective evaluation gate remains closed; no Brier/LogLoss claim is possible.

## 2026-10-28 05:01 UTC — original V2: identity-only evaluation-gate reader CI proof

**Source of truth re-read:** default branch `main` is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This entry documents research-branch work only; it does not imply any PR merge or main change.

PR #701 adds `market_anchor_1x2_v2_completed_fixture_gate.py`, a read-only adapter that queries only `match_date,home_team,away_team` from `public.league_finished_results` for Serie A 2026/27. It constructs the evaluator's digest-bound attestation from the actual returned metadata rows, pins the existing query-contract SHA `181d76b75c092d46b57535591abbb4e625c3e54e9b0f876402c9a3e0ed2457fb`, applies the existing V2-local team alias, validates exact row keys, real UTC offset, season/date cutoff, reversed-duplicate identities and the identity-set SHA. It has no score/outcome selection, network call, model load or database write. The pure evaluator remains database-free.

Exact PR #701 HEAD: `e28c74cac7455c0a9d813c52f0754577358cba48`. **6/6 required CI checks SUCCESS**:
- Research PR Validation [#40635404169](https://github.com/MaksimBlud/football-ai/actions/runs/40635404169) — **67 evaluator tests passed**, including five new metadata-adapter regressions.
- Serie A [#40635404138](https://github.com/MaksimBlud/football-ai/actions/runs/40635404138)
- Bundesliga [#40635404153](https://github.com/MaksimBlud/football-ai/actions/runs/40635404153)
- Ligue 1 [#40635404292](https://github.com/MaksimBlud/football-ai/actions/runs/40635404292)
- Eredivisie [#40635404159](https://github.com/MaksimBlud/football-ai/actions/runs/40635404159)
- Product [#40635404280](https://github.com/MaksimBlud/football-ai/actions/runs/40635404280)

A first implementation exposed an unnecessary transitive scikit-learn import through the full source-capture module; the adapter now imports only the lightweight Serie A runtime configuration, and the final exact-head Research suite passes. This is test evidence, not yet a live invocation of the adapter against Supabase.

Fresh read-only Supabase checks on 2026-10-28:
- `public.odds_snapshots`: 3,966 rows; latest `snapshot_time_utc=2026-10-13T14:48:53.042620Z`; zero rows in the last 24 hours; zero future pre-kickoff rows.
- `public.matches`: zero rows with `match_date > current_date`.
- `public.league_finished_results` metadata-only query for Serie A 2026/27, selecting only date/home/away: 83 rows, 83 raw distinct identity triples, latest date 2026-10-25. These are identity counts, not target-outcome scoring.
- The existing source artifact still reflects the earlier 80-event gate snapshot; a fresh daily source capture must re-check coverage of all then-current identities before any future quote can be admitted.

The prospective evaluation gate remains CLOSED. No fresh admissible quote or future fixture exists, and `FROZEN_INCUMBENT_REFERENCE` remains unpinned; the evaluator must not substitute market probabilities for the missing incumbent. No 2026/27 target outcomes were read, and Brier/LogLoss were not computed. Original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19-feature contract, weights, `active_lambda=0`, and research-only `shadow_lambda=1` remain unchanged. HUMAN-MERGE only; no production `.pkl`, Supabase writes/DDL, paid calls, auto-promotion, or schedule changes.

## 2026-10-28 04:05 UTC — evaluator gate attestation and fresh read-only source/quote audit

**Original V2 only.** PR #701's updated exact HEAD `29229dbce2ce9096eb717b59d80db296ec2621e0` adds a required digest-bound completed-fixture identity attestation to the pure prospective evaluator. The evaluator now rejects missing/extra attestation fields, wrong source table/query contract, selected columns beyond `match_date, home_team, away_team`, identity count/digest mismatch, and identities on/after the UTC date-only cutoff. It still never loads the target outcomes before the gate and cannot score until the separately pinned incumbent exists. This is a structural contract check: the eventual capture caller must build the attestation directly from the actual metadata-only query result; the pure helper cannot independently prove which SQL the caller executed. Exact-head Research CI #40630182112 and the five league/product checks #40630182099, #40630182109, #40630182123, #40630182131, #40630182138 all completed SUCCESS; evaluator tests **62 passed**. [PR #701](https://github.com/MaksimBlud/football-ai/pull/701).

Fresh read-only Supabase audit at approximately `2026-10-28T03:50Z` selected only pre-match odds timestamps/identities/prices and metadata-only completed fixture identities:
- `public.odds_snapshots`: 3,966 rows total, 625 `SERIE_A`, latest saved Serie A quote `2026-10-13T14:48:53.042620Z`, 0 snapshots in the last 24h, 0 future strictly pre-kickoff snapshots.
- `public.league_prediction_ledger`: 630 `SERIE_A / MARKET_ONLY` rows, same latest snapshot timestamp, 0 future strictly pre-kickoff rows. These are market records, not a frozen incumbent.
- `public.league_finished_results` metadata query for `SERIE_A / 2026-2027`, `2026-07-01 <= match_date < current UTC date`, selected only `match_date, home_team, away_team`: 83 raw rows, 80 canonical unique fixture identities after frozen aliases, latest date `2026-10-25`. No score/result fields were selected.
- The latest free source capture [run #40493535578](https://github.com/MaksimBlud/football-ai/actions/runs/40493535578) succeeded on main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; artifact `12730175586` digest `sha256:f0fb3565d2e5f44faadf488820c36327cb9d0d7b83b3da826af9b877f0804986`. Existing independent byte/identity audit confirms the archived current-season source has the same 80 canonical identities and digest `a19ac284b11337ea54591025683a721e0bd2c9815820309b3797188826055f27`.
- Latest current-form forward preview [run #40522068472](https://github.com/MaksimBlud/football-ai/actions/runs/40522068472) succeeded and artifact `12740943343` was uploaded (digest `sha256:d23b1f70e6da5845e9dc6c18e54174b1da9aa4a9e21402ca94ab7cb0d2ae3bd8`). It still admitted 0 new prospective shadows because all stored quotes are stale; no target outcomes were read/scored. The free diagnostic [run #40500863999](https://github.com/MaksimBlud/football-ai/actions/runs/40500863999) also succeeded with no fresh quote.
- Consolidation audit: #699's exact source/forward files now contain the URL allowlists and redirect-denial from #683/#695/#700, the source/gate identity digest coverage from #694, and the dependency-trigger guards from #696/#698. Prefer #699 as the single consolidated HUMAN-MERGE candidate; do not separately merge overlapping branches without a fresh diff/CI review. Exact #699 HEAD `5ee0946427e4f9cbf1b688a746c268813ba399ab`, 7/7 checks SUCCESS.

**Blockers unchanged:** no admissible new quote since Oct 13, zero new prospective V2 forecasts, no pinned non-legacy frozen incumbent vector/reference, evaluation gate CLOSED. No Brier/LogLoss comparison or superiority claim. Frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, original 19 features/weights, `active_lambda=0`, `shadow_residual_lambda=1`, parent protocol and production artifacts unchanged. No paid API, Supabase writes/DDL, production changes, promotion, betting, or protected target-outcome reads. HUMAN-MERGE only.

---

## 2026-10-28 — Original V2 evaluator strict-schema guard and fresh runtime/data checkpoint

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Fresh main blob checks: `historical_football_signal_lab.py` = `401b3a0893371bfa4a488ec92a4a54af2678c8f7`; `experiments/market_anchor_1x2_v2_protocol.json` = `65729e9639720e67624c1481190aa22ae606f151`. Frozen candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original 19 features/weights and lambda contract unchanged.
- **PR #701 latest exact HEAD** `ae060db279995ca02c94cd746033b24d3c27ec56`, base main above. The evaluator rejects known outcome aliases and enforces exact allowlists for top-level forecast fields and nested incumbent evidence. Each incumbent vector must attest the same league, canonical match date/home/away identity, and exact UTC kickoff as the V2 forecast; mismatches/missing identity fail before the lazy outcome callback. Exact-head CI **6/6 SUCCESS**: Research #40624082593 (evaluator suite **58 passed**, production `.pkl` guard passed), Serie A #40624082655, Bundesliga #40624082644, Ligue 1 #40624082633, Eredivisie #40624082583, Product #40624082649. PR remains open for HUMAN-MERGE.
- **Fresh read-only Supabase pre-match check** at `2026-10-28T02:53:20Z`: `public.odds_snapshots` = 3,966 rows, 625 Serie A; latest quote `2026-10-13T14:48:53.042620Z`; zero rows in last 24h and zero future pre-kickoff snapshots. `public.product_prediction_snapshots` = 40 EPL-only `EPL_AI_MARKET_PAIR_V1` records. `public.league_prediction_ledger` = 630 Serie A records, all `MARKET_ONLY:CALIBRATION_REQUIRED`, zero future pre-kickoff rows. A separate metadata-only `public.matches` query returned 3,880 rows and **zero future fixture rows**. No same-event frozen incumbent vector exists for the primary Serie A cohort.
- Actual runtime logs re-read: current-form source run [#40493535578](https://github.com/MaksimBlud/football-ai/actions/runs/40493535578) SUCCESS, 19 tests, 11 source CSVs (10 frozen historic + current `2627/I1.csv`), 80 metadata-gated prior-day identities, zero paid calls/writes/outcome reads. Current-form forward run [#40522068472](https://github.com/MaksimBlud/football-ai/actions/runs/40522068472) SUCCESS, 53 tests, verified the source artifact and parent, but `quotes_seen=0` and zero shadows. Original old-season forward run [#40520212205](https://github.com/MaksimBlud/football-ai/actions/runs/40520212205) SUCCESS, 71 tests, verified 10 pre-prospective source files / 3,800 historical fixtures, but zero quotes and zero previews.
- **Independent byte-level archive proof (2026-10-28):** downloaded actual GitHub source artifact #12730175586; local ZIP SHA-256 equals GitHub digest `f0fb3565d2e5f44faadf488820c36327cb9d0d7b83b3da826af9b877f0804986`, and **all 11 archived CSV bytes match their manifest SHA-256**. Manifest says current-season CSV has 80 completed prior-day rows and no future/unplayed fixtures; the gate selected only `match_date,home_team,away_team`. Source observation `11:06:30.975279Z`, archive creation `11:06:31.056931Z`, parent run completion `11:06:34Z`. No CSV result rows were parsed for this byte-level check. Main candidate file blob SHA `ac1303f6b096664983fbf52443bd0a381b23ba21` contains candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 named features / 19 medians / 20 weight slots, active lambda 0, shadow lambda 1, stability gate false, training through 2026-06-30, and no opened 2026/27 outcomes.
- **Outcome gate remains closed**: no new eligible quotes exist and `FROZEN_INCUMBENT_REFERENCE` remains deliberately unset. The evaluator must not read outcomes even after 30 eligible completed forecasts until a separate approved protocol amendment pins the exact acceptable incumbent version and artifact SHA. No Brier/LogLoss superiority claim.
- **PR overlap / merge ordering:** #699 is the consolidated source/clock/identity/outcome-guard candidate (latest exact head `5ee0946427e4f9cbf1b688a746c268813ba399ab`, **7/7 CI SUCCESS**: Research #40624464535, Serie A #40624464792, Bundesliga #40624464664, Ligue 1 #40624464693, Eredivisie #40624464565, Product #40624464709, Original V2 Frozen Shadow Tests #40624464514). The latest test change also requires `experiments/market_anchor_1x2_v2_protocol.json` to remain in the original-forward workflow push paths, so a protocol edit cannot silently skip that audit. Its diff contains the historical redirect guard/tests also exposed in #700 and dependency-trigger changes overlapping #696/#698. Review the integrated #699 diff/CI before considering smaller overlapping PRs separately; do not merge overlapping branches blindly. #699 is not on main; post-merge live runtime proof is still required.
- Safety: no main changes or merges, no Supabase writes/DDL, paid calls, production `.pkl` edits, refits, threshold tuning, promotion, schedule changes, or protected target-outcome reads.


## 2026-10-27 18:56 UTC — original V2 evaluator: preregistration cutoff enforced

Fresh GitHub state:
- `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main mutation occurred.
- [PR #701](https://github.com/MaksimBlud/football-ai/pull/701) current exact HEAD: `7e92e9838d6a459fdafc7a7ec6d05d662c0f9346`, base `40887ebb215730190d7a6c7a1693373ec4afcdfc`, open and not merged.
- Exact-head validation: **6/6 SUCCESS** — [Research #40564441879](https://github.com/MaksimBlud/football-ai/actions/runs/40564441879), [Serie A #40564441940](https://github.com/MaksimBlud/football-ai/actions/runs/40564441940), [Bundesliga #40564442109](https://github.com/MaksimBlud/football-ai/actions/runs/40564442109), [Ligue 1 #40564441989](https://github.com/MaksimBlud/football-ai/actions/runs/40564441989), [Eredivisie #40564443793](https://github.com/MaksimBlud/football-ai/actions/runs/40564443793), [Product #40564442100](https://github.com/MaksimBlud/football-ai/actions/runs/40564442100). Research's prospective evaluator test step and no-production-artifact guard passed.
- [PR #699](https://github.com/MaksimBlud/football-ai/pull/699) remains open at `fb2e584f08cd4a139a2c9c4fc2e056c98c1fd0b8`; exact-head CI was 7/7 SUCCESS. Its new source/identity guards still require a real post-HUMAN-MERGE run on the resulting main SHA.

### New fail-closed evaluator boundary

The current-form policy was introduced by main commit `9df6f63db10e0128aff89c38fb8c6d88703ef8b8`, committed at `2026-10-18T08:15:32Z`. PR #701 now pins that cutoff and rejects any quote at or before the freeze timestamp, plus any fixture date outside the frozen 2026/27 season (`2026-07-01` through `2027-06-30`). New synthetic regressions verify both rejection paths occur before the lazy outcome loader can run. This prevents pre-contract quotes, including October 13 snapshots, from being counted just because their local source/quote timestamps look ordered. No original feature, weight, candidate SHA, lambda, or evaluation threshold changed.

### Fresh read-only data check (2026-10-27)

- `public.odds_snapshots`: 3,966 total; 625 Serie A; latest `2026-10-13T14:48:53.042620Z`; zero rows in the last 24 hours; zero future pre-kickoff rows.
- `public.predictions`: 0 rows.
- No new eligible prospective quote or shadow forecast exists. The evaluator still lacks a same-event, already-recorded incumbent vector for the Serie A primary cohort. Do not substitute market probabilities, load/revive the legacy XGBoost model, or read protected outcomes early.
- The existing source archive/current metadata identity parity remains 80/80 canonical fixture IDs, sorted-set SHA-256 `a19ac284b11337ea54591025683a721e0bd2c9815820309b3797188826055f27`; that proves identity parity only, not a fresh quote or model quality.

Safety remains binding: `active_lambda=0` is the market; `shadow_lambda=1` is research-only; the 30-eligible-completed-prospective-forecast outcome gate remains CLOSED. No target outcomes read/scored, no paid calls, no Supabase writes/DDL, no production `.pkl` changes, no model refit/promotion/bets, and no schedule changes. HUMAN-MERGE only.

---

## 2026-10-27 15:47 UTC — current-form forward runtime and incumbent-vector audit

Fresh verification on unchanged `main` SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`:

- [Serie A V2 Current-Form Forward-Only Preview run #40522068472](https://github.com/MaksimBlud/football-ai/actions/runs/40522068472) completed SUCCESS at `2026-10-27T14:33:05Z` on that exact main SHA. Its actual job log records **53 tests passed**, then verifies source artifact `12730175586`, ZIP SHA-256 `f0fb3565d2e5f44faadf488820c36327cb9d0d7b83b3da826af9b877f0804986`, from source parent run `40493535578`. Source observation was `11:06:30.975279Z`, archive creation `11:06:32Z`, and parent completed `11:06:34Z`; the artifact was verified at `14:32:58.534370Z` (~12,387 seconds old, within the frozen 24-hour limit).
- The same actual run reports `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes read/scored `false`, paid provider calls `0`, and writes `0`. This proves safe real archive/parent verification and no-quote behavior on old main, **not** the new gate-identity-set/SHA guard in PR #699; that guard still requires post-merge runtime proof.
- Fresh read-only Supabase query in this audit: `public.odds_snapshots` has **3,966** rows; latest snapshot `2026-10-13T14:48:53.042620Z`; zero rows in the preceding 24 hours and zero future pre-kickoff snapshots. Serie A has 625 saved rows, with the same latest timestamp and zero future pre-kickoff snapshots. No new eligible quote exists, so no new forecast can be admitted.
- Identity-only feature-gate query against `public.league_finished_results` returned **83 raw rows** for `SERIE_A` season `2026-2027` (`2026-08-22` through `2026-10-25`). After applying the frozen V2 alias rules (`Atalanta BC → Atalanta` plus the existing runtime aliases), those rows canonicalize to **80 unique fixture identities**. I independently recomputed the sorted identity-set SHA-256 from the real archived `serie_a_2627.csv` and the live metadata-only set: both equal `a19ac284b11337ea54591025683a721e0bd2c9815820309b3797188826055f27` (80/80 exact match). The raw 83 count is caused by alias duplicates, not missing source events. Only league/season/date/team identity fields were selected from Supabase; no score/result values were used in the comparison. This feature-input gate does not open the separate target-outcome evaluation gate.
- Read-only incumbent-source audit: `public.product_prediction_snapshots` contains **40** strictly pre-kickoff records, all `EPL` / `EPL_AI_MARKET_PAIR_V1` with model SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`; there are **no Serie A 2026/27 snapshots** in that table. These EPL vectors cannot be reused for the preregistered Serie A primary cohort. PR #701 correctly fails closed if the required same-event `incumbent_1x2` vector is absent; do not load or revive the legacy production model.
- PR #699 remains open for HUMAN-MERGE at exact HEAD `f603a222e4134d72af2343a27c50342c74e2f8a7` with 7/7 checks successful. PR #701 remains open at exact HEAD `6c006cd3a8a3f920fdf8ea29a287131a5a90e6fc` with 6/6 checks successful. Neither has been merged; the new source identity-set guard has not yet run on main.

No target outcomes were queried, read, or scored in this audit. No paid provider calls, Supabase writes/DDL, production `.pkl` changes, refit, promotion, or schedule changes. The original candidate SHA, 19-feature/weight contract, `active_lambda=0`, `shadow_lambda=1`, and 30-eligible-completed-prospective-forecast evaluation gate remain unchanged.

---

## 2026-10-27 12:13 UTC — consolidated V2 guard head and dependency-trigger CI

- Original V2 guard PR [#699](https://github.com/MaksimBlud/football-ai/pull/699) is still OPEN and requires HUMAN-MERGE. Latest exact HEAD: `f603a222e4134d72af2343a27c50342c74e2f8a7`; base `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Main was not modified.
- The consolidated diff now covers 23 files. In addition to source/clock/identity/outcome guards, it includes the missing source workflow contract test, the current-form dependency-trigger regression, the original-forward/frozen-shadow protocol dependency assertions, and the manual quote-trigger checks. Unique trigger hunks from #681/#684/#696/#698 have been incorporated into #699; those overlapping PRs were commented with the exact-head result and must not be merged independently.
- **7/7 exact-head CI SUCCESS on `f603a222e4134d72af2343a27c50342c74e2f8a7`:**
  - [Original V2 Shadow Tests #40501831651](https://github.com/MaksimBlud/football-ai/actions/runs/40501831651) — 198 passed in 5.30s; production-model hash guard passed.
  - [Research #40501831744](https://github.com/MaksimBlud/football-ai/actions/runs/40501831744), [Serie A #40501831683](https://github.com/MaksimBlud/football-ai/actions/runs/40501831683), [Bundesliga #40501831681](https://github.com/MaksimBlud/football-ai/actions/runs/40501831681), [Ligue 1 #40501831705](https://github.com/MaksimBlud/football-ai/actions/runs/40501831705), [Eredivisie #40501831816](https://github.com/MaksimBlud/football-ai/actions/runs/40501831816), and [Product #40501831706](https://github.com/MaksimBlud/football-ai/actions/runs/40501831706) — all SUCCESS.
- Regression process: intermediate HEAD `a36bd0d1b945df308c1a749d586cd5805f6e9e6e` failed two dependency-trigger tests because the source workflow omitted the current-form forward test and manual quote-trigger test from its source workflow dependency set/test command. Both were added to source workflow paths and executed tests; the corrected exact HEAD above now passes all 7 checks.
- Live runtime scope remains unchanged: source run #40493535578 and forward preview #40493645751 ran on old `main`, so they prove the existing count-based source capture, artifact/parent SHA provenance and fail-closed no-quote behavior, but not the new identity-set/SHA guard. Post-HUMAN-MERGE runtime proof on the resulting exact new `main` SHA is still required.
- Fresh read-only odds audit at `2026-10-27T12:12:26Z`: `public.odds_snapshots` still has 3,966 rows; latest snapshot `2026-10-13T14:48:53.042620Z`; zero snapshots in the last 24h and zero future pre-kickoff snapshots. No new forecast can be produced.
- Frozen original candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with original 19 features/weights unchanged. `active_lambda=0` remains market reference, `shadow_lambda=1` research-only. The separate 30-eligible-completed-prospective-forecast outcome gate remains CLOSED. No target outcomes read/scored, paid calls, Supabase writes/DDL, production `.pkl` changes, or schedule changes.

## 2026-10-27 11:59 UTC — fresh source archive and forward-only runtime proof

- Fresh read-only workflow audit on unchanged `main` SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc` found a successful source capture followed by a successful forward-only preview:
  - [Source Capture run #40493535578](https://github.com/MaksimBlud/football-ai/actions/runs/40493535578), completed `2026-10-27T11:06:34Z`.
  - [Forward-Only Preview run #40493645751](https://github.com/MaksimBlud/football-ai/actions/runs/40493645751), completed `2026-10-27T11:07:20Z`.
- Source capture ran current-form source/manifest regressions: **19 passed**. Its safe summary reports frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19-feature contract, 10 historical-season CSVs plus one current-season source file, 80 completed prior-day feature-input gate identities by count, `target_outcomes_read=false`, `target_outcomes_scored=false`, zero paid provider calls and zero Supabase writes.
- Downloaded source ZIP artifact `12730175586` and independently recomputed its SHA-256: `f0fb3565d2e5f44faadf488820c36327cb9d0d7b83b3da826af9b877f0804986`, matching the Actions upload digest. Source manifest SHA-256: `92a3372e027f59e38555548235c40a068fe407ce493aba6663c1a6e9ae081f74`. Current-source raw-byte SHA declared in the manifest: `6cf59ded608d3d23da083b1f8510d2ca22b219f0927f64addeaadfde1b495e11`. The independent archive audit did not open current-season score/result columns.
- Forward-only run executed **53 regression tests successfully**, then verified the actual GitHub source artifact and successful parent run. It reports unchanged candidate SHA, `source_file_count=11`, `feature_input_gate_count=80`, source observed at `2026-10-27T11:06:30.975279Z`, and source verification `VERIFIED`. Forward ZIP artifact `12729885760` was independently hashed: `399423f92edbb0f149b8040098184c0641aa1e08d9c15ad670aaf40ddc1139a0`, matching the Actions upload digest.
- **Critical scope limitation:** both runs executed on the old `main` SHA above. Its source capture uses a count-based feature-input gate and its forward reader does **not** yet have PR #699's independently recomputed fixture-identity-set/SHA coverage guard. Therefore these runs prove fresh source download, artifact ZIP/hash, parent-workflow provenance and old-path fail-closed no-quote behavior; they do **not** constitute live runtime proof of PR #699's new identity-set guard. That guard still needs exact-head CI, HUMAN-MERGE, and a post-merge live run.
- **No quote or forecast was produced:** `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `no_bet=true`; no target outcomes were read/scored, no paid calls, no Supabase writes and no production writes. Source-before-quote prediction ordering is not yet exercised with a genuine fresh quote.
- Fresh read-only audit of `public.odds_snapshots` at `2026-10-27T11:59:15Z`: 3,966 rows, latest snapshot `2026-10-13T14:48:53.04262Z`, zero snapshots in the last 24 hours and zero future pre-kickoff snapshots. This is the active blocker to a new forecast.
- Keep `active_lambda=0` as the exact de-vigged market and `shadow_lambda=1` research-only. This run proves source/archive integrity and fail-closed no-quote behavior, **not** predictive quality. Do not open protected target outcomes before the separately preregistered 30-primary-completed-event gate, and do not claim Brier/LogLoss superiority without the eligible independent cohort. No schedule or `main` changes.

## 2026-10-27 — exact current-form gate/source identity comparison (09:50 UTC)

- Downloaded the existing read-only source artifact #12647281024 from [run #40316117199](https://github.com/MaksimBlud/football-ai/actions/runs/40316117199). Recomputed archive ZIP SHA-256 exactly matches the recorded digest: `0ecfd702f0cd24f21894e93b0cbe63c65340a3eb48d3180e27652a3ad43c5e9b`. The ZIP contains 10 historical CSVs, `serie_a_2627.csv`, and the manifest.
- Inspected only `Date`, `HomeTeam`, and `AwayTeam` from the current-season CSV; no score/result columns were parsed. It contains 70 unique canonical fixture identities dated 2026-08-22 through 2026-10-19. Canonical identity-set SHA-256: `afc5b86fc2b116d4c2a46abd5dcd2453b64b13101abe618dd28cb66424e4fb73`.
- A fresh read-only query of `public.league_finished_results` selected only `match_date,home_team,away_team` for `SERIE_A`, season `2026-2027`, dates before 2026-10-27. It returned 83 rows / 80 unique canonical identities / 3 duplicate alias rows, spanning 2026-08-22 through 2026-10-25.
- Recomputed the same sorted identity-set SHA-256 over live metadata strictly through 2026-10-19; it is exactly `afc5b86fc2b116d4c2a46abd5dcd2453b64b13101abe618dd28cb66424e4fb73`. Therefore the archive's 70 identities match the earlier metadata set exactly; all ten additional current gate identities are later fixtures:
  - 2026-10-23 — Torino vs Monza
  - 2026-10-24 — Cagliari vs Bologna
  - 2026-10-24 — Como vs Sassuolo
  - 2026-10-24 — Lazio vs Parma
  - 2026-10-24 — Napoli vs AS Roma
  - 2026-10-25 — Atalanta vs Frosinone
  - 2026-10-25 — Genoa vs Venezia
  - 2026-10-25 — Inter Milan vs Fiorentina
  - 2026-10-25 — Lecce vs Juventus
  - 2026-10-25 — Udinese vs AC Milan
- This is a confirmed source freshness/coverage gap, not a guessed set difference. The Oct-26 archive's current-season CSV is stale relative to the latest completed-fixture metadata even though its archive timestamp is Oct-26. PR #699's current HEAD `3dc49392e905a2e3958180701a17b6bf7971204b` adds the identity-set attestation and fail-closed coverage checks; its exact-head CI is 7/7 SUCCESS (182 V2 shadow tests). Keep HUMAN-MERGE; no main merge.
- Odds audit remains unchanged: 3,966 saved snapshots, latest 2026-10-13 14:48:53 UTC, zero last-24h snapshots, zero future pre-kickoff snapshots. No forecasts or outcome evaluation are available. Evaluation gate remains closed until 30 eligible prospective forecasts complete.

## 2026-10-27 — gate/source identity proof strengthened; live gate has advanced (09:24 UTC)

- Fresh `main` is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`; default-branch commit date is 2026-10-18T08:20:05Z. No merge or main write was performed in this iteration.
- The daily source workflow on main remains `.github/workflows/serie-a-v2-current-form-source-capture.yml`, cron `50 5 * * *`. A read of scheduled Actions runs created since 2026-10-27T00:00Z found no `Serie A V2 Current-Form Source Capture` run as of 09:23Z; this is an absent run in the observed query window, not a claim that GitHub cannot deliver a delayed run.
- Latest real source capture is [run #40316117199](https://github.com/MaksimBlud/football-ai/actions/runs/40316117199), completed 2026-10-26T11:35:41Z on main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`; artifact `12647281024`, ZIP SHA-256 `0ecfd702f0cd24f21894e93b0cbe63c65340a3eb48d3180e27652a3ad43c5e9b`. It contains 10 frozen historical CSVs / 3,800 historical rows and 70 current-season completed rows; the feature-input gate at capture time was 70.
- Latest real forward preview is [run #40347056896](https://github.com/MaksimBlud/football-ai/actions/runs/40347056896), SUCCESS on main, 53 tests passed. It verified the source artifact and parent run, but `quotes_seen=0`, `v2_current_form_shadow_captured=0`, and read/scored no target outcomes. Artifact `12661661676`, ZIP SHA-256 `14dcf23a9787e491d5de5304473daf1ab5dca647d2371835951f1fce798906bf`. Its source freshness statement only reflects the old archive's age at that run, not today's gate coverage.
- Fresh read-only query of `public.league_finished_results` selected only `match_date,home_team,away_team` for Serie A 2026/27 before the current UTC date; no score/result fields were selected. It returned **83 raw rows / 80 canonical ordered fixture identities**, with three duplicate alias rows after `Atalanta BC → Atalanta`. The latest source archive has only 70 current-season identities, so it cannot cover all 80 current gate identities. Do not use it for new quote-time forecasts.
- This exposes an important pre-merge safety gap: current main's forward capture does not yet re-read the live feature-input identity set when deciding whether a source archive still covers the gate. Existing quote ledger currently has **3,966** snapshots, latest `2026-10-13T14:48:53.042620Z`, **0** snapshots in the last 24 hours and **0** future pre-kickoff snapshots, so no forecast was admitted; nevertheless, stale gate coverage must be fixed before any new quote is processed.
- Existing PR [#699](https://github.com/MaksimBlud/football-ai/pull/699) now has exact HEAD `3dc49392e905a2e3958180701a17b6bf7971204b`, **7/7 exact-head CI SUCCESS**. The frozen V2 shadow suite reports **182 passed**, and the production-model hash guard passed. The new change adds canonical metadata-only gate fixture identities to the source manifest and independently recomputes their count/SHA and checks actual subset coverage against the validated current-season CSV. Regression tests reject a self-claimed complete gate that substitutes an unrelated fixture and reject a missing identity list. Exact runs: [shadow #40480312989](https://github.com/MaksimBlud/football-ai/actions/runs/40480312989), [research #40480312997](https://github.com/MaksimBlud/football-ai/actions/runs/40480312997), [Serie A #40480313013](https://github.com/MaksimBlud/football-ai/actions/runs/40480313013), [Bundesliga #40480313122](https://github.com/MaksimBlud/football-ai/actions/runs/40480313122), [Ligue 1 #40480313003](https://github.com/MaksimBlud/football-ai/actions/runs/40480313003), [Eredivisie #40480313024](https://github.com/MaksimBlud/football-ai/actions/runs/40480313024), [Product #40480313035](https://github.com/MaksimBlud/football-ai/actions/runs/40480313035).
- PR #699 also consolidates the overlapping source-clock, event-identity, manifest-policy, historical CSV redirect, and frozen-dependency trigger protections from nearby PRs. Do not merge the overlapping variants independently; review #699's combined diff and then use HUMAN-MERGE. PR #699 remains open.
- No paid provider calls, Supabase writes/DDL, production `.pkl` changes, protected target-outcome reads, model refit, weight/feature/lambda changes, promotion, bets, or schedule changes. Frozen candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original feature count 19; `active_lambda=0` market baseline and `shadow_lambda=1` research only. Evaluation gate remains CLOSED until 30 eligible prospective forecasts complete; Brier/LogLoss and superiority claims remain unavailable.

---

## 2026-10-27 04:10 UTC — current-form gate/source clock ordering integrated on PR branch; no new quote

Current `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No merge or main change was performed.

Existing PR [#699](https://github.com/MaksimBlud/football-ai/pull/699) now has exact HEAD `0672312fd0b3d8ab4178736e1b3a9fe99fe446c1`, with **7/7 exact-head GitHub Actions SUCCESS**: Research [40448129312](https://github.com/MaksimBlud/football-ai/actions/runs/40448129312), original frozen V2 shadow tests [40448129283](https://github.com/MaksimBlud/football-ai/actions/runs/40448129283), Serie A [40448129275](https://github.com/MaksimBlud/football-ai/actions/runs/40448129275), Bundesliga [40448129287](https://github.com/MaksimBlud/football-ai/actions/runs/40448129287), Ligue 1 [40448129357](https://github.com/MaksimBlud/football-ai/actions/runs/40448129357), Eredivisie [40448129314](https://github.com/MaksimBlud/football-ai/actions/runs/40448129314), Product [40448129311](https://github.com/MaksimBlud/football-ai/actions/runs/40448129311). The exact frozen-shadow job ran the relevant V2/current-form suite: **127 passed**; production model hash guard passed.

The branch incorporates the temporal guard from overlapping PR #680: the metadata-only feature-input gate clock must be offset-aware and satisfy `gate_checked_at <= latest_source_observed_at <= archive_created_at`. Two regressions cover a gate clock later than the source and an offsetless gate clock, with the outer archive digest recomputed to reach temporal validation. #699 also consolidates the current-form protections from #694/#695/#688. It remains an unmerged research PR; no weights, feature order, candidate SHA, `active_lambda=0`, `shadow_lambda=1`, schedules, production artifacts, or Supabase data/schema were changed.

**Integration is not yet complete:** historical CSV redirect protection is separately proposed in #683/#700, while dependency path-trigger coverage is in #696/#698. Their overlapping workflow/source hunks must be reconciled and the full CI rerun on the exact combined SHA before HUMAN-MERGE. Per-PR green CI does not prove the combined head.

Fresh read-only Supabase audit selected only `match_date,home_team,away_team` for the Serie A 2026/27 feature-input gate and no target results. It returned 73 raw metadata rows, including three Atalanta alias duplicates, which normalize to 70 fixture identities. The odds ledger has **3,966** rows, latest snapshot `2026-10-13 14:48:53.04262+00`, **0** snapshots in the last 24 hours and **0** future pre-kickoff snapshots. The current-main source artifact #12647281024 remains the latest verified source archive; no fresh quote exists, so no new forecast can be admitted and the 30-completed-prospective-forecast evaluation gate remains CLOSED. Brier/LogLoss and any superiority claim remain unavailable. No target outcome values were queried, no paid provider call or Supabase write/DDL occurred.

A separate Supabase schema advisor still reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. This is a critical access-control warning; no DDL was applied because enabling RLS without designed policies can break legitimate application access.

---

## 2026-10-26 — exact-head V2 outcome-key hardening and current source-archive attestation

The main branch remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no PR was merged by this automation. Existing original-V2 safety PR #678 was updated in place (not duplicated) to HEAD `130950e112e8fb7e9f5cd9ebf17914617aa78d2b`. Its frozen shadow input guard now rejects additional normalized final-score/full-time aliases (including `finalHomeScore`, `fullTimeResult`, `scoreLine`, `homeScoreFT`, and `goalsHome`) in top-level and feature payloads. Exact-head CI is **7/7 SUCCESS**; the specialized frozen V2 workflow reports **115 passed**, and `git diff --exit-code -- '*.pkl'` passed. Exact runs: Research [40408668054](https://github.com/MaksimBlud/football-ai/actions/runs/40408668054), Product [40408668074](https://github.com/MaksimBlud/football-ai/actions/runs/40408668074), Serie A Frozen V2 Shadow [40408667993](https://github.com/MaksimBlud/football-ai/actions/runs/40408667993), Serie A [40408668101](https://github.com/MaksimBlud/football-ai/actions/runs/40408668101), Ligue 1 [40408668056](https://github.com/MaksimBlud/football-ai/actions/runs/40408668056), Bundesliga [40408668050](https://github.com/MaksimBlud/football-ai/actions/runs/40408668050), and Eredivisie [40408668006](https://github.com/MaksimBlud/football-ai/actions/runs/40408668006). PR #678 remains open for HUMAN-MERGE; original 19-feature order, frozen candidate/weights, `active_lambda=0`, `shadow_lambda=1`, gates, production artifacts, Supabase, and schedules are unchanged.

Downloaded and independently inspected the real current-main source artifact from successful [Current-Form Source Capture run #40316117199](https://github.com/MaksimBlud/football-ai/actions/runs/40316117199): artifact `12647281024`, GitHub digest and ZIP SHA-256 `0ecfd702f0cd24f21894e93b0cbe63c65340a3eb48d3180e27652a3ad43c5e9b`. Manifest source archive time is `2026-10-26T11:35:37.777651Z`; it pins frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 original features, ten historical CSVs / 3,800 historical rows, and current-season CSV SHA-256 `8d4a049abd91d687a63b95051828c00a440c7444e1614a52025addf76a0fb763`. The metadata-only feature-input gate passed at 70 unique completed primary fixture identities; the archived current-season CSV also has 70 completed prior-day rows. The current-main manifest attests counts but not the canonical metadata-vs-CSV identity-set hash; open PR #699 (HEAD `ee19d3ef9619fbc0a3b237d45cdc3523ffe10bdf`, 7/7 CI SUCCESS) adds exact identity-set coverage/hash and is still unmerged. Source artifact itself remains non-forecast/non-product eligible; no target outcomes were read/scored, no Supabase writes or paid provider calls occurred, and the separate evaluation gate remains CLOSED until 30 eligible prospective V2 forecasts have completed.

Fresh read-only `public.odds_snapshots` aggregate: 3,966 rows, latest snapshot `2026-10-13 14:48:53.04262+00`, zero future pre-kickoff rows, zero fresh future pre-kickoff rows in the last 24 hours; 51 rows are at/after kickoff and excluded from prospective evaluation. Thus no new V2 forecast or quote-level source-before-quote evidence can be added yet. Brier/LogLoss and any superiority claim remain unavailable. No Supabase writes/DDL, paid calls, protected outcome reads, model refit/promotion, or main change.

---

# Football AI — Project Continuity


## 2026-10-26 19:56 UTC — original historical CSV redirects fail closed; no fresh quotes

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. New V2-only PR [#700](https://github.com/MaksimBlud/football-ai/pull/700) adds exact HTTPS host/path validation for the ten frozen pre-2026/27 Football-Data CSVs, disables automatic redirects, and requires the final response URL to equal the approved URL before response bytes are read. Offline regressions cover HTTP redirects, unexpected final URLs, and an unapproved endpoint. Existing current-form source/forward workflow path filters now include this shared historical-source reader and test; cron cadence is unchanged.

PR #700 exact head `d2a6608ef8c11d2e517f8aec5637d12206760346` has **7/7 exact-head CI SUCCESS**: Research [40391014094](https://github.com/MaksimBlud/football-ai/actions/runs/40391014094), Serie A [40391014224](https://github.com/MaksimBlud/football-ai/actions/runs/40391014224), Ligue 1 [40391014341](https://github.com/MaksimBlud/football-ai/actions/runs/40391014341), Bundesliga [40391014365](https://github.com/MaksimBlud/football-ai/actions/runs/40391014365), Original Frozen V2 Shadow [40391014350](https://github.com/MaksimBlud/football-ai/actions/runs/40391014350), Product [40391014439](https://github.com/MaksimBlud/football-ai/actions/runs/40391014439), Eredivisie [40391014491](https://github.com/MaksimBlud/football-ai/actions/runs/40391014491). PR remains open for HUMAN-MERGE; no main change or merge.

Fresh read-only Supabase checks at this iteration: `public.odds_snapshots` contains **3,966** rows; latest snapshot is still `2026-10-13 14:48:53.04262+00`; selecting future kickoff rows returned **0**. Serie A 2026/27 metadata-only query returned **73 raw rows** (only match date/team identity fields were selected; no score/result fields). This does not establish new source-before-quote observations because no quote exists. No paid provider calls, Supabase writes/DDL, protected outcome reads, model changes, or schedule cadence changes.

Scientific status remains unchanged: original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features and weights frozen, `active_lambda=0` market fallback, `shadow_lambda=1` research only. The 30-prospective-completed-event evaluation gate remains closed; no Brier/LogLoss or superiority claim is available.

---
## 2026-10-26 18:56 UTC — separate original-path clock guards still await HUMAN-MERGE

Fresh GitHub reads reconfirmed `main` at `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The current-form integration [PR #699](https://github.com/MaksimBlud/football-ai/pull/699), exact head `ee19d3ef9619fbc0a3b237d45cdc3523ffe10bdf`, has **7/7 exact-head CI SUCCESS** (all seven workflow runs completed successfully). Its changed-file list is limited to the current-form source/forward modules and their tests; it does **not** change the separate original-path modules below.

A fresh source scan found that unchanged `main` still checks only `tzinfo is None` in the following original V2 entry points, without rejecting a custom `tzinfo` whose `utcoffset()` is `None`:

- `serie_a_v2_attest_real_source.py::attest_latest_source` and `serie_a_v2_forward_capture.py::prepare_forward_capture`: covered by open PR [#677](https://github.com/MaksimBlud/football-ai/pull/677), exact head `cc8b13d44b38b2e12ae5d1bc840221a7f6b96c8c`, **7/7 exact-head CI SUCCESS**. That PR also validates all snapshots for stable event identity before any source callback and blocks stale quotes before source selection.
- `serie_a_v2_prequote_source_archive_gate.py::verify_archive`, `serie_a_v2_frozen_shadow_preview.py::shadow_preview/fetch_saved_upcoming_serie_a_quotes`, and `serie_a_v2_live_diagnostic_report.py::make_report`: covered by open PR [#678](https://github.com/MaksimBlud/football-ai/pull/678), exact head `82dbfaa39a0e41ce93ff5539078663994777210b`, **7/7 exact-head CI SUCCESS**.

Both PRs remain open and unmerged. Their guards are not live on `main`; review and manual merge are still required. No duplicate branch was created. Current-form-only PRs #675, #676, #679 and #680 also remain open and touch files that overlap PR #699; reconcile exact diffs rather than merging overlapping branches independently.

**Fresh read-only runtime/data check:** current-form forward run [40347056896](https://github.com/MaksimBlud/football-ai/actions/runs/40347056896) verified source artifact `12647281024` and its SHA, the successful parent run, 70 feature-input-gate identities, 3,870 old-season match rows and frozen candidate SHA; 53 tests passed, but it saw **0 saved quotes and captured 0 shadows**. Original forward run [40346041505](https://github.com/MaksimBlud/football-ai/actions/runs/40346041505) passed 71 tests and also saw 0 quotes. A read-only per-league aggregate of `public.odds_snapshots` during this audit found **0 future-kickoff pre-match snapshots of any age** and **0 within 24 hours** across all nine leagues. No quote means no new forecast and no actual new quote-level source-before-quote proof.

No protected target outcomes were read, no Supabase writes/DDL or paid calls were made, and no schedule, frozen feature/weight contract, production artifact, or `main` ref changed. The separate 30-eligible-prospective-completed-forecast evaluation gate remains CLOSED; Brier/LogLoss and any superiority claim remain unavailable.

## 2026-10-26 — metadata identity audit and open-PR CI status

A fresh read-only Supabase query selected only `match_date,home_team,away_team` from the Serie A 2026/27 feature-input metadata; no score/result fields were selected. It returned **73 raw rows and 70 canonical fixture identities** after the V2-local `Atalanta BC → Atalanta` alias. The three duplicated representations are 2026-08-23 Atalanta–Sassuolo, 2026-08-31 Atalanta–Bologna, and 2026-09-05 AS Roma–Atalanta. Thus 73 raw rows versus the earlier 70-row source archive is explained by aliases at the count level, but exact source/metadata set parity still must be proven by the runtime identity check.

A separate read-only `public.odds_snapshots` aggregate found **0 future pre-kickoff quote rows**, **0 such rows in the last 24 hours**, and no future event IDs with saved snapshots. The latest stored snapshot remains `2026-10-13 14:48:53.04262+00`. No target outcomes were selected, and no Supabase write/DDL was executed.

Fresh `main` code still validates only the feature-source event count. Open PR [#699](https://github.com/MaksimBlud/football-ai/pull/699) adds a fail-closed canonical identity set-difference check. Exact head `8e658ac9411fc9e1081f015013c77092d38f21fa` has **7/7 exact-head CI SUCCESS** (runs 40345533303, 40345533392, 40345533254, 40345533452, 40345533492, 40345533764, 40345533446), but remains open for HUMAN-MERGE. Related workflow dependency-trigger PRs #693 (`41531ee98403e49dc4a48d0c4c1ceefa089306d2`), #696 (`c9edeace674dfad8d58dc44e474331c52b3dc5d8`), and #698 (`5678cb090cb19ebba67e2fb31edd35c6c7fe9938`) also have recorded 7/7 exact-head CI success and remain open. PR CI is not evidence of deployment.

The previous documentation head `1c59e5f58686c9552f0a2f9ab0d9ee84df145672` passed all seven PR-validation workflows (runs 40354188995, 40354188653, 40354188832, 40354188667, 40354188605, 40354188602, 40354188789). This update changes the documentation PR head and must receive its own exact-head CI before review. Main SHA remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge was performed.

**Current blocker:** no eligible saved pre-match quotes means no new forecast observations. The 30-completed-prospective-event outcome gate remains closed. Do not backfill October 13 quotes, change the frozen 19-feature/weight contract, or claim V2 superiority.

---

## 2026-10-26 15:13 UTC — second live forward proof, still no admissible quotes

Fresh read-only verification on unchanged `main` SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`:

- **Current-form forward-only preview** [run 40347056896](https://github.com/MaksimBlud/football-ai/actions/runs/40347056896) completed SUCCESS at 15:13:20Z; its six-file regression suite passed **53 tests**. The runtime report verified current-form source artifact `12647281024`, ZIP SHA-256 `0ecfd702f0cd24f21894e93b0cbe63c65340a3eb48d3180e27652a3ad43c5e9b`, successful parent run `40316117199`, parent SHA equal to main, source observation `2026-10-26T11:35:37.712979Z`, and the frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. Gate count/current-season rows = **70**, frozen history = **3,870 matches across 10 old-season CSVs**. At verification time source age was 13,054 seconds (~3 h 38 min), below the fixed 24-hour source-age cap. The run saw **0 saved quotes**, captured **0** current-form shadow forecasts, read/scored **0** target outcomes, made **0** paid-provider calls and **0** production/Supabase writes. Artifact `12661661676`, uploaded ZIP SHA-256 `14dcf23a9787e491d5de5304473daf1ab5dca647d2371835951f1fce798906bf`.
- **Original frozen V2 forward-only preview** [run 40346041505](https://github.com/MaksimBlud/football-ai/actions/runs/40346041505) completed SUCCESS at 15:07:09Z; **71 tests passed**. The independent real-source attestation verified artifact `12651690084` and SHA, 10 pre-prospective source files / 3,800 historical matches. Its original V2 quote pass saw **0 quotes** and generated **0** previews. No paid calls, Supabase writes, or protected-outcome reads. Artifact `12660854128`, uploaded ZIP SHA-256 `8916346ea8b9051879f021f9cc64e3c07c7ffd8b71896890a3eb6b71b5ad84c5`.

The separate read-only Supabase aggregate at 15:51Z still returns **0** future pre-kickoff quote rows and **0** such rows in the last 24 hours; latest stored quote remains `2026-10-13 14:48:53.04262+00`. These runs prove the source/forward code executes and authenticates the old source, not `source-before-quote` for a new market observation and not model quality. Do not relax freshness, backfill old quotes, open the protected 30-completed-event evaluation gate, or claim V2 beats market. No main merge or schedule change was performed.

---

## 2026-10-26 — schedule-observation note — 2026-10-26 13:05 UTC

The source-capture workflow on fresh `main` declares cron `50 5 * * *` (05:50 UTC). Its successful scheduled run `40316117199` was created/started at `2026-10-26T11:34:50Z`, **5 h 44 min 50 s after the nominal cron time**. This is one observed schedule-time discrepancy, not enough evidence to conclude a persistent outage or to change the schedule. The run itself completed successfully at 11:35:41Z and produced source artifact `12647281024`; the chained forward preview `40316226164` completed successfully but had zero saved quotes and zero forecasts. Do not change workflow schedules or other agents on the basis of this single observation; monitor subsequent scheduled runs and preserve HUMAN-MERGE.

---

## 2026-10-26 11:57 UTC — fresh live current-form source and forward run

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; original frozen candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. No main change or merge was performed.

**New actual source-capture proof:** [run 40316117199](https://github.com/MaksimBlud/football-ai/actions/runs/40316117199) completed SUCCESS on the exact main SHA. It ran the real read-only capture, passed **19 tests**, and emitted `completed_primary_events=70`, `current_season_completed_prior_day_rows=70`, ten frozen historical CSVs plus one current-season CSV, and **3,870 historical match rows**. Uploaded artifact [12647281024](https://github.com/MaksimBlud/football-ai/actions/runs/40316117199/artifacts/12647281024), GitHub artifact ZIP SHA-256 `0ecfd702f0cd24f21894e93b0cbe63c65340a3eb48d3180e27652a3ad43c5e9b`. Candidate SHA in the runtime report matches the frozen original.

**New actual current-form forward proof:** [run 40316226164](https://github.com/MaksimBlud/football-ai/actions/runs/40316226164) completed SUCCESS on the same main SHA, passed **53 tests**, independently verified source artifact 12647281024 and successful parent run 40316117199, verified artifact SHA and candidate SHA, and reported latest source observation `2026-10-26T11:35:37.712979Z`. Verification was performed at `2026-10-26T11:36:18.447045Z`; source age was 40 seconds. The run read **0 saved quotes**, captured **0 new V2 shadows**, read/scored **0 target outcomes**, made **0 paid-provider calls**, and made **0 Supabase writes**. Its report artifact is [12647321126](https://github.com/MaksimBlud/football-ai/actions/runs/40316226164/artifacts/12647321126), uploaded ZIP SHA-256 `c4148dbcdb2151edcf069b1735a4213d2ca6a49e5ebd5492bc1fb036a79f1d4e`. This is live provenance/runtime evidence, not prediction-quality evidence; no quote existed to test a real quote's source-before-quote ordering.

**Read-only gate/market recheck at 11:57 UTC:** `public.league_finished_results` metadata-only aggregation returned 73 raw Serie A 2026/27 rows and 70 unique ordered fixture identities after the exact runtime aliases (Inter/Milan/Roma/Verona plus the V2-local Atalanta BC alias); canonical unordered identity count was also 70, so no reversed canonical pair was observed. The live source run's 70-event gate count is consistent with this normalization. However, that run predates open PR #694's explicit identity-set SHA/parity manifest; do not claim that the archive has passed the new set-equality attestation until that code is integrated and a new run proves it.

The read-only `public.odds_snapshots` query selected only snapshot/kickoff timestamps and aggregate counts: **0 future-kickoff rows**, **0 within the last 24 hours**, latest saved snapshot `2026-10-13T14:48:53.042620Z`. No outcome fields were selected. New prediction capture and scientific scoring remain blocked by absence of saved pre-match quotes.

No protected 2026/27 target outcomes were read; no paid calls, Supabase writes/DDL, production `.pkl` changes, refits, promotions, or bets occurred. The separate 30-eligible-prospective-completed-event evaluation gate remains CLOSED. Brier/LogLoss and any claim that V2 beats market remain unavailable.

---

## 2026-10-26 09:09 UTC — current-form source clocks hardened; runtime-data blocker persists

Fresh `main` verified at `40887ebb215730190d7a6c7a1693373ec4afcdfc`; frozen original candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. No main update or merge was performed.

**New code proof in existing PR #694:** exact head `c9022e5a6ca5711c3b37ff3c48886bc9919652f4`, base `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Current-form source capture now rejects a non-datetime, missing tzinfo, or `utcoffset() is None` for the metadata gate clock, CSV cutoff clock, capture-entry clock, source-observation clock, and archive-creation clock. Five regressions prove invalid clocks fail before the relevant Supabase read, body consumption, or current-source/manifest write. Exact-head CI is **7/7 SUCCESS**: [V2 shadow](https://github.com/MaksimBlud/football-ai/actions/runs/40297046024), [Research](https://github.com/MaksimBlud/football-ai/actions/runs/40297046036), [Serie A](https://github.com/MaksimBlud/football-ai/actions/runs/40297046058), [Bundesliga](https://github.com/MaksimBlud/football-ai/actions/runs/40297046048), [Ligue 1](https://github.com/MaksimBlud/football-ai/actions/runs/40297046103), [Eredivisie](https://github.com/MaksimBlud/football-ai/actions/runs/40297046134), [Product](https://github.com/MaksimBlud/football-ai/actions/runs/40297046061). PR remains open, HUMAN-MERGE only.

**Current-form workflow trigger coverage:** open PR #698 head `5678cb090cb19ebba67e2fb31edd35c6c7fe9938` passed **7/7** exact-head CI. PR #696 head `2a4059860fcb7da2eab39b538b4e264ef6fc8192` also passed **7/7**. #694 and #696 overlap on `serie_a_v2_current_form_forward_capture.py` and its tests; reconcile those before any manual merge. #698 changes the distinct current-form forward workflow and manual-trigger contract test. No PR is to be auto-merged.

**Current live-data blocker (read-only, 2026-10-26 09:08–09:09 UTC):**
- Supabase feature-input metadata query selected only `match_date, home_team, away_team` and returned **73** unique Serie A 2026/27 fixture identities (first 2026-08-22, last 2026-10-19). No score/result columns were read.
- `public.odds_snapshots` query used only league, snapshot/kickoff timestamps, event IDs and market prices. It found **0** future-kickoff pre-match snapshots in the last 24 hours and **0** future-kickoff pre-match snapshots of any age across all nine leagues. Latest saved Serie A snapshot remains 2026-10-13 14:48:53 UTC; EPL 2026-10-09 15:25:57 UTC; RPL 2026-09-05 15:07:55 UTC.
- The Oct 26 `main` Actions run list contained 119 runs but no `Serie A V2 Current-Form Source Capture` or `Serie A V2 Current-Form Forward-Only Preview` run. Their YAML schedules remain 05:50 UTC and 08:18 UTC; reason for missing executions is not established.
- Last verified live source capture remains run [40183765742](https://github.com/MaksimBlud/football-ai/actions/runs/40183765742) with 70 current-season source rows, while metadata now reports 73 identities. The current-form parity gate must fail closed until a new successful capture includes every eligible identity. Last verified current-form forward preview remains run [40196498784](https://github.com/MaksimBlud/football-ai/actions/runs/40196498784); it admitted **0** forecasts because its saved quotes were stale.

No new predictions were created; no protected 2026/27 outcomes were read; no Supabase writes/DDL, paid provider calls, production `.pkl` changes, refit, promotion, or bets occurred. The separate 30-eligible-prospective-completed-event evaluation gate remains CLOSED; Brier/LogLoss comparison and any V2 superiority claim remain unavailable.

**Security note:** Supabase schema advisory still reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No setting was changed; admin policy review is required before enabling RLS.

---

## 2026-10-26 — Forward-only clock guard closes custom offsetless-tzinfo path

Fresh main rechecked: `40887ebb215730190d7a6c7a1693373ec4afcdfc`; frozen original V2 candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. Main was not changed.

Updated existing HUMAN-MERGE PR #696 on branch `research/v2-current-form-dependency-recheck-20261025`, exact head `2a4059860fcb7da2eab39b538b4e264ef6fc8192`. Review found that the new `verify_latest_source_archive` helper and `prepare_forward_capture` entry point only checked `tzinfo is None`. A custom tzinfo with `utcoffset() is None` could still be normalized using the runner's local timezone. Both entry points now reject non-datetime, naive, and offsetless clocks before callbacks or output writes. Regression coverage tests both entry points and proves source callbacks/output writes do not occur for an invalid clock.

Exact-head CI for #696: **7/7 SUCCESS**. Original V2 shadow job [run 40289658905](https://github.com/MaksimBlud/football-ai/actions/runs/40289658905) reports **96 tests passed** and confirms `git diff --exit-code -- '*.pkl'`. Other exact-head successful runs: [Research](https://github.com/MaksimBlud/football-ai/actions/runs/40289659034), [Product](https://github.com/MaksimBlud/football-ai/actions/runs/40289659162), [Eredivisie](https://github.com/MaksimBlud/football-ai/actions/runs/40289658892), [Bundesliga](https://github.com/MaksimBlud/football-ai/actions/runs/40289658889), [Serie A](https://github.com/MaksimBlud/football-ai/actions/runs/40289659001), [Ligue 1](https://github.com/MaksimBlud/football-ai/actions/runs/40289659018). PR remains open and unmerged.

Read-only Supabase `public.odds_snapshots` audit at **2026-10-26 08:04:02 UTC**: 0 quote rows for future kickoffs in the prior 24 hours; 0 saved future-kickoff quote rows of any age; latest future-kickoff quote is null; latest quote in the table is `2026-10-13 14:48:53 UTC`. No score/result fields were queried. The source-capture workflow YAML still specifies daily `05:50 UTC`, but the queried set of 111 main-branch workflow runs created on Oct 26 contains no `Serie A V2 Current-Form Source Capture` or `Serie A V2 Current-Form Forward-Only Preview` run. Therefore no new on-main source artifact or forward runtime proof is claimed for Oct 26. Last documented live source/forward evidence remains the Oct 25 runs below.

No model feature/weight/lambda changes, production `.pkl` edits, Supabase writes/DDL, paid calls, target-outcome reads, evaluation-gate opening, or merges. The 30-completed-prospective-forecast evaluation gate remains CLOSED; no Brier/LogLoss comparison is available.

---

## 2026-10-26 — Source-gate parity and transitive CI dependency hardening (runtime still blocked)

Latest checked `main` is still `40887ebb215730190d7a6c7a1693373ec4afcdfc` (commit 2026-10-18); this document update is on the existing documentation PR branch only. The frozen original candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. No production model, frozen feature contract, weights, lambda settings, or main-branch files were changed.

**Exact-head CI results for open V2 PRs (not merged):**
- PR #694 head `6e68c032a108c3962005ed625ee1a5ed854575b8`: **7/7 checks SUCCESS**; the original V2 shadow job ran **100 tests PASS**. Added defensive source-gate checks for pre-season metadata and reversed duplicate fixtures after V2-local alias normalization, in both count and identity paths.
- PR #693 head `41531ee98403e49dc4a48d0c4c1ceefa089306d2`: **7/7 checks SUCCESS**; **89 tests PASS**. The free diagnostic now triggers and compiles both `market_anchor_1x2_v2_shadow.py` and its transitive dependency `market_anchor_1x2_v1.py`.
- PR #698 head `5678cb090cb19ebba67e2fb31edd35c6c7fe9938`: **7/7 checks SUCCESS**; **86 tests PASS**. The current-form forward workflow now triggers and compiles both residual/runtime modules.
- PR #696 head `783b4a0a8dfb7b9baf2ecd49bcb04dd884d6a523`: **7/7 checks SUCCESS**, `Serie A Frozen V2 Shadow Tests` ran **94 tests PASS**. It extends dependency coverage to the original forward and current-form source-capture workflows and the frozen-shadow PR path filter.
- PR #695 head `b721154f73a050f8b2648b1dd7d41ab4951f8033`: **7/7 checks SUCCESS** in isolation. It attests the frozen candidate before source access and requires the exact approved HTTPS URL plus a direct HTTP 200; it overlaps #694 in `serie_a_v2_current_form_source_capture.py`, so integration must preserve both sets of guards and rerun CI on the final combined SHA.
- PRs #693, #694, #695, #696 and #698 remain open and unmerged. HUMAN-MERGE remains mandatory. #694 and #695 overlap in the source-capture module; #693, #696 and #698 cover separate workflow-trigger surfaces. Before any manual integration, preserve all guards/tests, resolve overlap deliberately, and rerun the complete CI on the exact final SHA.

**Fresh read-only odds audit (Supabase `public.odds_snapshots` only):** grouped by league using `snapshot_time_utc`, `commence_time_utc`, `event_id`, and `league`; no score/result columns were read. There are **0 pre-match quote rows in the last 24 hours** and **0 saved quote events whose kickoff is still in the future**. Latest saved pre-match snapshots are Serie A 2026-10-13 14:48:53 UTC, EPL 2026-10-09 15:25:57 UTC, RPL 2026-09-05 15:07:55 UTC, and the other six queried leagues last on 2026-09-11. Therefore there is no current admissible quote to pair with the source archive; do not backfill or relax the 24-hour/source-before-quote rules.

**Scientific state unchanged:** active lambda remains 0 (market anchor); lambda 1 remains research-only shadow. The separate prospective outcome gate remains closed until 30 eligible forecasts from the preregistered cohort have completed. No protected 2026/27 target outcomes were read; no Brier/LogLoss comparison or V2-over-market claim is available. No paid odds calls, Supabase writes/DDL, production `.pkl` edits, refit, threshold tuning, or promotion occurred.

**Next:** finish exact-head CI for #696; keep the three passing PRs unmerged until integration order/conflicts are checked; after HUMAN-MERGE, read fresh main and verify the live source archive/parent-run SHA and source-before-quote ordering. Wait for a genuinely new, user-authorized pre-kickoff quote saved after the source archive; only then capture prospective frozen V2 shadow, still NO_BET and outcome-blind until the separate 30-completed-forecast gate.

---

## 2026-10-25 — Reconciled live source/forward proof and current data blocker

Fresh main inspected for this update: `40887ebb215730190d7a6c7a1693373ec4afcdfc` (PR #673; the original V2 candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`). The live source and forward workflows have now run on this exact main; this supersedes the October 18 statement below that first post-merge runtime proof was still pending.

**Verified source capture:** [run #40183765742](https://github.com/MaksimBlud/football-ai/actions/runs/40183765742) completed successfully at 2026-10-25 10:12:36 UTC. Artifact `12595098381`, ZIP SHA-256 `6268eab2b690fb5feb02287a1c0af55afb510afe6a86b73b1bcb33094fa6ff22`, 10 frozen historical CSVs plus current-season `2627/I1.csv`, 3,800 historical match rows plus 70 completed current-season rows. The metadata-only feature-input gate observed 70 completed Serie A fixtures at capture time. Frozen candidate SHA verified. Paid provider calls: 0; Supabase writes: 0; target outcomes read/scored: false.

**Verified original forward-only run:** [run #40196251553](https://github.com/MaksimBlud/football-ai/actions/runs/40196251553) completed successfully at 2026-10-25 13:09:06 UTC. Four saved future quotes were inspected; all four were blocked as having no earlier source archive. Zero previews were captured. The October 13 quotes remain inadmissible because the source archive was created later; no backfill.

**Verified current-form forward-only run:** [run #40196498784](https://github.com/MaksimBlud/football-ai/actions/runs/40196498784) completed successfully at 2026-10-25 13:12:21 UTC. The current-form source artifact and parent run were verified, but all four saved quotes were blocked as stale (`STALE_MARKET_QUOTE`); zero V2 shadows were captured. No paid calls, Supabase writes, or target-outcome reads.

**Fresh read-only Supabase audit, 2026-10-25:** the current metadata-only feature-input count is now 73 unique completed fixture identities (only `match_date,home_team,away_team` selected; no scores/results). The archived source correctly contains 70 because it was captured at 10:12 UTC, before three additional fixture identities appeared in the later metadata view. Across all nine checked leagues, there are currently zero fresh future pre-match quote snapshots in the last 24 hours and zero future events with any saved pre-match snapshot. The existing quote supply is the binding blocker, not a reason to relax freshness or source-before-quote checks.

**Scientific status unchanged:** current-form source is research-only; `active_lambda=0` remains the exact de-vigged market, `shadow_lambda=1` is inactive research shadow, and NO_BET/product publication remain enforced. The evaluation gate stays CLOSED until 30 eligible prospective forecasts have completed. The 70/73 feature-input metadata counts do not satisfy that outcome gate. Do not read protected 2026/27 target outcomes, backfill October 13 quotes, refit/tune, or claim V2 beats market without independent Brier/LogLoss evaluation.

**Integration status:** relevant hardening remains in open HUMAN-MERGE PRs (#676/#677 clock and event identity, #688 malformed source rows and metadata boundary, #694 gate-to-CSV identity coverage, #695 frozen candidate/current URL verification, #696 dependency-trigger coverage). Their individual green CI does not establish combined compatibility; compare overlaps and rerun exact-head CI after human integration. No PR was merged and main/production artifacts were not changed by this audit.

---



## 2026-10-26 — Additional live source/forward proof and free diagnostic

Fresh read-only audit on 2026-10-26 confirms that the original V2 source/forward pipeline ran on the unchanged `main` SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`:

- [Source Capture run 40316117199](https://github.com/MaksimBlud/football-ai/actions/runs/40316117199) completed SUCCESS at 2026-10-26T11:35:41Z. 19 tests passed; gate count 70; current-season prior-day rows 70; historical source 10 CSV / 3,870 matches; total source files 11; candidate SHA remained `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. Source artifact `12647281024`, ZIP SHA-256 `0ecfd702f0cd24f21894e93b0cbe63c65340a3eb48d3180e27652a3ad43c5e9b`.
- [Current-Form Forward-Only Preview run 40316226164](https://github.com/MaksimBlud/football-ai/actions/runs/40316226164) completed SUCCESS. 53 tests passed; source archive and parent workflow provenance verified; source age was 40 seconds at verification; 0 saved quotes were eligible, 0 shadow forecasts were captured, 0 target outcomes were read/scored, 0 paid provider calls, and 0 Supabase writes. Forward artifact `12647321126`, ZIP SHA-256 `c4148dbcdb2151edcf069b1735a4213d2ca6a49e5ebd5492bc1fb036a79f1d4e`.
- [Free real-quote diagnostic run 40325839042](https://github.com/MaksimBlud/football-ai/actions/runs/40325839042) completed SUCCESS at 12:52Z; 53 tests passed and a new diagnostic/source artifact `12651690084` was uploaded (ZIP SHA-256 `f58de4b962978f86574ccaf761a7f4b2ca3e8e00a182ce305d61cdb9fb68e537`). The report explicitly says `quoted_fixtures=0`, `diagnostic_scored=0`, `eligible_for_frozen_prospective_cohort=false`, `eligible_for_product_publication=false`, and `mode=RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`.
- Read-only Supabase odds audit at `2026-10-26T14:01:11Z` found 0 future prematch snapshots total and 0 in the previous 24 hours; latest valid prematch snapshot remains `2026-10-13T14:48:53Z`. This blocks new prospective inference. No target outcomes were queried.

This is genuine runtime/source-provenance evidence, **not** a prediction-quality result. Since there were no eligible quotes, the run does not demonstrate source-before-quote for a new market observation and does not count toward the 30-primary-completed-event evaluation gate. The current main still lacks the unmerged hardening in PRs #694/#695/#688/#692; those remain separate review work. No weights/features, active lambda, production artifacts, database rows/schema, or protected outcomes were changed.



## 2026-10-18 — Original V2: preregistered current-form forward-only source and quote pipeline (runtime proof pending)

PRs #668 and #669 are now merged to main: exact original feature-builder parity is pinned to `historical_football_signal_lab.py` Git blob `401b3a0893371bfa4a488ec92a4a54af2678c8f7`, and the original lambda-1 shadow vector is pinned to an exact 1e-12 reference; stale SHA weight tampering fails closed. Latest main before this new branch: `a3db1325f9ad29d2cbf412e0f8e1d7a43642acbf`.

**New contract, separate cohort:** `experiments/market_anchor_1x2_v2_current_form_policy.json` and `research/SERIE_A_V2_CURRENT_FORM_FORWARD_ONLY_CONTRACT_20261018.md` preregister the same unchanged frozen V2 candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with current-season history allowed only as lagged inputs to future quotes. The original old-season-only cohort and protocol remain unchanged; the October 13 quotes cannot be backfilled.

Feature-input gate queries only `match_date,home_team,away_team` (no score/result columns) from Serie A 2026/27 results metadata and requires 30 unique completed fixtures. Read-only metadata query on 2026-10-18 returned **63** unique fixtures; this is solely a feature-input gate and does **not** satisfy the separate evaluation gate. The latter remains CLOSED until **30 eligible prospective V2 forecasts** from the new cohort have completed. Target outcomes are never read or scored in source/forward capture; no model refit, selection, threshold tuning, production change, paid provider request, or Supabase write.

New code/workflows under review: `serie_a_v2_current_form_source_capture.py` plus daily `Serie A V2 Current-Form Source Capture` archives ten frozen history CSVs plus current `2627/I1.csv` after the input gate, with exact hashes and timestamps. `serie_a_v2_current_form_forward_capture.py` plus `Serie A V2 Current-Form Forward-Only Preview` accepts only source artifact + successful main parent run completed before quote, current source age <=24h, quote age <=24h and strictly pre-kickoff. It reads existing saved odds only and captures research-only lambda-1 residual shadow plus exact de-vigged market fallback; active lambda remains 0, NO_BET, no publication.

**Not yet verified:** new branch CI and first post-merge live source/forward runs. Expected first live run must capture 11 source CSVs only after the gate and prove hashes; existing Oct13 quotes must remain blocked as stale/source-after-quote. No prospective result metrics can be claimed until new pre-kickoff quotes and the 30-event target outcome gate are satisfied.


## 2026-10-14 — Original V2: actual 20/20 feature coverage restored, real runtime proof and stale-form limit

**PR #665 MERGED** to main `3afc76d2ca056a31623b3c5ff9a22389dc3518e4` after 8/8 full CI: exact original 19-feature V2 source team match counts, per-venue prior sample, date and imputation evidence; zero-evidence/all-median shadow pseudo forecasts fail closed, original weights/feature definitions/market-fallback untouched. [Real free source diagnostic run 38588541087](https://github.com/MaksimBlud/football-ai/actions/runs/38588541087) SUCCESS: 46 tests PASS, actual 20 bookmaker fixtures, 18/20 full features, 2/20 all-imputed, output source archive `11906114191`. Both all-imputed were exactly **Atalanta BC–Frosinone** and **AC Milan–Atalanta BC**. Verified all 10 real Football-Data historical CSVs spell club `Atalanta`, while bookmaker uses `Atalanta BC`.

**PR #666 MERGED** to main `ab6fa8b3010ad81d34c719afa77adf3f76c8fe46` after 8/8 exact-head CI: tiny **V2-local** historic football alias `Atalanta BC → Atalanta`, preserves exact bookmark fixture names/event IDs, original frozen 19 feature values/median scheme/weights, candidate SHA, active lambda=0/NO_BET; does NOT touch other leagues or production models. Adds `days_since_last_historical_match` to V2 source coverage audit, with no tuned freshness threshold, and dedicated synthetic-home/away alias + collision regression tests in all 3 original V2 CI workflows.

**Postmerge live successful proof:** [free diagnostic run 38589939799](https://github.com/MaksimBlud/football-ai/actions/runs/38589939799) PASS **49 tests**, 20/20 existing Serie A real fixture pairs now **19/19** computed historical features, 0 all-median, 0 imputed fields across fixtures; original historical sources **10 CSV / 3800 matches**, artifact `11906648084`. Parallel [forward source-checked V2 run 38589939938](https://github.com/MaksimBlud/football-ai/actions/runs/38589939938) SUCCESS **58 tests**, verified actual source artifact and parent SHA, but 0 new candidate shadow forecasts: 20 existing Oct13 quotes predate source archive (forward source gate) and are now older than the fixed 24h quote-age gate (daily diagnostic). NO prospective backfill, NO paid Odds API calls, NO Supabase writes, NO product publication.

**Important substantive V2 quality caveat:** all 19 historical fields can be numeric while old. Exact Oct13 quote-time history shows **6 of 20** fixture pairs contain a club whose most recent lawful pre-2026/27 historical match was **≥365 days earlier**: Frosinone (870d, 2 fixtures), Monza (507d, 2), Venezia (506d, 2). This is descriptive data age, NOT a threshold for bet/training/selection. Data for all teams are missing protected current 2026/27 form; cannot claim model is accurate, active V2 > market or scientifically finished. Archive report `research/SERIE_A_V2_REAL_20_FIXTURE_COVERAGE_LIVE_PROOF_20261014.md` has exact source/live URLs and per-match ages.

**Next:** without touching protected 2026/27 results, accumulate a genuinely new user-authorized bookmaker quote only AFTER the independently source-archived 2025/26 history, capture original V2 research shadow before kickoff, and await valid outcome-read gate (30 completed primary cohort) before any Brier/LogLoss improvement test. Separately solve independently timestamped *current form* source; do not loosen old model or use another paid API credit without fresh owner authorization. Autonomous Research Brain remains V2-only, no other changes here.



## 2026-10-14 — V2-only real data shows Atalanta BC identity gap; alias repair under CI

First actual live feature coverage after merged [PR #665](https://github.com/MaksimBlud/football-ai/pull/665): on-main [free run 38588541087](https://github.com/MaksimBlud/football-ai/actions/runs/38588541087) SUCCESS, **46 V2 tests PASS**, real saved **20 Serie A quotes**, source **10** old-season CSV/3800 matches, **18/20** full original 19 features and **2/20** all-median/missing. Diagnostics **0 scored** because all old 2026-10-13 bookmaker snapshots >24h stale on Oct14 15:21 UTC; **do not relax** quote expiry or backfill to frozen prospective cohort. Parallel live [forward run 38588540998](https://github.com/MaksimBlud/football-ai/actions/runs/38588540998) **55 tests PASS**, independent real source ZIP success, existing 20 correctly blocked by source later than quote, zero new V2 future predictions. No paid The Odds API requests, Supabase writes, protected 2026/27 results, model refits or production changes.

Downloaded verified **original live archive artifact ID 11906114191** with per-fixture history audit. Exact two 0/19 events: **Atalanta BC–Frosinone** and **AC Milan–Atalanta BC**. All ten Football-Data raw CSVs refer to the club as `Atalanta` but bookmaker saved labels use `Atalanta BC`. Zero evidence was an **alias failure**, NOT absence of Atalanta's match history. Other 18 fixtures 19/19 historical features observed. Some full-vectors are dangerously stale despite being nonmissing: Frosinone last pre-protected history May 2024; Venezia May 2025; current 2026/27 fixtures remain protected from result reads.

New V2-only branch locally reconciles `Atalanta BC -> Atalanta` **inside the 19-feature history adapter**, leaving market fixture identity, original frozen trained weights, imputer medians, active market fallback, lambda/shadow, frozen eligibility and production unchanged. Adds precise `days_since_last_historical_match` diagnostic without tuning thresholds, and synthetic 2025-only regressions for either fixture side, original V2 confidence/NO_BET and historic alias collisions. Tests added to all relevant frozen V2, free-source and forward-only workflows. See `research/SERIE_A_V2_ATALANTA_IDENTITY_REPAIR_20261014.md`.

**Next proof:** after exact-head CI and merge verify on-main free real report no longer sees 2 all-median Atalanta fixtures. Historical feature completeness is NOT enough to claim current form or superior forecasts; original frozen 30-completed-event protected outcomes gate and failed V2 stability gate remain in force. Do not change production .pkl or pay for more bookmaker quotes without new authorization.



## 2026-10-14 — Original frozen Serie A V2 input-completeness/median-imputation audit

**Owner direction:** only restored original `MARKET_ANCHOR_1X2_V2` research/recovery (not abandoned older product model). V2 original candidate remains frozen SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 football inputs, `active_lambda=0` (market fallback), `shadow_lambda=1` research-only, original stability/prospective gates FAILED/not yet fulfilled; no bets/promotion.

**Identified real V2 modeling quality gap:** frozen median imputer could take **all 19 absent features** (e.g. a 2026 promoted club with zero pre-2026/27 history) and still emit research shadow probabilities as though they were supported by team form. Original date-only feature manifester gave no per-team history or imputation disclosure. New V2-only patch, covered by `research/SERIE_A_V2_FEATURE_COVERAGE_IMPUTATION_AUDIT_20261014.md`:
- Original as-of 19-feature manifest now reports for home/away: count of prior matches inside unchanged 30-game state window, count at fixture side's home/away venue, last historical match date, observed original features and count requiring frozen training median imputation. No changes to frozen candidate inputs, weights or median values.
- Shadow preview now exposes those exact feature missingness counts and names for each scored diagnostic and **blocks entirely all-median/zero-evidence vectors** (`ALL_FEATURES_MEDIAN_IMPUTED`), while partial missingness still uses original frozen median semantics unchanged. The semantic empty-input block does not optimize on outcomes or tune probability thresholds.
- Original free daily 10-source V2 live diagnostic now outputs per-fixture missingness and summary counts. Regression tests cover entirely unseen clubs, normal partial historical venue gaps and preserved market-fallback identity, original `NO_BET`, protected source rules.
- Do not pretend this makes 2026/27 current form available: the free V2 source intentionally excludes any protected 2026/27 outcomes, and original Oct 13 paid market snapshots preceded source archive, so 0/20 are prospective admissible. Existing [GitHub real archive run 38583665006](https://github.com/MaksimBlud/football-ai/actions/runs/38583665006) remains independently proven 10 old season CSV/3800 matches, not a genuine V2 win over market.
- **Verification pending** on this PR: full exact-head CI, safe fresh-main merge, then on-main free real-quote coverage report. No new paid API, Supabase writes, protected outcomes, legacy model work, original V2 refit or auto-promotion.



## 2026-10-14 — Genuine GitHub source archive V2 attestation LIVE proof (no new paid quote)

**PR #663 MERGED:** [PR #663](https://github.com/MaksimBlud/football-ai/pull/663), full **8/8 exact-head CI SUCCESS**, resulting main `193acfa9878649e8cb8a738e3db96934766dbe17`. Adds `serie_a_v2_attest_real_source.py` and offline negative regressions to the original V2 free forward-only workflow, without changing candidate 19 features/weights/lambdas or product .pkl.

**Confirmed actual GitHub workflow:** [run 38583665006](https://github.com/MaksimBlud/football-ai/actions/runs/38583665006) on that exact main completed **SUCCESS**. Test step **51 PASS**. Source-only actual GitHub Actions ZIP attestation (zero bookmaker quotes read) SUCCESS: `source_artifact_id=11898045201`, authenticated creating free history `source_run_id=38569619954`, validated GitHub ZIP SHA256, exact **10** pre-prospective original CSV source files and **3,800** historical finished fixtures, original frozen V2 candidate SHA verified. New report is source evidence only: `SOURCE_ARCHIVE_ONLY_NO_PREDICTION_NO_BET`, **0** forecasts generated, **0** protected 2026/27 results read, **0** paid API calls, **0** Supabase reads/writes, **0** model refits/promotions. Run uploaded report artifact ID **11904595542**, GitHub ZIP SHA256 `21c78f70936ff038408a7e424db566bce12135e3d504b1e4a2c2dc00f6cab04d`.

Same on-main run's actual forward quote step SUCCESS and correctly classified **20/20** existing 2026-10-13 quotes `NO_EARLIER_SOURCE_ARCHIVE`, **0** prospective-valid V2 forecasts, no data backfill, zero paid calls/DB writes. This is a real live end-to-end source-read proof; **not** scientific validation of candidate prediction accuracy.

**Critical remaining external and scientific blocker:** no new bookmaker quotes after the independently archived source (Oct 13 15:22 onward) have been saved; existing authorized single paid collection cost 1 credit and separate consent is required for further paid calls. Even a later matched quote would still be research-only while current 2026/27 form is protected/unavailable, frozen V2 active lambda=0 (market fallback), old stability gate failed, original 30-primary-event outcome-read gate remains closed, independent matched prediction/evaluation not evidenced. User directed exclusive work on original V2; do NOT revive legacy model or claim V2 has beaten market.

**Next:** maintain free history/source and read-only forward V2 capture. With independently new authorized post-archive quote, confirm actual prekickoff V2 probabilities, source ID/SHA, GitHub parent completion time, quote time, and output archive BEFORE kickoff; then work on separately preregistered V2-only independent evaluation without reading frozen protected results prematurely.



## 2026-10-14 — Original V2: verify real pre-2026/27 CSV source bytes on GitHub without waiting for a new paid quote

- Already merged [PR #662](https://github.com/MaksimBlud/football-ai/pull/662) at main `3f0cc9c084a8a9841e4742ce50882731f6639a7d` after 8/8 CI PASS. Follow-up live [run 38582177791](https://github.com/MaksimBlud/football-ai/actions/runs/38582177791) SUCCESS: 47 tests PASS, 20/20 real existing pre-archive quotes correctly blocked, 0 new V2 predictions, 0 paid requests, 0 Supabase writes, immutable report artifact ID 11903421811. Original 19 frozen features, original candidate weights and market fallback untouched.
- **Further runtime validation needed before genuinely new future quote:** No source ZIP ever preceded the October 13 existing 20 quotes, so `verify_source_run` + `verify_archive` on a real GitHub archive had never been executed at runtime; all positive ZIP tests were synthetic.
- New V2-only `serie_a_v2_attest_real_source.py` performs an independent real GitHub Actions source proof even with **zero bookmaker quotes**. It finds the latest genuine `main` free history archive, checks authentic exact successful parent source collector (run ID/SHA/path, before now), downloads ZIP read-only, validates GitHub ZIP SHA, all 10 original pre-prospective Football-Data CSV bytes, per-source SHA, historical results before 2026-07-01 and candidate SHA, and writes strictly diagnostic NO_BET JSON. It **does not access Supabase/odds, produce forecasts, call paid Odds API, open protected 2026/27 outcomes, fit/train or promote**. Existing free forward V2 workflow runs it *before* checking future real quotes, uploads source attestation and forecast result together. New synthetic ZIP/error regressions run in both existing frozen and forward workflow CI.
- After exact-head PR CI and merge: **verify live actual ZIP metadata/path/content proof**. If it fails, diagnose actual ZIP format or API provenance and fix fail-closed. No artificial quote injection allowed. If successful, the V2 infrastructure is live-tested through the real raw historical archive but original V2 quality still not proven: original stability gate failed and protected prospective 30-event Brier+LogLoss rules must not be relaxed.
- Do not claim model is ready to beat market or full production until independent prospective evidence and current-season form exist. No permission for another paid bookmaker API credit.



## 2026-10-14 — Original V2 GitHub source-run attestation hardening (CI/PR pending)

Original frozen `MARKET_ANCHOR_1X2_V2` only. Initial `serie_a_v2_forward_capture.py` source-before-quote checks verified GitHub archive ZIP SHA/time, ten old-season CSVs, and `main` artifact metadata, but **the artifact name did not independently authenticate its creating GitHub workflow**. A different main-branch workflow could publish a same-named artifact. New research-only fix now requires a separate authenticated GitHub Actions parent run read: parent run ID/head SHA must match artifact metadata, exact free collector path `.github/workflows/serie-a-v2-free-real-quote-diagnostic.yml`, `main`, allowed `push|schedule|workflow_dispatch`, `completed`/`success`, and run finalized **strictly before** individual quote time. Parent provenance is saved per predicted observation, and missing/invalid/late source blocks before archive download/model inference.

Regression tests cover authentic parent and wrong path/SHA/status/event/time/missing-run denial; existing real 20 quotes stay `NO_EARLIER_SOURCE_ARCHIVE`. No paid Odds API, Supabase mutation, protected 2026/27 score read, legacy model analysis, production files, original weights, lambda, NO_BET or frozen outcome gates changed. See `research/SERIE_A_V2_SOURCE_WORKFLOW_PROVENANCE_20261014.md`. Follow exact-head CI → fresh-main → safe PR merge → on-main runtime proof before claiming deployment. No scientific inference about V2 > market.



## 2026-10-14 — Original V2 forward archive-to-quote workflow LIVE success; next automatic quote-trigger wiring

- [PR #660](https://github.com/MaksimBlud/football-ai/pull/660) **merged** into main `670022823a46439f65d10d01e7c90bfe8afda0f5`, after **8/8 exact-head GitHub CI SUCCESS** and zero old-model/production model changes.
- The new on-main [run 38576996823](https://github.com/MaksimBlud/football-ai/actions/runs/38576996823) **SUCCESS** end to end: **41** frozen-V2/offline tests PASS, 20/20 future Serie A stored quotes inspected, **20** blocked by `NO_EARLIER_SOURCE_ARCHIVE` (the first correct source artifact was created later than 2026-10-13 bookmaker quote), **0** retroactive V2 previews admitted, zero paid provider calls, zero Supabase writes, unchanged frozen model. The run attached audit artifact **11902550076** (GitHub ZIP sha256 `d13feadc592bf5bbe0ca0ba890124032def2c35a9501b9dc980eb05b16a99e1d`); do not falsely describe these 20 as V2-produced bona-fide prospective predictions.
- Discovered practical timing issue: the V2 reader only runs 08:08 UTC daily and can miss **later same-day** new paid-manual quote captures before kickoff. New separate V2-only change adds GitHub `workflow_run` subscriber on **completion** of existing owner-manual `Serie A Odds Snapshots` workflow, with a strict job guard: upstream success, source branch main, event `workflow_dispatch` exclusively. It executes ONLY read-only original V2 archive-before-quote inference, no paid Odds API request, no scheduling or dispatching the paid collector; original one-credit hard-reserve workflow remains **workflow_dispatch-only**. Existing daily/checkout triggers unchanged.
- Tests `tests/test_serie_a_v2_manual_quote_trigger_contract.py` assert manual-only paid source, `--max-cost 1` budget guard, main/success/manual-only listener condition, read-only permissions, original frozen NO_BET and no DB writes. Frozen V2 PR and forward workflow CI both include the new regression.
- **Not yet proven:** a genuinely *new* bookmaker quote captured after historical source ZIP upload and before kickoff (the existing 20 are all from 2026-10-13, older than first ZIP). Do not invent its existence or consume an additional paid credit without explicit NEW user authorization. Further **active** V2 eligibility needs resolved 2026/27 current-form data, preregistered outcome gate and independent evidence beating the market; cannot be guaranteed by automation.
- No old model diagnosis or training, no original frozen V2 19-feature/weights/lambda changes, no protected 2026/27 results. Work remains research-only/NO_BET until demonstrated criteria, not a product promotion.



## 2026-10-14 — Original V2-only free forward-prequote forecast capture (PR pending CI)

User requires exclusive focus on restored frozen V2 (NOT old XGBoost). Prior [PR #657](https://github.com/MaksimBlud/football-ai/pull/657) source-before-quote ZIP verifier merged `75c8f08dc3e2ce23e1c8ac787318f1055a975d55`; calculation-time forbidden 2026/27 source embargo from the source-conflicted #658 landed as [PR #659](https://github.com/MaksimBlud/football-ai/pull/659), merged `d196967ba0f4ab36afeebe75478e2e3352b46045`, full 8/8 CI PASS. Superseded #658 closed after code was carried forward.

**New source-to-V2 actual live readiness implementation:** `serie_a_v2_forward_capture.py`, tests and free GitHub Actions `.github/workflows/serie-a-v2-forward-preview.yml`:
- Quotes fetched exclusively read-only from existing Supabase `odds_snapshots` SERIE_A, with no new Odds API credential/call.
- Authenticated GitHub Actions artifact metadata supplies main-source ZIP digest/created UTC. Per quote, select latest previously uploaded original historical CSV archive with strict *source capture time and complete ZIP upload time before quote*. If none, fail closed as `NO_EARLIER_SOURCE_ARCHIVE`.
- SHA-verifies GitHub ZIP, all ten original pre-2026/27 CSVs, SHA/row/date/season embargo and frozen original 19-feature SHA, then calculates frozen inactive residual shadow on saved real prices using the exact archived bytes. Separate output+ZIP archival; **no protected outcomes, Supabase writes, retraining, promotion, or old-model research**.
- Automated free scheduled job at 08:08 UTC, after historical source capture 06:13 UTC. No paid bookmaker poll is scheduled. Forecasts remain **RESEARCH_ONLY, NO_BET, not prospective**, due frozen incumbent/current-form/stability/data-time gaps. October 13 original 20 quotes precede first archive, so are expected **0/20** prequote-ready; never retroactively enroll.
- `research/SERIE_A_V2_ORIGINAL_FORWARD_CAPTURE_20261014.md` explains scientific limits, original model status, tests, operational retry. Await full exact-head PR CI, then fast-forward-safe merge and real Action run proof before claiming deployed.

Next valid scientific gate: independent current-form availability without protected 2026/27 outcomes, and real pre-kickoff baseline comparison; original frozen 30-primary-event outcome gate must be observed. No guarantee model beats market; never change `active_lambda=0` or promote without separate valid prospective evaluation.



## 2026-10-14 — V2-only recovery: independent source archive and pre-inference embargo

**Owner directive:** concentrate solely on restoring and testing the original frozen `MARKET_ANCHOR_1X2_V2`. Do not revive, audit, retrain or promote the legacy production XGBoost. Keep the market as an external comparison only. Preserve original V2 SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, exact 19 inputs, trained weights, market fallback `active_lambda=0`, shadow `lambda=1`, failed stability gate, frozen prospective gate, NO_BET and no auto promotion.

[PR #657](https://github.com/MaksimBlud/football-ai/pull/657) **MERGED** at `75c8f08dc3e2ce23e1c8ac787318f1055a975d55` after all 8 exact-head CI checks succeeded. It added independent offline GitHub archive ZIP + raw historical source SHA/date checks and strict prequote information-time source gate. Exact 2026/27 prospective results remain off limits. The older 20 stored real Serie A quotes preceded independent source capture; 0/20 qualify retroactively.

PR #658 had passed all 8 CI checks but became merge-conflicted only after #657 updated the continuity document. This subsequent **fresh-main V2-only branch** faithfully forwards its calculation-time protect-season guard and tests without overwriting the just-merged #657 journal. `serie_a_v2_live_diagnostic_report.make_report` now rejects any injected direct 2026/27 result (history date on/after 2026-07-01), wrong or duplicated season manifest, wrong source URL/name, malformed SHA, empty source or future collection timestamp **before** original V2 feature inference. This fixes an actual bypass of the existing pre-HTTP embargo. Only pre-2026/27 synthetic fixture data are used in regression. Detailed note: `research/SERIE_A_V2_INFERENCE_OUTCOME_EMBARGO_20261014.md`.

This guard alone does not cryptographically link every in-memory historical row to archived ZIP; PR #657 addresses archive integrity separately. It also does not provide current 2026/27 form, valid incumbent as-of predictions, completed 30-event outcome evaluation, or prove market improvement. **No model promotion or protected outcome access.** Next concrete priority: use the verified old-season source archive as a prequote future input for V2 and independently record model-plus-market prediction at a legitimate later quote, with no further paid provider call absent new explicit consent.



## 2026-10-13 — prequote source-archive integrity gate for original Serie A V2 (PR #657, pending HUMAN-MERGE)

**STATUS: PR [#657](https://github.com/MaksimBlud/football-ai/pull/657) is NOT merged.** Preserve owner-requested HUMAN-MERGE policy for scheduled agents. Work is research-only: `serie_a_v2_prequote_source_archive_gate.py`, `tests/test_serie_a_v2_prequote_source_archive_gate.py`, accompanying research note and frozen-V2/free-source workflow regression coverage.

The existing independent daily free source job archives 10 raw 2016/17–2025/26 Football-Data CSVs, observed-at timestamps, and per-file SHA256. New **offline, zero-paid, zero-Supabase-read/write** tool validates the *exact GitHub Actions ZIP archive* and pre-2026/27 history. With independently obtained GitHub Actions artifact SHA and creation time supplied, it checks the full ZIP hash, all raw CSV hashes, exact season list, trusted quote/snapshot ordering, results pre-2026-07-01, source capture strictly before quote, artifact upload strictly before quote, exact frozen candidate SHA; invalid/duplicate identities and protected outcome fields fail closed. Caller-provided GitHub metadata cannot authenticate itself: output says `independently_authenticated_github_metadata=false`, and even if `source_archive_prequote_ready` is true, **V2 prospective eligibility, product publication and betting ALWAYS remain false**, pending full feature information-time proof, actual current form, incumbent and original stability/prospective gates.

Historical check: original archived 20 real Serie A quotes from 2026-10-13 14:48Z predate the 2026-10-13 15:22Z source archive: **0/20 can be claimed source-before-quote ready**. This is a timing comparison, not an empirical validation of V2 performance. The previous outcome-peeking first prototype archive remains disqualified, with 2026/27 source hard embargo in place. Do not ask for or spend another paid The Odds API credit without new explicit permission.

**Next step after owner merges PR #657:** inspect fresh main, run normal zero-cost diagnostic and verify future old-season archive matching using independent GitHub artifact metadata, then design non-peeking current-form source/true pre-match incumbent capture. No production .pkl, frozen threshold, prospective outcomes, quota or promotion changes.



## 2026-10-13 — Original Serie A V2 real-quote free diagnostic, outcome embargo tightened and rerun

- **PR #654 MERGED** to main `2e0538f5652d0d1dc804be7925b680305ab3da12`, after **7/7 full CI successful**: new `serie_a_v2_live_diagnostic_report.py` + tests + free, daily GitHub Actions `.github/workflows/serie-a-v2-free-real-quote-diagnostic.yml`. Reads already-persisted Serie A odds, downloads configured public Football-Data CSV, captures raw source bytes with sha256 + observed time, computes actual original SHA-pinned 19-feature frozen V2 (inactive residual) diagnostic, never calls paid Odds API, never mutates Supabase/production.
- The first technical [run 38420548335](https://github.com/MaksimBlud/football-ai/actions/runs/38420548335) succeeded and produced 20 original V2 diagnostics, **but it fetched current 2026/27 CSV containing outcomes that can overlap the frozen prospective protected period**. **SUPERSEDED / DO NOT USE** that artifact for frozen research evaluation. Source date-filter alone is not an acceptable embargo. Neither train nor promote from this diagnostic.
- **PR #655 MERGED** to main `ede9dfa9b71d7611a7dd17c83d8cda0e9448861d`, after **7/7 full CI successful**. The new free source collection now enforces current-season embargo **before HTTP requests**; does not fetch any `2627/I1.csv`, even temporarily. Latest results are necessarily stale to 2025/26, not a finished live model.
- Corrected [run 38421462384](https://github.com/MaksimBlud/football-ai/actions/runs/38421462384) verified **SUCCESS**, **28 tests PASS**, 10 public historical CSVs (2016/17–2025/26), 3,800 pre-prospective historical results, 20/20 authentic original V2 read-only diagnostic predictions, zero paid calls, zero Supabase writes, no `2026/27` source download, original `active_lambda=0`, `NO_BET`. SHA-archived source and all probability outputs: artifact ID **11827095266**.
- Directional analysis on *corrected* data: **0/20 market favourite changes**; average per-fixture maximum absolute market-vs-shadow probability shift **3.20 pp**, maximum **6.34 pp**. **Not evidence** of improved hit rate, log loss, Brier or value, and no frozen outcome read permitted. The 20 quote times preceded the new raw source retrieval, independently attested source availability is missing, and no original as-of production incumbent was captured.
- Research report `research/SERIE_A_V2_FREEZE_SAFE_REAL_QUOTE_DIAGNOSTIC_20261013.md` contains numeric examples and explicit limitations. Public source free daily 06:13 UTC observation workflow is autonomous only for its defined collection/scoring job; ChatGPT itself is **not** continuously working between chat sessions. Paid quote collection remains manual-only with hard 100 credit reserve and already-spent one-off permission.
- Next safe task: immutable forward capture linking feature-source SHA/timestamp and later quote with independently stored pre-kickoff incumbent, preserving freeze gate and not peeking at prospective outcomes; do not treat 20 `MARKET_ONLY` live ledger entries as V2 forecasts.



## 2026-10-13 — Paid Serie A market capture succeeded; research MARKET_ONLY live cycle completed

**Live, verified user-authorized once-only action:** owner triggered existing manual [Serie A Odds Snapshots run 38416542414](https://github.com/MaksimBlud/football-ai/actions/runs/38416542414), on main `5cc3c94a77c570f6ebc0890f06c2939d522f4ec7`, completed SUCCESS. No automatic paid cadence was enabled.
- Provider's zero-cost quota preflight passed with **499 remaining**, `max_cost=1`, hard reserve **100**. A single EU/1X2 `h2h` paid request cost **exactly 1 credit**, leaving **498** (`used=2`, `last_cost=1`) in provider-reported response; permission for additional paid calls **not** inferred.
- `public.odds_snapshots` Serie A increased from **605 to 625** rows. **20** new separate future fixtures, all 20 pre-kickoff, no null/invalid decimal 1X2 prices, source timestamp **2026-10-13T14:48:53.042620Z**; kickoffs 2026-10-16 through 2026-10-25; bookmaker contributions per averaged event **14–24**.
- Bookmaker-granularity sidecar **did not persist** (0 research rows), despite aggregated odds success: error `permission denied for table league_h2h_bookmaker_snapshots`; read-only grant attestation: current `service_role` SELECT=true, INSERT=true, UPDATE=false. A separately reviewed, scoped grant/migration is needed. Do not modify production DB privileges implicitly based on this diagnostic.
- Before live cycle, `league_prediction_ledger` and `league_structural_v2_observations` each contained 600 historical rows and zero future rows.
- Existing scheduled [Serie A Live Cycle run 38360656777](https://github.com/MaksimBlud/football-ai/actions/runs/38360656777), earlier failed from missing future fixtures, was safely rerun as **attempt 2 / SUCCESS**, **zero additional paid calls**. Re-run uses existing earlier workflow SHA `cd307c951623aa24da5649fe376b4c6bfa1b4a9e`; inspected relevant current/runtime modules and confirmed identical blobs to main except `league_supabase_persistence.py`, whose subsequent alias-finished-result fix is not used for result writes by this cycle. 
- Live-cycle proof: **20 upcoming fixtures**, **20 OK market-only shadows**, **20 observations inserted**, **20 prediction ledger rows inserted**, **0 conflicts**, finished-results count unchanged at **63**. Read-after-write SQL confirms **620** rows each in observation and prediction ledgers, **20** future records, and exact all-20 quote→ledger pairing by event, kickoff, snapshot and teams, **0** unexpected modes and **0** invalid market probability sums.
- **CRITICAL V2 boundary:** the 20 new records are the already operational **MARKET_ONLY** research infrastructure, *not* `MARKET_ANCHOR_1X2_V2` 19-feature AI forecasts. Original frozen candidate file remains SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 3,799 training rows, 19 exact features, `active_lambda=0`, `shadow_residual_lambda=1`, failed original stability gate, no auto promotion, NO_BET. No independently verified 19-feature as-of cutoff manifest **as of the paid quote time** nor separately timestamped frozen-incumbent prediction has been captured; **do not backfill or relabel** these 20 as frozen prospective V2 evidence or read protected 2026/27 V2 cohort outcomes before its predeclared 30-completed-event gate.
- **Next:** establish independently auditable forward-only 19-feature source/availability capture and exact pre-kickoff incumbent comparison on the **next genuine quote window**, avoiding unapproved extra paid provider calls; separately audit/grant minimal required `UPDATE` on research bookmaker sidecar after security review. Production .pkl, site and frozen outcomes unchanged.


## 2026-10-13 — Serie A free finished-results sync restored end-to-end; paid odds remain manual

**User authorization:** user explicitly approved one further Serie A The Odds API credit, preserving shared 100-credit hard reserve. **No credit was actually spent in this conversation.** Attempt to re-run original manual Serie A H2H collector job `103325482610` from 11 September run `34618255157` failed with GitHub 403: a workflow run more than one month old cannot be rerun. The connected GitHub connector does not expose new `workflow_dispatch` invocation. Existing `.github/workflows/serie-a-odds-snapshots.yml` remains manual-only, with free quota preflight, `--max-cost 1`, and preserved 100-credit reserve. **Next required paid action**: the owner may manually launch the existing GitHub Actions 'Serie A Odds Snapshots' workflow on `main`; do not change its schedule or automatically spend other credits.

**Independent provider-free result-sync defect found and fixed:**
- GitHub scheduled [run 38357916942](https://github.com/MaksimBlud/football-ai/actions/runs/38357916942) previously failed when canonical team aliases `Atalanta` and `Atalanta BC` had two immutable stored rows for one 2026-08-31 fixture. Read-only Supabase comparison exposed **2 aliases with exactly 1 distinct score/outcome version**, differing *only in source provenance metadata*, without disclosing scores from any protected prospective cohort.
- [PR #650](https://github.com/MaksimBlud/football-ai/pull/650), **7/7 exact-head CI SUCCESS**, squash merge `0d9a5d6dbef89b441200fc348ca6e7cd96864b99`: `league_supabase_persistence.py` now tolerates only SERIE_A alias-spelling duplicates with exactly identical canonical fixture, goals, result and all other non-provenance attributes, retaining **both original immutable rows**. Changed scores/other fields/same-spelling duplicates/other leagues still hard-fail. Regression tests added. Existing provider-free sync push paths watched.
- The triggered [run 38414419017](https://github.com/MaksimBlud/football-ai/actions/runs/38414419017) proved the fix **wrote 10 new finished results, 50 unchanged, 0 conflicts, 0 paid calls** from the existing Football-Data source. It exposed another legacy duplicate handling issue in the separate read-only market evaluator; the sync step itself had succeeded.
- [PR #651](https://github.com/MaksimBlud/football-ai/pull/651), **6/6 exact-head CI SUCCESS**, squash merge `5b4d72abdc751cd6f24f70ef4adf063a73c2c69f`: `evaluate_serie_a_predictions.py` now de-duplicates only same canonical fixture with **different original raw team spelling AND identical known goals and result**; any missing/disagreeing score or same-spelling duplicate fails closed. Pure evaluation, no stored-row mutation. Synthetic regressions added; existing free workflow can retry after merge.
- Subsequent [run 38415369662](https://github.com/MaksimBlud/football-ai/actions/runs/38415369662) proved **complete GitHub Actions SUCCESS**, including free source-sync, explicit status verification and read-only legacy market evaluator. No model promotion, no production .pkl change, no paid Odds API request, no new V2 prospective evidence, and no frozen outcome gate changes.

**Remaining live blocker unchanged:** Serie A bookmaker `odds_snapshots` had 605 stored historical rows and zero future rows as checked before the user consented; newest quote was 2026-09-11. New results do not create pre-kickoff 1X2 prices. Valid live V2 requires genuinely fresh, time-stamped Serie A odds and independently attested point-in-time 19-feature source provenance; existing restored V2 candidate remains `active_lambda=0`, `shadow_lambda=1`, `NO_BET`, research-only, without production promotion.


## 2026-10-13 — Frozen Serie A V2 19-feature as-of adapter restored (research-only)

**Completed and verified:** [PR #648](https://github.com/MaksimBlud/football-ai/pull/648) merged after **all 7 exact-head CI checks SUCCESS** on head `677b287ac896c1ea5da81a1be3f508701532a6a6`, main merge SHA `c306d9f55ef170245d7b6d4ecfe0856c4a3212b7`; fresh main and new script confirmed post-merge.

- New `serie_a_v2_asof_feature_manifest.py` reads an **already stored Football-Data-compatible Serie A history CSV** and **existing saved odds JSON** offline. Reuses original historical `TeamMatch`/`_snapshot` feature calculations and checks that the 19 frozen `ALL_FOOTBALL` feature names match exact restored V2 artifact. Emits the input manifest expected by the runnable existing `serie_a_v2_frozen_shadow_preview.py`. No refit, source change, database mutation, .pkl alteration, paid provider call or automatic promotion.
- **Fail-closed boundaries:** excludes all historical match rows on the snapshot's UTC calendar day or later because the historical source has match dates but no independently attested publication times. Rejects missing corner/card/goal columns or values, corrupt results, duplicated historical identities, wrong-league or inconsistent market fixture identity, and quote after kickoff. Legitimate empty venue/rolling history uses JSON null for frozen original median-imputer semantics, not invented zeros. Audit hashes input files. Date-only data are NOT sufficient to attest true real-time knowledge: `eligible_for_frozen_prospective_cohort=false` and `eligible_for_product_publication=false` unchanged.
- Regression tests `tests/test_serie_a_v2_asof_feature_manifest.py` exercise real original frozen V2 shadow inference, 19-feature order, same-day/future leakage isolation and source fail-closed checks. Dedicated shadow workflow now includes the adapter. All seven CI jobs succeeded. Documentation `research/SERIE_A_V2_ASOF_FEATURE_MANIFEST_20261013.md`.
- **Live confirmed read-only:** Serie A `odds_snapshots`: **605** rows, latest **2026-09-11 15:48:24.896863Z**, zero upcoming observations. `league_finished_results` Serie A 2026/27 has **53** results only through **2026-09-20**; `matches` contains EPL only and cannot supply Serie A historical football stats. `league_multi_market_snapshots` has only **2 rows total** and is not full multi-market coverage.
- **Why collection is not automatically repaired:** existing `.github/workflows/serie-a-odds-snapshots.yml` permits `workflow_dispatch` only, by design: `tests/test_paid_provider_workflow_budget_contract.py` requires **manual-only paid workflows**, the existing free /sports/ budget guard, and preserved hard reserve. The two-hour Serie A live cycle reads snapshots but does not generate them. Do NOT enable paid schedule or invoke any paid Odds API endpoint without fresh explicit user permission.
- **Next priority:** independent source availability/provenance for current Serie A 19 features and genuine **fresh upcoming 1X2** odds under the user's existing source/quota approval process. Then complete frozen prospective V2 comparison with exact SHA-pinned incumbent and market, no data contamination or early gate reading. Keep failed original V2 stability gate and NO_BET. Separately audit old incumbent XGBoost and calibrator data flow and readiness of other leagues/markets.
- **Security notice discovered in Supabase metadata:** RLS currently disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, `public.epl_ai_market_pair_ledger`. DO NOT auto-enable RLS without scoped policies and reader/writer impact analysis. Inform owner and plan separate authorized security migration.


## 2026-10-13 — Restored MARKET_ANCHOR V2 is now runnable in safe Serie A shadow inference

**Concrete code and verified merge:** [PR #646](https://github.com/MaksimBlud/football-ai/pull/646) 7/7 exact-head CI SUCCESS, squash merged at `dca3a3c713e476198aeedeeb62a1caa73cf0b4c2`. New `serie_a_v2_frozen_shadow_preview.py`, `tests/test_serie_a_v2_frozen_shadow_preview.py`, dedicated scientific tests GitHub workflow, and [readme](research/SERIE_A_V2_RESTORED_SHADOW_INFERENCE_20261013.md) are now in main.

- **Not a new model.** Original September 2026 frozen **SERIE_A_ONLY** residual SHA256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 3,799 old training rows, exact 19-feature order, scaler/imputer and original weights recovered by PR #644 and reused **unchanged**. No new fit, no parameter-selection on settled outcomes.
- **Actual executable inference:** against an explicit offset-aware upcoming Serie A fixture, an already-saved pre-kickoff `odds_snapshots` quote and a separate 19-feature as-of history manifest, it emits margin-free market probabilities, **active-market fallback** (`lambda=0`) and the original **frozen residual shadow** (`lambda=1`) side by side, with full SHA and date-time provenance. Synthetic tests use the actual SHA-pinned original coefficients to prove shadow differs from market.
- **Strict fail-closed eligibility:** no prediction is scored for absent/stale (>24h) quote, invalid prices, bad kickoff, missing feature manifest, feature history cutoff newer than market snapshot, mismatched identity, duplicate snapshot, or outcome/settlement fields. The provided feature manifest's independent origin cannot yet be attested, so **every preview explicitly says NOT prospective-admissible and NOT product-publication-eligible**. No database writes, The Odds API calls, betting or production model promotion. Retains failed September V2 stability gate and `NO_BET`.
- **Live blocker measured read-only:** as of 13 October 2026, Supabase `odds_snapshots` has 605 old Serie A quote rows but **zero future fixtures / zero future quote observations**, latest quote timestamp **2026-09-11T15:48:24.896863Z**. There is no independently verified current-series 19-feature history manifest. Thus this PR truthfully creates **zero real new predictions**; never fill with fabricated odds/features.
- **Next real user-visible milestone:** ensure existing authorized quota-controlled The Odds API collection for Serie A produces genuinely fresh provider 1X2 snapshots, while the historical feature pipeline independently supplies verifiable as-of 19-feature Serie A inputs; only then begin *new, pre-kickoff, independently attested* V2 shadow capture with incumbent and canonical market provenance under frozen V2 protocol. No new paid API call without explicit permission. Do NOT relabel fallback odds as AI and do NOT modify old .pkl.
- **Safeguard:** separated scientific tests from lightweight `product-pr-validation.yml` to avoid installing NumPy/scikit-learn for all product checks. Dedicated `shadow-tests` green alongside six standard mandatory checks.

## 2026-10-13 — ORIGINAL MARKET_ANCHOR V2 SERIE A CANDIDATE RESTORED AND DURABLY SAVED

**Completed real restoration:** [PR #644](https://github.com/MaksimBlud/football-ai/pull/644) merged via exact-head after **7/7 CI success**, merge `c17f0b906ecaea96ae38e0918a657d0741056135`. The original Sept-2026 **frozen MODEL WEIGHTS** of `MARKET_ANCHOR_1X2_V2` for **SERIE_A_ONLY** are now permanently committed at [research/models/market_anchor_v2_serie_a_frozen_candidate.json](research/models/market_anchor_v2_serie_a_frozen_candidate.json); no more reliance on ephemeral Codespaces/Action artifacts.

- **Exact canonical candidate SHA256** `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. Validated against the frozen V2 Python internal SHA function using the original Python-generated JSON numeric strings; an earlier JavaScript JSON reserialization changed float decimal spelling and was rejected, then fixed by verbatim recovery from the successful original GitHub Actions run log.
- **Original training fingerprint SHA256** `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; exactly **3,799 original rows**, all 2016/17–2025/26 CSV source file SHA256 hashes individually matched the September report.
- **Recovery run:** [GitHub Actions 38345664423](https://github.com/MaksimBlud/football-ai/actions/runs/38345664423) SUCCESS on exact PR head `293a6d11d49fd007dccb32c53b66269d594e2907`. Restored three exact September Git source blobs; pinned Python/dependencies and 1-thread BLAS; stored-original candidate and newly fitted candidate had **identical artifact SHA256**, weight matrices, scaler means/scales and imputer medians (max absolute difference **0**). Manifest makes exactness and deviations explicit; if future refit numerical results differ >1e-8 it fails, and no refit overwrites the SHA-pinned original.
- **Why prior PR #337 remained open:** old research replay passed, but its additional continuity-writing helper failed with a Python string syntax error. Its original canonical report and replay tests are restored separately into `main`; broken helper was **not** imported. 2026/27 mutable CSV now differs from its full September checksum, so strict recovery is done using only the 2016/17–2025/26 **training** source; later-match full replay is NOT claimed freshly reproduced. The old saved 10-match Serie A replay remains **post-outcome diagnostic only**, not prospective evidence: market Brier 0.566295 / log loss 0.967488, V2 shadow 0.561608 / 0.961292; tiny N=10. No results used to retroactively choose a candidate.
- **User's model concern answered:** published product 1X2 records (40 snapshots at audit) refer to old XGBoost artifact SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`. September MARKET_ANCHOR V2 source + weights were real and are recoverable, but **stability gate remains FAILED**, `active_lambda=0.0`, `shadow_lambda=1.0`, league scope **SERIE_A_ONLY**. Do **not** claim it is EPL model or that it has a verified advantage over market.
- **No production or budget change:** no .pkl writes, XGBoost promotion, main site deploy, Supabase data writes/DDL, paid The Odds API calls, bets or relaxation of frozen evaluation contracts.
- **Next meaningful product milestone:** join the existing saved V2 research model to the product **via read-only/shadow capture for Serie A**, using existing market snapshot source and pre-match time gates. Do not silently replace 1X2 with market-only odds represented as AI; keep no-bet state. Obtain a newly frozen prospective cohort and pass unchanged stability and sample gates before any production promotion. Separately investigate actual XGBoost input/calibrator pipeline; don't retrain what we already preserved.

## 2026-10-13 — independent-Poisson / Dixon–Coles market blend REJECTED after later-period comparison

**Actual finished research-only delivery:** [PR #642](https://github.com/MaksimBlud/football-ai/pull/642) merged safely after ALL SIX exact-head CI checks passed; merge SHA `19c5931434c33332c5e0322538084227ef402a9d`. Files: `epl_poisson_market_blend_v1.py`, `tests/test_epl_poisson_market_blend_v1.py`, [report](research/EPL_POISSON_MARKET_BLEND_V1_20261013.md), required Product CI. No production release, model promotion, database writes or Odds API spend.

**Data, time separation and real scores:**
- Live Supabase read-only `public.matches` **EPL matches 2016-08 to 2022-07 only**; historical old seasons, not frozen prospective research event datasets. 2,280 total historical matches; priced 1X2 observations 1,140 (2019/20–2021/22). Older fixtures provide ONLY prior scoring strengths. Same-date matches all receive as-of-prior-date goal histories; each day's results are incorporated only after that day's predictions are constructed.
- Predefined 36 Poisson/DC/market-blend candidates: goal smoothing 5/12/25, low-score DC rho -0.08/0/0.08, Poisson blend 0.1/0.25/0.4/0.6. Explicit 2019/20 validation 380, then later-period historical 2020/21–2021/22 evaluation 760.
- Selected on validation alone: smoothing **5**, rho **0**, Poisson 40% + normalized bookmaker market 60%. Validation improvement: Brier **0.572696** vs market **0.575034**; log loss **0.967385** vs market **0.972590**.
- **Failure on next 760 matches:** candidate Brier **0.577015** vs market **0.575253**, candidate log loss **0.972675** vs market **0.970092**; accuracy candidate **53.82%** vs market **54.74%**. Failure deltas +0.001762 Brier / +0.002583 log loss. **`FAILED_FORWARD_HISTORICAL_EVAL`**, NO promotion. All 6 CI checks green and tests prove same-day outcome isolation, deterministic 36-grid selection and refusal to accept later-period degradation.
- No candidate is proven at least market-equal as an independent AI model. A `market-only` fallback is mathematically identical to the no-vig bookmaker probability, **not** a new model nor proof of a betting edge.
- **Honest evidence level:** historic `matches` bookmaker odds do not have exact quote timestamps, and the 2020/21–2021/22 matches appeared in previous exploratory training. Thus later-period replay is **not pristine independent/prospective**. No frozen prospective outcomes were accessed.
- **Research-only safety:** no `.pkl`, new provider calls, research unblinding, Supabase writes, changed thresholds, ROI/CLV/value claims or live production predictions. Product reliability >=100 settled unique exact-model fixtures spanning >=4 months remains frozen. No automatic promotion.
- **Next direction:** test an explicitly preregistered NEW architecture with an independent not-previously-inspected forward period rather than tune to 2019/20, 2020–22, 2023–25 or 2026 already observed historical/product results. Where a market baseline is shown, always identify it as bookmaker-derived, never silently label it AI.

## 2026-10-12 — EPL 1X2 independent historical market-floor research COMPLETED; NO AI UPLIFT

**Research complete on latest verified main** `1f70b8b2ecf381e546a30f456b19313a5cb1cd52` (squash-merged [PR #640](https://github.com/MaksimBlud/football-ai/pull/640), all six exact-head CI checks SUCCESS). Prior [PR #639](https://github.com/MaksimBlud/football-ai/pull/639) created aggregate-only product-vs-market diagnostic.

- **Actual settled product score (diagnostic, not training):** on 29 EPL same exact model predictions 10/29 correct vs 12/29 for bookmaker favorite; model Brier 0.674421 vs no-vig market 0.646360. Split by registration provenance: legacy bootstrap 6/20 vs market 8/20; live_publish 4/9 vs market 4/9. Model top pick HOME 26, DRAW 0, AWAY 3. Not enough evidence to claim model outperforms market, and no prospective contract gates bypassed.
- **Time-separated historical replay using only pre-2025-08 EPL matches**, older than any model's 2026 product deployment: fit 2019/20–2021/22 **N=1140**; validation 2022/23 **N=380**; subsequent held-out 2023/24–2024/25 **N=760**. No-vig market reference: validation Brier **0.573674**, LL **0.965801**, accuracy **56.05%**; heldout Brier **0.556008**, LL **0.939901**, favorite accuracy **56.58%**.
- **Price-temperature + historical-prior correction** selected gamma=1.1 / shrink=0.1 from validation, but FAILED heldout, Brier **0.556902** and LL **0.942372** (both worse than market).
- **Market-anchored multiclass residual model** (as-of previous 5 matches / prior 10 venue games: points, goals, shots-on-target, home/away win rates) evaluated **64 fixed candidates** with training only in 2019/20–2021/22. No candidate beat baseline in BOTH Brier and log loss on validation; best observed Brier **0.574045**, LL **0.966357** vs market **0.573674**, **0.965801**. No candidate qualified to be evaluated for independent adoption.
- **Only verified floor = unmodified no-vig BOOKMAKER estimate**, guaranteed exactly equal to market scores when the SAME valid historical decimal odds are supplied; it is explicitly **NOT AN AI MODEL** and does not show any edge, ROI or market outperformance. `epl_market_floor_v1.py` runs historical read-only regression and outputs fail-closed status `MARKET_FLOOR_ONLY_NO_AI_UPLIFT`. GitHub `tests/test_epl_market_floor_v1.py` asserts frozen chronology, no same-match outcome leakage, no retrospective auto-selection on heldout, no paid calls/writes/model changes. Research note: [EPL_MARKET_FLOOR_V1_20261012.md](research/EPL_MARKET_FLOOR_V1_20261012.md).
- **Important comparison limitation:** historic `matches` odds lack quote timestamps, so that study is not a proven timestamped pre-match or live-prospective advantage. It never read any outcomes from frozen prospective research experiment tables. Existing product reliability gate (same model SHA/league `>=100` settled spanning `>=4` calendar months) remains unchanged.
- **Release status:** research code only, no production `.pkl` changed, no model promotion, no Supabase write, no Odds API request, no site deployment. Research-only code is merged; no new live betting forecast can truthfully be claimed at least as good as market from these tests.
- **Next independent step:** preregister genuine model architecture / calibration alternatives BEFORE a fresh, non-overlapping OOS period and collect permitted market data using existing provider quota/permission and settlement gates. Future comparisons must require both Brier and log loss not worse than same-time no-vig market, with an explicit statistical uncertainty interval; do not tune from the October 2026 29 settled product outcomes, the 2023/24–2024/25 heldout results, or protected prospective experiment targets. Request explicit promotion authorization only after the frozen evaluation gate.

## 2026-10-11 — two bot-created UI draft PRs completed after exact-head CI (06:12 UTC)

**Verified fresh main after code merges:** `2e46579557824e39fa41615897740e76254f89d5`. **Do not conflate interactive merge with unattended scheduled ChatGPT merge.**

- GitHub Actions relay had independently created safe code+test bot-drafts [#622](https://github.com/MaksimBlud/football-ai/pull/622) and [#625](https://github.com/MaksimBlud/football-ai/pull/625), and six required CI jobs had been dispatched and completed on their exact PR heads. #622 later received owner-attributed branch refresh `b1da8d1a0f05a3bbfb53073e7e1671d94ec196e8`, preserving both base and branch changes; exact-head **6/6 CI SUCCESS**, fresh main `3bb5008f39fbe3d52c4608c9f8380cdbfd2348cf`, behind_by=0, mergeable=true. This conversation **interactively** marked #622 ready, rechecked gates, and squash-merged to `6b50cd9b11d229f78f6c1c070182dc2e9506cc85`.
- #625 was now behind main, so interactive ChatGPT built a **no-force, fast-forward**, 2-parent merge commit `765eadb3aeb3b93b7932922aa69a1a09fe9a76ab` from branch head `fee8c33f89271634027b47aa5fd4245341ec1903` plus fresh main `6b50cd9b11d229f78f6c1c070182dc2e9506cc85`, preserving the only two intended UI code/test differences. After another **6/6 green CI on exact new head**, behind_by=0 and unchanged fresh main, interactively marked ready and squash-merged #625 to `2e46579557824e39fa41615897740e76254f89d5`; live GitHub main and both PR.merged confirmed.
- Two hourly **ChatGPT Frontend Builder / Backend Builder** automations remain enabled on the same hourly schedule. Their prompts have been updated to prioritize exact-head safe completion of their own code+test PRs (including github-actions[bot] drafts), requiring an allowlisted product file scope, all SIX exact-head completed SUCCESS CI checks, behind_by=0 relative to freshly read main, mergeable=true, expected_head_sha, and post-merge verification. Research/model and frozen gates remain excluded. **This is a prospective scheduled-autonomy test configuration, not proof of unattended ChatGPT coding/merging.**
- Remaining #609 acceptance: obtain externally attributable proof that an hourly scheduled ChatGPT Builder created real code+tests, and itself completes the safe PR→CI→exact-head merge in an independent scheduled run. No other model API, paid The Odds API, Supabase writes/DDL, production `.pkl` changes or production deployment.

## 2026-10-11 — autonomous bot-created PR and six exact-head CI successes (verified)

**Last verified engineering main:** `b38fe581c229329f5c2a9fc9bfb7b2b608db3d83`. The source PR branch was prepared **interactively**, but creation of its PR and dispatch of its six CI suites were performed autonomously by GitHub Actions, without model or paid API calls.

- [PR #623](https://github.com/MaksimBlud/football-ai/pull/623), commit `b45bcab7937e5b19f63965ebd83f2c29712eb44f` after **7/7 executed green PR checks**, added `workflow_dispatch` + required pinned `expected_head_sha` to six existing required validators (Product, Research, Bundesliga, Ligue1, SerieA, Eredivisie) and added bot-draft-only relay dispatch and resume. The relay's `actions:write` permission is limited to its job; no code push, PR merge, production deploy, fake checks, or permissive human-PR access.
- **Legacy case:** the first post-merge relay [run 38116246423](https://github.com/MaksimBlud/football-ai/actions/runs/38116246423) resumed bot-created [draft #622](https://github.com/MaksimBlud/football-ai/pull/622) at head `6084ecb02dbc1e583fb2451a2471f6780f7d9365` but pinned validation dispatch failed **HTTP 422** because that source branch predated the workflow-dispatch trigger. The draft remains OPEN, UNVALIDATED and UNMERGED. Do not claim CI or auto-rebase it.
- [PR #624](https://github.com/MaksimBlud/football-ai/pull/624), commit `b38fe581c229329f5c2a9fc9bfb7b2b608db3d83` after **7/7 executed green PR checks**, made the relay log only that exact legacy-branch 422, preserve old draft and continue scanning new eligible branches. Unrelated errors continue to fail closed. Main merge is still never automatic.
- The automatic [relay run 38116463938](https://github.com/MaksimBlud/football-ai/actions/runs/38116463938) from the #624 main push **created [draft PR #625](https://github.com/MaksimBlud/football-ai/pull/625)** as `github-actions[bot]`, using real scoped code+test on `dev/ui-z-loading-status-announcement-20261011`, exact head `fee8c33f89271634027b47aa5fd4245341ec1903`. Relay autonomously dispatched real Product [38116479617], Research [38116480690], Bundesliga [38116481867], Ligue1 [38116483184], SerieA [38116484357], Eredivisie [38116486044] workflows; **all SIX reported completed SUCCESS at the exact #625 head**. #625 remains OPEN DRAFT and UNMERGED; no auto-merge claims.
- **Autonomy status:** `SCHEDULED_BRANCH_COMMIT_PARTIAL_EVIDENCE + DETERMINISTIC_BOT_PR_AND_6_CHECK_CI_CONFIRMED`, but **unattended ChatGPT authoring of full code+tests and exact-head PR merge remains UNPROVEN**. Next safe work is resolving the legacy draft #622 via a reviewed update, then deciding any gated merge policy without loosening safety contracts. No paid/model APIs, frozen-outcome peeking, Supabase writes/DDL, production `.pkl` changes or production deployment.

## 2026-10-11 — LIVE autonomous draft PR blocker proven (05:05 UTC)

**Source of truth:** fresh main `f6041ec6317423bc8de9d7fe9acff1909886d571`. **Manual repository Actions permission gate confirmed. No unattended end-to-end autonomy.**

- [PR #618](https://github.com/MaksimBlud/football-ai/pull/618): safe draft-PR relay now tolerates a bounded 0–6-commit `behind_by` drift while keeping strict source+test allowlist, freshness, branch/head/main race gates, no production writes, and **no auto-merge**. Added path-filtered immediate post-merge `push` trigger in addition to hourly `43 * * * *` schedule. Verified **7/7 executed CI successes** plus intentionally skipped on-PR relay job; exact-head squash merge to `3bea6eac0831f7ce9d7a53294df77d5005d981fe`.
- Real automatic push-triggered GitHub Actions [run 38113525560](https://github.com/MaksimBlud/football-ai/actions/runs/38113525560): **10/10 relay unit tests passed**; discovered Frontend agent branch `dev/ui-match-error-focus-20261011-0405` (old original agent commit `93dd5fd4d739441c26d7528848bb70d335a8f606`; modified `static/match.html` plus new `tests/test_match_detail_error_accessibility.py`). **Draft PR creation attempted autonomously and definitively rejected by GitHub: `HTTP 403 GitHub Actions is not permitted to create or approve pull requests`.** No bypass tried. GitHub Actions repository admin must enable **Settings → Actions → General → Workflow permissions → Allow GitHub Actions to create and approve pull requests**. A workflow-created PR might not auto-trigger `pull_request` CI; it is not safe to merge without exact-head green checks.
- [PR #619](https://github.com/MaksimBlud/football-ai/pull/619) **interactive** recovery of agent's UI error-focus code. Added `9137fa8b7414dbfcb277b70446d8881f92e72507` to make required Product PR Validation actually run the new Node-backed accessibility tests; **6/6 green CI**, safe exact-head squash merge, verified fresh main `f6041ec6317423bc8de9d7fe9acff1909886d571`.
- Agent scheduled triggers are enabled, branch-only code commits are observed. **Creating a PR from a scheduled GitHub Actions relay is blocked by repository settings.** Do not claim full autonomy or propose waiting another hourly cycle to solve this administrator permission. No paid/model API, frozen outcomes, Supabase writes/DDL, Vercel production deployment or production `.pkl` changes.

Этот файл — каноническая память проекта между чатами. Source of truth: **fresh GitHub `main` + live Supabase**. Git history хранит полный исторический detail; здесь фиксируются binding rules, действующие contracts/gates, доказанные live facts, существенные решения текущего рабочего дня и официальный execution pointer.

## 2026-10-11 — guarded unattended branch-to-draft-PR handoff installed (04:18 UTC)

**Verified main at implementation merge:** `efa98193af37eeece1d817e55466935b4b956340`. This mechanism was implemented **interactively by ChatGPT**, NOT by an unattended model run. No independent scheduled draft PR has yet been proven.

- [PR #616](https://github.com/MaksimBlud/football-ai/pull/616) safely squash-merged to `efa98193af37eeece1d817e55466935b4b956340`, with **7 executed CI checks successful** at exact PR head `11871712cc2f012e40435670b916b62754b8856f` (the new relay job intentionally skipped on the PR event; this is not a failing check).
- Installed `engineering_pr_relay.py`, `tests/test_engineering_pr_relay.py` (8 passing tests), and `.github/workflows/football-ai-engineering-pr-relay.yml` (`43 * * * *` hourly, plus manual dispatch). Existing read-only heartbeat untouched.
- This is a **deterministic, zero-model-API GitHub Actions** handoff from independently created Builder branches into DRAFT PRs only, not an autonomous coder. Rejects non-fresh/behind-main branches, missing code or tests, out-of-allowlist paths, deletes, excessive diffs, existing PRs, concurrent HEAD races, and old commits. Max one candidate per Frontend and Backend per run. No writes to code/main, no paid API, production .pkl or DB mutations; NEVER auto-merge/deploy.
- Both existing ChatGPT Backend Builder and Frontend Builder hourly tasks were updated **without schedule or enable-state changes** to prioritize finishing incomplete source-plus-tests branches and opening PR before long CI waits.
- **Remaining gates:** on first live GitHub Actions schedule/dispatch, establish whether repository settings allow `GITHUB_TOKEN` PR creation (otherwise log `PR_RELAY_WRITE_BLOCKED`); `GITHUB_TOKEN`-created draft PRs may not trigger `pull_request` CI. Exact-head green CI and protected merge still required. **Unattended ChatGPT code → PR → CI → merge remains UNPROVEN**, see [Issue #609](https://github.com/MaksimBlud/football-ai/issues/609).
- No direct production deployment, model training/promotion, frozen prospective outcome reading, live Supabase changes, or paid Odds API calls occurred.

## 2026-10-11 — recovered scheduled Backend Builder branch / strict kickoff boundary (03:58 UTC)

**Verified current main after code merge:** `a9a04dee8aa6236a2da301d49c1012e111f309df`. [PR #614](https://github.com/MaksimBlud/football-ai/pull/614) merged after **6/6 exact-head CI successes** from head `be5c5a160ef2bb64bf719a0cb6da3c67e9b202ec`.

- During an hourly scheduled-task window, a **branch-only Backend test commit** `98a85c4316374a333605aa31c2b11b3aff8afcef` appeared at 03:39 UTC on `dev/backend-581-kickoff-boundary-20261011`; no PR had been created by that worker. Timestamp/branch proximity is evidence of background work but **the task's full tool log was not available to independently prove invocation attribution**.
- Original commit introduced a failing boundary test: at `now == kickoff`, the public upcoming forecast and bookmaker query should exclude the fixture. The code still used `gte` and the fake PostgREST test adapter lacked `gt`.
- In an **interactive** ChatGPT conversation, committed `6a6de972d30be46d325d38141f0b585db509dcee` to use strict `gt` for both prediction and odds kickoff filters; committed `be5c5a160ef2bb64bf719a0cb6da3c67e9b202ec` adding `gt` fake-query semantics and extra exactly-at-kickoff regression tests. Opened PR #614, verified 6/6 CI, unchanged fresh main, exact PR head, safely squash merged, verified GitHub main `a9a04dee8aa6236a2da301d49c1012e111f309df`.
- Research Scout also wrote branch-only note `578ee8ef04beccca2a4fd5ab6f0fefa7241fa716` at 03:23 UTC: an outcome-free stadium altitude source audit with `IDEA / BLOCKED_BY_SOURCE_AND_MARKET_BASELINE`. It is NOT a confirmed signal and was not merged or promoted.
- The **end-to-end unattended scheduled ChatGPT code → PR → CI → merge remains UNPROVEN**, despite durable branch-only code and Scout documentation. Issue #609 stays open. No model API, paid Odds API, production model changes, Supabase writes/DDL, frozen-outcome reads or production deployment.

## 2026-10-11 — backend 1X2 normalization gate proof (02:10 UTC)

**Verified post-merge main:** `cfe0a499df6f46fddc2f11e67092382caf5fbcc4`. This change was completed **interactively in ChatGPT**, NOT by an unattended hourly task.

- [PR #612](https://github.com/MaksimBlud/football-ai/pull/612) merged safely at exact PR head `58d1ffd1df443298178f8d7ca9045fd4d2a325dd` after **6/6 green CI**; source commit `b3e8c0dcba0c4ab8e60de8b6fbebf0c862ed42e8`, test commit `58d1ffd1df443298178f8d7ca9045fd4d2a325dd`.
- `product_snapshot_store.py` now rejects missing/non-finite/out-of-range/inconsistent 1X2 probabilities before selecting the latest pre-kickoff snapshot, preserving an older valid snapshot. `tests/test_product_snapshot_store.py` covers invalid inputs, preservation, and rounded probabilities. No production model artifacts were changed.
- Live Supabase **read-only** sanity check of recent 60 days: 40 prediction rows, zero missing and zero >0.015 non-normalized 1X2 distributions. No Supabase writes/DDL.
- Connected GitHub schedule event for `Football AI Engineering Checkpoint (No API)` on 2026-10-11 at 01:00 UTC succeeded, but its workflow remains **read-only with zero AI calls and zero code writes**. No attributable autonomous ChatGPT coding PR found at this check; Issue #609 stays OPEN, `AUTONOMY_NOT_PROVEN`.
- No Gemini/Groq/OpenAI model APIs, paid The Odds API requests, production `.pkl` promotion, frozen-outcome peeking, direct-main modification or production deployment.

## 2026-10-11 — real interactive ChatGPT UI development proof (01:53 UTC)

**Verified post-merge main:** `43020bd37667639412e0d296ddf7db2f83a14e93`. This result was completed **interactively in ChatGPT**, NOT by an unattended scheduled task. It must not be counted as scheduled AI autonomy.

- Resumed stranded Frontend Builder branch `dev/ui-match-trust-20261010-1506` with pre-existing commit `77f147b781d2e33ec85778a09c6a5767f3778d75` (originally based on main `96d9a4f8be6cd6fd9f7412603c0695ad48bcf7bb`).
- Added executed-Node regression contract tests to `tests/test_product_ui_contract.py` as `eb6d7b7a1ee7863b0c429111748f3820c7f95579`: quoted bookmaker odds display only with verified pre-kickoff provenance, missing/future/ambiguous market quotes hidden, string odds rejected, missing timezone labelled, keyboard focus/alert semantics.
- [PR #610](https://github.com/MaksimBlud/football-ai/pull/610) passed **6/6 exact-head CI checks** (Eredivisie, Ligue 1, Research, Serie A, Product and Bundesliga). Pre-merge main remained `96d9a4f8be6cd6fd9f7412603c0695ad48bcf7bb`, PR mergeability verified; exact-head squash merged to `43020bd37667639412e0d296ddf7db2f83a14e93`, then confirmed live GitHub main and merged PR state.
- Actual changes: `static/match.html` and `tests/test_product_ui_contract.py`. No production model .pkl, Supabase, paid Odds API, additional model API, direct-main write, frozen prospective outcome reads or deployment.
- Evidence recorded on [Issue #609](https://github.com/MaksimBlud/football-ai/issues/609) and [Issue #582](https://github.com/MaksimBlud/football-ai/issues/582). **Autonomous scheduled ChatGPT code → PR → CI remains unproven**, notwithstanding this successful interactive cycle. Next autonomous task must read fresh main and avoid redoing PR #610.

## 2026-10-10 — no-API GitHub/ChatGPT build proof and state (12:19 UTC)

**Verified main:** `a407d9496eca440cb084e883eefd28b4deadb068`. All changes below were made through connected GitHub in an interactive ChatGPT session; do **not** attribute them to a scheduled autonomous AI worker.

- PR [#603](https://github.com/MaksimBlud/football-ai/pull/603) merged as `7ee3c5c606d07d2c2ce7f56b03bd76a8df1c2b06`. Installed an engineering GitHub Action plus strict write-scope guard/tests. The original action called Gemini and was **not** a viable zero-API autonomous coding worker.
- PR [#598](https://github.com/MaksimBlud/football-ai/pull/598) merged as `1334c5876150015237f0f5ff1b3d46af38ebd0a7` after six required CI successes: snapshot as-of timestamp DB filters, matching provider event identity/fixture kickoff, pricing sanity, and fail-closed saturation. No automatic DB DDL or .pkl promotion.
- PR [#604](https://github.com/MaksimBlud/football-ai/pull/604) merged as `12aed7dbe65201c93cd6c89d08c261b43833444e` after six required CI successes: match-page snapshot timestamp/provenance and explicit unavailable/ambiguous market states.
- PR [#605](https://github.com/MaksimBlud/football-ai/pull/605) merged as `13275ad9cbe2061a357f22b96a8fa85223b18073` after required CI: removed the Gemini API dependency. `.github/workflows/football-ai-engineering-autopilot.yml` is now an **hourly read-only GitHub engineering checkpoint** (cron minute 17) that reports main SHA, engineering issues, and open PRs. It never invokes an AI model or writes code. It does **not** wake this ChatGPT conversation.
- PR [#606](https://github.com/MaksimBlud/football-ai/pull/606) merged as `c9cc29f7c2aa8f1b420b08078671c56b01cf2c98` after 6/6 CI: homepage verifies backend market timestamps and pre-kickoff identity; unverified prices/value signals are hidden, with mobile/desktop UI and Node-backed tests.
- PR [#607](https://github.com/MaksimBlud/football-ai/pull/607) merged as `a407d9496eca440cb084e883eefd28b4deadb068` after 6/6 CI: independent keyless EPL fixture **schedule-only** endpoint and responsive fallback if model feed has no forecasts; official published matchweek-6 fallback automatically expires. No synthetic AI forecast or bookmaker quote. Superseded draft PR [#599](https://github.com/MaksimBlud/football-ai/pull/599) closed, not merged.
- Independent GitHub checkpoint's **pull_request** validation job succeeded, but **first schedule-triggered execution remains unverified** at this checkpoint. Do not infer successful hourly operation from a CI event.
- Existing ChatGPT Backend Builder, Frontend Builder, Research Brain and Signal Scout hourly tasks are configured, but the prior task self-disable/recovery pattern means **end-to-end unattended ChatGPT coding is still not proven stable**. A green GitHub heartbeat without SHA/PR created by an AI worker is **not** autonomous development.
- No new Gemini/Groq/OpenAI model APIs were configured or called in this work. No paid Odds API request, Supabase write/DDL, research frozen-outcome read, production .pkl change or production Vercel deployment was performed. Production Vercel site still requires a separately authorised promotion to include new main commits.

**Next execution pointer:** verify a **schedule** event for the no-API GitHub checkpoint (not merely PR CI), continue regression-tested engineering/research work with explicit PR/CI evidence, confirm old #599 is not reused, review stale PRs, and obtain **new explicit user permission** before any production deploy. Without a separate model service or always-on local model, GitHub alone cannot awaken consumer ChatGPT for autonomous code generation; never claim that this gap is solved.

---

## Правила работы

- Repo: `MaksimBlud/football-ai`, default branch `main`.
- Существенный change: fresh main -> isolated branch -> tests -> PR -> полный required CI -> fresh-main compare -> exact-head merge -> post-merge/live proof -> continuity-only update.
- Production `.pkl` нельзя менять как побочный эффект research/training. Training/research != production promotion. Automatic model promotion запрещён.
- Не делать mass-clean/reset/mass-format и не перетирать параллельные изменения.
- Frozen/preregistered research contracts нельзя ослаблять задним числом; prospective outcomes нельзя читать до разрешённого gate.
- Paid provider calls остаются manual-only и требуют explicit permission; сначала использовать zero-cost/read-only proof.
- Реальные дефекты закрывать regression-тестами. Fail-closed red нельзя искусственно превращать в green.
- Point-in-time history нельзя реконструировать ретроспективно, если durable source её не сохранил.
- Forecast, value, bet decision и portfolio exposure — разные сущности и не подменяют друг друга.
- Unsupported markets/results нельзя синтезировать ради полноты UI.

---

# Research state

## `ALL_LEAGUES_MARKET_ONLY_V1_1` — FROZEN / SAMPLE_CLOSED / COLLECT, DON'T PEEK

- Freeze: `2026-09-12T02:04:34Z`; first seed kickoff: `2026-09-12T12:00:00Z`.
- Frozen seed: exact `127` immutable keys across 8 leagues.
- Gate: минимум `100` eligible events **в каждой** лиге + минимум `4` distinct UTC kickoff months **в каждой** лиге; все 8 проходят одновременно.
- Primary sample = deterministic prefix by kickoff/event/key; outcomes закрыты минимум до 24h после latest primary-prefix kickoff.
- Interim outcome peeking, threshold search, subgroup selection и performance-based optional stopping запрещены.
- Primary metrics после открытия gate: multiclass log loss + multiclass Brier; secondary: argmax accuracy; report per league + pooled micro + unweighted league macro.
- До gate разрешены только outcome-blind health/identity/completeness checks и frozen future-only capture.

## `EPL_AI_MARKET_PAIR_V1` — SEPARATE FROZEN EPL EXPERIMENT

- Не смешивать с eight-league MARKET_ONLY cohort и не backfill product rows как research evidence.
- Production EPL model нельзя переносить на другие лиги ради ускорения sample.
- Product bootstrap использует durable paired-AI outputs, но не меняет frozen membership/gates.
- Frozen model artifact SHA: `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`.

## Historical corners — CLOSED / STOP RULE

`CORNERS10` остаётся полезным football-only signal для 1X2, но не доказательством качества corner-total prediction. Historical corner-total V1–V4 не переоткрывать на тех же данных без independent evidence.

---

# Signal Discovery 2026-09-13 — BLOCKS 1–7 COMPLETE / RESEARCH-ONLY

Этот bounded historical pass завершён полностью. Он **не заменяет P0–P4 anti-jump strategy, не меняет frozen cohorts, не открывает prospective outcomes и не разрешает Candidate V2/production promotion**.

Общая методология:
- existing Historical Football Signal Lab reused; no second incompatible framework;
- Football-Data seasons `2016-2017` through `2025-2026`, EPL + La Liga + Serie A, `11,400` historical fixtures total;
- expanding-season walk-forward: first 3 seasons train, next season test, then expand; 7 evaluated seasons per league;
- feature/capability contracts fixed before reading each new result;
- no post-result window/threshold/combination search;
- point-in-time feature construction only; regression contracts protect current-match leakage;
- performance candidates separated football-only quality from incremental value beyond `MARKET_MODEL`;
- unsupported lineup/tactical/xG inputs fail closed instead of being fabricated;
- no frozen prospective outcome reads, no Supabase writes, no paid-provider calls, no training/promotion;
- production `.pkl` hashes remained unchanged through full historical runs.

### Block 1 — `TEAM_STRENGTH_TRAJECTORY_V1`

Status: **FOOTBALL-ONLY STRONG / MARKET-INCREMENTAL NOT PROVEN**.

Fixed signals: pre-match Elo level difference; five-prior-match Elo trajectory difference; five-prior-match performance-vs-Elo-expectation residual difference.

Vs `CORNERS10`:
- EPL: accuracy `+0.003759`, Brier `-0.010168`, log loss `-0.012839`; Brier wins `7/7`, log-loss wins `6/7`;
- La Liga: accuracy `+0.018421`, Brier `-0.012917`, log loss `-0.016970`; Brier/log-loss wins `7/7`;
- Serie A: accuracy `+0.007895`, Brier `-0.009481`, log loss `-0.013597`; Brier/log-loss wins `7/7`.

Vs `MARKET_MODEL`:
- EPL Brier `+0.000235`, log loss `+0.000741`;
- La Liga Brier `+0.000092`, log loss `+0.000356`;
- Serie A Brier `-0.000435`, log loss `-0.000412`.

Decision: retain as a promising portable football-only candidate; no production/prospective insertion without a new allowed contract.

PR #291: head `0c0332555bcf30af931ad3083ff8ce75e80d254d`; run `34747661915`; artifact `10315155019`; exact-head merge `174775e5f80710aac36aa492b065ab6b1bc25ceb`.

### Block 2 — `REST_CONGESTION_V1`

Status: **NEGATIVE / CLOSED**.

These are league-schedule proxies, not full physical congestion because the source does not contain complete cup/Europe/travel calendars.

Fixed signals: relative rest days; relative prior-7-day league match count; relative prior-14-day league match count.

Vs `CORNERS10`: EPL Brier/logloss `+0.002043/+0.005107`; La Liga `+0.000933/+0.001509`; Serie A `+0.002033/+0.013757`.

Vs `MARKET_MODEL`: EPL `+0.002429/+0.007620`; La Liga `+0.001607/+0.002576`; Serie A `+0.002104/+0.015254`.

Decision: exact V1 is closed. Do not tune alternative windows/thresholds on the same sample. Reopen only with independent richer schedule evidence or genuinely new hypothesis.

PR #292: head `a5467159b7baae1872277180e2677b5a54c61c44`; run `34747790372`; artifact `10314692143`; exact-head merge `0eda74a2bc9dd5a0bbd8246add263b26ca79edd2`.

### Block 3 — `SHOT_QUALITY_PROXY_V1`

Status: **FOOTBALL-ONLY PROMISING / MARKET-INCREMENTAL NEGATIVE; TRUE xG SEPARATE**.

The real 30 downloaded season files contain shots/shots-on-target but no detected true-xG pair. Shots/SOT are therefore a proxy and must never be called xG.

PRIMARY EPL + La Liga vs `CORNERS10`:
- EPL: accuracy `-0.003008`, Brier `-0.001493`, log loss `-0.001770`; Brier/log-loss wins `5/7`;
- La Liga: accuracy `+0.001880`, Brier `-0.004266`, log loss `-0.006725`; wins `7/7`.

PRIMARY vs `MARKET_MODEL`:
- EPL: accuracy `-0.004511`, Brier `+0.002504`, log loss `+0.004006`;
- La Liga: accuracy `+0.003383`, Brier `+0.001169`, log loss `+0.001616`.

Serie A remains sensitivity-only due source shots-definition caveat.

Decision: retain as football-only research evidence; market-incremental negative; no same-sample feature/window search. True xG remains separate data-source gate.

PR #293: head `e3252edbbda71b975b65f01d8c20b268b134d534`; run `34747980991`; artifact `10315020904`; exact-head merge `2dfc375d51a6d0c825597c1280b77d5120c0bd00`.

### Block 4 — `LINEUP_STRENGTH_CAPABILITY_V1`

Status: **DATA_GAP / FAIL-CLOSED**.

Current source lacks supported point-in-time lineup/player-strength inputs. Generic team aggregates such as `TeamStrength` are explicitly forbidden as substitutes for lineup strength. A future experiment requires identifiable XI/lineup data, explicit player/lineup value and pre-kickoff temporal provenance.

PR #295: head `ee3f765f4afa934d556451be7097dc0a2bc50494`; historical run `34750466337`, job `103705987342`; all required CI + `.pkl` guard green; merge `c6872f5fe244fb4c42175e513d7bf6be97e69dfc`.

### Block 5 — `TACTICAL_MATCHUP_CAPABILITY_V1`

Status: **DATA_GAP / FAIL-CLOSED**.

Shots/corners/fouls/cards remain team-stat proxies and are not relabeled tactical data. A tactical experiment requires explicit tactical context such as formation, possession/passing structure or pressing fields plus point-in-time provenance.

PR #296: head `b26ae4b59a94657180553a883fc22d5f430ce9dc`; historical run `34750626439`; all required CI green; merge `c33fc73d7ed78a1e50403315d22cb42a325290bd`.

### Block 6 — `TRUE_XG_CAPABILITY_V1`

Status: **DATA_GAP / FAIL-CLOSED**.

True-xG experiment requires a genuine paired home/away xG schema plus temporal provenance. Shots/SOT are never synthesized into xG; a partial xG schema also fails closed.

PR #297: head `7e8cfbb3a5c1b9ca4d374ab4b814c83f53e2da1e`; historical run `34750911202`, job `103707181172`; full lab + production-hash guard green; merge `f9dcf4576164fb92b41fb7ce3dce39d1b1d69c43`.

### Block 7 — `TRAJECTORY_SHOT_INTERACTIONS_V1`

Status: **NEGATIVE / CLOSED**.

This was a bounded interaction test. Baseline already contained full Trajectory + Shot Quality main effects. Candidate added only two fixed predeclared moderation terms; `REST_CONGESTION_V1` was excluded because it was already closed.

PRIMARY incremental deltas, positive = worse:
- EPL vs football main-effect baseline: Brier `+0.000481`, log loss `+0.000745`;
- EPL vs market + main-effect baseline: Brier `+0.000334`, log loss `+0.000515`;
- La Liga vs football main-effect baseline: Brier `+0.001188`, log loss `+0.001955`;
- La Liga vs market + main-effect baseline: Brier `+0.000899`, log loss `+0.001462`.

Decision: exact interaction hypothesis closed. No same-sample interaction mining/retuning.

PR #298: all required CI + Historical Signal Interactions + production-hash guard green; exact-head merge `63623a30441725247ba1092ec783e6b55667f174`.

Continuity closure for blocks 4–7: PR #299, documentation-only head `79d193c0a80e30fb96c975651d9a072f46cb4daa`, all six validations green, merge `d5a82c6d684f08a94d6406f3849cfeccd9f4f425`.

### Signal Discovery synthesis

- strongest new football-only result: `TEAM_STRENGTH_TRAJECTORY_V1`;
- `SHOT_QUALITY_PROXY_V1`: smaller but directionally useful football-only evidence;
- neither proved robust historical incremental superiority over bookmaker market;
- league-only Rest/Congestion exact V1 is negative/closed;
- Lineup Strength, Tactical Matchup and True xG are current-source capability gates, not fabricated negative performance results;
- fixed trajectory × shot-quality interaction is negative/closed;
- no new prospective cohort created; no frozen membership changed; Candidate V2/model promotion stays closed until existing evidence gates permit a new separately preregistered decision.

---

# Product state / contracts

Binding invariant: **forecast != value != bet != portfolio position**.

Current market maturity:
- EPL / 1X2 = `OPERATIONAL`;
- EPL / Total Goals = `PROVISIONAL` / model-only;
- EPL / Handicap = `RESEARCH_ONLY`;
- EPL / Corners Total = `RESEARCH_ONLY`;
- `bet_decision = no_bet` in Decision Framework v1.

Durable product path:
`immutable prediction snapshot -> Supabase -> independent odds join by provider event_id -> server contract -> UI/API`.

Last proven live state before the current deployment block:
- product prediction snapshots = `20`, duplicate provider event IDs = `0`;
- future EPL product coverage = `13/13` at last live product proof;
- lifecycle = `20 PREDICTION_REGISTERED / 7 MARKET_OBSERVED / 7 SETTLED = 34` rows;
- duplicate lifecycle event keys = `0`;
- settled exact-scope reliability sample = `7`, all EPL and exact frozen model SHA;
- reliability state = `ACCUMULATING_SAMPLE / INCONCLUSIVE`; required gate remains >=`100` settled exact-scope predictions + >=`4` kickoff months;
- descriptive tiny-sample metrics: accuracy `1/7`, mean multiclass Brier `0.8476987182`, mean log loss `1.3455261760`; these are not a promotion/reliability verdict;
- Portfolio/Risk v1 remains structural-only; zero actionable positions at last proof; no staking/Kelly/bankroll policy;
- new scopes can automatically reach at most `REVIEWABLE`; `OPERATIONAL` requires explicit approval.

## Product Operational Automation v1 — LIVE RUNTIME / IDEMPOTENCY PROVEN

- workflow cadence `37 */2 * * *` plus manual dispatch;
- private Supabase append-only path only;
- no paid-provider call, model inference/training/promotion, frozen research target read, bet or stake;
- first-prediction-only revision guard prevents repeated forecasts of one fixture from inflating evidence;
- lifecycle reads paginated; >5000-row regression exists.

Implementation PR #286: head `66a42a559f792d4f2d6fd187509c1b521c947f84`; six required CI green; merge `680ce8a694f6f49dd83452f0e3c776593c70a5e2`.

Bounded runtime bootstrap PR #288: exact head `2c75d1470ba0e28bbfa8a88dd565e41d47daa9ce`; path-scoped workflow push only; merge `182f0fc0a3fbd0e392b08a3c77f8579ae7b61ebd`.

First real runtime run `34745945144`, first job `103693795481`: exact main checkout, private credential contract passed, appended exactly `2 MARKET_OBSERVED + 7 SETTLED`, product snapshots `0`, no paid/model/betting actions. Same run rerun job `103693963665` applied `0/0`, proving idempotency.

Cleanup PR #289 removed its temporary push bootstrap and merged as `26608134c1cb68a6ce68da5d8c3c304870d88f4c`.

---

# Exact-main Vercel deployment — CONTRACT MERGED / EXECUTION BLOCKED BY MISSING SECRET

Target Vercel project:
- project name `football-ai-real-epl-snapshot`;
- project ID `prj_lXttnTmlPncJPn2nKGSlid2vaxvg`;
- team ID `team_EDncljUUtFDTumz5hYleW8R3`;
- public alias `https://football-ai-real-epl-snapshot.vercel.app`;
- Vercel project is not Git-linked (`link=null`).

Previous public/runtime audit established that the deployed site lagged repository main. The connector's generic deployment action did not expose a safe repository+exact-SHA source contract, so a blind no-arg deploy was deliberately rejected.

## Real repository web contract

The actual Vercel runtime in fresh main is:
- `pyproject.toml`: `[tool.vercel] entrypoint = "web_app:app"`;
- `vercel.json`: function `web_app.py`;
- public routes: `/`, `/match`, `/health`, `/product-market-view`, `/portfolio-risk-view`, `/production-readiness-view`, `/product-market-view/{match_id}`.

Important correction: earlier provisional smoke planning referenced `/api/product/markets`, `/api/product/reliability`, `/api/product/portfolio`, `/api/product/readiness`. Those are **not** the current `web_app.py` routes and must not be used as canonical deployment smoke targets.

## PR #300 — exact-main deployment proof contract

Branch: `ops/exact-main-vercel-deploy`, based on `d5a82c6d684f08a94d6406f3849cfeccd9f4f425`.

Final tested head: `9ec514a55105e13c2fb9c8437921fc6bb78a1ff0`.

Changes:
- dependency-free `deployment_identity.py` reads explicit `DEPLOYMENT_GIT_SHA`, falls back to `VERCEL_GIT_COMMIT_SHA`, otherwise `unknown`;
- `/health` now includes `deployment_git_sha` without changing model/product semantics;
- new regression `tests/test_exact_main_vercel_deployment.py`;
- Product PR Validation runs the deployment regression;
- `.github/workflows/exact-main-vercel-deploy.yml` stages a Production-environment build with `vercel deploy --prod --skip-domain`, injects exact source SHA, validates staged `/health`, real product routes, rechecks `origin/main`, promotes only after proof, then verifies the public alias;
- workflow has no Odds API or Supabase write credentials and cannot train/infer/promote a model.

First PR CI attempt on head `4005ef26c028ae2e20a05518c9ef7ad24f1d1d02` found a real test-environment issue: new test imported `web_app`, while Product PR Validation intentionally installs only `pytest`; job `103734328113` failed with missing FastAPI. Fix moved source identity into dependency-free `deployment_identity.py` and tested that helper directly while source-checking the `web_app.py` wiring.

Final head `9ec514a55105e13c2fb9c8437921fc6bb78a1ff0` passed all six required PR workflows:
- Product PR Validation run `34761449717` — success;
- Research PR Validation run `34761449740` — success, including production `.pkl` guard;
- Serie A PR Validation run `34761449723` — success;
- Bundesliga PR Validation run `34761449746` — success;
- Ligue 1 PR Validation run `34761449741` — success;
- Eredivisie PR Validation run `34761449756` — success.

Because the connected GitHub execution surface cannot create a `workflow_dispatch` run, PR #300 uses the previously proven bounded bootstrap pattern: `push` on `main` **only when `.github/workflows/exact-main-vercel-deploy.yml` itself changes**. There is no schedule or PR deploy trigger; ordinary product/research commits do not auto-deploy.

Fresh-main before merge remained exact base `d5a82c6d684f08a94d6406f3849cfeccd9f4f425`. PR #300 was exact-head merged as:

`4e2e8d5848d07ef6ba924e669833f20d807ddd32`

## First real exact-main deployment attempt

Bounded merge trigger created:
- workflow `Exact Main Vercel Deployment`;
- run ID `34761518406`, run number `1`, event `push`;
- exact head/source SHA `4e2e8d5848d07ef6ba924e669833f20d807ddd32`;
- job ID `103735079637`.

Runtime proof:
- checkout succeeded on exact `main` SHA `4e2e8d5848d07ef6ba924e669833f20d807ddd32`;
- `Capture exact main source identity` succeeded;
- `Check Vercel credential contract` failed explicitly with `VERCEL_TOKEN is not configured`;
- Actions environment showed `VERCEL_TOKEN` empty; no secret value was exposed;
- Vercel CLI installation, settings pull, staged deploy, staged SHA smoke, product smoke, main recheck, promotion and public-production verification were all **skipped**;
- therefore **no Vercel deployment or production alias change occurred**;
- no paid provider, Supabase write, model inference/training/model promotion, bet or stake occurred.

This converts the former deployment uncertainty into a concrete infrastructure gate:

**`EXACT_MAIN_DEPLOYMENT = BLOCKED_BY_MISSING_GITHUB_ACTIONS_SECRET(VERCEL_TOKEN)`**.

Do not claim exact-main is live until this secret exists and the workflow completes staged SHA proof + product smoke + promotion + public SHA proof.

## Post-merge public runtime proof — 2026-09-13 14:17 UTC

After continuity PR #301 merged, a new read-only verification was performed against both Vercel deployment metadata and the public production alias:
- current GitHub `main` after PR #301 = `142bfd1d1d0604cbf7b92f15909a243639f5c8a9`;
- Vercel deployment listing from `2026-09-13T14:00:00Z` onward returned `0` deployments, consistent with the fail-closed credential stop;
- public `/health` returned HTTP `200` but exposed only `status`, `mode`, `credential_mode`, and `match_identity`; the new `deployment_git_sha` field from PR #300 is absent;
- public `/product-market-view` returned HTTP `200` and still serves the older product-market contract;
- public `/portfolio-risk-view` returned HTTP `404`;
- public `/production-readiness-view` returned HTTP `404`.

Therefore the public alias is not merely unproven: these route/health observations positively demonstrate that it is **not running the PR #300 exact-main runtime contract**. No deployment was created by this post-check and production remained unchanged.

---

# Durable PR reference — 2026-09-13

Product/runtime chain: #267–#277 foundation/live pipeline; #278 Decision Framework; #279 Lifecycle; #280 lifecycle security hardening; #281 Reliability; #282 Portfolio/Risk; #283 continuity correction; #284 Production Readiness; #286 Operational Automation; #287 pre-runtime continuity; #288 runtime bootstrap; #289 bootstrap cleanup; #300 exact-main Vercel deployment contract.

Signal discovery chain: #291 `TEAM_STRENGTH_TRAJECTORY_V1`; #292 `REST_CONGESTION_V1`; #293 `SHOT_QUALITY_PROXY_V1`; #294 blocks 1–3 continuity; #295 Lineup capability; #296 Tactical capability; #297 True xG capability; #298 fixed interactions; #299 blocks 4–7 continuity.

Continuity chain: #301 records the exact-main deployment blocker and execution pointer; the current continuity-only follow-up records the post-merge public runtime proof.

All substantive PRs were required to pass their applicable Product/Research/league CI and production artifact guards before exact-head merge.

---

# Current checkpoint

- Latest substantive repository change: PR #300 merge `4e2e8d5848d07ef6ba924e669833f20d807ddd32`; latest merged continuity checkpoint before this follow-up: PR #301 merge `142bfd1d1d0604cbf7b92f15909a243639f5c8a9`.
- Production `.pkl` state was not changed by Signal Discovery or deployment work.
- Signal Discovery blocks 1–7: **COMPLETE** with stop-rules above.
- Frozen V1.1 and EPL paired-AI outcome gates remain closed; no-peek remains binding.
- Product snapshots/lifecycle/reliability last proven state remains `20` snapshots, `34` lifecycle events (`20/7/7`), `7` exact-scope settled, `ACCUMULATING_SAMPLE / INCONCLUSIVE`.
- Readiness remains EPL 1X2 operational; goals provisional; handicap/corners research-only.
- Exact-main deployment contract is merged and CI-proven, but production deploy is **not complete** because `VERCEL_TOKEN` is missing from GitHub Actions.
- Public production is positively proven to lag PR #300: `/health` lacks `deployment_git_sha`, `/product-market-view` is `200`, while `/portfolio-risk-view` and `/production-readiness-view` are `404`; no Vercel deployments appeared after `14:00 UTC` during the deployment attempt window.

# Текущий execution pointer

## Research

- `ALL_LEAGUES_MARKET_ONLY_V1_1`: **COLLECT, DON'T PEEK / SAMPLE_CLOSED**.
- `EPL_AI_MARKET_PAIR_V1`: separate frozen experiment; no cohort inference from product bootstrap.
- Any paid refresh remains a separate manual gate.
- Candidate V2/model promotion remains closed.
- No same-sample reopening of closed Rest/Interaction/Corner-total hypotheses.
- Lineup/Tactical/True-xG wait for genuinely supported point-in-time data sources and new preregistered contracts.

## Product — immediate next action

1. **Provision GitHub Actions secret `VERCEL_TOKEN` with access to the known Vercel team/project.** This is now the only proven blocker to the exact-main deploy workflow.
2. Rerun `Exact Main Vercel Deployment` on current `main` (prefer `workflow_dispatch`; the path-scoped push remains only a bounded bootstrap mechanism).
3. Require staged `/health.deployment_git_sha == current GitHub main SHA`.
4. Require staged smoke success for `/product-market-view`, `/portfolio-risk-view`, `/production-readiness-view`.
5. Recheck that `main` did not move before `vercel promote`.
6. Promote only the verified staged deployment and repeat public `/`, `/health` and three product-route checks; exact production SHA must match current GitHub main.
7. After exact-main live proof, close this deployment block in continuity and proceed to **Total Goals readiness** as the next product expansion block.

Do **not** jump to Total Goals activation while exact-main public deployment remains blocked/unproven. Goal total work starts only after the deployment gate above is closed, unless a future explicitly approved roadmap change says otherwise.

---

# Research cycle 2026-09-14/15 — OPENED EVIDENCE + MARKET_ANCHOR_1X2_V1

Этот раздел **суперседит устаревший research checkpoint выше**, где EPL outcome gate ещё считался полностью закрытым. Старую запись оставляем как исторический audit trail.

## Eval43 cross-league replay — PR #322 / #323

PR #322 froze deterministic mature `43`-event evaluation cohort from the 47-event point-in-time replay; four not-yet-mature identities remained rollover. Merge: `23b86b03e0af66adf7ace06a87718373b8a18982`.

PR #323 recorded the allowed Eval43 outcome join and fixed pooled metrics; merge: `28b7a4a3bf02e1cf13c0ca21b2dc53901413e68f`.

Canonical report: `experiments/point_in_time_cross_league_replay_v1_eval43_report.json`.

Eval43, `n=43`:
- AI Brier `0.6125651124394431` vs Market `0.5975406259362642`; delta `+0.015024486503178891` — AI worse.
- AI LogLoss `1.0249478419454585` vs Market `0.9958508866152331`; delta `+0.029096955330225382` — AI worse.
- AI accuracy `17/43 = 39.53%`; Market `21/43 = 48.84%`.
- top-1 disagreements `10`: AI correct / market wrong `0`; market correct / AI wrong `4`; both wrong `6`.
- formal status `WARNING`; `bet_decision = NO_BET`.

League deltas, AI-Market:
- Bundesliga: Brier `+0.0291226809`, LogLoss `+0.0440517904`;
- Eredivisie: `+0.0114017352`, `+0.0316031669`;
- La Liga: `+0.0760267328`, `+0.1229242526`;
- Ligue 1: `+0.0074269370`, `+0.0232138378`;
- Serie A: Brier `-0.0671068156`, LogLoss `-0.1064237240` — the only positive league slice, too small for a standalone claim.

Eval43 remains valid research evidence; it was **not retired**. Do not repeat the earlier transient claim that PR #324 invalidated its identity contract.

## EPL early exploratory 11 — PR #324

Under explicit user authorization, `11` already-settled prospective EPL paired-AI outcomes were opened early. PR #324 merge: `57cace46bcf61557837a8235f1239b06813f39eb`.

Canonical report: `experiments/epl_ai_market_pair_v1_early_interim_11_report.json`.

Exact exploratory metrics, `n=11`:
- AI Brier `0.7387143340906316` vs Market `0.7153976428033418`; delta `+0.023316691287289748`.
- AI LogLoss `1.1913041652574738` vs Market `1.1545062906860382`; delta `+0.036797874571435685`.
- AI accuracy `2/11 = 18.18%`; Market `4/11 = 36.36%`.
- top-1 disagreements `2`; AI wins `0`, market wins `2`.
- `bet_decision = NO_BET`.

The predictions themselves were genuinely frozen pre-outcome, but opening these outcomes before the original `2026-11-01T12:16:54.672903Z` gate means the old pristine 100-match EPL primary no-peek claim is **no longer available**. Do not present the 11 as a completed primary experiment and do not silently restore the old no-peek claim.

## Architectural diagnosis

Production `football_model_xgboost_elo.pkl` consumes bookmaker odds as ordinary model features together with football state. It therefore has no structural obligation to preserve bookmaker probabilities as a strong prior and can arbitrarily deform them. The 43-event replay and 11-event EPL exploratory evidence both showed the same practical failure mode: current AI probabilities were worse than market on Brier, LogLoss and top-1 accuracy.

This motivated a new architecture rather than another unconstrained `market + features -> classifier` refit.

## `MARKET_ANCHOR_1X2_V1` — historical temporal OOT / research-only

PR #325 branch: `research/market-anchor-1x2-v1`, created from exact main `57cace46bcf61557837a8235f1239b06813f39eb`.

Final exact tested head: `ace9d9f346c78a1532b5956913fafe9c4bfb3ba5`.
Exact-head merge: `5a818b0babf013d79227a78f3e62237e85c3d16f`.
All 8 final head checks completed without failure; production artifact guards stayed green.

Architecture:
- mandatory prior = de-vigged market H/D/A distribution `m`;
- football-only residual logits `r(x)`;
- candidate `p = softmax(log(m) + lambda * r(x))`;
- `lambda = 0` is exact market identity, not an approximation;
- regularized residual uses football-only state; market is an offset, not a trainable football feature;
- fixed feature variants: `FORM`, `FORM_GOALS`, `FORM_GOALS_CORNERS`, `ALL_FOOTBALL`;
- fixed lambda grid: `[0.0, 0.10, 0.25, 0.50, 0.75, 1.0]`;
- train `2016-2017..2023-2024`;
- validation `2024-2025`;
- untouched final OOT `2025-2026`;
- opened September 2026 outcomes are excluded from train, selection and final OOT;
- within each league, non-zero residual is admissible on validation only if it improves **both** Brier and LogLoss; otherwise exact market fallback;
- pooled final OOT accepts residual only if both Brier and LogLoss beat market; otherwise active output is exact market.

Canonical frozen OOT report: `experiments/market_anchor_1x2_v1_report.json`.
First fixed OOT run: `34917928502`; artifact `10376584443`; digest `sha256:d015b35f305fe934e99559184425ec3b69f165e1f85e57294eddb5a06b771746`.

Untouched 2025-2026 pooled OOT, `n=1140`:
- Market Brier `0.588996235405689`; active candidate `0.5886577613918851`; delta `-0.0003384740138039355`.
- Market LogLoss `0.9881046787642729`; active candidate `0.9877190854806019`; delta `-0.0003855932836709375`.
- Market accuracy `52.63%`; active candidate `52.72%`.
- formal V1 gate: `residual_accepted = true`, `active_mode = RESIDUAL`.

League selection remained fail-closed:
- EPL: `MARKET`, `lambda=0`; exact market equality on final OOT.
- La Liga: `MARKET`, `lambda=0`; exact market equality on final OOT.
- Serie A: `ALL_FOOTBALL`, `lambda=1.0`; `n=380`; Brier `0.5844386773 -> 0.5834232552`, delta `-0.0010154220`; LogLoss `0.9821022022 -> 0.9809454224`, delta `-0.0011567799`; accuracy `53.95% -> 54.21%`.

Interpretation: the new architecture reached the user's minimum in a defensible structural sense — where incremental football signal is not proven, the active candidate falls back to exact market rather than degrading it. The pooled untouched V1 sign is also slightly positive, but the magnitude is small and **does not authorize production promotion**.

## V1 robustness — corrected post-selection diagnostic

A real implementation defect was found during robustness work: an initial diagnostic version would have refit the final Serie A model using validation 2024-2025, while frozen V1 final OOT used training only through 2023-2024. That path was rejected before being treated as authoritative. Regression tests now explicitly require the frozen split and prohibit validation from entering final refit.

Corrected robustness run: `34918346551`; job `104220736279`; artifact `10377595106`; digest `sha256:56ebad616726e6c3f690a4b2c05949e4a5971d1a3a60d828bf65bb054b9b4734`.
Canonical report: `experiments/market_anchor_1x2_v1_robustness_report.json`.

Exact frozen Serie A OOT (`n=380`):
- Brier mean delta `-0.0010154220414116213`; paired bootstrap 95% CI `[-0.005165043497376611, +0.003236877119355216]`; bootstrap probability better than market `0.6831`.
- LogLoss mean delta `-0.0011567798510132698`; 95% CI `[-0.008068947941734678, +0.006038957657259541]`; probability better than market `0.6317`.
- candidate beats market per-match on Brier in `53.68%` and LogLoss in `57.63%` of fixtures.
- fixed post-selection configuration wins both metrics in only `2/6` earlier retrospective seasons.

Therefore V1's formal historical OOT acceptance remains true, but persistent superiority is **not robustly proven**: both uncertainty intervals cross zero and historical season stability is weak. Status stays research/shadow only, `NO_BET`, **NO PRODUCTION PROMOTION**.

## Freeze/safety hardening in PR #325

- `market_anchor_1x2_v1_freeze_guard.py` compares the complete frozen JSON structure and all non-floats exactly; finite floats may drift only within `1e-12` to avoid false failures from platform/library last-bit differences.
- Separate regression tests cover the freeze guard.
- Corrected robustness is cross-checked against the exact frozen Serie A V1 sample/training split.
- Dedicated workflows snapshot production `.pkl` hashes before/after and fail on any change.
- No paid Odds API calls, no Supabase writes, no model promotion, no bet/stake action occurred in this research block.

---

# Current checkpoint — 2026-09-15 (supersedes the stale checkpoint above)

- Current substantive `main` after PR #325 = `5a818b0babf013d79227a78f3e62237e85c3d16f`.
- Production `.pkl` artifacts remain unchanged by Eval43, EPL exploratory read, MARKET_ANCHOR V1 and robustness work.
- Existing production XGBoost is **not** considered proven competitive with the market; opened 43-event replay and 11-event EPL exploratory evidence both favor market.
- `MARKET_ANCHOR_1X2_V1` is the new research baseline architecture: exact market fallback by construction; historical OOT residual edge is positive but small and not robust enough for production.
- EPL old pristine 100-match primary no-peek claim is no longer available after the authorized early 11-outcome read. Do not claim otherwise.
- `ALL_LEAGUES_MARKET_ONLY_V1_1` remains a separate frozen collect/don't-peek experiment; its binding gate must not be weakened.
- Product/deployment facts from the 2026-09-13 section remain unchanged unless separately re-verified; this research cycle did not deploy or promote a model.

# Текущий execution pointer — research

1. **Do not retune V1 on the now-opened 2025-2026 OOT or September-2026 Eval43/EPL outcomes.** Those samples are evidence, not reusable selection data.
2. Define `MARKET_ANCHOR_1X2_V2` as a new preregistered contract with a stricter stability gate before any fresh prospective outcomes are read. Stability must be a requirement, not post-hoc decoration.
3. V2 should keep the exact market fallback invariant. A football residual may become active only under predeclared multi-period / uncertainty requirements; otherwise `lambda=0`.
4. Create a **new prospective 2026-2027 shadow cohort** after V2 freeze. Previously opened September-2026 outcomes are excluded from tuning and cannot be relabeled prospective evidence.
5. Keep V1/Serie-A residual shadow-only while fresh prospective sample accumulates. `NO_BET`; no production `.pkl` promotion.
6. Paid refresh remains manual-only; use already durable/future-only inputs and zero-cost/read-only checks first.
7. Continue to search for genuinely supported point-in-time lineup/tactical/true-xG sources separately; do not fabricate them from generic aggregates.

Minimum target going forward: **active probability output must never be allowed to abandon a proven market baseline without predeclared evidence that the residual adds value**. The next milestone is not a larger backtest score; it is a stable, prospective proof that any non-zero residual survives fresh data.

---

# Research cycle 2026-09-15 — BOOKMAKER RECONSTRUCTION + LIVE H2H TRANSFERABILITY

Этот раздел **суперседит research execution pointer выше** и фиксирует завершённый bookmaker-reconstruction/live-capture блок. Он не меняет product/deployment state и не разрешает production promotion.

## Historical bookmaker reconstruction chain — PR #330–#333

### PR #330 — `BOOKMAKER_RECONSTRUCTION_DEVIG_V1`

Merge: `f1264785a0f1b0a4e2ad8f2f5b0843ed0782f3e3`.

Fixed contract:
- raw Football-Data decimal odds only; already de-vigged market probabilities are not reused because they have lost overround information;
- fixed methods: `PROPORTIONAL`, `POWER`, `SHIN`;
- selection season: `2024-2025`, primary selector LogLoss then Brier tie-break;
- untouched OOT: `2025-2026`;
- no 2026-2027 outcomes;
- research-only / `NO_BET`; no Supabase writes, paid-provider calls, production `.pkl` writes or promotion.

`POWER` was selected in the frozen V1 comparison, but one selected OOT season is not enough to claim persistent superiority.

### PR #331 — de-vig robustness

Merge: `b1cf18f19cca944e4d42d07e1593b34816c8ce49`.

`POWER` vs `PROPORTIONAL` was replayed with no method re-selection across retrospective pre-validation seasons, the selection season and final OOT. This is robustness evidence only. The result does **not** justify replacing proportional de-vig in production by itself; persistent advantage must survive fresh evidence.

### PR #332 — bookmaker source/consensus diagnostic

Merge: `df6dafd1ea8b98b9c79b399d0fda91e76e06ffaf`.

Fixed source comparison: B365 vs PS vs Football-Data `AVG` on common fixtures. Coverage audit found an important data limitation on 2025-2026 OOT:
- B365 coverage = `1140/1140`;
- AVG coverage = `1140/1140`;
- PS coverage = `599/1140`;
- PS is temporally truncated toward the first half of the season, so the common-source cohort is not representative of the full 2025-2026 season.

Therefore the common-source performance comparison is diagnostic only; no post-hoc PS/AVG/B365 fallback or hybrid rule is authorized from it.

### PR #333 — full-coverage AVG vs B365

Merge: `8630e4ad338ea533b5b90c9c0aaef404cb7be5d9`.

`AVG` was compared with B365 on the full-coverage same-fixture historical cohort using fixed proportional de-vig. `AVG` is a multi-book aggregate and remains available across the full 2025-2026 three-league cohort, unlike PS.

**Evidence-class caveat is binding:** PR #333 is explicitly a **post-outcome diagnostic**, not a new untouched OOT experiment, because 2025-2026 outcomes had already been inspected in the preceding source work. Its results may motivate a separately frozen prospective source/consensus contract, but must not be used to declare AVG a proven production replacement after the fact.

## PR #334 — `H2H_BOOKMAKER_V1` durable live capture

Exact tested head: `0924353ac93d4a3865a175a8490298599b3e0b59`.
Merge: `0c6f9e5afc22ed665ce66e3834c6247c57abfbb0`.

Purpose: preserve bookmaker-level H2H quotes from the **same already-fetched The Odds API response** instead of discarding them after aggregate odds are computed.

Binding safety/cost contract:
- **zero additional provider requests** for bookmaker capture;
- each league's existing collector/freshness/quota gate remains authoritative for whether a paid H2H request happens at all;
- strict pre-kickoff persistence only;
- research payload forbids outcome/result/score fields;
- deterministic `snapshot_key` and payload hash;
- idempotent `upsert` on `snapshot_key`;
- research persistence is best-effort and cannot turn a successful paid aggregate snapshot into collector failure/retry;
- separate table avoids coupling H2H research writes to Multi-Market freshness logic;
- no new probability output, POWER/SHIN activation, model promotion, betting or staking is authorized.

Wired collectors: EPL, Serie A, Bundesliga, Eredivisie, Ligue 1, La Liga, RPL, Turkey Super Lig and Primeira Liga. Manual-only collectors remain manual-only.

Dedicated H2H PR workflow on final head passed compile, `7/7` regression tests and production `.pkl` diff guard. All eight PR validation workflows on the exact final head were green before merge.

## Live Supabase migration + discovered privilege defect

PR #334 migration created `public.league_h2h_bookmaker_snapshots` with:
- primary key `snapshot_key`;
- pre-kickoff check `snapshot_time_utc < kickoff_utc`;
- mandatory `research_only=true` payload flag;
- mandatory schema version `H2H_BOOKMAKER_V1`;
- provider fixed to `THE_ODDS_API`;
- bookmaker-count and payload-hash constraints;
- RLS enabled;
- service-role SELECT/INSERT policies.

Post-merge live verification found a real Supabase default-privilege issue: despite the intended narrow grant, `service_role` inherited broader table privileges including UPDATE/DELETE/TRUNCATE. This was treated as a defect, not accepted as residual risk.

## PR #335 — live grant hardening

Merge: `f7e7bc98305a91c4a4cb0f7f189b3d9d2fbaf252`.

Additive migration `20260915142500_h2h_bookmaker_grant_hardening.sql` now explicitly:
- `REVOKE ALL` table privileges from `anon`, `authenticated`, and `service_role`;
- grants back only `SELECT, INSERT` to `service_role`.

A regression test protects the ordering and forbids grants of UPDATE/DELETE/TRUNCATE. Dedicated H2H CI and all applicable Research/Product/league validations were green before exact-head merge.

### Final live Supabase proof

After both merged migrations were applied:
- table exists and `row_count = 0`;
- RLS = enabled;
- `anon` grants = none;
- `authenticated` grants = none;
- `service_role` grants = exactly `INSERT`, `SELECT`;
- policies = service-role `INSERT` + `SELECT` only;
- pre-kickoff, research-only, schema-version, provider, counts and payload-hash constraints are live;
- migrations `league_h2h_bookmaker_snapshots` and `h2h_bookmaker_grant_hardening` are registered in live Supabase.

`row_count=0` is expected at closure because **no paid Odds API call was made merely to manufacture a proof row**. The first rows should arrive only when an already-authorized existing collector performs its normal provider read and the same response contains usable H2H bookmaker quotes.

Supabase security advisor produced no new H2H security finding after hardening. Performance advisor marked the two new H2H indexes unused, which is expected while the table is empty and is not a reason to remove them now.

## Current checkpoint — bookmaker reconstruction block CLOSED

- Current substantive `main` after PR #335 = `f7e7bc98305a91c4a4cb0f7f189b3d9d2fbaf252`.
- Production `.pkl` artifacts were not changed by PR #330–#335.
- No production model promotion occurred.
- `MARKET_ANCHOR_1X2_V2` remains fail-closed to the market baseline; current active residual state is not promoted by this work.
- `NO_BET` remains binding.
- No prospective outcome gate was weakened or opened by this block.
- No extra Odds API request was consumed for H2H bookmaker capture or live proof.
- Historical findings around POWER and AVG are research evidence only; neither is authorized as a production baseline replacement without a new preregistered prospective transferability contract.

# Текущий execution pointer — bookmaker reconstruction / market baseline

1. **Collect forward bookmaker-level H2H evidence without increasing provider-call frequency.** `H2H_BOOKMAKER_V1` should piggyback only on provider responses that existing league collectors already decided to fetch.
2. Do not backfill bookmaker-level point-in-time history from later states and do not synthesize missing books. Durable pre-kickoff rows are the evidence source.
3. Before reading outcomes from the new H2H bookmaker rows, freeze a separate prospective transferability contract. At minimum predeclare candidate de-vig methods/source representations, cohort identity, minimum sample/time coverage, metrics and acceptance gate.
4. Candidate baseline work should distinguish three separate questions: margin removal (`PROPORTIONAL`/`POWER`/`SHIN`), market representation (single book vs consensus/aggregate), and football residual value beyond that market baseline. Do not tune all three layers on the same opened sample.
5. Keep exact-market fallback as the safety invariant for Market Anchor work. A non-zero football residual must earn activation under the predeclared stability/prospective gate; otherwise active probability remains the market baseline.
6. Do not promote POWER, AVG, consensus weighting, dispersion features or any residual based solely on PR #330–#333 historical/post-outcome evidence.
7. Continue zero-cost/read-only health checks while the live bookmaker sample accumulates. Any deliberate extra paid refresh remains a separate explicit manual gate.
8. Production `.pkl`, betting/staking and automatic model promotion remain out of scope until a separately authorized gate is satisfied.

Next research milestone: **prospectively prove which market reconstruction is the strongest stable prior on fresh bookmaker-level data, then test whether football information adds incremental value beyond that stronger prior without ever allowing the active output to degrade below the proven market fallback.**

---

# La Liga prospective Market Anchor micro-cohort — 2026-09-15

## `LA_LIGA_MARKET_ANCHOR_PROSPECTIVE_20260915_V1` — FROZEN PRE-MATCH / OUTCOME-BLIND

PR #338 merged to `main` as `3d03fbb1613b2858fc10acbff5cf1b08a13d2d32`.

Purpose: create a genuinely forward, pre-match check of a La Liga analogue of the fixed Market Anchor residual architecture on the three 2026-09-15 fixtures, without transferring the Serie A artifact across leagues and without reading target outcomes.

Frozen contract before first kickoff:
- league = `LA_LIGA`;
- feature set = exact historical `ALL_FOOTBALL`;
- L2 = `1.0`;
- training = La Liga `2016-2017..2025-2026`, `3800` rows;
- training cutoff = `2026-06-30T23:59:59Z`;
- target feature-history cutoff = `2026-09-15T00:00:00Z`;
- active lambda = `0.0` (exact market fallback);
- shadow lambda = `1.0`;
- no feature/lambda/threshold/source tuning is authorized on these three outcomes;
- Brier + LogLoss are primary; accuracy is secondary;
- a directional micro-cohort win requires shadow to beat market on both pooled Brier and pooled LogLoss;
- `n=3` can never authorize production promotion, betting or staking by itself.

Durable market baseline:
- all three market rows were captured in live Supabase at `2026-09-11T15:45:28.192487Z`;
- all three used `19` bookmakers;
- no paid Odds API refresh was made for this experiment.

Canonical pre-kickoff freeze:
- capture time = `2026-09-15T15:55:40.251172Z`;
- first kickoff = `2026-09-15T17:00:00Z`;
- candidate artifact SHA256 = `9c0f004e14c075851ae874528e7d587ad344b12cdd89e227be68e84801b9d614`;
- freeze SHA256 = `58338f7f8823693aee81b5b0cf709e96c180af61c83204f904d55b972306d461`;
- canonical file = `experiments/la_liga_market_anchor_prospective_20260915_freeze.json`.

Frozen probabilities H/D/A:

1. Rayo Vallecano vs Espanyol — event `b9a6e597fd597637efa24b92d51dda62`, kickoff `17:00Z`
   - market / active lambda=0: `0.46932048598728 / 0.275291229511983 / 0.255388284500737`
   - shadow lambda=1: `0.4499889040086503 / 0.3122695776275001 / 0.23774151836384952`

2. Alavés vs Valencia — event `d6474326396cdd0e300afd0193c7c93d`, kickoff `18:00Z`
   - market / active lambda=0: `0.447759791488515 / 0.304537995169928 / 0.247702213341557`
   - shadow lambda=1: `0.5030653349939371 / 0.2749672990334827 / 0.22196736597258007`

3. Elche CF vs Real Madrid — event `0b57607f4a514ee24df31b0c2db9ddc5`, kickoff `19:30Z`
   - market / active lambda=0: `0.104522793893611 / 0.165700942434781 / 0.729776263671608`
   - shadow lambda=1: `0.09562785290451811 / 0.18196752022617652 / 0.7224046268693054`

Safety / proof:
- freeze runner contains no result/score/outcome fields;
- exact frozen historical source blobs are verified from commit `df19777087fb89af049eedce44ff93f0aa6e6360`;
- six dedicated regression tests passed before freeze generation;
- canonical freeze validation passed after the JSON was committed;
- all seven applicable PR CI workflows were green on exact head `6f5835cb836cf83cec77df52f9c4b56540abf95b`;
- tracked production `.pkl` hashes were unchanged;
- `NO_BET`, no production promotion, no Supabase write and no paid provider call occurred.

Outcome gate:
- evaluator = `evaluate_la_liga_market_anchor_prospective_20260915.py`;
- evaluation is fail-closed before `2026-09-15T21:30:00Z`;
- all three final H/D/A outcomes are required at once; no one-match early peek is authorized;
- evaluator validates the freeze SHA and cannot refit or retune the model.

An exact one-time post-match check is scheduled for `2026-09-16 00:00 Europe/Warsaw` to verify all three finals and report market vs frozen shadow Brier, LogLoss, accuracy and per-match deltas without retuning.

## Current execution pointer — this micro-cohort

1. Do not modify or regenerate the canonical freeze.
2. Do not inspect/evaluate target outcomes before the gate and do not evaluate a partial cohort.
3. After all three fixtures are final and the gate is open, run the locked evaluator on exactly these three event IDs.
4. Record pooled Brier/LogLoss first, accuracy second, plus per-match deltas and the predeclared dual-metric verdict.
5. Regardless of result, do not tune on these three outcomes. Treat them as prospective directional evidence only.
6. Keep active Market Anchor fail-closed to market and keep `NO_BET` / no production promotion unless a separately defined larger evidence gate is satisfied.


---

# Continuity update — 2026-09-15 16:01:43Z → 2026-09-18 current

Последнее сохранение `PROJECT_CONTINUITY.md` до этого блока было сделано commit `90262677902102ac33421109179d8bcf7649d86d` at `2026-09-15T16:01:43Z` (`Record La Liga prospective freeze continuity`). Всё ниже — работа после этой точки.

Current canonical merged `main` before this continuity-only update: `17bf1ac9a2e1b27df54b519b2972860037eaf733`.

Binding interpretation for this whole interval:
- research/training never promoted production `.pkl`;
- `NO_BET` remained binding;
- no result below authorizes staking, automatic betting or model promotion;
- historical/post-outcome diagnostics are not to be relabeled prospective;
- opened OOT samples must not be retuned;
- market-state movement research is distinct from predicting match outcomes or the final number of corners.

## La Liga prospective three-match micro-cohort — evaluation completed

PR #339 was a documentation-only continuity checkpoint after the already-frozen three-match La Liga prospective cohort.

PR #340 merged as `f528d01ba08d10ebbdbe17946a5abd4f7f013230` and recorded the locked evaluation of `LA_LIGA_MARKET_ANCHOR_PROSPECTIVE_20260915_V1`.

Final three-match result:
- market Brier = `0.4644053497`;
- shadow `lambda=1` Brier = `0.5032927022`;
- market LogLoss = `0.8223382306`;
- shadow LogLoss = `0.8763090448`;
- both accuracies = `2/3`;
- delta Brier vs market = `+0.0388873525` (worse);
- delta LogLoss vs market = `+0.0539708142` (worse);
- frozen dual probabilistic metric win = **false**.

Decision: `FAIL_DUAL_PROBABILISTIC_METRIC_WIN`. The micro-cohort is prospective evidence that the fixed full football residual did not improve the market on these three matches. No lambda/feature retuning from this sample is authorized.

## 1X2 market-state / repricing research chain — PR #341–#361

This block moved the project away from trying to force a football residual over the market and toward asking whether **pre-close market state predicts the market's own later repricing**.

Chronology:

- **PR #341 — POWER Market Anchor V3**, merge `350a59910f05fcb6c4dd1c1b0bf4e4be4389175a`: tested the existing football residual on top of a fixed POWER de-vigged La Liga market prior. The global residual did not establish a production-worthy incremental win.
- **PR #342 — Conditional Residual V4**, merge `0756347408ee3d53e8597fdf500832a7a4ba577b`: froze a small selective gate using pre-match residual disagreement + market entropy. The untouched OOT gate did not justify activation.
- **PR #343 — Multi-Market Anchor V5**, merge `01310a0019fde188b37bf537885966c9ba08a60a`: tested whether O/U 2.5 and Asian Handicap prices add 1X2 information beyond the fixed POWER 1X2 prior. This remained research-only and did not authorize a production baseline change.
- **PR #344 — Standard-to-Close Signal V6**, merge `4ba6603917e298fcfb042550d582f56795f90d20`: changed the target from match outcome to explicit Bet365 STANDARD→closing 1X2 movement. STANDARD fields were deliberately not mislabeled as opening prices.
- **PR #345 — Market Movement Regimes V7**, merge `49310172395425a152b4fa4a2fa9390cf41bc2c5`: after the directional regression was not a sufficient path, reframed the task as classification of **material repricing** using a train-only 75th-percentile movement threshold and constant-prevalence baseline. This produced the accepted repricing-risk research signal that became the basis of the next robustness work.
- **PR #346 — Regime Direction V8**, merge `8637964c4c80c3a83b1cd66fb7c5fcfb883c2124`: tested sign/direction inside the already-frozen material-movement regime without retuning V7. Direction was kept separate from magnitude/risk.
- **PR #347 — Incremental Robustness V9**, merge `4c6b0a2bc5edbf5b0774f14fd4e68253c8dc0fcc`: decomposed the accepted V7 signal into MARKET_STATE vs FORM contribution. The robust research path increasingly pointed to market-state geometry, not to a new football residual.
- **PR #348 — Walk-Forward Robustness V10**, merge `6c216d86b9b674cb5a84ffe8171635ec55d3490b`: expanding temporal folds re-tested the repricing-risk construction with all fitting performed only on earlier seasons.
- **PR #349 — Market-State Decomposition V11**, merge `608cf3785dc66b092d30a2a30519ebd5602a91f3`: decomposed the market-state signal into fixed interpretable geometry: full probabilities, favorite strength, draw level, entropy, top-two gap and fixed combinations.
- **PR #350 — Market-State Walk-Forward V12**, merge `4c76fa4d6749723d3d18f8a0229b7ae1d0065cf3`: walked the interpretable components forward across seasons, preserving the same V7 target construction.
- **PR #351 — Serie A Repricing V13**, merge `a183000ed20933221cd0ff12e5b354708fcfec9a`: transferred the frozen La Liga repricing-risk construction to Serie A without Serie A tuning.
- **PR #352 — EPL Repricing V14**, merge `548a6387b6c7624f6fc923ae17561f73f1f85bce`: independent EPL replication of the market-state repricing-risk question.
- **PR #353 — EPL Cross-Book Direction V15**, merge `4950a63f2386a758d6f3425cb73b32c21870de26`: tested whether STANDARD Pinnacle-vs-Bet365 fair-probability disagreement predicts subsequent B365 repricing direction.
- **PR #354 — EPL Direction Decomposition V16**, merge `80abfb8588dd10ed9a1019d184f03af7dabd8cd9`: decomposed the cross-book direction evidence without retuning.
- **PR #355 — Serie A Direction V17**, merge `dd7655f34bd50bd7c7789a5e9bdd8c72c6e6d324`: transferred the frozen EPL disagreement-only direction signal to Serie A.
- **PR #356 — La Liga Direction V18**, merge `f3824e94cf19e7ddfe6acc20ae4802ef7bc40bb2`: second independent league transfer of the same frozen cross-book direction construction.
- **PR #357 — Structural Break V19**, merge `0d09aae8148bcaed441ab8f8fa9b26c314bdcd84`: identified a synchronized 2025-26 failure/break in the frozen cross-book direction behavior across EPL, Serie A and La Liga.
- **PR #358 — Regime Calibration V20**, merge `49576124c40263f779ad19eee864a80d09c1ba05`: tested a predeclared two-season recent-history calibration against expanding history; it did not remove the need to treat the 2025-26 break as a real unresolved problem.
- **PR #359 — Source Drift V21**, merge `b51fce06a63ead23dfb84bd24971678c5dd2b39a`: separated bookmaker-specific STANDARD→closing movement from cross-book disagreement and diagnosed the 2025-26 Pinnacle coverage break.
- **PR #360 — Common-Support V22**, merge `b0d0b17e1e3afb4045b032d3002b5a6ad835a5a2`: tested whether Pinnacle availability alone selected a different Bet365 movement subset. Common-support selection did **not** explain away the directional break.
- **PR #361 — Historical Cross-Book Closure V23**, merge `2799a1362d1fd8f1571852e9bc96a1c55e01bfd3`: formally closed the historical cross-book direction branch as **NO_BET**. The 2025-26 coverage break is a confounder, but not a sufficient explanation of the failed direction transfer. Any future direction work must use explicit timestamped prospective snapshots rather than further same-sample historical tuning.

Synthesis of PR #341–#361:
- strongest durable concept from this branch is **repricing-risk / movement magnitude**, not a stable universal direction classifier;
- market-state geometry proved more interesting than forcing additional football residuals;
- cross-book direction looked promising in earlier folds/transfers but failed a synchronized later-period robustness check;
- therefore the historical direction path is closed and must not be reopened by threshold/window mining on the same data.

## Direct O/U 2.5 and Asian Handicap research — PR #362–#366

- **PR #362** (`Research market-anchored O/U 2.5 V1`) remains **open / non-merged**. It is not canonical `main` evidence and should not be treated as an active accepted experiment.
- **PR #363**, merge `40aba10087558f213d595474764e948ef4031079`, became the canonical direct-market experiment across EPL, La Liga and Serie A: O/U 2.5 plus Asian Handicap, temporal train 2016-17..2023-24, validation 2024-25, untouched OOT 2025-26.
- **PR #364**, merge `b342d34ae5f029fcf02716dda111abd5d1e1cac4`, recorded the frozen result:
  - O/U 2.5 = **0/3 league PASS → SKIP**;
  - Asian Handicap = **0/3 league PASS → SKIP**;
  - EPL and Serie A AH were validation-admissible but reversed on untouched 2025-26;
  - bookmaker corners = `DATA_UNAVAILABLE → COLLECT`.
- **PR #365**, merge `a8bdf7859a5b7d08c3710d531b79897057fbf814`, froze and executed a separate O/U 2.5 **opening-to-closing movement** test: fixed Ridge(`alpha=1.0`), football-state candidate vs no-movement baseline, MAE+RMSE gate.
- **PR #366**, merge `96ee5a27ff0481148d4270237cff902eced70696`, recorded:
  - EPL FAIL;
  - La Liga FAIL;
  - Serie A FAIL;
  - pass count `0/3`;
  - pooled decision **SKIP**.

Binding conclusion: direct O/U/AH outcome modeling did not beat the paired market under frozen V1, and the tested O/U closing-movement football-state model also failed. Do not retune these exact V1s on their opened OOT.

## Bookmaker corners data-source qualification — PR #367–#378

This block first solved the missing-data problem before any corner model-vs-market claim.

- **PR #367**, merge `8e5c09f9d2d0fe9f440ae6969223d172396cc725`: audited historical corner-price sources and added a fail-closed TotalCorner parser/client. OddsPapi history was too shallow; 7M lacked a reproducible bulk contract; TotalCorner had suitable historical depth but required VIP/token.
- **PR #368**, merge `60218392a7aea6bee73520215ceb72c1d066d416`: froze a 30-match TotalCorner acquisition-only pilot (10 each EPL/Serie A/La Liga; source qualification requires >=8/10 in every league).
- **PR #369**, merge `77ab0c10529272fb7090f67c0dc25b164577dfbb`: added the manual-only TotalCorner live runner.
- **PR #370** was closed **unmerged as a duplicate** of #369.
- **PR #371**, merge `c8f0b38a314739f9d028355a68babeb785f90f2c`: temporarily closed the TotalCorner path as `CLOSED / COLLECT / EXTERNAL_CREDENTIAL_REQUIRED`.
- **PR #372**, merge `5a7843f1517716e09cd3b173c8e178f0a69b9908`: qualified 5DollarFootballAPI using a frozen acquisition-only Bet365 corner pilot on five latest finished fixtures per league.
- **PR #373**, merge `6ef875d8fd2bdf3f125f61012180bbe24e45fc7f`: immutable source result = **15/15 covered**, EPL 5/5, La Liga 5/5, Serie A 5/5; decision `SOURCE_QUALIFIED_FOR_BACKFILL`.
- **PR #374**, merge `ad110a6cc7800284b8881ce48544925e8c0a27c3`: froze the first `CORNERS10 vs Bet365 opening corner market` experiment before backfill. Half-lines only, fixed rolling corner-state features, C=0.1, validation gate + untouched 2025-26 OOT, dual Brier/LogLoss acceptance.
- **PR #375**, merge `b2965c78cc2585d2f3c542f54ab5ffe6aa2c21d0`: implemented fail-closed 2016-17..2025-26 historical 5Dollar backfill with preflight, raw/normalized separation, hard request budget and no model metrics during acquisition.
- **PR #376** was closed **unmerged as a duplicate** of #375.
- **PR #377**, merge `2cc81873ae5141ae4214551a360e9872f7049dc1`: added an explicit one-request PR-gated historical access preflight; full backfill remained manual-only.
- **PR #378**, merge `f547aa7fc68288ee23dadc3704247647bcaf6da5`: one-request live preflight result = **`HISTORY_ACCESS_BLOCKED_BY_PLAN`** for the earliest frozen EPL 2016-17 bulk-odds window. No full historical backfill and no CORNERS10-vs-market evaluation were run.

Binding conclusion: 5Dollar is qualified for currently exposed Bet365 corner opening/closing data, but the frozen deep historical backfill is blocked by the plan. Do not claim the unavailable 2016-17..2025-26 bookmaker-history experiment was executed.

## Free corners football-vs-market screen — PR #379–#382

Because the historical plan blocked the original backfill, a separate free-window screen was created instead of weakening the historical contract.

### PR #379 — `FREE_CORNERS_SIGNAL_SCREEN_V1`

Merge: `9a5c29a0b65ff67a191440ddd64907ca75da69d5`.

Frozen screen:
- five free top leagues;
- 11 most recent finished fixtures per league, max 55;
- Bet365 opening corner line/prices;
- historical football corner model trained only on 2016-17..2025-26 public corner outcomes;
- 2026-27 held out;
- fixed 25% football / 75% market blend;
- Brier, LogLoss and residual-alignment screen;
- no ROI/betting/production use.

Important implementation work inside this PR:
- bounded provider rate-limit handling was added and regression-tested;
- the final aggregate evaluation was converted to a **zero-provider-request offline replay** using immutable acquired Bet365 artifacts;
- pinned Football-Data mirrors were used where official transport failed;
- source-native missing corner rows were preserved rather than silently fabricated/dropped;
- Serie A mirror season mapping was corrected before the final frozen replay.

### PR #381 — immutable result

Merge: `5ed605de71d8ebac8d69ff593402c531f421205f`.

Result = **`NO_CLEAR_SIGNAL_SCREEN`**:
- 55 selected fixtures;
- 55 market rows;
- 44 eligible evaluation rows;
- all five leagues passed sample coverage gate;
- pooled fixed blend improved Brier/LogLoss only marginally;
- pooled residual alignment was near zero and its 90% bootstrap interval crossed zero;
- only `2/5` leagues had positive residual alignment;
- Serie A was retained only as a **post-result diagnostic hypothesis**, not a confirmed edge.

### PR #382 — Serie A prospective replication

Merge: `2fc3396f12879f745c5d23b9b9cb45a11dd8102c`.

A separate prospective Serie A-only replication was preregistered:
- fixtures from `2026-09-19T00:00:00Z` onward;
- opening capture >=6h before kickoff;
- same frozen model/blend;
- first 30 eligible finished fixtures;
- no performance metrics opened before the 30-row gate;
- free plan only.

This track was later judged to answer the **wrong question** for the intended market-movement research and was superseded before confirmatory evaluation.

## Corner market-state repricing signal — PR #383–#386

This is the most important new research result of the interval.

### PR #383 — correctly scoped market-only corner repricing experiment

Merge: `653b0c10433f522d0b8a2becdc3608a8f2bba57b`.

The project returned to the same question that had been productive in 1X2:
> can opening bookmaker state predict **how much the bookmaker's own corner market will be repriced by closing?**

Frozen design:
- market-only; no match outcomes, CORNERS10 or football-state inputs;
- existing free Bet365 opening+closing corner artifacts;
- proportional de-vig + Poisson-reconstructed comparable opening/closing market centre;
- material move = top quartile;
- fixed `q=.75`, LogisticRegression `C=.1`;
- fixed interpretable opening-state variants;
- leave-one-league-out across EPL, La Liga, Serie A, Bundesliga and Ligue 1;
- Brier + LogLoss vs constant prevalence baseline.

At the same time the Serie A football-model prospective collector from PR #382 was **paused/superseded** so it would not consume free quota answering a different question.

### PR #384 — discovery result

Merge: `ab81ccec5daf9e965a5c23ad55f34a27fed567b2`.

Frozen verdict = **`STRONG_REPRICING_SIGNAL`**.

Primary feature = `FAIR_CENTRE` (Poisson-reconstructed opening market centre):
- `4/5` held-out leagues beat the constant baseline on **both** Brier and LogLoss;
- pooled Brier = `0.18173669` vs baseline `0.19886364`;
- pooled LogLoss = `0.53968369` vs baseline `0.58730361`;
- pooled ROC AUC = `0.7458`;
- coefficient was negative in all five folds: lower opening `FAIR_CENTRE` associated with higher probability of a material repricing.

Interpretation limit: this established **repricing magnitude/risk**, not profitability and not a proven movement sign.

Artifact: `10550262038`; digest `sha256:92177e4ddb39331b33e9c97fc75541b0371f744f17a9dd6a2355188839960b92`.

### PR #385–#386 — fresh unseen replication

PR #385 merge: `ed16e6551e2b567e147c76905c02642cbc7b0803`.
PR #386 merge/current main: `17bf1ac9a2e1b27df54b519b2972860037eaf733`.

Frozen before opening the new closing data:
- old 55 rows immutable discovery/training only;
- `FAIR_CENTRE` only as primary feature;
- same market-centre reconstruction;
- 10 previously unused fixtures per league = 50 new rows;
- frozen V1 q75 threshold and LogisticRegression(`C=0.1`);
- magnitude replication by pooled Brier + LogLoss;
- separate high-risk direction diagnostic.

Fresh 50-row result:
- baseline Brier = `0.1826115702`;
- frozen FAIR_CENTRE Brier = `0.1631186776`;
- baseline LogLoss = `0.5516446554`;
- frozen FAIR_CENTRE LogLoss = `0.5174742619`;
- magnitude/risk signal therefore **replicated on previously unused fixtures**.

Frozen high-risk direction gate also technically passed:
- non-zero high-risk moves = `9`;
- upward = `9`;
- downward = `0`;
- positive share = `1.00`;
- one-sided binomial p vs 0.50 = `0.001953125`.

Critical caveat:
- non-high-risk non-zero rows = `12`;
- upward among them = `11/12`;
- overall non-zero fresh moves = `20` up vs `1` down.

Therefore the supported claim is:
> opening corner-market state, especially `FAIR_CENTRE`, contains replicated information about **whether the market will be materially repriced**.

The unsupported/unfinished claim is:
> `FAIR_CENTRE` uniquely predicts **the sign** of repricing.

The fresh window had a broad upward market regime, so direction must be tested against a contemporaneous regime baseline, not against 50/50.

Fresh replication artifact: `10551727936`; digest `sha256:ca3c0f96338cf213e1dc76dbf47e88d01f7ad551f18e83ef2c185d4bc9eb6ba3`.
Provider requests: `55/60`.
Paid subscription used: false.
Match outcomes used: false.
Production `.pkl` changed: false.

## Non-canonical/open corner branch note — PR #380

PR #380 (`Run free EPL corners market screen V2`) remains **open / non-merged**.

It attempted a football-model-vs-opening-market EPL-only screen after V1 acquisition difficulties. That question is now **superseded** by the market-only repricing line in PR #383–#386. Do not treat PR #380 as current canonical direction and do not resume it merely because it remains open.

## Active current work — PR #387 `CORNER_REGIME_ADJUSTED_DIRECTION_V1`

Status at this continuity update:
- PR #387 = **open / unmerged**;
- head = `92df9d88b1998dd01f7496f7979acbca880a830d`;
- canonical main remains `17bf1ac9a2e1b27df54b519b2972860037eaf733`;
- dedicated final live workflow run `35361459609` is **in progress**;
- offline contract on that head is green, including compile, focused regression tests, frozen-constant assertions and production `.pkl` hash guard.

Purpose: determine whether `FAIR_CENTRE` contains **individual direction discrimination after removing a contemporaneous league-day market regime**.

Frozen primary construction:
- only candidate score: `direction_score = -opening_lambda`;
- regime block = `(league, UTC kickoff date)`;
- compare only pairs of matches inside the same regime block;
- concordant pair = lower opening FAIR_CENTRE subsequently has the larger `centre_delta`;
- primary effect = pooled within-block pairwise concordance;
- null = **20,000** deterministic permutations, seed `20260918`, shuffling `centre_delta` only inside the same regime block;
- this preserves the exact upward/downward regime of each league-day while destroying individual match assignment.

Frozen sample gate:
- >=30 eligible fresh rows;
- >=4 leagues with at least one comparable pair;
- >=8 contributing regime blocks;
- >=40 comparable pairs.

Frozen confirmation gate:
- concordance >= `0.60`;
- one-sided regime-preserving permutation p < `0.10`.

Third-sample acquisition amendments were made **before any third-sample odds/closing data were opened**:
1. run `35360780913` stopped in fixture metadata discovery because first-page Bundesliga exclusions left only 6 unseen IDs; no fixture odds request had occurred;
2. pagination was added, but run `35361107211` proved from metadata that the Free Bundesliga inventory itself had only 27 finished fixtures and `has_more=false`; 21 were already consumed by the two earlier frozen samples, leaving exactly 6 unseen. Again, no third-sample odds request had occurred;
3. final metadata-only frozen rule: up to 10 unseen fixtures per league, minimum 6, no cross-league backfill. Expected selection = **46**: EPL 10, La Liga 10, Serie A 10, Bundesliga 6, Ligue 1 10.

The statistical feature, sign hypothesis, regime blocks, concordance threshold and permutation p-value gate were **not changed** by these metadata-only amendments.

The live marker was removed from the PR body after the final run was triggered so no accidental repeated provider run should start from later PR events.

Until the immutable final `report.json` from the currently running frozen execution exists, **do not claim regime-adjusted direction replication**.

## Current research checkpoint — 2026-09-18

Canonical merged facts:
- strongest new replicated movement signal: **corner-market repricing magnitude/risk via opening FAIR_CENTRE**;
- discovery: 55 rows, cross-league leave-one-league-out, strong pooled discrimination;
- replication: independent 50-row fresh sample improved both Brier and LogLoss;
- movement sign remains unresolved because the replication window was overwhelmingly upward market-wide;
- PR #387 is the correct next test because it removes the common league-day regime before testing individual direction;
- historical 1X2 cross-book direction branch is closed `NO_BET` after the 2025-26 structural break;
- direct O/U 2.5 and AH V1 both ended `SKIP`;
- O/U 2.5 football-state closing-movement V1 ended `SKIP`;
- free corners football-vs-market screen ended `NO_CLEAR_SIGNAL_SCREEN`;
- deep historical 5Dollar corner backfill is blocked by plan and must not be represented as completed;
- no production `.pkl` promotion occurred in any of these blocks.

## Current execution pointer

1. Let the already-running PR #387 frozen live execution finish; do not create a parallel/replacement sample after odds access has begun.
2. Read the immutable `report.json` only after the run completes and record the frozen verdict without changing feature/sign/sample/statistical gates.
3. If PR #387 passes: treat it as evidence of individual direction discrimination **conditional on league-day regime**, still research-only / NO_BET.
4. If PR #387 fails: keep the replicated magnitude/risk signal, but close the current FAIR_CENTRE direction hypothesis; do not rescue it with post-hoc thresholds, alternative signs or subgroup mining on the opened sample.
5. Do not resume PR #380 as the canonical corner path; it answers a different, already-superseded football-model question.
6. Do not treat open PR #362 as canonical direct-market evidence; merged PR #363–#366 are the source of truth for O/U/AH.
7. Continue separating:
   - probability of the match/corner outcome;
   - probability of material market repricing;
   - direction of repricing;
   - betting/value profitability.
   Evidence for one does not automatically prove the others.
8. Production artifacts, automatic promotion, betting and staking remain out of scope unless a separate explicitly frozen evidence gate is satisfied.


---

# Continuity update — 2026-09-19 — CORNER_REGIME_ADJUSTED_DIRECTION_V1 CLOSED

This section supersedes the prior execution pointer that left PR #387 in progress.

## PR #387 — regime-adjusted corner direction V1

Merged to `main` as:

`47b9c42a909992e3f0a3cd114e57f452cb240870`

Final implementation/result head before merge:

`346fbfeae579c477a1f8eea65cd1c420c7d4847f`

Purpose:

test whether the previously observed FAIR_CENTRE direction pattern survives after removing a contemporaneous league-day market regime.

The frozen primary construction remained:

- candidate score = `-opening_lambda` / `-FAIR_CENTRE`;
- regime block = same league + same UTC kickoff date;
- primary statistic = within-regime unordered pairwise concordance;
- 20,000 regime-preserving permutations;
- RNG seed = `20260918`;
- minimum eligible rows = 30;
- minimum contributing leagues = 4;
- minimum contributing regime blocks = 8;
- minimum comparable pairs = 40;
- confirmation requires concordance >= 0.60 and one-sided permutation p < 0.10.

No threshold, feature, sign, regime definition or statistical gate was changed after opening third-sample data.

## Third-sample acquisition and bounded-timeout recovery

The final frozen selected cohort contains 46 previously unused fixtures:

- EPL: 10;
- La Liga: 10;
- Serie A: 10;
- Bundesliga: 6;
- Ligue 1: 10.

The Bundesliga reduction was frozen from metadata before third-sample odds were opened. The Free provider inventory contained only six unseen Bundesliga fixtures after excluding the previous 55-row discovery and 50-row replication samples. No cross-league backfill was allowed.

Initial final live run:

`35361459609`

The run froze all 46 selected fixture IDs first and then began odds acquisition. It preserved 17 successful raw odds responses before the 75-minute GitHub Actions timeout was reached while using the bounded provider rate-limit path.

Timeout artifact:

- artifact ID: `10557603810`;
- digest: `sha256:5530abd643fa4bac1c6ca25609bd9979dd3e0e90ce1c05601d234aca807e406b`.

Important boundary:

- no aggregate `report.json` existed at timeout;
- therefore no statistical result had been opened;
- production `.pkl` hash guard passed.

Because closing data were partially opened at that point, the 46-fixture selection became immutable.

A same-sample resume path was then added and regression-tested. It:

- reads the exact selected fixture IDs from the timeout artifact;
- reuses the 17 already-preserved raw odds responses;
- performs no fixture discovery;
- requests only the 29 missing fixture odds;
- forbids replacement/backfill of selected fixtures;
- runs the original frozen analysis unchanged.

Final authorized resume run:

`35369631434`

Result artifact:

- artifact ID: `10557706131`;
- digest: `sha256:5ff43199cdf1bb73e6b87649c3e68aa57bac628c68888a06a809c5df473b8d1f`.

Resume facts:

- `acquisition_mode = IMMUTABLE_SAME_SAMPLE_RESUME`;
- reused raw odds responses = 17;
- provider requests during resume = 29;
- selected fixture count = 46;
- eligible normalized rows = 46;
- production `.pkl` hash guard = PASS;
- paid subscription used = false;
- match outcomes used = false;
- CORNERS10 / football-state used = false.

No further provider run is authorized for V1.

## Frozen statistical result

Sample-gate components:

- eligible rows = 46 — PASS vs minimum 30;
- contributing leagues = 5 — PASS vs minimum 4;
- contributing regime blocks = 9 — PASS vs minimum 8;
- comparable within-regime pairs = **30 — FAIL vs frozen minimum 40**.

Therefore the binding verdict is:

**`SAMPLE_TOO_SMALL`**

Because the sample gate failed, the frozen contract correctly did not run/interpret the 20,000-permutation confirmation statistic:

- `permutation_pvalue = null`;
- `direction_discrimination_confirmed = false`.

The 40-pair threshold must not be weakened after seeing this sample.

## Diagnostic-only effect

Although it cannot be promoted to confirmation:

- comparable pairs = 30;
- concordant pairs = 21;
- observed concordance = **0.70**.

By league:

- EPL = 4/11 = 0.3636;
- La Liga = 4/6 = 0.6667;
- Serie A = 5/5 = 1.00;
- Bundesliga = 4/4 = 1.00;
- Ligue 1 = 4/4 = 1.00.

These numbers are diagnostics only because the preregistered comparable-pair sample gate failed.

Movement diagnostics across 46 rows:

- positive centre moves = 13;
- negative = 5;
- zero = 28;
- positive share among non-zero = 0.7222;
- top-minus-bottom regime-adjusted mean = +0.1252142136.

This third window was much less one-sided than the prior 50-row replication, but there still were not enough comparable same-league/day pairs to authorize the frozen direction claim.

## Binding interpretation

The correct conclusion is **inconclusive direction evidence because of insufficient comparable-pair structure**.

Do not restate V1 as:

- direction replicated;
- direction statistically failed;
- p-value approximately significant;
- 0.70 concordance confirmed the hypothesis.

None of those statements is authorized.

The separately replicated result that remains intact is:

> opening FAIR_CENTRE contains out-of-sample information about the probability that the Bet365 corner market will later undergo a material repricing.

That is a **repricing magnitude/risk** result, not a direction result.

## Current execution pointer

1. PR #387 is closed/merged. Do not rerun its provider workflow.
2. Do not retune the 46-row third sample and do not weaken the 40-pair gate.
3. If direction research continues, create a **new separately frozen future-data continuation** designed to accumulate enough untouched same-league/day blocks for the preregistered comparable-pair requirement.
4. Preserve the separation between:
   - repricing magnitude/risk;
   - repricing direction;
   - final match/corner outcome;
   - tradable value/CLV;
   - betting profitability.
5. The strongest current corner result remains replicated repricing magnitude/risk via FAIR_CENTRE.
6. Direction remains unresolved.
7. `NO_BET`, no production promotion and no production `.pkl` changes remain binding.


---

# Continuity update — 2026-09-19 — CORNER_REGIME_ADJUSTED_DIRECTION_V2 FROZEN

This section supersedes the prior execution pointer that said direction research should continue only through a separately frozen future-data continuation.

## PR #390 — future block-locked corner direction V2

Merged to `main` as:

`1431cec32bec5c039a4ac396d2ab383fdd77efcf`

Final PR head:

`c922ea39aeaa378ca9af9c1d3bedb289c7c6295a`

Purpose:

continue the unresolved FAIR_CENTRE direction question on **new future data only**, while fixing the sample-structure problem that caused V1 to end `SAMPLE_TOO_SMALL`.

V2 does **not** change the statistical hypothesis or confirmation gate.

The only design change is acquisition planning: fixture metadata must first lock sufficiently dense **whole league-day blocks** before any V2 corner opening/closing odds may be read.

## Evidence boundary

All previously opened corner samples are excluded from V2 tuning:

- original 55-row repricing discovery;
- fresh 50-row repricing replication;
- 46-row V1 regime-adjusted direction sample.

Prior samples may be used only for fixture-ID exclusion and to preserve the already-defined market representation/statistical contract.

The V1 diagnostic observed concordance of 0.70 is **not** used as a V2 target, threshold or effect-size gate.

## Future-only cutoff

V2 candidate fixtures require:

`kickoff_utc >= 2026-09-19T00:00:00Z`

Leagues remain:

- EPL;
- La Liga;
- Serie A;
- Bundesliga;
- Ligue 1.

## Metadata-only cohort planner

Before any V2 odds request:

1. read fixture metadata only;
2. retain finished fixtures after the future cutoff;
3. exclude every prior corner-sample fixture ID;
4. group fixtures by `(league, UTC kickoff date)`;
5. discard metadata blocks with fewer than two fixtures because they cannot contribute a primary within-block pair;
6. include **whole blocks**, never cherry-pick individual matches;
7. order candidate blocks by UTC date ascending and frozen league order.

For metadata block size `n`:

`potential_pairs = n * (n - 1) / 2`

No FAIR_CENTRE, opening odds, closing odds, centre_delta, outcome or football-state information enters the planner.

## Frozen V2 cohort-lock gate

A cohort may be locked only when the earliest deterministic block prefix contains all of:

- all 5 leagues;
- at least 2 metadata blocks per league;
- at least 12 metadata blocks pooled;
- at least 80 metadata potential pairs pooled.

The 80-pair target is an operational 2x buffer over the unchanged 40-comparable-pair statistical minimum. It is not derived from V1's observed concordance.

If the metadata inventory does not satisfy the lock:

`WAIT_FOR_COHORT`

No odds acquisition or statistical evaluation is authorized.

Once the lock is reached:

- selected block membership and fixture IDs become immutable;
- later metadata must not change the earliest locked prefix;
- fixtures may not be removed/replaced because later market data are inconvenient or missing.

Regression tests explicitly verify this prefix stability.

## Statistical contract remains unchanged from V1

Primary candidate:

`direction_score = -opening_lambda = -FAIR_CENTRE`

Regime block:

`league + UTC kickoff date`

Primary statistic:

within-regime unordered pairwise concordance.

Frozen permutation test:

- 20,000 permutations;
- seed `20260918`;
- shuffle `centre_delta` only inside each regime block.

Frozen statistical sample gate:

- >=30 eligible rows;
- >=4 leagues with comparable pairs;
- >=8 contributing regime blocks;
- >=40 comparable pairs.

Frozen confirmation gate:

- sample gate passes;
- concordance >=0.60;
- one-sided permutation p <0.10.

Verdicts remain:

- `INDIVIDUAL_DIRECTION_DISCRIMINATION_REPLICATED`;
- `INDIVIDUAL_DIRECTION_DISCRIMINATION_NOT_CONFIRMED`;
- `SAMPLE_TOO_SMALL`.

The 80 metadata potential-pair lock does not replace or weaken the 40 **actual comparable-pair** requirement.

## Current implementation state

PR #390 deliberately implemented **offline planning only**:

- `corner_regime_adjusted_direction_v2.py` contains deterministic metadata normalization/block selection/cohort-lock logic;
- regression tests protect cutoff, exclusions, whole-block selection, fail-closed WAIT state and stable earliest-prefix lock;
- dedicated V2 CI passed;
- general Research/Product/league validations passed;
- production `.pkl` hash guard passed.

Critically:

- V2 currently has **no live odds transport**;
- no provider odds endpoint exists in the V2 module;
- no live marker exists;
- no V2 opening/closing odds have been read;
- no Supabase write occurred;
- no paid provider action occurred.

The preregistration document was committed **before** planner implementation.

## Binding current execution pointer

1. Treat PR #390 / merge `1431cec32bec5c039a4ac396d2ab383fdd77efcf` as the frozen V2 source of truth.
2. Do not add live odds acquisition until the metadata-only planner can be run against future fixture inventory and either:
   - returns `WAIT_FOR_COHORT`, in which case no odds call is allowed; or
   - returns an immutable `COHORT_LOCKED` artifact satisfying the frozen metadata gate.
3. The first live-capable change must consume the exact locked fixture IDs only and must preserve resume semantics for partial acquisition.
4. Do not use V1's 0.70 diagnostic to alter V2 thresholds.
5. Do not weaken the V2 metadata lock or the unchanged 40-comparable-pair statistical gate after future market data are opened.
6. The strongest confirmed corner finding remains **repricing magnitude/risk via FAIR_CENTRE**.
7. Repricing direction remains unresolved pending V2 future evidence.
8. `NO_BET`, no production promotion and no production `.pkl` changes remain binding.


---

# Continuity update — 2026-09-19 — V2 metadata check = WAIT_FOR_COHORT

This section extends the V2 execution pointer after PR #390.

## Metadata-only live planner path

PR #392 merged as:

`fa7745519fb7f919b0b064a46670e0b98b1660a6`

It added the bounded metadata-only live inventory runner for `CORNER_REGIME_ADJUSTED_DIRECTION_V2`.

Allowed live surface:

- fixture-list metadata only;
- no odds endpoint;
- no market prices;
- no match-outcome evaluation;
- no Supabase writes;
- no paid provider action;
- maximum 2 fixture-list pages per league / 10 provider requests pooled;
- exact exclusion of the 151 fixture IDs from the three prior corner samples.

PR #393 merged as:

`2043de27f4877355f3f5c1c3a510ce8bb6ccfa7d`

It hardened the same-repo explicit metadata trigger because the connected GitHub integration did not expose `workflow_dispatch` directly.

An accidental pre-full-CI metadata-only trigger occurred when the literal execution marker appeared in explanatory PR prose. That run is non-authoritative and must not be used as a cohort lock. Trigger matching was hardened before the authoritative execution. No odds endpoint was involved.

## Authoritative V2 metadata check

Authoritative workflow run:

`35424349695`

Tested PR head:

`0746a721554b03ae28eca575b489fe4399e55385`

Immutable artifact:

- artifact ID: `10578826642`;
- digest: `sha256:d486527409bed8e4a0cc11ed562ac7574e9362f3c9c83808038b90918d9388e4`.

Safety/results:

- provider requests = **5 / 10**;
- live fixture metadata rows returned = **197**;
- prior excluded fixture IDs = **151**;
- odds endpoint used = false;
- market prices opened = false;
- paid subscription used = false;
- production `.pkl` hash guard = PASS.

Frozen future cutoff:

`2026-09-19T00:00:00Z`

Planner result:

- normalized finished future fixtures = **0**;
- candidate future regime blocks = **0**;
- metadata potential pairs = **0**;
- selected/locked fixtures = **0**.

Binding status:

**`WAIT_FOR_COHORT`**

The empty future cohort is expected at this time. The metadata check ran shortly after the frozen cutoff, while the provider's currently finished inventory still ended before the cutoff (latest captured EPL finished fixture: `2026-09-18T19:00:00Z`).

## Current V2 execution pointer

1. V2 direction research is now in **WAIT_FOR_COHORT** state.
2. Do not open any V2 corner odds while the planner returns WAIT_FOR_COHORT.
3. Do not lower the metadata lock:
   - all 5 leagues;
   - >=2 blocks per league;
   - >=12 blocks pooled;
   - >=80 metadata potential pairs.
4. Do not weaken the unchanged downstream V1 statistical gate:
   - >=30 eligible rows;
   - >=4 leagues with comparable pairs;
   - >=8 contributing regime blocks;
   - >=40 actual comparable pairs;
   - concordance >=0.60;
   - one-sided 20,000-permutation p <0.10.
5. A future check may rerun the **same metadata-only planner** after more fixtures have finished.
6. If a future metadata check first returns `COHORT_LOCKED`, save the exact fixture IDs/block membership immutably before creating any separate odds-acquisition PR.
7. Even `COHORT_LOCKED` does not itself authorize betting, staking, production promotion or post-hoc retuning.
8. The strongest confirmed corner result remains replicated **repricing magnitude/risk via FAIR_CENTRE**. Repricing direction remains unresolved.
9. `NO_BET`, no production promotion and no production `.pkl` changes remain binding.


---

# Continuity update — 2026-09-19 — V2 immutable cohort-lock readiness merged

This section extends the current V2 `WAIT_FOR_COHORT` state with the next offline-only safety layer.

## PR #395 — immutable cohort-lock validator

Merged to `main` as:

`65993504cce3e4cc6580702abd592c658a324f79`

Purpose:

prepare the exact fail-closed transition from a future authoritative metadata result:

`COHORT_LOCKED`

to an immutable lock manifest **before any V2 odds acquisition is allowed**.

The validator is implemented in:

`corner_regime_adjusted_direction_v2_lock.py`

Preregistration:

`research/CORNER_REGIME_ADJUSTED_DIRECTION_V2_COHORT_LOCK.md`

Dedicated regression coverage:

`tests/test_corner_regime_adjusted_direction_v2_lock.py`

Dedicated CI:

`.github/workflows/corner-regime-adjusted-direction-v2-lock.yml`

## Lock validator contract

Accepted source state:

`COHORT_LOCKED`

Rejected source state:

`WAIT_FOR_COHORT`

The validator rechecks all critical frozen conditions, including:

- V2 experiment identity;
- metadata-live experiment identity;
- research-only / metadata-only flags;
- no odds endpoint / no market prices;
- future cutoff `2026-09-19T00:00:00Z`;
- exact prior exclusion count = **151**;
- metadata lock gate:
  - >=2 blocks per league;
  - >=12 blocks pooled;
  - >=80 metadata potential pairs;
- unchanged downstream statistical gate inherited from V1:
  - >=30 eligible rows;
  - >=4 leagues with comparable pairs;
  - >=8 contributing regime blocks;
  - >=40 actual comparable pairs;
  - concordance >=0.60;
  - 20,000 regime-preserving permutations;
  - seed `20260918`;
  - one-sided p <0.10.

It then recomputes the deterministic earliest qualifying prefix from `candidate_blocks` and requires exact equality with the source plan's:

- selected blocks;
- selected fixture IDs;
- selected block count;
- selected fixture count;
- metadata potential pairs;
- blocks-by-league counts.

Any reorder, removal, replacement, backfill, duplicate fixture ID or inconsistent pair total fails closed.

## Immutable manifest identity

For a valid future `COHORT_LOCKED` artifact the validator will emit:

- exact source run/artifact provenance;
- exact ordered selected blocks;
- exact ordered selected fixture IDs;
- selected counts;
- frozen gates;
- prior exclusion count;
- deterministic `selection_sha256`.

The selection hash is computed from canonical JSON containing only frozen selection identity:

- cutoff;
- lock-gate constants;
- selected blocks;
- selected fixture IDs.

Regression tests confirm that the hash is stable to irrelevant source JSON key ordering.

## Authorization boundary remains unchanged

A valid lock manifest will explicitly contain:

- `odds_acquisition_authorized = false`;
- `betting_enabled = false`;
- `production_promotion_authorized = false`.

Therefore even after future `COHORT_LOCKED`:

1. the exact cohort must first be materialized as this immutable lock manifest;
2. only then may a **separate** odds-acquisition PR be designed;
3. that later PR must consume the exact lock manifest and must not perform fixture reselection.

PR #395 itself contains:

- no provider HTTP transport;
- no odds endpoint;
- no market prices;
- no Supabase writes;
- no paid action;
- no live marker;
- no production promotion.

Dedicated V2 cohort-lock CI and full repository validations passed, including production `.pkl` hash guard.

## Current execution pointer

Current authoritative V2 metadata state is still:

**`WAIT_FOR_COHORT`**

from run:

`35424349695`

artifact:

`10578826642`

digest:

`sha256:d486527409bed8e4a0cc11ed562ac7574e9362f3c9c83808038b90918d9388e4`

Current planner facts remain:

- normalized finished future fixtures = 0;
- candidate future regime blocks = 0;
- metadata potential pairs = 0;
- selected/locked fixtures = 0;
- no V2 odds opened.

Therefore:

- do **not** run the cohort-lock validator against the current WAIT artifact as if it were a lock;
- do **not** add or enable V2 odds acquisition yet;
- do **not** lower metadata or statistical gates;
- the next live action, when enough future matches have finished, is another run of the **same metadata-only planner**;
- only the first authoritative future `COHORT_LOCKED` artifact may proceed to immutable lock validation;
- after that lock is created, odds acquisition still requires a separate explicitly controlled PR.

The strongest confirmed corner finding remains the replicated **repricing magnitude/risk signal via FAIR_CENTRE**.

Repricing direction remains unresolved.

`NO_BET`, no automatic model promotion and no production `.pkl` changes remain binding.


---

# Continuity update — 2026-09-19 — V2 offline odds-acquisition plan merged

This section extends the V2 readiness chain after the immutable cohort-lock validator.

## PR #397 — deterministic offline odds-acquisition plan

Merged to `main` as:

`3bd1f7565c722d03b083e93a3ce35b7a3d69739a`

Purpose:

prepare, before any V2 odds are opened, the exact deterministic request plan that may later be used only after a valid immutable V2 cohort lock exists.

Preregistration:

`research/CORNER_REGIME_ADJUSTED_DIRECTION_V2_ODDS_PLAN.md`

Implementation:

`corner_regime_adjusted_direction_v2_odds_plan.py`

Regression coverage:

`tests/test_corner_regime_adjusted_direction_v2_odds_plan.py`

Dedicated CI:

`.github/workflows/corner-regime-adjusted-direction-v2-odds-plan.yml`

## Source requirement

The planner accepts only a manifest from:

`CORNER_REGIME_ADJUSTED_DIRECTION_V2_COHORT_LOCK`

with:

- `lock_status = IMMUTABLE_COHORT_LOCKED`;
- `immutable = true`;
- `research_only = true`;
- `offline_only = true`;
- `odds_acquisition_authorized = false`;
- valid `selection_sha256`;
- unchanged V2 cutoff/metadata gate;
- unchanged V1/V2 statistical gate.

It re-computes the frozen selection hash before building any request plan.

Any tampering with:

- selected fixture order;
- selected fixture membership;
- duplicate IDs;
- lock gate;
- statistical gate;
- source selection hash;
- prior authorization flags

fails closed.

## Frozen deterministic batching rule

Maximum planned odds requests per future live run:

**30**

This is an operational safety cap fixed before any V2 market prices are opened. It responds to the earlier V1 bounded provider-rate-limit wait / 75-minute CI timeout and does not alter statistical sample membership.

Rules:

1. preserve exact ordered locked fixture IDs;
2. split sequentially into chunks of at most 30 IDs;
3. every locked fixture appears in exactly one batch;
4. no reselection, replacement, backfill or dropping is allowed;
5. total planned odds requests equals locked fixture count;
6. any later partial acquisition must resume by requesting only missing IDs from the same immutable locked cohort.

## Authorization boundary

The generated acquisition plan explicitly contains:

- `live_odds_acquisition_authorized = false`;
- `requires_explicit_live_authorization = true`;
- `fixture_reselection_allowed = false`;
- `betting_enabled = false`;
- `production_promotion_authorized = false`.

PR #397 itself contains:

- no provider HTTP transport;
- no odds endpoint;
- no market-price reads;
- no Supabase writes;
- no paid action;
- no live marker;
- no production model changes.

Dedicated odds-plan CI and all repository validations passed, including production `.pkl` hash guards.

## Current V2 execution pointer

The authoritative V2 state remains:

**`WAIT_FOR_COHORT`**

The latest authoritative metadata artifact is still:

- run `35424349695`;
- artifact `10578826642`;
- digest `sha256:d486527409bed8e4a0cc11ed562ac7574e9362f3c9c83808038b90918d9388e4`.

It contains:

- 0 normalized finished fixtures after cutoff;
- 0 candidate future regime blocks;
- 0 metadata potential pairs;
- 0 locked fixtures.

Therefore, despite the new offline readiness:

- there is currently **no immutable V2 cohort lock**;
- there is currently **no valid V2 odds-acquisition plan instance** generated from real future data;
- no V2 odds endpoint may be opened;
- no live acquisition workflow may be enabled yet.

The next real live action remains another run of the **same metadata-only planner** after future matches have finished.

Only if that returns `COHORT_LOCKED`:

1. create/validate immutable cohort lock;
2. generate deterministic offline acquisition plan from that lock;
3. record both artifacts;
4. only then create a separate live-capable odds-acquisition PR.

The strongest confirmed corner result remains replicated **repricing magnitude/risk via FAIR_CENTRE**.

Repricing direction remains unresolved.

`NO_BET`, no automatic model promotion and no production `.pkl` changes remain binding.


---

# Continuity update — 2026-09-19 — V2 lock fixture-metadata identity hardened

This section extends the V2 pre-live safety chain after PR #397.

## PR #399 — bind exact fixture metadata into immutable lock identity

Merged to `main` as:

`624b28d3f38004327c0e34e1f6922d0f1bade802`

This hardening was frozen and implemented **before any real V2 `COHORT_LOCKED` artifact existed and before any V2 corner market prices were opened**.

Reason:

future odds normalization depends not only on provider fixture IDs, but also on exact fixture context:

- league;
- provider league ID;
- kickoff UTC;
- home team;
- away team.

The metadata-only live artifact already persists these fields in `future_fixture_metadata.json`.

Without binding them into the immutable lock, a later evaluation could accidentally depend on re-fetched or drifted fixture metadata even while fixture IDs themselves remained frozen.

## Updated immutable lock contract

The future cohort-lock validator now requires the source metadata artifact to contain exactly one:

- `cohort_plan.json`;
- `future_fixture_metadata.json`.

For every selected fixture it validates:

- fixture ID appears exactly once;
- fixture ID remains numeric/provider-native;
- league matches the selected regime block;
- league ID matches the frozen provider league mapping;
- kickoff is valid and at/after `2026-09-19T00:00:00Z`;
- kickoff UTC date matches the selected league-day regime block;
- home team is non-empty;
- away team is non-empty.

Extra non-selected metadata rows may exist in the source artifact but do not enter the immutable cohort identity.

## Updated selection identity

The deterministic `selection_sha256` now binds:

- future cutoff;
- frozen metadata lock gate;
- exact ordered selected blocks;
- exact ordered selected fixture IDs;
- exact ordered selected fixture metadata.

The lock also records a dedicated:

`fixture_metadata_sha256`

for the canonical ordered metadata rows.

The immutable manifest persists:

`selected_fixture_metadata`

in exact `selected_fixture_ids` order.

Regression tests verify:

- missing selected metadata fails closed;
- duplicate metadata fails closed;
- changed league ID fails closed;
- changed kickoff/block membership fails closed;
- missing home/away fails closed;
- irrelevant source JSON key order does not change the lock hash;
- extra non-selected metadata does not change the selected lock identity.

## Offline odds-plan propagation

The already-merged offline V2 odds acquisition planner was hardened in the same PR.

It now:

- requires `selected_fixture_metadata`;
- recomputes and verifies `fixture_metadata_sha256`;
- recomputes and verifies the metadata-bound `selection_sha256`;
- requires metadata order to exactly match selected fixture-ID order;
- carries immutable selected fixture metadata into the acquisition plan;
- carries matching fixture metadata inside each deterministic <=30-request batch.

This means a later live acquisition/evaluation path does not need to re-fetch fixture identity/context in order to interpret raw odds.

## What did NOT change

PR #399 does not change:

- V2 future cutoff;
- eligible leagues;
- whole league-day block selection;
- >=2 blocks per league metadata gate;
- >=12 pooled block metadata gate;
- >=80 metadata potential-pair gate;
- >=40 actual comparable-pair statistical gate;
- FAIR_CENTRE direction score;
- 20,000 regime-preserving permutations;
- seed `20260918`;
- concordance >=0.60;
- p <0.10 confirmation gate;
- any historical/opened result.

It also adds no:

- provider HTTP transport;
- odds endpoint;
- market-price read;
- live marker;
- paid action;
- Supabase write;
- production promotion.

Both dedicated V2 lock and V2 odds-plan workflows passed, as did all repository validations and production `.pkl` hash guards.

## Current execution pointer

The authoritative V2 state remains:

**`WAIT_FOR_COHORT`**

Latest authoritative metadata run/artifact remain:

- run `35424349695`;
- artifact `10578826642`;
- digest `sha256:d486527409bed8e4a0cc11ed562ac7574e9362f3c9c83808038b90918d9388e4`.

That artifact has:

- 0 finished future fixtures after cutoff;
- 0 candidate future regime blocks;
- 0 metadata potential pairs;
- 0 locked fixtures;
- no V2 odds opened.

Therefore the metadata-identity hardening is **readiness only**. No real V2 lock manifest or odds-plan instance exists yet.

Next real live action remains another run of the same metadata-only planner after future fixtures have finished.

Only after the first authoritative future `COHORT_LOCKED`:

1. validate and materialize the metadata-bound immutable lock;
2. generate the metadata-bound offline acquisition plan;
3. record both artifacts and hashes;
4. only then design a separate live-capable odds-acquisition PR.

The strongest confirmed corner result remains replicated **repricing magnitude/risk via FAIR_CENTRE**.

Repricing direction remains unresolved.

`NO_BET`, no automatic model promotion and no production `.pkl` changes remain binding.


---

# END-OF-DAY CONSOLIDATED SNAPSHOT — 2026-09-19

This section is the **authoritative end-of-day transfer snapshot for 2026-09-19**. It consolidates all substantive project work performed today, including merged work, closed/unmerged probes, and the current unmerged WIP evaluator branch.

Canonical merged `main` before this documentation-only update:

`b78b4219aa6892e5bcc1eff1c802294c88e9ece0`

The detailed historical context remains in the earlier sections of this file. The purpose of this section is to make cross-account/chat transfer safe without requiring reconstruction from individual PRs.

## 1. PR #387 — V1 regime-adjusted corner direction closed

PR #387 merged as:

`47b9c42a909992e3f0a3cd114e57f452cb240870`

Final frozen V1 verdict:

**`SAMPLE_TOO_SMALL`**

Final third-sample facts:

- 46 selected / 46 eligible rows;
- 5 contributing leagues;
- 9 contributing league-day regime blocks;
- only **30 actual comparable within-regime pairs**;
- frozen minimum required = **40**;
- diagnostic concordance = **21/30 = 0.70**;
- permutation p-value was intentionally **not computed** because the preregistered sample gate failed;
- `direction_discrimination_confirmed = false`.

Correct interpretation:

- this result is **inconclusive**, not a positive confirmation and not a statistical rejection;
- V1 must not be rescued by lowering the 40-pair minimum after seeing the sample;
- the separately replicated corner **repricing magnitude/risk** signal via `FAIR_CENTRE` remains intact;
- repricing **direction** remains unresolved.

The V1 acquisition required a same-sample timeout recovery:

- timed-out run: `35361459609`;
- timeout artifact: `10557603810`;
- timeout artifact digest: `sha256:5530abd643fa4bac1c6ca25609bd9979dd3e0e90ce1c05601d234aca807e406b`;
- 46 fixture IDs were already frozen;
- 17 raw odds responses were preserved;
- no statistical `report.json` existed yet.

Same-sample resume:

- run: `35369631434`;
- final result artifact: `10557706131`;
- digest: `sha256:5ff43199cdf1bb73e6b87649c3e68aa57bac628c68888a06a809c5df473b8d1f`;
- reused raw odds responses: 17;
- missing odds fetched during resume: 29;
- no fixture reselection;
- no threshold/sign/gate change;
- production `.pkl` hash guards passed.

## 2. Continuity after V1

PR #389 recorded the final V1 state in continuity and merged as:

`6f7b06163b5535a778ea406978431c9c6e25e08f`

This means V1 is formally closed and must not be rerun or retuned.

## 3. PR #390 — V2 future-data continuation preregistered and implemented offline-only

PR #390 merged as:

`1431cec32bec5c039a4ac396d2ab383fdd77efcf`

Experiment:

`CORNER_REGIME_ADJUSTED_DIRECTION_V2`

V2 preserves the V1 statistical hypothesis and changes only prospective sample acquisition so the next untouched sample has enough same-day pair density.

Frozen future cutoff:

`2026-09-19T00:00:00Z`

Frozen leagues:

- EPL
- LA_LIGA
- SERIE_A
- BUNDESLIGA
- LIGUE_1

Frozen metadata block:

`(league, UTC kickoff date)`

Frozen metadata cohort-lock gate:

- all 5 leagues represented;
- >=2 metadata blocks per league;
- >=12 metadata blocks pooled;
- >=80 metadata potential unordered pairs pooled.

Selection rule:

- whole blocks only;
- candidate blocks ordered by UTC kickoff date ascending, then fixed league order;
- stop at the first deterministic prefix that satisfies all metadata gates;
- no cherry-picking individual matches;
- no cross-league backfill.

Frozen downstream statistical gate remains unchanged from V1:

- >=30 eligible normalized rows;
- >=4 leagues with comparable pairs;
- >=8 contributing regime blocks;
- >=40 actual comparable pairs;
- direction score = `-opening_lambda` / `-FAIR_CENTRE`;
- concordance >=0.60;
- 20,000 regime-preserving permutations;
- seed `20260918`;
- one-sided p <0.10.

Implementation is intentionally metadata/offline-first and did not open V2 odds.

## 4. PR #391 — V2 continuity checkpoint

PR #391 merged as:

`af1fd3ca04b3874bf15f53aff9c40e78b4495296`

It recorded the frozen V2 contract before any V2 odds access.

## 5. PR #392 — metadata-only live planner

PR #392 merged as:

`fa7745519fb7f919b0b064a46670e0b98b1660a6`

It added a bounded metadata-only live inventory path.

Allowed provider surface:

- fixture-list metadata only;
- no odds endpoint;
- no market prices;
- no outcomes used for research evaluation;
- no Supabase writes;
- no paid provider action.

Request budget:

- max 2 fixture-list pages per league;
- max 10 provider requests pooled.

Prior frozen corner fixture IDs excluded:

- 55 discovery fixtures;
- 50 fresh repricing-replication fixtures;
- 46 V1 regime-adjusted direction fixtures;
- total = **151 excluded fixture IDs**.

## 6. PR #393 — metadata trigger hardening

PR #393 merged as:

`2043de27f4877355f3f5c1c3a510ce8bb6ccfa7d`

Purpose:

allow controlled same-repository triggering of the metadata-only planner where direct `workflow_dispatch` was not available through the connected GitHub integration.

Important incident:

- a literal execution marker in explanatory PR prose accidentally triggered a metadata-only run before full CI;
- that run is **non-authoritative**;
- trigger matching was hardened before the authoritative run;
- no odds endpoint was exposed and no market prices were opened.

## 7. Authoritative V2 metadata run = WAIT_FOR_COHORT

Authoritative run:

`35424349695`

Immutable artifact:

`10578826642`

Digest:

`sha256:d486527409bed8e4a0cc11ed562ac7574e9362f3c9c83808038b90918d9388e4`

Observed facts:

- provider metadata requests: **5 / 10**;
- fixture metadata rows returned: **197**;
- prior excluded fixture IDs: **151**;
- odds endpoint used: false;
- market prices opened: false;
- paid subscription used: false;
- production `.pkl` hash guard: PASS;
- normalized finished future fixtures at/after cutoff: **0**;
- candidate future regime blocks: **0**;
- metadata potential pairs: **0**;
- locked fixtures: **0**.

Binding state:

**`WAIT_FOR_COHORT`**

This is expected because the run happened almost immediately after the future cutoff; the latest captured EPL finished fixture was still `2026-09-18T19:00:00Z`.

No V2 odds acquisition is authorized while the planner returns WAIT_FOR_COHORT.

## 8. PR #394 — metadata result + continuity

PR #394 merged as:

`acdbf823b31b3eb6540afb411b1700833455bc4c`

It created:

`research/CORNER_REGIME_ADJUSTED_DIRECTION_V2_METADATA_RESULTS.md`

and recorded the authoritative WAIT_FOR_COHORT result in `PROJECT_CONTINUITY.md`.

## 9. PR #395 — immutable cohort-lock validator

PR #395 merged as:

`65993504cce3e4cc6580702abd592c658a324f79`

It added an offline-only immutable lock validator:

`corner_regime_adjusted_direction_v2_lock.py`

Preregistration:

`research/CORNER_REGIME_ADJUSTED_DIRECTION_V2_COHORT_LOCK.md`

Purpose:

when a future authoritative metadata artifact first returns `COHORT_LOCKED`, independently revalidate the frozen deterministic earliest qualifying prefix and produce an immutable lock manifest.

Current WAIT_FOR_COHORT artifacts are rejected fail-closed.

The lock does **not** authorize odds acquisition.

## 10. PR #396 — lock-readiness continuity

PR #396 merged as:

`4ca0ca4790731a1feab13cf5dc81fab5bb32c524`

It recorded cohort-lock readiness while preserving WAIT_FOR_COHORT as the authoritative state.

## 11. PR #397 — offline odds acquisition plan

PR #397 merged as:

`3bd1f7565c722d03b083e93a3ce35b7a3d69739a`

It added:

`corner_regime_adjusted_direction_v2_odds_plan.py`

Preregistration:

`research/CORNER_REGIME_ADJUSTED_DIRECTION_V2_ODDS_PLAN.md`

Purpose:

for a future immutable V2 lock only, deterministically define the exact provider fixture IDs and batching that a later separately authorized live acquisition may use.

Frozen operational batching:

- preserve exact locked fixture order/membership;
- max **30 odds requests per future live run**;
- sequential deterministic batches;
- no reselection;
- no replacement;
- no backfill;
- partial acquisition may resume only missing IDs from the same immutable locked cohort.

The offline plan explicitly sets:

- `live_odds_acquisition_authorized = false`;
- `requires_explicit_live_authorization = true`;
- `fixture_reselection_allowed = false`;
- `betting_enabled = false`;
- `production_promotion_authorized = false`.

No live provider transport exists in this block.

## 12. PR #398 — odds-plan continuity

PR #398 merged as:

`f3f39c7b42925304620e51daf8c80edfbaee9228`

It recorded the deterministic offline acquisition-plan readiness.

## 13. PR #399 — fixture metadata bound into immutable lock identity

PR #399 merged as:

`624b28d3f38004327c0e34e1f6922d0f1bade802`

This hardening happened **before any real V2 COHORT_LOCKED artifact and before any V2 market prices were opened**.

Reason:

future odds normalization requires immutable fixture context, not only fixture IDs.

The lock now binds exact selected fixture metadata:

- `fixture_id`;
- `league`;
- `league_id`;
- `kickoff_utc`;
- `home_team`;
- `away_team`.

Future lock input must contain exactly one:

- `cohort_plan.json`;
- `future_fixture_metadata.json`.

The lock validates:

- selected fixture ID appears exactly once;
- league matches selected block;
- league_id matches frozen provider mapping;
- kickoff is valid and >= future cutoff;
- kickoff UTC date matches selected regime block;
- home/away names are non-empty.

The immutable identity now includes:

- cutoff;
- metadata lock gate;
- exact selected blocks;
- exact selected fixture IDs;
- exact selected fixture metadata.

New hash:

`fixture_metadata_sha256`

The main:

`selection_sha256`

also includes selected fixture metadata.

The offline odds plan was hardened in the same PR to propagate the immutable metadata without a later metadata re-fetch.

## 14. PR #400 — fixture-metadata lock continuity

PR #400 merged as current canonical main:

`b78b4219aa6892e5bcc1eff1c802294c88e9ece0`

It recorded the metadata-bound lock identity and offline odds-plan propagation in continuity.

All dedicated V2 workflows and repository validations passed, including production `.pkl` hash guards.

## 15. Current unmerged WIP — offline frozen evaluator

A new branch exists:

`research/corner-regime-v2-offline-evaluator`

It is currently **ahead of main by 2 commits and unmerged**.

Commits:

1. `5a0832dc8efa198465014086c3272c87817105d5`
   - `Preregister offline V2 frozen evaluator`
2. `1d75e76025f6fd99121ee8c85d68b4df659310b9`
   - `Implement offline V2 frozen evaluator`

Files currently present only on that branch:

- `research/CORNER_REGIME_ADJUSTED_DIRECTION_V2_EVALUATOR.md`;
- `corner_regime_adjusted_direction_v2_evaluator.py`.

Current evaluator design:

- offline-only;
- no provider HTTP transport;
- consumes:
  1. immutable V2 lock manifest;
  2. deterministic V2 acquisition plan;
  3. immutable raw-odds artifact;
- validates lock/acquisition-plan identity;
- verifies raw artifact SHA-256 supplied by provenance;
- raw artifact must contain one response for every locked fixture ID;
- duplicate raw responses fail closed;
- non-locked raw responses fail closed;
- if any locked raw response is missing:
  - status = `ACQUISITION_INCOMPLETE`;
  - `statistical_evaluation_performed = false`;
  - no market normalization;
  - no FAIR_CENTRE reconstruction;
  - no concordance;
  - no permutations;
  - no direction verdict.

Only after complete raw acquisition does it:

- use the existing Bet365 full-time corner normalizer;
- use immutable selected fixture metadata from the lock;
- derive opening/closing market centre with the existing V1 representation;
- run the already-frozen V1 regime-adjusted direction evaluator unchanged.

Important current WIP status:

- preregistration exists;
- implementation file exists;
- **tests have NOT yet been added**;
- **dedicated CI has NOT yet been added**;
- **no PR has been opened for the evaluator**;
- therefore this branch is **not canonical main** and must not be treated as completed.

The correct next coding step after transfer is:

1. add fail-closed evaluator regression tests;
2. add dedicated offline evaluator CI with production `.pkl` hash guard;
3. verify there is no network/provider transport;
4. compare branch vs fresh main;
5. open separate PR;
6. run full CI;
7. fresh-main check;
8. exact-head merge only if green;
9. immediately update `PROJECT_CONTINUITY.md`.

## 16. PR #401 — late no-goal historical totals probe (closed / unmerged)

PR #401:

`Guarded probe for late no-goal historical totals`

State:

**closed / NOT merged**

Head:

`58758a5748d21fc7350731918832b92a1c44493b`

Result:

- configured The Odds API key was on a Free plan;
- historical odds endpoint was unavailable;
- result status from provider path: `HISTORICAL_UNAVAILABLE_ON_FREE_USAGE_PLAN`;
- no credits consumed: **185 -> 185**;
- production model hash unchanged;
- PR deliberately closed without merge.

Interpretation:

this is a research-access probe only. It does **not** add canonical code/data to main and must not be treated as a completed historical late-no-goal market dataset.

## 17. PR #402 — Betfair BASIC direct-access probe (closed / unmerged)

PR #402:

`Probe Betfair BASIC direct access`

State:

**closed / NOT merged**

Head:

`0fd81f343e83bcfa0eae22b0355d27cbe362e4bd`

Zero-cost probe result:

- unauthenticated BASIC direct file access returned HTTP 403;
- `DownloadFile` access returned HTTP 403;
- `GetCollectionOptions` access returned HTTP 403;
- no merge required.

Interpretation:

unauthenticated direct Betfair BASIC access is blocked in the tested path. No canonical project code/data resulted from this probe.

## 18. PR #403 — public Smarkets live-archive probe (closed / unmerged)

PR #403:

`Probe public Smarkets live archive for late no-goal prices`

State:

**closed / NOT merged**

Head:

`029b03a29ff3b21c89708a0117908ad88a844cf7`

Research-only public archive probe facts:

- scanned **234** Smarkets live archive files;
- covered **200** top-5 events in the final scan;
- no provider keys used;
- no paid requests used;
- production model hash unchanged;
- results were extracted externally;
- PR deliberately closed without merge.

Interpretation:

this probe establishes only that the public Smarkets live archive was inspected through a zero-cost research path. Because the PR was not merged, it is not canonical main code/data and must not be treated as a durable project dataset unless its extracted result is separately materialized and reviewed.

## 19. Canonical corner research state at end of day

Strongest supported corner result:

> opening `FAIR_CENTRE` contains replicated out-of-sample information about whether the Bet365 corner market will later undergo a material repricing.

This is a **repricing magnitude/risk** result.

Not yet supported:

> FAIR_CENTRE provides statistically confirmed individual repricing direction after controlling contemporaneous league-day market regime.

V1 direction status:

**inconclusive / SAMPLE_TOO_SMALL**

V2 direction status:

**WAIT_FOR_COHORT**

No V2 odds have been opened.

No real V2 immutable lock exists.

No real V2 acquisition-plan instance exists from future data.

No V2 raw odds artifact exists.

No V2 statistical evaluation exists.

## 20. Current V2 execution pointer

Current authoritative metadata provenance:

- run: `35424349695`;
- artifact: `10578826642`;
- digest: `sha256:d486527409bed8e4a0cc11ed562ac7574e9362f3c9c83808038b90918d9388e4`.

Current state:

**`WAIT_FOR_COHORT`**

Next real live action is **not** an odds call.

It is:

> rerun the same metadata-only V2 planner later, after enough future matches have actually finished.

Do not lower:

- 5-league requirement;
- >=2 blocks per league;
- >=12 pooled blocks;
- >=80 metadata potential pairs;
- >=40 actual comparable pairs;
- concordance >=0.60;
- p <0.10;
- 20,000 permutations;
- seed `20260918`.

If/when the first authoritative future run returns `COHORT_LOCKED`:

1. create the metadata-bound immutable lock;
2. verify `selection_sha256` and `fixture_metadata_sha256`;
3. generate deterministic offline acquisition plan;
4. record both artifacts;
5. only then design a separate controlled live odds acquisition PR;
6. raw acquisition must use the exact locked fixture IDs and immutable fixture metadata;
7. only after full acquisition may the frozen offline evaluator produce the direction verdict.

## 21. End-of-day safety state

Still binding:

- `NO_BET`;
- research-only;
- no automatic model promotion;
- research/training != production promotion;
- production `.pkl` must not change as a research side effect;
- no mass clean/reset/format;
- no post-result weakening of frozen gates;
- no opened OOT retuning;
- no synthetic replacement of missing selected fixtures;
- free/read-only checks before paid actions;
- no paid provider-plan upgrade without explicit user approval;
- GitHub `main` + live Supabase remain source of truth;
- Vercel must be checked when deployment/live-site state matters.

## 22. Transfer-critical state

For a new account/chat:

- first read this entire `PROJECT_CONTINUITY.md`;
- then read `AGENTS.md`;
- then verify fresh GitHub `main`;
- then inspect open branches/PRs;
- do **not** assume the WIP evaluator branch is merged;
- do **not** repeat closed V1 research;
- do **not** open V2 odds while status is WAIT_FOR_COHORT;
- do **not** treat PR #401 or #402 as canonical merged project state;
- continue the current coding task from the WIP evaluator branch only after checking fresh main for conflicts.


---

# Continuity update — 2026-09-26 — V2 offline frozen evaluator completed

This section supersedes the 2026-09-19 transfer note that described the evaluator as WIP.

## PR #405 — offline frozen evaluator

Merged to `main` as:

`3abb807dca9f88bdabb269998ff760f1f3cb9662`

Final PR head:

`b1006223094f978c5965d24a29e371723b0167e4`

Canonical files now in `main`:

- `research/CORNER_REGIME_ADJUSTED_DIRECTION_V2_EVALUATOR.md`;
- `corner_regime_adjusted_direction_v2_evaluator.py`;
- `tests/test_corner_regime_adjusted_direction_v2_evaluator.py`;
- `.github/workflows/corner-regime-adjusted-direction-v2-evaluator.yml`.

The old branch:

`research/corner-regime-v2-offline-evaluator`

is now historical/superseded. Do not continue from it. The canonical evaluator implementation is the one merged by PR #405 from:

`research/corner-regime-v2-offline-evaluator-fresh`.

## Frozen evaluator contract

The evaluator is strictly offline-only.

Required inputs:

1. immutable V2 cohort-lock manifest;
2. matching deterministic V2 offline odds-acquisition plan;
3. immutable raw-odds artifact.

Before any normalization/statistics it validates:

- lock identity;
- acquisition-plan identity;
- `selection_sha256`;
- `fixture_metadata_sha256`;
- raw artifact SHA-256 provenance;
- exact locked fixture membership;
- no duplicate raw responses;
- no raw responses for non-locked fixture IDs;
- one raw response for every locked fixture ID.

If any locked raw response is missing:

`status = ACQUISITION_INCOMPLETE`

and:

`statistical_evaluation_performed = false`

In that state the evaluator does **not**:

- call the Bet365 corner normalizer;
- reconstruct FAIR_CENTRE;
- calculate centre_delta;
- calculate pairwise concordance;
- run permutations;
- produce a direction verdict.

This prevents a partial provider acquisition from silently becoming a smaller post-hoc evaluation sample.

## Complete-acquisition path

Only after every locked fixture has a captured raw odds response, the evaluator:

- uses exact immutable `selected_fixture_metadata` from the lock;
- uses the already-existing Bet365 full-time corner normalizer;
- uses the unchanged opening/closing market-centre representation;
- preserves selected cohort identity;
- permits structurally invalid/missing market rows to become ineligible only at normalization;
- never replaces/backfills an ineligible selected fixture;
- invokes the already-frozen V1 regime-adjusted direction evaluator unchanged.

Frozen downstream direction contract remains:

- direction score = `-opening_lambda` / `-FAIR_CENTRE`;
- regime block = league + UTC kickoff date;
- within-block unordered pairwise concordance;
- ties omitted;
- >=30 eligible rows;
- >=4 leagues with comparable pairs;
- >=8 contributing regime blocks;
- >=40 actual comparable pairs;
- concordance >=0.60;
- 20,000 regime-preserving permutations;
- seed `20260918`;
- one-sided p <0.10.

Allowed evaluated verdicts remain:

- `INDIVIDUAL_DIRECTION_DISCRIMINATION_REPLICATED`;
- `INDIVIDUAL_DIRECTION_DISCRIMINATION_NOT_CONFIRMED`;
- `SAMPLE_TOO_SMALL`.

No new thresholds, feature search, sign changes or post-result tuning were introduced.

## Regression/CI proof

Dedicated evaluator regression tests cover:

- incomplete acquisition stops before normalizer/statistics;
- complete synthetic acquisition reaches the frozen evaluation orchestration;
- structurally ineligible selected fixtures are reported without replacement;
- non-locked raw fixture rejection;
- duplicate raw response rejection;
- lock/acquisition-plan mismatch rejection;
- selection/fixture-metadata identity mismatch rejection;
- raw artifact digest mismatch rejection;
- no-network/no-live-transport source guard.

Dedicated workflow:

`Corner Regime-Adjusted Direction V2 Evaluator`

passed fully.

Full repository validations also passed:

- Research PR Validation;
- Product PR Validation;
- Bundesliga PR Validation;
- Serie A PR Validation;
- Ligue 1 PR Validation;
- Eredivisie PR Validation.

Production `.pkl` hash guard passed.

## Current V2 execution pointer after evaluator merge

The live/prospective state is still the last authoritative metadata state:

**`WAIT_FOR_COHORT`**

Latest authoritative metadata provenance remains:

- run `35424349695`;
- artifact `10578826642`;
- digest `sha256:d486527409bed8e4a0cc11ed562ac7574e9362f3c9c83808038b90918d9388e4`.

That run occurred on 2026-09-19 and found:

- 0 finished future fixtures after cutoff;
- 0 candidate future regime blocks;
- 0 metadata potential pairs;
- 0 locked fixtures;
- no V2 odds opened.

Now that the offline evaluator is canonical, the full pre-live chain is ready:

1. metadata-only planner;
2. immutable metadata-bound cohort lock;
3. deterministic offline odds-acquisition plan;
4. frozen offline evaluator.

The next real live action remains a **metadata-only** V2 inventory check using the same frozen planner. It must not open odds.

If a future metadata check returns `WAIT_FOR_COHORT`, remain blocked and do not change gates.

If it first returns `COHORT_LOCKED`:

1. materialize/validate the immutable lock;
2. record `selection_sha256` and `fixture_metadata_sha256`;
3. generate the deterministic offline acquisition plan;
4. record lock + plan;
5. only then design a separately authorized live odds-acquisition PR;
6. after complete raw acquisition, pass the immutable raw artifact to the canonical evaluator.

## Safety remains binding

- research-only;
- `NO_BET`;
- no automatic model promotion;
- no production `.pkl` changes as research side effect;
- no paid provider-plan upgrade without explicit approval;
- no odds access while metadata state is WAIT_FOR_COHORT;
- no fixture reselection/backfill after lock;
- no weakening of metadata or statistical gates;
- no opened-sample retuning.

---

# Continuity update — 2026-09-26 — second V2 metadata check remains WAIT_FOR_COHORT

This section supersedes the previous execution pointer that referenced the 2026-09-19 zero-fixture metadata state.

## PR #407 — execution harness only

PR #407:

`Run 2026-09-26 metadata-only V2 cohort recheck`

Exact head:

`62420be164e744be2db2a7b08da5921f53476746`

The PR was used only to trigger the already-merged metadata-only workflow after all exact-head CI checks were green.

The live marker was:

- added only after required CI passed;
- placed as the first PR-body line per the hardened trigger contract;
- removed immediately after `live-metadata` entered `in_progress`.

PR #407 was then closed **without merge** after the authoritative result was captured.

No contract/code from this execution harness is canonical main.

## Authoritative 2026-09-26 metadata-only run

Workflow run:

`36218178333`

Immutable artifact:

- artifact ID: `10898320900`;
- digest: `sha256:276812a4c34c4c1fac5ea9c3f45e82c997bbda85a8fc629eb0c930f76577d635`;
- size: 23,329 bytes.

Safety:

- provider requests = **5 / 10**;
- fixture-list metadata only;
- odds endpoint used = false;
- market prices opened = false;
- match outcomes used = false;
- football-state used = false;
- paid subscription used = false;
- production `.pkl` hash guard = PASS.

Frozen cutoff remains:

`2026-09-19T00:00:00Z`

Prior excluded fixture IDs remain:

**151**

## Current metadata inventory

Observed:

- live fixture metadata rows returned = **231**;
- normalized finished future fixtures after cutoff = **43**;
- qualifying league-day candidate blocks = **10**;
- candidate fixtures inside those blocks = **43**;
- metadata potential pairs = **74**.

Blocks by league:

- EPL = 2;
- La Liga = 2;
- Serie A = 2;
- Bundesliga = 2;
- Ligue 1 = 2.

Therefore all five leagues now satisfy the frozen per-league requirement of >=2 blocks.

The pooled lock gate still fails:

- pooled qualifying blocks = **10 / 12**;
- metadata potential pairs = **74 / 80**.

Binding planner status remains:

**`WAIT_FOR_COHORT`**

No cohort has been locked:

- selected blocks = 0;
- selected fixture IDs = 0.

## Interpretation

V2 has progressed materially since the 2026-09-19 metadata run:

- previous normalized future fixtures: 0;
- current normalized future fixtures: 43;
- previous candidate blocks: 0;
- current candidate blocks: 10;
- previous metadata potential pairs: 0;
- current metadata potential pairs: 74.

However, this is still **not** `COHORT_LOCKED`.

Relative to the preregistered metadata gate, the current inventory is short by:

- 2 qualifying pooled blocks;
- 6 metadata potential pairs.

This distance is descriptive only.

Do not:

- lower 12 pooled blocks;
- lower 80 potential pairs;
- manually choose two blocks;
- open odds for the existing 43 fixtures;
- pre-lock fixture IDs;
- run the direction evaluator;
- substitute current 74 potential pairs for the later >=40 actual comparable-pair statistical gate.

## Current execution pointer

The full pre-live V2 chain is now canonical and ready:

1. metadata-only planner;
2. metadata-bound immutable cohort-lock validator;
3. deterministic offline odds-acquisition planner;
4. frozen offline evaluator.

The live state remains:

**`WAIT_FOR_COHORT`**

The next allowed live action is another run of the **same metadata-only planner** after more future matches have finished.

Only when the first authoritative future result is exactly:

`COHORT_LOCKED`

may the project:

1. materialize the exact metadata-bound immutable cohort lock;
2. record `selection_sha256` and `fixture_metadata_sha256`;
3. generate the deterministic offline acquisition plan;
4. record lock + plan provenance;
5. create a separate explicitly authorized live odds-acquisition PR.

Until then:

- no V2 odds;
- no market-price reads;
- no live acquisition workflow;
- no direction statistic;
- no betting/staking;
- no production promotion.

The strongest confirmed corner result remains replicated **repricing magnitude/risk via FAIR_CENTRE**.

Regime-adjusted direction remains unresolved.

---

# Continuity update — 2026-09-26 — immediate V2 metadata recheck unchanged

At user request, the already-frozen metadata-only planner was run again immediately rather than waiting for another full league round.

Execution harness:

- PR #409;
- exact head `8ebab42da35d69f11d199975011a2128b7f9c194`;
- exact-head CI passed before live marker insertion;
- marker was removed immediately after the live job was created;
- PR #409 was closed **without merge** after the result.

Authoritative run:

`36218898253`

Immutable artifact:

- ID `10898297066`;
- digest `sha256:eb163d097dc2713b8f8f03370eacead91a15d3a38c0757e48b301d82e799446c`;
- size 23,329 bytes.

Safety remained intact:

- 5 metadata requests;
- no odds endpoint;
- no market prices;
- no match outcomes;
- no football-state input;
- no paid subscription;
- production `.pkl` unchanged.

Result was exactly unchanged from the immediately preceding authoritative metadata check:

- 231 provider fixture metadata rows;
- 43 normalized future finished fixtures;
- 10 qualifying league-day blocks;
- 43 candidate fixtures in those blocks;
- 74 metadata potential pairs;
- 2 blocks in each of all five leagues.

Binding state:

**`WAIT_FOR_COHORT`**

Frozen shortfall remains:

- 10 / 12 pooled blocks;
- 74 / 80 metadata potential pairs.

No V2 cohort lock exists.

No V2 odds acquisition is authorized.

Operational note:

because this immediate duplicate check produced identical provider inventory, do not spend further metadata requests repeatedly without a plausible provider-inventory change. The next metadata-only run should be triggered only when newly finished league-day inventory is reasonably expected or another specific operational reason exists.

All previously frozen V2 gates remain unchanged.

---

# Continuity update — 2026-09-26 — V2B 10/74 cohort is now immutably locked

This section supersedes the prior V2 `WAIT_FOR_COHORT` execution pointer for the active direction experiment.

## Why V2B was created

At explicit user instruction, the operational metadata gate was changed from V2's:

- 12 pooled qualifying blocks;
- 80 metadata potential pairs;

to a new experiment:

`CORNER_REGIME_ADJUSTED_DIRECTION_V2B`

with:

- 10 pooled qualifying blocks;
- 74 metadata potential pairs.

This was done as a **new experiment**, not by rewriting V2 history.

Important methodological note:

- fixture metadata density had already been observed;
- no V2B odds/market prices had been opened;
- therefore V2B is a post-metadata / pre-odds operational amendment;
- the downstream statistical direction gate remains unchanged.

The original V2 remains historically valid as `WAIT_FOR_COHORT` under its original 12/80 metadata gate.

## PR #411 — V2B implementation

Merged as:

`385df56a54d36a8326f02ae07c02dd868111dca1`

Added:

- `research/CORNER_REGIME_ADJUSTED_DIRECTION_V2B.md`;
- `corner_regime_adjusted_direction_v2b.py`;
- `corner_regime_adjusted_direction_v2b_lock.py`;
- `tests/test_corner_regime_adjusted_direction_v2b.py`;
- dedicated V2B offline CI.

Frozen V2B metadata gate:

- >=2 blocks per league;
- >=10 pooled blocks;
- >=74 metadata potential pairs.

Frozen downstream statistical gate remains:

- >=30 eligible normalized rows;
- >=4 leagues with comparable pairs;
- >=8 contributing blocks;
- >=40 actual comparable pairs;
- concordance >=0.60;
- 20,000 regime-preserving permutations;
- seed `20260918`;
- p <0.10.

## PR #412 — immutable lock materialization workflow

Merged as:

`277f53c3717c468c21ac704e1ca041bd5a91c007`

Authoritative offline lock run:

`36219786013`

Immutable lock artifact:

- artifact ID: `10899325930`;
- digest: `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- size: 9,198 bytes.

Source immutable metadata artifact:

- run `36218898253`;
- artifact `10898297066`;
- digest `sha256:eb163d097dc2713b8f8f03370eacead91a15d3a38c0757e48b301d82e799446c`.

The source artifact digest was verified before replanning.

No provider call was made while materializing the V2B lock.

## Current V2B locked cohort

Binding status:

**`IMMUTABLE_COHORT_LOCKED`**

Locked cohort:

- selected blocks = **10**;
- selected fixtures = **43**;
- metadata potential pairs = **74**;
- blocks by league:
  - EPL = 2;
  - La Liga = 2;
  - Serie A = 2;
  - Bundesliga = 2;
  - Ligue 1 = 2.

This exact 43-fixture cohort is now frozen.

No fixture may be:

- removed;
- replaced;
- reordered for selection purposes;
- backfilled;
- rediscovered from provider metadata.

## Immutable hashes

`selection_sha256`:

`sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73`

`fixture_metadata_sha256`:

`sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb`

These hashes bind the exact selected blocks, fixture IDs and immutable fixture metadata.

Fixture metadata includes:

- fixture_id;
- league;
- league_id;
- kickoff_utc;
- home_team;
- away_team.

## Safety state

Lock materialization was:

- offline-only;
- no odds endpoint;
- no market-price reads;
- no outcomes;
- no football-state inputs;
- no paid action;
- no Supabase writes;
- no production model change.

Production `.pkl` hash guard passed.

The lock explicitly sets:

- `odds_acquisition_authorized = false`;
- `betting_enabled = false`;
- `production_promotion_authorized = false`.

## Current execution pointer

The project no longer waits for additional finished fixtures for V2B.

The next allowed step is now:

**generate the deterministic offline odds-acquisition plan from immutable lock artifact `10899325930`.**

That plan must:

- consume only this immutable lock;
- preserve exact 43 fixture IDs;
- preserve immutable fixture metadata;
- verify `selection_sha256`;
- verify `fixture_metadata_sha256`;
- define deterministic request batches;
- prohibit fixture reselection/backfill;
- keep live odds acquisition disabled until a separate controlled live PR is created.

Only after the acquisition plan is frozen may live odds requests be made.

The later statistical direction test remains unchanged and must still pass the >=40 actual comparable-pair gate after normalization.

---

# Continuity update — 2026-09-26 — V2B deterministic acquisition plan materialized

PR #414 merged as:

`8809fc7b61b2a1d9807a536a8d4de1a876cc2e2c`

Canonical module:

`corner_regime_adjusted_direction_v2b_odds_plan.py`

Preregistration:

`research/CORNER_REGIME_ADJUSTED_DIRECTION_V2B_ODDS_PLAN.md`

Authoritative offline plan workflow run:

`36220204953`

Immutable acquisition-plan artifact:

- artifact ID: `10899305926`;
- digest: `sha256:8fe2203443f4e59a5800fd7315df6d333a19771e9827d3cad64ef4f658119c56`;
- size: 3,142 bytes.

Source immutable lock:

- run `36219786013`;
- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`.

The acquisition plan verifies and preserves:

- `selection_sha256 = sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73`;
- `fixture_metadata_sha256 = sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb`;
- exact 43 fixture IDs;
- exact immutable fixture metadata;
- exact fixture order.

Deterministic batches:

- batch 1 = **30** fixture IDs;
- batch 2 = **13** fixture IDs;
- total planned odds requests = **43**.

Resume rule:

`REQUEST_ONLY_MISSING_IDS_FROM_SAME_LOCKED_COHORT`

The plan explicitly forbids:

- fixture reselection;
- fixture replacement;
- backfill;
- provider fixture discovery.

Authorization state in the plan remains:

- `live_odds_acquisition_authorized = false`;
- `requires_explicit_live_authorization = true`;
- `fixture_reselection_allowed = false`;
- `betting_enabled = false`;
- `production_promotion_authorized = false`.

No provider request was made while building the plan.

## Current execution pointer

The V2B cohort is locked and the deterministic acquisition plan is now frozen.

The next step is a **separate controlled live odds-acquisition PR** that must:

1. consume only artifact `10899305926`;
2. verify its digest;
3. consume only the exact locked fixture IDs;
4. make no fixture-list/discovery requests;
5. fetch only the corner odds endpoint for the planned IDs;
6. preserve raw responses immutably;
7. if partial, resume only missing IDs from the same cohort;
8. never evaluate a partial acquisition;
9. keep production `.pkl` unchanged.

---

# Continuity update — 2026-09-26 — V2B raw odds acquisition complete

PR #416 merged as:

`5902c6fb99e34b03f97e20638ac824c25b6b6cd7`

Canonical live-acquisition module/workflow:

- `corner_regime_adjusted_direction_v2b_acquisition.py`;
- `.github/workflows/corner-regime-adjusted-direction-v2b-acquisition.yml`;
- `research/CORNER_REGIME_ADJUSTED_DIRECTION_V2B_LIVE_ACQUISITION.md`.

The V2B cohort was already frozen before acquisition:

- 10 league-day blocks;
- 43 selected fixtures;
- 74 metadata potential pairs;
- `selection_sha256 = sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73`;
- `fixture_metadata_sha256 = sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb`.

Source immutable lock:

- run `36219786013`;
- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`.

Source deterministic acquisition plan:

- run `36220204953`;
- artifact `10899305926`;
- digest `sha256:8fe2203443f4e59a5800fd7315df6d333a19771e9827d3cad64ef4f658119c56`.

## Authoritative acquisition run

Workflow run:

`36222282829`

Batch 1:

- planned requests = 30;
- captured raw responses = 30;
- missing locked fixtures = 13;
- status = `ACQUISITION_PARTIAL`;
- no normalization;
- no statistical evaluation;
- artifact `10898524057`;
- digest `sha256:5a15902ea9b73cc778bd8a116010f83edf24af38973dcf45de619e4a729f0fee`.

Batch 2:

- planned requests = 13;
- used batch-1 raw artifact as same-run resume;
- fetched only the 13 remaining locked IDs;
- captured locked raw responses after completion = **43**;
- missing locked fixtures = **0**;
- status = `ACQUISITION_COMPLETE`;
- no normalization;
- no statistical evaluation.

Final immutable complete raw artifact:

- artifact ID `10899611444`;
- digest `sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`;
- size 15,623 bytes.

Total provider raw-odds requests:

**43 = 30 + 13**

There were no:

- fixture-list requests;
- provider fixture discovery;
- reselection;
- replacement;
- backfill;
- outcomes;
- football-state features;
- paid subscription use;
- production `.pkl` changes.

Production artifact hash guards passed.

## Current execution pointer

The V2B acquisition phase is complete.

Do **not** make more provider requests for this locked cohort.

The next step is now strictly offline:

1. use complete raw artifact `10899611444`;
2. verify digest `sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`;
3. use only immutable V2B lock `10899325930`;
4. use only immutable V2B plan `10899305926`;
5. normalize raw odds with the already-frozen Bet365 corner normalizer;
6. preserve selected cohort identity;
7. never backfill structurally ineligible rows;
8. run the unchanged V1/V2 regime-adjusted direction statistic;
9. preserve the unchanged statistical gate:
   - >=30 eligible rows;
   - >=4 leagues with comparable pairs;
   - >=8 contributing regime blocks;
   - >=40 actual comparable pairs;
   - concordance >=0.60;
   - 20,000 regime-preserving permutations;
   - seed `20260918`;
   - one-sided p <0.10.

At this point no V2B statistical result has yet been inspected.

The raw acquisition being complete does not imply signal confirmation.

---

# Continuity update — 2026-09-26 — V2B regime-adjusted corner direction final result

The V2B direction block is now statistically evaluated and closed.

Canonical evaluator implementation was merged through PR #418 as:

`fbd66a5201a2bbcf1b51d25c7134b56f4fe04399`

Preregistered evaluator contract:

`research/CORNER_REGIME_ADJUSTED_DIRECTION_V2B_EVALUATOR.md`

Canonical evaluator:

`corner_regime_adjusted_direction_v2b_evaluator.py`

## Frozen cohort and provenance

The V2B cohort was frozen before any V2B corner odds were opened:

- selected regime blocks = **10**;
- selected fixtures = **43**;
- metadata potential pairs = **74**;
- two selected league-day blocks in each of EPL, La Liga, Serie A, Bundesliga and Ligue 1.

Immutable cohort identity:

- `selection_sha256 = sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73`;
- `fixture_metadata_sha256 = sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb`.

Immutable lock:

- run `36219786013`;
- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`.

Immutable acquisition plan:

- run `36220204953`;
- artifact `10899305926`;
- digest `sha256:8fe2203443f4e59a5800fd7315df6d333a19771e9827d3cad64ef4f658119c56`;
- frozen batching = 30 + 13.

Complete raw acquisition:

- run `36222282829`;
- artifact `10899611444`;
- digest `sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`;
- 43 / 43 locked raw responses;
- zero missing;
- no fixture discovery/reselection/replacement/backfill;
- total provider odds requests = 43.

## Important operational amendment

Historical V2 expected a metadata stopping rule of 12 blocks / 80 metadata potential pairs.

After metadata availability was observed but **before any V2B odds were opened**, V2B was separately preregistered with:

- minimum 2 blocks per league unchanged;
- pooled metadata gate = **10 blocks / 74 potential pairs**.

Therefore V2B must **not** be described as a fully untouched replication of the original V2 12/80 metadata stopping rule.

The final statistical direction test itself was **not weakened**:

- >=30 eligible normalized rows;
- >=4 leagues with comparable pairs;
- >=8 contributing regime blocks;
- >=40 actual comparable pairs;
- concordance >=0.60;
- 20,000 regime-preserving permutations;
- seed `20260918`;
- one-sided p <0.10.

## First evaluator execution attempt was non-statistical

Workflow run:

`36222975287`

Result artifact:

- `10899821631`;
- digest `sha256:ae0f6e2b88cd5df211699c56d9c513539cac2999915b60e87d78c74c189a5f1c`.

The immutable source digests verified, but the inherited ZIP loader only matched paths containing `/raw/odds/`, while the GitHub artifact stored files as root-level `raw/odds/<fixture_id>.json`.

Consequently that attempt reported:

- captured raw responses = 0;
- missing = 43;
- status = `ACQUISITION_INCOMPLETE`;
- statistical evaluation performed = false;
- verdict = null.

This attempt is **not** a statistical result.

No normalizer, FAIR_CENTRE, concordance or permutation statistic was run.

The only amendment was a path-normalization fix plus a regression test for root-level artifact layout. No sample/statistical parameter changed.

## Authoritative successful evaluation

Authoritative workflow run:

`36223204711`

Immutable evaluation artifact:

- artifact ID `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`;
- size 4,120 bytes.

Evaluation completeness:

- locked fixtures = **43**;
- captured locked raw responses = **43**;
- eligible normalized rows = **43**;
- ineligible selected fixtures = **0**;
- missing selected fixtures = **0**.

Rows by league:

- EPL = 9;
- La Liga = 9;
- Serie A = 9;
- Bundesliga = 8;
- Ligue 1 = 8.

Frozen sample gate result:

- contributing leagues = **5**;
- contributing regime blocks = **9**;
- actual comparable pairs = **42**;
- concordant pairs = **25**;
- sample gate = **PASS**.

Observed concordance:

`25 / 42 = 0.5952380952380952`

Frozen minimum:

`0.60`

Permutation result:

- 20,000 permutations;
- seed `20260918`;
- one-sided p = **0.207939603019849**.

Frozen maximum p-value:

`< 0.10`

## Final verdict

**`INDIVIDUAL_DIRECTION_DISCRIMINATION_NOT_CONFIRMED`**

`direction_discrimination_confirmed = false`

This is **not** a `SAMPLE_TOO_SMALL` outcome.

The frozen sample gate passed. The direction hypothesis failed the frozen confirmation gate because:

- concordance = 0.595238 < 0.60;
- p = 0.207940 > 0.10.

## Diagnostics only

League concordance:

- Bundesliga = 5 / 7 = 0.7143;
- EPL = 0 / 7 = 0.0000;
- La Liga = 6 / 7 = 0.8571;
- Ligue 1 = 6 / 9 = 0.6667;
- Serie A = 8 / 12 = 0.6667.

Overall centre-movement diagnostics:

- positive = 9;
- negative = 4;
- zero = 30;
- positive share among non-zero = 0.6923076923.

Regime-adjusted top-minus-bottom score diagnostic:

`0.14700833159517418`

These diagnostics must not be used to exclude EPL, reverse the score, change thresholds or otherwise retune V2B after opening the sample.

## Binding interpretation

The replicated `FAIR_CENTRE` **repricing magnitude/risk** signal remains valid.

What V2B does **not** confirm is a stronger claim:

> after controlling for contemporaneous league-day market regime, lower opening FAIR_CENTRE does not currently show sufficient frozen evidence to predict the individual match's repricing direction.

Therefore:

- do not turn V2B into a live direction betting rule;
- do not lower the concordance threshold;
- do not relax the p-value gate;
- do not exclude unfavorable leagues post hoc;
- do not rerun a tuned version on these same 43 matches and call it replication.

## Safety

The complete block remained research-only:

- no match outcomes;
- no football-state/CORNERS10 inputs;
- no betting/staking;
- no production promotion;
- no Supabase writes;
- production `.pkl` hash guards passed;
- no provider calls were made during evaluation.

## Current execution pointer

The V2B individual-direction hypothesis is now **closed as NOT CONFIRMED** on the frozen 43-match cohort.

The next research step should not try to rescue this same direction rule on the opened sample.

The strongest surviving corner-market finding is still:

**opening FAIR_CENTRE carries replicated information about the probability/magnitude of material pre-match repricing, but not a confirmed regime-adjusted direction.**

A safe next block is therefore to use already-opened datasets only for **hypothesis generation**, and preregister any new directional mechanism on a future unseen cohort before opening its odds.

No additional provider request is required to close or reinterpret V2B.

---

# Continuity update — 2026-09-26 — FAIR_CENTRE simple timing filter not portable

After closing V2B direction as NOT CONFIRMED, a secondary retrospective portability audit tested whether the already-replicated FAIR_CENTRE repricing-risk signal could support a simple operational timing rule.

Experiment:

`CORNER_REPRICING_TIMING_POLICY_V1`

Canonical implementation:

`corner_repricing_timing_policy_v1.py`

Contract:

`research/CORNER_REPRICING_TIMING_POLICY_V1.md`

Result:

`research/CORNER_REPRICING_TIMING_POLICY_V1_RESULTS.md`

Implementation/audit PR:

- PR #420;
- merged as `d22e025057443e9deb141e74481c786d00e907c0`.

Authoritative audit run:

`36225197468`

Immutable artifact:

- ID `10900099199`;
- digest `sha256:2f3c41a393e7cfad67cc26f00bad1c5184372557244c1ae403451bb345617785`;
- size 7,724 bytes.

## Evidence boundary

All three evaluation cohorts were already opened in prior research.

Therefore this is:

- secondary retrospective reuse;
- not an untouched prospective replication;
- not a new betting/execution validation.

The frozen risk predictor was fitted only on the original 55-row discovery cohort.

Frozen policy reused without search:

- top 25% risk per league = `WAIT`;
- remaining 75% = `STABLE_OPEN`.

Frozen original-55 material-move threshold:

`0.362835012901983`

No provider calls were made.

## Cohort results

### Fresh 50

WAIT versus STABLE_OPEN:

- material-move prevalence = **53.33% vs 11.43%**;
- risk ratio = **4.67**;
- mean movement magnitude difference = **+0.230884**.

Consistent with WAIT policy.

### V1 46

WAIT versus STABLE_OPEN:

- material-move prevalence = **14.29% vs 28.13%**;
- risk ratio = **0.508**;
- mean movement magnitude difference = **-0.024117**.

Both relationships reverse.

This cohort is not consistent with the WAIT policy.

### V2B 43

WAIT versus STABLE_OPEN:

- material-move prevalence = **23.08% vs 6.67%**;
- risk ratio = **3.46**;
- mean movement magnitude difference = **+0.136950**.

Consistent with WAIT policy.

## Pooled descriptive view

Across 139 later rows:

- WAIT rows = 42;
- STABLE_OPEN rows = 97;
- WAIT material-move prevalence = **30.95%**;
- STABLE_OPEN material-move prevalence = **15.46%**;
- pooled risk ratio = **2.00**;
- WAIT minus STABLE mean movement magnitude = **+0.117011**.

The pooled effect is favorable but cannot erase the complete reversal in V1_46.

## Binding classification

**`NOT_PORTABLE_AS_SIMPLE_WAIT_FILTER`**

The simple rule:

> top 25% FAIR_CENTRE risk => WAIT

must not be promoted to product/betting/execution logic from current evidence.

Do not:

- tune the 25% cutoff on these opened cohorts;
- discard V1_46;
- weight cohorts post hoc;
- claim the pooled RR=2.0 proves a stable timing edge.

The stronger surviving conclusion remains narrower:

> FAIR_CENTRE contains replicated information about repricing magnitude/risk, but neither a stable individual direction rule nor a portable simple WAIT/STABLE execution rule has been established.

## Independent football-state direction idea

A conceptually stronger future direction mechanism would use an independent football-only signal for the sign of movement and FAIR_CENTRE only for repricing risk/magnitude.

The canonical football-only signal available in the repository is CORNERS10.

However, current 2026/27 corner-history coverage is not sufficient to reconstruct exact point-in-time CORNERS10 for the opened market cohorts across all required leagues without introducing a new external data source:

- `public.match_statistics` currently has 0 rows;
- `public.league_corner_results` currently has 0 rows;
- current EPL 2026/27 rows in `public.matches` have no populated home/away corner counts.

Do not synthesize missing CORNERS10 histories from goals or later data.

A future CORNERS10-vs-opening-market-centre direction experiment requires a timestamp-safe current-season corner-result source first.

## Supabase security advisory discovered during read-only source audit

A read-only Supabase schema inspection returned a critical advisory that Row Level Security is disabled on five public tables:

- `public.teams`;
- `public.predictions`;
- `public.match_statistics`;
- `public.league_prediction_ledger`;
- `public.epl_ai_market_pair_ledger`.

This is a security/configuration issue, not a corner-research result.

Do **not** blindly enable RLS in production: enabling it without appropriate policies could break application/client access.

Before remediation:

1. identify which client/server roles read or write each table;
2. define explicit select/insert/update policies where needed;
3. test policies safely;
4. then enable RLS through a reviewed migration.

No RLS change was made during this audit.

## Current research pointer

Closed findings:

- FAIR_CENTRE repricing magnitude/risk = replicated;
- regime-adjusted individual direction = not confirmed;
- simple top-25%-risk WAIT filter = not portable.

The next useful direction research should introduce genuinely new independent information rather than keep tuning opening-market state on the same opened cohorts.

Preferred candidate remains:

**football-only expected corner pressure/total minus opening market centre**

but only after a reliable point-in-time current-season corner-history source is established.

---

# Continuity update — 2026-09-26 — V2B CORNERS10 replay feasibility established

A zero-cost source/identity feasibility audit was completed for the frozen 43-fixture V2B cohort.

Experiment:

`V2B_CORNERS10_REPLAY_FEASIBILITY`

Workflow run:

`36227211286`

Immutable artifact:

- ID `10900784704`;
- digest `sha256:66c83b96f8c1143397aca660701d0a7f5950c3b59a1bd0158bbefe6501d7ecfb`;
- size 2,634 bytes.

Frozen cohort source remained the immutable V2B lock:

- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- 43 fixtures.

## What was checked

Only public/repository-owned Football-Data corner-result sources were used:

- 2025/26 top-flight season;
- 2026/27 top-flight season;
- EPL, La Liga, Serie A, Bundesliga, Ligue 1.

The audit used continuous point-in-time history across the season boundary and counted only matches strictly before each locked fixture.

It did **not**:

- read V2B odds;
- compute opening/closing market features;
- calculate centre_delta;
- test direction;
- make Odds API requests;
- write Supabase;
- modify production models.

## Source/identity result

All frozen fixtures matched uniquely:

**43 / 43**

Therefore provider-to-Football-Data fixture identity is no longer the blocker for this research path.

## Canonical CORNERS10 availability

Fixtures with >=10 prior top-flight corner-result matches for **both teams**:

**31 / 43**

By league:

- EPL = 6 / 9;
- La Liga = 6 / 9;
- Serie A = 7 / 9;
- Bundesliga = 6 / 8;
- Ligue 1 = 6 / 8.

Binding feasibility status:

**`PARTIAL_REPLAY_FEASIBLE`**

The 12 ineligible fixtures are caused by insufficient prior top-flight history, primarily promoted/returning clubs.

Examples:

- Hull = 4 prior top-flight matches;
- Ipswich = 4;
- Coventry = 4;
- Racing Santander = 6;
- Malaga = 6;
- Deportivo A Coruna = 6;
- Venezia = 4;
- Frosinone = 4;
- Schalke = 3;
- Elversberg = 3;
- Paderborn = 3;
- Le Mans = 4;
- Troyes = 4.

No lower-division history was synthesized or used to fill those gaps.

## Current research pointer

The next safe research step is now possible offline:

> construct the canonical pre-match CORNERS10 football-state signal for the exact 31 eligible V2B fixtures and explore whether an independent football-only signal explains the sign of already-opened market centre movement.

Important boundary:

- this will be hypothesis generation on an opened sample, not independent confirmation;
- the eligible 31-fixture subset is frozen by the feasibility rule and must not be altered after viewing direction results;
- the 12 ineligible fixtures must remain explicit and cannot be backfilled/replaced;
- any promising mechanism must later be preregistered and tested on a new unseen market cohort before being treated as evidence.

The previously closed findings remain unchanged:

- FAIR_CENTRE repricing magnitude/risk = replicated;
- regime-adjusted individual direction = not confirmed;
- simple top-25%-risk WAIT filter = not portable.

---

# Continuity update — 2026-09-28 — V2B CORNERS10 direction hypothesis explored

The next post-V2B hypothesis-generation block has been completed and merged through PR #430.

Merge commit:

`c4e32bbb186f97f1cac119d8107ebc38b568cc65`

Experiment:

`V2B_CORNERS10_DIRECTION_HYPOTHESIS_V1`

This block used only the exact 31 fixtures previously frozen as CORNERS10-replay-feasible by PR #427.

The other 12 V2B fixtures remained ineligible and were not replaced or backfilled.

## Signal tested

Using only prior top-flight corner history:

`corners10_total = 0.5 * (home_for10 + home_against10 + away_for10 + away_against10)`

`football_gap = corners10_total - opening_lambda`

The sign of football_gap was compared with the already-opened V2B market `centre_delta`.

This was hypothesis generation only, not independent confirmation.

## Authoritative result

Workflow run:

`36427498130`

Artifact:

- ID `10971841803`;
- digest `sha256:4bf2ef0c7defa48c6fef5cc96b56e08309a6cacdd0aed872e88759590264a4f1`;
- size 2,647 bytes.

Evaluated rows:

**31**

Observed zero-movement rows:

**21**

Comparable non-zero direction rows:

**10**

Concordant:

**8 / 10 = 0.80**

League diagnostics:

- Bundesliga 2/2;
- EPL 1/2;
- La Liga 2/2;
- Ligue 1 1/1;
- Serie A 2/3.

However, the preregistered exploratory consistency condition failed:

- positive football-gap mean centre_delta = +0.132574;
- negative football-gap mean centre_delta = **+0.032076**, not negative;
- Pearson football_gap vs centre_delta = -0.138894;
- Spearman = 0.013111.

Final classification:

**`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`**

Do not interpret the 8/10 subset agreement as an 80% predictive direction edge. Only 10/31 eligible fixtures had non-zero movement, while the continuous relationship was weak and the negative-gap group did not move down on average.

## Current corner-market research state

Still supported:

- FAIR_CENTRE repricing magnitude/risk = replicated.

Not supported as reliable portable rules:

- regime-adjusted individual direction;
- simple top-25% FAIR_CENTRE WAIT filter;
- current scalar CORNERS10 football-gap direction mechanism.

The next useful research step should introduce a genuinely different pre-match direction mechanism or a more informative target structure, rather than tune this opened 31-fixture sample.

No further tuning of the current CORNERS10 formula, thresholds or league subset is allowed on these opened rows.



---

# Continuity update — 2026-09-28 — Stage-B mechanism screen completed

A bounded, zero-cost mechanism screen was completed for the proposed two-stage corner
market direction structure.

Research record:

`research/CORNER_STAGE_B_MECHANISM_SCREEN_V1.md`

No new provider odds were requested, no Supabase rows were written, and no direction
model was fitted on V2B outcomes.

Four mechanism families were screened:

- `RESULT_STRENGTH_TRAJECTORY_5`;
- `CORNER_TREND_5V5`;
- `SHOT_QUALITY_TREND`;
- `CROSS_MARKET_H2H_LEAD`.

## Selected feasibility winner

**`RESULT_STRENGTH_TRAJECTORY_5`**

Reason:

- it uses result/Elo state rather than corner-history level or opening corner-market state;
- it reuses the existing leakage-safe team-strength trajectory implementation;
- it is reconstructable from free prior completed-match data;
- it avoids reopening the formally closed SHOTS10 family;
- it does not require a new paid provider call.

Using the already-frozen V2B prior-history counts, a strict five-prior-top-flight-match
trajectory state is reconstructable for:

**34 / 43 V2B fixtures**

This is only a feasibility result. It is not a direction-accuracy result.

The 34 comes from:
- all 31 existing CORNERS10-feasible fixtures (both teams >=10 prior top-flight matches);
- plus three La Liga fixtures whose promoted/returning side has 6 prior top-flight matches;
- the remaining nine fixtures contain at least one team with only 3-4 prior top-flight matches.

## Rejected / deferred candidates

`CORNER_TREND_5V5`:
- technically available for 31/43;
- rejected as the primary next mechanism because it reuses the same corner-history family
  and is too close to post-hoc retuning of the opened CORNERS10 signal.

`SHOT_QUALITY_TREND`:
- not selected because SHOTS10 / HS-AS-HST-AST feature-family retuning is already closed;
- reopening requires genuinely richer information such as timestamp-safe true xG or
  shot-location quality.

`CROSS_MARKET_H2H_LEAD`:
- conceptually independent, but not reconstructable for V2B from current durable data;
- read-only live audit on 2026-09-28 found no rows in
  `league_h2h_bookmaker_snapshots`, only 2 EREDIVISIE rows in
  `league_multi_market_snapshots`, and top-five `odds_snapshots` ending on
  2026-09-11, before the V2B cutoff 2026-09-19.

## Current execution pointer

Next bounded block:

> reconstruct and freeze the exact 34-fixture `RESULT_STRENGTH_TRAJECTORY_5` V2B feature
> cohort without reading V2B odds, then preregister one small interpretable Stage-B mapping.

Important:
- do not inspect row-level V2B direction and then search signs/thresholds/formulas;
- any V2B direction evaluation remains hypothesis generation only;
- confirmation still requires a genuinely new unseen market cohort.


---

# Continuity update — 2026-09-28 — V2B result-strength Stage-B features frozen

The next bounded corner-direction block has been completed without opening any new
market-direction information.

Experiment:

`V2B_RESULT_STRENGTH_TRAJECTORY_FREEZE_V1`

Primary mapping:

`JOINT_PERFORMANCE_RESIDUAL_5_SIGN_V1`

Formula frozen before direction evaluation:

`stage_b_score = home_performance_residual_5 + away_performance_residual_5`

- score > 0 -> UP;
- score < 0 -> DOWN;
- score == 0 -> NO_CALL.

No fitted weights, thresholds, league-specific signs or subset search are allowed.

## Authoritative zero-cost freeze

Workflow run:

`36434578760`

Successful live-zero-cost job:

`108969276571`

Artifact:

- ID `10975465958`;
- digest `sha256:d30f4231e7e0a9149d0869ac6d775eac9d2182316593610f2b42637afc26dbe3`;
- generated at branch head `b7c5f00a458931ff9a4264aeff4754ddad81a127`.

Exact five-match eligible cohort:

**34 / 43**

By league:

- EPL 6;
- La Liga 9;
- Serie A 7;
- Bundesliga 6;
- Ligue 1 6.

Eligible fixture identity hash:

`sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1`

Frozen feature-only calls:

- UP = **16**;
- DOWN = **18**;
- NO_CALL = **0**.

These counts are not market-direction results.

## Safety proof

The successful job confirmed:

- direction test = false;
- V2B odds read = false;
- opening_lambda read = false;
- centre_delta read = false;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.

The first CI attempt found only a test-harness issue involving NaN equality in the
leakage regression. The test was corrected without weakening any research rule, and
the repeated regression run passed.

## Current execution pointer

The exact Stage-B feature cohort and sign rule are now frozen.

Next bounded block may evaluate this exact frozen mapping against the already-opened V2B
market-direction artifact, but only as **hypothesis generation**.

The evaluator must:

1. consume the exact artifact ID/digest and eligible-fixture hash above;
2. never alter the mapping after reading direction;
3. preserve all leagues and all 34 eligible fixture identities;
4. report zero movement separately from UP/DOWN-comparable rows;
5. not introduce a Stage-A threshold based on the same opened outcomes;
6. keep confirmation reserved for a genuinely new unseen cohort.

Still binding:

- FAIR_CENTRE repricing magnitude/risk = replicated;
- reliable portable direction remains unconfirmed;
- NO_BET;
- no automatic production promotion.


---

# Continuity update — 2026-09-28 — V2B result-strength Stage-B evaluated and closed

The frozen `JOINT_PERFORMANCE_RESIDUAL_5_SIGN_V1` Stage-B mapping has now been
evaluated against the already-opened V2B market rows.

Experiment:

`V2B_RESULT_STRENGTH_TRAJECTORY_EVALUATOR_V1`

Workflow run:

`36436521309`

Authoritative evaluator artifact:

- ID `10975498533`;
- digest `sha256:0cf19ad84659227ad85197c4d3e8f6453a6f67db65f213e521f35dd86c07f004`;
- exact frozen feature cohort remained 34 fixtures.

No provider call, Supabase write, model training or production promotion occurred.

## Result

Evaluated rows:

**34**

Observed V2B market movement inside those rows:

- UP = 7;
- DOWN = 3;
- ZERO = 24.

Direction-comparable rows:

**10**

Concordant:

**6 / 10 = 0.60**

Frozen consistency gate required pooled concordance **>0.60**, so this condition failed.

By league:

- Bundesliga 2/2 = 1.00;
- EPL 1/2 = 0.50;
- La Liga 1/2 = 0.50;
- Ligue 1 0/1 = 0.00;
- Serie A 2/3 = 0.6667.

Supporting leagues with >=2 comparable rows and concordance >0.50:

**2**, below the frozen requirement of >=3.

Call-group mean centre movement:

- frozen UP calls: **+0.126077**;
- frozen DOWN calls: **+0.054838**.

The DOWN group therefore moved upward on average instead of downward.

Continuous association:

- Pearson = +0.126471;
- Spearman = +0.143616.

Final classification:

**`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`**

## Binding conclusion

The exact result/Elo residual Stage-B mapping is closed on V2B.

Do not:

- reverse its sign;
- threshold its score;
- change the five-match window;
- fit weights after this result;
- exclude unfavorable leagues;
- combine it with a post-hoc Stage-A threshold on these same V2B outcomes.

The Stage-A FAIR_CENTRE repricing magnitude/risk result remains separately supported.
Reliable individual direction remains unresolved.

## Current execution pointer

Continue direction research only by introducing another genuinely independent
point-in-time information family.

Do not reopen the already-seen families by same-sample transformation:

- CORNERS10;
- SHOTS10 / HS-AS-HST-AST;
- result/Elo residual Stage B;
- FAIR_CENTRE opening-state direction.

Next step: perform another bounded **source/mechanism feasibility screen** before any
new direction outcome comparison.

Still binding:

- NO_BET;
- no automatic model promotion;
- research/training != production promotion;
- free/read-only feasibility checks before paid acquisition.


---

# Continuity update — 2026-09-28 — V2B true-xG source feasibility established

A new independent Stage-B source family has passed point-in-time source feasibility.

Experiment:

`V2B_TRUE_XG5_REPLAY_FEASIBILITY_V1`

Workflow run:

`36438275056`

Artifact:

- ID `10976063737`;
- digest `sha256:a5431c36071fe378791c7d4ace446133fcada6a5b2ba67e51b0dacea7a0de28c`.

Source:

public Understat true xG/npxG league history for 2025/26 + 2026/27.

All five source leagues/seasons were fetched without paid credentials.

## Identity and coverage

After source-driven alias normalization:

**43 / 43 V2B fixtures identity-matched**

Strict five-prior-match true-xG feasibility:

**34 / 43**

By league:

- EPL 6/9;
- La Liga 9/9;
- Serie A 7/9;
- Bundesliga 6/8;
- Ligue 1 6/8.

The nine ineligible fixtures are caused by promoted/returning clubs with only 3-4
prior top-flight xG rows. No lower-division backfill was used.

## Safety boundary

This feasibility audit did not read:

- V2B market rows;
- opening lambda / FAIR_CENTRE;
- centre_delta;
- observed direction.

It made:

- zero Odds API requests;
- zero Supabase writes;
- zero production-model operations.

Production .pkl hashes remained unchanged.

## Current execution pointer

True xG/npxG is now the preferred next Stage-B candidate because:

- it is genuinely richer than SHOTS10 counts;
- source feasibility is established across all five V2B leagues;
- exact point-in-time five-match features exist for 34 fixtures;
- no market-direction result has been used to select an xG mapping.

Next block:

> freeze one simple, interpretable xG-based total-pressure mapping for the exact
> 34-fixture xG5 cohort before any direction comparison.

Do not:

- search xG formulas after opening direction;
- fit weights on V2B;
- change league subset;
- backfill lower divisions;
- reopen closed CORNERS10/SHOTS10/result-Elo mappings.

Still binding:

- FAIR_CENTRE repricing magnitude/risk remains replicated;
- individual direction remains unresolved;
- NO_BET;
- no automatic production promotion.


---

# Continuity update — 2026-09-28 — true-xG Stage-B mapping frozen

After true-xG source feasibility passed, one mapping was frozen before opening any
new market-direction comparison.

Experiment:

`V2B_TRUE_XG_STAGE_B_FREEZE_V1`

Mapping:

`POOLED_2025_NPXG_ENVIRONMENT_SIGN_V1`

Previous-season pooled top-five baseline:

**2.8041087623 npxG**

The baseline used 3,504 completed 2025/26 Understat team-match rows across EPL,
La Liga, Serie A, Bundesliga and Ligue 1.

Frozen formula:

- expected home npxG = 0.5 * (home attack npxG5 + away npxGA5);
- expected away npxG = 0.5 * (away attack npxG5 + home npxGA5);
- joint expected npxG = sum;
- score = joint expected npxG - 2.8041087623;
- score >0 -> UP;
- score <0 -> DOWN.

No fitted weight, league-specific threshold, opening line, FAIR_CENTRE or market
direction was used.

## Frozen artifact

Workflow run:

`36442273923`

Artifact:

- ID `10978762060`;
- digest `sha256:e48adcc90274fbb06b6d915d0e1bb521d75cbcc564a86a6290f17da3cd8f189f`.

Exact cohort:

**34 / 43**

Eligible fixture hash:

`sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1`

Frozen feature hash:

`sha256:f4128f41a541788a4690bd8f1065cef468622494fe56de2a561a4ba07b59b0a5`

Frozen calls:

- UP = **30**;
- DOWN = **4**;
- NO_CALL = **0**.

This strong UP imbalance was observed from feature values only. It is not a market
result and does not authorize rebalancing or threshold adjustment.

## Current execution pointer

Next bounded block:

> evaluate the exact frozen true-xG Stage-B artifact against the already-opened V2B
> market-direction artifact.

Because the frozen calls are 30/4, the evaluator must contextualize raw concordance
rather than treating a high hit rate alone as evidence.

Still prohibited:

- change pooled baseline;
- use league-specific xG thresholds;
- switch to another xG formula after direction is opened;
- combine Stage A through a post-hoc threshold;
- claim confirmation from V2B.

Still binding:

- opened-sample evaluation only;
- NO_BET;
- no automatic production promotion.


---

# Continuity update — 2026-09-28 — true-xG Stage-B evaluated and closed

The exact frozen true-xG mapping has been evaluated on the opened V2B sample.

Experiment:

`V2B_TRUE_XG_STAGE_B_EVALUATOR_V1`

Workflow run:

`36443401120`

Artifact:

- ID `10978848942`;
- digest `sha256:966521425bbed4a589e6e1c9b59d335b519ce2a0cd7784724f895c2e64d6358c`.

## Result

Frozen rows:

**34**

Observed movement:

- UP 7;
- DOWN 3;
- ZERO 24.

Comparable non-zero movers:

**10**

Frozen mapping concordance:

**7 / 10 = 0.70**

However, frozen calls were strongly imbalanced:

- 30 UP;
- 4 DOWN.

All 10 comparable movers received an UP call. The four DOWN calls all had zero
market movement.

Therefore:

- constant-UP baseline = **7/10 = 0.70**;
- Stage-B excess over constant UP = **0.00**;
- UP recall = 1.00;
- DOWN recall = 0.00;
- balanced accuracy = **0.50**.

Frozen DOWN-call mean centre_delta:

**0.000000**, not negative.

Continuous score relationship:

- Pearson = +0.325976;
- Spearman = +0.097325.

Final classification:

**`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`**

## Binding conclusion

Close `POOLED_2025_NPXG_ENVIRONMENT_SIGN_V1`.

Do not retune:

- pooled baseline;
- xG/npxG weights;
- horizon;
- league subset;
- call balance;
- Stage-A threshold.

The 7/10 raw number is not a direction edge because it exactly equals the constant-UP
baseline and provides no DOWN discrimination.

Reliable individual direction remains unresolved.

## Current execution pointer

The following Stage-B families are now closed on this opened V2B sample:

- scalar CORNERS10 football-gap;
- result/Elo residual mapping;
- absolute true-npxG environment mapping.

SHOTS10 same-family retuning was already closed.

Next work should be a **new source/time-provenance feasibility screen**, not another
formula search on these families.

Priority candidates:

1. genuinely point-in-time squad availability / confirmed lineup state, if a historical
   first-seen source exists;
2. full-calendar congestion/travel including cup and European fixtures, not league-only
   rest proxies;
3. pre-match corner-market microstructure from independent books, if the existing locked
   raw V2B artifact already contains cross-book information at the relevant timestamp.

Do free/read-only source audits before any new paid acquisition.

Still binding:

- FAIR_CENTRE repricing magnitude/risk remains replicated;
- individual direction remains unconfirmed;
- NO_BET;
- no automatic production promotion.


---

# Continuity update — 2026-09-28 — Understat tactical-pressure source feasible

A new independent source family has passed point-in-time feasibility.

Experiment:

`V2B_UNDERSTAT_TACTICAL_PRESSURE5_FEASIBILITY_V1`

Workflow run:

`36444258107`

Artifact:

- ID `10979534783`;
- digest `sha256:c44f2494d53e627c04aa21b5cc6d733fd4d7373004e959f77892b6af9c9d77a2`.

Source:

public Understat prior-match:

- deep;
- deep_allowed;
- PPDA;
- PPDA_allowed.

All required fields were present across EPL, La Liga, Serie A, Bundesliga and Ligue 1.

## Coverage

Identity:

**43 / 43 matched**

Strict five-prior-tactical-match feasibility:

**34 / 43**

By league:

- EPL 6/9;
- La Liga 9/9;
- Serie A 7/9;
- Bundesliga 6/8;
- Ligue 1 6/8.

The same nine promoted/returning fixtures remain below five prior top-flight rows.
No lower-division backfill was used.

## Method safety

Snapshots use only rows strictly before target kickoff.

PPDA dicts are normalized as `att / def` with finite positive denominator; malformed
values fail closed.

No V2B market row, opening line, FAIR_CENTRE, centre_delta or observed direction was read.

## Current execution pointer

The source is suitable for one separately frozen Stage-B hypothesis.

Next bounded block:

> freeze one simple and interpretable tactical-pressure mapping for the exact 34-fixture
> cohort before opening direction.

Important:

- lower PPDA means more aggressive pressing, so orientation must be frozen explicitly;
- no fitted weights;
- no league-specific threshold;
- no outcome-based feature selection;
- no Stage-A threshold selection on V2B.

Still binding:

- scalar CORNERS10 Stage B = closed;
- result/Elo Stage B = closed;
- absolute true-npxG Stage B = closed;
- SHOTS10 same-family tuning = closed;
- FAIR_CENTRE repricing magnitude/risk = replicated;
- reliable direction remains unconfirmed;
- NO_BET;
- no automatic production promotion.


---

# Continuity update — 2026-09-28 — territorial-depth Stage-B frozen

After tactical-pressure source feasibility passed, one primary mapping was frozen before
opening any new V2B direction comparison.

Experiment:

`V2B_DEEP_STAGE_B_FREEZE_V1`

Mapping:

`POOLED_2025_DEEP_ENVIRONMENT_SIGN_V1`

PPDA was deliberately excluded from the primary mapping to avoid mixing an inverse
pressure metric with absolute deep counts without an independent normalization contract.

## Frozen artifact

Workflow run:

`36448872259`

Artifact:

- ID `10982056918`;
- digest `sha256:e92112d98805a06e2452ce70c365735c2a2dd308a7a62be66b1081182fa7f812`.

Pooled completed-2025/26 top-five baseline:

**12.8561643836 deep environment**

from **3,504** valid team-match rows.

Exact cohort:

**34 / 43**

Eligible fixture hash:

`sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1`

Frozen feature hash:

`sha256:7d114e4fb36ef08dc9e2e7998bc4560ea1b10b28e6296743a68ca08bb073b483`

Frozen calls:

- UP = **28**;
- DOWN = **6**;
- NO_CALL = **0**.

This imbalance was observed before market direction and must not be corrected post-hoc.

## Current execution pointer

Next bounded block:

> evaluate this exact frozen deep/deep_allowed mapping against the already-opened V2B
> market-direction artifact.

The evaluator must include a constant-UP comparison and balanced-direction diagnostics so
that an imbalanced 28/6 call distribution cannot create a misleading raw hit rate.

Still prohibited:

- move baseline;
- switch to PPDA;
- fit weights;
- change horizon;
- exclude leagues;
- add Stage-A threshold from the same V2B outcomes.

Still binding:

- opened-sample hypothesis generation only;
- FAIR_CENTRE repricing magnitude/risk remains replicated;
- reliable individual direction remains unconfirmed;
- NO_BET;
- no automatic production promotion.

---

# Continuity update — 2026-09-29 — territorial-depth Stage-B evaluated and closed

The exact frozen `POOLED_2025_DEEP_ENVIRONMENT_SIGN_V1` mapping has now been
evaluated against the already-opened V2B market-direction artifact.

Experiment:

`V2B_DEEP_STAGE_B_EVALUATOR_V1`

Workflow run:

`36579933258`

Artifact:

- ID `11039795640`;
- digest `sha256:6bb5aa4131189a518b3e57a2878c615d67a2afe0e75ceb1d4c57975d6ee382f3`.

## Result

Frozen rows:

**34**

Observed movement:

- UP = 7;
- DOWN = 3;
- ZERO = 24.

Comparable non-zero movers:

**10**

Frozen deep mapping:

**6 / 10 = 0.60**

Constant always-UP baseline:

**7 / 10 = 0.70**

Stage-B excess over always-UP:

**-0.10**

Direction discrimination:

- UP recall = 0.8571;
- DOWN recall = 0.0000;
- balanced accuracy = **0.4286**.

Frozen DOWN-call group:

- 6 rows;
- 5 ZERO;
- 1 observed UP;
- 0 observed DOWN;
- mean centre_delta = **+0.136056**, not negative.

Continuous relationship:

- Pearson = -0.005102;
- Spearman = +0.100145.

Final classification:

**`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`**

## Binding conclusion

Close `POOLED_2025_DEEP_ENVIRONMENT_SIGN_V1`.

Do not:

- move the pooled deep baseline;
- switch to PPDA on this sample;
- reverse the sign;
- fit weights or a threshold;
- change the five-match horizon;
- drop unfavorable leagues;
- add a post-hoc Stage-A threshold.

The 6/10 raw result is worse than the 7/10 constant-UP baseline and provides no DOWN
discrimination.

## Current execution pointer

Reliable individual direction remains unresolved.

Closed opened-sample Stage-B families now include:

- CORNERS10 scalar gap;
- result/Elo residual;
- absolute true-npxG environment;
- absolute deep/deep_allowed environment;
- SHOTS10 same-family tuning.

Next bounded direction block should be a **new source/time-provenance feasibility audit**,
not another formula search on these opened feature families.

Priority:

1. inspect immutable raw V2B response structure for cross-book / market-microstructure
   information already paid for and already stored;
2. if insufficient, inspect full-calendar congestion/travel source feasibility;
3. keep availability externally gated unless a genuine point-in-time first-seen source
   becomes available.

Still binding:

- FAIR_CENTRE repricing magnitude/risk remains replicated;
- individual direction remains unconfirmed;
- NO_BET;
- no automatic production promotion.


---

# Continuity update — 2026-09-29 — existing V2B cross-book path closed

The immutable raw V2B odds artifact has now been audited directly for bookmaker diversity.

Experiment:

`V2B_CROSS_BOOK_RAW_FEASIBILITY_V1`

Workflow run:

`36582565629`

Audit artifact:

- ID `11040276332`;
- digest `sha256:e8f83be1ed950b53d32788b921b678971d8cb7bc4d8d4cf38a46104aea8626e2`.

Immutable raw source:

- artifact `10899611444`;
- digest `sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`.

## Result

Raw responses:

**43 / 43**

Bookmaker-count distribution:

- 1 bookmaker = **43**;
- >=2 bookmakers = **0**.

Unique bookmaker:

**Bet365**

Bet365 coverage:

**43 / 43**

All 43 have Bet365 corner opening, closing and in-play structures, but these are states
of one bookmaker and are not cross-book microstructure.

Final status:

**`INSUFFICIENT_CROSS_BOOK_DIVERSITY`**

No direction target or centre_delta was read.

No provider request, Supabase write or production model operation occurred.

## Binding conclusion

The already-paid V2B raw artifact cannot support:

- bookmaker disagreement;
- consensus-vs-sharp;
- leader/laggard book;
- cross-book dispersion;
- multi-book direction.

Do not create a synthetic second bookmaker from Bet365 or its opening/closing states.

A future cross-book experiment would require a different source that demonstrably returns
>=2 independent bookmaker corner lines at the same timestamp.

## Current execution pointer

Move to the next independent zero-cost source feasibility block:

> full-calendar congestion / recovery / travel, including domestic cups and European
> fixtures where point-in-time historical schedules are available.

Do source coverage/time provenance first. Do not define a direction sign until feasibility
is established.

Still binding:

- FAIR_CENTRE repricing magnitude/risk remains replicated;
- individual direction remains unconfirmed;
- CORNERS10 / SHOTS10 / result-Elo / absolute npxG / absolute deep Stage-B mappings are closed;
- existing V2B cross-book path is now also closed;
- NO_BET;
- no automatic production promotion.

---

# Continuity update — 2026-09-29 — full-calendar congestion source feasible

The exact V2B 14-day pre-match calendar has now been reconstructed with materially more
complete information than the old league-only schedule proxy.

Experiment:

`V2B_FULL_CALENDAR_LOAD_FEASIBILITY_V1`

Workflow run:

`36586153137`

Artifact:

- ID `11041174634`;
- digest `sha256:366ac99df321757c0a12bf306c0bbef0512632adb29023c7b5465b06dc61be87`.

## Exact scope

Targets:

19–20 September 2026.

Lookback:

**14 days strictly before target date.**

League source:

Understat 2026/27.

Frozen official non-league manifest:

- UEFA Champions League;
- UEFA Europa League;
- Carabao Cup;
- relevant Coppa Italia fixtures.

Other top-five domestic/UEFA competitions were explicitly checked against their official
2026/27 calendars and fall outside this exact target window.

## Result

Identity matched:

**43 / 43**

Full-calendar feasible:

**43 / 43**

Final status:

**`FULL_43_RECONSTRUCTABLE_14D`**

The source change is material:

- 42/86 team-sides have >=1 non-league event in the 14-day window;
- 27/43 V2B fixtures change their load profile vs league-only;
- 25/86 team-sides have a different most-recent-match date;
- mean rest reduction among those changed sides = 3.84 days;
- home-minus-away rest differential changes in 15/43 fixtures.

Changed V2B fixtures by league:

- EPL 9/9;
- La Liga 6/9;
- Serie A 6/9;
- Bundesliga 3/8;
- Ligue 1 3/8.

## Binding interpretation

The prior negative league-only `SCHEDULE_V1` experiment does not close this family.
The full-calendar source contains genuinely new information that the old experiment did
not have.

Do not yet claim direction value.

No centre_delta, market row or V2B direction outcome was read.

## Current execution pointer

Next bounded block:

> freeze one simple full-calendar recovery/load Stage-B mapping before any direction join.

Requirements:

- use only frozen full-calendar load fields;
- no fitted weights;
- no post-outcome choice between 7d/14d windows;
- no league-specific threshold;
- no FAIR_CENTRE combination;
- keep travel separate until venue/distance provenance is audited.

Still binding:

- FAIR_CENTRE repricing magnitude/risk remains replicated;
- reliable individual direction remains unconfirmed;
- CORNERS10 / SHOTS10 / result-Elo / absolute npxG / absolute deep Stage-B mappings are closed;
- existing V2B cross-book path is closed;
- NO_BET;
- no automatic production promotion.


---

# Continuity update — 2026-09-29 — full-calendar recovery Stage-B frozen

The new full-calendar congestion source has now been converted into one frozen
outcome-blind Stage-B hypothesis.

Experiment:

`V2B_FULL_CALENDAR_REST_STAGE_B_FREEZE_V1`

Mapping:

`JOINT_FULL_REST_COHORT_MEDIAN_SIGN_V1`

Workflow run:

`36588058549`

Artifact:

- ID `11042123742`;
- digest `sha256:5157a50d2516aa7088eb1c89a0b95e8d31a8c328a6c0b8ee4488489ee8559918`.

## Frozen mapping

For each of all 43 V2B fixtures:

`joint_full_rest_days = home_full_rest_days + away_full_rest_days`

Feature-only cohort median:

**11.0 days**

`stage_b_score = joint_full_rest_days - 11.0`

- positive -> UP;
- negative -> DOWN;
- zero -> NO_CALL.

Frozen calls:

- UP = **17**;
- DOWN = **19**;
- NO_CALL = **7**.

Fixture identity hash:

`sha256:c2891591d871b3ad8432915761f90065f6941f9055204d4d0b5327d71e4e52ea`

Frozen feature hash:

`sha256:d876b37f9315a535a0a92ef9ff2f06e62a3c70321c96982ba6395ec7be5feec6`

## League distribution

- EPL: 1 UP / 8 DOWN / 0 NO_CALL;
- La Liga: 0 UP / 8 DOWN / 1 NO_CALL;
- Serie A: 4 UP / 1 DOWN / 4 NO_CALL;
- Bundesliga: 6 UP / 0 DOWN / 2 NO_CALL;
- Ligue 1: 6 UP / 2 DOWN / 0 NO_CALL.

This heterogeneity is frozen, not corrected.

Do not introduce league-specific medians or a different load feature after direction is
opened.

## Safety proof

The freeze read no V2B market row, opening line, FAIR_CENTRE or centre_delta.

No Odds API request, Supabase write, model training or production promotion occurred.

## Current execution pointer

Next bounded block:

> evaluate the exact frozen 43-fixture full-calendar rest Stage-B artifact against the
> already-opened V2B market-direction artifact.

Required:

- preserve exact 17/19/7 calls;
- keep NO_CALL and ZERO movement separate;
- compare against constant directions on the same comparable subset;
- report UP/DOWN recall, balanced accuracy, by-league results and continuous association;
- no threshold/sign/window/league change.

Still binding:

- opened-sample hypothesis generation only;
- FAIR_CENTRE repricing magnitude/risk remains replicated;
- reliable individual direction remains unconfirmed;
- NO_BET;
- no automatic production promotion.


---

# Continuity update — 2026-09-29 — full-calendar rest Stage-B evaluated and closed

The exact frozen `JOINT_FULL_REST_COHORT_MEDIAN_SIGN_V1` mapping has now been evaluated
against the already-opened V2B market-direction artifact.

Experiment:

`V2B_FULL_CALENDAR_REST_STAGE_B_EVALUATOR_V1`

Workflow run:

`36589336181`

Artifact:

- ID `11042867553`;
- digest `sha256:f45c216801e991d1629ecba347cc522360aa55059b142dbe6b70cf11b570810b`.

## Result

All rows:

**43**

Frozen calls:

- UP 17;
- DOWN 19;
- NO_CALL 7.

Observed movement:

- UP 9;
- DOWN 4;
- ZERO 30.

Direction-comparable rows after excluding frozen NO_CALL and observed ZERO:

**12**

Frozen rest mapping:

**7 / 12 = 0.5833**

Constant always-UP baseline on the same comparable subset:

**8 / 12 = 0.6667**

Stage-B excess:

**-0.0833**

Direction discrimination:

- UP recall = 0.625;
- DOWN recall = 0.500;
- balanced accuracy = **0.5625**.

Frozen call-group means:

- UP mean centre_delta = **+0.100342**;
- DOWN mean centre_delta = **+0.026434**.

The DOWN group mean has the wrong sign.

Continuous association:

- Pearson = +0.102621;
- Spearman = +0.078583.

Supporting leagues with >=2 comparable and concordance >0.50:

**3**

But pooled concordance and sign-alignment conditions fail.

Final classification:

**`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`**

## Binding conclusion

Close `JOINT_FULL_REST_COHORT_MEDIAN_SIGN_V1` on opened V2B.

Do not:

- move the 11-day threshold;
- introduce league-specific medians;
- reverse sign;
- switch to home-away rest differential;
- select 7d/14d counts;
- reassign NO_CALL;
- weight competitions;
- exclude unfavorable leagues;
- combine with FAIR_CENTRE post hoc.

The full-calendar source remains a valid and materially improved schedule reconstruction,
but this exact directional mechanism is not supported.

## Current execution pointer

Reliable individual direction remains unresolved.

Next bounded research block should use a genuinely different source family, not another
rest/congestion transformation on the opened V2B outcomes.

Priority candidates:

1. travel/venue burden with independently audited geography/distance provenance;
2. point-in-time squad availability / confirmed lineup state if a first-seen historical
   source becomes available.

Still binding:

- FAIR_CENTRE repricing magnitude/risk remains replicated;
- full-calendar schedule source is feasible;
- exact joint-rest direction mapping is closed;
- NO_BET;
- no automatic production promotion.


---

# Continuity update — 2026-09-29 — travel venue identity fully feasible

The first travel-specific source layer is now complete without using coordinates or
market outcomes.

Experiment:

`V2B_TRAVEL_VENUE_IDENTITY_FEASIBILITY_V1`

Workflow run:

`36591494472`

Artifact:

- ID `11044111558`;
- digest `sha256:8c895a500169760c1fe36fe5eeb40861d06d2aa23a4b26e15d3f580f3243837b`.

## Result

Immediately previous competitive fixture:

**86 / 86 team-sides resolved**

Both sides resolved:

**43 / 43 V2B fixtures**

Final status:

**`FULL_86_VENUE_IDENTITY_FEASIBLE`**

Previous fixture was away:

**39 / 86 sides**

Immediately previous fixture was non-league:

**25 / 86 sides**

Previous venue identity differs from target venue identity:

**72 / 86 sides**

The only first-pass identity gap was Rayo Vallecano because Football-Data uses
`Vallecano`. Adding that alias alone closed coverage from 85/86 to 86/86.

## Interpretation

For every frozen V2B team-side we now have a deterministic route identity:

`previous fixture venue -> target fixture venue`

This does not yet represent kilometers.

Do not infer distance from club-label inequality.

## Current execution pointer

Next bounded block:

> audit public stadium/club coordinate coverage for the exact unique venue identities
> present in the frozen route artifact.

Requirements:

- freeze coordinate source provenance;
- distinguish stadium coordinates from city-level fallback;
- report ambiguous/unresolved labels;
- no market rows or direction outcomes;
- no travel-direction formula until coordinate coverage is fixed.

Still binding:

- full-calendar aggregate-rest Stage B is closed as weak/inconsistent;
- FAIR_CENTRE repricing magnitude/risk remains replicated;
- reliable individual direction remains unconfirmed;
- NO_BET;
- no automatic production promotion.


---

# Continuity update — 2026-09-29 — exact stadium coordinate layer complete; travel direction remains closed

The exact travel route identities are now fully mapped to stadium-level coordinates
without using market direction.

Experiment:

`V2B_TRAVEL_COORDINATE_FEASIBILITY_V1`

Workflow run:

`36596063770`

Coordinate artifact:

- ID `11046082462`;
- digest `sha256:f6b334614adde392ad9195c00c883ecf2d1e4d5f1d810b87e86c4d21ae549b02`.

Immutable route source:

- `V2B_TRAVEL_VENUE_IDENTITY_FEASIBILITY_V1`;
- artifact `11044111558`;
- digest `sha256:8c895a500169760c1fe36fe5eeb40861d06d2aa23a4b26e15d3f580f3243837b`.

## Coordinate result

Unique previous/target venue labels:

**93**

Stadium coordinates:

**93 / 93**

Club-coordinate fallbacks:

**0**

Ambiguous active venues:

**0**

Unresolved club identities:

**0**

Team-side routes with both endpoints resolved at stadium level:

**86 / 86**

Fixtures with both teams fully coordinate-feasible:

**43 / 43**

Final status:

**`FULL_86_STADIUM_COORDINATE_FEASIBLE`**

The final audit used batched English-Wikipedia pageprops -> Wikidata QID resolution,
then Wikidata club P115 -> stadium P625. Only 6 public HTTP requests were required.

Five generic English title collisions were disambiguated as football-club titles:
Chelsea, Crystal Palace, Everton, Fulham and Liverpool.

SC Freiburg required one source-backed current-venue override to
Europa-Park-Stadion (`Q64586775`) because Wikidata exposed two active
coordinate-bearing P115 values. OpenFootball independently identifies
Europa-Park-Stadion as SC Freiburg's current home.

No market row, centre_delta or direction target was read by this coordinate audit.

## Parallel travel-direction result now binding

While the coordinate audit was running, `main` independently completed the
city-centroid travel Stage-B path.

Frozen mapping:

`JOINT_TRAVEL_CITY_COHORT_MEDIAN_SIGN_V1`

Opened-sample result:

- comparable rows = **13**;
- concordant = **4 / 13 = 30.77%**;
- constant-UP baseline = **9 / 13 = 69.23%**;
- excess vs constant-UP = **-38.46 pp**;
- UP recall = **33.33%**;
- DOWN recall = **25.00%**;
- balanced accuracy = **29.17%**;
- final = **`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`**.

Therefore travel as an opened-sample corner-direction family is closed.

Do not use the improved stadium coordinates to:

- tune a new travel threshold on V2B;
- reverse the travel sign;
- switch to away-only/max travel;
- add a travel/rest interaction;
- choose favorable leagues;
- combine travel with FAIR_CENTRE post hoc.

## Current execution pointer

Exact stadium Haversine distances may still be computed as reusable infrastructure for
future unseen cohorts, but not as another direction test on the already-opened V2B sample.

For current direction research, move to a genuinely different information family
before any outcome join.

Preferred next source-feasibility direction:

1. **time-aligned market-path structure** using genuinely pre-move historical states if a
   durable source exists;
2. **cross-market relationships** from independent point-in-time markets if their
   timestamps and source coverage can be proven;
3. otherwise wait for an **unseen prospective cohort** rather than re-engineer opened
   travel/schedule features.

Still binding:

- FAIR_CENTRE repricing magnitude/risk remains replicated;
- individual corner-market direction remains unconfirmed;
- full-calendar rest and travel-city directional mappings are closed;
- exact stadium coordinate layer is infrastructure only on opened V2B;
- NO_BET;
- no automatic production promotion.


---

# Continuity update — 2026-10-02 — V2B raw source cannot support time-aligned corner paths

A dedicated structural audit of the already-paid V2B raw corner artifact is complete.

Experiment:

`V2B_CORNER_MARKET_PATH_SOURCE_AUDIT_V1`

Workflow run:

`37025543210`

Artifact:

- ID `11234538332`;
- digest `sha256:7b7be3476112b6f1cb2811d5d249c9cfb3f8bebc72c2752f47b533e07e4461d8`.

Immutable raw source:

- artifact `10899611444`;
- digest `sha256:c2f5313efad4afb8663d9980f5ea004f52fe02827a83b5c99a8b775c35498a57`.

## Structural finding

Across all 43 V2B raw corner payloads:

- exactly one bookmaker = **43/43**;
- bookmaker = Bet365 in **43/43**;
- `corner_line.opening` present = **43/43**;
- `corner_line.closing` present = **43/43**;
- `corner_line.inplay` present = **43/43**;
- timestamp/date/update fields = **0/43**;
- history/snapshot/timeline/sequence fields = **0/43**;
- multiple bookmakers = **0/43**.

Final status:

**`NO_TIME_ALIGNED_PATH_SOURCE`**

## Binding interpretation

The V2B endpoint artifact cannot be used to construct honest pre-move path features.

Do not derive or claim:

- slope;
- speed;
- acceleration;
- early path volatility;
- revision count;
- time since last move;
- cross-book dispersion;
- bookmaker lead/lag.

`closing` and `inplay` are not permissible substitutes for timestamped pre-decision
observations.

No new provider request is justified for the same endpoint payloads.

## Existing 1X2 path experiment

`PROSPECTIVE_MARKET_PATH_V1` remains separately frozen and active for timestamped 1X2
snapshots. It must not be expanded with new corner-path features.

## Current execution pointer

The next useful zero-cost block is source feasibility for a **new prospective corner-path
collector**, not retrospective engineering on V2B.

Before defining any Stage-B direction rule, prove whether current multi-market corner
infrastructure can persist repeated timestamped observations containing:

- fixture identity;
- observation timestamp;
- bookmaker;
- corner line;
- over/under prices;
- at least three pre-kickoff observations across a useful span.

If that prospective source is unavailable, move to another independent information
family rather than reuse opened schedule/travel/xG/deep features.

Still binding:

- FAIR_CENTRE repricing magnitude/risk remains replicated;
- reliable individual corner-market direction remains unconfirmed;
- rest and travel directional mappings are closed on opened V2B;
- exact stadium coordinate layer is infrastructure only;
- V2B raw endpoint source has no time-aligned path;
- NO_BET;
- no automatic production promotion.

---

# Continuity update — 2026-10-04 — six remaining corner signal families closed

Experiment:

`CORNER_SIX_SIGNAL_SCREEN_V1`

Authoritative workflow run:

`37179398571`

Artifact:

- ID `11294063833`;
- digest `sha256:92b958e6f5f8c911236f5e6451ed2f974d4e02af727637644dc2ad037cd78aa0`.

Evidence:

- V1_55 = 55;
- REP50 = 50;
- V1_46 = 46;
- V2B_43 = 43;
- total = **194 unique already-opened corner-market fixtures**.

No new prospective fixture collection occurred.

## Final six-family verdicts

1. `OPENING_PRICE_PRESSURE_DIRECTION_V1`
   -> **`NO_PORTABLE_OPENING_PRICE_PRESSURE_DIRECTION_SIGNAL`**

   Pooled comparable 73, balanced accuracy 43.16%, Spearman -0.1101,
   majority-direction baseline 79.45% vs signal raw accuracy 41.10%.

2. `OPENING_PRESSURE_LINE_TRANSITION_V1`
   -> **`NO_LINE_TRANSITION_MECHANICS_SIGNAL`**

   Actual line-step balanced accuracy 58.05%, but any-line-move AUC only 0.4792 and only
   2/4 cohorts were directionally positive. Not portable.

3. `CROSS_MARKET_MATCH_SHAPE_CORNER_GAP_V1`
   -> **`PROMISING_CROSS_MARKET_CORNER_DIRECTION_SIGNAL`**

   Historical match-shape corner-count model won 2025/26 MAE vs league mean in 3/3:
   EPL, La Liga, Serie A.

   On saved corner cohorts:
   - 117 usable rows;
   - 56 non-zero comparable direction rows;
   - balanced accuracy = 66.06%;
   - pooled Pearson = +0.6815;
   - pooled Spearman = +0.6239;
   - Spearman positive in 4/4 cohorts.

   Critical caveat:
   raw accuracy = 78.57% vs always-UP majority = 80.36%.
   DOWN recall = 45.45%, and V2B DOWN recall = 0%.

   Therefore this is a **promising rank/direction hypothesis**, not a confirmed betting
   edge or a 78.6% accuracy claim.

4. `REFEREE_CORNER_BIAS_DIRECTION_V1`
   -> **`NO_PORTABLE_REFEREE_CORNER_SIGNAL`**

   Historical referee model failed even in EPL; referee field absent in La Liga and
   Serie A source files. Current small direction diagnostic cannot override that gate.

5. `CORNER_ENV_VOLATILITY_INCREMENTAL_REPRICING_V1`
   -> **`NO_INCREMENTAL_VOLATILITY_REPRICING_SIGNAL`**

   Eligible 84.
   Volatility-vs-movement Spearman -0.0122.
   FAIR_CENTRE+volatility lost Brier and LogLoss in **0/4** held-out cohorts.
   Pooled deltas: +0.00548 Brier, +0.01224 LogLoss.

6. `COACH_LINEUP_AVAILABILITY_REGIME_CHANGE_V1`
   -> **`EXISTING_SOURCE_DATA_GAP_FOR_REGIME_CHANGE_SIGNAL`**

   Existing Football-Data schemas expose no manager/coach/lineup/injury/suspension
   point-in-time fields. Existing prospective availability lab remains externally gated
   and retrospective injury reconstruction remains prohibited.

## Binding interpretation

Only family #3 survives this retrospective screen.

Do not retune #3 on these opened 2026/27 corner movement cohorts:

- no sign reversal;
- no league selection;
- no threshold search;
- no dropping V2B;
- no coefficient fitting to centre_delta;
- no claim of tradable edge.

#1, #2, #4 and #5 are closed for same-sample feature/window/sign retuning.

#6 is source-gated rather than empirically rejected.

## Current execution pointer

For research without new data collection:

- preserve `CROSS_MARKET_MATCH_SHAPE_CORNER_GAP_V1` as the best surviving Stage-B
  hypothesis;
- do not call it confirmed;
- any further work on existing opened corner cohorts should be limited to method/safety
  documentation, not tuning;
- independent confirmation requires untouched evidence when the user later chooses to
  resume new-data work.

Still binding:

- FAIR_CENTRE repricing magnitude/risk remains the strongest confirmed Stage-A signal;
- individual Stage-B direction is not yet independently confirmed;
- NO_BET;
- no automatic production promotion.

---

# Continuity update — 2026-10-07 — multi-market 1X2 repricing representation closed

Research program:

`multi_market_repricing_state`

Child Issue:

`#573 — Multi-market state -> future 1X2 repricing vector`

Deterministic V5 result:

**`NO_STABLE_MULTI_MARKET_REPRICING_SIGNAL`**

## Frozen design

The experiment compared an identical temporal Ridge pipeline on exactly the same fixtures:

- baseline: Bet365 STANDARD/PRE-CLOSE 1X2 state only;
- candidate: the same 1X2 state plus O/U 2.5 and Asian Handicap state;
- target: later Bet365 closing 1X2 repricing in two log-ratio coordinates;
- reference: 2019/20–2023/24;
- validation: 2024/25;
- retrospective test: 2025/26;
- five leagues: EPL, La Liga, Serie A, Bundesliga, Ligue 1;
- no match outcomes;
- no paid API;
- no Supabase writes;
- no production operation or promotion.

All five leagues passed the preregistered zero-cost source/coverage gate.

## Validation 2024/25

Candidate minus 1X2-only baseline:

- MSE = **-0.00005356** (better);
- MAE = **+0.00016130** (worse).

Therefore the validation gate was already not fully passed.

## Retrospective test 2025/26

Candidate minus baseline:

- MSE = **-0.00007956** (better);
- MAE = **-0.00011262** (better);
- league-stratified 5,000-draw bootstrap 95% CI for MSE delta =
  **[-0.00015624, -0.00000395]**.

However the cross-league stability gate failed:

- Bundesliga MSE delta = **+0.00008991**;
- EPL = **+0.00005737**;
- Ligue 1 = **+0.00006907**;
- La Liga = **-0.00016175**;
- Serie A = **-0.00039097**.

The candidate worsened MSE in **3 of 5 leagues**, while the frozen contract allowed at most one.

## Binding interpretation

The pooled effect is interesting but not portable enough to count as a stable signal.

Do not rescue #573 on the same opened history by:

- adding corner-market state;
- selecting only La Liga / Serie A;
- changing Ridge alpha;
- changing the market feature subset;
- changing AH line scope;
- changing target coordinates;
- mining sign thresholds;
- reversing signs or dropping unfavorable leagues.

Historical closing targets through 2025/26 were already opened by related research, so they cannot be reused for iterative tuning.

Parent program status:

**`PROGRAM_DONE`**

Product status:

**NO_BET**

A future restart requires genuinely new prospectively frozen information or a new independent research question.

## 2026-10-08 — WEBSITE_H2H_BATCH_BUDGET_DRY_RUN_V1

- User corrected prior false source blocker: The Odds API league-wide H2H endpoint already batches **all provider-offered future fixtures of one league into one 1-market/1-region request** (typical one-credit cost). No new odds provider is necessary for this feature; coverage horizon is provider-limited.
- P0 #579 source root cause: paid odds snapshot GitHub Actions remain intentionally **manual-only**; API budget guard preserves 100-credit reserve. The last live market snapshot was 2026-09-11, and at 2026-10-08 read-only check there were 0 future EPL/product snapshots; the existing AI product bridge correctly cannot create future rows from absent markets.
- Implementation P1 #580: PR #591 merged exact-head after **7/7 required PR workflows PASS**, source head `9bbd2689c8fa4a5580c89544cf757cfd8e076738`, merge main `3877cc1bfa49ebb7dd3749e3e6e13860f92ba0fb`.
- New `odds_h2h_batch_dry_run.py` + `tests/test_odds_h2h_batch_dry_run.py` and Provider Budget PR Validation wiring. Plan is **OFFLINE_DRY_RUN_ONLY**; no API, Supabase, model or deployment operations. EPL-first Monday/Friday 12 UTC candidate windows; one league-wide `uk/h2h` quote batch costs max 1 credit; shared provider billing-cycle ceiling 80 used credits counts all consumers; existing 100 hard reserve, verified counter and >=48h gap requirements. Optional other leagues are preview-only.
- Critical contract: PR #591 **does not add cron to paid collectors or authorize a single paid call**. `.github/workflows/odds-snapshots.yml` and tests continue to forbid automatic paid collection. The dry-run cap is independent of real provider usage and is not proof that quota is currently available. The website's real upcoming AI predictions remain blocked until point-in-time odds return via a separately approved paid collection path.
- Autonomous ChatGPT Website Builder and Research Brain hourly tasks reenabled on 2026-10-08 following user request. Their activation does not authorize paid calls and does not reopen closed frozen research programs (#584/#585 remain blocked by independent source/provenance).
- Next engineering pointer: safe P1 follow-up plan for **explicit, bounded user-authorized paid activation** if desired; meanwhile continue independent read-only public API freshness/unknown states #581, front-end #582 and historical track record #583. No public Vercel production release without separate gate.
- Evidence: https://github.com/MaksimBlud/football-ai/pull/591 ; https://github.com/MaksimBlud/football-ai/issues/580 .


## 2026-10-10 — WEBSITE_MOBILE_MATCH_CARDS_V1, PR #601

- User identified a ~13-hour gap with no merged code and an unexpectedly disabled Frontend Builder. Frontend automation `6ac90b5ada548191a43bf8f06f610a98` was re-enabled on 2026-10-10 and retargeted to mobile match-detail UX; backend remains separate on #581 and PR #598.
- PR [#601](https://github.com/MaksimBlud/football-ai/pull/601) introduced real responsive match cards in `static/index_v2.html` for screens <=900px, three 1X2 outcome probabilities and already-saved bookmaker odds, a stable match-detail link, focus-visible navigation, fail-closed loading/error states and explicit data-source/freshness honesty: the public contract does not supply the market snapshot timestamp, so prices are labelled as saved, **not live**. No browser-side recalc of odds/EV. Tests in `tests/test_product_ui_contract.py` cover mobile, provenance warnings, keyboard links, and Node JS syntax.
- CI: **6/6 required PR workflows PASS** on exact source head `ff253530d3c532d437670ea3baf766a9a7f30e12` (Product, Research, Serie A, Bundesliga, Eredivisie, Ligue 1). Fresh `main` before merge `668f1841a753993478c2070b395eebb409581ae7`; PR clean/mergeable. Exact-head squash merged to `main` **`0ebec4089df38d7dc1922dd014073b71412b70e9`**.
- Independent Vercel **preview** `dpl_5YnYbaEEsqJBcvwjHc7tL3yqU7BW` READY: https://football-ai-real-epl-snapshot-pvrf0iym3-max-7d3e.vercel.app/ . HTTP home 200 with new card/freshness code; `/product-market-view` HTTP 200 with 20 matches, 20 model forecasts, 20 priced events. No production deployment done: stable production alias https://football-ai-real-epl-snapshot-max-7d3e.vercel.app/ remained READY at older SHA `202d46796f031caa0c9d7138c402eefb0cc56971`. A production release requires separate explicit authorization.
- Live Supabase read-only proof 2026-10-10: 20 future EPL odds snapshots across 20 events, 20 public model-prediction snapshots, 20 AI/market pairs; newest paid-provider market snapshot is `2026-10-09T15:25:57Z`. The separately user-authorized single H2H request spent **one** The Odds API credit; **499/500** remained at the last provider preflight. That consent is exhausted; **no additional paid API calls or paid cron** without a new explicit authorization (hard reserve >=100).
- Next: Frontend Builder owns responsive `static/match.html` and #582; Backend Builder handles #581 / PR #598 with as-of paging/atomic consistency caveats. Research Brain and Signal Scout separately validate independent new signal ideas. No model `.pkl` changes, promotion, research frozen gate relaxation, live DB writes, or production Vercel promotion.


## 2026-10-27 06:49 UTC — fresh pre-match odds audit and V2 PR coordination

- Fresh source of truth checked in this run: `main` is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The current-form source-capture workflow on that SHA still watches only its own script, policy, source test, and workflow file on `push`; it does not yet re-run on all imported frozen/runtime dependencies. Current open, exact-head CI-green candidates are #696 (`2a4059860fcb7da2eab39b538b4e264ef6fc8192`) for original-forward/source triggers and #698 (`5678cb090cb19ebba67e2fb31edd35c6c7fe9938`) for current-form forward triggers. Older #681 (`fcc867ed3d5e10d314fbe10bb7d2ac7840903a56`) and #684 (`ca22f11655ff07958702109d986ae002998d45e6`) overlap portions of those trigger changes; do not merge all four blindly.
- Historical-source redirect hardening overlaps too: #683 (`7508d8e3bcdb894f882e405497ccc25ebee30f3f`) and #700 (`d2a6608ef8c11d2e517f8aec5637d12206760346`) both change the original historical CSV reader and its tests; #700 additionally updates the source/forward workflow paths for that reader. Each current HEAD has successful PR checks, but the shared implementation must be integrated once and full CI re-run on the final merged SHA.
- Current-form source integrity consolidation remains open as #699, exact HEAD `0672312fd0b3d8ab4178736e1b3a9fe99fe446c1`, with 7/7 associated checks completed successfully. It includes candidate verification, approved current-source URL checks, metadata-to-CSV identity parity, strict UTC clocks, and fail-closed time ordering. PR #697 is documentation-only; its current branch records the latest runtime proof available from Oct 25. This audit did not obtain a newer scheduled source/forward run ID, so no claim is made about today's scheduled run outcome.
- A fresh read-only query of `public.odds_snapshots` at approximately `2026-10-27T06:49:57Z` selected only league, snapshot/kickoff timestamps, and event IDs. It found **3,966 total snapshots**, **0 snapshots in the last 24 hours**, and **0 snapshots for future fixtures saved strictly before kickoff** across all nine leagues. Latest saved snapshot remains Serie A at `2026-10-13T14:48:53.042620Z`; EPL at `2026-10-09T15:25:57.102061Z`; all other checked leagues last have snapshots on Sep 11 or earlier. No score/result columns were queried.
- The existing current-form gate evidence records 73 metadata fixture identities versus 70 rows in the previously archived current-season source. The forward/source integrity code in #699 must fail closed on any identity not covered by the exact source archive; a fresh source capture on the eventual merged `main` is required before any preview.
- No fresh admissible quote or prospective V2 forecast was evidenced in this audit. The 30-primary-completed-event outcome gate remains CLOSED; no target outcomes were read/scored, no Supabase writes/DDL or paid provider calls occurred, and the frozen 19-feature candidate/weights/lambda contract were not changed. HUMAN-MERGE remains mandatory.


## 2026-10-27 — final current-form + original forward guard integration (exact-head CI proof)

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main mutation was performed.
- Consolidated integration PR [#699](https://github.com/MaksimBlud/football-ai/pull/699), exact HEAD `df2160c41a4fd520773e14296199b33d3cfb7ef9), changes 17 research/test/workflow files across the original old-season and current-form forward-only paths.
- **All 7/7 exact-head GitHub Actions checks SUCCESS**: [Original V2 Shadow Tests #40478010420](https://github.com/MaksimBlud/football-ai/actions/runs/40478010420), [Research #40478010395](https://github.com/MaksimBlud/football-ai/actions/runs/40478010395), [Serie A #40478010525](https://github.com/MaksimBlud/football-ai/actions/runs/40478010525), [Bundesliga #40478010529](https://github.com/MaksimBlud/football-ai/actions/runs/40478010529), [Ligue 1 #40478010382](https://github.com/MaksimBlud/football-ai/actions/runs/40478010382), [Eredivisie #40478010398](https://github.com/MaksimBlud/football-ai/actions/runs/40478010398), [Product #40478010359](https://github.com/MaksimBlud/football-ai/actions/runs/40478010359). The V2 shadow job ran **165 tests successfully** and the production-model hash guard passed.
- Consolidated protections: exact frozen-candidate/current-source URL preflight; current gate fixture identity set/count/digest parity; malformed, pre-season, reversed-duplicate and alias-collision rejection; strict HTTP URL and redirect checks for current and historical Football-Data CSVs; real-offset and gate/source/archive clock ordering; source-parent provenance; bidirectional event-ID/fixture identity; stale-quote rejection; protected score/result alias denylist; and dependency-path coverage for the existing source/forward workflows.
- Overlapping PRs #677/#678/#680/#679/#686/#675/#682/#688/#694/#695/#700/#696/#698 have been annotated as incorporated into #699 to avoid separate conflicting merges. Do not merge these independently without re-reviewing the consolidated diff.
- Existing schedules remain unchanged: current-form source capture `50 5 * * *` UTC, current-form forward preview `18 8 * * *` UTC, original forward preview `8 8 * * *` UTC. No new schedule or paid collector was added.
- Read-only odds audit: **3,966** saved snapshots; latest `2026-10-13T14:48:53.042620Z`; zero snapshots in the last 24h and zero future pre-kickoff snapshots. The latest confirmed current-form source capture remains run #40316117199 (2026-10-26 11:35:41Z, main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`), artifact #12647281024, SHA-256 `0ecfd702f0cd24f21894e93b0cbe63c65340a3eb48d3180e27652a3ad43c5e9b`, with 70 current-season rows. Latest metadata-only gate has 83 rows; the recorded canonical identity count is 80 after V2-local alias normalization. Exact identity coverage must fail closed until a fresh source archive is captured and verified.
- No current-form source-capture or current-form forward-preview run appeared in the Actions window through 2026-10-27 09:05Z. The last paired forward run #40316226164 verified the old archive but saw zero quotes and produced zero forecasts.
- Frozen candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with 19 unchanged features/weights. `active_lambda=0` remains the market reference; `shadow_lambda=1` remains research-only. Evaluation gate stays closed until 30 eligible completed prospective forecasts. No target outcomes read, no Supabase writes/DDL, no production `.pkl` changes, no refit/promotion.
- **HUMAN-MERGE:** PR #699 and this documentation PR remain open. Do not merge automatically.


## 2026-10-27 12:56 UTC — independently verified live gate identity parity (old-main artifact)

- Downloaded the actual source ZIP artifact **12730175586** from [Source Capture run #40493535578](https://github.com/MaksimBlud/football-ai/actions/runs/40493535578). Independent ZIP SHA-256: `f0fb3565d2e5f44faadf488820c36327cb9d0d7b83b3da826af9b877f0804986`, matching the uploaded artifact digest. Manifest SHA-256: `92a3372e027f59e38555548235c40a068fe407ce493aba6663c1a6e9ae081f74`; declared current CSV raw-byte SHA-256: `6cf59ded608d3d23da083b1f8510d2ca22b219f0927f64addeaadfde1b495e11`.
- Independently parsed **only** `Date, HomeTeam, AwayTeam` from `serie_a_2627.csv`: 80 rows / 80 unique fixture identities. A separate read-only Supabase query selected **only** `match_date, home_team, away_team`: 83 metadata rows. After the frozen V2-local alias normalization (Atalanta BC→Atalanta; Inter→Inter Milan; Milan→AC Milan; Roma→AS Roma; Verona→Hellas Verona), both sets contain 80 canonical identities and have the same independently computed SHA-256: `a19ac284b11337ea54591025683a721e0bd2c9815820309b3797188826055f27`.
- This proves the actual old-main archive's identity set matches the live metadata gate at capture time. However, the old-main manifest attests only the count (80) and has no identity list/SHA; the new independent gate-identity attestation in PR #699 is still required and has **not** yet been exercised live. Require HUMAN-MERGE, then re-run source capture and forward preview on the resulting exact main SHA.
- The paired forward preview #40493645751 saw zero quotes and captured zero shadows. Current odds audit still shows 3,966 rows, latest snapshot `2026-10-13T14:48:53.042620Z`, zero snapshots in the last 24h and zero future pre-kickoff snapshots. No target score/result columns were selected in these identity checks, no protected outcomes were read/scored, and no paid calls, Supabase writes/DDL, production changes, or merges occurred.


## 2026-10-28 12:50 UTC — current-form source, forward and free diagnostic proof

- Fresh source-of-truth audit: `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No merge or main mutation was performed.
- Current-form source capture [run #40681895214](https://github.com/MaksimBlud/football-ai/actions/runs/40681895214) completed successfully on that exact main SHA. GitHub artifact #12812553701 has independently rechecked ZIP SHA-256 `fb5f38f6c569de63dce7d9c1c58533ea873665e132d51bfc878ead7a684df6df` (435,794 bytes), matching the GitHub artifact digest. It contains 10 historical season CSVs plus the current-season `serie_a_2627.csv` and manifest. Manifest source-observation time is `2026-10-28T11:42:18.949888Z`; artifact was created at `2026-10-28T11:42:21Z`; parent workflow completed at `2026-10-28T11:42:25Z`. The metadata-only feature-input gate observed 80 eligible Serie A 2026/27 identities and selected no score/result fields.
- Paired [current-form forward preview #40682031414](https://github.com/MaksimBlud/football-ai/actions/runs/40682031414) completed successfully. Artifact #12812339141 SHA-256 is `16a43caf5d004cb122f63484e5206563953355ab8f853437c19141cbd2866707`, matching the GitHub artifact digest. It independently verified source artifact #12812553701, candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, source age 48 seconds at verification, 11 source files, 3,880 total rows across the ten historical files plus 80 current-season rows. Forward preview saw **0 quotes** and captured **0 shadow forecasts**. Target outcomes read/scored = false; paid calls and Supabase writes = 0.
- Separate free diagnostic [run #40690314722](https://github.com/MaksimBlud/football-ai/actions/runs/40690314722) completed successfully on the same main SHA. Artifact #12817246160 SHA-256 `274eb16af10f9d2253341f764afb50a87718e5507a4847dd14c91d4a09ca498e` matches GitHub metadata. This diagnostic fetched only ten public historical Serie A CSVs (2016/17–2025/26); it explicitly downloaded no 2026/27 public results. It recorded 19 frozen features, 0 quoted fixtures, 0 scored diagnostics, 0 feature rows with all 19 observed, `original_incumbent_asof_prediction_captured=false`, `eligible_for_frozen_prospective_cohort=false`, no promotion, no paid requests and no Supabase writes. This is source/provenance evidence only, not a successful model forecast or quality result.
- Fresh read-only query of `public.odds_snapshots` selected only snapshot/kickoff timestamps and counts: 3,966 rows; latest snapshot `2026-10-13T14:48:53.042620Z`; zero snapshots in the last 24 hours, zero in the last seven days, and zero future events with a snapshot strictly before kickoff. Therefore no eligible quote exists for the fresh source archive to score.
- Frozen original candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19-feature/weight contract unchanged. `active_lambda=0` remains the market reference and `shadow_lambda=1` remains research-only. `FROZEN_INCUMBENT_REFERENCE` is still unset, so the prospective outcome evaluator must remain fail-closed even after 30 forecasts until the separate approved protocol pins the exact incumbent. No protected 2026/27 target outcomes were read or scored.
- Supabase schema advisory independently reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No remediation was applied. This is a separate critical security issue; enabling RLS without designed policies may block application access.
- Next bounded actions: (1) HUMAN-MERGE review of consolidated source/clock/identity guard PR #699 before overlapping source PRs; (2) retain free source capture and verify its exact artifact on resulting main; (3) obtain only already-authorized/pre-existing pre-match quotes if available—no paid API call or paid cron; (4) pin incumbent only through a separately approved frozen-protocol amendment; (5) keep outcome gate closed until all preregistered conditions are satisfied.
- No Supabase writes/DDL, paid provider calls, production `.pkl` changes, model promotion, betting, target-outcome access, schedule changes, or merges occurred in this audit.


## 2026-10-28 20:47 UTC — later original/current-form forward runs and fresh odds audit

- Re-read current `main` before this audit: `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No merge or main mutation was performed.
- **Original frozen V2 forward preview:** [run #40711770789](https://github.com/MaksimBlud/football-ai/actions/runs/40711770789) completed SUCCESS on that exact main SHA. Its job log confirms **71 tests passed**; real source ZIP attestation succeeded for artifact `12817246160` from free diagnostic run `40690314722` (10 pre-prospective CSVs / 3,800 historical matches). Forward result: `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`; target outcomes read/scored = false; paid provider calls = 0; Supabase writes = 0. Uploaded run artifact `12826501542`, 1,459 bytes, SHA-256 `79a1cd9211e051851f621f9d971041f3a049e673f792c25f2c1aa6f941e197c4`, matching the Actions upload log.
- **Current-form V2 forward preview:** [run #40712651474](https://github.com/MaksimBlud/football-ai/actions/runs/40712651474) completed SUCCESS on the same main SHA. Its job log confirms **53 tests passed** and verifies source artifact `12812553701`, SHA-256 `fb5f38f6c569de63dce7d9c1c58533ea873665e132d51bfc878ead7a684df6df`, source observation `2026-10-28T11:42:18.949888Z`, parent source run `40681895214` completed at `11:42:25Z`, and the unchanged frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. The archive attestation reports 11 CSV files, 3,880 historical rows across ten frozen historical files, 80 current-season rows, feature-input gate count 80, and source age 12,312 seconds at verification. Forward result: `quotes_seen=0`, `v2_current_form_shadow_captured=0`; target outcomes read/scored = false; paid calls = 0; Supabase writes = 0. Uploaded run artifact `12825974332`, 436,969 bytes, SHA-256 `3659cc9e56f34da38abe86844a63b02686abd91153662a73bc2f5af3a171608e`, matching the Actions upload log.
- A fresh read-only query at `2026-10-28T20:47Z` selected only odds snapshot metadata/timestamps: **3,966** saved rows, latest `2026-10-13T14:48:53.042620Z`, **0** rows in the last 24 hours, **0** in the last 7 days, and **0** future snapshots strictly before kickoff. No score/result fields were selected.
- The scheduled forward jobs succeeded but started about 6h49–6h54 after their declared 08:08/08:18 UTC schedule. This records observed queue delay only; no workflow schedules/settings were changed.
- Interpretation remains unchanged: these are source/provenance and no-quote fail-closed proofs, **not** V2 quality evidence. No eligible prospective forecasts were captured; `FROZEN_INCUMBENT_REFERENCE` remains unset; the 30-completed-forecast outcome gate remains CLOSED. No protected target outcomes were read/scored, no paid requests, no Supabase writes/DDL, no production `.pkl` changes, no refit/promotion, and no merge occurred.


## 2026-10-29 05:48 UTC — exact-head guard audit and current pre-match data state

- Re-read default-branch source: `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main mutation occurred. This section is appended on the existing documentation PR branch only.
- Consolidated source/clock/identity guard PR [#699](https://github.com/MaksimBlud/football-ai/pull/699) is open at exact HEAD `e50ad26c3d6b4c9bac8d584dead0ab043b4f3792`, base `main` unchanged, with 7/7 exact-head validations successful (Research 40814628667; Serie A 40814628917; Bundesliga 40814628641; Ligue 1 40814628726; Eredivisie 40814628702; Product 40814628636; Frozen V2 Shadow 40814628724). Read-only inspection of that exact SHA confirms current-season Football-Data capture uses `allow_redirects=False`, checks exact approved final URL and HTTP status before reading body bytes, and the three secret-bearing V2 workflows require `github.ref == 'refs/heads/main'` before their secret environment blocks. This is static/CI evidence, not a post-merge live runtime proof.
- Free fixture feature-readiness PR [#702](https://github.com/MaksimBlud/football-ai/pull/702) is open at exact HEAD `ce589718afb2aebf02ee36872f17169e83bb2a9d`, base `main` unchanged, with 7/7 exact-head validations successful; its mocked bounded-response suite passed 15 tests. No live provider request was made, and its manual-only workflow remains unmerged.
- Protected evaluator PR [#701](https://github.com/MaksimBlud/football-ai/pull/701) remains an independent 6/6-CI guard. It intentionally fails closed while the approved non-legacy incumbent vector/reference is unset. The only strictly pre-kickoff product prediction group found in read-only metadata remains EPL / `EPL_AI_MARKET_PAIR_V1` (40 rows); it is not a valid Serie A incumbent and must not be substituted.
- Fresh read-only `public.odds_snapshots` aggregate at this audit: 3966 rows; latest `2026-10-13 14:48:53.04262+00`; 0 in the last 24h, 0 in the last 7d, and 0 future snapshots strictly before kickoff. The query selected only snapshot/kickoff timestamps and aggregate counts; no outcome columns.
- Fresh metadata-only query selected exactly `match_date, home_team, away_team` from Serie A 2026/27 finished-event metadata before the current UTC date: 83 raw rows, 80 canonical unique identities after the already frozen V2-local aliases, dates 2026-08-22 through 2026-10-25. This meets the separate 30-event lagged-feature-source gate only; it does not open the evaluation gate.
- The 30-eligible-completed-prospective-forecast outcome gate remains CLOSED: no admissible new saved market quotes exist, no eligible prospective forecasts are confirmed, and `FROZEN_INCUMBENT_REFERENCE` is unset. Original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features/weights, `active_lambda=0` market fallback and `shadow_lambda=1` research-only remain unchanged. No protected target outcomes were read or scored.
- Supabase's current schema advisory still reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. This is a separate critical access-control issue; no DDL was applied. Enabling RLS without reviewed policies may break application access.
- No paid provider calls, Supabase writes/DDL, production `.pkl` changes, promotion, betting, schedule changes, or merge occurred in this audit. HUMAN-MERGE remains mandatory.

## 2026-10-29 06:58 UTC — Free fixture preview dependency-trigger hardening

- **Current `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main write was performed.**
- PR #702 now has exact HEAD `80d457467f5ae5ea5c148082622bdec3cf8eb8de`. A distinct CI blind spot was closed: its new offline test workflow now watches 25 frozen/runtime dependencies and regression-test paths in both existing `pull_request.paths` and `push.paths`. A static test asserts every path appears in both triggers. No schedule or dispatch was added.
- Exact-head PR validation: **7/7 SUCCESS**. The new workflow suite passed **16 tests** in both PR run [40832333953](https://github.com/MaksimBlud/football-ai/actions/runs/40832333953) and push run [40832330355](https://github.com/MaksimBlud/football-ai/actions/runs/40832330355). This is offline CI proof only; no live provider request was made. PR #702 remains open for HUMAN-MERGE.
- Documentation PR #697 current HEAD `ef83acf70fb68abbaa7d8c6e325ff766e498d30c` has **7/7 SUCCESS** on its exact SHA; it remains open.
- Fresh read-only `public.odds_snapshots` query: **3,966** rows; latest `snapshot_time_utc=2026-10-13T14:48:53.042620Z`; **0** snapshots in the last 24h, **0** in the last 7d, and **0** future events with a pre-kickoff snapshot. No score/result fields were selected.
- Fresh metadata-only Serie A 2026/27 query selected only `match_date, home_team, away_team`: **83 raw identities** from 2026-08-22 through 2026-10-25. This raw count is not interchangeable with the source archive's **80 canonical identities** because alias normalization collapses the Atalanta / Atalanta BC labels.
- Latest discovered main-branch current-form source-capture run remains [40681895214](https://github.com/MaksimBlud/football-ai/actions/runs/40681895214), completed 2026-10-28; no newer Oct 29 source-capture run was present in the Actions listing at this audit. Do not assume a fresh archive until a new successful artifact and parent-run attestation are observed.
- Original candidate remains frozen SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, original 19 features/weights unchanged, `active_lambda=0` market and `shadow_lambda=1` research-only. No eligible prospective forecasts, no pinned non-legacy incumbent, no target outcomes read/scored, and the 30-primary-completed-forecast outcome gate remains CLOSED.
- No paid calls, Supabase writes/DDL, production `.pkl` changes, model refit, promotion, schedule changes, or merge. HUMAN-MERGE only.

## 2026-10-29 08:58 UTC — duplicate-key fail-closed and verified source archive audit

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main write was performed.
- PR #702 current exact HEAD is `b890514dda0c9a388c6855fa0d843a21a62a7306`. Its free-fixture JSON parser now rejects duplicate object keys (rather than silently retaining the last duplicate value), with a dedicated fail-closed regression. Exact-head CI is **7/7 SUCCESS**; the mocked-provider workflow passed **17 tests** in run [40845825309](https://github.com/MaksimBlud/football-ai/actions/runs/40845825309). CI made no provider request. PR #702 remains open for HUMAN-MERGE.
- PR #697 documentation HEAD `de20d4bd708bcd617b07e183609eff8d90f671bf` has **7/7 exact-head CI SUCCESS** (six repository validation workflows plus the prospective contract check); still open, no merge.
- Independently downloaded the actual main source-capture artifact from run [40681895214](https://github.com/MaksimBlud/football-ai/actions/runs/40681895214). GitHub artifact ID `12812553701`, size 435,794 bytes, declared digest `sha256:fb5f38f6c569de63dce7d9c1c58533ea873665e132d51bfc878ead7a684df6df`; locally computed ZIP SHA-256 matches exactly. Inspected only the ZIP member list and manifest, not CSV rows or target outcomes.
- Manifest evidence: 11 CSVs total; ten old-season files contain 3,800 historical rows; the current-season source contains 80 completed prior-day rows through the manifest gate. Current-season source SHA-256 `6cf59ded608d3d23da083b1f8510d2ca22b219f0927f64addeaadfde1b495e11`; latest source observation `2026-10-28T11:42:18.949888Z`; archive created `2026-10-28T11:42:19.025465Z`; frozen candidate SHA and feature-builder blob match the original V2 contract. Manifest states `target_outcomes_read=false`, `target_outcomes_scored=false`, paid provider calls 0 and Supabase writes 0.
- The archive's 24-hour freshness boundary approaches at approximately `2026-10-29T11:42:18Z`. The main source-capture workflow declares cron `50 5 * * *`, but no source-capture run appeared in the observed GitHub Actions window 2026-10-29 05:30–06:30 UTC. Do not infer that it is disabled; recheck for a delayed run and require a new successful artifact before any provider request. The manual free-fixture workflow is still unmerged and has not made a live request.
- Fresh read-only Supabase aggregate across nine leagues: **3,966** saved odds snapshots; 0 in the last 24h; 0 in the last 7d; 0 future events with a snapshot strictly before kickoff. Latest per league: Serie A `2026-10-13T14:48:53Z`, EPL `2026-10-09T15:25:57Z`, remaining leagues no newer than 2026-09-11 (RPL 2026-09-05). Query used only league, snapshot/kickoff timestamps and aggregate counts.
- The 30-completed-prospective-forecast outcome gate remains CLOSED: no admissible new prospective market snapshots/forecasts and no pinned non-legacy incumbent. Original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features/weights, `active_lambda=0` market fallback and `shadow_lambda=1` research-only remain unchanged. No protected target outcomes were read/scored.
- No paid calls, Supabase writes/DDL, production `.pkl` changes, schedule changes, promotion, betting or merge. HUMAN-MERGE remains mandatory.



## 2026-10-29 09:48 UTC — source refresh gap, quote-timing audit, and incumbent-gate blocker

- Fresh main read remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No merge or main write was performed. PR #697 exact HEAD `39b942eaa81b506f1657a93397723d9ce304d04c` has now completed **7/7 SUCCESS**: [Research](https://github.com/MaksimBlud/football-ai/actions/runs/40846082936), [Serie A](https://github.com/MaksimBlud/football-ai/actions/runs/40846081987), [Bundesliga](https://github.com/MaksimBlud/football-ai/actions/runs/40846082185), [Ligue 1](https://github.com/MaksimBlud/football-ai/actions/runs/40846081955), [Eredivisie](https://github.com/MaksimBlud/football-ai/actions/runs/40846081972), [Product](https://github.com/MaksimBlud/football-ai/actions/runs/40846081939), and [La Liga prospective contract](https://github.com/MaksimBlud/football-ai/actions/runs/40846082161). PR remains open for HUMAN-MERGE.
- Exact-head CI was re-read: PR #699 `e50ad26c3d6b4c9bac8d584dead0ab043b4f3792` is 7/7 SUCCESS; PR #702 `b890514dda0c9a388c6855fa0d843a21a62a7306` is 7/7 SUCCESS including [17 mocked-provider tests](https://github.com/MaksimBlud/football-ai/actions/runs/40845825309); PR #701 `7ee3eda3f396735e00737d8e8e42e0c8c146c57f` is 6/6 SUCCESS. None is merged.
- Read-only GitHub Actions run-list query for `2026-10-29T05:00:00Z..2026-10-29T09:48:00Z` returned 98 runs and **no** run named `Serie A V2 Current-Form Source Capture`, `Serie A V2 Current-Form Forward-Only Preview`, or `Serie A V2 Original Forward-Only Preview`. The latest verified source remains run [40681895214](https://github.com/MaksimBlud/football-ai/actions/runs/40681895214), artifact ID `12812553701`; manifest source observation `2026-10-28T11:42:18.949888Z`, archive SHA-256 `fb5f38f6c569de63dce7d9c1c58533ea873665e132d51bfc878ead7a684df6df`. At this audit the observation is about 22h06m old and reaches the fixed 24h age boundary at approximately `2026-10-29T11:42:18.95Z`. No new artifact is assumed until a new successful main run and digest are verified.
- Read-only aggregate on `public.odds_snapshots` selected only league and quote/kickoff timestamps. Across all leagues: **3,966** snapshots; latest `2026-10-13T14:48:53.04262Z`; **0** snapshots in the last 24h or 7d; **0** future events with a strictly pre-kickoff quote; **51** rows at/after kickoff. Serie A: **625** snapshots, **620** strictly pre-kickoff, **5** at/after kickoff, latest `2026-10-13T14:48:53.04262Z`. Current original forward code rejects quote timestamps not strictly before kickoff (`serie_a_v2_forward_capture.py` and `serie_a_v2_current_form_forward_capture.py`); the 51 non-admissible rows must never count as prospective evidence. No score/result columns were selected.
- New hard evaluation blocker confirmed by reading the frozen evaluator and policy: `FROZEN_INCUMBENT_REFERENCE` is `None`, and `evaluate_after_gate` returns `EVALUATION_BLOCKED_UNPINNED_INCUMBENT` without calling the lazy outcome loader, even if the 30-forecast count is met. The preregistered protocol requires comparison against a frozen incumbent, but no exact incumbent model version/artifact SHA is pinned. Do not guess, load, or revive the legacy XGBoost model and do not read target outcomes to work around this. Scientific evaluation remains blocked until an owner-approved immutable comparator reference or separately approved protocol amendment exists before any outcome read.
- Original V2 remains candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features/weights unchanged; `active_lambda=0` market, `shadow_lambda=1` research-only; no eligible prospective forecasts or Brier/LogLoss results. No paid provider calls, Supabase writes/DDL, production `.pkl` changes, outcome reads, schedule changes, model refit/promotion, or merge.


## 2026-10-29 10:54 UTC — exact current-form source identity parity verified read-only

Read-only verification on unchanged main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no scores or result columns were read.

- The latest verified main source-capture run available in the connected GitHub records is [run 40681895214](https://github.com/MaksimBlud/football-ai/actions/runs/40681895214), completed successfully. Artifact ID `12812553701`, created `2026-10-28T11:42:21Z`; ZIP size 435,794 bytes and SHA-256 `fb5f38f6c569de63dce7d9c1c58533ea873665e132d51bfc878ead7a684df6df`. The archive has ten frozen historical CSVs plus `serie_a_2627.csv`; current-season source SHA-256 `6cf59ded608d3d23da083b1f8510d2ca22b219f0927f64addeaadfde1b495e11`, observed `2026-10-28T11:42:18.949888Z`.
- Archive manifest records 80 completed prior-day current-season rows and a metadata-only feature-source gate of 80 canonical identities. I independently computed the current-season CSV identity set using only `Date, HomeTeam, AwayTeam` columns; no score/result columns were selected or parsed. The canonical identity count is 80 and SHA-256 is `a19ac284b11337ea54591025683a721e0bd2c9815820309b3797188826055f27`.
- A fresh read-only Supabase query selected only `match_date, home_team, away_team` from `public.league_finished_results` for Serie A 2026/27 strictly before the current UTC date. It returned 83 raw metadata rows but 80 identities after the frozen aliases `Inter → Inter Milan`, `Milan → AC Milan`, `Roma → AS Roma`, `Verona → Hellas Verona`, and V2-local `Atalanta BC → Atalanta`. The independently computed canonical identity SHA-256 is the same `a19ac284b11337ea54591025683a721e0bd2c9815820309b3797188826055f27`. First/last dates: 2026-08-22 / 2026-10-25. This proves exact identity-set parity for the archived source as of the current metadata snapshot; it does not open the target-outcome evaluation gate.
- Fresh read-only `public.odds_snapshots` audit: 3,966 rows, latest quote `2026-10-13T14:48:53.042620Z`, zero snapshots in the prior 24 hours or 7 days, and zero future fixtures with strictly pre-kickoff saved quotes. No new prospective V2 forecast is admitted.
- PR #699 HEAD `e50ad26c3d6b4c9bac8d584dead0ab043b4f3792` has 7/7 exact-head CI success and includes current-season plus historical source URL/redirect guards, source identity parity, clock/fixture guards, and expanded frozen-dependency triggers. PR #700's historical CSV redirect patch overlaps code already present in #699; review merge order before merging either. PR #701 remains separately blocked from target-outcome reads while `FROZEN_INCUMBENT_REFERENCE` is unpinned. PR #702 HEAD `b890514dda0c9a388c6855fa0d843a21a62a7306` has 7/7 exact-head CI success for the free fixture/feature-readiness tests.
- No workflow was dispatched or rescheduled; no paid provider call, Supabase write/DDL, production model change, outcome read, model refit, or promotion occurred.

Interpretation: the existing source archive's 80 canonical fixture identities exactly match the current metadata gate; the remaining blocker is the lack of fresh, admissible pre-kickoff market quotes and the unpinned incumbent required by the frozen evaluator. The original 19-feature contract/weights, candidate SHA, `active_lambda=0`, `shadow_lambda=1`, and NO_BET behavior remain unchanged.


## 2026-10-29 11:54 UTC — source freshness crossed the 24-hour gate

Fresh main/continuity/open-PR review and read-only Supabase audit. Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main mutation or merge.

### Actual source and forward runtime

- Latest confirmed current-form source artifact remains **12812553701**, from successful main run [40681895214](https://github.com/MaksimBlud/football-ai/actions/runs/40681895214). GitHub artifact digest and independently verified ZIP SHA-256: `fb5f38f6c569de63dce7d9c1c58533ea873665e132d51bfc878ead7a684df6df`; the prior byte-level audit verified all 11 CSV digests against the manifest.
- Source observation: `2026-10-28T11:42:18.949888Z`; artifact created `2026-10-28T11:42:21Z`. At audit time `2026-10-29T11:54:09Z`, source age was **24h 11m 50s**, beyond the frozen 24-hour maximum. Treat this artifact as stale for any new quote; do not relax freshness or backfill.
- Last confirmed current-form forward run [40712651474](https://github.com/MaksimBlud/football-ai/actions/runs/40712651474) succeeded on main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`, but `quotes_seen=0` and `v2_current_form_shadow_captured=0`. Last confirmed original forward run [40711770789](https://github.com/MaksimBlud/football-ai/actions/runs/40711770789) also completed successfully with no admissible saved quote. These are no-quote fail-closed proofs, not model-quality evidence. No newer source artifact was confirmed in this audit.

### Read-only Supabase evidence

Audit time: `2026-10-29T11:54:09.027257Z`. Query against `public.odds_snapshots` used only timestamps, league, kickoff and aggregate counts; no target outcomes:

- Total saved snapshots: **3,966**; latest snapshot `2026-10-13T14:48:53.042620Z`.
- Snapshots in prior 24 hours: **0**; prior 7 days: **0**.
- Future events with a snapshot strictly before kickoff: **0**; future non-pre-match snapshots: **0**.
- Serie A: **625** snapshots; latest also `2026-10-13T14:48:53.042620Z`.

The metadata-only query on `public.league_finished_results` selected only `match_date, home_team, away_team` for Serie A 2026/27 before the UTC audit date. It returned **83** raw directional identities, dated 2026-08-22 through 2026-10-25. The established V2-local alias normalization yields **80** canonical fixture identities. No score/result columns were selected.

### Exact open-PR state rechecked

- [PR #699](https://github.com/MaksimBlud/football-ai/pull/699), HEAD `e50ad26c3d6b4c9bac8d584dead0ab043b4f3792`: **7/7** required checks SUCCESS. Consolidates source, clock, identity, target-field and workflow guards; remains unmerged.
- [PR #702](https://github.com/MaksimBlud/football-ai/pull/702), HEAD `b890514dda0c9a388c6855fa0d843a21a62a7306`: **7/7** required checks SUCCESS; dedicated mocked suite **17 passed**. It remains manual-dispatch-only and emits feature readiness, not probabilities. Official API documentation states that GET `/v4/sports/{sport}/events` does not count against usage quota ([documentation](https://the-odds-api.com/liveapi/guides/v4/)); no provider request was made in this audit or by CI.
- [PR #701](https://github.com/MaksimBlud/football-ai/pull/701), HEAD `29229dbce2ce9096eb717b59d80db296ec2621e0`: **6/6** required checks SUCCESS, evaluator suite **62 passed**. Outcome evaluation remains blocked by the intentionally unpinned non-legacy incumbent reference.
- This update is documentation-only; it does not alter code, workflow schedules, source/feature policy, the frozen candidate, or any gate.

### Binding disposition

No fresh strictly pre-kickoff quote or new eligible V2 forecast exists. At the 2026-10-29 21:55 UTC audit, the latest source archive was approximately 10 hours old (so it had NOT crossed the 24-hour age limit); its current-gate freshness remains unproven because the captured manifest recorded only 80 gate identities and omitted the exact gate identity-set SHA. Keep source/gate attestation and the 30-completed-prospective-forecast outcome gates closed. Frozen candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original 19 features/weights unchanged; `active_lambda=0` market, `shadow_lambda=1` research only. No target outcomes read/scored, no paid provider request, no Supabase writes/DDL, no production `.pkl` change, no schedule change and no merge. HUMAN-MERGE only.

## 2026-10-29 — current-form archive identity parity and gate-time mismatch

Read-only audit performed at 2026-10-29T20:51:48Z against fresh main
40887ebb215730190d7a6c7a1693373ec4afcdfc, the real current-form source artifact,
and Supabase metadata. No score/result columns were selected or parsed.

- Source run: [40868280531](https://github.com/MaksimBlud/football-ai/actions/runs/40868280531), scheduled, SUCCESS.
- Source artifact: 12894054589; independently downloaded ZIP SHA-256:
  b4b1144ca28414ccf7a5a7a5c02fde4611e8e0f1a37997012de031a38baa14b0.
- Current-season CSV SHA-256 from the archive manifest:
  d2fa45e92d662ab8a79421475361ac694cace2deb75fbe799b6c04baaabe9691.
- Parsing only Date, HomeTeam, AwayTeam from the archived current-season CSV yields 88 canonical identities:
  80 dated through 2026-10-25 and 8 dated 2026-10-26 through 2026-10-28.
- Independent read-only Supabase metadata query selected only match_date, home_team, away_team.
  Its canonical identity set is also 88, with SHA-256
  7ba862a3a52a982ef6482feae6d20eb200f6888dc2132fd966c2da6ca0d2e8fa.
  The exact same SHA was independently computed from the archived CSV identity columns.
- Saved odds remain unchanged: 3,966 snapshots; latest
  2026-10-13T14:48:53.042620Z; zero in the previous 24h/7d and zero future strict-pre-kickoff rows.

**Important gate-time caveat:** the artifact manifest records feature_source_gate.checked_at_utc =
2026-10-29T11:49:31.742325Z and observed_completed_primary_events = 80, while the source CSV
captured in the same run contains 88 identities and the ZIP was created at
2026-10-29T11:49:49.284743Z. Current parity is now demonstrated, so the older statement
that the newest archive itself has only 80 identities is stale. However, the manifest does not
store the exact gate identity-set SHA; therefore current parity does not retroactively prove
which exact 80 identities the gate returned at capture time.

Keep PRs #694/#699 fail-closed: persist the gate identity-set hash and source identity-set hash
from the same run, and require every gate identity to be present before attesting the archive.
Do not infer source correctness from row counts alone. This is source-integrity evidence only,
not a V2 forecast or model-quality result. No outcomes read, no paid calls, no Supabase writes,
no production artifact/model changes, no main mutation, and no merge.


## 2026-10-29 — corrected source-age interpretation and raw metadata count (21:55 UTC)

Fresh read-only Supabase queries selected only the saved-odds timestamps/kickoff timestamps and the Serie A 2026/27 fixture metadata fields. No score/result/settlement columns were selected.

- `public.odds_snapshots`: 3,966 total; latest `2026-10-13T14:48:53.042620Z`; zero snapshots in the prior 24 hours or 7 days; zero future rows with `snapshot_time_utc < commence_time_utc`.
- `public.league_finished_results` for `league='SERIE_A'`, season dates from 2026-07-01: 91 rows and 91 raw (date, home, away) tuples, dated 2026-08-22 through 2026-10-28. Applying the existing V2-local canonical team aliases yields 88 fixture identities, consistent with the prior identity-only archive comparison.
- Correction to the earlier paragraph: at this audit the source archive from run 40868280531 was about 10 hours old, **not older than 24 hours**. The active blocker is not elapsed archive age; it is that the manifest records a gate count of 80 without the exact gate identity-set SHA, while the latest canonical metadata set now contains 88 identities. A current 88-to-88 identity parity result does not retroactively prove which exact 80 identities were seen at gate time.
- Original current-form forward-only run 40899523036 and original forward-only run 40898762675 both completed SUCCESS on main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`, but produced no admissible forecasts because no fresh saved pre-kickoff quotes exist.
- PR #699 HEAD `e50ad26c3d6b4c9bac8d584dead0ab043b4f3792` was rechecked directly through GitHub's commit check-runs API: all seven named checks completed SUCCESS on that exact SHA (last completion 2026-10-29 03:54:20 UTC). It remains open and unmerged under HUMAN-MERGE.

This note corrects source-age wording only; no code, frozen weights/features, gates, workflow schedules, Supabase data, or production artifacts were changed. No outcomes were read or scored, no paid requests were made, and no merge occurred.

## 2026-10-30 — Original V2: bounded GitHub source-artifact ZIP downloads (PR #699)

- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main mutation occurred.
- The consolidated original V2 source/forward PR #699 now also bounds the two GitHub Actions ZIP download paths: old-season `get_archive` uses the existing 12,000,000-byte limit; current-form `get_archive` uses the existing 16,000,000-byte limit.
- Both paths request `stream=True`, reject malformed or over-limit `Content-Length` before body reads, count actual yielded bytes in 64 KiB chunks, stop immediately when the configured limit is crossed, reject empty bodies, and close the response in a `finally` block.
- Six synthetic regressions cover successful streaming/cleanup, declared oversize rejected before any body read, and actual streamed oversize stopped at the first excess chunk (three tests per path).
- Exact PR #699 head: `3d6c52c86c8298167b39e66fee388d0dd9399fe9`. All **7/7** required PR workflows passed on this exact SHA. Original V2 Shadow Tests: **220 passed**; the `git diff --exit-code -- '*.pkl'` production-model guard passed.
- CI run IDs: Original V2 Shadow Tests `40983644455`; Research `40983644638`; Serie A `40983644536`; Bundesliga `40983644513`; Ligue 1 `40983644417`; Eredivisie `40983644484`; Product `40983644459`.
- This is code/CI resource-integrity proof only. The new ZIP downloader has **not** yet been exercised by a post-merge live source/forward run; PR #699 remains open under HUMAN-MERGE. The existing main workflows still lack the new main-ref job guard until that PR is manually merged.
- Read-only Supabase audit (identity-only metadata columns; no scores/results selected): Serie A 2026/27 had **91** raw rows / **88** canonical identities through **2026-10-28**. Odds audit: **3,966** rows total, **3,915** strictly pre-kickoff snapshots; latest strictly pre-kickoff snapshot `2026-10-13T14:48:53.042620Z`; **0** snapshots in the last 24 hours, **0** in the last 7 days, and **0** future events with a strictly pre-kickoff quote. Therefore no new forecast or quality metric was available.
- PR #657, #659, and #660 are confirmed merged. PR #694/#700 overlap the consolidated #699 source-identity / URL protections and should not be merged independently without a fresh diff review. PR #697 remains documentation-only; #701 remains blocked by the missing frozen incumbent; #702 remains an unrun manual-only zero-credit fixture/feature-readiness probe.
- Frozen candidate SHA, original 19 features/weights, `active_lambda=0`, `shadow_lambda=1`, and the 30-primary-completed-event target-outcome gate remain unchanged. No target outcomes were read, no odds-provider request was made, and no Supabase write/DDL occurred.

## 2026-10-30 02:52 UTC — Original V2: main-only secret isolation and fresh metadata audit

**PR #699 exact HEAD:** `72a3993046d66e4d1c09a4407e365885c70f04ed` (base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`). A further V2-only workflow hardening adds a job-level `github.ref == 'refs/heads/main'` guard to the free real-quote diagnostic, which receives `SUPABASE_URL` and `SUPABASE_KEY`. A regression test proves manual dispatch from a non-main ref is blocked while the existing workflow_dispatch and free-only schedule declaration remain unchanged. The other three secret-bearing V2 source/forward jobs already receive equivalent main-ref guards in this consolidated PR.

Exact-head validation on `72a3993046d66e4d1c09a4407e365885c70f04ed`: **7/7 SUCCESS** (Original V2 Shadow, Research, Serie A, Bundesliga, Ligue 1, Eredivisie, Product). Original V2 Shadow suite: **226 passed**; its `Verify no production model hashes changed` step passed. Research PR Validation's `Enforce no production artifact changes` step also passed. No frozen 19-feature/weight candidate, lambda semantics, evaluation protocol, workflow cadence, paid provider call, Supabase write/DDL, production `.pkl`, target outcome, or main ref was changed.

Fresh read-only Supabase audit (2026-10-30 approximately 02:50 UTC):
- `public.odds_snapshots`: **3,966** rows across leagues; zero snapshots in the last 24 hours and zero in the last 7 days; zero future strict pre-kickoff snapshots. Serie A: **625** rows, latest `2026-10-13T14:48:53.042620Z`.
- Metadata-only `public.league_finished_results` query selected exactly `match_date, home_team, away_team` for Serie A 2026/27. It returned **91 raw rows / 88 canonical fixture identities**, dates 2026-08-22 through 2026-10-28. No score, goals, result, settlement or target-outcome fields were selected. This is the feature-source input gate only; it does not open the separate 30-eligible-prospective-forecast evaluation gate. The canonical identity-set SHA must be emitted by the new source-capture implementation and matched to the archived CSV; this manual count is not substituted for that runtime attestation.
- `public.model_artifact_bundles` remains empty (**0** registered bundles). No independently pinned same-event non-legacy incumbent is available; the evaluator remains fail-closed.
- Supabase Security Advisor reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. This is a separate critical access-control issue; no DDL was run because enabling RLS without reviewed policies can block application access.

**Disposition:** #699 is still open and requires HUMAN-MERGE. After manual merge, verify the exact resulting main SHA, run the existing free source capture on main, compare gate identity-set SHA and full CSV coverage, then run original/current-form forward-only readers. Existing October 13 quotes remain stale/source-after-quote and cannot be backfilled. No prospective forecasts, Brier/LogLoss, incumbent comparison or model-superiority claim is available yet.

## 2026-10-30 02:58 UTC — Original V2: fail-closed source clock rollback proof

The final audit of the consolidated source capture found that offset-aware timestamps were validated, but the source writer did not itself reject a backwards wall-clock transition. The current-form forward reader already requires `gate_checked <= latest_source <= declared_archive`; the source writer now enforces the corresponding order before writing:
- `source_observed_at_utc >= feature_source_gate.checked_at_utc`;
- `source_archive_created_at_utc >= source_observed_at_utc`.

The two new regressions simulate (1) observation time earlier than the gate timestamp and (2) archive time earlier than observation. Both prove that the complete bounded response body was read, the response was closed, and neither the current-season CSV nor manifest was written. This consolidates the missing source-capture behavior from overlapping #686 into #699; #680's forward-reader gate/source/archive check is also present in #699. Do not merge #686/#680 independently.

Latest #699 exact HEAD: `ab888b32e6ea5a231d271b00e4db42fab186986b`; base main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. All **7/7** required checks passed on that exact SHA. Original V2 Shadow Tests: **228 passed**; production `*.pkl` diff guard passed. Research PR Validation's no-production-artifact guard passed. The earlier main-ref secret guard also remains in #699 for all four V2 workflows that expose Supabase credentials. Existing schedules are unchanged.

The fresh metadata-only / odds audit recorded above remains the latest:
- 3,966 stored odds snapshots; zero in the last 24h/7d and zero future strict pre-kickoff rows; Serie A latest snapshot 2026-10-13 14:48:53 UTC.
- Serie A 2026/27 identity-only metadata: 91 raw rows / 88 canonical fixture identities through 2026-10-28. The exact gate SHA and CSV-coverage proof must come from the new on-main source-capture manifest after HUMAN-MERGE; this count is not a substitute for it.
- `public.model_artifact_bundles`: 0; no eligible frozen incumbent is registered. The separate 30-eligible-prospective-forecast outcome gate remains closed.
- Security Advisor still reports RLS disabled on five public tables. No DDL was run.
- GitHub API reports `main` as unprotected (`protected=false`); no repository settings were changed.

**Next proof:** wait for HUMAN-MERGE of #699, verify the resulting exact main SHA, then run the existing free source capture and original/current-form forward-only workflows on main. Do not dispatch secret-bearing V2 workflows from a feature branch before that merge. No live source/forward run has yet exercised the new clock rollback and main-ref guards; current October 13 quotes remain stale and cannot be backfilled.


## 2026-10-30 03:58 UTC — Free fixture request parameter allowlist

PR [#702](https://github.com/MaksimBlud/football-ai/pull/702) received a test-only hardening commit:
- Exact HEAD: `b91773b6677bd2be7df67d5b2c69c27b9a202397`.
- New regression `test_events_request_uses_only_zero_credit_metadata_parameters` pins the sole query parameter allowlist to `apiKey`, `dateFormat`, and `commenceTimeFrom`; it explicitly rejects markets, regions, odds-format, bookmaker, event-ID and score parameters.
- The existing request remains one manual-only HTTPS `/events` call, with redirects disabled and `x-requests-last=0` required. The test asserts the API key is not serialized in the output.
- Exact-head CI: **8/8 checks SUCCESS**. Offline contract test run [#41000192490](https://github.com/MaksimBlud/football-ai/actions/runs/41000192490) reports **18 passed**. This is mocked/offline validation only; no live provider request was made.

Fresh read-only data checkpoint:
- Strictly pre-kickoff `odds_snapshots`: **3,915** of 3,966 total; zero strictly pre-kickoff rows in the last 24 hours or 7 days; zero future fixtures with a saved pre-kickoff quote. Serie A latest remains `2026-10-13T14:48:53.042620Z`.
- Metadata-only Serie A 2026/27 identity query selected only `match_date, home_team, away_team`: **91 raw rows / 88 canonical fixture identities**, from 2026-08-22 through 2026-10-28.
- The last old-main source archive still records a gate count of **80** and 88 completed current-season CSV rows (artifact `12894054589`, ZIP SHA-256 `b4b1144ca28414ccf7a5a7a5c02fde4611e8e0f1a37997012de031a38baa14b0`). It does not attest the later 88-identity metadata set. PR #699's current-gate/source-coverage guard must be exercised by a fresh post-merge capture before any current-form shadow is admitted.

Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; PR #699 remains open at `ab888b32e6ea5a231d271b00e4db42fab186986b`, 7/7 CI / 228 original V2 tests. No new quotes or prospective forecasts exist; no target outcomes were read. Frozen candidate/19-feature/weight contract, `active_lambda=0`, `shadow_lambda=1`, and the 30-completed-prospective-forecast evaluation gate are unchanged. No live provider request, paid call, Supabase write/DDL, production `.pkl` change, merge, or schedule change.


## 2026-10-30 07:55 UTC — exact-head and source-gate drift audit

This checkpoint supersedes earlier SHA references in PR descriptions and older continuity sections. Always use the live GitHub Pull Request API `head.sha` plus Actions runs attached to that exact commit; several PR body text blocks contain older HEAD values.

### Exact open V2 PR heads and CI

- **#699** actual API head: `3e772c859bf3538a492aaffc314be533285d7db0`, base `40887ebb215730190d7a6c7a1693373ec4afcdfc`, open and mergeable. Exact-head Actions: 7/7 SUCCESS. Original V2 Shadow Tests [run #41011507232](https://github.com/MaksimBlud/football-ai/actions/runs/41011507232): **229 passed**; `git diff --exit-code -- '*.pkl'` passed. The actual head is 16 commits ahead of the older `32251b847b01c0891ea6f94ec3a16471ee6cc95a` SHA quoted in an older PR-body section.
- **#697** actual API head: `6e0e25ac8797225e23a1d1c39349d19cb576d7dd`; exact-head Actions 7/7 SUCCESS. This documentation update is being appended to the same branch, not main.
- **#701** actual API head: `7ee3eda3f396735e00737d8e8e42e0c8c146c57f`; exact-head Actions 6/6 SUCCESS. The evaluator remains fail-closed because no approved non-legacy frozen incumbent reference is pinned; do not substitute the market or revive the old XGBoost model.
- **#702** actual API head: `b91773b6677bd2be7df67d5b2c69c27b9a202397`; exact-head Actions 7/7 SUCCESS. It is manual-only and only probes free event metadata; it does not retrieve odds or create forecasts.

No PR was merged. HUMAN-MERGE remains mandatory.

### Fresh main and actual source artifact

- Default branch is still `main` at `40887ebb215730190d7a6c7a1693373ec4afcdfc`; its committed `PROJECT_CONTINUITY.md` still begins with the 2026-10-18 checkpoint.
- Latest discovered successful main-ref Current-Form Source Capture is [run #40868280531](https://github.com/MaksimBlud/football-ai/actions/runs/40868280531), completed 2026-10-29 11:49:54Z. Artifact `12894054589` has GitHub digest `sha256:b4b1144ca28414ccf7a5a7a5c02fde4611e8e0f1a37997012de031a38baa14b0`; independently downloaded ZIP bytes reproduced the same SHA-256.
- The actual ZIP manifest is the older count-only schema: feature-input gate count **80**, 11 source CSVs, no gate identity list or identity SHA. The current-season CSV was inspected using only `Date, HomeTeam, AwayTeam` columns: 88 fixture-metadata rows, latest date **2026-10-28**. No score/result columns were read.
- A fresh read-only Supabase metadata query on 2026-10-30 07:55Z selected only `match_date, home_team, away_team` from `public.league_finished_results` for Serie A 2026/27 before 2026-10-30: **93 raw rows / 90 unique canonical identities**, latest date **2026-10-29**, including two raw Oct 29 fixture rows. At least those Oct 29 identities post-date the archived current-season CSV. The old archive therefore cannot prove coverage of the current gate and must not be used for a new shadow calculation.
- No Oct 30 source-capture run was present in the recent main Actions run history as of 07:55Z, although the main workflow file declares its existing daily 05:50 UTC schedule. This is an observed missing run, not proof that the workflow is disabled; do not change its schedule or settings.

### Fresh pre-match odds audit

Read-only `public.odds_snapshots` audit at the same checkpoint:

- **3,966** total snapshots; **3,915** strictly pre-kickoff.
- **0** strictly pre-kickoff snapshots in the last 7 days.
- **0** future fixtures with a saved strictly pre-kickoff snapshot.
- Latest Serie A pre-match snapshot remains **2026-10-13 14:48:53.042620 UTC**.

No new prospective V2 forecasts can be captured from the current saved-odds table. No paid Odds API request was made.

### Required next proof

1. HUMAN-MERGE #699 at its live exact head `3e772c859bf3538a492aaffc314be533285d7db0`.
2. Verify the resulting main SHA and run the existing free Current-Form Source Capture on main.
3. Confirm the new manifest contains the metadata-only gate identity set/count/SHA, all current gate identities are covered by the downloaded CSV, all 11 source CSV hashes match, and gate → source observation → archive creation ordering is valid.
4. Run Current-Form and Original Forward-Only on the resulting main SHA. Existing stale quotes must remain blocked; do not backfill.
5. Wait for genuinely new saved pre-kickoff quotes before any shadow capture. PR #702's free `/events` probe may provide fixture metadata only, not market odds.

Frozen candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features/weights and protocol remain unchanged; `active_lambda=0` remains the market and `shadow_lambda=1` research-only. The separate evaluation gate remains closed until 30 eligible prospective forecasts have completed, and the incumbent blocker remains unresolved. No target outcomes were read/scored, no Supabase writes/DDL, no production `.pkl` changes, no model refit/promotion/bets, no paid calls, no merge, and no schedule changes occurred.

## 2026-10-30 09:49 UTC — source schedule liveness, canonical gate digest, and PR overlap

This checkpoint is a fresh read-only audit. Main remains 40887ebb215730190d7a6c7a1693373ec4afcdfc. The current main continuity file blob is 2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b. No merge or main update occurred.

### Exact open V2 PR state

- #699 remains open/mergeable at exact head 3e772c859bf3538a492aaffc314be533285d7db0, base 40887ebb215730190d7a6c7a1693373ec4afcdfc. Its seven exact-head checks are SUCCESS; Original V2 Shadow Tests [#41011507232](https://github.com/MaksimBlud/football-ai/actions/runs/41011507232) reports 229 passed. The production .pkl diff guard passed.
- #697 was at exact head 3bd0d030a5c532ac89ad3767828f19f313c2ab7c before this documentation-only append; its seven exact-head checks were SUCCESS.
- #701 remains at 7ee3eda3f396735e00737d8e8e42e0c8c146c57f with 6/6 SUCCESS. The prospective evaluator remains blocked by the absent approved non-legacy frozen incumbent; do not substitute market probabilities or revive the legacy XGBoost model.
- #702 remains at b91773b6677bd2be7df67d5b2c69c27b9a202397 with 7/7 SUCCESS. It is a manual-only, one-request, zero-credit event-metadata probe; no live request has been made.
- #700 remains open at d2a6608ef8c11d2e517f8aec5637d12206760346. Its changed paths overlap #699. The current #699 patch already includes the historical CSV no-redirect control (allow_redirects=False), bounded streaming, and corresponding redirect regression coverage in serie_a_v2_live_diagnostic_report.py. Treat #700 as overlapping/superseded for that core change; do not merge it independently without a post-#699 content comparison.

HUMAN-MERGE remains mandatory.

### Oct 30 scheduled V2 workflow liveness

The main workflow files still declare these UTC schedules:

- Current-Form Source Capture: 05:50 UTC.
- Free Real-Quote Diagnostic: 06:13 UTC.
- Original Forward-Only Preview: 08:08 UTC.
- Current-Form Forward-Only Preview: 08:18 UTC.

A fresh Actions query covered 216 main-branch runs created from 00:00 through 08:58 UTC on Oct 30 (three pages, 100 + 100 + 16). No run with any of the four V2 workflow names above appeared. This is an observed missing scheduled-run set, not proof that GitHub has disabled the workflows. Do not alter schedules or settings. No manual dispatch was possible through the available read-only Actions interface.

### Current metadata-only feature-input gate

Read-only Supabase query selected only match_date, home_team, away_team from public.league_finished_results for Serie A 2026/27 before the current UTC date. It returned:

- raw rows: 93;
- unique canonical identities after the existing V2-local Atalanta BC → Atalanta alias: 90;
- latest metadata date: 2026-10-29;
- sorted canonical identity-set SHA-256: 7c91dad874222ff98e6cce033ce36c71c51306b5979a7854ff8c3c60eab36bce.

This satisfies the separate lagged-feature input count (>=30) but does not open target-outcome evaluation. The latest available source archive is still run [#40868280531](https://github.com/MaksimBlud/football-ai/actions/runs/40868280531), artifact 12894054589, ZIP SHA-256 b4b1144ca28414ccf7a5a7a5c02fde4611e8e0f1a37997012de031a38baa14b0. Its manifest records only 80 gate identities and its current-season CSV ends 2026-10-28. It therefore does not cover the current 90-identity gate and must not be used for a new current-form calculation. A fresh post-#699 source capture and full identity/SHA coverage proof are required.

### Fresh strictly pre-match odds audit

Read-only public.odds_snapshots aggregation enforced snapshot_time_utc < commence_time_utc:

- total rows: 3,966;
- strictly pre-match rows: 3,915;
- future fixtures with a saved strictly pre-match quote: 0;
- latest Serie A pre-match quote: 2026-10-13 14:48:53.042620 UTC;
- no league has a saved strictly pre-match quote in the last seven days.

Per-league latest saved strictly pre-match quote: EPL 2026-10-09; Serie A 2026-10-13; Bundesliga, Eredivisie, La Liga and Ligue 1 2026-09-11; RPL 2026-09-05; Primeira Liga and Turkey Super Lig 2026-09-11. No odds values or outcomes were read by this audit.

public.model_artifact_bundles currently contains 0 registered bundles, so the frozen incumbent blocker remains unresolved.

### Required next proof

1. HUMAN-MERGE #699 at exact head 3e772c859bf3538a492aaffc314be533285d7db0.
2. Verify the new main SHA; then obtain a fresh source artifact on main.
3. Verify all 11 source CSV hashes, the exact 90-identity set/count/SHA, and gate → source observation → archive ordering.
4. Run both existing forward-only V2 workflows on the resulting main SHA. Existing stale quotes must remain blocked; do not backfill.
5. Wait for genuinely new strictly pre-kickoff quotes. Only then may a new original-V2 research shadow be captured.
6. Keep the separate 30-eligible-prospective-forecast outcome gate closed until its frozen conditions are met, and resolve the non-legacy incumbent reference without changing the parent protocol.

Frozen candidate remains a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6; the 19-feature/weight contract, active_lambda=0, and research-only shadow_lambda=1 are unchanged. No target outcomes were read/scored, no paid provider call, no Supabase write/DDL, no production .pkl change, no merge, no promotion, and no schedule change.


## 2026-10-30 10:56 UTC — canonical identity digest serialization cross-check

A fresh read-only Supabase query selected only `match_date, home_team, away_team` from `public.league_finished_results` for Serie A 2026/27 with dates before 2026-10-30. It selected no score, goal, result, settlement, or target-outcome fields.

- Raw rows: **93**.
- Canonical identities after the frozen runtime aliases (`Inter → Inter Milan`, `Milan → AC Milan`, `Roma → AS Roma`, plus V2-local `Atalanta BC → Atalanta`): **90**.
- Latest date: **2026-10-29**.
- Reversed canonical fixture pairs: **0**.
- The three-row raw-to-canonical reduction is the duplicate Atalanta/Atalanta BC spelling, not three additional fixtures.

The audit explicitly checked the two different digest serializers currently present in the open research branches. They must not be compared as if they were the same hash:

1. The prospective evaluator's `_sha_fixture_set` uses compact JSON arrays (`json.dumps(sorted_identities, ensure_ascii=False, separators=(",", ":"))`). SQL/pgcrypto recomputation over the exact current 90-identity set produced **`09442a8a74c0471e3b6ae161d39cd73e1015fc5d541c994a09134555cc720c93`**.
2. The source-capture helper `_fixture_identity_sha256` uses sorted tab-delimited identity rows joined by LF. SQL/pgcrypto recomputation over the same set produced **`95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`**.

Both counts are 90 and the different hashes are expected because the byte serializations differ. The previously recorded manual digest `7c91dad874222ff98e6cce033ce36c71c51306b5979a7854ff8c3c60eab36bce` was not reproduced by either exact in-repository serializer against this fresh result; retain it only as a historical note, not as a current attestation. The post-#699 on-main source artifact must publish its own algorithm-labelled gate/source digests and prove exact set equality before any current-form feature calculation is admitted.

This is a metadata/hash audit only. The last source archive still records 80 gate identities and ends at 2026-10-28; the current gate has 90 identities through 2026-10-29, so that archive remains stale for this set. Saved odds remain unchanged (3,966 total / 3,915 strictly pre-kickoff / zero future strictly pre-kickoff rows), so no new prospective forecast or quality metric exists. No target outcomes were read, no paid call, Supabase write/DDL, production `.pkl` change, merge, or schedule change occurred.

**Next:** HUMAN-MERGE #699 at its exact live API head, then run the existing source capture on the resulting `main` and verify both serializer-labelled digests against the actual archive and current metadata identities. Do not backfill old quotes or open the separate 30-eligible-prospective-forecast outcome gate.


## 2026-10-30 11:43 UTC — live source archive and canonical identity parity

A fresh scheduled **Current-Form Source Capture** ran on unchanged main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`:

- Source run [#41049950849](https://github.com/MaksimBlud/football-ai/actions/runs/41049950849), created 2026-10-30 11:42:02 UTC, completed 11:43:04 UTC; exact main SHA above.
- Offline regression step: **19 passed**.
- Source manifest: 10 frozen old-season CSVs plus current `2627/I1.csv`; current completed prior-day rows **90**; historical old-season rows **3,800**; combined history rows reported by the forward verifier **3,890**.
- Feature-input gate read only `match_date, home_team, away_team`, observed **90** unique primary identities against the fixed minimum 30. It selected no score/result fields.
- Current CSV SHA-256 from manifest and independently recomputed bytes: `32ca618587c90db25f16ea647cb55060f519c03830a1e8ec4a6c4204e27d5135`.
- Source artifact ID **12973598320**; GitHub Actions artifact digest and independently downloaded ZIP SHA-256 both equal `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`. The ZIP contains the 11 CSVs and the source manifest; all 11 CSV byte hashes independently match their manifest entries.
- Source observation: **11:42:59.273193 UTC**; archive creation: **11:42:59.333069 UTC**; parent workflow completed: **11:43:04 UTC**.

The automatic **Current-Form Forward-Only Preview** then ran from that successful main-branch parent:

- Run [#41050080529](https://github.com/MaksimBlud/football-ai/actions/runs/41050080529), created 11:43:07 UTC and completed 11:43:50 UTC.
- Offline regression step: **53 passed**.
- It downloaded and verified the exact source artifact and parent run; source age at verification was **44 seconds**.
- Forward artifact ID **12974157310**; GitHub digest and independently downloaded ZIP SHA-256 both equal `80df126dc31e3de9280a396fe48e2e4f04a6f600db8bafc75a2f547f98f9b394`.
- Report: `status=VERIFIED`, `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, `production_or_supabase_writes=0`, `paid_provider_calls=0`, `no_bet=true`. There were no eligible quotes, so no probability vector or forecast was emitted. This is source/forward provenance proof, **not** model-quality evidence.

### Independent source/gate identity-set parity

A fresh read-only Supabase query again selected only the three approved identity columns for Serie A 2026/27 before 2026-10-30:

- Raw metadata rows: **93**.
- Canonical unique identities: **90**.
- Canonicalization exactly follows the existing runtime aliases `Inter → Inter Milan`, `Milan → AC Milan`, `Roma → AS Roma`, `Verona → Hellas Verona`, plus the V2-local `Atalanta BC → Atalanta`.
- SQL/pgcrypto SHA-256 of sorted tab-delimited canonical identities joined by LF: `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`.
- Independently recomputed from the actual archived `serie_a_2627.csv` identity columns using the same aliases and serializer: **90** identities and the exact same SHA-256 `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`.

This resolves the apparent source-vs-gate digest mismatch in the earlier ad-hoc comparison: that CSV-side calculation applied only the Atalanta alias and omitted the four existing `SERIE_A_ALIASES` mappings. The in-repository canonicalizer applies all five mappings. The old manual digest `7c91dad874222ff98e6cce033ce36c71c51306b5979a7854ff8c3c60eab36bce` remains unreproduced and must not be used as an attestation. The canonical 90-event identity set is now independently matched between current Supabase metadata and the actual downloaded source CSV.

**Scope limitation:** both live workflow runs used old main SHA `40887ebb...`; main's source manifest does not yet persist the identity digests. This independent parity check mirrors the canonicalizer/serializer now present in open PR #699, but it is **not** a post-merge live execution of #699. PR #699 remains open at exact HEAD `3e772c859bf3538a492aaffc314be533285d7db0`, with all seven exact-head checks SUCCESS. After HUMAN-MERGE, rerun the source workflow and require the new manifest to publish and the forward verifier to recalculate both identity digests before treating the guard as live-proven.

### Quotes and scheduled workflow timing

A fresh read-only aggregation of `public.odds_snapshots` with strict `snapshot_time_utc < commence_time_utc` returned **zero rows in the last seven days**. Consequently, the successful forward run had no new pre-kickoff quote and correctly emitted no shadow.

The source-capture schedule nominally targets 05:50 UTC but its run was created at 11:42:02 UTC; the forward preview followed at 11:43:07 UTC via `workflow_run`. In the latest main-run page checked at 11:55 UTC, no 2026-10-30 run was present for the separate Free Real-Quote Diagnostic or Original Forward-Only workflow. This is a bounded observation only, not proof that either workflow is disabled. No schedules or settings were changed.

The separate 30-eligible-prospective-forecast target-outcome gate remains CLOSED; the frozen non-legacy incumbent is still absent. Candidate SHA, 19 features/weights, active lambda 0 and research-only shadow lambda 1 remain unchanged. No target outcomes were read for evaluation, no paid calls, no Supabase writes/DDL, no production `.pkl` change, no merge or promotion.


## 2026-10-30 12:48 UTC — independently downloaded current-form artifacts; no new quote

Fresh GitHub API read still shows `main=40887ebb215730190d7a6c7a1693373ec4afcdfc`; no V2 PR was merged. The current-form runs below are genuine old-main runtime evidence, not post-#699 guard proof.

- **Current-Form Source Capture** [run #41049950849](https://github.com/MaksimBlud/football-ai/actions/runs/41049950849) completed SUCCESS on that exact main SHA. Its test step passed **19** tests. Artifact **12973598320**, GitHub ZIP SHA-256 `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`. Independently downloaded ZIP recomputed to the same SHA. It contains 10 historical CSVs (3,800 rows), current `serie_a_2627.csv` (90 completed prior-day rows), and one manifest. All **11/11** CSV SHA-256 values independently recomputed from archive bytes match the manifest. The manifest records feature-input gate count 90, metadata-only selected fields `match_date,home_team,away_team`, frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 0 paid calls, 0 Supabase writes, and no target-outcome reads/scoring.
- Manifest limitation: this old-main artifact records the gate count but does not yet contain `gate_fixture_identity_sha256`, the explicit canonical identity list, or exact gate-to-CSV coverage fields. Independently, after capture I re-read only `match_date,home_team,away_team` from `public.league_finished_results` and only `Date,HomeTeam,AwayTeam` from the archived current-season CSV, applied the exact existing Serie A aliases plus V2-local `Atalanta BC → Atalanta`, and recomputed the same sorted tab/LF identity digest on both sides: **90 unique identities / exact SHA-256 `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811` on Supabase and CSV**. This is an independent external parity audit, not an in-manifest attestation and not post-#699 runtime proof. PR #699 adds the canonical identity list/SHA and fail-closed exact coverage check; that guard still requires HUMAN-MERGE and a fresh main capture.
- **Current-Form Forward-Only** [run #41050080529](https://github.com/MaksimBlud/football-ai/actions/runs/41050080529) completed SUCCESS on the same main SHA; **53** tests passed. It independently verified source artifact 12973598320 and parent run 41049950849, including parent path/SHA/status and source ZIP digest. Parent completion was `11:43:04Z`; forward verification was `11:43:43Z`; source age was 44 seconds. Artifact **12974157310**, ZIP SHA-256 `80df126dc31e3de9280a396fe48e2e4f04a6f600db8bafc75a2f547f98f9b394`, independently recomputed. Report: `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, 0 paid calls and 0 writes. The source is VERIFIED, but no actual forecast was produced because no saved quote existed.
- **Free Real-Quote Diagnostic** [run #41057970063](https://github.com/MaksimBlud/football-ai/actions/runs/41057970063) completed SUCCESS at 12:48Z; **53** tests passed. Artifact **12978111278**, ZIP SHA-256 `dd9c9fd43b61f78075bee68b016507d5d766733099e532b79131d566125716da`, independently recomputed. This is the separate old-season-only diagnostic: 10 historical CSVs / 3,800 rows, 0 quoted fixtures, 0 diagnostic scores, no 2026/27 CSV and mode `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`. It must not be counted as current-form V2 forecast evidence.
- Fresh read-only odds metadata query: 3,966 total saved rows, 3,915 with `snapshot_time_utc < commence_time_utc`, **0** strict pre-match rows in the last 24 hours or 7 days, latest strict pre-match snapshot `2026-10-13 14:48:53.042620Z`, and 0 future events with a saved strict pre-match quote. Query selected timestamp/aggregate fields only.
- PR #699 remains open at exact head `3e772c859bf3538a492aaffc314be533285d7db0`, with 7/7 exact-head workflow runs SUCCESS, including **229 Original V2 shadow tests**. It contains the source identity-set digest and exact coverage guard missing from today's old-main manifest. PR #694 adds overlapping gate-identity coverage logic and is a subset/overlap; do not merge #694 separately while #699 remains the consolidated guard candidate. PR #697 remains documentation-only and HUMAN-MERGE.
- No prospective quote or V2 shadow forecast was created. The separate 30-completed-prospective-forecast outcome gate remains CLOSED; no target outcomes were read/scored and no Brier/LogLoss claim is available. No paid request, Supabase write/DDL, production `.pkl` change, refit, threshold tuning, bet, publication, promotion, schedule change, or main merge occurred.

Next permitted proof: HUMAN-MERGE #699 at the exact tested head, verify the resulting main SHA, then rerun source capture and confirm the manifest includes the canonical gate identity set/SHA and zero missing gate fixtures before running either forward reader.


## 2026-10-30 19:55 UTC — fresh exact-head, source runtime, and pre-match registry checkpoint

Fresh GitHub API reads confirm default branch `main=40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main mutation occurred.

### Current-form source and forward runtime on unchanged main

- **Current-Form Source Capture** [run #41049950849](https://github.com/MaksimBlud/football-ai/actions/runs/41049950849): SUCCESS on the exact main SHA above; **19 tests passed**. The runtime log reports frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, metadata-only feature-input gate count **90**, completed prior-day current-season CSV rows **90**, 10 old-season CSVs / 11 total source files, zero paid calls, zero Supabase writes, and no target-outcome scoring. Artifact **12973598320**, GitHub SHA-256 `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`.
- **Current-Form Forward-Only Preview** [run #41050080529](https://github.com/MaksimBlud/football-ai/actions/runs/41050080529): SUCCESS on the same main SHA; **53 tests passed**. It authenticated source artifact 12973598320 and parent run 41049950849; source age at verification was **44 seconds**. Artifact **12974157310**, GitHub SHA-256 `80df126dc31e3de9280a396fe48e2e4f04a6f600db8bafc75a2f547f98f9b394`. Runtime report: `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes not read/scored, paid calls 0, writes 0. Source provenance passed, but no forecast or probability vector was created.
- **Free Real-Quote Diagnostic** [run #41057970063](https://github.com/MaksimBlud/football-ai/actions/runs/41057970063): SUCCESS; **53 tests passed**; 0 quoted fixtures, 0 diagnostic scores, 0 paid provider requests, 0 Supabase writes. Artifact **12978111278**, GitHub SHA-256 `dd9c9fd43b61f78075bee68b016507d5d766733099e532b79131d566125716da`. This is old-season diagnostic evidence, not a prospective V2 forecast.

The 11:43 UTC source artifact was created on old main, whose manifest records the 90-event gate count but does not yet persist the canonical gate identity list/SHA or exact gate-to-CSV coverage. The prior independent metadata-only parity audit in this continuity file found 90/90 canonical identities and matching tab/LF SHA-256 `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`; that external cross-check is not a substitute for the in-manifest guard. PR #699 supplies that missing fail-closed attestation, which still requires HUMAN-MERGE and a fresh main capture.

### Exact open V2 PR heads and CI

- **#699** remains open, base main above, current API HEAD `3e02ad265306a5dd9347b7ac4b310adb746ca68d`; **7/7 exact-head checks SUCCESS**, including [Original V2 Shadow Tests #41111939589](https://github.com/MaksimBlud/football-ai/actions/runs/41111939589) with **236 passed** and the production `*.pkl` diff guard. It includes the source identity-set SHA/control-character hardening and `github.ref == refs/heads/main` job guards for all four existing secret-bearing V2 workflows.
- The current-main versions of Original Forward-Only, Current-Form Source Capture, Current-Form Forward-Only, and Free Real-Quote Diagnostic still lack the complete main-ref job guard. Do not manually dispatch these secret-bearing workflows from a feature branch. #699 is the consolidated fix; use its current API HEAD above, not older SHA strings in the PR description/comments.
- **#697** is documentation-only and remains HUMAN-MERGE; this update records the latest verified state.
- **#701** remains open at `7ee3eda3f396735e00737d8e8e42e0c8c146c57f`, **6/6** exact-head checks SUCCESS. Its prospective evaluator correctly remains fail-closed because no approved non-legacy frozen incumbent reference/vector exists.
- **#702** remains open at `b91773b6677bd2be7df67d5b2c69c27b9a202397`, **7/7** exact-head checks SUCCESS. Its manual-only, main-only, one-request zero-credit `/events` probe is fixture metadata/19-feature readiness only; it does not request odds or emit probabilities. No live request has been made.

### Fresh read-only Supabase pre-match audit

Only saved market snapshot timestamps/kickoffs and pre-match prediction metadata were queried; no scores, results, settlements, or target-outcome fields were selected.

- `public.odds_snapshots`: **3,966** total rows; **3,915** satisfy strict `snapshot_time_utc < commence_time_utc`; **0** strict pre-match snapshots in the last 24 hours or 7 days; **0** future fixtures with a saved strict pre-match quote. Latest Serie A snapshot remains **2026-10-13 14:48:53.042620 UTC**.
- `public.product_prediction_snapshots`: **40** strict pre-match rows, all EPL / `EPL_AI_MARKET_PAIR_V1`; **0** Serie A incumbent rows.
- `public.model_artifact_bundles`: **0** registered bundles.

Therefore there is still no fresh saved quote and no valid Serie A frozen incumbent. The 30-eligible-completed-prospective-forecast outcome gate remains CLOSED. No Brier/LogLoss evaluation or V2-over-market claim is available.

Frozen candidate, original 19-feature order/weights, `active_lambda=0` market baseline, research-only `shadow_lambda=1`, NO_BET and both embargoes remain unchanged. No target outcomes read/scored, no paid calls, no Supabase writes/DDL, no production `.pkl` change, no refit, no threshold tuning, no merge, no promotion, and no schedule/other-agent changes.

**Next proof:** HUMAN-MERGE #699 at exact HEAD `3e02ad265306a5dd9347b7ac4b310adb746ca68d`; verify the resulting main SHA; rerun source capture and require the manifest to attest the exact canonical gate identity set/count/SHA and zero missing fixtures; then rerun both forward-only readers. Keep the old quotes blocked and the evaluation gate closed.


## 2026-10-30 21:57 UTC — independently rechecked latest main runtime artifacts and source identity parity

Fresh GitHub metadata still shows `main=40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge occurred. This is a read-only runtime audit plus a continuity update on this documentation PR branch only.

### Latest actual main workflow runs

- **Current-Form Source Capture** [run #41049950849](https://github.com/MaksimBlud/football-ai/actions/runs/41049950849): job SUCCESS, 19 tests passed. Artifact **12973598320** was downloaded again; its ZIP SHA-256 recomputed locally is `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`. It contains ten historical CSVs (3,800 rows), current `serie_a_2627.csv` (90 completed prior-day rows), and the source manifest. All **11/11** individual CSV SHA-256 values match the manifest; current CSV raw SHA is `32ca618587c90db25f16ea647cb55060f519c03830a1e8ec4a6c4204e27d5135`. The frozen candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`. The old-main manifest still records only gate count 90, not the canonical gate identity list/SHA.
- **Current-Form Forward-Only Preview** [run #41077147924](https://github.com/MaksimBlud/football-ai/actions/runs/41077147924): job SUCCESS, **53 tests passed**. Artifact **12987716790**, ZIP SHA-256 `90ad2e9e026762db807b42f5165697e03a7257bdc6a331101a6b27df0a07376a`. It verified source artifact 12973598320, its successful main parent run, and candidate SHA; source age at verification was 12,058 seconds (within the fixed 24-hour limit). Runtime report: `quotes_seen=0`, `v2_current_form_shadow_captured=0`, no target outcomes read/scored, zero paid calls and zero writes. This is a real source-artifact verification, not a quote-level source-before-quote forecast.
- **Original old-season Forward-Only** [run #41076521488](https://github.com/MaksimBlud/football-ai/actions/runs/41076521488): job SUCCESS, **71 tests passed**. Artifact **12988120716**, ZIP SHA-256 `0283dd379d41843a12f4b287ace9f9f2e8f1a8a695fc1bad7633904a46443c59`. It authenticated the separate old-season source artifact from Free Diagnostic run #41057970063; `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, and `forecasts_created=0`.
- **Free Real-Quote Diagnostic** [run #41057970063](https://github.com/MaksimBlud/football-ai/actions/runs/41057970063): job SUCCESS, **53 tests passed**. Artifact **12978111278**, ZIP SHA-256 `dd9c9fd43b61f78075bee68b016507d5d766733099e532b79131d566125716da`; ten historical CSVs / 3,800 rows, zero quoted fixtures, zero diagnostic scores, no 2026/27 current-season CSV, zero paid requests and zero writes. It is not current-form prospective forecast evidence.

### Independent current-source identity parity

A fresh read-only Supabase query selected only `match_date, home_team, away_team` for Serie A 2026/27 through the exclusive UTC cutoff 2026-10-30. It returned **93 raw rows / 90 canonical unique fixture identities** after the existing aliases (`Inter → Inter Milan`, `Milan → AC Milan`, `Roma → AS Roma`, `Verona → Hellas Verona`) and V2-local `Atalanta BC → Atalanta`.

Using the exact sorted tab-delimited identity tuples joined by LF, SQL/pgcrypto computed SHA-256 `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`. The same serialization independently recomputed from the downloaded current-season CSV produced **90 identities and the exact same SHA-256**. This confirms 90/90 parity for this source snapshot. It remains an external cross-check: the old-main artifact manifest does not persist that digest. PR #699 adds the in-manifest identity list/count/SHA and fail-closed gate-to-source coverage check; a fresh post-merge main capture is still required.

### Current quote availability and PR coordination

A read-only strict pre-match query (`snapshot_time_utc < commence_time_utc`) across the nine stored league groups returned **3,966** total snapshots, **3,915** strict pre-match rows, **0** future events with a saved strict pre-match quote, and no strict pre-match snapshots in the last 24 hours or seven days. Latest Serie A strict pre-match snapshot remains **2026-10-13 14:48:53.042620 UTC**. No outcomes/results/settlements were selected.

Current exact PR heads and CI:
- **#699** `3e02ad265306a5dd9347b7ac4b310adb746ca68d`: **7/7 SUCCESS**, including 236 Original V2 shadow regression tests and the production `*.pkl` diff guard. Its branch contains the historical exact-HTTPS/no-redirect and bounded-streaming fix plus regressions also present in older #700; #699 is the consolidated review target, so do not merge #700 separately. It also supplies the missing source identity SHA/coverage guard and main-ref job guards for all four secret-bearing V2 workflows.
- **#701** `7ee3eda3f396735e00737d8e8e42e0c8c146c57f`: **6/6 SUCCESS**. The prospective evaluator remains fail-closed because no approved non-legacy frozen incumbent reference/vector is pinned.
- **#702** `b91773b6677bd2be7df67d5b2c69c27b9a202397`: **7/7 SUCCESS**. Its live probe is manual-only/main-only and requests only one documented zero-credit `/events` metadata response after source verification; it does not request odds or emit probabilities. No live request was made in this audit.
- **#697** is documentation-only; this commit adds the above verified run/artifact details to this PR branch.

### Security warning

Fresh Supabase schema inventory still reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. This is a critical access-control warning for anon/authenticated roles. No DDL was run; enabling RLS without reviewed policies can block legitimate application access.

The original 19-feature order/weights, frozen candidate, `active_lambda=0` market fallback, research-only `shadow_lambda=1`, NO_BET and both evaluation/source embargoes remain unchanged. No paid request, Supabase write/DDL, protected target-outcome read, production `.pkl` change, merge, refit, threshold tuning, promotion, schedule change, or other-agent setting change occurred.


## 2026-10-30 22:49 UTC — current-form CSV has no upcoming fixtures; quote source remains empty

A fresh read-only audit was performed against the exact main source archive and Supabase metadata/market tables. No main ref, schedule, model, or database state was changed.

- Source archive: Current-Form Source Capture run [#41049950849](https://github.com/MaksimBlud/football-ai/actions/runs/41049950849), artifact **12973598320**, ZIP SHA-256 `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`. The current-season CSV `serie_a_2627.csv` contains **90 rows** dated 2026-08-22 through 2026-10-29. A metadata-only scan found **zero unplayed/future fixture rows** (no rows with both full-time goal fields absent). Its manifest records 90 completed prior-day rows, the unchanged frozen candidate SHA, 19 original features, and no outcome evaluation, paid calls, or Supabase writes. This source supplies lagged historical features, but not upcoming fixture IDs.
- Therefore the separate PR [#702](https://github.com/MaksimBlud/football-ai/pull/702) remains the only reviewed path in this workstream for future fixture metadata without odds: manual dispatch on `main` only, one `/events` request, strict zero-credit response-header attestation, no odds fields, no probabilities, and original 19-feature readiness only. Its exact HEAD `b91773b6677bd2be7df67d5b2c69c27b9a202397` has **8/8 check runs SUCCESS** (the check API returns two same-named offline-contract checks). No live provider request was made. HUMAN-MERGE remains required.
- Fresh read-only `odds_snapshots` audit at 22:49 UTC: **3,966** total rows, **3,915** with `snapshot_time_utc < commence_time_utc`, **0** in the last 24 hours, **0** in the last 7 days, and **0** future events with a strictly pre-kickoff quote. Latest Serie A snapshot remains **2026-10-13 14:48:53.042620 UTC**.
- Serie A `league_prediction_ledger` still contains **630** `MARKET_ONLY / CALIBRATION_REQUIRED` rows and **0** future pre-kickoff rows. `model_artifact_bundles` contains **0** registered bundles. This is not an independent frozen incumbent and must not be substituted for one.
- The current source artifact and forward previews remain technically successful but have `quotes_seen=0`, `v2_current_form_shadow_captured=0`, and `forecasts_created=0`. No prospective V2 observation or metric exists.

This is a source-availability finding, not a model-quality result. Keep `active_lambda=0`, `shadow_lambda=1` research-only, the 30-eligible-prospective-forecast outcome gate CLOSED, and the frozen 19-feature/weight contract unchanged.


## 2026-10-30 23:58 UTC — free fixture preview now requires live current-gate identity parity

A further integration audit found that the open free fixture preview (#702) called `verify_latest_source_archive()` without supplying the current completed-fixture identity set. The consolidated source guard in #699 deliberately marks source freshness false when that live metadata-only gate is not supplied. Thus the preview would safely fail closed after #699 merged, but could never reach the intended fixture metadata request.

Updated PR [#702](https://github.com/MaksimBlud/football-ai/pull/702) on exact HEAD `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`:

- Before archive discovery or any provider request, the workflow now requires a read-only Supabase identity query selecting exactly `match_date, home_team, away_team` for the Serie A 2026/27 completed-fixture gate.
- It passes the canonical identity set into #699's `verify_latest_source_archive(current_gate_identities=...)` contract and requires the current gate to be fresh, the archived gate identity list/count/SHA to be verified, all gate identities to be covered by the archived current-season CSV, and zero missing identities.
- If #699's identity reader or verifier API is not yet present on main, #702 fails closed before archive discovery and before the provider request. No compatibility fallback weakens the source gate.
- The output records the gate/source identity attestations and explicitly states that Supabase access is limited to the three metadata fields, with zero writes and zero DDL.
- The live workflow remains `workflow_dispatch` only, main-ref only, no cron, no workflow-run trigger, and exactly one `/events` metadata request only after source verification. It requests no odds and requires `x-requests-last: 0`. No live request was made during this change.

Exact-head validation on `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`: **8/8 SUCCESS**:
- Ligue 1 validation #41147422463
- Research PR validation #41147422438
- Product contract tests #41147422447
- Serie A validation #41147422430
- Dedicated offline fixture tests #41147422466 — **22 passed**
- Targeted research tests #41147422416 — final no-production-artifact check passed
- Bundesliga validation #41147422421
- Push offline fixture tests #41147417948 — **22 passed**

The research validation log also confirms `git diff --exit-code -- '*.pkl'` passed. These are offline/mocked and CI checks only; they are not a live fixture capture, forecast, or model-quality result.

Merge order remains HUMAN-MERGE: **#699 first**, then a fresh successful Current-Form Source Capture on the resulting main SHA (the old pre-#699 archive lacks the new persisted gate identity SHA), then **#702**. Do not manually dispatch #702 until that new archive is verified. PR #701 remains separately gated by the absence of a valid frozen incumbent and 30 eligible completed prospective forecasts.

Fresh read-only Supabase audit at this run found no future fixture metadata in `public.matches`, no future strictly pre-kickoff odds rows, and no new strict pre-match quote in the last 24 hours or 7 days. The market snapshot inventory remains 3,966 total / 3,915 strictly pre-match; latest Serie A quote remains 2026-10-13 14:48:53.042620 UTC. `model_artifact_bundles` remains empty. No protected target outcomes were selected or read.

The original frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, its 19 feature names/order, weights, `active_lambda=0`, research-only `shadow_lambda=1`, and NO_BET behavior remain unchanged. No main merge, paid request, Supabase write/DDL, production `.pkl` change, outcome read, refit, threshold tuning, promotion, schedule change, or other-agent setting change occurred.


## 2026-10-31 — Correct Serie A metadata source, 90-identity gate SHA, and fresh runtime audit

This update corrects the scope of the prior note that found no Serie A fixtures in `public.matches`: that table currently contains EPL rows only and is **not** the V2 current-form feature-input gate source. The original V2 source-capture code queries `public.league_finished_results` read-only, selecting exactly `match_date,home_team,away_team` for `league='SERIE_A'`, `season='2026-2027'`, and the configured season/date cutoff. Do not interpret an empty Serie A query against `public.matches` as absence of Serie A metadata.

### Live metadata-only gate audit (Supabase read-only, observed 2026-10-31 00:58 UTC)

- Raw `league_finished_results` rows for 2026/27 from 2026-07-01 through (exclusive) 2026-10-31: **93**.
- Raw ordered identities: **93**; raw unordered fixture pairs: **93**.
- After the frozen V2-local identity aliases (`Atalanta BC -> Atalanta`, plus the four existing runtime aliases), canonical unique identities: **90**.
- Exactly three duplicate alias pairs collapse: 2026-08-23 Atalanta–Sassuolo; 2026-08-31 Atalanta–Bologna; 2026-09-05 AS Roma–Atalanta.
- Canonical identity SHA-256, using sorted `date<TAB>home<TAB>away` rows joined by LF: **`95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`**.
- First/last metadata dates: 2026-08-22 / 2026-10-29. All 90 canonical identities precede the 2026-10-31 UTC cutoff and exceed the unchanged 30-event **feature-input** minimum.

The canonical SHA exactly matches the previously independently recorded 90-row CSV identity SHA. This is a reconciliation of the live metadata set with prior evidence, **not** a substitute for the new persisted identity attestation required by #699: the existing main archive predates that manifest contract, so a fresh source capture on the post-#699 main SHA remains mandatory before #702 may run.

### Actual GitHub Actions runtime (main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`)

- [Current-Form Source Capture #41049950849](https://github.com/MaksimBlud/football-ai/actions/runs/41049950849) completed SUCCESS on 2026-10-30 11:43 UTC. Its job log reports feature gate **90**, current-season completed prior-day CSV rows **90**, 10 frozen historical CSVs, 11 total source CSVs, candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, zero paid calls, zero Supabase writes, and no target outcomes scored. Artifact **12973598320**, GitHub ZIP SHA-256 `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`.
- [Current-Form Forward-Only #41077147924](https://github.com/MaksimBlud/football-ai/actions/runs/41077147924) completed SUCCESS on 2026-10-30 15:04 UTC. It independently verified artifact 12973598320, parent run 41049950849, ZIP digest, 90 current-season rows and 3,890 total historical rows. But `quotes_seen=0`, `v2_current_form_shadow_captured=0`; no inference occurred.
- [Original Forward-Only #41076521488](https://github.com/MaksimBlud/football-ai/actions/runs/41076521488) completed SUCCESS; `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`. This is source/contract runtime proof, not prediction-quality evidence.

### Current market/incumbent availability (read-only, pre-match fields only)

- `public.odds_snapshots`, `SERIE_A`: **625** snapshots / **63** event IDs; **620** strictly pre-kickoff; **0** future strictly pre-kickoff snapshots. Latest saved quote: **2026-10-13 14:48:53.042620 UTC**.
- `public.league_prediction_ledger`, `SERIE_A`: **630** rows, all `MARKET_ONLY / CALIBRATION_REQUIRED`; latest prediction/market snapshot 2026-10-13 14:48:53.042620 UTC; latest kickoff 2026-10-25 19:45 UTC.
- `public.model_artifact_bundles`: **0** registered bundles. No independent frozen incumbent is currently available from this registry.

The feature-input gate is therefore satisfied at 90 canonical completed identities, but the separate prospective evaluation gate remains CLOSED: there are no new eligible prospective V2 forecasts, and the required **30 completed primary forecasts** have not been accumulated. No target outcomes were selected or read in this audit. Existing October 13 quotes remain stale and cannot be backfilled.

### PR coordination / next proof

At this audit: #699 exact HEAD `3e02ad265306a5dd9347b7ac4b310adb746ca68d` had 7/7 PR workflow runs SUCCESS; #702 exact HEAD `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e` had 8/8 validation/test runs SUCCESS (including both 22-test offline fixture runs); #701 exact HEAD `7ee3eda3f396735e00737d8e8e42e0c8c146c57f` had 6/6 validation runs SUCCESS; #697's prior HEAD `3fbc29f52d91aa35c5f0e0383a5dd78128cc5570` had 7/7 SUCCESS. All remain HUMAN-MERGE. Required order: human merge #699; verify fresh main; obtain a new source capture whose manifest persists gate identity list/count/SHA and whose CSV covers all 90 current canonical identities; only then manually dispatch #702's zero-credit `/events` metadata-only preview. #702 emits no probabilities and does not count toward the 30-event evaluation gate. #701 remains closed until eligible prospective forecasts and a valid frozen incumbent exist.

No merge, main mutation, paid request, Supabase write/DDL, production `.pkl` change, protected outcome read, model refit, weight/feature/lambda change, betting, promotion, schedule change, or other-agent setting change occurred.


## 2026-10-31 03:58 UTC — identity-only metadata response hardening and artifact-download failure-path proof

A fresh review of the consolidated original-V2 source/forward branch found two fail-closed gaps in the current-form metadata reader: date parsing sliced the first ten characters of a string (so a noncanonical suffix could be silently ignored), and rows returned by the identity-only Supabase select were not checked for unexpected extra fields. This mattered to the protected-outcome embargo: if a proxy/client ever returned a result/score field despite the explicit select list, the reader would ignore the field instead of rejecting the response.

Updated consolidated PR [#699](https://github.com/MaksimBlud/football-ai/pull/699) to exact HEAD `e760994249b488a3693116974963509b85788bb6`:

- Both the count gate and identity-set/SHA gate now require the exact row-key allowlist `match_date, home_team, away_team`; any additional field (including `result`, `home_goals`, or `score`) fails closed.
- Metadata date strings must be canonical `YYYY-MM-DD`; timestamp suffixes, arbitrary trailing text, and compact alternate forms are rejected rather than truncated.
- The current-form GitHub artifact downloader now rejects a missing Actions read token before making a request.
- Original and current-form artifact download regression tests now cover malformed Content-Length, empty streams, HTTP-error cleanup, and missing-token behavior. The existing declared-size and streamed-overrun tests remain in place.

Exact-head CI on `e760994249b488a3693116974963509b85788bb6`: **7/7 SUCCESS**:
- Original V2 Shadow [#41166528822](https://github.com/MaksimBlud/football-ai/actions/runs/41166528822) — **256 passed**; `git diff --exit-code -- '*.pkl'` passed.
- Research [#41166528793](https://github.com/MaksimBlud/football-ai/actions/runs/41166528793)
- Serie A [#41166528855](https://github.com/MaksimBlud/football-ai/actions/runs/41166528855)
- Bundesliga [#41166528806](https://github.com/MaksimBlud/football-ai/actions/runs/41166528806)
- Ligue 1 [#41166528814](https://github.com/MaksimBlud/football-ai/actions/runs/41166528814)
- Eredivisie [#41166528812](https://github.com/MaksimBlud/football-ai/actions/runs/41166528812)
- Product [#41166528789](https://github.com/MaksimBlud/football-ai/actions/runs/41166528789)

The fresh metadata-only Supabase query again returned **93 raw rows / 90 canonical unique identities** through 2026-10-29 (exclusive cutoff 2026-11-01), selecting only `match_date, home_team, away_team`. The previously independently verified canonical identity SHA remains `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`; this run rechecked count/date parity, not a new SHA recomputation.

The fresh Serie A odds query selected only strict pre-match rows (`snapshot_time_utc < commence_time_utc`): **620** total, **0** in the last 24 hours, **0** in the last 7 days, and **0** future events with a saved pre-kickoff quote. Latest strict pre-match quote remains **2026-10-13 14:48:53.042620 UTC**. The model artifact registry still contains **0** bundles, so no approved non-legacy frozen incumbent is available to pin.

PR #703's bounded-download patch overlaps materially with the two artifact `get_archive` functions already modified in #699. #699 now has the stricter current-form ZIP uncompressed-member/aggregate caps as well. A coordination comment was added to #703: do not merge it independently; after HUMAN-MERGE of #699, rebase/compare and retain only a genuinely distinct guard (currently explicit non-bytes chunk rejection) if still needed.

Scientific status is unchanged: the 90-event feature-input gate is open, but there are **0** eligible new prospective V2 forecasts, no pinned non-legacy incumbent, and the outcome/evaluation gate remains CLOSED. The original candidate SHA, frozen 19 features/order/weights, `active_lambda=0`, research-only `shadow_lambda=1`, and all embargoes remain unchanged. No target outcomes were selected/read/scored; no paid request, Supabase write/DDL, production `.pkl` change, refit, threshold tuning, promotion, betting, merge, schedule change, or other-agent setting change occurred.


---

# Continuity update — 2026-10-31 06:00 UTC — exact V2 CI, source identity and dependency reproducibility

## Repository state

- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; the current main branch has not moved.
- Main `PROJECT_CONTINUITY.md` blob SHA at this audit: `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`.
- This update is documentation on the existing #697 branch only. No main merge or mutation.

## Exact open V2 PR heads and CI

| PR | Exact current HEAD | Required CI | Dedicated evidence |
|---|---|---:|---|
| #699 source/clock/identity/outcome guards | `e760994249b488a3693116974963509b85788bb6` | 7/7 SUCCESS | Frozen V2 shadow: 256 passed; production `*.pkl` diff guard passed |
| #697 continuity | `dc490b83dd8c1d3bc647c0745564a19756dc356e` | 7/7 SUCCESS | Documentation-only |
| #701 prospective evaluator | `4ea2f9e60fc073d1850ae2b999f518db5d501a3f` | 6/6 SUCCESS | Evaluator-specific suite: 73 passed |
| #702 free fixture/feature preview | `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e` | 7/7 SUCCESS | Offline preview suite: 22 passed |
| #703 bounded artifact downloads | `078a04c6b5bfdf6c61a8b368f9ca6c28fb4f487c` | 7/7 SUCCESS | Frozen V2 shadow suite: 97 passed |
| #704 version-pinned V2 CI dependencies | `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3` | 7/7 SUCCESS | Python 3.11: 87 passed; Python 3.12: 87 passed; `pip check` passed in Python 3.12 |

All remain open and target the unchanged main SHA above. HUMAN-MERGE only.

## New PR #704 — reproducible original-V2 CI dependencies

The five original-V2 workflows previously installed unpinned packages. Successful runtime logs showed different numerical versions by Python minor:
- Python 3.11: NumPy 2.4.6, SciPy 1.17.1.
- Python 3.12: NumPy 2.5.4, SciPy 1.18.1.
- Both: pandas 3.1.0, scikit-learn 1.9.1, requests 2.34.2, Supabase 2.33.0, pytest 9.2.0.

#704 adds exact-version lock files for both Python versions, switches the original V2 source/forward/diagnostic/shadow workflows to the corresponding lock, and tests that the existing cron expressions are unchanged. These are version pins, not hash-enforced supply-chain locks.

An initial Python-3.12 test-job addition exposed a test-only string-splitting bug (1 failed, 86 passed in each runtime). The assertion was corrected. On the final exact HEAD `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`, both Python-version jobs now pass 87/87; the Python-3.12 `pip check` passes; both production `*.pkl` diff guards pass; all 7/7 required workflows are SUCCESS.

#704 changes workflow files also changed by #699. Merge #699 first, then rebase #704 and rerun exact-head CI. Do not merge the old base-main heads independently.

## Coordination correction for #703

The current #699 diff already modifies `get_archive()` in both `serie_a_v2_forward_capture.py` and `serie_a_v2_current_form_forward_capture.py`, adding streaming, Content-Length checks, bounded chunks and response cleanup. #703 modifies those same functions and adds an explicit non-bytes chunk guard; its Content-Length conversion is less strict than #699's decimal-only validation. A correction comment is recorded on #703. After #699 is manually merged, rebase/review #703 and retain only a genuinely useful distinct guard if still needed.

## Read-only source and runtime evidence

Current-form source capture on unchanged main:
- Run #41049950849: SUCCESS; 19 source/manifest tests passed.
- 90 completed prior-day feature-source events; 10 historical CSVs plus one current-season CSV (11 files total).
- Candidate SHA: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Artifact ID `12973598320`; ZIP SHA-256 `02013d5984117f48f5efab2b8662fed7e291bdfd49689d27152325e129c877b4`.
- Paid provider calls 0; Supabase writes 0; target outcomes scored false.

Current-form forward-only run #41077147924: SUCCESS; 53 tests passed; verified the above source archive and parent run; `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes not read/scored, no paid calls or writes.

Original forward-only run #41076521488: SUCCESS; 71 tests passed; 3,800 historical rows verified; `quotes_seen=0`, `forecasts_created=0`, no paid calls or Supabase writes.

These runs are on old main and predate #699's persisted identity-list/SHA contract. They prove source ZIP/parent provenance and safe no-quote behavior, but **do not** prove the new identity-set guard live. After #699 HUMAN-MERGE, require a new source capture on the resulting exact main SHA before #702 or any forward quote processing.

## Fresh read-only Supabase audit — 2026-10-31

Metadata query against `public.league_finished_results` selected only `match_date, home_team, away_team`, for Serie A 2026/27 and dates before 2026-10-31:
- Raw rows: 93.
- Canonical unique identities: 90.
- Duplicate rows after the original V2 aliases: 3.
- Independently recomputed SHA using the #699 newline/tab canonical serialization: `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`.

Odds metadata:
- All leagues: 3,966 snapshots; 3,915 strictly pre-match (`snapshot_time_utc < commence_time_utc`); 51 at/after kickoff.
- New snapshots in the last 24 hours: 0; last 7 days: 0; future fixtures with a strict pre-kickoff quote: 0.
- Latest saved snapshot: 2026-10-13 14:48:53.042620 UTC.
- Serie A: 625 snapshots, 620 strict pre-match.
- Serie A prediction ledger: 630 rows, all prediction timestamps before kickoff and all `MARKET_ONLY / CALIBRATION_REQUIRED`; future rows 0.
- `model_artifact_bundles`: 0 registered bundles.

No scores, results, settlement columns or protected target outcomes were selected.

## Scientific status and next sequence

- Frozen original candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original 19 features and weights unchanged; `active_lambda=0` remains market; `shadow_lambda=1` remains research-only.
- The 90-event feature-input gate is open, but the new persisted identity attestation still requires #699 merge plus a fresh post-merge source capture.
- Eligible new prospective V2 forecasts: 0. Frozen non-legacy incumbent reference: unavailable (zero registered bundles). Evaluation gate CLOSED; no independent Brier/LogLoss comparison is currently possible.
- #702 remains blocked until #699 is merged, a fresh source archive with identity list/count/SHA is captured on the new main, and #702 is then manually dispatched.
- #701 must remain fail-closed; do not substitute the market or the old XGBoost model for the missing incumbent.

No merge, main change, Supabase write/DDL, paid request, target-outcome read, production `.pkl` change, weight/feature change, schedule change, or other-agent setting change occurred.


---

# Continuity update — 2026-10-31 13:05 UTC — live 31 Oct source archive, forward attestation and schedule audit

## Repository and exact PR state

- Fresh default branch remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main commit was created or merged in this cycle.
- Main `PROJECT_CONTINUITY.md` remains blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`; this entry is added only on documentation branch `research/v2-continuity-live-proof-20261025`.
- PR #699 current HEAD: `53b7b184005e8516bfff8c1483e5ab9a4c41e73e`, base main above, open/mergeable, **7/7 exact-head CI SUCCESS**. Dedicated frozen V2 run #41194794442: **257 passed**, production `*.pkl` diff guard passed. The added AST dependency-closure test rejects XGBoost/joblib/pickle runtime use and production pickle paths; original candidate, 19 features, weights and lambdas are unchanged.
- PR #697 before this documentation update: `799ac6c5c0819e79287c6ef2d4f2164090c23bf6`, base main above, 7/7 exact-head CI SUCCESS. A new exact-head CI run is required after this append.
- PRs #701, #702, #703 and #704 remain open/HUMAN-MERGE only at their previously recorded heads. #702 must not be live-dispatched before #699 is merged and a fresh post-merge source artifact is verified.

## New real Current-Form Source Capture — 31 October

Main-only scheduled run [#41196139664](https://github.com/MaksimBlud/football-ai/actions/runs/41196139664) completed SUCCESS at 2026-10-31 11:16 UTC.

- Dedicated source/manifest tests: **19 passed**.
- Feature-input metadata gate: 90 canonical completed Serie A 2026/27 identities.
- Source files: 10 frozen historical CSVs plus one current-season CSV (11 CSVs; 3,800 historical rows plus 90 current-season rows).
- Frozen candidate SHA: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Feature builder blob SHA: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- Source artifact ID: `13040356986`; size 437,016 bytes; GitHub digest and independently downloaded ZIP SHA-256 both equal `feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a`.
- All **11/11 CSV hashes** independently recomputed from the downloaded ZIP match the source manifest.
- Current-season source CSV: 90 rows, all prior to capture day; after the exact V2 aliases (Inter→Inter Milan, Milan→AC Milan, Roma→AS Roma, Verona→Hellas Verona, Atalanta BC→Atalanta), 90 unique fixture identities.
- Independently computed current-source identity SHA-256: `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`; it matches the independently computed Supabase metadata-only identity SHA below.

**Important contract limitation:** this run executed on unchanged main `40887ebb...`, so its manifest still lacks persisted `gate_fixture_identity_sha256`, `current_source_fixture_identity_sha256`, the full canonical identity list and explicit coverage counts. The external CSV↔Supabase SHA parity is independently proven, but it is **not** the new #699 persisted-manifest proof. #699 branch code adds both SHA values, the identity list/counts and missing-identity coverage fail-closed checks. A new source capture on the post-#699 main is still mandatory after HUMAN-MERGE.

## New real Current-Form Forward-Only run

Main-only workflow-run [#41196202296](https://github.com/MaksimBlud/football-ai/actions/runs/41196202296) completed SUCCESS at 2026-10-31 11:17 UTC.

- Forward regression suite: **53 passed**.
- Verified source artifact `13040356986`, ZIP SHA above, and authenticated parent run `41196139664`.
- Source observation: 11:16:50.931690 UTC; artifact creation: 11:16:52 UTC; source parent completion: 11:16:55 UTC; forward verification: 11:17:32.720184 UTC.
- Source age at verification: 41 seconds; `fresh_for_new_quote=true`.
- Historical/current-form rows verified: 3,890 total.
- `quotes_seen=0`; `v2_current_form_shadow_captured=0`.
- `target_outcomes_read=false`; `target_outcomes_scored=false`; `paid_provider_calls=0`; `production_or_supabase_writes=0`.
- Forward artifact ID `13040403015`; independently downloaded ZIP SHA-256 `6be708a2a6ac92d78f66e65e2c3ed1f5c56c56ad8f3c3083688cfd573568d0e2`.

This is live source/parent attestation and no-quote safety proof, **not** a prospective prediction or model-quality result.

## New real free Original V2 diagnostic

Main-only scheduled run [#41200476529](https://github.com/MaksimBlud/football-ai/actions/runs/41200476529) completed SUCCESS at 2026-10-31 12:18 UTC.

- Diagnostic regression suite: **53 passed**.
- Public source HTTP requests: 10; exactly 10 frozen historical CSVs / 3,800 historical matches.
- `quoted_fixtures=0`; `diagnostic_scored=0`; per-fixture feature coverage rows: 0.
- `paid_provider_requests=0`; `supabase_writes=0`; 2026/27 public results were not downloaded.
- Diagnostic artifact ID `13042322093`; independently downloaded ZIP SHA-256 `8c39e6db1f95727a2d6c62513b68c929bcb8560df2ca329eb735dd8229fa470b`.

The diagnostic source archive contains the 10 old-season CSVs only. It is distinct from the 11-file current-form source artifact above.

## Fresh read-only Supabase metadata and odds

Only `match_date, home_team, away_team` were selected from `public.league_finished_results` for Serie A season `2026-2027`; no score/result/settlement fields were selected.

- Raw rows: 93.
- Canonical unique identities after original V2 aliases: 90.
- First date: 2026-08-22; latest date: 2026-10-29.
- Canonical sorted tab/LF SHA-256: `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811`.

Read-only `public.odds_snapshots` audit for `league='SERIE_A'`:

- Total snapshots: 625.
- Strictly pre-kickoff: 620.
- At/after kickoff: 5.
- New snapshots in last 24 hours: 0; last 7 days: 0.
- Future events with strictly pre-kickoff snapshots: 0.
- Latest saved snapshot: 2026-10-13 14:48:53.042620 UTC.

`public.model_artifact_bundles` count remains 0. No non-legacy frozen incumbent is registered.

## Original Forward-Only scheduled-run liveness

The unchanged main workflow `.github/workflows/serie-a-v2-forward-preview.yml` still declares `8 8 * * *` (08:08 UTC) and its last confirmed run is [#41076521488](https://github.com/MaksimBlud/football-ai/actions/runs/41076521488), 2026-10-30 14:59 UTC.

A fresh GitHub Actions run-list audit for 31 October covered the returned run pages from 12:57 UTC back through 02:58 UTC. It found the Current-Form Source Capture #41196139664 and Current-Form Forward #41196202296, but **no 31 October run** for the Original Forward-Only workflow at its 08:08 UTC scheduled slot. This is an observed missing run, not proof the workflow is disabled. No schedule was changed and no manual dispatch was made.

The main Original Forward workflow also still lacks the explicit `github.ref == 'refs/heads/main'` job guard. PR #699 adds this guard; until #699 is manually merged, do not dispatch the original forward/source workflows from a feature branch because they expose Supabase secrets in their job environment.

## Scientific status

- Original `MARKET_ANCHOR_1X2_V2` candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Frozen 19 features/order/weights unchanged.
- `active_lambda=0` remains exact de-vigged market; `shadow_lambda=1` remains research-only.
- Current-form feature-input gate: 90, passed.
- Eligible new prospective V2 forecasts: 0.
- Frozen non-legacy incumbent: absent.
- 30-primary-completed-event evaluation gate: CLOSED.
- Independent Brier/LogLoss comparison: unavailable; no superiority claim is justified.

No protected target outcomes were read or scored. No paid provider request, Supabase write/DDL, main change, PR merge, production `.pkl` mutation, model refit, threshold tuning, promotion, betting, schedule change, or other-agent setting change occurred.


## 2026-10-31 13:52 UTC — source-manifest contract gap and free fixture-source availability

Fresh read-only audit after the 11:00 UTC entry:

- Main is unchanged at `40887ebb215730190d7a6c7a1693373ec4afcdfc`. PR #699 remains the required HUMAN-MERGE integration at exact HEAD `53b7b184005e8516bfff8c1483e5ab9a4c41e73e`, with 7/7 exact-head CI SUCCESS and 257 original-V2 shadow tests passing. No merge occurred.
- Current-Form Source Capture [run 41196139664](https://github.com/MaksimBlud/football-ai/actions/runs/41196139664) completed successfully on old main and uploaded artifact 13040356986 (437,016 bytes). Independently recomputed ZIP SHA-256: `feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a`; this matches the GitHub artifact digest. The manifest SHA-256 is `4038e73c83a7c7f3fab66acf83eb73768b161f064cde67a191ac36cfb8f8a22a`. All 11/11 archived CSV raw-byte hashes match the manifest; the current-season CSV byte hash matches `current_season_source_sha256`. CSV contents were not parsed for this integrity check.
- The old-main manifest reports 90 completed prior-day current-season rows and a passed count-only metadata gate, but its schema `SERIE_A_V2_CURRENT_FORM_SOURCE_CAPTURE_V1` does **not** persist `gate_fixture_identity_sha256`, the canonical gate identity list, or current-source identity coverage. The read-only Supabase identity set independently hashes to `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811` under the exact #699 tab/newline serialization, but that digest is not embedded in this old-main archive. This is parity evidence, not post-#699 runtime proof.
- Current-Form Forward [run 41196202296](https://github.com/MaksimBlud/football-ai/actions/runs/41196202296) completed SUCCESS with 53 tests, verified the source artifact and parent run, but observed `quotes_seen=0` and captured `0` shadow forecasts. Free Real-Quote Diagnostic [run 41200476529](https://github.com/MaksimBlud/football-ai/actions/runs/41200476529) completed SUCCESS with 53 tests; it made 10 public CSV requests, saw `quoted_fixtures=0`, scored `0`, and reported `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`. Neither run read target outcomes or wrote Supabase.
- The existing `public.matches` table currently contains EPL rows only (2016/17–2025/26 plus 80 rows in 2026/27); no Serie A fixture rows are available there. Therefore the separate free future-fixture preview in #702 remains the only reviewed route to obtain Serie A fixture metadata for original 19-feature readiness without reading outcomes or requesting odds. #702 remains manual-only/main-only, and must not be dispatched until #699 is merged and a fresh post-merge source archive verifies the persisted gate identity SHA and full coverage. Its `/events` response must still attest zero quota use.
- Read-only odds audit: 3,966 total snapshots / 3,915 strictly pre-kickoff across leagues; Serie A 625 / 620. There are zero snapshots in the last 24h or 7d and zero future strictly pre-kickoff quotes. Latest Serie A quote remains `2026-10-13T14:48:53.042620Z`. Registered `model_artifact_bundles`: 0.
- The Original Forward workflow declares `08:08 UTC` in main. The 31 October GitHub Actions run inventory for 08:00–14:00 UTC contains no run named `Serie A V2 Original Forward-Only Preview`; its latest confirmed run remains #41076521488 from 30 October. Treat this as a missed/unobserved scheduled execution, not proof that the workflow is disabled. No dispatch or schedule change was made.

The original candidate, 19-feature order/weights, `active_lambda=0`, `shadow_lambda=1`, no-bet behavior and both frozen gates remain unchanged. The 30-primary-completed-prospective-forecast outcome gate is CLOSED; no eligible prospective forecasts or frozen incumbent are registered, so no independent Brier/LogLoss comparison can be claimed. No target outcomes were read or scored, no paid provider calls, no Supabase writes/DDL, no production `.pkl` changes, no main mutation, and no merge occurred. HUMAN-MERGE remains mandatory.


## 2026-10-31 16:53 UTC — scheduled original and current-form V2 forward runtime proof; quote and incumbent gates remain closed

Read-only audit on unchanged `main` SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This entry corrects the prior cycle's incomplete run inventory: the scheduled Original Forward workflow did run successfully on 2026-10-31.

### Scheduled Original Forward — real runtime proof

- GitHub Actions [run 41210303100](https://github.com/MaksimBlud/football-ai/actions/runs/41210303100), workflow `serie-a-v2-forward-preview.yml`, event `schedule`, created 2026-10-31 14:28:46 UTC, SUCCESS.
- Exact job `original-v2-forward-preview`: 71 tests passed. The real-source attestation step verified the old-season-only diagnostic archive from run `41200476529`, artifact `13042322093`, ZIP SHA-256 `8c39e6db1f95727a2d6c62513b68c929bcb8560df2ca329eb735dd8229fa470b`; 10 historical CSV files / 3,800 historical matches; original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Forward output: `quotes_seen=0`, `future_quotes_checked=0`, `rows=[]`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`, `eligible_for_frozen_prospective_cohort=false`, `independent_incumbent_asof_verified=false`, `uses_2026_27_results=false`, `protected_2026_27_results_read=false`, paid calls 0, Supabase writes 0.
- Output artifact `13045239180`, size 1,461 bytes. GitHub ZIP digest and independently recomputed local SHA-256 both equal `764060555f19a6d8ea4efc8bd06768bccbeaf77e5846230a8ceb7156b1ed1b02`. Its two JSON members independently hash to `b3428d19ba871a7ea49efe4b94739de2a23b9433e01b3e3d35459ca50469d92f` (forward report) and `44172ae76281f7eae9fb1bf5842a35dd1cae76bf0fda1102fcd368ab2be86cf3` (source attestation).

### Scheduled Current-Form Forward — current-season source verification

- GitHub Actions [run 41210600837](https://github.com/MaksimBlud/football-ai/actions/runs/41210600837), workflow `serie-a-v2-current-form-forward-preview.yml`, event `schedule`, created 2026-10-31 14:32:28 UTC, SUCCESS.
- Exact job `current-form-forward-preview`: 53 tests passed. It verified source run `41196139664`, artifact `13040356986`, archive SHA-256 `feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a`; 11 source CSVs, 3,890 combined historical/current rows, 90 current-season history rows and 90 metadata-only feature-input gate identities. Source observation `2026-10-31T11:16:50.931690Z`, archive creation `11:16:52Z`, verification `14:33:01.480718Z`; source age 11,770 seconds, inside the frozen 24-hour limit.
- No saved quotes existed: `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `rows=[]`, `eligible_for_current_form_forward_shadow=false`, `target_outcomes_read=false`, `target_outcomes_scored=false`, paid calls 0, production/Supabase writes 0. This is source verification, not a prospective forecast and not evidence of 19-feature values for future fixtures.
- Output artifact `13045987954`, size 438,190 bytes. GitHub digest and independent local SHA-256 both equal `32623b30e1ef5a6706db7bc09cc6fd801b408ccfa2b64b911fcde2914d4b64c0`. The JSON member SHA-256 is `1eecbb93483d5fb38ec99881849d14201d33f348e4a66b785649917dc27569e5`; the nested original source ZIP independently hashes to `feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a`, matching the parent source artifact.

### Fresh read-only pre-match database audit

The audit selected only market snapshot timestamps, kickoff timestamps, league labels, and fixture identities; no target score/result fields were selected. At approximately 2026-10-31 16:53 UTC:

- Across all nine stored leagues, future strictly pre-kickoff snapshots = **0**; strictly pre-kickoff snapshots saved in the preceding 24 hours = **0** and preceding 7 days = **0**.
- Serie A: 625 total snapshots, 620 strictly before kickoff, 0 future pre-kickoff; latest strictly pre-kickoff snapshot remains `2026-10-13T14:48:53.042620Z`.
- The identity-only query for future Serie A rows in `public.matches` returned 0 rows. The current completed-fixture identity source remains separate and its read-only 2026/27 metadata query selects only `match_date, home_team, away_team`.
- `public.model_artifact_bundles` currently returns no registered bundles. The evaluator in PR #701 explicitly keeps `FROZEN_INCUMBENT_REFERENCE=None` because the preregistered policy requires three comparators (de-vigged market, frozen production incumbent, and V2 lambda-one shadow) but does not pin an exact incumbent artifact/version. The existing production/XGBoost model must not be revived or substituted. No protocol amendment or outcome read was made; this remains a hard scientific blocker even after the 30-forecast count gate.

Additional pre-match prediction inventory (metadata/provenance only; no target outcomes selected): `public.league_prediction_ledger` contains **630 Serie A rows, all `prediction_mode=MARKET_ONLY` and all 630 strictly pre-kickoff**; its latest prediction timestamp is the same stale `2026-10-13T14:48:53.042620Z`. There are no Serie A incumbent-model rows in this ledger. `public.product_prediction_snapshots` contains only 40 EPL rows with `model_1x2_version=EPL_AI_MARKET_PAIR_V1` and a different artifact SHA; it contains no Serie A incumbent. This independently confirms that neither the market ledger nor the existing EPL product snapshot can satisfy the frozen Serie A incumbent comparator.

### Binding interpretation

The two scheduled forward workflows now have confirmed real SUCCESS runs, correcting the earlier incomplete inventory. Both verify their respective source archives correctly, but neither produced a prospective forecast because no admissible saved quote exists. The free fixture feature preview in PR #702 remains dependent on HUMAN-MERGE of #699, then a new post-merge source capture with persisted gate identity SHA, then HUMAN-MERGE of #702 and a separate manual dispatch. No provider request was made in this cycle.

The preregistered evaluation gate remains CLOSED: zero eligible prospective forecasts; the required frozen incumbent reference is also absent. Keep `active_lambda=0` as exact de-vigged market, `shadow_lambda=1` research-only, and NO_BET. Do not read 2026/27 target outcomes, relax the 30-event gate, substitute the old production model, or claim V2 superiority.

No main change, PR merge, Supabase write/DDL, paid provider call, model/weight/feature change, schedule change, or production artifact access occurred.


## 2026-11-01 04:57 UTC — prospective evaluator uncertainty addition; exact-head CI proof

PR #701 was extended on its existing research branch (no main mutation) to add a supplementary paired fixture-level bootstrap summary to the frozen-gate evaluator.

- PR #701 exact HEAD: `3e859a3a25f56aa62b8f806d23f2b09c6a6be005`; base main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Exact-head PR checks: **6/6 SUCCESS** (validate, Bundesliga, product contract, Serie A, targeted research, Ligue 1).
- The targeted research job compiled the evaluator and ran `tests/test_market_anchor_1x2_v2_prospective_evaluator.py`: **76 passed in 0.84s**. The same job's no-production-artifact guard passed: no `.pkl` changes.
- Once the existing outcome gate and frozen-incumbent pin both permit scoring, the evaluator will report paired fixture-level bootstrap percentile 95% intervals for shadow-minus-market and shadow-minus-incumbent Brier/LogLoss differences. It uses 10,000 resamples and fixed seeds 20261101–20261104. The resample fraction below zero is explicitly descriptive only, not a p-value or posterior probability.
- The bootstrap is supplementary and is not used by the gate or review signal. The 30-eligible-completed-forecast gate, required comparator set, frozen V2 weights/features, `active_lambda=0`, `shadow_lambda=1`, and NO_BET policy are unchanged. The outcome callback remains lazy; no protected 2026/27 target outcomes were read or scored. All tests use synthetic outcomes.
- PR #701 remains open/HUMAN-MERGE only. No merge or main update occurred.

Current blocker is unchanged: Supabase has 0 future strictly pre-kickoff Serie A quotes; latest saved Serie A snapshot remains 2026-10-13 14:48:53 UTC. The current-form feature-input metadata gate has 90 canonical completed identities, but eligible completed prospective forecasts remain 0 and no permitted non-legacy frozen incumbent is pinned. Therefore the independent Brier/LogLoss comparison remains unavailable and no V2 superiority claim is justified.


## 2026-11-01 — Original V2 prospective evaluator: live identity-gate orchestration and current blockers

**PR #701 updated on a separate research branch; main remains unchanged.** The current exact PR HEAD is `a9fdb39fc30f32aa6ede96d63846610198faca17` against main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Its six required PR workflows are all SUCCESS: Research `41290965587`, Serie A `41290965620`, Bundesliga `41290965602`, Ligue 1 `41290965566`, Eredivisie `41290965586`, Product `41290965571`. The Research run executed the prospective evaluator suite (**76 passed**) and the new live-runner integration suite (**2 passed**), compiled the completed-fixture gate and runner, and passed `git diff --exit-code -- '*.pkl'`.

The new `market_anchor_1x2_v2_prospective_runner.py` exposes `evaluate_live_prospective_cohort(client, forecast_rows, outcome_loader)`. It obtains completed fixture identities and the digest-bound attestation itself through the production metadata-only gate reader; callers cannot inject their own identity set, attestation, or cutoff. It delegates to the pure evaluator with the lazy outcome callback unchanged. Offline regressions prove that a failed identity gate stops before evaluator/outcome access and that even 30 synthetic eligible forecasts remain `EVALUATION_BLOCKED_UNPINNED_INCUMBENT` with zero outcome-callback calls while the non-legacy incumbent remains unpinned. This is an orchestration-safety improvement, not a live forecast or outcome evaluation.

**Fresh read-only pre-match Supabase audit (2026-11-01):**
- `public.odds_snapshots`, strict `snapshot_time_utc < commence_time_utc`: Serie A **620** snapshots / **63** events; latest **2026-10-13 14:48:53.042620 UTC**; zero snapshots in the last 24 hours and zero future events with saved pre-kickoff quotes. The other eight represented leagues also have zero last-24h strict pre-kickoff snapshots and zero future events with saved quotes.
- `public.league_prediction_ledger`, strict pre-kickoff Serie A: **630** rows / **63** events, all `prediction_mode=MARKET_ONLY`, latest **2026-10-13 14:48:53.042620 UTC**, zero future kickoffs. This is not a distinct frozen incumbent vector.
- `public.product_prediction_snapshots`, strict pre-kickoff: the only registered rows are **40 EPL** events under `EPL_AI_MARKET_PAIR_V1`, SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`; **zero Serie A rows**. The matching SHA constant in the older V2 shadow module is therefore not sufficient evidence of a same-league, same-information-time Serie A incumbent. Do not substitute it or the legacy XGBoost model.
- No result/score/settlement columns were selected in these queries. No Supabase writes/DDL or paid provider requests were made.

The separate 30-eligible-completed-prospective-forecast evaluation gate remains CLOSED: no new strict pre-kickoff quotes exist after the 2026-10-18 cohort preregistration, so no new eligible forecasts have been captured. `FROZEN_INCUMBENT_REFERENCE` also remains unset; both blockers must be resolved under an explicitly approved non-legacy protocol before any target-outcome callback can run. Do not open protected 2026/27 outcomes, change the original 19 features/weights/lambdas, or claim V2 superiority.

PR #699 remains open on exact HEAD `fa10c4c8ce3971c3da965e07c28af867f3a3abb3` with **7/7 SUCCESS** (Original V2 shadow suite **263 passed**, production `.pkl` diff guard passed). HUMAN-MERGE only. PR #700's historical-source redirect work is already represented in #699's consolidated diff; do not merge overlapping branches independently. PR #703 and #704 still touch files shared with #699 and must be rebased/retested after any manual #699 merge. No main, production artifact, schedule, or agent-setting changes were made.


## 2026-11-01 10:03 UTC — independent source-byte, identity-parity and seven-day quote audit

- Re-downloaded the actual GitHub Actions source artifact from run #41196139664 (artifact #13040356986, 437,016 bytes). The locally recomputed ZIP SHA-256 is `feb008fa6ebc15d9125572d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, exactly matching the GitHub artifact digest. Independently checked all 11 archived CSV byte hashes against the manifest: **11/11 match**. Row counts are 10 historical seasons × 380 plus 90 current-season rows = **3,890**.
- A fresh read-only Supabase query selected exactly `match_date, home_team, away_team` from `public.league_finished_results` for Serie A 2026/27 through 2026-10-31. It returned 93 raw metadata rows; after the frozen Serie A aliases (including Atalanta BC → Atalanta), there are 90 unique fixture identities. The exact frozen sorted tab/newline SHA-256 is `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811` in both PostgreSQL and the downloaded current CSV. No score/result/settlement columns were selected.
- A new read-only audit of `public.odds_snapshots` across all nine represented leagues, requiring `snapshot_time_utc < commence_time_utc`, found **0 snapshots in the preceding 24 hours, 0 in the preceding 7 days, and 0 future events with saved strict pre-kickoff quotes**. Serie A remains 625 total / 620 strict pre-match / 63 events; latest strict pre-match snapshot is `2026-10-13T14:48:53.042620Z`. The other leagues' latest stored snapshots are also stale (September 5–11).
- Latest verified current-form source run remains #41196139664 (2026-10-31 11:16:03Z); latest current-form forward-only run remains #41210600837 (2026-10-31 14:32:28Z). At this audit time, the source observation is 22h46m50s old and reaches the frozen 24-hour source-age limit at 2026-11-01 11:16:50Z. No November 1 current-form source-capture or current-form forward-preview schedule run was present in the checked GitHub Actions run windows through 10:03Z. No schedule was changed and no workflow was dispatched.
- The incumbent blocker remains unchanged: pre-kickoff product snapshots contain only 40 EPL events for `EPL_AI_MARKET_PAIR_V1` (SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`) and zero Serie A events; the Serie A ledger contains market-only rows, not a distinct incumbent. The evaluator must remain fail-closed with no non-legacy Serie A incumbent pinned.

No paid provider request, Supabase write/DDL, protected 2026/27 outcome read, production `.pkl` change, model/weight/feature change, merge, main mutation, or schedule change occurred. The 30-primary-completed-event outcome gate remains closed; no Brier/LogLoss quality claim is possible.


## 2026-11-01 11:04 UTC — evaluator compatibility with the real forward schema

- Re-read fresh main at 40887ebb215730190d7a6c7a1693373ec4afcdfc, the original serie-a-v2-forward-preview.yml, both current-form workflows, and the current-form forward-capture source. The actual current-form forward rows contain the de-vigged market, exact active_lambda=0 market fallback, and original shadow_lambda=1 vector, but no same-league incumbent vector/evidence.
- Found and fixed a real integration defect in PR #701: its evaluator required incumbent fields even while FROZEN_INCUMBENT_REFERENCE=None, so it rejected genuine market+shadow-only forward rows before it could return the intended unpinned-incumbent block. The validator now permits both incumbent fields to be absent only while the reference is unpinned; partial fields still fail, and a pinned reference makes both fields mandatory. No probabilities are fabricated and no comparator is substituted.
- Exact PR #701 HEAD d4070bc2fa59a2d83e31baa53c41f96e5573574c: evaluator 76 passed, live runner 2 passed, required CI 6/6 SUCCESS, production .pkl diff guard PASS. The runner now accepts the real forward schema and returns EVALUATION_BLOCKED_UNPINNED_INCUMBENT without calling the lazy outcome loader.
- Fresh read-only Supabase odds audit still shows 0 strict pre-kickoff snapshots in the preceding 7 days and 0 future events with saved pre-match quotes across all nine represented leagues. Latest Serie A pre-match quote remains 2026-10-13T14:48:53.042620Z.
- Source artifact #13040356986 from scheduled run #41196139664 was created 2026-10-31T11:16:52Z; at 11:04Z on November 1 it is about 23h47m old and reaches the frozen 24-hour source-age boundary at approximately 2026-11-01T11:16:50Z. The next 05:50Z scheduled source-capture run was not yet visible in the checked run window. The previous day's scheduled run itself started at 11:16Z, so treat this as a possible GitHub schedule delay, not proof the workflow is disabled. No manual dispatch or schedule change was made.
- The original frozen candidate, feature builder, 19-feature order, weights, parent protocol, active_lambda=0, and shadow_lambda=1 are unchanged. No target outcomes were read, no Supabase writes/DDL or paid calls occurred, and no main/production change or merge occurred. The outcome gate remains closed until the frozen 30-primary-completed-forecast gate and a separately approved, same-league non-legacy incumbent reference are both satisfied.


## Corrected independent read-only pre-match audit — 2026-11-01 13:15 UTC

This audit supersedes any earlier cross-table attribution in PR metadata and independently re-verifies the original source artifact.

- Re-downloaded GitHub Artifact #13040356986. ZIP SHA-256 from the actual bytes is `feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a`, exactly matching GitHub's artifact digest. All 11 CSV hashes match the embedded manifest; 3,890 rows total (10 historical seasons × 380 plus 90 current-season rows).
- The 630 Serie A strict pre-kickoff rows / 63 events belong to `public.league_structural_v2_observations`. `public.league_h2h_bookmaker_snapshots` is empty (direct grouped query returned no rows; table metadata also reports zero rows). Structural observations' latest Serie A timestamp is `2026-10-13T14:48:53.042620Z`; zero in the last 7 days and zero future events.
- `public.league_multi_market_snapshots`: two strict pre-kickoff EREDIVISIE rows, no Serie A rows. `public.matches`: zero future fixture rows.
- `public.odds_snapshots`: 3,966 rows total, 3,915 strictly pre-kickoff; zero strictly pre-kickoff rows in the last 7 days and zero future events with saved pre-match quotes across all nine represented leagues. Latest Serie A quote remains `2026-10-13T14:48:53.042620Z`.
- `public.product_prediction_snapshots`: zero future strictly pre-match rows carrying frozen V2 candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- At `2026-11-01T13:15:26Z`, artifact #13040356986 is about 25h58m35s old, beyond the frozen 24-hour source-age limit. The manifest's 90-event feature-input gate passed, but `eligible_for_current_form_forward_shadow=false` is expected at source-capture stage; no quote-backed feature vector or forecast was produced. The 90 metadata identities are not 30 eligible completed prospective forecasts and do not open the outcome gate.

Only pre-match snapshot/fixture metadata was selected. No quote payloads, prices, probabilities, score/result fields, or protected target outcomes were read. No Supabase writes/DDL, paid calls, schedule changes, production artifact changes, or main changes. HUMAN-MERGE only.


## 2026-11-01 — current-form source freshness, free diagnostic, and refresh reliability

### Verified source artifacts

- Current-form source capture run **#41196139664** (main SHA
  `40887ebb215730190d7a6c7a1693373ec4afcdfc`) produced artifact
  **13040356986**, GitHub digest / independently recomputed ZIP SHA-256:
  `feb008fa6ebc15d9125573c8e69061c4bc63bcd81e506265b4d6f948d0a4621a`.
- ZIP contains 10 frozen old-season CSVs plus the 2026/27 CSV and manifest:
  3,800 historical rows + 90 current-season rows = 3,890 rows. All 11 CSV
  SHA-256 values were independently recomputed and matched the manifest.
- The 2026/27 source CSV SHA-256 is
  `32ca618587c90db25f16ea647cb55060f519c03830a1e8ec4a6c4204e27d5135`.
- The source observation was `2026-10-31T11:16:50.931690Z`. It crossed the
  frozen 24-hour limit at approximately `2026-11-01T11:16:50.931690Z`;
  therefore it is stale for new prospective quotes at the 14:00 UTC audit.
- Current-form forward run **#41210600837** verified that source at
  `2026-10-31T14:33:01Z`, when it was still fresh, but saw
  `quotes_seen=0`, `v2_current_form_shadow_captured=0`, and an empty
  `rows=[]`. No prospective forecast was created.

### New free historical diagnostic on 2026-11-01

- Free diagnostic run **#41310276961** completed on main at
  `2026-11-01T13:14:16Z`; artifact **13084892998**, 425,067 bytes,
  GitHub digest / independently recomputed ZIP SHA-256:
  `bcd6fcfb6e2c05c88914812a54067539319fd8894a9d9e2387eea1fba93b38c5`.
- It contains only the 10 pre-freeze historical CSVs (3,800 rows); all 10
  CSV hashes independently matched the manifest. It does **not** contain a
  current-season 2026/27 CSV and is not a replacement for the current-form
  source archive.
- Manifest confirms `history_stale_without_2026_27_form=true`,
  `quoted_fixtures=0`, `paid_provider_requests=0`,
  `supabase_writes=0`, and no 2026/27 public results download.
  Its 19-feature diagnostic is not a prospective V2 observation.

### Read-only Supabase state

- Identity-only Serie A 2026/27 query through 2026-10-31 returned 93 raw
  metadata rows and **90 canonical unique fixture identities** after the
  frozen Serie A aliases (including Atalanta BC -> Atalanta). This matches
  the 90-identity feature-input gate in the 2026-10-31 source manifest.
  Only `match_date, home_team, away_team` were selected.
- Across the nine `odds_snapshots` leagues: 3,966 total snapshots, 3,915
  strictly pre-match (`snapshot_time_utc < commence_time_utc`), zero new
  strict pre-match snapshots in the last seven days, and zero future events
  with a stored strict pre-match quote. Latest Serie A strict pre-match quote:
  `2026-10-13T14:48:53.042620Z`.
- `product_prediction_snapshots` has 40 total rows but **zero** rows with
  the original V2 candidate SHA. Those records are not an admissible V2
  incumbent and must not be represented as one.

### PR #699 — source refresh reliability, without changing cron

- Updated exact PR head:
  `58bdb5bfc88f1b33f3e9843b164b8c036306e882`.
- Added a `workflow_run` trigger after successful main
  `Serie A V2 Free Real-Quote Diagnostic` schedule/manual runs. The
  existing `50 5 * * *` source-capture schedule is unchanged.
- Before a diagnostic-triggered capture, the workflow verifies the latest
  successful current-form source artifact, its SHA/parent run, the 24-hour
  freshness rule, and current metadata-only feature-gate coverage. It skips
  a duplicate capture only when both quote freshness and current-gate
  freshness are proven; otherwise it performs the existing public-CSV /
  Supabase-read-only source capture.
- The new check reads only completed fixture identities
  (`match_date, home_team, away_team`) and GitHub artifact/run metadata.
  It performs no odds-provider call, no target-outcome read, no Supabase
  write, and no production artifact change. The forward verifier now accepts
  `workflow_run` as a parent event; the workflow contract restricts that
  event to the named free diagnostic on main, with upstream event
  `schedule` or `workflow_dispatch`.
- Exact-head CI: **7/7 SUCCESS**. Research PR Validation run
  **#41313954608** passed its 43 pytest invocations (233 passing test
  instances); Frozen V2 Shadow run **#41313954700** passed **271 tests**.
  Research log confirms `PASS: no .pkl changes in PR`.
- PR remains open and mergeable. HUMAN-MERGE applies; do not merge from
  automation.

### Evaluator and scientific gate

- PR #701 head `86f4710eb11b2ea881ba6a2d6364ad8b889d2eb8` has 6/6
  successful required workflows. Its supplementary market-vs-shadow
  diagnostic uses the same 30 unique eligible completed prospective-forecast
  gate and remains `review_signal=false` while no permitted incumbent is
  pinned. The full three-way evaluation remains blocked.
- No new prospective V2 forecasts exist; no 2026/27 target outcomes were
  read; the outcome gate remains closed. No Brier/LogLoss claim is possible.

### Next action

After the user manually merges #699, wait for the next successful free
historical diagnostic run (or unchanged source schedule) to trigger the
current-form source workflow. Verify the new artifact SHA, 90-identity gate
coverage, source-before-quote ordering, and fresh current-form forward run.
Then continue the 19-feature preview and prospective evaluator integration.
Do not change the frozen candidate, weights, feature order, lambda semantics,
24-hour limits, schedule, or 30-event outcome gate.


## 2026-11-02 06:20 UTC — Public-source download budget and current V2 data state

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This continuity change is on the open documentation PR only; main is not changed.
- Official Football-Data.co.uk policy page updated 2026-10-30 states free CSV/Excel data is intended for private personal betting or academic research and allows at most light automated downloads (twice per week maximum); it also excludes commercial or data-training projects involving heavy repeated automated downloads. The Serie A page showed a 2026-10-29 update. Frequency control does not grant commercial, redistribution, or model-training rights.
- Main still has daily source schedules at 05:50 UTC (Current-Form Source Capture) and 06:13 UTC (Free Real-Quote Diagnostic). The last inspected run evidence showed 11 public CSV downloads in Source Capture and 10 public CSV requests in the diagnostic. This is a new provider-use blocker.
- New PR #705 adds a shared GitHub Actions marker ledger and 85-hour cooldown across both workflows, a shared concurrency group, marker upload before any public CSV fetch, and fail-closed behavior when GitHub metadata cannot be verified. Existing cron expressions are unchanged. Exact PR head: `5a516d5d2f65ea797cc251130b415bc05a24a1c6`; 8/8 CI checks succeeded, including 17 dedicated budget tests and the existing Frozen V2 Shadow check. PR #705 is open, not merged.
- Important limitation: the 85-hour guard caps workflow download sessions, not CSV files per session. Source Capture still fetches ten frozen historical CSVs plus the changing current-season CSV. The provider page does not define whether its frequency wording is per session or per file. Reusing already verified frozen historical bytes and fetching only the current-season CSV remains a separate optimization. Do not claim full provider compliance from the session cap alone.
- The current-form forward source-age contract remains 24 hours. A skipped refresh never refreshes source observation time; stale source must produce no forecast.
- Read-only Supabase metadata audit (no score/result columns selected): Serie A 2026-2027 has 93 raw rows and 90 identities after the existing Atalanta BC alias normalization; latest match date 2026-10-29; last persisted 2026-10-30 05:33:49 UTC; `source_updated_at_utc` is missing on all 93 rows. Future strictly pre-match odds snapshots: 0. Original V2 candidate rows in `product_prediction_snapshots`: 0.
- No protected 2026/27 outcomes were read. No Supabase writes/DDL, paid calls, model/weight/feature changes, production .pkl changes, bets, or promotions occurred.
- Merge order: #699 first. PR #705 must then be rebased onto resulting main and rerun exact-head CI before HUMAN-MERGE. PR #703 is not wholly redundant: it has overlapping bounded-streaming changes plus distinct defensive header handling and tests; preserve/rebase that delta after #699 rather than merging its current main-based diff blindly.

### Next safe work

1. HUMAN-MERGE #699 only after its exact HEAD and CI are rechecked.
2. Rebase #705 on resulting main and retain its shared 85-hour guard; do not change cron.
3. Reduce per-session provider requests by reusing SHA-verified frozen historical CSV bytes; fetch only the changing current-season CSV, subject to the same shared budget and explicit provider-use rights.
4. Recheck source freshness and strictly pre-match quotes. Keep the 24-hour source gate and 30-event outcome gate unchanged.
5. Continue the frozen 19-feature V2 shadow path; do not claim market outperformance without an eligible independent Brier/LogLoss evaluation.


## 2026-11-02 06:42 UTC — verified source artifact, free-source limit, and CI guard correction

### Frozen original V2 identity

- Main SHA remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main's continuity document is still the 2026-10-18 snapshot. This entry is on the documentation PR branch only.
- Frozen candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; candidate JSON Git blob SHA on main is `ac1303f6b096664983fbf52443bd0a381b23ba21`.
- Candidate contains exactly 19 frozen features and a 20×2 coefficient matrix (intercept + 19 features, two residual logits). `active_lambda=0`, `shadow_residual_lambda=1`, `stability_gate_passed=false`; no weight, feature, or contract change.
- The source-capture feature-input gate reads only `match_date`, `home_team`, `away_team` from Supabase metadata. It passed with 90 unique 2026/27 primary fixtures (minimum 30). This does not open the separate prospective evaluation gate.

### Independently downloaded current-form source artifact

- Source Capture run: [#41304706414](https://github.com/MaksimBlud/football-ai/actions/runs/41304706414), main SHA above; 19 tests passed.
- Artifact #13082408243, 437,021 bytes; SHA-256 independently recomputed from downloaded ZIP bytes: `09fd39e2e7371f6db887963b5da85e4bb3bb6008314cc97b2a31eabf41d115fe`, matching GitHub artifact metadata.
- Manifest: 11 CSVs (ten frozen prior seasons, 380 rows each; current 2026/27 CSV, 90 completed rows). Current CSV SHA-256: `32ca618587c90db25f16ea647cb55060f519c03830a1e8ec4a6c4204e27d5135`.
- Independent ZIP inspection confirms current-season dates 2026-08-22 through 2026-10-29; the latest two rows are dated 2026-10-29. Football-Data's official Italy page says the page was last updated 2026-10-29.
- Manifest records 90 completed primary event identities, metadata-only feature gate passed, `target_outcomes_read=false`, `target_outcomes_scored=false`, `supabase_writes=0`, `paid_provider_calls=0`. The current-season results are used only as lagged feature inputs after the preregistered 30-identity feature-input gate; no prospective target outcomes were opened for evaluation.

### Actual Forward evidence

- Current-Form Forward run [#41319862002](https://github.com/MaksimBlud/football-ai/actions/runs/41319862002): source archive SHA verified; source age 11,153 seconds at verification; `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes not read/scored, zero paid calls and writes.
- Original Forward run [#41318729126](https://github.com/MaksimBlud/football-ai/actions/runs/41318729126): `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, no paid calls or writes.
- Free Real-Quote Diagnostic [#41310276961](https://github.com/MaksimBlud/football-ai/actions/runs/41310276961): 10 public HTTP requests, zero quoted fixtures, zero rows with all 19 features observed, zero scored diagnostics, zero paid calls and writes.
- These are real runtime/guard proofs, not evidence of predictive superiority.

### Read-only pre-match Supabase audit

- `public.odds_snapshots`: 3,966 total snapshots; 3,915 satisfy strict `snapshot_time_utc < commence_time_utc`.
- Future events with saved strictly pre-kickoff quotes: 0 across all queried leagues.
- Latest Serie A snapshot: `2026-10-13T14:48:53.042620Z`.
- `public.matches` returned no future fixture metadata rows.
- Queries selected only pre-match odds timestamps/fixture metadata; no score, result, or 2026/27 target-outcome fields were selected.
- No Supabase writes or DDL.

### Free source usage and PR #705

Football-Data's official [fair-use policy](https://football-data.co.uk/contact.php) says its free data is intended for private personal betting or academic research and allows at most light automated downloading (twice per week maximum); it says the free data is not intended for commercial or data-training projects involving heavy repeated automated downloads. Its [Italy data page](https://football-data.co.uk/italym.php) shows last updated 2026-10-29.

- PR #705 exact HEAD `102c575b2e88612de1dacd636696ddd01088db75`, base main above, completed 8/8 exact-head checks successfully. Dedicated download-budget suite: 17 passed; frozen V2 shadow suite: 85 passed on current main base.
- PR #705 adds one shared artifact marker/concurrency group and an 85-hour minimum interval, which prevents three attempts fitting inside any rolling 168-hour week. It does not change cron expressions.
- Limitation remains explicit: Source Capture still requests ten historical CSVs plus the current-season CSV; Diagnostic still requests ten CSVs. The provider does not clarify whether the limit is counted per session or per file. The cap is a best-effort frequency guard, not a grant of commercial, redistribution, or model-training rights. Reusing verified historical bytes and fetching only the changing current-season file remains unimplemented.
- **Superseding merge order for #699/#705:** HUMAN-MERGE #705 first, then rebase #699 onto the resulting main and rerun exact-head CI. #699 changes paths watched by Source Capture and Free Diagnostic push triggers; #705 must install the shared 85-hour budget guard first so merging #699 cannot trigger unbudgeted public CSV downloads.

### Fail-open production-pickle CI guard discovered and corrected in PR #706

On PR #705's earlier Research PR Validation run, the log contained `fatal: origin/main...HEAD: no merge base` followed by `PASS: no .pkl changes in PR`. The old pipeline masked the failed diff because the downstream grep returned 1; it did not prove the absence of a production artifact change.

- PR #705's own dedicated budget workflow was corrected at HEAD `102c575b...`: explicit base-ref fetch, real merge-base, fail-closed diff errors; exact-head 8/8 CI passed.
- PR #706 exact HEAD `7125faf88a9d969c6d6a074193dd78c7052644e2`, base main above, changed only the Research/Serie A PR-validation workflows and `tests/test_eredivisie_workflow_contract.py`. GitHub compare shows no production `.pkl` file in the PR diff.
- PR #706's four triggered checks completed SUCCESS: Eredivisie #41401391753, Bundesliga #41401391722, Ligue 1 #41401391854, Product #41401391716. The unmodified Eredivisie workflow ran the expanded contract file: 6 passed, including the new test asserting both Research and Serie A guards require a real fetched base ref, merge-base, fail-closed diff errors, and a literal `.pkl` check.
- The Research and Serie A workflow files were themselves modified, so their own PR-triggered runs were not present in this PR's run set. Their new `-k pickle_guard` step is installed for future PRs; this is not reported as 8/8 or as live execution of those two changed workflow jobs. PR #706 remains open and HUMAN-MERGE only.

### Scientific status

- Original V2 prospective completed forecasts: 0/30.
- Evaluation gate: CLOSED.
- No new Brier or LogLoss sample exists; no claim of superiority over market.
- No 2026/27 target outcomes were read for evaluation, no thresholds tuned, no production `.pkl` or model weights changed, no paid provider call, no Supabase write/DDL, no merge, and no schedule/other-agent setting changed.

### Supabase security finding (not remediated)

Supabase's security advisor reports RLS disabled on five public tables: `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No DDL was executed. Enabling RLS without first designing policies would block existing access; this requires a separate manual security decision.


### Independent current-season completeness warning — 2026-11-02

An independent public index (StatsNext, updated 2026-11-01) reports **93 completed Serie A 2026/27 matches through 2026-10-31**. The downloaded Football-Data current-season CSV in artifact #13082408243 contains **90 rows through 2026-10-29**. The three later fixture identities listed by the independent index are Bologna–Monza, Udinese–Roma, and AC Milan–Internazionale (all dated 2026-10-31).

This is a content-completeness warning, not evidence of CSV corruption. Supabase's 90 canonical identities match the same 90-row CSV, so source/Supabase parity proves consistency between those two views but does not prove that either contains every completed fixture. Do not treat the current-form source as complete through 2026-10-31 until a new permitted source publication or an independent metadata-only fixture identity check closes this gap. The external index is not admitted as a V2 feature source or evaluation set; no score/outcome from it was used for model scoring, target evaluation, or Brier/LogLoss. The separate prospective evaluation gate remains CLOSED.


## 2026-11-02 — PR #706 fail-closed production-pickle guard: final shell/YAML correction

PR #706's initial HEAD `7125faf88a9d969c6d6a074193dd78c7052644e2` added the intended explicit base fetch, merge-base check, and fail-closed diff handling, but its two edited workflow files also contained an unintended trailing duplicate `; then` fragment after the final shell block. The earlier 4/4 triggered checks did not execute the modified Research and Serie A workflows, so they did not prove those final workflow files were executable.

The fragment was removed from both workflows and a regression was added to extract each final `run: |` block and execute `bash -n`.

Final exact HEAD: `28104a5b943b697d581d578e133585701a395c43`; base main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.

Exact-head CI: **6/6 SUCCESS**:
- Research PR Validation #41404442560 — SUCCESS; `pytest -k pickle_guard`: **2 passed**; actual guard printed `PASS: no .pkl changes in PR`.
- Serie A PR Validation #41404442533 — SUCCESS; actual guard printed `PASS: no .pkl changes in PR`.
- Bundesliga #41404442712 — SUCCESS.
- Ligue 1 #41404442556 — SUCCESS.
- Product #41404442561 — SUCCESS.
- Eredivisie #41404442553 — SUCCESS; full `test_eredivisie_workflow_contract.py`: **7 passed**.

GitHub compare confirms only `.github/workflows/research-pr-validation.yml`, `.github/workflows/serie-a-pr-validation.yml`, and `tests/test_eredivisie_workflow_contract.py` changed. No model source, original 19-feature contract, weights, candidate SHA, production `.pkl`, Supabase, schedule, target outcome, or promotion behavior changed. PR #706 remains open; HUMAN-MERGE only. Because #701 also modifies the Research workflow, #706 must be rebased after #701 and its exact-head CI rerun before manual merge.


## 2026-11-02 — latest original V2 runtime and pre-match data audit

Audit time: 2026-11-02 09:51 UTC. Source of truth remains main
`40887ebb215730190d7a6c7a1693373ec4afcdfc`. This is a read-only runtime/data
snapshot; no workflow was manually dispatched and no public source was downloaded
during this audit.

### Exact main-only runtime evidence from 2026-11-01

| Workflow | Run | Actual UTC start/end | Main result |
|---|---:|---|---|
| Current-Form Source Capture | `41304706414` | 12:04:17–12:05:19 | SUCCESS |
| Original Forward | `41318729126` | 14:57:22–14:58:02 | SUCCESS |
| Current-Form Forward | `41319862002` | 15:10:27–15:11:15 | SUCCESS |

All three were `schedule` events on exact main SHA
`40887ebb215730190d7a6c7a1693373ec4afcdfc`. Compared with their configured
UTC cron times (05:50, 08:08, 08:18 respectively), the actual starts were
approximately 6h14m, 6h49m, and 6h52m later. This is evidence of substantial
GitHub scheduled-run delay on that date, not proof that a later scheduled run
failed. Do not change cron or infer that a run is missing solely from the nominal
cron time.

Source Capture:
- 19 source-capture regressions passed.
- 3,800 historical rows across ten frozen-season CSVs; 90 current-season rows
  through 2026-10-29; eleven CSV files total.
- Output: `completed_primary_events=90`,
  `current_season_completed_prior_day_rows=90`,
  `feature_source_gate_passed=true`, `paid_provider_calls=0`,
  `supabase_writes=0`, `target_outcomes_scored=false`.
- Artifact ID `13082408243`, 437,021 bytes, ZIP SHA-256
  `09fd39e2e7371f6db887963b5da85e4bb3bb6008314cc97b2a31eabf41d115fe`.
- This is the pre-#699 main-era source manifest. It does not carry the new
  #699 digest-bound current-gate identity list; a fresh capture on resulting
  main after #699 is required before using the integrated identity-SHA path.

Original Forward:
- 71 tests passed.
- Ten historical source files / 3,800 verified historical results.
- `quotes_seen=0`, `v2_diagnostic_previews_captured=0`,
  `paid_provider_calls=0`, `supabase_writes=0`,
  `target_outcomes_read=false`.
- Artifact ID `13088352792`, ZIP SHA-256
  `fb2331e0fbb7a19c3979277814762935a7be0098caf34c149c13c154279c0c11`.

Current-Form Forward:
- 53 tests passed.
- The parent Source Capture artifact was independently verified; reported
  source age at verification was 11,153 seconds.
- `feature_input_gate_count=90`, `current_season_history_rows=90`,
  `quotes_seen=0`, `v2_current_form_shadow_captured=0`,
  `target_outcomes_read=false`, `paid_provider_calls=0`,
  `production_or_supabase_writes=0`.
- Artifact ID `13089345402`, ZIP SHA-256
  `0511879f1a3e425ee97326158bb366912e771d2084653d010f7926ac15251a02`.

### Fresh read-only Supabase pre-match metadata

The Serie A 2026/27 identity-only query selected exactly
`match_date, home_team, away_team` plus separate timestamp aggregates; it did
not select score, goals, or result fields.

- `public.league_finished_results`: 93 raw rows / 93 raw identity strings.
- After the existing V2 Atalanta alias normalization: 90 canonical fixture
  identities. Three duplicate pairs are Atalanta–Sassuolo (2026-08-23),
  Atalanta–Bologna (2026-08-31), and Roma–Atalanta (2026-09-05).
- Date range: 2026-08-22 through 2026-10-29.
- `source_updated_at_utc` is null on all 93 rows; latest
  `persisted_at_utc` is 2026-10-30 05:33:49 UTC.
- The 90 canonical identities match the current CSV's 90 identities, but this
  parity is internal consistency, not independent proof of full fixture
  coverage. Preserve the existing 93-vs-90 external completeness caveat.

Strict pre-match quote predicate remains
`snapshot_time_utc < commence_time_utc`. For Serie A there are 620 such saved
rows; the latest is 2026-10-13 14:48:53 UTC. Across every league in
`public.odds_snapshots`, the count of strictly pre-match snapshots later than
the frozen cohort timestamp `2026-10-18T08:15:32Z` is zero. There are zero
future fixtures in `public.matches` and zero future events with a strictly
pre-match quote.

`public.product_prediction_snapshots` contains 40 rows, all with model
1X2 SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`;
none carries the frozen original V2 candidate SHA
`a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
These are metadata-only checks; no prediction probabilities or target outcomes
were selected.

### Current prospective gate interpretation

The prospective cohort remains frozen at main commit
`9df6f63db10e0128aff89c38fb8c6d88703ef8b8`, with cohort freeze time
`2026-10-18T08:15:32Z`. Since there are zero strictly pre-match quotes after
that freeze time, there are currently zero eligible prospective V2 forecasts.
The 30-primary-completed-forecast gate is therefore CLOSED. No target outcomes
were read.

PR #701 exact HEAD `04233460becc99dcbac0beb83a4e105bb8d64e3c` has 6/6 exact-head
PR workflows SUCCESS. Its Research job log confirms 79 prospective evaluator
tests and 12 forward-adapter/workflow-contract tests passed. This is code/test
readiness, not live market-evaluation evidence. The separate market-only path
remains diagnostic-only; the full three-way review remains blocked until a
permitted non-legacy incumbent is separately pinned.

### Open V2 PR exact-head review snapshot

- #699 `5a1d1bda1c62d36fd092d9e9018a7d2d923e4513`: 7/7 SUCCESS; dedicated
  Frozen V2 Shadow job reports 286 passed. It still needs rebase and exact-head
  CI after #705 is manually merged.
- #705 `102c575b2e88612de1dacd636696ddd01088db75`: 8/8 SUCCESS; dedicated
  shared download-budget tests report 17 passed. Its 85-hour reservation limits
  workflow sessions but not the eleven individual CSV requests in one capture;
  it does not itself establish source permission for repeated model-training
  use.
- #701 `04233460becc99dcbac0beb83a4e105bb8d64e3c`: 6/6 SUCCESS; see the
  prospective-gate note above.
- #702 `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`: 7/7 SUCCESS; 22 offline
  fixture-preview tests passed. It remains manual-only and requires #699,
  a fresh post-#699 source capture, and a separate manual dispatch.
- #706 `28104a5b943b697d581d578e133585701a395c43`: 6/6 SUCCESS; Research
  and Serie A exact-head jobs executed the fail-closed pickle guard, with
  `2 passed` for the targeted guard test and explicit
  `PASS: no .pkl changes in PR`. Rebase after #701 because both touch the
  Research validation workflow.
- #704 `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: exact-head PR validation
  runs succeeded; rebase after #705 and #699 because workflow files overlap.
- #697 remains the documentation PR; its current branch HEAD
  `c69054f738ae1668bf58fe4b9159683fba67b09c` has 7/7 SUCCESS.

HUMAN-MERGE order remains: #705 first; then rebase #699 and rerun exact-head CI;
then #701; then #702 after a fresh #699-era source capture and manual dispatch;
then #704 after #705+#699; then #706 after #701. Do not merge any PR
automatically or move main from this research task.

No source download or provider request was made during this audit. No paid API
calls, Supabase writes/DDL, production `.pkl` changes, model/weight/feature
changes, target-outcome reads, betting, or promotion occurred.


## 2026-11-02 — fresh main runtime and pre-match-only Supabase audit (Research Brain)

Source of truth re-read: main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No PR was merged and no main ref was changed.

### Actual main Current-Form Source Capture and Forward runs

- [Source Capture run 41456825300](https://github.com/MaksimBlud/football-ai/actions/runs/41456825300) completed SUCCESS on main at 2026-11-02 13:53:01–13:54:01 UTC. Its single job passed **19 tests** and produced artifact **13147815874**, 437,965 bytes, GitHub ZIP SHA-256 `67cd15e2e6319196eb13e83b4b65059302c0256b718e876756567efec81614f3`.
- The archive contains ten frozen old-season CSVs plus current `2627/I1.csv`; 3,800 old-season rows and **98** current-season completed prior-day rows. The metadata-only feature-input gate reported **90 canonical identities**. The run reported zero paid calls, zero Supabase writes, and no target-outcome scoring.
- [Current-Form Forward run 41456979071](https://github.com/MaksimBlud/football-ai/actions/runs/41456979071) completed SUCCESS at 13:54:05–13:54:55 UTC; **53 tests passed**. It independently verified artifact 13147815874 and its successful main parent; source age at verification was 49 seconds. It correctly reported `quotes_seen=0`, `v2_current_form_shadow_captured=0`, evaluation gate closed, no target-outcome reads, no paid calls, and no Supabase writes. This proves source archive verification, not a model forecast.

### Latest main old-season diagnostic — important provenance and request finding

[Free Real-Quote Diagnostic run 41473879081](https://github.com/MaksimBlud/football-ai/actions/runs/41473879081) completed SUCCESS at 15:40:19–15:41:25 UTC; **53 tests passed**. Artifact **13155539394** is 425,067 bytes with ZIP SHA-256 `a2c5e7a6e35faeea4829342c732625292bea2ef897c7ec24f18b41eb40a335b5`.

The actual log summary is `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`, `history_rows=3800`, `public_http_requests=10`, `quoted_fixtures=0`, `paid_provider_requests=0`, `quotes_with_source_observed_after_quote=0`, and `supabase_writes=0`. This run is not prospective source-before-quote evidence and produced no scored quote or feature row. It made ten public CSV requests even though a separately verified fresh 11-file current-form archive already existed earlier that day. Next safe engineering task: reuse an already SHA/parent-attested historical archive for old-season diagnostic reads instead of repeating ten public downloads; never relax provenance or freshness rules. The #705 workflow-session budget is not by itself a provider licence and does not prove that eleven individual CSV GETs per session are permitted.

### Read-only Supabase pre-match metadata (no scores, results, probabilities, or payloads selected)

- `league_finished_results`, Serie A 2026–27: **93 raw identity rows / 90 canonical identities** after the existing `Atalanta BC → Atalanta` V2 alias; dates 2026-08-22 through 2026-10-29; latest persistence 2026-10-30 05:33:49 UTC. The query selected identity/date columns only.
- `odds_snapshots`, Serie A: 625 rows, **620** with `snapshot_time_utc < commence_time_utc`, 5 not strictly pre-kickoff, 63 events, zero future strict-pre-kickoff rows. Latest snapshot 2026-10-13 14:48:53 UTC.
- `league_structural_v2_observations`, Serie A: 630/630 strictly pre-kickoff rows across 63 events; latest snapshot also 2026-10-13 14:48:53 UTC; zero future events.
- `league_h2h_bookmaker_snapshots`: zero Serie A rows.
- `product_prediction_snapshots` with the frozen original V2 SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`: zero rows / zero events.
- Strict Serie A quotes after the frozen prospective-cohort timestamp `2026-10-18T08:15:32Z`: **0**; future strict quotes: **0**. Therefore the prospective V2 evaluation gate remains **0/30 and CLOSED**. These were metadata/count queries only; no target outcomes were read.

### Open PR coordination — current exact heads and HUMAN-MERGE dependencies

- #707 `33371988097f02b9e34d37b57c5f0b8731df303a`: 7/7 exact-head checks SUCCESS, including recovery validation. It includes the verified historical-only GitHub artifact loader and recursive fail-closed production `.pkl` inventory guard. Actual recovery is still main-only and has not run on main. #710 is closed unmerged as superseded by #707; do not merge #710 separately.
- #705 `a9144033f5bc3e3138595efc64e9436feaf3ad32`: 8/8 exact-head checks SUCCESS, including 17 shared-budget tests. It is the shared public-source budget PR.
- #709 `268f3fdc82036fca0e44dc0aef20d39423cfda2d`: 7/7 SUCCESS; push validation for current-form source capture is offline.
- #699 `5a1d1bda1c62d36fd092d9e9018a7d2d923e4513`: 7/7 SUCCESS; source/clock/identity/outcome guards, main-ref secret guards, and expanded original-forward dependencies. Rebase and exact-head CI are required after #705 and #709 because the workflow files overlap.
- #701 `04233460becc99dcbac0beb83a4e105bb8d64e3c`: 6/6 SUCCESS; prospective scoring remains fail-closed behind 30 eligible completed forecasts.
- #702 `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`: 7 associated exact-head checks SUCCESS, including its offline feature-preview tests. It is manual-only and makes one zero-credit metadata-only `/events` request (not `/odds`); it emits the original 19 features/readiness only, no probabilities. It requires #699 and a fresh post-#699 source archive before any manual dispatch.
- #704 `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: 7/7 exact-head checks SUCCESS; pins the Python 3.11/3.12 original-V2 research environments, including the free diagnostic workflow. Rebase after #705/#699.
- #706 `28104a5b943b697d581d578e133585701a395c43`: 6/6 SUCCESS; fail-closed `.pkl` diff-guard correction. Rebase after #701.
- #697 remains documentation-only; this entry updates its evidence. HUMAN-MERGE only.

Safe integration order: #707 may be manually merged independently after review; merge #705 before source/diagnostic workflow-trigger changes; rebase and revalidate #709 on resulting main; then rebase and revalidate #699 on that resulting main. Follow with #701, then #702 only after a fresh #699-era source capture and an explicit manual dispatch; rebase #704 after #705/#699 and #706 after #701. Do not auto-merge any PR.

No merge, main mutation, Supabase write/DDL, production `.pkl` change, paid API request, cron/schedule change, target-outcome read, betting, or promotion occurred in this audit.


## Latest MARKET_ANCHOR_1X2_V2 runtime checkpoint — 2026-11-02 17:56 UTC

The current main SHA remains 40887ebb215730190d7a6c7a1693373ec4afcdfc. The November 2 source/recovery audit, including exact artifact digests, source-reader Git blob checks, pre-match-only Supabase aggregates, and the full PR integration order, is recorded in PROJECT_CONTINUITY_ADDENDUM_20261102_V2_RUNTIME_AUDIT.md.

Critical recovery constraint: artifact 13155539394 has a valid ZIP SHA and ten historical CSVs, but its parent main source-reader blob is fae3698769f857fbcb6c8d3ea7826eb81135fec4. PR #707 intentionally requires the integrated strict no-redirect blob 932e58a4f93b0d471ac4b4e0c81fa01f923e46d5 from PR #699, so the current artifact is not admissible. Do not dispatch recovery until #705 is manually merged, #699 is rebased and manually merged, and a fresh successful main diagnostic run uses the exact pinned source-reader blob.

PR #705 is now at 2b9cafedb6deb414e2a5340ebd8f8da566793ecf with exact-head CI 8/8 SUCCESS; it includes the shared 85-hour download budget and offline-only push validation formerly in #709. HUMAN-MERGE only. Main has not been changed.


## Superseding source-budget checkpoint — 2026-11-02 18:08 UTC

The earlier global 85-hour source-download cooldown is superseded. PR #705 now uses 170 hours per approved workflow path, one attempt per path per rolling seven days, a shared concurrency group, and offline-only push validation. This allows both unchanged 05:50 and 06:13 UTC workflows to run once per week without one starving the other. Exact PR #705 HEAD e368326ad52f728f1c3975989aa7a60de2be50c3 has 8/8 CI SUCCESS (20 budget tests, 86 frozen V2 shadow tests; no .pkl changes). The complete integration and legacy-artifact cooldown calculation are in the addendum. HUMAN-MERGE only; main remains unchanged.


## Latest MARKET_ANCHOR_1X2_V2 audit — 2026-11-02 20:57 UTC

Source of truth re-read: main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The main `PROJECT_CONTINUITY.md` still contains the older 2026-10-18 checkpoint; this branch is the pending documentation update. No PR was merged and main was not changed.

### Exact main runtime since the previous checkpoint

The latest relevant scheduled V2 runs are still:

- Source Capture [#41456825300](https://github.com/MaksimBlud/football-ai/actions/runs/41456825300), successful on main 2026-11-02 13:53:01–13:54:01 UTC. Artifact `13147815874`, 437,965 bytes, GitHub digest `sha256:67cd15e2e6319196eb13e83b4b65059302c0256b718e876756567efec81614f3`. The actual job log reports 10 old-season CSVs / 3,800 historical rows, 98 current-season completed prior-day rows, metadata-only feature-input gate count 90, zero paid calls, zero Supabase writes, and no target-outcome scoring.
- Free Real-Quote Diagnostic [#41473879081](https://github.com/MaksimBlud/football-ai/actions/runs/41473879081), successful 2026-11-02 15:40:19–15:41:25 UTC. Artifact `13155539394`, 425,067 bytes, digest `sha256:a2c5e7a6e35faeea4829342c732625292bea2ef897c7ec24f18b41eb40a335b5`. It contains the ten frozen historical CSVs and no prospective quote/forecast. Its parent used the pre-#699 source-reader blob `fae3698769f857fbcb6c8d3ea7826eb81135fec4`; therefore this artifact is **not admissible** for #707 recovery, despite its valid ZIP/member hashes.
- Original Forward [#41498178161](https://github.com/MaksimBlud/football-ai/actions/runs/41498178161), successful 2026-11-02 18:11:22–18:12:16 UTC. Artifact `13166733478`, digest `sha256:a095fd8d3352e441592f47d4382bafa7e828210232a00a948c6e4142810e295e`. Log: `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`, `v2_diagnostic_previews_captured=0`; source archive SHA verified; no paid calls or Supabase writes.
- Current-Form Forward [#41500098611](https://github.com/MaksimBlud/football-ai/actions/runs/41500098611), successful 2026-11-02 18:23:23–18:24:10 UTC. Artifact `13168611787`, digest `sha256:d553efb56a9f937ce2d8b922f2055bcad8f77367bf22790467fa62e58f5ad507`. It verified the source artifact `13147815874` and parent run, but logged `quotes_seen=0` and `v2_current_form_shadow_captured=0`; target outcomes were neither read nor scored.

No newer Original Forward, Current-Form Forward, Current-Form Source Capture, or Free Real-Quote Diagnostic scheduled run appeared in the fresh schedule-filtered Actions inventory through 20:57 UTC.

### Direct source-before-quote code audit on PR #699

The exact #699 branch HEAD is `89d2fc7533e26f24eb51c67323f9d7ac756a8539`; its `serie_a_v2_live_diagnostic_report.py` blob is exactly `932e58a4f93b0d471ac4b4e0c81fa01f923e46d5`, which is the source-reader blob pinned by #707.

Direct code inspection confirms:

- Current-season source observation time is recorded after the HTTP response body is read and validated, not before the request.
- Archive creation time is recorded after source validation and must not precede source observation.
- Forward parent verification requires `run_created_at <= artifact_created_at <= run_completed_at < quote_time`; the parent must be a successful main run of the exact approved source workflow and its SHA must match the artifact.
- The forward verifier checks the persisted gate-identity SHA against the current metadata-only identity set, recomputes the current CSV identity SHA, checks the source CSV SHA, and rejects missing gate identities.
- The current-season latest completed fixture date is separately recorded and recomputed from the CSV; a recent download timestamp is not treated as proof of recent source contents.

This is a code-path verification, not a live quote forecast. The new #699 guards are not yet on main.

### Fresh read-only Supabase strictly pre-match odds inventory

The query selected only `league,event_id,snapshot_time_utc,commence_time_utc` from `public.odds_snapshots`, with strict predicate `snapshot_time_utc < commence_time_utc`. No scores, results, probabilities, or payloads were selected.

| League | Strict pre-match rows | Events | Latest strict pre-match snapshot (UTC) | Rows last 7 days | Future events with strict pre-match quotes |
|---|---:|---:|---|---:|---:|
| Serie A | 620 | 63 | 2026-10-13 14:48:53 | 0 | 0 |
| EPL | 1,135 | 70 | 2026-10-09 15:25:57 | 0 | 0 |
| La Liga | 798 | 52 | 2026-09-11 15:45:28 | 0 | 0 |
| Bundesliga | 394 | 35 | 2026-09-11 15:49:52 | 0 | 0 |
| Ligue 1 | 387 | 35 | 2026-09-11 15:49:24 | 0 | 0 |
| RPL | 153 | 15 | 2026-09-05 15:07:55 | 0 | 0 |
| Eredivisie | 410 | 39 | 2026-09-11 15:50:20 | 0 | 0 |

Primeira Liga and Turkey Super Lig each have nine strict pre-match rows, both last updated 2026-09-11; neither has a future event with a saved strict pre-match quote. Across the listed leagues, there are zero strict pre-match snapshots in the last seven days and zero future events with such quotes. Supabase remained read-only.

### Current V2 PR heads and exact-head CI

- #705 `e368326ad52f728f1c3975989aa7a60de2be50c3`: open; 8/8 exact-head checks SUCCESS, including 20 budget tests and 86 frozen V2 shadow tests. It already includes offline-only Source Capture push validation; #709 is superseded and must not be merged separately.
- #699 `89d2fc7533e26f24eb51c67323f9d7ac756a8539`: open; 7/7 exact-head checks SUCCESS, including 288 frozen V2 shadow tests. Rebase after #705 and rerun exact-head CI before HUMAN-MERGE.
- #703 `f12abfd3a8fc37fb3aff6d394ec3966bc1311b51`: open; 7/7 prior exact-head checks SUCCESS; rebase after #699 before considering merge.
- #704 `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: open; associated exact-head CI runs succeeded in both pinned Python environments; rebase after #705/#699 and rerun.
- #701 `04233460becc99dcbac0beb83a4e105bb8d64e3c`: open; 6/6 exact-head checks SUCCESS. Its prospective market-only scoring remains lazy and closed until 30 eligible prospective completed forecasts; no Brier/LogLoss result exists.
- #706 `28104a5b943b697d581d578e133585701a395c43`: open; 6/6 exact-head checks SUCCESS. Rebase after #701 so the evaluator test and fail-closed production-`.pkl` guard both remain present.
- #707 `cdc93ca0aab9dc75434238bec75ea8759d77ffbd`: open; 7/7 exact-head checks SUCCESS. The recovery code is artifact-only and its PR tests are offline. Do not dispatch main-only recovery until a new successful main diagnostic artifact is produced by exact source-reader blob `932e58...` after #699 is integrated and the new artifact is independently reverified.
- #702 `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`: open; offline preview only; requires #699 and a fresh identity-attested source archive before any manual dispatch.
- #709 is functionally superseded by #705; #694 and #700 overlap the integrated #699 scope. #710 is superseded by the recursive guard already included in #707.

Recommended HUMAN-MERGE sequence: #705; rebase and revalidate #699; then integrate/rebase #703, #704, #701, #706, #702 and #707 according to their workflow overlaps. No automatic merge or main update is permitted.

### Scientific status

The frozen original candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with 19 unchanged features and original weights; `active_lambda=0`, `shadow_lambda=1`. The source feature-input gate count of 90 is not the prospective evaluation cohort. Eligible prospective forecasts remain **0/30**; evaluation gate CLOSED. No protected 2026/27 target outcomes were opened. No V2-over-market claim is supported; Brier/LogLoss comparison has not been run.

No merge, main mutation, Supabase write/DDL, production `.pkl` change, paid provider call, schedule/cron change, target-outcome read, betting, or promotion occurred in this audit.


## Official Football-Data usage-policy blocker — 2026-11-02

The official [Football-Data.co.uk Fair Data Usage Policy](https://football-data.co.uk/contact.php), page updated 2026-11-02, was checked directly. It states that the free CSV/Excel data is intended for private individuals' personal betting or academic research, through manual download or at most light automated downloading (twice per week maximum). It explicitly says the free data is **not intended for commercial or AI data-training projects** and says users seeking such use should assume no permission is granted.

Implications for this V2 recovery:

- The project is an AI model project and its frozen historical candidate/source workflow uses Football-Data CSVs. The current public policy does not establish permission for that AI data-training use.
- PR #705's two-per-week workflow-session cap addresses frequency only. It is not a licence, does not authorize AI training, and does not resolve whether 10 or 11 separate CSV requests inside one session count as heavy automated data demand.
- A verified GitHub artifact digest, per-CSV SHA, source timestamp, or source-before-quote chain proves provenance/integrity, not permission to use the data.
- Do not initiate further Football-Data automated downloads or represent its free CSVs as cleared training data until a source with appropriate rights is established. No paid provider has been authorized or used in this audit.
- This policy finding does not change the frozen V2 weights, candidate SHA, 19-feature contract, active_lambda=0, shadow_lambda=1, or evaluation gate. It is a source-rights blocker, not a model-quality result.

The policy page also states that requests for permission for commercial or AI data-training use should be assumed not to receive approval. This must remain visible in any review of #699, #705, and #707; their technical source guards and frequency cap do not resolve the usage-rights issue.


## Fresh MARKET_ANCHOR_1X2_V2 audit — 2026-11-03 06:55 UTC

This checkpoint was added to the pending continuity branch only. Canonical main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main mutation or merge occurred. Main `PROJECT_CONTINUITY.md` remains the older 2026-10-18 version.

### Frozen original candidate on main

- Candidate JSON path: `research/models/market_anchor_v2_serie_a_frozen_candidate.json`.
- Candidate JSON Git blob SHA on main: `ac1303f6b096664983fbf52443bd0a381b23ba21`.
- Frozen candidate artifact SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- The candidate declares 19 ordered features and a 20 x 2 weight matrix.
- `active_lambda=0` remains the exact de-vigged market; `shadow_lambda=1` remains research-only.
- No original feature, weight, lambda, or candidate file was edited.

### Corrected metadata-only Serie A identity query

The Supabase season key is exactly `2026-2027` (not `2026/27`). The earlier slash-form filter returns zero rows and must not be reused.

A fresh read-only query selected only `match_date, home_team, away_team, source, source_updated_at_utc, persisted_at_utc`; no score/result/settlement column was selected.

- Raw `league_finished_results` rows: 101.
- Canonical fixture identities after the approved Atalanta BC → Atalanta alias: 98.
- Rows with `source IS NULL`: 90.
- Rows without `source_updated_at_utc`: 101.
- Source breakdown: 90 NULL-source rows and 11 `the-odds-api` rows.
- Latest match date: 2026-11-01.
- Latest persistence timestamp: 2026-11-02 21:40 UTC.

The 98 metadata identities are not 98 V2 forecasts and do not open outcomes. The frozen prospective evaluator still requires 30 distinct eligible completed forecasts.

### Strictly pre-kickoff odds inventory

The read-only aggregate used only `league,event_id,snapshot_time_utc,commence_time_utc` and the strict predicate `snapshot_time_utc < commence_time_utc`.

- `odds_snapshots`: 3,966 rows total; 3,915 strictly pre-kickoff rows.
- Strict pre-kickoff snapshots in the preceding seven days: 0.
- Future events with a saved strictly pre-kickoff quote: 0.
- Serie A: 625 raw rows, 620 strictly pre-kickoff rows; latest valid snapshot 2026-10-13 14:48:53 UTC.
- `product_prediction_snapshots`: 40 rows, all under the unrelated EPL market-pair version; 0 rows match the frozen V2 candidate SHA.
- `model_artifact_bundles`: 0 rows.

No quote price was used to select a forecast and no target outcome was queried.

### Important correction: the market-only evaluator already exists in PR #701

The open #701 implementation has two separate paths:

1. The full three-way evaluator still requires a separately pinned non-legacy incumbent and can emit its full review signal only under that contract.
2. The supplementary market-only diagnostic is already implemented separately as `evaluate_market_only_after_gate`, `evaluate_live_market_only_prospective_cohort`, and `evaluate_live_market_only_from_supabase`.

The actual `market_anchor_1x2_v2_prospective_evaluation.py` workflow calls the market-only path. It compares only the de-vigged market with original V2 `shadow_lambda=1`, computes Brier and LogLoss plus paired-bootstrap uncertainty, and does not require the old XGBoost model or a different incumbent. It accepts no incumbent vectors/evidence, opens the exact result-label loader only after 30 eligible completed forecasts, and always suppresses the review signal (`review_signal=false`), betting, and promotion. Therefore the unpinned incumbent blocks the separate full three-way review, but it does **not** block the user's requested market-vs-V2 diagnostic.

This is an additive diagnostic path; it does not modify the original V2 model contract or the existing full three-way review. The 30-primary-completed-forecast gate remains unchanged and closed.

Current eligible prospective V2 forecasts remain 0/30. No Brier or LogLoss result exists. No protected 2026/27 target outcomes were opened.

### Exact current open-PR heads and PR-triggered CI

- #705: HEAD `927174fe85c4ff6e7cf91e994a3dc9b7418494e7`, 8/8 PR-triggered workflow runs SUCCESS; dedicated budget test run `41563655079` and Frozen V2 Shadow run `41563655067`. Budget test log reports 20 passed; shadow log reports 86 passed.
- #699: HEAD `89d2fc7533e26f24eb51c67323f9d7ac756a8539`, 7/7 SUCCESS; Frozen V2 Shadow run `41508145356`, 288 passed.
- #701: HEAD `04233460becc99dcbac0beb83a4e105bb8d64e3c`, 6/6 SUCCESS; market-only evaluator and lazy 30-event outcome gate are covered by its tests.
- #707: HEAD `dfbeed39507fea3cff3c46ef6c64bc25461385a6`, 7/7 SUCCESS; recovery test run `41556671103`, 36 passed. Its PR runtime attestation is synthetic/offline; no main-only historical recovery was executed.
- #702: HEAD `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`, 7/7 SUCCESS.
- #704: HEAD `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`, 8/8 SUCCESS.
- #706: HEAD `28104a5b943b697d581d578e133585701a395c43`, 6/6 SUCCESS.

These are PR-triggered runs attached to the exact listed heads. The available GitHub Actions connector does not expose a repository-wide scheduled-run listing, and `fetch_commit_workflow_runs` explicitly filters to pull-request events. Therefore the 2026-11-03 scheduled Source Capture (05:50 UTC) and Free Real-Quote Diagnostic (06:13 UTC) run IDs/conclusions were not independently retrievable in this audit; do not claim either succeeded or failed.

PR #657, #659 and #660 are merged. #709 is superseded by #705; #700/#694 and the other integrated source/identity protections are represented in #699. #710 is closed unmerged and superseded by #707. HUMAN-MERGE remains mandatory.

### Source rights and remaining operational blockers

The #707 rights manifest still records `rights_status=NOT_GRANTED`, `ai_model_training_permitted=false`, and `commercial_use_permitted=false`. The original frozen candidate can be executed for research without retraining; historical AI-training recovery must remain blocked. A valid SHA or artifact chain is provenance/integrity evidence, not a licence.

PR #705's 170-hour per-workflow-path guard is a frequency guard only, not a licence. Each existing source session still contains multiple CSV GETs; do not infer that the provider's per-week policy permits every individual request merely because the workflow session is rate-limited. No paid The Odds API call or manual public-source download was initiated in this audit.

The next documented engineering task remains reuse of an already verified current-form source artifact for the Free Real-Quote Diagnostic's ten old-season CSVs, without opening the 2026/27 ZIP member. Any such implementation must independently verify artifact SHA, successful main parent run, exact source-code blobs, source timestamps, and strict source-before-quote ordering; it must fail closed if no eligible archive exists. Do not relax the source-rights gate or use the current-season member as a shortcut.

Supabase Security Advisor/list-table metadata also reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. This is a separate security issue; no RLS DDL or policy change was attempted.

No merge, main mutation, Supabase write/DDL, production `.pkl` change, paid request, schedule/cron change, protected-outcome read, bet, or promotion occurred.


## Fresh MARKET_ANCHOR_1X2_V2 operational audit — 2026-11-03 07:23 UTC

This update is documentation-only on the pending continuity branch. Canonical main is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main mutation or merge occurred.

### Latest actual Original Forward / Current-Form Forward evidence

The most recent successful main-only forward runs remain on the exact main SHA above:

- Original Forward-Only Preview [run 41498178161](https://github.com/MaksimBlud/football-ai/actions/runs/41498178161), created 2026-11-02 18:11:22 UTC. The real job log reports **71 tests passed**, source archive attestation verified 3,800 historical rows from 10 pre-freeze CSVs, parent Free Diagnostic run 41473879081 and artifact 13155539394 (GitHub ZIP digest `sha256:a2c5e7a6e35faeea4829342c732625292bea2ef897c7ec24f18b41eb40a335b5`). The forward result is `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`, `v2_diagnostic_previews_captured=0`, `paid_provider_calls=0`, `supabase_writes=0`; target outcomes were not read.
- Current-Form Forward-Only Preview [run 41500098611](https://github.com/MaksimBlud/football-ai/actions/runs/41500098611), created 2026-11-02 18:23:23 UTC. The real job log reports **53 tests passed** and independently verifies Source Capture run 41456825300 / artifact 13147815874, digest `sha256:67cd15e2e6319196eb13e83b4b65059302c0256b718e876756567efec81614f3`. Its manifest reports 98 current-season history rows but feature-input gate count 90; source age at verification was 16,205 seconds. It reports `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `paid_provider_calls=0`, and `production_or_supabase_writes=0`.
- Source Capture [run 41456825300](https://github.com/MaksimBlud/football-ai/actions/runs/41456825300) reports 19 tests passed, 10 historical CSVs plus one current-season CSV, `completed_primary_events=90`, `current_season_completed_prior_day_rows=98`, and no paid calls or Supabase writes. The 98-row CSV count and 90-event feature gate remain distinct; this archive does not attest the later 98 canonical metadata identities.
- Free Real-Quote Diagnostic [run 41473879081](https://github.com/MaksimBlud/football-ai/actions/runs/41473879081) reports 53 tests passed, 3,800 historical rows, 19 original features, `FUTURE_QUOTE=0`, zero feature rows, zero eligible fixtures, zero paid requests and zero writes. The reported zero late-source quotes is vacuous because no quotes were available; it is not a live source-before-quote pass on a non-empty cohort.

No new forward run or real V2 prediction is established by these artifacts.

### 2026-11-03 scheduled-run inventory

A direct GitHub Actions API query for main-branch `schedule` events created between 2026-11-03 05:40 and 07:25 UTC returned 14 scheduled runs. Other repository schedules ran, but **no** run named `Serie A V2 Current-Form Source Capture` or `Serie A V2 Free Real-Quote Diagnostic` appeared in that interval.

Their unchanged main workflow crons are 05:50 UTC and 06:13 UTC respectively. At the 07:23 UTC audit time both were due but absent from the returned schedule-run set. Original Forward (08:08 UTC) and Current-Form Forward (08:18 UTC) were not yet due. This records an observed missing run only; it does not infer why GitHub did not create it. No manual dispatch, retry, schedule edit, or source request was made.

### Fresh read-only pre-match database check

- `odds_snapshots`: 3,966 rows, 3,915 satisfy `snapshot_time_utc < commence_time_utc`, 51 do not; zero strictly pre-match snapshots in the preceding seven days and zero future events with a saved strictly pre-match quote. Serie A: 625 rows / 620 strictly pre-match; latest valid quote remains 2026-10-13 14:48:53 UTC.
- Serie A 2026/27 `league_finished_results` metadata only: 101 raw rows, 101 simple lower/trim identities before approved alias canonicalization, 98 canonical identities after Atalanta BC → Atalanta, 90 `source IS NULL`, 101 `source_updated_at_utc IS NULL`, last match date 2026-11-01, latest persistence 2026-11-02 21:40:05 UTC. No score/result/settlement columns were selected.
- Exact frozen candidate SHA query against `product_prediction_snapshots`: zero rows.
- Future-fixture metadata query against `public.matches` (only league, season, date and team names; no score/result columns): zero rows with `match_date >= CURRENT_DATE`.

The market and source freshness blockers therefore remain unchanged; no V2 prospective forecast exists and the 30-completed-forecast outcome gate remains CLOSED.

### Frozen model and PR state

Main candidate JSON blob remains `ac1303f6b096664983fbf52443bd0a381b23ba21`, candidate artifact SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 ordered features and a 20×2 weight matrix. `active_lambda=0` remains the exact de-vigged market; `shadow_lambda=1` remains research-only.

Exact open PR heads and latest PR-triggered checks re-read for this audit: #705 `927174fe85c4ff6e7cf91e994a3dc9b7418494e7` 8/8 SUCCESS; #699 `89d2fc7533e26f24eb51c67323f9d7ac756a8539` 7/7; #701 `04233460becc99dcbac0beb83a4e105bb8d64e3c` 6/6; #702 `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e` 7/7; #703 `f12abfd3a8fc37fb3aff6d394ec3966bc1311b51` 7/7; #704 `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3` 8/8; #706 `28104a5b943b697d581d578e133585701a395c43` 6/6; #707 `dfbeed39507fea3cff3c46ef6c64bc25461385a6` 7/7; #709 `268f3fdc82036fca0e44dc0aef20d39423cfda2d` 7/7. #709's push-only validation change is already present in #705 and should not be integrated as a duplicate.

#702 remains manual-only and has no live provider execution. Its free `/events` metadata probe is distinct from odds collection; it does not fetch odds or spend odds credits, but remains blocked until the source identity attestation and fresh post-guard source archive exist. No request was made.

Source rights remain research-use-only / AI-training-not-granted; no new Football-Data request was made. The documented next independent engineering task remains reuse of an already verified current-form source artifact for the ten old-season CSVs in Free Diagnostic, reading only old-season ZIP members and never opening the 2026/27 member. This requires the bounded artifact downloader from #703 and the source/identity contract from #699; it is not yet implemented.

No target outcomes, paid calls, Supabase writes/DDL, production `.pkl` changes, model refit, promotion, main changes, or schedule changes occurred. HUMAN-MERGE remains mandatory.


### Independent byte verification of the saved source artifact

Artifact 13147815874 was downloaded through the GitHub artifact connector and inspected without opening the protected 2026/27 CSV member.

- Local ZIP SHA-256: `67cd15e2e6319196eb13e83b4b65059302c0256b718e876756567efec81614f3`, matching both GitHub artifact metadata and the upload-job log.
- ZIP contains 10 historical CSVs, the 2026/27 CSV member, and the JSON manifest.
- The manifest and ZIP central directory were read. All **10/10 pre-freeze historical CSV members** were read and independently SHA-256 matched to their manifest entries; each contains 380 rows, 3,800 total.
- The `serie_a_2627.csv` member was **not opened, hashed, parsed, or read**. Only its filename/size from the ZIP central directory and its non-outcome source timestamp/SHA metadata in the manifest were observed.
- Historical source observations run from 13:53:40 to 13:53:54 UTC; the 2026/27 source observation metadata is 13:53:55.657 UTC; the artifact was created at 13:53:57 UTC. These source times are later than all saved Serie A pre-match quotes (latest 2026-10-13 14:48:53 UTC), so none of those older quotes can pass source-before-quote using this archive.

This independently confirms the old-season bytes and their per-file provenance while preserving the 2026/27 target-outcome embargo. It does not create a prospective forecast or open the 30-event evaluation gate.


## Fresh MARKET_ANCHOR_1X2_V2 operational audit — 2026-11-03 10:47 UTC

This is a documentation-only addendum on the pending continuity branch. Canonical main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main update or merge occurred.

### Frozen original candidate re-read from main

- Candidate JSON blob: `ac1303f6b096664983fbf52443bd0a381b23ba21`.
- Candidate artifact SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original feature list: 19 ordered football features; coefficient matrix: 20×2 (19 features plus intercept).
- Training rows: 3,799; training data cutoff: `2026-06-30T23:59:59+00:00`; training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- Protocol blob: `65729e9639720e67624c1481190aa22ae606f151`; current-form policy blob: `394a426c7ced81e27e12de61087a349bb972b612`; runtime frozen SHA constant matches the candidate SHA.
- `active_lambda=0`, `shadow_residual_lambda=1`, `stability_gate_passed=false`, `automatic_promotion=false`, `opened_2026_27_outcomes_used=false`.

No candidate, weights, feature order, protocol, production `.pkl`, or lambda semantics were changed.

### Main-only scheduled V2 workflow inventory — 2026-11-03

A read-only GitHub Actions API inventory covered four pages (up to 400 most recent main-branch scheduled runs) at 10:47 UTC. The four existing V2 workflows had no 2026-11-03 scheduled run in that inventory, although other main-branch scheduled workflows did run.

Unchanged main cron times:
- Current-Form Source Capture: 05:50 UTC.
- Free Real-Quote Diagnostic: 06:13 UTC.
- Original Forward-Only Preview: 08:08 UTC.
- Current-Form Forward-Only Preview: 08:18 UTC.

All four times had elapsed by the audit. Latest successful V2 main runs remain:
- Source Capture: [41456825300](https://github.com/MaksimBlud/football-ai/actions/runs/41456825300), 2026-11-02 13:53:01 UTC.
- Free Diagnostic: [41473879081](https://github.com/MaksimBlud/football-ai/actions/runs/41473879081), 2026-11-02 15:40:19 UTC.
- Original Forward: [41498178161](https://github.com/MaksimBlud/football-ai/actions/runs/41498178161), 2026-11-02 18:11:22 UTC.
- Current-Form Forward: [41500098611](https://github.com/MaksimBlud/football-ai/actions/runs/41500098611), 2026-11-02 18:23:23 UTC.

This establishes missing scheduled-run records at the audit time, not the root cause. No workflow was manually dispatched, retried, disabled, or rescheduled. No source request was made.

### Fresh read-only Supabase pre-match/source metadata audit

Project `besxwboamipygwvrsblz`. All SQL was read-only; no target score/result/settlement columns were selected.

- `public.odds_snapshots`: 3,966 rows total; 3,915 satisfy strict `snapshot_time_utc < commence_time_utc`; 51 are not strictly pre-match. Across all nine stored leagues: zero strict pre-match rows in the preceding seven days and zero future events with a saved strict pre-match quote.
- Serie A: 625 rows / 620 strict pre-match / 5 not strict; latest strict quote remains `2026-10-13T14:48:53.042620Z`.
- Serie A 2026/27 `league_finished_results` metadata: 101 rows and 101 raw exact (date, home, away) tuples; V2 canonicalization (Atalanta BC → Atalanta, Roma → AS Roma) yields 98 unique identities and 3 alias-collision rows. Date range: 2026-08-22 through 2026-11-01.
- Source provenance on those 101 rows: 90 missing `source`, 90 missing `source_competition`, and **101/101 missing `source_updated_at_utc`**. Latest persistence timestamp: `2026-11-02T21:40:05.112350Z`. The identity query selected only `match_date, home_team, away_team`; the provenance aggregate selected only source/timestamp metadata.
- `product_prediction_snapshots`: zero rows for the exact frozen V2 candidate SHA.
- `model_artifact_bundles`: zero registered bundles.

The last main Source Capture artifact (run 41456825300 / artifact 13147815874) was created on 2026-11-02 and its manifest recorded a 90-identity feature-input gate. Current metadata now has 98 V2-canonical identities. It cannot be treated as a fresh exact-identity source for the current gate; no post-#699 identity-attested source archive exists. The 2026/27 CSV member was not downloaded or opened in this audit.

### Exact open-PR state and integration blockers

All heads below were re-read from GitHub and all listed checks are tied to the exact SHA:

- #705 HEAD `df28494e095ae131e553e3f4e303b2eecca4a0db`: **8/8 SUCCESS**. Includes the 170-hour per-workflow source budget, `GITHUB_TOKEN` / `actions:read`, and the push-only offline validation split for Current-Form Source Capture.
- #699 HEAD `49383700ce50ac6df5d648d2b0c932748414f1f2`: **7/7 SUCCESS**. Its current source-capture workflow still has one capture job on push. After #705 is manually merged, a rebase must preserve #705's offline-only push job split and budget; a new integration warning was posted to #699 (comment 6601743680). Do not merge the stale branch over #705.
- #712 HEAD `140fe272027fb5c3f6ce6aa1c3f659294cbf3bb4`: **8/8 SUCCESS**, but not mergeable as-is from a safety perspective. Its current-season CSV request still uses an unbounded default redirect-following `get(...)`, and a missing token can fall back to ten direct historical downloads. It must be rebased onto the guarded #699/#705 implementation, retain strict current-source URL/stream limits, and fail closed before public requests when authenticated cache provenance is absent. Existing review comment: 6601143722.
- #701 HEAD `04233460becc99dcbac0beb83a4e105bb8d64e3c`: **6/6 SUCCESS**. Its independent evaluator still requires 30 eligible prospective completed forecasts before any target-outcome read.
- #707 HEAD `dfbeed39507fea3cff3c46ef6c64bc25461385a6`: **7/7 SUCCESS**. The rights manifest remains `rights_status=NOT_GRANTED`, `ai_model_training_permitted=false`, `commercial_use_permitted=false`; do not retrain/recover weights from that source archive.
- #697's prior exact head `de8700b8ff3999860c42100e86dde306692f1918` had 7/7 SUCCESS before this documentation update; rerun its exact-head checks after this commit.

HUMAN-MERGE only. No branch was merged and main was not changed.

### Scientific and safety status

- Eligible prospective V2 forecasts: **0/30**.
- No Brier/LogLoss result exists for the frozen candidate on an eligible independent prospective cohort.
- No 2026/27 target outcomes were read or scored.
- No public Football-Data download, paid odds request, Supabase write/DDL, production `.pkl` change, model refit, promotion, bet, or schedule change occurred.
- Supabase Security Advisor at 2026-11-03 10:51 UTC still reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`; four other tables have RLS enabled but no policies. This is a separate security issue; no DDL or policy change was attempted.

The next technical milestone remains a compatible, exact-head integration of #705 + #699 + one historical-source reuse implementation, followed by a fresh source identity attestation and a real pre-kickoff quote. No model-quality claim is permitted before the frozen 30-event gate and independent Brier/LogLoss comparison.


## Fresh MARKET_ANCHOR_1X2_V2 audit — 2026-11-03 13:10 UTC

This addendum records a new read-only Supabase/GitHub audit and a producer/consumer integration defect found in the open historical-source reuse PR. Main is unchanged at `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` blob remains `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`. This documentation update is on the existing continuity PR branch only.

### Live identity-only feature gate and saved pre-match quotes

At 2026-11-03 13:10:27 UTC, a read-only query of `public.league_finished_results` selected/aggregated only identity and source-provenance metadata for Serie A season `2026-2027`; no goals, scores, results, settlement or prediction-correctness fields were selected.

- Raw identity rows: **101**.
- V2-canonical unique identities: **98** (runtime aliases Inter→Inter Milan, Milan→AC Milan, Roma→AS Roma, Verona→Hellas Verona, plus V2-local Atalanta BC→Atalanta).
- Date range: 2026-08-22 through 2026-11-01.
- Source metadata: 90 rows have NULL `source` and `source_competition`; 11 rows are tagged `the-odds-api / soccer_italy_serie_a`; all 101 lack `source_updated_at_utc`.
- Latest persistence metadata: 2026-11-02 21:40:05.112350 UTC.

The feature-input gate is open by count, but this metadata is not itself a source archive or source-rights attestation. The model feature source still requires its own archived CSV SHA and source-before-quote proof.

The same read-only query found, across all nine stored leagues, **zero strict pre-match quote snapshots in the preceding 7 days and zero future fixtures with a saved strict pre-match quote**. Serie A has 625 stored rows, 620 strictly pre-kickoff; its latest strict pre-match quote remains 2026-10-13 14:48:53.042620 UTC. There are zero `product_prediction_snapshots` for the exact frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.

### Re-read of actual main runtime artifacts

The latest verified main runs remain on main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`:

- Source Capture run [41456825300](https://github.com/MaksimBlud/football-ai/actions/runs/41456825300), artifact `13147815874`, ZIP SHA-256 `67cd15e2e6319196eb13e83b4b65059302c0256b718e876756567efec81614f3`. Its actual log reports the feature-input gate count **90**, 98 completed prior-day CSV rows, 10 old-season files, 11 total files, no paid calls, no Supabase writes and no target scoring.
- Free Diagnostic run [41473879081](https://github.com/MaksimBlud/football-ai/actions/runs/41473879081) reports zero scored diagnostics, zero source-after-quote cases, zero paid calls and zero Supabase writes.
- Original Forward run [41498178161](https://github.com/MaksimBlud/football-ai/actions/runs/41498178161) verified the old-season source archive (10 CSVs / 3,800 rows) but reports `quotes_seen=0`, `forecasts_created=0`.
- Current-Form Forward run [41500098611](https://github.com/MaksimBlud/football-ai/actions/runs/41500098611) verified artifact `13147815874` and correctly read no target outcomes, but captured `quotes_seen=0` and `v2_current_form_shadow_captured=0`.

The source archive's feature-input gate count (90) is now behind the 98 canonical identities in Supabase. The old archive cannot be used as proof of complete coverage for the current identity set. The older main forward implementation reported freshness by age only; the identity-set SHA/coverage guard in #699 is needed before a later quote can be admitted. No current-season CSV member was opened in this audit.

### Original V2 runtime execution — synthetic only

PR #707's main-only recovery/runtime-attestation workflow [41556671103](https://github.com/MaksimBlud/football-ai/actions/runs/41556671103) was re-read. It completed SUCCESS; its dedicated test command reported **36 passed**. The log attests:

- frozen source commit `df19777087fb89af049eedce44ff93f0aa6e6360`;
- original candidate artifact SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, candidate Git blob `ac1303f6b096664983fbf52443bd0a381b23ba21`;
- 19 ordered features and 20×2 weights;
- `active_lambda=0` equals the synthetic market vector exactly;
- `shadow_lambda=1` output is finite and sums to one;
- `stability_gate_passed=false`, `real_events_scored=0`, `training_performed=false`, `target_outcomes_read=false`, `production_pkl_touched=false`, `no_bet=true`.

This is a real execution of the original frozen inference code on deterministic synthetic input, **not** a real-match forecast, prospective evaluation, or evidence of superiority.

### New PR #712 producer/consumer contract defect

PR #712 current HEAD is `b1c38a8f579c1a2de7d6d63a592bb97ddc82d904`; its eight CI workflows are SUCCESS. Static review found that its producer and consumer do not share a manifest contract:

- The #712 `serie_a_v2_current_form_source_capture.py` reads an integer gate count and writes only count/field-name metadata; it contains no `gate_fixture_identity_*` or `current_source_fixture_identity_*` fields.
- Its `serie_a_v2_historical_source_reuse.py` requires the full gate identity list, count/SHA, current-source identity count/SHA and zero-missing coverage. An archive produced by the current #712 capture function would therefore be rejected by its own later reuse verifier.
- The 42 reuse tests construct synthetic archives that already contain the required fields; the current source-capture tests do not assert those producer fields or exercise a producer-to-consumer round trip.
- Integrated PR #699 HEAD `49383700ce50ac6df5d648d2b0c932748414f1f2` does emit the identity list/count/SHA and current-source identity digest. Those fields must be preserved when #712 is rebased/integrated.

A specific review comment was added to #712: [comment 6604625779](https://github.com/MaksimBlud/football-ai/pull/712#issuecomment-6604625779). Required fix: integrate the #699 identity-attested producer while retaining #705's budget and push-only offline split, then add an end-to-end test that feeds a manifest produced by `capture_source_archive()` into the reuse verifier. Do not merge #712's current HEAD independently.

### Current integration and scientific gates

- #705 HEAD `df28494e095ae131e553e3f4e303b2eecca4a0db`: 8/8 exact-head CI SUCCESS; contains the 170-hour per-workflow public-source budget and push-only offline validation.
- #699 HEAD `49383700ce50ac6df5d648d2b0c932748414f1f2`: 7/7 exact-head CI SUCCESS; contains the strict source URL/clock and identity-set SHA/coverage producer. It must be integrated after #705 without losing #705's workflow split/budget.
- #712 HEAD `b1c38a8f579c1a2de7d6d63a592bb97ddc82d904`: 8/8 CI SUCCESS, but blocked by the producer/consumer mismatch above and its old base.
- #701 remains exact-head 6/6 SUCCESS. Its evaluator has `FROZEN_INCUMBENT_REFERENCE=None` and correctly returns before calling the lazy outcome loader. The frozen policy still requires a distinct pinned non-legacy incumbent; no eligible same-league non-XGBoost incumbent is registered. Do not substitute the old XGBoost model or duplicate the market vector as a separate incumbent.
- Eligible prospective forecasts remain **0/30**; no target outcomes were read. Even after 30 eligible forecasts, evaluation remains blocked until the preregistered incumbent requirement is legitimately resolved without changing the frozen contract.
- PR #707 source-rights manifest remains `NOT_GRANTED` for AI model training/recovery. Do not rebuild weights from that archive; integrity hashes are not data-use permission.

No PR was merged, main was not modified, no source/odds request was made, no paid provider call or Supabase write/DDL occurred, no protected 2026/27 target outcome was read, no production `.pkl` changed, and no workflow schedule or other agent was changed. HUMAN-MERGE remains mandatory.


## 2026-11-03 19:05 UTC — fail-closed AI-usage rights across V2 live entrypoints

### Fresh main and immutable model

- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No main update or merge was made.
- The original `MARKET_ANCHOR_1X2_V2` candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with the frozen 19-feature contract, `active_lambda=0`, and `shadow_residual_lambda=1`. No weights, features, or production pickle files were changed.
- The current main `PROJECT_CONTINUITY.md` was read before work; this entry is being added only to this documentation PR branch.

### Main-only runtime and pre-match data audit

Verified existing main runs and their artifacts; no workflow was dispatched and no new provider request was made:

- Source Capture run `41640753996`, artifact `13231843819`, ZIP SHA-256 `4e6fb5531a2206a353fe00fa1ebb0b4d20b3c6ae41ab49a7c672f8dab6d29cd8`. Its parent report recorded 10 old-season CSVs, 3,800 old-season rows, 100 current-season completed prior-day rows, and 98 canonical primary fixture identities.
- Free Real-Quote Diagnostic run `41650074683`: 10 historical source files, 3,800 historical rows, `quoted_fixtures=0`, `diagnostic_scored=0`, no paid calls.
- Original Forward run `41670482076`, artifact `13248390793`: `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`; no outcomes read.
- Current-Form Forward run `41672409582`, artifact `13249097138`: verified source artifact `13231843819` and its parent run, but `quotes_seen=0` and `v2_current_form_shadow_captured=0`; no outcomes read.

Read-only Supabase pre-match audit:

- `odds_snapshots`: 3,915 strictly pre-kickoff rows across 327 events; zero strict pre-match rows in the last seven days; zero future events with a saved pre-match quote.
- Latest strict pre-match snapshots by league remain: Serie A 2026-10-13 14:48:53 UTC; EPL 2026-10-09 15:25:57 UTC; the other queried leagues are older (September 2026).
- `product_prediction_snapshots`: 40 total, zero with the frozen V2 candidate SHA, latest generated 2026-10-09 15:29:33 UTC.
- Identity-only `league_finished_results` query: 101 raw Serie A 2026/27 rows, 98 canonical fixture identities after the frozen Atalanta alias. The query selected only `match_date,home_team,away_team`; no score/result fields were read. Provenance metadata is incomplete: 90 rows lack `source`, 90 lack `source_competition`, and all 101 lack `source_updated_at_utc`.

### Source rights — newly enforced, not merely documented

The official Football-Data policy page was rechecked on 2026-11-03. It expressly addresses AI-usage requests and says users seeking such use should assume no data-use permission is granted; the free CSVs are intended for personal betting or academic interest/research via manual or at most light (twice-weekly maximum) automated download. Source: https://football-data.co.uk/contact.php.

The fail-closed manifest records `rights_status=NOT_GRANTED`, `ai_usage_permitted=false`, and `ai_model_training_permitted=false`. The new exact-head #707 commit `240f32e4f5094c57de7a7b9355b61cc352daab51` adds a separate SHA-bound `AI_USAGE` permission check and a no-network/no-inference blocked report. It is called before Supabase reads, GitHub artifact listing, public HTTP requests, feature extraction, or inference in the four live V2 entrypoints:

- `serie_a_v2_live_diagnostic_report.py`;
- `serie_a_v2_current_form_source_capture.py`;
- `serie_a_v2_current_form_forward_capture.py`;
- `serie_a_v2_forward_capture.py`.

The #707 exact-head CI is **8/8 SUCCESS**. Its recovery job compiled all four entrypoints, ran **42 tests** in the recovery/rights/runtime suite, completed the synthetic original-V2 runtime attestation, and proved production `.pkl` hashes unchanged. This is a branch result only; the gate is not active on main until HUMAN-MERGE and the required rebase sequence.

The prospective evaluator is a separate live entrypoint. PR #701 was therefore also updated at HEAD `3dd5ec66e196c57a1a0f3de8629b39554ffd07b4` to carry the identical helper/manifest and block before artifact, Supabase, or outcome access. Its exact-head CI subsequently completed **6/6 SUCCESS**: evaluator tests **79 passed**, runner tests **8 passed**, and forward-artifact/selection/workflow tests **14 passed**. Do not treat the evaluator as rights-gated on main until that PR is integrated.

### Exact evaluation distinction

- The market-only path `evaluate_market_only_after_gate` is a supplementary **de-vigged market vs frozen V2 shadow** diagnostic. It does not require or fabricate a third incumbent vector, but it still requires 30 unique eligible completed primary forecasts and invokes the lazy outcome loader only after that gate. It cannot emit the full three-way review signal.
- The full three-way `evaluate_after_gate` remains blocked because `FROZEN_INCUMBENT_REFERENCE=None`; a distinct, pinned, same-league non-legacy incumbent is not registered. Do not substitute the old XGBoost production model or duplicate the market vector as a fake incumbent.
- Current eligible prospective forecasts remain **0/30**. No protected 2026/27 target outcomes were read; no Brier/LogLoss result exists; no V2 advantage over market is established.

### Current PR queue — exact heads, not stale continuity hashes

- #705 `8b139335e6722b7c4f5286962486bca84bced20d`: 8/8 exact-head CI SUCCESS. First HUMAN-MERGE step; shared 170-hour download budget. Do not merge automatically.
- #699 `fecf8dd01ad6ea3b9eabd0dfb31167f397ae4e3a`: 7/7 exact-head CI SUCCESS. Rebase after #705; preserve the budget and identity-attested producer.
- #712 `331e7934f92763d8df2c6c35e01b6b26a80bcf5d`: 9/9 exact-head CI SUCCESS. Keep open until rebased on the integrated #699/#705 line; require the end-to-end producer-to-consumer archive test and do not use the pre-#699 main archive as identity-attested cache input. #711 remains a draft overlapping alternative; do not merge both.
- #701 `3dd5ec66e196c57a1a0f3de8629b39554ffd07b4`: new rights-gated evaluator HEAD; CI pending at the time of this entry.
- #707 `240f32e4f5094c57de7a7b9355b61cc352daab51`: 8/8 exact-head CI SUCCESS; must be rebased after #699 before integration.
- #697 documentation branch: this update is pending exact-head CI. #709 remains redundant with the push/offline protection already included in #705.

No PR was merged, no main ref changed, no workflow schedule or other agent was changed, no paid provider request or Football-Data download was initiated, no Supabase write/DDL occurred, no protected outcome was read, and no production `.pkl` was changed. HUMAN-MERGE remains mandatory.


### Integration-order correction — overlapping V2 source files

A fresh changed-file intersection check confirms that #707 and #712 both modify exactly:

- `serie_a_v2_current_form_source_capture.py`;
- `serie_a_v2_live_diagnostic_report.py`.

Therefore the safe HUMAN-MERGE/rebase order is stricter than a simple #699 → #707 sequence:

1. #705 first (shared 170-hour budget and push-only offline validation).
2. Rebase #699 on the resulting main, rerun exact-head CI, then human-merge #699 (identity-attested source producer and strict URL/clock checks).
3. Rebase #712 on that integrated #705/#699 main, preserve its producer-to-consumer identity-manifest round-trip and negative regressions, rerun exact-head CI, then human-merge #712. Its current 9/9 is on the old main base and is not sufficient by itself.
4. Rebase #707 **after #712**, not before it, so the AI-usage rights guard is applied to the final historical-reuse versions of the two overlapping scripts. Rerun exact-head CI and human-merge only after that rebase.
5. Rebase #701 after #707 and rerun exact-head CI. Its new branch carries byte-identical rights helper and manifest blobs (`d1a3bcfe...` and `0f2cde54...`) to #707, so the shared files should converge to one identical main version.
6. Merge the documentation PR #697 only after its current exact-head CI passes; it can then record the integrated heads.

Do not merge #707 before #712: that could overwrite the verified historical-cache producer/consumer work. Do not merge #712 before #699: its source reader must inherit #699's exact URL/clock/identity protections and #705's shared budget. #709 is redundant with #705; #711 is the overlapping draft alternative to #712.


## 2026-11-03 19:20 UTC — correction: research inference is distinct from AI training

A fresh line-by-line re-read of the provider's current official policy (page updated 03/11/26) corrected the broader interpretation in the preceding entry. The page says the free CSV/Excel data are intended for private individuals' **personal betting and/or academic interest/research only**, by manual download or at most light automated download (maximum twice per week). It says the data are **not intended for commercial or AI data-training projects** and that users seeking those uses should assume no permission is granted. It does **not expressly prohibit frozen-weight inference** for personal/academic research. Source: https://football-data.co.uk/contact.php.

Therefore the earlier `AI_USAGE` permission gate was too broad for the stated V2 research task and has been corrected on the open branches. This project uses the already-frozen 19-feature/weight candidate only for noncommercial personal/academic research inference, with current-season results used solely as lagged features. No fit, refit, feature selection, threshold tuning, commercial use, public product publication, betting, or production promotion is permitted. This is an operational interpretation of the provider's stated personal/academic research category, **not** a provider-issued AI-inference licence; if the intended use changes to a public product or commercial service, this free-data scope is not sufficient.

The revised manifest is `rights_status=CONDITIONAL_RESEARCH_ONLY`, `research_inference_permitted=true`, `research_inference_scope=PERSONAL_BETTING_OR_ACADEMIC_RESEARCH_ONLY`, `ai_model_training_permitted=false`, `commercial_use_permitted=false`, and `public_product_use_permitted=false`. The new `require_personal_research_inference_scope()` gate checks these restrictions, the official policy URL/date, and a maximum of two automated download sessions per rolling seven days. The separate training-recovery function still requires explicit SHA-bound evidence and remains blocked. #705's shared 170-hour budget and #712's verified historical cache remain required before any further automated source refresh; do not dispatch a manual download.

Revised exact heads (CI was starting after these updates):
- #699: `61c77cef65714d4ca9035fc6763f8b2d65c773cd` — scope gate applied to all four live V2 entrypoints on top of the strict #699 source reader.
- #707: `4ef792b2bb5b425b6909bbddab1ed3395fe7c76e` — same helper/manifest and recovery rights gate.
- #701: `af31c747e6deb636157bf3f60ca84b6361ac1d36` — prospective evaluator checks the same restricted research scope before any external read.

The revised helper and manifest have identical blob SHAs across all three branches, so they converge without duplicate implementations. The safe integration order remains #705 → #699 → #712 → #707 → #701, with #707 rebased after #712 because both modify the current-form source-capture and diagnostic scripts. #712 must preserve #699's URL/clock/identity hardening and the restricted research-scope gate.

The main-only data audit remains unchanged: zero strict pre-match quotes in the last seven days, zero future fixtures with saved pre-match quotes, zero original-V2 product snapshots, and zero eligible prospective forecasts. No target outcomes were read and no Brier/LogLoss was computed. No source request, paid request, Supabase write/DDL, production `.pkl` change, main update, schedule change, or other-agent change occurred in this correction.


## 2026-11-04 08:34 UTC — rights-trigger regression and fresh main-only runtime audit

### Exact main baseline
- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main ref was changed.
- Frozen candidate JSON Git blob remains `ac1303f6b096664983fbf52443bd0a381b23ba21`; candidate artifact SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Protocol JSON Git blob remains `65729e9639720e67624c1481190aa22ae606f151`; the V2 implementation and feature-builder blobs remain unchanged. The original 19-feature order, weights, scaler, imputer, `active_lambda=0`, `shadow_lambda=1`, and failed stability gate are unchanged.

### New #699 exact-head regression fix
- Updated the existing #699 research branch only; exact new HEAD: `bda4c810cb1248a67c69f8746191fc9c76c959ab`.
- Found that the four live V2 workflow push-path filters omitted their newly imported source-rights helper and checked-in rights manifest. A policy/helper edit could therefore change the runtime gate without triggering the corresponding offline workflow re-audit.
- Added `market_anchor_v2_source_rights.py` and `research/source_rights/football_data_co_uk.json` to the push-path filters of:
  - `serie-a-v2-current-form-source-capture.yml`;
  - `serie-a-v2-current-form-forward-preview.yml`;
  - `serie-a-v2-forward-preview.yml`;
  - `serie-a-v2-free-real-quote-diagnostic.yml`.
- Extended `tests/test_serie_a_v2_current_form_dependency_triggers.py` and added `test_source_rights_changes_reaudit_every_live_v2_workflow` to `tests/test_serie_a_v2_current_form_source_workflow_contract.py`.
- The new regression requires both rights inputs to trigger all four live workflow audits. No cron, job condition, permission, source URL, data, model, or outcome-gate behavior was changed.
- Exact-head CI: **7/7 SUCCESS** on `bda4c810cb1248a67c69f8746191fc9c76c959ab`:
  - Product #41800141105;
  - Serie A Frozen V2 Shadow Tests #41800141067;
  - Eredivisie #41800141053;
  - Bundesliga #41800141073;
  - Serie A #41800141055;
  - Ligue 1 #41800141052;
  - Research #41800141149.
- The frozen shadow job ran **315 passed**. Its final production-pickle check ran `git diff --exit-code -- '*.pkl'` and passed. Research validation also completed successfully. The PR remains open and HUMAN-MERGE only.

### Fresh main-only workflow evidence
- The latest main V2 workflow runs still belong to 2026-11-03; no main-branch Serie A V2 source-capture, free diagnostic, original forward, or current-form forward run was present in the latest Actions run listing at 2026-11-04 08:32 UTC.
- Last verified main runs:
  - Source Capture #41640753996 — schedule, SUCCESS; 98 primary feature-gate identities, 100 current-season completed rows, 10 historical CSVs, 11 total source files; paid calls 0, Supabase writes 0, target outcomes not scored.
  - Free Real-Quote Diagnostic #41650074683 — schedule, SUCCESS; 3,800 historical rows, 19 features, 10 public historical HTTP requests, zero quotes, zero diagnostic scores, Supabase writes 0.
  - Original Forward #41670482076 — schedule, SUCCESS; 3,800 historical results verified, zero quotes, zero forecasts, zero future quotes checked, zero V2 diagnostic previews, no protected outcomes read.
  - Current-Form Forward #41672409582 — schedule, SUCCESS; source artifact SHA verified, source age 11,616 seconds, 98 gate identities, zero quotes, zero V2 current-form shadows, target outcomes not read/scored.
- These are successful technical/source runs, not model-quality evidence. No fresh quote-backed 19-feature V2 forecast exists.

### Read-only pre-match Supabase audit
- `public.odds_snapshots`: 3,966 total rows; 3,915 strictly pre-match; zero strictly pre-match rows in the last seven days; zero future events with a strictly pre-match quote; latest strict pre-match quote remains 2026-10-13 14:48:53 UTC.
- `public.product_prediction_snapshots`: 40 rows total and 40 strictly pre-match rows, but **zero** rows for the original V2 candidate SHA and zero original-V2 events.
- Queries used only snapshot/generated timestamps, kickoff timestamps, event IDs, and the frozen candidate SHA. No target score/result/settlement columns were selected.

### Integration and execution boundaries
- #705 remains open at `8b139335e6722b7c4f5286962486bca84bced20d`, with 8/8 exact-head checks successful. It must be manually merged first to install the shared two-session-per-rolling-week source-download guard and offline-only push validation.
- #699 must then be rebased onto the #705-integrated main and rerun at its exact new head, preserving #705's budget and push/offline behavior. #699 is not authorized for automatic merge.
- #712 remains open at `1c0f5a424dd51abc0f1a7dedfb7f8ff1047b3339` with 8/8 checks successful, but must be rebased after #699 because it modifies the same source producer/diagnostic files.
- #701 remains open at `0dbb1106e98f4c83f2bce79d9fb7dd634087e367` with 6/6 checks successful; rebase after the verified source producer/consumer chain before any prospective evaluation.
- #704 dependency locks (14/14 checks), #706 production-pickle guard (6/6), and #702 manual-only zero-credit fixture/feature-readiness probe (7/7) remain open on the old main base; revalidate exact heads after their dependencies are integrated.
- #707's manual recovery workflow performs a historical `fit_candidate_artifact` reproduction check and requires `ai_model_training_permitted=true`; the checked-in rights manifest currently says false. Do not dispatch it under the present rights scope. The frozen candidate already exists with its expected SHA; this recovery is not required for the current frozen-weight inference path.
- #713 is closed as superseded and was never merged.

### Scientific gate
- Eligible prospective completed forecasts remain **0/30**.
- Brier Score and LogLoss remain uncomputed; no superiority claim against the de-vigged market or incumbent is justified.
- No protected 2026/27 outcomes were read. No fitting/refitting, threshold tuning, candidate/weight/protocol changes, production `.pkl` changes, paid API calls, Supabase writes/DDL, promotion, betting, merge, or schedule changes occurred in this update.


## 2026-11-04 15:22 UTC — V2 exact-head recheck, cumulative source-use breach, and current data gate

### Frozen original identity rechecked

Main is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`.

The original frozen inputs remain byte-identical between main and the current #699 branch:
- Candidate JSON Git blob: `ac1303f6b096664983fbf52443bd0a381b23ba21`; embedded candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Protocol JSON Git blob: `65729e9639720e67624c1481190aa22ae606f151`.
- Original feature builder: `historical_football_signal_lab.py`, blob `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- Frozen V2 shadow engine: `market_anchor_1x2_v2_shadow.py`, blob `b2770d726ffafe7a3cef706b57d3391063cbfe1b`.

The #699 wrapper file `serie_a_v2_frozen_shadow_preview.py` is not byte-identical to main: its `shadow_preview` clock check now requires a real UTC offset, and the outcome guard adds recursive forbidden-key detection. The core frozen shadow engine, candidate JSON, protocol JSON, feature builder, and the `load_verified_original` / market-normalization functions are unchanged. The wrapper diff does not alter the frozen probability formulas. The V2-only active identity remains market (`active_lambda=0)); `shadow_lambda=1` remains research-only.

### Current main source and forward runtime — actual run logs

- Source Capture [run 41836971469](https://github.com/MaksimBlud/football-ai/actions/runs/41836971469), scheduled on main: SUCCESS; 19 focused tests passed; 10 historical CSVs plus one current-season CSV; 100 current-season completed rows; 3,900 historical/current history rows; candidate SHA matched; 0 paid calls, 0 Supabase writes, no target scoring. Artifact #13327281383, ZIP SHA-256 `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`.
- Current-Form Forward [run 41837103174](https://github.com/MaksimBlud/football-ai/actions/runs/41837103174), SUCCESS: independently verified the source artifact and its successful main parent at a source age of 42 seconds; candidate SHA matched; 0 saved quotes, 0 V2 shadow forecasts, no outcome read/scoring, 0 paid calls, 0 writes. Artifact #13327081347.
- Free Real-Quote Diagnostic [run 41847314320](https://github.com/MaksimBlud/football-ai/actions/runs/41847314320), SUCCESS; 53 tests passed, but the live diagnostic made 10 public HTTP requests, saw 0 quoted fixtures, scored 0, and reported `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`. Artifact #13332260799, ZIP SHA-256 `72a32dc61d6e230be46bc5fe69a52e97142a79816af33c66f58066e0ceb6e8d8`. No paid provider calls or Supabase writes.

The Nov 4 source artifact is still from the pre-#699 producer: it has a numeric feature-input gate count but not the canonical identity-list/count/SHA attestation and rights-helper provenance required by the new #699 consumer. It is therefore not eligible for #699's identity-attested evaluator/cache chain despite the successful legacy forward verification.

### Cumulative public-source use — policy blocker

Four actual automated public-source sessions are verified within roughly 25 hours:
- Nov 3 Source Capture #41640753996, artifact #13231843819, 11 source files.
- Nov 3 Free Diagnostic #41650074683, artifact #13236383688, 10 public HTTP requests, 0 quotes and 0 scores.
- Nov 4 Source Capture #41836971469, artifact #13327281383, 11 source files.
- Nov 4 Free Diagnostic #41847314320, artifact #13332260799, 10 public HTTP requests, 0 quotes and 0 scores.

The checked-in rights manifest limits automated source access to **two sessions per rolling seven days**. The four observed sessions exceed that limit. No further Football-Data source session should be initiated while the shared guard is absent or before its cooldown permits access. This is a source-use compliance blocker, not a model-quality finding.

Main still has the unguarded daily source-capture cron at 05:50 UTC and free-diagnostic cron at 06:13 UTC; both current main workflows also have download-capable push paths. The next source-capture slot on current unguarded main is Nov 5 05:50 UTC. Do not manually dispatch either workflow.

PR #705 is now at exact HEAD `97a94f5ba3aa921175071e490a9c698aaf0a414b`, **8/8 exact-head checks SUCCESS** (23 shared-budget tests, 86 frozen V2 shadow tests, production-`.pkl` diff guard passed). It adds the shared 170-hour per-workflow guard, common concurrency, attempt marker before source requests, and offline-only push validation. HUMAN-MERGE is still required; main has not changed. Its bootstrap tests include both latest Nov 4 artifacts. After manual merge, expected next unchanged schedule slots after each 170-hour cooldown are source capture **Nov 12 05:50 UTC** and free diagnostic **Nov 12 06:13 UTC**. The guard controls frequency; it does not grant rights.

PR #699 current exact HEAD `09c95fde22091311cbe56da236e76360aad33f72`: **7/7 SUCCESS**, 321 frozen shadow tests and 13 current-form dependency-trigger tests; no production-`.pkl` changes. It must be rebased after #705 and its workflow YAMLs reconciled to retain #705's shared concurrency, marker reservation, actions:read/GITHUB_TOKEN, and offline push validation while preserving #699's rights, source identity SHA, and workflow-run freshness checks. Do not merge its present workflow files over #705 unmodified.

PR #701 current exact HEAD `99e67b61f474aa5de51d7b829405a23a44cbc4fe`: **6/6 SUCCESS**, including 79 evaluator/runner tests and 17 forward-artifact bridge tests. Its market-only outcome loader remains behind the unchanged 30-primary-completed-forecast gate; the full incumbent comparison remains separately blocked until a same-league non-legacy incumbent is pinned.

PR #712 current exact HEAD `4b9b1281a8ab81988ea713eb5974d1e55dbba81d`: only its targeted offline source-reuse workflow is verified on this HEAD (53 tests); the broader 9/9 claim is for an older predecessor. Rebase after #705/#699 and rerun full exact-head CI. Do not consume the pre-#699 Nov 4 artifact as identity-attested cache input.

### Read-only Supabase pre-match audit

Only pre-match snapshot fields and metadata-only fixture identities were queried:
- Across `public.odds_snapshots`, 3,966 total rows and 3,915 strictly pre-match rows; **zero** strictly pre-match rows in the last seven days and **zero** future events with a strictly pre-match quote.
- Serie A: 625 rows, 620 strictly pre-match, 63 events; latest strictly pre-match quote remains **2026-10-13 14:48:53 UTC**; zero future and zero last-seven-day pre-match rows.
- The feature-input metadata query selected only `match_date, home_team, away_team` for Serie A 2026/27: 103 unique raw identity tuples through 2026-11-02. No scores/results were selected.
- `public.product_prediction_snapshots`: 40 rows total, zero rows carrying the original V2 version or candidate SHA.

The prospective evaluation gate remains **0/30**. No target outcomes were read; Brier Score and LogLoss remain uncomputed. No source/paid provider call, Supabase write/DDL, model refit, weight/contract change, production-`.pkl` change, promotion, betting, merge, schedule change, or other-agent change was performed in this audit.

