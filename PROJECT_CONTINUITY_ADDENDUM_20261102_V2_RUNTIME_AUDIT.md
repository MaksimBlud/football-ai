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
