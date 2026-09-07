# SEASON_INVARIANT_CORNERS_V1 — Results

Status: HISTORICAL PRIMARY RESULT COMPLETE

## Evidence provenance

The decision thresholds were preregistered before this invariant result was calculated.

Primary season evidence comes from the already completed PR #57 Historical Football Signal Lab artifact:
- PR: #57
- head SHA: `ccd8ac88c7948cfdd0075dbe36ae1939e36a29fc`
- workflow run: `33772658431`
- artifact id: `9900313244`
- artifact digest: `sha256:711b12ee40c66555fc9039f2abdbb244d457591e72bf03cc17f5bb5d856bb7fa`
- artifact created: 2026-09-03, before this V1 invariant classification was defined.

The pinned paired reference used by the deterministic V1 audit is derived only from that artifact. Its repository digest is:
`dbca91d70590a03acc892f65a72ae46518582d27282882f3dba17fbe47cbd01f`.

No 2026-2027 outcomes were used.

## Primary result: CORNERS10 vs GOALS10

Lower Brier and log-loss are better.

| League | Unseen test seasons | Mean Brier delta | Brier wins | Mean log-loss delta | Log-loss wins | Frozen classification |
|---|---:|---:|---:|---:|---:|---|
| EPL | 7 | -0.005147 | 6/7 | -0.007027 | 6/7 | STRONG |
| La Liga | 7 | -0.004641 | 5/7 | -0.005603 | 5/7 | STRONG |
| Serie A | 7 | -0.006509 | 7/7 | -0.010516 | 7/7 | STRONG |

Frozen overall classification: **PORTABLE_STRONG**.

Interpretation: adding the fixed CORNERS10 football-state information to the comparable football-only GOALS10 model improved probability quality repeatedly across unseen seasons in all three tested leagues. The effect is not concentrated in one season or one league.

## Window robustness available from pre-existing evidence

The earlier PR #57 artifact contains fixed 5-match and 10-match windows.

For CORNERS5 vs GOALS5:
- EPL: mean Brier delta -0.006640; Brier wins 6/7; mean log-loss delta -0.009855; log-loss wins 5/7.
- La Liga: mean Brier delta -0.004026; Brier wins 6/7; mean log-loss delta -0.005248; log-loss wins 6/7.
- Serie A: mean Brier delta -0.008301; Brier wins 7/7; mean log-loss delta -0.012598; log-loss wins 7/7.

This supports the direction of the CORNERS10 result and argues against the effect existing only at exactly ten matches.

The preregistered 15-match robustness check is **not evaluated yet**. The old artifact predates CORNERS15, and Football-Data is currently returning HTTP 503 even for historical CSV paths. The 15-match check must remain pending rather than being reconstructed from a different or outcome-selected source.

The primary PORTABLE_STRONG decision does not depend on choosing CORNERS15; CORNERS10 was frozen as the primary candidate before evaluation.

## Incremental value over bookmaker market

Because the football-only result is PORTABLE_STRONG, the contract requires revisiting the already completed MARKET vs MARKET_CORNERS10 evidence.

This evidence comes from PR #58:
- PR: #58
- head SHA: `2b7e0257f34586834ae37beffe2072e496b4deb0`
- workflow run: `33773058968`
- artifact id: `9900461967`
- artifact created: 2026-09-03.

Historical paired result for MARKET_CORNERS10 vs fitted MARKET_MODEL:
- EPL: Brier wins 0/7, log-loss wins 0/7; mean deltas are worse (+0.003621 Brier, +0.006270 log-loss).
- La Liga: Brier wins 0/7, log-loss wins 0/7; mean deltas are worse (+0.005055 Brier, +0.007899 log-loss).
- Serie A: Brier wins 2/7, log-loss wins 2/7; mean deltas are worse overall (+0.003496 Brier, +0.005427 log-loss).

Interpretation: CORNERS10 is a real and portable football-state signal, but the historical 1X2 bookmaker market already appears to contain most or all of that information. Adding CORNERS10 on top of market probabilities did not improve the historical market model.

Historical bookmaker prices in this lab are research data; their timestamp is not assumed to be identical to the live prediction-time market snapshot.

## Decision

1. Keep CORNERS10 as a validated portable football-state signal.
2. Do not promote CORNERS10 as a proven 1X2 market edge.
3. Do not change production `.pkl` models from this result.
4. Use CORNERS10 as a candidate ingredient for other targets where the market may not already absorb the same information, especially future corners-specific and related football-state research.
5. Use fresh 2026-2027 observations as a separate drift monitor with its own prospective contract, not as another 100-match discovery requirement.
6. Complete the fixed CORNERS15 robustness check only when the historical source is available again or an equivalently preregistered point-in-time source is established.

## External-source state during this block

On 2026-09-07 the existing live Historical Football Signal Lab could not re-download the source because Football-Data returned HTTP 503, including an old EPL 2016/17 path. The existing live-source workflow remains fail-closed; this V1 block does not weaken or disguise that external red signal.
