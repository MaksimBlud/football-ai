# Original MARKET_ANCHOR_1X2_V2 — 2026-11-05 live source and budget audit

Audit time: 2026-11-05 16:03 UTC  
Fresh main: `40887ebb215730190d7a6c7a1693373ec4afcdfc`

## Actual scheduled Nov 5 V2 runs

- **Current-Form Source Capture** [run #42036450692](https://github.com/MaksimBlud/football-ai/actions/runs/42036450692) SUCCESS on main. Artifact **13418048952**, created 2026-11-05 13:31:55 UTC, ZIP SHA-256 `941cb910b4b412027de196156147b164ba6705159ef90e34a99af02e0de04f10`. Log: 11 source files (10 frozen historical CSVs plus current-season CSV), 3,900 historical rows, 100 prior-day current-season rows, metadata-only feature-input gate count 100, zero paid calls, zero Supabase writes, no target outcomes scored.
- **Current-Form Forward-Only Preview** [run #42036593390](https://github.com/MaksimBlud/football-ai/actions/runs/42036593390) SUCCESS. It verified artifact #13418048952 and its successful main parent, but `quotes_seen=0` and `v2_current_form_shadow_captured=0`. It read no target outcomes and wrote nothing. This is source-attestation runtime, not a forecast.
- **Free Real-Quote Diagnostic** [run #42046051819](https://github.com/MaksimBlud/football-ai/actions/runs/42046051819) SUCCESS. Artifact **13424482168**, created 2026-11-05 14:33:47 UTC, ZIP SHA-256 `4f735f1e4636250b0b711963e9f6a660838afc521396968fcb19acb2b39d3559`. Log: `quoted_fixtures=0`, `diagnostic_scored=0`, zero paid-provider requests and zero Supabase writes.
- **Original Forward-Only Preview** has its main schedule `08:08 UTC`, but no Nov 5 scheduled run was found in current Actions history. Last confirmed success remains [run #41864632742](https://github.com/MaksimBlud/football-ai/actions/runs/41864632742) on Nov 4. Absence of a run does not prove the workflow is disabled.

The current-season source gate is **100 unique fixture identities**, above its 30-event minimum. This only permits completed prior matches to be used as lagged features for future quotes; the separate target-outcome evaluation gate remains CLOSED at **0/30 eligible prospective forecasts**.

## Source-rights and download-budget controls remain unmerged

The Nov 5 source capture and diagnostic ran on unguarded main. Direct code comparison confirms that main's `serie_a_v2_current_form_source_capture.py`, `serie_a_v2_live_diagnostic_report.py`, and `serie_a_v2_forward_capture.py` do not call `require_personal_research_inference_scope()`; the helper and conditional-research manifest are present only in #699. Therefore the Nov 5 archive has GitHub parent/run/SHA provenance but is **not rights-attested**. Do not consume it in #712's historical cache or admit it to a new prospective source chain.

The same two public-source workflows ran on both Nov 4 and Nov 5, about 24 hours apart. The intended 170-hour per-workflow guard in #705 would have blocked both Nov 5 runs. #705 remains unmerged. Its branch is now updated to HEAD `c86e9d658809a1c5e77ebf178569ca154a53e0d9`; the bootstrap regression now selects the actual Nov 5 source artifact #13418048952 and diagnostic artifact #13424482168, and the budget audit note records their exact digests/times. The exact-head CI subsequently completed **8/8 SUCCESS**. Dedicated budget run [#42060962914](https://github.com/MaksimBlud/football-ai/actions/runs/42060962914) reports **23 passed**, and the fail-closed `.pkl` diff guard printed `PASS: no .pkl changes in PR`.

Bootstrap from those Nov 5 artifacts yields next 170-hour instants of **2026-11-12 15:31:55 UTC** (Source Capture) and **2026-11-12 16:33:47 UTC** (Free Diagnostic). The next unchanged daily schedule slots after both cooldowns are **2026-11-13 05:50 UTC** and **06:13 UTC**, assuming no later attempts. The schedules were not changed. The Nov 5 source archive was created before #699's source-rights helper existed on main; it must not be treated as a fully source-rights-attested prospective artifact.

The #699 branch's manifest records only a conditional personal-betting/academic-research interpretation for frozen-weight inference. It explicitly disallows AI model training, commercial use, public product use and redistribution, and says it is not a provider-issued AI-inference licence. The policy's “twice per week” wording does not define whether a session is a workflow invocation or an individual CSV request; #705 implements the project's conservative per-workflow-session interpretation.

## Corrected read-only Supabase pre-match provenance audit

The SQL read only pre-match quote fields/timestamps/event identity and structural-observation timestamps/persistence metadata. No score, result, goal, settlement or target-outcome fields were selected.

- Strict pre-match quote rows: **3,915**.
- Exact event/league/kickoff and exact home/away team identity rows with a structural observation strictly before quote time, persisted no later than quote creation, and `payload.pre_kickoff_valid=true`: **2,266**, not 2,768. The stricter team/payload-validity join returned the same per-league counts. The earlier 2,768 aggregate was an arithmetic error; 2,266 is the correct sum of the per-league rows.
- Strict pre-match quote rows in the last seven days: **0**.
- Future events with a saved strict pre-match quote: **0**.
- Latest Serie A strict pre-match quote: **2026-10-13 14:48:53 UTC**.

| League | Strict pre-match rows | Source-before-quote rows |
|---|---:|---:|
| Bundesliga | 394 | 359 |
| EPL | 1,135 | 478 |
| Eredivisie | 410 | 370 |
| La Liga | 798 | 13 |
| Ligue 1 | 387 | 352 |
| Primeira Liga | 9 | 0 |
| RPL | 153 | 138 |
| Serie A | 620 | 556 |
| Turkey Super Lig | 9 | 0 |

The source-before-quote total is a historical metadata join, not proof of provider licensing or a new prospective quote. No saved future quote exists to pair with the Nov 5 source artifact.

## Exact PR dependencies

- #699 `a6725ca49e90d551baa7e9f647151f7e524e42c7`: 7/7 SUCCESS; contains source-rights, clock, identity and outcome guards; still requires HUMAN-MERGE after #705/#714.
- #714 `ea4880dca6b7d41434160a298798b0312744ae56`: offline validation and budget tests SUCCESS; live diagnostic intentionally SKIPPED; stacked on #705.
- #701 `1a01f9f82dcd2c6be2061aea1eb5164d0af47f73`: 6/6 SUCCESS, but base is older than #699 and must be rebased/revalidated.
- #712 `c7a5b5f7db1bc0de13ba8f878e75d6b651fea119`: 9/9 check-runs SUCCESS (offline/mock-only); must wait for a post-#699 rights-attested source artifact and then rebase.
- #715 `0039b51e1d6de2a70ef17065d831052fec837c05`: Draft, no CI; stacked on #699.
- #706 `caab7c07ad720866616ce9fa62664b0d398e5fe0`: 6/6 SUCCESS; fail-closed production `.pkl` diff guard. It overlaps with #701 in `research-pr-validation.yml` and `serie-a-pr-validation.yml`, so rebase/revalidate #706 **after #701** to preserve both evaluator and pickle-guard steps.
- #697 prior HEAD `fcd9f34676f85d66bac4d3214cc7b72f0a42ffac`: 7/7 SUCCESS; this addendum is a new documentation follow-up.

HUMAN-MERGE order remains #705 → rebase/revalidate #714 → #714 → rebase/revalidate #699 → #699. Then rebase/revalidate #701; after #701, rebase/revalidate #706 because both touch the Research/Serie A PR-validation workflows. Rebase #712 and #715 after #699 and admit neither source artifact until a post-#699 rights-attested capture exists. No PR was merged.

## Frozen original V2 and critical security notice

Candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 frozen features, original weights, `active_lambda=0`, `shadow_lambda=1`, stability gate FAILED. Outcome gate remains 0/30; Brier and LogLoss remain uncomputed; no V2 superiority claim is justified.

Supabase inventory still reports RLS disabled on `public.teams`, `public.predictions`, `public.match_statistics`, `public.league_prediction_ledger`, and `public.epl_ai_market_pair_ledger`. No DDL or policy change was performed; enabling RLS without policies may block application access and requires separate review. The latest Security Advisor also reports RLS enabled but no policies on `public.competitions`, `public.match_stats`, `public.matches`, and `public.standings`; no policy changes were made.


## 2026-11-05 17:12 UTC — original MARKET_ANCHOR_1X2_V2 provenance-scope correction

The 2,935/3,915 source-before-quote join above is a read-only diagnostic over `public.league_structural_v2_observations` and `public.la_liga_structural_v2_observations`. These are Structural Edge V2 observation stores, not the Football-Data historical CSV source consumed by original MARKET_ANCHOR_1X2_V2. Their JSON payloads contain no `sha256`, `source_sha`, or `hash` provenance key. The 2,266 generic-table count and 2,935 union count are therefore **not** original MARKET_ANCHOR_1X2_V2 source-before-quote evidence and must not be used as such. This correction does not alter the DB-only diagnostic; it narrows what it proves.

For original MARKET_ANCHOR_1X2_V2, source-before-quote proof must be tied to the exact `serie-a-v2-free-real-quote-diagnostic` GitHub artifact, the successful approved parent workflow/run, the GitHub artifact SHA-256, all ten frozen historical CSV member SHA-256 values, source-observation timestamps, and a quote snapshot strictly later than both source observation and successful source-workflow completion. The source archive must also satisfy the frozen 24-hour source-age rule and the source-rights gate. Supabase Structural Edge rows cannot substitute for any of these attestations.

The Nov 5 Current-Form Source Capture artifact #13418048952 contains a 2026/27 current-season CSV and belongs to the separate current-form experiment; it is excluded from the original frozen historical-only 19-feature V2 chain. The Nov 5 Free Diagnostic artifact #13424482168 was created before #699's rights helper was integrated into main and its run had `quoted_fixtures=0`, `diagnostic_scored=0`; it is not a new prospective forecast. The Nov 4 Original Forward run #41864632742 verified an old-season source archive but recorded `quotes_seen=0` and `v2_diagnostic_previews_captured=0`; it is source attestation only.

The original candidate remains `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, exactly 19 frozen features and 20x2 weights, `active_lambda=0`, `shadow_residual_lambda=1`, stability gate FAILED. The current main feature-builder Git blob `401b3a0893371bfa4a488ec92a4a54af2678c8f7` matches the frozen manifest pin. The synthetic frozen reference-vector test is not a live or prospective forecast. Outcome evaluation remains 0/30; no Brier/LogLoss or market-superiority claim is available.

The #699 rights manifest has `authorization=null` and calls its frozen-inference scope a conditional operational interpretation, not a provider-issued AI-inference licence. No new public CSV request should be initiated until the intended use is demonstrably within the provider's personal-betting/academic-research scope or written permission is obtained.

## 2026-11-05 17:10 UTC — exact V2 integration and review snapshot

- Main is unchanged at `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- **#705** exact HEAD `f3e7451ee9cebc9280a8f86421a509d9bc177da0`, base main, mergeable, **8/8 exact-head PR workflows SUCCESS**. It now consolidates the 170-hour shared source budget, fail-closed production-`.pkl` guard, and offline-only Free Diagnostic push validation. Budget tests: 23 passed; frozen V2 shadow suite: 86 passed; Research and Serie A each passed three fail-closed guard tests. #706 and #714 are closed as superseded and must not be merged separately. HUMAN-MERGE only.
- **#699** exact head `f11b3e1a5fc62f7415ae72944b058b05e3fddd94`, **7/7 SUCCESS** on its old-main base. Rebase after #705 is manually merged; preserve the shared budget/offline push changes and this PR's rights, source/clock, identity-SHA and outcome guards.
- **#701** exact head `1a01f9f82dcd2c6be2061aea1eb5164d0af47f73`, reported **6/6 push validations SUCCESS**, still stacked on an older #699 base. Its targeted Research run #42026189766 includes 20 passed prospective-evaluator workflow tests and the gate-open kickoff-binding regression. Rebase after #699 and rerun exact-head CI.
- **#712** exact head `c7a5b5f7db1bc0de13ba8f878e75d6b651fea119`, **8/8 SUCCESS**, not 9/9. Historical source reuse run #42050748514 reports 54 passed; this is offline/mock-only and does not authorize consuming the pre-#699 artifacts. Wait for a new post-#699 rights-attested original historical source archive before any prospective use.
- **#715** exact head `0039b51e1d6de2a70ef17065d831052fec837c05`, Draft, no CI; it gates the standalone frozen-shadow CLI with the #699 source-rights helper. Rebase and run full CI after #699.
- **#704** exact head `cc4918caf1ae0bb906b6a1949b2b352b3cce64f3`, existing dependency-pin checks are successful but the branch is based on old main and overlaps source workflow files. Rebase after #705/#699 if retaining it; it is not a prerequisite for the shared budget guard.
- **#697** documentation HEAD `88ef1e612b016cadff3b3661a0e872832166a3d5`, **7/7 SUCCESS**. This exact documentation head contains the correction that Structural Edge V2 observation tables are not the original MARKET_ANCHOR_1X2_V2 Football-Data source archive and cannot attest its SHA.

No new source download, paid odds request, Supabase write/DDL, protected target-outcome read, production artifact change, model refit, weight/feature/lambda change, schedule change, or main merge occurred in this audit. The original candidate remains SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, 19 features, 20x2 weights, `active_lambda=0`, `shadow_residual_lambda=1`, stability gate FAILED. Prospective outcome gate remains 0/30; Brier/LogLoss remain unavailable.
