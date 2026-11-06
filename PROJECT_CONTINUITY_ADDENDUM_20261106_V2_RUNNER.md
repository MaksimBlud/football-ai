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
