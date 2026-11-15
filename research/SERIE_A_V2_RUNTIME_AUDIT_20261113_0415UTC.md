# Original MARKET_ANCHOR_1X2_V2 runtime and access audit — 2026-11-13 04:15 UTC

Repository: `MaksimBlud/football-ai`  
Main SHA: `40887ebb215730190d7a6c7a1693373ec4afcdfc`  
Default branch: `main`  
Frozen candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`

## 1. Frozen candidate re-read from current main

File: `research/models/market_anchor_v2_serie_a_frozen_candidate.json`  
Git blob SHA-1: `ac1303f6b096664983fbf52443bd0a381b23ba21`

- Original ordered football feature vector: 19.
- Weight matrix: 20 × 2 (19 feature rows plus intercept).
- Training rows: 3,799.
- Training fingerprint: `f27ab985ae90bb8e94ba8d548847695888c232f43b3e9be93074f39e1a7a5098`.
- Training cutoff: `2026-06-30T23:59:59+00:00`.
- `active_lambda=0`; `shadow_residual_lambda=1`.
- `stability_gate_passed=false`; `research_only=true`; automatic promotion disabled.

No candidate bytes, feature order, weights, scaler, imputer, or production `.pkl` were changed.

## 2. Current main still has live scheduled source workflows

The following main-branch workflow files were read directly:

| Workflow | Schedule (UTC) | Artifact behavior |
|---|---:|---|
| `serie-a-v2-current-form-source-capture.yml` | 05:50 daily | `if: always()`, 90-day artifact |
| `serie-a-v2-free-real-quote-diagnostic.yml` | 06:13 daily | `if: always()`, 90-day artifact |
| `serie-a-v2-forward-preview.yml` | 08:08 daily | `if: always()`, 90-day artifact |
| `serie-a-v2-current-form-forward-preview.yml` | 08:18 daily | `if: always()`, 90-day artifact |

The current-form source workflow downloads Football-Data CSVs after a metadata-only feature-input gate. Its current-form forward reader verifies the source artifact and its successful parent run before examining saved quotes. The original forward workflow separately verifies the historical archive and then reads already-saved quotes. None of these workflows makes a paid odds request itself.

**Policy conflict:** PR #780 records that the official Football-Data `/data` page was updated 2026-11-10 and now describes free data as for private individuals, excluding commercial or data-training products using automated bots, scrapers, or AI. The project's conservative manifest therefore sets automated source capture and inference permission to false pending written clarification. The main schedules above nevertheless remain enabled until the owner manually merges the default-deny hold. Do not treat the earlier successful captures as evidence of provider permission.

## 3. Actual main-branch Actions runtime (logs read)

All four runs below used main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc` and completed successfully. Success means the workflow ran as coded; it does not clear the source-policy issue or prove model quality.

### Current-form source capture

