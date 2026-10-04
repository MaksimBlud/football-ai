# CROSS-MARKET LEAD-LAG V1 — Results

Status: **FINAL / SUGGESTIVE BUT NOT SUPPORTED / NO_BET**.

## Provenance

First complete frozen run:

- workflow run: `37178316661`;
- artifact ID: `11293204444`;
- artifact digest:
  `sha256:e5ea14c9a877cc578bebd05c2da9b2b347375b4dc9a10215c421c605b9b7a359`;
- generating head:
  `dd26f222465934c8b1ab086f974cc2d0f9990990`.

No match outcome was used.

No 2026/27 data were used.

No paid provider call was made.

## Live source audit

The preferred true intraday experiment is not yet feasible from the current live
multi-market store.

`public.league_multi_market_snapshots` currently contained:

- 2 rows;
- 2 unique events;
- one snapshot per event;
- both events in Eredivisie;
- provider keys only `spreads` and `totals`.

Therefore V1 correctly used the historical Football-Data **opening -> closing** proxy rather
than pretending that a timestamped intraday sequence exists.

## What V1 tested

At Bet365 opening:

- derive opening 1X2 probabilities;
- use opening O/U 2.5 + half-goal Asian Handicap to reconstruct an independent synthetic
  1X2 distribution.

Then compare that opening cross-market lead vector with the later change from opening
Bet365 1X2 to closing Bet365 1X2.

Primary statistic:

`alignment_dot = dot(p_score_open - p_1x2_open, p_1x2_close - p_1x2_open)`.

Positive values mean closing 1X2 moved in the direction suggested by the other opening
markets.

The primary null permuted opening lead vectors among matches **within league and season**,
preserving the distributions of both leads and closing movements while destroying the
match-specific link.

## Coverage

Reference seasons 2019/20–2023/24:

**1,328 eligible matches**.

Validation 2024/25:

**282 matches**.

Untouched OOT 2025/26:

**256 matches**.

OOT by league:

- EPL: 93;
- La Liga: 81;
- Serie A: 82.

All frozen minimum sample gates were satisfied.

The AH inversion was numerically exact to floating-point tolerance in every retained row.

## Reference-period diagnostic

Across 2019/20–2023/24:

- mean alignment dot = **+0.00014860**;
- positive alignment rate = **58.06%**.

This was only a reference diagnostic and did not establish support.

## Validation — 2024/25

Validation passed the preregistered admissibility gate.

Pooled mean alignment:

**+0.00005292**

Positive mean alignment leagues:

**2 / 3**

Within-league permutation test:

- null mean = **-0.00003969**;
- observed mean = **+0.00005292**;
- one-sided p = **0.00050**.

Thus the match-specific opening O/U+AH residual aligned with later 1X2 movement much more
than randomly pairing another match's lead vector with the same closing movement.

Validation bootstrap was weaker:

- 95% CI = **[-0.00000274, +0.00011078]**.

A positive bootstrap CI was not required by the frozen validation gate, so:

`validation_admissible = true`.

By league mean alignment:

- EPL: **+0.00013573**;
- La Liga: **+0.00002825**;
- Serie A: **-0.00000645**.

## Untouched OOT — 2025/26

The OOT result remained directionally interesting.

Pooled mean alignment:

**+0.00004572**

All three leagues had positive mean alignment:

- EPL: **+0.00006637**;
- La Liga: **+0.00001872**;
- Serie A: **+0.00004896**.

The match-specific permutation result was again strong:

- null mean = **-0.00006302**;
- null 95% range = **[-0.00011907, -0.00000638]**;
- observed mean = **+0.00004572**;
- one-sided p = **0.00020**.

So the observed match-specific pairing was very unlikely under the frozen shuffled-link
null.

### Why the final gate still failed

The final protocol also required the stratified bootstrap 95% CI of the **absolute mean
alignment** to be entirely above zero.

Observed bootstrap:

- mean = **+0.00004584**;
- 95% CI = **[-0.00001073, +0.00010252]**;
- probability mean > 0 = **94.6%**.

The lower CI bound remained slightly below zero.

Therefore the preregistered final gate fails.

`test_gate = false`.

## Important diagnostics

The effect is not a simple majority-direction hit-rate signal.

OOT positive-alignment rate:

**49.61%**

That is essentially 50/50.

The information appears, if real, in the **magnitude and match-specific alignment** of
moves rather than in simply calling the sign correctly more often than not.

Component Pearson correlations on OOT:

- HOME lead vs HOME future move: **+0.138**;
- DRAW lead vs DRAW future move: **+0.150**;
- AWAY lead vs AWAY future move: **+0.196**.

Those are small but consistently positive.

At the same time, the closing 1X2 vector did **not** simply converge to the frozen opening
synthetic score vector.

Mean TV gap reduction on OOT:

**-0.01495**

So closing 1X2 was, on average, farther from the static opening synthetic vector in total
variation distance.

This matters: the result is not "AH/O-U predicts the exact closing probabilities." It is
only a possible weak match-specific directional component inside a larger market move.

## Formal decision

`NO_OPEN_TO_CLOSE_CROSS_MARKET_LEAD_SIGNAL`

`NO_BET`

The strict preregistered gate does not pass.

## Interpretation

This is **not** the same kind of clean negative result as the previous static coherence
experiment.

Two facts are simultaneously true:

1. validation and OOT both show highly significant match-specific alignment against the
   within-league permutation null;
2. the absolute OOT effect is small enough that its stratified bootstrap CI still crosses
   zero.

Therefore the correct interpretation is:

`SUGGESTIVE_MATCH_SPECIFIC_ALIGNMENT_BUT_FINAL_CI_CROSSES_ZERO`.

Do not:

- relax the CI gate;
- switch to a one-sided bootstrap after seeing the result;
- drop a league;
- select HOME/AWAY components post hoc;
- change the half-goal AH restriction;
- claim a tradable lead-lag signal;
- spend paid Odds API credits on this evidence alone.

## Next logical step

Before paying for a real timestamped intraday collector, use another **zero-cost independent
league replication** if byte-identical Football-Data open/close sources can be pinned for
Bundesliga and Ligue 1.

The exact V1 statistic, sign, same-bookmaker contract and permutation method must be
transferred unchanged.

If independent leagues reproduce positive match-specific alignment, that would justify
considering a prospective timestamped collector.

If they do not, close the lead-lag family without paid acquisition.

## Safety

- research-only;
- no outcomes used;
- no 2026/27 data;
- no paid Odds API calls;
- no Supabase writes;
- no model training;
- no production promotion;
- production `.pkl` unchanged.
