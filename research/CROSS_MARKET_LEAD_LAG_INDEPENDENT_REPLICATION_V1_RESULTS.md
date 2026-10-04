# CROSS-MARKET LEAD-LAG — INDEPENDENT LEAGUE REPLICATION V1 — Results

Status: **FINAL / NOT SUPPORTED / NO_BET**.

## Provenance

First complete frozen run:

- workflow run: `37178894589`;
- artifact ID: `11294905716`;
- artifact digest:
  `sha256:d37588ac0fdcdaa9cf319c63859eda2e3703a338650ac1a0e86c38a236c31f4c`;
- generating head:
  `e74d13d3139d59e64e6a6eb9948337a1e6573cbb`;
- preregistration commit:
  `67f8cfae2364bb44444502ae3cc9d9c7e3cba1b7`.

The preregistration was committed before opening the Bundesliga / Ligue 1
target-bearing closing-price data.

No match outcomes were used.

No 2026/27 data were used.

No paid provider call or Supabase write was made.

Production model hashes were captured before the experiment and verified unchanged after
the run.

## Question

The parent `CROSS_MARKET_LEAD_LAG_V1` found suggestive but formally unsupported
match-specific alignment in EPL, La Liga and Serie A:

`opening Bet365 O/U + AH synthetic 1X2 residual -> later Bet365 closing 1X2 move`.

This replication transferred the exact statistic and direction to two independent leagues:

- Bundesliga;
- Ligue 1.

The frozen per-match statistic remained:

`alignment_dot = dot(p_score_open - p_1x2_open, p_1x2_close - p_1x2_open)`.

Positive values mean closing 1X2 moved in the direction implied by the other opening
markets.

## Sample

The minimum frozen sample gate was 40 eligible matches per league in both validation and
OOT. It passed.

Validation 2024/25:

- Bundesliga: **64**;
- Ligue 1: **73**;
- pooled: **137**.

Untouched OOT 2025/26:

- Bundesliga: **76**;
- Ligue 1: **92**;
- pooled: **168**.

Reference 2019/20–2023/24 contained **749** eligible matches.

All retained Asian Handicap inversions reconstructed successfully; no reconstruction
failure was recorded.

## Reference diagnostic — 2019/20 through 2023/24

Descriptive only:

- mean alignment dot: **+0.00013964**;
- positive-alignment rate: **56.48%**;
- mean synthetic-gap reduction: **-0.01420**.

The reference period looked directionally similar to the parent experiment, but it did
not participate in the final support decision.

## Frozen validation — 2024/25

The validation gate **failed**.

Pooled mean alignment:

**+0.00001213**

By league:

- Bundesliga: **-0.00000053**;
- Ligue 1: **+0.00002323**.

Thus only **1 of 2** frozen leagues had positive mean alignment, while the preregistered
gate required both.

Within-league permutation test:

- observed mean: **+0.00001213**;
- shuffled-null mean: **-0.00002982**;
- null 95% range: **[-0.00012253, +0.00006502]**;
- one-sided p: **0.1933**.

Validation bootstrap:

- 95% CI: **[-0.00008197, +0.00009962]**;
- probability pooled mean > 0: **60.99%**.

Positive-alignment rate:

**48.18%**.

Therefore:

`validation_admissible = false`.

This is decisive under the preregistered protocol.

## Untouched OOT — 2025/26

The OOT season was much stronger.

Pooled mean alignment:

**+0.00010681**

Both leagues were positive:

- Bundesliga: **+0.00012494**;
- Ligue 1: **+0.00009183**.

Within-league permutation test:

- observed mean: **+0.00010681**;
- shuffled-null mean: **+0.00001174**;
- null 95% range: **[-0.00006405, +0.00008831]**;
- one-sided p: **0.00760**.

Stratified bootstrap:

- mean: **+0.00010660**;
- 95% CI: **[+0.00003668, +0.00018327]**;
- probability mean > 0: **99.86%**.

Positive-alignment rate:

**52.98%**.

Component Pearson correlations were all positive:

- HOME: **+0.189**;
- DRAW: **+0.139**;
- AWAY: **+0.116**.

So, considered in isolation, the untouched 2025/26 split passed every frozen OOT condition:

`test_gate = true`.

## Why the final decision is still negative

The final rule was frozen before the data were opened:

`supported = validation_admissible AND test_gate`.

The 2024/25 validation failed, so the later strong 2025/26 season cannot rescue the
experiment.

Changing the rule after seeing this pattern would convert the replication into a
post-hoc selection exercise.

Formal decision:

`INDEPENDENT_LEAGUE_REPLICATION_NOT_SUPPORTED`

`NO_BET`

## What this tells us

The parent three-league result was not reproduced with enough temporal stability to treat
the open cross-market residual as a robust lead-lag signal.

At the same time, the family is not a simple clean zero:

- the long reference period was positive;
- parent V1 showed strong shuffled-link evidence in its validation and OOT, but failed its
  absolute-effect CI;
- the independent 2025/26 split passed all frozen OOT gates;
- the independent 2024/25 split did not.

The safest interpretation is therefore:

`SEASON_DEPENDENT_ALIGNMENT_WITHOUT_STABLE_REPLICATION`.

This is not evidence for a trading rule.

## Additional diagnostic

As in the parent experiment, closing 1X2 did not simply converge to the static opening
synthetic O/U+AH vector.

Mean gap reduction was negative:

- validation: **-0.01566**;
- OOT: **-0.01568**.

So the possible information, when present, is a small match-specific directional
component inside a larger price-discovery process, not a prediction of the exact closing
probability vector.

## Research decision

Do not:

- weaken the validation gate;
- select only 2025/26;
- drop Bundesliga from 2024/25;
- change the sign/statistic;
- optimize a magnitude threshold on these opened data;
- spend paid Odds API credits on a timestamped collector for this hypothesis;
- promote anything to production.

The specific historical open→close cross-market lead-lag proxy is closed as **not
supported** under its frozen rules.

A future revisit should require genuinely new information, especially true timestamped
multi-market paths collected prospectively for a different preregistered hypothesis.

## Safety

- research-only;
- no outcome scoring;
- no 2026/27 data;
- zero paid Odds API calls;
- zero Supabase writes;
- no model training;
- production hashes unchanged;
- no production promotion;
- `NO_BET`.
