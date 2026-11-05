# Original MARKET_ANCHOR_1X2_V2 — runtime and pre-match source audit

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

No prospective target outcomes were read or scored; the Supabase feature-gate query selected identity metadata only. No paid provider request, workflow dispatch, Supabase write/DDL, production .pkl change, weight/contract change, promotion, merge or bet occurred. Main remains unchanged. See the detailed addendum below for artifact and SQL evidence.

## 2026-11-02 10:55 UTC

This addendum records a read-only audit of the original V2 pipeline. It does not change the frozen model, the 19-feature contract, weights, lambdas, evaluation gate, schedules, production artifacts, or database.

## 1. Main and workflow state

- Fresh `main`: `40887ebb215730190d7a6c7a1693373ec4afcdfc` (commit time 2026-10-18 08:20:05 UTC).
- The four original V2 schedules on main are:
  - Current-Form Source Capture: `50 5 * * *` (05:50 UTC).
  - Free Real-Quote Diagnostic: `13 6 * * *` (06:13 UTC).
  - Original Forward-Only Preview: `8 8 * * *` (08:08 UTC).
  - Current-Form Forward-Only Preview: `18 8 * * *` (08:18 UTC).
- At 10:55 UTC on 2026-11-02, none of those four workflows had a 2026-11-02 run in the first four pages (400 most recent) of main-branch GitHub Actions runs. Other main-branch scheduled workflows did run. This establishes a missing V2 run as of the audit time, not its root cause. No manual dispatch was made and no schedule was changed.

Last successful V2 main runs, all on main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`:

| Workflow | Run | Created UTC | Result |
|---|---:|---|---|
| Current-Form Source Capture | [41304706414](https://github.com/MaksimBlud/football-ai/actions/runs/41304706414) | 2026-11-01 12:04:17 | SUCCESS |
| Free Real-Quote Diagnostic | [41310276961](https://github.com/MaksimBlud/football-ai/actions/runs/41310276961) | 2026-11-01 13:14:16 | SUCCESS |
| Original Forward-Only Preview | [41318729126](https://github.com/MaksimBlud/football-ai/actions/runs/41318729126) | 2026-11-01 14:57:22 | SUCCESS |
| Current-Form Forward-Only Preview | [41319862002](https://github.com/MaksimBlud/football-ai/actions/runs/41319862002) | 2026-11-01 15:10:27 | SUCCESS |

The Source Capture job reported 90 canonical completed primary identities, 90 current-season completed prior-day rows, 10 historical CSVs plus one current-season CSV, 0 paid calls and 0 Supabase writes. Its artifact is ID `13082408243`, ZIP SHA-256 `09fd39e2e7371f6db887963b5da85e4bb3bb6008314cc97b2a31eabf41d115fe`, created 2026-11-01 12:05:15 UTC.

The Original Forward job verified the historical source artifact and parent run, but reported `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`, and `v2_diagnostic_previews_captured=0`. It did not read target outcomes.

The Current-Form Forward job verified the same current-form source artifact and the frozen candidate SHA, but reported `quotes_seen=0` and `v2_current_form_shadow_captured=0`. It recorded 90 current-season history rows, 3,890 historical match rows in the combined source archive, source age 11,153 seconds at verification, 0 paid calls, 0 Supabase writes, and no target-outcome reads.

The Free Diagnostic completed successfully in public-source/no-paid mode and reported no frozen-cohort eligibility, no paid requests, and no Supabase writes.

Artifacts:
- Source Capture: ID `13082408243`, digest `sha256:09fd39e2e7371f6db887963b5da85e4bb3bb6008314cc97b2a31eabf41d115fe`.
- Free Diagnostic: ID `13084892998`, digest `sha256:bcd6fcfb6e2c05c88914812a54067539319fd8894a9d9e2387eea1fba93b38c5`.
- Original Forward: ID `13088352792`, digest `sha256:fb2331e0fbb7a19c3979277814762935a7be0098caf34c149c13c154279c0c11`.
- Current-Form Forward: ID `13089345402`, digest `sha256:0511879f1a3e425ee97326158bb366912e771d2084653d010f7926ac15251a02`.

No current-season CSV or artifact containing 2026/27 outcomes was downloaded or opened during this audit.

## 2. Read-only Supabase pre-match audit

All SQL was read-only. No score, goals, result, or settlement columns were selected.

### Existing 1X2 snapshots

Across the nine stored league values:

- 3,966 total snapshot rows;
- 3,915 rows satisfy the strict pre-match condition `snapshot_time_utc < commence_time_utc`;
- 51 rows are not strictly pre-match;
- zero strictly pre-match snapshots were created on or after the V2 current-form freeze time, 2026-10-18 08:15:32 UTC;
- no future commence time was present in the saved odds rows.

Serie A specifically:

- 625 rows / 63 distinct event IDs;
- 620 strictly pre-match rows;
- latest strictly pre-match snapshot: 2026-10-13 14:48:53 UTC;
- zero strictly pre-match rows after the freeze time;
- no future event with a saved quote.

### Current-season metadata

The metadata-only `public.league_finished_results` query selected only `match_date, home_team, away_team` and timestamps:

- league/season: `SERIE_A / 2026-2027`;
- 93 raw rows and 93 raw fixture identities;
- first date 2026-08-22; last date 2026-10-29;
- all 93 rows have `source_updated_at_utc IS NULL`;
- latest persistence timestamp: 2026-10-30 05:33:49.584335 UTC.

The V2 identity adapter canonicalizes three alias-colliding identities, yielding the 90-event feature-input count reported by the source capture. The current archived CSV also contains 90 completed prior-day rows through 2026-10-29. This internal 90-row parity does not prove external calendar completeness; the previously recorded independent 93-fixture calendar discrepancy remains unresolved.

Exact frozen candidate SHA query against `public.product_prediction_snapshots` returned zero rows:
`a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.

## 3. Binding source-use limitation

The current Football-Data.co.uk fair-use page was rechecked on 2026-11-02:
https://football-data.co.uk/contact.php

It states that the free CSV files are intended for private individuals for personal betting and/or academic research, via manual download or at most light automated download (twice per week maximum), and are not intended for commercial or data-training projects using heavy repeated automated downloads. It also says requests for AI/model-training permission should be assumed not to grant permission.

Therefore:
- do not initiate further automatic or manual CSV downloads for this project unless a clearly applicable permission basis is established;
- the 85-hour workflow-session budget in PR #705 is a technical rate guard, not a data licence or permission for commercial/model-training use;
- do not merge a workflow change that will trigger a new public-source download until its push-trigger consequences and the source-use basis have been reviewed;
- do not replace the source with scraped or unlicensed third-party data.

No Football-Data CSV request was made during this audit.

## 4. Frozen scientific state

The main protocol blob is `65729e9639720e67624c1481190aa22ae606f151`. It still fixes:

- original candidate SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- 19 original features and frozen weights;
- `active_lambda=0` (market fallback);
- `shadow_lambda=1` (research only);
- `stability_gate_passed=false`;
- 30 eligible prospective completed primary forecasts before any target-outcome read;
- NO_BET and no automatic promotion.

The 30-forecast outcome gate remains closed. There are zero V2 candidate prediction snapshots in Supabase and no new eligible forecasts to score. No Brier/LogLoss superiority claim is supported.

## 5. Open V2 PR snapshot and HUMAN-MERGE

Exact current heads and PR-triggered workflow results checked during this audit:

- #705 `102c575b2e88612de1dacd636696ddd01088db75`: 8/8 SUCCESS; shared 85-hour download-session budget.
- #699 `5a1d1bda1c62d36fd092d9e9018a7d2d923e4513`: 7/7 SUCCESS; source, clock, identity and outcome guards; Frozen V2 Shadow job 286 passed.
- #701 `04233460becc99dcbac0beb83a4e105bb8d64e3c`: 6/6 SUCCESS; prospective evaluator remains outcome-gated.
- #702 `8cf6ee1cb66838e8263dd2c7c5ebf42e86964d7e`: 7/7 SUCCESS; fixture feature preview remains manual-only and requires fresh source evidence.
- #703 `f12abfd3a8fc37fb3aff6d394ec3966bc1311b51`: 7/7 SUCCESS; bounded streaming of GitHub artifact ZIPs.
- #700 `8ffbf2119754e8c7d7a8e4f14f75fd94d103c3f0`: 7/7 SUCCESS; historical-source redirect/final-URL guard.
- #704 `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: latest exact-head validation set 7/7 SUCCESS; Python dependency locks.
- #706 `28104a5b943b697d581d578e133585701a395c43`: 6/6 SUCCESS; fail-closed production-pickle diff guard.
- #697 documentation branch before this addendum: `ae5e8622a9fd8cef69ef4c4085d8a109bf70661b`, 7/7 SUCCESS.

