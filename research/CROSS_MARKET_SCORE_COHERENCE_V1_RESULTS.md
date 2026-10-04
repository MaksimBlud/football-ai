# CROSS-MARKET SCORE COHERENCE V1 — Results

Status: **FINAL / NO_INDEPENDENT_CROSS_MARKET_COHERENCE_SIGNAL / NO_BET**.

## Provenance

First complete historical temporal-OOT run:

- workflow run: `37027753874`;
- artifact ID: `11236122159`;
- artifact digest:
  `sha256:ab6e0e49eb13265aa888ff5c809b94cccae06dc3b46ad812ebd3a97cbc2b991e`;
- generating head:
  `7249a90e515b3a11af0fe214277157e8ec79c998`.

The experiment used Bet365-only 1X2, O/U 2.5 and half-goal Asian Handicap prices.

No 2026/27 outcomes were used.

## What was tested

For each eligible match:

1. remove margin from Bet365 1X2;
2. infer total expected goals from Bet365 O/U 2.5;
3. infer home/away goal share from Bet365 Asian Handicap;
4. reconstruct a Poisson/Skellam score model;
5. convert that score model back to a synthetic 1X2 vector;
6. calculate total-variation distance between quoted Bet365 1X2 and synthetic 1X2.

Primary feature:

`score_gap_tv`.

The primary target was **excess Brier**, not raw Brier:

`excess_brier = realized_market_brier - (1 - sum(p_market_i^2))`.

This explicitly controls for the fact that strong-favorite markets naturally have a
different raw Brier distribution.

## Historical coverage

Because the required Bet365 O/U + Asian Handicap columns are absent in 2016/17–2018/19,
the effective reconstruction sample begins in 2019/20.

Total reconstructed rows:

- EPL: **654**;
- La Liga: **594**;
- Serie A: **618**.

Every retained AH row was an exact half-goal line and every structural inversion succeeded
with a bracketed root.

The 2024/25 validation sample contained **282** reconstructed matches.

The untouched 2025/26 OOT sample contained **256** reconstructed matches.

## Train-only thresholds

The HIGH/LOW thresholds were fixed from train/reference seasons only.

EPL:

- LOW q25 = **0.0116254**;
- HIGH q75 = **0.0202850**.

La Liga:

- LOW q25 = **0.0109443**;
- HIGH q75 = **0.0216524**.

Serie A:

- LOW q25 = **0.0126345**;
- HIGH q75 = **0.0234802**.

No threshold was changed after validation or OOT was opened.

## Validation — 2024/25

The primary hypothesis required HIGH coherence-gap matches to have **higher** excess Brier
than LOW-gap matches.

Observed pooled HIGH-minus-LOW excess Brier:

**-0.0527824**

So the sign was opposite the preregistered hypothesis.

By league:

- EPL: **-0.111270**;
- La Liga: **-0.024465**;
- Serie A: **-0.003732**.

Positive leagues:

**0 / 3**

The validation gate therefore failed.

There was also a frozen sample-size failure in La Liga:

- HIGH = 27;
- LOW = 13;

while the preregistered minimum was 15 per tail.

Formal result:

`validation_admissible = false`.

### Validation market-vs-synthetic diagnostic

Actual Bet365 1X2:

- Brier = **0.541707**;
- LogLoss = **0.919938**;
- Accuracy = **59.93%**.

Synthetic O/U+AH score-model 1X2:

- Brier = **0.540016**;
- LogLoss = **0.916879**;
- Accuracy = **59.93%**.

The synthetic score model was marginally better in this single validation season, but this
was a secondary diagnostic and cannot override the failed primary coherence gate.

## Untouched OOT — 2025/26

The final OOT sample did not rescue the hypothesis.

Pooled HIGH-minus-LOW excess Brier:

**+0.0004701**

This is effectively zero.

By league:

- EPL: **+0.151520**;
- La Liga: **-0.047115**;
- Serie A: **-0.131089**.

Positive leagues:

**1 / 3**

The OOT sample-size gate itself passed:

- EPL: HIGH 24 / LOW 26;
- La Liga: HIGH 35 / LOW 16;
- Serie A: HIGH 24 / LOW 19.

But the directional robustness gate failed because only EPL had the expected positive sign.

### OOT bootstrap

Stratified-by-league bootstrap, 10,000 draws:

- mean delta = **-0.0000577**;
- 95% CI = **[-0.113122; +0.110887]**;
- probability delta > 0 = **0.5006**.

The confidence interval spans zero very widely. There is no statistical evidence that
large cross-market structural disagreement identifies less reliable 1X2 prices.

### OOT market-vs-synthetic diagnostic

Actual Bet365 1X2:

- Brier = **0.629424**;
- LogLoss = **1.046580**;
- Accuracy = **47.66%**.

Synthetic O/U+AH score-model 1X2:

- Brier = **0.631630**;
- LogLoss = **1.049261**;
- Accuracy = **47.66%**.

On untouched OOT, the actual 1X2 market was slightly better than the synthetic score model.

## Continuous diagnostic

On OOT, `score_gap_tv` versus excess Brier:

- Pearson = **-0.0090**;
- Spearman = **+0.0747**.

This is effectively no useful monotonic relationship.

The AH inversion itself was numerically exact to floating-point tolerance, so the null
result is not caused by failed AH root fitting.

## Final decision

`NO_INDEPENDENT_CROSS_MARKET_COHERENCE_SIGNAL`

`NO_BET`

The experiment does **not** support the idea that static disagreement between Bet365 1X2
and the score distribution implied by Bet365 O/U 2.5 + Asian Handicap is a robust
uncertainty signal beyond the quoted 1X2 probabilities themselves.

Do not:

- change the HIGH/LOW quantiles;
- reverse the sign because validation was negative;
- select EPL post hoc because it was positive in 2025/26;
- drop La Liga or Serie A;
- replace excess Brier with raw Brier to manufacture support;
- promote the synthetic score model from the validation-season secondary diagnostic;
- use this result for betting or production promotion.

## What this teaches us

This closes another class of **static-price transformations**.

So far, simple de-vig alternatives, global market calibration, Max-vs-Avg spread and now
static 1X2/O-U/AH structural disagreement have all failed to provide robust independent
information after proper controls.

The stronger remaining research direction is therefore **temporal market information**:
how prices move, in what order different markets move, and whether one market leads another
before kickoff.

That is genuinely different information because it uses the path through time, not another
deterministic transformation of one static pre-match snapshot.

## Safety

- research-only;
- historical temporal OOT;
- 2026/27 outcomes not used;
- no paid Odds API calls;
- no Supabase writes;
- no production model changes;
- no production promotion;
- result remains `NO_BET`.
