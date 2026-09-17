# CROSS_LEAGUE_DIRECT_MARKETS_V1 — frozen result record

This file records the first successful execution of the preregistered `CROSS_LEAGUE_DIRECT_MARKETS_V1` contract. It does not modify the frozen experiment, reopen selection, authorize betting, or promote any model.

## Provenance

- Contract/implementation merge: PR #363.
- Exact tested PR head: `e17ce1bc806ab5f00aa78619bb5f2aee5c45696d`.
- Exact merge commit: `40aba10087558f213d595474764e948ef4031079`.
- Dedicated workflow: `Cross-League Direct Markets V1`.
- Successful run: `35224447842`.
- Result artifact: `10498882335` (`cross-league-direct-markets-v1`).
- Artifact digest: `sha256:f7b317294c7adb1eff8f00a0de7473346a675ebca28f789d5b35e48f58588a5a`.
- Evidence class: `HISTORICAL_TEMPORAL_OOT`.
- Train: 2016-17 through 2023-24.
- Validation/selection: 2024-25.
- Final OOT: 2025-26.
- 2026-27 outcomes used: false.
- Betting enabled: false (`NO_BET`).
- Production promotion: false.
- Production `.pkl` hash guard: passed.
- Paid Odds API calls: zero.
- Supabase writes: zero.

GitHub Actions could not reach the official Football-Data host because the runner network redirected it to loopback. The successful run therefore used the transport-only pinned raw-copy fallback already committed in PR #363. Every fallback CSV was accepted only after its computed Git blob SHA matched the preregistered manifest. The evaluator, targets, features, temporal splits, estimator and gates were unchanged.

## Direct O/U 2.5 result

All three leagues failed validation admissibility. The candidate was therefore not allowed to replace the bookmaker market in final active mode.

| League | OOT n | Validation Δ Brier | Validation Δ LogLoss | OOT market Brier | OOT candidate Brier | OOT market LogLoss | OOT candidate LogLoss | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| EPL | 380 | +0.003662737 | +0.007871049 | 0.247675914 | 0.250990889 | 0.688674454 | 0.695917272 | FAIL / MARKET_FALLBACK |
| La Liga | 380 | +0.001447033 | +0.002817354 | 0.241923164 | 0.245132336 | 0.676734541 | 0.683621907 | FAIL / MARKET_FALLBACK |
| Serie A | 380 | +0.001927658 | +0.003996282 | 0.252294526 | 0.259278267 | 0.698106071 | 0.713325206 | FAIL / MARKET_FALLBACK |

Frozen market-level decision:

- league PASS count: `0 / 3`;
- pooled OOT n: `1140`;
- because every league failed validation selection, pooled active probabilities are exact market probabilities;
- **decision: `SKIP`**.

Interpretation: under this fixed feature set and estimator, pre-match football-state did not add stable probabilistic information beyond the bookmaker O/U 2.5 price. The negative result applies to this preregistered construction; it is not a claim that no possible totals model can ever add value.

## Direct Asian Handicap result

EPL and Serie A were validation-admissible, but both reversed on untouched OOT. La Liga was not validation-admissible. Therefore every league finishes in market fallback.

| League | OOT n | Validation admissible | Validation Δ Brier | Validation Δ LogLoss | OOT Δ Brier | OOT Δ LogLoss | Status |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| EPL | 155 | yes | -0.005812943 | -0.011726438 | +0.000940173 | +0.002020743 | FAIL / MARKET_FALLBACK |
| La Liga | 141 | no | +0.001214259 | +0.002491671 | +0.005040188 | +0.009930172 | FAIL / MARKET_FALLBACK |
| Serie A | 150 | yes | -0.002649488 | -0.005331913 | +0.001087878 | +0.002192203 | FAIL / MARKET_FALLBACK |

Paired pooled OOT for the validation-selected candidates:

- n: `446`;
- market Brier: `0.249696602`;
- selected-candidate Brier: `0.250389222`;
- Δ Brier: `+0.000692620`;
- market LogLoss: `0.692506480`;
- selected-candidate LogLoss: `0.693946044`;
- Δ LogLoss: `+0.001439564`;
- league PASS count: `0 / 3`;
- **decision: `SKIP`**.

Accuracy does not override the frozen probabilistic gate. In particular, some AH candidate rows had slightly better classification accuracy while still worsening Brier and LogLoss; those variants remain rejected exactly as preregistered.

Interpretation: the apparent AH improvement seen in 2024-25 for EPL and Serie A did not persist into untouched 2025-26. That validation-to-OOT reversal is evidence against promoting this construction.

## Bookmaker corners

No bookmaker corner line+price test was run.

- status: `DATA_UNAVAILABLE`;
- post-match corner counts substituted for bookmaker prices: false;
- decision: **`COLLECT`**.

This remains separate from `CORNERS10` as a football-state signal. Historical corner counts can be pre-match features; they are not evidence about bookmaker corner-market prices.

## Final research decision

- O/U 2.5 direct market augmentation: **`SKIP`**.
- Asian Handicap direct market augmentation: **`SKIP`**.
- Bookmaker corners: **`COLLECT`** until provenance-verified line+both-side prices exist.
- 1X2 market-anchor work remains a separate evidence track and must not be conflated with these direct-market results.
- `NO_BET` and `NO_PRODUCTION_PROMOTION` remain binding.

Do not tune this V1 against the now-open 2025-26 OOT. Any different target definition, AH settlement scope, feature set, estimator, regularization or market-price transformation must be a separately named preregistered experiment with fresh evidence.