The safe engineering dependency order remains #705 before #699 because #699 changes source workflow push paths. However, because #705's merge can itself trigger those push paths, do not treat the order as permission to download: pause source-triggering integration until the source-use limitation above is resolved. Then rebase overlapping workflow PRs and rerun exact-head CI. #703 must be rechecked after #699 because both change forward-reader files; #700's historical redirect guard must be compared against the resulting #699 source reader before deciding whether it is still needed. #701/#702/#704/#706 remain subject to their documented workflow dependencies.

HUMAN-MERGE only. No PR was merged, no branch was pushed to main, no schedule was changed, and no agent settings were changed in this audit.


## 6. 2026-11-02 13:03 UTC follow-up — verified archive timing, current gate, and PR integration risks

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main mutation occurred.

### Actual historical archive timing and byte proof

Independently downloaded only the existing GitHub Actions artifact `13084892998` from Free Real-Quote Diagnostic run `41310276961` (no Football-Data request). Its ZIP SHA-256 is:

`bcd6fcfb6e2c05c88914812a54067539319fd8894a9d9e2387eea1fba93b38c5`

Observed chain of custody:

- Parent main run started: 2026-11-01 13:14:16 UTC.
- Ten historical CSV source observations: 13:14:48.033 through 13:14:58.951 UTC.
- Diagnostic report timestamp: 13:14:58.998 UTC.
- GitHub artifact creation: 13:15:00 UTC.
- Parent run completion: 13:15:03 UTC.

Independent ZIP inspection confirmed exactly ten historical CSVs plus one diagnostic JSON, 3,800 rows total, no 2026/27 CSV, all dates before 2026-07-01, and all ten per-file SHA-256 values and row counts match the embedded report. Every source observation occurred after the parent run started and before the report; report preceded artifact creation; artifact preceded run completion.

PR #707 was strengthened with an explicit fail-closed check that every source observation timestamp must be at or after the successful parent run's `created_at`. A regression test covers a timestamp one second before parent-run creation. Updated PR head is `d21e2854eb752ef234971d62bddc18bd5daabe2b`; exact-head CI is **7/7 SUCCESS** (including the recovery workflow). This is still PR-only: the main-only recovery dispatch and rebuilt-candidate artifact have not run on main.

### Fresh pre-match-only Supabase status

The current read-only odds aggregate returned 3,966 rows across stored leagues, of which 3,915 satisfy `snapshot_time_utc < commence_time_utc`; zero are within the last 24 hours and zero have future kickoff times. Serie A has 625 rows, 620 strictly pre-match, and its latest strict pre-match quote remains 2026-10-13 14:48:53 UTC.

A metadata-only count query selected distinct `match_date, home_team, away_team` for Serie A 2026/27 and returned 93 raw fixture identities. The V2-local three-name alias canonicalization yields the previously observed 90 identities. The 30-event feature-input gate is therefore open, but this does not open the separate 30-prospective-forecast target-outcome evaluation gate. Querying `product_prediction_snapshots` by the frozen candidate SHA returned zero rows. No target score/result columns were selected.

### V2 scheduled runtime

A fresh main-branch scheduled-run query covering 2026-11-01 onward returned no 2026-11-02 runs for the four original V2 workflows. The last successful Original Forward and Current-Form Forward runs remain `41318729126` and `41319862002` on 2026-11-01. Their zero-quote/zero-forecast results remain the last live forward evidence. Root cause of missing 2026-11-02 V2 runs is not established; no manual dispatch or schedule change was made.

### Open-PR overlap audit — do not merge these branches as independent patches

Exact-head CI currently passes for #699 (7/7), #700 (7/7), #705 (8/8), #707 (7/7), #709 (7/7), and #710 (7/7). However, these results are not an integration test:

- #699's source reader already uses `allow_redirects=False`, exact final-URL checks, bounded streaming, and a total collection byte cap. That subsumes the central historical redirect guard in #700; #700 should not be merged independently without comparing its full diff against the resulting #699 reader.
- #699, #705, and #709 all change `.github/workflows/serie-a-v2-current-form-source-capture.yml`. #699 adds the verified-source `workflow_run` refresh path and gate-identity parity; #705 adds the shared 85-hour budget; #709 separates push-only offline validation from main-only capture. Their current independent CI runs do not prove that all three behaviours coexist. A single resulting workflow must preserve all three, retain the existing cron unchanged, and never allow a push to reserve/download source data.
- #707 and #710 both change `.github/workflows/recover-market-anchor-v2-candidate.yml`. #710's recursive, fail-closed production `.pkl` inventory is stronger than the current #707 workflow's older suppressed-error snapshot. Recheck/rebase or integrate these changes before treating recovery as fully protected.

HUMAN-MERGE remains mandatory. No PR was merged, no main ref moved, no source download was initiated, no Supabase write/DDL occurred, and no schedules or other agents were changed.

## 7. 2026-11-02 13:54 UTC — first live current-form source archive and forward verification

Fresh main remained 40887ebb215730190d7a6c7a1693373ec4afcdfc. No PR was merged and no main ref was changed.

### Actual scheduled source capture

