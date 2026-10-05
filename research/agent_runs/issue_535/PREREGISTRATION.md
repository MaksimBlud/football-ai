# Frozen bookmaker margin-structure protocol

Status: **PREREGISTERED / TEMPORAL OOS / MATCHED FIXTURES / RESEARCH ONLY / NO_BET**.

Question: do Bet365 and Pinnacle differ systematically not only in total 1X2 overround but in where they allocate price pressure across favourite, middle and longshot outcomes?

Frozen scope:
- leagues: EPL, La Liga, Serie A;
- bookmakers: Bet365 and Pinnacle only;
- primary market: 1X2;
- horizons: opening and closing;
- reference: 2019/20-2023/24;
- validation: 2024/25;
- untouched OOT: 2025/26.

Outcome-free source audit must pass before FTR is read. Required on every validation/test league-season:
- Bet365 opening + closing 1X2;
- Pinnacle opening + closing 1X2;
- Football-Data market-average opening + closing 1X2 (AvgH/AvgD/AvgA and AvgCH/AvgCD/AvgCA).

No bookmaker may be added or removed after outcomes. Exact 24h/6h/1h snapshots are unavailable in the frozen source and must be reported as SOURCE_GAP, never interpolated.

Primary external consensus:
- multiplicatively de-vigged Football-Data market-average odds.

For each bookmaker and fixture:
- q_i = 1 / odds_i;
- S = sum(q_i);
- total overround = S - 1;
- uniform-margin expected implied probability around consensus = consensus_p_i * S;
- allocation_tilt_i = q_i / (consensus_p_i * S) - 1.

This construction removes each bookmaker's total overround before asking where the remaining relative price tilt sits.

Frozen rank is determined from external consensus fair probabilities:
- favourite = highest consensus p;
- longshot = lowest consensus p;
- middle = remaining outcome.

Primary allocation statistic:
fl_allocation_contrast = longshot_allocation_tilt - favourite_allocation_tilt.

Primary paired effect:
Bet365 minus Pinnacle on the same fixture.

Secondary:
- draw allocation tilt;
- total overround difference;
- bookmaker fair-probability TV distance to market consensus;
- historical flat-stake return by frozen consensus-probability bins (diagnostic only).

Consensus sensitivity:
recompute the favourite-longshot allocation contrast using the mean of Bet365 and Pinnacle de-vigged fair probabilities as an alternate consensus. This sensitivity cannot create a positive result when the primary external-consensus gate fails.

Inference:
deterministic league-stratified fixture bootstrap, 5000 draws.

SUPPORTED_BOOKMAKER_MARGIN_HETEROGENEITY requires all:
1. validation closing primary allocation CI excludes zero;
2. untouched OOT closing primary allocation CI excludes zero;
3. validation and OOT primary effects have the same non-zero sign;
4. OOT opening and closing primary effects have the same non-zero sign;
5. alternate-consensus OOT allocation CI excludes zero;
6. alternate-consensus OOT effect has the same sign as the primary OOT effect;
7. at least two of three OOT league effects have the pooled OOT sign.

Otherwise return NO_STABLE_BOOKMAKER_MARGIN_HETEROGENEITY. Missing source coverage returns BLOCKED_BY_SOURCE_GAP.

The draw result is always reported separately. Total overround cannot rescue a failed allocation gate. Observational pricing differences must not be interpreted as causal evidence about bettor demand, bookmaker liabilities, or intent.

No production weighting/calibration change, no paid API, no Supabase, no promotion.
