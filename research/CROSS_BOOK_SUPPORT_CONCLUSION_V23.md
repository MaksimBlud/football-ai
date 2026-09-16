# Cross-book Support Conclusion V23

## Status

Research-only. `NO_BET`. No production promotion.

## Question

Did the sharp loss of Pinnacle STANDARD coverage in Football-Data 2025/26 explain the synchronized failure of the historical `Pinnacle - Bet365` direction signal in EPL, Serie A and La Liga?

## Evidence frozen by V21/V22

V21 established a common 2025/26 Pinnacle STANDARD coverage break while Bet365 STANDARD and explicit closing coverage remained available. V22 then compared Bet365 STANDARD-to-explicit-closing movement on the full Bet365-valid sample against the subset where Pinnacle STANDARD was present.

For 2025/26:

| League | Pinnacle support | Material movement: covered vs full | Material direction: covered vs full |
| --- | ---: | ---: | ---: |
| EPL | 55.26% | 22.38% vs 23.68% | 31.91% vs 35.56% |
| Serie A | 52.63% | 26.50% vs 25.00% | 28.30% vs 29.47% |
| La Liga | 49.74% | 19.05% vs 17.63% | 50.00% vs 49.25% |

The missing-Pinnacle subset is not sufficiently different to explain the direction break. In particular, covered and full direction rates are close in Serie A and La Liga; EPL has a modest difference but the full Bet365 sample still shows the same large directional regime shift.

## Decision

Treat 2025/26 historical cross-book direction evidence as **confounded by a source-coverage break but not explained by common-support selection**. Do not repair the historical direction model by tuning `q`, `C`, rolling-window length, or a coverage filter against 2025/26.

The historical branch has now answered its useful question: cross-book STANDARD disagreement carried direction information in earlier seasons, but the relationship is not stable enough and the latest source semantics are not reliable enough for promotion.

## Next research contract

Return to timestamped prospective market-path data, where snapshot time is explicit. A future direction experiment must use a fixed earlier pre-kickoff snapshot and a last-pre-kickoff snapshot rather than Football-Data STANDARD as an opening proxy. Historical STANDARD remains historical context only.

Before any new prospective experiment is frozen, perform a read-only audit of live `odds_snapshots` coverage/cadence and verify that the chosen earlier horizon is actually supported. Reuse the existing frozen `PROSPECTIVE_MARKET_PATH_V1` contract where applicable; do not weaken its timing or sample gates to obtain results faster.
