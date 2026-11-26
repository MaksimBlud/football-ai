# Original MARKET_ANCHOR_1X2_V2 — stability evidence and live-input attribution

**Audit time:** 2026-11-26 02:55 UTC  
**Scope:** original frozen Serie A `MARKET_ANCHOR_1X2_V2` only. This is a read-only evidence-classification audit and offline regression guard. It does not refit, infer, read protected 2026/27 target outcomes, access Supabase for result fields, call a provider, or change the candidate.

## Decision

The V2 stability gate is inherited from the pinned V1 robustness report. Its bootstrap intervals and prior-season dual-metric count are **not V2's own independent OOT performance**. The gate remains FAILED. The current active output remains exact de-vigged market (`active_lambda=0`); `shadow_lambda=1` is research-only.

## Frozen candidate

- SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`
- 19 ordered football features; 20×2 residual weights
- 3,799 training rows, cutoff 2026-06-30
- `active_lambda=0`, `shadow_lambda=1`
- `stability_gate_passed=false`, no automatic promotion, NO_BET

## Exact V1 evidence identity

| Source | Git blob SHA-1 | Role |
|---|---|---|
| `experiments/market_anchor_1x2_v1_report.json` | `9d5e1aad2a9cf5bb833cfea491c4f828d7cb72fd` | V1 feature/lambda selection provenance |
| `experiments/market_anchor_1x2_v1_robustness_report.json` | `96d2f462849a70276a2c27a2c0cc18ec0672b00a` | V1 uncertainty and prior-season robustness |

Frozen V1 robustness observations (2025/26 final OOT, n=380):

| Metric | Observed | Frozen V2 admission requirement |
|---|---:|---:|
| Prior seasons | 6 | exactly 6 |
| Dual Brier + LogLoss wins | 2 | at least 4 |
| Brier bootstrap 95% CI high | +0.0032368771 | below 0 |
| LogLoss bootstrap 95% CI high | +0.0060389577 | below 0 |
| Brier probability better than market | 0.6831 | at least 0.95 |
| LogLoss probability better than market | 0.6317 | at least 0.95 |

The gate fails on both CI upper bounds, both bootstrap probabilities, and the dual-win count. A small negative point estimate does not override the frozen uncertainty requirements. These are V1 values, not V2 performance.

## Two distinct 30-event controls

1. **Feature-input gate:** completed Serie A fixture identities may become lagged inputs after the feature-input threshold. The 2026/27 source capture reported 120 completed prior-day rows; this is feature history only.
2. **Target-outcome evaluation gate:** requires 30 eligible original-V2 pre-kickoff capture rows matched to completed primary fixtures, with authenticated source-before-quote provenance, before target outcomes may be read/scored.

The 120 feature-history events do not count as 120 prospective V2 forecasts. The target-outcome gate remains **0/30**. No target outcomes were read.

## Fresh GitHub Actions evidence on public main

All runs below used main SHA `40887ebb215730190d7a6c7a1693373ec4afcdfc`.

- Source Capture [run #45651589668](https://github.com/MaksimBlud/football-ai/actions/runs/45651589668): 120 completed primary events, 120 current-season prior-day rows, 10 historical-season files, 11 source files; zero paid-provider calls, zero Supabase writes, and no target outcomes scored. It uploaded artifact #15040616453 (440,661 bytes; SHA-256 `831287e5b04743e97ddf7410fa7194836a32964346f6de63d8fcec298175d05e`).
- Its workflow-run child [#45651684165](https://github.com/MaksimBlud/football-ai/actions/runs/45651684165) verified the parent/source archive (3,920 historical rows including 120 current-season rows), but saw **0 quotes and 0 V2 shadow captures**. It still uploaded a second public artifact #15040836400 (441,846 bytes; SHA-256 `2be9e37f4e05fa2ce32d0caf2aedd368ff7cfc56e0fc15dc4fdc40615160b3f5`).
- Later Current-Form Forward [run #45677293419](https://github.com/MaksimBlud/football-ai/actions/runs/45677293419) again reported 0 quotes, 0 shadow captures, and no target-outcome reads; it uploaded artifact #15050714548 (441,847 bytes; SHA-256 `782e136ddcac7c9f83f2dcbfd8bc6e38843fb19d4da24fbc04360fee08769c25`).
- Original Forward [run #45676816331](https://github.com/MaksimBlud/football-ai/actions/runs/45676816331): 3,800 verified historical rows, 0 future quotes, 0 previews, 0 paid calls, 0 Supabase writes.
- Free diagnostic [run #45661222160](https://github.com/MaksimBlud/football-ai/actions/runs/45661222160): 3,800 historical rows, 19-feature contract, 0 feature rows with all 19 observed because no future quote existed, 0 paid requests and 0 Supabase writes; it uploaded public artifact #15045735754 (425,066 bytes; SHA-256 `b5eb1a3c17de5fc06c9bbbc270193f946fd0b285643d36750e397124372b8bc1`).

These artifacts are public because the repository is public. SHA proves byte integrity, not provider permission or private retention rights. The root default-deny/private-storage PR chain remains unmerged; no new source collection should be enabled before manual integration and a fresh-main proof.

## Read-only Supabase pre-match audit

Only `public.odds_snapshots` timestamp/fixture metadata was selected. Conditions:

```sql
snapshot_time_utc < commence_time_utc
AND created_at >= snapshot_time_utc
AND created_at < commence_time_utc
```

- All strict pre-match rows: 3,915 across 9 leagues / 327 events.
- Serie A: 620 strict pre-match rows / 63 events.
- Future strict pre-match rows/events: 0 / 0.
- Latest strict Serie A pre-match snapshot: 2026-10-13 14:48:53.042620 UTC.

No score, result, settlement, or protected 2026/27 target-outcome field was selected. No Supabase write or DDL occurred.

## Provider decision

No reviewed free source is presently cleared for full 19-feature V2 capture:
- Big Balls: promising Free statistics route and private-research terms, but upstream rights, free season depth, field completeness and first-observed/correction semantics remain unresolved.
- OpenFootAPI: research/private storage terms are promising, but Free tier does not document match-level corner/statistics coverage needed for the frozen 19 features.
- footballapi.org: free scope is Premier League only, not the frozen Serie A primary league; retention/training rights and source chronology remain unresolved.
- Football Soccer API: Free is yesterday-only and does not establish the historical statistics required for rolling features.
- PitchAPI: reviewed public docs do not establish data licensing, upstream rights, corners coverage or source chronology.
- Football-Data public CSVs: usable as an integrity diagnostic, but current project rights/retention clearance is not established; public Actions artifact publication is unacceptable as a raw-source store.

Decision remains HOLD / NO INTEGRATION. No provider request, account/key creation, data download, or live source permission is granted by this note.

## Regression guard

The accompanying tests recompute Git blob SHA-1 for both pinned V1 reports, verify the protocol labels the stability source as V1 robustness rather than V2, reconcile the frozen metrics, and pin the original V2 candidate identity and lambda/gate invariants.

No model-quality conclusion is added. A valid independent V2-vs-market assessment still requires admissible prospective captures, the frozen 30-primary-event target-outcome gate, and Brier plus LogLoss against the exact de-vigged market and the frozen incumbent. Until then, active output is market-only and NO_BET.
