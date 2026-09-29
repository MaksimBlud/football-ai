# 1X2_PRECLOSE_CLOSING_FORECAST_V1

Status: **research-only preregistered historical experiment**.

## Motivation

Two completed de-vig experiments kept the current multiplicative margin removal, but the
same common-fixture audit showed that explicit closing 1X2 prices are a better historical
probability benchmark than Football-Data's earlier ("first set") prices.

Football-Data documents that, since 2019/20, the first odds set is collected after market
opening at scheduled fixture-collection times and the second set (columns containing
`C`) is the closing set. This experiment therefore asks a different question:

> Can information available in the first-set 1X2 market predict part of the subsequent
> move to the explicit closing market?

This is a **closing-forecast / CLV-benchmark** experiment, not an outcome-betting strategy.

## Source and seasons

Zero-cost Football-Data EPL CSV files:

- 2019/2020
- 2020/2021
- 2021/2022
- 2022/2023
- 2023/2024
- 2024/2025
- 2025/2026

Exactly 380 matches per season are required.

Primary target source:

- first set: `B365H / B365D / B365A`
- explicit closing: `B365CH / B365CD / B365CA`

All odds are converted to fair 1X2 probabilities with the already-retained
MULTIPLICATIVE de-vig transform.

No Odds API calls and no Supabase access are required.

## Point-in-time feature sets

Closing columns and match outcomes are forbidden as model inputs.

### STATE

From the first-set Bet365 line only:

- fair home / draw / away probability;
- bookmaker overround;
- probability entropy;
- top probability;
- second probability;
- top-minus-second probability gap;
- home-minus-away probability.

### STATE_PLUS_CONSENSUS

STATE plus information from the contemporaneous Football-Data market average
`AvgH / AvgD / AvgA`:

- average fair home / draw / away probability;
- average overround;
- Bet365 minus average fair probability for H/D/A;
- Bet365 overround minus average overround.

The 2025/26 Football-Data market average composition changed because Pinnacle was no
longer included after its public API became unreliable. Therefore
STATE_PLUS_CONSENSUS must prove itself on the final season rather than being assumed
stable.

## Target

For each outcome:

`delta_i = closing_probability_i - first_set_probability_i`

A candidate predicts the three deltas. The resulting predicted closing vector is:

`predicted_close = normalize(first_set_probability + predicted_delta)`

Negative/zero entries are clipped only at `1e-9` before final normalization.

## Candidates

Baseline:

- `ZERO`: no predicted movement; predicted close equals first-set probabilities.

Diagnostics:

- `MEAN_DELTA`: historical mean 3-vector from development data.

Learned candidates:

- `RIDGE_STATE`
- `RIDGE_STATE_PLUS_CONSENSUS`

Frozen Ridge alpha grid:

- 0.01
- 0.1
- 1.0
- 10.0
- 100.0

Ridge is fit independently for H/D/A movement using only first-set inputs.

## Temporal protocol

### Development

Train: 2019/20–2022/23.

Selection validation: 2023/24.

A non-ZERO candidate is selectable only if it improves **both** closing-distance metrics
against ZERO on 2023/24:

1. mean per-match probability MAE to explicit close;
2. close cross-entropy
   `-sum(p_close * log(p_predicted_close))`.

Among eligible candidates, lowest close cross-entropy wins; MAE is the tie-breaker.
If none qualify, selection fails closed to ZERO.

### Holdout 1

2024/25.

The selected candidate/hyperparameters are frozen. Model coefficients are refit on
2019/20–2023/24, then evaluated once.

### Holdout 2 / replication

2025/26.

The same selected feature variant and alpha remain frozen. Coefficients are allowed to
expand through 2024/25, then evaluated once on 2025/26.

No hyperparameter or feature-set selection is repeated.

## Primary support gate

`ROBUST_PRECLOSE_TO_CLOSE_SIGNAL` requires:

- a non-ZERO candidate selected on 2023/24;
- lower close MAE and lower close cross-entropy on 2024/25;
- lower close MAE and lower close cross-entropy on 2025/26;
- on the pooled 760 holdout matches, paired-bootstrap 95% CIs for candidate-minus-ZERO
  are entirely below zero for both metrics.

Otherwise interpretation is `NO_ROBUST_PRECLOSE_TO_CLOSE_SIGNAL`.

## Secondary diagnostics

Not used for model selection:

- realized-outcome 1X2 LogLoss and Brier for first-set, predicted-close, and actual close;
- component-wise movement direction accuracy;
- maximum absolute movement MAE;
- by-season average movement;
- share of matches where closing argmax differs from first-set argmax.

