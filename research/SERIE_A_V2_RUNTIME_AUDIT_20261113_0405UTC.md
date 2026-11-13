# Original MARKET_ANCHOR_1X2_V2 — runtime and source audit

**Audit time:** 2026-11-13 04:05 UTC  
**Fresh main:** `40887ebb215730190d7a6c7a1693373ec4afcdfc`  
**Scope:** original V2 only; GitHub main/PR/workflow logs and read-only Supabase pre-match metadata. No target outcomes, score/result columns, paid provider calls, Supabase writes/DDL, production artifact changes, or main changes.

## 1. Frozen candidate

The original candidate on main remains SHA-256 `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`, with exactly 19 frozen features and unchanged weights/scaler/imputer/training fingerprint.

- `active_lambda=0` — market anchor.
- `shadow_lambda=1` — research only.
- Stability gate remains FAILED.
- NO_BET; no automatic promotion.
- No legacy XGBoost production model was restored or changed.

## 2. Main remains unheld; #781 is still HUMAN-MERGE only

Re-read main `PROJECT_CONTINUITY.md` and the original forward, free diagnostic, current-form source and recovery workflow files. The main continuity file still starts with the 2026-10-18 entry and does not contain the November runtime addenda.

Main's original forward, free diagnostic and current-form source workflows still contain live/manual or scheduled triggers, Supabase secret scopes, and `upload-artifact` steps with `if: always()`. The workflow-level default-deny hold is not on main.

