# Original MARKET_ANCHOR_1X2_V2 — runtime, pre-match and rights audit (2026-11-13)

**Audit window:** 2026-11-13, approximately 12:51–12:58 UTC  
**Fresh main:** `40887ebb215730190d7a6c7a1693373ec4afcdfc`  
**Scope:** original frozen V2 only; main files, exact open-PR heads/CI, scheduled Actions runs, and read-only Supabase pre-match/fixture-identity metadata.

## 1. Frozen original candidate

- Candidate: `research/models/market_anchor_v2_serie_a_frozen_candidate.json`
- Candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`
- Git blob: `ac1303f6b096664983fbf52443bd0a381b23ba21`
- Original feature-builder blob: `401b3a0893371bfa4a488ec92a4a54af2678c8f7`
- 19 ordered features; 20×2 weight matrix; 3,799 training rows.
- Training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- Training cutoff: `2026-06-30T23:59:59+00:00`.
- `active_lambda=0` (market anchor); `shadow_lambda=1` (research only).
- Stability gate remains FAILED; NO_BET; automatic promotion disabled.

No candidate bytes, feature order, weights, scaler, imputer or production artifact were changed. No legacy XGBoost model was loaded or used.

## 2. Main and scheduled V2 workflows

Main remains `40887ebb215730190d7a6c7a1693373ec4afcdfc`; its continuity file still begins with the 2026-10-18 entry. The November refresh is in open PR #740 only.

Re-read the four main workflow files:

| Workflow | UTC cron |
|---|---:|
| Current-Form Source Capture | `50 5 * * *` |
| Free Real-Quote Diagnostic | `13 6 * * *` |
| Original Forward Preview | `8 8 * * *` |
| Current-Form Forward Preview | `18 8 * * *` |

The date-bounded GitHub Actions query for 2026-11-13 05:30–09:00 UTC returned 24 runs. None matched these four V2 workflow names. Other scheduled workflows did run in the same window (including Serie A Results Sync, Serie A Live Cycle and Multi-Market V2 Cycle), so this is not evidence of a repository-wide Actions outage. The cause of the missing V2 runs is unresolved; workflow enabled/disabled state was not exposed by the available read endpoint. No workflow was dispatched, re-enabled, edited or rescheduled.

Main branch protection remains `protected=false`. No settings were changed.

**Rights conflict:** PR #780 records that the official Football-Data page was updated 2026-11-10 and automated AI/source-capture permission is withdrawn pending written clarification. Main still contains the live schedules; PR #781's default-deny hold is not merged and therefore is not active on main. Do not treat earlier successful captures as evidence of provider permission.

## 3. Supabase — read-only pre-match and identity metadata

Project: `besxwboamipygwvrsblz`.

Strict odds condition: `snapshot_time_utc < commence_time_utc`.

- All leagues: 3,915 strict pre-match rows / 327 unique events.
- Serie A: 620 rows.
- First snapshot: 2026-08-15 12:23:35 UTC.
- Latest snapshot: 2026-10-13 14:48:53 UTC.
- Strict pre-match rows in the last seven days: 0.
- Future events with saved strict pre-match quotes: 0.

In `public.product_prediction_snapshots`, exact candidate SHA `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with both `generated_at_utc < commence_time_utc` and `created_at < commence_time_utc`: 0 rows / 0 events.

The separate Serie A 2026/27 feature-input query selected only `match_date, home_team, away_team` from `public.league_finished_results`:

- 113 rows / 113 unique fixture identities;
- 2026-08-22 through 2026-11-08.

Thus the 30-fixture **feature-input** gate is open (113 ≥ 30). It does not open the separate target-outcome evaluation gate. No score, goals, result, settlement or correctness column was selected. The 30 eligible prospective forecast evaluation gate remains CLOSED at 0/30. No Brier/LogLoss result is available.

## 4. Market-only evaluator — diagnostic only

PR #793 exact HEAD `a7eeb519d967a05bc528c878b0a8fc458cfbe016`; both exact-head workflow runs SUCCESS.

