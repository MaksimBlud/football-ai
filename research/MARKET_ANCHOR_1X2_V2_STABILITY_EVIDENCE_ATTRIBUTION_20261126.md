# Original MARKET_ANCHOR_1X2_V2 — stability-evidence attribution audit

**Audit date:** 2026-11-26 UTC  
**Scope:** original frozen Serie A `MARKET_ANCHOR_1X2_V2` only. This is a read-only evidence-classification audit plus an offline regression guard. It does not refit, infer, read 2026/27 target outcomes, access Supabase, call a provider, or change the candidate.

## Decision

The original V2 stability gate is **explicitly inherited from the frozen V1 robustness report**. Its bootstrap intervals and prior-season dual-metric count are not a direct historical OOT estimate of the V2 19-feature residual. The gate remains **FAILED** exactly as frozen. This audit does not change or reinterpret its thresholds.

The original V2 candidate is still the distinct frozen artifact:

- candidate SHA-256: `a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6`;
- 19 ordered football features and a 20×2 residual-weight matrix;
- 3,799 training rows through 2026-06-30;
- `active_lambda=0` (exact de-vigged market fallback);
- `shadow_residual_lambda=1` (research-only);
- `stability_gate_passed=false`, `research_only=true`, no automatic promotion.

The V2 refit recipe inherits the V1-selected Serie A `ALL_FOOTBALL` residual specification, but the V2 candidate's own weights/scaler/imputer and training fingerprint are frozen separately. The V1 report is used only as the conservative admission guard declared by the original V2 protocol.

## Exact source identity

The protocol pins two historical V1 source files by Git blob SHA-1:

| Source | Git blob SHA-1 | Purpose |
|---|---|---|
| `experiments/market_anchor_1x2_v1_report.json` | `9d5e1aad2a9cf5bb833cfea491c4f828d7cb72fd` | V1 feature/lambda selection provenance |
| `experiments/market_anchor_1x2_v1_robustness_report.json` | `96d2f462849a70276a2c27a2c0cc18ec0672b00a` | V1 uncertainty and prior-season robustness evidence |

The protocol's `provenance.source_experiment` is `MARKET_ANCHOR_1X2_V1`; its `stability_gate.evaluation_source` is `MARKET_ANCHOR_1X2_V1_ROBUSTNESS`. The regression test computes each Git blob SHA from the exact repository bytes and checks both against the protocol, then checks that the protocol's displayed gate observations equal the pinned V1 report.

## What the inherited V1 robustness evidence says

The pinned V1 robustness report records a 2025/26 final OOT slice of 380 matches. Its uncertainty evidence is:

| Frozen gate quantity | Observed V1 value | Frozen V2 requirement |
|---|---:|---:|
| Prior seasons | 6 | exactly 6 |
| Prior-season dual Brier + LogLoss wins | 2 | at least 4 |
| Brier bootstrap 95% CI high | +0.0032368771 | below 0 |
| LogLoss bootstrap 95% CI high | +0.0060389577 | below 0 |
| Bootstrap probability better than market — Brier | 0.6831 | at least 0.95 |
| Bootstrap probability better than market — LogLoss | 0.6317 | at least 0.95 |

The gate therefore fails on the dual-win count, both confidence-interval upper bounds, and both bootstrap probability requirements. A lower point estimate on the final V1 OOT slice does not override those frozen uncertainty requirements.

**Interpretation limit:** these numbers describe the pinned V1 robustness evidence. They must not be labelled as V2's own OOT Brier/LogLoss, and they do not establish either V2 superiority or V2 inferiority. The gate's role is to keep V2 active at the exact market until its separate prospective evidence is admissible.

## Separate prospective gates

Do not conflate the two 30-event controls in the current-form addendum:

1. The feature-input gate counts canonical, completed Serie A fixture identities using only date/home/away metadata. It allows completed 2026/27 matches to become lagged features for later future fixtures; it is not an outcome-evaluation sample.
2. The target-outcome evaluation gate requires 30 eligible, genuinely prospective V2 forecasts from that cohort to have completed before target outcomes may be read/scored.

The 120-event source feature-input count recorded in the 2026-11-25 source archive does **not** count as 120 prospective forecasts. The separate target-outcome gate remains closed at 0/30. The old 2026-10-13 quotes cannot be backfilled because the verified source archive was created later.

## Current pre-match evidence check — 2026-11-26 00:55 UTC

A read-only query of `public.odds_snapshots` used only pre-match timing metadata:

- total saved snapshot rows: 3,966;
- future rows/events: 0 / 0;
- future rows/events satisfying `snapshot_time_utc < commence_time_utc` and `snapshot_time_utc <= created_at < commence_time_utc`: 0 / 0;
- latest saved snapshot: 2026-10-13 14:48:53.042620 UTC.

No score, result, settlement, or protected 2026/27 target-outcome field was selected. No database write or DDL was performed.

The latest verified main runtime still has no saved quote for a future event, so it produced no new V2 preview. The public Football-Data source/forward workflows remain a rights/privacy hold pending the manual integration of the default-deny chain; a matching SHA proves byte integrity, not provider permission.

## Regression guard added

The accompanying offline test:

- recomputes Git blob SHA-1 for both V1 source reports;
- verifies the protocol labels the stability evidence as V1 robustness, not V2;
- reconciles the protocol's frozen observed metrics against the exact V1 report;
- verifies the original V2 candidate SHA, 19-feature order, 20×2 weights, training-row count and lambda/gate invariants.

It changes no production artifact, model code, weights, thresholds, gates, schedules, Supabase data/schema, or provider permissions.

**No model-quality conclusion is added.** A valid independent V2-vs-market comparison still requires admissible prospective captures, the frozen outcome gate, and both Brier and LogLoss evaluated against the exact de-vigged market and an admissible incumbent. Until then the active output remains market-only and `NO_BET`.
