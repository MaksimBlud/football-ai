# SEASON_INVARIANT_CORNERS_V1 — Results

Status: HISTORICAL PRIMARY RESULT COMPLETE

## Evidence provenance

The underlying season-by-season metrics already existed in the completed PR #57 Historical Football Signal Lab before this V1 block. Therefore this block is a repeatable retrospective portability audit, not a new independent prospective trial.

Primary season evidence:
- PR: #57
- head SHA: `ccd8ac88c7948cfdd0075dbe36ae1939e36a29fc`
- workflow run: `33772658431`
- artifact id: `9900313244`
- artifact digest: `sha256:711b12ee40c66555fc9039f2abdbb244d457591e72bf03cc17f5bb5d856bb7fa`
- artifact created: 2026-09-03

The pinned paired season reference used by the deterministic V1 audit has repository digest:
`dbca91d70590a03acc892f65a72ae46518582d27282882f3dba17fbe47cbd01f`.

The pinned early-drift summary was derived from the same PR #57 point-in-time artifact using expanding-season training and chronological held-out-season prefixes. Its repository digest is:
`643c51418fd385e6a961ef356c8b7fe704c4bb749a7527262906c049b8962ca1`.

No 2026-2027 prospective outcomes were used.

## Primary result: CORNERS10 vs GOALS10

Lower Brier and log-loss are better.

| League | Unseen test seasons | Mean Brier delta | Brier wins | Mean log-loss delta | Log-loss wins | Classification |
|---|---:|---:|---:|---:|---:|---|
| EPL | 7 | -0.005147 | 6/7 | -0.007027 | 6/7 | STRONG |
| La Liga | 7 | -0.004641 | 5/7 | -0.005603 | 5/7 | STRONG |
| Serie A | 7 | -0.006509 | 7/7 | -0.010516 | 7/7 | STRONG |

Overall classification: **PORTABLE_STRONG**.

Across the three leagues, `CORNERS10` beat `GOALS10` on Brier in **18 of 21** held-out season tests and on log-loss in **18 of 21**.

Plain-language interpretation: the useful information in recent corner history is not concentrated in one league or one season. It repeatedly improves a comparable football-only 1X2 model on seasons that were not used for fitting.

## Window robustness

The older PR #57 artifact already contains fixed 5-match and 10-match windows.

For `CORNERS5` vs `GOALS5`:
- EPL: mean Brier delta -0.006640; Brier wins 6/7; mean log-loss delta -0.009855; log-loss wins 5/7.
- La Liga: mean Brier delta -0.004026; Brier wins 6/7; mean log-loss delta -0.005248; log-loss wins 6/7.
- Serie A: mean Brier delta -0.008301; Brier wins 7/7; mean log-loss delta -0.012598; log-loss wins 7/7.

This is important because the result is not dependent on exactly one magical 10-match window.

The fixed 15-match robustness check remains **pending**. The old artifact predates `CORNERS15`, and Football-Data is currently returning HTTP 503 even on historical CSV paths. We do not replace the source, reconstruct a selected result, or weaken the check just to make it complete.

The primary `PORTABLE_STRONG` result does not depend on the pending 15-match check.

## Early-season drift: do we really need to wait 100 matches?

We simulated a new season using the same historical held-out seasons. For each season the model trained only on earlier seasons, then we looked at the cumulative result after 20, 40, 80 and 160 matches.

The most useful comparison is `CORNERS10` vs `GOALS10`:

| Matches into held-out season | Brier direction agrees with full season | Log-loss direction agrees with full season | CORNERS10 Brier better at checkpoint | CORNERS10 log-loss better at checkpoint |
|---:|---:|---:|---:|---:|
| 20 | 66.7% | 76.2% | 71.4% | 81.0% |
| 40 | 66.7% | 76.2% | 71.4% | 71.4% |
| 80 | **81.0%** | **90.5%** | 66.7% | 76.2% |
| 160 | 81.0% | 85.7% | 76.2% | 71.4% |

Against the simpler `FORM10` baseline, the same pattern is visible: 20 matches are noisy, 40 are informative but uncertain, and around 80 matches the direction agrees with the eventual season result in roughly 81-86% of historical tests.

### Practical interpretation

We do **not** need a rigid rule that every new signal must wait for 100 fresh matches before we can learn anything.

For future non-overlapping drift monitoring:
- about **20 matches** = too noisy for a decision;
- about **40 matches** = useful early warning;
- about **80 matches** = materially stronger confirmation that the historical relationship is still present or has changed;
- 160 matches can add evidence, but this historical audit did not show that it must always be better than the 80-match checkpoint.

This changes the role of fresh data. Historical cross-season/cross-league testing provides the main structural evidence; fresh matches are used to detect drift much earlier instead of rediscovering the whole signal from zero every season.

These checkpoints are not automatic model-promotion gates and cannot be used to read outcomes belonging to an existing frozen prospective experiment before its allowed evaluation gate.

## Incremental value over bookmaker market

Because the football-only result is `PORTABLE_STRONG`, we revisit the already completed MARKET vs MARKET_CORNERS10 evidence from PR #58.

Historical paired result for `MARKET_CORNERS10` vs fitted `MARKET_MODEL`:
- EPL: Brier wins 0/7, log-loss wins 0/7; mean deltas are worse (+0.003621 Brier, +0.006270 log-loss).
- La Liga: Brier wins 0/7, log-loss wins 0/7; mean deltas are worse (+0.005055 Brier, +0.007899 log-loss).
- Serie A: Brier wins 2/7, log-loss wins 2/7; mean deltas are worse overall (+0.003496 Brier, +0.005427 log-loss).

Plain-language interpretation: `CORNERS10` is a real and portable football-state signal, but the historical 1X2 bookmaker market already appears to contain most or all of that information. Adding it on top of market probabilities did not improve the historical market model.

Historical bookmaker prices in this lab are research data; their timestamp is not assumed to be identical to the live prediction-time market snapshot.

## Decision

1. Keep `CORNERS10` as a validated, portable football-state signal.
2. Do **not** promote it as a proven 1X2 betting edge over the bookmaker market.
3. Do not change production `.pkl` models from this result.
4. Use the signal as a candidate ingredient for other targets where the market may not already absorb the same information, especially corners-specific research.
5. Replace the simplistic "wait 100 matches for every idea" mindset with historical portability + early drift monitoring: 40 matches as a warning checkpoint and about 80 as a stronger checkpoint, under a separate prospective contract.
6. Complete the fixed `CORNERS15` robustness check when the historical source is available again or an equivalently frozen point-in-time source is established.
7. Never use the early-drift framework to bypass `collect, don't peek` or any other frozen outcome embargo.

## External-source state during this block

On 2026-09-07 the live Historical Football Signal Lab could not re-download Football-Data because the provider returned HTTP 503, including old historical paths. This V1 block uses pinned prior evidence instead of disguising or bypassing that external outage.
