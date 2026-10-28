## 2026-10-28 08:55 UTC — current-form scheduled runtime gap and source/metadata coverage mismatch

**Fresh source of truth:** `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Current-form source workflow blob `9722416862b42d55ff7181003353c39620f23cf2` declares `05:50 UTC` daily; forward-preview workflow blob `6ebbcaff290a78e9ccffa4ac9a09bc0982eaff35` declares `08:18 UTC` daily and listens for successful source-capture completion.

**Observed runtime:** the latest successful source-capture run in the fresh scheduled-main run history is [#40493535578](https://github.com/MaksimBlud/football-ai/actions/runs/40493535578), created 2026-10-27 11:05:44 UTC and completed 11:06:34 UTC. Its verified source artifact is `12730175586`, ZIP SHA-256 `f0fb3565d2e5f44faadf488820c36327cb9d0d7b83b3da826af9b877f0804986`. The latest current-form forward preview is [#40522068472](https://github.com/MaksimBlud/football-ai/actions/runs/40522068472), completed 2026-10-27 14:33:05 UTC; artifact `12740943343`, SHA-256 `d23b1f70e6da5845e9dc6c18e54174b1da9aa4a9e21402ca94ab7cb0d2ae3bd8`. The fresh scheduled-main run pages show no source-capture run after Oct 27 11:05 UTC and no current-form forward run after Oct 27 14:32 UTC, so neither expected Oct 28 schedule has a confirmed run yet. This does not prove whether GitHub skipped or disabled either workflow; no settings or schedule were changed.

**New coverage discrepancy:** the Oct 27 forward artifact reports `current_season_history_rows=80` and `feature_input_gate_count=80`. A fresh read-only Supabase query at 2026-10-28 08:54 UTC selected only `match_date, home_team, away_team` and returned 83 Serie A 2026/27 metadata rows, 83 unique fixture identities, latest date 2026-10-25. The three-row count difference does not prove which fixtures differ, but it means the older archive is not sufficient evidence of current identity coverage. PR #699 adds a canonical identity-set digest and fails closed when any metadata-gate fixture is absent from the downloaded current-season CSV; after HUMAN-MERGE, run a fresh capture and verify its identity-set evidence before claiming coverage.

**Quote availability:** read-only `public.odds_snapshots` audit at 2026-10-28 08:54:29 UTC returned 3,966 snapshots, latest 2026-10-13 14:48:53 UTC, zero snapshots in the prior 24 hours, and zero future events with a saved snapshot strictly before kickoff. The forward run itself reports `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, `paid_provider_calls=0`, and `production_or_supabase_writes=0`.

**Next:** manual review only for #699/#701/#697. Do not change schedules, dispatch paid collectors, write to Supabase, or loosen source/quote-age gates. The evaluation gate remains closed and no Brier/LogLoss claim is possible.

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

# Football AI — Project Continuity

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
