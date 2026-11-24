## 2026-11-24 — Big Balls Sports Data free Serie A statistics source audit

A new provider was screened using only official public Terms, pricing, coverage and OpenAPI documentation. No account/key was created, no provider API request was sent, and no match data was downloaded.

**Positive evidence:** the provider's Terms (effective 2026-08-10) explicitly permit private API-response storage and use as input to internal models, including training, evaluation and backtesting; derived models and outputs belong to the customer. Its documented Free soccer statistics route `GET /v1/matches/{id}/statistics` is available on Free, stores post-match home/away team statistics hourly, and documents corners, yellow cards and red cards. Scores provide goals; points can be derived from completed scores. This is a potential future-only current-form source for the unchanged original 19-feature builder, not a market-odds source.

**Hold reasons:** official pricing and Serie A pages conflict on whether Free covers the current plus most-recent season or current season only; either scope does not replace the original 2014–2026 training corpus. The public coverage matrix marks soccer team statistics Partial and every fixture stat field is nullable, so exact Serie A 2026/27 per-fixture completeness is not proven. The API aggregates 19+ upstream sources and 10 MCP scrapers; `meta.source` is explicitly an opaque tier label and hides vendor identity. The soccer statistics route does not document per-record/per-field first-observed or correction timestamps. A related stored-stats route's `meta.as_of` is ingestion time, not upstream update time, and is often empty for soccer. The official Serie A landing page also visibly renders a Soldier Field 20–10 Q4/NFL-drive tile, NFL player names in a Serie A fantasy tile, and NFL player names/metrics in a Serie A fantasy tile. The page's 4,941 total matches versus 4,671 finished games differs by 270, consistent with unplayed fixtures, so that count difference is not treated as a contradiction. The cross-sport content remains a severe public data-integrity red flag pending provider explanation.

**Decision:** `HOLD_NO_INTEGRATION`. Written upstream vendor/field-level rights confirmation and per-fixture coverage evidence are required. If later cleared, only a future-only lagged-input capture with exact response bytes, local receipt UTC and SHA-256 before the market quote may be considered. No feature, weight, candidate, training corpus, quote source, lambda or frozen gate is changed.

Audit: `research/MARKET_ANCHOR_1X2_V2_BIGBALLSDATA_FREE_STATS_SOURCE_AUDIT_20261124.md`  
Machine-readable audit: `research/source_rights/bigballsdata_20261124.json`  
Offline regression: `tests/test_serie_a_v2_bigballsdata_source_audit.py`

Frozen candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features, 20×2 weights, `active_lambda=0`, `shadow_lambda=1`, stability gate FAILED, no automatic promotion. The audit made zero provider API requests, zero provider downloads, zero Supabase writes/DDL, and read no protected 2026/27 outcomes.

---

## 2026-11-24 — Footiqo free-source rights and pre-match suitability audit

A new public-source candidate, Footiqo, was screened using its official pages only; no account was created, no file/sample/export was downloaded, and no automated request was sent.

Official evidence:
- Dataset Licence & Data Access Policy (last updated 2026-10-08): https://footiqo.com/dataset-licence/
- Serie A public database page: https://footiqo.com/database/leagues/italy-serie-a/
- Dataset coverage/pricing: https://footiqo.com/premium/premium-football-database/

What the official pages establish:
- The Serie A page exposes current and historical match tables and CSV/Excel export controls. It advertises separate views for scores, corners/cards, shots/possession, xG and odds. The public table visibly includes match date, home/away teams, full-time goals and result; field availability varies by match, season and page.
- The policy expressly permits users who legitimately obtain data through official download/export functions to retain it privately for personal, non-commercial research, statistical analysis, predictive modelling, backtesting and machine-learning experiments. It applies to free samples and public-table exports as well as purchased datasets.
- The same policy prohibits automated scraping/crawling, automated bulk extraction, automated access to export endpoints, and automated downloading of free or premium datasets unless Footiqo gives separate written authorization. It says no public API is currently provided. Manual export is permitted for personal non-commercial research.
- The policy does not override third-party data-provider rights; it states that underlying source rights can differ. Coverage/completeness is not guaranteed.
- The full historical database is listed at €49.99 and the separate 19-bookmaker historical pre-match-odds collection at €99.99; free samples are not the full datasets.

V2 decision:
- **HOLD for automated source capture and scheduled ingestion**: the published policy does not authorize automation, there is no public API, and written automation permission is absent.
- **Possible manual research-only source** if the project use is personal/non-commercial and the official export route is used. This is not an approved replacement for the automated source-before-quote pipeline.
- The public pages do not establish a per-match first-observed timestamp, complete 19-feature coverage, or upstream rights for every field. A match date is not a provider-observed timestamp. Therefore Footiqo cannot presently satisfy the frozen source-before-quote evidence contract or be admitted as a complete 19-feature prospective source.
- Do not use public exports to backfill the frozen prospective cohort. Do not treat the advertised 1X2 odds tables as a substitute for the project's independently timestamped saved market snapshots.
- Next evidence required before reconsideration: written permission for automated capture (if automation is desired), a provider statement covering upstream rights and ML use, exact field/season coverage for all 19 frozen features, and a provider-observed first-available timestamp or equivalent immutable receipt evidence.

This is a source-rights/field-provenance screen only; it does not change the original V2 model, protocol, feature order, weights, lambda values, source cohort, workflow schedules, or outcome gates.

---

## 2026-11-24 02:00 UTC — Original V2: recomputed frozen stability gate and comparator/provenance audit

### Independent recomputation of the frozen historical stability gate
- Read only the original V2 Python contract/tests and the two frozen historical JSON reports; no 2026/27 target outcomes or production model bytes were read.
- Main `market_anchor_1x2_v2_shadow.py` blob: `b2770d726ffafe7a3cef706b57d3391063cbfe1b`.
- Frozen V2 protocol blob: `65729e9639720e67624c1481190aa22ae606f151`.
- Frozen V1 robustness report blob: `96d2f462849a70276a2c27a2c0cc18ec0672b00a`, exactly matching the SHA pinned in the V2 code and protocol.
- Recomputed the unchanged gate directly from the pinned report:
  - prior seasons: 6 (passes the count requirement);
  - prior seasons winning both metrics: 2 (required at least 4);
  - Brier bootstrap CI95 high: **+0.003236877119355216** (must be below 0);
  - probability Brier is better than market: **0.6831** (must be at least 0.95);
  - LogLoss bootstrap CI95 high: **+0.006038957657259541** (must be below 0);
  - probability LogLoss is better than market: **0.6317** (must be at least 0.95).
- Result: **1 of 6 checks passes; stability gate remains FAILED**. This independently reproduces the existing test result; no threshold, feature, weight, or report was changed.

### Frozen comparator limitation
- The protocol comparator set is exactly `DE_VIGGED_MARKET`, `FROZEN_PRODUCTION_INCUMBENT`, and `INACTIVE_LAMBDA_1_RESIDUAL_SHADOW`.
- The code pins `INCUMBENT_MODEL_SHA256=1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5` and validates the supplied row hash against that constant, but the capture contract does not independently attest how the incumbent probability triplet was generated.
- Because the user prohibits returning to the legacy XGBoost production model and prohibits production `.pkl` changes, no incumbent model was executed, loaded, or modified. Incumbent prediction provenance therefore remains unresolved; do not fabricate it or open the outcome gate. The market-only baseline remains independently identifiable, but the frozen protocol still lists the incumbent as a required comparator.

### Source-provenance writer/validator compatibility review
- Compared the exact offline patches of #944's `build_source_provenance()` writer and #942's `_validate_capture_source_provenance()` gate validator.
- The outer and nested `parent_run` field sets match exactly; both enforce source observation ≤ archive creation, parent creation ≤ archive creation ≤ parent completion < market quote, and the validator additionally requires the feature cutoff not later than the verified source observation.
- This is static schema alignment only. #944 and #942 remain separate open draft branches; no combined integration test or live source/quote row has yet demonstrated the writer output passing the validator. Keep the gate closed until the code is integrated in dependency order and an actual permitted source/quote capture exists.
- No source/provider request, archive download, quote read, Supabase access, target-outcome read, XGBoost execution, production `.pkl` access/change, refit, threshold tuning, schedule change, merge, main update, promotion, or bet occurred.

Frozen V2 invariants remain unchanged: 19 features, original 20×2 weights, candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, `active_lambda=0`, `shadow_lambda=1`, NO_BET, automatic promotion false, and the 30-primary-completed-event outcome gate CLOSED.

## 2026-11-24 01:52 UTC — Original V2: fresh all-league pre-match quote audit and exact documentation CI

