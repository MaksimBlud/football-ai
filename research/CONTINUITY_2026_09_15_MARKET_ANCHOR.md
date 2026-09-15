# Continuity checkpoint — 2026-09-15 — EPL early read + MARKET_ANCHOR_1X2_V1

This checkpoint is documentation-only. Source of truth remains fresh GitHub `main` + live Supabase. Where this checkpoint conflicts with older status language in `PROJECT_CONTINUITY.md`, the newer facts below supersede those older statements; historical records themselves remain unchanged.

## PR #324 — early EPL outcome read / pristine gate retired

PR #324 (`Record early exploratory EPL AI-market interim`) was merged as `57cace46bcf61557837a8235f1239b06813f39eb`.

The user-authorized early read opened outcomes for 11 already-completed `EPL_AI_MARKET_PAIR_V1` fixtures. The underlying predictions remain genuine pre-kickoff prospective records, but the former claim that the full 100-event EPL cohort could remain pristine/no-peek is no longer valid. Do not describe that older primary gate as still pristine or unopened.

A separate 43-match cross-league replay/debug evaluation produced AI underperformance versus market (AI Brier `0.6125651124` vs market `0.5975406259`; AI LogLoss `1.0249478419` vs market `0.9958508866`; accuracy `39.53%` vs `48.84%`). This result is retained only as historical/debug evidence because later identity/freezing review retired that replay contract as primary evidence. It must not be promoted to prospective/frozen proof.

## PR #325 — `MARKET_ANCHOR_1X2_V1`

PR #325 (`Add fail-closed market-anchored 1X2 candidate`) final tested head:

`ace9d9f346c78a1532b5956913fafe9c4bfb3ba5`

Exact-head merge:

`5a818b0babf013d79227a78f3e62237e85c3d16f`

Architecture:

`p = softmax(log(de-vigged_market) + lambda * football_residual)`

- `lambda=0` is exact market identity.
- football-only candidate sets: `FORM`, `FORM_GOALS`, `FORM_GOALS_CORNERS`, `ALL_FOOTBALL`.
- fixed lambda grid: `[0.00, 0.10, 0.25, 0.50, 0.75, 1.00]`.
- train: 2016-2017 through 2023-2024.
- validation: 2024-2025.
- untouched OOT: 2025-2026.
- 2026-2027 and the already-opened September 2026 outcomes are excluded from train/selection/OOT.
- nonzero residual is allowed only when validation beats the market on both multiclass Brier and LogLoss; otherwise that league fails closed to `lambda=0`.
- pooled OOT residual is accepted only when both Brier and LogLoss beat market; otherwise active probabilities are exactly market.
- accuracy cannot override the probabilistic gate.
- research-only; no production promotion; `NO_BET`.

### First untouched OOT

Frozen report: `experiments/market_anchor_1x2_v1_report.json`.

First final-OOT run: `34917928502` on pre-result-tuning head `9898fdea005b6344d638fb65c39e394886bced28`.
Artifact: `10376584443`.
Artifact digest: `sha256:d015b35f305fe934e99559184425ec3b69f165e1f85e57294eddb5a06b771746`.

Pooled 2025-2026 (`n=1140`):

- market Brier `0.588996235405689`;
- candidate Brier `0.5886577613918851`;
- delta Brier `-0.0003384740138039355`;
- market LogLoss `0.9881046787642729`;
- candidate LogLoss `0.9877190854806019`;
- delta LogLoss `-0.0003855932836709375`;
- market accuracy `0.5263157894736842`;
- candidate accuracy `0.5271929824561403`;
- formal V1 gate: `RESIDUAL` accepted.

League behavior:

- EPL: exact market fallback (`lambda=0`), test delta exactly zero.
- La Liga: exact market fallback (`lambda=0`), test delta exactly zero.
- Serie A: `ALL_FOOTBALL`, `lambda=1.0`; Brier delta about `-0.0010154220`; LogLoss delta about `-0.0011567799`; accuracy `0.5421052632` vs market `0.5394736842`.

