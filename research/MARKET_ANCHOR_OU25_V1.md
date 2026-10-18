# MARKET_ANCHOR_OU25_V1 — preregistered historical research contract

Status: **RESEARCH ONLY / FIXED BEFORE FIRST O/U 2.5 HISTORICAL RUN / NO PRODUCTION PROMOTION**.

## Question

Does fixed pre-match football state add incremental probability information beyond the de-vigged bookmaker **Over/Under 2.5 goals** market, when the market remains a mandatory prior and the candidate fails closed to the exact market if incremental value is not demonstrated?

This is a new market question. Previous Historical Football Signal Lab and Market Anchor 1X2 work evaluated H/D/A; this contract does not reinterpret those 1X2 results as evidence for totals.

## Data and temporal split

- Source: Football-Data CSV, using the same EPL, La Liga and Serie A historical provider configuration already used by the repository.
- Seasons: `2016-2017` through `2025-2026`.
- Train: `2016-2017..2023-2024`.
- Validation/selection: `2024-2025`.
- Untouched final OOT: `2025-2026`.
- 2026/27 and opened September 2026 outcomes are excluded.
- Historical rolling football features are built strictly before each fixture outcome is appended to team history.

## Market definition

Only the standard/non-closing O/U 2.5 pair is eligible. Deterministic source priority per row is:

1. `Avg>2.5 / Avg<2.5`;
2. `BbAv>2.5 / BbAv<2.5` (legacy consensus naming);
3. `B365>2.5 / B365<2.5`;
4. `P>2.5 / P<2.5`.

Closing fields such as `AvgC>2.5`, `B365C>2.5`, etc. are deliberately excluded so the 2019/20+ closing feed is not mixed with earlier seasons that only contain the standard price set.

Market probability is the normalized inverse-odds probability of Over 2.5. A league-season must have at least 90% valid paired O/U market coverage or the run fails closed.

## Target

`Over 2.5 = 1` when full-time home goals + full-time away goals >= 3; otherwise `0`.

## Fixed football feature variants

Two variants are allowed before validation is read:

- `GOALS10`: home/away 10-match goals-for/goals-against state plus venue-specific 5-match goal state.
- `GOALS_CORNERS10`: the exact `GOALS10` block plus analogous 10-match and venue-5 corner state.

No other features, windows, interactions or thresholds may be added after observing validation/test performance in V1.

## Architecture

The de-vigged market Over probability `m` is the mandatory prior. A regularized football-only residual logit `r(x)` is fit on training data and combined as:

`p = sigmoid(logit(m) + lambda * r(x))`.

`lambda=0` is exact market identity. Fixed lambda grid: `[0.00, 0.10, 0.25, 0.50, 0.75, 1.00]`. Fixed L2 penalty: `1.0`.

Within each league, non-zero residual is admissible on 2024/25 validation only if it improves **both** Brier and LogLoss versus the market. Otherwise that league selects exact market (`lambda=0`). Among admissible candidates, selection is lowest LogLoss, then Brier, then lower lambda, then feature name.

## Untouched OOT gate

The selected per-league configurations are evaluated once on 2025/26. The pooled residual candidate is accepted only if pooled OOT Brier **and** pooled OOT LogLoss are both lower than the de-vigged market. Otherwise the active V1 output is exact market fallback.

Accuracy is descriptive only. No betting threshold, edge cutoff, ROI optimization, stake sizing, Kelly rule, team filter, league exclusion, or post-result subgroup search is authorized in V1.

## Safety / interpretation

- Research only; no `.pkl` training or promotion.
- No Supabase write and no paid provider call.
- No frozen prospective cohort outcome read.
- Historical totals evidence is not production evidence.
- A positive OOT result would justify robustness diagnostics, not betting activation.
- A negative result closes this exact V1 hypothesis; it must not trigger same-sample threshold/window mining.
- Source/schema plumbing may be repaired if the first run fails for non-performance reasons, but the statistical contract above must not change after the first O/U run begins.