[Run 43232728352](https://github.com/MaksimBlud/football-ai/actions/runs/43232728352)

- Feature-input metadata gate: 110 unique completed primary fixture identities.
- Current-season completed prior-day CSV rows: 110.
- Historical files: 10; total source files: 11.
- Historical rows: 3,910.
- Candidate SHA matched the frozen candidate.
- 0 paid provider calls; 0 Supabase writes; target outcomes not scored.
- Artifact ID `13951945358`; 439,426 bytes; ZIP SHA-256 `e7bb6e90466c278882225766424b17c229cab46da35dd80a4418e627c8ccb1e8`.

### Current-form forward preview

[Run 43232894044](https://github.com/MaksimBlud/football-ai/actions/runs/43232894044)

- Authenticated source artifact and successful parent source run.
- Source age at verification: 48 seconds.
- `quotes_seen=0`; `v2_current_form_shadow_captured=0`.
- No target outcomes read/scored; evaluation gate closed.
- Artifact ID `13951795906`; 440,577 bytes; ZIP SHA-256 `5b522ac1c95cee939f2120f584c131c8a51ae3cfd7b6ead882ec09e534037d65`.

### Free historical diagnostic

[Run 43243852372](https://github.com/MaksimBlud/football-ai/actions/runs/43243852372)

- Historical source: 3,800 rows.
- 0 quoted fixtures, 0 feature rows, 0 V2 previews.
- `eligible_for_frozen_prospective_cohort=false`; `no_bet=true`.
- Mode: `RESEARCH_ONLY_UNVERIFIED_PROVENANCE_NO_BET`.
- Artifact ID `13954739310`; 425,066 bytes; ZIP SHA-256 `b81100b497ce689aa339da25853999c2ffe306eb7fc3541fc0fb22f2c4ccbb95`.

### Original V2 forward-only preview

[Run 43261918181](https://github.com/MaksimBlud/football-ai/actions/runs/43261918181)

- Real historical source ZIP attestation: SHA verified, 10 pre-prospective CSVs, 3,800 historical results.
- `quotes_seen=0`; `v2_diagnostic_previews_captured=0`.
- 0 paid provider calls; 0 Supabase writes; no target-outcome evaluation.
- Artifact ID `13963024080`; 1,459 bytes; ZIP SHA-256 `f7cd7ec7d7b20138dbfad18d510464026308e1a5d89e530b801a6bcfd01c56b2`.

All four artifacts remain unexpired and are downloadable from this public repository's Actions pages; each currently expires on 2027-02-10. PR #781 prevents future workflow uploads after it is manually merged, but it does not delete already-published artifacts. No artifact was downloaded or deleted in this audit.

## 4. Fresh read-only Supabase check — pre-match odds only

Project: `besxwboamipygwvrsblz`. Query condition: `snapshot_time_utc < commence_time_utc AND snapshot_time_utc <= now()`. No result, score, settlement, or outcome columns were selected.

| League | Strict pre-match rows | Events | Latest snapshot UTC |
|---|---:|---:|---|
| Bundesliga | 394 | 35 | 2026-09-11 15:49:52 |
| EPL | 1,135 | 70 | 2026-10-09 15:25:57 |
| Eredivisie | 410 | 39 | 2026-09-11 15:50:20 |
| La Liga | 798 | 52 | 2026-09-11 15:45:28 |
| Ligue 1 | 387 | 35 | 2026-09-11 15:49:24 |
| Primeira Liga | 9 | 9 | 2026-09-11 16:06:24 |
| RPL | 153 | 15 | 2026-09-05 15:07:55 |
| Serie A | 620 | 63 | 2026-10-13 14:48:53 |
| Turkey Super Lig | 9 | 9 | 2026-09-11 16:06:26 |
| **Total** | **3,915** | **327** | **2026-10-13 14:48:53** |

Strict pre-match rows in the last seven days: **0 for every league**.  
Rows in `product_prediction_snapshots` with the exact frozen V2 SHA and `generated_at_utc < commence_time_utc`: **0 rows / 0 events**.

No Supabase write or DDL was performed. No 2026/27 target outcomes were queried.

## 5. Supabase security finding — surfaced, not changed

The read-only schema inspection returned a Critical RLS-disabled advisory for five public tables:

- `public.teams`
- `public.predictions`
- `public.match_statistics`
- `public.league_prediction_ledger`
- `public.epl_ai_market_pair_ledger`

These tables may be exposed to the `anon` and `authenticated` roles. This is outside the V2 research data path but is a material project security issue. Do not apply RLS without first designing and testing the required policies; no DDL was run.

Supabase's suggested enablement statements, for owner review only:

```sql
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.match_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.league_prediction_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.epl_ai_market_pair_ledger ENABLE ROW LEVEL SECURITY;
```

## 6. Open V2 PR state and exact-head CI

| PR | Purpose | Exact-head result | State |
|---|---|---:|---|
| [#781](https://github.com/MaksimBlud/football-ai/pull/781) | Default-deny hold for live source/quote/recovery workflows | 8/8 success; 103 Frozen V2 tests | Open, non-draft, HUMAN-MERGE |
| [#795](https://github.com/MaksimBlud/football-ai/pull/795) | Reject ambiguous source clocks | 7/7 success | Open, non-draft |
| [#796](https://github.com/MaksimBlud/football-ai/pull/796) | Atomic current-form archive publication | 7/7 success | Open, non-draft |
| [#803](https://github.com/MaksimBlud/football-ai/pull/803) | SportAPI rights/coverage audit | 7/7 success | Open, draft, HOLD |
| [#804](https://github.com/MaksimBlud/football-ai/pull/804) | Live Football API rights/coverage audit | 7/7 success | Open, draft, HOLD |

#781 exact head: `27da7c204d402b76f1f0a52fc1a3bef845fcc5d2`, base main `40887ebb215730190d7a6c7a1693373ec4afcdfc`. It adds `MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED=false` to the relevant workflows and skips candidate rebuild, live capture/inference and artifact publication. It is not merged; therefore it is not yet protecting main.

#787 and #793 are an additional direct-entrypoint/evaluator stack whose bases are other research branches, not main. They must be reviewed in dependency order rather than treated as independently mergeable main PRs. #780 records the Football-Data policy recheck. #800's offline 5Dollar adapter remains HOLD because the Free-vs-Pro Serie A entitlement conflicts and upstream rights/private retention/field semantics are unresolved. #802 records that Footballdata.io's Free plan does not include Serie A.

## 7. Scientific status and next actions

- The original candidate remains saved and byte-identifiable; no refit or restoration from the legacy XGBoost production model is needed.
- Main has 0 prospective forecasts carrying the exact original V2 SHA.
- The pre-match quote ledger has no new rows in the last seven days.
- The 30-primary-completed-event feature-input gate and the separate 30-eligible-prospective-forecast outcome-evaluation gate must not be conflated. The latter remains CLOSED.
- No Brier/LogLoss comparison exists. No claim of V2 superiority, calibration, production readiness or betting value is justified.
- `active_lambda=0` remains the market; `shadow_lambda=1` remains research-only.

Next: owner manually merges #781 only after reviewing its exact SHA/CI; verify the fresh main workflows are default-deny; separately handle old public artifact exposure with an owner-approved retention/removal decision; obtain written provider clearance before any further automated Football-Data capture; then review #795 → #796 and the direct-access rights stack in dependency order. No paid API, source download, Supabase write/DDL, production model change, schedule edit or target-outcome read was performed in this audit.