Actual closing probabilities are an historical benchmark only and are never treated as
available before their true timing.

## Safety

- research only;
- zero paid API calls;
- no Supabase reads/writes;
- no production model reads or writes required;
- no `.pkl` creation;
- no promotion;
- JSON research output only.

## First frozen execution

First complete run:

- workflow run: `36514670639`
- head: `d6cb036250a12ff37df64fba6f07a1e1d807b06f`
- artifact: `11010521032`
- artifact digest:
  `sha256:4fc3aea2fea56c1efa1256eea8301dace6b20ea9499035d2d997fe2e6daa69f4`

Environment:

- pandas `3.0.6`
- numpy `2.5.3`
- requests `2.32.5`
- scikit-learn `1.9.1`

### Selection result — 2023/24

The frozen selector chose:

`RIDGE_STATE_PLUS_CONSENSUS_A0.01`

The Bet365-only STATE variants did **not** beat ZERO on both closing-distance metrics.
The improvement appeared only after adding contemporaneous market-average information and
Bet365-vs-average disagreement features.

Validation:

| Metric | ZERO | Candidate | Delta |
| --- | ---: | ---: | ---: |
| close MAE | 0.01625106 | **0.01608266** | **-0.00016839** |
| close cross-entropy | 0.95350626 | **0.95336207** | **-0.00014419** |
| realized outcome LogLoss | **0.90921248** | 0.90975646 | +0.00054398 |

The candidate passed the preregistered closing-distance selection gate. Outcome LogLoss
was deliberately not a selection metric.

### Holdout 1 — 2024/25

| Metric | ZERO | Candidate | Delta |
| --- | ---: | ---: | ---: |
| close MAE | 0.01707185 | **0.01707100** | **-0.00000085** |
| close cross-entropy | 0.97097449 | **0.97094777** | **-0.00002672** |
| outcome LogLoss | **0.97075767** | 0.97137479 | +0.00061711 |
| outcome Brier | **0.57866380** | 0.57917178 | +0.00050798 |
| max-move magnitude MAE | 0.02560777 | **0.01980044** | **-0.00580733** |

Movement-component direction accuracy: **53.25%**.

The primary closing-distance gate passed, but the candidate did not improve realized
match-outcome probability quality in this season.

### Holdout 2 — 2025/26

| Metric | ZERO | Candidate | Delta |
| --- | ---: | ---: | ---: |
| close MAE | 0.01735239 | **0.01720323** | **-0.00014916** |
| close cross-entropy | 1.00020401 | **1.00007775** | **-0.00012626** |
| outcome LogLoss | 1.01854743 | **1.01627488** | **-0.00227255** |
| outcome Brier | 0.61151221 | **0.61039310** | **-0.00111911** |
| max-move magnitude MAE | 0.02602858 | **0.02046285** | **-0.00556573** |

Movement-component direction accuracy: **55.53%**.

This season passed the closing-distance gate and also improved the secondary realized
outcome metrics.

### Pooled 760-match bootstrap

Candidate minus ZERO:

**Close cross-entropy**

- mean delta: `-0.00007649`
- 95% CI: `[-0.00013686, -0.00001495]`
- bootstrap probability candidate better: **99.12%**

**Close MAE**

- mean delta: `-0.00007501`
- 95% CI: `[-0.00032192, +0.00017374]`
- bootstrap probability candidate better: **71.57%**

Therefore the strict frozen gate is **not** passed because the close-MAE confidence
interval crosses zero.

Frozen interpretation:

`NO_ROBUST_PRECLOSE_TO_CLOSE_SIGNAL`

## Research interpretation

V1 does **not** justify production use of the predicted closing probabilities.

However, it produced a narrower signal worth independent replication:

> Bet365 first-set market state alone was insufficient; the selected model required
> contemporaneous **market-consensus / Bet365-vs-average disagreement** features.

That model then improved close cross-entropy in both holdouts, improved movement-magnitude
MAE materially in both holdouts, and achieved modestly-above-chance movement-direction
accuracy. The evidence is incomplete because probability MAE did not achieve the frozen
bootstrap requirement and realized-outcome gains were inconsistent across the two
holdouts.

The next defensible test is therefore **not** to loosen the V1 threshold. It is to freeze
this exact signal family and replicate it out of league (La Liga, Serie A, Bundesliga,
Ligue 1) without retuning the feature set or Ridge alpha.
