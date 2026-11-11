# Continuity update — 2026-11-11 09:18 UTC — superseded V2 branches closed

The exact-head audit now confirms the following duplicate branches have been closed, without merge:
- #742 → superseded by #783 (strict pre-kickoff quote query on the updated source-policy stack).
- #774 → superseded by #784 (direct saved-quote rights gate).
- #777 → superseded by #785 (direct shadow-scoring rights gate).
- #778 → superseded by #786 (frozen candidate SHA/refit lock).
- #767 → its bidirectional fixture identity and no-offset attestation changes are now included in #787 exact HEAD `013dccc0ef195721977c52ac663c8bc0312022b8`; the duplicate main-based PR was closed after #787's 433+433 regression tests and 15 V2 validation tests passed.

The replacement chain remains Draft where stacked; no PR was merged and main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The only ready main-based integration priorities are the independent live-access hold #781 (8/8 exact-head checks) and source-rights/download-budget #720 (9/9 exact-head runs). HUMAN-MERGE remains mandatory.

---

# Continuity update — 2026-11-11 09:16 UTC — bidirectional fixture identity and final direct-access audit

## Fresh main and original V2 contract

- `refs/heads/main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main update or merge.
- Original `MARKET_ANCHOR_1X2_V2` candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, candidate blob `ac1303f6b096664983fbf52443bd0a381b23ba21`. The 19-feature order, 20×2 weights, scaler/imputer, 3,799 training rows, `active_lambda=0`, `shadow_lambda=1`, failed stability gate and no-promotion rule remain unchanged.

## #787 — direct-access and fixture-identity gaps closed on the same branch

- PR #787 remains Draft, stacked on #786 HEAD `6e61c92fd211862ef1ad067faa6789fe535779e5`.
- Current #787 HEAD: `013dccc0ef195721977c52ac663c8bc0312022b8`, parent `b4cf76bb8e477a9681b657aba5a2949a57e76bc7`.
- The prior #787 direct-access audit fix now requires provider inference rights plus private artifact storage at the original low-level V2 scorers, candidate loader, direct shadow preview, saved-quote reader and CLI before model bytes, inputs, Supabase or feature files are touched.
- A further audit of the actual forward code found that the branch rejected one event ID changing identity, but did not reject two different provider IDs representing the same fixture in reversed Home/Away order. Ported the independent #767 bidirectional-identity fix into #787: canonical team aliases/case/spacing are used only for identity checks; unordered team-pair + kickoff collisions across provider IDs are rejected; surrounding event-ID whitespace and identical canonical teams fail before archive or parent-run access. Quote prices and the frozen feature/model contract are untouched.
- Exact-head CI for `013dccc0ef195721977c52ac663c8bc0312022b8`:
  - [Serie A Frozen V2 Shadow Tests #42993430189](https://github.com/MaksimBlud/football-ai/actions/runs/42993430189): **433 passed on Python 3.11 and 433 passed on Python 3.12**; dependency lock `pip check` succeeded; candidate file presence and `git diff --exit-code -- '*.pkl'` succeeded.
  - [Market Anchor 1X2 V2 Shadow Validation #42993430037](https://github.com/MaksimBlud/football-ai/actions/runs/42993430037): **15 passed**.
- These are offline/synthetic regression results only. They do not authorize source capture or inference and are not model-quality evidence.
- #767's bidirectional identity logic and no-offset attestation guard are now present in the #787 branch; avoid merging both versions without rebase. #787 remains Draft until its #786 parent stack is integrated and exact-head CI is rerun.

## Current data and evaluation status (read-only)

- Strict pre-match quote predicate: `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= NOW()`.
- `public.odds_snapshots`: 3,915 strict pre-match snapshots / 327 events; zero future events with saved strict pre-match quotes; latest observation `2026-10-13T14:48:53.042620Z`.
- Exact original-candidate SHA query in `public.product_prediction_snapshots`: zero strict pre-match V2 predictions / zero events.
- Serie A 2026-2027 feature-input metadata query selected only `match_date,home_team,away_team`: 113 unique fixture identities through 2026-11-08. No target scores/results/settlements were selected; the separate 30-completed-forecast target-outcome gate remains closed.
- Latest actual V2 source/diagnostic/original-forward/current-form-forward runs remain the 2026-11-10 runs #42827889788, #42837720155, #42853738496 and #42854487569. They show respectively a source archive with 110 feature-source events, zero eligible quotes, zero original V2 quote previews, and zero current-form shadow captures. No new V2 scheduled run was present in the latest Actions history for 2026-11-11 at this audit time.

## Manual integration blockers and safety

- #781 remains OPEN / Ready for review / mergeable, exact HEAD `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`, with 8/8 exact-head CI SUCCESS. It is not merged; main live schedules remain present until owner HUMAN-MERGE.
- #720 remains OPEN / Ready for review / mergeable, exact HEAD `1b9464834dd5256b7d69499c1443378518dde256`, with 9/9 exact-head runs SUCCESS. Its proposed rights manifest still records inference unresolved/false and `authorization=null`; its two-session ceiling is not a rights grant.
- The repository remains public. Private-artifact guard therefore correctly blocks source/inference artifact access. Do not change repository visibility or schedules.
- Supabase writes/DDL = 0; paid provider calls = 0; no source download or inference in this audit; production `.pkl` unchanged; no target-outcome reads, bets, threshold tuning or promotion.

---

# Continuity update — 2026-11-11 09:10 UTC — close remaining direct frozen-inference/private-artifact bypasses

## Fresh main, PR stack and exact candidate

- Fresh `refs/heads/main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository visibility is **public**. No main update or merge was performed.
- Original `MARKET_ANCHOR_1X2_V2` candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, candidate blob `ac1303f6b096664983fbf52443bd0a381b23ba21`; original 19-feature order, 20×2 weights, scaler/imputer, 3,799 training rows, `active_lambda=0`, `shadow_lambda=1`, failed stability gate and no-promotion rule are unchanged.
- The current code work is still isolated in Draft PR #787, stacked on exact #786 HEAD `6e61c92fd211862ef1ad067faa6789fe535779e5`. New #787 HEAD: `b4cf76bb8e477a9681b657aba5a2949a57e76bc7`, parent `628bd531447fbe742b667a52bf43e09f37de1481`. No merge.

## New direct-entrypoint audit and repair

A second pass over the actual callable V2 surfaces found a gap in the initial #787 pass: `market_anchor_1x2_v2_shadow` low-level `_artifact_residual_logits`, `predict_shadow_residual`, and `predict_candidate`, plus `serie_a_v2_frozen_shadow_preview` candidate loading, direct preview, saved-quote reader and CLI, checked provider inference rights but did not consistently require the separate private-artifact gate.

Commit `b4cf76bb8e477a9681b657aba5a2949a57e76bc7` routes these entrypoints through `require_v2_inference_access()` before caller inputs, candidate bytes, Supabase reads or feature-file access. Negative regressions were added for the low-level scoring APIs, candidate loader, direct preview, quote reader and CLI.

