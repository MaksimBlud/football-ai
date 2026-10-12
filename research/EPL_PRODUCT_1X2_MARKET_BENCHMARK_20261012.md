# Football AI — product EPL 1X2: frozen model vs bookmaker baseline (2026-10-12)

**Status: DIAGNOSTIC / RESEARCH-ONLY, INCONCLUSIVE.** Checked 2026-10-12 15:26:05 UTC using **read-only SQL aggregates** of `public.product_prediction_lifecycle_events`. This is the *already-settled product forecast history*, **not** a frozen prospective research OOS dataset. Never use these completed matches to post-hoc tune/promote the production model or claim a strategy advantage.

## Source and reproducibility

The immutable join requires one `PREDICTION_REGISTERED` + one `SETTLED` fact on the same `source_prediction_snapshot_id` and exact fixture. The current artifact scope is EPL model 1X2 SHA256 `1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5`. It uses the **frozen** 3-way probabilities, verified settlement scores, and bookie `market_reference_at_registration` (prices present at or before the prediction snapshot). **Not** the closing line, CLV, ROI, payout or realized bet results. Bookmaker probabilities are the inverse decimal odds, **normalized to remove the bookmaker margin**. All comparisons on the **same exact fixtures**. Any missing/ambiguous price fails closed.

Run read-only:

```bash
python report_product_market_benchmark.py --model-sha256 1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5
```

This only reads the existing **product lifecycle table** (requires already-authorized server database credentials). No paid Odds API, Supabase writes, model modification or training. Synthetic unit tests `tests/test_product_market_benchmark.py` are offline and prohibit unsuitable comparisons.

## Exact paired sample

| Sample type | N | Model hits | Market favorite hits | Model Brier | No-vig market Brier | Model log loss | No-vig market log loss |
|:--|--:|--:|--:|--:|--:|--:|--:|
| Retrospectively registered previously saved pre-kickoff forecasts | 20 | 6 (30.0%) | 8 (40.0%) | 0.695962 | 0.671814 | 1.130442 | 1.098960 |
| `live_publish`: published by the usual operational cycle | 9 | 4 (44.4%) | 4 (44.4%) | 0.626554 | 0.589797 | 1.059280 | 0.988050 |
| **All, descriptive aggregate** | **29** | **10 (34.5%)** | **12 (41.4%)** | **0.674421** | **0.646360** | **1.108357** | **1.064540** |

Lower Brier and log loss are better. The market is lower in **both** registration modes and on the overall mixed sample. The market still contains bookmaker information as of registration, not closing information. A 2-fixture hit-rate gap on 29 and 9 live fixtures is **not statistically decisive**.

Other findings (read-only aggregates):
- **Model picks** HOME=26, DRAW=0, AWAY=3. The observed results are HOME=10, DRAW=9, AWAY=10. 9 live forecasts all selected HOME; actual outcomes were HOME=4, DRAW=3, AWAY=2.
- Across the same settled 29, mean model probabilities HOME=51.80%, DRAW=20.99%, AWAY=27.20% versus observed outcome frequencies 34.48%, 31.03%, 34.48%. This **suggests** possible home/draw calibration problems. It does not by itself prove an error, because of very small and non-random sample.
- Model average confidence in selected outcome was 54.17% versus 34.5% correct. This is an indicative aggregate calibration gap; confidence intervals and additional prospective observations are necessary.
- On 19 fixtures with identical model and bookmaker favorite, both were correct 7 times. On 10 disagreements model was correct 3 times and bookmaker 5 times. **Do not post-hoc promote "always follow bookmaker if disagree" based on this split.**
- The 29 source records have valid three-way frozen probabilities and consistent stored settlement scores; all 29 market references had nonnegative source-time age and were no more than 24h before their model registration. This excludes one class of mismatched-time data, not every possible feature/model construction defect.

## Practical conclusions / next independent tests

1. **Audit training/inference classes and feature order, calibration and home advantage** using *historical data before the frozen product period*. Assert `model.classes_` and frozen model feature names before predicting; never simply assume array index 0 is HOME without contract evidence. Inspect `predict_match.py` class-to-outcome mapping and 1X2 calibrator; run separate research-only regression tests. Production `.pkl` unchanged.
2. **Test draw-specific probability calibration** with time-separated walk-forward folds and prior-only calibration, comparing multiclass log loss/Brier against same-date no-vig market. Do not modify frozen product outputs, retrospective event identities or existing decisions.
3. **Resolve actual future inputs under the existing quota policy**, not by sourcing substitute odds. Current 11 future EPL pairs have last stored odds 9 October; new market requests remain subject to separate paid The Odds API permission and reserve. New unpriced matches must remain "no market available".
4. Expand to totals/BTTS only when properly versioned goal-model bundle, truthful probabilities and valid external market comparison are available. Existing snapshot fields have **0/40** populated O/U2.5 or BTTS model-probability rows. Research-only data is not production readiness.

**Frozen gates unchanged:** at least 100 settled same SHA/league product fixtures spanning 4 calendar months before reliability review; even REVIEWABLE never auto PASS/promote. Outcomes of frozen prospective research experiments must remain unread until their separate preregistered gates. `NO_BET`; no ROI/CLV/staking claims.