The main-branch scheduled workflow [run 41456825300](https://github.com/MaksimBlud/football-ai/actions/runs/41456825300) completed SUCCESS on the exact main SHA. This was a scheduled run; no manual dispatch was made in this audit.

- Workflow: .github/workflows/serie-a-v2-current-form-source-capture.yml.
- Parent run started: 2026-11-02 13:53:01 UTC.
- Metadata-only feature-input gate checked at 13:53:37.551097 UTC and returned 90 canonical completed Serie A 2026/27 fixture identities; it selected only match_date,home_team,away_team, not score/result fields.
- Ten frozen historical CSV observations occurred from 13:53:40.530934 through 13:53:54.443615 UTC.
- Current-season CSV observation: 13:53:55.657343 UTC.
- Source archive created: 13:53:55.717567 UTC.
- GitHub artifact ID: 13147815874, created 13:53:57 UTC, size 437,965 bytes, GitHub digest and independently downloaded ZIP SHA-256 both 67cd15e2e6319196eb13e83b4b65059302c0256b718e876756567efec81614f3.
- Parent run completed: 13:54:01 UTC.

Independent ZIP inspection found exactly 12 members: ten frozen historical CSVs, one serie_a_2627.csv, and the source manifest. All 11 CSV SHA-256 values match the manifest. The ten old-season files each contain 380 rows (3,800 total). The current-season CSV contains 98 completed rows dated 2026-08-22 through 2026-11-01; all 98 have full-time goals/result fields, with no same-day or future rows. Its SHA-256 is aa5b3500dea71e654e543c1b083637f17b0268134baf3e93904d31f7cda9c297.

This is the first live proof that main can pass the feature-input gate, capture the current-season CSV as lagged history, and archive all source bytes/hashes. It does not prove a source-before-quote pair: no quote was available in the subsequent forward run.

### Actual forward-only verification

The workflow-run-triggered main run [41456979071](https://github.com/MaksimBlud/football-ai/actions/runs/41456979071) completed SUCCESS on the same main SHA.

- It authenticated source artifact 13147815874 and its successful parent run.
- Parent completion preceded forward verification; latest source observation was 49 seconds old at verification.
- Frozen candidate SHA remained a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6.
- Reported quotes_seen=0, v2_current_form_shadow_captured=0, source_artifacts_used=[], active_lambda=0, shadow_residual_lambda=1, no_bet=true.
- latest_source_archive_verification.status=VERIFIED; target-outcome evaluation gate remained closed; target outcomes were not read/scored; paid provider calls and Supabase writes were zero.
- Forward artifact ID: 13147505973, digest d68eb6f5c5146e541e1cf1f5f9bfcdf51acda9ef3f272a80e62b6689e6340338.

The source archive was verified independently of quote availability. Since quotes_seen was zero, source-before-quote admission and an actual shadow forecast remain untested.

### Pre-match quote state

A fresh read-only Supabase aggregate over public.odds_snapshots, filtered to league=SERIE_A, returned:

- 625 total rows;
- 620 strict pre-match rows where snapshot_time_utc < commence_time_utc;
- 63 distinct event IDs among strict pre-match rows;
- zero future-kickoff pre-match rows;
- latest strict pre-match snapshot: 2026-10-13 14:48:53.042620 UTC.

Thus the new source archive is real and fresh, but there is still no saved future Serie A quote to pair with it. The forward pipeline correctly generated zero forecasts.

### Remaining source-identity and fair-use blockers

Main's current source-capture manifest attests the gate count (90) but does not include the gate identity-set SHA/count and an explicit source-coverage comparison. The new CSV has 98 completed rows, which is not itself proof that all 90 metadata gate identities are present. Do not treat the 90/98 counts as identity parity. PR #699's current branch already contains the metadata-only gate identity set, SHA attestations, source-coverage comparison, and forward freshness enforcement. A GitHub compare of the exact branches confirms PR #694 head 2fd95bb07befb00b6efb4a14815ad925d50cac71 is the merge base/ancestor of PR #699 head 5a1d1bda1c62d36fd092d9e9018a7d2d923e4513; #699 is 82 commits ahead. Therefore #694 is superseded for these changes and must not be merged separately. The #699 external 90-vs-93 calendar-completeness caveat remains separate; integrate #699 with #705/#709, preserve the budget and offline-push guards, then rerun exact-head CI before relying on the combined source pipeline.

The source capture occurred via its existing daily schedule. PR #705's 85-hour technical download budget and PR #709's offline-only push validation are still unmerged, so neither guard is active on main. The provider's fair-use/model-training permission issue recorded above remains unresolved. Do not manually dispatch another CSV capture or treat a rate-limit PR as a data licence. No additional public-source download was initiated by this audit.

### Frozen scientific status

- Original candidate SHA remains a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6.
- Original 19 features/weights unchanged; active_lambda=0, shadow_lambda=1.
- Feature-input gate: 90 canonical completed primary events; passed.
- Prospective evaluation gate: CLOSED (30 eligible completed forecasts required; no new forecast captured).
- No target-outcome read, Brier/LogLoss comparison, model refit, threshold tuning, production .pkl mutation, Supabase write/DDL, paid provider call, promotion, or bet.

HUMAN-MERGE only. No main update, no schedule change, and no other-agent setting change.

## 2026-11-02 15:18 UTC — exact live identity-set parity independently recomputed

This section corrects the earlier conservative statement that the 98-row current CSV count alone did not prove coverage. I independently recomputed the exact identity set using only date/home/away columns from the downloaded current-season CSV and the same V2 alias rules used by the source-identity guard:

- Runtime aliases: `Inter → Inter Milan`, `Milan → AC Milan`, `Roma → AS Roma`, `Verona → Hellas Verona`.
- V2-only alias: `Atalanta BC → Atalanta`.
- CSV identity cutoff: strictly before 2026-10-30, matching the latest date present in the read-only Supabase gate metadata.
- Supabase query selected exactly `match_date,home_team,away_team` from `public.league_finished_results` for `SERIE_A` / `2026-2027`; no score/result/settlement columns were selected.

The exact canonical sets are equal, not merely equal in count:

| Evidence | Canonical identities | SHA-256 of sorted tab/newline identity serialization |
|---|---:|---|
| Supabase identity-only gate metadata through 2026-10-29 | 90 | `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811` |
| Artifact 13147815874 current CSV through 2026-10-29 | 90 | `95e3d71ab97076b5edee503301843f55d22eb14a832f7e1aab7f2012e6013811` |

The whole ZIP SHA-256 independently recomputed from the downloaded artifact remains `67cd15e2e6319196eb13e83b4b65059302c0256b718e876756567efec81614f3`; the current-season CSV SHA-256 remains `aa5b3500dea71e654e543c1b083637f17b0268134baf3e93904d31f7cda9c297`. The CSV has 98 completed rows in total through 2026-11-01; eight additional identities dated 2026-10-30 through 2026-11-01 are beyond the Supabase metadata cutoff and were not included in the equality comparison.

This is an independent offline audit of the exact identity set, not yet the automated source-manifest attestation that PR #699 adds. It does not establish external calendar completeness beyond the approved source, does not establish a source-before-quote pair, and does not create any forecast. Supabase still has zero saved strictly pre-kickoff Serie A quotes after the source archive time; the 30-prospective-forecast outcome gate remains closed. The earlier warning about relying on counts alone is superseded only for the exact Supabase-to-CSV identity-set parity described above.


## 2026-11-02 16:04 UTC — latest scheduled diagnostic, byte verification, and quote-gate status

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This update records existing scheduled artifacts and read-only database aggregates only; no workflow dispatch, PR merge, schedule edit, Supabase write/DDL, or target-outcome read occurred.

### Latest main Free Real-Quote Diagnostic

Scheduled main run [41473879081](https://github.com/MaksimBlud/football-ai/actions/runs/41473879081) completed SUCCESS on the exact main SHA.

- Parent run: 2026-11-02 15:40:19–15:41:25 UTC.
- Offline regression suite: 53 passed.
- Public source mode: Football-Data historical Serie A only; 10 public HTTP requests; 0 paid-provider requests.
- Diagnostic report: 3,800 historical rows; 0 quoted fixtures; 0 diagnostic previews/scored rows; `eligible_for_frozen_prospective_cohort=false`; `history_stale_without_2026_27_form=true`; `2026_27_public_results_downloaded=false`; `supabase_writes=0`.
- Artifact ID: `13155539394`; size 425,067 bytes; GitHub digest `sha256:a2c5e7a6e35faeea4829342c732625292bea2ef897c7ec24f18b41eb40a335b5`.
- Independently downloaded ZIP SHA-256 exactly matches the GitHub digest. ZIP has exactly 11 members: one diagnostic JSON and the ten frozen historical CSVs. All ten CSV hashes in the report match their archived bytes; each contains 380 rows. No 2026/27 CSV is present.

### Current-form archive and forward result

The same-day scheduled Source Capture run [41456825300](https://github.com/MaksimBlud/football-ai/actions/runs/41456825300) completed SUCCESS at 13:54 UTC. Its artifact `13147815874` has size 437,965 bytes and independently verified ZIP SHA-256 `67cd15e2e6319196eb13e83b4b65059302c0256b718e876756567efec81614f3`. It contains ten historical CSVs, the 2026/27 CSV, and the manifest. The ten historical files contain 3,800 rows; the current-season file contains 98 completed prior-day rows through 2026-11-01. All 11 CSV hashes match the manifest. The metadata-only feature-input gate reported 90 canonical completed primary identities and passed.

The immediately following Current-Form Forward run [41456979071](https://github.com/MaksimBlud/football-ai/actions/runs/41456979071) completed SUCCESS. It verified artifact `13147815874` and its successful main parent, but `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `source_artifacts_used=[]`; no source-before-quote pair or real forecast was admitted. `active_lambda=0`, `shadow_residual_lambda=1`, `no_bet=true`; no target outcomes were read/scored; paid calls and writes were zero.

These are two separate scheduled public-source sessions on 2026-11-02 (13:53 and 15:40 UTC), separated by about 1 hour 47 minutes. The shared 85-hour budget in PR #705 is not on main, so it did not guard these runs. The source-use policy issue recorded above remains binding: no further manual or automated CSV request should be initiated until the permitted use basis and the shared download guard are resolved. The existing schedules were not changed in this audit.

### Fresh read-only pre-match database aggregates

Database time at query: 2026-11-02 16:04:10 UTC. SQL selected only snapshot/event/commence timestamps, league, and metadata-only fixture identities; no score, goal, result, settlement, or target-outcome columns were selected.

For `public.odds_snapshots`:
- 3,966 total rows across nine leagues; 3,915 satisfy strict `snapshot_time_utc < commence_time_utc`.
- Zero strict pre-match rows in the last seven days; zero strict pre-match rows on/after the 2026-10-18 08:15:32 UTC V2 freeze; zero future-kickoff events with saved quotes.
- Serie A: 625 total, 620 strict pre-match, latest strict quote 2026-10-13 14:48:53.042620 UTC.

For `public.league_structural_v2_observations`, Serie A has 630 rows, all strict pre-match, latest observation 2026-10-13 14:48:53.042620 UTC; no future-kickoff quote. This table does not supply a newer quote cohort.

The exact frozen candidate SHA query against `public.product_prediction_snapshots` returned zero rows. Metadata-only Serie A 2026/27 identity query returned 93 raw identities (90 after the frozen V2 alias canonicalization), last metadata date 2026-10-29, and 93 null `source_updated_at_utc` values. `public.matches` has zero future Serie A rows. No new eligible prospective forecast exists.

### Original Forward schedule remains unproven for 2026-11-02

The main-branch recent-run listing contains no 2026-11-02 Original Forward-Only Preview run. The last confirmed Original Forward remains run `41318729126` on 2026-11-01, with `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`, and `v2_diagnostic_previews_captured=0`. The workflow file on main still declares the existing 08:08 UTC schedule and the restricted manual-odds workflow_run trigger. The missing Nov 2 run's root cause is not established; no manual dispatch or schedule change was made.

### Recovery PR integration finding

PR #710's exact-head CI run `41445450598` passed, but its pull_request job executed the old main recovery path: `market_anchor_v2_saved_cohort_replay.py` called `download_csv` once for each of its ten frozen seasons because the #710 branch does not contain PR #707's local `--training-csv-dir`/verified-artifact path. Thus #710 is not safe to merge as a standalone patch and its CI is not evidence of an offline recovery path.

PR #707 contains the verified existing-artifact loader and makes artifact verification/rebuild conditional on main-only `workflow_dispatch`, but its original `.pkl` inventory guard suppressed errors. I integrated #710's recursive fail-closed `.pkl` inventory and regression test directly into the #707 branch, preserving #707's offline pull_request path and manual-main-only artifact recovery. Updated #707 branch HEAD is `33371988097f02b9e34d37b57c5f0b8731df303a`; exact-head CI has started (7 checks pending at 16:10 UTC). No public CSV request is made by the new PR path. Do not merge #710 standalone; after #707's combined head passes, #710 is redundant/superseded.

### Frozen scientific state

- Candidate SHA: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original 19 features and weights unchanged; `active_lambda=0`, `shadow_lambda=1`.
- Feature-input gate: 90 canonical completed primary identities; passed.
- Prospective target-outcome gate: CLOSED; 30 eligible unique primary completed forecasts required; zero candidate prediction snapshots and zero new eligible forecasts.
- No Brier/LogLoss comparison or superiority claim is supported.

HUMAN-MERGE only. Main remains unchanged. No production `.pkl` change, Supabase write/DDL, paid API call, target-outcome read, model refit, threshold tuning, promotion, or bet occurred.

## Latest source/recovery audit — 2026-11-02 17:56 UTC

### Fresh main and real runtime

- Main is still 40887ebb215730190d7a6c7a1693373ec4afcdfc. PROJECT_CONTINUITY.md on main therefore still predates the open November 2 integration PRs; this addendum remains a review-branch update only.
- Main Current-Form Source Capture run [41456825300](https://github.com/MaksimBlud/football-ai/actions/runs/41456825300) succeeded on that SHA. Artifact 13147815874 is 437,965 bytes, ZIP SHA-256 67cd15e2e6319196eb13e83b4b65059302c0256b718e876756567efec81614f3. Its ten old-season CSVs have 3,800 rows total; current serie_a_2627.csv has 98 completed prior-day rows through 2026-11-01, SHA-256 aa5b3500dea71e654e543c1b083637f17b0268134baf3e93904d31f7cda9c297. The metadata-only feature-input gate is 90 canonical primary identities and passed.
- Current-Form Forward run [41456979071](https://github.com/MaksimBlud/football-ai/actions/runs/41456979071) succeeded but verified zero saved quotes and captured zero shadow forecasts. It reports active_lambda=0, shadow_residual_lambda=1, no_bet=true, and no outcome reads/scoring.
- Main Free Real-Quote Diagnostic run [41473879081](https://github.com/MaksimBlud/football-ai/actions/runs/41473879081) succeeded. Artifact 13155539394 is 425,067 bytes with ZIP SHA-256 a2c5e7a6e35faeea4829342c732625292bea2ef897c7ec24f18b41eb40a335b; independently downloaded bytes match. The ZIP contains exactly one diagnostic report plus ten allowlisted historical CSVs, each 380 rows; all ten file hashes match the report, all dates precede 2026-07-01, and no 2026/27 CSV or outcome/score key is present. The report has 19 features, 3,800 history rows, zero scored diagnostics, zero paid-provider requests, zero Supabase writes, and preserves the 2026/27 outcome embargo.

### Recovery source-code admissibility — do not conflate ZIP integrity with provenance

- The parent run for artifact 13155539394 used main SHA 40887ebb215730190d7a6c7a1693373ec4afcdfc; at that commit, serie_a_v2_live_diagnostic_report.py has Git blob SHA fae3698769f857fbcb6c8d3ea7826eb81135fec4.
- PR #707 intentionally pins SOURCE_SCRIPT_BLOB_SHA to 932e58a4f93b0d471ac4b4e0c81fa01f923e46d5, which is the integrated strict no-redirect source-reader blob currently in #699, not current main. Thus artifact 13155539394 is structurally/hash compatible but not admissible to #707 recovery; the loader must reject it before artifact listing/download.
- Do not dispatch recovery yet. Required sequence: manual merge #705; rebase/review and manually merge #699 preserving the exact no-redirect source reader; obtain a fresh successful main Free Diagnostic run; verify its source-reader blob is exactly 932e58...; only then run main-only recovery against that new historical-only artifact.

### Current pre-match Supabase state

The read-only query selected only quote/event/commence timestamps and league, with no score/result/settlement fields:

- Serie A: 625 total quote rows, 620 strict snapshot_time_utc < commence_time_utc, 63 events, latest strict pre-match snapshot 2026-10-13 14:48:53.042620 UTC, zero future-kickoff pre-match rows.
- Every other league in public.odds_snapshots also has zero future-kickoff pre-match rows.
- The metadata-only query against public.matches found zero future fixture identities.
- No current saved quote can enter either original or current-form V2 forward capture; no forecast should be fabricated or backfilled.

### Exact PR state and integration order

- PR #705 current HEAD 2b9cafedb6deb414e2a5340ebd8f8da566793ecf, base main 40887ebb215730190d7a6c7a1693373ec4afcdfc: exact-head CI 8/8 SUCCESS. It consolidates the shared 85-hour source-download marker/concurrency guard with #709's offline-only push validation. Pushes run local tests only; scheduled/manual-main capture alone can reserve a public-source attempt. Existing cron expressions are unchanged. #709 must not be merged separately.
- PR #699 current HEAD 5a1d1bda1c62d36fd092d9e9018a7d2d923e4513: prior exact-head CI 7/7 SUCCESS, but it is still based directly on old main and overlaps #705 workflow paths. It must be rebased/integrated after the user's manual #705 merge, preserving the budget and push-isolation jobs, then exact-head CI rerun.
- PR #707 current HEAD cdc93ca0aab9dc75434238bec75ea8759d77ffbd: exact-head CI 7/7 SUCCESS; recovery PR job ran 23 tests. Artifact retrieval/rebuild/publication were skipped on the PR event, and recursive production .pkl inventory matched before/after. Its latest code verifies the parent source-code blob before artifact listing/download. No main-only recovery has been run.
- PR #702 remains 7/7 CI-successful but cannot be dispatched until #699 is merged and a fresh post-#699 source archive contains the required authenticated identity-set attestation. Its manual-only endpoint is fixture metadata only, expects zero credits, and emits no probabilities.
- #700's redirect guard is represented in the more complete #699 source-reader version (blob 932e58...); #677/#681 overlap #699's original/current-form forward code and expanded tests; #710's recursive pickle guard is already integrated into #707. Do not merge these overlapping PRs as standalone patches without a unique-diff review. #703 remains a distinct bounded GitHub artifact-download hardening PR and needs rebase/review after #699.
- #697 is still a documentation-only review PR; this addendum update does not change main.

### Frozen V2 contract remains unchanged

- Candidate SHA: a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6; training rows 3,799; training fingerprint f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098.
- Exact original 19-feature order and weights unchanged; active_lambda=0, shadow_lambda=1; stability gate remains FAILED.
- Metadata-only feature-input gate: 90 primary identities, passed. Separate prospective evaluation gate: 30 eligible completed forward forecasts, still CLOSED; current forecasts = 0. No 2026/27 target outcomes were read or scored; no Brier/LogLoss superiority claim is supported.

HUMAN-MERGE only. Main remains unchanged. No production .pkl changes, Supabase writes/DDL, paid Odds API calls, target-outcome reads, schedule changes, refit, threshold tuning, promotion, or betting action occurred in this audit.


## Superseding source-budget design — 2026-11-02 18:08 UTC

This section supersedes the earlier 85-hour **global** cooldown described in historical notes above. Review of the unchanged schedule order found that a global cooldown would let the 05:50 Current-Form Source Capture reserve the slot every week and starve the 06:13 Free Real-Quote Diagnostic. That would leave the original forward/recovery source artifact stale.

PR #705 was therefore revised to use a 170-hour cooldown **per approved workflow path**, while retaining one shared GitHub concurrency group:
- Current-Form Source Capture: at most one attempt in any 170-hour interval.
- Free Real-Quote Diagnostic: at most one attempt in any 170-hour interval.
- Exactly two approved paths; therefore at most two download sessions in any rolling 7-day interval.
- Both workflows pass their own exact --workflow-path; a marker from one workflow does not block the other.
- The shared concurrency group serializes reservations; the marker is uploaded before any public CSV request.
- Existing cron expressions remain 05:50 and 06:13 UTC; push events remain offline-only.

Current PR #705 HEAD: e368326ad52f728f1c3975989aa7a60de2be50c3. Exact-head CI: 8/8 SUCCESS (Research 41497453471, Product 41497453467, Bundesliga 41497453493, Ligue 1 41497453700, Eredivisie 41497453567, Serie A 41497453486, Frozen V2 Shadow 41497453444, Budget Tests 41497453479). The budget suite passed 20 tests; Frozen V2 Shadow passed 86 tests; Research and Serie A production-artifact guards passed with no .pkl changes.

Bootstrap cooldowns from the last existing main artifacts (assuming no later attempt): Current-Form Source Capture artifact 13147815874 was created 2026-11-02 13:53:57 UTC, so its next eligible time is 2026-11-09 15:53:57 UTC; Free Real-Quote Diagnostic artifact 13155539394 was created 2026-11-02 15:41:21 UTC, so its next eligible time is 2026-11-09 17:41:21 UTC. Their unchanged schedules therefore next align after both cooldowns on 2026-11-10 at 05:50 and 06:13 UTC. The actual main workflows do not have this guard until the user manually merges #705.

No public CSV request was initiated by this automation. Source-use permission remains a separate unresolved question; a rate budget is not a licence. HUMAN-MERGE only; main is unchanged.


## Fresh live audit — 2026-11-03 19:52 UTC

### Main, original forward workflow, and actual execution

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` blob is `2ce2f8f5b2d1a26ec85a6f8dbdd70f5f18a87c3e`. No main ref was changed.
- Re-read `.github/workflows/serie-a-v2-forward-preview.yml` (the actual **Serie A V2 Original Forward-Only Preview** workflow), both current-form workflows, the free diagnostic workflow, and the candidate/evaluator contracts.
- Main run [41640753996](https://github.com/MaksimBlud/football-ai/actions/runs/41640753996), Current-Form Source Capture, succeeded at 13:02:10–13:03:01 UTC. It archived 10 historical season files plus the current-season file; the current-season file had 100 rows and the metadata-only feature-input identity gate had 98 canonical identities. Source artifact ID: `13231843819`; ZIP SHA-256: `4e6fb5531a2206a353fe00fa1ebb0b4d20b3c6ae41ab49a7c672f8dab6d29cd8`. Latest source observation: 13:02:58.382703 UTC; archive creation: 13:02:59 UTC; parent completion: 13:03:01 UTC.
- Main run [41650074683](https://github.com/MaksimBlud/football-ai/actions/runs/41650074683), Free Real-Quote Diagnostic, succeeded at 14:04:13–14:05:09 UTC. It made 10 public historical CSV requests, verified 3,800 historical rows, but reported `quoted_fixtures=0`, `diagnostic_scored=0`, `feature_rows_all_median_imputed=0`, `paid_provider_requests=0`, and `supabase_writes=0`.
- Main run [41670482076](https://github.com/MaksimBlud/football-ai/actions/runs/41670482076), Original Forward-Only Preview, succeeded at 16:04:57–16:05:40 UTC. Its log reports `forecasts_created=0`, `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`; it verified 3,800 historical rows and 10 pre-prospective source files. This is a successful source/provenance check, not a real forecast run.
- Main run [41672409582](https://github.com/MaksimBlud/football-ai/actions/runs/41672409582), Current-Form Forward-Only Preview, succeeded at 16:16:00–16:16:42 UTC. Its log reports `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`. It did verify source artifact `13231843819`, source SHA above, candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 100 current-season rows and 98 feature-input identities. At verification (16:16:34.610679 UTC), source age was 11,616 seconds and the archive was fresh for a new quote.
- The only later V2-named run found in the latest Actions window is PR run [41701270604](https://github.com/MaksimBlud/football-ai/actions/runs/41701270604), not a main production run. It ran on PR #707 HEAD `3a79d333eb246d92aea88b569c8cb5b4474b9fbd`. Its report explicitly says `mode=SYNTHETIC_ONLY_RUNTIME_SMOKE`, `real_events_scored=0`, `target_outcomes_read=false`, `training_performed=false`, and `production_pkl_touched=false`. The recovery job passed 43 tests; the synthetic runtime report confirms the frozen candidate SHA, 19 features, weights shape 20x2, exact active-market equality at lambda 0, finite/summing shadow output at lambda 1, and unchanged FAILED stability gate. This proves synthetic runtime integrity only; it does **not** prove archive recovery or real-match inference.

### Current read-only Supabase state

Queries selected only pre-kickoff quote metadata, prediction metadata, or future fixture identities; no result, score, goals, or settlement columns were selected.

- `public.odds_snapshots`: 3,966 rows / 327 distinct events overall; 3,915 rows pass strict `snapshot_time_utc < commence_time_utc`. Latest strict pre-match snapshot is 2026-10-13 14:48:53.042620 UTC. Future-kickoff rows with a strictly pre-kickoff snapshot: **0 rows / 0 events**.
- `public.product_prediction_snapshots`: 40 strictly pre-kickoff rows / 40 events; latest generation 2026-10-09 15:29:33.136613 UTC. Original V2 candidate SHA/version rows: **0**.
- `public.matches` future fixture identity-only aggregate (`match_date, home_team, away_team`): **0 rows / 0 events**.
- No Supabase write or DDL was performed. No protected target outcome was read.

### Free fixtures page timing — no admissible pair yet

The official Football-Data fixtures page reports its latest fixture-file upload as **03/11/2026 10:17 UK time** and says midweek odds are collected on Tuesdays no later than 13:00 UK time (weekend odds Fridays no later than 17:00 UK time): https://football-data.co.uk/matches/fixtures.csv.

The current-season source archive above was not observed until **13:02:58 UTC on 03/11/2026**, after the provider's stated Tuesday 13:00 collection bound and after the 10:17 page update. Therefore that archive cannot prove source-before-quote for the 03/11 fixture/odds file. The existing evaluator's frozen 24-hour source-age limit also prevents carrying this 03/11 source archive forward to a later weekly quote collection. The fixtures page is a possible free quote source for future work, but it is not integrated, and no row from it is admitted to the V2 cohort. Do not relax the frozen 24-hour source-age contract or infer an exact bookmaker quote timestamp from a page-upload timestamp.

### Exact open PR heads and CI

All remain open against main; no PR was merged in this audit.

- #705 `8b139335e6722b7c4f5286962486bca84bced20d`: **8/8 SUCCESS**. It adds the per-workflow 170-hour shared public-source budget. The guard is not active on main until HUMAN-MERGE; current main source workflows still retain their existing daily schedules.
- #699 `42c967f28fd274d8a8f9924e698dc5492f7f13e3`: **7/7 SUCCESS**; rebase after #705 and preserve the shared budget/offline-push guards.
- #712 `331e7934f92763d8df2c6c35e01b6b26a80bcf5d`: **9/9 SUCCESS** on its old main base; rebase after #705/#699 and preserve the identity-attested producer/consumer round-trip. #711 remains the overlapping draft alternative; do not merge both.
- #707 `3a79d333eb246d92aea88b569c8cb5b4474b9fbd`: **8/8 SUCCESS**; rebase after #712 because of overlapping source-capture/diagnostic files.
- #701 `268885f437379a1610c0c56abb883cf7963f9d9c`: **6/6 SUCCESS**; rebase after #707. Its market-only evaluator remains the only admissible path while no non-legacy incumbent is pinned.
- #704 `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: **16/16 SUCCESS**; pinned research dependencies, separate from the source/identity integration chain.
- #706 `28104a5b943b697d581d578e133585701a395c43`: **6/6 SUCCESS**; fail-closed production-`.pkl` diff guard.
- #697 documentation branch before this append: `35c3abc483d3e2822522b578aedc87ac1a80dcdf`, **7/7 SUCCESS**; this addendum update is documentation-only and remains in the same review branch.

### Frozen scientific status

- Original candidate SHA: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original 19-feature order/weights unchanged; training rows 3,799; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- `active_lambda=0` remains exactly the de-vigged market; `shadow_lambda=1` remains research-only. Stability gate remains FAILED.
- Feature-input identity gate: 98 identities in the current source archive. This is not the prospective outcome gate.
- Prospective eligible completed forecasts: **0/30**. The market-only evaluator may read exact H/D/A labels only after 30 unique eligible completed primary forecasts; before that, the lazy outcome loader remains uncalled. No Brier/LogLoss has been computed and no V2 advantage over market is established.
- Full three-way evaluation remains blocked because no distinct, pinned, non-legacy incumbent is registered. Do not substitute the old XGBoost model or duplicate the market vector as an incumbent.

HUMAN-MERGE remains mandatory. Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No source download was initiated in this audit; no paid provider request, Supabase write/DDL, target-outcome read, production `.pkl` change, weight/contract change, schedule change, automatic promotion, or bet occurred.

## 2026-11-03 20:56 UTC — exact current-source identity parity

### Exact source archive and current gate identity comparison

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Existing main Source Capture run [41640753996](https://github.com/MaksimBlud/football-ai/actions/runs/41640753996) produced artifact `13231843819`. The artifact was downloaded from GitHub Actions only; no Football-Data request was made. Its ZIP SHA-256 independently matches the GitHub artifact digest: `4e6fb5531a2206a353fe00fa1ebb0b4d20b3c6ae41ab49a7c672f8dab6d29cd8`.
- The embedded manifest records the metadata-only feature-input gate at 2026-11-03 13:02:46.498639 UTC with 98 canonical identities. The current-season CSV was observed at 13:02:58.382703 UTC, archived at 13:02:59 UTC, and the parent workflow completed at 13:03:01 UTC. It contains 100 completed prior-day rows.
- Independently inspected only `Date`, `HomeTeam`, and `AwayTeam` in the archived `serie_a_2627.csv`. Applied the exact runtime aliases (`Inter → Inter Milan`, `Milan → AC Milan`, `Roma → AS Roma`, `Verona → Hellas Verona`) plus the V2-local `Atalanta BC → Atalanta` alias. This yields 100 unique source identities with SHA-256 `f85872547e745eae8854ee245902c1e522657fb3a687032be83b000199f2a99e`, using the same sorted tab/newline serialization as PR #699's `_fixture_identity_sha256`.
- A fresh read-only Supabase query selected only `match_date, home_team, away_team` for `SERIE_A / 2026-2027`, dates before the current UTC date. It returned 103 raw rows, 100 canonical unique identities, and three alias duplicates. Applying the same canonicalization and serialization produced the exact same SHA-256: `f85872547e745eae8854ee245902c1e522657fb3a687032be83b000199f2a99e`. Latest identity date: 2026-11-02.
- **Exact identity-set parity is independently confirmed as of 2026-11-03 20:56 UTC.** The earlier apparent hash mismatch was caused by omitting the runtime aliases for Inter, Milan, and Roma; after applying the complete frozen alias map, the source and Supabase hashes match. No score, goals, result, or settlement columns were selected or opened.
- This confirms current source coverage of the presently known 100 fixture identities. It does not create a quote, a forecast, or an evaluation observation. The existing forward run still had `quotes_seen=0` and `v2_current_form_shadow_captured=0`; there are no future-kickoff pre-match quotes in Supabase. No source-before-quote pair or Brier/LogLoss result exists.

### PR integration consequence

- Main's current source archive predates the identity-attestation fields now required by the strict consumer in PR #699. The independent audit above is evidence for this review record only; it is not a retroactive in-workflow attestation and must not be used to bypass the frozen archive contract.
- PR #699 HEAD `42c967f28fd274d8a8f9924e698dc5492f7f13e3` contains the identity-only gate set, canonical SHA, source-coverage check, and forward freshness guard. GitHub compare confirms PR #694 HEAD `2fd95bb07befb00b6efb4a14815ad925d50cac71` is an ancestor of #699 (102 commits behind); do not merge #694 separately.
- PR #699 exact-head CI is 7/7 SUCCESS; its check-runs completed 2026-10-26. Rebase it after the user's manual #705 integration, preserve the shared source budget and push-offline guard, then rerun exact-head CI. The old main archive lacks the new embedded identity list/attestation; a new capture would be required by the strict PR #699 contract.
- PR #705 remains open at `8b139335e6722b7c4f5286962486bca84bced20d`, exact-head CI 8/8 SUCCESS. Main's existing daily source schedules are still unguarded until HUMAN-MERGE. The next scheduled attempts are 2026-11-04 05:50 UTC (Source Capture) and 06:13 UTC (Free Diagnostic). Do not initiate another source request: the provider's twice-weekly fair-use limit and unresolved AI-use scope remain binding; the budget PR is a technical guard, not a licence.

### Frozen V2 and safety state

Original candidate SHA, 19-feature order, weights, protocol, `active_lambda=0`, and `shadow_lambda=1` are unchanged. Feature-input identity gate is open; prospective completed-forecast outcome gate remains CLOSED at 0/30. No target outcomes were read/scored, no model refit or threshold tuning occurred, no paid provider calls, Supabase writes/DDL, production `.pkl` changes, schedule changes, merges, promotion, or bets occurred. HUMAN-MERGE only.



## Research Brain exact-head audit — 2026-11-04 11:54 UTC

This update records a fresh read-only audit. Main, production, schedules, other agents, and Supabase were not changed.

### Fresh main and frozen original V2 identity

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Main `PROJECT_CONTINUITY.md` blob: `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`. The main document still predates the November 4 runtime audit; this addendum is on the existing documentation PR branch.
- Main original forward workflow `.github/workflows/serie-a-v2-forward-preview.yml` blob: `48ce3b0d8e31c4cf293b94500e9c320047311467`. It remains read-only and only awakens after the existing manually dispatched, successful main `Serie A Odds Snapshots` workflow; this does not schedule or call the paid collector.
- Frozen candidate JSON blob is unchanged on main and #699: `ac1303f6b096664983fbf52443bd0a381b23ba21`; frozen candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- V2 protocol blob is unchanged: `65729e9639720e67624c1481190aa22ae606f151`.
- Historical feature-builder blob is unchanged: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- `market_anchor_1x2_v2_shadow.py` is byte-identical on main and #699 (blob `b2770d726ffafe7a3cef706b57d3391063cbfe1b`).
- `serie_a_v2_frozen_shadow_preview.py` has a guard-only change (main blob `799d2e2f8e6f5733e2d2310c7d02546b00714268`, #699 blob `01dcc546b5d05f273d8a8d6a6c710cf2759fe06f`): real UTC-offset validation and recursive normalized outcome-key rejection. The entire function body from `previews = []` through the end of `shadow_preview` is byte-identical (4,843 characters), including the calls to `predict_candidate` / `predict_shadow_residual`, the exact active-market identity assertion, and the research-only shadow output. No candidate, feature, coefficient, weight, lambda, or inference-math change was found.
- Contract remains 19 features, 20×2 original weights, `active_lambda=0` (market identity), `shadow_lambda=1` (research only), stability gate FAILED, NO_BET.

### Exact open V2 PR heads and actual CI evidence

- **#705** HEAD `8b139335e6722b7c4f5286962486bca84bced20d`: 8/8 associated PR workflows SUCCESS. Dedicated public-source-budget workflow #41666171494 ran **22 tests**. Its workflow blob `7fae79252472cc849668e73da04bc436104b6f82` already includes both (a) offline-only `validate-source-capture` on push and (b) `capture-current-form` only for non-push main events, plus the 170-hour per-workflow budget reservation, shared concurrency group, and pre-download marker. Cron expressions remain unchanged. The guard is not active on main until HUMAN-MERGE.
- **#699** current branch HEAD `8f767e0877a87d002209b80c19ce6dbdb2a3050b`: 7/7 associated PR workflows SUCCESS; exact frozen V2 shadow job #41804425498 ran **320 tests**. The branch contains the source-rights helper/manifest and the source/clock/identity/outcome guards. However, its current source-capture workflow blob `df5a6eba91fcec857f5e14c277aed802f45cb6a2` still has a single capture job eligible on push and lacks #705's budget reservation/offline push split. Do not merge #699 as-is. Rebase after #705 and preserve all three: the #705 budget marker, offline-only push validation, and #699 rights/provenance guards. A comment with this exact integration finding was added to #699.
- **#709** HEAD `268f3fdc82036fca0e44dc0aef20d39423cfda2d`: 7/7 associated PR workflows SUCCESS. Its source workflow blob `ad5e7a93edbf3d398a1155abc7dc852528dac38f` has the offline push split but lacks the budget guard. #705 already contains the same offline split plus the budget; #709 must not be merged independently after #705 because it risks reverting budget protection. A comment documenting the supersession was added to #709.
- **#712** current HEAD `4b9b1281a8ab81988ea713eb5974d1e55dbba81d`, commit at 10:59:23 UTC: GitHub currently reports `mergeable=false`. The current HEAD has one dedicated `offline-source-reuse-tests` run, #41817875512, SUCCESS with **53 tests passed**. It has no full PR-validation run set on this exact HEAD. The PR body's 9/9 statement refers to the older `1c0f5a424dd51abc0f1a7dedfb7f8ff1047b3339`; it must not be represented as current exact-head CI. Rebase after #705/#699 and the chosen #704 dependency-lock integration, preserve the #699 rights helper before source artifact consumption/extraction or inference, then rerun all required CI. A comment with the exact-head CI distinction was added to #712.
- **#704** HEAD `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`: 14 associated PR check runs observed, all SUCCESS; it pins Python 3.11/3.12 research dependencies but is not a hash-enforced supply-chain lock.
- **#701** HEAD `0dbb1106e98f4c83f2bce79d9fb7dd634087e367`: 6/6 SUCCESS; the 30-eligible-completed-forecast gate remains mandatory before the lazy target-outcome loader.
- **#702** HEAD `3935fc601eff30d2ca0a7670dae797d0cb365228`: 7/7 SUCCESS; manual-only feature-readiness probe, no probabilities.
- **#706** HEAD `caab7c07ad720866616ce9fa62664b0d398e5fe0`: 6/6 SUCCESS; fail-closed production-`.pkl` diff guard.
- #711 remains the overlapping draft alternative to #712; do not merge both. #707 remains excluded from this recovery path because it rebuilds/refits a candidate rather than merely verifying the frozen original.
- Recommended integration remains HUMAN-MERGE: **#705 → rebase/revalidate #699 while preserving #705 guards → #704/#706 as reviewed → rebase/revalidate #712 → #701/#702**. #709 is superseded by #705 and should not be merged independently.

### Current pre-match Supabase state (read-only)

- `public.odds_snapshots`: 3,966 rows overall; 3,915 satisfy strict `snapshot_time_utc < commence_time_utc`. Across all leagues there are **0 future-kickoff rows with a strictly pre-kickoff snapshot**. Serie A specifically has 625 rows, 620 strictly pre-match rows, 63 distinct pre-match event identities, and latest strict pre-match snapshot `2026-10-13 14:48:53.042620 UTC`.
- `public.product_prediction_snapshots`: 40 rows, all `EPL_AI_MARKET_PAIR_V1` with model SHA `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`; all 40 are pre-kickoff. There are **zero** original V2 candidate SHA/version rows.
- The current-season feature-input query selected exactly `match_date, home_team, away_team` from `public.league_finished_results` for `SERIE_A / 2026-2027`, dates 2026-07-01 through 2026-11-03. It returned **103 raw identities**, 103 exact unique rows, and **100 canonical identities** after the existing V2-local `Atalanta BC → Atalanta` alias; three rows are alias duplicates. Date range: 2026-08-22 through 2026-11-02. No score, goals, result, or settlement fields were selected. This is only the feature-input gate; it does not open the separate evaluation gate.
- The prospective evaluation gate remains **0/30**. No Brier or LogLoss has been calculated; no V2-over-market claim is supported.

### Runtime discovery boundary and source rights

- The last verifiable main Source Capture / Free Diagnostic / Original Forward / Current-Form Forward runs remain the 2026-11-03 runs #41640753996, #41650074683, #41670482076, and #41672409582. Their jobs were SUCCESS, but the forward logs recorded zero quotes and zero V2 previews. The available GitHub connector does not expose repository-wide discovery of scheduled workflow runs for 2026-11-04; today's scheduled run status is therefore **unknown**, not inferred as absent or failed.
- No new public CSV download, paid provider call, Supabase write/DDL, production artifact change, target-outcome read, or manual workflow dispatch occurred in this audit. No current-season archive member was downloaded or opened.
- The Football-Data manifest is `CONDITIONAL_RESEARCH_ONLY`: it operationally interprets frozen-weight, noncommercial personal/academic research inference as within the stated personal/academic scope, but explicitly records `provider_issued_ai_inference_license=false`. AI training, commercial use, and public product publication remain prohibited by the current manifest. This is not a provider-issued AI-inference licence; do not describe it as one or use these data for a public/commercial product.
- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No merge, production `.pkl` change, weight/contract change, schedule/cron change, Supabase write/DDL, protected target-outcome read, promotion, or bet occurred. HUMAN-MERGE only.


## Research Brain exact-head audit — 2026-11-04 16:56 UTC

### Fresh main, original forward workflow, and frozen candidate

- GitHub's latest commit search still returns main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; open PRs #697/#699/#701/#705 all retain that exact base SHA.
- Main `PROJECT_CONTINUITY.md` blob: `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`.
- Main original-forward workflow `.github/workflows/serie-a-v2-forward-preview.yml` blob: `48ce3b0d8e31c4cf293b94500e9c320047311467`. It remains read-only: daily 08:08 UTC, plus a successful main manual `Serie A Odds Snapshots` workflow_run; this does not schedule or dispatch the paid collector.
- Main current-form forward workflow blob: `6ebbcaff290a78e9ccffa4ac9a09bc0982eaff35`; current-form source-capture workflow blob: `9722416862b42d55ff7181003353c39620f23cf2`.
- Candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features and original weights remain frozen; `active_lambda=0), `shadow_lambda=1` research-only. No candidate/protocol/feature-builder changes were made.

### PR #701 — real CI failure isolated to the documented #699 dependency

- At HEAD `8d8d86a4dc242b88d90973091c7edcda9d10eda4`, Research PR Validation #41862587677 failed because the new bridge test imported the original feature chain without installing scikit-learn (`ModuleNotFoundError: sklearn`).
- Added `scikit-learn==1.9.1` to the existing research-validation test dependency line, using the version recorded in the reviewed #704 Python 3.12 lock proposal. New exact HEAD: `499c95cea970d42ee6512b77986af6143295e653`; workflow blob: `43fc6faa338ab76bacbf328e298ea4500da06059`. Main's corresponding workflow blob remains `e80f59f6b6b9bc2525d0df2064e02e3984b0cc2a`; no main write occurred.
- On new HEAD, five of six required PR validations completed SUCCESS. Research PR Validation #41872721087 then failed later in the import chain: `market_anchor_1x2_v2_prospective_evaluation.py` imports `_current_gate_freshness`, which is absent from main's `serie_a_v2_current_form_forward_capture.py` blob `326ac1921ce901a31aa6d73e6cbddb0782071964`, but present in #699's blob `3c397abc02d4f8b7532a526d0af2f6d751b3cf4a`. The dependency package issue is therefore fixed; the remaining failure is the known stacked source-guard dependency, not a reason to duplicate the helper in #701.
- Added an exact-head explanation to #701. Keep it unmerged; after manual #705 → #699 integration, rebase #701 onto the resulting main and rerun all six checks on the exact new SHA. The frozen 30-primary-completed-forecast gate and lazy outcome loader remain unchanged.

### PR #712 — source-reuse integration must include #699 rights guard

- Re-read exact #712 HEAD `4b9b1281a8ab81988ea713eb5974d1e55dbba81d`. Its current-form source capture reads the identity-only Supabase feature gate and then calls `fetch_public_history_with_provenance()`, which discovers/downloads the GitHub source artifact and extracts historical CSVs through `load_verified_historical_source_archive()`.
- This branch does not yet import/call #699's `require_personal_research_inference_scope()` before those source/metadata/artifact operations. The rights helper/manifest are also absent from #712's changed-file list.
- Added an exact-head PR comment. This is an integration blocker, not evidence of a live unauthorized request. Rebase #712 after #699 and call the approved rights guard before Supabase/source-artifact access, artifact download/extraction, or inference. Do not copy a duplicate rights helper. The #711 draft remains an overlapping alternative; do not merge both.

### PR integration and source-use safety

- #705 HEAD `97a94f5ba3aa921175071e490a9c698aaf0a414b`: 8/8 associated checks SUCCESS; dedicated budget tests and frozen V2 shadow tests passed. Its workflow diffs include a shared 170-hour per-workflow marker, shared concurrency, offline-only source-capture push validation, and main-only source capture. It also excludes push from the current-form forward job. Cron expressions are unchanged. It is not active on main until HUMAN-MERGE.
- #699 HEAD `09c95fde22091311cbe56da236e76360aad33f72`: 7/7 SUCCESS; must be rebased after #705 while preserving the shared marker/concurrency/offline-push behavior and adding its rights, identity, clock and outcome guards.
- #709 remains superseded by #705: #705 already contains the same offline push split plus the budget marker. Do not merge #709 independently.
- Main's source-capture cron remains unguarded until #705 is manually merged; next slot is 2026-11-05 05:50 UTC. No source workflow was dispatched and no Football-Data request was made in this audit. The 170-hour guard is a technical control, not a provider licence; the rights manifest remains conditional personal/academic frozen-weight inference only, not AI training, commercial use, or public product publication.

### Fresh read-only Supabase pre-match/identity audit

- Project: `besxwboamipygwvrsblz`; all queries were read-only.
- `public.odds_snapshots`, Serie A only: 625 rows; 620 strictly pre-kickoff (`snapshot_time_utc < commence_time_utc)); 63 distinct pre-kickoff event IDs; latest strict pre-kickoff snapshot `2026-10-13 14:48:53.042620 UTC`; zero strict pre-kickoff rows in the last 24 hours or seven days.
- `public.league_finished_results` query selected only `match_date, home_team, away_team` metadata via aggregate identity count for Serie A 2026/27; 103 raw unique tuples through 2026-11-02. No goals, scores, results or settlement fields were selected. This is feature-input metadata only, not the prospective evaluation cohort.
- `public.product_prediction_snapshots`: 40 EPL rows, all strictly pre-kickoff; zero rows and zero events with the frozen original V2 candidate SHA.
- No fresh pre-kickoff quote or original-V2 product prediction was found. No target outcomes were selected/read; Brier and LogLoss remain uncomputed. The prospective gate remains blocked pending 30 eligible prospective completed forecasts; no V2-over-market claim is supported.

No source download, paid provider call, Supabase write/DDL, production `.pkl` change, model refit, threshold/weight/contract change, promotion, bet, merge, main update, schedule change, or other-agent change occurred. HUMAN-MERGE only.


## 2026-11-05 02:07 UTC — fresh-main exact PR-head correction and forward-gate state

Fresh default-branch ref is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`. This entry corrects older SHA references in this addendum using current GitHub PR metadata and exact-head workflow-run associations. Main was not changed.

- **PR #705** is open at exact current HEAD `8cf5ded4dfc18820e10f59f8ccd2a462479ccfe5`, based on main `40887ebb...`. All **8/8** PR-triggered workflows on this exact SHA completed SUCCESS: Budget Tests #41929171733 (23 passed), Frozen V2 Shadow #41929171736 (86 passed), Research #41929171651 (explicit `PASS: no .pkl changes in PR`), plus Serie A, Bundesliga, Ligue 1, Eredivisie and Product validation. Earlier references to `97a94f5...` in this PR body/comments are stale and are not the current PR head. HUMAN-MERGE only.
- **PR #699** is open at exact current HEAD `b1ca50494d529f3fd84dcb2e1435f078c4876099`, based on the same main. All **7/7** PR workflows on this exact SHA completed SUCCESS; its Frozen V2 Shadow job #41921583855 ran **323 passed**. It contains the identity-only gate/freshness helpers and conditional personal/academic frozen-inference scope; AI training, commercial use and public product use remain disallowed by the checked-in source-rights manifest. Older SHA references in the PR description are stale.
- **PR #714** is a new open follow-up at `00daa9dd5442bcb21d64b4bb319e593c18a7ee22`, stacked on #705's branch head `8cf5ded4...`. It separates the Free Real-Quote Diagnostic's push-only offline validation from the secret-bearing live job; the validation job has no Supabase credentials or GitHub API token, and the live diagnostic excludes push events. It changes only the diagnostic workflow and its budget-contract test. No exact-head CI run was present at this audit. Required order: merge #705 manually, rebase #714 onto resulting main, then run full exact-head CI; do not merge #714 directly to main before #705.
- **PR #701** remains open at `499c95cea970d42ee6512b77986af6143295e653`. Its five non-Research checks passed, but Research PR Validation failed at import time because main lacks `_current_gate_freshness`; the helper is supplied by #699. This is a dependency failure, not evidence to duplicate the helper. Rebase and rerun only after #699 is integrated.
- **PR #702** remains open at `3935fc601eff30d2ca0a7670dae797d0cb365228`, with 7/7 exact-head checks SUCCESS. It is manual-dispatch/main-only and makes one metadata-only The Odds API `/events` request after source/identity attestation; the official V4 docs state this endpoint does not count against usage quota. The code requires `x-requests-last: 0`, rejects odds/outcome fields, computes only the original 19 V2 input features, and emits no probabilities or forecast. It depends on #699 and a fresh post-integration identity-attested source archive; it has not been dispatched.
- **PR #712** is currently open at `4b9b1281a8ab81988ea713eb5974d1e55dbba81d`. No PR-triggered workflow run was associated with this current HEAD. Its description's 9/9 evidence refers to older SHA `1c0f5a424dd51abc0f1a7dedfb7f8ff1047b3339`; do not treat that as current-head CI.

Read-only Supabase audit at this run:
- `odds_snapshots`: 3,966 total rows, 3,915 with `snapshot_time_utc < commence_time_utc`, 51 not strictly pre-kickoff; zero strict pre-kickoff snapshots in the last seven days across the nine leagues.
- Serie A: 625 total, 620 strictly pre-kickoff, latest strict quote `2026-10-13T14:48:53.042620Z`; zero future events with a saved strict pre-kickoff quote.
- The feature-input metadata query selected only `match_date,home_team,away_team`: 103 raw Serie A 2026/27 rows, 100 unique identities after the frozen V2-local `Atalanta BC -> Atalanta` alias, from 2026-08-22 through 2026-11-02. No score/result columns were selected.
- Existing source artifact #13327281383 has ZIP SHA-256 `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd`; the Nov 4 independent audit recorded 100/100 canonical identity parity and digest `f85872547e745eae8854ee245902c1e522657fb3a687032be83b000199f2a99e`. It predates #699 and lacks the new manifest's rights/identity attestation, so it is not admissible to the post-#699 evaluator.
- The 170-hour source-capture interval from the Nov 4 13:19:46 UTC attempt ends at Nov 11 15:19:46 UTC; with the unchanged 05:50 UTC cron, the first scheduled eligible capture is Nov 12 05:50 UTC. The free-diagnostic interval ends Nov 11 16:25:54 UTC; its unchanged 06:13 UTC cron first falls after that on Nov 12 06:13 UTC. The 24-hour source freshness boundary arrives Nov 5 around 13:19:45 UTC. Do not weaken freshness or bypass the two-session weekly source limit.

No new quotes, V2 forecasts, target-outcome reads, Supabase writes/DDL, paid provider calls, model/weight/lambda changes, production `.pkl` changes, merges, schedule changes or promotions occurred. Prospective evaluation remains **0/30**; Brier/LogLoss are not yet available.