Interpretation: direction is positive under the frozen gate, but pooled effect size is very small. This is historical temporal OOT evidence, not production-quality proof.

### Corrected robustness

An audit found a diagnostic-only implementation defect: the initial robustness code refit final Serie A weights including validation 2024-2025. Frozen V1 did **not** do that; validation selected configuration only. The defect was fixed and regression-tested so the robustness final split trains only through 2023-2024 and exactly replays the frozen Serie A OOT row.

Corrected run: `34918346551`.
Artifact: `10377595106`.
Artifact digest: `sha256:56ebad616726e6c3f690a4b2c05949e4a5971d1a3a60d828bf65bb054b9b4734`.
Frozen report: `experiments/market_anchor_1x2_v1_robustness_report.json`.

Exact frozen Serie A OOT (`n=380`):

- Brier delta `-0.0010154220414116`; paired-bootstrap 95% interval `[-0.0051650435, +0.0032368771]`; bootstrap probability better than market `0.6831`.
- LogLoss delta `-0.0011567798510133`; paired-bootstrap 95% interval `[-0.0080689479, +0.0060389577]`; bootstrap probability better than market `0.6317`.
- fixed post-selection config wins both metrics in only `2/6` earlier retrospective seasons.

Therefore the positive OOT sign is uncertain: both intervals cross zero and persistence is weak. `MARKET_ANCHOR_1X2_V1` remains **research-only / NO_BET / NO_PRODUCTION_PROMOTION**.

### Freeze/reproducibility guard

A byte-for-byte `cmp` of JSON reports failed only because repeated numerical execution differed in last-bit float serialization (~`1e-16`, e.g. `0.5834232552235167` vs `0.5834232552235168`). The frozen report was **not rewritten**.

PR #325 instead added `market_anchor_1x2_v1_freeze_guard.py`:

- dict/list structure, keys, strings, booleans, integer counts, feature/lambda selections and ordering must match exactly;
- finite float values may differ by at most `1e-12`;
- material metric drift or any selection/status/count/schema change fails CI;
- regression tests verify acceptance of last-bit drift and rejection of changes above tolerance.

This is a reproducibility transport guard only. It does not loosen the model acceptance rule or alter frozen metrics.

## CI / post-merge proof

All eight exact-head PR workflows on `ace9d9f3...` passed, including:

- Product PR Validation;
- Research PR Validation;
- Bundesliga PR Validation;
- Eredivisie PR Validation;
- Ligue 1 PR Validation;
- Serie A PR Validation;
- `MARKET_ANCHOR_1X2_V1`;
- `MARKET_ANCHOR_1X2_V1 Robustness`.

Post-merge `main` proof on `5a818b0b...` also passed:

- `MARKET_ANCHOR_1X2_V1` push run `34918844569` — full semantic frozen replay, fail-closed gate and production `.pkl` hash guard green;
- `MARKET_ANCHOR_1X2_V1 Robustness` push run `34918844547` — exact frozen Serie A replay and production `.pkl` hash guard green.

No production `.pkl` was changed, no paid Odds API call was used, no Supabase write was performed, and no model was promoted.

## Current research decision / execution pointer

1. Do **not** promote `MARKET_ANCHOR_1X2_V1` to production from this evidence.
2. Do **not** tune V1 using the now-open 2025-2026 OOT; any architectural/feature/lambda change must become a separately named new version with fresh evidence.
3. Treat market-anchor as the preferred research architecture over unconstrained bookmaker-odds-as-features deformation because it has an exact market fallback, but not yet as proven alpha.
4. The next legitimate evidence step is fresh prospective validation of the frozen market-anchor construction (or a separately preregistered V2), keeping it isolated from already-open outcomes.
5. `NO_BET` remains binding; forecast probability quality, value selection, betting decision and portfolio exposure remain separate decisions.
6. Product/deployment work remains governed by the separate exact-main/Vercel and product-readiness contracts; this research block does not authorize activation of any new market or product scope.
