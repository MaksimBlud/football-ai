# CROSS-MARKET LEAD-LAG REPLICATION V2 — Results

Status: **FINAL / VALIDATION FAILED / 2025-26 OOT STRONGLY POSITIVE / REPLICATION NOT SUPPORTED / NO_BET**.

## Provenance

First successful independent-league replication run:

- workflow run: `37178799308`;
- artifact ID: `11294635923`;
- artifact digest:
  `sha256:85d697a58ee70365bf44c33cbb6860fb04091e5bbfcd0e40df2cbd309b1f6469`;
- generating head:
  `960861f2ecad900a43ae8cc22d2ce7245f57a4e3`.

An earlier workflow failed before reading replication data because the generic historical
runner did not register Bundesliga/Ligue 1. The repair froze explicit Football-Data source
codes `D1` and `F1`; the hypothesis, metric, sign and statistical gates were unchanged.

## What was transferred unchanged from V1

Same bookmaker:

**Bet365**

Primary statistic:

`alignment_dot = dot(p_score_open - p_1x2_open, p_1x2_close - p_1x2_open)`.

Where the synthetic opening score distribution is reconstructed from opening O/U 2.5 +
half-goal Asian Handicap.

Null:

- within-league permutation of opening lead vectors;
- 10,000 draws;
- seed `20261004`.

Final uncertainty gate:

- stratified-by-league bootstrap;
- 10,000 draws;
- same seed;
- 95% CI of absolute mean alignment must be entirely above zero.

No football outcome was used.

## Independent leagues

- Bundesliga;
- Ligue 1.

Pinned historical sources were verified by Git blob SHA before calculation.

No paid provider credits were used.

## Reference period — 2019/20–2023/24

Eligible rows:

**749**

Mean alignment:

**+0.00013964**

Positive-alignment rate:

**56.48%**

This again suggests some historical directional alignment, but it is a descriptive reference
period and cannot establish replication.

## Validation — 2024/25

Eligible rows:

**137**

Per league:

- Bundesliga: 64;
- Ligue 1: 73.

Pooled mean alignment:

**+0.00001213**

This is positive but very small.

By league:

- Bundesliga: **-0.00000053**;
- Ligue 1: **+0.00002323**.

Only **1/2** replication leagues had the required positive mean.

Positive per-match alignment rate:

**48.18%**

### Validation permutation

Observed mean:

**+0.00001213**

Permutation null mean:

**-0.00002982**

Null 95% interval:

**[-0.00012253, +0.00006502]**

One-sided permutation p:

**0.1933**

So the 2024/25 independent-league validation does not show statistically convincing
match-specific lead-lag.

### Validation bootstrap

95% CI:

**[-0.00008197, +0.00009962]**

Probability mean > 0:

**60.99%**

Frozen validation decision:

`validation_admissible = false`.

The preregistered replication already fails here.

## Untouched OOT — 2025/26

The 2025/26 result is very different.

Eligible rows:

**168**

Per league:

- Bundesliga: 76;
- Ligue 1: 92.

Pooled mean alignment:

**+0.00010681**

Both independent leagues were positive:

- Bundesliga: **+0.00012494**;
- Ligue 1: **+0.00009183**.

Positive per-match alignment rate:

**52.98%**

### OOT permutation

Observed mean:

**+0.00010681**

Permutation null mean:

**+0.00001174**

Null 95% interval:

**[-0.00006405, +0.00008831]**

One-sided permutation p:

**0.00760**

Thus the exact match-specific O/U+AH opening residual aligns with the later 1X2 move more
strongly than shuffled same-league pairings in 2025/26.

### OOT bootstrap

Mean:

**+0.00010660**

95% CI:

**[+0.00003668, +0.00018327]**

Probability mean > 0:

**99.86%**

This passes the frozen absolute-effect uncertainty gate.

Therefore:

`test_gate = true`.

## Why V2 is still formally negative

The protocol explicitly required **both**:

1. validation 2024/25 passes;
2. untouched OOT 2025/26 passes.

Validation failed.

OOT is not permitted to rescue the experiment after seeing it.

Formal V2 decision:

`LEAD_LAG_REPLICATION_NOT_SUPPORTED`

`NO_BET`

This protects us from declaring success by selecting the season that happened to work best.

## Combined interpretation with V1

The result is nevertheless scientifically interesting.

Original V1 OOT 2025/26:

- EPL: positive mean alignment;
- La Liga: positive;
- Serie A: positive;
- permutation p = **0.00020**;
- bootstrap CI only narrowly crossed zero.

Independent V2 OOT 2025/26:

- Bundesliga: positive;
- Ligue 1: positive;
- permutation p = **0.00760**;
- bootstrap CI fully above zero.

Thus **all five tested major leagues have positive mean alignment in 2025/26** under the
same frozen statistic.

But V2 validation 2024/25 did not reproduce the relationship.

The correct current interpretation is therefore not "lead-lag proven". It is:

> there may be a **season-dependent market regime** in 2025/26 in which opening O/U+AH
> disagreement contains information about subsequent 1X2 movement, but the relationship
> is not historically stable enough to satisfy the preregistered replication design.

## Important negative diagnostic

As in V1, the closing 1X2 distribution did not simply converge to the exact static opening
synthetic score distribution.

Mean gap reduction TV:

- validation: **-0.01566**;
- OOT: **-0.01568**.

So this is not a rule of the form "closing 1X2 eventually becomes the O/U+AH-implied
probability vector".

If there is a real mechanism, it is a small directional component within broader repricing.

## Decision

Do not:

- declare the lead-lag signal confirmed;
- change the validation season;
- combine validation and OOT after seeing the results to manufacture significance;
- select only 2025/26 as the new support window;
- drop Bundesliga from validation because it was near zero;
- change the sign or statistic;
- spend paid Odds API credits on a high-frequency collector yet;
- use the signal for betting or production.

## Next permitted step

A zero-cost **post-hoc regime-stability audit** is justified.

Its purpose is diagnostic only:

- calculate the already-frozen `alignment_dot` season-by-season across all five leagues;
- do not refit anything;
- identify whether 2025/26 is genuinely exceptional relative to prior seasons;
- examine whether the shift is broad across leagues or driven by one market component.

Because this question is motivated by the opened V1/V2 results, it must be labeled post-hoc
and cannot itself provide confirmatory support.

Only a future independently frozen prospective sample could convert a regime observation
into evidence strong enough to justify operational use.

## Safety

- research-only;
- NO_BET;
- no match outcomes;
- no 2026/27 data;
- zero paid Odds API calls;
- no Supabase writes;
- no production model operations;
- no production promotion;
- production `.pkl` unchanged.