Exact-head CI:
- [Serie A Frozen V2 Shadow Tests #42992707133](https://github.com/MaksimBlud/football-ai/actions/runs/42992707133): **428 passed on Python 3.11 and 428 passed on Python 3.12**.
- [Market Anchor 1X2 V2 Shadow Validation #42992707166](https://github.com/MaksimBlud/football-ai/actions/runs/42992707166): **15 passed**.
- Both exact-head PR runs completed SUCCESS. These are offline/synthetic regressions only, not a live inference authorization or model-quality result.

## Rights, private storage and live workflow status

- PR #720 is still open and not merged. Its rights manifest/policy remains fail-closed: source capture and inference are not authorized; the two-session weekly ceiling is a limit, not permission.
- The repository is public, so the private GitHub Actions artifact gate correctly denies source/inference artifact access. No visibility change was made.
- PR #781 remains OPEN / Ready for review / mergeable at exact HEAD `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`, based on main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; exact CI remains **8/8 SUCCESS**. It has not been merged. Main's four scheduled V2 workflows therefore remain unheld until the owner manually merges #781; their cron expressions were not changed.
- The latest successful live V2 workflow runs remain on 2026-11-10: source capture #42827889788 (110 completed feature-source events, 11 CSVs, artifact #13770560196, SHA-256 `f29363e28775032937108d102da1dda1ca2d5c1aa0f921cb4518bf3a82e9aec6`); free diagnostic #42837720155 (0 eligible quotes); original forward #42853738496 (0 quotes / 0 V2 previews); current-form forward #42854487569 (0 quotes / 0 shadow captures, target-outcome gate false). No new V2 schedule run was present in the latest Actions history for 2026-11-11 at this audit time.

## Read-only Supabase inventory

- Strict quote predicate remains `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= NOW()`.
- `public.odds_snapshots`: **3,915** strict pre-match snapshots / **327** unique events; **0** future events with saved strict pre-match quotes; latest observation `2026-10-13T14:48:53.042620Z`.
- Serie A 2026-2027 feature-input metadata query selected only `match_date,home_team,away_team`: **113 rows / 113 unique fixture identities**, latest date 2026-11-08. This is only the feature-input gate.
- No target score/result/settlement columns were selected; the prospective 30-completed-forecast outcome gate remains closed. No new V2 prospective forecasts or Brier/LogLoss evidence exist.

## Safety state

- Production `.pkl` unchanged; original weights/contract unchanged; Supabase writes/DDL = 0; paid provider requests = 0; no source download or inference in this audit; no bet, threshold tuning, promotion or protected-outcome read.
- Keep #787 Draft until the parent stack is manually integrated and exact-head CI is rerun. Do not merge or change main automatically.

---

# Continuity update — 2026-11-11 08:01 UTC — direct-entrypoint guard stack exact-head completion

## Fresh main and frozen original candidate

- Fresh `refs/heads/main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main update or merge was performed.
- Original `MARKET_ANCHOR_1X2_V2` candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; candidate blob `ac1303f6b096664983fbf52443bd0a381b23ba21`.
- The exact original 19-feature order, 20×2 weights, scaler, imputer, medians, 3,799 training rows, `active_lambda=0`, `shadow_lambda=1`, failed stability gate and no-promotion policy remain unchanged. No legacy XGBoost production path is used.

## Current direct-entrypoint guard PR

- PR #787 remains Draft and is stacked on exact parent #786 HEAD `6e61c92fd211862ef1ad067faa6789fe535779e5`; exact current HEAD is `628bd531447fbe742b667a52bf43e09f37de1481`.
- Exact PR CI [42983473604](https://github.com/MaksimBlud/football-ai/actions/runs/42983473604): **425 passed under Python 3.11 and 425 passed under Python 3.12**. Candidate-presence and production `.pkl` diff guards succeeded.
- The branch uses one fail-closed direct-access module with separate `INFERENCE` and `SOURCE_CAPTURE` scopes. Direct quote, archive, feature, current-form forward, source-capture and source-attestation entrypoints check the appropriate rights/privacy gate before external reads or filesystem output.
- Historical CSV loading is split: inference uses the inference scope; current-form source capture uses the narrower source-only scope. The source-only path no longer calls `load_verified_original()` or loads model weights; it pins the expected frozen candidate SHA as a code-level contract value. The later inference path independently loads and SHA-validates the actual candidate bytes before features/scoring.
- CLI regressions prove the feature-manifest and prequote archive gate check rights before reading input files. Additional regressions prove private storage is required for source-only access and source-only rights cannot authorize inference entrypoints.
- Older direct-entrypoint branches #779 and #782 and sibling #788 were closed as superseded; none was merged. PR #787 remains Draft until the #786 parent stack is integrated and exact-head CI is rerun.

## Live-access hold remains the immediate manual action

- Main still declares schedules: current-form source capture 05:50 UTC, free real-quote diagnostic 06:13 UTC, original forward-only 08:08 UTC, current-form forward-only 08:18 UTC. The current main workflow files do not yet contain the new live-access hold.
- PR #781 is OPEN, Ready for review, mergeable, exact HEAD `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; exact CI is **8/8 SUCCESS**.
- PR #781 has not been merged. Manual merge remains the next operational action. Do not auto-merge or change the schedules.

## Source rights and private storage remain blocking

- The checked Football-Data manifest has `research_source_capture_permitted=false`, `research_inference_permitted=false`, `ai_model_training_permitted=false`, and `authorization=null`. The two-session download ceiling is a limit, not permission.
- The GitHub repository is public; the private-artifact guard therefore denies source archive access. SHA integrity does not grant data-use rights or confidentiality.
- No provider source request, new source archive, model inference, paid API call or source upload was made in this run. Keep both source and inference scopes fail-closed pending provider clarification and private storage.

## Read-only Supabase pre-match inventory (2026-11-11)

- Strict filter: `public.odds_snapshots.snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= NOW()`.
- **3,915** strict pre-match snapshots / **327** unique events across nine leagues.
- New strict pre-match snapshots in the last seven days: **0**. Future events with saved strict pre-match quotes: **0**.
- Latest Serie A strict pre-match snapshot: `2026-10-13T14:48:53.042620Z`.
- Serie A 2026-2027 feature-input metadata query selected only `match_date,home_team,away_team`: **113 rows / 113 unique fixture identities**, from 2026-08-22 through 2026-11-08. This is only the feature-input gate, not the prospective target-outcome gate.
- No score, result, settlement, target outcome or protected 2026/27 outcome columns were selected. Supabase writes/DDL = 0.

## Supabase security advisory

- RLS remains disabled on five public tables: `teams`, `predictions`, `match_statistics`, `league_prediction_ledger`, `epl_ai_market_pair_ledger`.
- This is a critical exposure. Do not auto-enable RLS without reviewing policies because existing application access may break. Owner-controlled remediation SQL:
  ```sql
  ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
  ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
  ALTER TABLE public.match_statistics ENABLE ROW LEVEL SECURITY;
  ALTER TABLE public.league_prediction_ledger ENABLE ROW LEVEL SECURITY;
  ALTER TABLE public.epl_ai_market_pair_ledger ENABLE ROW LEVEL SECURITY;
  ```

## Evaluation status

- No new admissible prospective V2 forecasts or independent outcomes were created/read in this run. No new Brier/LogLoss comparison is available.
- No superiority claim against the market. `active_lambda=0` remains the market; `shadow_lambda=1` remains research-only.
- Production `.pkl` unchanged; paid The Odds API calls = 0; no bets, promotion, threshold tuning or outcome-gate bypass.
---

# Continuity update — 2026-11-11 06:17 UTC — clean rights-stack rebase and exact-head CI audit

## Fresh main and immutable original candidate

- GitHub refs/heads/main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; signed commit date 2026-10-18 08:20:05 UTC. No main update or merge was performed.
- Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; candidate blob `ac1303f6b096664983fbf52443bd0a381b23ba21); protocol blob `65729e9639720e67624c1481190aa22ae606f151); historical feature builder blob `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- Original 19-feature order, 20×2 weights, medians, scaler, 3,799 training rows, `active_lambda=0`, `shadow_lambda=1`, failed stability gate and no-promotion policy remain unchanged.

## Fresh strict pre-match Supabase inventory

Read-only queries used only timestamps, event/team identity, league/season metadata and the exact candidate SHA. No odds prices, scores, results, settlements or target outcomes were selected.

- `public.odds_snapshots`: 3,915 strict pre-kickoff snapshots / 327 events; 0 future events with saved strict pre-match quotes; latest strict snapshot `2026-10-13T14:48:53.04262Z`.
- `public.product_prediction_snapshots`, exact original candidate SHA: 0 strict pre-match predictions / 0 events.
- `public.epl_ai_market_pair_ledger`, exact original candidate SHA: 0 strict pre-match rows / 0 events.
- Serie A current-form identity metadata in `public.league_finished_results`: 113 unique `(match_date, home_team, away_team)` identities for season `2026-2027`, latest date 2026-11-08. The query did not select score/result fields. This is only the feature-input metadata gate, not the separate target-outcome evaluation gate.
- The 30-primary-completed-event target-outcome gate remains CLOSED; no 2026/27 target outcomes were read.

## Current clean-ancestry rights stack

The new linear replacement chain is:

`#720 → #727 → #780 → #783 → #784 → #785 → #786`

- #720: exact HEAD `1b9464834dd5256b7d69499c1443378518dde256`; 9/9 associated workflow runs SUCCESS.
- #727: exact HEAD `18a3cfda4e83e44aca1252665d01804267d16467`; Frozen V2 suite 388 passed in Python 3.11 and 3.12; public-source-budget suite 24 passed; production `.pkl` guards passed.
- #780: exact HEAD `48f55b6ef4dc40879d5232ac78ce55df51d2dce4`; run #42812927009 SUCCESS, 388 passed in both Python versions, production `.pkl` guards passed. This conservatively blocks automated Football-Data access pending provider clarification; it is not a rights grant.
- #783 replaces #742 on #780: HEAD `a9c77854bc03036f1a15d0fed2dadf29e02c23e9`, 3 ahead / 0 behind; run #42966318614 SUCCESS, 388 passed in Python 3.11 and 3.12.
- #784 replaces #774 on #783: HEAD `e6bf94944fc1fe075d588f325c5e88ce8b5c43ab`, 3 ahead / 0 behind; run #42966555209 SUCCESS, 390 passed in both Python versions.
- #785 replaces #777 on #784: HEAD `dba4556c618239f6a67ea810195e5662b4772466`, 8 ahead / 0 behind; run #42967054287 SUCCESS, 391 passed in both Python versions; `pip check` and both production `.pkl` hash guards passed.
- #786 replaces #778 on #785: HEAD `6e61c92fd211862ef1ad067faa6789fe535779e5`, 5 ahead / 0 behind; run #42967497143 SUCCESS (15 direct V2 contract tests) and run #42967497201 SUCCESS (414 passed in Python 3.11 and 414 in Python 3.12); compile, dependency and production `.pkl` guards passed.

These are offline/synthetic regression results only. They do not authorize source capture or inference and are not model-quality evidence.

## Separate direct-forward/report branch is not yet on the clean chain

- #782 is the clean-ancestry replacement for #779 relative to the older #778 HEAD: exact HEAD `984f00cf1c4c236dc4124ec1903e3ddd4c51474e`, 17 ahead / 0 behind #778; run #42964659477 SUCCESS, 440 passed in Python 3.11 and 440 in Python 3.12, with production `.pkl` guards.
- However, compare #786 HEAD against #782 HEAD returns `diverged`, 43 ahead / 29 behind, merge base #727 HEAD `18a3cfda4e83e44aca1252665d01804267d16467`. #782 is therefore not part of the new #783→#786 linear chain and must not be merged directly or treated as current.
- After the parent chain is manually integrated, port/rebase #782's unique direct forward/report and private-artifact checks onto the latest #786 descendant and rerun exact-head CI. Do not integrate both #779 and #782. Keep #782 Draft.

## Main live-workflow hold remains a manual blocker

- PR #781 remains OPEN / Ready for review / mergeable / HUMAN-MERGE at exact HEAD `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- All 8 exact-head PR workflow runs are SUCCESS, including the Frozen V2 suite and recovery workflow. The recovery job's candidate rebuild/proof/upload remain skipped; offline tests and production `.pkl` guard pass.
- Static comparison confirms #781 gates five live source/quote steps and all four artifact uploads across the four scheduled V2 workflows plus the recovery workflow. It preserves the existing cron strings: 05:50, 06:13, 08:08 and 08:18 UTC. The corresponding main workflow files still lack the hold flag because #781 is not merged.
- Manual integration order remains #781 first, then rebase #720 → #727 → #780 → #783 → #784 → #785 → #786 on fresh main. #781 does not change schedules; no workflow was dispatched by this audit.

## Separate Supabase security advisory

The current table metadata still reports RLS disabled on five public tables: `teams`, `predictions`, `match_statistics`, `league_prediction_ledger`, and `epl_ai_market_pair_ledger`. No DDL or writes were performed. Do not enable RLS without designing and validating access policies; this is a separate application-security issue, not V2 evidence.

No source CSV was downloaded, no bookmaker quote was read, no paid API was called, no target outcome was opened, no Supabase write/DDL occurred, no production `.pkl` or schedule changed, and no other-agent setting changed. HUMAN-MERGE only.

---

# Continuity update — 2026-11-11 00:56 UTC — exact original V2 artifact identity pin

## Fresh main and frozen candidate

- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; the branch API reports `protected=false`. No main update or merge was performed.
- Original candidate blob: `ac1303f6b096664983fbf52443bd0a381b23ba21`; embedded SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Protocol blob: `65729e9639720e67624c1481190aa22ae606f151`; historical feature builder blob: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- Frozen 19-feature order, 20×2 weights, medians, scaler, 3,799 training rows, `active_lambda=0`, `shadow_residual_lambda=1`, failed stability gate and no-promotion policy remain unchanged.

## New direct-API identity gap closed on PR #778

A fresh audit of the PR branch found that the low-level candidate validator checked only a self-reported SHA-256. A caller could alter the frozen weights, recompute the self-hash, and pass the recipe/shape checks. The prospective capture-row validator also accepted any syntactically valid candidate SHA.

PR #778 now pins both the direct candidate validator and every captured shadow row to the exact original candidate SHA. Its tests use the real frozen JSON and reject re-hashed non-original weights and a wrong candidate hash.

- Exact PR #778 HEAD: `aa0cd076a15033d2d90c7c08cb3ff14c94c2e8ec`.
- Frozen V2 Shadow Tests [run 42935139447](https://github.com/MaksimBlud/football-ai/actions/runs/42935139447): **2/2 jobs SUCCESS**, Python 3.11 **414 passed**, Python 3.12 **414 passed**; production `.pkl` diff guards passed.
- Market Anchor 1X2 V2 Shadow Validation [run 42935139489](https://github.com/MaksimBlud/football-ai/actions/runs/42935139489): **1/1 SUCCESS**, **15 passed**, production `.pkl` guard passed.
- This is a PR-branch guard only; it is not on main until the required parent stack is manually integrated.

## Direct-forward stack and HUMAN-MERGE

- PR #779 remains based on stale #778 parent `b2a034614d999683a8c334569dc07eb07b7ac589`, HEAD `3e936d64b1f490b8c8dc31951b35e446096ca94c`. Compare with the new #778 HEAD: diverged, **28 ahead / 3 behind**, merge base `60d1025e9556cdce05f93b9a71ce46d4d06096cb`. Keep Draft; rebase after parent integration and rerun exact-head CI.
- PR #781 remains OPEN / Ready for review / HUMAN-MERGE at exact HEAD `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`. Direct commit check-runs: **8/8 SUCCESS**. It is not on main; the live hold is not deployed.
- PR #720 remains OPEN / Ready for review at `1b9464834dd5256b7d69499c1443378518dde256`; the source-rights/shared-download-budget tests and associated PR validations are green. PR #727 remains stacked on #720 at `18a3cfda4e83e44aca1252665d01804267d16467`. PR #780 remains Draft on #727 at `48f55b6ef4dc40879d5232ac78ce55df51d2dce4` and explicitly withdraws automated source-capture permission pending provider clarification.
- The safe-agent auto-merge workflow ran on main but logged `SAFE_AUTO_MERGE_HEALTHY_NOOP: no eligible bot PR with verified six-check CI`; no V2 PR was merged. HUMAN-MERGE remains binding.

## Read-only pre-match Supabase check

Only strict pre-kickoff timestamp/identity aggregates were queried; no prices, results, scores, settlements or target outcomes were selected.

- `public.odds_snapshots`: **3,915** strict pre-match rows / **327** events; **0** rows in the last seven days; **0** future events with saved quotes; latest strict snapshot `2026-10-13T14:48:53.04262Z`.
- `public.product_prediction_snapshots`, exact original candidate SHA: **0** strict pre-match V2 predictions / **0** events; no generation timestamp exists.
- No new source/quote pair or independent prospective V2 sample is available. No Brier/LogLoss superiority claim is supported.

## Security and operational blockers

- Supabase Security Advisor reports RLS disabled on five public tables: `teams`, `predictions`, `match_statistics`, `league_prediction_ledger`, and `epl_ai_market_pair_ledger`. It also reports RLS enabled without policies on `competitions`, `match_stats`, `matches`, and `standings`. No DDL or writes were performed; do not enable RLS without policy design and validation.
- Main still contains the four scheduled live V2 workflows because #781 is not merged. Their existing UTC cron slots remain 05:50 (current-form source), 06:13 (free diagnostic), 08:08 (original forward), and 08:18 (current-form forward). The latest run window inspected for this cycle contained no new scheduled V2 run; no workflow was dispatched.
- No provider source was downloaded, no quote was read, no paid API was called, no protected 2026/27 outcome was opened, no Supabase write/DDL occurred, and no production `.pkl` or schedule was changed.

---

# Continuity update — 2026-11-10 18:05 UTC — V2 live-hold regression hardening and source-policy audit

## Fresh main and immutable original V2

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Candidate Git blob `ac1303f6b096664983fbf52443bd0a381b23ba21`; embedded candidate SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original protocol blob `65729e9639720e67624c1481190aa22ae606f151`; feature builder blob `401b3a0893371bfa4a488ec92a4a54af2678c8f7`; separate current-form policy blob `394a426c7ced81e27e12de61087a349bb972b612`.
- Candidate still has 19 frozen features, 20x2 weights, 3,799 training rows through 2026-06-30, `active_lambda=0`, `shadow_residual_lambda=1`, stability gate false and automatic promotion false. The original 30-completed-primary-event outcome gate and the separate 30-eligible-prospective-forecast evaluation gate remain distinct and closed.
- No weights, medians, scaler, feature order, training fingerprint, production `.pkl`, or model contract changed.

## Exact PR #781 latest head

PR #781 remains the direct-main interim live-access hold. Latest exact HEAD `ac9cee6748f7e380d97ad9040a32adb080514552`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, OPEN / Ready for review / mergeable / HUMAN-MERGE.

Two additional static regressions now prove:
1. the fail-closed environment flag has exactly one workflow-level definition set to `false`, with no job/step override;
2. every `actions/upload-artifact` action in each of the four live V2 workflows is gated, not merely the currently named upload step.

Exact-head CI: **7/7 SUCCESS**. Frozen V2 Shadow Tests [run 42871106817](https://github.com/MaksimBlud/football-ai/actions/runs/42871106817): **91 passed**, Python compilation and production `.pkl` diff guard passed. Other exact-head runs: Serie A 42871106947, Research 42871106924, Product 42871106995, Bundesliga 42871106967, Ligue 1 42871106776, Eredivisie 42871106735 — all SUCCESS. Offline/synthetic only.

The four live workflows audited are free diagnostic, original forward-only, current-form source capture and current-form forward-only. The other V2-related workflows found on main are PR-only regression workflows or the manual fixed-input candidate-recovery workflow; they are not scheduled live source/quote capture paths. All four live workflow cron strings remain unchanged in #781.

## Verified main-branch runtime before the hold is merged

- Original Forward-Only run [42853738496](https://github.com/MaksimBlud/football-ai/actions/runs/42853738496), main SHA above, SUCCESS: source attestation verified source artifact 13773563645 / parent run 42837720155 / 10 historical CSVs / 3,800 rows. Forward JSON artifact 13782226394, SHA-256 `24906d82f8d15b6597ba0227be9253b460d55038116a1b03b85bb21443a42d94`; `quotes_seen=0`, `future_quotes_checked=0`, zero previews and zero prospective eligibility.
- Current-Form Forward-Only run [42854487569](https://github.com/MaksimBlud/football-ai/actions/runs/42854487569), same main SHA, SUCCESS: 53 tests passed; re-attested source artifact 13770560196, ZIP SHA-256 `f29363e28775032937108d102da1dda1ca2d5c1aa0f921cb4518bf3a82e9aec6`, parent run 42827889788 completed at 13:49:20 UTC; 10 historical CSVs + one current-form source archive, 3,910 historical rows and 110 metadata-only feature-input identities. The JSON-only report says `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes not read/scored, no paid calls or writes.
- Current-form forward artifact 13780824313, 440,596 bytes, SHA-256 `62196fcf3dfb6b384d5f1f4c11b532073ffe7bff57f06bec712afa34336cdfeb`, remains in public GitHub Actions artifact storage until 2027-02-08. Its nested current-season source file was deliberately NOT opened in this audit; the artifact is not deleted by #781.
- No V2 live workflow run appears after the 16:21 and 16:26 UTC main runs in the latest 100-run window. Those runs predate PR #781's 17:01 UTC head and therefore do not demonstrate the hold is active.

## Current read-only pre-match Supabase inventory

Queries touched only `public.odds_snapshots` timestamp/identity/league columns and applied `snapshot_time_utc < commence_time_utc` plus `snapshot_time_utc <= NOW()`. No prices, scores, results, settlements or target outcomes were selected.

- All leagues: 3,915 strict pre-match snapshots / 327 distinct events; zero new snapshots/events in the last 7 days; zero future events with saved pre-match quotes.
- Serie A: 620 strict pre-match snapshots / 63 distinct events; zero new snapshots/events in the last 7 days; zero future events with saved pre-match quotes.
- Latest saved strict pre-match snapshot: 2026-10-13 14:48:53 UTC.

## Provider terms and source hold

The current official Football-Data pages state that the free CSV/Excel data is intended for private individuals for personal betting and/or academic interest/research, via manual download or at most light automated download (twice per week maximum), and is not intended for commercial or data-training products using heavy repeated automated bots/scrapers/AI. The project is an AI research model and the prior workflows were daily automated downloads. Treat permission for this use as unresolved; do not resume automated capture or inference without clear authorization. Official pages: https://football-data.co.uk/data.php and https://football-data.co.uk/contact.php.

PR #781 is an interim hold only; because it is not merged, the old main still contains live-access steps. Do not claim the hold is deployed until the owner manually integrates it and a fresh-main audit confirms all live steps and artifact uploads remain skipped.

## Supabase security advisory (separate from V2)

Security Advisor at 2026-11-10 18:04 UTC reports RLS disabled on five public tables: `teams`, `predictions`, `match_statistics`, `league_prediction_ledger`, `epl_ai_market_pair_ledger`. It also reports RLS enabled without policies on `competitions`, `match_stats`, `matches`, `standings`. No DDL or writes were performed; do not enable RLS without designing and validating policies.

No protected 2026/27 target outcomes were opened. No new forecasts or Brier/LogLoss observations were created. No paid API, Supabase writes/DDL, production `.pkl` changes, schedule changes, other-agent changes, or main updates occurred.

---

# Continuity update — 2026-11-10 17:05 UTC — Original V2 forward rerun and credential-scoped live hold

## Fresh main and frozen identity

Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; this checkpoint records evidence only. Original candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; candidate Git blob `ac1303f6b096664983fbf52443bd0a381b23ba21`; original protocol blob `65729e9639720e67624c1481190aa22ae606f151`; separate current-form policy blob `394a426c7ced81e27e12de61087a349bb972b612`. The original protocol requires 30 completed primary Serie A events before its first target-outcome read. The separate current-form cohort requires 30 completed eligible prospective forecasts before its evaluation read. These are different gates. Original 19 features/weights, `active_lambda=0`, `shadow_lambda=1`, NO_BET and failed stability gate remain unchanged.

## New real Original Forward-Only run

[Run 42853738496](https://github.com/MaksimBlud/football-ai/actions/runs/42853738496), main SHA above, SUCCESS. Offline regression step: **71 tests passed**. Real GitHub source attestation verified artifact `13773563645`, parent source run `42837720155`, GitHub ZIP SHA, **10** pre-prospective historical CSVs and **3,800** historical results. Forward JSON artifact `13782226394` has ZIP SHA-256 `24906d82f8d15b6597ba0227be9253b460d55038116a1b03b85bb21443a42d94`; parsed report: `quotes_seen=0`, `future_quotes_checked=0`, `eligible_for_frozen_prospective_cohort=false`, `supabase_writes=0`, `paid_provider_calls=0`. This proves source attestation only, not a forecast.

## New real Current-Form Forward-Only run

[Run 42854487569](https://github.com/MaksimBlud/football-ai/actions/runs/42854487569), same main SHA, SUCCESS; **53 tests passed**. Artifact `13780824313` ZIP SHA-256 `62196fcf3dfb6b384d5f1f4c11b532073ffe7bff57f06bec712afa34336cdfeb`. Its JSON-only report re-attests source artifact `13770560196` SHA-256 `f29363e28775032937108d102da1dda1ca2d5c1aa0f921cb4518bf3a82e9aec6`, parent run `42827889788` completed at 13:49:20 UTC, 11 source files (10 historical + current-form archive), 3,910 historical rows and 110 metadata-only current-season feature-input identities. Source age at verification: 9,447 seconds (<24h). Report: `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes not read/scored, no paid calls and no Supabase/production writes. The nested current-season source ZIP was not opened for this audit. No source-before-quote pair exists because there was no quote.

## Read-only pre-match Supabase aggregate

`public.odds_snapshots`, strictly `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`, league `SERIE_A`: **620 snapshots / 63 distinct events**; zero snapshots or events in the last seven days; zero future fixtures with saved snapshots; latest snapshot `2026-10-13 14:48:53 UTC`. No prices, scores, results or settlements were selected.

## Live access is still active on main

PR #781 is not merged, so main workflows ran at 16:21 and 16:26 UTC after the hold PR was opened. PR #781 now gates all five live source/quote steps and four artifact uploads across the four workflows; it also scopes Supabase/GitHub credentials only to gated steps so offline tests do not inherit them. Existing four cron expressions are preserved. Updated exact HEAD `d901055e667697f65a3bea6686cdbbd38785a1f5`, **7/7 exact-head CI SUCCESS**; Frozen V2 suite **89 passed**, compilation and production `.pkl` diff guard passed. PR #781 is Ready for review, OPEN, mergeable and HUMAN-MERGE only: [PR #781](https://github.com/MaksimBlud/football-ai/pull/781). It is not yet active on main.

## Rights stack remains open

- #720 HEAD `1b9464834dd5256b7d69499c1443378518dde256` — exact CI green.
- #727 HEAD `18a3cfda4e83e44aca1252665d01804267d16467` — exact CI green.
- #780 HEAD `48f55b6ef4dc40879d5232ac78ce55df51d2dce4` — exact CI green, Draft.

Keep the order #781 manual hold first, then rebase/revalidate #720 → #727 → #780 and direct-reader/inference descendants on fresh main. No source/quote access should resume without provider clearance and private artifact storage.

No target outcomes were opened, no new forecasts were created, no model fit/refit or threshold tuning occurred, and no production `.pkl`, Supabase data/schema, schedule, other agent or main change was made.

---

# Continuity update — 2026-11-10 15:59 UTC — interim live-workflow hold PR #781

## Fresh main and frozen original V2 identity

- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main write occurred.
- Candidate Git blob: `ac1303f6b096664983fbf52443bd0a381b23ba21`; candidate artifact SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original protocol Git blob: `65729e9639720e67624c1481190aa22ae606f151`.
- Original feature builder Git blob: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- The frozen candidate still has 19 features, 3,799 training rows through 2026-06-30, `active_lambda=0`, `shadow_residual_lambda=1`, `stability_gate_passed=false`, and `automatic_promotion=false`. No model artifact, weights, scaler, imputer, feature order, training fingerprint, or production `.pkl` changed.

## Why an interim hold was necessary

The official Football-Data data page is still marked `Updated: 10/11/26` and says the free CSV/Excel data is intended for private individuals only, not commercial or data-training products using automated bots, scrapers, or AI: https://football-data.co.uk/data.

The main branch remains public and still lacks `market_anchor_v2_source_rights.py`. Its four live V2 workflows still contain source/quote/archive steps and 90-day artifact uploads. The newer source-rights decision in PR #780 is not on main because #780 is stacked on #727 → #720. Therefore the old main could continue live access while the safer rights stack awaited HUMAN-MERGE.

## New direct-main Draft PR #781

PR: https://github.com/MaksimBlud/football-ai/pull/781

- Branch: `research/v2-workflow-live-access-hold-20261110-run11`.
- Base: `main` at `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Final exact HEAD: `685c314e5429d4d7ae07db452bfa9bdeafd71a0c`.
- Six files changed: four live V2 workflows, the existing Frozen V2 Shadow Tests workflow, and one static workflow-contract test.
- A workflow-level `MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED: "false"` now gates every live source/quote/archive-read step and every associated `upload-artifact` step. Offline regression tests remain enabled.
- Existing schedules are byte-for-byte retained: diagnostic `13 6 * * *`; original forward `8 8 * * *`; current-form source `50 5 * * *`; current-form forward `18 8 * * *`.
- Static tests pin the fail-closed default, all six live-step guards, all four upload guards, and those four cron expressions.

Exact-head GitHub Actions: **7/7 SUCCESS** on `685c314e5429d4d7ae07db452bfa9bdeafd71a0c`:
- Frozen V2 Shadow Tests run 42849762620: **88 passed**, compile PASS, production `.pkl` diff guard PASS.
- Serie A 42849761802; Research 42849761894; Product 42849762163; Bundesliga 42849762161; Ligue 1 42849761770; Eredivisie 42849762354 — all SUCCESS.

These CI runs are offline/synthetic. They made no provider, Supabase, quote, or outcome reads. PR #781 remains Draft / HUMAN-MERGE; it has not been merged.

## Current live-data state

Latest registered original-V2 diagnostic remains run 42837720155 (2026-11-10 14:47 UTC): SUCCESS, but zero saved quotes, zero scored previews, zero prospective predictions, and no eligible prospective cohort. The current-form source/forward pair #42827889788 / #42828048742 verified a source archive and parent run, but also saw zero quotes and captured zero forecasts. The original old-season forward workflow had no new run in the retrieved latest 100-run window; do not dispatch it manually.

Read-only Serie A `public.odds_snapshots` aggregate, restricted to `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= now()`:
- 620 strictly pre-match snapshots across 63 events.
- Latest saved quote timestamp: 2026-10-13 14:48:53 UTC.
- New snapshots/events in the last seven days: 0 / 0.
- Future events with saved pre-match quotes: 0.
No odds values, scores, settlements, or protected target outcomes were selected.

## Integration order and restrictions

- PR #781 is the temporary direct-main hold and should be manually integrated first if the owner chooses to stop current public-main live access immediately.
- Then rebase/revalidate the rights/privacy stack #720 → #727 → #780 and its descendants on fresh main. PR #720 is OPEN/Ready; #727 OPEN/Ready; #780 OPEN/Draft.
- No automatic merge, no main write, no schedule/trigger change, no paid API, no Supabase write/DDL, no protected outcome read, no model refit, no threshold tuning, no betting, and no promotion.
- Original first-outcome-read gate remains 30 completed primary Serie A events; separate current-form evaluation gate remains 30 eligible completed prospective forecasts. Metadata-only feature-input identities do not count as forecasts.

# Continuity correction — 2026-11-10 14:51 UTC — new real runs, independent historical ZIP SHA, zero quote coverage

## Fresh source of truth

- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Repository remains public.
- The main copy of `PROJECT_CONTINUITY.md` still has its last top-level checkpoint dated 2026-10-18. This November journal is on the existing documentation PR #740 branch only.
- No main update, merge, workflow dispatch, schedule edit, or other-agent setting change occurred.

## New real GitHub Actions runs on 2026-11-10

The earlier 12:59 UTC audit correctly found no runs in the then-current listing window. Later runs were registered after that checkpoint; the earlier statement must not be carried forward as a full-day result.

1. **Current-Form Source Capture** — run **42827889788**, scheduled, SUCCESS, 13:48:21–13:49:20 UTC, main SHA above. Artifact **13770560196**, 439,422 bytes, digest `sha256:f29363e28775032937108d102da1dda1ca2d5c1aa0f921cb4518bf3a82e9aec6`, created 13:49:17 UTC, expiry 2027-02-08 13:48:21 UTC.
2. **Current-Form Forward-Only Preview** — run **42828048742**, workflow_run, SUCCESS, 13:49:24–13:50:09 UTC, same main SHA. Artifact **13769184138**, digest `sha256:dc75f076de30584cb74985f4c487612546e5c91f3c521749fa080abf90ce894f`.
3. **Free Real-Quote Diagnostic** — run **42837720155**, scheduled, SUCCESS, 14:47:47–14:48:39 UTC, same main SHA. Artifact **13773563645**, 425,065 bytes, digest `sha256:c04e21994365159382372f8596956dfaf1766c9170285773346778e291b6e823`, created 14:48:35 UTC, expiry 2027-02-08 14:47:47 UTC.

The original V2 Original Forward-Only workflow did not have a new run in the retrieved latest 100-run window. Do not infer why or dispatch it manually.

## Current-form source → forward attestation (metadata/report only)

The Forward-Only artifact JSON was inspected; the nested source ZIP/current-season CSV was not opened or parsed in this audit.

- Source artifact ID: **13770560196**; ZIP digest matches its GitHub artifact metadata.
- Source observation: **2026-11-10 13:49:15.294332 UTC**.
- Source archive creation: **13:49:17 UTC**.
- Authenticated parent run: **42827889788**, main SHA exact, completed **13:49:20 UTC**.
- Forward verification: **13:50:00.398213 UTC**, source age **45 seconds**, status `VERIFIED`, `fresh_for_new_quote=true`.
- The report records 10 historical old-season CSVs plus the current-season file (11 source files), 3,800 historical rows plus 110 current-season prior-day rows, feature-input gate count **110**, and the unchanged candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- `quotes_seen=0`, `rows=[]`, `source_artifacts_used=[]`, `v2_current_form_shadow_captured=0`; no target outcomes read/scored, no Supabase writes, no paid calls, no product publication.

This proves the current-form source artifact and its successful parent run were verified before the forward process. It does **not** prove source-before-quote for an individual quote, because there were zero quotes.

## Independent verification of the 14:47 UTC free diagnostic archive

Downloaded artifact #13773563645 from the existing GitHub run and independently checked the ZIP bytes:

- Computed ZIP SHA-256 exactly matches GitHub artifact digest: `c04e21994365159382372f8596956dfaf1766c9170285773346778e291b6e823`.
- Diagnostic JSON SHA-256: `9d43fbccd8c1241d3a1d532bb518ad2358e2b7ddadec2a4f3f67dae3797acf35`.
- The archive contains the diagnostic JSON and **10 old-season historical CSVs** (1617–2526); all **10/10** CSV byte hashes match the per-file manifest. Manifest reports 380 completed source rows per season, 3,800 total historical rows.
- The diagnostic archive does not contain the current 2026/27 CSV. No 2026/27 score/result rows were opened in this audit.
- Diagnostic fields: `quoted_fixtures=0`, `diagnostic_scored=0`, `diagnostic_previews=[]`, `independently_attested_feature_availability_at_quote=false`, `original_incumbent_asof_prediction_captured=false`, `eligible_for_frozen_prospective_cohort=false`, `history_stale_without_2026_27_form=true`.
- It made **10 public HTTP requests** for the ten historical CSVs; paid provider requests **0**; Supabase writes **0**; `2026_27_public_results_downloaded=false`; model training/promotion false; NO_BET true.

`quotes_with_source_observed_after_quote=0` is vacuous with zero quoted fixtures and is not evidence that a quote passed the source-before-quote gate. No new V2 prediction or prospective observation was created.

## Important live rights/privacy gap demonstrated by the new run

The 14:47 diagnostic run executed on old main. The main copy of `serie_a_v2_live_diagnostic_report.py` still lacks `require_personal_research_inference_scope()`; the main workflow `.github/workflows/serie-a-v2-free-real-quote-diagnostic.yml` still schedules at 06:13 UTC and uploads its artifact with 90-day retention. Thus it performed ten public source GETs and published the diagnostic/raw historical archive after the 2026-11-10 provider-policy recheck.

The existing PR chain is intended to close this, but is **not active on main**:
- #727 adds inference/private-repository preflight before external reads and artifact access.
- #780 changes the current policy manifest to `research_source_capture_permitted=false`, `research_source_capture_scope=NONE_PENDING_PROVIDER_CLARIFICATION`, and `research_inference_permitted=false`; its tests assert rights guards precede external reads in the diagnostic, original forward, current-form forward, current-form source capture, and source-attestation entrypoints.
- Exact #780 HEAD `48f55b6ef4dc40879d5232ac78ce55df51d2dce4` has 2/2 checks SUCCESS; #727 exact HEAD `18a3cfda4e83e44aca1252665d01804267d16467` has 4/4 SUCCESS. Both remain open; #780 is Draft and stacked on #727.
- The current-form source artifact #13770560196 is also an unexpired artifact in the still-public repository. No artifact was deleted. Existing public artifact cleanup remains a separate owner decision.

Do not run or dispatch the old main source workflows again. Do not claim that the PR gates are active until the owner manually integrates them and fresh-main checks prove it. HUMAN-MERGE remains binding.

## Fresh read-only Supabase pre-match inventory

Only `public.odds_snapshots` aggregates were queried, selecting league, counts, distinct event IDs and timestamps, with both `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`. No prices, results, scores, settlements or target outcomes were selected.

- All leagues: **3,915** strictly pre-kickoff snapshots / **327** unique events; **0** snapshots and **0** events in the last seven days; **0** future events with saved strictly pre-kickoff quotes.
- Serie A only: **620** strictly pre-kickoff snapshots / **63** unique events; **0** new in the last seven days.
- Latest Serie A pre-match snapshot: **2026-10-13 14:48:53.042620 UTC**.

Supabase table metadata also reports RLS disabled on five public tables: `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. This is a separate critical security warning. No DDL was run; enabling RLS without first defining appropriate policies can block existing application access.

## Original frozen V2 remains unchanged

Candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original 19 features, weights/scaler/imputer, training fingerprint, `active_lambda=0`, `shadow_lambda=1`, and FAILED stability gate remain unchanged. No new eligible prospective forecasts, Brier/LogLoss evaluation, outcome read, refit, threshold tuning, promotion, production `.pkl` change, paid provider call, Supabase write/DDL, or merge occurred.


# Continuity correction — 2026-11-10 13:02 UTC — Serie A-only quote inventory and existing public artifact retention

## Correctly scoped primary-cohort pre-match inventory

The earlier aggregate of 3,915 snapshots / 327 events is the all-league total, not the original V2 primary-cohort count. A separate read-only query filtered `public.odds_snapshots` to `league='SERIE_A'` and applied both `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`. It selected only aggregate counts, distinct event IDs and the latest timestamp:

- Original V2 primary Serie A cohort: **620 strictly pre-kickoff snapshots across 63 events**.
- New Serie A pre-match snapshots in the last seven days: **0**.
- New Serie A events in the last seven days: **0**.
- Future Serie A events with a saved strictly pre-kickoff quote: **0**.
- Latest Serie A pre-match snapshot: **2026-10-13 14:48:53.042620 UTC**.

The all-league count remains 3,915 / 327, but it must not be reported as the V2 Serie A cohort. No odds prices, scores, settlements, or protected target outcomes were selected.

## Existing main-branch Actions artifacts remain unexpired

Read-only GitHub artifact metadata confirms the last successful main source/forward runs left these artifacts unexpired in the still-public repository:

- Source Capture artifact **13681778268**, SHA-256 `f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101`, expires **2027-02-07 14:25:18 UTC**.
- Free Diagnostic artifact **13689701985**, SHA-256 `c968b357235029c5e96283470d5ac4d40fe1a0647b1d510dbf7270e976db9c4d`, expires **2027-02-07 16:07:28 UTC**.
- Original Forward artifact **13700981366**, expires **2027-02-07 18:40:28 UTC**.
- Current-Form Forward artifact **13700368254**, expires **2027-02-07 18:48:55 UTC**.

The source and diagnostic artifacts were produced by main workflows that upload with 90-day retention. PR #727's private-repository preflight prevents future source-artifact access/uploads when the repository is public; it does not retroactively remove these existing artifacts. PR #780 additionally sets source capture to false under the 2026-11-10 policy recheck. No artifact was downloaded or deleted in this audit. Existing artifact exposure remains a separate privacy cleanup decision for the repository owner.

No Supabase write/DDL, source download, quote request, protected-outcome read, or workflow dispatch occurred.

---

# Continuity update — 2026-11-10 12:59 UTC — repository-wide V2 run audit and main-branch rights/privacy gap

## Repository-wide scheduled-run audit

A read-only GitHub Actions repository run listing was checked for `branch=main`, pages 1 and 2, 100 runs per page, newest first. The returned time ranges were:

- Page 1: 2026-11-10 12:58:29 UTC through 2026-11-10 01:25:31 UTC.
- Page 2: 2026-11-10 01:25:28 UTC through 2026-11-09 19:09:04 UTC.

These pages cover all four 2026-11-10 scheduled windows (05:50, 06:13, 08:08, and 08:18 UTC). No run with any of the four original V2 workflow names was present in either page:

- Serie A V2 Current-Form Source Capture;
- Serie A V2 Free Real-Quote Diagnostic;
- Serie A V2 Original Forward-Only Preview;
- Serie A V2 Current-Form Forward-Only Preview.

The latest matching successful main runs remain on 2026-11-09: Source Capture #42634501531, Free Real-Quote Diagnostic #42651542041, Original Forward-Only #42676083517, and Current-Form Forward-Only #42677383722. This establishes no registered run for the four 2026-11-10 windows; it does not establish why they did not run or that the workflows are disabled. No manual dispatch or schedule change was made.

## Main still lacks the new source-rights/privacy gates

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository visibility is still public.

Direct main-branch content reads returned 404 for both `market_anchor_v2_source_rights.py` and `research/source_rights/football_data_co_uk.json`. The main workflow YAMLs still contain the existing daily schedules and artifact uploads (90-day retention in the inspected source/forward workflows). Thus the rights/privacy preflight code is not yet on main. The current main workflow definitions still expose the old scheduled source path; do not dispatch it, do not infer permission from the absence of a run, and do not claim the new fail-closed controls are active on main.

The four schedules remain untouched. No source CSV was downloaded and no Actions artifact was uploaded in this audit.

## Official provider-page recheck

The official page at https://football-data.co.uk/data displays `Updated: 10/11/26` and says the free data are intended for private individuals only, not commercial or data-training products using automated bots, scrapers, or AI. The conservative project decision in PR #780 remains appropriate: automated source capture and frozen inference stay blocked pending provider clarification or an applicable written licence. This is an internal fail-closed control, not a legal conclusion about every form of manual personal research.

## Exact open-PR evidence

- #720 remains OPEN/Ready for review, exact HEAD `1b9464834dd5256b7d69499c1443378518dde256`; 10/10 exact-head checks SUCCESS.
- #727 remains OPEN/Ready for review, exact HEAD `18a3cfda4e83e44aca1252665d01804267d16467`; current exact check-runs API reports 4/4 SUCCESS. Its workflow tests place rights and private-repository checks before source access and artifact upload.
- #780 remains OPEN/Draft, stacked on #727, exact HEAD `48f55b6ef4dc40879d5232ac78ce55df51d2dce4`; 2/2 exact-head checks SUCCESS (388 tests on each Python version; production `.pkl` guard passed). It sets automated source capture to false under the 2026-11-10 policy recheck.
- #742 remains OPEN/Ready, stacked on #727, exact HEAD `fac462a10509a14c63d7f39abb5614bab756fcae`; 2/2 exact-head checks SUCCESS. Its server-side quote query requires `snapshot_time_utc <= as_of`.
- Direct entrypoint rights-gate chain #774 → #777 → #778 → #779 and parallel #776 remain unmerged; preserve their ancestry and re-run exact CI after parent updates.
- This documentation PR #740 is updated on its existing branch only; no main change or merge is performed.

The staged chain must be manually reviewed/rebased/retargeted with exact-head CI at each step. Do not treat any branch CI as proof that the corresponding protection is active on main.

## Fresh pre-match-only Supabase aggregate

A read-only aggregate over `public.odds_snapshots` applied both `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`, selecting counts, distinct event IDs, and the latest timestamp only:

- Strictly pre-kickoff snapshots: 3,915 across 327 events.
- Strictly pre-kickoff snapshots in the last seven days: 0 across 0 events.
- Future events with a saved strictly pre-kickoff quote: 0.
- Latest strictly pre-kickoff snapshot: 2026-10-13 14:48:53.042620 UTC.

No odds values, match results, scores, settlements, or protected 2026/27 target outcomes were selected. No Supabase writes/DDL occurred.

## Original frozen V2 boundary

The candidate blob remains `ac1303f6b096664983fbf52443bd0a381b23ba21`, candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, protocol blob remains `65729e9639720e67624c1481190aa22ae606f151`, and original feature-builder blob remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`. The 19-feature order, original weights/scaler/imputer, training cutoff, `active_lambda=0`, `shadow_lambda=1`, and FAILED stability gate remain unchanged. No new prospective forecast or Brier/LogLoss result exists; no target outcome was read. The scientific evaluation gate remains closed.

No paid provider request, source download, forecast, Supabase write/DDL, production `.pkl` change, refit, threshold tuning, promotion, bet, merge, main update, schedule change, or other-agent change occurred.

---

# Continuity update — 2026-11-10 06:49 UTC — refreshed Serie A feature-input metadata, no new pre-match quotes

## Read-only feature-input metadata gate

A fresh Supabase SELECT read only `match_date, home_team, away_team` from `public.league_finished_results` for `league='SERIE_A'`, `season='2026-2027'`, and dates before the current UTC date. No score, goal, result, settlement, or outcome columns were selected.

- Raw metadata rows: **113**.
- After the original V2-local `Atalanta BC → Atalanta` alias normalization: **110 unique date/team fixture identities**.
- Three duplicate rows are the same Atalanta fixtures under the two source names; no reversed-orientation duplicate was found in this metadata sample.
- Date range: **2026-08-22 through 2026-11-08**.

This confirms the separate lagged feature-input gate has more than its 30 required completed fixture identities. It is **not** the frozen target-outcome evaluation gate and does not authorize reading outcomes. Eligible completed prospective primary V2 forecasts remain **0/30**; target outcomes remain unread.

## Fresh strict pre-match quote inventory

A separate read-only aggregate selected only counts, event IDs and timestamps from `public.odds_snapshots`, requiring `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`:

- Strictly pre-kickoff snapshots: **3,915** across **327** events.
- New strict pre-match snapshots in the last seven days: **0**.
- Upcoming events with a saved strict pre-match quote: **0**.
- Latest strict pre-match snapshot: **2026-10-13 14:48:53.042620 UTC**.

No new quote or source download was requested. The main daily source schedules are unchanged; this audit does not claim whether the 2026-11-10 05:50/06:13 UTC scheduled runs executed, because the available connected GitHub Actions reads expose known-run jobs but not the repository-wide run listing. Do not infer success or failure without a run ID/log.

## Documentation PR validation

The seven exact-head jobs on documentation commit `8211ba5099780692e47ac2864f59df1e96e40e3a` have all completed SUCCESS: Research #42758625330, Product #42758625381, Serie A #42758625363, Bundesliga #42758625319, Eredivisie #42758625522, Ligue 1 #42758625322, and La Liga #42758625318. The La Liga job is a shared-document path-filter side effect, not V2 runtime/model evidence.

Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; this is documentation-only. No merge, source download, quote read, target-outcome read, Supabase write/DDL, paid provider request, production artifact change, schedule change, or model-contract change occurred. HUMAN-MERGE only.

---

# Continuity update — 2026-11-10 04:52 UTC — fresh main, pre-match availability, rights risk, and exact-head corrections

## Source of truth

- Fresh `main` is still `40887ebb215730190d7a6c7a1693373ec4afcdfc` (branch metadata re-read 2026-11-10 04:48 UTC); no main update or merge occurred.
- The `main` copy of this file is blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b` and its newest top-level checkpoint remains 2026-10-18. This continuity PR branch is the current November journal.
- Repository visibility is still `public`; the `main` branch protection metadata reports protection disabled. HUMAN-MERGE remains an operational instruction; no merge was performed.

## Immediate scheduled-source risk

The four existing main workflows were read again; schedules are unchanged:

- Current-Form Source Capture: `05:50 UTC` daily.
- Free Real-Quote Diagnostic: `06:13 UTC` daily.
- Original V2 Forward-Only Preview: `08:08 UTC` daily.
- Current-Form Forward-Only Preview: `08:18 UTC` daily.

At this audit's 04:52 UTC checkpoint, the next two public-source runs were due at 05:50 and 06:13 UTC. PR #720 remains OPEN, Ready for review, mergeable, at exact HEAD `1b9464834dd5256b7d69499c1443378518dde256` on base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; exact 10/10 checks passed. Its 2026-11-10 03:54 UTC description update records 13 successful automated Football-Data sessions in 2026-11-02 19:08–2026-11-09 19:08 UTC against the provider's stated maximum of two: seven source-capture and six diagnostic sessions, at least eleven over the cap. The failed Nov 8 attempt is excluded. Until #720 is HUMAN-MERGED, main's scheduled workflows do not yet have its shared fail-closed budget/rights gate. Do not dispatch them, alter schedules, or infer provider permission from public access.

PR #727 remains OPEN, Ready for review, at `18a3cfda4e83e44aca1252665d01804267d16467`, stacked on #720. Its exact V2/budget checks passed. It additionally blocks source-artifact access while the repository is public and keeps frozen inference separately unauthorized. The intended sequence remains #720 first, then rebase/revalidate #727 against fresh main.

## Fresh read-only pre-match quote state

A single Supabase read-only aggregate queried only `public.odds_snapshots` rows satisfying both `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`; it selected only counts, event IDs, and timestamps. It did not query results, scores, settlements, or finished-result tables.

- Strictly pre-kickoff snapshots: **3,915**.
- Unique events: **327**.
- Strictly pre-kickoff snapshots in the last seven days: **0**.
- Future events with an already-saved pre-kickoff quote: **0**.
- Latest strictly pre-kickoff snapshot: **2026-10-13 14:48:53.042620 UTC**.

No new source download, quote request, artifact download, or forecast was performed. This does not create any prospective V2 observation.

## New exact-head / integration corrections

- **#762** is still OPEN, Ready for review, based on main, exact HEAD `dc18a149315053818eec20d7e36a74596f899270`. Its distinct two-file change checks the raw source date token before pandas parsing and rejects explicit time/timezone syntax, including `10/10/2026 00:00:00`; a post-parse midnight normalization check alone cannot detect that representation. All seven exact-head PR workflows passed, including Frozen V2 run [#42591737924](https://github.com/MaksimBlud/football-ai/actions/runs/42591737924) with 86 tests and the production `.pkl` diff guard. Its updated PR description correctly says to integrate it after #720/#727 and before rebasing #773.
- **#773** carries #760's separate historical-row integrity deltas on top of #720: finite, nonnegative integer count checks and reversed-fixture duplicate rejection after the frozen V2 alias normalization. Exact HEAD `d13b4bc3f510be47baa2fc9c4d31a3bedc05ab15`, 2 ahead / 0 behind its #720 base, exact run [#42707544006](https://github.com/MaksimBlud/football-ai/actions/runs/42707544006) SUCCESS with 346 tests on both Python 3.11 and 3.12. Do not merge #760 separately; its unique changes are represented in #773. Because #762 and #773 touch the same adapter/test files, rebase/revalidate #773 after #762.
- **#767** remains an independent main-based, non-draft PR at `b173b24600a8db9fc46301ee5b75d2db0159a8dd`, 12 ahead / 0 behind. Exact 7/7 workflows passed; Frozen V2 run [#42650217349](https://github.com/MaksimBlud/football-ai/actions/runs/42650217349) reports 94 tests and the production `.pkl` guard PASS. It rejects both event-ID reuse and duplicate real fixtures split across IDs/reversed Home-Away orientation. It touches `serie_a_v2_forward_capture.py`, also changed by #779; if #767 is integrated first, #779's downstream stack must be rebased and exact-head revalidated.
- **#779**'s PR description was corrected on its existing branch after re-reading the actual PR metadata, compare, and job logs. Current HEAD is `6002e823e08438c1109aac6374629cf713d97324`, parent #778 HEAD `b2a034614d999683a8c334569dc07eb07b7ac589`, compare 10 ahead / 0 behind, seven intended files. Exact run [#42734842832](https://github.com/MaksimBlud/football-ai/actions/runs/42734842832) is 2/2 SUCCESS: 411 passed on Python 3.11 and 411 on Python 3.12; Python 3.12 pip check and both production-artifact guards passed. It remains Draft and HUMAN-MERGE only.
- **#772** exact HEAD `46025507677dcafa5b42421d5b79a52ff76d6c5a` has 428 passed on Python 3.11 and 428 on Python 3.12 in exact run [#42737911980](https://github.com/MaksimBlud/football-ai/actions/runs/42737911980). #776/#777/#778/#779 remain a rights-gated direct-call chain; preserve their parent order and revalidate descendants after any parent integration. These are offline contract tests, not live authorization or inference.

## Frozen original V2 boundary

The candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with the original 19-feature order, original weights/scaler/imputer, `active_lambda=0` market fallback and `shadow_lambda=1` research-only. Provider-issued inference permission remains unresolved/false; repository privacy still blocks private source archival. Stability gate remains FAILED. Eligible completed prospective primary events remain **0/30**. No Brier/LogLoss superiority claim is supported.

## Safety for this update

No main change/merge, schedule or other-agent change, source/quote download, artifact download, target-outcome read, paid provider call, Supabase write/DDL, production `.pkl` change, refit, threshold tuning, promotion, or bet occurred. The only Supabase operation was the strictly pre-kickoff aggregate above. HUMAN-MERGE remains mandatory.

---

# Continuity correction — 2026-11-10 02:51 UTC — actual Nov 9 V2 workflow runs and merge-ready identity guard

This section supersedes the earlier 2026-11-09 23:59 UTC sentence claiming that no Original V2 Forward, Current-Form Source Capture, Current-Form Forward, or Free Real-Quote Diagnostic run occurred on Nov 9. That statement was incorrect: exact main-branch workflow runs and their job logs were re-read.

## Actual successful main runs (all on main SHA 40887ebb215730190d7a6c7a1693373ec4afcdfc)

- **Current-Form Source Capture** run [#42634501531](https://github.com/MaksimBlud/football-ai/actions/runs/42634501531), 2026-11-09 14:25 UTC: SUCCESS. Log summary: feature-input gate 100; 110 current-season prior-day rows; 10 historical plus 1 current-season source file; 3,910 total historical/current-form rows; candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; target outcomes not scored; paid calls 0; Supabase writes 0. Artifact #13681778268 SHA-256 `f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101`.
- **Free Real-Quote Diagnostic** run [#42651542041](https://github.com/MaksimBlud/football-ai/actions/runs/42651542041), 2026-11-09 16:07 UTC: SUCCESS. Its report mode was `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`; paid requests 0; Supabase writes 0. Artifact #13689701985 SHA-256 `c968b357235029c5e96283470d5ac4d40fe1a0647b1d510dbf7270e976db9c4d`.
- **Original V2 Forward-Only Preview** run [#42676083517](https://github.com/MaksimBlud/football-ai/actions/runs/42676083517), 2026-11-09 18:40 UTC: SUCCESS. It independently verified the diagnostic source artifact #13689701985 and SHA, 3,800 historical rows across 10 pre-prospective files; `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`, shadow previews 0, paid calls 0, Supabase writes 0. Mode `SOURCE_ARCHIVE_ONLY_NO_PREDICTION_NO_BET`. Output artifact #13700981366 SHA-256 `e6f625a9dad6e7351ae08c38a45f80412266c08c8d2a55769d18d86f73faef37`.
- **Current-Form Forward-Only Preview** run [#42677383722](https://github.com/MaksimBlud/football-ai/actions/runs/42677383722), 2026-11-09 18:48 UTC: SUCCESS. It verified source artifact #13681778268 and its SHA; source parent run #42634501531 completed before the source artifact. It saw `quotes_seen=0`, captured 0 current-form shadows, kept `target_outcome_evaluation_gate_open=false`, `target_outcomes_read=false`, `target_outcomes_scored=false`, paid calls 0, and Supabase writes 0. Mode `READ_ONLY_PREKICKOFF_SHADOW_NO_BET`. Output artifact #13700368254 SHA-256 `25b1b327b47f0ebfa0eb75a258604427e785eaa86eafc80a6fdc40907b4847c8`.

All four job logs and artifact metadata were read; artifact bytes were not downloaded/opened. These runs establish source/runtime plumbing only, **not** a prospective V2 prediction or model-quality evidence. The 100-event feature-input gate is separate from the closed 30-completed-prospective-event outcome-evaluation gate.

## Public artifact and upcoming source-workflow risk

GitHub repository metadata still reports `visibility=public`. The Nov 9 source and diagnostic workflows uploaded artifacts while the #720/#727 rights/budget/private-storage stack remained unmerged. SHA proves integrity, not confidentiality; these artifacts are visible to repository readers. No artifact bytes were downloaded in this audit.

The main source workflows remain scheduled (unchanged): Current-Form Source Capture 05:50 UTC and Free Real-Quote Diagnostic 06:13 UTC daily. The next scheduled windows are 2026-11-10 05:50 and 06:13 UTC. Do not change schedules or dispatch workflows. The safe resolution is the existing HUMAN-MERGE rights/privacy/budget stack, not another source run:
- #720 HEAD `1b9464834dd5256b7d69499c1443378518dde256`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, 118 ahead / 0 behind; its exact PR checks are successful.
- #727 HEAD `18a3cfda4e83e44aca1252665d01804267d16467`, based on exact #720 HEAD; 49 ahead / 0 behind; exact V2/budget checks are successful. Its own description says merge #720 first, then retarget/revalidate #727 against fresh main. Do not merge a stale child base or assume #727 is already on main.

## Newly verified independent merge candidate

PR [#767](https://github.com/MaksimBlud/football-ai/pull/767), `b173b24600a8db9fc46301ee5b75d2db0159a8dd`, is based directly on current main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`, 12 ahead / 0 behind, `mergeable=true`, non-draft, and exact-head **7/7 workflows SUCCESS**. The Frozen V2 job reports 94 tests passed and production `.pkl` diff guard PASS. It rejects both (a) one provider event ID reused for conflicting fixtures and (b) one fixture split across multiple event IDs, including reversed Home/Away orientation and V2-local alias/case/whitespace duplicates. It also rejects stale quotes before source-parent/archive access. Original features/weights/lambdas remain unchanged. HUMAN-MERGE only; this is ready for manual review/merge, not merged here.

## Current direct-rights stack snapshot

- #772 HEAD `46025507677dcafa5b42421d5b79a52ff76d6c5a`, based on #727 exact HEAD, 28 ahead / 0 behind; exact run [#42737911980](https://github.com/MaksimBlud/football-ai/actions/runs/42737911980) SUCCESS, Python 3.11 428 passed and Python 3.12 428 passed, pip/compile/production artifact guards PASS. It enforces source-only rights, private storage and exact current-run download reservation inside the importable historical downloader before filesystem/network access. Draft until the parent rights stack is integrated.
- #776 exact-head CI remains green (391/391 on Python 3.11 and 3.12); #777 exact-head CI green (391/391); #778 exact-head CI green (405/405 plus dedicated Market Anchor V2 validation); #779 exact-head CI green (411/411). These are stacked Draft PRs; preserve their parent order and do not merge out of sequence.
- #775 remains on the divergent #770 ancestry; successful tests do not make that stack integration-safe.

## Fresh read-only pre-match quote aggregate

Query used only `public.odds_snapshots` fields `event_id`, `snapshot_time_utc`, and `commence_time_utc`, with `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`. Result: 3,915 eligible snapshots, 327 events, latest snapshot 2026-10-13 14:48:53 UTC, 0 eligible snapshots in the last 7 days, 0 future events with saved pre-match quotes. No score/result/settlement data were queried; no Supabase writes/DDL.

## Frozen model and safety

Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features and original weights unchanged; `active_lambda=0` remains market fallback and `shadow_lambda=1` research-only. No inference license, no eligible prospective quotes, no target-outcome reads, and evaluation remains 0/30. Stability gate remains FAILED. No production `.pkl` change, refit, threshold tuning, promotion, bet, paid API call, Supabase write/DDL, main update, merge, schedule change, or other-agent setting change occurred.

---

## 2026-11-09 23:59 UTC — direct shadow API gate, exact CI, and fresh live-state recheck

- Source of truth re-read: public repository MaksimBlud/football-ai, exact main SHA 40887ebb215730190d7a6c7a1693373ec4afcdfc. Main has not changed in this cycle. Main PROJECT_CONTINUITY.md is still the older October 18 checkpoint; this section is being added only to this documentation PR branch.
- New PR #777 (fix(v2): gate direct shadow scoring on inference rights) HEAD 12a64174341f8d3716c1206ee63d4f4c01ca817d, base exact #774 HEAD f4180d8ce4142096f7a2ad1cd86ba95c78b3ae30, 8 ahead / 0 behind. It enforces require_personal_research_inference_scope() inside the public shadow_preview() function before candidate loading or iteration of market/feature inputs. The test explicitly proves denial occurs before either access. Synthetic offline tests stub only the rights function with SYNTHETIC_TEST_ONLY; this is not a live grant.
- Exact PR #777 Actions run 42724727467 completed SUCCESS: Python 3.11 391 passed, Python 3.12 391 passed, pip check clean, compile PASS, production .pkl diff guard PASS. Initial run 42724610802 failed because one existing feature-manifest test lacked the synthetic-only fixture; that fixture was added, and the final exact-head run above is green.
- The unique direct shadow_preview() fix from stale/diverged #743 was ported to #777. #743 compares to #742 as 12 ahead / 50 behind and is not integration-safe; a superseded warning was posted on #743. #777 is the clean isolated replacement for that direct scoring guard.
- Current direct-rights stack remains open and unmerged: #720 (10/10 checks), #727 (4/4), #742 (2/2), #753 (2/2), #772 (4 successful check-runs across two identical runs), #773 (2/2), #774 (4 successful check-runs across two identical runs), #776 (4 successful check-runs across two identical runs), and #777 (2/2). #775 has 2 successful check-runs but is stacked on #770's divergent ancestry; do not integrate it until its unique clock guard is ported onto a clean chain.
- #777 is Draft and stacked on #774; #774 depends on #742 → #727 → #720. No PR was merged and main was not changed.
- Fresh read-only Supabase aggregate on public.odds_snapshots used only league, event_id, snapshot_time_utc, and commence_time_utc, with strict snapshot_time_utc < commence_time_utc and snapshot_time_utc <= now(). It still returns 3,915 pre-match snapshots across 327 events, and 0 future events with saved quotes. Latest Serie A quote remains 2026-10-13 14:48:53 UTC; no new snapshots appeared.
- GitHub Actions main-run audit for 2026-11-09 found no run of the Original V2 Forward-Only Preview, Current-Form Source Capture, Current-Form Forward Preview, or Free Real-Quote Diagnostic workflows. Their main YAML schedules remain 08:08, 05:50, 08:18, and 06:13 UTC respectively. The only V2-named run in the Nov 9 main run page was the unrelated Multi-Market V2 Cycle at 22:40 UTC. Do not dispatch paid workflows or alter schedules; investigate only if a future safe read identifies a disabled workflow or repository setting.
- Rights manifest on the #727 branch still says provider_issued_ai_inference_license=false, research_inference_permitted=false, and scope NONE_PENDING_SCOPE_CLARIFICATION; authorization=null. Source-only private archival is not an inference grant. The repository remains public. Thus no real source artifact was opened, no real V2 inference/feature scoring was performed, and the new API guard correctly blocks live inference pending explicit provider-issued clearance or a separately licensed source.
- Original candidate SHA remains a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6; 19 features, active lambda 0 / market fallback, shadow lambda 1 research-only, stability gate FAILED, target-outcome read gate 0/30. No protected outcomes were read.
- This cycle: Supabase writes/DDL 0; paid provider calls 0; source downloads 0; production .pkl changes 0; model refits/promotions 0; betting actions 0; schedule changes 0; other-agent changes 0.

# Continuity update — 2026-11-09 20:06 UTC — exact ancestry audit, direct downloader gate, pre-match quote state

## Source of truth and frozen contract

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository visibility was re-read from GitHub metadata and is **public**.
- The main candidate remains pinned to artifact SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with the original 19 features and 20×2 weight matrix unchanged.
- The main protocol still specifies `active_lambda=0` / `MARKET_FALLBACK`, `shadow_residual_lambda=1`, `stability_gate_passed=false`, and a first target-outcome read gate of **30 completed primary Serie A events**. Before that gate, no target outcomes may be read. The gate is diagnostic only; it is not a promotion gate. Betting and automatic promotion remain disabled.
- No model inference, fitting, refit, candidate write, or target-outcome read was performed in this audit.

## Read-only pre-match quote audit

A single aggregate read used only `public.odds_snapshots` and only rows satisfying `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`. No results, scores, settlements, or finished-results tables were queried.

| League | Strictly pre-match snapshots | Events | Latest saved snapshot (UTC) | Future events with saved quotes |
|---|---:|---:|---|---:|
| Bundesliga | 394 | 35 | 2026-09-11 15:49:52 | 0 |
| EPL | 1,135 | 70 | 2026-10-09 15:25:57 | 0 |
| Eredivisie | 410 | 39 | 2026-09-11 15:50:20 | 0 |
| La Liga | 798 | 52 | 2026-09-11 15:45:28 | 0 |
| Ligue 1 | 387 | 35 | 2026-09-11 15:49:24 | 0 |
| Primeira Liga | 9 | 9 | 2026-09-11 16:06:24 | 0 |
| RPL | 153 | 15 | 2026-09-05 15:07:55 | 0 |
| Serie A | 620 | 63 | 2026-10-13 14:48:53 | 0 |
| Turkey Super Lig | 9 | 9 | 2026-09-11 16:06:26 | 0 |
| **Total** | **3,915** | **327** | — | **0** |

There are no future fixtures with a saved pre-kickoff quote in any of these leagues. The latest Serie A quote remains 2026-10-13 14:48:53 UTC. Do not trigger source downloads or paid odds calls to compensate.

## Fresh main workflow and artifact audit (metadata/logs only)

The four relevant main-branch workflows were re-read. Their current schedules and public artifact retention remain:

- Original forward preview: daily `08:08 UTC`; 90-day artifact retention.
- Current-form source capture: daily `05:50 UTC`; 90-day artifact retention.
- Free real-quote diagnostic: daily `06:13 UTC`; 90-day artifact retention.
- Current-form forward preview: daily `08:18 UTC`; 90-day artifact retention.

No schedule was changed. These are free research workflows; no paid odds request was made.

Exact main run logs and artifact metadata were re-read without downloading any artifact:

| Workflow run | Actual logged result | Artifact metadata |
|---|---|---|
| #42634501531 — current-form source capture | SUCCESS; candidate SHA matches frozen V2; feature-input gate 100; 110 current-season completed prior-day rows; 10 historical + 1 current-season source file; `target_outcomes_scored=false`; paid calls 0; Supabase writes 0 | #13681778268, 439,419 bytes, expires 2027-02-07 |
| #42651542041 — free real-quote diagnostic | SUCCESS; paid provider requests 0; Supabase writes 0 | #13689701985, 425,067 bytes, expires 2027-02-07 |
| #42676083517 — original V2 forward preview | SUCCESS; source archive SHA verified; 3,800 historical rows / 10 pre-prospective files; `quotes_seen=0`; `future_quotes_checked=0`; forecasts 0; shadow previews 0; paid calls 0; Supabase writes 0 | #13700981366, 1,460 bytes, expires 2027-02-07 |
| #42677383722 — current-form forward preview | SUCCESS; source #13681778268 verified against SHA-256 `f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101`; 3,910 historical rows; 110 current-season rows; feature-input gate 100; source age 15,793 seconds; `quotes_seen=0`; shadow captures 0; `target_outcome_evaluation_gate_open=false`; `target_outcomes_read=false`; paid calls 0; writes 0 | #13700368254, 440,605 bytes, expires 2027-02-07 |

All four jobs completed SUCCESS, but none produced a V2 forecast. The current-form source run's 100-event feature-input gate is distinct from the protocol's 30-primary-event target-outcome evaluation gate. The forward preview explicitly confirms the latter remains closed and no target outcomes were read. Do not count these runs as prospective forecasts or model-quality evidence.

**Public-storage blocker remains real:** GitHub confirms the repository visibility is `public`, while the current main workflows still upload source/diagnostic artifacts with 90-day retention and do not yet contain the #720/#727 rights/privacy gates. Artifact contents were not downloaded or opened. The #720/#727 stack must reach main and the repository must be private before any further source-artifact access is allowed.

## Provider scope and privacy

- The official Football-Data fair-use page says free CSV/Excel data are intended for private individuals' personal betting and/or academic research, with manual access or at most two light automated download sessions per week; it excludes commercial and AI data-training projects. It does not explicitly resolve this project's frozen-model inference scope. Treat inference as unresolved and fail closed; do not infer a licence from public availability.
- The #720 manifest keeps `research_inference_permitted=false`, `ai_model_training_permitted=false`, `commercial_use_permitted=false`, and `public_product_use_permitted=false`. The separate #727 scope is private, noncommercial source archival/validation only; it does not authorize inference or training.
- Because the repository is still public, the #727 private-artifact gate must block source artifact access. Do not change repository visibility or provider scope automatically.
- Official policy reference: https://football-data.co.uk/contact.php.

## Exact ancestry audit — do not integrate stale/diverged stacks

The following commit comparisons were run against the exact PR HEADs, not inferred from PR base labels:

**Clean current rights/quote chain**
- #720 HEAD `1b9464834dd5256b7d69499c1443378518dde256` → #727 HEAD `18a3cfda4e83e44aca1252665d01804267d16467`: **49 ahead / 0 behind**.
- #727 → #742 HEAD `fac462a10509a14c63d7f39abb5614bab756fcae`: **1 ahead / 0 behind**.
- #742 → #753 HEAD `a3f8cb4e8d4447f15eaed3fb283c1e7670e944f0`: **1 ahead / 0 behind**.
- These are the only currently verified source-rights/private-storage/quote-cutoff stack in this group. #720 and #727 each have their exact V2/budget workflow runs successful; #742 and #753 exact-head Python 3.11/3.12 jobs are successful.

**Diverged/stale chains — CI success does not make these integration-safe**
- #742 → #743 is **12 ahead / 50 behind** and diverged; #743 is not mergeable. #744 → #745 → #746 are each clean descendants of their immediate parent, but inherit the broken #743 ancestry. #768 is also a clean descendant of #743, so its successful direct-quote-reader CI does not repair the missing #727 private-storage base.
- #727 → #728 is **1 ahead / 4 behind** and diverged. #729 → #730 → #731 → #732 → #769 → #770 are clean descendants of their immediate parents, but inherit #728's stale base and must not be integrated until rebuilt/rebased on current #727.
- #769 and #770's direct-reader tests are useful regression evidence, but their current ancestry is not a safe merge path.
- #767 is a separate main-based original-forward identity guard; its exact-head workflow runs are successful and it does not depend on the diverged #743/#728 stacks.

## Direct historical-source downloader gap and corrected PR

A new static audit found that `serie_a_v2_live_diagnostic_report.fetch_public_history()` was publicly importable and performed Football-Data HTTP requests / optional directory creation without enforcing the CLI's inference-rights and private-storage preflights. The CLI-only guard was insufficient.

- PR #771 was opened on the wrong #746 stack. Its exact CI correctly failed at `py_compile` because that diverged branch did not contain `market_anchor_v2_artifact_privacy.py`. #771 was closed unmerged as superseded; do not revive it.
- PR #772 rebuilds the same narrow fix on the verified #727 HEAD. It enforces inference rights first, then private repository storage, before directory creation or HTTP. Two tests prove both denials stop before filesystem/network side effects.
- #772 current HEAD is `64efe827263c96aa176af5145fe7ae261ccdabe2`, base #727 exact HEAD `18a3cfda4e83e44aca1252665d01804267d16467`; comparison is **5 ahead / 0 behind**.
- Its first exact run #42689292661 exposed two expected source-loader pin regressions (388 passed, 2 failed): the two forward modules still pinned the previous loader blob. Both constants were updated to the new loader blob SHA-1 `6bc51aa2551765c06862cd9bb39a425c85f3b67a`.
- Exact-head rerun #42689630724 completed **SUCCESS** on `64efe827263c96aa176af5145fe7ae261ccdabe2`: Python 3.11 **390 passed**, Python 3.12 **390 passed**, pip check clean, compile PASS, and production `.pkl` diff guard PASS. Both new fail-before-filesystem/network regressions passed. #772 remains Draft because its verified base #727 is not yet merged; this is offline/synthetic safety evidence, not live inference or model-quality evidence.

## Safety for this audit

No source files were downloaded; the only Supabase operation was the pre-match quote aggregate above. No Supabase writes/DDL, paid API calls, target-outcome reads, production `.pkl` changes, main changes, merges, schedule changes, or other-agent changes occurred. HUMAN-MERGE remains mandatory.

---

# Continuity update — 2026-11-09 16:08 UTC — frozen V2 direct-API and refit audit

## Main-code finding

A fresh read of main `market_anchor_1x2_v2_shadow.py` confirms that the current main branch still exposes the original V2 numerical functions and the old `fit_candidate_artifact` / `write_candidate_artifact` implementations. They were not invoked. The candidate JSON itself remains unchanged at SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.

## Open direct-API/refit hardening stack

The following exact heads were re-read; each has both its dedicated Market Anchor V2 validation workflow and the Serie A Frozen V2 Shadow Tests workflow SUCCESS, with the production `.pkl` diff guard passing:

- #748 `34be143c9460c5214791c6c15e092708fe08ef3d`: direct `predict_shadow_residual` now checks unresolved provider inference rights before residual logits; **360 V2 tests PASS**.
- #749 `66d09810f4239486452d4014e6e7da03c066459b`: direct `predict_candidate` has the same rights guard; **361 V2 tests PASS**.
- #750 `ff22e4605637b05c46415a8153d261608bfab54a`: direct residual-logit helper is rights-gated and candidate refit/write APIs fail closed; **363 V2 tests PASS**.
- #751 `afa38aff86fdb60b5a9104f17a82633f954f9e1d`: removes re-exported V1 fit/prepare helpers and the training fingerprint from the V2 namespace; **364 V2 tests PASS**.
- #754 `55b120afdbfe06885e7e4323a4932d337565e074`: removes unreachable writer statements after the fail-closed stub; **365 V2 tests PASS**.

All five remain Draft and stacked in order; none is merged. Keep the stack intact and revalidate exact heads after each parent/base change. Until these changes reach main, the original V2 module still contains direct APIs and refit helper bodies, even though no refit or inference was performed in this cycle.

## Safety

No inference, fitting, refit, artifact write, production `.pkl` change, Supabase write/DDL, paid API call, source download, protected target-outcome read, promotion, bet, or main update occurred. This is static/API-contract hardening evidence only, not model-quality evidence.

---

# Continuity update — 2026-11-09 16:05 UTC — rights, privacy, quote and original-forward workflow audit

## Provider policy versus current source cadence

The official Football-Data fair-use page now says it was updated **2026-11-09** and limits free CSV/Excel use to personal/academic research via manual download or light automated download **at most twice per week**. It says commercial or AI data-training projects with heavy automated requests are not intended uses and unapproved requests should be treated as not granted: https://football-data.co.uk/contact.php.

Main's current-form source workflow still has its daily `50 5 * * *` schedule. Today's main run #42634501531 downloaded 10 historical CSVs plus the current-season CSV (11 source files). This daily cadence is not compatible with the provider's twice-weekly automated-download limit unless the shared budget gate prevents most scheduled downloads. Do not change the schedule in this research task; prioritize the already-open #720 budget/rights guard and do not manually trigger another source download.

## Source rights / private artifact stack — exact heads

- PR #720 exact HEAD `1b9464834dd5256b7d69499c1443378518dde256`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`: **9/9 workflows SUCCESS**. Frozen V2 suite: **342 PASS** under Python 3.11 and **342 PASS** under Python 3.12; pip check and production `.pkl` diff guard PASS. It includes the source-rights fail-closed path and shared free-download budget cap of two per rolling seven days.
- PR #727 exact HEAD `18a3cfda4e83e44aca1252665d01804267d16467`, stacked on #720: **3/3 workflows SUCCESS**. Frozen V2 suite: **388 PASS** under Python 3.11 and **388 PASS** under Python 3.12; pip check and production `.pkl` diff guard PASS. It adds private-artifact storage gating and read-only quote preflight. Repository is still public, so the gate must block source artifact access until privacy is actually resolved.
- A fresh branch comparison confirms #727 still has the fail-open missing-response-URL fallback `getattr(response, "url", url)`. The separate #753 fix uses `getattr(response, "url", None)`, but #753 exact HEAD `40d4980b76834a17a0c455945a9d16809a48d980` is based on stale #727 base `8894ce8e0248a5502d60571ff073fc6d7847a43a`; its V2 workflow passes **385 tests** under both Python versions. Rebase/reapply this delta onto the current #727 HEAD before integration; it is not yet in #727 or #759.

## Quote and original-forward workflow guards

- PR #742 exact HEAD `727b4456fb103557039c3daac09bcaf93bcd36fa`, stacked on #720: its V2 workflow passes **342 tests** under Python 3.11 and Python 3.12, with production `.pkl` diff guard PASS. It adds a server-side `snapshot_time_utc <= as_of` filter to the saved-quote query, so future-dated snapshots are not even read and then discarded in Python. It remains open/Ready, dependent on #720.
- Fresh main read of `.github/workflows/serie-a-v2-forward-preview.yml` shows a daily 08:08 UTC original-forward reader, a paid-snapshot `workflow_run` wake-up restricted to manually dispatched successful upstream runs, and 90-day public Actions artifact retention. Main does not yet have the source-rights/private-storage preflight.
- PR #739 adds the original-forward source-rights/private-storage preflight and transitive dependency triggers, but its exact workflow test command omitted a shell continuation after `tests/test_serie_a_v2_current_form_dependency_triggers.py`; later rights/privacy tests would not be passed to pytest. PR #752 fixes that exact continuation. #739 exact head `8dc0f4bc7d7057d98bd5dc40386c888bcf124106` and #752 exact head `9b86cff7985f569016081367b8c3657e9d798213` each have their Original V2 Live Runner Rights Gate Validation workflow SUCCESS; #752 is still Draft and stacked on #739.
- #681/#691/#696 are separate ready dependency-trigger audits. They must be compared/ordered carefully rather than merged as duplicates; their exact heads each have 7/7 PR CI SUCCESS.

## Current status

- Original old-season forward identity consolidation: #767 exact HEAD `b173b24600a8db9fc46301ee5b75d2db0159a8dd`, 7/7 CI SUCCESS, 94 V2 tests PASS; #677 is Draft/superseded.
- Current-form identity: #676 exact HEAD `0de1f60bea9e7d879ab6f4c543bde66f32eb3d44`, 7/7 CI SUCCESS, 91 V2 tests PASS; #766 is Draft/superseded.
- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. No PR was merged; no schedule or agent setting changed.

---

# Continuity update — 2026-11-09 16:00 UTC — Original V2 forward identity and live source refresh

## Fresh main / frozen candidate

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository visibility is still **public**.
- Frozen candidate file Git blob: `ac1303f6b096664983fbf52443bd0a381b23ba21`; embedded artifact SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- The candidate remains 19 original features, 3,799 training rows through 2026-06-30, `active_lambda=0`, `shadow_residual_lambda=1`, stability gate FAILED, refit/promotion disabled. Protocol blob remains `65729e9639720e67624c1481190aa22ae606f151`.
- No legacy XGBoost model is used.

## Original old-season forward identity consolidation — PR #767

PR [#767](https://github.com/MaksimBlud/football-ai/pull/767) is now the consolidated original-forward identity PR, based on fresh main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, exact HEAD `b173b24600a8db9fc46301ee5b75d2db0159a8dd`.

- Includes the validated #677 protections: real UTC-offset clock, event_id-to-fixture guard, and stale-quote guard.
- Adds the missing reverse fixture-to-event-ID guard, using the unordered canonical team pair plus exact kickoff so a reversed Home/Away duplicate cannot inflate the prospective event count.
- Normalizes whitespace/case and the existing Serie A runtime aliases plus the frozen V2-local Atalanta BC → Atalanta alias only for identity comparison; quote labels, features and probabilities remain unchanged.
- Adds regressions for exact duplicate fixture IDs, alias/case/whitespace duplicates, reversed Home/Away duplicates, and event-ID whitespace normalization; each fails before source archive or parent-run callbacks.
- Exact-head CI: **7/7 SUCCESS**. Original V2 Shadow Tests run **94 PASS**; production `.pkl` diff guard PASS. Exact run IDs: #42650217349 (V2), #42650217337 (Research), #42650217535 (Serie A), #42650217329 (Bundesliga), #42650217428 (Eredivisie), #42650217419 (Ligue 1), #42650217346 (Product).
- PR #677 was moved to Draft/superseded by #767; it remains unmerged. #767 remains open for HUMAN-MERGE; no main change.

## Avoiding a weaker duplicate in current-form identity work

- PR #676 already contains a stronger current-form `_latest_quotes` guard than the newly-created #766: event_id-to-fixture AND fixture-to-event_id checks, V2-local alias normalization, and UTC-offset clock validation.
- #676 exact HEAD `0de1f60bea9e7d879ab6f4c543bde66f32eb3d44` has 7/7 CI; its V2 job log shows **91 PASS** and the production `.pkl` diff guard PASS.
- PR #766 was therefore moved to Draft and annotated as superseded by #676; no merge occurred. Do not integrate #766 separately.

## Latest real source / forward runtime — 2026-11-09

- Current-form source run [#42634501531](https://github.com/MaksimBlud/football-ai/actions/runs/42634501531) SUCCESS on main. Feature-input gate count: **100** after V2-local alias normalization; only date/team identity metadata was used for this gate. It archived 10 old-season CSVs plus the current-season CSV, **3,910** historical rows and **110** completed prior-day current-season rows. Source artifact ID **13681778268**, GitHub artifact SHA-256 `f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101`.
- Current-form forward run [#42634693506](https://github.com/MaksimBlud/football-ai/actions/runs/42634693506) SUCCESS. It independently verified the real artifact ZIP SHA and successful main parent run; source age at verification **47 seconds**. However, **quotes_seen=0** and **v2_current_form_shadow_captured=0**. No saved future pre-kickoff quote was available, so this proves source attestation/runtime only, not a quote-level source-before-quote prediction.
- Forward artifact ID **13682418549**, SHA-256 `51afce059c43a33b9751fd308196cf33f4dd661344eefaa6d809c9f5b529bd5a`.
- Target outcomes read/scored: false. Evaluation gate remains **0/30**. Paid calls 0; Supabase writes 0.

## Fresh read-only Supabase inventory

- Strict pre-match aggregate used only `odds_snapshots` with `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= now()`.
- All leagues: **3,915** snapshots / **327** events; zero snapshots in the last seven days; zero upcoming events with a saved strict pre-match quote.
- Serie A: **620** snapshots / **63** events; latest `2026-10-13 14:48:53.042620+00`; zero in the last seven days; zero future events with a saved quote.
- Metadata-only Serie A 2026/27 feature-input query returned **103** raw unique fixture identities (22 Aug–2 Nov); V2 alias-normalized gate count is **100**. No score/result fields were selected.
- No target outcome, score, settlement or protected 2026/27 result was read.

## Separate Supabase security finding

Supabase Security Advisor reports RLS disabled (CRITICAL) on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No remediation was run because enabling RLS without approved policies can block legitimate access; this is a separate owner decision. No Supabase writes/DDL were performed.

## Safety

No main update, Supabase writes/DDL, paid provider calls, production `.pkl` changes, refit, weight/feature/lambda changes, target-outcome reads, bets, threshold tuning, promotion, or schedule changes occurred. All PRs remain HUMAN-MERGE only.

---

# Continuity update — 2026-11-09 09:16 UTC — Research Brain follow-up

This update follows a fresh default-branch commit search, current V2 policy/candidate reads, open-PR and exact-head CI checks, and read-only Supabase queries restricted to already-observed pre-kickoff quote metadata and completed-fixture identities. It updates this documentation PR branch only; main and runtime are unchanged.

## Fresh main and frozen original V2

- Latest default-branch commit remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` is still the older 2026-10-18 entry.
- Original candidate file still embeds SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Candidate remains 3,799 training rows through 2026-06-30, exact 19 original features/weights/scaler/imputer, `active_lambda=0`, `shadow_residual_lambda=1`, stability gate FAILED, refit disabled, automatic promotion false.
- No legacy XGBoost model is used or restored.

## Follow-up source-date finding — PR #762

A direct review of PR #760 found that checking only whether the parsed date equals its midnight normalization does not reject an explicit timestamp exactly at midnight (for example `10/10/2026 00:00:00`). PR [#762](https://github.com/MaksimBlud/football-ai/pull/762) adds a raw-source clock/timezone syntax check before pandas parsing and a regression for this exact midnight case.

- Exact HEAD: `dc18a149315053818eec20d7e36a74596f899270`; base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- All 7 PR workflows completed SUCCESS on that exact HEAD.
- Frozen V2 shadow suite: **86 passed**; production `.pkl` diff guard PASS.
- Runs: #42591737924 (V2), #42591737957 (Product), #42591738012 (Bundesliga), #42591737811 (Eredivisie), #42591738033 (Research), #42591737820 (Ligue 1), #42591737945 (Serie A).
- PR #762 is open, Ready for review, mergeable, HUMAN-MERGE only. It changes only historical date-source validation and its test; no feature values or model parameters.
- A temporary stacked draft #761 was closed as superseded by #762; it was never merged.

PR #760 remains independently open/ready at exact HEAD `8f4837fbd9a4b403252b3c6618a58e7fa0fbabca`, with 7/7 exact-head CI and 89 V2 tests. PR #740 itself remains open/ready at exact HEAD `4e27d76b2e60f1ad944f5a5a3484ff5ff2e4e845`, 7/7 CI. None of these PRs is merged.

## Fresh read-only Supabase pre-match inventory — 2026-11-09 09:10 UTC

The aggregate selected only `odds_snapshots` timestamps, league, and event identity; it did not select odds prices or any outcome fields. Admission required `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= now()`.

- All leagues: **3,915** strictly pre-kickoff snapshots across the same 327 event identities; **0** new strict pre-match snapshots in the last seven days; **0** upcoming events with an already-saved strict pre-match quote.
- Serie A: **620** strictly pre-kickoff snapshots / **63** event IDs; latest snapshot `2026-10-13 14:48:53.042620+00`; zero in the last seven days; zero upcoming events with a saved pre-match quote.
- Identity-only `SERIE_A` 2026-2027 query selected only distinct `season, match_date, home_team, away_team`: **103** unique fixture identities. This supports the separate lagged-feature-input gate only; no score/result fields were selected.
- The target-outcome evaluation gate remains **0/30**. No protected 2026/27 result, score, goal, settlement, or target outcome was read.
- The latest independently verified current-form source capture/forward runtime remains the November 8 evidence recorded below; no later successful run ID was independently established in this pass, so no new capture or forecast is claimed.

## Official Football-Data fair-use policy rechecked

The provider's official contact page was updated **2026-11-06**: https://football-data.co.uk/contact.php. It limits free CSV/Excel use to private individuals' personal betting or academic research, via manual download or light automated download (maximum twice per week). It says free data is not intended for commercial or AI data-training projects involving heavy repeated automated downloads, and requests for permission for those uses should be assumed not granted.

This does not expressly settle the project's frozen-inference/public-product rights. The internal rights gate therefore remains fail-closed; no inference permission is inferred from the free-data availability or the download-frequency allowance. The official policy finding was recorded as a comment on PR #720. No CSV was downloaded for this policy check.

## Safety

No main update, Supabase writes/DDL, source download, odds-provider request, production `.pkl` change, model refit, feature/weight/lambda change, schedule change, threshold tuning, protected-outcome read, bet, promotion, or publication occurred. This is provenance/contract/CI work, not evidence that V2 beats the market.

---

# Continuity update — 2026-11-09 — Research Brain run 11 follow-up

This update follows a fresh read of `main`, the open V2 PR stack, exact-head GitHub Actions runs, the frozen candidate/policies, and a read-only Supabase query restricted to already-observed pre-kickoff Serie A quote rows. It updates this documentation PR only; no main/runtime/data changes are made here.

## Frozen original V2 baseline

- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; the default-branch commit search confirms no newer main commit.
- Original candidate file remains `research/models/market_anchor_v2_serie_a_frozen_candidate.json`; its embedded SHA-256 is `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Candidate metadata remains: 3,799 training rows through `2026-06-30T23:59:59Z`, exact 19-feature order, original weights/scaler/imputer, `active_lambda=0`, `shadow_residual_lambda=1`, stability gate FAILED, refit disabled, automatic promotion false.
- No legacy XGBoost model is loaded or used. The market remains the active lambda-zero baseline; the lambda-one residual remains research-only.

## New historical-source integrity finding — PR #760

A direct audit of `serie_a_v2_asof_feature_manifest.py` found three malformed-history cases that could pass the original source validator:

1. A same-date duplicate fixture with home/away reversed could evade the ordered duplicate key, including after the local `Atalanta BC -> Atalanta` alias.
2. The code declared a date-only historical source but accepted a time-bearing, timezone-naive `Date`; differing timestamps on one calendar day could bypass date-level fixture identity checks.
3. Historical goals/corners/cards rejected missing and negative values but accepted fractional counts and positive infinity after numeric conversion.

PR [#760](https://github.com/MaksimBlud/football-ai/pull/760) now:
- rejects same-date duplicate unordered canonical team pairs;
- rejects any historical date with a non-midnight time component or timezone;
- requires goals, corners and cards to be finite, nonnegative integer counts;
- preserves the exact original feature builder, feature order, candidate SHA, weights, scaler/imputer and lambda semantics.

Final exact HEAD: `8f4837fbd9a4b403252b3c6618a58e7fa0fbabca`.

All 7 PR workflows passed on that exact SHA:
- Serie A Frozen V2 Shadow Tests run #42576204390: **89 passed**, compile PASS, production `.pkl` diff guard PASS.
- Serie A #42576204400, Research #42576204455, Product #42576204393, Bundesliga #42576204404, Eredivisie #42576204391, and Ligue 1 #42576204398: all SUCCESS.

Two intermediate heads failed only in regression/test-fixture assertions; those were corrected, and the final exact head above is the one with 7/7 success. This is source-contract/code validation using synthetic fixtures, not validation against a downloaded real archive, not live inference, and not model-quality evidence. PR #760 is open, ready for review, mergeable, and HUMAN-MERGE only.

## Current pre-match data availability

A new read-only SQL aggregate selected only rows satisfying `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= now()`, restricted to `league='SERIE_A'`:

- 620 strictly pre-kickoff snapshots across 63 event IDs.
- Latest observed pre-kickoff snapshot: `2026-10-13 14:48:53.04262+00`.
- New observed pre-kickoff snapshots in the last 7 days: 0.
- Upcoming events with an already-observed pre-kickoff quote: 0.

No result, score, goal, settlement, or outcome columns were selected. No Supabase write or DDL was performed.

The last independently verified current-form source capture remains run #42479299556, artifact #13617155063, ZIP SHA-256 `5395ff50d5e312f395b4f76e9cdf63fcb2a71ab831e07fd24cb3418602ad3af6`: 10 historical CSVs / 3,900 matches plus one current-season CSV / 100 prior-day completed rows; 100 canonical identities passed the feature-input gate. The last verified current-form forward run #42493688915 re-attested the artifact/parent but found zero quotes and zero V2 shadows. The old-season forward run #42492484513 also found zero quotes and zero previews.

The 100-event feature-input gate is not the evaluation gate. Eligible prospective V2 forecasts remain **0/30**. No protected 2026/27 outcomes have been read.

## Rights, privacy and evaluation blockers remain binding

- Repository visibility is still PUBLIC. The existing source artifact SHA proves integrity, not confidentiality. Do not download or open the public artifact as part of this run.
- Source-only archival rights and frozen-model inference rights remain separate. The current internal rights manifest conservatively blocks inference; no provider-issued AI inference permission has been evidenced.
- PR #720 (source rights / free-download budget), #727 (private storage / quote preflight), #742 (server-side observed-quote cutoff), and #753 (exact privacy-response URL) remain open in their dependency chain. Their exact heads/checks were re-read; none is merged into main.
- The market-only evaluator in the open #728 stack preserves the 30-eligible-completed-forecast gate and always leaves `review_signal=false`; the full three-way review remains blocked because the preregistered incumbent is unpinned. The legacy XGBoost comparator is explicitly not to be revived or substituted.
- The supplementary market-only Brier/LogLoss diagnostic can only run after 30 eligible prospective forecasts complete. No outcome callback has been invoked.

No model weights, protocol, thresholds, production artifacts, Supabase data/schema, workflows, schedules, main branch, or other agents were changed. No paid API calls, bets, target-outcome reads, automatic promotion, or product publication occurred.

---

## Continuity follow-up — PR #755 mandatory source SHA preflight

A fresh audit of PR #731's direct live market-only runner found that its `preflight` callback was optional. The supported GitHub bridge supplied the source-artifact verifier, but a direct import could omit it and still reach the 30-forecast outcome reader. This left a gap in the required source-before-quote/SHA proof.

- New Draft PR **#755**: require preflight in both live market-only entrypoints, pass an immutable snapshot of forecast rows, require the verifier to return an artifact-ID -> SHA-256 map, and reject any selected forecast row whose source artifact ID/SHA is not covered before the lazy outcome reader can be reached.
- The real bridge now returns the verified map from the existing GitHub artifact, parent-run, and embedded-ZIP verification. The 30-primary-identity and 30-eligible-completed-forecast gates are unchanged.
- Exact final HEAD: `ae0ffbbe6347729050d4e1d849d6b38d3f861b8e`, based on PR #731 exact HEAD `2f4c9a7849c64db4d11d6e29b99239d9ed0c1a58`.
- Exact-head push run #42528057658: SUCCESS; 47 passed, Python compilation passed, production-`.pkl` guard passed.
- Exact-head PR run #42528062571: SUCCESS; 47 passed, Python compilation passed, production-`.pkl` guard passed.
- The initial head `bf717c3e7de1d1408864516fa8c9bc61457a97c5` had one stale two-argument synthetic callback in a workflow test; it failed, was corrected in the next commit, and is superseded by the passing final HEAD above.
- PR #755 remains Draft/open and mergeable; HUMAN-MERGE only after #731 and its predecessors. No main merge occurred.

This is offline/synthetic gate hardening, not live inference, not a source download, and not evidence of model quality. No protected outcomes, paid calls, Supabase writes/DDL, production `.pkl` changes, or model-weight/contract changes occurred.

---

# Continuity update — 2026-11-08 — Research Brain run 11 final exact-head audit

This addendum is based on fresh GitHub main/PR reads, exact GitHub Actions job logs, and read-only Supabase metadata/odds aggregates. It updates this existing documentation PR only; it does not change main or any runtime behavior.

## Baseline and frozen V2

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; `PROJECT_CONTINUITY.md` on main is still the older 2026-10-18 entry. This PR #740 is still open and is the only continuity update branch being maintained.
- Frozen candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 3,799 training rows through 2026-06-30; original 19-feature order and original weights/scaler/imputer unchanged.
- `active_lambda=0`; `shadow_lambda=1` research-only; stability gate FAILED; automatic promotion false.

## New exact-head direct-inference / freeze PRs

All listed PRs remain open and are not active on main. Their checks are offline/synthetic CI, not live inference or model-quality evidence.

- **#746** — guard the public 19-feature manifest builder and standalone CLI before candidate/history/quote access. Exact HEAD `80e226a14bde226afad2711d10b5c589e8c7c388`; run #42500360760 SUCCESS, 349 passed under Python 3.11 and 3.12.
- **#748** — guard direct `predict_shadow_residual()`. Exact HEAD `34be143c9460c5214791c6c15e092708fe08ef3d`; runs #42500942392 and #42500942428 SUCCESS; 11 targeted tests and 360 frozen-V2 tests under each Python version.
- **#749** — guard direct `predict_candidate()` before residual weights/features are read. Exact HEAD `66d09810f4239486452d4014e6e7da03c066459b`; runs #42501779681 and #42501779789 SUCCESS; 12 targeted tests and 361 frozen-V2 tests under each Python version.
- **#750** — guard direct `_artifact_residual_logits()` and disable direct refit/write APIs. Exact HEAD `6487283044c231cf678f770293a452b560f509df`; runs #42501979671 and #42501979740 SUCCESS; 14 targeted tests and 363 frozen-V2 tests under each Python version.
- **#751** — remove V1 fitting/preparation helper re-exports from the V2 namespace and remove the dormant refit implementation/fingerprint helper. Its exact base for #754 is `afa38aff86fdb60b5a9104f17a82633f954f9e1d`.
- **#752** — repair the original-forward workflow's missing shell continuation so rights/privacy test paths are actual pytest arguments. Exact HEAD `9b86cff7985f569016081367b8c3657e9d798213`; push and PR runs #42512766311/#42512771879 SUCCESS, 330 passed in each run. Stacked on #739.
- **#753** — fail closed if the GitHub privacy response has no exact `url`. Exact HEAD `40d4980b76834a17a0c455945a9d16809a48d980`; run #42517796143 SUCCESS, 385 passed under Python 3.11 and 3.12. Stacked on #727.
- **#754** — remove unreachable writer statements after the frozen-artifact `PermissionError` and add an AST regression proving both refit/write functions contain only the fail-closed stub. Exact HEAD `55b120afdbfe06885e7e4323a4932d337565e074`; runs #42523164631/#42523164731 SUCCESS, 16 targeted tests and 365 frozen-V2 tests under each Python version; `pip check` and production-`.pkl` diff guards passed. Stacked on #751.

The #742–#745 quote/inference stack already recorded above remains separate and based on #720. Preserve HUMAN-MERGE and rebase/revalidate every dependent stack on fresh main after its manual predecessors; no merge or main update occurred.

## Latest verified runtime and source-before-quote state

- Current-form Source Capture run #42479299556 (2026-11-08 12:14 UTC) succeeded. It passed the metadata-only feature-input gate at 100 canonical unique completed fixtures, captured 10 historical CSVs / 3,900 matches plus one current 2026/27 CSV / 100 completed prior-day rows (11 files total), with zero paid calls and zero Supabase writes.
- Source artifact #13617155063, ZIP SHA-256 `5395ff50d5e312f395b4f76e9cdf63fcb2a71ab831e07fd24cb3418602ad3af6`.
- Current-form Forward run #42493688915 (2026-11-08 15:13 UTC) re-verified that exact artifact SHA and successful parent run; source age at verification was 10,706 seconds. It found `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, and `target_outcomes_scored=false`; no paid calls or production/Supabase writes.
- Original old-season Forward run #42492484513 (2026-11-08 14:59 UTC) passed 71 tests, verified 3,800 historical matches / 10 old-season files, but found `future_quotes_checked=0`, `quotes_seen=0`, and zero diagnostic previews. It did not generate a forecast.
- Source-before-quote provenance is verified for the source archive and parent workflow; no actual quote existed, so no source-before-quote forecast pair was created.

## Fresh read-only Supabase aggregates

- `public.odds_snapshots`: 3,966 total rows; 3,915 strictly pre-kickoff; 51 at/after kickoff.
- Strictly pre-kickoff rows in the last seven days: 0. Future events with a saved strictly pre-kickoff quote: 0.
- Latest Serie A strictly pre-kickoff quote remains 2026-10-13 14:48:53 UTC.
- Metadata-only `public.league_finished_results` query for `SERIE_A` / `2026-2027`, selecting only distinct `match_date,home_team,away_team`, returned 103 identities from 2026-08-22 through 2026-11-02. Source-capture canonicalization/alias handling yielded 100 identities at its 2026-11-08 run. Neither count is the prospective forecast cohort.
- Prospective eligible forecasts remain 0/30. No target outcome/result/score fields were selected in this audit.

## Rights, privacy, and security blockers

- The current official Football-Data page states that the free data are intended for private individuals and not commercial or AI data-training products using automated bots/scrapers/AI. It does not expressly resolve the narrow frozen-model inference scope. The repository manifest conservatively records `research_inference_permitted=false`, `provider_issued_ai_inference_license=false`, and `authorization=null`; this is an internal fail-closed interpretation, not a claim that the page explicitly bans every form of noncommercial inference.
- Repository visibility remains public. The November 8 source/forward artifacts were uploaded by current main before the private-storage PRs; SHA proves integrity, not confidentiality. Do not initiate more source capture until the rights/privacy gates are integrated and the owner has resolved repository privacy.
- Supabase advisory remains: RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No DDL was run; enabling RLS without designed policies may break application access.

## Binding conclusion

The frozen candidate and code contracts are intact, and the offline CI coverage has expanded. There is still no qualifying fresh pre-kickoff quote, no prospective V2 forecast, no 30/30 completed forecast gate, and no Brier/LogLoss evidence. Do not claim V2 beats the market. No target outcomes, paid provider calls, Supabase writes/DDL, production `.pkl` changes, schedule changes, auto-promotion, or main merges occurred in this update.

---

# Football AI — Project Continuity

## 2026-11-08 — Current main, real forward runs, and unresolved rights/privacy gates

This operational entry supersedes the 2026-10-18 “runtime proof pending” status for the checks below. It does **not** change the frozen model, original protocol, source-rights interpretation, or evaluation embargo.

### Exact baseline and frozen model

- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc` (commit dated 2026-10-18 08:20:05 UTC).
- Repository visibility is still **public**.
- Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original feature contract remains 19 features; `active_lambda=0` (market), `shadow_residual_lambda=1` (research only), stability gate FAILED, automatic promotion false.
- No original weights, feature definitions, production `.pkl`, or Supabase schema/data were changed.

### Real current-form source and forward runs on 2026-11-08

**Source capture:** [GitHub Actions run 42479299556](https://github.com/MaksimBlud/football-ai/actions/runs/42479299556), scheduled main run, SUCCESS.

- Feature-input gate: 100 canonical unique completed fixture identities.
- The read-only gate query selects only `match_date,home_team,away_team`; no score/result fields.
- A separate metadata-only audit returned 103 rows / 103 raw fixture triples for Serie A 2026/27 from 2026-08-22 through 2026-11-02. The source code canonicalizes configured team aliases before counting, producing the 100 unique identities reported by the run.
- Captured 10 frozen historical CSVs / 3,900 historical matches plus one 2026/27 CSV with 100 completed prior-day rows; 11 files total.
- Source artifact ID `13617155063`, created `2026-11-08T12:15:16Z`, size 438,211 bytes, GitHub SHA-256 `5395ff50d5e312f395b4f76e9cdf63fcb2a71ab831e07fd24cb3418602ad3af6`.

**Current-form forward preview:** [GitHub Actions run 42479367957](https://github.com/MaksimBlud/football-ai/actions/runs/42479367957), SUCCESS.

- Verified the exact source artifact ID/SHA, parent workflow ID/HEAD, and source observation time before quote admission.
- Source was 43 seconds old at verification and marked fresh for a future quote.
- `quotes_seen=0`; `v2_current_form_shadow_captured=0`.
- `target_outcomes_read=false`; `target_outcomes_scored=false`; no paid calls; no Supabase writes.
- Forward artifact ID `13616738214`, SHA-256 `ba3cb97f0e3c51fd7f82e243d4a4e67118622e1e7154f1c02d975d89554fa5c8`.

**Original old-season forward:** [GitHub Actions run 42383500443](https://github.com/MaksimBlud/football-ai/actions/runs/42383500443), 2026-11-07 14:50:47 UTC, SUCCESS.

- 71 regression tests passed.
- Real source attestation verified 10 historical CSVs / 3,800 matches.
- `quotes_seen=0`; `future_quotes_checked=0`; `v2_diagnostic_previews_captured=0`; no paid calls; no Supabase writes.
- Forward artifact ID `13578712079`, SHA-256 `143b0699bc1d3c5d00e5cde4107068e03775032919024bf0a30a2e48aa074859`.

### Read-only Supabase pre-match audit (2026-11-08)

Only `public.odds_snapshots` fields needed for timing/market inventory were aggregated. Rows with `snapshot_time_utc >= commence_time_utc` were excluded.

- Serie A strictly pre-kickoff snapshots: **620** across **63** event IDs.
- Latest saved Serie A pre-kickoff snapshot: **2026-10-13 14:48:53 UTC**.
- New strictly pre-kickoff Serie A snapshots in the last 7 days: **0**.
- Future events with a strictly pre-kickoff saved quote: **0**.

This is the immediate data blocker: source history is available, but no new qualifying market quotes exist. No outcomes/score columns were selected in this audit.

### Rights and confidentiality are still blocking live inference

- The official Football-Data data page currently says the free files are intended for private individuals and not commercial or data-training products using automated bots/scrapers/AI: https://football-data.co.uk/data
- The branch rights manifest records source-only private noncommercial archival/validation as the narrow scope; it explicitly leaves frozen-model inference, AI training, commercial use, and public product use unapproved. Frozen inference must remain blocked pending explicit scope clarification or a separately licensed source.
- The repository is still public. The 2026-11-08 source and forward artifacts above were uploaded by the current main workflows before the privacy-gate PRs were merged. Their digests prove integrity, **not confidentiality**. The artifacts were not downloaded or opened in this audit.
- PRs #720/#727 and the stacked privacy/rights fixes remain unmerged. Do not treat their protections as active on main. Do not change repository visibility/settings from this research task; private storage requires owner action.
- Main forward workflows still install floating package versions. The version-pinned `requirements-v2-research-py312.lock` and its workflow adoption exist in the open #720/#727 branch stack, not current main.

### PR and CI state checked 2026-11-08

- #720 — Ready; source/inference rights and bounded free download gate.
- #727 — Ready; integrated private-storage gate and fail-closed quote preflight.
- #728–#738 — open stacked research/rights/privacy PRs; #738 head `9cc3c676f53e298c1378b29770eebde68ec19abc`.
- **#739 — new Draft**, stacked on exact #738 HEAD. It adds the missing transitive source-capture-rights dependencies/tests to the original forward workflow trigger and regression contract. Exact HEAD `8dc0f4bc7d7057d98bd5dc40386c888bcf124106`; PR CI [run 42484153504](https://github.com/MaksimBlud/football-ai/actions/runs/42484153504) and push CI [run 42484148786](https://github.com/MaksimBlud/football-ai/actions/runs/42484148786) both SUCCESS; **329 tests passed**, production pickle diff guard passed. It is not merged.
- #696 and #698 remain separate open workflow-dependency audit PRs; inspect their exact heads before any future merge decision to avoid duplicating their coverage.

The required HUMAN-MERGE order for the stacked rights/privacy chain is #720 → #727 → #728 → #729 → #730 → #731 → #732 → #733 → #734 → #735 → #736 → #737 → #738 → #739. No PR was merged and main was not changed.

### Scientific gate status and next safe steps

- The 100-event feature-input gate is **not** the prospective outcome-evaluation gate.
- The 30-eligible-completed-prospective-forecast outcome gate remains CLOSED. The 2026-11-08 forward run read/scored no target outcomes.
- No eligible prospective V2-vs-market Brier/LogLoss comparison exists; no superiority claim is justified.
- Next: owner manually integrates the rights/privacy chain in order and resolves repository privacy; obtain written provider clarification for frozen inference (or an applicable explicit licence); then wait for genuinely new strictly pre-kickoff saved quotes after a verified source archive; capture the unchanged 19-feature V2 shadow prospectively; only after the preregistered 30-forecast completion gate may the independent evaluator read target outcomes.

No paid The Odds API calls, paid cron, production writes, Supabase writes/DDL, model refit, threshold tuning, promotion, or protected target-outcome reads were performed in this iteration.


## 2026-11-08 — additional original V2 quote and direct-inference gates (Research Brain run 11)

This addendum records the next exact-head code audits after the November 8 runtime snapshot above. All PRs below remain open/unmerged and are **not active on main**. Current main/base remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository visibility remains public.

### Frozen candidate reconfirmed

- Candidate file: `research/models/market_anchor_v2_serie_a_frozen_candidate.json`; Git blob SHA-1 `ac1303f6b096664983fbf52443bd0a381b23ba21`.
- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Training rows: 3,799; training data through 2026-06-30.
- Exact original 19-feature order, 20×2 weights, 19 imputer medians and 19-element scaler parameters remain unchanged.
- `active_lambda=0`; `shadow_residual_lambda=1`; stability gate FAILED; automatic promotion false; no 2026/27 target outcomes used for fit/selection.
- Protocol still requires 30 completed primary forecasts before any protected target-outcome read. Current eligible prospective forecasts: 0/30. No Brier/LogLoss comparison or superiority claim exists.

### New exact-head PRs and regression evidence

**PR #742 — server-side strictly pre-match quote cutoff**

- Head `727b4456fb103557039c3daac09bcaf93bcd36fa`, based on PR #720 head `1b9464834dd5256b7d69499c1443378518dde256`.
- The shared saved-quote query now requires both `commence_time_utc > as_of` and `snapshot_time_utc <= as_of` before returning rows. Since kickoff is strictly after the same cutoff, every returned quote is strictly pre-kickoff and already observed. Projection remains explicit; no `SELECT *`.
- Frozen V2 Shadow Tests [run #42492038152](https://github.com/MaksimBlud/football-ai/actions/runs/42492038152): SUCCESS; Python 3.11 and 3.12 each **342 passed**; production `.pkl` guard PASS.
- This is query-contract regression evidence, not a live Supabase inference run.

**PR #743 — inference rights enforced inside the public `shadow_preview()` API**

- Head `e468da0e54a935dbf5f3c114f2f0d7cff793c0c5`, stacked on #742.
- A direct import could previously call the scoring function without going through the CLI's rights preflight. The function now checks frozen-inference scope before loading the candidate or iterating quote/features.
- [Run #42497538837](https://github.com/MaksimBlud/football-ai/actions/runs/42497538837): SUCCESS; Python 3.11 and 3.12 each **343 passed**; production `.pkl` guard PASS.

**PR #744 — inference rights enforced inside both forward preparation APIs**

- Head `62fa017799cf052511adbce66128a1aa56fb5aa4`, stacked on #743.
- Both original and current-form `prepare_forward_capture()` functions now check rights before iterating quote/archive metadata, invoking parent/archive callbacks, creating output directories, loading ZIPs or building features.
- Direct-call regressions prove denied rights block before input iteration/callbacks/output.
- [Run #42498077784](https://github.com/MaksimBlud/football-ai/actions/runs/42498077784): SUCCESS; Python 3.11 and 3.12 each **345 passed**; production `.pkl` guard PASS.

**PR #745 — inference rights enforced inside the diagnostic `make_report()` API**

- Head `8ec091091a1ba8838166dcfcf5c36f978a997e52`, stacked on #744.
- Direct callers could previously build the 19-feature manifest before reaching the guarded shadow scorer. `make_report()` now checks rights before source-embargo inspection, quote-time iteration and feature construction.
- PR #736 already covers the separate direct `fetch_public_history()` source-only/private-storage downloader; #745 does not duplicate that work.
- [Run #42498338407](https://github.com/MaksimBlud/football-ai/actions/runs/42498338407): SUCCESS; Python 3.11 and 3.12 each **346 passed**; production `.pkl` guard PASS.

PRs #743 → #745 are a dependent stack on #742; #742 is based on #720. They require fresh-main rebase and exact CI after the #720/#727 rights/privacy integration. No PR in this stack is merged.

**Existing original-forward dependency checks**

- PR #739 head `8dc0f4bc7d7057d98bd5dc40386c888bcf124106`, offline rights-validation run #42484153504: SUCCESS, **329 passed**, production `.pkl` guard PASS.
- PR #741 head `93827b4442a65ef683631dd74fa517f6b4dc0c9e`, offline rights-validation run #42487475354: SUCCESS, **329 passed**, production `.pkl` guard PASS. This is not a live Original Forward source/quote/inference run.
- #718 is closed/superseded by #720. Open #705/#699 are superseded/reference-only; do not merge them separately because #720 carries the consolidated shared download budget plus the refreshed rights gate.
- #720 is Ready on main; #727 is Ready on #720. #728–#741 form the downstream privacy/forward/evaluator stack. #742–#745 are a separate quote/inference-gate stack based on #720. HUMAN-MERGE only.

### Latest read-only pre-match data and runtime

- The 2026-11-08 source capture [run #42479299556](https://github.com/MaksimBlud/football-ai/actions/runs/42479299556) succeeded: 10 historical CSVs / 3,900 matches plus one current-season CSV / 100 completed prior-day rows; 11 files total; feature-input gate 100; zero paid calls and zero Supabase writes.
- Source artifact ID `13617155063`; ZIP SHA-256 `5395ff50d5e312f395b4f76e9cdf63fcb2a71ab831e07fd24cb3418602ad3af6`.
- Current-form forward [run #42479367957](https://github.com/MaksimBlud/football-ai/actions/runs/42479367957) verified the exact source artifact SHA, parent run and source observation time (43 seconds old), but `quotes_seen=0`, `v2_current_form_shadow_captured=0`; no target outcomes read/scored.
- Free diagnostic [run #42484124054](https://github.com/MaksimBlud/football-ai/actions/runs/42484124054) passed its 53 offline tests and public-only/no-paid preflight, then failed on a 30-second HTTPS ReadTimeout from `www.football-data.co.uk`; no diagnostic JSON/artifact was produced.
- Read-only `odds_snapshots` aggregate at 2026-11-08 approximately 15:47 UTC: Serie A 625 total rows, 620 strictly pre-kickoff across 63 events, latest strictly pre-kickoff snapshot 2026-10-13 14:48:53 UTC; zero new strictly pre-kickoff rows in seven days and zero future events with an already-saved pre-kickoff quote. The same seven-day new-pre-match count was zero for every other tracked league. No score/result columns were selected.
- Therefore there is still no live quote to score and no new prospective V2 forecast.

### Binding rights/privacy and Supabase security blockers

- The repository is public. November 8 Actions artifacts were uploaded by current main before the private-storage PR stack was integrated. Their SHA proves integrity, not confidentiality; ZIPs were not downloaded/opened.
- The Football-Data rights manifest still has `authorization=null`, `provider_issued_ai_inference_license=false`, and `research_inference_scope=NONE_PENDING_SCOPE_CLARIFICATION`. The new rights tests are synthetic only; they do not grant permission or execute live inference.
- Supabase read-only schema advisory: RLS is disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No DDL was run. Enabling RLS without designed policies can block the application; handle separately with owner review.
- No source/quote writes, Supabase writes/DDL, paid provider calls, protected outcome reads, model refit, threshold tuning, production `.pkl` changes, promotion, schedule changes or main updates occurred in this run.




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


---

# Continuity follow-up — 2026-11-09 11:59 UTC — feature-gate identity guard and fresh pre-match audit

This addendum records only new, independently re-read evidence. It updates this existing documentation PR branch, not `main`.

## Fresh main and exact V2 state

- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- The main-branch `PROJECT_CONTINUITY.md` still has only the older 2026-10-18 top-level entry; this PR #740 branch remains the maintained current continuity update.
- Frozen original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 3,799 training rows through 2026-06-30; exact original 19 features/weights/scaler/imputer; `active_lambda=0`, `shadow_lambda=1); stability gate FAILED; refit and automatic promotion disabled.

## New PR #765 — reversed duplicate identities in the feature-input gate

PR [#765](https://github.com/MaksimBlud/football-ai/pull/765) adds a fail-closed check to `count_unique_completed_primary_events()`:

- canonicalize V2-local team aliases first;
- key fixtures by date plus unordered team pair to detect the same match represented once as Home/Away and once reversed;
- reject a reversed duplicate instead of counting it as another completed primary event;
- retain exact alias duplicates as one fixture;
- the gate continues to inspect only `match_date, home_team, away_team`, never scores/results.

Exact HEAD: `9752541e35b850c2f8d69f0fb4894ce98addeec6`; parent `65ed4131f1b5ee00713c5c421cee1dc1d3565919`; base `main` `40887ebb215730190d7a6c7a1693373ec4afcdfc`.

All 7 exact-head PR workflows completed SUCCESS:
- Frozen V2 Shadow Tests #42612781599 — **87 passed**; production candidate/hash guard passed.
- Research #42612781507, Serie A #42612781460, Ligue 1 #42612781438, Product #42612781168, Bundesliga #42612781314, Eredivisie #42612781299 — all SUCCESS.

PR #765 remains Draft/open. It is a defensive contract guard, not evidence of a currently observed reversed duplicate. Do not merge it ahead of the overlapping strict-date/source-row work: PRs #763, #764 and #765 are all based on the same current main and must be integrated one at a time, with remaining branches refreshed and exact-head CI rerun after each manual merge.

## Fresh read-only identity check

The read-only Serie A 2026-2027 query selected only identity metadata. After the same V2-local `Atalanta BC -> Atalanta` normalization:

- raw identity rows: **103**;
- canonical ordered identities: **100**;
- canonical unordered pair identities: **100**;
- reversed-orientation excess: **0**;
- date range: **2026-08-22 through 2026-11-02**.

Thus the new reversed-pair guard did not discover an existing reversed duplicate in the current rows; it prevents future metadata corruption from inflating the 30-fixture feature-input gate. The 100 canonical identities satisfy only the lagged-feature input gate. The separate target-outcome evaluation gate remains **0/30**.

## Exact-head status of adjacent source validation PRs

- PR #763 — `0adc9b9441a8b4066d0a08c4a29773b0fe7993a1`: 7/7 exact-head workflows SUCCESS.
- PR #764 — `52b21e39d65c1de36864220c7e9ab825780dbe3d`: 7/7 exact-head workflows SUCCESS.
- PR #765 — `9752541e35b850c2f8d69f0fb4894ce98addeec6`: 7/7 exact-head workflows SUCCESS.

All remain open; none is merged. Preserve HUMAN-MERGE. Because the PRs overlap in the source-capture validation area, do not treat the independent CI passes as proof that their unrebased branches are mutually mergeable.

## Fresh source-before-quote runtime and saved-market availability

Re-read the exact main workflow logs:

- Source capture run [#42479299556](https://github.com/MaksimBlud/football-ai/actions/runs/42479299556), 2026-11-08 12:14 UTC, SUCCESS. It created artifact **13617155063**, ZIP SHA-256 `5395ff50d5e312f395b4f76e9cdf63fcb2a71ab831e07fd24cb3418602ad3af6`, with 10 historical CSVs / 3,900 historical matches plus one current-season source CSV / 100 lagged rows. Parent run and artifact timestamps were authenticated.
- Current-form forward run [#42493688915](https://github.com/MaksimBlud/football-ai/actions/runs/42493688915), 2026-11-08 15:13 UTC, SUCCESS; **53 tests passed**. It re-verified the real artifact and parent run, but `quotes_seen=0`, `v2_current_form_shadow_captured=0`; target outcomes read/scored false; paid calls and Supabase writes zero.
- Original old-season forward run [#42492484513](https://github.com/MaksimBlud/football-ai/actions/runs/42492484513), 2026-11-08 14:59 UTC, SUCCESS; **71 tests passed**, source ZIP verified, but zero future quotes and zero previews.
- No newer current-form source-capture or forward-preview run was found in the latest 100 main scheduled runs. No new source download or workflow dispatch was initiated in this pass.

Fresh read-only Supabase aggregate on `public.odds_snapshots` admitted only `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= now()`:

- **3,915** strict pre-kickoff snapshots across **327** event IDs;
- **0** snapshots in the last seven days;
- **0** future events with a saved strict pre-kickoff quote;
- Serie A: **620** snapshots / **63** events; latest `2026-10-13 14:48:53.042620+00`.

No odds prices or outcome columns were selected. No target outcomes were read.

## Binding conclusion and safety

The source archive and parent provenance are genuinely verified, but there is no new quote to pair with that archive and no new V2 shadow forecast. The feature-input count is not the outcome-evaluation gate. There is still no admissible 30/30 prospective cohort and no independent Brier/LogLoss evidence; no claim that V2 beats the market is justified.

The provider-rights/private-storage chain (#720/#727 and dependent protections) remains open; the public repository/artifact boundary and unresolved frozen-inference permission remain blockers. Do not initiate further source capture or inference until the applicable rights/privacy gates are resolved.

No main merge/update, Supabase write/DDL, paid API request, protected target-outcome read, model refit, candidate/weight/feature/lambda change, production `.pkl` change, schedule change, bet, publication, or promotion occurred in this addendum.


---

# Integration overlap audit — 2026-11-09 12:56 UTC

A direct comparison of the exact #720 branch source and its regression tests against open #763–#765 found that the current merge plan should avoid duplicating guards already present in the consolidated rights branch.

## What #720 already contains

PR #720 exact HEAD remains `1b9464834dd5256b7d69499c1443378518dde256`, based on main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Its nine associated PR workflow runs are all completed SUCCESS, including the dual-Python frozen-V2 suite (342 tests under Python 3.11 and 3.12) and the 24-test shared download-budget suite.

On that exact branch, `serie_a_v2_current_form_source_capture.py` and its tests already:
- canonicalize the V2-local Atalanta alias and reject reversed same-date fixture pairs in both the metadata feature-input gate and the downloaded current-season CSV;
- deduplicate exact alias-equivalent metadata identities;
- require current-season goal/corner/card counts to be nonnegative integers;
- test both reversed-duplicate cases and exact alias deduplication;
- require a real UTC offset for source-gate, capture, observation and archive clocks;
- pin the approved current-season HTTPS URL, disable redirects, stream the response with a hard byte bound, and verify current-source fixture coverage against the metadata gate.

These are already in #720's diff/tests and should not be reimplemented by separately merging overlapping PRs.

## Incremental status of #763–#765 against #720

- **#763 is still materially incremental.** #720's `_primary_event_metadata_identity()` currently converts a `datetime` object to `.date()`. #763 explicitly rejects datetime/timestamp objects and requires canonical full-string `YYYY-MM-DD`. Preserve this stricter date-only metadata rule when rebasing after #720.
- **#764 is partially overlapping.** #720 already rejects non-integer counts and reversed duplicate rows. #764's distinct addition is checking the raw CSV date cells for time/offset syntax *before* Pandas can normalize them; retain that pre-parse date-only guard (and its explicit finite-number assertion) if it remains absent after rebase.
- **#765 is functionally superseded by #720.** The same V2-local alias-normalized reversed-pair rejection is already implemented in #720's `count_unique_completed_primary_events()` and `_primary_event_identities()`, with dedicated tests for the counter, identity reader, and current CSV. The #720 tests also already prove exact Atalanta alias duplicates collapse to one identity. Do not merge #765 independently unless a post-rebase diff reveals genuinely new coverage not present in #720.

All #763, #764 and #765 heads remain based on the unchanged main rather than #720. Their standalone CI passes do not establish compatibility with #720. After HUMAN-MERGE of #720, re-read the new main, rebase only the unique #763/#764 protections, inspect exact diffs, and rerun exact-head CI. Keep #765 Draft/superseded rather than adding a duplicate merge.

## Privacy/evaluator dependency reminder

PR #727 is stacked on #720 at head `8894ce8e0248a5502d60571ff073fc6d7847a43a`; its three relevant V2/budget validation runs are SUCCESS. PR #753 is stacked on #727 and corrects the privacy helper's missing-response-URL fallback; it must be included/revalidated before relying on that privacy check. The evaluator chain #728 and #755–#759 remains stacked on #727 / its descendants and must not be rebased or merged ahead of its exact rights, privacy and mandatory source-SHA predecessors.

HUMAN-MERGE remains binding. No branch was merged, no main ref moved, no workflow was dispatched, and no source/quote/outcome data were accessed for this overlap audit. This is an integration-order finding, not model-quality evidence.


## 2026-11-09 14:30 UTC — corrected current-form overlap and exact runtime audit

### Corrected overlap audit (direct source/test comparison)

A direct re-read of the actual PR #720 branch at `1b9464834dd5256b7d69499c1443378518dde256` supersedes the earlier 13:06 overlap note above. The #720 branch already contains all of the following in `serie_a_v2_current_form_source_capture.py` and its tests:

- strict metadata date-only validation: `datetime` objects and noncanonical/timestamp strings are rejected before counting;
- same-date reversed fixture rejection after V2 alias normalization in both metadata and current-season CSV;
- configured season-boundary validation;
- finite/nonnegative integer-count behavior (the integer check rejects non-finite values);
- the associated Atalanta alias regressions.

Therefore PRs #763 and #765 are duplicate protections relative to the current #720 branch and should not be merged separately. In #764, the reversed-duplicate and integer protections are also already present in #720. Its unique delta is the raw CSV `Date` cell check **before** `pandas.to_datetime`, preventing a timestamp such as midnight from being normalized into a date. The prior continuity statement that #720 still converted metadata `datetime` objects to dates was incorrect.

That unique raw-date delta was integrated directly into the existing #727 branch rather than creating another overlapping PR. Final #727 HEAD: `18a3cfda4e83e44aca1252665d01804267d16467` (base remains #720 `1b9464834dd5256b7d69499c1443378518dde256`). It rejects midnight/non-midnight times, ISO timestamps with `Z`, and explicit offsets before pandas parsing. The forward-capture verifier's pinned source-script Git blob SHA-1 was updated to the exact source blob `4f5837671727066903e798dd893753f13a925434`.

Exact-head validation for #727:
- Frozen V2 Shadow Tests [#42634756592](https://github.com/MaksimBlud/football-ai/actions/runs/42634756592): SUCCESS; Python 3.11 **388 passed**, Python 3.12 **388 passed**, `pip check` clean.
- Public Source Download Budget Tests [#42634756621](https://github.com/MaksimBlud/football-ai/actions/runs/42634756621): SUCCESS, **24 passed**.
- Production `.pkl` guards: PASS.
- La Liga workflow [#42634756714](https://github.com/MaksimBlud/football-ai/actions/runs/42634756714) was an existing shared-path side effect, SUCCESS, and is not V2 evidence.

The first run on superseded #727 HEAD `f14142fceb836531b73ae805a95371c479b46993` correctly caught the stale forward source-blob pin (387 passed, one pin test failed). The pin was corrected and the final exact HEAD above passes.

### Fresh main runtime and artifact privacy

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The original forward workflow is `.github/workflows/serie-a-v2-forward-preview.yml`; the current-form forward workflow is `.github/workflows/serie-a-v2-current-form-forward-preview.yml`.

Actual main runs re-read from GitHub Actions:
- Original old-season-only forward run [#42492484513](https://github.com/MaksimBlud/football-ai/actions/runs/42492484513), 2026-11-08 14:59 UTC: SUCCESS; 71 tests passed; source artifact `13574818932` SHA-256 `d8f73d4845dfbbcc835723183f9c2e07bdbf061af68ff3447c166874d605f7b1`; `quotes_seen=0`, `forecasts_created=0`, no Supabase writes or paid calls.
- Current-form source capture run [#42479299556](https://github.com/MaksimBlud/football-ai/actions/runs/42479299556), 2026-11-08 12:14 UTC: SUCCESS; 19 tests passed; 10 old-season CSVs plus current-season CSV, 3,900 historical rows plus 100 current-season rows; artifact `13617155063`, ZIP SHA-256 `5395ff50d5e312f395b4f76e9cdf63fcb2a71ab831e07fd24cb3418602ad3af6`.
- Current-form forward-only run [#42493688915](https://github.com/MaksimBlud/football-ai/actions/runs/42493688915), 2026-11-08 15:13 UTC: SUCCESS; 53 tests passed; independently reverified artifact `13617155063` and parent run/SHA; `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes read/scored false, paid calls 0, Supabase writes 0.

Artifact metadata for `13617155063` was read without downloading the ZIP: it remains unexpired, size 438,211 bytes, and GitHub reports expiry `2027-02-06T12:14:28Z`. The repository visibility is still `public`. This is a live confidentiality blocker: the main source-capture workflow has not yet received #720/#727's private-storage preflight. Do not initiate another source capture or download the artifact while this remains unresolved; do not change the workflow schedule or delete artifacts in this task.

Read-only Supabase pre-match aggregate (strict `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= NOW()`): **3,915** snapshots across **327** events; **0** snapshots/events in the last seven days; **0** snapshots for future fixtures. Latest Serie A pre-match snapshot remains `2026-10-13 14:48:53 UTC`. No individual prices or outcome/result fields were selected.

### Binding state

- Source archive SHA and parent-workflow chronology are technically verified for the November 8 artifact, but the artifact's public-repository confidentiality gate is not integrated on main.
- Provider-issued frozen-inference permission remains unresolved; no inference is authorized by the open PRs.
- No new pre-match quote has appeared, so no new forecast exists.
- The separate prospective outcome gate remains **0/30**; no 2026/27 target outcome was read.
- Original candidate SHA, 19 features, weights/scaler/imputer, `active_lambda=0`, `shadow_lambda=1`, NO_BET and no-promotion rules remain unchanged.
- HUMAN-MERGE only; no main update, merge, Supabase write/DDL, paid request, schedule change, or production artifact change.

---

## 2026-11-09 15:08 UTC — fresh main source/forward run and quote-identity guard

### Exact main and new live source evidence

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or ref update was performed.
- Existing scheduled current-form source run [#42634501531](https://github.com/MaksimBlud/football-ai/actions/runs/42634501531) completed SUCCESS on that main. Its source-validation step passed **19 tests**.
- The metadata-only feature-input query reported **100** unique completed Serie A 2026/27 fixtures. An independent read-only identity aggregate selected only `match_date, home_team, away_team`: 103 rows, 100 ordered identities, 100 unordered identities after V2-local Atalanta alias normalization, date range 2026-08-22 through 2026-11-02. No score/result columns were selected.
- The source archive contains ten historical CSVs (**3,910** historical rows) plus the current-season CSV (**110** completed prior-day rows), for **11** source files.
- Source artifact ID **13681778268**, size 439,419 bytes, GitHub ZIP SHA-256 `f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101`. Latest current-source observation: `2026-11-09T14:26:18.118320Z`; artifact upload: `14:26:19Z`; parent workflow completion: `14:26:23Z`.
- The chronology is recorded explicitly: artifact upload preceded parent-run completion by about four seconds. The downstream verifier requires the successful parent run to be completed before any quote is admitted. This run itself contained no quote, so it does **not** establish a quote-level source-before-quote forecast.

### Downstream forward-only verification

- Existing current-form forward run [#42634693506](https://github.com/MaksimBlud/football-ai/actions/runs/42634693506) completed SUCCESS; **53 tests passed**.
- It independently verified source artifact **13681778268**, the exact ZIP SHA-256 above, the source parent run, and the frozen candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- At verification, the source archive was 47 seconds old and marked fresh for a future quote.
- Actual result: `quotes_seen=0`, `v2_current_form_shadow_captured=0`; target outcomes read/scored false; paid provider calls 0; Supabase writes 0. Forward report artifact **13682418549**, ZIP SHA-256 `51afce059c43a33b9751fd308196cf33f4dd661344eefaa6d809c9f5b529bd5a`.
- Therefore the live proof is real source-artifact/parent verification, not a V2 forecast and not a source-before-quote prediction. The separate target-outcome gate remains **0/30**.

### Fresh read-only saved-quote inventory

Strict pre-match definition: `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= NOW()`.

- All leagues: **3,915** snapshots / **327** events; **0** new snapshots in seven days; **0** upcoming events with a saved strict pre-match quote.
- Serie A: **620** snapshots / **63** events; latest saved strict pre-match quote `2026-10-13 14:48:53.042620+00`.
- No individual odds, scores, results, or target-outcome columns were selected.

### New PR #766 — event-ID identity integrity

PR [#766](https://github.com/MaksimBlud/football-ai/pull/766) adds a V2 forward-capture guard binding one saved provider event ID to exactly one (home team, away team, kickoff) identity. Reversed home/away rows or a conflicting kickoff for the same event ID now fail before source-archive loading, feature construction, or shadow inference. Multiple timestamped quotes for the same exact fixture remain supported.

Exact HEAD: `d4f4eabf0389ffbebf0447dfd6a7330c2e3a9da8`; base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; two changed files; two new regressions. All **7/7** exact-head workflows succeeded:
- Frozen V2 Shadow Tests [#42641305908](https://github.com/MaksimBlud/football-ai/actions/runs/42641305908): **87 passed**, production candidate/hash guard passed.
- Research [#42641305845](https://github.com/MaksimBlud/football-ai/actions/runs/42641305845), Serie A [#42641305912](https://github.com/MaksimBlud/football-ai/actions/runs/42641305912), Ligue 1 [#42641305691](https://github.com/MaksimBlud/football-ai/actions/runs/42641305691), Product [#42641306021](https://github.com/MaksimBlud/football-ai/actions/runs/42641306021), Bundesliga [#42641306052](https://github.com/MaksimBlud/football-ai/actions/runs/42641306052), Eredivisie [#42641305841](https://github.com/MaksimBlud/football-ai/actions/runs/42641305841) — all SUCCESS.
- PR #766 is Ready for review, mergeable, and **not merged**. HUMAN-MERGE remains mandatory.

### Rights/privacy blocker remains binding

- Repository visibility remains `public`; main current-form source capture still uploads raw source archives as public Actions artifacts with 90-day retention.
- PR #720/#727 have not been merged. #720's manifest explicitly keeps provider frozen-inference permission unresolved and blocks V2 inference/source access; #727 adds the private-storage gate. PR #753's missing-response-URL fail-closed correction is a dependent privacy hardening and must be included/revalidated before relying on that helper.
- Do not dispatch or initiate another source download, quote collection, or V2 inference until the rights and private-storage conditions are resolved. Do not change existing schedules here.

### Frozen model and safety state

Candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 original features/weights/scaler/imputer unchanged; active lambda 0; shadow lambda 1; NO_BET; stability gate FAILED; no refit or promotion. The 100-event feature-input gate does not open the 30-forecast evaluation gate. No target outcome was read, no production .pkl changed, no Supabase write/DDL or paid call occurred, and main was not changed.


**Additional source-access cadence finding:** the current main source workflows still declare daily schedules: current-form capture at `50 5 * * *` and the old-season free real-quote diagnostic at `13 6 * * *`. The provider policy snapshot in the rights manifest describes at most two light automated sessions per rolling seven days. The shared cross-workflow two-session budget is only in open PR #720, not main. No schedule was changed and no manual source dispatch was made; until the rights/budget stack is integrated, do not initiate extra source sessions.


## 2026-11-09 15:12 UTC — evaluator stack base-SHA freshness audit

A fresh metadata read shows the privacy/evaluator descendants have not all been refreshed onto the latest #727 code head:

- #727 current HEAD is `18a3cfda4e83e44aca1252665d01804267d16467`, based on #720 HEAD `1b9464834dd5256b7d69499c1443378518dde256`.
- #728 still uses base SHA `8894ce8e0248a5502d60571ff073fc6d7847a43a` (the earlier #727 snapshot).
- #753 also still uses base SHA `8894ce8e0248a5502d60571ff073fc6d7847a43a`; it does not yet contain #727's later raw-date guard/source-script pin update.
- The outcome-reader/source-verifier descendants #755–#759 are stacked through #730/#731 and then sequentially (#755 → #756 → #757 → #758 → #759). Their current mergeability flags do not prove that the full stack contains #727's latest HEAD or the #753 response-URL fix.

Do not merge these descendants in their current ancestry. After HUMAN-MERGE of #720 and #727, refresh #728 and #753 from the new exact main in the intended order, rerun exact-head CI, then rebuild/revalidate #755–#759 on that refreshed base. #753 must remain part of the privacy hardening before relying on the repository-response URL check. No PR was merged or rebased in this audit.

## Latest main free-diagnostic privacy audit — 2026-11-09 16:08 UTC

Fresh main is still 40887ebb215730190d7a6c7a1693373ec4afcdfc. The scheduled main workflow [Serie A V2 Free Real-Quote Diagnostic #42651542041](https://github.com/MaksimBlud/football-ai/actions/runs/42651542041) completed SUCCESS at 16:08 UTC. Its log confirms 53 offline tests passed, then the unguarded main workflow fetched the public Football-Data source and uploaded a new GitHub Actions artifact:

- Artifact ID: 13689701985.
- Name: serie-a-v2-free-real-quote-diagnostic.
- Size: 425,067 bytes.
- GitHub ZIP SHA-256: c968b357235029c5e96283470d5ac4d40fe1a0647b1d510dbf7270e976db9c4d.
- Expires: 2027-02-07 16:07:28 UTC.

The run's printed diagnostic summary had 19 expected features but zero feature rows and zero diagnostic scores, zero paid-provider requests, zero Supabase writes, and zero quote rows reported as having source observed after quote. This is not a forecast or model-quality evidence. The artifact was inspected only through GitHub metadata and job logs; its ZIP/source bytes were not downloaded by this audit.

This confirms the confidentiality blocker is still active on main: repository visibility is public, while the main workflow still runs without the private-repository preflight and uploads source bytes with 90-day retention. The #720/#727 rights/privacy stack is not merged; do not initiate manual source collection or new artifact downloads. #727's private-storage preflight remains the intended fail-closed fix, and #753 has now been rebased onto current #727 HEAD 18a3cfda4e83e44aca1252665d01804267d16467 as HEAD 2d53f9bc6160410bbca81a990b5c1a482864705a; exact-head frozen V2 CI #42659444261 passed 389 tests on both Python 3.11 and 3.12, with pip check and production .pkl guards clean. #753 remains Draft until its #727 parent is manually integrated.

A fresh read-only Supabase aggregate selected only prematch odds fields and used snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= NOW(): 3,915 strict prematch snapshots across 327 events, 0 in the last seven days, and 0 future events with a saved strict prematch quote. Latest Serie A prematch snapshot remains 2026-10-13 14:48:53 UTC. No scores/results/target outcomes were selected.

Binding state remains unchanged: original candidate SHA a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6, 19 frozen features, 3,799 training rows through 2026-06-30, active_lambda=0, shadow_lambda=1, stability gate FAILED, and prospective outcome gate 0/30. No inference is authorized while provider frozen-inference scope remains unresolved.

No main update, merge, Supabase write/DDL, paid request, schedule change, production artifact change, model refit, threshold tuning, or target-outcome read was performed by this audit. HUMAN-MERGE only.

## Strict prematch quote-reader and privacy stack — 2026-11-09 17:03 UTC

Dependency audit confirmed #727 and #742 were sibling PRs: #727's current branch still used the saved-quote query without the server-side snapshot-time upper bound, while #742 alone added lte(snapshot_time_utc, as_of). Do not treat #727 alone as the final prematch quote-reader contract.

PR #742 was rebased onto current #727 HEAD 18a3cfda4e83e44aca1252665d01804267d16467. Current #742 HEAD is fac462a10509a14c63d7f39abb5614bab756fcae. Its exact one-commit diff against #727 contains the strict server-side snapshot cutoff, the query-builder regression, and the frozen-V2 test workflow allowlist for the #727 base. It preserves the #727 privacy/source-rights tests. Exact run #42660308461 succeeded: Python 3.11 388 passed, Python 3.12 388 passed, pip check clean, production .pkl guards PASS.

PR #753 was then rebased on top of #742, creating a linear dependency stack #720 → #727 → #742 → #753. Current #753 HEAD is a3f8cb4e8d4447f15eaed3fb283c1e7670e944f0, based on #742 HEAD fac462a10509a14c63d7f39abb5614bab756fcae. Exact comparison shows only the privacy helper's missing-response-URL fail-closed change, its single regression test, and the workflow base-branch allowlist. Exact run #42660688361 succeeded: Python 3.11 389 passed, Python 3.12 389 passed, pip check clean, production .pkl guards PASS. #753 remains Draft until the parent stack is manually integrated.

Earlier intermediate #742/#753 rebase commits were superseded before final validation and are not the accepted heads. Only #742 HEAD fac462a10509a14c63d7f39abb5614bab756fcae and #753 HEAD a3f8cb4e8d4447f15eaed3fb283c1e7670e944f0 are the final exact-head results for this stack.

The strict quote reader now has a server-side condition: future kickoff and snapshot_time_utc <= as_of, so the database does not return snapshots observed after the evaluation clock. The query keeps the explicit market-only projection and never uses SELECT *.

No main update or merge occurred. No Supabase writes/DDL, paid calls, source downloads, schedule changes, target-outcome reads, model refit, weight/feature/lambda changes, production .pkl modifications, or promotion occurred during this stack work. HUMAN-MERGE only.

## Latest original V2 runtime / direct-read rights follow-up — 2026-11-09 18:59 UTC

Current main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc` and the repository is still public.

### Fresh real forward-only runs

- Original forward run [#42676083517](https://github.com/MaksimBlud/football-ai/actions/runs/42676083517), exact main SHA above:
  - 71 offline regression tests passed.
  - Real historical source attestation verified 10 pre-prospective source CSVs / 3,800 historical rows, candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
  - `quotes_seen=0`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`, paid calls 0, Supabase writes 0, no target outcomes read/scored.
  - Forward artifact ID `13700981366`, ZIP digest `sha256:e6f625a9dad6e7351ae08c38a45f80412266c08c8d2a55769d18d86f73faef37`, 1,460 bytes.
- Current-form forward run [#42677383722](https://github.com/MaksimBlud/football-ai/actions/runs/42677383722), exact main SHA above:
  - 0 quotes and 0 current-form shadow captures; no target outcomes read/scored, paid calls 0, production/Supabase writes 0.
  - It re-verified source artifact `13681778268`, SHA-256 `f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101`, from successful parent run `42634501531` at head `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
  - The verified archive contains 10 historical CSVs / 3,910 historical match rows and 110 current-season history rows; the metadata-only feature-input gate is 100 canonical events. At the 18:49 UTC verification, source age was 15,793 seconds and the source was still within the 24-hour freshness bound.
  - Current-form forward artifact ID `13700368254`, ZIP digest `sha256:25b1b327b47f0ebfa0eb75a258604427e785eaa86eafc80a6fdc40907b4847c8`, 440,605 bytes, 90-day retention. It was uploaded while the repository was public; do not download or treat SHA as confidentiality. The private-storage/right gates in #720/#727 are not yet on main.

These are source-attestation / no-quote runtime proofs, not live V2 predictions or quality evidence.

### Fresh read-only Supabase pre-kickoff inventory

Query used only `league`, `event_id`, `snapshot_time_utc`, and `commence_time_utc`, with `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= NOW()`. No odds prices or result/outcome columns were selected.

- All leagues: **3,915** strict pre-match snapshots / **327** distinct events.
- New strict pre-match snapshots in the last 7 days: **0**.
- Upcoming events with saved strict pre-match quotes: **0**.
- Serie A: **620** snapshots / **63** events; latest strict pre-match snapshot `2026-10-13T14:48:53.042620Z`.
- Latest per other league: EPL `2026-10-09T15:25:57.102061Z`; Bundesliga, Eredivisie, La Liga, Ligue 1, Primeira Liga, RPL and Turkey Super Lig have no snapshots in the last 7 days.

The 100-event feature-input gate is separate from the 30-primary-completed-event outcome gate. Evaluation remains **0/30**.

### Rights and confidentiality remain separate blockers

The #727 branch's reviewed Football-Data manifest explicitly distinguishes:
- private noncommercial source archive/validation only;
- frozen inference not permitted pending provider-issued scope;
- AI training, commercial use and public product use not permitted;
- at most two automated source-download sessions per rolling seven days;
- no provider-issued authorization evidence (`authorization=null`).

The repository metadata still reports `private=false`. Therefore #727's source-capture path must block before Supabase/source access and #727's forward path must block before quote access until the repository is private and the corresponding scope is satisfied. This is a fail-closed project policy, not a claim that the provider expressly prohibits all academic inference.

### New direct Supabase-read bypass PR

PR [#768](https://github.com/MaksimBlud/football-ai/pull/768), stacked on PR #743 exact base `e468da0e54a935dbf5f3c114f2f0d7cff793c0c5`, adds an inference-rights check inside the public `fetch_saved_upcoming_serie_a_quotes()` helper before `client.table(...)` can be accessed. This closes a direct-import bypass not covered by the CLI, forward-preparation, or scoring guards.

Exact HEAD: `dc53d77c2a503ae6a8bd09bde4fd14ad38cdd1fe`.
Two duplicate-trigger workflow runs on that same exact HEAD both completed SUCCESS:
- [#42678674472](https://github.com/MaksimBlud/football-ai/actions/runs/42678674472): Python 3.11 and 3.12 each **345 passed**, production `.pkl` diff guards PASS.
- [#42678665725](https://github.com/MaksimBlud/football-ai/actions/runs/42678665725): Python 3.11 and 3.12 each **345 passed**, production `.pkl` diff guards PASS.

The two runs are duplicate triggers on one HEAD, not four independent test suites. #768 remains Draft until its #743 base dependency is integrated and revalidated.

### Current security finding

The live Supabase Security Advisor still reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger` (CRITICAL). No RLS DDL or policy change was made; enabling RLS without correct policies could break existing access.

### Frozen model status unchanged

- Original candidate SHA: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- 19 features; 3,799 training rows through 2026-06-30.
- `active_lambda=0`; `shadow_lambda=1`; stability gate FAILED; prospective evaluation gate **0/30**.
- No refit, weight/feature/contract change, production `.pkl` change, target-outcome read, scoring, promotion or betting.

HUMAN-MERGE only. Main, Supabase data/schema, source schedules and other agents remain unchanged.


## Direct source-metadata reader hardening — 2026-11-09 19:04 UTC

PR #769 closes a remaining direct-call gap beneath the already-guarded `capture_source_archive()` entrypoint in #732. The public `read_completed_primary_event_count()` and `read_completed_primary_event_identities()` helpers each performed a Supabase identity-only read without re-checking source-only rights and private artifact storage when imported directly.

- Both helpers now require `require_personal_research_source_capture_scope()` and `require_private_repository_for_source_artifacts()` before `client.table(...)`.
- The selected metadata allowlist remains exactly `match_date,home_team,away_team`; no score/result/outcome columns were added.
- Rights-denial and public-storage-denial regressions cover both helpers and prove the Supabase client is untouched.
- Existing `capture_source_archive()` checks remain in place. The nested reader re-check is intentional defense in depth; the capture-order regression records both pairs of checks before the metadata query.

PR #769 exact HEAD: `df1d6ff024e4ccc3b06d3cdb55ee56125a327e7c`, stacked on #732 exact base `b0e3085fae0bbdad4405b028a93dcc00cca0019a`, Draft/HUMAN-MERGE only.

Both exact-head offline CI triggers completed SUCCESS:
- [#42679535830](https://github.com/MaksimBlud/football-ai/actions/runs/42679535830): **140 passed**, Python 3.12, production `.pkl` diff guard PASS.
- [#42679527984](https://github.com/MaksimBlud/football-ai/actions/runs/42679527984): **140 passed**, Python 3.12, production `.pkl` diff guard PASS.

They are duplicate push/PR triggers on the same HEAD, not independent cohorts. No Supabase, source, quote, outcome, paid-provider or production artifact access occurred in these tests.

The source-only scope remains private noncommercial archive/validation only; frozen-model inference, AI training, commercial use and public-product use remain unauthorized. This PR does not change those permissions or the two-download-sessions-per-rolling-seven-days budget.


## Direct prospective completed-fixture metadata reader hardening — 2026-11-09 19:08 UTC

PR #770 closes a second direct-import bypass in the original V2 prospective gate. The live runner in #730 checked inference rights before calling the identity-only completed-fixture reader, but the public `read_completed_fixture_gate()` function itself did not re-check rights when imported directly.

- The public reader now calls `require_personal_research_inference_scope()` before the identity-only Supabase query.
- Its frozen query allowlist is unchanged: `match_date,home_team,away_team`; no score, H/D/A result, persistence timestamp, or other target-outcome field is selected.
- Regressions prove denial occurs before `client.table(...)`, and the actual unresolved rights manifest blocks the direct call before Supabase.
- The offline validation workflow now compiles the gate module and tests this exact stack.

PR #770 exact HEAD: `3888b77f85445e88d6cd20047e56e86202d51897`, stacked on #769 exact base `df1d6ff024e4ccc3b06d3cdb55ee56125a327e7c`, Draft/HUMAN-MERGE only.

Both exact-head offline validation runs completed SUCCESS:
- [#42680275346](https://github.com/MaksimBlud/football-ai/actions/runs/42680275346): **143 passed**, Python 3.12, production `.pkl` diff guard PASS.
- [#42680258247](https://github.com/MaksimBlud/football-ai/actions/runs/42680258247): **143 passed**, Python 3.12, production `.pkl` diff guard PASS.

Earlier failures were on superseded HEAD `e48c28fd82ca30413f64bdb82c294d23f28e2881`; the actual-manifest test was corrected on the final HEAD above. Duplicate triggers on the same HEAD are not independent cohorts.

The direct-reader chain is now: #732 capture entrypoint gate → #769 direct source identity-reader gates → #770 direct prospective completed-fixture identity gate. These are rights/metadata protections only; they do not open the protected outcome reader. The 30-eligible-completed-primary-forecast gate and lazy post-gate outcome reader remain unchanged. No outcome data was read by this PR or its CI.


## Critical rolling-seven-day public-source budget audit — 2026-11-09 19:12 UTC

A second, date-scoped read-only audit confirms the daily source workflows on main have exceeded the provider's stated maximum of two automated sessions per rolling seven days. The rolling window checked was **2026-11-02 19:08 UTC through 2026-11-09 19:08 UTC**. Main is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`; its two live workflow files have daily schedules and contain no shared budget reservation/gate.

### Successful scheduled sessions in the rolling window

**Current-Form Source Capture — 7 successful sessions, one per day Nov 3–9:**

| Date UTC | Run | Artifact | Historical CSVs | ZIP SHA-256 |
|---|---:|---:|---:|---|
| Nov 3 | [#41640753996](https://github.com/MaksimBlud/football-ai/actions/runs/41640753996) | #13231843819 | 10 | `4e6fb5531a2206a353fe00fa1ebb0b4d20b3c6ae41ab49a7c672f8dab6d29cd8` |
| Nov 4 | [#41836971469](https://github.com/MaksimBlud/football-ai/actions/runs/41836971469) | #13327281383 | 10 | `9dced08f96d81c39dcc199afba481fab07961ce6b61d14776fdc78563bc8cccd` |
| Nov 5 | [#42036450692](https://github.com/MaksimBlud/football-ai/actions/runs/42036450692) | #13418048952 | 10 | `941cb910b4b412027de196156147b164ba6705159ef90e34a99af02e0de04f10` |
| Nov 6 | [#42224162373](https://github.com/MaksimBlud/football-ai/actions/runs/42224162373) | #13504817564 | 10 | `d8e96884c6fefd6687b82d72bf4c6cc08433b6d42e3b87879252115137a6e7ea` |
| Nov 7 | [#42370312212](https://github.com/MaksimBlud/football-ai/actions/runs/42370312212) | #13573502390 | 10 | `92b3ff34565c96ef17c12fdfb99cfa6f562ff37037235e02a8a9bb3b1d3d1afe` |
| Nov 8 | [#42479299556](https://github.com/MaksimBlud/football-ai/actions/runs/42479299556) | #13617155063 | 10 | `5395ff50d5e312f395b4f76e9cdf63fcb2a71ab831e07fd24cb3418602ad3af6` |
| Nov 9 | [#42634501531](https://github.com/MaksimBlud/football-ai/actions/runs/42634501531) | #13681778268 | 10 | `f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101` |

Each successful run reports 10 historical old-season CSVs, 11 total archive files, and zero paid-provider calls / Supabase writes.

**Free Real-Quote Diagnostic — 6 successful sessions, Nov 3–7 and Nov 9:**

| Date UTC | Run | Artifact | Historical rows | Public CSV HTTP requests | ZIP SHA-256 |
|---|---:|---:|---:|---:|---|
| Nov 3 | [#41650074683](https://github.com/MaksimBlud/football-ai/actions/runs/41650074683) | #13236383688 | 3,800 | 10 | `8386044e795e208e112e9af8d9ebcb0d5a77cf8f00f51147c70df8d01785c143` |
| Nov 4 | [#41847314320](https://github.com/MaksimBlud/football-ai/actions/runs/41847314320) | #13332260799 | 3,800 | 10 | `72a32dc61d6e230be46bc5fe69a52e97142a79816af33c66f58066e0ceb6e8d8` |
| Nov 5 | [#42046051819](https://github.com/MaksimBlud/football-ai/actions/runs/42046051819) | #13424482168 | 3,800 | 10 | `4f735f1e4636250b0b711963e9f6a660838afc521396968fcb19acb2b39d3559` |
| Nov 6 | [#42231648250](https://github.com/MaksimBlud/football-ai/actions/runs/42231648250) | #13510280643 | 3,800 | 10 | `4cb7780bc52e64d4b9f761107e79451fcf7541fb79a6ea70a520c96df9bc54dd` |
| Nov 7 | [#42374478720](https://github.com/MaksimBlud/football-ai/actions/runs/42374478720) | #13574818932 | 3,800 | 10 | `6909afcba069000449d033e20fee00aafe4b4e0f044087d4e0b48901260b7d88` |
| Nov 9 | [#42651542041](https://github.com/MaksimBlud/football-ai/actions/runs/42651542041) | #13689701985 | 3,800 | 10 | `c968b357235029c5e96283470d5ac4d40fe1a0647b1d510dbf7270e976db9c4d` |

The Nov 8 diagnostic [#42484124054](https://github.com/MaksimBlud/football-ai/actions/runs/42484124054) failed before producing an artifact and is excluded from the successful-session lower bound. Each successful diagnostic reports `paid_provider_requests=0`, `public_http_requests=10`, and uploads a ~425 KB artifact.

### Policy consequence / immediate safe response

This is at least **13 successful automated public-source sessions** in the rolling seven-day window (7 capture + 6 diagnostic), versus the stated maximum of **2**: at least 11 sessions over the limit, excluding the failed Nov 8 attempt. The diagnostic and source-capture workflows are separate sessions even though they use the same public source.

No new provider request was made during this audit; only existing GitHub run logs/artifact metadata and the live pre-match Supabase aggregate were read. The main workflows have not been edited and their cron expressions were not changed.

PR #720 already adds one shared two-sessions-per-rolling-seven-days budget gate to **both** workflows, with a single concurrency group and reserved-attempt markers; it leaves both cron expressions unchanged. It is Ready for review at exact HEAD `1b9464834dd5256b7d69499c1443378518dde256`, with **10/10** exact-head check-runs SUCCESS. PR #727 then adds private-repository and source-rights preflight, but the repository remains public and the inference scope remains unresolved. These must be manually integrated in dependency order; no automatic merge or schedule change was made.

This budget breach risk is independent of model quality. It does not create any V2 forecast or authorize inference. The candidate, 19 features, weights, lambdas and 30-event outcome gate remain frozen.

## Latest V2-only recovery cycle — 2026-11-09 22:00 UTC

Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository visibility is still public. The original candidate was re-read from main and remains artifact SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with the unchanged 19-feature order, `active_lambda=0`, `shadow_residual_lambda=1`, `stability_gate_passed=false`, 3,799 training rows through 2026-06-30, and `opened_2026_27_outcomes_used=false`. Protocol still requires 30 completed primary Serie A prospective forecasts before any target-outcome read; other leagues do not count.

### Latest real main forward runs (logs and artifact metadata rechecked)

- Original old-season forward [run #42676083517](https://github.com/MaksimBlud/football-ai/actions/runs/42676083517), main SHA above, completed SUCCESS at 2026-11-09 18:41 UTC. It ran **71** frozen-V2 tests, verified source artifact #13689701985 / SHA-256 `c968b357235029c5e96283470d5ac4d40fe1a0647b1d510dbf7270e976db9c4d` (10 pre-prospective CSVs / 3,800 rows), then reported `quotes_seen=0`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`, paid calls 0, Supabase writes 0. Output artifact #13700981366, SHA-256 `e6f625a9dad6e7351ae08c38a45f80412266c08c8d2a55769d18d86f73faef37`, 1,460 bytes.
- Current-form forward [run #42677383722](https://github.com/MaksimBlud/football-ai/actions/runs/42677383722), same main SHA, completed SUCCESS at 18:49 UTC. It ran **53** tests and re-verified current-form source artifact #13681778268 / SHA-256 `f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101`: 10 old-season CSVs / 3,910 historical rows, 110 lagged current-season rows, metadata-only feature-input gate 100, source age 15,793 seconds. It reported `quotes_seen=0`, `v2_current_form_shadow_captured=0`, no target-outcome read/scoring, paid calls 0, writes 0. Output artifact #13700368254, SHA-256 `25b1b327b47f0ebfa0eb75a258604427e785eaa86eafc80a6fdc40907b4847c8`, 440,605 bytes, 90-day retention.
- Free diagnostic [run #42651542041](https://github.com/MaksimBlud/football-ai/actions/runs/42651542041) completed SUCCESS with 53 tests, but its report was `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`, with no quote rows. Artifact #13689701985 remains public while repository visibility is public; do not download it.

These are genuine source/forward runtime checks, not quote-level forecasts or model-quality evidence. The current-form source artifact's 100-event feature-input gate is not the separate 30-forecast outcome gate.

### Fresh read-only Supabase pre-match aggregate

Read only `league,event_id,snapshot_time_utc,commence_time_utc`, filtered by `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= NOW()`. No prices, scores, results or target outcomes were selected.

- All leagues: **3,915** strict pre-match snapshots / **327** events.
- Last 7 days: **0** new strict pre-match snapshots.
- Upcoming events with saved strict pre-match quotes: **0**.
- Latest strict pre-match snapshot: 2026-10-13 14:48:53 UTC (Serie A).
- Serie A: 620 snapshots / 63 events.

No new quote is available for prospective inference or evaluation.

### New historical-row integrity transplant: PR #773

PR [#773](https://github.com/MaksimBlud/football-ai/pull/773) carries the unique integrity delta from #760 onto the current #720 rights/budget stack, preserving #720's extra workflow-contract tests:

- Reject time-bearing values where the historical source contract is date-only.
- Reject missing, non-finite, negative or fractional historical goals/corners/cards.
- Reject same-date duplicate fixtures with reversed Home/Away after V2-local alias normalization.
- No change to the original feature builder, 19-feature order, candidate, weights, scaler/imputer, lambda, market fallback or outcome gates.

Exact stack: base #720 HEAD `1b9464834dd5256b7d69499c1443378518dde256`; PR #773 HEAD `d13b4bc3f510be47baa2fc9c4d31a3bedc05ab15`; compare is **2 ahead / 0 behind**, exactly two files. Exact PR CI run [#42707544006](https://github.com/MaksimBlud/football-ai/actions/runs/42707544006) SUCCESS: **346 passed** under Python 3.11 and **346 passed** under Python 3.12; compile, `pip check`, and production `.pkl` diff guard PASS. This is offline contract/regression evidence, not live inference.

PR #760 is now Draft/superseded to prevent duplicate integration; its unique two-file delta is carried by #773. #773 remains Draft until #720 is manually merged and the child is rebased/revalidated on fresh main. HUMAN-MERGE only.

No main update/merge, source download, quote read, protected outcome read, paid request, Supabase write/DDL, schedule change, production artifact change, refit, threshold tuning, promotion, betting, or other-agent change occurred in this cycle.

## Direct saved-quote reader rights hardening — 2026-11-09 22:04 UTC

PR [#774](https://github.com/MaksimBlud/football-ai/pull/774) transplants the unique direct-reader guard from #768 onto the correct strict-prematch stack:

- Exact base: #742 HEAD `fac462a10509a14c63d7f39abb5614bab756fcae`.
- Exact head: `f4180d8ce4142096f7a2ad1cd86ba95c78b3ae30`; compare **6 ahead / 0 behind**, exactly three files (quote reader, tests, frozen V2 workflow).
- `fetch_saved_upcoming_serie_a_quotes()` now checks `require_personal_research_inference_scope()` before any `client.table(...)` access. It retains the strict server-side `commence_time_utc > as_of` and `snapshot_time_utc <= as_of` filters and explicit market-only projection.
- Regression proves a denied rights scope blocks before Supabase; the existing offline query test explicitly mocks the scope as allowed.
- Exact corrected CI run [#42708210273](https://github.com/MaksimBlud/football-ai/actions/runs/42708210273) SUCCESS: **390 passed** under Python 3.11 and **390 passed** under Python 3.12; compile, `pip check`, and production `.pkl` diff guard PASS. Duplicate run #42708193908 on the same HEAD also passed and is not a second independent cohort.
- The first pre-fixture-fix attempt failed because an existing offline query test did not explicitly grant the newly required scope; this was corrected before the accepted exact-head run.

PR #768 remains Draft/superseded on the divergent #743/#728 stack; its direct-reader delta is carried by #774. PR #774 remains Draft until #720 → #727 → #742 are manually integrated and the child is rebased/revalidated on fresh main. HUMAN-MERGE only.

No live Supabase read, source/quote download, target-outcome read, paid provider call, write/DDL, main change, production artifact change, or model-contract change was performed.

## 2026-11-09 23:01 UTC — outcome-clock hardening and fresh runtime audit

### Fresh source-of-truth state

- `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- The repository is still public (`private=false`). Do not expose or create further source archives while the privacy gate is absent from main.
- The open continuity PR branch is separate from main; this note does not modify main.

### Actual original V2 forward runs on the exact main SHA

- Original forward run #42676083517 completed SUCCESS at 2026-11-09 18:41 UTC. Its source attestation verified artifact 13689701985, parent run 42651542041, source ZIP SHA-256 `c968b357235029c5e96283470d5ac4d40fe1a0647b1d510dbf7270e976db9c4d`, 10 historical source files and 3,800 historical results. The actual forward report states `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `paid_provider_calls=0`, and `supabase_writes=0`. Its output artifact is 13700981366 (1,460 bytes; ZIP SHA-256 `e6f625a9dad6e7351ae08c38a45f80412266c08c8d2a55769d18d86f73faef37`).
- Current-form forward run #42677383722 completed SUCCESS at 2026-11-09 18:49 UTC. It verified source artifact 13681778268, parent run 42634501531, source ZIP SHA-256 `f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101`, 3,910 historical rows, 110 current-season history rows, and the 100-event feature-input gate. Source age at verification was 15,793 seconds. The report states `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcome_evaluation_gate_open=false`, `target_outcomes_read=false`, `target_outcomes_scored=false`, `paid_provider_calls=0`, and `production_or_supabase_writes=0`. Output artifact 13700368254 is 440,605 bytes (ZIP SHA-256 `25b1b327b47f0ebfa0eb75a258604427e785eaa86eafc80a6fdc40907b4847c8`).
- These are successful source/provenance checks, not live V2 forecasts. No new forecast was produced.

### Strict pre-match Supabase aggregate (read-only)

Query was restricted to `odds_snapshots` metadata and the predicate `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= NOW()`; no prices, scores, results, or target outcomes were selected.

- Strict pre-match snapshots: 3,915.
- Unique events: 327.
- Strict pre-match snapshots in the last seven days: 0.
- Future events with saved pre-match quotes: 0.
- Latest strict pre-match snapshot: 2026-10-13 14:48:53.042620 UTC.

There is currently no fresh saved quote from which to produce a prospective V2 preview.

### Original frozen candidate re-verified from main

- Candidate artifact SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Exact feature-builder Git blob SHA: `401b3a0893371bfa4a488ec92a4a54af2678c8f7` (matches the previously pinned source).
- Frozen features: 19, in the original stored order.
- Weight matrix: 20 × 2.
- Training rows: 3,799; training cutoff: 2026-06-30 23:59:59 UTC.
- `active_lambda=0`; `shadow_residual_lambda=1`; `stability_gate_passed=false`; automatic promotion remains false.
- No candidate, feature order, weight, lambda, or model file was changed.

### New PR #775 — bind evaluator observation time to the actual clock

- PR: https://github.com/MaksimBlud/football-ai/pull/775
- Base: PR #770 exact HEAD `3888b77f85445e88d6cd20047e56e86202d51897`.
- Head: `90055f62475a29d91019969165356ddf588d9fd9`, 3 commits ahead / 0 behind.
- Finding: the gated outcome reader accepted caller-supplied `observed_at_utc` values later than the real runtime clock. The 30-event gates remained in place, but a future timestamp could incorrectly validate a result row whose `persisted_at_utc` was also in the future.
- Change: capture the actual UTC clock and reject a later supplied observation time before the completed-fixture gate, source preflight, or outcome query. Historical timestamps remain usable for deterministic replay. Added a regression proving zero gate/result reads on a future timestamp.
- Exact-head push CI #42716672932: SUCCESS, 144 tests passed, Python 3.12 compilation passed, production `.pkl` diff guard passed.
- Exact-head pull-request CI #42716742925: SUCCESS, 144 tests passed, compilation passed, production `.pkl` diff guard passed.
- PR remains Draft and HUMAN-MERGE only. No outcome query was run by this PR or its tests.

### Current integration and rights blockers

- Exact commit check-runs remain successful: #720 10/10; #727 4/4; #742 2/2; #753 2/2; #772 4/4; #773 2/2; #774 4/4; #740 prior HEAD 7/7.
- #773 remains stacked on #720; #774 remains stacked on #742; #772 remains stacked on #727; #775 remains stacked on #770. Do not flatten or merge these branches out of order.
- The repository is public, so #727's private-artifact gate will block source archive capture until repository privacy is changed by the owner. No repository setting was changed here.
- The rights manifest permits only private noncommercial source archival/validation under its internal interpretation; frozen V2 inference remains explicitly blocked pending provider-issued scope clarification or an alternative appropriately licensed source. Making the repository private alone does not grant inference rights.
- The current main scheduled source workflows have not yet received the #720/#727 gates. Their latest successful run artifacts above remain public metadata. No schedule was changed and no additional download was initiated.
- The preregistered 30-primary-completed-event outcome gate remains closed. No 2026/27 target outcomes were read.

### Safety ledger for this iteration

No main update or merge; no production `.pkl` changes; no Supabase writes/DDL; no paid provider requests; no new source downloads; no target-outcome reads; no refit, threshold tuning, lambda/feature/weight changes, promotion, betting, schedule changes, or other-agent changes.

## 2026-11-09 23:10 UTC — direct feature-manifest rights gate and ancestry correction

### New clean-stack PR #776

- PR: https://github.com/MaksimBlud/football-ai/pull/776
- Base is exact PR #727 HEAD `18a3cfda4e83e44aca1252665d01804267d16467`.
- Head: `9957d504c1e2010a1b582f8f45abcc4267f5ff6b`, 12 commits ahead / 0 behind; final diff is limited to the feature-manifest module, its regression tests, and its validation workflow.
- Finding: the importable original V2 `build_manifest()` and standalone CLI could construct frozen 19-feature inputs without checking the unresolved provider inference scope. The CLI could open the history CSV and saved-quote JSON before authorization.
- Fix: enforce `require_personal_research_inference_scope()` inside `build_manifest()` before feature-builder SHA verification/candidate/input access, and at the CLI before any history or quote file read. A denied CLI call writes the standard blocked report without creating a manifest.
- Existing numerical tests now use explicit test-only synthetic inference-scope fixtures. These fixtures are not live provider authorization and do not change the rights manifest.
- Exact-head push CI #42718014660: SUCCESS; Python 3.11 **391 passed**, Python 3.12 **391 passed**, Python 3.12 pip check clean, compilation PASS, production `.pkl` diff guard PASS.
- Initial runs exposed nine existing offline tests that needed those explicit synthetic fixtures after the new gate. The fixtures were added; the final exact HEAD above is green.
- PR remains Draft, cleanly stacked on #727, HUMAN-MERGE only.

### Superseded duplicate and remaining direct-report gate

- The unique direct `build_manifest()` / CLI gate from divergent PR #746 is ported to #776 on the clean #727 stack. #746 is marked in its conversation as Draft/superseded; do not merge it.
- PR #745's separate direct `make_report()` gate is not covered by #776 and remains a separate pending delta.

### Re-audited outcome-reader ancestry

- PR #728 base #727 exact HEAD `8894ce8e0248a5502d60571ff073fc6d7847a43a`, head `e075e4160f4e9be750ba0cb8a0f47a1ba419d01d`: **1 ahead / 4 behind (diverged)**.
- PR #770 head `3888b77f85445e88d6cd20047e56e86202d51897` compared with #727 exact HEAD: **33 ahead / 4 behind (diverged)**, inherited through #728 → #729 → #730 → #731 → #732 → #769 → #770.
- Therefore PR #775's future-observation-clock guard is exact-head CI-green (144 tests on push and PR runs) but remains Draft and is **not integration-ready** until the #728–#770 outcome-reader chain is ported/rebased onto the clean #727 ancestry. Do not merge #775 or flatten its parents in the current state.
- The #743 → #746 branch remains separately divergent from #742 (12 ahead / 50 behind). Its direct feature-manifest delta is now safely ported to #776; other unique deltas still require individual clean-base review.

### Safety and evaluation state

- Main is unchanged at `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- The exact main original-forward and current-form-forward runs remain #42676083517 and #42677383722; both had zero quotes, zero previews, zero target-outcome reads, zero paid provider calls, and zero writes.
- The strict pre-match Supabase aggregate remains 3,915 snapshots / 327 events, zero new snapshots in seven days, zero future events with saved pre-match quotes; latest is 2026-10-13 14:48:53 UTC.
- Candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original 19-feature order and 20×2 weights unchanged; feature-builder blob SHA remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- Repo remains public; #727 private-artifact gate will block new source capture until owner changes repository visibility. Provider inference scope is independently unresolved, so privacy alone does not authorize frozen inference.
- The 30-primary-completed-event outcome gate remains closed; no protected 2026/27 target outcomes were read.

No main update/merge, production model change, Supabase write/DDL, paid request, source download, target-outcome read, refit, threshold tuning, lambda/feature/weight change, promotion, betting, schedule change, or other-agent change.


## 2026-11-10 01:05 UTC — core V2 inference/refit surfaces sealed; fresh quote and main-run audit

### Fresh repository/main state

- Default branch remains `main` at exact commit `40887ebb215730190d7a6c7a1693373ec4afcdfc` (latest commit message: #673 current-form source attestation).
- Repository metadata still reports `visibility=public`, `private=false`.
- The latest continuity documentation branch is separate from main; no main ref or repository setting was changed.

### New clean-stack PR #778 — core inference and refit bypasses

PR [#778](https://github.com/MaksimBlud/football-ai/pull/778) is Draft/HUMAN-MERGE only.

- Exact base: #777 HEAD `12a64174341f8d3716c1206ee63d4f4c01ca817d`.
- Exact HEAD: `b2a034614d999683a8c334569dc07eb07b7ac589`.
- Compare: **3 ahead / 0 behind**, exactly three intended files (core V2 module, core V2 tests, frozen-V2 workflow).
- Direct `predict_shadow_residual()`, `predict_candidate()`, and `_artifact_residual_logits()` now each enforce the provider-issued frozen-inference scope before touching model/input data.
- `fit_candidate_artifact()` and `write_candidate_artifact()` now fail closed before inspecting training inputs or creating files. The dormant training fingerprint and V1 fit/prepare/market/result helper re-exports were removed from the V2 module.
- Offline numerical tests explicitly use `SYNTHETIC_TEST_ONLY`; negative tests prove direct-call denial. The original candidate recipe metadata remains unchanged.

Exact-head CI:
- Frozen V2 workflow [#42732823241](https://github.com/MaksimBlud/football-ai/actions/runs/42732823241): Python 3.11 **405 passed** and Python 3.12 **405 passed**; `pip check`, compilation and production `.pkl` diff guards PASS.
- Core Market Anchor V2 validation [#42732823023](https://github.com/MaksimBlud/football-ai/actions/runs/42732823023): **14 passed**, compile and production artifact guard PASS.
- The dedicated core suite has 14 tests. These are offline/synthetic contract tests, not real inference or model-quality evidence.

PR #778 is stacked on #777 → #774 → #742 → #727 → #720. Do not merge or flatten the chain. The #777 parent remains Draft at exact HEAD `12a64174341f8d3716c1206ee63d4f4c01ca817d`, with 391/391 tests on both Python 3.11 and 3.12. The direct quote reader #774 remains Draft at `f4180d8ce4142096f7a2ad1cd86ba95c78b3ae30`, with 390/390 on both versions.

### Fresh actual Original V2 forward runtime audit

Verified GitHub run metadata and jobs, not just prior narrative summaries:

- Original old-season forward [run #42676083517](https://github.com/MaksimBlud/football-ai/actions/runs/42676083517): `schedule`, `main`, exact main SHA above, SUCCESS on 2026-11-09 18:40:27–18:41:09 UTC. All steps completed, including real source ZIP attestation and forward-only preview. Its report has zero saved quotes, zero candidate previews, zero paid provider calls, zero Supabase writes.
- Current-form forward [run #42677383722](https://github.com/MaksimBlud/football-ai/actions/runs/42677383722): `schedule`, `main`, same exact main SHA, SUCCESS on 2026-11-09 18:48:55–18:49:39 UTC. All steps completed. It verified the current-form source archive and 100-event feature-input gate, but had zero saved quotes, zero current-form V2 shadows, no target-outcome reads/scoring, no paid calls and no writes.
- A fresh `main` Actions query from 2026-11-09 18:40 UTC through 2026-11-10 01:05 UTC found no later Original V2 source/forward workflow run. Other main runs in that interval (Multi-Market V2 Cycle, Serie A Results Sync, Serie A Live Cycle) are not evidence of Original V2 inference.
- The latest verified Original V2 runs are source/provenance checks only; **no real prospective V2 forecast was produced**.

### Fresh read-only Supabase pre-match inventory

The only database query in this audit selected `league`, `event_id`, `snapshot_time_utc`, and `commence_time_utc` from `public.odds_snapshots`, with strict predicates `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`. No prices, score/result/settlement columns or target outcomes were selected.

As of 2026-11-10 01:02 UTC:

- Strict pre-match snapshots: **3,915** across all leagues.
- Unique events: **327**.
- New strict pre-match snapshots in the preceding seven days: **0**.
- Future events with a saved strict pre-match quote: **0**.
- Latest strict pre-match snapshot overall: **2026-10-13 14:48:53.042620 UTC** (Serie A).
- Serie A specifically remains 620 snapshots / 63 events; latest timestamp above.

There is no saved quote to admit into a new prospective V2 forecast. No paid quote request or source download was made.

### Rights and confidentiality blockers remain independent

The #720 rights manifest branch records:

- `research_use_permitted=true`, but `research_inference_permitted=false`;
- `provider_issued_ai_inference_license=false`;
- `research_inference_scope=NONE_PENDING_SCOPE_CLARIFICATION`;
- `ai_model_training_permitted=false`, `commercial_use_permitted=false`, `public_product_use_permitted=false`;
- `authorization=null`;
- maximum automated public-source sessions: **2 per rolling seven days**.

The rights manifest is not on main yet; the repository remains public. #720 is still open/Ready at `1b9464834dd5256b7d69499c1443378518dde256` with 10/10 exact-head checks; #727 is still open/Ready on top of #720. Private storage does not itself grant frozen-inference rights. The source/inference pipeline must remain fail-closed until both the private-storage and provider-scope issues are resolved.

### Frozen candidate / scientific gate

Re-read the candidate from main:

- Candidate file Git blob: `ac1303f6b096664983fbf52443bd0a381b23ba21`.
- Embedded candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original feature-builder blob: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- Exactly 19 frozen features, 20×2 weight matrix, 3,799 training rows.
- `active_lambda=0`, `shadow_residual_lambda=1`, `stability_gate_passed=false`, automatic promotion false.
- Feature-input gate and target-outcome evaluation gate remain distinct. The 100 completed fixture identities in the current-form source contract are not 100 forecasts.
- Eligible prospective forecasts: **0/30**. No target outcomes were read. No Brier/LogLoss superiority claim is supported.

### Safety ledger

No main update/merge, repository visibility change, Supabase write/DDL, paid provider request, source download, target-outcome read, refit, weight/feature/lambda change, production `.pkl` change, schedule/cron change, promotion, betting, or other-agent change occurred. The original candidate and its 19-feature/weight contract remain byte-for-byte unchanged.

## 2026-11-10 — Original V2: source-only rights separation, direct forward guards, and fresh runtime inventory

Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository visibility is still **public**. No merge or main update was performed.

### Latest exact-head direct-entrypoint hardening

- **PR #772** now correctly distinguishes *source-only archival* from *frozen-model inference*. `fetch_public_history()` only downloads public historical CSV bytes, so its inner guard now requires `require_personal_research_source_capture_scope()` followed by private-repository storage. It does not require an inference licence. The diagnostic CLI retains its separate inference-rights gate before saved-quote reads, feature construction, or scoring. Exact HEAD `66c02b0e258736dc1be7dc93f0a368b33e78ffb2`, base #727 HEAD `18a3cfda4e83e44aca1252665d01804267d16467`, 10 ahead / 0 behind, five intended files. Exact push #42735375606 and PR #42735378792 both SUCCESS: 390 tests on Python 3.11 and 390 on Python 3.12, pip check/compile/.pkl diff guard PASS. This remains blocked from real source download while the repository is public; no live request was made.
- **PR #779** adds provider-inference and private-storage gates inside both original/current-form `prepare_forward_capture()` builders and the diagnostic `make_report()`, before input iteration, archive callbacks, directory creation, manifest construction, or scoring. Exact HEAD `6002e823e08438c1109aac6374629cf713d97324`, base #778 HEAD `b2a034614d999683a8c334569dc07eb07b7ac589`, 10 ahead / 0 behind, seven intended files. Exact push #42734839489 and PR #42734842832 both SUCCESS: 411 tests on Python 3.11 and 411 on Python 3.12, pip check/compile/.pkl diff guard PASS. The first failed attempt was corrected by moving the existing fixture-identity parametrization back to its intended test and repinning both forward readers to the exact diagnostic-loader blob.
- **PR #778** exact HEAD `b2a034614d999683a8c334569dc07eb07b7ac589` remains the parent of #779. Its exact run #42732823241 passed both Frozen V2 and Market Anchor V2 Shadow Validation jobs; it guards direct low-level inference/refit APIs and removes dormant V1 fit-helper re-exports from the V2 namespace without changing the frozen candidate or contract.
- #772 and #779 are Draft/HUMAN-MERGE only. No PR was merged.

### Fresh main runtime evidence (read-only)

- Original old-season forward run [#42676083517](https://github.com/MaksimBlud/football-ai/actions/runs/42676083517), main SHA above: 71 tests passed; real GitHub source attestation verified 10 pre-prospective CSVs / 3,800 historical results and source artifact `13689701985` (parent run `42651542041`); `quotes_seen=0`, `v2_diagnostic_previews_captured=0`, zero paid calls and zero Supabase writes.
- Current-form forward run [#42677383722](https://github.com/MaksimBlud/football-ai/actions/runs/42677383722), same main SHA: 53 tests passed; source artifact `13681778268`, SHA-256 `f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101`, parent source run `42634501531` completed before verification. Manifest reports 10 old-season CSVs / 3,910 rows plus 110 lagged current-season rows, 100-identity feature-input gate, source status VERIFIED; `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes read/scored false, zero paid calls and zero writes.
- These runs prove source/archive integrity and a zero-quote forward path only. They do not prove a prospective forecast or V2 superiority.

### Fresh strictly pre-kickoff Supabase inventory

Read-only aggregate from `public.odds_snapshots`, selecting only `league,event_id,snapshot_time_utc,commence_time_utc`, with `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= now()`:

- **3,915** strict pre-match snapshots across **327** unique events.
- **0** new strict pre-match snapshots in the last seven days.
- **0** future events with saved pre-match quotes.
- Latest saved snapshot by league: Serie A 2026-10-13 14:48:53 UTC; EPL 2026-10-09 15:25:57 UTC; all other listed leagues no later than 2026-09-11 (RPL 2026-09-05).
- No odds values, scores, result columns, or protected target outcomes were selected.

### Binding rights/security state

- Rights manifest: private noncommercial source-only archival is separately permitted; frozen-model inference remains `false`; provider-issued AI inference licence remains `false`.
- GitHub repository remains public, so private-artifact gates block source ZIP archival and inference. Do not bypass them or download source artifacts until the repository privacy prerequisite is met.
- Supabase table inspection raised a critical advisor finding: RLS is disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No DDL or policy change was made; this is a separate owner-controlled security decision and must not be silently remediated by this research task.
- Original candidate SHA, 19-feature order, weights, scaler/imputer, `active_lambda=0`, `shadow_lambda=1`, NO_BET, and the 30-primary-completed-event outcome gate remain unchanged. Prospective evaluation remains 0/30; no Brier/LogLoss superiority claim is permitted.

### Next execution pointer

Preserve source-only/inference separation. Continue auditing direct original-V2 entrypoints and clean-stack ancestry, but do not duplicate superseded branches. Keep #775 out of integration until its #728–#770 evaluator chain is ported onto the clean #727 ancestry. The current main still has no admissible new quotes; do not spend paid credits, change schedules, or read protected outcomes.


## 2026-11-10 01:45 UTC — corrected direct source-download budget test and exact-head CI

### PR #772 correction

A later edit to PR #772 exposed one test-fixture error that was not present in its earlier 66c02b0 snapshot:

- Failed exact-head run #42736988150 on HEAD e8bac5b8b13ca1c5f5e97bf1ca6156f29e697df7: 427 passed, 1 failed on both Python 3.11 and 3.12.
- The sole failure was in test_direct_public_history_fetch_requires_current_budget_marker_before_http. Production code imports require_current_download_reservation locally from serie_a_v2_public_source_download_budget; the test incorrectly attempted to monkeypatch a nonexistent attribute on serie_a_v2_live_diagnostic_report.
- Corrected only the test to monkeypatch the budget module actually imported by the helper. No production gate was weakened or changed.
- Current PR #772 HEAD: 46025507677dcafa5b42421d5b79a52ff76d6c5a, exact base #727 HEAD 18a3cfda4e83e44aca1252665d01804267d16467; compare 28 ahead / 0 behind, nine intended files.
- Exact-head run #42737911980: SUCCESS. Python 3.11: 428 passed; Python 3.12: 428 passed; pip check, compilation, and production .pkl diff guards PASS.
- PR #772 remains Draft/HUMAN-MERGE only. The passing tests use synthetic permissions and mocked HTTP/budget responses; they are not a live public-source download or permission to bypass the private-repository prerequisite.

### Direct inference/forward stack recheck

- #778 remains exact HEAD b2a034614d999683a8c334569dc07eb07b7ac589, base #777 12a64174341f8d3716c1206ee63d4f4c01ca817d, 3 ahead / 0 behind. Run #42732823241: 405 passed in each Python 3.11/3.12 suite; core V2 validation #42732823023: 14 passed; compile and production-artifact guards PASS.
- #779 remains exact HEAD 6002e823e08438c1109aac6374629cf713d97324, base #778 b2a034614d999683a8c334569dc07eb07b7ac589, 10 ahead / 0 behind. Run #42734842832: 411 passed in each Python 3.11/3.12 suite; pip check, compile, and production-artifact guards PASS.
- These are independent offline/synthetic rights-boundary regressions, not live model inference or model-quality evidence.

### Frozen candidate identity recheck

- Candidate file Git blob remains ac1303f6b096664983fbf52443bd0a381b23ba21 on both main and the #778 branch.
- Embedded original candidate SHA-256 remains a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6.
- Original feature-builder blob remains 401b3a0893371bfa4a488ec92a4a54af2678c8f7 on both main and the #778 branch.
- No change to the 19-feature order, frozen 20×2 weights/scaler/imputer, active_lambda=0, shadow_lambda=1, failed stability gate, or 30-primary-completed-event outcome gate.

### Read-only data/runtime status

Re-inspected successful main runs #42676083517 and #42677383722 and their actual job logs:

- #42676083517: 71 tests passed; real source ZIP attestation verified 10 pre-prospective CSVs / 3,800 historical results; quotes_seen=0, zero previews, zero paid calls, zero Supabase writes.
- #42677383722: 53 tests passed; verified source artifact 13681778268 with SHA-256 f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101, 10 old-season CSVs / 3,910 historical rows plus 110 lagged current-season rows, 100-identity feature-input gate; quotes_seen=0, zero current-form shadows, no target-outcome reads/scoring, zero paid calls and writes.
- Fresh read-only aggregate of public.odds_snapshots using only strict pre-kickoff timestamps: 3,915 snapshots / 327 unique events; 0 new strict pre-match rows in seven days; 0 future events with saved pre-match quotes; latest strict pre-match snapshot 2026-10-13 14:48:53.042620+00.
- No prices, scores, completed results, or protected 2026/27 target outcomes were selected.

### Binding blockers and safety

- Main remains 40887ebb215730190d7a6c7a1693373ec4afcdfc; repository remains public. #720/#727 and all descendants remain open; no PR was merged.
- The rights manifest still permits only narrowly scoped private noncommercial source archival; frozen inference remains unauthorized (research_inference_permitted=false, provider_issued_ai_inference_license=false, authorization=null). Public repository visibility independently blocks private artifact storage.
- Supabase schema inspection still reports RLS disabled on public.teams, public.predictions, public.match_statistics, public.league_prediction_ledger, and public.epl_ai_market_pair_ledger. No DDL or policy changes were made.
- Prospective evaluation remains 0/30; no Brier/LogLoss comparison is admissible and no V2 superiority claim is made.

No main update/merge, repository visibility change, source download, quote read, target-outcome read, Supabase write/DDL, paid provider request, schedule/cron change, refit, threshold tuning, weight/feature/lambda change, production artifact change, promotion, betting, or other-agent change occurred.


## 2026-11-10 07:54 UTC — fresh main, scheduled-source, prematch-Supabase and branch-ancestry audit

### Exact repository and frozen identity

- Fresh default-branch main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository remains public.
- Re-read `PROJECT_CONTINUITY.md` on main and this PR branch before updating this record.
- Candidate file blob is identical on main and the #778/#779 inference-rights stack: `ac1303f6b096664983fbf52443bd0a381b23ba21`.
- Embedded candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Protocol blob is identical on main and that branch: `65729e9639720e67624c1481190aa22ae606f151`.
- Original feature-builder blob is identical on main and that branch: `06393c494e454149e679b2a0826c194de94ed3f5`.
- No candidate, protocol, feature order, weight, scaler/imputer, active/shadow lambda or production artifact change is present in this audit.

### Actual scheduled workflow inventory at 07:54 UTC

Read the main workflow files and the repository's scheduled-run listing (main branch, event=schedule). The configured UTC cron slots remain:

- Current-Form Source Capture: 05:50 UTC.
- Free Real-Quote Diagnostic: 06:13 UTC.
- Original Forward-Only: 08:08 UTC.
- Current-Form Forward-Only: 08:18 UTC.

By 07:54 UTC on Nov 10, the scheduled-run listing contained no Nov 10 run for either 05:50 or 06:13 workflow. Latest observed source runs are still:
- #42634501531, Current-Form Source Capture, 2026-11-09 14:25:18 UTC, SUCCESS, main SHA above.
- #42651542041, Free Real-Quote Diagnostic, 2026-11-09 16:07:28 UTC, SUCCESS, main SHA above.

Latest forward-only runs remain #42676083517 at 18:40:27 UTC and #42677383722 at 18:48:55 UTC on Nov 9, both SUCCESS. The Nov 10 08:08/08:18 slots had not yet arrived at this audit time. Absence of a Nov 10 source run is recorded as "not observed by 07:54 UTC", not as a proven workflow failure. No workflow was manually dispatched and no schedule was changed.

### Fresh strictly pre-kickoff Supabase metadata aggregate

Read-only query against `public.odds_snapshots` selected only `league,event_id,snapshot_time_utc,commence_time_utc`, requiring `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= now()`. No odds values, scores, result columns or protected outcomes were selected.

| League | Strict pre-match snapshots | Unique events | Snapshots last 7d | Future events with saved quotes | Latest snapshot UTC |
|---|---:|---:|---:|---:|---|
| BUNDESLIGA | 394 | 35 | 0 | 0 | 2026-09-11 15:49:52.864729 |
| EPL | 1,135 | 70 | 0 | 0 | 2026-10-09 15:25:57.102061 |
| EREDIVISIE | 410 | 39 | 0 | 0 | 2026-09-11 15:50:20.804995 |
| LA_LIGA | 798 | 52 | 0 | 0 | 2026-09-11 15:45:28.192487 |
| LIGUE_1 | 387 | 35 | 0 | 0 | 2026-09-11 15:49:24.632280 |
| PRIMEIRA_LIGA | 9 | 9 | 0 | 0 | 2026-09-11 16:06:24.367764 |
| RPL | 153 | 15 | 0 | 0 | 2026-09-05 15:07:55.574301 |
| SERIE_A | 620 | 63 | 0 | 0 | 2026-10-13 14:48:53.042620 |
| TURKEY_SUPER_LIG | 9 | 9 | 0 | 0 | 2026-09-11 16:06:26.034182 |
| TOTAL | 3,915 | 327 | 0 | 0 | 2026-10-13 14:48:53.042620 |

This is a metadata-only freshness result. It does not establish any new prospective forecast.

### Open-PR ancestry correction

The direct-entrypoint protections are split across multiple non-equivalent stacks; do not treat them as one linear chain:

- #720 is main-based. #727 is stacked on #720. #742 is stacked on #727. #774 → #777 → #778 → #779 is the direct quote/scoring/refit/forward-builder chain.
- #772 is independently stacked on #727 and adds source-only rights/budget protection inside the diagnostic history downloader.
- #733 → #734 → #735 → #736 → #737 → #738 → #739 → #752 is a separate chain rooted in #731/#730/#729, not the #727/#742/#779 chain. It covers direct source attestation, artifact discovery/download, original-forward dependency triggers and the pytest shell-continuation repair.
- #752 fixes the missing shell continuation in #739; its exact offline validation run #42512771879 passed 330 tests. #739's earlier 329-test run does not validate the corrected shell command.
- #762 is main-based; #773 is stacked on #720 and contains the unique historical-row integrity transplant. Rebase/revalidate after integrating its prerequisites; do not merge the superseded #760 separately.
- #767 is main-based and independent; it must be integrated/rebased before #779 if the shared original-forward identity code conflicts.

All these branches remain HUMAN-MERGE only. Exact-head CI is offline/synthetic contract evidence, not live source access, inference or model-quality evidence. No merge is performed by this task.

### Safety

No source download, manual workflow dispatch, paid provider call, Supabase write/DDL, quote-value read, target-outcome read, production `.pkl` change, refit, threshold tuning, promotion, betting, main update, schedule change or other-agent change occurred in this audit. Prospective evaluation remains 0/30 and no Brier/LogLoss superiority claim is permitted.


## Artifact-byte SHA verification — 2026-11-10 09:52 UTC

This addendum records a read-only verification of the actual Nov 9 GitHub Actions ZIP bytes, beyond the run/artifact metadata already recorded above.

### Current-form source archive #13681778268

- Parent run: [#42634501531](https://github.com/MaksimBlud/football-ai/actions/runs/42634501531), main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`, successful.
- GitHub artifact digest and independently computed ZIP SHA-256 both equal `f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101`.
- Manifest SHA-256: `3c5264a9cedd4fdf4e2875c4843601f009226c2b5a0d72956493617498ea79fd`.
- All **11/11** archived CSV raw-byte SHA-256 values match the manifest, including the ten frozen historical files and the 2026/27 current-season file. The current-season CSV was hashed as opaque bytes only; no score, result, goal, or outcome field was parsed or inspected during this verification.
- The current-form forward artifact #13700368254 contains a nested copy of this source ZIP; its independently computed SHA-256 is the same `f4fb869b...` digest.

The source manifest records the separate metadata-only feature-input gate as passed (100 identities at source capture) and 110 completed prior-day current-season CSV rows. This is source-integrity evidence only. It does not open the target-outcome evaluation gate.

### Forward-only runtime remains empty

- Current-form forward run [#42677383722](https://github.com/MaksimBlud/football-ai/actions/runs/42677383722) completed SUCCESS on the same main SHA. Its exact report has `quotes_seen=0`, `rows=[]`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, and `target_outcomes_scored=false`.
- Original old-season forward run [#42676083517](https://github.com/MaksimBlud/football-ai/actions/runs/42676083517) also completed SUCCESS, with `quotes_seen=0`, `future_quotes_checked=0`, and `v2_diagnostic_previews_captured=0`.
- The read-only Supabase quote aggregate still reports 3,915 strictly pre-kickoff snapshots / 327 events, zero new in seven days, zero future events with a saved pre-kickoff quote, and latest quote 2026-10-13 14:48:53 UTC.
- At the 2026-11-10 09:52 UTC audit, the latest repository-wide Actions run listing and latest scheduled-run listing contained no later V2 source/diagnostic/forward run IDs than the four successful Nov 9 runs recorded above. This is a run-list observation, not proof of why the Nov 10 schedules did not register.

### Confidentiality and rights remain binding blockers

The repository remains public. The downloaded source artifact proves that its current-season CSV bytes were present in a public-repository Actions artifact. The #727 private-storage helper explicitly fails closed for public repositories; its branch remains unmerged. SHA verification proves integrity, not confidentiality. Do not treat this archive as a new permission to publish, infer, or evaluate.

The source-only rights scope in #727 is private, noncommercial archival/validation only. Frozen V2 inference remains explicitly false/unresolved. The separate target-outcome gate remains **0/30**; no target outcomes were read or scored. The #720 → #727 manual integration order remains binding.

No source download was initiated by this audit; no quote was read individually; no target outcome was parsed; no Supabase write/DDL, paid request, production `.pkl` change, model refit, threshold change, promotion, merge, or main update occurred. HUMAN-MERGE only.


## 2026-11-10 10:49 UTC — source-window deadline and fresh run-list audit

### Current main and frozen model identity

- Current `main`: `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Original candidate Git blob: `ac1303f6b096664983fbf52443bd0a381b23ba21`; candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Original protocol Git blob: `65729e9639720e67624c1481190aa22ae606f151`.
- Original feature builder Git blob: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- Candidate remains 19 features, 20x2 weights, 3,799 training rows through 2026-06-30, `active_lambda=0`, `shadow_residual_lambda=1`, stability gate FAILED, refit/promotion disabled. No candidate/protocol/feature-builder change.

### Nov 10 scheduled-run audit

The four main-branch V2 workflows were re-read directly from main:

| Workflow | UTC schedule | Latest successful run observed |
|---|---:|---|
| Current-Form Source Capture | 05:50 | #42634501531, Nov 9 14:25:18Z |
| Free Real-Quote Diagnostic | 06:13 | #42651542041, Nov 9 16:07:28Z |
| Original Forward-Only Preview | 08:08 | #42676083517, Nov 9 18:40:27Z |
| Current-Form Forward-Only Preview | 08:18 | #42677383722, Nov 9 18:48:55Z |

At 2026-11-10 10:49:43Z, the repository-wide `event=schedule, branch=main` run listing contained no Nov 10 run ID for any of these four workflows. This is an observed absence of registered runs, not proof of the cause. No workflow was manually dispatched and no schedule was changed.

### Source archive freshness deadline

The latest verified current-form source archive is artifact **13681778268**, created 2026-11-09 14:26:19Z, digest `sha256:f4fb869be6e065ca611f012fe21b6d1eafe22434c60ced3a2e7b7ea6c5602101`. Its successful main parent run **42634501531** completed at 14:26:23Z. The manifest's source observation time is **2026-11-09 14:26:18.118320Z**.

The unchanged current-form contract allows a source observation no more than 24 hours before a quote. Therefore this archive's source-age eligibility boundary is **2026-11-10 14:26:18.118320Z**. At this audit time, approximately **3h36m35s** remained. A quote after that boundary cannot use this archive; no backfill is allowed. Do not manually rerun the downloader to refresh it: the source budget/private-storage prerequisites remain unmerged and no new provider permission was granted.

### Corrected feature-input count interpretation

The real source-capture job log reports:
- `completed_primary_events=100` — the metadata-only Supabase feature-input gate count;
- `current_season_completed_prior_day_rows=110` — the validated prior-day rows in the captured current-season CSV.

These are different quantities. **100**, not 110, is the observed metadata gate count in that source run. Both exceed the feature-input minimum of 30, but neither count is a prospective forecast or opens the separate target-outcome gate.

The current-form forward run #42677383722 independently verified the source archive and parent provenance, ran 53 tests, then reported `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, and `target_outcomes_scored=false`. The original forward run #42676083517 ran 71 tests, verified the ten historical source files / 3,800 historical rows, and reported `quotes_seen=0`, `future_quotes_checked=0`, and zero V2 previews. These are real runtime/guard proofs, not model-quality evidence.

### Fresh read-only Supabase pre-match aggregate

A new read-only query selected only `league,event_id,snapshot_time_utc,commence_time_utc` and required `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`:

| Metric | Value |
|---|---:|
| Strictly pre-match snapshots | 3,915 |
| Unique events | 327 |
| Strictly pre-match snapshots in last 7 days | 0 |
| Future events with an already-saved valid pre-match quote | 0 |
| Latest valid pre-match snapshot | 2026-10-13 14:48:53.042620Z |

No odds values, score/result fields, or protected target outcomes were selected. The prospective cohort remains at **0 eligible forecasts**; the 30-forecast outcome-read gate remains CLOSED.

### Historical-row guard PR duplication correction

A fresh exact file-patch comparison shows #760 and #773 both change the same two files (`serie_a_v2_asof_feature_manifest.py` and its test file), with identical validator code hunks and the same three regression cases (reversed alias duplicate, non-date timestamp, and finite integer statistics). They are duplicate carriers of the same historical-row guard, not two independent fixes.

- #760 is main-based and its exact HEAD `8f4837fbd9a4b403252b3c6618a58e7fa0fbabca` has 7/7 returned PR workflow runs SUCCESS.
- #773 is stacked on #720 and its exact V2 frozen-test run #42707544006 is SUCCESS.
- Do not merge both. Select one carrier during manual integration; if #773 is retained on the #720 stack, #760 remains a duplicate Draft. No PR state or merge was changed in this audit.

### Safety

No source download, manual dispatch, paid request, Supabase write/DDL, quote-value read, target-outcome read, production `.pkl` change, model refit, threshold tuning, promotion, bet, merge, main update, schedule change, or other-agent change occurred in this audit. The source archive's remaining freshness window is an operational deadline, not permission to bypass the provider budget or inference-rights gate.


## 2026-11-10 12:06 UTC — Football-Data policy recheck and fail-closed source-capture update

### Official policy page changed

A fresh read of the official Football-Data data page at `https://football-data.co.uk/data` shows `Updated: 10/11/26`. The current page describes the free CSV/Excel data as intended for private individuals and excludes commercial or data-training products using automated bots, scrapers, or AI.

The previous rights manifest review was recorded on 2026-11-07 against a page date of 2026-11-06. That review is now superseded. The current page does not give this automated AI workflow a sufficiently clear source-capture authorization.

### Conservative code/test carrier

New Draft PR #780 is stacked on #727:

- Parent #727 HEAD: `18a3cfda4e83e44aca1252665d01804267d16467`.
- PR #780 HEAD: `48f55b6ef4dc40879d5232ac78ce55df51d2dce4`.
- Exact comparison: 10 commits ahead, 0 behind its parent.
- Exact V2 CI run #42812927009: both `shadow-tests` and `py312-lock-tests` SUCCESS.
- Each Python suite reports 388 passed; the production `.pkl` guard also passed.

The first run #42812730024 exposed three regression issues (two stale source-rights blob pins and a future-clock fixture made stale by the new test clock). Those were corrected in the later commit; the final exact HEAD above is the one with 2/2 SUCCESS.

PR #780 changes only the source-rights manifest/helpers, their SHA pins, tests, the V2 test-workflow trigger for this stacked base, and this policy-recheck note. It does not change the candidate, features, weights, scaler/imputer, training fingerprint, lambda values, or production artifacts.

### Rights state after recheck

The PR sets:

- `research_source_capture_permitted=false`;
- `research_source_capture_scope=NONE_PENDING_PROVIDER_CLARIFICATION`;
- `research_inference_permitted=false`;
- `provider_issued_ai_inference_license=false`;
- `ai_model_training_permitted=false`.

This is a conservative internal fail-closed decision pending provider clarification, not a legal conclusion about every form of manual personal research. The two-session weekly limit is a ceiling, not a grant of permission. The repository is still public; the separate private-storage gate remains required if a future clarification permits source archival.

PR #780 remains Draft/HUMAN-MERGE only and must not be merged before its parent #727. The sibling quote-cutoff and direct-entrypoint PRs require fresh exact-head validation after their parent chain is integrated.

### Runtime and data status

The Nov 10 scheduled windows checked for Current-Form Source Capture (05:40–06:30 UTC) and the two forward previews (08:00–08:35 UTC) still had no V2 schedule run IDs. This records absence of registered runs only; it does not infer the cause. No workflow was manually dispatched and no schedule was changed.

The latest read-only Supabase aggregate remains 3,915 strictly pre-kickoff snapshots / 327 events, zero snapshots in the last seven days, zero future events with saved pre-match quotes, and latest saved pre-match snapshot 2026-10-13 14:48:53.042620 UTC. No odds values or target outcomes were selected.

The last source archive's 24-hour source-age boundary remains 2026-11-10 14:26:18.118320 UTC, but no refresh is authorized under the current policy/privacy state. No source download or archive upload was performed.

### Safety and model status

The main SHA remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; protocol and feature-builder blobs remain unchanged. The original 19-feature / 20x2 candidate, `active_lambda=0`, `shadow_lambda=1`, and FAILED stability gate remain intact.

No source CSV was downloaded; no quote value or protected target outcome was read; no prospective forecast was created; target-outcome gate remains 0/30. No paid request, Supabase write/DDL, merge, main update, production `.pkl` change, refit, threshold change, promotion, bet, schedule change, or other-agent change occurred.


### Gate-count distinction — do not conflate the 30-event and 30-forecast gates

The frozen original V2 protocol's `first_outcome_read_gate` is defined in terms of **30 completed primary-league events**. The current-form source workflow has a separate **feature-input gate** with the same numeric minimum; the last source-capture log recorded 100 metadata-only completed-primary event identities for that feature-input gate. That 100 is not a count of prospective forecasts and does not itself authorize reading protected target outcomes.

The current-form policy also has a distinct **target-outcome evaluation gate** requiring 30 eligible completed prospective forecasts. Its count remains **0/30** because no prospective V2 forecasts have been captured. These gates must not be substituted for one another. No protected 2026/27 target outcomes were read in this audit; no claim is made that the original V2 outcome-read gate has been exercised or that the current-form evaluation gate is open.


## 2026-11-10 13:53 UTC — scheduled source capture completed after the rights recheck; no quote or forecast

This addendum supersedes the earlier 12:06 UTC statement that no November 10 source run had been registered. The scheduled workflow did run later on the unchanged public main; it was not manually dispatched by this audit.

### Exact real runs on main

- Current-Form Source Capture: [run #42827889788](https://github.com/MaksimBlud/football-ai/actions/runs/42827889788), event `schedule`, created 13:48:21Z, completed 13:49:20Z, exact main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Job `capture-current-form` succeeded; its offline source tests were **19 passed**.
- Current-Form Forward-Only: [run #42828048742](https://github.com/MaksimBlud/football-ai/actions/runs/42828048742), event `workflow_run`, created 13:49:24Z, completed 13:50:09Z, same main SHA. Its frozen/source/no-outcome tests were **53 passed**.

### Independently verified source artifact bytes

The source run uploaded public GitHub Actions artifact **13770560196**, 439,422 bytes, retention through 2027-02-08 13:48:21Z, GitHub digest `sha256:f29363e28775032937108d102da1dda1ca2d5c1aa0f921cb4518bf3a82e9aec6`. The downloaded ZIP's independently calculated SHA-256 matches that digest exactly.

The ZIP contains 10 frozen historical Serie A CSVs, the 2026/27 CSV, and one JSON manifest. The manifest SHA-256 is `0f8edf23c47c4f59cf152b4386299a5f827b2c934c268f6b71ec0ea33f770da4`. All **11/11** CSV byte hashes independently match their manifest entries. Current-season CSV SHA-256 is `91f517fedb41215a32e80faa8f4ec44e26d970e557c6c120a664686dbc4d22f0`. This audit hashed raw bytes only; it did not parse current-season CSV rows or inspect any 2026/27 score/result.

The manifest records:
- feature-input gate: **110** metadata-only completed primary event identities (minimum 30); only `match_date,home_team,away_team` were selected;
- current-season prior-day rows: **110**;
- original frozen candidate SHA-256 unchanged: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- original feature-builder blob unchanged: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`;
- source observed at 13:49:15.294332Z and archive created at 13:49:15.307474Z;
- `eligible_for_current_form_forward_shadow=false`, target-outcome gate closed, no outcomes read/scored, no paid provider calls, and no Supabase writes.

The earlier 100 metadata identities were from the prior source run; the current run's manifest now records 110. The 110 feature-input identities are not 110 prospective forecasts and do not open either outcome-read/evaluation gate.

### Forward result and quote availability

The forward job independently verified the exact source artifact and its successful main parent. It reported source age 45 seconds, `fresh_for_new_quote=true`, but:
- `quotes_seen=0`;
- `v2_current_form_shadow_captured=0`;
- all blocked-reason counters were zero because no quote rows were available to classify;
- `target_outcomes_read=false` and `target_outcomes_scored=false`;
- no model refit, promotion, bet, production write, Supabase write, or paid request.

Thus this is new source-integrity/feature-input runtime evidence, **not** a new V2 forecast or model-quality result. Source-before-quote ordering is proven for the source archive itself, but there is still no source-before-quote *quote pair* because no quote was seen.

### Fresh read-only Serie A pre-match quote inventory

The live Supabase aggregate required `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`, filtered only `league='SERIE_A'`, and returned:

| Metric | Value |
|---|---:|
| Strict pre-match snapshots | 620 |
| Unique events | 63 |
| New strict pre-match snapshots in the last 7 days | 0 |
| New strict pre-match events in the last 7 days | 0 |
| Future events with saved pre-match quotes | 0 |
| Latest strict pre-match quote | 2026-10-13 14:48:53.042620Z |

No odds values or outcome columns were selected.

### Rights/privacy discrepancy requiring HUMAN-MERGE

The official Football-Data data page now states that the free CSV/Excel data are intended for private individuals only and excludes commercial or data-training products using automated bots, scrapers, or AI. The updated page was checked at 13:53 UTC; see [official policy page](https://football-data.co.uk/data). The source-capture run above nevertheless executed from old main code after the policy recheck and uploaded its source ZIP to a public repository artifact with 90-day retention. This was an existing scheduled main workflow, not a manual action by this audit; the artifact was not deleted or altered.

The rights/privacy fixes remain unmerged. PR #720 adds the fail-closed preflight and shared download budget; #727 adds private-storage and quote preflight; #780 updates the source-rights decision to block automated capture pending provider clarification. Their current exact heads remain:
- #720 `1b9464834dd5256b7d69499c1443378518dde256`;
- #727 `18a3cfda4e83e44aca1252665d01804267d16467`;
- #780 `48f55b6ef4dc40879d5232ac78ce55df51d2dce4`.

**Do not manually dispatch or otherwise trigger another source download.** Keep automated source capture and all V2 inference blocked pending provider clarification and HUMAN-MERGE of the fail-closed chain. Do not change the existing schedule in this research branch; no schedule or other-agent setting was changed by this audit. The public artifact is a confidentiality/rights issue for owner review; no artifact deletion was attempted.

### Frozen-model and evaluation status

The original protocol blob remains `65729e9639720e67624c1481190aa22ae606f151`; original candidate SHA, 19 feature order, weights, scaler, imputer, 3,799-row training fingerprint, `active_lambda=0`, `shadow_lambda=1`, and FAILED stability gate remain unchanged. The original protocol's first outcome-read gate is 30 completed primary-league events; the current-form policy separately requires 30 completed eligible prospective forecasts for its target evaluation gate. No protected 2026/27 target outcomes were read in this audit. No Brier/LogLoss result was generated; no superiority claim is justified.

No main ref, schedule, Supabase row/schema, production `.pkl`, other agent, or automation setting was changed. No merge, paid API request, or Supabase write/DDL occurred.


## 2026-11-10 19:02 UTC — extended live-access hold to the frozen-candidate recovery workflow

Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The original frozen candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features, original weights/scaler/imputer, `active_lambda=0`, `shadow_lambda=1`, and failed stability gate are unchanged.

### New gap found and closed in PR #781

The separate `Recover Frozen Market Anchor V2 Candidate` workflow was not among the four daily live workflows previously held. It has `workflow_dispatch` and PR triggers and its rebuild step downloads the ten 2016/17–2025/26 Football-Data CSVs and reconstructs the frozen training artifact. Although this path did not write production `.pkl`, it still performed automated provider downloads and a reconstruction/refit while the provider's AI/data-training scope remained unresolved.

PR #781 now also holds this fifth workflow, without changing its triggers or adding/removing any schedule:
- workflow-level `MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=false`;
- the source-download/rebuild and subsequent proof steps require the same fail-closed flag;
- candidate artifact upload is gated;
- the workflow's offline V2 feature/candidate checks remain active;
- the legacy saved-cohort post-outcome replay test suite is no longer invoked by this recovery workflow;
- the production `.pkl` before/after hash check remains active.

### Exact-head proof

PR #781 HEAD: `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`, 27 commits ahead / 0 behind fresh `main`, seven changed files. Exact PR checks: **8/8 SUCCESS**:
- Frozen V2 Shadow Tests [#42881013776](https://github.com/MaksimBlud/football-ai/actions/runs/42881013776) — **92 passed**; production `.pkl` diff guard PASS.
- Candidate recovery workflow [#42881013880](https://github.com/MaksimBlud/football-ai/actions/runs/42881013880) — SUCCESS. Offline tests and frozen source checkout ran; the data rebuild, checksum proof dependent on its output, and artifact upload were all **SKIPPED** because the flag is false; production `.pkl` before/after check PASS.
- Serie A [#42881013628](https://github.com/MaksimBlud/football-ai/actions/runs/42881013628) — SUCCESS.
- Bundesliga [#42881013669](https://github.com/MaksimBlud/football-ai/actions/runs/42881013669) — SUCCESS.
- Eredivisie [#42881013674](https://github.com/MaksimBlud/football-ai/actions/runs/42881013674) — SUCCESS.
- Ligue 1 [#42881013797](https://github.com/MaksimBlud/football-ai/actions/runs/42881013797) — SUCCESS.
- Research [#42881013676](https://github.com/MaksimBlud/football-ai/actions/runs/42881013676) — SUCCESS.
- Product [#42881014040](https://github.com/MaksimBlud/football-ai/actions/runs/42881014040) — SUCCESS.

This is workflow/contract safety evidence only, not a new V2 forecast or model-quality result. The four daily live workflows and the recovery workflow remain active on `main` until #781 is manually merged. No PR was merged, no main ref or schedule was changed, no provider CSV was downloaded in this recovery run, no quote or protected target outcome was read, no paid provider call or Supabase write/DDL occurred.

### Fresh strict pre-match quote inventory

Read-only Supabase aggregate on `public.odds_snapshots` used only `league`, event IDs, and timestamps, with `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`:
- all leagues: 3,915 strict pre-match snapshots / 327 events;
- Serie A: 620 snapshots / 63 events;
- new strict pre-match snapshots/events in the last seven days: 0 / 0;
- future events with saved strict pre-match quotes: 0;
- latest saved Serie A quote timestamp: `2026-10-13 14:48:53.04262+00` UTC.

The current Football-Data fair-use wording continues to block assuming that free CSV access grants permission for automated AI/data-training use. No source collection was restarted. A new source requires explicit rights/terms compatible with this research or a different licensed/open source with documented permitted use.

PR #781 remains OPEN / Ready for review / HUMAN-MERGE only. No merge performed.


## 2026-11-10 21:00 UTC — free-source alternative feasibility review

Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The GitHub branch metadata reports `protected=false`; no repository setting was changed. HUMAN-MERGE remains a manual owner action.

### Exact V2 branch/runtime status

- PR #781 remains OPEN / Ready for review at `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`; its exact 8/8 PR checks remain successful, including the recovery workflow's expected skipped download/rebuild/upload steps while live access is false.
- PR #778 is at `60d1025e9556cdce05f93b9a71ce46d4d06096cb`; its exact frozen V2 tests and shadow validation succeeded (416 tests in the frozen suite).
- PR #779 is a descendant of the current #778 head (compare: 28 ahead / 0 behind) at `3e936d64b1f490b8c8dc31951b35e446096ca94c`. Exact run [#42892646330](https://github.com/MaksimBlud/football-ai/actions/runs/42892646330) passed both Python 3.11 and 3.12 suites: **430 passed** in each; dependency check and production `.pkl` diff guard passed. Earlier failed push runs on superseded intermediate commits are not the final exact-head result.
- No new main-branch Original V2 source-capture, quote-diagnostic, or forward-only runtime run appeared in the latest Actions run page; the recent V2 runs were PR validation runs. This is an observed run-list absence, not a claim about why scheduled runs did not register.

### Read-only pre-match inventory

A fresh read-only aggregate on `public.odds_snapshots` selected only league, event IDs and timestamps, with `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= NOW()`. It returned the same inventory as the previous audit:

- 3,915 strict pre-match snapshots / 327 events across leagues;
- Serie A: 620 snapshots / 63 events;
- 0 new strict pre-match snapshots and 0 new events in the last seven days;
- 0 future events with a saved strict pre-match quote;
- latest saved Serie A quote: `2026-10-13 14:48:53.04262+00` UTC.

No odds values, scores, results, or settlement fields were selected.

### Free-source feasibility against the unchanged 19-feature contract

The original 19 football features require lagged points/goals plus corners-for/against and yellow/red-card history (including the unchanged 5/10-match and venue variants). A candidate source must provide all of those fields with lawful, reproducible access; partial coverage is not a substitute for the frozen feature contract.

1. **OpenFootball / football.json** — its repository declares CC0/public-domain data and documents fixtures/results with date, teams and full-time score. It does not provide per-match corners or yellow/red-card statistics, so it can support fixture/result identity only, not the complete 19-feature V2 input.  
   https://github.com/openfootball/football.json

2. **SportAPI.ai** — its current terms allow use in the user's own websites, apps, analysis and products, prohibit raw-data feed resale/redistribution, and its advertised free tier is 1,000 requests/day and 7,000/month. The reviewed football match-stat documentation lists shots, shots on target, fouls, passes, tackles and saves, but does not document corners; coverage depth also varies by competition. It therefore does not currently establish full original-V2 feature coverage. No account was created and no API call was made.  
   https://sportapi.ai/terms  
   https://sportapi.ai/docs

3. **API-Football / API-SPORTS** — the provider advertises a free 100-request/day plan with access to endpoints but limited historical seasons. Its terms say it does not grant a general licence for use/publication of supplied data in user products and leave third-party competition rights to the user to verify. This may merit written clarification for internal frozen-model research and current-season stats, but it is not treated as cleared for automated AI source capture/inference. No account, key, or API request was used.  
   https://www.api-football.com/terms  
   https://www.api-football.com/

4. **Cornerflick** — its data page advertises season CSV/JSON and match statistics including corners under CC BY 4.0, but its Terms (updated 2026-11-09) restrict use to personal non-commercial reading and prohibit scraping, harvesting or bulk downloads except as permitted by law. The data page also says the CC BY licence covers Cornerflick's compilation while underlying match facts remain subject to provider terms. These conflicting scopes require written clarification; no automated capture is permitted by this project pending that clarification.  
   https://cornerflick.com/data  
   https://cornerflick.com/terms

5. **SportScore** — its terms restrict site information to personal use and prohibit automated requests, scraping, embedding, aggregation and substantial database extraction without express consent. It is not an approved automated source.  
   https://sportscore.com/terms/

6. **Football-Data.co.uk** — the 2026-11-10 official-page review is already recorded in PR #780. The project continues to keep automated source capture and frozen inference fail-closed pending provider clarification or an applicable written licence.

### Binding source decision

No reviewed alternative currently proves both (a) complete coverage of the original 19 feature inputs and (b) clear permission for automated archival and frozen-model research/inference. Do not wire a partial source, do not impute away systematic missing corners/cards, and do not relax the frozen feature contract. The next valid path is written provider clarification/licensing or a genuinely open dataset whose licence and field coverage explicitly satisfy the complete contract.

This was a documentation-only feasibility review. No external sports API was called, no account/key was created, no source bytes were downloaded, no quote or protected 2026/27 outcome was read, no Supabase write/DDL occurred, and no model/candidate/weight/feature/lambda/production file/schedule/main change was made.


### Candidate-specific pre-match snapshot check — 2026-11-10

A second read-only Supabase aggregate filtered `public.product_prediction_snapshots` to the exact frozen V2 candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, and required `generated_at_utc < commence_time_utc` and `generated_at_utc <= NOW()`. It selected only league, row count, distinct event count and latest generation timestamp. Result: **zero rows**. No original-candidate strict pre-match prediction snapshots are currently recorded in this product snapshot table. No probability, target outcome, score, result or settlement field was selected.

## 2026-11-10 21:55 UTC — exact main runtime, rights, and additional open-source review

### Fresh main and frozen candidate

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Frozen candidate Git blob remains `ac1303f6b096664983fbf52443bd0a381b23ba21`; embedded artifact SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- The candidate still has the unchanged 19-feature order, 3,799 training rows, `active_lambda=0`, `shadow_residual_lambda=1`, `stability_gate_passed=false`, and `automatic_promotion=false`.
- Historical feature-builder Git blob remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.

### Re-read of actual main-branch runtime logs

The following are main-branch scheduled runs, not PR test runs:

- Original Forward-Only [#42853738496](https://github.com/MaksimBlud/football-ai/actions/runs/42853738496), created 2026-11-10 16:21:37 UTC, exact main SHA above: 71 tests passed; 10 historical source files / 3,800 rows were attested and the parent archive SHA verified. Runtime JSON reports `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`, `supabase_writes=0`, and `paid_provider_calls=0`. Artifact #13782226394 SHA-256: `24906d82f8d15b6597ba0227be9253b460d55038116a1b03b85bb21443a42d94`.
- Current-Form Source Capture [#42827889788](https://github.com/MaksimBlud/football-ai/actions/runs/42827889788), created 2026-11-10 13:48:21 UTC: 19 tests passed; the lagged feature-input gate recorded 110 completed prior-day identities and 11 source files (10 historical files plus current-season source). Runtime reports `target_outcomes_scored=false`, `supabase_writes=0`, and `paid_provider_calls=0`. Artifact #13770560196 SHA-256: `f29363e28775032937108d102da1dda1ca2d5c1aa0f921cb4518bf3a82e9aec6`. This is feature-input/source-attestation evidence only, not the separate prospective outcome gate.
- Current-Form Forward-Only [#42854487569](https://github.com/MaksimBlud/football-ai/actions/runs/42854487569), created 2026-11-10 16:26:06 UTC: 53 tests passed; the 11-file parent source archive and SHA were verified, but runtime reports `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, and `production_or_supabase_writes=0`. Artifact #13780824313 SHA-256: `62196fcf3dfb6b384d5f1f4c11b532073ffe7bff57f06bec712afa34336cdfeb`.
- Free Real-Quote Diagnostic [#42837720155](https://github.com/MaksimBlud/football-ai/actions/runs/42837720155): 53 tests passed; it made 10 public CSV HTTP requests, but found `quoted_fixtures=0`, `FUTURE_QUOTE=0`, `eligible_for_frozen_prospective_cohort=false`, and `feature_rows_with_all_19_observed=0`. No paid-provider request or Supabase write occurred. Artifact #13773563645 SHA-256: `c04e21994365159382372f8596956dfaf1766c9170285773346778e291b6e823`.

PR #781 was opened at 2026-11-10 15:55:27 UTC. The main Current-Form Forward-Only run #42854487569 therefore executed after the hold PR was opened but before it was merged. This is direct evidence that opening a PR does not stop main-branch workflows. The run itself created no quote-based shadow and read/scored no target outcome.

The existing public Actions artifacts #13770560196, #13773563645, and #13780824313 remain available until their recorded expiry. Their contents were not downloaded or inspected in this audit. In particular, the current-form artifact's `sources_used` directory was not opened. PR #781 gates future live steps/uploads only; it does not retroactively remove existing artifacts.

### Additional free-source feasibility review

No reviewed source is approved for the frozen V2 pipeline:

1. **open-matchday** ([README](https://github.com/oladeeayo/open-matchday/blob/master/README.md)): it provides free 2026/27 fixtures/results for 75 competitions, but its own coverage table says shots/fouls/cards and corner totals are present in only about 19% of result rows. It combines OpenLigaDB, fixturedownload, ESPN, Football-Data, FotMob, and Soccerway; provider rights remain with those providers. Its terms describe informational/non-commercial use and it has no OSI-approved data licence. It cannot provide a complete, consistently licensed 19-feature input set.
2. **Footiqo** ([free data page](https://footiqo.com/football-data/), [terms](https://footiqo.com/terms-of-use/), [premium dataset terms/coverage](https://footiqo.com/premium/premium-football-database/)): its free pages support CSV/Excel export and describe AI/ML research, but the public Terms restrict copying/reproduction and do not grant automated bulk extraction. The site states there is no public API and automated scraping/crawling/bulk extraction requires prior written authorisation. A free Big-Five sample is offered, while the complete multi-season 150,000+ match database is paid (€49.99). No download, account, or contact was made.
3. **Gamblistics Lab sport-statistics** ([dataset card](https://huggingface.co/datasets/gamblistics-lab/sport-statistics)): declares CC BY-NC 4.0 and documents 1,190 match rows / 810 match-stat rows with corners and cards, but describes recent EPL coverage only; this is not the Serie A 2016/17–2025/26 history or a complete original-V2 source. Its upstream rights were not independently established.
4. **WideMan football_matches** ([dataset card](https://huggingface.co/datasets/WideMan/football_matches)): the visible sample is EPL-only and the page does not declare a dataset licence. It is not eligible for automated capture or model use.

No source bytes were downloaded and no external sports API was called for this review. Do not substitute partial rows, infer missing corners/cards as zero, or change the frozen feature contract.

### Fresh read-only Supabase inventory

Queries used only pre-kickoff odds timestamps, league labels, event IDs, and candidate SHA/time metadata:

- `public.odds_snapshots`: 3,915 strict pre-match snapshots / 327 events across leagues; 0 new in the last seven days; 0 future fixtures with saved quotes. Serie A remains 620 snapshots / 63 events, latest `2026-10-13 14:48:53.04262+00` UTC.
- `public.product_prediction_snapshots`: 0 strict pre-match rows for candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- No odds values, scores, results, settlement fields, or protected target outcomes were selected.

### Exact PR #781 integration state

- PR #781 remains OPEN / Ready for review at exact HEAD `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`, based directly on main.
- All 8 exact-head checks are SUCCESS; Frozen V2 suite: 92 passed; recovery workflow's source download, rebuild, and artifact upload steps were skipped under the false live-access flag; production `.pkl` before/after guard passed.
- Main remains unmodified and its live workflows remain active until manual merge.
- Do not merge PR #720 as currently based on main without first integrating #781 and then rebasing/revalidating #720 on the new main. #720 changes the same workflow files and its older source-only manifest must not undo the hold or re-enable capture. The subsequent #727 private-storage gate and #780 updated rights block must be integrated and revalidated before any source access can be reconsidered.
- HUMAN-MERGE only. No PR was merged by this audit.

### Supabase security advisory recheck

At 2026-11-10 21:51 UTC, Supabase Security Advisor still reports five public tables with RLS disabled (`teams`, `predictions`, `match_statistics`, `league_prediction_ledger`, `epl_ai_market_pair_ledger`) and four tables with RLS enabled but no policies (`competitions`, `match_stats`, `matches`, `standings`). No remediation SQL was executed; enabling RLS without policies could block the application. This is a separate security issue, not V2 evidence.

No model, weights, feature order, lambda, schedule, production `.pkl`, Supabase row/schema, repository visibility, or other-agent configuration was changed.


## 2026-11-10 23:47 UTC — fresh-main entrypoint, exact-head CI, and PR ancestry re-audit

### Fresh main and original candidate

- Re-read refs/heads/main directly from GitHub: 40887ebb215730190d7a6c7a1693373ec4afcdfc.
- Original frozen candidate file research/models/market_anchor_v2_serie_a_frozen_candidate.json still has Git blob ac1303f6b096664983fbf52443bd0a381b23ba21 and embedded SHA-256 a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6.
- Its exact 19-feature order, 20×2 weight matrix, 3,799 training rows, active_lambda=0, shadow_residual_lambda=1, failed stability gate, and no-promotion flag are unchanged.

### Main workflow still live until HUMAN-MERGE

Fresh main's .github/workflows/serie-a-v2-forward-preview.yml (blob 48ce3b0d8e31c4cf293b94500e9c320047311467) still has workflow_dispatch, daily 8 8 * * * schedule, a workflow_run trigger after Serie A Odds Snapshots only when the paid snapshot workflow was itself manually dispatched, job-level Supabase/GitHub credentials, source attestation, saved-quote forward capture, and if: always() artifact upload with no live-access hold on main.

The free diagnostic workflow still has 13 6 * * *; current-form source capture still has 50 5 * * *. The paid Serie A Odds Snapshots workflow was re-read and has only workflow_dispatch, with no cron. No paid workflow was dispatched and no provider request was made in this audit.

PR #781 remains OPEN / Ready for review / HUMAN-MERGE only at exact HEAD c48e0c2f6a486c9320b04c7a1693373ec4afcdfc. Its description reports 8/8 exact-head CI success. Independently opened recovery workflow run #42881013880, which is on that exact HEAD: offline V2 tests and production .pkl hash guard succeeded; candidate rebuild, proof, and research-artifact upload were all correctly skipped under the false live-access flag. This is a workflow-safety result, not an inference result. Main remains unchanged, so the hold is not active on main until the owner manually merges #781.

### Current V2 hardening PRs — exact current heads and ancestry

- PR #778 current metadata HEAD is 3ecbef08babe4c24cb1a22e492e83a08fad3be5b, based on #777 HEAD 12a64174341f8d3716c1206ee63d4f4c01ca817d (10 ahead / 0 behind). Exact push run #42919157425 is on that exact HEAD: both Python 3.11 and 3.12 jobs succeeded, each reporting 413 passed, and both production .pkl guards passed.
- PR #779 current metadata HEAD is 3e936d64b1f490b8c8dc31951b35e446096ca94c, with base SHA b2a034614d999683a8c334569dc07eb07b7ac589. Exact PR run #42892646330 is on that exact HEAD: both Python 3.11 and 3.12 jobs succeeded, each reporting 430 passed, and both production .pkl guards passed.
- New ancestry correction: comparing #778's current HEAD to #779's current HEAD returns diverged: #779 is 28 commits ahead and 2 commits behind #778, with merge base 60d1025e.... Comparing #779's base SHA to #778's current HEAD shows #778 has 7 commits not present in that base. Thus #779 must be rebased onto the current #778 HEAD and exact-head CI rerun before it can be treated as a clean descendant/integration candidate. Older statements that #779 was 28 ahead / 0 behind are stale. PR #779's body also contains an older exact-head reference (6002e823...); use current GitHub metadata and run #42892646330, not that stale body reference.
- Keep both PRs Draft where specified; no merge, branch rewrite, or main update was performed.

### Read-only pre-match Supabase recheck

A fresh aggregate queried only event IDs, league labels, pre-kickoff timestamps, and exact candidate SHA/time metadata:
- strict pre-match public.odds_snapshots: 3,915 rows / 327 events;
- new strict pre-match odds snapshots in the last seven days: 0;
- future events with a saved strict pre-match quote: 0;
- strict pre-match product_prediction_snapshots for the exact V2 SHA: 0 rows / 0 events.

No odds values, scores, result/settlement columns, or protected 2026/27 target outcomes were selected. No Supabase writes/DDL, paid provider calls, source downloads, model refit, production artifact change, or schedule change occurred.

### Scientific status

The original V2 artifact and 19-feature contract remain intact, but there are still no new admissible pre-kickoff V2 forecasts in Supabase and no independent prospective evaluation sample. The 30-primary-completed-event outcome gate remains closed. No new Brier/LogLoss comparison exists; superiority to the market is not established. active_lambda=0 remains the market baseline and shadow_lambda=1 remains research-only.


## 2026-11-10 23:59 UTC — newly found PDDL Serie A mirror (technical candidate only; rights not cleared)

A fresh search found public repository qhtexas/football-dataset, whose Serie A datapackage declares ODC-PDDL-1.0 and lists 33 season resources from 1993/94 through 2025/26. Its schema includes Date, teams, goals/result, corners (HC/AC), yellow cards (HY/AY), and red cards (HR/AR). For the frozen training window 2016/17–2025/26, this is a potentially complete historical field source on paper. The metadata lists no 2026/27 resource, so it cannot provide current-season lagged form for the separate current-form cohort.

The repository README and datapackage explicitly identify Football-Data.co.uk as the upstream source. The current official Football-Data policy says its free files are intended for private individuals' personal betting/academic research via manual download or at most light automated download twice per week, and are not intended for commercial or AI data-training products using automated bots/scrapers. The PDDL text itself cautions that a party can only license rights it owns and that users may need to clear other rights. Therefore the mirror's PDDL declaration is promising but does not independently establish that its maintainer owns or is authorized to waive the upstream database/data rights. Do not download, archive, infer from, or substitute this mirror until its maintainer's rights in the underlying Football-Data material are clarified or an applicable provider permission is recorded.

Metadata only was inspected: no season CSV bytes (including no 2026/27 result file) were downloaded or opened. No API, account, paid provider, Supabase, target outcome, or model run was used. Treat this as a new historical-source candidate for rights review, not an approved source or a source-before-quote attestation.


## 2026-11-11 01:06 UTC — exact candidate pin, downstream ancestry, and fresh pre-match database audit

### Fresh main and frozen original V2 identity

- Re-read `refs/heads/main` directly from GitHub: `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main is unchanged.
- Original candidate `research/models/market_anchor_v2_serie_a_frozen_candidate.json`: Git blob `ac1303f6b096664983fbf52443bd0a381b23ba21`; embedded artifact SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Candidate metadata still reports exactly 19 features, 3,799 training rows, a 20×2 weight matrix, `active_lambda=0`, `shadow_residual_lambda=1`, `stability_gate_passed=false`, and `automatic_promotion=false`.
- Historical builder blob remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`; its `FEATURE_SETS["ALL_FOOTBALL"]` list matches the candidate's 19 names in the same order. No candidate, feature, weight, scaler, imputer, or production file changed.

### New exact-head direct-inference identity guard — PR #778

PR [#778](https://github.com/MaksimBlud/football-ai/pull/778) advanced to exact HEAD `aa0cd076a15033d2d90c7c08cb3ff14c94c2e8ec` (2026-11-11 00:55 UTC). Its new guard closes a frozen-identity gap: candidate validation previously trusted a self-reported artifact hash, so altered 20×2 weights with a recomputed self-hash could pass recipe/shape checks; capture-row validation also accepted any syntactically valid 64-character candidate SHA.

The branch now pins candidate validation and every prospective shadow row to the exact original SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, tests the real frozen candidate JSON, and rejects recomputed-self-hash weight tampering and wrong capture-row candidate hashes. It does not alter the candidate or its weights.

Exact-head evidence:
- Frozen V2 Shadow Tests [#42935139447](https://github.com/MaksimBlud/football-ai/actions/runs/42935139447): **414 passed on Python 3.11 and 414 passed on Python 3.12**, both jobs SUCCESS; production `.pkl` guards passed.
- Market Anchor 1X2 V2 Shadow Validation [#42935139489](https://github.com/MaksimBlud/football-ai/actions/runs/42935139489): **15 passed**, SUCCESS; production `.pkl` guard passed.
- PR remains Draft and stacked on #777; HUMAN-MERGE only.

### PR #779 ancestry is now three commits behind the updated #778

PR [#779](https://github.com/MaksimBlud/football-ai/pull/779) remains at `3e936d64b1f490b8c8dc31951b35e446096ca94c`, based on `b2a034614d999683a8c334569dc07eb07b7ac589`. A fresh compare of #778 HEAD `aa0cd076...` to #779 HEAD returns **diverged, 28 ahead / 3 behind**, merge base `60d1025e9556cdce05f93b9a71ce46d4d06096cb`.

The old #779 exact-head run [#42892646330](https://github.com/MaksimBlud/football-ai/actions/runs/42892646330) (430 tests per Python version) does not include the latest #778 candidate-SHA guard. Keep #779 Draft; rebase it on the integrated current #778 chain and rerun exact-head CI before treating it as a descendant or merge candidate. No branch rewrite was performed.

### Main still has unheld V2 live workflow definitions

Re-read the actual main workflow files. The original forward workflow is `.github/workflows/serie-a-v2-forward-preview.yml` (blob `48ce3b0d8e31c4cf293b94500e9c320047311467`); it still has the daily 08:08 UTC schedule, manual dispatch, and a no-cost `workflow_run` reader awakened only by a successful manually dispatched Serie A Odds Snapshots workflow. Other main schedules remain Current-Form Source Capture at 05:50 UTC, Free Real-Quote Diagnostic at 06:13 UTC, and Current-Form Forward-Only at 08:18 UTC.

PR [#781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review at exact HEAD `c48e0c2f6a486c9320b04c7a1693373ec4afcdfc`, with **8/8 exact-head checks SUCCESS** (Frozen V2 suite 92 passed; recovery rebuild/proof/upload skipped under the false hold flag; production `.pkl` guard passed). It gates five original-V2 workflows and associated public artifact uploads, but has not been merged. Therefore the hold is **not active on main**; do not describe main as blocked. HUMAN-MERGE only. No cron or other agent setting was changed.

### Fresh read-only Supabase audit — pre-match metadata only

Database time: `2026-11-11 01:04:53 UTC`.

The query selected only league, event ID, pre-kickoff timestamps and candidate-SHA/time metadata:
- `public.odds_snapshots`: **3,915 strict pre-match snapshots / 327 events** across nine league labels.
- New strict pre-match snapshots in the last seven days: **0**.
- Future fixtures with saved strict pre-match quotes: **0**.
- Latest saved Serie A strict pre-match quote: `2026-10-13 14:48:53.04262 UTC`.
- `public.product_prediction_snapshots`, exact original candidate SHA plus `generated_at_utc < commence_time_utc` and `generated_at_utc <= NOW()`: **0 predictions / 0 events**.

No odds values, match scores, results, settlements, or protected 2026/27 target outcomes were selected.

### Scientific and operational boundary

There is still no new admissible pre-kickoff original-V2 prediction cohort and no independent Brier/LogLoss comparison. The 30-primary-completed-event outcome gate remains CLOSED; do not read protected outcomes before it. `active_lambda=0` remains the market baseline and `shadow_lambda=1` remains research-only. Provider rights for automated historical/current-form source capture remain unresolved, so no source download or inference is authorized by this audit.

No PR was merged; main, schedules, other agents, Supabase rows/schema, production `.pkl`, candidate weights and model contract were not changed. Paid provider calls and Supabase writes/DDL: zero.


## 2026-11-11 01:25 UTC — direct source/feature entrypoint closure and exact-head regression proof

### Fresh repository / original candidate

- Fresh `main` is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main update was made.
- Original frozen candidate Git blob: `ac1303f6b096664983fbf52443bd0a381b23ba21`; embedded SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- The candidate remains 19 features, 3,799 training rows, 20×2 weights, `active_lambda=0`, `shadow_residual_lambda=1`, failed stability gate, and no automatic promotion. The original builder's `ALL_FOOTBALL` order still matches the candidate exactly.

### New direct-entrypoint guards in PR #779

PR [#779](https://github.com/MaksimBlud/football-ai/pull/779) is now at exact HEAD `44766eed08ceedb1736a0095e5e67f175928ed89`, still Draft. The audit found and closed callable bypasses that were not protected merely by guarding the workflow/main runner:

- The public pre-quote archive verifier now requires inference rights and private storage before ZIP stat/read or CSV parsing; its CLI checks before reading the quote JSON. The lower-level verifier also enforces the scope.
- The direct date-only feature manifest builder and CLI require inference clearance before inspecting historical frames, quotes, or files.
- Historical loading is separated into explicit inference and source-only wrappers; the shared bounded loader always enforces a valid scope and private storage. Source-only capture cannot be treated as model-inference permission.
- Current-form source-capture metadata readers, CSV validation, and archive capture require the source-capture scope; archive capture additionally checks private repository storage before candidate/Supabase/network/output access.
- Direct original and current-form `verify_source_run()` calls now require inference rights/private storage before GitHub run metadata is requested.

Regression tests prove denied paths do not reach archive stat/read, quote-file read, CSV parsing, Supabase, public HTTP, or GitHub metadata. Synthetic scope stubs exist only in offline tests.

Exact-head run [#42938320207](https://github.com/MaksimBlud/football-ai/actions/runs/42938320207): **442 passed on Python 3.11 and 442 passed on Python 3.12**, both jobs SUCCESS; production `.pkl` diff guards SUCCESS. An earlier run on a superseded intermediate HEAD failed because source-loader blob pins and the synthetic attestation fixture had not yet been updated; both were corrected, and the final exact HEAD above is green.

The parent-loader pins now match the actual branch blobs: historical loader `f42ddd8ab1fdc939d909c2823d516c5b5f06de00`; current-form source-capture script `6c2e04077dc325a255cc92c6b288fd035e9c981b`.

### Downstream ancestry remains a separate integration blocker

PR #778 latest exact HEAD is `aa0cd076a15033d2d90c7c08cb3ff14c94c2e8ec`; its exact frozen suite [#42935139447](https://github.com/MaksimBlud/football-ai/actions/runs/42935139447) passed **414 on Python 3.11 and 414 on Python 3.12**, and its separate shadow validation [#42935139489](https://github.com/MaksimBlud/football-ai/actions/runs/42935139489) passed 15.

PR #779 HEAD `44766eed08ceedb1736a0095e5e67f175928ed89` remains based on `b2a034614d999683a8c334569dc07eb07b7ac589`. Fresh comparison to #778 HEAD is still **diverged, 52 ahead / 3 behind**, merge base `60d1025e9556cdce05f93b9a71ce46d4d06096cb`. Keep #779 Draft; rebase after the parent chain is manually integrated, then rerun exact-head CI. No branch rewrite or merge was performed.

### Hold / main runtime

PR [#781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review at exact HEAD `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`, with all eight exact-head checks SUCCESS. It is not merged, so its hold is not active on main. Main's original forward, current-form source, free diagnostic, and current-form forward workflow schedules remain present. Do not treat the open hold PR as an active main-branch block.

The actual main runtime logs re-opened in this run still show:
- Original Forward [#42853738496](https://github.com/MaksimBlud/football-ai/actions/runs/42853738496): source archive SHA attested; 3,800 historical rows / 10 old-season files; `quotes_seen=0`, `future_quotes_checked=0`, `forecasts_created=0`, `supabase_writes=0`, `paid_provider_calls=0`.
- Current-Form Source Capture [#42827889788](https://github.com/MaksimBlud/football-ai/actions/runs/42827889788): 110 identity-only completed-primary-event inputs and 11 source files; this is a feature-input gate, not the separate outcome gate; target outcomes not scored, writes 0, paid calls 0.
- Current-Form Forward [#42854487569](https://github.com/MaksimBlud/football-ai/actions/runs/42854487569): `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, writes 0.
- Free Diagnostic [#42837720155](https://github.com/MaksimBlud/football-ai/actions/runs/42837720155): `quoted_fixtures=0`, `feature_rows_with_all_19_observed=0`, `eligible_for_frozen_prospective_cohort=false`; no paid call or Supabase write.

These are real main-branch runs on the unchanged main SHA, not evidence of new forecasts.

### Fresh read-only Supabase pre-match audit

Database time at audit: `2026-11-11 01:04:53 UTC`. The query selected only league labels, event IDs, pre-kickoff timestamps, and exact candidate SHA/time metadata:
- strict pre-match odds inventory: **3,915 snapshots / 327 events**;
- new strict pre-match snapshots in the last seven days: **0**;
- future events with a saved strict pre-match quote: **0**;
- exact original candidate SHA strict pre-match predictions: **0 rows / 0 events**;
- latest saved Serie A strict pre-match quote: `2026-10-13 14:48:53.04262 UTC`.

No odds values, scores, results, settlements, or protected 2026/27 target outcomes were selected.

### Scientific boundary

No new admissible original-V2 prospective forecast exists in Supabase, so no independent Brier/LogLoss comparison can be computed. The 30-primary-completed-event outcome gate remains CLOSED. `active_lambda=0` remains the market baseline; `shadow_lambda=1` remains research-only. Provider rights for automated source access/inference remain unresolved; no source download or inference was performed in this audit.

No PR merge, main ref change, production `.pkl` change, Supabase write/DDL, paid provider call, target-outcome read, schedule change, or other-agent configuration change occurred.


## 2026-11-11 01:32 UTC — Big Balls free-tier source candidate reviewed (not approved for capture)

A new public-source review found Big Balls Sports Data. Its official Terms of Service (effective 2026-08-10) explicitly allow customers to store API responses and use stored data as input to internal models, including training, evaluation and backtesting; derived models/predictions may be published, but raw field values may not be republished or resold. This is materially clearer than the Football-Data mirror situation for internal research: https://bigballsdata.com/legal/terms.

The soccer documentation lists the free `/v1/matches/:id/statistics` route and per-team match fields including final home/away score, corners ("Won Corners"), yellow cards and red cards. These fields are potentially mappable to the frozen V2 inputs (points, goals for/against, corners for/against, yellow/red cards) without changing the 19-feature contract. The route's expected-goals field is Solo+ and is not required by this V2 candidate. Official field/endpoint reference: https://bigballsdata.com/soccer-api.

However, the source is NOT cleared for live use:
- Free soccer access is documented as current-season only; the 2016/17–2025/26 history needed to reproduce the frozen training cohort is not included in the free tier.
- The public soccer documentation marks team statistics as partial and says team-stat data was last ingested 2026-09-16, while its Serie A page shows the current 2026/27 standings updated 2026-11-10. That freshness gap is material for November current-form features; standings freshness cannot be substituted for match-stat freshness.
- Published coverage figures are aggregate across seasons and do not establish current-season completeness for every one of the required 19-feature inputs. Exact per-match field coverage, null rates, update timestamps and source provenance still need verification.
- The provider forbids republishing raw field values. The repository is public, and the current private-source-artifact gate requires private repository storage; no raw API response may be placed in public code, commits, logs or Actions artifacts. Supabase writes remain prohibited.

The provider advertises a free request allowance (1,000/day; higher with GitHub), but no API key was created, no API endpoint was called, no response bytes were downloaded, and no account or repository setting was changed. Do not add a collector or enable capture until (a) current-season match-stat freshness and field-level completeness are demonstrated on an authorized, non-outcome sample, (b) the source's capture timestamp can be pinned strictly before each quote, and (c) an approved private archive destination exists. Treat this as a promising rights candidate for internal research, not an approved source or evidence of any V2 forecast.


### Correction to the Big Balls free-tier assessment — plan and freshness conflict

A closer read of the provider's own league-specific page found a material contradiction that narrows the candidate further. The shared soccer hub lists `/v1/matches/:id/statistics` as Free (with xG restricted to Solo+), but the Serie A capability matrix lists advanced match statistics (possession, shots, cards and xG) as **Edge**; the separate free `/v1/stored/matches/:id/stats` endpoint is documented as possession, shots and passes, which does not by itself supply the V2 corners/cards inputs. The provider must clarify in writing whether the required per-match score/corners/yellow/red fields are available on Free before this can be called a free source.

The freshness evidence is also insufficient: the shared soccer page says team-stat data was last ingested 2026-09-16, while the Serie A page shows standings refreshed 2026-11-10. Current standings freshness does not establish current match-stat freshness. The page's aggregate historical coverage cannot be used as a current-season completeness denominator. Consequently, Big Balls remains an **unapproved candidate only**; do not create a collector, spend requests, or infer from it. No API key, account, API request, response download, or raw-data storage was used. References: https://bigballsdata.com/soccer-api and https://bigballsdata.com/serie-a-api.


## 2026-11-11 01:48 UTC — stale #779 ancestry reintroduced retired target rows; embargo restored

A deeper audit of the exact #779 branch found a critical regression that was not visible from the earlier workflow-level summary: because #779 still inherited the older #778 base, its copy of `market_anchor_v2_saved_cohort_replay.py` still contained 10 embedded target rows and its direct `validate_targets()` function did not have the current #778 deny guard. Current #778 HEAD `aa0cd076a15033d2d90c7c08cb3ff14c94c2e8ec` already had the safe state (`TARGETS=()`, direct validator denied). The old #779 branch therefore could not be treated as a safe descendant, even though its prior CI was green.

Remediation committed to the existing Draft #779 branch (no new PR and no main change):
- commit `efd60eec09113d7d66ab8b4db76792f5668ba2f5` copied the fail-closed saved-cohort module from current #778;
- commit `19d1332bd69d345f1e7507e35dead8a5012bfe09` replaced the stale replay tests with the current #778 embargo tests;
- current source now has an empty `TARGETS` tuple and direct `validate_targets()` is denied before validation; tests assert the empty tuple and early denial.
- exact-head CI runs `42941355893` and `42941361473` both completed SUCCESS on this exact SHA: Python 3.11 **439 passed**, Python 3.12 **439 passed**, and the production `.pkl` hash guard passed in both jobs.

PR #779 remains Draft and ancestry-stale: base `b2a034614d999683a8c334569dc07eb07b7ac589`; compare current #778 HEAD to new #779 HEAD remains diverged (52 ahead / 3 behind; merge base `60d1025e9556cdce05f93b9a71ce46d4d06096cb`). Keep HUMAN-MERGE. After parent integration, rebase the whole chain and rerun exact-head CI. The retired post-outcome replay must stay disabled; do not use its old report or any target rows for inference, scoring, selection, or promotion.


## 2026-11-11 — fresh pre-match inventory, source-rights candidates, and V2 ancestry audit

### Fresh main and frozen model identity

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; branch metadata still reports `protected=false`. No main update or merge occurred.
- Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; protocol blob `65729e9639720e67624c1481190aa22ae606f151`; historical feature-builder blob `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- Frozen 19-feature order, 20×2 weights, imputer/scaler, 3,799 training rows, `active_lambda=0`, `shadow_lambda=1`, failed stability gate, NO_BET and no-promotion policy remain unchanged.

### Fresh read-only Supabase pre-match inventory

Only timestamp/identity/league aggregates were queried. For odds snapshots the predicate was `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= NOW()`; no odds prices, scores, results, settlements or target-outcome fields were selected.

- All leagues: **3,915** strict pre-match snapshots / **327** unique events.
- New strict pre-match snapshots in the last seven days: **0**; upcoming events with a saved strict pre-match quote: **0**.
- Latest strict pre-match snapshot: Serie A, **2026-10-13 14:48:53 UTC**.
- Exact original candidate SHA in `public.product_prediction_snapshots`: **0** strict pre-match V2 rows / **0** events.
- Correct current-form feature-input metadata source is `public.league_finished_results`, not `public.matches`. A metadata-only query selecting/counting only `match_date, home_team, away_team` for Serie A 2026-27 returned **113** unique fixture identities, latest metadata date **2026-11-08**. This is only the lagged-feature input gate; it does not open the separate 30-eligible-prospective-forecast outcome gate.

### New source-rights candidates — not approved for use

- **OpenScores** publishes terms allowing internal research and caching/transformation, and documents top-five league fixtures/statistics. Its docs were last updated 2026-06-12; its changelog describes Sofascore/Flashscore ingestion. Upstream rights for those feeds and verified 2026-27 Serie A field completeness remain unresolved. No account/key was created and no API call was made. References: `https://openscores.ai/terms`, `https://openscores.ai/docs`, `https://openscores.ai/changelog`.
- **Cornerflick** publishes a CC BY 4.0 compilation and per-match CSV/JSON with stats/provenance, but its own data page explicitly limits that licence to its compilation and says underlying match facts remain subject to provider terms. A sampled page identifies API-Football as the feed; no upstream permission for this V2 use was established. Do not treat the compilation licence as clearing provider rights. No CSV was downloaded or used. References: `https://cornerflick.com/data`, `https://www.api-football.com/terms`.
- Neither source replaces the current Football-Data source-rights block. No source was added to the V2 pipeline.

### Current V2 PR state and exact verification

- PR #781 remains OPEN / Ready for review / HUMAN-MERGE at `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`; its eight PR-triggered workflows are SUCCESS. The recovery run `42881013880` completed offline tests and the production hash check, while candidate rebuild, proof and artifact upload were SKIPPED. This hold is not on main; the four scheduled live workflows remain active until manual integration.
- PR #778 current HEAD `aa0cd076a15033d2d90c7c08cb3ff14c94c2e8ec` pins both candidate validation and captured shadow rows to the exact original candidate SHA. Exact frozen V2 CI: Python 3.11 **414 passed**, Python 3.12 **414 passed**; separate V2 shadow-validation run **15 passed**; production `.pkl` guards passed.
- PR #779 current HEAD `19d1332bd69d345f1e7507e35dead8a5012bfe09` has exact frozen V2 CI **439 passed** in Python 3.11 and **439 passed** in Python 3.12. However, compare #778 HEAD → #779 HEAD is **diverged, 54 ahead / 3 behind**, merge base `60d1025e9556cdce05f93b9a71ce46d4d06096cb`. Direct blob comparison confirms #779 still has an older `market_anchor_1x2_v2_shadow.py` that lacks #778's exact `FROZEN_CANDIDATE_SHA256` pin. Keep #779 Draft; do not merge it. Rebase/port the complete latest #778 state, then rerun exact-head CI before considering integration.
- PR #740 itself remains a documentation-only branch; its previous exact HEAD `ee97565092f99ba34eff5950d5fc405fbaf812c3` passed 7/7 PR workflows. This addendum must receive fresh exact-head CI after this commit.

### Boundaries

No source download, API request, odds-provider request, quote-price read, target-outcome query, Supabase write/DDL, production `.pkl` change, model refit, threshold tuning, promotion, betting, schedule change, main update, or other-agent setting change was performed. No 2026/27 result values were used for model features, forecast scoring, candidate selection, or evaluation. The 30-forecast outcome gate remains CLOSED; no Brier/LogLoss superiority claim is supported.


### Source-review boundary incident — 2026-11-11

During external licence research, a public Cornerflick Serie A results page and search surfaces inadvertently displayed 2026/27 result listings before the V2 evaluation workflow was authorized to use outcomes. This was an accidental browsing exposure. No score/result values were copied into the repository or Supabase, supplied to the model, used for candidate/feature selection, forecast scoring, Brier/LogLoss, or evaluation; no Supabase outcome columns were queried. Treat the surfaced public data as contaminated and do not use it for any V2 work. Cornerflick is not an approved V2 source regardless: its CC BY 4.0 licence covers only its compilation, while its own data page leaves underlying match facts subject to upstream provider terms. No CSV or API data was downloaded. Keep all original outcome gates unchanged.


# Incremental pre-match audit — 2026-11-11 03:51 UTC

## Fresh Supabase metadata and prospective state

- Read-only metadata-only query for `SERIE_A / 2026-2027` now finds **113 unique fixture identities**, latest metadata date 2026-11-08. Only `match_date, home_team, away_team` were aggregated; no score/result fields were selected.
- This is the lagged-feature input gate only. It does not open the separate target-outcome evaluation gate, which remains CLOSED until 30 eligible prospective V2 forecasts have completed.
- Strict pre-kickoff `public.odds_snapshots`: **3,915 snapshots / 327 events** across the existing nine leagues; no new snapshots in this read. Latest Serie A quote remains 2026-10-13 14:48:53 UTC.
- `public.product_prediction_snapshots` filtered to exact original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`: **0** strictly pre-kickoff V2 predictions / **0** events.

## Exact main-branch source/forward runtime

On main `40887ebb215730190d7a6c7a1693373ec4afcdfc`:
- Current-Form Source Capture [run 42827889788](https://github.com/MaksimBlud/football-ai/actions/runs/42827889788) SUCCESS on 2026-11-10 13:48 UTC; log reports feature-input gate **110** at capture time, 10 frozen historical CSVs + one current-season source, 3,910 historical rows, 0 paid calls and 0 Supabase writes. Source artifact **13770560196**, ZIP SHA-256 `f29363e28775032937108d102da1dda1ca2d5c1aa0f921cb4518bf3a82e9aec6`. Artifact contents were not downloaded/opened in this audit.
- Current-Form Forward [run 42828048742](https://github.com/MaksimBlud/football-ai/actions/runs/42828048742) and later [run 42854487569](https://github.com/MaksimBlud/football-ai/actions/runs/42854487569) SUCCESS; both report **0 saved quotes / 0 V2 shadows**, target outcomes not read/scored, 0 paid calls and 0 Supabase writes.
- Original Forward [run 42853738496](https://github.com/MaksimBlud/football-ai/actions/runs/42853738496) SUCCESS; **0 quotes / 0 previews / 0 prospective eligibility**.
- Thus the current-form source archive is real and SHA-attested, but no new forecast was generated and no independent evaluation sample exists.

## Current live-access hold

- PR #781 exact HEAD remains `c48e0c2f6a486c9320b04c7a1693373ec4afcdfc`; its eight exact-head PR workflows are SUCCESS. The recovery job correctly skipped candidate rebuild, candidate proof and artifact upload.
- PR #781 is still open and not merged; main retains the existing live workflow schedules: 05:50, 06:13, 08:08 and 08:18 UTC. The next source-capture slot after this audit is 05:50 UTC on 2026-11-11.
- The PR hold is the required fail-closed protection pending provider AI-use clearance. HUMAN-MERGE remains mandatory; do not merge automatically or change the schedules in this research task.

No artifact payload, score/result column, target outcome, or quote price was read in this incremental audit. No source/API request, Supabase write/DDL, paid provider call, model refit, threshold tuning, production `.pkl` change, merge, main update, or other-agent setting change occurred. The original candidate SHA, 19-feature contract, weights, `active_lambda=0`, `shadow_lambda=1`, NO_BET and both outcome gates remain unchanged.


## 2026-11-11 05:20 UTC — clean rebase replacement for V2 direct forward/report gate

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main update or merge occurred.

### PR #782 replaces the stale #779 branch

- PR #782 base is the exact current #778 HEAD `aa0cd076a15033d2d90c7c08cb3ff14c94c2e8ec`.
- Current #782 head is `984f00cf1c4c236dc4124ec1903e3ddd4c51474e`.
- GitHub compare confirms **17 commits ahead / 0 behind**, with 16 changed files.
- The PR description was corrected to this current SHA; earlier intermediate SHA `10f84be3937f5c48fcc324010855e2acf68c9070` is stale.
- Exact-head push run [42964652147](https://github.com/MaksimBlud/football-ai/actions/runs/42964652147) and pull-request run [42964659477](https://github.com/MaksimBlud/football-ai/actions/runs/42964659477) both completed **2/2 jobs SUCCESS** on `984f00cf...`. Python 3.11 and Python 3.12 each report **440 passed**; production `.pkl` hash guards passed.
- The new direct-call checks enforce inference scope and private artifact storage before quote/archive inspection, callbacks, filesystem creation, feature construction, or shadow scoring. Source capture and source-archive reading have their separate scope checks. CI uses synthetic permission stubs only; this is not live provider clearance or inference evidence.
- #782 remains **Draft** because #778 and its parent stack are not merged. HUMAN-MERGE only.

PR #779 remains Draft and is superseded for integration purposes. Its HEAD `19d1332bd69d345f1e7507e35dead8a5012bfe09` remains based on stale ancestry and lacks #778's exact candidate SHA pin in the shadow module. Its 439-test CI does not cure that code difference. Do not merge #779.

### Current live-workflow hold and schedule audit

PR #781 remains OPEN / Ready for review at exact HEAD `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`; all eight exact-head workflows are SUCCESS, including the offline V2 shadow suite and recovery job. It is not merged to main.

Direct comparison of the four main workflow files with #781 confirms that #781 preserves the existing cron strings while hard-gating the live data/inference steps and their artifact uploads behind `MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true'` (fixed false in the PR):
- current-form source capture: `50 5 * * *`;
- free diagnostic: `13 6 * * *`;
- original forward: `8 8 * * *`;
- current-form forward: `18 8 * * *`.

The unchanged main workflows still contain their original live steps and credentials until #781 is manually integrated. No schedule was edited in this task.

### Fresh read-only pre-match Supabase audit

At this check:
- strict pre-kickoff odds snapshots: **3,915 / 327 events** across nine leagues;
- future-event snapshots satisfying `snapshot_time_utc < commence_time_utc`: **0**;
- latest Serie A pre-kickoff snapshot: **2026-10-13 14:48:53 UTC**;
- exact original-candidate rows in `product_prediction_snapshots` satisfying `generated_at_utc < commence_time_utc`: **0 / 0 events**;
- Serie A 2026/27 feature-input metadata: **113 unique date/home/away identities**, latest match date **2026-11-08**, selecting no score/result fields.

The 113 metadata identities satisfy only the lagged feature-input gate. The separate prospective target-outcome gate remains CLOSED; no 2026/27 target outcomes were read or scored. No Brier/LogLoss or V2-over-market claim is available.

No source/API download, paid request, live inference, Supabase write/DDL, production `.pkl` change, model refit, threshold tuning, promotion, bet, schedule change, main update, merge, or other-agent setting change occurred. Original candidate SHA, 19-feature order, weights, scaler/imputer, `active_lambda=0`, `shadow_lambda=1`, and all frozen gates remain unchanged.

### Direct original-candidate guard: main versus frozen PR stack

A fresh file-level comparison was made against main `40887ebb215730190d7a6c7a1693373ec4afcdfc`:

- Main candidate JSON blob is `ac1303f6b096664983fbf52443bd0a381b23ba21`. Its embedded `artifact_sha256` is the unchanged original `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; it declares 19 ordered features, 20×2 weights, 3,799 training rows, `active_lambda=0`, `shadow_residual_lambda=1`, failed stability gate and no promotion.
- Main protocol blob is `65729e9639720e67624c1481190aa22ae606f151`; it keeps the first target-outcome read gate at 30 completed primary Serie A events, with no outcome read before the gate and NO_BET.
- Main historical feature-builder blob is `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- **Important code gap on main:** `market_anchor_1x2_v2_shadow.py` blob `b2770d726ffafe7a3cef706b57d3391063cbfe1b` does not contain `FROZEN_CANDIDATE_SHA256` and still exposes the old refit helper bodies.
- The corresponding file on #778/#782 is blob `f3a572e3fd5c9fdc9f8ca1950ba7e551b0edd97e`; it pins `FROZEN_CANDIDATE_SHA256` to the exact original candidate and makes refit/write paths fail closed. #782 inherits that exact #778 file byte-for-byte.

Therefore the candidate artifact itself is present and unchanged on main, but the strongest direct-call SHA/refit protections are still only in the unmerged frozen PR stack. Do not treat the candidate file's presence as proof that main has the full protected execution path. Preserve the #778 → #782 order and HUMAN-MERGE; do not merge #779.

# Incremental V2 audit — 2026-11-11 05:49 UTC

## Frozen original protocol gate: metadata count only

The original protocol blob remains `65729e9639720e67624c1481190aa22ae606f151`. Its `first_outcome_read_gate` requires 30 completed primary-cohort events, with non-primary leagues excluded. A new metadata-only Supabase query against `public.league_finished_results` for `SERIE_A / 2026-2027` selected only `match_date, home_team, away_team` and returned:

- 113 completed rows / 113 unique date-team fixture identities;
- first date 2026-08-22; latest date 2026-11-08.

Thus the protocol's **30-primary-completed-event count threshold is met**. This is only a count check; no score/result/outcome columns were selected and no target outcomes were opened or scored. It does not satisfy the separate current-form prospective evaluation requirement of 30 completed eligible forecasts. Exact original-candidate pre-kickoff predictions remain 0 rows / 0 events, so there is still no prospective V2 sample to score and no Brier/LogLoss comparison to report.

## New source-policy dependency discovered in clean-rebase PR #782

PR #782 is the clean-ancestry replacement for stale #779:

- Base: exact #778 HEAD `aa0cd076a15033d2d90c7c08cb3ff14c94c2e8ec`.
- HEAD: `984f00cf1c4c236dc4124ec1903e3ddd4c51474e`.
- Compare: 17 ahead / 0 behind, 16 files.
- Exact push run #42964652147 and PR run #42964659477 both completed 2/2 SUCCESS on that exact HEAD; Python 3.11 and 3.12 each passed 440 tests, and production `.pkl` hash guards passed.
- #782 inherits #778's exact original candidate SHA pin and retired replay (`TARGETS=()`).

However, #782 does **not** include the later source-policy recheck in sibling PR #780:

- #782 manifest blob `b09ed11feb7a03ff729171bf39e88cda1341d488` still says `research_source_capture_permitted=true`, `PRIVATE_NONCOMMERCIAL_RESEARCH_ARCHIVE_ONLY`, policy page date `2026-11-06`.
- #780 HEAD `48f55b6ef4dc40879d5232ac78ce55df51d2dce4` has manifest blob `b138d29f98e4cf3071d4c6a35a01dbb4e80e5afd`, sets `research_source_capture_permitted=false`, `NONE_PENDING_PROVIDER_CLARIFICATION`, and policy page date `2026-11-10`. Its source-capture rights module is also newer (blob `3029fae3dc4ef4c8c2b65d032db618579bf9b1ff` versus #782 blob `5bb688be5529469d0712e00b02d2014fc0a6ebd0`).
- #782's direct `capture_source_archive()` still calls the source-capture permission gate and private-repository check. The current public-repository check blocks source archive access today, but if the repository later becomes private, #782's stale manifest would permit source-only capture without the newer #780 provider-policy hold.

A top-level review comment was added to #782 (comment ID `6788433657`) with the exact blob/manifest evidence. **Keep #782 Draft** until #780's source-rights code, manifest, and tests are incorporated (or the descendant stack is rebased so #780 is included), then rerun full exact-head CI. The correct stack must carry #780 before the #742 → #774 → #777 → #778 → #782 descendants are considered ready. This does not authorize any source download.

PR #780 itself is still Draft on #727 at exact HEAD `48f55b6ef4dc40879d5232ac78ce55df51d2dce4`; its exact PR run #42812927009 completed 2/2 SUCCESS. It remains a provider-policy hold, not a licence grant.

## Main/live hold and current pre-match data

Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. PR #781 remains OPEN / Ready for review / HUMAN-MERGE at exact HEAD `c48e0c2f6a486c9320b04c7670d84b74e8d2322a`; its eight PR-triggered runs are SUCCESS, including the frozen V2 suite and recovery job. It is not merged, so main still has live steps in the four existing workflows. Their cron strings remain unchanged: 05:50, 06:13, 08:08, 08:18 UTC. No schedule or workflow was changed or dispatched.

Fresh read-only Supabase aggregates, restricted to strict pre-kickoff timestamp/identity metadata:
- `public.odds_snapshots`: 3,915 snapshots / 327 events; 0 new in seven days; 0 future events with saved strict pre-match quotes; latest `2026-10-13 14:48:53.04262 UTC`.
- `public.product_prediction_snapshots`, exact original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`: 0 strict pre-match predictions / 0 events.

## Static review boundary note

The static audit fetched the legacy `market_anchor_v2_saved_cohort_replay.py` source on main to inspect its callable entrypoints; that retired file contains pre-existing hardcoded post-outcome labels. No labels were copied into this addendum or used for feature construction, candidate/threshold selection, scoring, or metrics. Do not execute or use the legacy main-branch replay. The clean #778/#782 branch has `TARGETS=()` and blocks the retired replay entrypoints. This is a source-review exposure, not a new evaluation result.

Supabase Security Advisor still reports critical RLS-disabled exposure on `teams`, `predictions`, `match_statistics`, `league_prediction_ledger`, and `epl_ai_market_pair_ledger`. No DDL or writes were performed; enabling RLS without designed policies could break access.

No source download, odds/API request, target-outcome query, live inference, Supabase write/DDL, production `.pkl` change, model refit, threshold tuning, promotion, bet, merge, main update, schedule change, or other-agent setting change occurred. Original 19-feature order/weights, candidate SHA, `active_lambda=0`, `shadow_lambda=1`, failed stability gate and NO_BET remain unchanged.

## 2026-11-11 09:49 UTC — prospective evaluator regression repair and exact live-data recheck

### PR #728 — offline-only evaluator test repair

- PR #728 remains Draft. Current exact HEAD: `245420b83308d5b4e20f51fe7fd7a3c5e1ddd582`; it is based on base SHA `8894ce8e0248a5502d60571ff073fc6d7847a43a`.
- Repaired a real type-contract defect in `run_live_evaluation`: its public `now` parameter was annotated `datetime | None`, but the implementation passed aware `datetime` objects to a string-only ISO parser. It now accepts an aware `datetime` or explicit-offset ISO string, normalizes to UTC, rejects naive datetimes, and still rejects any observation clock later than the actual system clock.
- Updated only synthetic tests to model the current direct-access and source-preflight contracts. Unit fixtures explicitly stub provider/private-storage permission as `SYNTHETIC_TEST_ONLY`; a separate negative test proves unresolved inference rights fail before the identity gate or outcome callback. Synthetic source attestations are test fixtures only and are not provider authorization or real source evidence.
- Updated the mocked bridge to pass the same gate/source attestations and keyword-only provenance expected by the lazy outcome reader. No real Supabase outcome reader or live evaluator was run.
- Exact-head validation on Python 3.12: **120 passed**, production pickle diff guard SUCCESS on both [push run 42997996998](https://github.com/MaksimBlud/football-ai/actions/runs/42997996998) and [PR run 42998005892](https://github.com/MaksimBlud/football-ai/actions/runs/42998005892).
- The branch is not ready to merge: comparing its HEAD with the current #727 head `18a3cfda4e83e44aca1252665d01804267d16467` reports **diverged (9 ahead / 4 behind)**, merge base `8894ce8e0248a5502d60571ff073fc6d7847a43a`. Rebase/reconciliation is required after its parent stack is integrated. The live source-rights manifest still records inference permission false, and the repository is public; those runtime gates remain fail-closed. Keep #728 Draft.

### Re-read original forward workflow and actual latest main runs

- Main's `.github/workflows/serie-a-v2-forward-preview.yml` still defines the original V2 forward-only workflow; its daily 08:08 UTC schedule and manual-paid-snapshot-only `workflow_run` trigger are unchanged. The current-form source/forward schedules remain 05:50 and 08:18 UTC. No workflow was dispatched or edited.
- Actual 2026-11-10 source capture run [42827889788](https://github.com/MaksimBlud/football-ai/actions/runs/42827889788) succeeded on main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`: 110 completed feature-input identities, 10 historical CSVs + 1 current-season CSV, source artifact `13770560196`, SHA-256 `f29363e28775032937108d102da1dda1ca2d5c1aa0f921cb4518bf3a82e9aec6`, zero paid calls and zero Supabase writes.
- Actual original forward run [42853738496](https://github.com/MaksimBlud/football-ai/actions/runs/42853738496) succeeded but reported `quotes_seen=0`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`. Current-form forward run [42854487569](https://github.com/MaksimBlud/football-ai/actions/runs/42854487569) verified that source artifact and its parent run, but reported `quotes_seen=0`, `v2_current_form_shadow_captured=0`, and target-outcome gate false. These are source-integrity proofs, not model predictions or quality evidence.

### Fresh read-only Supabase pre-match aggregates

- `public.odds_snapshots` was queried only with `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= NOW()`. Counts: Bundesliga 394/35 events; EPL 1,135/70; Eredivisie 410/39; La Liga 798/52; Ligue 1 387/35; Primeira Liga 9/9; RPL 153/15; Serie A 620/63; Turkey Super Lig 9/9. Total **3,915 snapshots / 327 events**.
- `public.product_prediction_snapshots`, filtered by the exact original candidate SHA and strict generated-before-kickoff predicate: **0 predictions / 0 events**.
- Serie A 2026/27 feature-gate query selected only `match_date, home_team, away_team`: **113 unique identities**, latest date 2026-11-08. No score, result, settlement, or target-outcome fields were selected.
- Therefore the protected 30-primary-completed-event outcome gate remains closed; no Brier/LogLoss or market-superiority claim is available.

### Safety

- Supabase Security Advisor re-confirmed RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. This is a critical exposure. No DDL was executed; enabling RLS without reviewed policies can block legitimate access.
- No main update/merge, production pickle change, source download, paid request, Supabase write/DDL, live inference, target-outcome read, bet, threshold change, or promotion occurred. Original candidate SHA, 19-feature contract, weights, `active_lambda=0`, `shadow_lambda=1`, and failed stability gate remain unchanged.