### Fresh repository and PR state
- Re-read public `main`: `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` blob remains `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`. The main branch and its workflows were not modified.
- Existing documentation PR [#839](https://github.com/MaksimBlud/football-ai/pull/839) exact HEAD before this checkpoint: `be8060f00820d0850ed88fa31ae1751632b15954`.
- All eight exact-head PR jobs on that SHA completed SUCCESS: Research `45301110919`, Product `45301110949`, Serie A `45301110908`, Bundesliga `45301111409`, Frozen V2 Shadow `45301111449`, Ligue 1 `45301110960`, Eredivisie `45301111052`, and La Liga `45301111230`. Each run's sole job was independently read and reported `completed/success`.
- Root workflow HOLD [#781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review / HUMAN-MERGE at `5552bec363ae72ad7aef04c598d2ce861f33eb42`; its eight exact-head jobs remain SUCCESS. It is not integrated, so it does not protect main yet. Private-artifact guard #879 and source-first chain #938 remain draft children and are not integrated.

### Read-only Supabase pre-match aggregate
- Queried only `public.odds_snapshots` and only `league,event_id,snapshot_time_utc,commence_time_utc,created_at`; no scores, results, settlement, target outcomes, or other result-bearing fields were selected.
- Strict predicate: `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= created_at AND created_at < commence_time_utc`.
- All nine stored leagues: **3,966 total rows; 3,915 strict pre-match rows; 327 distinct strict pre-match events; 0 future-kickoff strict rows/events**. Thus 51 stored rows do not satisfy the strict persistence/time predicate.
- Per-league result (total / strict rows / strict events / future strict rows):
  - Bundesliga: 404 / 394 / 35 / 0
  - EPL: 1,151 / 1,135 / 70 / 0
  - Eredivisie: 412 / 410 / 39 / 0
  - La Liga: 806 / 798 / 52 / 0
  - Ligue 1: 394 / 387 / 35 / 0
  - Primeira Liga: 9 / 9 / 9 / 0
  - RPL: 156 / 153 / 15 / 0
  - Serie A: 625 / 620 / 63 / 0
  - Turkey Super Lig: 9 / 9 / 9 / 0
- Latest strict Serie A quote remains `2026-10-13T14:48:53.042620Z`. No new future event has a strict pre-match quote. These are timestamp-consistency counts, not cryptographic source attestation: privileged writers can alter `created_at`.
- The table schema reports RLS enabled for `public.odds_snapshots`. No Supabase write, DDL, source download, provider request, or outcome query occurred.

### Live V2 runtime remains diagnostic-only
- Current-Form Source Capture [run #45217596300](https://github.com/MaksimBlud/football-ai/actions/runs/45217596300) succeeded on main and produced a public source archive despite the project's current Football-Data manifest HOLD. The archive was not downloaded or reused in this audit.
- Current-Form Forward [run #45257233004](https://github.com/MaksimBlud/football-ai/actions/runs/45257233004): `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes not read/scored.
- Original Forward [run #45255423039](https://github.com/MaksimBlud/football-ai/actions/runs/45255423039): 71 tests passed, but `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`; no eligible prospective forecast.
- The main workflows still need the manual root HOLD integration. Do not treat a successful diagnostic workflow or a public artifact as permission to use provider data.

### Frozen V2 and evaluation boundary
- Original candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features, original 20×2 weights, scaler/imputer and training fingerprint unchanged; `active_lambda=0`, `shadow_lambda=1`.
- The independent 30-primary-completed-event outcome gate remains CLOSED / 0 of 30. No prospective Brier/LogLoss comparison or superiority claim is available.
- No XGBoost execution, production `.pkl` access/change, refit, threshold tuning, promotion, bet, paid API request, schedule change, merge, or main update.

HUMAN-MERGE only. This checkpoint is documentation-only and does not authorize source capture, inference, quote access, or outcome reads.

## 2026-11-23 21:58 UTC — Original V2: current-form archive was re-fetched and republished despite zero quotes

### Fresh main and frozen candidate
- Re-read `main`: exact SHA remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; branch protection is disabled and repository visibility is public.
- Original candidate on main remains Git blob `ac1303f6b096664983fbf52443bd0a381b23ba21`, declared SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`, 3,799 training rows, original 19-feature contract, 20×2 weights, active lambda 0, shadow lambda 1, stability gate FAILED, automatic promotion false. No candidate bytes or model parameters changed.

### New real current-form source/forward runtime proof
- Current-form source parent [run #45217596300](https://github.com/MaksimBlud/football-ai/actions/runs/45217596300) completed successfully on main at 2026-11-23 16:33:11 UTC. Its source artifact is `14839276758`, GitHub SHA-256 `2a6cb4902da93c4d15050ba9407543a19bc32c68c3f1f5c4ebe07202bb8c7bd9`, created at 16:33:07 UTC; latest source observation was 16:33:05.648572 UTC. The manifest reports the metadata-only feature-input gate count 110, 10 frozen old-season CSVs plus one current-season CSV (11 files), 3,919 historical rows total and 119 completed prior-day current-season rows.
- The separate feature-input gate query selected only `match_date, home_team, away_team` from the Serie A 2026/27 metadata: 113 raw rows / 113 raw fixture identities, latest date 2026-11-08. The frozen V2-local alias normalization yields 110 canonical identities. This opens only the lagged-feature input gate (minimum 30); it does NOT open target-outcome evaluation.
- Current-form forward [run #45257233004](https://github.com/MaksimBlud/football-ai/actions/runs/45257233004) completed SUCCESS on exact main SHA at 20:14:40 UTC. Exact run summary: `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, `target_outcome_evaluation_gate_open=false`, paid provider calls 0, production/Supabase writes 0, no-bet true.
- **Important runtime detail:** main's `serie_a_v2_current_form_forward_capture.py` calls `verify_latest_source_archive(..., write_sources_to=...)` unconditionally BEFORE fetching saved quotes. That helper downloads, verifies, and copies the latest source ZIP even when there are no quotes. The run uploaded public forward artifact `14857862796` (441,731 bytes; GitHub digest `sha256:5e9515e6105164a2c3a4421c580c38ec73d29bb5b9b2de69c1967bd134c3a8`). The workflow upload step is currently `if: always()`. Thus zero quotes did not mean zero source download or zero source-archive publication. This run proves archive integrity and the metadata gate, but it proves no source-before-quote prediction because there were no quotes.
- The current-form code's own manifest/summary explicitly reports no target-outcome read/scoring and the separate 30-prospective-forecast evaluation gate remains closed. No outcome labels were inspected in this audit.

### New real original-forward runtime proof
- Original Forward [run #45255423039](https://github.com/MaksimBlud/football-ai/actions/runs/45255423039) completed SUCCESS on main at 20:04:29 UTC; 71 regression tests passed.
- It verified old-season source artifact `14845759695` (parent run `45233225104`), SHA-256 `fa2cd29f5b6f8c7155f3d8081764aed2f653df20f05bcc35a281bdc788455a37`, 10 pre-prospective CSVs / 3,800 historical results. Exact forward summary: `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `eligible_for_frozen_prospective_cohort=false`, paid calls 0, Supabase writes 0. Its output artifact `14859255542` was 1,459 bytes (digest `sha256:aa3c94d7013939c9744db0af4bc6e2cbe8c385cf2eb125e7ce7f855c155829a8`).
- This is source-attestation proof only, not a forecast, and not a model-quality result.

### Read-only pre-match Supabase evidence
- Queried only `public.odds_snapshots` metadata/probability clocks, with strict conditions `snapshot_time_utc < commence_time_utc`, `created_at < commence_time_utc`, and `snapshot_time_utc <= created_at`.
- Serie A: 625 total rows, 620 strict pre-match rows, 63 unique events, 0 strict future rows/events. Latest strict pre-match quote remains 2026-10-13 14:48:53.042620 UTC. No score, settlement, payload or target-outcome fields were selected.
- No fresh prospective Serie A market quote exists. The separate outcome-evaluation gate remains 0/30; Brier/LogLoss comparison is unavailable.

### Root hold and human-merge verification
- [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / ready for review / HUMAN-MERGE, exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, based on the exact main SHA above. All eight exact-head PR workflows are SUCCESS. Its workflow patches set `MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=false`, remove Supabase/GitHub live credentials from job-wide environments, gate source/quote reads, and gate artifact uploads on success plus explicit access permission; schedules are preserved. It is not merged and therefore has no effect on main yet.
- [PR #879](https://github.com/MaksimBlud/football-ai/pull/879) remains OPEN / Draft, child of #781, exact HEAD `02bf0873979551ddd98511df013a27f872893990`. The private-repository artifact guard is not on main.
- [PR #946](https://github.com/MaksimBlud/football-ai/pull/946) remains OPEN / Draft, exact HEAD `8c13bb0178b1b7e18b16e2c74ce46cdc70d94ce9`; its isolated source-rights/source-first validation is SUCCESS. It remains branch-only.
- The independent Safe Engineering Agent Auto-Merge run [#45255225408](https://github.com/MaksimBlud/football-ai/actions/runs/45255225408) completed with `SAFE_AUTO_MERGE_HEALTHY_NOOP: no eligible bot PR with verified six-check CI`. The inspected script is restricted to same-repository `github-actions[bot]` engineering-relay drafts with a bounded allowlist and exact six-check CI. It did not merge a PR; no V2 PR was eligible. This Research Brain run did not merge anything.

### Next admissible work
1. HUMAN-MERGE #781 manually; then re-read fresh main and revalidate #879 before any dependent source-first PR.
2. Keep live source capture and forward artifact publication on HOLD until provider rights and private artifact storage are cleared. The current main runtime demonstrates why the hold matters: current-form source ZIP retrieval/publication still occurs even with zero quotes.
3. Continue only offline, V2-specific source/provenance/feature-parity regressions while HOLD remains. Do not use the current public source artifact as an authorized training/inference feed.
4. Only after written source/inference clearance, private artifact storage and fresh source-before-quote market observations may the unchanged 19-feature candidate capture prospective shadows. Keep the independent 30-eligible-prospective-forecast outcome gate closed until satisfied.
5. No Brier/LogLoss superiority claim until a preregistered independent cohort is admissible and the frozen comparison is completed.

No merge, main update, Supabase write/DDL, paid provider request, production `.pkl` change, model refit, threshold tuning, target-outcome read/scoring, promotion, or betting output was performed for this checkpoint.


## 2026-11-23 — Original V2: current-form artifact redirect transport hardening

### Fresh main and frozen candidate
- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository visibility is still public. No main changes or merges were made.
- Re-read the original candidate on main: Git blob `ac1303f6b096664983fbf52443bd0a381b23ba21`, candidate SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`, 3,799 rows, unchanged 19-feature order and 20×2 weights, active lambda 0, shadow lambda 1, stability gate FAILED, automatic promotion false. Feature-builder Git blob remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- The current main `serie_a_v2_current_form_forward_capture.py` still has no direct-access guard import and its `get_archive()` follows redirects automatically. The `market_anchor_v2_direct_access.py` guard is present on the #923 research chain but not on main. #781 (live-access hold) and #879 (private-repository artifact gate) remain OPEN and unmerged; do not treat branch-only guards as deployed.

### PR #936 — current-form artifact redirect origin guard
- [PR #936](https://github.com/MaksimBlud/football-ai/pull/936) is OPEN / Draft / HUMAN-MERGE, child of exact #923 HEAD `2ddef8a7b66324224e5a0d243f364a36109b9420`; final HEAD `5abd4e1db8301bfca34efec09a95accedd082641`, 5 commits ahead / 0 behind, 3 files changed.
- Current-form `get_archive()` now requires exactly one HTTP 302 from the exact GitHub artifact API URL, validates HTTPS Azure artifact-storage host/authority/path, and fetches the signed Location in a separate request with redirects disabled and no GitHub token/API headers. It requires exactly one HTTP 200 and retains the downstream archive-size and SHA-256 checks.
- Offline synthetic tests cover allowed redirect, untrusted/malformed origins, userinfo, nonstandard/trailing port, wrong path, missing query/Location, API 200, second redirect, final URL/history mismatch, invalid artifact IDs, and missing token. No live artifact was downloaded.
- Exact final-head PR CI [#45143275390](https://github.com/MaksimBlud/football-ai/actions/runs/45143275390) and push CI [#45143265405](https://github.com/MaksimBlud/football-ai/actions/runs/45143265405) both SUCCESS. Python 3.11: 64 passed; Python 3.12: 64 passed; compile and production `.pkl` diff guard PASS.
- Intermediate SHA `bd8bc4d5f136e2820436ec3027323b0a1827457c` initially failed both matrix runs due an over-escaped hostname regex; the matcher was corrected to a literal-dot character-class pattern and the exact final SHA above passed both runs. Do not report the intermediate run as passing.
- #936 does not activate any workflow or access path on main. It must not be merged before its #923 → #922 → #921 source-chain parents and the broader #781/#879 rights/private-storage chain are manually reviewed.

### Current-form source and quote chronology
- Re-read current-form source/forward code and workflows on main and #923. The #923 chain retains the fail-closed source-capture access guard and live workflow hold; main does not yet contain that complete rights/private-storage guard.
- Existing original V2 source/quote ordering work remains in #884/#935 and #913–#923. #935's original-forward redirect guard is separate from this new #936 current-form guard; neither has live archive-download proof because live access is held.
- #923 exact source-capture validation runs [#45069538763](https://github.com/MaksimBlud/football-ai/actions/runs/45069538763) and [#45069538786](https://github.com/MaksimBlud/football-ai/actions/runs/45069538786) both SUCCESS. #935 exact isolated validation [#45138819630](https://github.com/MaksimBlud/football-ai/actions/runs/45138819630) SUCCESS.
- #933 exact shadow validation [#45122002023](https://github.com/MaksimBlud/football-ai/actions/runs/45122002023) SUCCESS. #781 exact-head workflows: 8/8 SUCCESS; #902 exact-head workflows: 7/7 SUCCESS. All remain unmerged; HUMAN-MERGE applies.

### Read-only pre-match Supabase evidence
- Queried only `public.odds_snapshots` and only quote/clock/identity columns with strict predicates `snapshot_time_utc < commence_time_utc`, `created_at < commence_time_utc`, and `snapshot_time_utc <= created_at`.
- Result: 3,915 strict pre-match rows across 327 unique events and 9 leagues. Serie A: 620 rows / 63 events; latest strict quote `2026-10-13 14:48:53.042620+00`. No post-match scores, outcomes, settlement, or protected 2026/27 results were queried. No Supabase writes/DDL.
- No fresh prospective Serie A quotes exist after the October 13 snapshot window; the independent prospective evaluation gate remains 0/30. No Brier/LogLoss superiority claim is justified.

### Safety invariants
- No paid The Odds API calls, no production `.pkl` changes, no candidate/weight/feature changes, no Supabase writes/DDL, no main merge, no promotion, no betting output, and no protected outcome reads.
- Next: preserve HUMAN-MERGE ordering; manually review #781/#879 rights and private-storage hold first, then restack source-first parents and current-form redirect guard. Only after legal/source clearance may real pre-match archives and 19-feature V2 shadows be captured prospectively.


## 2026-11-22 03:00 UTC — Original V2 identity SHA and source-clock boundary restacks

### Fresh main and frozen candidate
- Fresh \`main\` is still \`40887ebb215730190d7a6c7a1693373ec4afcdfc\`; the main \`PROJECT_CONTINUITY.md\` blob is still \`2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b\`. This checkpoint is documentation-PR-only; no main update or merge.
- Frozen candidate remains SHA-256 \`a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6\`, original 19-feature order and 20×2 weights, training fingerprint \`f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098\`, active lambda 0, shadow lambda 1, stability gate FAILED. No model bytes, weights, scaler, imputer, or production \`.pkl\` were changed.

### PR #919 — exact metadata/source fixture identity digest
- [PR #919](https://github.com/MaksimBlud/football-ai/pull/919) is OPEN / Draft / HUMAN-MERGE, based on exact #918 HEAD \`81de6253521ac095148480a140e4c6057e2d1987\`; final HEAD \`430411c454807c30f1319dcdb74129d61bc4cddd\`, compare 4 ahead / 0 behind.
- Cleanly restacks the existing #904 identity reconciliation onto the current source-rights/source-clock chain. The Supabase side selects only \`match_date,home_team,away_team\`; the source side hashes only \`Date,HomeTeam,AwayTeam\` after the validated CSV is filtered to completed prior-day rows. Both use the frozen V2-local alias map and deterministic domain-separated SHA-256.
- Exact count AND SHA-256 equality are required before writing the current-season CSV or manifest. Same-count substitutions, duplicate identities, and reversed home/away duplicates fail closed. Both metadata and source digests are recorded in the manifest.
- Exact final-head push run [#44978401107](https://github.com/MaksimBlud/football-ai/actions/runs/44978401107) and PR run [#44978404206](https://github.com/MaksimBlud/football-ai/actions/runs/44978404206) both SUCCESS: Python 3.11 **46 passed**, Python 3.12 **46 passed**, compile and production \`.pkl\` diff guard PASS.
- PR #904 remains an older branch based on #882; #919 is the current restack. Neither was merged. Live source-vs-metadata digest equality remains unproven because the current provider manifest denies automated capture and the current-season CSV was not downloaded.

### PR #920 — strict source-capture entry clock
- [PR #920](https://github.com/MaksimBlud/football-ai/pull/920) is OPEN / Draft / HUMAN-MERGE, based on exact #919 HEAD \`430411c454807c30f1319dcdb74129d61bc4cddd\`; final HEAD \`064209e1acfc5ec05ed45f78fa1a567543a0463b\`, compare 4 ahead / 0 behind.
- The earliest \`_capture_source_archive\` boundary now reuses \`_clock_utc\`, rejecting both naive datetimes and non-null \`tzinfo\` objects whose \`utcoffset()\` is \`None\` before metadata queries, source requests, directory creation, or archive writes.
- Exact final-head push run [#44978577558](https://github.com/MaksimBlud/football-ai/actions/runs/44978577558) and PR run [#44978581183](https://github.com/MaksimBlud/football-ai/actions/runs/44978581183) both SUCCESS: Python 3.11 **48 passed**, Python 3.12 **48 passed**, compile and production \`.pkl\` diff guard PASS.
- #920 is a child of #919; both remain Draft/HUMAN-MERGE and unmerged. No schedule, rights manifest, source provider, inference permission, model contract, or main workflow was changed.

### Fresh read-only Supabase feature-gate and quote audit
- Metadata-only Serie A 2026/27 query through 2026-11-21 UTC selected only \`match_date,home_team,away_team\`: **113 rows**, **113 raw unique identities**, **110 canonical V2 identities** after the existing \`Atalanta BC → Atalanta\` alias; latest date 2026-11-08. This passes only the separate feature-input gate; it does not open target-outcome evaluation.
- Serie A odds metadata query selected only league, event identity and timestamps: **625 rows / 63 events**, **620 strict pre-kickoff rows / 63 events**, **0** strict future rows/events. Latest strict pre-match snapshot remains \`2026-10-13T14:48:53.042620Z\`.
- No score, result, settlement, payload, or protected target-outcome fields were selected. No Supabase writes/DDL, source download, paid request, model inference, or outcome read occurred.
- Current rights manifest remains HOLD after the official provider policy update dated 2026-11-20: automated source capture, frozen V2 inference, AI training, commercial/public use remain denied pending provider-issued permission. The 30-primary-event feature-input gate and separate 30-prospective-forecast evaluation gate must not be conflated; evaluation remains 0/30.

### Main-branch integration blocker
- Root [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review / HUMAN-MERGE, exact HEAD \`3a70a8648895076efec2a80dc10b1798ed0d9261\`, base main \`40887ebb215730190d7a6c7a1693373ec4afcdfc\`, exact-head 8/8 CI PASS. Its default-deny workflow changes are not active until the owner manually merges and fresh-main/runtime proof is repeated.
- Main remains public and still has the unguarded current-form source workflow with \`if: always()\` artifact publication. Actual scheduled source run #44910356674 after the 2026-11-20 policy update uploaded public artifact #14709831168 (439,428 bytes; SHA-256 \`3e38a5274aa79c00114c4f763cb32defc5f1840cba5c27a5c1e5083a1e767207\`). The artifact was not downloaded or reused. Do not treat that run as authorized source capture.
- No Brier/LogLoss superiority claim: no admissible prospective V2 forecasts/outcomes exist for the separate 30-event evaluation gate, and the original stability gate remains FAILED.

### Non-actions
No merge, main update, Supabase write/DDL, provider request/download, paid API call, protected outcome read, inference, refit, threshold tuning, production \`.pkl\` modification, betting, promotion, schedule change, or other-agent change.

## 2026-11-22 00:04 UTC — Original V2 workflow-egress scanner restacked on current rights chain

### Fresh main and frozen candidate
- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` blob remains `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`. This update is confined to documentation PR #839; no main change or merge.
- The main frozen candidate JSON blob is `ac1303f6b096664983fbf52443bd0a381b23ba21`; its declared original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`.
- Independently parsed the candidate and protocol: 19 frozen features in the original order, 20×2 weights (intercept plus 19 features), 19 imputer medians, 19 scaler means and scales, 3,799 training rows, fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`, active lambda 0, shadow lambda 1, stability gate false, automatic promotion false. Original feature-builder Git blob remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.
- No candidate bytes, weights, feature definitions, scaler/imputer, training inputs, or production model files were changed.

### New PR #916 — close workflow-egress inventory bypasses on the current chain
- PR [#916](https://github.com/MaksimBlud/football-ai/pull/916) is OPEN / Draft / HUMAN-MERGE, based on exact PR #915 HEAD `38831b5118126612dcdb7527902c43c3fa0d4661`; exact current HEAD `b174b4a7d036d0405dc9e6d6105080133bcbb70c`.
- Restacks the already-reviewed #895 workflow-hold scanner changes onto the current #781-rooted chain. It adds raw TCP/UDP clients, remote-copy/transfer protocols, alternate compiled runtimes, shell/container launchers and unreviewed composite/marketplace actions to the external-I/O inventory. It preserves the safe negative case for repository-metadata-only `git fetch origin main`.
- The first restacked CI attempt exposed four stale assertions that expected the older simple gate expression. The tests were corrected to require both the workflow-level default-deny flag and verified-private-storage condition while allowing stricter additional predicates.
- Exact current-head PR workflow [#44964743425](https://github.com/MaksimBlud/football-ai/actions/runs/44964743425): SUCCESS. Python 3.11: 24 passed; Python 3.12: 24 passed; compile and production `.pkl` diff guard passed in both jobs. This is offline workflow-contract validation, not model-quality evidence.
- PR #895 remains the original source branch; #916 is the current-chain restack. Neither was merged.

### Current main runtime / root blocker
- PR #781 remains OPEN / Ready for review / HUMAN-MERGE, exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Its exact-head 8/8 CI is recorded in the PR. The default-deny changes are not active on main until manual merge and fresh-main verification.
- Main Original Forward still reads Supabase/saved quotes before source archive discovery/verification; the source-first repair remains in #884 and the current rights restacks. Main free/current-form capture workflows still have live access and public artifact behavior. Actual main Current-Form Source Capture run [#44910356674](https://github.com/MaksimBlud/football-ai/actions/runs/44910356674) completed SUCCESS on the public main SHA and uploaded public artifact 14709831168 (SHA-256 `3e38a5274aa79c00114c4f763cb32defc5f1840cba5c27a5c1e5083a1e767207`). The Football-Data rights manifest remains HOLD; this audit did not download or reuse the artifact. #781 must be manually reviewed before any new live run is considered safe.
- Actual main Original Forward run [#44922609676](https://github.com/MaksimBlud/football-ai/actions/runs/44922609676) completed SUCCESS. Its source attestation verified parent source run 44914641563 / artifact 14710324968, SHA-valid archive, 10 original pre-prospective CSV files and 3,800 historical fixtures. The quote step reported `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`, `paid_provider_calls=0`, and `supabase_writes=0`. The output artifact 14714123247 has SHA-256 `5d382e02818491619b3699559c266419394b89c6987748a09040d285af429358`. This is a real source-attestation/runtime proof only, not a forecast or evidence of model quality. The current main CLI still imports the database and reads saved quotes before its own archive discovery/verification; the #884 source-first CLI fix is therefore still required. Neither source artifact was downloaded or reused by this audit.
- The dependency chain now continues #781 → #879 → #884 → #885 → #887 → #911 → #912 → #913 → #914 → #915 → #916. #839 is the separate documentation branch. Do not merge or alter main automatically.

### Corrected read-only Supabase pre-match audit
- The corrected aggregate query first selected all rows with `snapshot_time_utc < commence_time_utc`, then counted persistence chronology violations; it selected only league, event_id, snapshot_time_utc, created_at and commence_time_utc. No score, result, settlement, or target-outcome columns were read.
- All leagues: 3,915 pre-kickoff snapshot rows / 327 events; missing `created_at`: 0; persisted before observation: 0; persisted at/after kickoff: 0; strict rows/events: 3,915 / 327; future strict rows/events: 0. Latest strict snapshot: `2026-10-13T14:48:53.042620Z`.
- Serie A: 620 rows / 63 events; same zero chronology violations; latest strict snapshot `2026-10-13T14:48:53.042620Z`.
- This supports chronology consistency in the stored rows only. Supabase `created_at` remains mutable by service_role and is not a cryptographic provenance certificate. It also does not substitute for a verified source artifact and successful parent workflow completing before each quote.

### Non-actions
No provider/source request, artifact download, new quote, Supabase write/DDL, protected 2026/27 outcome read, inference, refit, threshold tuning, promotion, betting, paid API call, production `.pkl` modification, schedule change, main update, merge, or other-agent change. No Brier/LogLoss superiority claim; independent prospective evaluation remains closed until its preregistered 30-primary-completed-forecast gate.


# Football AI — Project Continuity

## 2026-11-23 08:28 UTC — Original Forward artifact redirect boundary hardened; exact CI passed

### Fresh main and unchanged candidate
- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` blob remains `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`. No main update or merge occurred.
- Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; 3,799 training rows; 19 frozen features; 20×2 weights; active lambda 0; shadow lambda 1; stability gate FAILED. No model, weights, scaler, imputer, or production `.pkl` changes.

### Root hold and current Original Forward source-first chain
- Root [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review / HUMAN-MERGE, exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; 8/8 exact-head workflows SUCCESS. Frozen V2 Shadow: 113 passed; Recovery: 59 passed; other six validation workflows SUCCESS. Main is still public and these default-deny controls are not active on main until manual merge.
- [PR #879](https://github.com/MaksimBlud/football-ai/pull/879) is the private-storage child of #781 at HEAD `02bf0873979551ddd98511df013a27f872893990`.
- [PR #884](https://github.com/MaksimBlud/football-ai/pull/884) is the source-first Original Forward child of #879 at HEAD `9bfbe01eef1280167285018adadf207248212d07`. Exact-head run [#45137153740](https://github.com/MaksimBlud/football-ai/actions/runs/45137153740) succeeded on Python 3.11 and 3.12: **80 tests passed in each**, compilation and production `.pkl` diff guard passed. Its sibling private-artifact validation [#45137153902](https://github.com/MaksimBlud/football-ai/actions/runs/45137153902) succeeded on both Python versions.
- Fresh main still has Original Forward blob `5db02cbd1367ed25b994b152acf371421859a014` and the wrong direct-CLI order: Supabase client / saved-quote read precedes source archive discovery and verification. #884 moves the lazy DB import and saved-quote reader after successful source-parent and complete ZIP SHA verification. This is not yet active on main.

### New PR #935 — artifact redirect origin and token-isolation guard
- [PR #935](https://github.com/MaksimBlud/football-ai/pull/935) is a Draft child of #884, based on exact #884 HEAD `9bfbe01eef1280167285018adadf207248212d07`; current HEAD `d2e6d84fbe080fe05271d576c815a551d36487ef`; compare **4 ahead / 0 behind**, exactly two files changed.
- Finding: #884's `get_archive()` correctly runs only after source-parent verification, but its artifact ZIP request still used automatic HTTP redirects. GitHub documents the artifact ZIP endpoint as a **302** with a short-lived `Location` URL: https://docs.github.com/en/rest/actions/artifacts#download-an-artifact.
- The new guard disables automatic redirects, requires the documented single 302, validates the current expected HTTPS GitHub Actions Azure artifact-storage host/path shape, then performs a separate bare GET without forwarding the GitHub bearer token or API headers. It requires one HTTP 200 and rejects unknown/lookalike origins, HTTP, userinfo, nonstandard ports, unsigned/malformed paths, missing Location and a second redirect.
- Offline synthetic exact-head run [#45138819630](https://github.com/MaksimBlud/football-ai/actions/runs/45138819630): **92 tests passed on Python 3.11 and 92 on Python 3.12**; compile and production `.pkl` diff guards passed. No real artifact URL was requested and no ZIP was downloaded. The host/path allowlist is therefore CI-tested synthetically; a real artifact redirect remains deliberately unverified while provider rights/private storage are on HOLD.
- PR #935 is OPEN / Draft / mergeable. It is not integrated. The #885/#887 private-CLI and inference-rights descendants are based on an older #884 ancestry and must be deliberately restacked before any integration; do not merge a sibling/duplicate branch.

### Current pre-match quote store — read-only
- Read-only `public.odds_snapshots` query used only league, event ID, snapshot time, kickoff time and created-at chronology; no result/score/settlement fields were selected.
- Strict chronology (`snapshot_time_utc < commence_time_utc`, `created_at < commence_time_utc`, `snapshot_time_utc <= created_at`) returns **3,915 rows / 327 events** across nine leagues.
- Future strict rows/events: **0 / 0**. Latest strict snapshot: `2026-10-13T14:48:53.042620Z`. No fresh prospective market quote exists in this table.
- No Supabase write/DDL or protected outcome query occurred.

### Separate integrity and evaluation controls
- [PR #902](https://github.com/MaksimBlud/football-ai/pull/902) remains OPEN / Ready for review on main, HEAD `0ecc8097bc9f34849a5d1f1ecf05966f1a6f619d`; its seven exact-head workflows succeeded, including the original V2 candidate integrity test. No merge occurred.
- [PR #933](https://github.com/MaksimBlud/football-ai/pull/933) remains OPEN / Draft on the strict temporal-order / outcome-gate branch, HEAD `9fc4fb17dae8d47952983dde0af6b7d006bf3403`; exact-head run [#45122002023](https://github.com/MaksimBlud/football-ai/actions/runs/45122002023) succeeded. Its recursive protected-outcome embargo and canonical duplicate-event gate are offline controls only.
- The 30-primary-completed-event evaluation gate remains 0/30 for eligible prospective V2 forecasts. The separate 110-event feature-input metadata gate must not be conflated with it. No protected 2026/27 outcomes were read; no Brier/LogLoss superiority claim is permitted.

### Non-actions
No main update, merge, source/artifact download, provider request, paid API call, Supabase write/DDL, protected outcome read, inference, refit, threshold tuning, production `.pkl` change, promotion, bet, schedule change, or other-agent change. HUMAN-MERGE only.

---


## 2026-11-21 08:17 UTC — Original V2 source-before-quote restack and free-source rights audit

### Fresh main / continuity
- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` remains 6,152 lines at blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`. This entry is appended only to the open continuity PR #839 branch; no main update or merge occurred.
- PR #781 remains OPEN / HUMAN-MERGE, exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, 8/8 exact-head workflows SUCCESS. The default-deny hold is not active on main until owner merge and fresh-main proof.
- PR #884 remains OPEN; exact HEAD `c38834ec6c2bd0079afca9e63a9ce75a8cd17043`, exact PR workflow SUCCESS, Python 3.11/3.12 each 80 passed. Its old Original Forward source-first fix is not on main.
- PR #900 remains OPEN / Draft, exact HEAD `d0f66f3495fc94a492a2ac8079c963730cbc2057`; exact PR CI SUCCESS, Python 3.11/3.12 each 18 passed.
- PR #901 remains OPEN / Draft, exact HEAD `eab0ef1429c604b30e69874a0557c36d0ecabaac`; exact PR CI SUCCESS, Python 3.11/3.12 each 18 passed.
- PR #902 remains OPEN / Draft, exact HEAD `0ecc8097bc9f34849a5d1f1ecf05966f1a6f619d`; 7/7 exact-head PR workflows SUCCESS; the dedicated original-candidate integrity test reports 11 passed.

### New PR #903 — current-form quote reader now fails closed before any Supabase access
- PR [#903](https://github.com/MaksimBlud/football-ai/pull/903) is OPEN / Draft / unmerged / mergeable, based on exact PR #900 HEAD `d0f66f3495fc94a492a2ac8079c963730cbc2057`; exact head `16b50f2c70e0477fdcbb23faad5e639da3533652`; compare 13 ahead / 0 behind, four files changed.
- Restacks the existing source-before-quote fix from #880 onto #900. It requires exact frozen candidate SHA, source artifact ID/SHA, authenticated parent-run identity, exact source workflow path and strict parent/source/verification time ordering before any quote reader can run.
- Source-capture rights are checked before inspecting the attestation; inference rights are checked before the lazy quote callback. Supabase URL/key are resolved only inside that callback, after both gates.
- If no verified source exists, it emits an outcome-free metadata-only skip report with zero quotes, no inference, no Supabase credentials/client and no copied source artifact. If a source exists but inference rights are unresolved, it fails before secret lookup or client creation.
- Exact push [#44883790037](https://github.com/MaksimBlud/football-ai/actions/runs/44883790037) and PR [#44883795454](https://github.com/MaksimBlud/football-ai/actions/runs/44883795454) both SUCCESS on exact head: Python 3.11 and 3.12 each **28 passed**, compile and production `.pkl` guard PASS.
- #903 is a parallel child of #900, not a child of #901. If #901 is merged first, #903 must be restacked before integration. A comment on #880 says not to merge #880 independently; #903 is the current restack.
- No live source, quote, Supabase, or target-outcome access was performed by #903 CI. No model inference or production changes.

### New source audit — Soccer Data Free API (HOLD)
- Updated source-rights audit PR [#868](https://github.com/MaksimBlud/football-ai/pull/868), exact HEAD `f90379ad5e222d318cdb1fa13ac569252126d4b4`, 6/6 exact-head PR workflows SUCCESS; one documentation file changed.
- Official terms/pricing/docs show Free has 50 requests/day, current-season-only stats, no odds; stats endpoint exposes corners/cards/shots on target but field coverage varies and is per match. Terms permit storage only while account/plan is active and prohibit raw data redistribution; they do not expressly grant AI/ML training or long-term research-archive rights and do not identify upstream field-level rights. Finished-match list returns score fields in the same response and documents no field projection; no historical-stat update timestamp is documented. Candidate remains **HOLD**, no API key/account/request.
- Football-Data, OpenLigaDB and open-matchday remain HOLD for the reasons recorded in #868. No new free source is approved for original V2 capture.

### Read-only Supabase pre-match status
- Aggregate SELECT on `public.odds_snapshots`, restricted to `snapshot_time_utc < commence_time_utc` and `created_at < commence_time_utc`, returned **3,915** strict pre-kickoff rows across **327** events; Serie A **620** rows / **63** events. Latest strict Serie A snapshot remains `2026-10-13T14:48:53.042620Z`.
- A separate future-only aggregate with the same strict timestamp conditions returned **0** future rows / **0** events. No new eligible quote exists for a source-before-quote forecast pair.
- No score/result/settlement fields or protected target outcomes were selected. `created_at` remains mutable by service_role and is not cryptographic proof.

### Frozen model and binding gates
- Candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098` (as recorded in the existing candidate audit); 3,799 training rows; 19 frozen features; 20×2 weights; original scaler/imputer; `active_lambda=0`; `shadow_lambda=1`; stability FAILED; independent prospective evaluation **0/30**.
- No Brier/LogLoss comparison or V2-over-market claim is supported.
- No main update or merge; Supabase writes/DDL=0; paid API requests=0; target outcomes read/scored=0; production `.pkl` unchanged; no schedules or other agents changed. HUMAN-MERGE remains mandatory.

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


## 2026-11-21 02:30 UTC — authoritative original V2 recovery checkpoint

This checkpoint is appended to the exact current-main PROJECT_CONTINUITY.md bytes. The previous branch copy had a large non-additive rewrite (3,975 deleted lines in the PR diff); that rewrite is not retained. Current main's 6,152 lines are preserved byte-for-byte as the prefix, and this section is additive only.

### Current main and original workflow order

- Main SHA: 40887ebb215730190d7a6c7a1693373ec4afcdfc.
- Main source file blob: serie_a_v2_forward_capture.py SHA 5db02cbd1367ed25b994b152acf371421859a014.
- On main, main() still imports Supabase and reads saved Serie A quotes before discover_archives(); source-before-quote remains broken on main. PR #884 corrects this in its isolated branch.
- Main schedules remain: free diagnostic 06:13 UTC; current-form source capture 05:50 UTC; original forward 08:08 UTC; current-form forward 08:18 UTC. PR #781 retains schedules but gates live source/read/upload steps.
- Main still has no merged default-deny hold. The next scheduled daily Football-Data source capture is not authorized under the provider's current published free-use wording; do not interpret a prior successful run as permission.

### Real GitHub Actions results on main

- Original Forward #44777970547: SUCCESS, 71 passed; 10 historical CSVs / 3,800 historical matches verified; quotes_seen=0, future_quotes_checked=0, diagnostic previews=0, no paid calls or Supabase writes. Artifact 14650229424 SHA-256 6a0c0a0a6c210462cf3f48290eadeb24c3d6a1418973d9e093ca45adaba0eec2.
- Current-Form Source Capture #44753230529: SUCCESS, 19 passed; 10 historical CSVs plus current-season CSV, 3,910 total match rows; 110 completed fixture identities passed the feature-input identity gate. target_outcomes_scored=false. Artifact 14636526350 SHA-256 2237cc30b84b2e982586ce7ef44b3ab4887c286e5f3320b8f9579cdc8e9dbca8.
- Current-Form Forward #44778623731: SUCCESS, 53 passed; source artifact ID, SHA, parent workflow/head/completion verified; source age 9,169 seconds (<24h). quotes_seen=0, shadow forecasts=0, target_outcomes_read=false, target_outcomes_scored=false, no provider calls/writes. Artifact 14650324439 SHA-256 62a1b4cc86a0a70e7b89da63e58391ec4d4e383c7c3720f69397dccc98a122ee.
- The 110 feature-input events do not open the separate prospective evaluation gate. Evaluation remains CLOSED at 0/30; no protected 2026/27 target outcomes were read.

### Supabase — read-only, pre-match fields only

At 2026-11-21 02:16 UTC, SELECT-only aggregate over public.odds_snapshots:

- 3,966 total rows.
- 3,915 rows satisfy both snapshot_time_utc < commence_time_utc and created_at < commence_time_utc.
- 327 unique events in that strict subset.
- 0 strict pre-kickoff rows for future events.
- Latest eligible Serie A snapshot 2026-10-13T14:48:53.042620Z; created_at 2026-10-13T14:48:53.157404Z.

No scores, match outcomes, settlements or protected targets were queried. created_at is mutable by service_role and is not cryptographic proof; require the private source archive SHA, parent workflow completion and source-before-quote chain.

### Original frozen candidate reverified from main

Candidate artifact SHA-256: a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6.
Training fingerprint: f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098.
Training rows: 3,799.
Feature count: 19; weights: 20×2; scaler mean, scaler scale and imputer medians each have 19 entries.
Original feature order:
1. diff_points_5
2. diff_points_10
3. diff_points_venue5
4. diff_goals_for_5
5. diff_goals_for_10
6. diff_goals_against_5
7. diff_goals_against_10
8. diff_corners_for_5
9. diff_corners_for_10
10. diff_corners_against_5
11. diff_corners_against_10
12. diff_yellow_5
13. diff_yellow_10
14. diff_red_5
15. diff_red_10
16. diff_goals_for_venue5
17. diff_goals_against_venue5
18. diff_corners_for_venue5
19. diff_corners_against_venue5

active_lambda=0 remains the market fallback; shadow_residual_lambda=1 remains research-only. Stability gate FAILED, automatic promotion false. No refit, weight/feature-order/scaler/imputer change or production .pkl change.

### Exact-head research PR chain

- #781 root default-deny hold: HEAD 3a70a8648895076efec2a80dc10b1798ed0d9261, base main 40887ebb215730190d7a6c7a1693373ec4afcdfc, 8/8 exact-head SUCCESS, OPEN / Ready for review. Owner manual merge required. It gates all four live V2 workflows and archive publication while preserving offline tests and schedules.
- #879 private-retention prerequisite: HEAD b78010585c80b05ae5fc2a8b3572df14b32d9651, 4/4 exact-head SUCCESS, Draft.
- #884 source-before-quote: HEAD c38834ec6c2bd0079afca9e63a9ce75a8cd17043, base #879 HEAD, 4/4 exact-head checks SUCCESS; Python 3.11 and 3.12 each 80 passed; tampered-ZIP SHA rejection precedes DB import and quote access.
- #885 private-repository CLI guard: restacked on #884 HEAD c38834ec6c2bd0079afca9e63a9ce75a8cd17043; current HEAD a1d065f1c3a03895bbef5b72e5bf664cdd68f33f, compare 1 ahead / 0 behind, 4/4 exact-head checks SUCCESS; Python 3.11 and 3.12 each 84 passed; production .pkl diff guard passed. Draft.
- #868 Football-Data rights audit correction: HEAD 2daefda90169f260ef99b0b2a58e34e505c0e4c3, 6/6 exact-head SUCCESS. The separate contact/fair-use page updated 2026-11-20 caps otherwise permitted light automated downloads at twice per week maximum and excludes commercial or AI data-training projects using bots/scrapers. The data page's “updated at least twice weekly” is publication cadence, not a download allowance.
- #794 Big Balls current docs recheck: HEAD 4328d066fc76d55848b6903438c6da733b3faef8, 6/6 exact-head SUCCESS. Its Terms expressly permit stored responses as internal-model inputs, but its OpenAPI marks the factual match-stat route Free while the Serie A plan matrix marks advanced stats Edge; FAQ says Free except xG (Solo+). No written resolution, current-season per-fixture completeness or per-field first-observation timestamp. HOLD.
- #839 documentation/runtime PR itself: previous exact-head HEAD 71857032439d3bb179a3882c19b048f7dd954e68, 8/8 SUCCESS; Frozen V2 Shadow Tests 88 passed. This new additive checkpoint triggers a fresh exact-head CI run.

### Source eligibility and next gates

Football-Data.co.uk's current free-use scope does not clear the daily automated AI source capture or the frozen training-corpus/learned-weight rights. Big Balls is the strongest current-season candidate screened so far, but remains HOLD pending written resolution of its plan conflict, upstream rights and field coverage. 5DollarFootballAPI, API-Football, DataSportsAPI, ODSS, Soccer Data, 11footy and official Lega reports remain unapproved under their documented limitations/rights/contract gates. No provider was connected, no key/account created, no API or odds request made.

Next sequence: owner manually merges #781; reread fresh main; then resolve #879 private retention, #884 source-before-quote and #885 private-repository checks in dependency order; obtain written source rights/plan confirmation; only then consider a private raw source archive with exact bytes, SHA, receipt timestamp and parent completion strictly before each saved quote. No new quote provider is admitted: the frozen V2 quote contract remains the existing saved Serie A 1X2 observations. After eligible source and quote capture, calculate the unchanged 19 features; only after 30 eligible prospective forecasts may the protected target-outcome gate open for independent Brier/LogLoss diagnostics against de-vigged market and frozen incumbent.

No merge, main update, Supabase write/DDL, paid API request, target-outcome read, production artifact change, model refit, threshold tuning, auto-promotion, bet or schedule/other-agent setting change occurred.


## 2026-11-21 02:40 UTC — descendant PR ancestry after #885 restack

#885 was restacked and its exact new HEAD is green, but its descendants have not yet been restacked. Do not merge any descendant from this old stack until the chain is rebuilt and exact-head CI is rerun:

- #885 current HEAD a1d065f1c3a03895bbef5b72e5bf664cdd68f33f, parent #884 current HEAD c38834ec6c2bd0079afca9e63a9ce75a8cd17043; 4/4 exact-head checks SUCCESS (84 passed on Python 3.11 and 3.12).
- #887 still records old base 24b0928ad3d73f9a2e4f91f1948e6521d7c41de8 rather than #885 current HEAD. Its own HEAD 954be44504bfa8c519d3813cbf43ab7c53efcaad has 4/4 successful checks on the old ancestry.
- #888 still bases on old #887 HEAD 954be44504bfa8c519d3813cbf43ab7c53efcaad; its own HEAD 6cfef9ffe8e13009284a3227775ec5bfcda0b84e has 4/4 successful checks on that old ancestry.
- #889 still bases on old #888 HEAD 6cfef9ffe8e13009284a3227775ec5bfcda0b84e; its own HEAD 7d95be58d40ee0d851fbef042b098b749aa13384 has 4/4 successful checks on that old ancestry.
- #890 still bases on old #889 HEAD 7d95be58d40ee0d851fbef042b098b749aa13384; its own HEAD aade422896d32e38f1a1afb5dde7e1bae5351399 has 4/4 successful checks on that old ancestry.
- #891, #892 and #893 each still base on old #890 HEAD aade422896d32e38f1a1afb5dde7e1bae5351399; their recorded heads e0d729d78a24a977f8cf76c04bcee19de4488c22, 5408e7392b4a73b89b2525735c3cfd17c736e4dc and 5fd6fe2a8ef131dd166dfcac2785d74fab970a4d respectively each have 4/4 successful checks on the old ancestry.

These checks are real exact-head results for those historical commits, but they are not evidence that the current #885→#887→#888→#889→#890→(#891/#892/#893) stack is integrated. Rebase/restack sequentially, preserve all source-rights gates, then rerun exact-head CI at every child. No descendant merge is authorized by this checkpoint.


## 2026-11-21 02:52 UTC — full rights-gate child stack restacked

The private/inference-rights child chain was restacked sequentially after #885's corrected private-CLI test fixtures. Every new child now names the current parent HEAD as its base; all new heads are one commit ahead of their parent. Exact check-runs:

- #885 HEAD a1d065f1c3a03895bbef5b72e5bf664cdd68f33f on #884 c38834ec6c2bd0079afca9e63a9ce75a8cd17043: 4/4 SUCCESS.
- #887 HEAD a24ddc440e5eae36edc120e53c7f63d59c754475 on #885 a1d065f1c3a03895bbef5b72e5bf664cdd68f33f: 4/4 SUCCESS.
- #888 HEAD 2fe841747355c4909c551a17d9df372b3b1bae2a on #887 a24ddc440e5eae36edc120e53c7f63d59c754475: 4/4 SUCCESS.
- #889 HEAD 2948deab0a1f651b4f2331a739a2c80af65d0c8c on #888 2fe841747355c4909c551a17d9df372b3b1bae2a: 4/4 SUCCESS.
- #890 HEAD 48c5ab40a8ad0408f60262fbff46728f5bda4108 on #889 2948deab0a1f651b4f2331a739a2c80af65d0c8c: 4/4 SUCCESS.
- #891 HEAD 3714eadd432d580a2d848c1b35599223dc581ab0 on #890 48c5ab40a8ad0408f60262fbff46728f5bda4108: 4/4 SUCCESS.
- #892 HEAD 7501c4cd2f38a55462b0564590ee2109280d2e99 on #890 48c5ab40a8ad0408f60262fbff46728f5bda4108: 4/4 SUCCESS.
- #893 HEAD 6082fc9f80dff501c220166c5a53abe0b71db13e on #890 48c5ab40a8ad0408f60262fbff46728f5bda4108: four exact-head checks are still in progress at this checkpoint.

The new heads are not merge approvals. Keep all these PRs Draft / HUMAN-MERGE and preserve dependency order. No merge was performed.

### Big Balls source recheck and current V2 contract

PR #794 current official-docs audit HEAD 4328d066fc76d55848b6903438c6da733b3faef8 has 6/6 exact-head CI SUCCESS. Its Terms (effective 2026-08-10) explicitly permit stored API responses as internal-model inputs, including training/evaluation/backtesting, and allow derived outputs to be published/sold; raw fields cannot be redistributed. The current OpenAPI marks /v1/matches/{id}/statistics Free with expected_goals Solo+, while the same Serie A plan matrix marks advanced match stats Edge and the FAQ says Free except xG. The provider has not resolved that contradiction in writing. Current-season standings show 20 clubs with 11 matches each as of 2026-11-19, but per-fixture stats completeness is not published. The endpoint is stored-only/hourly and exposes no per-field first-observed timestamp. Decision remains HOLD; no account/key/API request or data download.

The source rights gate also remains independent from the frozen training corpus. Football-Data.co.uk's 2026-11-20 contact page caps otherwise permitted light automated downloads at twice per week maximum and excludes AI data-training projects; the main daily collector therefore remains unauthorized. Big Balls' own terms do not clear the original Football-Data.co.uk training corpus or the learned frozen weights.

### Continuity PR validation state

This PR's PROJECT_CONTINUITY.md is now exact current-main content plus additive checkpoints; current main lines are preserved byte-for-byte and the diff contains no deletions in PROJECT_CONTINUITY.md. The latest documentation HEAD is 4f31ffc26cceeef49af211bfa2e61a1a0cee365e; its new exact-head CI is pending and must be rechecked before this documentation PR is presented as green.


## 2026-11-21 02:48 UTC — fresh V2-only main, CI and pre-match data revalidation

### Immutable main baseline and source-order defects

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; current-main `PROJECT_CONTINUITY.md` blob is `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b` (6,152 lines).
- Main `serie_a_v2_forward_capture.py` blob `5db02cbd1367ed25b994b152acf371421859a014`: its CLI imports the database client and reads saved quotes before `discover_archives()`. This is still a real source-before-quote defect on main; #884 is the isolated correction.
- Main `serie_a_v2_current_form_forward_capture.py` blob `326ac1921ce901a31aa6d73e6cbddb0782071964`: it verifies the latest source archive, then unconditionally creates the Supabase client and reads saved quotes even when verification returned `NO_SOURCE_ARCHIVE`. #880 contains the lazy quote-read correction.
- The current main workflows still contain their live steps. The free diagnostic workflow blob is `60bd304153e5c731ff6246c76fe2f3ace1bc0dcb`; the current-form forward workflow blob is `6ebbcaff290a78e9ccffa4ac9a09bc0982eaff35`. The default-deny #781 hold is not in main.

### Current exact-head PR state — commit-bound Actions reads

- #781 root live-workflow hold: base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, OPEN / Ready for review, 8/8 exact-head checks SUCCESS. HUMAN-MERGE only.
- #879 private artifact/repository gate: HEAD `b78010585c80b05ae5fc2a8b3572df14b32d9651`; dedicated run #44433687358 SUCCESS.
- #884 original-forward source-before-quote CLI: HEAD `c38834ec6c2bd0079afca9e63a9ce75a8cd17043`; exact-commit run #44854473405 SUCCESS.
- #885 private-repository CLI guard: HEAD `a1d065f1c3a03895bbef5b72e5bf664cdd68f33f`; run #44855586194 SUCCESS.
- Restacked rights descendants are now all green on their current exact commits: #887 `a24ddc440e5eae36edc120e53c7f63d59c754475` / run #44856571059; #888 `2fe841747355c4909c551a17d9df372b3b1bae2a` / #44856603410; #889 `2948deab0a1f651b4f2331a739a2c80af65d0c8c` / #44856627660; #890 `48c5ab40a8ad0408f60262fbff46728f5bda4108` / #44856649953; #891 `3714eadd432d580a2d848c1b35599223dc581ab0` / #44856698681; #892 `7501c4cd2f38a55462b0564590ee2109280d2e99` / #44856732341; #893 `6082fc9f80dff501c220166c5a53abe0b71db13e` / #44856767023. Each named dedicated workflow completed SUCCESS on the commit passed to the run lookup.
- #880 current-form no-quote-without-verified-source: HEAD `d16fa3c1e9d83b6917c8a46975b18ab238572c2f`, base #877 HEAD `245c20b1acc398c5c8bad8541282378b66902cf3`, exact run #44852999179 SUCCESS; Python 3.11 and 3.12 each report 43 passed. Its branch is the #875 → #876 → #877 line. #893 is a separate descendant of #890 and also changes the same current-form forward file. Do not integrate both branches independently without a deliberate restack/ancestry reconciliation.
- #893's live PR API base SHA is #890 HEAD `48c5ab40a8ad0408f60262fbff46728f5bda4108`; its PR body still contains an older parent SHA `aade422896d32e38f1a1afb5dde7e1bae5351399`. Refresh that stale body sentence before merge review.
- #895 raw-socket/remote-transfer workflow-hold scanner: HEAD `9431c13c3696d063f1c7ba0989bbfb87656639af`, run #44723931083 SUCCESS, based on #781.
- #896 strict saved-quote persistence: HEAD `7a47d310b2a6fda62267cd63557fb3cdd10d2b03`, run #44666194948 SUCCESS, but GitHub currently reports mergeable=false. #897 is its child, HEAD `9915b039621ac5317feae7f449c493a344fe45f4`, run #44671316543 SUCCESS. Do not merge #897 ahead of #896.
- #839 documentation/source-audit PR: exact HEAD `e461a3ea3af4686c660df144e3e40fe5459c3daa`, 8/8 exact-head Actions workflows SUCCESS. The Frozen V2 Shadow job log for run #44856827814 explicitly reports 88 passed and the production `.pkl` diff guard passed.

### Free-source research status

- #792 5DollarFootballAPI official audit HEAD `e48239d0a405a0e98a5dd270f1740deef7b3eb7d`: 6/6 exact-head workflows SUCCESS. The provider's fixture example does not contain per-fixture `league_season_id`; the schema correction is recorded. Provider remains HOLD due Free-vs-Pro Serie A conflict, unresolved upstream rights/private retention and no upstream observation timestamp.
- #800 offline 5Dollar adapter HEAD `140baffdc9ec55a4fb04de8806d0ee8811686940`: 7/7 exact-head workflows SUCCESS; Frozen V2 Shadow suite 120 passed. It has no network client and makes no request. It is not source approval.
- #794 Big Balls audit HEAD `4328d066fc76d55848b6903438c6da733b3faef8`: 6/6 exact-head workflows SUCCESS. HOLD remains: plan matrix conflicts with the Free OpenAPI route, upstream attribution points to Football-Data, and there is no per-match upstream first-observed timestamp.
- #886 11footy remains HOLD: CC BY-NC 4.0, upstream source rights unresolved and no per-match first-observed timestamp; no exact-head Actions run was returned for its current commit.
- Football-Data's current free-use wording does not authorize the existing daily automated AI source/training pattern. No provider is approved for capture or inference.

### Supabase — SELECT only, pre-match fields only

A new aggregate queried only `public.odds_snapshots`, requiring BOTH `snapshot_time_utc < commence_time_utc` and `created_at < commence_time_utc`:

- 3,966 total rows; 3,915 strict pre-match rows; 327 unique events.
- Strict pre-match Serie A rows: 620; unique events: 63; latest snapshot `2026-10-13T14:48:53.042620Z`.
- No future strict pre-match odds rows were returned.
- A separate metadata-only query of `public.matches` selected only league/date/home/away fixture fields for dates from current_date onward and returned no future fixture rows.
- The mutable `created_at` field is not a cryptographic attestation; the source ZIP SHA and authenticated parent-workflow completion must remain part of the proof.

No scores, outcomes, settlements or protected target fields were queried.

### Frozen original candidate and scientific gate

- Candidate SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; 3,799 training rows.
- Exact original 19-feature order, 20×2 weights, scaler and imputer remain frozen.
- `active_lambda=0` remains the market; `shadow_lambda=1` remains research-only; stability gate FAILED; prospective outcome-read gate remains 0/30.
- The 110 completed-event feature-input identity count is not the separate 30-prospective-forecast evaluation gate. No Brier/LogLoss claim is available and no protected 2026/27 target outcome was read.

### Non-actions

No merge, main update, Supabase write/DDL, provider request, paid API call, target-outcome read, production `.pkl` change, refit, weight/feature/contract change, promotion, bet, schedule change or other-agent setting change. All branches remain subject to HUMAN-MERGE and dependency order.


## 2026-11-21 03:12 UTC — restacked timestamp chain and final exact-head validation

### New restack and regression evidence

- #896 was stale/dirty against the current #891 branch. It has been restacked directly on #891 HEAD `3714eadd432d580a2d848c1b35599223dc581ab0`.
- Current #896 HEAD: `cd2bc9cceeba7a5b69eb3172315e7b5810bc6b85`; GitHub reports 1 ahead / 0 behind and `mergeable=true`.
- #896 exact-head validation: 4/4 check runs SUCCESS (push + PR, Python 3.11 and 3.12); each Python run reports 72 passed. Compilation and production `.pkl` diff guard passed. The intermediate HEAD `e98dd72a...` failed two forward tests because the synthetic test fixture had not stubbed the newly imported frozen-preview inference guard; that fixture is now explicitly patched, and the expired-fixture and persistence-at-kickoff cases are separate tests.
- #897 was restacked directly on corrected #896 HEAD `cd2bc9cceeba7a5b69eb3172315e7b5810bc6b85`. Current #897 HEAD: `ea3a9d5bc86294239ed693948044c5b065cbdecd`; GitHub reports 1 ahead / 0 behind and `mergeable=true`.
- #897 exact-head validation: 4/4 check runs SUCCESS (push + PR, Python 3.11 and 3.12); each Python run reports 76 passed. Compilation and production `.pkl` diff guard passed.
- The strict reader now selects `created_at`, filters both `snapshot_time_utc` and `created_at` no later than the capture clock, and rejects either timestamp at/after kickoff. The trusted collector regression proves the repository writer drops caller-supplied `created_at` and leaves the Postgres default. The database field remains mutable by service_role; this is not a cryptographic attestation.

### Current-form source-order branch integration warning

- #880 remains the separate source-before-quote fix on the #875 → #876 → #877 line: HEAD `d16fa3c1e9d83b6917c8a46975b18ab238572c2f`, exact run #44852999179 SUCCESS, 43 passed on Python 3.11 and 3.12.
- #893 remains on the #890 rights line: HEAD `6082fc9f80dff501c220166c5a53abe0b71db13e`, exact run #44856767023 SUCCESS. Its PR body ancestry sentence was corrected to live API base #890 HEAD `48c5ab40a8ad0408f60262fbff46728f5bda4108`.
- Both #880 and #893 change `serie_a_v2_current_form_forward_capture.py`. Do not merge them independently without choosing a merge order and restacking the later PR onto the earlier one. No branch has been merged.

### Continuity PR exact-head state

- #839 current HEAD is `882bf5052e7ba37e5e7c390abeed0e6c9bd40b09` against main `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Exact-head checks: 8/8 SUCCESS. Frozen V2 Shadow job #44858904016 reports 88 passed; production `.pkl` diff guard passed.
- The continuity file remains additive versus main: 6,152 original lines retained in order; current diff reports 173 additions and zero deletions in `PROJECT_CONTINUITY.md`. The PR includes research/audit/test files only; no model artifact or schedule modification.

### Latest pre-match-only evidence remains unchanged

- Supabase SELECT over `public.odds_snapshots`, requiring both `snapshot_time_utc < commence_time_utc` and `created_at < commence_time_utc`: 3,966 total, 3,915 strict pre-match rows, 327 unique events.
- Strict Serie A: 620 rows / 63 events; latest `2026-10-13T14:48:53.042620Z`.
- No future strict pre-match odds rows; metadata-only future fixture query on `public.matches` returned no rows.
- Free-source approvals remain HOLD: Football-Data daily automated AI capture is not cleared; 5Dollar and Big Balls have unresolved Free/Pro/Edge or upstream-rights/timestamp questions; 11footy is CC BY-NC 4.0 and not approved.
- Separate Supabase security finding: RLS is disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No policy/DDL change was attempted because DDL is outside scope.

### Original V2 remains frozen and unevaluated

Candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; 3,799 rows; 19 features; 20×2 weights; frozen scaler/imputer; `active_lambda=0`; `shadow_lambda=1`; stability gate FAILED; prospective evaluation gate 0/30. No Brier/LogLoss conclusion and no protected 2026/27 target outcomes read.

No merge, main write, Supabase write/DDL, paid API, source-provider request, model artifact mutation, refit, weight/feature/contract change, promotion, bet, schedule change or other-agent setting change.


## 2026-11-21 03:14 UTC — additional free-source screen (no provider access)

A fresh public-docs scan was completed without creating accounts, keys, API calls, downloads, or source capture:

- **open-matchday** advertises daily 2026/27 CSVs for 75 competitions including Serie A, fixtures, scores and some match statistics. It explicitly limits the compilation to informational/non-commercial use; upstream providers retain their own terms. Its own README says detailed shots/fouls/cards/corners occur in only about 19% of result rows, stats can lag one or two gameweeks, and the pipeline mixes OpenLigaDB, fixturedownload, ESPN, Football-Data, FotMob and Soccerway. There is no per-row first-observed timestamp; the daily build time is not a per-field source attestation. **HOLD / not approved for V2 capture or inference.**
- **PitchAPI** is advertised as free with no paid tier, but the public documentation/independent coverage record does not establish a licence, commercial-use right, named upstream data provider, or verified per-league coverage. **HOLD pending written terms and provenance.**
- **Footballdata.io / Soccer Data / SportStatsAPI** advertise free tiers, but the reviewed free-tier material does not establish unrestricted model-training/commercial rights; some explicitly restrict the free tier to non-commercial use. **HOLD.**
- **Openplay** is CC BY 4.0 but is a snapshot ending in 2025/26 and the upstream event source is WhoScored; it does not solve current 2026/27 pre-match capture or the upstream-rights question. **HOLD.**
- The FootballAPIs.com directory is a catalogue of API plans, not a match-data source and is not a data integration candidate.

No candidate in this scan is approved. Do not use the open-matchday data merely because the CSV is public or its compilation is free; its non-commercial restriction and upstream provider terms remain binding questions. The existing #792/#794/#800 source audits remain the authoritative detailed reviews of 5Dollar and Big Balls.

## 2026-11-21 03:30 UTC — current-form source-capture rights restack and strict pre-match recheck

### Fresh main and HUMAN-MERGE baseline

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; it was not modified in this cycle.
- Main branch protection is disabled (`protected=false`; required status enforcement off). Do not infer that green PR checks protect main; retain HUMAN-MERGE.
- Root live-workflow hold [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / not merged, HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, exact-head CI 8/8 SUCCESS. The daily source/forward workflow schedules remain present on main and are not held there yet. No live workflow was manually dispatched.

### New current-form source-capture rights restack

- [PR #898](https://github.com/MaksimBlud/football-ai/pull/898), Draft / OPEN, exact HEAD `dd96b6bb9ed628ec5d85814ee779fb90d12c9c86`, base is PR #891 HEAD `3714eadd432d580a2d848c1b35599223dc581ab0`.
- Exact PR-triggered run [44861183108](https://github.com/MaksimBlud/football-ai/actions/runs/44861183108) SUCCESS: Python 3.11 **19 passed**, Python 3.12 **19 passed**; production `.pkl` diff guard passed in both jobs. Matching push run [44861155971](https://github.com/MaksimBlud/football-ai/actions/runs/44861155971) also SUCCESS on the same HEAD.
- Confirmed gap: current-form source-capture public API, metadata helper and CLI did not enforce the newer provider-issued source-capture rights/private-storage chain before Supabase metadata or source access. #898 applies the existing SHA-pinned rights validator and private repository check before those entrypoints.
- #898 also ports the exact preregistered V2 gate semantics previously isolated in #875: protocol blob SHA `65729e9639720e67624c1481190aa22ae606f151`, `FIRST_OUTCOME_READ_GATE=30`, Serie A-only primary cohort, metadata-only gate query, and separate still-closed 30-prospective-forecast evaluation gate. Protocol tampering fails before metadata/source access.
- The checked-in Football-Data rights manifest still says source capture is not permitted. The real manifest test proves denial occurs before private-repository API lookup; CI used synthetic rights only for offline fixture tests. No live source request occurred.
- #898 is a restack of the #875/#876 source-capture work on the newer #888/#889/#890/#891 rights chain. Do not merge #875/#876 independently; review #898 as the replacement current-form source-capture path.

### Strict pre-match Supabase audit (SELECT only)

- The stricter filter `snapshot_time_utc < commence_time_utc AND created_at < commence_time_utc` returned **3,915** rows across **327** unique events.
- No row had a pre-kickoff snapshot with a missing or post-kickoff `created_at` value.
- Latest strict Serie A snapshot remains `2026-10-13T14:48:53.042620Z`.
- Previous same-cycle filter confirmed **0** future-event strict pre-match quote rows. No scores, results, settlements or protected target outcomes were selected.

### Original V2 and live-data state

- Candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; 3,799 training rows; 19 frozen features; 20×2 weights; frozen scaler/imputer.
- `active_lambda=0` remains the market fallback; `shadow_lambda=1` remains research-only; stability gate remains FAILED; independent evaluation remains **0/30**.
- Last verified main runs remain Original Forward #44777970547, Current-Form Source Capture #44753230529 and Current-Form Forward #44778623731. No new admissible quote or shadow forecast was observed in this cycle.
- No Brier/LogLoss claim or V2-over-market superiority is supported.

No merge, main update, Supabase write/DDL, paid API request, target-outcome read, production artifact change, model refit, threshold tuning, promotion, bet, schedule change or other-agent setting change occurred.

## 2026-11-21 03:32 UTC — final exact-head retest for current-form capture rights

- PR #898 received a least-privilege workflow adjustment: `GITHUB_TOKEN` is now scoped only to the gated capture step, not the whole job. The live workflow flag remains `false`; schedules and triggers are unchanged.
- Current PR #898 HEAD is `ea97737d02cdbf4952ab94bfb8e7436b7a4f5828`, based on #891 HEAD `3714eadd432d580a2d848c1b35599223dc581ab0`.
- Exact PR run [44861467621](https://github.com/MaksimBlud/football-ai/actions/runs/44861467621) SUCCESS; Python 3.11 and 3.12 each report **19 passed**; production `.pkl` diff guard passed in both jobs. Exact matching push run [44861463277](https://github.com/MaksimBlud/football-ai/actions/runs/44861463277) also SUCCESS.
- This final HEAD supersedes the earlier #898 HEAD `dd96b6bb9ed628ec5d85814ee779fb90d12c9c86` recorded in the preceding checkpoint. No merge was performed; #898 remains Draft/HUMAN-MERGE and its parent chain remains unmerged.
- The documentation PR #839 itself is now at HEAD `43ca64a7a2744112d9dbaae0e448bd957b1f732e`; its exact eight workflows all completed SUCCESS (8/8). The current-main 6,152-line continuity file remains an exact prefix; this branch adds only checkpoint text.


## 2026-11-21 03:56 UTC — rights-gated source capture, token binding, and fresh runtime audit

### Fresh main and continuity

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no merge or main write occurred in this iteration.
- This update is appended to the existing PR #839 continuity branch; it does not rewrite prior history.
- Original candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`, 3,799 training rows, 19 features, 20x2 weights. `active_lambda=0`, `shadow_lambda=1`; stability FAILED and evaluation gate CLOSED at 0/30. The 110 feature-input identities do not open the separate evaluation gate.

### New PR #899 — step-scoped rights token

- PR [#899](https://github.com/MaksimBlud/football-ai/pull/899), HEAD `90cc6d93b283ea4411ab6331021c6db396c2525f`, is stacked on #898 HEAD `ea97737d02cdbf4952ab94bfb8e7436b7a4f5828`.
- Finding: the rights-gated original free diagnostic calls the source-capture and inference/private-storage checks before Supabase import or public CSV fetch, but its workflow did not pass `GITHUB_TOKEN` to the live step. The privacy check therefore could not authenticate repository visibility. Current-form source capture also now requires the token, so the static contract test was updated for both paths.
- Fix: `GITHUB_TOKEN` is step-scoped only to the already private-storage-gated free-diagnostic live step; the workflow-level live flag remains literal `false`. No schedule or trigger changed.
- Exact PR workflow run [44863575065](https://github.com/MaksimBlud/football-ai/actions/runs/44863575065): SUCCESS, Python 3.11 and 3.12; **72 tests passed on each**, compile and `.pkl` diff guard passed.
- No live workflow was dispatched. Public repository visibility still causes the private-storage preflight to hold; no source, quote, or Supabase access was enabled.

### Related exact-head CI

- #898 HEAD `ea97737d02cdbf4952ab94bfb8e7436b7a4f5828`: 2/2 matrix jobs SUCCESS, 19 tests passed on each Python 3.11/3.12.
- #896 HEAD `cd2bc9cceeba7a5b69eb3172315e7b5810bc6b85`: 2/2 SUCCESS, 72 tests passed on each; strict `snapshot_time_utc` and `created_at` pre-kickoff filtering added to the research reader.
- #897 HEAD `ea3a9d5bc86294239ed693948044c5b065cbdecd`: 2/2 SUCCESS, 76 tests passed on each; pins the repository Serie A writer to omit caller-supplied `created_at`, leaving new-row timestamp generation to the database default. This does not make the database column immutable: service_role can still override it.
- #884 source-before-quote isolated validation: exact-head PR run SUCCESS.
- #781 root default-deny hold: 8/8 required workflows SUCCESS, OPEN / Ready for review, not merged. HUMAN-MERGE remains mandatory.

### Actual main workflow runs — 2026-11-20

All three runs below are on main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc` and completed SUCCESS:

- Original Forward [44777970547](https://github.com/MaksimBlud/football-ai/actions/runs/44777970547): 71 tests passed; source ZIP SHA verified; 10 historical CSVs / 3,800 historical matches; quotes_seen=0, future_quotes_checked=0, diagnostic previews=0, target outcomes not read, paid calls=0, Supabase writes=0.
- Current-Form Source Capture [44753230529](https://github.com/MaksimBlud/football-ai/actions/runs/44753230529): 19 tests passed; 110 completed fixture identities passed the input gate; 10 old-season files plus current-season file (11 total), 3,910 historical/current rows in the archive; 0 paid calls and 0 Supabase writes. The 110 input identities are not the evaluation gate.
- Current-Form Forward [44778623731](https://github.com/MaksimBlud/football-ai/actions/runs/44778623731): 53 tests passed; source artifact 14636526350 SHA-256 `2237cc30b84b2e982586ce7ef44b3ab4887c286e5f3320b8f9579cdc8e9dbca8` and parent run/head/completion verified; source age 9,169 seconds. quotes_seen=0, shadow forecasts=0, target_outcomes_read=false, target_outcomes_scored=false, paid calls=0, Supabase writes=0.

**Critical main-branch gap:** these live steps are still present on main because #781 has not been manually merged. Its default-deny change preserves schedules but gates source downloads, quote reads, and artifact publication. Do not enable live access by changing the flag; provider source rights remain unresolved and this repository is public.

### Supabase — read-only odds fields only

Fresh SELECT against `public.odds_snapshots` used only `league,event_id,snapshot_time_utc,commence_time_utc,created_at`:

- Total rows: 3,966.
- Strict pre-kickoff rows requiring both timestamps before kickoff: 3,915.
- Unique events in that strict subset: 327.
- Future strict pre-kickoff rows/events: 0/0.
- Serie A strict pre-kickoff rows: 620; latest snapshot `2026-10-13T14:48:53.042620Z`; latest row `created_at` `2026-10-13T14:48:53.157404Z`.

No scores, results, settlements, or protected evaluation outcomes were queried. `created_at` is mutable by service_role and is not cryptographic proof; retain the source archive SHA, authenticated parent workflow completion, and strict quote-time evidence.

### Binding next step

Owner manually reviews/merges #781 first. Then re-read fresh main and integrate the rights-gated ancestry in dependency order. Keep #899 stacked on #898. Do not merge any child independently, do not make Supabase writes/DDL, do not use paid APIs, and do not claim V2 superiority before the separate frozen 30-forecast evaluation gate and Brier/LogLoss comparison.

## 2026-11-21 05:00 UTC — current-form forward direct-access restack and live pre-match availability recheck

### Fresh main / continuity

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` remains 6,152 lines at blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b` and its latest original-V2 section is still the 2026-10-18 entry. This checkpoint is appended only to the open documentation PR #839 branch; no main write or merge occurred.
- PR #781 remains OPEN / not merged, exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, exact-head CI 8/8 SUCCESS. Its default-deny hold is not active on main until owner HUMAN-MERGE and fresh-main proof.

### New PR #900 — restack of current-form forward direct-access guard

- PR [#900](https://github.com/MaksimBlud/football-ai/pull/900) is Draft / OPEN, based on exact PR #899 HEAD `90cc6d93b283ea4411ab6331021c6db396c2525f`; current exact HEAD `d0f66f3495fc94a492a2ac8079c963730cbc2057`; compare is 5 ahead / 0 behind with exact base merge point.
- It restacks the existing direct-access delta from #893 onto the current #899 → #898 → #891 rights chain. Four files changed: `serie_a_v2_current_form_forward_capture.py`, its existing tests, a new direct-access poison-input test, and a new offline validation workflow.
- Direct source entrypoints now require source-capture rights before GitHub metadata/archive access; quote normalization and feature/preview construction require inference rights; CLI checks inference rights before Supabase client creation and saved-quote reads.
- Exact push run [#44868681400](https://github.com/MaksimBlud/football-ai/actions/runs/44868681400) SUCCESS: Python 3.11 **18 passed**, Python 3.12 **18 passed**, compile and production model-pickle diff guard passed.
- Exact PR run [#44868684776](https://github.com/MaksimBlud/football-ai/actions/runs/44868684776) SUCCESS: Python 3.11 **18 passed**, Python 3.12 **18 passed**, compile and production model-pickle diff guard passed.
- The first pre-fix run #44868524934 exposed a test-only synthetic-fixture issue: the test patched the direct-access module but not the already-imported inference-rights function inside `serie_a_v2_frozen_shadow_preview`. The fixture now patches both references. Production rights checks were not weakened.
- PR #893 remains open as the earlier parent-#890 implementation; a comment points reviewers to #900. Do not merge #893 independently; review the restack after its parent chain.

### Current exact rights-chain state

- #898 HEAD `ea97737d02cdbf4952ab94bfb8e7436b7a4f5828`: exact PR CI 2/2 SUCCESS, 19 tests per Python 3.11/3.12.
- #899 HEAD `90cc6d93b283ea4411ab6331021c6db396c2525f`: exact PR CI 2/2 SUCCESS, 72 tests per Python 3.11/3.12.
- #900 HEAD `d0f66f3495fc94a492a2ac8079c963730cbc2057`: exact PR CI 2/2 SUCCESS, 18 tests per Python 3.11/3.12.
- All three remain Draft/HUMAN-MERGE; their parent chain is not integrated into main.

### Actual main V2 runtime — 2026-11-20

- Original Forward [run #44777970547](https://github.com/MaksimBlud/football-ai/actions/runs/44777970547), main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`: SUCCESS, **71 tests passed**; source attestation verified SHA for 10 old-season CSVs / 3,800 historical rows; `quotes_seen=0`, `future_quotes_checked=0`, previews=0, paid calls=0, Supabase writes=0. No source/quote pair or V2 forecast was created.
- Current-Form Source Capture [run #44753230529](https://github.com/MaksimBlud/football-ai/actions/runs/44753230529), same main SHA: SUCCESS, **19 tests passed**; 110 completed Serie A 2026/27 fixture identities passed the metadata-only feature-input gate; 10 old-season CSVs plus one current-season CSV (11 files; 3,910 total rows) were archived. Artifact #14636526350 SHA-256 `2237cc30b84b2e982586ce7ef44b3ab4887c286e5f3320b8f9579cdc8e9dbca8`; paid calls=0; Supabase writes=0. The 110 completed matches were read only as lagged feature-source rows after the 30-primary-event input gate; they are not prospective target outcomes.
- Current-Form Forward [run #44778623731](https://github.com/MaksimBlud/football-ai/actions/runs/44778623731), same main SHA: SUCCESS, **53 tests passed**; it verified the source artifact digest, parent workflow ID/HEAD and parent completion time. `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target evaluation outcomes read/scored=false, paid calls=0, Supabase writes=0. With no saved quotes there is no end-to-end source-before-quote event pair yet.
- Free Real-Quote Diagnostic [run #44762405350](https://github.com/MaksimBlud/football-ai/actions/runs/44762405350), same main SHA: SUCCESS, **53 tests passed**; 3,800 historical rows, 10 public HTTP source requests, `quoted_fixtures=0`, `diagnostic_scored=0`, `eligible_for_frozen_prospective_cohort=false`, paid provider requests=0, Supabase writes=0. Its output artifact #14642541146 SHA-256 `6c8c60378b656e43f918f7630c089278e4ebec43488d2b75a9616d2cb7b66c09` is public while the repository remains public.
- Important: the feature-input gate count 110 is not the separate prospective evaluation gate. The latter remains CLOSED at **0/30 eligible prospective forecasts**. No target-cohort 2026/27 outcomes were read or scored.

### Supabase — read-only pre-match odds only

- A fresh SELECT on `public.odds_snapshots` restricted to `snapshot_time_utc < commence_time_utc AND created_at < commence_time_utc` returned **620 strict pre-match Serie A rows** across **63 events**. First snapshot `2026-08-29T09:00:20.381498Z`; latest snapshot `2026-10-13T14:48:53.042620Z`.
- A separate aggregate over all leagues with the same strict pre-match timestamp filter and `commence_time_utc > now()` returned **0 future strict pre-match quote rows/events**.
- No scores, results, settlements, prediction outcomes or protected evaluation targets were selected. `created_at` is mutable by service_role and is not cryptographic evidence; retain the source ZIP SHA, authenticated parent workflow completion and strict quote-time checks.

### Binding blockers and model state

- Football-Data provider rights remain unresolved under the checked-in HOLD manifest; the public repository also fails the private-storage preflight. #781 is the required interim default-deny hold, but remains unmerged. Do not manually dispatch live workflows or loosen the flag.
- Candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; 3,799 training rows; 19 frozen features; 20×2 weights; frozen scaler/imputer; `active_lambda=0`; `shadow_lambda=1`; stability FAILED; evaluation 0/30.
- No Brier/LogLoss comparison or V2-over-market claim is supported. No model/production artifact, weights, features, schedule, other agent, Supabase schema/data or main ref changed.


## 2026-11-21 — Original V2 replay/train-rights hold restacked; forward CLI exact-head proof refreshed

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository visibility is **public**. Root live-workflow hold [#781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready / HUMAN-MERGE, exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, **8/8 exact-head checks SUCCESS**. The public-repository private-storage gate in #879 and descendants therefore remains closed even after a future #781 integration until owner-controlled privacy/storage clearance exists.
- Re-read main `.github/workflows/serie-a-v2-forward-preview.yml` and `serie_a_v2_forward_capture.py`: main still reads saved quote rows / imports the Supabase client before source archive discovery and SHA verification. [#884](https://github.com/MaksimBlud/football-ai/pull/884) now has exact current HEAD `c38834ec6c2bd0079afca9e63a9ce75a8cd17043`; exact PR run [#44854473405](https://github.com/MaksimBlud/football-ai/actions/runs/44854473405) is **2/2 SUCCESS**, Python 3.11 and 3.12 each **80 passed**, compile and production-`.pkl` guard PASS. The code's intended order is archive discovery → parent-run verification → ZIP/SHA validation → lazy Supabase client / quote read. This fix is not on main.
- Restacked the existing saved-cohort replay / training-rights hard hold [#892](https://github.com/MaksimBlud/football-ai/pull/892) onto the current #900 rights chain as [#901](https://github.com/MaksimBlud/football-ai/pull/901), avoiding the older #890-only ancestry. Exact base #900 HEAD `d0f66f3495fc94a492a2ac8079c963730cbc2057`; new HEAD `eab0ef1429c604b30e69874a0557c36d0ecabaac`. Exact push run [#44873661323](https://github.com/MaksimBlud/football-ai/actions/runs/44873661323) and PR run [#44873685824](https://github.com/MaksimBlud/football-ai/actions/runs/44873685824) both SUCCESS: **4/4 exact-head check-runs**, Python 3.11/3.12 each **18 passed**, compile and production-`.pkl` guard PASS. The post-outcome replay entrypoints now fail closed before target materialization; training-source access requires provider-issued bounded evidence plus private source-capture rights; tests are outcome-blind AST / synthetic-only. #901 remains Draft / HUMAN-MERGE and must follow #900 and the full #781-rooted chain.
- Read-only Supabase query selected only strict pre-kickoff odds metadata: `snapshot_time_utc < commence_time_utc` and `created_at < commence_time_utc`. It returned **3,915** rows across **327** events; Serie A **620** rows / **63** events; latest strict Serie A snapshot `2026-10-13T14:48:53.042620Z`. No scores, results, settlement fields, or target outcomes were selected. No newer pre-match quote is available for V2; no source-before-quote prediction pair can currently be created.
- Frozen model remains candidate `a9d5abc2...`, 19 features, original 20×2 weights, `active_lambda=0`, `shadow_lambda=1`; no Brier/LogLoss superiority claim. Evaluation remains 0/30 eligible prospective forecasts.
- No main update or merge, no Supabase write/DDL, no paid API, no inference or target-outcome read, no production `.pkl` change, no schedule or other-agent change. HUMAN-MERGE only.


## 2026-11-21 18:06 UTC — source-capture rights hold, exact workflow regression, and fresh quote availability

### Fresh main and live workflows

- Fresh main is still `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main write or merge occurred. Main `PROJECT_CONTINUITY.md` remains at blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`; this update is appended only to this open documentation PR branch.
- Main `.github/workflows/serie-a-v2-current-form-source-capture.yml` is still not default-deny: workflow blob `9722416862b42d55ff7181003353c39620f23cf2`, schedule `50 5 * * *`, no `MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=false`, unconditional `if: always()` artifact upload, and floating action tags `checkout@v4`, `setup-python@v5`, `upload-artifact@v4`. The schedule was not changed.
- After the provider-policy review at `2026-11-21T11:52:37Z` recorded in #906, main run [#44910356674](https://github.com/MaksimBlud/football-ai/actions/runs/44910356674) still completed source capture at 13:45:04Z. It read only fixture identity/date metadata for the 30-event input gate, then downloaded 10 historical CSVs plus the 2026/27 current-season CSV (110 completed prior-day rows) and publicly uploaded artifact `14709831168`, 439,428 bytes, ZIP SHA-256 `3e38a5274aa79c00114c4f763cb32defc5f1840cba5c27a5c1e5083a1e767207`. Paid calls=0 and Supabase writes=0, but automated capture is DENIED by the refreshed source-rights manifest; the repository remains public.
- Main Current-Form Forward [#44923045119](https://github.com/MaksimBlud/football-ai/actions/runs/44923045119) verified artifact `14709831168` and its parent run/HEAD/completion. It then reported `quotes_seen=0`, `v2_current_form_shadow_captured=0`, and `target_outcomes_read/scored=false`. Its public diagnostic artifact `14714631201` has ZIP SHA-256 `3ec306f8fe4e47a0e6b4f5f0df7be50ba84392fd4298bae37d260ac182c238c0`.
- Main Free Real-Quote Diagnostic [#44914641563](https://github.com/MaksimBlud/football-ai/actions/runs/44914641563) made 10 public HTTP source requests, but `quoted_fixtures=0` and `diagnostic_scored=0`; public artifact `14710324968` SHA-256 `215a9d282afa850bd1e1a54482487a1a17c74098de58e4df4bd5eeb221035443`.
- Main Original Forward [#44922609676](https://github.com/MaksimBlud/football-ai/actions/runs/44922609676) passed 71 tests, verified 10 historical source files / 3,800 rows, and reported `quotes_seen=0`, `future_quotes_checked=0`, and `v2_diagnostic_previews_captured=0`. Its 1,458-byte artifact is a source-checked report, not a forecast. Main source code still calls the saved-quote reader before source archive discovery; the source-before-quote correction is not on main.

### Exact PR progress

- PR [#898](https://github.com/MaksimBlud/football-ai/pull/898) now has exact HEAD `6ea8b3a88e7bc7a95a1ddb2c1f4419656bb615f3`. Added one independent workflow-contract regression: default-deny live access, private-storage gate, gated Supabase secret scope, gated artifact upload, and unchanged cron. Exact run [#44933105902](https://github.com/MaksimBlud/football-ai/actions/runs/44933105902) is SUCCESS: Python 3.11 **20 passed**, Python 3.12 **20 passed**, compile and production `.pkl` diff guard PASS. Draft / HUMAN-MERGE.
- Active Original Forward rights child PR [#887](https://github.com/MaksimBlud/football-ai/pull/887) exact HEAD `fb14e5385aa760e357f5167ffd9164375a476780`: run [#44927447936](https://github.com/MaksimBlud/football-ai/actions/runs/44927447936), Python 3.11/3.12 **29 passed each**, compile and production `.pkl` diff guard PASS. Parent #885 exact HEAD `a1d065f1c3a03895bbef5b72e5bf664cdd68f33f` has run #44855586194, **84 passed each**; source-first parent #884 exact HEAD `c38834ec6c2bd0079afca9e63a9ce75a8cd17043` has run #44854473405, **80 passed each**.
- PR #908 is a duplicate restack relative to #885: its `serie_a_v2_forward_capture.py` and test file have identical Git blob SHAs to #885 (`905a5f3d...` and `251c8e23...`). Only the validation workflow differs; compare is diverged 3 ahead / 2 behind with merge base #884. Do not merge #908 alongside #885/#887.
- PR #906 keeps Football-Data automated capture and inference fail-closed. Existing audit #868 already assessed open-matchday and rejected it as a complete independent V2 source because its Serie A stats inherit mixed upstream terms and coverage gaps; #907 also keeps Global Football Data Lake on HOLD. No new source was authorized.

### Supabase and frozen model

- Read-only aggregate against `public.odds_snapshots` at `2026-11-21T17:55:54Z` selected only timestamp/event/kickoff metadata. Strict pre-match historical rows: **3,915**; latest strict pre-match snapshot: `2026-10-13T14:48:53.042620Z`; future rows/events satisfying `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= created_at < commence_time_utc`: **0 / 0**. No score, result, settlement, or target-outcome columns were read.
- Supabase Security Advisor reports RLS disabled on five public tables: `teams`, `predictions`, `match_statistics`, `league_prediction_ledger`, `epl_ai_market_pair_ledger`. Four other tables (`competitions`, `match_stats`, `matches`, `standings`) have RLS enabled but no policies. No DDL or writes were made; remediation requires owner-designed policies before enabling RLS on the five exposed tables.
- Original candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`, 3,799 training rows, 19 frozen features, 20×2 weights, `active_lambda=0`, `shadow_lambda=1`, stability gate FAILED. Prospective outcome evaluation remains 0/30; no Brier/LogLoss superiority claim is supported.
- No paid API calls, no Supabase writes/DDL, no target-outcome reads, no model refit/promotion, no production `.pkl` change, no weight/feature/threshold change, no schedule or other-agent change, and no merge/main update.


## 2026-11-21 19:02 UTC — Original V2 rights chain consolidated and exact-head CI recovered

### Fresh main and live entrypoints
- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository visibility is PUBLIC. No main update or merge occurred.
- Main `.github/workflows/serie-a-v2-forward-preview.yml` blob `48ce3b0d8e31c4cf293b94500e9c320047311467` still wires the original forward workflow to stored-odds reads and an unconditional `if: always()` artifact upload. Main `serie_a_v2_forward_capture.py` blob `5db02cbd1367ed25b994b152acf371421859a014` still imports the saved-quote reader before archive discovery/source verification. Source-before-quote is not on main.
- Main `.github/workflows/serie-a-v2-current-form-source-capture.yml` blob `9722416862b42d55ff7181003353c39620f23cf2` still has schedule `50 5 * * *`, no default-deny live-access env, unconditional secrets in job env, and `if: always()` artifact upload. Schedule was not changed. Do not manually dispatch or enable these main workflows.
- The 2026-11-21 main capture run `44910356674` occurred after the updated Football-Data policy review and published public artifact `14709831168` (ZIP SHA-256 `3e38a5274aa79c00114c4f763cb32defc5f1840cba5c27a5c1e5083a1e767207`). The refreshed manifest denies automated AI source capture; this was a policy violation by the still-unprotected main workflow, not permission. The subsequent forward run `44923045119` saw zero quotes and zero shadow forecasts; no target outcomes were read/scored. Preserve the artifact only as audit evidence; do not reuse it for further live inference.
- Original Forward main run `44922609676`: 71 tests passed, 10 historical CSVs / 3,800 rows source-attested, zero quotes, zero previews. No source-before-quote prediction pair exists.

### Root chain and consolidated PR #911
- Root #781 remains OPEN / Ready / HUMAN-MERGE, exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, all 8/8 exact-head workflows SUCCESS. It has not changed main.
- Current dependency heads and exact CI: #879 `b78010585c80b05ae5fc2a8b3572df14b32d9651` (20 tests per Python 3.11/3.12); #884 `c38834ec6c2bd0079afca9e63a9ce75a8cd17043` (80 each); #885 `a1d065f1c3a03895bbef5b72e5bf664cdd68f33f` (84 each); #887 `fb14e5385aa760e357f5167ffd9164375a476780` (29 each). All corresponding exact-head runs completed SUCCESS, compile and production `.pkl` guards passed.
- The policy-refresh #906, diagnostic direct-access #891, and current-form source-capture #898 branches had diverged after parent updates. Clean restacks #909 and #910 were created and validated, then superseded by a single consolidated restack to avoid merging siblings independently.
- New [PR #911](https://github.com/MaksimBlud/football-ai/pull/911) is OPEN / Draft / HUMAN-MERGE, based on exact current #887 HEAD `fb14e5385aa760e357f5167ffd9164375a476780`, exact HEAD `d888cbe434ec27b400426b4bddb7419d6d19af4a`; compare 2 ahead / 0 behind, 18 files changed. It consolidates final #888/#889/#890/#906 source-rights files, #891 direct-access tests/guards, and #898 source-capture guard/workflow.
- Exact-head PR CI on `d888cbe...`: inference-rights gate run `44938607967` — 48 passed on Python 3.11 and 48 on 3.12; diagnostic direct-access run `44938608016` — 39 + 39 passed; current-form source-capture rights run `44938608033` — 20 + 20 passed. All six matrix jobs SUCCESS, compile PASS, production `.pkl` diff guard PASS. Exact-head push run `44938601731` also SUCCESS, 48 + 48 passed. The first attempt on prior HEAD `e9533fbb...` exposed two tests whose import-bound inference guard was not patched by the synthetic fixture; a test-only patch now stubs the local import bindings, while dedicated rights tests still verify the real HOLD manifest denies access. No production rights check was weakened.
- Older #906, #891, #898, #909 and #910 were commented as superseded for integration by #911. #908 is a duplicate of #885's private-CLI delta and must not be merged alongside #885/#887.
- #911 remains a child of #887. Manual integration order remains #781 → #879 → #884 → #885 → #887 → #911. No automatic merge.

### Provider rights, Supabase and frozen candidate
- The exact policy manifest carried by #911 is still HOLD: `research_source_capture_permitted=false`, `research_inference_permitted=false`, `provider_issued_ai_inference_license=false`, `authorization=null`. The GitHub repository is public, so the private-artifact preflight also fails. No source download, quote read or model inference was performed by the new PR CI.
- Read-only aggregate against `public.odds_snapshots` used only `league,event_id,snapshot_time_utc,commence_time_utc,created_at`, with strict persistence ordering `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= created_at < commence_time_utc`. Serie A: **620 rows / 63 events**, latest strict snapshot `2026-10-13T14:48:53.042620Z`; future strict pre-match rows/events **0 / 0**. The looser pre-kickoff-only filter returned 625 rows; five rows failed the persistence-after-snapshot condition and are excluded. No score/result/settlement/target-outcome fields were selected. `created_at` remains mutable by service_role and is not cryptographic proof.
- Original candidate JSON on main blob `ac1303f6b096664983fbf52443bd0a381b23ba21`; frozen candidate SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; 3,799 training rows; 19 features; 20×2 weights; original scaler/imputer; `active_lambda=0`; `shadow_lambda=1`; stability gate FAILED; prospective outcome evaluation **0/30**. No Brier/LogLoss comparison or V2-over-market claim is supported.
- No main update, merge, Supabase writes/DDL, paid API calls, protected outcome reads, production `.pkl` change, weight/feature/threshold change, schedule change, or other-agent change. HUMAN-MERGE remains mandatory.


## 2026-11-21 19:06 UTC — Current-form forward and outcome/training holds restacked

### Exact-head restacks after consolidated #911
- [PR #912](https://github.com/MaksimBlud/football-ai/pull/912) restacks #899 free-diagnostic token binding on #911. Base SHA `d888cbe434ec27b400426b4bddb7419d6d19af4a`; exact HEAD `de358ceefcac084aa92add7b6f93a0f7153df030`; compare 1 ahead / 0 behind; 3 files. Exact-head PR run `44938841482` and push run `44938835762` SUCCESS, 72 tests on Python 3.11 and 72 on 3.12. No production `.pkl` file is in the diff.
- [PR #913](https://github.com/MaksimBlud/football-ai/pull/913) restacks #903 (including #900 direct-access changes) on #912. Base SHA `de358ceefcac084aa92add7b6f93a0f7153df030`; exact HEAD `23ba2b6b9651f07f819004ab9c2fbd9fc37c641b`; compare 1 ahead / 0 behind; 4 files. Exact-head PR run `44938903345` and push run `44938897826` SUCCESS, 31 tests on Python 3.11 and 31 on 3.12; compile and production `.pkl` diff guard PASS. It verifies source artifact ID/SHA, authenticated parent run and source/parent/verification chronology/freshness before any saved-quote reader, Supabase secret lookup or client creation. Invalid/missing/stale source returns metadata-only skip with zero quote reads.
- [PR #914](https://github.com/MaksimBlud/football-ai/pull/914) restacks #901's outcome-blind saved-cohort replay and training-rights hold on #913. Base SHA `23ba2b6b9651f07f819004ab9c2fbd9fc37c641b`; exact HEAD `b3c84eb308a0991f6fa3eabaafdda13720f7c18d`; compare 1 ahead / 0 behind; 5 files. Exact-head PR run `44939040481` and push run `44939034654` SUCCESS, 18 tests on Python 3.11 and 18 on 3.12; compile and production `.pkl` diff guard PASS.
- #914 merges the stricter provider-training validator into the current #911 source-rights helper (rather than reverting to the stale #901 file): provider-issued grant, provider-domain evidence URL, local evidence SHA-256, both explicit validity bounds, and policy-page-update-before-review chronology are required. The current manifest has no authorization and denies AI training.
- #914 moves the old saved-cohort outcome literals behind a lazy function and an unconditional `PermissionError` replay gate. Its tests are AST/static and replace the target-literal function body before parsing; they do not import, materialize or score saved target outcomes. Training entrypoints require both provider training rights and separately cleared source-capture rights before network access.
- #899, #900, #901 and #903 are commented as superseded by #912/#913/#914 respectively. These are all Draft/HUMAN-MERGE and remain chained: #911 → #912 → #913 → #914, after the #781 → #879 → #884 → #885 → #887 root chain. No automatic merge.
- #911 exact HEAD remains `d888cbe434ec27b400426b4bddb7419d6d19af4a`, 18 files, 2 ahead / 0 behind #887; three exact-head PR workflows pass 48/48, 39/39 and 20/20 per Python version respectively, plus final-head push run `44938601731` (48/48 each). Its first prior HEAD `e9533fbb...` failed only two synthetic forward tests because import-bound guards were not patched; the test-only fixture patch fixed those without weakening the real rights gate.
- Documentation PR #839 has latest HEAD `964eee1a77e2aa7fabbc40311339c4aba966cbe9`, 121 ahead / 0 behind main, 10 files. All 8/8 exact-head workflow runs completed SUCCESS after the previous continuity append; this current append will require a fresh documentation CI run.

### Current model/data status unchanged
- Football-Data policy still has `research_source_capture_permitted=false`, `research_inference_permitted=false`, `provider_issued_ai_inference_license=false`, `authorization=null`. Public repository/private-artifact preflight fails. No live capture or inference was attempted.
- Strict persisted pre-match Supabase aggregate remains 620 Serie A rows / 63 events, latest snapshot `2026-10-13T14:48:53.042620Z`; future strict pre-match rows/events 0 / 0. Filter includes `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= created_at < commence_time_utc`. No outcomes read.
- Original candidate SHA, 19-feature contract, 20×2 weights, scaler/imputer, training fingerprint, `active_lambda=0`, `shadow_lambda=1`, stability gate FAILED, evaluation 0/30; no Brier/LogLoss comparison or superiority claim.
- No main update, merge, Supabase writes/DDL, paid API, target-outcome read, production `.pkl` change, model/threshold change, schedule change or other-agent change.


## 2026-11-21 19:53 UTC — exact main/runtime, source-order and V2 rights checkpoint

### Fresh main and live workflow evidence

- Default branch remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; the main `PROJECT_CONTINUITY.md` blob remains `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`. No main update or merge occurred.
- Re-read the main `serie_a_v2_forward_capture.py`: `main()` still imports/initializes Supabase and calls `fetch_saved_upcoming_serie_a_quotes` before `discover_archives()`. This is a real source-before-quote ordering defect on main. PR #884 changes this to discover/authenticate the latest source parent, download and SHA-verify the archive, then lazily import `database.supabase` only inside the quote callback. #884 is still open; therefore its fix is not live on main.
- Main Current-Form Source Capture [run 44910356674](https://github.com/MaksimBlud/football-ai/actions/runs/44910356674): SUCCESS, 19 tests passed; output reports 10 old-season CSVs + current-season CSV, 3,910 rows, 110 completed fixture identities, artifact `14709831168`, ZIP SHA-256 `3e38a5274aa79c00114c4f763cb32defc5f1840cba5c27a5c1e5083a1e767207`. This is technical evidence only. The current Football-Data policy denies this automated AI/source-capture use, and the repo is public; do not treat this archive or its downstream use as authorized.
- Main Current-Form Forward [run 44923045119](https://github.com/MaksimBlud/football-ai/actions/runs/44923045119): SUCCESS, 53 tests passed; verified source artifact ID/SHA, exact parent run/head/path and source freshness (8,727 seconds). It reports `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`; output artifact `14714631201`, ZIP SHA-256 `3ec306f8fe4e47a0e6b4f5f0df7be50ba84392fd4298bae37d260ac182c238c0`. It did not create a forecast. The source archive itself remains disallowed under the current provider policy.
- Main Original Forward [run 44922609676](https://github.com/MaksimBlud/football-ai/actions/runs/44922609676): SUCCESS, 71 tests passed; independent source attestation reports 3,800 historical fixtures and 10 pre-prospective CSVs, source artifact `14710324968`, source ZIP SHA-256 `215a9d282afa850bd1e1a54482487a1a17c74098de58e4df4bd5eeb221035443`. The subsequent forward step reports `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`; output artifact `14714123247`, SHA-256 `5d382e02818491619b3699559c266419394b89c6987748a09040d285af429358`. Because main still reads quotes before its own archive discovery, this run is not proof that the original CLI source-before-quote ordering is fixed.
- Main Free Real-Quote Diagnostic [run 44914641563](https://github.com/MaksimBlud/football-ai/actions/runs/44914641563): SUCCESS, 53 tests passed, `diagnostic_scored=0`, artifact `14710324968`, SHA-256 `215a9d282afa850bd1e1a54482487a1a17c74098de58e4df4bd5eeb221035443`. It is not a new prediction or provider-rights clearance.

### Supabase — read-only, pre-match columns only

At 2026-11-21 19:53:46 UTC, the aggregate read used only `league`, `event_id`, `snapshot_time_utc`, `created_at`, and `commence_time_utc` from `public.odds_snapshots`. Strict rows required `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= created_at < commence_time_utc`.

| League | Strict pre-match rows | Events | Future strict rows/events | Latest strict snapshot UTC |
|---|---:|---:|---:|---|
| Serie A | 620 | 63 | 0 / 0 | 2026-10-13 14:48:53 |
| EPL | 1,135 | 70 | 0 / 0 | 2026-10-09 15:25:57 |
| Bundesliga | 394 | 35 | 0 / 0 | 2026-09-11 15:49:52 |
| Eredivisie | 410 | 39 | 0 / 0 | 2026-09-11 15:50:20 |
| La Liga | 798 | 52 | 0 / 0 | 2026-09-11 15:45:28 |
| Ligue 1 | 387 | 35 | 0 / 0 | 2026-09-11 15:49:24 |
| RPL | 153 | 15 | 0 / 0 | 2026-09-05 15:07:55 |
| Primeira Liga | 9 | 9 | 0 / 0 | 2026-09-11 16:06:24 |
| Turkey Super Lig | 9 | 9 | 0 / 0 | 2026-09-11 16:06:26 |

No future event has a strict eligible saved quote in any listed league. No score, result, settlement or target-outcome column was queried. `created_at` remains mutable by service_role and is not cryptographic proof; source archive SHA and authenticated parent-run chronology are still required.

### Exact-head PR chain re-read

- #781 root live-access hold: HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, base main, 8/8 exact-head checks SUCCESS; OPEN / Ready for review. It sets the live-access flag false, removes live secrets from job-level environments, gates live source/quote steps and artifact upload, and preserves the four existing schedules. This is the first manual merge needed to stop the currently unauthorized main collectors.
- #879 private artifact prerequisite: HEAD `b78010585c80b05ae5fc2a8b3572df14b32d9651`, base #781, 4/4 SUCCESS, Draft.
- #884 original-forward source-first preflight: HEAD `c38834ec6c2bd0079afca9e63a9ce75a8cd17043`, base #879, 4/4 SUCCESS, Draft; tests assert parent verification + ZIP SHA precede the quote callback.
- #885 private-repository CLI guard: HEAD `a1d065f1c3a03895bbef5b72e5bf664cdd68f33f`, base #884, 4/4 SUCCESS, Draft.
- #887 original-forward direct inference/private-storage gate: HEAD `fb14e5385aa760e357f5167ffd9164375a476780`, base #885, 4/4 SUCCESS, Draft.
- #911 consolidated provider-rights/direct-access restack: HEAD `d888cbe434ec27b400426b4bddb7419d6d19af4a`, base #887, 8/8 SUCCESS, Draft.
- #912 free-diagnostic token binding: HEAD `de358ceefcac084aa92add7b6f93a0f7153df030`, base #911, 4/4 SUCCESS, Draft.
- #913 current-form forward direct-access/source-before-quote gate: HEAD `23ba2b6b9651f07f819004ab9c2fbd9fc37c641b`, base #912, 4/4 SUCCESS, Draft.
- #914 outcome-blind replay/training-rights hold: HEAD `b3c84eb308a0991f6fa3eabaafdda13720f7c18d`, base #913, 4/4 SUCCESS, Draft.
- Independent frozen-candidate integrity PR #902: HEAD `0ecc8097bc9f34849a5d1f1ecf05966f1a6f619d`, base main, 7/7 SUCCESS, Draft. It does not alter the candidate artifact.
- Documentation PR #839 prior HEAD `8086cd5903064ec554c9486fa818f19d86672a39` had 8/8 SUCCESS before this additive checkpoint. This commit changes only this continuity file; rerun all applicable checks on the new exact HEAD.
- Older #908 is a duplicate private-CLI restack based directly on #884, not a child of #887; do not merge it alongside #885/#887. Older #891/#898/#903/#899 descendants are superseded by the #911→#914 consolidated chain unless a later audit proves otherwise.

### Binding V2 status and non-actions

Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; 3,799 training rows; exact 19-feature order; 20×2 weights; 19-element scaler/imputer vectors. `active_lambda=0` remains exact market fallback; `shadow_residual_lambda=1` remains research-only. Stability gate FAILED; prospective outcome-read gate CLOSED at 0/30. No Brier/LogLoss comparison is admissible.

No main update or merge, no provider API/account/key request, no paid API, no new quote read in this audit, no Supabase write/DDL, no target-outcome read, no feature inference, no refit, no threshold tuning, no promotion, no betting, no production `.pkl` change, no schedule change and no other-agent setting change. All open PRs remain HUMAN-MERGE.


## 2026-11-21 20:01 UTC — remove embedded protected targets from the replay source

- Re-auditing the open #914 outcome/training hold exposed that its saved-cohort loader still carried protected target literals in source, even though the loader and replay path were blocked by an unconditional `PermissionError`. The source-level literals have now been removed; the loader only invokes the unconditional gate and contains an unreachable fail-closed raise. Do not restore target records to the research source.
- Added an AST regression that asserts the loader body contains only the gate call and fail-closed raise, with no literal target containers.
- #914 current exact HEAD: `c6fabb453013274b59a23d817f1d21e00c414572`; base remains #913 `23ba2b6b9651f07f819004ab9c2fbd9fc37c641b`; PR remains Draft / HUMAN-MERGE.
- Exact-head PR validation [#44944026413](https://github.com/MaksimBlud/football-ai/actions/runs/44944026413) and push validation [#44944021117](https://github.com/MaksimBlud/football-ai/actions/runs/44944021117) both SUCCESS. Python 3.11 and 3.12 each report 19 passed; compile and production `.pkl` diff guard PASS.
- No replay execution, Supabase target-outcome query, scoring, refit, or promotion occurred. No V2 feature/weight/lambda change, production artifact change, main update, merge, schedule change, or other-agent setting change.


## 2026-11-21 22:05 UTC — quote persistence guard restacked on current rights chain

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main update or merge.
- Added Draft PR [#915](https://github.com/MaksimBlud/football-ai/pull/915) as a child of #914, exact base `c6fabb453013274b59a23d817f1d21e00c414572`, current exact HEAD `38831b5118126612dcdb7527902c43c3fa0d4661`, 10 ahead / 0 behind.
- #915 restores the strict `created_at >= snapshot_time_utc` guard missing from the current #914 frozen quote reader, selects `created_at`, validates it against capture time and kickoff, and records `quote_row_created_at_utc` in the diagnostic. It also adds synthetic missing/future/pre-observation/kickoff boundary tests and pins the trusted collector's omission of caller-supplied `created_at`.
- Exact-head PR Actions [#44954750424](https://github.com/MaksimBlud/football-ai/actions/runs/44954750424): 2/2 SUCCESS; Python 3.11 and 3.12 each report 87 passed; compile and production `.pkl` diff guard passed. #915 remains Draft / HUMAN-MERGE.
- The audit explicitly states `created_at` is mutable by `service_role`; this is a fail-closed chronology check, not immutable or cryptographic database attestation. No Supabase write/DDL, source/quote request, target-outcome read, inference/refit, threshold change, promotion, production artifact change, schedule change, or merge occurred.
- The live pre-match aggregate remains 3,915 strict rows / 327 events across stored leagues, with zero future strict rows/events; Serie A remains 620 rows / 63 events, latest strict snapshot `2026-10-13T14:48:53.042620Z`. No scores, results, settlement fields or target outcomes were queried.


## 2026-11-21 22:55 UTC — Lega Serie A report-derived dataset rights/provenance audit

A new free-looking 2026/27 candidate was reviewed: [matteovezzoli/serie-a-observatory](https://github.com/matteovezzoli/serie-a-observatory), which derives match/team/player CSVs from official Lega Serie A Match Report PDFs and says its dataset is refreshed weekly. The README says `reports.csv` records report publication and last-update dates, and reports can be corrected 0–12 days after a match.

**Decision: HOLD / NO INTEGRATION.** The official [Lega Serie A terms](https://www.legaseriea.it/terms-and-conditions), updated 2025-12-01, limit platform use to personal/non-commercial purposes and prohibit extraction or use of platform content without express written consent, explicitly including data mining, robots and similar acquisition/extraction tools. The repository's MIT LICENSE grants rights to the Software and associated documentation; it is not a separate upstream data license and cannot clear the underlying Lega database/content. Its own weekly PDF-extraction pipeline is not permission for this project to repeat that extraction.

The README describes publication/last-update dates, but no exact per-stat first-observed timestamp or immutable version history was established. Corrections up to 12 days after a match mean historical rows can change. Exact parity with the frozen original 19-feature order, rolling windows and venue windows is also unverified. Do not download, scrape, fork or use this dataset for V2 until written permission explicitly covers automated extraction, internal ML use, private raw retention and the required source-before-quote provenance.

Added:
- `research/MARKET_ANCHOR_1X2_V2_LEGA_REPORT_DERIVED_SOURCE_AUDIT_20261121.md`
- `research/market_anchor_1x2_v2_lega_report_derived_source_audit_20261121.json`
- A frozen-shadow regression asserting the source remains HOLD, upstream written consent is absent, no source/API access is enabled, and the original candidate SHA / 19-feature / lambda invariants remain unchanged.

This is an official-terms and public-repository documentation audit only. No repository data files or PDFs were downloaded; no provider account/key/API request, source capture, quote read, protected-outcome read, V2 inference, Supabase access for this provider audit, Supabase write/DDL, model/weight change, production `.pkl` change, schedule change, or merge occurred. The separate pre-match-only Supabase aggregate for existing saved odds remains read-only and is recorded above in the #915 checkpoint.

## 2026-11-22 00:55 UTC — source-clock guard, exact-head CI, and fresh pre-match-only audit

### Fresh repository state
- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` blob remains `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`.
- Repository visibility remains **public**. The root default-deny/private-storage hold [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / unmerged at HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, with its previously verified 8/8 exact-head CI. No merge or main change occurred.
- The open V2 chain is still HUMAN-MERGE only. Do not treat a green child PR as permission to run a source/quote workflow.

### New source-clock defect and PR #917
The current-form source capture used `clock().astimezone(timezone.utc)` for both the source observation and archive-creation timestamps. Python accepts a naive datetime and silently assumes the runner's local timezone. That could create a plausible UTC-looking timestamp without an explicit timezone offset, weakening source-before-quote evidence.

New child [PR #917](https://github.com/MaksimBlud/football-ai/pull/917):
- Parent #916 exact HEAD: `b174b4a7d036d0405dc9e6d6105080133bcbb70c`.
- New exact HEAD: `e78d6b63c482f2ff7b20be29b69892430e03a4b4`.
- Compare: **3 ahead / 0 behind**, merge base is exact parent #916.
- Exact workflow [#44968807080](https://github.com/MaksimBlud/football-ai/actions/runs/44968807080): **2/2 SUCCESS**.
- Python 3.11: **16 passed**; Python 3.12: **16 passed**. Both compile checks and the production `.pkl` diff guard passed.
- The helper rejects non-datetime, naive, or tzinfo-without-offset clock values, then normalizes explicit offsets to UTC. Regressions cover both timestamp boundaries and UTC normalization.
- Three changed files only: the V2 current-form source capture, its offline tests, and a dedicated pinned-action Python 3.11/3.12 validation workflow.

PR #916 remains the parent, exact HEAD `b174b4a7d036d0405dc9e6d6105080133bcbb70c`, **2/2 SUCCESS**, 24 tests passed on each Python version. PR #917 is Draft and must not be merged before #916 and its #781-rooted ancestors.

### Other independent candidate-integrity check
[PR #902](https://github.com/MaksimBlud/football-ai/pull/902) remains OPEN / Draft / mergeable, based directly on main:
- HEAD `0ecc8097bc9f34849a5d1f1ecf05966f1a6f619d`, compare **3 ahead / 0 behind**.
- **7/7 exact-head checks SUCCESS**; the original frozen-candidate integrity test reports **11 passed**, and the production `.pkl` diff guard passed.
- This pins the durable candidate JSON and its original feature/weight/training/lambda contract; it does not alter the candidate.

### Fresh real main-branch workflow evidence (read-only log inspection)
- Original Forward run [#44922609676](https://github.com/MaksimBlud/football-ai/actions/runs/44922609676), main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`, SUCCESS on 2026-11-21 16:05 UTC: **71 tests passed**; source attestation verified **10 pre-prospective CSVs / 3,800 historical rows** and source archive SHA verification; `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `paid_provider_calls=0`, `supabase_writes=0`. Its diagnostic artifact was uploaded publicly (artifact #14714123247, SHA-256 `5d382e02818491619b3699559c266419394b89c6987748a09040d285af429358`). No artifact was downloaded or reused in this audit.
- Current-Form Source Capture run [#44910356674](https://github.com/MaksimBlud/football-ai/actions/runs/44910356674), same public main, SUCCESS on 2026-11-21 13:44 UTC: **19 tests passed**, 110 completed event identities, 11 source CSVs, 3,910 rows; public artifact #14709831168, SHA-256 `3e38a5274aa79c00114c4f763cb32defc5f1840cba5c27a5c1e5083a1e767207`. The current Football-Data rights manifest remains HOLD for automated AI capture/inference; do not download, reuse, or treat this artifact as authorized. This audit read logs only.

### Fresh Supabase read-only audit — timestamps and identifiers only
Queries selected no score, result, settlement, or target-outcome fields. Across all stored leagues:
- **3,915** rows / **327** events satisfy `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= created_at < commence_time_utc`.
- **51** rows have snapshot time at/after kickoff; all 51 also have persistence at/after kickoff. They are excluded from the strict pre-match subset.
- **0** rows have `created_at < snapshot_time_utc`.
- **0** pre-kickoff snapshots have invalid persistence ordering.
- **0** future-kickoff events have a strict admissible saved quote.
- Latest strict Serie A snapshot remains `2026-10-13T14:48:53.042620Z`; no new future quote pair exists.

The `created_at` field is mutable by `service_role`; this is a database ordering check, not an immutable provenance certificate. Source SHA and authenticated parent-workflow chronology remain mandatory.

### Frozen model and evaluation state
Original candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 original features, 20×2 original weights, original scaler/imputer and training fingerprint. `active_lambda=0` remains exact market fallback; `shadow_lambda=1` remains research-only. Stability gate remains FAILED; independent prospective evaluation gate remains **0/30**. No Brier/LogLoss comparison or superiority claim is permitted.

### Non-actions
No source download/API request by this audit, no paid Odds API request, no Supabase write/DDL, no target-outcome read, no model inference/refit, no weight/feature/contract/threshold change, no production `.pkl` change, no merge/main update, no schedule change, and no other-agent setting change. All new PRs remain Draft / HUMAN-MERGE only.

## 2026-11-22 00:59 UTC — final exact-head source-clock guard

This supersedes the earlier #917 `e78d6b6...` and `b428358...` checkpoints above.

- [PR #917](https://github.com/MaksimBlud/football-ai/pull/917) current HEAD: `7b803505f9cab8c7e897a084283dbcca555e05a4`; parent #916 exact HEAD: `b174b4a7d036d0405dc9e6d6105080133bcbb70c`; compare **6 ahead / 0 behind**.
- Exact PR workflow [#44969234389](https://github.com/MaksimBlud/football-ai/actions/runs/44969234389): **2/2 SUCCESS**; Python 3.11 **17 passed**, Python 3.12 **17 passed**; both compile and production `.pkl` diff guards passed.
- In addition to explicit timezone validation for both provenance clocks, source archive creation time must now be greater than or equal to source observation time. A backwards wall clock fails before the manifest is written; equality is allowed, matching the downstream verifier's non-strict `archive_created_at >= source_observed_at` contract.
- Synthetic-only test; no source/quote request, Supabase access/write/DDL, protected outcome read, inference/refit, paid API call, model artifact/weight/feature change, or merge.
- PR remains Draft and is a child of #916; do not integrate before the #781-rooted chain.

## 2026-11-22 01:02 UTC — superseding final #917 exact-head result

This supersedes the earlier #917 `e78d6b6...`, `b428358...`, and `7b803505...` checkpoints.

- [PR #917](https://github.com/MaksimBlud/football-ai/pull/917) HEAD: `6c5a97a4f2b7d3aca0a2e16718a149267e8049fd`; exact parent #916 HEAD: `b174b4a7d036d0405dc9e6d6105080133bcbb70c`; compare **8 ahead / 0 behind**.
- Exact PR run [#44969449176](https://github.com/MaksimBlud/football-ai/actions/runs/44969449176): **2/2 SUCCESS**; Python 3.11 **41 passed**, Python 3.12 **41 passed**; compilation and production `.pkl` diff guards passed on both.
- The validation suite includes `tests/test_serie_a_v2_workflow_external_access_hold.py`; it confirms the new pinned-action clock-validation workflow is offline-only and does not escape the explicit live-workflow default-deny inventory.
- Final source chronology invariants: both source-observation and archive-creation clocks must carry explicit timezone offsets; explicit offsets normalize to UTC; archive creation cannot precede source observation; no manifest is written on invalid clocks.
- PR remains Draft, child of #916, and HUMAN-MERGE only. No live source/quote, Supabase, protected outcome, model, paid API, production artifact, or main action occurred.

## 2026-11-22 01:03 UTC — no historical market-quote cohort in Supabase

A separate read-only query grouped only `league`, `commence_time_utc`, and the strict pre-match timestamp predicates; no score, result, settlement, or target-outcome columns were selected.

- Strict pre-match events with kickoff before 2026-07-01: **0 in every league**.
- Strict pre-match events with kickoff on/after 2026-07-01 (2026/27 cohort): **327** total.
- Thus the current Supabase odds table contains no pre-2026/27 market-quote cohort for retrospective independent Brier/LogLoss benchmarking. The 327 current-season quote events cannot be opened as evaluation targets before the preregistered 30-primary-completed-prospective-forecast gate; the separate feature-input gate does not authorize that.
- No target outcomes were queried. No prospective eligible forecast cohort has been established; evaluation remains **0/30**.

This is a data-availability blocker, not evidence for or against V2. Do not substitute the 2026/27 training/feature-source rows for an independent market benchmark.


## 2026-11-22 02:04 UTC — feature-gate clock guard and fresh V2 runtime audit

### Repository / continuity state

- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc` (2026-10-18 commit); `PROJECT_CONTINUITY.md` on main remains the older 6,152-line checkpoint. The current documentation refresh is still open in [PR #839](https://github.com/MaksimBlud/football-ai/pull/839), branch HEAD `e6d308dcc0a77cf06dc447ca807c22f4e27ab4a0`, 139 ahead / 0 behind, exact eight-workflow CI successful.
- Root [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains open, non-draft, mergeable, and human-reviewable at exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261` (see live PR API for exact SHA). Its exact-head 8/8 CI passed. It includes the current-form source-capture workflow: default live-access flag false, secrets moved from job scope into the gated capture step, capture skipped unless explicitly enabled, and artifact upload restricted to successful explicitly enabled runs. Do not alter schedules; this is the required interim default-deny hold while provider rights and private storage remain unresolved.
- The current main repository is public. The refreshed Football-Data rights manifest still denies automated AI source capture and inference. Do not reuse any public artifact from the denied run described below.

### New PR #918 — feature-source clock integrity

- Child of [PR #917](https://github.com/MaksimBlud/football-ai/pull/917), exact base `6c5a97a4f2b7d3aca0a2e16718a149267e8049fd`.
- Exact HEAD `81de6253521ac095148480a140e4c6057e2d1987`, 4 ahead / 0 behind.
- [Push CI #44974278333](https://github.com/MaksimBlud/football-ai/actions/runs/44974278333): 2/2 SUCCESS; Python 3.11 and 3.12 each report 43 passed; compile and production `.pkl` diff guard passed.
- The feature-input metadata gate and direct current-season CSV validator previously rejected only `tzinfo is None`; a custom tzinfo object with `utcoffset() is None` could still be interpreted as runner-local time by `astimezone(UTC)`. Both boundaries now reject this invalid clock before database metadata access or CSV parsing. Two synthetic regressions cover the case.
- Only the source-capture helper, its tests and an isolated pinned-action validation workflow changed. Frozen candidate, protocol, 19-feature contract, weights, scaler/imputer, lambda settings and both gates are unchanged.

### Fresh read-only Supabase checks

- The Serie A 2026/27 feature-input metadata query selected only `match_date,home_team,away_team` from `public.league_finished_results` before 2026-11-22. It returned 113 raw rows / 113 raw identities; the frozen V2 alias `Atalanta BC -> Atalanta` yields 110 canonical unique primary-event identities (3 alias-collapsed rows). This exceeds the preregistered 30-primary-event feature-input threshold, but does not authorize source capture while provider rights remain HOLD and does not open the separate 30-prospective-forecast target-evaluation gate. No score/result/settlement fields were selected.
- A separate metadata-only aggregate of `public.odds_snapshots` returned 3,966 rows / 327 events; 3,915 rows / 327 events satisfy both `snapshot_time_utc < commence_time_utc` and `created_at < commence_time_utc`; 51 rows are non-pre-match/late; future strict pre-match rows/events = 0. No scores, results or settlement columns were selected.
- The 3,915-row chronology is a consistency check, not an immutable provenance certificate: Supabase `created_at` is mutable by privileged writers. No Supabase write or DDL occurred.

### Actual main workflow runs and rights incident

- [Current-Form Source Capture #44910356674](https://github.com/MaksimBlud/football-ai/actions/runs/44910356674), main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`, completed SUCCESS on 2026-11-21. Its log reports 19 tests passed, 110 completed metadata identities, 10 historical CSVs plus the current-season CSV (11 files / 3,910 rows), zero paid calls and zero Supabase writes. GitHub artifact metadata confirms public artifact `14709831168`, 439,428 bytes, created 2026-11-21 13:45:03 UTC, ZIP SHA-256 `3e38a5274aa79c00114c4f763cb32defc5f1840cba5c27a5c1e5083a1e767207`. This capture occurred after the refreshed provider policy review while the manifest still denied automated AI capture and the repository remained public. Treat it as audit evidence only: do not download, inspect, reuse, infer from, or attach it to any V2 evaluation. The unmerged #781 default-deny hold is the required prevention.
- [Original Forward #44922609676](https://github.com/MaksimBlud/football-ai/actions/runs/44922609676), same main SHA, completed SUCCESS on 2026-11-21: 71 tests passed; 10 historical CSVs / 3,800 rows were source-attested and SHA-verified; `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, paid calls=0, Supabase writes=0. Its successful source attestation is not a prospective forecast or model-quality result.
- Main remains uncorrected until the HUMAN-MERGE chain is integrated. Do not dispatch live workflows or enable the live-access flag.

### 5DollarFootballAPI official-page recheck — HOLD

- [Terms (updated October 2026)](https://5dollarfootballapi.com/terms) permit use in commercial products/models and caching, with visible attribution for public-facing Free/Community/Education products; raw-feed redistribution is prohibited.
- [Pricing](https://5dollarfootballapi.com/pricing) says Free covers the Top-5 leagues, but the first-party [measured data-quality table](https://5dollarfootballapi.com/docs/data-quality) lists **Italy Serie A as Pro**, with 380 finished matches in the last 12 months and 100% corners, HT corners, odds, events, live stats and cards. This conflicts with the Free Top-5 claim.
- [Fixture response documentation](https://5dollarfootballapi.com/docs/fixture) exposes kickoff and match statistics but no per-fixture source-observation timestamp for the stats. The status page reports collector freshness, not a timestamp for each statistic's first availability.
- No account, key, API call, download or integration was made. Require written confirmation of Free-plan Serie A entitlement, provider authority/upstream rights and a defensible source-observation protocol before approval. Existing #792/#800 adapter remains HOLD/offline-only.

### Frozen V2 status

- Original candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985...`; 19 features; 20x2 weights; `active_lambda=0`, `shadow_lambda=1`.
- Stability gate remains FAILED. Prospective target-evaluation gate remains 0/30. No Brier/LogLoss comparison against the market is available.
- No candidate/weight/feature/scaler/imputer change, no production `.pkl` change, no refit, no threshold tuning, no promotion, no betting, no target-outcome read, no paid API request, no Supabase write/DDL, no merge or main update.


## 2026-11-22 06:49 UTC — Original V2 atomic source archive and fresh pre-match quote audit

### Fresh main and continuity
- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main ref or file was changed in this run.
- Main `PROJECT_CONTINUITY.md` is still the 6,152-line checkpoint whose newest dated section is 2026-10-18. The documentation refresh remains [PR #839](https://github.com/MaksimBlud/football-ai/pull/839), open / non-draft / based on this unchanged main. This checkpoint is appended to the #839 branch only.
- Main `.github/workflows/serie-a-v2-forward-preview.yml` still has its scheduled and `workflow_run` triggers, and the main original forward CLI still has the previously documented quote-before-source ordering. Root [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review / mergeable at exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`; its eight exact-head checks remain SUCCESS. No merge was performed.

### Current source-first ancestry and new #923
- [PR #921](https://github.com/MaksimBlud/football-ai/pull/921) HEAD `5e298afa1d6091040bbb6478b8f9570a577fb080`, child of #920 at `064209e1acfc5ec05ed45f78fa1a567543a0463b). It pins the current-season source-observation clock to occur only after a successful HTTP response.
- [PR #922](https://github.com/MaksimBlud/football-ai/pull/922) HEAD `a62b91a3e8146930924b221934f8283a38c1f1f2`, child of #921. It disables HTTP redirects for historical and current-season CSV requests and requires HTTP 200 plus exact response-URL equality before body bytes, observation time, CSV, or manifest are accepted. Exact PR run [#44987253304](https://github.com/MaksimBlud/football-ai/actions/runs/44987253304): 2/2 jobs SUCCESS; Python 3.11 **65 passed**, Python 3.12 **65 passed**; compilation and production `.pkl` diff guards passed.
- New [PR #923](https://github.com/MaksimBlud/football-ai/pull/923) HEAD `924197669b9355012ef3a773fab70749cee1070f`, exact parent #922 HEAD above; compare **3 ahead / 0 behind** its parent. It stages the ten historical CSVs, current-season CSV and manifest in a temporary sibling directory and publishes the complete archive only after all source, identity, SHA and clock checks succeed via same-filesystem `os.replace`. Redirect/failure after historical staging leaves no published partial archive; occupied destinations are preserved; a success case verifies all 12 expected files (10 historical + current + manifest).
- Exact PR run [#44991894580](https://github.com/MaksimBlud/football-ai/actions/runs/44991894580): **2/2 SUCCESS**, Python 3.11 **68 passed**, Python 3.12 **68 passed**. Exact push run [#44991853932](https://github.com/MaksimBlud/football-ai/actions/runs/44991853932): **2/2 SUCCESS** on the same HEAD. Both matrix jobs compiled the source-capture module and passed the production `.pkl` diff guard. These are offline synthetic regressions only; no source/provider request, quote read, Supabase access, target-outcome read, inference, or refit occurred.
- The exact ancestry compare from root #781 HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261` to #923 HEAD `924197669b9355012ef3a773fab70749cee1070f` is **79 ahead / 0 behind**. This entire chain remains Draft / HUMAN-MERGE; none of #921–#923 is integrated or independently safe to merge.

### Fresh read-only pre-match Supabase availability
Only `public.odds_snapshots` was queried, selecting/grouping league, event identity and pre-match timestamps; no score, result, settlement, or finished-results table/field was read.
- Across nine leagues: **3,966** stored snapshot rows / **327** distinct event IDs.
- Strict timestamp-consistent pre-match subset (`snapshot_time_utc < commence_time_utc`, `snapshot_time_utc <= now()`, `created_at >= snapshot_time_utc`, `created_at < commence_time_utc`, `created_at <= now()`): **3,915 rows / 327 events**.
- Future-kickoff events with a strict pre-match snapshot: **0 in every league**.
- Serie A: **625** stored rows / **63** events; **620** strict pre-match rows; latest saved snapshot remains `2026-10-13 14:48:53.042620 UTC`.
- This recheck confirms there is still no fresh future quote cohort. The Supabase `created_at` timestamp is mutable by privileged writers, so this is a chronology consistency check, not an immutable source-provenance certificate. The source ZIP SHA and authenticated successful parent-run chronology remain mandatory.

### Frozen candidate and scientific state
- Original candidate JSON on main: SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; **19** frozen features; **20×2** weights (intercept plus 19 features); **3,799** training rows through `2026-06-30T23:59:59Z).
- `active_lambda=0` remains exact market fallback; `shadow_residual_lambda=1` remains research-only; `stability_gate_passed=false`; research-only and automatic-promotion=false.
- Prospective target-evaluation gate remains **0/30**. No Brier/LogLoss comparison or superiority claim is supported. No protected 2026/27 outcomes were read.

### Rights, security warning, and non-actions
- Football-Data automated source capture / AI inference remains HOLD; repository privacy and provider authorization are not cleared. #923 changes integrity mechanics only and grants no rights.
- Supabase schema inspection again surfaced the existing critical RLS-disabled warning for `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No DDL or policy change was made; enabling RLS without reviewed policies could break existing access and is outside this V2 run.
- No provider/API request, paid The Odds API call, source download, Supabase write/DDL, target-outcome read, inference/refit, threshold/feature/weight/contract change, production `.pkl` change, merge/main update, schedule change, bet/promotion, or other-agent setting change.


## 2026-11-22 07:58 UTC — fresh main-protection, frozen-artifact and pre-match availability checkpoint

### Main / HUMAN-MERGE safety
- Fresh GitHub branch API still reports main at `40887ebb215730190d7a6c7a1693373ec4afcdfc`, signed commit dated 2026-10-18 08:20:05 UTC. Main `PROJECT_CONTINUITY.md` remains blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`, 6,152 lines, newest dated section 2026-10-18.
- **New merge-safety finding:** GitHub reports `main.protected=false`, `protection.enabled=false`, and required-status-check enforcement `off` with no required contexts. No repository setting was changed. HUMAN-MERGE must therefore include a manual exact-HEAD/CI check; GitHub will not enforce required checks on main.
- Root [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review / mergeable at exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`. The live commit workflow-run API still returns all eight exact-head checks completed SUCCESS: #44153547152, #44153547150, #44153547394, #44153547324, #44153547126, #44153547345, #44153547374, #44153547414. No merge was performed.
- Main `serie_a_v2_forward_capture.py` still calls `fetch_saved_upcoming_serie_a_quotes` before `discover_archives`; main Original Forward still has the quote-before-source defect. The #781 default-deny hold is not integrated.

### Independent frozen-candidate integrity PR
- [PR #902](https://github.com/MaksimBlud/football-ai/pull/902) is an independent Draft / HUMAN-MERGE test-only PR, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, exact HEAD `0ecc8097bc9f34849a5d1f1ecf05966f1a6f619d`, 3 ahead / 0 behind, exactly two files changed.
- Its exact-head seven workflow runs are all SUCCESS; Original V2 Shadow Validation [#44878151827](https://github.com/MaksimBlud/football-ai/actions/runs/44878151827) reports **11 passed**, compile passed, and production `.pkl` diff guard passed. The test pins the durable candidate Git blob SHA-1, candidate artifact SHA-256, training fingerprint, 3,799 rows, exact 19-feature order, 20x2 weight shape, `active_lambda=0`, `shadow_residual_lambda=1`, failed stability and no-promotion invariants.
- Independently fetched main file blob SHAs match the PR's pins: candidate JSON `ac1303f6b096664983fbf52443bd0a381b23ba21`; parent protocol JSON `65729e9639720e67624c1481190aa22ae606f151`; original feature-builder source `401b3a0893371bfa4a488ec92a4a54af2678c8f7`. This is a durable artifact/contract integrity check, not model-performance evidence. PR remains Draft and unmerged.

### Current source-first chain
- [PR #923](https://github.com/MaksimBlud/football-ai/pull/923) remains Draft / HUMAN-MERGE at HEAD `924197669b9355012ef3a773fab70749cee1070f`, exact parent #922 HEAD `a62b91a3e8146930924b221934f8283a38c1f1f2`, 3 ahead / 0 behind its parent.
- Exact PR run [#44991894580](https://github.com/MaksimBlud/football-ai/actions/runs/44991894580): 2/2 SUCCESS, Python 3.11 **68 passed**, Python 3.12 **68 passed**, compilation and production `.pkl` diff guards passed. Exact push run [#44991853932](https://github.com/MaksimBlud/football-ai/actions/runs/44991853932) also succeeded on the same SHA.
- #922 exact PR run [#44987253304](https://github.com/MaksimBlud/football-ai/actions/runs/44987253304): 2/2 SUCCESS, Python 3.11/3.12 each **65 passed**. #921 pins source-observation clock invocation after successful HTTP response. #922 rejects redirects and requires HTTP 200 plus exact response URL. #923 stages all 11 source CSVs plus manifest and publishes the completed archive atomically. No live source capture was performed by these CI runs.
- Compare main to #923 is **128 ahead / 0 behind**. This is the full #781-rooted rights chain, not a small standalone merge. Keep sequential manual review; do not merge #923 wholesale.

### Fresh read-only pre-match Supabase aggregate
Only `public.odds_snapshots` pre-match fields were selected; no score, result, settlement, or target-outcome fields were read. Current aggregate across nine leagues:
- **3,966** snapshot rows / **327** distinct events.
- **3,915** strict timestamp-consistent pre-match rows / **327** events, requiring snapshot before kickoff, snapshot and row persistence no later than the current clock, persistence at/after snapshot observation, and persistence before kickoff.
- **0** future-kickoff events with a strict pre-match quote in every league.
- Serie A (`SERIE_A`): **625** rows / **63** events; **620** strict rows; latest saved observation remains **2026-10-13 14:48:53.042620 UTC**.
- Supabase `created_at` remains mutable by privileged writers; these predicates are chronology consistency only, not an immutable provenance certificate. Source archive SHA and authenticated source-parent workflow chronology remain mandatory.

### Rights and frozen scientific state
- The #923 source-capture rights helper still requires a provider-issued, SHA-pinned, time-valid grant and a private repository. The checked-in Football-Data manifest explicitly has `research_source_capture_permitted=false`, `provider_issued_ai_inference_license=false`, and `authorization=null`. The public repository also fails the private-artifact gate. No source request or artifact access is permitted.
- Original candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`, 19 features, 20x2 weights, 3,799 training rows through 2026-06-30, `active_lambda=0`, `shadow_lambda=1`, stability gate FAILED.
- Prospective target-evaluation gate remains **0/30**. No Brier/LogLoss market comparison is available; no protected 2026/27 target outcomes were read.

### Non-actions
No main update or merge, no branch-protection change, no provider/source/odds request, no paid API call, no Supabase write/DDL, no target-outcome read, no inference/refit, no threshold/feature/weight/contract change, no production `.pkl` change, no schedule or other-agent setting change, no bet or promotion.


## 2026-11-22 — Original V2 integrity review handoff and fresh automation audit

- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` remains the stale 6,152-line 2026-10-18 checkpoint. No main ref or file was changed.
- Independent [PR #902](https://github.com/MaksimBlud/football-ai/pull/902) is now **Ready for review** (not merged), base main at the exact SHA above, exact HEAD `0ecc8097bc9f34849a5d1f1ecf05966f1a6f619d`, 3 commits ahead / 0 behind, two files changed. Exact-head validation remains 7/7 SUCCESS; Original V2 Shadow Validation [#44878151827](https://github.com/MaksimBlud/football-ai/actions/runs/44878151827) reports 11 passed and the production `.pkl` guard passed. It pins the original candidate blob SHA, artifact SHA-256, training fingerprint, 3,799 rows, 19-feature order, 20x2 weights and frozen lambda/gate invariants. This is offline integrity evidence only. HUMAN-MERGE; no auto-merge.
- Main's [Safe Engineering Agent Auto-Merge run #45001569392](https://github.com/MaksimBlud/football-ai/actions/runs/45001569392) completed SUCCESS on main SHA above. Exact job log: 47 tests passed and `SAFE_AUTO_MERGE_HEALTHY_NOOP: no eligible bot PR with verified six-check CI`. It did not merge #902, #839, #781 or any V2 PR. The workflow's allowlist is limited to same-repository `github-actions[bot]` engineering-relay PRs.
- Root [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review at `3a70a8648895076efec2a80dc10b1798ed0d9261`, with all eight exact-head checks SUCCESS. Main's Original Forward, current-form source-capture and free-diagnostic workflows still contain live source/quote steps without the #781 default-deny hold; no such workflow was dispatched in this audit.
- Fresh read-only query of `public.odds_snapshots` only: 3,966 saved rows / 327 events; 3,915 timestamp-consistent pre-kickoff rows / 327 events; zero future-kickoff events with a strict pre-match quote. Latest Serie A snapshot remains 2026-10-13 14:48:53.042620 UTC. No score/result/settlement fields were selected. Supabase `created_at` is mutable by privileged writers, so this is chronology consistency, not immutable source attestation.
- The current GitHub connection returned HTTP 403 for the branch-protection endpoint; this run therefore does not independently re-confirm the previously recorded branch-protection state. No repository setting was changed.
- Frozen candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features, 20x2 weights, `active_lambda=0`, `shadow_lambda=1`; stability gate FAILED and prospective target-evaluation gate 0/30. No performance claim.
- No merge/main update, live source or odds request, paid API call, Supabase write/DDL, target-outcome read, inference/refit, model/production artifact change, threshold/feature/weight/contract change, schedule change, other-agent setting change, bet or promotion.


## 2026-11-22 — Private-storage preflight regression restored; latest main runtime and quote inventory

### New V2-only test commit on the current source/rights chain

- PR [#916](https://github.com/MaksimBlud/football-ai/pull/916) remains Draft and is based on open parent #915; no merge.
- Added test_private_repository_preflight_is_present_read_only_and_precedes_live_steps to tests/test_serie_a_v2_workflow_external_access_hold.py. This restores an explicit regression that had been dropped during the #916 restack: all five held V2 workflows must contain the read-only GitHub private-repository preflight, bind GH_TOKEN only to that step, map the exact repository's .private value to is_private=true|false, and run the guard before any source/quote step. Every live step and artifact upload must consume the verified is_private=true output.
- Exact current HEAD: c1b9fd04b6ac49d02d465a4401a134e30114579b; base #915 SHA 38831b5118126612dcdb7527902c43c3fa0d4661; six commits, two changed files (isolated validation workflow and offline tests only).
- Exact PR-triggered CI [run #45010502618](https://github.com/MaksimBlud/football-ai/actions/runs/45010502618): both Python 3.11 and 3.12 jobs SUCCESS; **25 tests passed in each**; compile and production .pkl diff guard passed. No model, weights, features, runtime workflow, schedule, source, quote, Supabase, or production artifact changed.

### Source-before-quote chain and current main discrepancy

- Fresh main remains 40887ebb215730190d7a6c7a1693373ec4afcdfc. Main serie_a_v2_forward_capture.py still reads saved quotes before discovering/verifying the source archive. The source-first implementation is present only on the open #884 → #908 → #911 → #915 → #916 research chain: it verifies the exact parent workflow and source ZIP SHA before lazily importing the database client and reading saved quotes. It also fails closed on the public repository.
- Root [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review at 3a70a8648895076efec2a80dc10b1798ed0d9261, with 8/8 exact-head checks SUCCESS. Its default-deny workflow hold is not on main.

### Actual main Actions runs re-read (pre-match/source metadata only)

- Original Forward [run #44922609676](https://github.com/MaksimBlud/football-ai/actions/runs/44922609676), 2026-11-21 16:05 UTC: 71 tests passed; source artifact 14710324968, SHA verified, ten pre-prospective CSVs / 3,800 historical matches; then quotes_seen=0, future_quotes_checked=0, v2_diagnostic_previews_captured=0, paid calls 0, Supabase writes 0.
- Current-Form Source Capture [run #44910356674](https://github.com/MaksimBlud/football-ai/actions/runs/44910356674), 2026-11-21 13:44 UTC: 19 tests passed; metadata-only gate 110 unique completed fixtures; 11 source files; candidate SHA unchanged; no target outcomes scored and no Supabase writes. **Governance mismatch:** this automated source capture ran after the provider policy page's 2026-11-20 update, while the refreshed rights manifest in #906 records automated source capture and inference as denied. No new source request was made in this audit; #781 must be manually integrated before the main workflows can be relied on to enforce the hold.
- Current-Form Forward [run #44923045119](https://github.com/MaksimBlud/football-ai/actions/runs/44923045119), 2026-11-21 16:09 UTC: 53 tests passed; source archive SHA and parent chronology verified, 3,910 historical rows plus 110 current-form rows; quotes_seen=0, v2_current_form_shadow_captured=0, target outcomes not read/scored, paid calls 0, writes 0.
- Free Real-Quote Diagnostic [run #44914641563](https://github.com/MaksimBlud/football-ai/actions/runs/44914641563): 53 tests passed; public-only source check, paid provider requests 0, Supabase writes 0.

### Fresh read-only Supabase odds inventory

At 2026-11-22 09:57:06 UTC, queried only public.odds_snapshots fields needed for pre-match chronology; no scores, results, or settlement fields:

- **3,915** rows / **327** events satisfy snapshot_time_utc < commence_time_utc and created_at < commence_time_utc.
- Serie A: **620** rows / **63** events; latest saved snapshot 2026-10-13 14:48:53 UTC.
- **0** future-kickoff events currently have a strict pre-match quote.
- This is timestamp consistency only: privileged writers can change created_at; it is not immutable source-before-quote attestation. No prospective quote is available to pair with a fresh source archive.

### Frozen candidate and non-actions

Original candidate remains SHA-256 a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6, 19 features, 20×2 weights, training fingerprint f27ab985..., 3,799 training rows, active_lambda=0, shadow_lambda=1; stability gate FAILED and prospective evaluation remains 0/30. No performance claim.

No merge/main update, paid API call, Supabase write/DDL, protected target-outcome read, inference/refit, weight/feature/contract change, production .pkl change, threshold tuning, schedule change, other-agent setting change, bet, or promotion.


## 2026-11-22 — Original V2 canonical identity validation and source-clock ancestry restack

### Fresh main and original-forward runtime

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` remains the 6,152-line 2026-10-18 checkpoint (blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`). No main update or merge.
- Main `.github/workflows/serie-a-v2-forward-preview.yml` blob `48ce3b0d8e31c4cf293b94500e9c320047311467` has a free read-only daily schedule at `08:08 UTC` and a `workflow_run` trigger that accepts only a successful manual `workflow_dispatch` from the existing `Serie A Odds Snapshots` workflow. It does not schedule the paid provider workflow.
- Main `serie_a_v2_forward_capture.py` blob `5db02cbd1367ed25b994b152acf371421859a014` still reads saved upcoming quotes in `main()` before discovering and verifying source archives. The direct CLI also lacks the provider-rights gate present only in the open research chain. Thus main is not yet safe to rely on for source-before-quote or rights enforcement.
- Root [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review at exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`; all eight PR-validation workflows completed SUCCESS. It has no submitted reviews or review threads and is not merged. The repository is public; private artifact preflight remains in child #879 and is not on main.

### New offline identity hardening — PR #929

- [PR #929](https://github.com/MaksimBlud/football-ai/pull/929) is Draft, stacked on exact #928 HEAD `bf18b785f9ab551390ad853739c35fc805f7cb96`; new exact HEAD `39ee3a3cd6b1ccd830aa8e14e67266301fa7dd0e`.
- The V2 shadow-row validator accepted required `home_team` / `away_team` fields without checking type/content, and accepted an event ID with surrounding whitespace while retaining the untrimmed raw value. The fix requires non-empty canonical team strings, rejects same-team home/away identities after whitespace/case normalization, and rejects noncanonical event-ID whitespace.
- Exact Actions run [#45058780676](https://github.com/MaksimBlud/football-ai/actions/runs/45058780676): compile PASS, **42 tests passed**, production-model binary guard PASS. This is offline validation only; no inference or data access.

### Source-clock PR ancestry repaired

- PR #917 previously pointed to stale #916 base SHA `b174b4a7d036d0405dc9e6d6105080133bcbb70c`, while current #916 HEAD was `9b9f586dacf3dcc3d8ce14c5bcde25050c8a405a`.
- Restacked existing [PR #917](https://github.com/MaksimBlud/football-ai/pull/917) without changing its PR identity. Final HEAD `77b39c0e93231c97709f6dd3aacb88fd6fe549b7`, exact base #916 HEAD `9b9f586dacf3dcc3d8ce14c5bcde25050c8a405a`, **4 commits ahead / 0 behind**. Exact Actions run [#45059688378](https://github.com/MaksimBlud/football-ai/actions/runs/45059688378): Python 3.11 and 3.12 both SUCCESS, **44 tests passed in each**, production binary guard passed. The source-clock validation workflow now includes #917 as a pull_request base and the #918 child branch in its push allowlist.
- Restacked existing [PR #918](https://github.com/MaksimBlud/football-ai/pull/918) on final #917 HEAD `77b39c0e93231c97709f6dd3aacb88fd6fe549b7`. Current #918 HEAD `f522c48ee8c04fcf72bdd816cd5f88224c2610ff`, **3 commits ahead / 0 behind**; only the feature-gate workflow, source-capture implementation and its tests are in the restacked delta. Exact-head CI was not yet visible at this checkpoint; keep Draft and do not merge until its parent-side source-clock workflow completes successfully.
- Descendants #919–#923 still point to the previous #918 HEAD `93d38031e3d6f724244050434e018144a48a2b51`; restack them sequentially only after #918 exact-head CI succeeds. No merge.

### Provider rights and free-source screen

- The rights manifest in open [PR #906](https://github.com/MaksimBlud/football-ai/pull/906), blob SHA `96ee20eb99abc2eb73d1ff67d71e1d6fcdeab310`, records Football-Data automated source capture, frozen inference and AI training as denied/unresolved; `provider_issued_ai_inference_license=false` and `authorization=null`. It is not on main. No provider request or source download was made in this cycle.
- [OpenScores Terms](https://openscores.ai/terms) permit internal tooling/research and caching/transformation, but its FAQ says it ingests public upstream sources. Upstream rights for the complete 19-feature feed, frozen inference and durable private raw storage are not established: HOLD pending explicit provider confirmation.
- [open-matchday](https://github.com/oladeeayo/open-matchday) publishes 2026/27 shots/corners but explicitly limits the compilation to non-commercial use and says upstream provider rights remain with those providers (including Football-Data, ESPN, FotMob and Soccerway): HOLD; no ingestion.
- [openfootball/football.json](https://github.com/openfootball/football.json) is public-domain fixtures/results but lacks the detailed shots/corners needed for the frozen 19-feature contract; fixtures-only, not a replacement statistics source.
- [StatsBomb Open Data](https://github.com/hudl/open-data) covers selected historical seasons and is not a 2026/27 current-season feed; its public-data agreement is research-oriented and restricts redistribution. Not sufficient for prospective V2: HOLD.

### Fresh read-only Supabase pre-match aggregate

Only `public.odds_snapshots` pre-match chronology fields were selected; no scores, results, settlements or target outcomes:
- **3,966** snapshot rows / **327** distinct events across nine leagues.
- **3,915** rows / **327** events satisfy `snapshot_time_utc < commence_time_utc` and `created_at < commence_time_utc`.
- **0** future-kickoff events have a strict pre-match quote in every league.
- Serie A: **625** rows / **63** events; **620** strict pre-match rows; latest saved observation `2026-10-13 14:48:53.042620 UTC`.
- `created_at` is mutable by privileged writers, so these predicates establish chronology consistency only, not immutable source provenance. Authenticated source-parent workflow chronology and archive SHA remain required.

### Frozen candidate and non-actions

- Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; 19 features; 20×2 weights; 3,799 training rows through 2026-06-30; `active_lambda=0`; `shadow_lambda=1`; stability gate FAILED; prospective target-evaluation gate 0/30. No Brier/LogLoss superiority claim.
- No main update or merge, no provider/source/odds request, no paid API call, no Supabase write/DDL, no target-outcome read, no live inference/refit, no threshold/feature/weight/contract change, no production `.pkl` change, no schedule or other-agent setting change, no bet or promotion.


## 2026-11-22 19:32 UTC — Shadow-row frozen SHA and source/quote chronology hardening

### Fresh main and immutable V2 candidate
- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` blob remains `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`. This update is confined to the existing documentation PR #839; no main update or merge.
- Original frozen candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; 19 ordered features; 20×2 weights; active lambda 0; shadow lambda 1; stability gate FAILED; prospective outcome evaluation 0/30.
- No candidate weights, feature order, imputer/scaler, training data, production `.pkl`, or frozen decision thresholds changed.

### New exact-head V2 validation PRs
- [PR #930](https://github.com/MaksimBlud/football-ai/pull/930) is OPEN / Draft / HUMAN-MERGE, child of #929; exact HEAD `acf939775426c071854eb49e5fa473338e5ea84f`. It pins `validate_shadow_capture_rows` to the original candidate SHA and makes the read-only preview import the same single constant. Exact-head workflow [#45061080136](https://github.com/MaksimBlud/football-ai/actions/runs/45061080136) SUCCESS: **43 tests passed**, compile PASS, production `.pkl` diff guard PASS.
- [PR #931](https://github.com/MaksimBlud/football-ai/pull/931) is OPEN / Draft / HUMAN-MERGE, child of #930; exact HEAD `b65ef3c97cabe8f563ab7cd3d87a35ca1bba9af8`. It enforces strict source/quote/prediction order in the row validator: feature cutoff < market snapshot <= incumbent/candidate prediction time <= capture < kickoff. Exact-head workflow [#45061202173](https://github.com/MaksimBlud/football-ai/actions/runs/45061202173) SUCCESS: **47 tests passed**, compile PASS, production `.pkl` diff guard PASS.
- The first #930 test run exposed an outdated mixed-artifact assertion after the new frozen-SHA check; the guard order was corrected so the batch-mixing regression remains independently exercised. The final exact HEAD above is green.
- Neither PR is merged. Their parent chain remains #928 → #929 → #930 → #931; keep HUMAN-MERGE and exact-head CI checks.

### Fresh source-clock chain and restack discrepancy
- [PR #918](https://github.com/MaksimBlud/football-ai/pull/918) exact HEAD `573507a03ee02821185f142d06c1ef77d596bd07`; both exact-head workflows [#45060175937](https://github.com/MaksimBlud/football-ai/actions/runs/45060175937) and [#45060172215](https://github.com/MaksimBlud/football-ai/actions/runs/45060172215) SUCCESS.
- [PR #919](https://github.com/MaksimBlud/football-ai/pull/919) currently has HEAD `430411c454807c30f1319dcdb74129d61bc4cddd` and base SHA `f522c48ee8c04fcf72bdd816cd5f88224c2610ff`; its base branch is the older #918 chain. Comparing current #918 HEAD `573507a03ee02821185f142d06c1ef77d596bd07` to #919 HEAD reports **DIVERGED: 16 ahead / 13 behind**, and GitHub currently reports #919 `mergeable=false`.
- This supersedes the earlier 03:00 continuity statement that #919 was 4 ahead / 0 behind from #918 HEAD `81de625...`. The current live PR graph is authoritative. Descendants #920–#923 still chain from #919 and must be restacked only after the #919 ancestry is reconciled; do not merge the stale chain.
- PR #839 itself remains OPEN / mergeable; this appended checkpoint records the discrepancy rather than silently rewriting the earlier historical entry.

### Fresh read-only pre-match quote audit
- Supabase read-only query selected only `odds_snapshots` event/league/timestamp fields. Strict historical pre-kickoff records require `snapshot_time_utc <= created_at < commence_time_utc` and `snapshot_time_utc < commence_time_utc`: **3,915 snapshots / 327 events across 9 leagues**; zero snapshot-after-persist anomalies.
- Strict future rows/events under the same timestamp conditions: **0 / 0**. Latest strict Serie A snapshot remains `2026-10-13T14:48:53.042620Z`.
- No scores, outcomes, settlement data, result tables, or protected 2026/27 target outcomes were selected. No Supabase writes/DDL occurred.

### Rights and runtime hold
- Football-Data automated capture and V2 inference remain HOLD / denied pending provider-issued written permission. The Lega report-derived dataset, DataSportsAPI, Global Football Data Lake, and ODSS quote source remain HOLD; no account, key, provider request, source download, or paid API call was made.
- Main remains public and branch protection remains disabled. [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review / HUMAN-MERGE, exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, 8/8 exact-head checks SUCCESS. Its default-deny live-workflow hold is not active until owner merge and fresh-main proof.
- No admissible future quotes exist in Supabase, so no new V2 forecast was generated. No Brier/LogLoss superiority claim; the 30-event evaluation gate remains closed.

### Non-actions
No merge, main update, provider request/download, paid API call, Supabase write/DDL, protected outcome read, live inference, refit, threshold tuning, production `.pkl` modification, betting, promotion, schedule change, or other-agent change.


## 2026-11-22 19:59 UTC — strict timestamp-order follow-up for original V2 shadow capture

### Exact-head PR and CI
- [PR #932](https://github.com/MaksimBlud/football-ai/pull/932) is OPEN / Draft / HUMAN-MERGE only, stacked directly on #931 exact HEAD `b65ef3c97cabe8f563ab7cd3d87a35ca1bba9af8`.
- Current #932 HEAD: `8ff52f14efbd7ca14836d40e92f47fa83ceadcad`.
- Exact-head workflow [#45063770428](https://github.com/MaksimBlud/football-ai/actions/runs/45063770428) completed SUCCESS: compile PASS, **51 V2 regression tests passed**, production `.pkl` diff guard PASS.
- The first draft HEAD `2f6b2165734b63374bd05e5527ed67f82c0de79b` correctly rejected equal timestamps but changed diagnostic wording and caused five existing regex assertions to fail. The diagnostics were restored without weakening the strict comparisons; final exact HEAD above is green.
- #932 now requires the strict sequence for both incumbent and candidate:
  `feature_history_cutoff_utc < market_snapshot_time_utc < model_generated_at_utc < capture_time_utc < kickoff_utc`.
  This closes the remaining equality case in #931: equal quote/prediction or prediction/capture timestamps do not establish event order and are rejected.
- No model feature/order, candidate SHA/weights/scaler/imputer, training fingerprint/cutoff, lambda, stability/evaluation threshold, 30-event gate, source/provider contract, production artifact, workflow schedule, main, Supabase, or other-agent setting changed.

### Current V2 validation chain
- #927: exact HEAD `85b8ff5cd4601a5edfe43681eb6e8abb22d15da7`, workflow [#45046594083](https://github.com/MaksimBlud/football-ai/actions/runs/45046594083) SUCCESS.
- #928: exact HEAD `bf18b785f9ab551390ad853739c35fc805f7cb96`, workflow [#45052642437](https://github.com/MaksimBlud/football-ai/actions/runs/45052642437) SUCCESS.
- #929: exact HEAD `39ee3a3cd6b1ccd830aa8e14e67266301fa7dd0e`, workflow [#45058780676](https://github.com/MaksimBlud/football-ai/actions/runs/45058780676) SUCCESS.
- #930: exact HEAD `acf939775426c071854eb49e5fa473338e5ea84f`, workflow [#45061080136](https://github.com/MaksimBlud/football-ai/actions/runs/45061080136) SUCCESS.
- #931: exact HEAD `b65ef3c97cabe8f563ab7cd3d87a35ca1bba9af8`, workflow [#45061202173](https://github.com/MaksimBlud/football-ai/actions/runs/45061202173) SUCCESS, 47 tests.
- #932: exact HEAD and 51-test SUCCESS as above.
- The chain is sequential: #927 → #928 → #929 → #930 → #931 → #932. Do not merge a child without all parents; HUMAN-MERGE remains mandatory.

### Fresh main runtime and pre-match-only Supabase audit
- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` blob remains `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`.
- Main Original V2 Forward-Only [run #45042303864](https://github.com/MaksimBlud/football-ai/actions/runs/45042303864) completed SUCCESS with 71 tests; source SHA attestation succeeded, but `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `supabase_writes=0`. Its output artifact is diagnostic only, not a forecast.
- Main Current-Form Forward-Only [run #45042946420](https://github.com/MaksimBlud/football-ai/actions/runs/45042946420) completed SUCCESS with 53 tests; source artifact `14756317850` and SHA `cf96923f75616bd2d045997e89863c0a32b7b453736a90cc353447c2c7dae955` verified against successful parent run `45028522381`; `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes not read/scored.
- Read-only Supabase query selected only `public.odds_snapshots` league/event/timestamp columns. Strict pre-match predicate was `snapshot_time_utc < commence_time_utc AND created_at < commence_time_utc AND snapshot_time_utc <= created_at`: **3,915 rows / 327 events across 9 leagues**; **0 future events** with strict saved quotes. Latest strict Serie A quote remains `2026-10-13 14:48:53.042620 UTC`. No result, score, settlement or target-outcome columns were selected.
- No new admissible quote or prospective V2 forecast exists. Evaluation remains 0/30; no Brier/LogLoss superiority claim.

### Live-access and database security blockers
- [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review / HUMAN-MERGE, exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, 8/8 exact-head workflow runs SUCCESS. It is not integrated; main still exposes the live source/quote workflows while provider clearance and private storage remain unresolved. Main repository is public and branch protection is disabled.
- Supabase schema metadata reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. This was metadata-only; no DDL or data write was executed. Do not enable RLS until policies are designed and owner-approved.
- Football-Data automated capture/inference remains HOLD pending provider-issued written permission. No provider request, source download, paid API call, Supabase write/DDL, protected target-outcome read, production `.pkl` change, refit, promotion, bet, schedule change, or other-agent setting change occurred in this checkpoint.


## 2026-11-22 20:56 UTC — restacked current-form identity proof; live-source governance violation confirmed

### Fresh repository state
- Fresh `main` remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; the main continuity file remains the October 18 blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`.
- Main is still public and branch protection is disabled.
- This checkpoint is on documentation PR #839 only; no main update or merge.

### PR #919 ancestry repaired without duplicating the PR
- The previous #919 head `430411c454807c30f1319dcdb74129d61bc4cddd` was based on the stale #918 parent `f522c48ee8c04fcf72bdd816cd5f88224c2610ff`, while current #918 had advanced to `573507a03ee02821185f142d06c1ef77d596bd07`.
- Restacked the existing #919 branch (preserving PR identity) on exact current #918 HEAD. New #919 HEAD: `6a871e1e01a34afb052650c1ebd2e0578f26c426`; compare is **1 ahead / 0 behind**, merge base equals #918 HEAD, and GitHub reports mergeable.
- The restacked change retains the metadata-only `match_date/home_team/away_team` gate, canonical fixture identity digest, exact CSV identity-set comparison, alias normalization, reversed-duplicate rejection and same-count substitution rejection. It also adds #919 push and pull-request target filters to the source-clock validation workflow so the relevant checks actually run.
- Exact-head CI: all four runs SUCCESS — Source Clock push [#45069137805](https://github.com/MaksimBlud/football-ai/actions/runs/45069137805), Feature Gate push [#45069137831](https://github.com/MaksimBlud/football-ai/actions/runs/45069137831), Source Clock PR [#45069143248](https://github.com/MaksimBlud/football-ai/actions/runs/45069143248), Feature Gate PR [#45069143226](https://github.com/MaksimBlud/football-ai/actions/runs/45069143226). Python 3.11 and 3.12 each report **49 passed** in both workflows; compile and production `.pkl` diff guards passed.
- #919 remains OPEN / Draft / HUMAN-MERGE. No merge. Its descendants #920–#923 still need sequential restacking onto the new #919 HEAD; do not merge their stale ancestry.

### Correction: fresh main workflow performed a live Football-Data download
The earlier 19:59 checkpoint said no source download occurred in that audit. A subsequent inspection of the actual GitHub Actions logs confirms that main did perform a live download after the provider policy revision dated November 20. This is a governance blocker, not evidence of permission:
- Current-Form Source Capture [run #45028522381](https://github.com/MaksimBlud/football-ai/actions/runs/45028522381), 2026-11-22 13:38 UTC: 19 tests passed; metadata-only gate counted 110 prior completed fixture identities; the workflow downloaded 10 historical CSVs plus current-season CSV (11 source files), and uploaded artifact **14756317850**, ZIP SHA-256 `cf96923f75616bd2d045997e89863c0a32b7b453736a90cc353447c2c7dae955`.
- The official Football-Data policy audit in #906 records automated AI/data-training capture and inference as denied/unresolved after the November 20 policy update. The live run therefore must not be treated as authorized merely because it succeeded technically. Do not repeat this source request or use this archive for V2 inference until a provider-issued written grant and private storage are established.
- Original Forward-Only [run #45042303864](https://github.com/MaksimBlud/football-ai/actions/runs/45042303864), 2026-11-22 16:10 UTC: 71 tests passed; verified the old-season source attestation, but `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`; no forecast.
- Current-Form Forward-Only [run #45042946420](https://github.com/MaksimBlud/football-ai/actions/runs/45042946420), 2026-11-22 16:16 UTC: 53 tests passed; verified source archive 14756317850 and its parent run, but `quotes_seen=0`, `v2_current_form_shadow_captured=0`, target outcomes not read/scored, paid calls 0, Supabase writes 0. This verifies plumbing only; it does not authorize the source archive or establish model quality.

### Fresh read-only Supabase pre-match inventory
Only `public.odds_snapshots` fields `league, event_id, snapshot_time_utc, created_at, commence_time_utc` were selected. No score, result, settlement or target-outcome fields:
- **3,915** strict pre-match rows / **327** distinct events across 9 leagues.
- Predicate: `snapshot_time_utc < commence_time_utc AND created_at < commence_time_utc AND snapshot_time_utc <= created_at`.
- **0** future-kickoff events have a strict saved pre-match quote.
- Serie A: **620** strict rows / **63** events; latest saved observation `2026-10-13T14:48:53.042620Z`.
- These database timestamps are chronology consistency only; privileged writers can mutate `created_at`, so this is not immutable source-before-quote provenance.

### Frozen V2 state and non-actions
- Original candidate SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features; 20×2 weights; 3,799 training rows through 2026-06-30; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- `active_lambda=0`; `shadow_lambda=1); stability gate FAILED; prospective evaluation remains 0/30. No Brier/LogLoss superiority claim.
- [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review, exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, 8/8 exact-head CI SUCCESS. Its hold is not active on main until owner manual merge and fresh-main proof.
- No merge/main update, provider request by this audit, paid API call, Supabase write/DDL, protected target-outcome read, inference/refit, threshold tuning, production `.pkl` modification, bet, promotion, schedule change or other-agent setting change.


## 2026-11-22 21:01 UTC — repaired #919–#923 source-provenance chain

### Exact ancestry and PR status
The stale #919–#923 branch graph has now been restacked sequentially without creating duplicate PRs or touching main. Every PR remains OPEN / Draft / HUMAN-MERGE and is 1 commit ahead / 0 behind its exact parent; GitHub reports each mergeable.

| PR | Exact HEAD | Exact base HEAD | Main change | Exact-head CI |
|---|---|---|---|---|
| [#919](https://github.com/MaksimBlud/football-ai/pull/919) | `6a871e1e01a34afb052650c1ebd2e0578f26c426` | #918 `573507a03ee02821185f142d06c1ef77d596bd07` | Metadata/CSV fixture identity SHA-256 reconciliation | 4/4 SUCCESS, 49 tests per job |
| [#920](https://github.com/MaksimBlud/football-ai/pull/920) | `cc54c7b73da1d03846dd29bb17b62cf0cbc95720` | #919 `6a871e1e01a34afb052650c1ebd2e0578f26c426` | Reject non-aware entry clocks before access | 4/4 SUCCESS, 51 tests per job |
| [#921](https://github.com/MaksimBlud/football-ai/pull/921) | `1f74bc134fe690bea2a397b7ede290a6ea6d64f5` | #920 `cc54c7b73da1d03846dd29bb17b62cf0cbc95720` | Source observation only after successful response | 4/4 SUCCESS, 51 tests per job |
| [#922](https://github.com/MaksimBlud/football-ai/pull/922) | `bb02ef0ad662041fcb1432cbe8ffcbabc1f87060` | #921 `1f74bc134fe690bea2a397b7ede290a6ea6d64f5` | Reject redirects and unexpected response origins | 4/4 SUCCESS; 55 Source Clock / 68 Feature Gate tests |
| [#923](https://github.com/MaksimBlud/football-ai/pull/923) | `2ddef8a7b66324224e5a0d243f364a36109b9420` | #922 `bb02ef0ad662041fcb1432cbe8ffcbabc1f87060` | Atomic publication of complete source archives | 4/4 SUCCESS; 58 Source Clock / 71 Feature Gate tests |

All listed test counts are reproduced under Python 3.11 and 3.12 for both push and pull-request event runs. Each job also passed Python compilation and the production `.pkl` diff guard. Exact workflow run IDs and details are in the corresponding PR descriptions.

### What the chain now proves
- The 30-event feature-input gate is based on canonical fixture identities, not count alone; current CSV identities must match the metadata-only gate by count and domain-separated SHA-256.
- Entry, observation and archive clocks must be timezone-aware and ordered; source observation is sampled only after successful HTTP completion.
- Redirects and unexpected final URLs are rejected before body access or timestamping.
- Source archives are staged privately in a temporary directory and become visible only after complete success via atomic rename; occupied destinations and symlinks are rejected.
- These are provenance/transport/atomicity controls around the original V2 research input path. They do not alter the frozen 19 features, weight matrix, scaler/imputer, candidate SHA, training fingerprint/cutoff, lambda values, market fallback, stability gate, evaluation protocol or thresholds.

### Important limitations
- The four-workflow CI matrix is synthetic/offline. It proves code and regressions, not provider permission, live source availability, a production inference, a new quote, or predictive quality.
- PR #781 remains the separate owner-controlled default-deny hold. No PR in this chain activates a workflow or authorizes Football-Data use.
- Main still contains the public live workflows until owner manual merge of #781 followed by fresh-main proof. The live source-capture run #45028522381 documented in the preceding checkpoint must be treated as an unauthorized provider download under the current #906 rights audit; do not reuse or refresh it.
- PR #920–#923 must remain in strict parent order. Do not merge a child before its parent; no autonomous merge.

### Non-actions
No main update/merge, source/provider request by this audit, paid API request, Supabase write/DDL, protected target-outcome read, V2 inference/refit, threshold tuning, production `.pkl` change, betting, promotion, schedule change or other-agent setting change.

## 2026-11-22 21:59 UTC — strict integer input for the frozen outcome-read gate

### Exact-head PR and CI
- [PR #933](https://github.com/MaksimBlud/football-ai/pull/933) is OPEN / Draft / HUMAN-MERGE only, stacked directly on #932 exact HEAD `8ff52f14efbd7ca14836d40e92f47fa83ceadcad`.
- Exact #933 HEAD: `91b9c29dc16ffe7674f55774aa42350c27f3368d`; compare is 1 ahead / 0 behind its exact #932 parent; GitHub reports mergeable.
- Exact-head workflow [#45075006891](https://github.com/MaksimBlud/football-ai/actions/runs/45075006891) completed SUCCESS: compile PASS, **60 V2 regression tests passed**, production `.pkl` diff guard PASS.
- The prior `outcome_read_permitted()` accepted any value that compared numerically with 30. A non-integer value such as `30.5` could therefore satisfy the frozen gate, and Python booleans are integer subclasses.
- The function now accepts only Python/NumPy integer scalars, explicitly rejects bool/NumPy bool, floats (including 30.0 and 30.5), strings and None, and rejects negative counts. The threshold remains exactly 30.
- The function still depends on its caller to supply a count derived from the preregistered canonical unique-primary-event identity gate; this type check does not itself prove event uniqueness or open the gate.

### Frozen state and non-actions
- Original candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features, 20×2 weights, 3,799 training rows, training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`, active lambda 0, shadow lambda 1, stability gate FAILED, evaluation 0/30.
- No new admissible pre-kickoff quote or prospective V2 shadow forecast was found. The latest read-only `public.odds_snapshots` aggregate remains 3,915 strict pre-kickoff rows / 327 events across nine leagues, 0 strict future rows/events, latest strict Serie A snapshot `2026-10-13T14:48:53.042620Z`.
- PR #781 remains OPEN / Ready for review, exact HEAD `3a70a8648895076efec2a80dc10b1798ed0d9261`, 8/8 exact-head CI SUCCESS. The default-deny hold is not active on main until owner manual merge and fresh-main verification.
- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; its continuity file is still the October 18 blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`. Supabase schema metadata still reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`; no DDL or policy change was attempted.
- No main update/merge, Supabase write/DDL, provider request/download, paid API call, protected outcome read, inference, refit, threshold tuning, production `.pkl` change, bet, promotion, schedule change or other-agent change.


## 2026-11-23 00:08 UTC — V2 live-workflow hold inventory strengthened

### Exact root-hold head and CI
- Root [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review / mergeable / not merged. It is based on main `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- After a fresh static audit, #781 was advanced to exact HEAD `020697894b79b25f981673925a6734007f8d5200`; exact compare is **50 ahead / 0 behind**, 7 changed files.
- Exact-head PR CI: **8/8 SUCCESS**. Frozen V2 Shadow [#45086912393](https://github.com/MaksimBlud/football-ai/actions/runs/45086912393): **107 passed**, compile and production `.pkl` diff guard PASS. Recovery [#45086912473](https://github.com/MaksimBlud/football-ai/actions/runs/45086912473): **53 passed**; candidate rebuild/proof/upload steps were skipped by the default-deny flag and production pickle hash guard passed.
- Other exact-head checks: Research [#45086912434](https://github.com/MaksimBlud/football-ai/actions/runs/45086912434), Serie A [#45086912328](https://github.com/MaksimBlud/football-ai/actions/runs/45086912328), Bundesliga [#45086912338](https://github.com/MaksimBlud/football-ai/actions/runs/45086912338), Ligue 1 [#45086912344](https://github.com/MaksimBlud/football-ai/actions/runs/45086912344), Eredivisie [#45086912365](https://github.com/MaksimBlud/football-ai/actions/runs/45086912365), Product [#45086912465](https://github.com/MaksimBlud/football-ai/actions/runs/45086912465). Research/Product/league runs are CI path-filter checks, not additional V2 model evidence.

### New static-guard gap closed
The earlier #781 inventory caught an unlisted new V2 workflow, but did not reject a new external-I/O or non-test Python step added inside one of the five already-inventoried V2 workflows. It also checked job-level credentials but not workflow-level secrets inherited by offline steps.

The one-file test update now:
- enumerates every top-level step in each of the five V2 live workflows;
- requires every external-I/O, credential-bearing or non-test Python entrypoint to be explicitly listed and gated as a live step or successful-only artifact upload;
- allows only the named existing offline inline-Python source-contract check;
- rejects workflow-level Supabase/GitHub/API credential bindings;
- includes synthetic regressions for an unlisted Python source helper, an unlisted network request and a workflow-level Supabase secret.

A temporary child PR #934 was closed after transplanting the same test-only change into root #781 so the root PR's exact-head CI could run. It was not merged. #781 remains HUMAN-MERGE only.

### Current limitations and non-actions
- This change strengthens the hold's regression coverage; it does not activate the hold on main. The live source/quote workflows remain unblocked on main until owner manual merge of #781 and fresh-main verification.
- No provider request/download, paid API call, Supabase write/DDL, protected target-outcome read, V2 inference/refit, threshold tuning, production `.pkl` change, main update, merge, schedule change or other-agent setting change occurred in this cycle.


## 2026-11-23 — 5DollarFootballAPI free Serie A source recheck (HOLD)

Official provider documentation was re-read on 2026-11-23. This was a documentation-only review: no account/key was created, no API endpoint was called, no match data was downloaded, and no provider integration was changed.

- **Terms:** the provider's Terms (last updated October 2026) permit use in models/internal tools and caching, prohibit reselling or redistributing raw responses as a competing feed, and require attribution on public-facing products using $0 plans. This is a provider-level grant; the reviewed terms do not identify or independently establish the upstream rights for every underlying match-statistics/odds source or a private raw-response retention period.
- **Free plan:** the pricing page lists $0 access to the top five leagues, explicitly including Serie A, at 60 requests/hour, with the last 3 months of results/history.
- **Community Access:** the pricing page lists a second $0 plan at 300 requests/hour, top-five leagues plus one country pack, and 12 months of results/odds history. Eligibility is self-attested for students, academic/non-profit research, early-career developers, or people for whom $5/month is a material decision. No eligibility or account activation was assumed.
- **Contradictory first-party entitlement:** the provider's measured data-quality table, recounted about 14 hours before this review, labels **Italy Serie A as Pro**, despite the pricing page's Free Top-5 statement. It reports 383 finished Serie A matches in the last 12 months and 100% coverage for corners, half-time corners, corner lines, odds, events, live statistics and cards; the history column says 2014 / 13 seasons. The plan label conflicts with the Free/Community marketing description and is not resolved by public documentation.
- **Feature compatibility:** the frozen original V2 still requires the exact 19-feature contract derived from FTHG, FTAG, FTR, HC, AC, HY, AY, HR, AR (rolling 5/10 and venue-5 points, goals, corners and cards). The API docs expose fixture events for goals/corners/cards and a statistics endpoint for attacks, dangerous attacks, shots and possession. The docs state timestamps are UTC, but the fixture-statistics examples contain no per-stat updated_at, last_updated or first-observed timestamp. The public status page reports aggregate freshness, not each statistic's first availability. A raw response archive captured and SHA-pinned strictly before each quote could establish the exact bytes observed before that quote, but it would not resolve the plan conflict or upstream licensing.
- **Coverage limitation:** Free's 3-month history is not enough to assume complete 30-match windows for every Serie A team. Community's 12-month window may be sufficient for many clubs, but complete per-team 30-match coverage (especially promoted/new teams) has not been demonstrated. The 13-season history shown in the quality table is marked Pro. No feature-completeness claim is made without a permitted data conformance test.

**Decision remains HOLD.** Before any API request or integration, require written clarification of (1) whether Serie A fixture/results/events/statistics are actually included on Free and Community despite the Pro label, (2) upstream rights covering AI/model feature use and private raw-response archiving, (3) retention/deletion terms for raw archives, and (4) the exact fields and historical window available to the $0 plan. If those are resolved, the first test must be a single non-production, read-only conformance capture with raw response bytes, UTC observation time, SHA-256, strict source-before-quote ordering, and a per-team 30-match coverage report. No original V2 feature, weight, training or market contract may change.

Provider references: https://5dollarfootballapi.com/terms ; https://5dollarfootballapi.com/pricing ; https://5dollarfootballapi.com/docs ; https://5dollarfootballapi.com/docs/data-quality ; https://5dollarfootballapi.com/status .


### 2026-11-23 01:48 UTC — fresh-main, workflow, PR ancestry, and pre-match database checkpoint

**Fresh repository state**
- Default branch is still `main` at `40887ebb215730190d7a6c7a1693373ec4afcdfc` (last commit 2026-10-18 08:20:05 UTC). Repository visibility is **public** and GitHub reports `main.protected=false`; no branch-protection rules are active.
- No main update or merge was made. This checkpoint is documentation-only on PR #839.

**Root live-workflow hold — PR #781**
- Current exact PR HEAD: `020697894b79b25f981673925a6734007f8d5200`; base main `40887ebb...`; compare is **50 ahead / 0 behind**. PR is OPEN, Ready for review, mergeable, not merged.
- Exact-HEAD workflow runs returned by the commit-specific GitHub Actions endpoint: **8/8 SUCCESS**. Frozen V2 Shadow [#45086912393](https://github.com/MaksimBlud/football-ai/actions/runs/45086912393) ran the original frozen candidate against strict synthetic inputs; recovery [#45086912473](https://github.com/MaksimBlud/football-ai/actions/runs/45086912473) passed 53 offline tests, restored the frozen code for comparison, skipped candidate rebuild/proof/publication, and passed the production-pickle hash guard.
- Independently fetched all five workflow files at the exact #781 branch HEAD. Each has workflow-level `MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED: "false"`; every identified live source/quote/recovery step is gated, and every upload-artifact step requires both success and the flag. Existing cron strings remain `13 6 * * *`, `8 8 * * *`, `50 5 * * *`, and `18 8 * * *`; the recovery workflow has no cron. These conditions are on the PR branch only and do **not** protect main until the owner manually merges #781.
- #781 does not itself prove provider rights or private storage. The private-repository child PR #879 is still based on the older #781 SHA `3a70a864...`. Current #879 HEAD is `b78010585c80b05ae5fc2a8b3572df14b32d9651`; comparing it with the new #781 HEAD `020697...` is **DIVERGED (1 ahead / 14 behind)**. Do not merge or retarget this child until it is safely restacked on the current parent.
- Original Forward source-first child #884 remains OPEN/Draft at `c38834ec6c2bd0079afca9e63a9ce75a8cd17043`, based on #879's old HEAD `b780105...`. Its PR description records that this latest SHA's CLI tampered-ZIP follow-up has **no independently surfaced exact-HEAD CI**; the last verified 2/2 run (79 tests per Python version) was on the older SHA `1d366777...`. Do not treat the older CI as validating the current head.

**Other exact-head V2 checks**
- PR #933 exact HEAD `91b9c29dc16ffe7674f55774aa42350c27f3368d`: [run #45075006891](https://github.com/MaksimBlud/football-ai/actions/runs/45075006891) SUCCESS; exact log shows **60 passed**, compilation and production `.pkl` diff guard passed. It hardens only the input type for the unchanged 30-event gate; it does not establish 30 eligible forecasts.
- PR #839 documentation branch HEAD before this checkpoint: `72b0a1935318cf2dc4a271d25b2e7174b3392984`, compare **4 ahead / 0 behind**. Its exact-head commit-specific run list is **8/8 SUCCESS**; Frozen V2 Shadow [#45092252758](https://github.com/MaksimBlud/football-ai/actions/runs/45092252758) reports **89 passed** and production `.pkl` guard passed. This new documentation commit requires its own fresh exact-head CI; prior CI is not inherited by the new SHA.

**Original Forward source-order finding**
- Fresh main source blob for `serie_a_v2_forward_capture.py` is `b2770d726ffafe7a3cef706b57d3391063cbfe1b`. Its current `main()` still imports/reads saved quotes before `discover_archives()`; this violates the requested source-before-quote order. The source-first preflight exists only in stacked PR #884 and is not integrated. No quote read or live run was initiated in this audit.

**Supabase — read-only, pre-match odds metadata only**
- Read-only aggregation of `public.odds_snapshots` using `snapshot_time_utc < commence_time_utc AND created_at < commence_time_utc AND snapshot_time_utc <= created_at`: **3,915 strict pre-match rows / 327 distinct events / 9 leagues**; future pre-match rows/events: **0**.
- By league (rows / events; latest qualifying snapshot UTC): Bundesliga 394/35 (2026-09-11 15:49:52); EPL 1,135/70 (2026-10-09 15:25:57); Eredivisie 410/39 (2026-09-11 15:50:20); La Liga 798/52 (2026-09-11 15:45:28); Ligue 1 387/35 (2026-09-11 15:49:24); Primeira Liga 9/9 (2026-09-11 16:06:24); RPL 153/15 (2026-09-05 15:07:55); Serie A 620/63 (2026-10-13 14:48:53); Turkey Super Lig 9/9 (2026-09-11 16:06:26). These are timestamp/identity aggregates only; no scores, outcomes, or settlement fields were selected.
- Schema inventory again reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. This is a CRITICAL exposure for anon/authenticated roles. No remediation SQL was executed; policies must be designed before enabling RLS. `public.odds_snapshots` has RLS enabled.

**Frozen V2 and non-actions**
- Original candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features and original weights unchanged; `active_lambda=0`, `shadow_lambda=1` research-only; stability gate remains FAILED; prospective evaluation remains **0/30**.
- No paid provider call, no source archive download/use, no Supabase write/DDL, no production `.pkl` change, no model refit/weight/feature/threshold change, no protected 2026/27 outcome read, no merge, and no schedule/other-agent setting change.
- Next integration order remains owner-controlled #781 first; then restack #879 on the exact merged root and revalidate #884 and descendants. Provider-rights and private-storage HOLDs remain mandatory. Do not claim model superiority without an eligible independent Brier/LogLoss comparison.

## 2026-11-23 03:28 UTC — harden the workflow-hold step inventory

- Fresh main remains 40887ebb215730190d7a6c7a1693373ec4afcdfc; no main update or merge occurred.
- Re-audit of the exact #781 head 020697894b79b25f981673925a6734007f8d5200 found a static-inventory gap: the step parser recognized only named steps and uses-first steps, so an unnamed top-level - run: could escape the inventory. The workflow-wide action check also inspected only the first action reference, so an unreviewed action after actions/checkout could be missed.
- Updated the existing #781 branch, not main: exact new HEAD 498bfef1ed811dac74767cb4e04ca69d1135fe29, one commit after 020697. The scanner now enumerates every top-level Actions step, gives unnamed steps explicit sentinel identities, checks every uses reference, and treats unreviewed actions as live-capable. Only the existing checkout and Python setup actions are allowlisted for offline validation; artifact publication remains confined to the named, separately gated upload step.
- Added regressions for unnamed Python collection, unnamed curl, an unreviewed action, an unreviewed action after checkout, and the exact offline-action allowlist.
- Exact new-head CI: 8/8 SUCCESS on 498bfef1:
  - Frozen V2 Shadow #45106091851: 110 passed; production model hash comparison passed.
  - Recovery #45106091871: 56 passed; default-deny recovery workflow completed successfully.
  - Research #45106091856.
  - Product #45106091806.
  - Serie A #45106091966.
  - Bundesliga #45106091933.
  - Ligue 1 #45106091916.
  - Eredivisie #45106091973.
- PR #781 remains OPEN / Ready for review / mergeable and unmerged. Its base remains main 40887ebb; it is 51 commits ahead / 0 behind. The live-access hold is still inactive on main until owner HUMAN-MERGE.
- PR #934 remains closed unmerged; its earlier test changes and this follow-up are carried directly in #781. No duplicate PR was opened.
- No source/provider request, artifact download, quote read, Supabase write/DDL, target-outcome read, production .pkl change, candidate/feature/weight change, schedule change, main update, merge, or other-agent setting change occurred in this update.

## 2026-11-23 03:34 UTC — close reusable-workflow job bypass in the live-access hold

- Rechecking the updated #781 scanner found one additional workflow form not represented by step-level uses parsing: a reusable workflow invoked directly at jobs.<job>.uses (four-space YAML indentation). A new original-V2 workflow could otherwise call an unreviewed reusable workflow without a Python command or known network marker.
- Updated the same #781 branch, not main. Exact new HEAD: 85541f1963db168be9d7f788725637b17ce9f5db. The action inventory now checks reusable-workflow job references as well as six-space uses-first steps and eight-space step uses fields. Unreviewed references fail closed.
- Added a synthetic regression for a V2 workflow whose job directly uses an unreviewed reusable workflow.
- Exact new-head CI: **8/8 SUCCESS**:
  - Frozen V2 Shadow [#45106690163](https://github.com/MaksimBlud/football-ai/actions/runs/45106690163): **111 passed**; production model hash check succeeded.
  - Recovery [#45106690149](https://github.com/MaksimBlud/football-ai/actions/runs/45106690149): **57 passed**; default-deny recovery path succeeded.
  - Research [#45106690207](https://github.com/MaksimBlud/football-ai/actions/runs/45106690207).
  - Product [#45106690147](https://github.com/MaksimBlud/football-ai/actions/runs/45106690147).
  - Serie A [#45106690200](https://github.com/MaksimBlud/football-ai/actions/runs/45106690200).
  - Bundesliga [#45106690171](https://github.com/MaksimBlud/football-ai/actions/runs/45106690171).
  - Ligue 1 [#45106690178](https://github.com/MaksimBlud/football-ai/actions/runs/45106690178).
  - Eredivisie [#45106690199](https://github.com/MaksimBlud/football-ai/actions/runs/45106690199).
- PR #781 remains OPEN / Ready for review / mergeable, base main 40887ebb215730190d7a6c7a1693373ec4afcdfc, 52 commits ahead / 0 behind. No merge or main update.
- Ancestry recheck: #879 remains diverged from current #781 by 14 commits ahead / 2 behind (merge base 3a70a8648895076efec2a80dc10b1798ed0d9261); #884 is 7 ahead / 0 behind its #879 parent; #885 is 2 ahead / 0 behind its #884 parent. Do not restack/merge these children until the owner manually integrates #781 and the fresh main is reread.
- Current original candidate remains unchanged: artifact SHA a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6; training fingerprint f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098; 3,799 training rows; exact 19-feature order; 20x2 weights; active_lambda=0; shadow_residual_lambda=1; stability gate FAILED; 30-prospective-forecast evaluation gate 0/30.
- Current Football-Data rights manifest remains fail-closed: rights status V2_FROZEN_INFERENCE_SCOPE_UNRESOLVED, AI training permission false, provider-issued AI-inference license false, authorization null. No inference/training is authorized by this project manifest.
- Supabase read-only odds_snapshots audit remains 3,915 strict pre-match snapshots across 327 events and nine leagues; future eligible quotes 0. The table schema contains odds and timestamp fields only, not the 19 historical team-statistic inputs. No match-result, score or settlement columns were queried.
- No provider/API request, source download, artifact download, quote read, Supabase write/DDL, protected target-outcome read, production .pkl change, candidate/feature/weight change, schedule change, main update, merge or other-agent setting change occurred.

## 2026-11-23 05:00 UTC — merge recursive outcome embargo into the strict V2 shadow branch

- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main update or merge occurred.
- Cross-branch audit found that the strict candidate/timestamp stack (#924–#933) still checked only top-level forbidden keys in `validate_shadow_capture_rows`. The separate nested-outcome stack (#854–#865) already had a recursive guard, but that guard was not present in the strict #933 branch. This left the two protections split across incompatible review stacks.
- Ported the previously CI-tested recursive implementation from #865 into the latest strict #933 branch, preserving the newer candidate SHA, type validation, exact 19-feature recipe, temporal checks, and exact-integer 30-event gate.
- The validator now rejects protected score/result/goal/winner/post-match-statistic keys anywhere in nested mappings, lists, or tuples; normalizes snake_case, camelCase, punctuation, dots, spaces, and compact provider abbreviations; and checks exact typed-stat descriptor fields. It deliberately preserves pre-match odds and frozen derived feature names such as `diff_goals_for_5`.
- Added ten regression functions, including nested provider payloads, Football-Data aliases, punctuation-separated abbreviations, 1X2 winner flags, typed descriptors, and positive controls for allowed market/derived fields. The strict V2 test module now has 40 test functions and 180 parametrized cases.
- Exact final PR #933 HEAD: `9034815100eb05030a462785483bb56375df0028`, based on #932 `8ff52f14efbd7ca14836d40e92f47fa83ceadcad`; 3 commits ahead / 0 behind; OPEN / Draft / mergeable; not merged.
- The first intermediate commit `2fe2a462...` produced six pytest fixture errors because the copied multi-line parametrization decorators were not included. This was corrected in the next commit before final verification. Exact final-head CI [#45115047106](https://github.com/MaksimBlud/football-ai/actions/runs/45115047106) is **SUCCESS**: **180 passed**, compile succeeded, and production `.pkl` diff guard passed. No claim is carried from the failed intermediate SHA to the final SHA.
- The earlier #865 source branch had 245 tests passing on its own exact head, but remains a separate open stack; the recursive protection is now also present in #933 so the latest candidate/timestamp contract no longer omits it. No existing PR was merged or closed.

**Fresh main runtime recheck**
- Main `serie_a_v2_forward_capture.py` blob `5db02cbd1367ed25b994b152acf371421859a014` still reads saved Supabase quotes before `discover_archives()`. This is still the original-forward source-before-quote violation. The source-first fix is in #884, not main.
- Main `serie_a_v2_current_form_forward_capture.py` blob `326ac1921ce901a31aa6d73e6cbddb0782071964` verifies the latest source archive, but then unconditionally creates the Supabase client and reads saved quotes even if source verification did not pass. The fail-closed source-before-quote fix is in #913, not main.
- Root workflow hold #781 remains OPEN / Ready for review at `5552bec363ae72ad7aef04c598d2ce861f33eb42`, exact 8/8 CI SUCCESS. It is not active on main until owner HUMAN-MERGE. No attempt was made to run, dispatch, cancel, or modify scheduled workflows.

**Supabase — pre-match-only read**
- Fresh read-only `odds_snapshots` aggregation returned **3,915** strict pre-kickoff rows across **327** events and **9** leagues; future eligible rows/events remain **0**.
- The latest qualifying Serie A snapshot remains 2026-10-13 14:48:53 UTC. No score, result, settlement, or target-outcome field was selected.

**Frozen V2 and non-actions**
- Candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 features, original weights, scaler, imputer, and training fingerprint remain unchanged. `active_lambda=0`, `shadow_lambda=1`, stability gate FAILED, prospective evaluation 0/30.
- No protected 2026/27 outcomes read; no source download/use; no provider request; no paid API call; no Supabase write/DDL; no production `.pkl` change; no model refit, threshold, weight, feature, or schedule change; no main update or merge; no other-agent setting change.


## 2026-11-23 06:03 UTC — prevent duplicate Serie A fixtures from inflating the V2 primary cohort

**Fresh repository and workflow state**
- Re-read main and the continuity branch before changes. Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main update or merge occurred.
- Re-read Original Forward and Current-Form workflow YAML on main and on the #781 hold branch. Main still has the old live workflow definitions; #781 has the fail-closed step gates but is not integrated.
- Main's latest visible V2 scheduled runs remain on 2026-11-22: Current-Form Forward [#45042946420](https://github.com/MaksimBlud/football-ai/actions/runs/45042946420), Original Forward [#45042303864](https://github.com/MaksimBlud/football-ai/actions/runs/45042303864), Free Real-Quote Diagnostic [#45033051083](https://github.com/MaksimBlud/football-ai/actions/runs/45033051083), and Current-Form Source Capture [#45028522381](https://github.com/MaksimBlud/football-ai/actions/runs/45028522381). No new V2 scheduled run for 2026-11-23 05:50 UTC was visible in the current scheduled-run listing; no workflow was dispatched or changed.
- The Safe Engineering Agent Auto-Merge run inspected at [#45115328533](https://github.com/MaksimBlud/football-ai/actions/runs/45115328533) reported `SAFE_AUTO_MERGE_HEALTHY_NOOP: no eligible bot PR with verified six-check CI`; it did not merge a PR. HUMAN-MERGE remains in force.

**New V2 cohort-integrity defect and fix**
- Re-audit of the strict #933 shadow validator found that it rejected duplicate `event_id` values but did not reject the same real fixture appearing under two different provider event IDs. Reversed home/away labels and known club aliases could therefore allow one fixture to be counted twice if a later cohort collector combined those rows. This is a pseudo-replication risk for the 30-primary-completed-event gate.
- Updated the existing #933 branch only. Exact final HEAD: `4dc97b5e6bf12d6bb47fa6229cb960d605b47c0f`; base #932 `8ff52f14efbd7ca14836d40e92f47fa83ceadcad`; compare 5 ahead / 0 behind; PR #933 remains OPEN / Draft / mergeable and unmerged.
- The validator now deduplicates within a complete supplied cohort by (Serie A, local Europe/Rome match date, unordered pair of canonical teams). Canonicalization applies the existing Serie A runtime aliases plus the V2 historical `Atalanta BC -> Atalanta` alias. It rejects duplicate fixtures across different event IDs, reversed home/away duplicates, and same-club aliases; it still permits the same clubs to meet on a different match date.
- This is a cohort-integrity check only. The frozen 19-feature order, candidate artifact SHA, training fingerprint, original weights/scaler/imputer, `active_lambda=0`, `shadow_lambda=1`, failed stability gate and prediction math are unchanged.
- Updated the pre-existing artifact-mismatch test fixture to use a genuinely distinct match, then added four regressions for duplicate IDs, reversed/aliased fixture duplicates, same-team runtime aliases, and distinct match dates.
- Exact final-head CI [#45121512759](https://github.com/MaksimBlud/football-ai/actions/runs/45121512759) is **SUCCESS**: **184 passed**, Python compilation passed, and production `.pkl` diff guard passed. This result applies only to exact HEAD `4dc97b5e...`; no result is inferred for intermediate commits.

**Free-source and rights recheck**
- PR #906's Football-Data manifest remains `V2_FROZEN_INFERENCE_SCOPE_UNRESOLVED`: automated source capture false, inference false, AI training false, provider-issued inference license false, authorization null. The official policy page was reported updated 2026-11-20; the two-download ceiling is not authorization for this automated AI workflow.
- PR #907's Global Football Data Lake audit remains HOLD: aggregate CC-BY-4.0 metadata does not clear mixed API-Football/Football-Data upstream rights; field-level lineage is unresolved; source-before-quote is unproven; `stats_fetched_at` is null for 74% of rows; `known_at` is derived kickoff+105 minutes, not a provider-observed timestamp; no raw source bytes or project SHA archive exists.
- PR #886's 11footy audit remains HOLD: declared CC BY-NC 4.0, upstream report/feed providers unidentified, signature not independently verified, no per-row first-observation time, and exact 19-feature field-definition parity/per-fixture coverage unverified.
- PR #883's Lega report audit remains HOLD: no express written consent for extraction, internal ML/inference, private raw retention or commercial use. No source asset was downloaded or used in any of these audits.

**Supabase — read-only pre-match metadata only**
- Repeated the strict timestamp-only aggregation on `public.odds_snapshots`: **3,915** strict pre-kickoff rows / **327** events / **9** leagues.
- A separate future-only query returned **0** future strict rows and **0** future strict events. Latest strict pre-match snapshot remains **2026-10-13 14:48:53 UTC** (Serie A).
- No scores, results, settlements or protected outcome columns were selected.

**Remaining blockers and non-actions**
- Root workflow hold PR #781 remains at exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, 8/8 CI SUCCESS, OPEN / Ready for review; it is not active on main until owner manual merge.
- Original Forward source-first fix remains in #884 and Current-Form fail-closed source-before-quote fix remains in #913; neither is integrated into main.
- No new prospective predictions, no source download/use, no provider/API request, no paid API call, no Supabase write/DDL, no protected 2026/27 outcome read, no production `.pkl` change, no weight/feature/threshold change, no main update, no merge, no schedule change, and no other-agent setting change occurred.
- The 30-primary-completed-event gate remains CLOSED; independent Brier/LogLoss evaluation against the market is still unavailable. Do not infer model superiority.


### 2026-11-23 06:08 UTC — exact final CI and re-read of main Original Forward runtime

**Final strict V2 cohort-identity CI**
- Added two final regressions to the existing #933 branch: the same fixture remains a duplicate when provider kickoff times differ but the Europe/Rome local match date is the same; the V2 historical alias map used for deduplication must remain identical to the original feature manifest's alias map.
- Exact final #933 HEAD: `9fc4fb17dae8d47952983dde0af6b7d006bf3403`; base #932 `8ff52f14efbd7ca14836d40e92f47fa83ceadcad`; 6 ahead / 0 behind; OPEN / Draft / mergeable; not merged.
- Exact-head CI [#45122002023](https://github.com/MaksimBlud/football-ai/actions/runs/45122002023) is **SUCCESS**: **186 passed**, compilation passed, and the production `.pkl` diff guard passed.
- The frozen candidate JSON blob is byte-identical on main and #933 (`ac1303f6b096664983fbf52443bd0a381b23ba21)); candidate SHA remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098); 3,799 rows; 19 features; 20x2 weights; active lambda 0; shadow lambda 1; stability gate false. The original feature-builder blob remains `401b3a0893371bfa4a488ec92a4a54af2678c8f7`.

**Re-read of actual main-branch V2 runs from 2026-11-22**
- Current-Form Source Capture [#45028522381](https://github.com/MaksimBlud/football-ai/actions/runs/45028522381): 110 completed primary-event identities, 10 historical source files plus 1 current-season file, zero paid calls, zero Supabase writes, zero outcome scoring. GitHub artifact ID `14756317850`; artifact ZIP SHA-256 `cf96923f75616bd2d045997e89863c0a32b7b453736a90cc353447c2c7dae955`.
- Free Real-Quote Diagnostic [#45033051083](https://github.com/MaksimBlud/football-ai/actions/runs/45033051083): 3,800 history rows, **0 diagnostic scored**, 0 rows with all 19 observed features, 0 paid requests, 0 Supabase writes. It uploaded artifact ID `14758338536`, ZIP SHA-256 `42b9a2557490a39e5b376bf425977aa25ec386372ae7a3b4158d77bafc866a11`.
- Original Forward [#45042303864](https://github.com/MaksimBlud/football-ai/actions/runs/45042303864): verified the parent source artifact and SHA, 3,800 historical rows / 10 source files, but `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `paid_provider_calls=0`, `supabase_writes=0). The report artifact was ID `14761239606`, SHA-256 `bc9b763893f3aae87ed2a2c6fe35077344da3b67bf97181861215ace29c2860b`.
- Current-Form Forward [#45042946420](https://github.com/MaksimBlud/football-ai/actions/runs/45042946420): verified source artifact `14756317850` with SHA above; 110 current-season history rows and 3,910 historical rows; `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, `production_or_supabase_writes=0`, `paid_provider_calls=0`. Its report artifact was ID `14762112192`, SHA-256 `9757907b9b72e771c5776362a38440d24441828966883a92e704a6cdf36c2359`.
- These are real main-branch runs, not PR simulations. They confirm no forecasts were captured because no qualifying quotes were present. The uploaded artifacts were inspected only through Actions logs/metadata; no artifact bytes were downloaded or used in this cycle.
- The latest visible V2 scheduled run remains 2026-11-22 16:16 UTC. No 2026-11-23 05:50 UTC Current-Form Source Capture run appeared in the fresh schedule listing. No manual dispatch or schedule change was made.

**Control gap**
- The main-branch capture/forward workflows above ran before the current rights-gate branch was integrated. PR #906's latest Football-Data manifest now says automated source capture is false and authorization is null; #781's workflow hold remains unmerged. Thus main still does not enforce the current internal HOLD. Owner manual merge of #781 (and the rights chain after restack/review) remains the required control; this run did not change main or dispatch/cancel any workflow.

**Supabase and evaluation**
- Read-only pre-match odds metadata remains 3,915 strict rows / 327 events / 9 leagues; future strict rows/events 0; latest strict Serie A snapshot 2026-10-13 14:48:53 UTC.
- The 30-primary-completed-event gate remains CLOSED. No protected outcomes were read. No independent Brier/LogLoss comparison is available, and no V2 superiority claim is justified.
- No Supabase write/DDL, paid provider call, source download/use, production `.pkl` change, candidate/feature/weight/threshold change, main update, merge, schedule change or other-agent setting change occurred in this cycle.


### 2026-11-23 06:10 UTC — exact-head CI correction for source-before-quote child PRs

This corrects the 2026-11-23 01:48 UTC checkpoint, which said the latest #884 SHA lacked independently surfaced exact-head CI. The current exact heads do have successful runs:

- **#884 Original Forward source-first** — HEAD `c38834ec6c2bd0079afca9e63a9ce75a8cd17043`; exact run [#44854473405](https://github.com/MaksimBlud/football-ai/actions/runs/44854473405); Python 3.12: **80 passed**, Python 3.11: **80 passed**; compilation and production `.pkl` diff guards passed.
- **#913 Current-Form fail-closed source-before-quote** — HEAD `23ba2b6b9651f07f819004ab9c2fbd9fc37c641b`; exact run [#44938903345](https://github.com/MaksimBlud/football-ai/actions/runs/44938903345); Python 3.12: **31 passed**, Python 3.11: **31 passed**; compilation and production `.pkl` diff guards passed.
- **#923 atomic source capture / feature-gate clock** — HEAD `2ddef8a7b66324224e5a0d243f364a36109b9420`; [#45069538763](https://github.com/MaksimBlud/football-ai/actions/runs/45069538763) Python 3.12/3.11: **71 passed each**; [#45069538786](https://github.com/MaksimBlud/football-ai/actions/runs/45069538786) Python 3.12/3.11: **58 passed each**. Compilation and production `.pkl` diff guards passed.
- These exact-head successes do not integrate the fixes. #884 remains based on old #879; #913 remains based on #912; #923 remains based on #922. All remain open Draft children requiring ancestry reconciliation after owner HUMAN-MERGE of root #781.

**Documentation checkpoint CI:** PR #839 exact HEAD `f903605c5114ee349863ec494aee46aabed1c58c` is OPEN / Ready for review / mergeable, not merged. Its exact-head commit run list is **8/8 SUCCESS**; V2-specific Frozen Shadow [#45122138210](https://github.com/MaksimBlud/football-ai/actions/runs/45122138210) reports **89 passed** and the production `.pkl` guard passed. The unrelated La Liga prospective run was not inspected or used for V2 conclusions.


### 2026-11-23 06:49 UTC — SportAPI free source audit (HOLD) and fresh control recheck

**New free-source candidate: SportAPI.ai**
- Reviewed only official public pages: Terms updated 2026-11-20, pricing, API documentation, coverage and the Serie A guide. No account or API key was created; no API request or data download was made.
- Free plan advertises all endpoints/leagues; quota is 2,000 requests/day and 14,000/month through 2026-11-30, then 1,000/day and 7,000/month from 2026-12-01. No odds endpoint.
- Official Serie A guide identifies league ID 3 and a 2026/27 example. The reviewed stats schema lists shots, passes, fouls, tackles, saves and yellow cards; events list goals and red/yellow cards; standings include points and goals for/against. Corners are not documented in the reviewed stats/event schemas. Six original V2 features are corner-dependent, so full 19-feature parity is not established. Per-fixture Serie A completeness and free historical depth remain unverified.
- Terms allow use in own websites/apps/analysis/products and prohibit raw-feed resale, but do not expressly resolve internal ML training/inference or private raw-response retention. Upstream providers/field-level rights are not identified. `updated_at` is documented as UTC but is not defined as per-field first-observed/correction time. Decision: **HOLD_NO_INTEGRATION** pending written rights, full feature coverage, retention and timestamp clarification.
- Audit manifest: `research/source_rights/sportapi_20261123.json`; offline contract tests: `tests/test_serie_a_v2_sportapi_source_audit.py`. No original model/feature/weight change.

**Fresh repository and runtime control check**
- GitHub main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; Branch API reports `protected=false` and `protection.enabled=false`. This is a concrete control gap: #781's hold is still not active on main.
- #781 exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`: 8/8 PR-triggered runs SUCCESS, including 113 Frozen V2 Shadow tests and 59 Recovery tests. OPEN / Ready for review / mergeable; HUMAN-MERGE only.
- #933 exact HEAD `9fc4fb17dae8d47952983dde0af6b7d006bf3403`: exact run #45122002023 SUCCESS, 186 tests, production `.pkl` diff guard PASS; OPEN / Draft, stacked on #932.
- #839 prior HEAD `533022658378b4716afafa0f12eb47ca816a1854`: 8/8 exact-head PR runs SUCCESS, including 89 Frozen V2 Shadow tests. This new audit commit will require its own exact-head CI.
- Original Forward source-first #884 and Current-Form fail-closed source-before-quote #913 remain open children, not integrated. Their exact offline validations remain #44854473405 (80 tests per Python 3.11/3.12) and #44938903345 (31 per Python 3.11/3.12), respectively. #923 atomic source capture remains on its separate #919→#923 chain.

**Read-only Supabase pre-match ledger**
- Rechecked only `public.odds_snapshots` using `snapshot_time_utc < commence_time_utc`, `created_at < commence_time_utc`, and `snapshot_time_utc <= created_at`.
- All nine leagues: 3,915 strict rows / 327 events; 0 future strict rows/events. Latest strict snapshot remains 2026-10-13 14:48:53 UTC (Serie A).
- No scores, results, settlements or protected outcomes were selected.

**Non-actions**
No main update, merge, Supabase write/DDL, provider/API request, source download, paid API call, inference, refit, threshold tuning, production `.pkl` change, candidate/feature/weight change, protected outcome read, schedule change or other-agent setting change. The 30-primary-completed-event evaluation gate remains CLOSED; no independent Brier/LogLoss result or V2 superiority claim exists.


### 2026-11-23 17:31 UTC — Original V2 source-provenance and rights-restack exact-head CI

**Fresh repository state**
- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` blob remains `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`. This main document still does not contain the current Nov 23 runtime entries; this note is on the open documentation PR #839 only.
- Re-read the original V2 protocol and frozen candidate on main. Candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; 3,799 training rows; exact 19-feature order; 20x2 weights; active lambda 0; shadow lambda 1; stability gate false. No candidate bytes, weights, feature order or thresholds changed.

**Source provenance / direct-access restack**
- [PR #944](https://github.com/MaksimBlud/football-ai/pull/944), exact HEAD `12f9df3b2df07dbf192292af5ac2dc7edb00fa83`, is a Draft child of #943. Exact run [#45213354517](https://github.com/MaksimBlud/football-ai/actions/runs/45213354517) succeeded on Python 3.11 and 3.12: 113 tests passed on each; compilation and production `.pkl` diff guard passed.
- [PR #945](https://github.com/MaksimBlud/football-ai/pull/945) is a Draft child of #944. Its first exact-head CI exposed six stale synthetic quote fixtures because the newly enforced market contract requires `created_at`. Only three test fixtures were corrected to supply an offset-aware persistence time one second after the quote; no production logic or frozen V2 contract was weakened.
- Final #945 HEAD: `8517d0d39879ed2564de3ca8d7ff003f10f4dd46`. Exact PR run [#45228090869](https://github.com/MaksimBlud/football-ai/actions/runs/45228090869) and push run [#45228080028](https://github.com/MaksimBlud/football-ai/actions/runs/45228080028) both succeeded: **181 tests passed on Python 3.11 and 181 on Python 3.12**, compilation passed, production `.pkl` guard passed. #945 remains OPEN / Draft / HUMAN-MERGE, based on #944; no merge occurred.
- #945 carries the source-first/private-artifact chain plus separate source-capture, frozen-inference and training-rights checks, and strict quote persistence ordering. The checked-in Football-Data manifest says automated source capture=false, frozen inference=false, AI training=false, provider-issued inference license=false, authorization=null. The repository is public, while source archives require private storage. Thus this is a fail-closed control stack, **not permission to collect or infer**.

**Actual main runtime / control gap**
- Main `.github/workflows/serie-a-v2-forward-preview.yml` still has its 08:08 UTC schedule and workflow_run trigger after a successful manually dispatched Serie A Odds Snapshots workflow. Main `serie_a_v2_forward_capture.py` still reads saved quotes before discovering/verifying the source archive in its current `main()` path. The source-first and rights fixes are in the open #938–#945 ancestry, not on main.
- Fresh scheduled Current-Form Source Capture run [#45217596300](https://github.com/MaksimBlud/football-ai/actions/runs/45217596300), 2026-11-23 16:32 UTC, completed SUCCESS. Only job/step metadata was inspected; the artifact listing returned no artifacts, and no artifact bytes were downloaded or opened. This is the separate current-form cohort, not evidence for the original old-season-only V2 cohort and not admissible prospective evidence. Because the current rights manifest denies automated source capture, this run does not clear the rights HOLD.
- Root workflow HOLD [#781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review at `5552bec363ae72ad7aef04c598d2ce861f33eb42`; it has not been integrated. HUMAN-MERGE remains mandatory. The branch-protection endpoint could not be read in this cycle (GitHub API returned 403 for the connected integration), so no new claim about branch protection is made.

**Supabase — read-only pre-match odds only**
- Strict filter: `snapshot_time_utc < commence_time_utc`, `created_at < commence_time_utc`, and `snapshot_time_utc <= created_at`.
- Aggregate: **3,966** rows total; **3,915** strict pre-match rows across **327** events and **9** leagues. Serie A: **625** total rows, **620** strict rows, **63** distinct events; latest strict Serie A snapshot remains **2026-10-13 14:48:53 UTC**.
- A separate rolling-24-hour future Serie A quote query returned **0 rows / 0 events**. No scores, results, settlements or protected 2026/27 outcome columns were selected.

**Scientific status / non-actions**
- The preregistered 30-primary-completed-event outcome-read gate remains CLOSED; no protected 2026/27 target outcomes were read. No independent Brier/LogLoss comparison exists; no V2-over-market superiority claim is justified.
- No Supabase writes/DDL, paid provider request, source-artifact download/use, production `.pkl` modification, feature/weight/threshold change, main update, merge, schedule change or other-agent setting change occurred.


### 2026-11-23 — Original V2 separate source-capture scope guard; exact-head CI

**Fresh main / frozen-candidate verification**
- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; Branch API reports `protected=false`. Main `PROJECT_CONTINUITY.md` blob is `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b` (6,152 lines); this new checkpoint is appended only on this open #839 documentation branch.
- Main Original Forward source file blob is `5db02cbd1367ed25b994b152acf371421859a014`. Static re-read confirms its current `main()` reads saved quote metadata before discovering/verifying source archives. The source-first and rights changes below are not on main.
- Frozen candidate JSON blob on main: `ac1303f6b096664983fbf52443bd0a381b23ba21`; candidate SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; 3,799 rows; exact 19 features; 20×2 weights; `active_lambda=0`; `shadow_residual_lambda=1`; stability gate false; research-only true; no 2026/27 outcomes used. The original V2 source blobs remain exactly `market_anchor_1x2_v2_shadow.py=b2770d726ffafe7a3cef706b57d3391063cbfe1b` and `historical_football_signal_lab.py=401b3a0893371bfa4a488ec92a4a54af2678c8f7`. No inference or feature calculation was run.

**New direct-access finding**
- A fresh audit of the exact #945 head `8517d0d39879ed2564de3ca8d7ff003f10f4dd46` found that original Forward required provider-issued frozen-inference permission and private storage, but did not independently require the distinct automated source-capture grant before archive discovery, parent-run metadata reads, or ZIP download.
- This is a real partial-scope bypass: an inference-only authorization could have allowed source-archive access even if automated source capture remained unauthorized. The checked-in rights manifest on the open rights branch currently denies automated capture, frozen inference and AI training; authorization is null. No such access was attempted in this audit.

**New Draft PR #946**
- [PR #946 — enforce separate source-capture rights in original Forward](https://github.com/MaksimBlud/football-ai/pull/946), Draft / OPEN / HUMAN-MERGE only; child of #945.
- Parent #945 HEAD: `8517d0d39879ed2564de3ca8d7ff003f10f4dd46`; exact #946 HEAD: `8c13bb0178b1b7e18b16e2c74ce46cdc70d94ce9`; compare **1 ahead / 0 behind**, merge base is exact parent.
- Adds a rights-only source-capture validator and requires it independently before original-forward archive metadata, parent workflow, ZIP download, caller-supplied archive processing, preflight callbacks and CLI source discovery. The separate inference/private-storage guard remains mandatory; neither scope substitutes for the other.
- Adds offline negative tests for the partial-scope case (inference synthetically allowed, capture denied), proving no input iteration, source metadata/HTTP, archive download, callback, quote/Supabase access or forecast occurs.
- Exact push CI [#45233429006](https://github.com/MaksimBlud/football-ai/actions/runs/45233429006) and exact PR CI [#45233487016](https://github.com/MaksimBlud/football-ai/actions/runs/45233487016) both completed SUCCESS on HEAD `8c13bb0178b1b7e18b16e2c74ce46cdc70d94ce9`. Python 3.11: **189 passed**; Python 3.12: **189 passed**; compile and production `.pkl` diff guard passed. PR remains Draft and unmerged.
- Parent #945 remains Draft at `8517d0d39879ed2564de3ca8d7ff003f10f4dd46`; exact PR [#45228090869](https://github.com/MaksimBlud/football-ai/actions/runs/45228090869) and push [#45228080028](https://github.com/MaksimBlud/football-ai/actions/runs/45228080028) passed **181 tests on each of Python 3.11 and 3.12**, compile and production `.pkl` guard. #944 remains the preceding provenance parent. None of #938–#946 is integrated into main.

**Root HOLD / live main control**
- [Root HOLD #781](https://github.com/MaksimBlud/football-ai/pull/781) is OPEN / Ready for review / mergeable at exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; it is not merged and its default-deny workflow hold is not active on main.
- All **8/8 exact-head runs** report SUCCESS on that SHA: Product [#45108795827](https://github.com/MaksimBlud/football-ai/actions/runs/45108795827), Recovery [#45108795897](https://github.com/MaksimBlud/football-ai/actions/runs/45108795897), Serie A [#45108795789](https://github.com/MaksimBlud/football-ai/actions/runs/45108795789), Bundesliga [#45108795785](https://github.com/MaksimBlud/football-ai/actions/runs/45108795785), Frozen V2 Shadow [#45108795798](https://github.com/MaksimBlud/football-ai/actions/runs/45108795798), Eredivisie [#45108795794](https://github.com/MaksimBlud/football-ai/actions/runs/45108795794), Ligue 1 [#45108795793](https://github.com/MaksimBlud/football-ai/actions/runs/45108795793), and Research [#45108795804](https://github.com/MaksimBlud/football-ai/actions/runs/45108795804). Frozen V2 Shadow log: **113 passed**; Recovery log: **59 passed**; recovery rebuild/proof/upload steps were skipped under default deny and production hash guard passed.
- Manual HUMAN-MERGE of #781 remains the immediate safety priority. Do not merge #946 or the descendants before the root hold and exact dependency chain are reviewed. No merge/main update was performed.

**Read-only Supabase pre-match inventory**
- Query selected only `public.odds_snapshots` league/event identity and quote/kickoff/persistence timestamps, with strict conditions `snapshot_time_utc < commence_time_utc`, `created_at < commence_time_utc`, and `snapshot_time_utc <= created_at`.
- Result: **3,966** total rows; **3,915** strict pre-match rows; **327** distinct events; **9** leagues; **0** future strict rows / **0** future strict events.
- Serie A: 625 total rows, 620 strict pre-match rows, 63 events. Latest strict Serie A snapshot: **2026-10-13 14:48:53.042620 UTC**.
- No score, result, settlement or protected outcome columns were selected. No Supabase write/DDL occurred.

**Scientific status and non-actions**
- The preregistered 30-primary-completed-event gate remains **0/30 / CLOSED**. No protected 2026/27 outcomes were read, and no independent Brier Score / LogLoss comparison is available. No V2-over-market superiority claim is justified.
- No provider/source request or download, paid API request, Supabase write/DDL, inference, training/refit, threshold tuning, production `.pkl` change, candidate/feature/weight change, main update, merge, schedule change or other-agent setting change occurred.
- `active_lambda=0` remains the market; `shadow_lambda=1` remains research-only; NO_BET and frozen gates remain unchanged.


### 2026-11-23 18:53 UTC — correction: main Free Real-Quote Diagnostic still downloaded and publicly archived source after the internal HOLD

**Exact live main run**
- Re-read the current main workflow and the latest scheduled run metadata/logs. Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; workflow `.github/workflows/serie-a-v2-free-real-quote-diagnostic.yml`.
- Actual run [#45233225104](https://github.com/MaksimBlud/football-ai/actions/runs/45233225104), event `schedule`, main branch, exact main SHA above, completed SUCCESS on 2026-11-23 17:57:39–17:58:36 UTC. Job [#137898029840](https://github.com/MaksimBlud/football-ai/actions/runs/45233225104) completed every step successfully.
- Offline regressions: **53 passed**. The live step then fetched Football-Data.co.uk CSV history and wrote an artifact. Log summary: **3,800 history rows**, 19 frozen feature slots, **0 quoted fixtures**, **0 diagnostic scores**, 0 rows with all 19 observed, 0 paid-provider requests, and 0 Supabase writes. With zero quotes, `quotes_with_source_observed_after_quote=0` is vacuous; this run does **not** demonstrate source-before-quote for any event and is not a V2 forecast.
- Artifact metadata: ID `14845759695`, 425,066 bytes, SHA-256 `fa2cd29f5b6f8c7155f3d8081764aed2f653df20f05bcc35a281bdc788455a37`, created 2026-11-23 17:58:33 UTC, 90-day retention. The upload log says **11 files** (diagnostic plus 10 raw source CSVs). The repository is public, so this Actions artifact is accessible to repository readers. Only Actions logs/metadata were inspected here; artifact bytes were not downloaded or opened.
- This is an actual main-branch source download and public artifact upload despite the current internal Football-Data manifest on the open rights branch explicitly setting automated source capture=false, frozen inference=false, AI training=false, and authorization=null. Main does not yet contain those guards.
- This corrects the earlier non-actions statement in the immediately preceding checkpoint: after the 17:57 UTC main run, it is no longer accurate to say that no source download/use occurred on main. The download/upload was performed by the already-existing main workflow, not by this research run. No additional source request or artifact download was made during this audit.
- Root HOLD [#781](https://github.com/MaksimBlud/football-ai/pull/781) remains the urgent owner action: OPEN / Ready for review, exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, 8/8 exact-head CI SUCCESS, not merged. Its default-deny step and artifact-upload guards are not active on main until HUMAN-MERGE. Do not dispatch or manually rerun the live workflow; do not change schedules. Do not delete or rewrite the existing artifact as part of this research run.
- Supabase was not written. The separate read-only pre-match ledger query remains 3,915 strict rows / 327 events / 9 leagues and 0 future strict rows/events; no score/result/settlement columns were selected. The 30-primary-completed-event outcome gate remains CLOSED; no protected target outcomes were read; no independent Brier/LogLoss result exists.


**Existing source-download budget work found; do not duplicate**
- Open Draft [PR #705](https://github.com/MaksimBlud/football-ai/pull/705), HEAD `f3e7451ee9cebc9280a8f86421a509d9bc177da0`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`, already contains a shared public-source budget guard. It reserves a metadata-only GitHub Actions marker before download, serializes both approved source workflows under one concurrency group, and enforces one attempt per workflow per 170 hours (at most two attempts across the two listed workflows in any seven-day span). It uses GitHub Actions metadata only, not Supabase or match outcomes.
- Exact-head CI on #705: **8/8 SUCCESS**, including dedicated budget tests [#42071252036](https://github.com/MaksimBlud/football-ai/actions/runs/42071252036), Frozen V2 Shadow [#42071252238](https://github.com/MaksimBlud/football-ai/actions/runs/42071252238), and the product/research/league PR validations listed on that exact SHA.
- Scope caution: #705 modifies both the original Free Real-Quote Diagnostic and the separate Current-Form Source Capture workflow. This task remains strictly original `MARKET_ANCHOR_1X2_V2`; do not blindly merge/restack its current-form changes or change that workflow's settings. The original-V2 diagnostic portion can be considered after the root HOLD and provider-rights chain are resolved. #705 predates the 2026-11-20 policy change and does **not** replace the newer source-capture/inference/privacy rights guards.
- #705 is still OPEN / Draft and not on main. The 2026-11-23 17:57 main diagnostic run above therefore had no active budget marker/guard. Do not repeat a separate implementation of the same two-workflow budget mechanism.


### 2026-11-23 19:54 UTC — correction: current-form source and forward artifacts are present

**Exact current-form source run and artifact metadata**
- Source workflow [#45217596300](https://github.com/MaksimBlud/football-ai/actions/runs/45217596300), event `schedule`, main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`, ran 2026-11-23 16:32:08–16:33:11 UTC. Job `137842843129` completed SUCCESS; 19 focused tests passed.
- The run summary reports 10 historical CSVs plus one current-season CSV (`source_file_count=11`), 3,919 historical match rows, 119 current-season prior-day rows, and **110 completed primary fixture identities** for the outcome-free feature-input gate. `target_outcomes_scored=false`; no target outcome values were read. The 110 metadata identities do not satisfy or open the separate evaluation gate.
- Artifact ID `14839276758`, 440,550 bytes, SHA-256 `2a6cb4902da93c4d15050ba9407543a19bc32c68c3f1f5c4ebe07202bb8c7bd9`, created 16:33:07 UTC, 90-day retention. Upload log says 12 files (11 source files plus accompanying capture metadata/report). Artifact bytes were not downloaded or opened.

**Exact current-form forward run**
- Follow-up [#45217802275](https://github.com/MaksimBlud/football-ai/actions/runs/45217802275), triggered by the successful source workflow, completed 16:33:16–16:33:53 UTC. Job `137843578402` completed SUCCESS; **53 tests passed**.
- Its log verifies source artifact `14839276758` and SHA above, parent run `45217596300`, main head SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`, source observation `2026-11-23T16:33:05.648572Z`, archive creation `16:33:07Z`, parent completion `16:33:11Z`, and verification at `16:33:46.945356Z`. This proves source/archive/parent integrity for the capture, but **quotes_seen=0 and current-form shadow forecasts=0**; no quote-level source-before-quote event was tested.
- The follow-up artifact is ID `14839356793`, 441,723 bytes, SHA-256 `946a440f135cbf69668ea175361227e965eb3040443e61dc070cf4547b9505fd`. Its bytes were not downloaded or opened.
- This corrects the earlier 17:31 checkpoint's statement that the source-run artifact listing returned no artifacts: the artifact is present in the current Actions metadata and the successful job log. The earlier statement is superseded; no archive bytes were inspected.

**Rights and hold interpretation**
- Both workflows ran on public main before the root HOLD was merged. The provider-rights restack #945/#946 still explicitly denies automated source capture and frozen inference; these successful runs do not grant permission and are not admissible prospective V2 forecasts.
- Root [#781](https://github.com/MaksimBlud/football-ai/pull/781) is the existing exact hold for the current-form source capture, current-form forward, original forward, free diagnostic and recovery workflows. Its exact HEAD remains `5552bec363ae72ad7aef04c598d2ce861f33eb42`, 8/8 PR-triggered checks SUCCESS, OPEN / Ready for review. Its patch gates all five live source/quote steps and all associated artifact uploads while preserving offline tests and existing schedules. It remains HUMAN-MERGE only; no main update was made.
- Branch API still reports `protected=false`; no branch-protection setting was changed.

**Read-only pre-match ledger recheck**
- SELECT-only query against `public.odds_snapshots`, using strict `snapshot_time_utc < commence_time_utc`, `created_at < commence_time_utc`, and `snapshot_time_utc <= created_at`: **3,966** total rows, **3,915** strict pre-match rows, **327** events, **9** leagues, **0** future strict rows/events. Latest strict Serie A snapshot remains `2026-10-13 14:48:53.042620 UTC`.
- No score/result/settlement columns were selected; no Supabase write/DDL occurred.

**Binding scientific state**
- Original frozen candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 3,799 training rows, exact 19-feature order, 20×2 weights, `active_lambda=0`, `shadow_lambda=1`; no inference or feature calculation was run in this checkpoint.
- The preregistered 30-primary-completed-event outcome gate remains **0/30 / CLOSED**. No protected 2026/27 outcome was read; no independent Brier/LogLoss result exists; no V2-over-market superiority claim is justified.
- No source download or artifact bytes were fetched by this audit, no paid API, no Supabase write/DDL, no model/weight/feature/threshold change, no production `.pkl` change, no main update, no merge, no schedule or other-agent setting change.


### 2026-11-23 — clarification: current-form feature history is distinct from target-outcome embargo

- Static re-read of main `serie_a_v2_current_form_source_capture.py` blob `9f48a4a6e78d5d7ffa193ec6f24b394162f36ab4` confirms that the current-season CSV validator requires and reads `FTHG`, `FTAG`, `FTR`, `HC`, `AC`, `HY`, `AY`, `HR`, and `AR` for completed prior-day rows. Thus the 119 rows in source run #45217596300 are not merely fixture identities; the source archive contains completed 2026/27 statistics/results intended as lagged feature history.
- Separately, the Supabase feature-source gate query in that script selects only `match_date,home_team,away_team` from `league_finished_results`; it does not select score/result columns from Supabase. The current-form forward run #45217802275 verified the source archive but had `quotes_seen=0`, `v2_current_form_shadow_captured=0`, and `target_outcomes_read/scored=false`. No prospective forecast target outcome was evaluated.
- Do not conflate the current-form **feature-input gate** (110 fixture identities / 119 prior-day CSV rows) with the separate preregistered **30-primary-completed-event evaluation gate** (still 0/30 / CLOSED). The source archive has not been opened by this audit, and it must not be used for a forecast or evaluation while source rights and the exact scope of the protected-outcome embargo remain unresolved.
- Conservative interpretation: if the user's embargo means no 2026/27 completed score/result data may be accessed even as lagged features before the evaluation gate, the existing scheduled source-capture run crossed that stricter boundary. The workflow output's `target_outcomes_read=false` refers only to prospective evaluation targets; it must not be represented as “no 2026/27 results were read” in the broad sense. Keep the root HOLD #781 and provider-rights HOLD in force; no further source artifact access is authorized by this checkpoint.
- This is a correction to terminology and scope, not a model change or a new data admission. No archive bytes were downloaded/opened by this audit; no target evaluation outcomes, score/settlement table values, or Supabase score/result columns were read.


### 2026-11-23 20:00 UTC — Soccer Data free-plan source audit

- Added a separate offline-only audit for `Soccer Data`: `research/MARKET_ANCHOR_1X2_V2_SOCCER_DATA_FREE_SOURCE_AUDIT_20261123.md`, `research/source_rights/soccer_data_20261123.json`, and `tests/test_serie_a_v2_soccer_data_source_audit.py`. The research validation workflow now runs this test beside the existing SportAPI rights audit.
- Public docs advertise a $0 Free plan, 50 requests/day, 10/minute, current-season-only, all statistics endpoints, no odds and an API key. Match stats document corners, yellow cards and red cards; results/goals and standings/points are documented. This is schema-level compatibility only: match stats may be unavailable and coverage varies by competition; exact Serie A 2026/27 per-fixture completeness was not checked.
- Terms (30 October 2026) say data belongs to Soccer Data or licensed third parties; grant a non-exclusive/non-transferable licence; permit caching/storage while the account and plan are active and display in own products; prohibit raw-data redistribution; and end the licence when the account/Terms end. The reviewed Terms do not expressly resolve internal ML training/inference or derived-weight retention; upstream identities and field-level rights remain unknown.
- The docs do not establish per-field first-observed/correction timestamps. A future authorized local receipt-time+SHA archive could prove project possession before a quote, not upstream first observation.
- Free is current-season-only and cannot replace the separate Football-Data historical training corpus used by the frozen candidate. Its rights and frozen-weight inference rights remain unresolved.
- Decision **HOLD_NO_INTEGRATION**. No provider account/key, provider API request, source download, provider-specific Supabase read, inference or outcome read was made for this candidate audit. The separate project-level pre-match odds-snapshot audit used SELECT only; no Supabase writes/DDL occurred. Original 19 features and candidate hashes are pinned unchanged.


### 2026-11-23 22:52 UTC — fresh main/runtime, all-league pre-match quote audit, and root-hold status

**Repository and branch state**
- Fresh GitHub repository metadata confirms default branch `main`, public visibility, and unchanged latest main commit `40887ebb215730190d7a6c7a1693373ec4afcdfc` (the latest commit search result remains dated 2026-10-18). Main `PROJECT_CONTINUITY.md` blob is `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b`; it still begins with the 2026-10-18 current-form contract. The current documentation checkpoint is being maintained only on this PR branch.
- Root HOLD [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review / not merged. Exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; all eight exact-head check-runs are completed SUCCESS. The hold is not active on main.
- Private-repository child [PR #879](https://github.com/MaksimBlud/football-ai/pull/879) remains Draft, exact HEAD `02bf0873979551ddd98511df013a27f872893990`, based on #781. Original-forward source-first chain #938 → #939 → #940 → #943 → #944 → #945 → #946 remains open/Draft and dependent on #879/#781. No PR was merged and main was not changed.
- Current documentation PR #839 is updated only on branch `research/v2-runtime-checkpoint-20261115-1354z`; the exact pre-update head was `1b02e852783e54fdfab79edec1f893bebed91e32`. No model, source archive, workflow, production artifact or database file is changed by this checkpoint.

**Actual main-branch Current-Form Source Capture**
- Run [#45217596300](https://github.com/MaksimBlud/football-ai/actions/runs/45217596300), main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`, completed SUCCESS on 2026-11-23.
- Exact job steps: 19 tests passed; the source capture completed. Log reports 10 historical CSVs, 119 completed prior-day 2026/27 rows, 110 unique completed-event identities admitted by the metadata-only feature-input gate, 11 source files, 0 paid provider calls and 0 Supabase writes.
- Public artifact metadata: ID `14839276758`, 440,550 bytes, GitHub SHA-256 `2a6cb4902da93c4d15050ba9407543a19bc32c68c3f1f5c4ebe07202bb8c7bd9`, created `2026-11-23T16:33:07Z`. The current-form source validator reads completed-match statistics including goals/results/cards/corners into the CSV archive; the feature-input Supabase query itself selects only `match_date,home_team,away_team`. These lagged feature inputs are not the separate target-outcome evaluation cohort. As already clarified above, the archive was not downloaded/opened by this audit, and source-rights plus the strict interpretation of the 2026/27 embargo remain unresolved.

**Actual main-branch Current-Form Forward**
- Run [#45257233004](https://github.com/MaksimBlud/football-ai/actions/runs/45257233004), same main SHA, completed SUCCESS at `2026-11-23T20:14:40Z`.
- The actual job completed 53 tests, verified parent source run #45217596300, source artifact #14839276758 and its SHA-256, with source age 13,288 seconds at verification (within the code's 24-hour limit).
- Log values: `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, `paid_provider_calls=0`, `production_or_supabase_writes=0`.
- Despite zero quotes and zero forecasts, the archive step completed and published artifact #14857862796 (441,731 bytes), GitHub digest `sha256:5e9515e6105164a2c3a4421c580c38ec73d29bbdd5b9b2de69c1967bd134c3a8`. This is new evidence that public main still uploads source ZIP bytes on an empty-quote run while the repository is public and the root HOLD/private-storage PRs are unmerged. No artifact bytes were downloaded/opened in this audit.

**Actual main-branch Original Forward**
- Run [#45255423039](https://github.com/MaksimBlud/football-ai/actions/runs/45255423039), same main SHA, completed SUCCESS at `2026-11-23T20:04:28Z`; 71 tests passed.
- It verified the pre-existing old-season source artifact #14845759695 (3,800 historical rows, 10 pre-prospective source files; SHA-256 `fa2cd29f5b6f8c7155f3d8081764aed2f653df20f05bcc35a281bdc788455a37`). It reported `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`, `paid_provider_calls=0`, `supabase_writes=0`, and `eligible_for_frozen_prospective_cohort=false`.
- Its small report/attestation artifact is #14859255542, 1,459 bytes, digest `sha256:aa3c94d7013939c9744db0af4bc6e2cbe8c385cf2eb125e7ce7f855c155829a8`. No forecast or quality metric resulted.

**Fresh read-only Supabase pre-match-only audit**
- Read only `public.odds_snapshots` timestamp/event/league fields; no result, score, settlement or payload columns were selected.
- Strict definition: `snapshot_time_utc < commence_time_utc`, `snapshot_time_utc <= created_at`, and `created_at < commence_time_utc`.
- Across nine leagues: 3,966 rows total; 3,915 strict pre-match rows; 327 distinct events with strict pre-match snapshots; **0 future events** with a strict pre-match snapshot. Latest strict snapshot remains Serie A `2026-10-13T14:48:53.042620Z`; latest EPL is `2026-10-09T15:25:57.102061Z`. No fresh saved pre-match quotes exist for a prospective V2 capture.

**Frozen model and gate status**
- Original candidate SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 3,799 training rows, exact 19-feature contract, 20×2 original weights, `active_lambda=0`, `shadow_lambda=1`; unchanged.
- Stability gate remains FAILED; target-outcome gate remains **0/30 / CLOSED**. No Brier/LogLoss independent evaluation and no V2-over-market claim.
- No target evaluation outcomes were read/scored; however, the current-form feature archive includes completed 2026/27 result/statistics rows as lagged features. Do not describe this as “no 2026/27 results accessed” in the broad sense. No archive bytes were opened by this audit.
- No paid odds API request, Supabase write/DDL, model inference/refit, threshold tuning, production `.pkl` change, schedule/other-agent change, main update, merge, promotion or bet.

**Next safe step:** HUMAN-MERGE review of #781 first; after it is manually integrated, re-read fresh main and prove every live source/quote step and artifact upload is skipped. Then revalidate the private-storage and source-first child chain on the new base. Do not access the current-form archive or initiate any new provider capture while the rights/embargo HOLD remains.

### 2026-11-23 23:52 UTC — fresh main ordering, live-action recheck, and strict pre-match odds inventory

**Fresh repository and PR state**
- GitHub repository metadata and commit lookup confirm the default branch is still public `main` at `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The main-branch `PROJECT_CONTINUITY.md` blob is `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b` and still begins with the 2026-10-18 entry; this checkpoint remains on the research branch only.
- Root live-access HOLD [#781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / not merged, exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, base `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The eight runs returned for that exact commit all completed SUCCESS: #45108795827, #45108795897, #45108795789, #45108795785, #45108795798, #45108795794, #45108795793, #45108795804. The HOLD therefore remains a reviewed change, not an active main-branch control.
- Private-artifact child [#879](https://github.com/MaksimBlud/football-ai/pull/879) remains Draft at `02bf0873979551ddd98511df013a27f872893990`, based on #781's exact HEAD. Original-forward source-first restack [#938](https://github.com/MaksimBlud/football-ai/pull/938) remains Draft at `14d765ca2b55e939d9ab5790abbbecd3a29f2614` on #879. Rights/provenance descendant [#946](https://github.com/MaksimBlud/football-ai/pull/946) remains Draft at `8c13bb0178b1b7e18b16e2c74ce46cdc70d94ce9`; its exact-head offline validation run #45233487016 passed on Python 3.11 and 3.12 (189 tests each). No dependency was merged.
- Documentation PR [#839](https://github.com/MaksimBlud/football-ai/pull/839) is still OPEN at exact HEAD `95bdc24bc272719e1efb7ef18b3aec688c005c7a`. Eight exact-head workflows completed SUCCESS: #45284172683, #45284172839, #45284172879, #45284172778, #45284172672, #45284172757, #45284172988, #45284172724.

**Main-branch code-order findings (read-only inspection)**
- In main `serie_a_v2_forward_capture.py`, `main()` reads saved upcoming quotes at line 279 before discovering source archives at line 280 and calling `prepare_forward_capture` at line 281. Thus the main-branch original-forward entrypoint does not establish source-before-quote ordering. The corrected source-first CLI implementation is still only in #938 and descendants; it is not on main.
- In main `serie_a_v2_current_form_forward_capture.py`, source archive discovery/verification occurs before the saved-quote reader, but the verified ZIP is written to the workflow artifact directory. The main workflow's upload-artifact step still uses `if: always()` (workflow lines 69–80); the source/quote live steps and artifact publication have not received #781's default-deny gate on main. The current-form workflow therefore still exposes source ZIP artifacts while the repository remains public.
- The #781 diff adds `MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=false` to the five held workflows, conditions live steps on explicit `true`, and conditions artifact upload on successful live steps plus that flag. This is the right root control to review manually; it has not been integrated.

**Latest real pre-match workflow evidence (main SHA above)**
- Current-form source capture [run #45217596300](https://github.com/MaksimBlud/football-ai/actions/runs/45217596300) completed SUCCESS. Its actual log reports 19 tests passed, ten old-season CSVs, 119 completed prior-day current-season rows, 110 unique completed-event identities at the metadata-only feature-input gate, 11 source files, zero paid provider calls and zero Supabase writes. Artifact #14839276758, 440,550 bytes, SHA-256 `2a6cb4902da93c4d15050ba9407543a19bc32c68c3f1f5c4ebe07202bb8c7bd9`.
- Current-form forward [run #45257233004](https://github.com/MaksimBlud/football-ai/actions/runs/45257233004) completed SUCCESS with 53 tests. It verified the parent run and source artifact above; source age at verification was 13,288 seconds. It reported `quotes_seen=0`, `v2_current_form_shadow_captured=0`, `target_outcomes_read=false`, `target_outcomes_scored=false`, zero paid calls and zero Supabase writes. Nevertheless it published artifact #14857862796 (441,731 bytes), SHA-256 `5e9515e6105164a2c3a4421c580c38ec73d29bbdd5b9b2de69c1967bd134c3a8`.
- Original forward [run #45255423039](https://github.com/MaksimBlud/football-ai/actions/runs/45255423039) completed SUCCESS with 71 tests. It verified 3,800 historical rows from ten pre-prospective files, but `quotes_seen=0`, `future_quotes_checked=0`, `v2_diagnostic_previews_captured=0`, `forecasts_created=0`, and zero paid calls/Supabase writes. No forecast-quality evidence resulted.
- The current-form source workflow log reports 119 current-season completed rows as lagged feature history. This audit did **not** download or open the source ZIP or inspect those rows. The separate target-outcome evaluation gate remains CLOSED; no target outcomes were read or scored here. Keep the feature-input metadata gate distinct from the 30-primary-completed-event target-outcome gate.

**Fresh read-only Supabase odds audit**
- Project `besxwboamipygwvrsblz`; SELECT only from `public.odds_snapshots`. Selected only league, event ID and snapshot/created/kickoff timestamps; no score, result, settlement or payload columns.
- Strict pre-match predicate: `snapshot_time_utc < commence_time_utc`, `created_at >= snapshot_time_utc`, and `created_at < commence_time_utc`.
- Across nine leagues: **3,966** snapshots total, **3,915** strict pre-match snapshots, **327** distinct events with strict pre-match snapshots, and **0** future events with a strict pre-match snapshot.
- Strict pre-match rows by league: Bundesliga 394/404 (35 events); EPL 1,135/1,151 (70); Eredivisie 410/412 (39); La Liga 798/806 (52); Ligue 1 387/394 (35); Primeira Liga 9/9 (9); RPL 153/156 (15); Serie A 620/625 (63); Turkey Super Lig 9/9 (9). Latest strict snapshot: Serie A `2026-10-13T14:48:53.042620Z`; EPL `2026-10-09T15:25:57.102061Z`. No new prospective pre-match quote is available.

**Supabase security advisory (not remediated)**
- The live schema/advisor reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. Supabase classifies these tables as exposed to `anon` and `authenticated` roles. `public.odds_snapshots` has RLS enabled.
- No DDL was executed. Supabase's suggested enablement statements are recorded for owner review only; policies must be designed before enabling RLS because doing so without policies can break legitimate access:

```sql
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.league_prediction_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.epl_ai_market_pair_ledger ENABLE ROW LEVEL SECURITY;
```

**Frozen V2 and non-actions**
- Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; original 19-feature contract and 20×2 weights unchanged; `active_lambda=0` remains the market, `shadow_lambda=1` remains research-only. Stability gate remains FAILED and prospective target-outcome gate remains **0/30 / CLOSED**. No Brier/LogLoss prospective comparison or superiority claim.
- No archive bytes or protected target outcomes were opened; no paid API call, Supabase write/DDL, inference, refit, threshold tuning, production `.pkl` change, main update, merge, promotion, bet, schedule change or other-agent change occurred.

**Next safe action:** HUMAN-MERGE review of #781 first. After a human integration, re-read fresh main and verify all five held workflows skip source/quote access and artifact upload. Only then rebase the private-repository/source-first chain and continue offline V2 verification. Do not initiate source capture or quote access while rights and embargo remain unresolved.


### 2026-11-24 00:52 UTC — incumbent comparator identity and provider-rights gate

**Fresh main and repository control**
- Re-read GitHub default branch and commit API: `main=40887ebb215730190d7a6c7a1693373ec4afcdfc`; main `PROJECT_CONTINUITY.md` blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b` still contains the October 18 checkpoint. The branch API reports `protected=false`; repository visibility is `public`.
- Main does not contain `market_anchor_v2_source_rights.py`, `market_anchor_v2_source_capture_rights.py`, or `research/source_rights/football_data_co_uk.json` (404 at main). Its original forward file remains the older blob `5db02cbd1367ed25b994b152acf371421859a014`. Main workflow `.github/workflows/serie-a-v2-free-real-quote-diagnostic.yml` remains blob `60bd304153e5c731ff6246c76fe2f3ace1bc0dcb`, with Supabase secrets available to the job and an unconditional `if: always()` source-artifact upload. The current-form source and forward workflows also still publish artifacts under `if: always()`.
- Root default-deny [#781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN, exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`; all eight workflow runs tied to that exact SHA completed SUCCESS. This is not active on main until HUMAN-MERGE.

**Provider rights — hard stop, not a scheduling problem**
- On the original-forward rights branch [#946](https://github.com/MaksimBlud/football-ai/pull/946), exact HEAD `8c13bb0178b1b7e18b16e2c74ce46cdc70d94ce9`, the pinned Football-Data manifest records `research_source_capture_permitted=false`, `research_inference_permitted=false`, `ai_model_training_permitted=false`, `rights_status=V2_FROZEN_INFERENCE_SCOPE_UNRESOLVED`, and `authorization=null`. The official policy pages were reviewed on 2026-11-21 and displayed an update date of 2026-11-20. The source-capture and inference guards fail closed; the two-downloads-per-week limit is explicitly only a ceiling, not authorization.
- #946's exact-head isolated validation run #45233487016 completed SUCCESS on Python 3.11 and 3.12. No source download, quote read, inference, training, or live call is authorized by this manifest. Do not resume automated Football-Data capture or frozen V2 inference without a provider-issued grant covering the exact use and private retention.

**New evaluation-integrity blocker: incumbent identity and as-of evidence**
- The frozen V2 protocol `experiments/market_anchor_1x2_v2_protocol.json` requires four-way row probabilities: de-vigged market, frozen production incumbent, original candidate, and lambda-1 residual shadow. Its review signal requires both Brier and LogLoss to beat market **and** incumbent.
- The outcome-gate validator at #942 hard-codes `INCUMBENT_MODEL_SHA256=1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5` and requires incumbent probabilities plus `incumbent_generated_at_utc`. The repository tree also contains `football_model_xgboost_elo.pkl`, but this audit did not access the binary and did **not** establish that its digest equals the incumbent SHA. Do not infer that mapping or run the legacy artifact.
- The current capture-row contract and #944 source-provenance writer establish source archive/parent-run chronology, but do not establish a separate incumbent model/input provenance envelope. Therefore the frozen incumbent comparator is not independently as-of verified. This must remain an explicit unresolved blocker; do not use or revive XGBoost to fill it, and do not change the registered V2 protocol or weights to bypass it.
- #942 itself states that existing forward writers did not yet emit its required source-provenance envelope; #944 adds that writer on a separate open branch. No real capture row is presently proven eligible for the 30-event gate.

**Current exact PR/CI checkpoint**
- Documentation PR #839 remains OPEN on this branch. Before this note, exact HEAD was `7b8ed429fd8f76ef5cfa33a3e4ac202cdcc58269`; its eight exact-head runs #45292961786, #45292961581, #45292961625, #45292961791, #45292961703, #45292961558, #45292961651, and #45292962786 all completed SUCCESS. This note is a documentation-only follow-up; new exact-head CI must pass before describing it as validated.
- Read-only `public.odds_snapshots` recheck remains 3,966 total rows, 3,915 strict pre-match rows, 327 event IDs, and zero future events with strict pre-match quotes. No result/score/payload/settlement columns were selected. Target-outcome gate remains 0/30 / CLOSED.

No protected 2026/27 target outcome was read, no production `.pkl` was opened or modified, no paid API was called, no Supabase write/DDL occurred, and no merge, main update, promotion, or bet was performed.


## 2026-11-24 02:52 UTC — Original V2: writer-to-gate integration and fresh main/runtime audit

### Fresh main and active workflow defect
- Repository default branch is `main`, visibility is `public`; current main commit remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Fresh main `PROJECT_CONTINUITY.md` blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b` still starts with the 2026-10-18 checkpoint; it does not carry the current November source-rights/provenance checkpoint.
- Main `serie_a_v2_forward_capture.py` blob `5db02cbd1367ed25b994b152acf371421859a014` still invokes `fetch_saved_upcoming_serie_a_quotes()` before `discover_archives()` and source verification. Main workflow `.github/workflows/serie-a-v2-forward-preview.yml` blob `48ce3b0d8e31c4cf293b94500e9c320047311467` still uploads the source/prediction artifact under `if: always()` and has no default-deny live-access or private-storage gate. Thus the unsafe ordering/public-artifact path remains active on main until the root HOLD chain is manually integrated.

### Current HOLD and dependency chain (all still open; HUMAN-MERGE)
- Root [#781](https://github.com/MaksimBlud/football-ai/pull/781): live PR API exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, Ready for review, base main `40887ebb...`; all eight associated exact-head workflow runs completed SUCCESS (run IDs: 45108795827, 45108795897, 45108795789, 45108795785, 45108795798, 45108795794, 45108795793, 45108795804). The PR body contains an older superseded SHA `3a70a864...`; use the live PR API HEAD above, not that stale body paragraph.
- [#879](https://github.com/MaksimBlud/football-ai/pull/879) remains Draft, child of #781, exact HEAD `02bf0873979551ddd98511df013a27f872893990`; exact validation run #45136504472 SUCCESS.
- [#938](https://github.com/MaksimBlud/football-ai/pull/938) remains Draft, child of #879, exact HEAD `14d765ca2b55e939d9ab5790abbbecd3a29f2614`; exact source-first validation run #45161516045 SUCCESS.
- [#944](https://github.com/MaksimBlud/football-ai/pull/944) remains Draft, exact HEAD `12f9df3b2df07dbf192292af5ac2dc7edb00fa83`; exact CI run #45213354517 SUCCESS (113 tests on Python 3.11 and 113 on 3.12; compile and production-binary diff guard pass).
- [#945](https://github.com/MaksimBlud/football-ai/pull/945) restacks rights, persistence timestamps and outcome holds on #944; remains Draft.
- [#946](https://github.com/MaksimBlud/football-ai/pull/946) remains Draft, exact HEAD `8c13bb0178b1b7e18b16e2c74ce46cdc70d94ce9`; exact source-first validation run #45233487016 SUCCESS, 189 tests on each Python version; no provider request or real source access.
- [#947](https://github.com/MaksimBlud/football-ai/pull/947) is the integration child of #946, exact HEAD `3839f256ac7c910d914d70cb0781cf58b55f82fa`; source-first validation runs #45309141329 (push) and #45309325902 (PR) SUCCESS, and frozen-shadow validation run #45309325907 SUCCESS. The exact Python 3.11 and 3.12 source-first jobs each report **396 passed**; production `.pkl` diff guard passes. #947 calls the actual `build_source_provenance()` writer and passes its returned envelope into `validate_shadow_capture_rows()` using synthetic offline fixtures. This proves writer/validator schema integration only, not live provenance or prediction quality.

### Provider rights and source access
- #946's manifest/guards retain separate denials for automated source capture, frozen inference and AI training; no permission was granted. No source/API request or archive download was performed in this checkpoint.
- Source-before-quote is implemented on the #938/#946/#947 research chain but is not yet on main. Do not run the public main live workflow while it remains unprotected; #781 must be manually reviewed first.

### Fresh Supabase pre-match-only read
Read-only SELECT from `public.odds_snapshots`, using `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= created_at < commence_time_utc`:
- 3,966 total rows; 3,915 strict pre-match rows; 327 distinct events; 0 future strict pre-match rows.
- League strict rows: Bundesliga 394; EPL 1,135; Eredivisie 410; La Liga 798; Ligue 1 387; Primeira Liga 9; RPL 153; Serie A 620; Turkey Super Lig 9.
- `created_at` is mutable by privileged database roles; these counts are temporal consistency evidence, not cryptographic source attestation.
- Supabase table/advisory inspection also reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No remediation DDL was executed; policies must be designed before enabling RLS.

### Frozen model and evaluation status
- Original candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 ordered features; 20×2 weights; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; `active_lambda=0`, `shadow_lambda=1`.
- Historical stability gate remains FAILED: 2/6 dual-metric prior-season wins; Brier CI95 upper +0.003236877; LogLoss CI95 upper +0.006038958; corresponding superiority probabilities 0.6831 and 0.6317. No thresholds or weights changed.
- Prospective outcome gate remains 0/30. Incumbent comparator provenance is unresolved; do not run the legacy XGBoost model, fabricate incumbent probabilities, or read protected 2026/27 outcomes.
- No scientific superiority claim is permitted until the original frozen gate is satisfied and independent Brier/LogLoss evaluation is completed.

No main update or merge, no Supabase write/DDL, no paid provider call, no production `.pkl` access/change, no inference/refit, no schedule/agent changes, and no protected target-outcome read.


## 2026-11-24 — Original V2: post-policy main workflow execution and public artifact evidence

### Official provider policy cross-check and actual main executions
- Official Football-Data data page says the free CSV/Excel data are intended for private individuals only and excludes commercial or data-training products using automated bots/scrapers/AI: https://football-data.co.uk/data
- Official fair-use/contact page says use is for personal betting or academic research via manual download or at most light automated downloads (twice weekly maximum), excludes commercial or AI data-training projects using automated bots/scrapers, and says to assume no permission for other use without a response: https://football-data.co.uk/contact.php
- Current project rights manifest `research/source_rights/football_data_co_uk.json`, blob `96ee20eb99abc2eb73d1ff67d71e1d6fcdeab310`, checked 2026-11-21T11:52:37Z: `research_source_capture_permitted=false`, `research_inference_permitted=false`, `ai_model_training_permitted=false`, `authorization=null`. The two-download ceiling is not an authorization.

Despite that internal HOLD, the unchanged public main (`40887ebb...`) executed the following scheduled runs on 2026-11-23:

- **Current-Form Source Capture** [run #45217596300](https://github.com/MaksimBlud/football-ai/actions/runs/45217596300), SUCCESS, main SHA `40887ebb...`, 16:32:08–16:33:11 UTC. It fetched/archived 10 historical CSVs plus one current-season CSV; the verified downstream manifest reports 3,919 historical rows, 119 current-season rows, 110 outcome-free feature-input-gate fixtures, 11 source files, and source observation at 16:33:05 UTC. Public artifact #14839276758, 440,550 bytes, SHA-256 `2a6cb4902da93c4d15050ba9407543a19bc32c68c3f1f5c4ebe07202bb8c7bd9`.
- **Current-Form Forward-Only Preview** [run #45257233004](https://github.com/MaksimBlud/football-ai/actions/runs/45257233004), SUCCESS, main SHA `40887ebb...`. Its log reports 53 tests passed, 0 saved quotes, 0 V2 current-form shadow captures, target outcomes not read/scored, 0 paid provider calls, and 0 Supabase/production writes. Nevertheless, it uploaded public artifact #14857862796, 441,731 bytes, SHA-256 `5e9515e6105164a2c3a4421c580c38ec73d29bbdd5b9b2de69c1967bd134c3a8`, containing the current-form preview and source bytes.
- **Original Forward-Only Preview** [run #45255423039](https://github.com/MaksimBlud/football-ai/actions/runs/45255423039), SUCCESS, main SHA `40887ebb...`. Its log reports 71 tests passed; source attestation verified 10 historical pre-prospective CSVs / 3,800 matches, but 0 quotes, 0 future quotes checked, 0 V2 previews, 0 paid calls and 0 Supabase writes. It still uploaded public diagnostic artifact #14859255542 (1,459 bytes), SHA-256 `aa3c94d7013939c9744db0af4bc6e2cbe8c385cf2eb125e7ce7f855c155829a8`.

These were scheduled main executions, not initiated by this research run. The current-form source and forward workflow accessed and republished source bytes after the project rights manifest had set automated capture and inference to false. This is a concrete reason to keep live access held. Do not repeat these source reads or downloads. Root PR #781 remains the required manual default-deny workflow hold; #879 adds the private-storage gate and #938/#945/#946 add source-first/direct-entrypoint rights enforcement. No PR was merged and main was not changed here.


## 2026-11-24 04:56 UTC — Original V2: preview-wrapper outcome embargo integrated and exact CI verified

### Fresh main / workflow audit
- Re-read repository metadata, default-branch commit, PROJECT_CONTINUITY.md, the main original-forward script and workflow. Main remains public at 40887ebb215730190d7a6c7a1693373ec4afcdfc; the main continuity file still begins with the October 18 checkpoint.
- Main serie_a_v2_forward_capture.py remains blob 5db02cbd1367ed25b994b152acf371421859a014. It reads saved quote rows at line 278 before discovering/verifying source archives at line 279.
- Main .github/workflows/serie-a-v2-forward-preview.yml remains blob 48ce3b0d8e31c4cf293b94500e9c320047311467; its artifact upload still uses if: always(). The default-deny #781 hold is not active on main.

### New source-first integration child
- [PR #947](https://github.com/MaksimBlud/football-ai/pull/947) remains Draft / HUMAN-MERGE, exact HEAD 3839f256ac7c910d914d70cb0781cf58b55f82fa, based on #946. Its exact source-first push and PR validation jobs each passed 396 tests on Python 3.11 and 3.12; the frozen shadow validation also passed. It joins the actual build_source_provenance() writer output to the actual frozen gate validator using synthetic/offline evidence only.
- Audit found that #947's core market_anchor_1x2_v2_shadow.py already carries the recursive outcome guard, while the separate serie_a_v2_frozen_shadow_preview.py::_guard_outcome_free wrapper still checked only a short top-level set and the nested feature mapping. That left a distinct direct-preview input boundary insufficiently guarded.

### New PR #948 — wrapper embargo hardening
- [PR #948](https://github.com/MaksimBlud/football-ai/pull/948) is Draft / HUMAN-MERGE, a child of #947, exact HEAD 73ce0e91df1f89fde9b8bfc13551b439149e3f0a; base is the exact #947 HEAD above.
- Reuses the core V2 canonical forbidden_outcome_field_match() and frozen alias set; recursively checks nested mappings/lists/tuples in both market and feature inputs; tracks visited container identities.
- Adds synthetic regressions for nested/case variants, raw statistics, Football-Data aliases, generic goal/score containers, punctuation-split aliases, explicit 1X2 winner/draw fields, typed-stat descriptors, valid pre-match labels, nested market payloads, and cyclic benign metadata.
- Exact HEAD CI: push [run #45329765110](https://github.com/MaksimBlud/football-ai/actions/runs/45329765110) and PR [run #45329787667](https://github.com/MaksimBlud/football-ai/actions/runs/45329787667) both 2/2 SUCCESS. Python 3.11 and 3.12 each report 492 passed; compilation and production .pkl diff guard pass. This is offline/synthetic safety evidence, not live data or model-quality evidence.
- PR #948 remains Draft and must not merge independently of #947 and its full rights/source-first parent chain.

### Rights and pre-match database status
- The #946 source-rights manifest remains blob 96ee20eb99abc2eb73d1ff67d71e1d6fcdeab310: automated source capture, frozen inference and AI training are all false; authorization is null. The separate source-capture and inference access guards require provider-issued, scope-specific evidence and fail closed.
- Fresh read-only Supabase SELECT used only league,event_id,snapshot_time_utc,created_at,commence_time_utc from public.odds_snapshots, with snapshot_time_utc < commence_time_utc and snapshot_time_utc <= created_at < commence_time_utc. Result: 3,915 strict pre-match rows, 327 distinct events, 0 future events with strict pre-match quotes. Latest strict snapshot remains Serie A 2026-10-13T14:48:53.042620Z; no target outcomes, score, result or settlement columns were queried.
- Per-league strict pre-match rows: Bundesliga 394; EPL 1,135; Eredivisie 410; La Liga 798; Ligue 1 387; Primeira Liga 9; RPL 153; Serie A 620; Turkey Super Lig 9.

### Frozen model and non-actions
- Original candidate remains SHA-256 a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6, 19 ordered features, 20×2 weights, training fingerprint f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098; active_lambda=0, shadow_lambda=1.
- Historical stability gate remains FAILED (2/6 dual-metric prior-season wins); prospective outcome gate remains 0/30 / CLOSED. Incumbent comparator provenance is still unresolved. No Brier/LogLoss superiority claim.
- No source/provider request or archive download, quote read by this cycle, protected 2026/27 outcome read, paid API call, Supabase write/DDL, inference/refit, threshold tuning, production .pkl change, main update, merge, promotion, bet, schedule change or other-agent change.


### 2026-11-24 04:59 UTC — Clarification: first outcome-read gate versus prospective evaluation gate

- The frozen protocol file (blob 65729e9639720e67624c1481190aa22ae606f151) explicitly sets first_outcome_read_gate.completed_primary_events = 30, with outcome_read_before_gate = false and purpose = diagnostic review only; it is not an activation or production-promotion gate.
- Main Current-Form Source Capture run #45217596300 first queried only match_date, home_team and away_team from public.league_finished_results for Serie A 2026/27. Its metadata-only count was 110 unique completed primary fixtures, above the preregistered threshold of 30. Only after that gate passed did the script download and parse the current-season CSV.
- The main script's REQUIRED_COLUMNS include FTHG, FTAG and FTR, and it parses those result fields plus corners/cards before archiving the raw current-season CSV. The run therefore DID read 2026/27 match outcomes, but only after the preregistered first-outcome-read gate had been met. Its target_outcomes_scored=false log field means no forecast outcomes were scored; it must not be interpreted as proof that no result columns were read.
- This does not open the separate prospective evaluation gate. The latter still requires 30 eligible prospective original-V2 forecasts from the frozen cohort to complete; current count remains 0/30 / CLOSED. No prospective Brier/LogLoss comparison was run.
- The source read remains independently blocked by the provider-rights manifest: automated source capture and inference are false and authorization is null. The old public-main workflow had no integrated rights guard and published artifact #14839276758 (440,550 bytes, SHA-256 2a6cb4902da93c4d15050ba9407543a19bc32c68c3f1f5c4ebe07202bb8c7bd9). Do not repeat this capture; #781 and the private/source-rights chain require HUMAN-MERGE and provider clearance.

## 2026-11-24 — Original V2: immutable workflow pins and free Community-source re-check

### Fresh main and original-forward defect
- Fresh main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`, public and unprotected. Main `PROJECT_CONTINUITY.md` remains blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b` (6,152 lines); this checkpoint is still on the research branch.
- Main `serie_a_v2_forward_capture.py` remains blob `5db02cbd1367ed25b994b152acf371421859a014`. The current entrypoint calls `fetch_saved_upcoming_serie_a_quotes()` before `discover_archives()`; source-before-quote is still not established on main. The source-first implementation is in #938 and descendants only.
- Main `.github/workflows/serie-a-v2-forward-preview.yml` remains without the #781 default-deny hold and still publishes under its existing artifact condition. #781 is not merged, so its protection is not active on main.

### Current V2 PR chain and exact-head Actions
- Root HOLD #781: OPEN / Ready for review, exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, 8/8 associated PR-triggered workflow runs completed SUCCESS (45108795827, 45108795897, 45108795789, 45108795785, 45108795798, 45108795794, 45108795793, 45108795804). HUMAN-MERGE only.
- #879: Draft, exact HEAD `02bf0873979551ddd98511df013a27f872893990`, its private-artifact gate run #45136504472 SUCCESS.
- #938: Draft, exact HEAD `14d765ca2b55e939d9ab5790abbbecd3a29f2614`, source-first validation run #45161516045 SUCCESS.
- #947: Draft, exact HEAD `3839f256ac7c910d914d70cb0781cf58b55f82fa`, source-first run #45309325902 and frozen-shadow run #45309325907 SUCCESS. It joins the real provenance writer to the frozen gate validator with synthetic fixtures only.
- #948: Draft, exact HEAD `73ce0e91df1f89fde9b8bfc13551b439149e3f0a`, source-first validation run #45329787667 SUCCESS. It adds recursive outcome-field rejection to the separate preview wrapper; no live outcomes were accessed.
- #949: Draft, exact HEAD `1003148980e7421a4014e0bafc6e466b4b0c4f12`, child of #948. Held-workflow action-pin run #45362170371 SUCCESS; its log reports **33 passed**. The five held workflows pin checkout `d23441a48e516b6c34aea4fa41551a30e30af803`, setup-python `ece7cb06caefa5fff74198d8649806c4678c61a1`, and upload-artifact `b7c566a772e6b6bfb58ed0dc250532a479d7789f`. The exact upstream `action.yml` files at those commits declare `runs.using: node24`. The PR description was corrected to list these current SHAs; no workflow was run against a paid provider.
- #949 remains stacked on #948; do not merge it independently or before the root hold chain.

### 5DollarFootballAPI — new $0 Community route, still HOLD
- Source audit PR #792 was updated on its separate branch to exact HEAD `a0a1d7074bdc9506bd6b858ba1f94e155a295419`; six associated PR validation runs completed SUCCESS: #45371366946, #45371366895, #45371367065, #45371366769, #45371366939, #45371366874. The only changed file is `research/SERIE_A_V2_5DOLLAR_FOOTBALL_API_SOURCE_AUDIT_20261111.md` (277 additions, 0 deletions). This CI validates the documentation change, not entitlement or data quality.
- The provider's [Community Access page](https://5dollarfootballapi.com/community), re-read 2026-11-24, describes a $0 plan for applicants who truthfully select an eligibility category and country pack; it adds one country pack, 12 months of history and 300 requests/hour (20/minute ceiling). The account holder must make the eligibility attestation. This automation must not self-attest, create an account, activate a plan or request a key.
- The [Italy Serie A measured data-quality page](https://5dollarfootballapi.com/docs/data-quality/3405541143), recounted 2026-11-24, labels the 12-month/13-season row Pro/Ultra and reports 380/380 finished matches with 100% corners, HT corners, corner lines, odds, events, live stats and cards. Its season table reports 110/110 finished 2026/27 fixtures through 2026-11-09 with 100% aggregate completeness. These are aggregate provider-published metrics only; no match-level result or outcome was read. The dedicated Serie A marketing page still claims Free access, so actual Community/Italy account entitlement remains unverified.
- Terms permit model/internal-tool use and caching, require attribution for public-facing $0-plan use, and prohibit raw-feed redistribution. The upstream data-rights chain and a durable private research-archive retention term are still not documented. Keep the rights manifest HOLD.
- Offline adapter PR #800 remains Draft, exact HEAD `a3be5ced21f768a53a2c6dbdf72a346efd040434`, 7/7 associated validation runs SUCCESS; Frozen V2 shadow suite #44897101429 reports 121 passed. It accepts only the $0 Free plan and deliberately rejects Community unless separate eligibility/entitlement approval is added. No API key, request, download, source archive, or feature build was performed.

### Fresh pre-match-only Supabase inventory
- Read-only SELECT used only `public.odds_snapshots` league/event/timestamp columns with strict predicates `snapshot_time_utc < commence_time_utc` and `created_at < commence_time_utc`.
- **3,915** strict pre-match rows; **327** unique events; **0** future strict pre-match rows/events. Latest strict snapshot: Serie A `2026-10-13T14:48:53.042620Z`.
- No score, result, settlement or target-outcome fields were selected. No Supabase writes/DDL.

### Frozen candidate and evaluation status
- Original candidate SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; 19 ordered features, 20×2 original weights, training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; `active_lambda=0`, `shadow_lambda=1`. No contract, weight, scaler or imputer changes.
- Historical stability gate remains FAILED. The first outcome-read gate was already passed by the earlier metadata-only 110-event check, but this is not the prospective evaluation gate. Prospective eligible forecasts remain **0/30 / CLOSED**; no independent Brier/LogLoss comparison or superiority claim.
- No protected match-level 2026/27 outcome was read in this checkpoint; the provider page supplied only aggregate coverage counts. No source/API request, paid request, Supabase write/DDL, model inference/refit, threshold tuning, production `.pkl` change, main update, merge, promotion, bet, schedule change or other-agent setting change.

**Next safe action:** HUMAN-MERGE review of #781 first. Keep #792/#800 as a no-cost source candidate only; no Community self-attestation or provider access without the account holder's authorization and written rights/retention clearance. Continue source-before-quote and frozen-contract verification on the research chain; do not open a new prospective evaluation until the separate 30-primary-completed-forecast gate and incumbent-provenance requirements are satisfied.


## 2026-11-24 13:09 UTC — Original V2 source audit and persisted-quote gate

### Fresh main and original forward chain
- Default branch remains public at `40887ebb215730190d7a6c7a1693373ec4afcdfc`. The main `PROJECT_CONTINUITY.md` is still the October 18 checkpoint; this open documentation branch carries the newer V2 continuity record. No main update or merge was performed.
- Root default-deny hold #781 remains OPEN / Ready for review at exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`; its eight exact-head workflow runs are SUCCESS. Until HUMAN-MERGE, the hold is not active on main.
- Original forward child #951 is OPEN / Draft at exact HEAD `f1ad14e783b4f03e8887516f6805d4650233fead`, parent #950 exact HEAD `79a71f0fa12c5ce52ee20915c9013bff4464c7ed`. Exact CI [#45390159817](https://github.com/MaksimBlud/football-ai/actions/runs/45390159817): 2/2 SUCCESS, 499 passed on Python 3.11 and 499 on Python 3.12. It closes the direct-helper bypass by requiring persisted quote `created_at` to be at/after the declared snapshot, no later than capture time, and strictly before kickoff. The stacked branch's saved-quote reader selects and validates `created_at`; the #951 change protects direct callers too.
- #951 remains dependent on the full source-first/private-storage chain; it is not a standalone main merge candidate.

### New independent free-source candidate — Big Balls Sports Data
- Draft PR #952 is an independent audit branch from main, exact HEAD `5513f7092d619f8984365ed5b719524862cd47b5`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; it does not integrate a provider.
- Exact-head PR checks: 7/7 SUCCESS. Dedicated original-V2 audit [#45400213689](https://github.com/MaksimBlud/football-ai/actions/runs/45400213689): 2/2 SUCCESS, 8 tests passed on Python 3.11 and 8 on Python 3.12; production `.pkl` diff guard passed. Research PR Validation [#45400213617](https://github.com/MaksimBlud/football-ai/actions/runs/45400213617) also ran the new contract test and passed.
- Official Big Balls Terms (effective 2026-08-10) permit storing API responses in private systems and internal model training/evaluation/backtesting, while prohibiting raw-feed redistribution. Official docs conflict on whether Serie A `/v1/matches/{id}/statistics` and two-season history are Free or paid/current-season-only. Published Serie A team-stat coverage is 4,210 / 4,591 (91.7%) across the measured archive; 2026/27 per-fixture and per-field coverage is not published.
- Decision remains `HOLD_NO_INTEGRATION`: upstream field-rights, account-level Free entitlement, current-season completeness, and timestamp/correction semantics remain unresolved. No account, API key, provider request, or download was made. See [PR #952](https://github.com/MaksimBlud/football-ai/pull/952).

### Fresh pre-match-only Supabase inventory
- Read-only query used only `public.odds_snapshots` and strict predicates `snapshot_time_utc < commence_time_utc` and `created_at < commence_time_utc`; no outcome, score, settlement or target fields were selected.
- **3,915** strict pre-match rows, **327** unique events, **0** future strict pre-match rows/events. Serie A: **620** strict pre-match rows, **63** events; latest strict Serie A snapshot `2026-10-13T14:48:53.042620Z`.
- No Supabase writes/DDL. The 30-primary-completed-event prospective evaluation gate remains **0/30 / CLOSED**; no independent Brier/LogLoss result and no superiority claim.

### Controls
- No provider/API request, source download, paid odds request, Supabase write/DDL, protected 2026/27 outcome read, inference on real data, retraining/refit, threshold tuning, production `.pkl` change, main update, merge, promotion, publication, bet, schedule change, or other-agent setting change occurred in this checkpoint.
- Preserve `active_lambda=0` as the market identity and `shadow_lambda=1` as research only. Keep source capture and inference held until provider rights, private storage, and source-before-quote evidence are independently cleared.

## 2026-11-24 13:52 UTC — Fresh main, exact-head V2 chain and strict pre-match ledger recheck

### Main and original-forward runtime
- Re-read repository metadata, default-branch commit, main continuity file, original forward script/workflow, and current open V2 PRs. Main remains public at `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Main `PROJECT_CONTINUITY.md` remains blob `2ce2b5f8a60333f3cc4a0cfdc9c27e7fbdb9741b` and still starts with the October 18 checkpoint.
- Main `serie_a_v2_forward_capture.py` remains blob `5db02cbd1367ed25b994b152acf371421859a014`; its old `main()` reads saved quote rows before discovering and verifying source archives. Main `.github/workflows/serie-a-v2-forward-preview.yml` still exposes Supabase/GitHub credentials at job scope and publishes its artifact under `if: always()`. The default-deny/source-first/private-storage chain is not active on main until HUMAN-MERGE.
- Main `serie_a_v2_frozen_shadow_preview.py` still has a `MARKET_KEYS` projection without `created_at`. The #951 research stack adds `created_at` to that projection and tests the persisted-quote query contract; do not cherry-pick or merge #951 without its complete #781 → #879 → #938 ancestry.

### Exact open V2 PRs and associated CI
- Root HOLD [#781](https://github.com/MaksimBlud/football-ai/pull/781): OPEN / Ready for review; live PR API HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. Eight exact-HEAD associated workflows all SUCCESS: 45108795827, 45108795897, 45108795789, 45108795785, 45108795798, 45108795794, 45108795793, 45108795804. Run #45108795798 independently reports the exact same head SHA. HUMAN-MERGE only.
- Private-storage child [#879](https://github.com/MaksimBlud/football-ai/pull/879): OPEN / Draft, exact HEAD `02bf0873979551ddd98511df013a27f872893990`; its exact validation run #45136504472 SUCCESS.
- Source-first original-forward child [#938](https://github.com/MaksimBlud/football-ai/pull/938): OPEN / Draft, exact HEAD `14d765ca2b55e939d9ab5790abbbecd3a29f2614`; isolated validation run #45161516045 SUCCESS. Its CLI verifies the latest source parent and ZIP SHA before importing Supabase or reading saved quotes.
- Immutable-action-pin child [#949](https://github.com/MaksimBlud/football-ai/pull/949): exact HEAD `1003148980e7421a4014e0bafc6e466b4b0c4f12`; run #45362170371 SUCCESS.
- Source-first validator hardening [#950](https://github.com/MaksimBlud/football-ai/pull/950): exact HEAD `79a71f0fa12c5ce52ee20915c9013bff4464c7ed`; run #45379676444 SUCCESS. It disables persisted checkout credentials in the isolated validator.
- Persisted quote-row chronology [#951](https://github.com/MaksimBlud/football-ai/pull/951): exact HEAD `f1ad14e783b4f03e8887516f6805d4650233fead`; exact validation run #45390159817 SUCCESS on Python 3.11 and 3.12, 499 tests in each job. It requires quote-row `created_at` to be at/after the declared snapshot, no later than the capture clock, and strictly before kickoff; the stacked quote reader selects and validates that field.
- Big Balls free-source audit [#952](https://github.com/MaksimBlud/football-ai/pull/952): exact HEAD `1c364dd83f9a9735112c58256c94d3dfc3c94c10`; seven associated PR workflows SUCCESS. Dedicated audit run #45401901429 is tied to that exact SHA. Decision remains HOLD / no integration: public plan/statistics documentation conflicts, current-season per-field completeness is unproven, and timestamp/correction provenance remains unresolved.
- The existing Soccer Data audit [#874](https://github.com/MaksimBlud/football-ai/pull/874) is already OPEN / Draft at exact HEAD `9f1afef57118e92265ff766931b506394a78f9cd`, with seven associated workflows SUCCESS. Do not create a duplicate audit. It records the Free-plan/current-season limitation, storage only while account/plan remain active, no explicit AI training/inference grant, upstream-rights uncertainty, stale-cache semantics and no account/API access.
- Documentation PR [#839](https://github.com/MaksimBlud/football-ai/pull/839) was at exact HEAD `4b5617f71778949c3887adbeaf15a4a6e28a6dd6` before this checkpoint; its eight associated exact-head workflows all SUCCESS (45400687075, 45400687083, 45400687146, 45400687253, 45400687217, 45400687458, 45400687062, 45400687094). Its PR body still names a different, superseded SHA `c6c707b1...`; the live PR API head is authoritative. This documentation update must receive fresh CI before it is described as validated.

### Fresh Supabase pre-match-only ledger check
Read-only SELECT from `public.odds_snapshots` used only league, event ID, snapshot time, persistence time and kickoff time. Eligibility required:
`snapshot_time_utc < commence_time_utc`,
`created_at < commence_time_utc`, and
`snapshot_time_utc <= created_at`.
- All leagues: 3,966 total rows; 3,915 strictly pre-match rows; 327 unique pre-match event IDs; zero rows for future events with a strictly pre-match quote.
- Serie A: 625 total rows; 620 strictly pre-match rows; 63 unique events; zero future-event pre-match rows. Latest eligible Serie A snapshot remains `2026-10-13T14:48:53.042620Z`.
- No score, result, settlement or protected target-outcome columns were selected. The ledger has no new prospective quotes for the original V2 cohort.

### Frozen original V2 and gates
- Candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; exact ordered 19 features and 20×2 weights unchanged; training fingerprint `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`; `active_lambda=0`, `shadow_lambda=1`.
- Historical stability gate remains FAILED. Prospective evaluation cohort remains 0/30 / CLOSED; no eligible independent Brier/LogLoss comparison and no superiority claim. The incumbent comparator's separate as-of provenance remains unresolved; do not revive or run the legacy XGBoost artifact to fill that gap.
- No source-provider account/key/request/download, no paid odds request, no protected 2026/27 target-outcome read in this cycle, no Supabase write/DDL, no inference/refit, no threshold tuning, no production `.pkl` change, no main update/merge/promotion/bet, and no schedule or other-agent change.

**Next safe action:** keep the root #781 HUMAN-MERGE review first. After a human merge, re-read main and verify the five live workflows skip source/quote access and artifact publication. Continue the existing #879 → #938 → #949 → #950 → #951 chain only after each parent is integrated; keep #952 and #874 as HOLD-only source audits until rights, exact coverage and private retention are independently cleared.


## 2026-11-24 16:52 UTC — fresh main runtime checkpoint: current-form source archive verified, zero quote rows

### Exact main and live workflows

- Fresh default-branch main remains 40887ebb215730190d7a6c7a1693373ec4afcdfc; repository visibility is PUBLIC.
- Read the exact current-main original-forward, current-form source-capture, and current-form forward workflow files. The original forward workflow still has the daily 08:08 UTC schedule, workflow_run on manually dispatched Serie A Odds Snapshots, live Supabase/GitHub credentials at job scope, and an artifact upload guarded by if: always(). The current-form source/forward workflows also still run on main with actions/checkout@v4, setup-python@v5, and public artifact uploads. No schedule was changed by this checkpoint.
- Root default-deny PR #781 remains OPEN / Ready for review / mergeable, exact HEAD 5552bec363ae72ad7aef04c598d2ce861f33eb42, base main 40887ebb215730190d7a6c7a1693373ec4afcdfc, 8/8 exact-head checks SUCCESS. It gates all five original V2 live source/quote/recovery workflows and their uploads, including current-form source capture; it is not active on main until HUMAN-MERGE. PR #879 remains its private-repository child and is also unmerged.

### Actual main-branch source and forward runs — metadata only, no artifact bytes copied into this report

- Current-form source capture run #45438071171 completed SUCCESS at 2026-11-24 16:32:06 UTC on the main SHA above. The real job log reports the feature-input-only metadata gate passed with 120 unique completed primary events / 120 prior-day current-season rows; it captured 10 frozen historical CSVs plus 1 current-season CSV, 3,920 historical match rows, original candidate SHA a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6, zero paid provider calls and zero Supabase writes. Source artifact ID 14942801007, 440,666 bytes, GitHub ZIP SHA-256 a2f9e5882f268040b13400e37b2e30d345d72c494129c955aa008b6e90ff64d1, created 16:32:04 UTC, expiry 2027-02-22. The current-season parser uses only prior-day completed rows as lagged feature inputs after the separate 30-event feature-input gate; this is not the prospective evaluation-outcome gate.
- Current-form forward preview run #45438267623 completed SUCCESS at 16:32:56 UTC. It independently verified source artifact ID 14942801007, its ZIP SHA, exact parent source workflow/run ID/head SHA, source observation 16:32:03.032 UTC, artifact creation 16:32:04 UTC, and parent completion 16:32:06 UTC before verification at 16:32:50 UTC (source age 46 seconds). It reports 3,920 historical match rows, 120 current-season history rows, 11 source files, 0 saved quote rows seen, 0 V2 current-form shadow captures, target evaluation gate CLOSED, no target outcomes read/scored, zero paid calls and zero production/Supabase writes. Forward artifact ID 14940799787, 441,831 bytes, SHA-256 37aad433404e55602b21df6f78f201d850f2720eac874daedef0ff5101d987ac, created 16:32:53 UTC, expiry 2027-02-22.
- Both runs used the still-public repository's standard Actions artifact store. Artifact metadata is recorded here; archive bytes and match outcome values were not downloaded or inspected in this checkpoint. This is real source-archive/SHA/parent chronology runtime evidence, but it is not a real quote, a V2 prediction, or a model-quality result. It also confirms that the unmerged #781 hold is operationally important: source capture and public artifact publication still ran on main despite the separate provider-rights/private-storage HOLD.

### Fresh Supabase pre-match-only read

Read-only SELECT from public.odds_snapshots; selected only league, event ID, snapshot time, persistence time and kickoff time. Eligibility required snapshot_time_utc < commence_time_utc, snapshot_time_utc <= created_at, and created_at < commence_time_utc. No score/result/settlement columns were selected.

- All leagues: 3,966 rows total; 3,915 strict pre-match rows; 327 unique events; 0 future-event eligible quote rows; 0 rows with persistence before snapshot.
- Serie A: 625 total; 620 strict pre-match; 63 unique events; 0 future eligible quote rows; latest eligible snapshot remains 2026-10-13 14:48:53.042620 UTC.
- No new prospective market quote is available for the original V2 current-form cohort.

### Frozen V2 boundary

Candidate SHA, exact 19-feature order, 20×2 weights, scaler/imputer, training fingerprint, active_lambda=0, shadow_lambda=1, failed historical stability gate and separate 30-eligible-prospective-forecast evaluation gate are unchanged. Evaluation remains 0/30 / CLOSED; no Brier/LogLoss comparison or superiority claim. No inference was performed because the current-form forward run had zero saved quotes.

No Supabase writes/DDL, paid API requests, target-evaluation outcome reads, production .pkl changes, main updates, PR merges, promotions, bets, schedule changes, or other-agent changes occurred. HUMAN-MERGE remains mandatory.


## 2026-11-24 18:03 UTC — current-form source-rights restack, exact CI, and public-artifact runtime audit

### Fresh main and actual current-form runtime

- Re-read main, `PROJECT_CONTINUITY.md`, original forward source/workflow, both current-form workflows, open V2 PR heads, exact GitHub check-runs, and pre-match-only Supabase aggregates. Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; repository visibility remains PUBLIC. Main was not changed.
- Main `.github/workflows/serie-a-v2-current-form-source-capture.yml` is blob `9722416862b42d55ff7181003353c39620f23cf2`. Its current job still puts `SUPABASE_URL` and `SUPABASE_KEY` at job scope, runs capture without a source-rights/private-storage check, and uploads the raw source artifact with `if: always()`.
- Main `.github/workflows/serie-a-v2-current-form-forward-preview.yml` is blob `6ebbcaff290a78e9ccffa4ac9a09bc0982eaff35`. It still puts Supabase/GitHub credentials at job scope and uploads the preview/source ZIPs with `if: always()`. Its daily schedule remains `18 8 * * *`; its workflow_run filter permits the odds-snapshot parent only when that parent was manually dispatched. No paid snapshot was dispatched by this checkpoint.
- Actual source-capture run [#45438071171](https://github.com/MaksimBlud/football-ai/actions/runs/45438071171), on exact main SHA above, completed SUCCESS. Its real job log reports 120 completed primary metadata events, 120 prior-day current-season rows, 3,920 historical rows, 10 old-season CSVs plus 1 current-season CSV, 11 source files, candidate SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 0 paid provider calls, 0 Supabase writes, and no target-outcome evaluation. Artifact ID `14942801007`, 440,666 bytes, SHA-256 `a2f9e5882f268040b13400e37b2e30d345d72c494129c955aa008b6e90ff64d1`.
- Actual current-form forward run [#45438267623](https://github.com/MaksimBlud/football-ai/actions/runs/45438267623) independently verified that exact source artifact SHA and its parent workflow/run identity. Source observation `16:32:03.032766Z`, artifact creation `16:32:04Z`, parent completion `16:32:06Z), verification `16:32:50Z), source age 46 seconds. It reports 0 saved quote rows, 0 V2 current-form shadow captures, 0 target outcomes read/scored, 0 paid calls, and 0 production/Supabase writes. Forward artifact ID `14940799787`, 441,831 bytes, SHA-256 `37aad433404e55602b21df6f78f201d850f2720eac874daedef0ff5101d987ac`.
- The source and forward job logs show the Supabase credentials were present across unrelated job steps because they are job-scoped. Both artifacts were uploaded to the still-public repository's Actions artifact store. Archive bytes and match outcome values were not downloaded or inspected in this checkpoint. This is real source-archive/SHA/parent chronology evidence, not a real quote, prediction, or model-quality result.

### Root default-deny hold

- [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN / Ready for review / mergeable / HUMAN-MERGE only, exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- Re-read the exact commit check-runs: all **8/8 completed SUCCESS**, every check reports the exact HEAD above. Runs: #45108795793, #45108795897, #45108795789, #45108795804, #45108795785, #45108795798, #45108795794, #45108795827.
- Until a human merges #781 and a fresh-main audit confirms the live steps and artifact uploads are skipped, its hold is not active on main. The actual 16:32 UTC runs above demonstrate why this manual root hold is urgent.

### New current-form source-capture rights restack — PR #954

- Created Draft [PR #954](https://github.com/MaksimBlud/football-ai/pull/954), a clean restack of the existing current-form rights work from #910 onto #951. Exact base #951 HEAD `f1ad14e783b4f03e8887516f6805d4650233fead`; final PR HEAD `ec7aa84293a10c46c2dfb07f68bb4e0f1ebcc8c1`; 7 commits from the exact parent; 4 changed files. It remains mergeable and unmerged.
- The public current-form source-capture helper previously lacked a direct rights/privacy guard even though its workflow had a default-deny flag. The restack requires explicit source-capture permission plus private-repository storage before public helpers, Supabase metadata reads, source HTTP, or archive creation. The CLI checks rights before creating the Supabase client.
- The feature-input gate now validates the unchanged protocol Git blob SHA-1 `65729e9639720e67624c1481190aa22ae606f151` and derives the 30-primary-completed-event threshold from the frozen V2 protocol. The gate query selects only `match_date,home_team,away_team`; completed current-season results are described separately as lagged feature inputs after that gate. The prospective evaluation-outcome gate remains separate and closed.
- Current `research/source_rights/football_data_co_uk.json` still has `research_source_capture_permitted=false`, `research_inference_permitted=false`, and `rights_status=V2_FROZEN_INFERENCE_SCOPE_UNRESOLVED`. Therefore the new direct guard fails closed before Supabase/source access; it does not authorize capture.
- Existing schedule/triggers are unchanged and `MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED` remains `false). `GITHUB_TOKEN` is now scoped only to the already-gated capture step; Supabase keys remain step-scoped. The source-first validator was extended to include this current-form module and its tests.

### Exact PR #954 CI evidence

- Dedicated current-form rights validation [#45454852550](https://github.com/MaksimBlud/football-ai/actions/runs/45454852550), predecessor SHA `9c04dd6f1bd7f7fb32bce9277debec35d5a8cc17`: **2/2 SUCCESS**, Python 3.11 **33 passed**, Python 3.12 **33 passed**, production `.pkl` diff guard passed.
- Full source-first validation [#45454852563](https://github.com/MaksimBlud/football-ai/actions/runs/45454852563), same predecessor SHA: **2/2 SUCCESS**, Python 3.11 **514 passed**, Python 3.12 **514 passed**, production `.pkl` diff guard passed. This run includes the current-form rights tests and original source-first/frozen-contract regressions.
- Exact final PR HEAD `ec7aa84293a10c46c2dfb07f68bb4e0f1ebcc8c1`: PR check run [#45454870284](https://github.com/MaksimBlud/football-ai/actions/runs/45454870284) **2/2 SUCCESS**. The final commit after the predecessor CI only deleted a redundant one-off validator workflow; the tested source, tests, and live workflow are unchanged.
- All these CI runs are offline/synthetic contract tests. They do not prove provider permission, private deployment, live source/quote runtime, or model quality. HUMAN-MERGE only; review #954 only after #951 and all ancestors.

### Exact open V2 PR heads and current CI refresh

- #950: exact HEAD `79a71f0fa12c5ce52ee20915c9013bff4464c7ed`, 4/4 check-runs SUCCESS (push + PR, Python 3.11/3.12).
- #951: exact HEAD `f1ad14e783b4f03e8887516f6805d4650233fead`, 2/2 SUCCESS; 499 tests per Python 3.11/3.12 job.
- #952 Big Balls audit: exact HEAD `1c364dd83f9a9735112c58256c94d3dfc3c94c10`, 10/10 check-runs SUCCESS. Decision remains HOLD / no integration; Free entitlement, current-season per-field completeness, and timestamp/correction provenance remain unresolved.
- #953 current-form direct quote-row persistence preflight: exact HEAD `2fa0aa46e79966075ed911052a9c6dfa9f19888f`, 4/4 check-runs SUCCESS; 102 tests per Python 3.11/3.12 job in its dedicated workflow.
- #839 documentation PR: exact HEAD `1015fcb90179f9da7b01a94195fee13f3cdd854a`, 8/8 check-runs SUCCESS. This checkpoint is appended here and requires a fresh CI rerun after this documentation commit.
- Existing #874 Soccer Data audit remains HOLD-only; no duplicate provider audit or integration was created.

### Fresh strict pre-match-only Supabase inventory

Read-only SELECT from `public.odds_snapshots`; only `league,event_id,snapshot_time_utc,created_at,commence_time_utc` were used. Strict eligibility required `snapshot_time_utc < commence_time_utc`, `snapshot_time_utc <= created_at`, and `created_at < commence_time_utc`. No score, result, settlement, or target-outcome columns were selected.

- All leagues: 3,966 total rows; 3,915 strictly pre-match rows; 327 unique strictly pre-match events; 0 future events with an eligible quote.
- Serie A: 625 total rows; 620 strictly pre-match rows; 63 events; latest eligible snapshot `2026-10-13T14:48:53.042620Z`.
- No new prospective quote or shadow forecast is available.

### Frozen original V2 boundary

Candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; exact ordered 19 features and 20×2 weights remain unchanged; `active_lambda=0`, `shadow_lambda=1`. Historical stability gate remains FAILED; prospective evaluation remains 0/30 / CLOSED. No independent Brier/LogLoss comparison and no superiority claim.

No provider/API request or download, paid odds request, Supabase write/DDL, protected evaluation-outcome read, real-data inference/refit, threshold tuning, production `.pkl` change, main update, merge, promotion, publication, bet, schedule change, or other-agent setting change occurred in this checkpoint.

## 2026-11-24 18:15 UTC — atomic current-form archive, redirect-origin, and provenance-clock restack

- Created Draft [PR #955](https://github.com/MaksimBlud/football-ai/pull/955) as a child of #954, exact parent HEAD `ec7aa84293a10c46c2dfb07f68bb4e0f1ebcc8c1`. Final HEAD `3d9e2b48c05db7c4d9899eacb30b937e01f09dc3`; 6 files, 412 additions, 16 deletions; mergeable, OPEN, not merged.
- This is a clean restack of the existing #917/#922/#923 source-clock, redirect-origin, and atomic-publication protections onto the current #954 source-rights/private-storage chain. It does not alter any original V2 model artifact, feature order, weight, scaler, lambda, threshold, or evaluation contract.
- Current-season and historical CSV GETs now disable redirects, require HTTP 200, and verify the exact configured response URL before reading bytes. Redirect or unexpected URL responses are rejected before body access and source-observation timestamps.
- The full source archive is assembled in a same-filesystem temporary directory and atomically renamed only after all source files and manifest checks succeed. Symlink/nonempty destinations fail before metadata/source access; a failure after partial historical writes discards the staging tree.
- Entry, source-observation, and archive-creation clocks require a timezone-aware datetime with a non-null UTC offset and are normalized to UTC. Archive creation may not predate the source observation.
- The current-form capture workflow's path/compile/test contract now covers the historical-source fetch helper; the existing source-first offline validator includes the expanded current-form and historical-source regression files. Existing schedules/triggers are unchanged and live access remains default-deny.
- The first exact-head attempt on predecessor `3ad932c6d6fe79a1e63a45566025b67445b39d42` failed on a missing `tempfile` import (5 failures; 520 tests passed). Added the import; final exact HEAD is `3d9e2b48c05db7c4d9899eacb30b937e01f09dc3`.
- Final exact-head CI [#45457151474](https://github.com/MaksimBlud/football-ai/actions/runs/45457151474): **2/2 SUCCESS**; Python 3.11 **525 passed**, Python 3.12 **525 passed**; module compilation and production `.pkl` diff guard both passed.
- These are offline/synthetic tests only. The provider rights manifest remains HOLD, so no real source/quote requests or inference are permitted. No Supabase access/write/DDL, protected target-outcome read, model refit, threshold tuning, production artifact change, main update, merge, schedule change, promotion, or betting occurred.
- PR #955 remains Draft/HUMAN-MERGE and must follow #954 and the existing #781-rooted chain.
## 2026-11-24 18:32 UTC — Big Balls Free endpoint recheck and exact-head audit

### Original V2 source candidate: Big Balls Sports Data

- Existing Draft [PR #952](https://github.com/MaksimBlud/football-ai/pull/952) was updated in place; no duplicate PR was created. Exact HEAD: `001c146eb92a4f31f9b7d56814951fb45ab662fe`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- The current official OpenAPI and Serie A FAQ now confirm `GET /v1/matches/{id}/statistics` is Free; `expected_goals` is Solo+ and is not part of the original 19 features. The earlier endpoint-tier discrepancy is superseded.
- The statistics endpoint is stored-only, persisted hourly, and upstream statistics generally appear about 30 minutes after full time. It is only a possible lagged input source for later fixtures, not live pre-kickoff statistics for the same match.
- Documented field families can map to the unchanged original features: final score -> goals and 3/1/0 points; `corner_kicks` -> corners; `yellow_cards` and `red_cards` -> cards. Exact 19-feature parity is NOT verified because current 2026/27 per-fixture and per-field completeness is unknown.
- The Free season-depth conflict remains: global pricing advertises current plus most-recent season, while the Serie A page says current season only. The OpenAPI describes 19+ free-tier upstream sources and 10 MCP scrapers without identifying the upstream source/rights chain per required field. Per-match first-observed and per-field correction timestamps are undocumented; account-closure retention is undefined.
- Provider decision remains `HOLD_NO_INTEGRATION`; no account/key, provider request, download, provider-specific Supabase read, integration, feature calculation or inference was performed. Private receipt UTC + SHA could prove project possession before a later quote, not upstream first observation.
- Exact-head validation for #952: **7/7 workflow runs SUCCESS** on `001c146...`; dedicated [run #45460140252](https://github.com/MaksimBlud/football-ai/actions/runs/45460140252) passed **10 tests on Python 3.11 and 10 on Python 3.12**; both production `.pkl` diff guards passed. This is offline audit CI, not a live provider test.

### Current main runtime and root hold

- Main remains public at `40887ebb215730190d7a6c7a1693373ec4afcdfc`; no main change or merge occurred.
- Main current-form source capture [#45438071171](https://github.com/MaksimBlud/football-ai/actions/runs/45438071171) succeeded with 120 feature-input gate events, 11 CSV files and archive SHA-256 `a2f9e5882f268040b13400e37b2e30d345d72c494129c955aa008b6e90ff64d1`. Raw source bytes were published as public Actions artifact `14942801007`.
- Forward verification [#45438267623](https://github.com/MaksimBlud/football-ai/actions/runs/45438267623) verified the parent workflow and archive SHA 46 seconds later; it had 0 eligible quote rows and 0 shadow captures. The archive's public publication remains a live privacy/rights blocker.
- Root default-deny PR #781 remains OPEN / Ready for review / mergeable, exact HEAD `5552bec363ae72ad7aef04c598d2ce861f33eb42`, exact-head CI 8/8 SUCCESS. It has not been merged; HUMAN-MERGE is required before treating the hold as active on main.
- Current-form rights/private-storage child #954 remains Draft, exact HEAD `ec7aa84293a10c46c2dfb07f68bb4e0f1ebcc8c1`; exact CI 2/2, 514 tests on Python 3.11 and 3.12. Atomic/redirect-safe child #955 remains Draft, exact HEAD `3d9e2b48c05db7c4d9899eacb30b937e01f09dc3`; exact CI 2/2, 525 tests on each version. Both are offline/synthetic only and must follow #781 and ancestors.
- Original-forward quote-persistence child #951 remains Draft at `f1ad14e783b4f03e8887516f6805d4650233fead`, 499 tests on each Python version; current-form helper child #953 remains Draft at `2fa0aa46e79966075ed911052a9c6dfa9f19888f`, 102 tests on each version. Neither grants source or inference rights.

### Pre-match market data and model status

- Read-only SELECT only from `public.odds_snapshots`; no target-outcome columns were queried. All leagues: 3,966 rows, 3,915 strict pre-match rows, 327 events, 0 future events with eligible quotes. Serie A: 625 total rows, 620 strict pre-match rows, 63 events, 0 future eligible quotes. Latest eligible Serie A snapshot remains 2026-10-13 14:48:53 UTC.
- Original frozen candidate SHA-256 remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`; exact 19 ordered features, 20×2 weights, `active_lambda=0`, `shadow_lambda=1`. Historical stability gate FAILED; prospective evaluation remains 0/30 / CLOSED. The 120 completed events passed only the feature-input threshold after the preregistered 30-event gate; the separate prospective target-outcome evaluation gate remains closed.
- No independent Brier/LogLoss comparison or superiority claim. No model inference on a future event, refit, threshold tuning, production `.pkl` change, Supabase write/DDL, paid API request, merge, promotion, bet, schedule change or other-agent setting change occurred.
## 2026-11-24 18:37 UTC — Big Balls season-depth contradiction pinned and exact CI completed

- Existing Draft [PR #952](https://github.com/MaksimBlud/football-ai/pull/952) now has exact HEAD `cb06a340a9d1c17b6cb3fd04ce08cba130e58d41` on base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`; the earlier `001c146...` checkpoint is superseded.
- The current official pricing page contradicts itself: its summary says Free is current-season only, while its Free-tier bullet says current plus most-recent season. The dedicated Serie A page says current season only. The audit/test now pin this conflict; no multi-season Free access is assumed.
- Exact-head validation on `cb06a...`: **7/7 workflow runs SUCCESS**. Dedicated Original V2 Big Balls audit [#45461017657](https://github.com/MaksimBlud/football-ai/actions/runs/45461017657) passed **10 tests on Python 3.11 and 10 on Python 3.12**; both production `.pkl` diff guards passed. Research validation [#45461017755](https://github.com/MaksimBlud/football-ai/actions/runs/45461017755) also completed SUCCESS.
- The match-statistics route remains confirmed Free by current OpenAPI/FAQ; xG remains Solo+ and is not in the original 19 features. The route is stored-only/post-match, hourly, with upstream stats generally arriving about 30 minutes after full time. Upstream field rights, season depth, current 2026/27 per-fixture/per-field coverage, and first-observed/correction timestamp semantics remain unresolved; `HOLD_NO_INTEGRATION` remains mandatory.
- No provider account/key/request/download, provider-specific Supabase access, integration, feature calculation or inference was performed. No model artifact, feature order, weights, scaler/imputer, lambda, threshold, production `.pkl`, main branch, schedule, or other-agent setting was changed.


## 2026-11-24 18:52 UTC — fresh main, current-form metadata gate, and exact source-rights CI

### Fresh main and actual V2 runtime

- Repository remains public; default branch main is still exactly 40887ebb215730190d7a6c7a1693373ec4afcdfc. No main update or merge occurred.
- Re-read the live .github/workflows/serie-a-v2-forward-preview.yml, current-form source/forward workflows, and their main Python entrypoints. The original-forward main workflow still uploads artifacts under if: always(); the original forward path still lacks the source-before-quote ordering now being restacked under #938 and descendants. Root hold #781 is not active on main.
- Latest main free diagnostic [run #45450183033](https://github.com/MaksimBlud/football-ai/actions/runs/45450183033), exact main SHA, completed SUCCESS on 2026-11-24 17:35 UTC. It passed 53 offline tests, verified public-only source access and zero paid provider requests, and read 3,800 historical rows. Runtime output: feature_count=19, quoted_fixtures=0, diagnostic_scored=0, paid_provider_requests=0, supabase_writes=0, mode RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET. It published artifact 14947466958 with ZIP SHA-256 f0ef55f97b781b4a25dc85107261ad49cd89f95c32090ee2460175980fd396d9. The artifact contains raw public-source bytes and was not downloaded or inspected.
- Earlier same-day main current-form source capture [run #45438071171](https://github.com/MaksimBlud/football-ai/actions/runs/45438071171) completed SUCCESS with 120 feature-input metadata events and 11 CSV files; forward check [run #45438267623](https://github.com/MaksimBlud/football-ai/actions/runs/45438267623) verified the parent and archive 46 seconds later but captured zero eligible quotes and zero shadow forecasts. The source artifact was public, so unresolved rights/private-storage risk remains.

### Outcome-blind feature-input gate and strict pre-match market inventory

- Fresh read-only metadata-only query against public.league_finished_results, selecting only match_date,home_team,away_team for SERIE_A / 2026-2027, returned 123 raw unique fixture keys dated 2026-08-22 through 2026-11-23. Applying the exact V2-local aliases (including Atalanta BC → Atalanta) collapses three duplicate rows to **120 canonical unique completed primary fixture identities**, matching the latest successful main source-capture gate. No score, result, settlement, or target-outcome column was selected. This exceeds the preregistered 30-event feature-input threshold only; it does NOT open the separate prospective outcome-read/evaluation gate.
- Fresh read-only public.odds_snapshots query used only quote/kickoff/persistence timestamps and league/event identifiers. All leagues: 3,966 total rows; 3,915 strictly pre-match rows; 327 unique eligible events; 0 future events with an eligible quote. Serie A: 620 strictly pre-match rows / 63 events / 0 future events. Latest eligible Serie A snapshot remains 2026-10-13T14:48:53.042620Z.
- Eligibility requires snapshot_time_utc < commence_time_utc, created_at >= snapshot_time_utc, and created_at < commence_time_utc. The created_at column is still mutable by privileged service_role; this is an ordering filter, not an immutable timestamp attestation.

### Exact current source-rights chain and CI

- Root [PR #781](https://github.com/MaksimBlud/football-ai/pull/781) remains OPEN, Ready for review, mergeable, and HUMAN-MERGE only. Exact API HEAD: 5552bec363ae72ad7aef04c598d2ce861f33eb42; exact-commit workflow runs: 8/8 SUCCESS (runs 45108795827, 45108795897, 45108795789, 45108795785, 45108795798, 45108795794, 45108795793, 45108795804). It has not been merged; public main therefore still executes the unheld live steps.
- [PR #954](https://github.com/MaksimBlud/football-ai/pull/954), current-form direct source-capture rights/private-storage guard, exact HEAD ec7aa84293a10c46c2dfb07f68bb4e0f1ebcc8c1: exact-head workflow #45454870284, 2/2 Python jobs SUCCESS; 514 tests passed on each of Python 3.11 and 3.12; production .pkl diff guard passed.
- [PR #955](https://github.com/MaksimBlud/football-ai/pull/955), child of #954, exact HEAD 3d9e2b48c05db7c4d9899eacb30b937e01f09dc3: exact-head workflow #45457166064, 2/2 Python jobs SUCCESS; 525 tests passed on each of Python 3.11 and 3.12; production .pkl diff guard passed. It adds no-redirect source fetches, atomic complete-archive publication, and timezone-aware source/creation clocks.
- #954/#955 are offline/synthetic CI only. The checked-in Football-Data rights manifest still denies automated source capture and frozen inference, so the new direct guard fails closed before Supabase metadata or provider bytes. No source integration or live inference is authorized.
- [PR #953](https://github.com/MaksimBlud/football-ai/pull/953) remains a separate Draft child of #936, exact HEAD 2fa0aa46e79966075ed911052a9c6dfa9f19888f; its exact-head Python 3.11/3.12 workflow passed 102 tests on each version. #951 remains at f1ad14e783b4f03e8887516f6805d4650233fead (499 tests each); #950 remains at 79a71f0fa12c5ce52ee20915c9013bff4464c7ed (495 tests each). These branches do not grant source or inference rights.
- Existing documentation PR #839 was at exact HEAD 2fca4b41f6969369f89d5aa4a03adf7a72d1231c immediately before this checkpoint; its eight exact-head PR workflows all completed SUCCESS. This append is a new docs-only commit and requires its own fresh exact-head CI.

### Frozen model and non-actions

- Original candidate SHA-256 remains a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6; 19 ordered features; 20×2 weights; active_lambda=0; shadow_lambda=1.
- Historical stability gate remains FAILED. Prospective evaluation remains 0/30 / CLOSED. No eligible future quote, no real 19-feature V2 inference on a new future event, no independent Brier/LogLoss comparison, and no superiority claim.
- No paid provider request, provider download, protected target-outcome read, Supabase write/DDL, model refit, threshold tuning, production .pkl change, main update, merge, promotion, publication of a prediction, bet, schedule change, or other-agent setting change occurred in this checkpoint.


## 2026-11-24 19:30 UTC — fresh main forward-only runtime recheck (no quote, no prediction)

- Current public main remains `40887ebb215730190d7c6a7a1693373ec4afcdfc`. The scheduled [Current-Form Forward-Only Preview run #45470879407](https://github.com/MaksimBlud/football-ai/actions/runs/45470879407) completed SUCCESS on that exact SHA. Its log independently re-verified the already-existing source archive **artifact 14942801007**, archive SHA-256 `a2f9e5882f268040b13400e37b2e30d345d72c494129c955aa008b6e90ff64d1`, original candidate SHA, 10 historical CSVs / 3,920 historical matches, and 120 current-season history rows / 120 feature-input identities. At verification time the source observation was 10,719 seconds old (still within the unchanged 24-hour source freshness rule).
- The same run reported `quotes_seen=0`, `v2_current_form_shadow_captured=0`, all block counters zero, `target_outcomes_read=false`, `target_outcomes_scored=false`, `paid_provider_calls=0`, and `production_or_supabase_writes=0`. Its forward artifact is ID **14956308026**, GitHub ZIP SHA-256 `f1111b896cfc875dc58f2b7e0a0817115f19ec81e37af3629fefa4a810447faa`. This is a real source-attestation/runtime check, not a V2 prediction or quality result.
- The same-hour [Original V2 Forward-Only Preview run #45470457348](https://github.com/MaksimBlud/football-ai/actions/runs/45470457348) also completed SUCCESS: original source attestation verified 10 pre-prospective CSVs / 3,800 historical fixtures, but `quotes_seen=0`, `v2_diagnostic_previews_captured=0`, and no protected outcomes were read. Output artifact ID **14957381523**, ZIP SHA-256 `ccb812b6d31b25ac4ea05436f49c7040b466eca02e3fc151a70c19605c819cb0`.
- No new source-capture run was triggered: public main still lacks the rights/private-storage guards, while the proposed #954/#955 branch carries an explicit denied Football-Data automated-capture manifest (`research_source_capture_permitted=false`, authorization null) and a default-false live-access hold. No new raw source bytes were downloaded or inspected in this checkpoint.
- Fresh read-only Supabase checks reproduce 3,966 total odds rows, 3,915 rows satisfying strict pre-match snapshot/persistence ordering, 327 unique eligible events, and **zero** future events with eligible quotes. Metadata-only Serie A query returned 123 raw fixture rows / keys; applying the exact V2-local `Atalanta BC → Atalanta` alias yields 120 canonical feature-input identities. No scores, results, settlements, or target outcomes were selected.
- Original candidate remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features, 20×2 weights, `active_lambda=0`, `shadow_lambda=1`. Historical stability gate FAILED; prospective evaluation remains 0/30 / CLOSED. No Brier/LogLoss comparison or superiority claim is possible.
- No merge/main update, paid provider request, Supabase write/DDL, production `.pkl` change, candidate/weight change, threshold tuning, promotion, bet, schedule change, or other-agent setting change occurred.


## 2026-11-24 20:58 UTC — held-workflow checkout credential isolation (new PR #956)

- Audited the five held original-V2 workflows on the source-rights/private-storage chain after immutable action pins were added by #949. Their checkout actions were SHA-pinned, but the checkout steps still used the default `persist-credentials: true`, leaving the short-lived `GITHUB_TOKEN` available through local Git configuration to later scripts/dependencies in each job.
- Added [PR #956](https://github.com/MaksimBlud/football-ai/pull/956), a draft child of [PR #955](https://github.com/MaksimBlud/football-ai/pull/955), exact parent SHA `3d9e2b48c05db7c4d9899eacb30b937e01f09dc3`. Exact PR HEAD: `c6d2ca5f8a669bf61b480a5e6ed15076ef71c93b`.
- #956 sets `persist-credentials: false` for the single immutable-pinned checkout step in all five held workflows (free diagnostic, original forward, current-form source capture, current-form forward, and frozen candidate recovery). Existing explicit read-only GitHub API token use remains unchanged; schedules, permissions, provider rights, live-access defaults, Supabase, model files, and candidate weights are untouched.
- Added a runtime assertion after checkout that local Git config contains neither the GitHub HTTP extraheader nor credential `includeIf` entries, plus a static regression across all five workflows. [Exact-head push validator #45486240507](https://github.com/MaksimBlud/football-ai/actions/runs/45486240507) completed SUCCESS: runtime credential cleanup assertion passed and offline regression passed (2 assertions).
- #956 remains Draft / HUMAN-MERGE and is stacked on #955; do not merge it ahead of #955 and the existing source-rights/private-storage chain. This hardening does not itself grant any source or inference permission.
- No paid provider requests, source downloads, Supabase access/writes, protected outcome reads, model inference, production `.pkl` changes, main updates, merges, schedule changes, or other-agent setting changes occurred.
