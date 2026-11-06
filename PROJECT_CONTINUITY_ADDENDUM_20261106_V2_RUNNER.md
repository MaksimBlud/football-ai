# Original MARKET_ANCHOR_1X2_V2 — runner identity-gate audit
Date: 2026-11-06 05:57 UTC

## Exact-head regression

PR #717 runner branch HEAD:
`ca61cb719698e82296783f858a6044ba8d4eb881`

The existing completed-fixture gate test now asserts the exact frozen query filters:
- `league = SERIE_A`
- `season = 2026-2027`
- `match_date < current UTC date`

The fixture includes both raw labels `Atalanta BC` and `Atalanta` for the same match; the original V2-local alias must collapse them to one canonical identity.

Exact push CI:
https://github.com/MaksimBlud/football-ai/actions/runs/42171360461

Result: SUCCESS, 47 passed. The live runner job was skipped as designed. No manual live dispatch occurred.

## Read-only Supabase evidence

The metadata-only query selected only `match_date, home_team, away_team` from `league_finished_results`, filtered to `SERIE_A / 2026-2027` and dates before the current UTC date.

- Raw rows: 103
- Canonical fixture identities: 100
- First date: 2026-08-22
- Last date: 2026-11-02

The three excess raw rows are the known Atalanta/Atalanta BC duplicate representations. No score/result columns were selected; no protected target outcomes were read.

Odds ledger aggregate:
- Total snapshots: 3,966
- Strictly pre-kickoff: 3,915
- Last seven days: 0
- Future pre-match snapshots: 0
- Latest snapshot: 2026-10-13 14:48:53 UTC

Therefore no quote-backed prospective V2 forecast exists yet. Brier/LogLoss remain uncomputed.

## Runtime and integration state

- Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`.
- The filtered Actions query returned no matching 05:50 source-capture run at audit time. This is recorded as not-yet-evidenced, not as a confirmed skipped schedule.
- PR #705 remains unmerged; its shared 170-hour download budget and offline-push guard are not active on main.
- Safe Engineering Agent Auto-Merge run #42166631172 logged `SAFE_AUTO_MERGE_HEALTHY_NOOP: no eligible bot PR with verified six-check CI`; no PR was merged by that run.

No main update, PR merge, source request, paid provider call, Supabase write/DDL, target-outcome read, live runner dispatch, model/weight/feature/policy change, production `.pkl` change, or schedule change occurred in this audit.

## Runner workflow rebase-trigger hardening — 2026-11-06 05:59 UTC

PR #717 exact HEAD is now `e34db80989f038ba73875d2551b3173918aa5d98`. The custom offline workflow's `pull_request.branches` now includes both `main` and the current stacked #716 base branch. This prevents the runner's own regression workflow from silently ceasing to trigger after #716 is HUMAN-MERGED and #717 is rebased/retargeted to main. A workflow-contract regression asserts both targets.

Exact-head CI on the same SHA: push run [#42171598196](https://github.com/MaksimBlud/football-ai/actions/runs/42171598196) and PR run [#42171600478](https://github.com/MaksimBlud/football-ai/actions/runs/42171600478) both SUCCESS, **47 passed** each; the live runner job was skipped in both runs. No live dispatch or external/database access occurred.


## Runner report serialization correction — 2026-11-06 07:58 UTC

PR #717 current exact HEAD: `89fd1a24d72fc7e74f76ebf0e4865307894f3f38`.

A code review of the actual runner found that its report writer appended the two literal characters `\\n` instead of a real newline. That would leave invalid trailing data after the JSON document, so a successful live run could upload a report that downstream tooling could not parse. This is an output-integrity defect, not a model or forecast defect.

Fixed by introducing `_write_json_report()`, which serializes the aggregate report as UTF-8 JSON and appends an actual newline. Added a regression that reads the emitted bytes, requires a real terminal newline, rejects a literal backslash-n suffix, and round-trips the complete report through `json.loads`.

Exact-head CI on `89fd1a24d72fc7e74f76ebf0e4865307894f3f38`:
- Push run [#42184234008](https://github.com/MaksimBlud/football-ai/actions/runs/42184234008) — SUCCESS, **48 passed**; live job skipped.
- Pull-request run [#42184238300](https://github.com/MaksimBlud/football-ai/actions/runs/42184238300) — SUCCESS, **48 passed**; live job skipped.

These are offline checks only. No live artifact scan, Supabase read, source request, or outcome read occurred. The runner remains Draft and stacked on #716; no merge or main change occurred.

## Source-budget and integration recheck — 2026-11-06 07:58 UTC

- PR #705 remains open at `f3e7451ee9cebc9280a8f86421a509d9bc177da0`; all eight exact-head PR checks remain SUCCESS. Its shared 170-hour/two-session source budget is still not active on main.
- The Nov 6 05:50 and 06:13 source workflows have no corresponding runs in the checked Actions window. This is only an observation that no run is recorded, not evidence that schedules are disabled. Next unchanged slots are Nov 7 05:50 and 06:13 UTC.
- PR #699 remains open at `a6725ca49e90d551baa7e9f647151f7e524e42c7`, with seven exact-head checks SUCCESS. A direct compare of #705 HEAD against #699 HEAD reports diverged histories (152 commits ahead on #699's side and 43 commits on #705's side); the workflow overlap still requires a deliberate reconciliation. No automatic merge/rebase was performed.
- PR #714 is a branch-trigger-only derivative of #705: its three-file diff adds the #714 branch name to push filters while retaining the same offline validation and budget behavior already present in #705. It adds no distinct main runtime protection and should not be treated as an independent merge prerequisite.
- Current read-only Supabase aggregate: 3,966 odds snapshots; 3,915 strictly pre-kickoff; 0 strictly pre-kickoff in the last seven days; 0 future events with saved pre-kickoff quotes; latest snapshot 2026-10-13 14:48:53 UTC.
- Identity-only Serie A 2026/27 gate query: 103 raw rows / 100 canonical identities after the frozen Atalanta alias, through 2026-11-02. No result or score columns were selected. Eligible completed forecasts remain 0/30; no Brier/LogLoss or protected outcomes were read.

The original candidate SHA, 19-feature order, 20×2 weights, `active_lambda=0`, `shadow_residual_lambda=1`, stability gate, production `.pkl`, Supabase data, and workflow schedules remain unchanged.
