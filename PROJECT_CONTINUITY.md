function content(value) {
    const iterate =
      typeof value === "string" ? undefined : value?.[iteratorKey];
    if (typeof iterate !== "function") {
      return emitBlock(value);
    }

    // Reuse the method from a potentially stateful getter, with its original
    // receiver. The for-of loop closes the iterator if the host rejects a block.
    const blocks = { [iteratorKey]: () => apply(iterate, value, []) };
    for (const block of blocks) {
      emitBlock(block);
    }
  }
## 2026-11-17 02:48 UTC — exact-head refresh, source-rights hold and pre-match-only ledger audit

### Repository and source-order proof

- Fresh main remains exactly 40887ebb215730190d7a6c7a1693373ec4afcdfc (signed commit dated 2026-10-18 08:20:05 UTC). GitHub branch API confirms protected=false; required-status-check enforcement is off. No branch settings or main ref were changed.
- Main serie_a_v2_forward_capture.py remains blob 5db02cbd1367ed25b994b152acf371421859a014. Its actual main() imports the Supabase reader and calls fetch_saved_upcoming_serie_a_quotes() before discover_archives(); the original source-before-quote defect is still present on main.
- Main .github/workflows/serie-a-v2-forward-preview.yml remains blob 48ce3b0d8e31c4cf293b94500e9c320047311467: job-level Supabase/GitHub credentials are present and its artifact upload is if: always(). Main .github/workflows/serie-a-v2-current-form-source-capture.yml remains blob 9722416862b42d55ff7181003353c39620f23cf2: credentials remain at job scope and source artifact upload is if: always().
- The five-workflow default-deny correction is still not active on main. PR #781 is OPEN / Ready for review / exact HEAD 27da7c204d402b76f1f0a52fc1a3bef845fcc5d2; its eight exact-head GitHub Actions runs all completed SUCCESS. It gates live source/quote/recovery steps and public artifact uploads while preserving existing triggers/schedules and offline tests.
- Child PR #853 pins checkout/setup-python/upload-artifact across all five held workflows. Exact HEAD bf56afdff8e2cb6074d93bef00c0fb8c10428c13, parent #781 exact HEAD above; exact run #43943659300 SUCCESS, 20/20 hold-contract tests. Draft; do not merge ahead of #781. After the owner integrates #781, rebase and fully revalidate this child.

### Latest actual main runtime evidence (16 November; no later run assumed)

- Original Forward-Only Preview run #43927778344, SUCCESS: 71 V2/source/embargo tests; 10 historical CSVs / 3,800 matches attested; quotes_seen=0, forecasts=0, paid calls=0, Supabase writes=0. It nevertheless uploaded public report artifact #14256147981 (1,457 bytes; ZIP SHA-256 9d294114b45c5c820bda2701d86cb9bd3b39eab5b61addfd0f36a8416ed641fc.
- Current-Form Source Capture run #43881612596, SUCCESS: metadata-only feature-input gate 110 identities; 10 historical CSVs / 3,910 rows plus current-season I1.csv with 110 rows; 11 files; artifact #14231524491; ZIP SHA-256 b7f80f8503058cba2b6b6f6fea4c169434349ecd81b1b471b1ae6ddac64b7e6a. No paid calls or Supabase writes.
- Current-Form Forward run #43930085547, SUCCESS: 53 tests; source artifact/parent SHA verified; quotes_seen=0, shadow forecasts=0, target outcomes not read/scored, paid calls=0, writes=0. It nevertheless uploaded public artifact #14257353951 (440,597 bytes; SHA-256 9a95b30c2f16f9e526a37db9eaa5c679603195a66632bdb45795452354f941be.
- Free Real-Quote Diagnostic run #43898091146, SUCCESS: 0 quoted fixtures / 0 diagnostic scores / 0 paid requests / 0 writes; public artifact #14240321194 was uploaded.
- These are workflow/source-artifact executions, not original V2 prediction or quality evidence. Public raw-source/report artifact upload while rights/private-storage clearance is unresolved is the reason to keep #781 as the immediate manual integration priority. Do not dispatch or repeat live capture while the hold remains unmerged.

### Current exact-head V2 PR status