[PR #781](https://github.com/MaksimBlud/football-ai/pull/781):
- exact HEAD `27da7c204d402b76f1f0a52fc1a3bef845fcc5d2`;
- 43 commits ahead / 0 behind main;
- Ready for review, open, mergeable;
- **8/8 exact-head workflows SUCCESS**;
- Frozen V2 Shadow Tests: **103 PASS**;
- Recovery: **49 PASS**;
- live source/quote/rebuild/proof/upload steps are default-denied; production `*.pkl` hash guard PASS.

The hold is not active on main until owner manual merge and fresh-main verification. No merge was performed.

## 3. Actual main workflow runs and public artifacts

Only run logs and artifact metadata were inspected; no artifact was downloaded or unpacked.

| Workflow run | Result | Artifact metadata |
|---|---|---|
| [Original V2 Forward #43261918181](https://github.com/MaksimBlud/football-ai/actions/runs/43261918181) | 71 tests PASS; source/parent attestation PASS; 0 quotes, 0 forecasts, 0 previews | `13963024080`, 1,459 bytes |
| [Current-Form Source #43232728352](https://github.com/MaksimBlud/football-ai/actions/runs/43232728352) | 19 tests PASS; 110 feature-input identities; 10 historical CSVs + 1 current-season CSV; source SHA verified | `13951945358`, 439,426 bytes; SHA-256 `e7bb6e90466c278882225766424b17c229cab46da35dd80a4418e627c8ccb1e8` |
| [Current-Form Forward #43262798305](https://github.com/MaksimBlud/football-ai/actions/runs/43262798305) | 53 tests PASS; source and parent verified; 0 quotes, 0 lambda-1 shadows, no outcome read/scoring | `13963944149`, 440,582 bytes |
| [Free Diagnostic #43243852372](https://github.com/MaksimBlud/football-ai/actions/runs/43243852372) | 53 tests PASS; no real 19-feature rows, no eligible forecast | `13954739310`, 425,066 bytes |

All four artifacts are still present in the public repository and show expiry on **2027-02-10**. PR #781 gates future live uploads but does not retroactively remove these four existing public artifacts. They were not deleted or downloaded. Provider rights and private retention remain HOLD.

## 4. Open V2 PRs — exact-head CI

- [#796 atomic source archive](https://github.com/MaksimBlud/football-ai/pull/796): HEAD `e69ad9c2700b999ef186e4771a2fe06fd010155d`; 5 ahead / 0 behind main; Ready for review; **7/7 CI SUCCESS**. Integrate only after #781 and fresh-main revalidation.
- [#803 SportAPI audit](https://github.com/MaksimBlud/football-ai/pull/803): HEAD `4a2bb0415d6a5833e25ff7bb0a1fd23e28522087`; **7/7 CI SUCCESS**, 86 frozen V2 tests PASS; Draft. SportAPI remains HOLD because six frozen corner features, upstream rights, ML/private-retention permission and source-time provenance are not established.
- [#798 Stats API audit](https://github.com/MaksimBlud/football-ai/pull/798): updated HEAD `16bbe1404b12c1b24823703b57dafb8cda7311b8`; **6/6 CI SUCCESS**. New official buyer-guide disclosure conflicts with broader endpoint claims; current beta scope and upstream source/rights remain unresolved. HOLD.
- [#804 Live Football API audit](https://github.com/MaksimBlud/football-ai/pull/804): HEAD `f2c2e00df612b06f9e2deda6a0febc8e1fc4ceec`; 3 commits ahead / 0 behind; Draft; **7/7 CI SUCCESS**, including **86 frozen V2 tests PASS**. Documentation + regression guard only; no provider calls or data capture.
- [#793 market-only evaluator](https://github.com/MaksimBlud/football-ai/pull/793): remains Draft and depends on the source-rights stack; exact-head evaluator and V2 suites are synthetic/offline only, not live model-quality evidence.
- [#740 continuity refresh](https://github.com/MaksimBlud/football-ai/pull/740): remains open; this report is the 2026-11-13 addendum to its existing continuity refresh. No merge.

No PR was merged.

## 5. New free-source candidate: Live Football API — HOLD

Official pages reviewed:
- https://www.live-football-api.com/terms
- https://www.live-football-api.com/pricing
- https://www.live-football-api.com/docs
- https://www.live-football-api.com/serie-a-api
- https://www.live-football-api.com/about

The provider documents a Serie A 2026/27 page, 500 one-time free credits, one credit per endpoint call, match corners and goal/card event types, and Terms permitting use in own products and redistribution to end users.

But the public evidence does not establish:
- upstream data provider and field-level rights;
- explicit internal ML feature/inference rights and private raw-response retention;
- availability of complete `/live_match_details` for already completed fixtures;
- exact yellow/red/second-yellow counting parity with the frozen feature source;
- upstream source-observation/correction timestamps.

`last_updated`/`stale` plus a local response SHA can establish when this project received exact bytes, but do not by themselves establish when the upstream fact was first observed or corrected. No account/key was created, no API request or free credit was spent, no data was downloaded. PR #804 records the HOLD.

## 6. Supabase — read-only pre-match data only

Read-only queries selected only pre-match quote timestamps/identities and exact V2 prediction metadata. No scores, result labels, settlements or target-outcome columns were selected.

- Strict `odds_snapshots`: **3,915** pre-match rows / **327** events.
- Latest strict pre-match quote: **2026-10-13 14:48:53 UTC**.
- Strict pre-match rows in last 7 days: **0**.
- Future events with saved pre-match quotes: **0**.
- `product_prediction_snapshots` rows with exact candidate SHA `a9d5abc2...` and generation before kickoff: **0**.

The 30-primary-completed-event outcome gate remains CLOSED. No Brier or LogLoss comparison is admissible.

### Separate critical Supabase security finding

Supabase table metadata reports RLS disabled on:
- `public.teams`
- `public.predictions`
- `public.match_statistics`
- `public.league_prediction_ledger`
- `public.epl_ai_market_pair_ledger`

Supabase's advisor marks this critical: these tables may be exposed to anon/authenticated roles. No DDL was run. Do not blindly enable RLS without policies because that may block legitimate access. Remediation SQL for owner review:

```sql
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.league_prediction_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.epl_ai_market_pair_ledger ENABLE ROW LEVEL SECURITY;
```

Owner must decide the intended read/write policies before applying any change.

## 7. Next safe order

1. Owner manually merges #781, then re-read main and prove every original V2 live source/quote/recovery/artifact path is held.
2. Owner reviews the four already-public Actions artifacts; #781 does not delete them.
3. Revalidate #796 against fresh main before manual merge.
4. Obtain written provider and upstream rights plus field-level source timestamps for any candidate; no source is approved yet.
5. Only after clearance, run a bounded source-only test with exact response bytes, SHA-256, retrieval UTC, null/completeness checks, no quotes and no inference.
6. Run the frozen original 19-feature V2 prospectively without changing its weights/contract. Keep active lambda 0 and shadow lambda 1 research-only.
7. Read target outcomes only after the preregistered 30 eligible completed primary forecasts; then report independent Brier/LogLoss against market.

No main change, PR merge, Supabase write/DDL, paid API request, production `.pkl` change, model-weight/feature change, automatic promotion, bet, schedule change, or target-outcome read occurred in this audit.
