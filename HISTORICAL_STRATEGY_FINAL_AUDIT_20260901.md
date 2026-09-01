# Historical Strategy Final Audit — 2026-09-01

Status: **CLOSED RETROSPECTIVE BLOCK / RESEARCH ONLY / NO PRODUCTION PROMOTION**.

## Scope

This audit freezes and closes the retrospective EPL + La Liga 2016/17–2025/26 market study. Further work on the candidate is prospective or separately predeclared explanatory research; the current historical sample must not be used for more threshold hunting.

## Evidence established

- Historical Strategy Lab sample: 7,600 matches, 3,800 EPL + 3,800 La Liga.
- Overall MARKET_ONLY favourite baseline is not profitable and remains a benchmark, not a strategy.
- EPL frozen candidate failed robustness checks and is rejected as a strategy candidate.
- La Liga frozen candidate is HOME market pick with margin-free market confidence in [0.60, 0.70).
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

The evidence supports a persistent historical **market-pricing anomaly** in this La Liga segment. It does **not** establish that Football AI has unique predictive information. The rule is market-derived: bookmaker prices plus realised outcomes, not a Football AI structural/model feature.

A strong competing explanation is the favourite–longshot bias documented in football betting research. Large European-soccer studies report that odds-implied probabilities tend to understate favourites and overstate longshots, and recent market-structure work shows this pattern can arise from bookmaker pricing itself. Therefore this candidate must not be called Football AI alpha unless a paired incremental-information test beats the same de-vigged market benchmark on untouched fixtures.

## Confirmed

1. The original all-market favourite strategy is not a profitable general strategy.
2. The EPL candidate does not survive robustness analysis and is rejected.
3. `LA_LIGA_MARKET_HOME_60_70_V1` is historically unusual and robust enough to justify prospective monitoring.
4. The observed historical effect is not explained by one season, one home club, one bookmaker, or only standard versus closing prices in the completed tests.
5. Historical discovery and live forward OOS are separate evidence streams and must remain separate.

## Not confirmed

1. No causal football mechanism has been established.
2. No unique Football AI model edge has been established.
3. No guarantee of future positive ROI exists.
4. Transaction limits, account restrictions, execution latency, stake sizing, taxes/commission, and real-world price availability are not modelled as production constraints.
5. Historical Football AI probabilities aligned point-in-time to the exact frozen fixtures are not currently established by this block, so a historical model-vs-market alpha claim is not permitted.

## Frozen prospective candidate

Research label: `LA_LIGA_MARKET_HOME_60_70_V1`.

Machine-readable contract: `research/la_liga_market_home_60_70_v1.json`.

Prospective protocol: `docs/LA_LIGA_MARKET_HOME_60_70_V1_PROSPECTIVE_PROTOCOL.md`.

Definition:
- league = LA_LIGA;
- market pick = H;
- margin-free market confidence >= 0.60 and < 0.70;
- decision must be based on a recorded pre-kickoff canonical market snapshot;
- one-unit flat stake only for research accounting;
- no post-result team/month/season exclusions and no threshold reselection.

The definition is frozen. Future observations may score it but must not alter it.

## Football AI incremental-information gate

The repository now contains `market_model_incremental_audit.py` for the later paired test. It compares market and model probabilities on the **same fixtures and decision timestamps** using multiclass Brier and log loss and reports paired model-minus-market score differences with bootstrap uncertainty. Negative deltas favour the model.

This tool deliberately performs no fitting, threshold search, Supabase write, Structural activation, or model promotion. A Football-AI-specific claim is not allowed until genuine point-in-time model probabilities are available for untouched fixtures and this paired test supports improvement beyond market.

## Retrospective stopping rule

Effective with this audit:

- do not change 0.60/0.70 using any already observed historical or forward outcome;
- do not discover post-hoc team exclusions from the 270-match frozen OOS sample;
- do not relabel the market anomaly as model alpha;
- do not pool historical matches into prospective performance when deciding replication;
- do not activate wagering or production logic from this audit.

## Decision

Historical block verdict: **PROMISING MARKET ANOMALY / RETROSPECTIVE RESEARCH CLOSED / PROSPECTIVE VALIDATION REQUIRED**.

The retrospective objective is complete. The next evidence is intentionally allowed to arrive only from new prospective observations or from separately frozen explanatory/model hypotheses evaluated on untouched data.
