# SHOTS10 Signal Lab — Closure

Status: **CLOSED AS RESEARCH-ONLY / NO INCREMENTAL MARKET VALUE**

The preregistered `SHOTS10_SIGNAL_LAB_V1` experiment was frozen before outcome inspection and executed once across EPL, La Liga, and Serie A using Football-Data historical match rows.

## Frozen signal

`SHOTS10_V1` used only the previous ten completed matches for each team. The fixed feature family contained home-away differences in total shots for, total shots against, shots on target for, and shots on target against. Current-match shot statistics and future rows were not used; each match snapshot was created before its `HS`, `AS`, `HST`, and `AST` values were appended to team history.

All ten seasons from 2016-2017 through 2025-2026 passed the required shot-column coverage check for each of EPL, La Liga, and Serie A. The resulting continuous research sample contained 3,800 matches per league.

The model family and evaluation were fixed in advance: expanding-season walk-forward with at least three prior training seasons, median imputation, standard scaling, logistic regression, and the primary paired comparison `MARKET_SHOTS10` versus `MARKET_MODEL` on multiclass Brier and log loss. No threshold search or post-result feature selection was permitted.

## Result

The frozen shot signal failed the incremental-information test in all three leagues on aggregate Brier and log loss:

| League | Matches | Seasons | Δ Brier | Δ Log loss | Brier-win seasons | Log-loss-win seasons |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| EPL | 2660 | 7 | +0.002465 | +0.003810 | 1/7 | 1/7 |
| La Liga | 2660 | 7 | +0.002040 | +0.003040 | 1/7 | 1/7 |
| Serie A | 2659 | 7 | +0.001216 | +0.001297 | 2/7 | 3/7 |

Positive deltas mean `MARKET_SHOTS10` was worse than the comparable fitted `MARKET_MODEL`. `SHOTS10_ONLY` contained real predictive information but remained materially weaker than market-based models in all three leagues.

## Decision

Do **not** add `SHOTS10_V1` to the market model. Do not tune the rolling window, select only shots-on-target, select only one league, or search subsets on these already-seen outcomes. Those would be post-selection tuning on the same sample.

The feature family is retained only as a documented negative research result. Any future shot-quality experiment must be a genuinely independent preregistered hypothesis using information not tested here, such as timestamp-safe expected-goals or shot-location quality rather than another transformation of the same `HS/AS/HST/AST` sample.

## Safety

The run changed no production `.pkl`, model, calibrator, threshold, inference path, Supabase row, market ledger, prediction ledger, or live selection logic. Production hashes were identical before and after the experiment.
