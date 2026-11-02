# Original MARKET_ANCHOR_1X2_V2 — runtime and pre-match source audit
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
