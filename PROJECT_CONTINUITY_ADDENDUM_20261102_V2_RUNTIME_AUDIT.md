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
