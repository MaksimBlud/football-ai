# CROSS-MARKET LEAD-LAG — INDEPENDENT LEAGUE REPLICATION V1

Status: **PREREGISTERED / RESEARCH-ONLY / NO_BET / ZERO-COST**.

## Purpose

Replicate the frozen `CROSS_MARKET_LEAD_LAG_V1` result on leagues that were not used in
the original EPL / La Liga / Serie A experiment.

The original V1 found statistically unusual match-specific alignment between opening
Bet365 O/U + Asian Handicap information and the later Bet365 1X2 move, but its final
absolute-effect bootstrap CI crossed zero. This replication must therefore preserve the
original statistic and direction and may not be tuned after seeing Bundesliga or Ligue 1
closing-price targets.

## Frozen leagues

- Bundesliga (`D1`)
- Ligue 1 (`F1`)

These leagues are independent of the original three-league sample.

## Frozen temporal split

Exactly the same seasons as V1:

- reference / descriptive only: 2019/20 through 2023/24
- validation: 2024/25
- untouched OOT test: 2025/26

No 2026/27 data are permitted.

## Frozen source

Football-Data season CSVs, transported through pinned byte-identical public GitHub copies
when the official host is unavailable in CI.

Pinned repository:

- `Emire221/kahin`
- commit `97c22f31564baafbd18ef818bb2df9fcb49319bc`

Pinned Git blob identities:

### Bundesliga

- 2019/20: `a07e4ab36464bd1c4b62c2e98e4559aff4fdb4ef`
- 2020/21: `0d3370c801e43c5dcb9012e405678dc5179b325d`
- 2021/22: `5796451d8caa093b8176f6eecf82051a239604f6`
- 2022/23: `406b28aee2ccd37177eec474447f4a3325247db4`
- 2023/24: `54efdb13aa7b537a80aca0a2378942d373594c06`
- 2024/25: `5ab934bebe32bfd689d97eb8303795dac4e8c407`
- 2025/26: `e8b2bffe7a16a794feb6985fe5ea50dcdd2f4137`

### Ligue 1

- 2019/20: `4e2cd6384a05d10cd9ad1a4c1b4d087d60fddd45`
- 2020/21: `0227119200af3698163fb0265d0910e377bcf335`
- 2021/22: `b98b8533c186704863ef63f25f65be770a4289d6`
- 2022/23: `f6cbe993e0a6be9322026acaed8015cb5e5ee14b`
- 2023/24: `3836a0b1a91ca4e9f97a61bbe3717b5fddd1a131`
- 2024/25: `fe5478bb28dd899b9646207ffc8e01bbb2dfc5ff`
- 2025/26: `cb484bdf3522fa081be58eefb497065fb4912810`

No source substitution is allowed after the first target-bearing run.

## Frozen market contract

Same bookmaker and same fields as V1.

Opening Bet365 1X2:
- `B365H`
- `B365D`
- `B365A`

Opening Bet365 O/U 2.5:
- `B365>2.5`
- `B365<2.5`

Opening Bet365 Asian Handicap:
- line: first finite value from `AHh`, then `B365AH`
- `B365AHH`
- `B365AHA`

Closing Bet365 1X2:
- `B365CH`
- `B365CD`
- `B365CA`

Exactly as V1, only exact half-goal Asian Handicap lines are eligible.

## Frozen reconstruction

Reuse the already-frozen `CROSS_MARKET_SCORE_COHERENCE_V1` reconstruction without
parameter changes:

1. infer total goal intensity from opening O/U 2.5;
2. infer home goal share from opening half-goal AH;
3. derive home/away Poisson intensities;
4. convert to synthetic HOME/DRAW/AWAY probabilities.

No match result, goals, shots, corners or any post-match field may be read by feature,
target, gate or subset logic.

## Frozen primary statistic

Let:

- `p_open` = opening Bet365 no-vig 1X2;
- `p_score_open` = opening synthetic 1X2 reconstructed from O/U + AH;
- `p_close` = closing Bet365 no-vig 1X2.

Define:

`lead = p_score_open - p_open`

`move = p_close - p_open`

Primary per-match statistic:

`alignment_dot = dot(lead, move)`

Positive values mean the later 1X2 move aligned with the discrepancy implied by the
other opening markets.

The sign, scale and statistic may not be changed after target-bearing data are opened.

## Frozen primary null

Use the V1 permutation design unchanged:

- keep each match's opening→closing 1X2 move fixed;
- permute opening lead vectors among matches within the same league;
- recompute pooled mean alignment;
- 10,000 draws;
- one-sided p-value for observed mean >= shuffled null;
- random seed `20261004`.

Because the replication split is one season at a time, league stratification is equivalent
to the original within-league-season rule.

## Frozen uncertainty estimate

Stratified-by-league bootstrap:

- 10,000 draws;
- random seed `20261004`;
- report two-sided 95% CI of pooled mean `alignment_dot`.

No one-sided bootstrap may be substituted after seeing results.

## Frozen sample gate

For both validation and OOT:

- each league must have at least 40 eligible reconstructed rows.

If either league misses this gate, the replication is `INSUFFICIENT_SAMPLE`, not a
positive or negative statistical result.

## Validation gate — 2024/25

Validation is admissible only if all are true:

1. sample gate passes;
2. pooled mean `alignment_dot > 0`;
3. **both 2/2 leagues** have positive mean alignment;
4. permutation one-sided p-value < 0.05.

No condition may be relaxed after validation.

## Untouched OOT gate — 2025/26

Independent replication is supported only if validation is admissible and all OOT
conditions are true:

1. sample gate passes;
2. pooled mean `alignment_dot > 0`;
3. **both 2/2 leagues** have positive mean alignment;
4. permutation one-sided p-value < 0.05;
5. stratified bootstrap 95% CI lower bound > 0.

Formal supported decision:

`INDEPENDENT_LEAGUE_REPLICATION_SUPPORTED`

Otherwise:

`INDEPENDENT_LEAGUE_REPLICATION_NOT_SUPPORTED`

The result always remains `NO_BET`.

## Supporting diagnostics

Report without changing the decision:

- mean / median alignment;
- positive-alignment rate;
- component Pearson/Spearman correlations;
- gap-reduction TV diagnostics;
- opening→closing move magnitude;
- by-league metrics;
- reconstruction residuals;
- row coverage by season.

## Interpretation boundary

A positive result would justify considering a separate prospective timestamped
multi-market collector.

It would **not** prove:
- exact intraday quote ordering;
- profitability;
- a production-ready betting rule;
- that AH rather than totals carries the information.

A negative result closes this specific historical lead-lag proxy family unless genuinely
new information becomes available.

## Safety

- research-only;
- `NO_BET`;
- no 2026/27 data;
- no paid Odds API calls;
- no Supabase writes;
- no model training;
- no production promotion;
- no production `.pkl` changes.
