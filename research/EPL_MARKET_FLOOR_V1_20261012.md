# EPL 1X2 MARKET-FLOOR V1 — completed research cycle (12 October 2026)

## Result — no validated AI improvement yet

**No safe replacement of production model is justified.** Two independent families of historical corrections were tested, and neither yielded a prospective-style advantage versus the margin-free bookmaker baseline. The only verified candidate that is **not worse than the reference market** is the **identical no-vig market baseline**; this is a *market estimate*, **not a new AI model** or proof of betting advantage. Its scoring equality to the market is by construction, **not** evidence of superior predictive information.

**Do NOT promote this fallback as an AI forecast.** `NO_BET`; no production `.pkl` changed; no data-provider calls or database writes.

### Cohort / chronological replay
Source: historical `public.matches`, league EPL only, **end date strictly before 2025-08-01**, 2016–2019 used to form previous-match rolling features, 2019–2025 priced subset for evaluation. Dataset queried from live Supabase **read-only** on 2026-10-12. Data counts:

| Strict time-split | EPL fixtures with complete decimal 1X2 prices | Use |
|---|---:|---|
| 2019/20–2021/22 | 1,140 | Fit correction / reference priors |
| 2022/23 | 380 | Select model and hyperparameters |
| 2023/24–2024/25 | 760 | Subsequent untouched held-out evaluation |

This is historical replay, **not an instrumented out-of-sample prospective deployment**. Historical `matches.home_odds/draw_odds/away_odds` lack source timestamps, so their prices **cannot be certified as available at a specific pre-match prediction moment**. In particular, no claims about closing-line performance, ROI or actionable value are allowed. Frozen prospective-research event outcomes were never queried.

### Benchmarks: 3-way multi-class losses (lower is better)

| Time slice | Baseline market no-vig Brier | Market log loss | Market favorite accuracy |
|---|---:|---:|---:|
| Validation 2022/23 (380 fixtures) | 0.573674 | 0.965801 | 56.05% |
| Held-out 2023/24–2024/25 (760 fixtures) | **0.556008** | **0.939901** | **56.58%** |

Market-anchored candidate families:
1. **No-vig price temperature `gamma` ∈ {0.8, 0.9, 1, 1.1, 1.2} plus historical unconditional outcome-prior shrinkage `w` ∈ {0, .05, .10, .20, .30}**, 25 predefined combinations. Validation winner improving both metrics: **gamma=1.1, shrink=.1**, validation Brier **0.572941** and log loss **0.965067**. It then **FAILED held-out**: Brier **0.556902** (>0.556008), log loss **0.942372** (>0.939901). Therefore rejected.
2. **Market-anchored multinomial residual** with *only information from team previous five fixtures/last-ten venue games*: prior-only points-per-game difference, goal-difference, shots-on-target, venue win difference, plus intercept. Fit 2019/20–2021/22 exclusively using cross-entropy with predetermined ridge regularization ∈ {.001,.01,.05,.20}, 4 feature dimensions {1,2,3,5}, and mixing weights {.25,.5,.75,1.0}: **64 predefined validation candidates**. Best candidate was intercept-only, ridge=.20, blend=.25 but validation **Brier 0.574045** and log loss **0.966357**, worse than the no-vig reference on **both**. **No candidate met the frozen validation acceptance rule**, so the untouched final cohort was not used to pick a correction. The fail-closed fallback is exactly the market probabilities (which therefore match market's held-out 0.556008 and 0.939901).

The separate temperature check was evaluated before fitting the residual model; its held-out outcome must **NOT** be used to choose a newly favorable hyperparameter family after the fact. Future ideas require another preregistered independent historical/forward period before making claims.

### Runnable independent audit

```bash
python epl_market_floor_v1.py --read-only-historical-supabase
python -m pytest -q tests/test_epl_market_floor_v1.py
```

The report implementation:
- Fetches only `public.matches` where `2016-08-01 ≤ match_date < 2025-08-01`, EPL and historical, paginated read-only. It immediately fails if later data enter the history or any duplicate is found.
- Reconstructs last-five team features and last-ten venue results **before** consuming that fixture's outcome. Emits **aggregate metrics only**, no fixture/outcome dataset; no private product lifecycle or prospective experiment settlement tables.
- Fits the fixed 64 residual alternatives on 1,140 older fixtures, decides solely from 380 validation fixtures using the **joint Brier and log-loss rule**, and only then examines 760 held-out historical matches. If no candidate passes validation, returns the unmodified no-vig market anchor with `MARKET_FLOOR_ONLY_NO_AI_UPLIFT`. If a candidate passes validation but fails holdout, the report returns `RESEARCH_CANDIDATE_FAILED_HELDOUT` and **never** silently switches to a model after seeing outcomes.
- Never writes production pickle or promotes model. A market-only result is labelled **not an AI predictor**.

### Why the existing 2026 model must not be promoted

Separate immutable **product** 1X2 outcome analysis has N=29 settled predictions, model top-pick 10/29, contemporaneous registration-time market favorite 12/29, model Brier 0.674421 vs market 0.646360. There are 20 earlier saved-prediction registrations (6 vs 8 hits) and 9 ordinary live registrations (4 vs 4 hits), and an extreme model HOME top-pick 26/29, DRAW 0/29. The sample is too small for a stable reliability judgment, but certainly does not substantiate a model-over-market claim. This protected product period was **not used for candidate parameter selection**.

### Required next milestone

To deliver a genuine football-AI improvement, rather than market parity, collect **new, genuinely preregistered** out-of-sample same-timestamp odds and independent model outputs under the existing The Odds API *paid-call approval gate* and immutable reliability contracts. Run time-split candidate training on permissible old fixtures, then compare a frozen candidate against no-vig market over a new, predeclared period with scoring/logloss/Brier and calibration. Do not read frozen prospective research outcomes before its gate, retrospectively retune on 2026 product results, dilute `>=100` settled exact-model fixtures spanning `>=4` months, or promise automatic promotion.

**Research-only outcome:** `MARKET_FLOOR_ONLY_NO_AI_UPLIFT`; benchmark meets equality to market because it *is* market, **not** because an AI model was proved superior.