- PR #854: OPEN / Ready for review, exact HEAD a8bb085dc58e486b511fd80a40722b1ac1fa5e60, 8/8 exact-head runs SUCCESS; frozen shadow job logged 101 passed and production .pkl diff guard PASS. Recursive nested-outcome-field embargo only; frozen features/weights unchanged.
- PR #855: Draft child of #850, exact HEAD eca944adb0a70e7f59f5bcff4ec7facf7c3d59d8; exact offline evaluator run #43983729183 SUCCESS, 219 passed, production .pkl diff guard PASS. It distinguishes attempted and returned result-query counts; synthetic tests only.
- PR #856: Draft child of #855, exact HEAD f79186de5e81b1f162676c45ed0e143dbb9b7ddc; exact offline evaluator run #43984469635 SUCCESS, 220 passed, production .pkl diff guard PASS. It pins immutable Actions in the prospective evaluator workflows.
- PR #842: OPEN / Ready for review, exact HEAD 0e14a8d490c72e95820d82453fa0746d5479001f, 7/7 exact-head runs SUCCESS; core shadow-validation job logged 11 passed and production .pkl guard PASS.
- PR #851: OPEN / Ready for review, exact HEAD c79445d10036c39b4d2cc88133434f67399983c5, 7/7 exact-head runs SUCCESS. It pins immutable Actions in the dedicated frozen V2 test workflow.
- Original forward ordering chain remains #837 → #843 → #848, with exact heads 659a15b6d5958d0cc74f08a9b7ef50279684bee3, 725d1c987a9bca1a936008a81dc8458a09791eac, and f766944dfa3f2c2abbc78094408ec0224d94c696. Their offline suites passed 544, 552 and 559 tests per Python 3.11/3.12 run respectively. They remain stacked and inactive on main; do not merge ahead of rights/private-storage parents.
- No PR was merged. #657, #659 and #660 remain previously merged; no duplicate work was created for them.

### Fresh read-only Supabase pre-match ledger

Only odds rows with snapshot_time_utc < commence_time_utc were counted. No score, result, settlement or correctness fields were selected.

| League | Strictly pre-match snapshots | Event IDs | Latest pre-match snapshot (UTC) |
|---|---:|---:|---|
| EPL | 1,135 | 70 | 2026-10-09 15:25:57 |
| La Liga | 798 | 52 | 2026-09-11 15:45:28 |
| Serie A | 620 | 63 | 2026-10-13 14:48:53 |
| Eredivisie | 410 | 39 | 2026-09-11 15:50:20 |
| Bundesliga | 394 | 35 | 2026-09-11 15:49:52 |
| Ligue 1 | 387 | 35 | 2026-09-11 15:49:24 |
| RPL | 153 | 15 | 2026-09-05 15:07:55 |
| Primeira Liga | 9 | 9 | 2026-09-11 16:06:24 |
| Turkey Super Lig | 9 | 9 | 2026-09-11 16:06:26 |
| **Total** | **3,915** | **327** | — |

- product_prediction_snapshots: 40 pre-kickoff rows, all EPL_AI_MARKET_PAIR_V1, model SHA 1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5; latest generated 2026-10-09 15:29:33 UTC. No frozen original V2 SHA row.
- epl_ai_market_pair_ledger: exact read-only aggregate 52 pre-kickoff pairs, all EPL_AI_MARKET_PAIR_V1, same non-V2 model artifact SHA; latest generation 2026-10-09 15:29:33 UTC.
- These tables do not prove an original V2 prospective capture. No Supabase write/DDL was executed.

### Frozen original candidate and evaluation status

- Main candidate JSON blob ac1303f6b096664983fbf52443bd0a381b23ba21; frozen artifact SHA-256 a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6; 19 original features; 20×2 weight matrix; 3,799 training rows.
- active_lambda=0 remains exact de-vigged market fallback; shadow_residual_lambda=1 remains research-only. Stability gate FAILED. Prospective outcome gate remains 0/30.
- No admissible independent prospective sample exists; no Brier/LogLoss superiority claim is allowed.
- No source provider is currently approved for automated AI inference and private raw-response retention. The updated Football-Data rights hold is in #780/#813, not main; #781 is the direct-main interim workflow hold. No source download, inference, target-outcome query, paid provider request, production .pkl change, promotion or bet was performed in this audit.

### Separate Supabase security warning

Supabase Security Advisor observed at 2026-11-17 02:48 UTC reports RLS disabled on five public tables: public.teams, public.predictions, public.match_statistics, public.league_prediction_ledger, and public.epl_ai_market_pair_ledger. No DDL was executed. Enabling RLS without suitable policies can block legitimate app access; see https://supabase.com/docs/guides/database/postgres/row-level-security and let the owner decide the policies.

No main ref, schedule, other agent, Supabase schema/data, paid budget, frozen model contract, production artifact or target-outcome access was changed by this run.
