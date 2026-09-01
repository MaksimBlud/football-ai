# Historical Strategy Final Audit — 2026-09-01

Status: RESEARCH ONLY. No production promotion.

## Scope

This audit freezes the historical investigation after the EPL + La Liga 2016/17–2025/26 market study and records what is supported versus what remains hypothesis.

## Evidence established before this audit

- Historical Strategy Lab sample: 7,600 matches, 3,800 EPL + 3,800 La Liga.
- Overall MARKET_ONLY favourite baseline is not profitable and is retained as a benchmark, not a strategy.
- EPL frozen candidate failed robustness checks and is rejected as a strategy candidate.
- La Liga frozen candidate is: HOME market pick with margin-free market confidence in [0.60, 0.70).
- The La Liga rule was selected on the first three seasons and frozen before evaluation on the next seven seasons.
- Frozen La Liga OOS: 270 matches, 204 wins, 75.56% hit rate, approximately +10.10% flat-stake ROI.
- Mean margin-free market expectation in the frozen sample is approximately 64.83%, corresponding to roughly 175 expected wins versus 204 observed.
- Season-block bootstrap 95% ROI interval: approximately +2.89% to +16.58%.
- Leave-one-season-out ROI remains positive: approximately +8.55% to +13.00%.
- Selection-aware null simulation: approximately p=0.00515.
- Family-wise correction across the two investigated leagues: approximately p=0.01415.
- Same-fixture Bet365/Pinnacle and standard/closing comparisons remained positive.
- Leave-one-home-team-out ROI remained positive.
- All 119 season × home-team double-removal stress combinations remained positive; worst observed stress ROI was approximately +6.04%.

## Interpretation

The evidence supports a persistent historical market-pricing anomaly in this particular La Liga segment. It does **not** establish that Football AI has discovered unique predictive information. The rule is currently market-derived: it uses bookmaker prices and realised outcomes, not a Football AI structural/model feature.

A plausible competing explanation is the well-documented favourite–longshot bias in football betting markets. Therefore the historical signal must not be presented as model alpha until an incremental-information test demonstrates value beyond an appropriately de-vigged market/closing-price benchmark.

## What is confirmed

1. The original all-market favourite strategy is not a profitable general strategy.
2. The EPL candidate does not survive robustness analysis and should not be promoted.
3. The frozen La Liga HOME 60–70% segment is historically unusual and robust enough to justify prospective monitoring.
4. The effect is not explained by one season, one home club, one bookmaker, or only standard versus closing prices in the tests completed so far.
5. Historical discovery and live forward OOS must remain separate evidence streams.

## What is not confirmed

1. No causal football mechanism has been established.
2. No unique Football AI model edge has been established.
3. No guarantee of future positive ROI exists.
4. Transaction limits, account restrictions, execution latency, stake sizing, taxes/commission, and real-world price availability have not been modelled as production constraints.
5. The historical rule must not be tuned further against the current forward OOS sample.

## Frozen prospective candidate

Research label: `LA_LIGA_MARKET_HOME_60_70_V1`

Definition:
- league = LA_LIGA
- market pick = H
- margin-free market confidence >= 0.60 and < 0.70
- evaluate only using a predeclared eligible price snapshot
- one unit flat stake for research accounting

The definition is frozen. Future live observations may score it but must not alter its thresholds.

## Next evidence gate

The next meaningful test is prospective:

1. Tag future canonical La Liga observations that meet `LA_LIGA_MARKET_HOME_60_70_V1` before kickoff.
2. Record eligible snapshot time, bookmaker/source, quoted odds, de-vigged probability, and result immutably.
3. Report hit rate, expected wins, Brier/log loss where applicable, flat-stake ROI, CLV versus closing, and cumulative drawdown.
4. Keep this candidate research-only. Do not modify production `.pkl`, Structural alpha, edge thresholds, or live prediction selection.
5. Separately test whether Structural/model probabilities add incremental information to the market. A model should only be considered additive if it improves proper scoring / calibration or produces a predeclared prospective edge beyond the market benchmark.

## Decision

Historical block verdict: **PROMISING MARKET ANOMALY / PROSPECTIVE VALIDATION REQUIRED**.

This is sufficient to stop retrospective threshold hunting on this candidate. The research value now comes from preserving the frozen rule and testing it prospectively, while using historical football features only for separately predeclared explanatory hypotheses.