The evaluator pins `FROZEN_INCUMBENT_REFERENCE=None` and fails closed on the full three-way path until a separately approved protocol amendment pins a non-legacy incumbent. Its separate market-only path uses the same 30-unique-eligible-completed-forecast gate and source/parent/quote/kickoff eligibility, compares only de-vigged market (`active_lambda=0`) with original V2 shadow (`shadow_lambda=1`), accepts/loads no incumbent model, and always returns `review_signal=false`.

Exact-head CI is synthetic/offline: 196 evaluator tests PASS; 440 Frozen V2 tests PASS on Python 3.11 and 440 on Python 3.12. These are implementation regressions, not real match-quality evidence. The market-only diagnostic does not amend the frozen policy's full three-way review requirement.

## 5. Open V2 PRs — exact heads

| PR | Exact HEAD | Current state / CI |
|---|---|---|
| [#781](https://github.com/MaksimBlud/football-ai/pull/781) | `27da7c204d402b76f1f0a52fc1a3bef845fcc5d2` | Open, non-draft, mergeable; 8/8 SUCCESS; 103 Frozen V2 tests. First manual-merge candidate. |
| [#796](https://github.com/MaksimBlud/football-ai/pull/796) | `e69ad9c2700b999ef186e4771a2fe06fd010155d` | Open, non-draft, mergeable; 7/7 SUCCESS. Revalidate after #781. |
| [#793](https://github.com/MaksimBlud/football-ai/pull/793) | `a7eeb519d967a05bc528c878b0a8fc458cfbe016` | Draft; 2/2 SUCCESS; based on #787 rights stack, not directly on main. |
| [#804](https://github.com/MaksimBlud/football-ai/pull/804) | `f2c2e00df612b06f9e2deda6a0febc8e1fc4ceec` | Draft; 7/7 SUCCESS; Live Football API source remains HOLD. |
| [#740](https://github.com/MaksimBlud/football-ai/pull/740) | `ed3caa59975ef075f2ec074636b830b0a1035327` before this update | Open; 7/7 SUCCESS; documentation-only net diff before this update. |

Other source audits remain HOLD: #794 Big Balls (upstream rights and provider observation clock), #803 SportAPI (six frozen corner features absent), #798 Stats API (current-season entitlement/provenance/rights), #802 Footballdata.io (Serie A not in Free plan), #797 Cornerflick (upstream rights), #790 open-matchday (non-commercial terms and mixed provenance), #791 Soccer Data (coverage and ML/retention rights), and #800 5Dollar (offline adapter only; Free-vs-Pro Serie A and upstream rights unresolved). No source account/key/request/download was used.

## 6. Supabase security advisor

Latest security advisor reports:
- 5 public tables with RLS disabled: `teams`, `predictions`, `match_statistics`, `league_prediction_ledger`, `epl_ai_market_pair_ledger` (ERROR).
- 4 tables with RLS enabled but no policies: `competitions`, `match_stats`, `matches`, `standings` (INFO).

This is outside the V2 pre-match path but is a material database exposure risk. No RLS, policy, DDL or data change was made. Owner review should design/test policies before enabling RLS, because enabling it without policies can block legitimate access.

References:
- https://supabase.com/docs/guides/database/database-linter?lint=0013_rls_disabled_in_public
- https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy

## 7. Next safe sequence

1. Owner manually reviews and merges #781 only after confirming exact SHA/CI; then verify all live/recovery workflows are default-deny on fresh main.
2. Investigate the missing four scheduled V2 runs using workflow enabled-state/admin visibility; do not dispatch, re-enable or change schedules without owner direction.
3. Revalidate #796 on fresh main after #781.
4. Obtain written upstream/ML/private-retention rights and a source-observation/correction clock before any free-provider ingestion.
5. Preserve exact raw response bytes privately with SHA-256 and capture/quote/kickoff UTC ordering; local retrieval time is not upstream observation time.
6. Run only the frozen original 19-feature V2 shadow prospectively; keep active lambda 0, shadow lambda 1 research-only.
7. Read target outcomes only after 30 eligible completed prospective forecasts, then report Brier/LogLoss against market without any claim of superiority absent real metrics.

No PR merge, main write, schedule change, agent change, paid API request, Supabase write/DDL, production `.pkl` change, model refit, bet, promotion or target-outcome read occurred in this audit.
